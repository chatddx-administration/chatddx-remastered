from pathlib import Path

import pytest
from pydantic import JsonValue

from chatddx.bench import Bench, NotFound
from chatddx.bench.test.helpers import correct_facts, move_model, trial
from chatddx.bench.updating import UPDATED
from chatddx.catalog import Edit, threads, titles
from chatddx.curation import Plan, init
from chatddx.factors.base import resolve
from chatddx.factors.engine import LocalEngine
from chatddx.factors.scoring import Judge, Scorer
from chatddx.factors.trial import Trial
from chatddx.inventory import DirectorySource, Inventory, World
from chatddx.store import Catalog, People, Store
from chatddx.test.world import (
    CASES,
    LINES,
    QWEN,
    QWEN_ARTIFACT,
    QWEN_MODEL,
    TEST,
    copied,
    edit,
    world_plan,
)


def _moved(bench: Bench) -> tuple[Edit, Inventory]:
    weights = move_model(bench, QWEN_ARTIFACT, revision="moved")
    store = Store(bench.conn)
    inventory = bench.inventory
    registry = store.load([inventory.endpoint(QWEN).engine, weights.digest])
    engine = resolve(registry.get, inventory.endpoint(QWEN).engine, LocalEngine)
    newer = registry.add(engine.model_copy(update={"model": weights.digest}))
    _ = store.add(registry, [newer])
    endpoints = dict(inventory.endpoints)
    endpoints[QWEN] = endpoints[QWEN].model_copy(update={"engine": newer})
    return weights, inventory.model_copy(update={"endpoints": endpoints})


def _head(bench: Bench, thread: int) -> Edit:
    return threads.head(bench.rows, thread)


def _named(bench: Bench, kind: str, name: str) -> int:
    [thread] = threads.find(bench.rows, kind, name)
    return thread


@pytest.mark.slow
def test_what_its_model_s_new_weights_leave_behind_is_outdated_and_updated(
    bench: Bench, plan: Plan
) -> None:
    mine = bench.thread(LINES, "configuration")[0].thread
    verdict = bench.fork(_named(bench, "judge", "verdict"), "my-verdict").edit.thread
    scorer = bench.fork(_named(bench, "scorer", "judged"), "my-judged").edit.thread
    made = trial(bench.conn, plan, LINES, "noted")
    tried = Catalog(bench.conn).create(made.digest, bench.person.id, name="mine").thread
    kinds = {mine: "skeleton", verdict: "judge", scorer: "scorer", tried: "trial"}
    assert not any(bench.outdated(_head(bench, t), k) for t, k in kinds.items())
    assert bench.update(verdict, _head(bench, verdict).id) is None

    weights, inventory = _moved(bench)
    later = Bench(bench.conn, bench.person, inventory)
    assert all(later.outdated(_head(later, t), k) for t, k in kinds.items())
    graded = later.title(
        resolve(later.store.get, _head(later, scorer).digest, Scorer).judges[-1]
    )
    updated = later.update_all()
    refused = {u.thread: u.refused for u in updated if u.refused is not None}
    assert list(refused) == [scorer]
    assert str(refused[scorer]) == f"my-judged can't be updated until {graded} is"
    assert [u.thread for u in updated][-3:] == [verdict, scorer, tried]
    assert {t for t, k in kinds.items() if later.outdated(_head(later, t), k)} == {
        scorer
    }

    judge = resolve(later.store.get, _head(later, verdict).digest, Judge)
    assert judge.model == weights.digest
    assert later.judged(judge).engine == inventory.endpoint(QWEN).engine
    compiled = later.rows.compilations(judge.skeleton)
    assert weights.digest in {c.recipe.model for c in compiled}
    ran = resolve(later.store.get, _head(later, tried).digest, Trial)
    assert ran.engine == inventory.endpoint(QWEN).engine
    assert weights.digest in {
        c.recipe.model for c in later.rows.compilations(ran.skeleton)
    }
    recipe = threads.recipe(later.rows, _head(later, mine))
    assert recipe is not None and recipe.model == weights.digest

    graded_fork = later.fork(_named(later, "judge", "graded"), "my-graded").edit.thread
    assert [u.thread for u in later.update_all()] == [graded_fork, scorer]
    asked = resolve(later.store.get, _head(later, scorer).digest, Scorer).judges
    assert set(asked) == {
        _head(later, verdict).digest,
        _head(later, graded_fork).digest,
    }
    assert not later.outdated(_head(later, scorer), "scorer")
    assert later.update_all() == []


def test_corrected_facts_alone_leave_it_usable(bench: Bench) -> None:
    mine = bench.thread(LINES, "configuration")[0].thread
    recommended = bench.facts.models[QWEN_MODEL].sampling.recommended
    sampled: dict[str, JsonValue] = {
        level: v.model_dump(mode="json") for level, v in recommended.items()
    }
    sampled |= {"off": {"temperature": 0.1}, "on": {"temperature": 0.2}}
    _ = correct_facts(bench, QWEN_MODEL, sampling={"recommended": sampled})
    assert bench.moved(mine) is not None
    assert not bench.outdated(_head(bench, mine), "skeleton")
    assert bench.update(mine, _head(bench, mine).id) is None


def test_only_its_owner_updates_it(bench: Bench) -> None:
    theirs = _named(bench, "judge", "verdict")
    with pytest.raises(NotFound, match=f"no judge {theirs} of yours"):
        _ = bench.update(theirs, _head(bench, theirs).id)


# Scope: a release as import-engine writes one, new weights under the handles and the
# engines serving them at the endpoints, loaded with init-data.
@pytest.mark.slow
def test_a_release_s_new_weights_leave_nothing_of_the_archive_s_out_of_date(
    bench: Bench, tmp_path: Path
) -> None:
    world = copied(tmp_path)
    engines = {
        r.digest: r.name for r in world_plan().stanzas if r.table == "local_engine"
    }
    edit(world / "engines.toml", 'revision = "fake"\n', 'revision = "released"\n')
    planned = world_plan(world, world / "_data")
    for spec in World.load(TEST).inventory.endpoints.values():
        if (name := engines.get(spec.engine)) is not None:
            new = planned.named("local_engine", name).digest
            edit(world / "endpoints.toml", spec.engine, new)
    released = World.load(world)
    source = released.inventory.source(kind=DirectorySource)
    plan = world_plan(world, world / "_data")
    _ = init(bench.conn, plan, CASES, source, bench.person, giftbag=True)

    later = Bench(bench.conn, bench.person, released.inventory)
    archive = People(bench.conn).find("archive")
    assert archive is not None
    held = [
        (k, e)
        for k in UPDATED
        for e, a in threads.heads(later.rows, k)
        if a.owner == archive.id
    ]
    assert held
    assert [
        f"{k} {titles.title(later.rows, e.thread)}"
        for k, e in held
        if later.outdated(e, k)
    ] == []
    assert later.outdated_own()

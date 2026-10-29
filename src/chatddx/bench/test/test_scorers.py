from typing import Any

import pytest
from pydantic import JsonValue

from chatddx.bench import Bench
from chatddx.bench.test.helpers import component, ran, trial, view_labels
from chatddx.catalog import Labels, threads
from chatddx.curation import Plan
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Scorer
from chatddx.identity import Person
from chatddx.scorers import metrics
from chatddx.scorers.scorer import Metrics
from chatddx.scorers.shipped import SCORERS
from chatddx.store import Catalog, People, Rows
from chatddx.store.store import Connection
from chatddx.test.helpers import SHIPPED
from chatddx.test.world import LINES

RAISED = metrics.score.version + 1


def _archive_s(bench: Bench, name: str) -> tuple[int, dict[str, Any]]:
    edit, about = bench.thread(name, "scorer")
    assert bench.login(about.owner) == "archive"
    return edit.thread, bench.store.get(edit.digest).model_dump(mode="json")


def _archive(conn: Connection) -> Person:
    found = People(conn).find("archive")
    assert found is not None
    return found


def test_a_person_writes_a_scorer_over_shipped_code_with_its_labels(
    conn: Connection, alice: Person, bench: Bench, plan: Plan
) -> None:
    _, doc = _archive_s(bench, "whole")
    assert (doc["entry_point"], doc["version"]) == (SHIPPED, metrics.score.version)
    ranked: JsonValue = {
        "split": "lines@1",
        "expectation": "/diagnosis",
        "metric": "reciprocal_rank",
    }
    mine = component({**doc, "views": [*doc["views"], ranked]})
    assert isinstance(mine, Scorer)

    made = bench.new(
        mine, "ranked", labels={("view", 0): "text", ("view", 1): "ranked"}
    )
    assert (made.what, made.findings) == ("created", [])
    assert view_labels(bench, made.edit) == {0: "text", 1: "ranked"}
    assert bench.labels(mine.digest) == {0: "text", 1: "ranked"}

    started = bench.run(ran(conn, alice, trial(conn, plan, LINES, "crlf")))
    assert "ranked" in {a.name for _, a, _ in bench.scorers(started)}
    assert mine.digest in bench.unscored(started)

    nowhere: JsonValue = {"expectation": "/nowhere", "metric": "mentions"}
    odd = bench.new(component({**doc, "views": [nowhere]}), "odd")
    assert [f.code for f in odd.findings] == ["view.unreachable"]


def test_a_scorer_the_running_code_could_never_score_with_is_refused(
    bench: Bench,
) -> None:
    _, doc = _archive_s(bench, "whole")
    [view] = doc["views"]
    refusals: list[tuple[dict[str, JsonValue], str]] = [
        ({"entry_point": "chatddx.scorers.patterns:_WORD"}, "isn't shipped with"),
        (
            {"version": RAISED},
            f"metrics:score is at version {RAISED - 1} in chatddx .*, not {RAISED}",
        ),
        ({"views": [{**view, "metric": "recall"}]}, "knows no metric recall"),
        (
            {"views": [{**view, "params": {"top": 3}}]},
            "view 0's params for first_mention don't fit",
        ),
        ({"params": {"top": 3}}, "the scorer's params don't fit"),
        ({"expectation_schema": "sha256:" + "0" * 64}, "not in the store"),
    ]
    for changes, refused in refusals:
        with pytest.raises(ValueError, match=refused):
            _ = bench.new(component({**doc, **changes}), "refused")

    scorer = component(doc)
    mislabelled: list[tuple[Labels, str]] = [
        ({("view", 1): "x"}, "has no view at position 1"),
        ({("resource", 0): "x"}, "has no resource at position 0"),
        ({("view", 0): ""}, "the label of view 0 is empty"),
    ]
    for labels, refused in mislabelled:
        with pytest.raises(ValueError, match=refused):
            _ = bench.new(scorer, "refused", labels=labels)
    sampling = bench.store.get(bench.thread("greedy", "sampling")[0].digest)
    with pytest.raises(ValueError, match="only a scorer's views and resources have"):
        _ = bench.new(sampling, "cool", labels={("view", 0): "x"})
    assert "refused" not in {a.name for _, a in bench.threads("scorer")}


@pytest.mark.slow
def test_a_fork_keeps_its_origin_s_labels_and_renames_its_own_views(
    conn: Connection, alice: Person, bench: Bench, plan: Plan
) -> None:
    origin, doc = _archive_s(bench, "list")
    head = threads.head(Rows(conn), origin)
    theirs = view_labels(bench, head)
    assert theirs == {0: "differential", 1: "dont-miss"}

    fork = bench.fork(origin, "my list")
    assert fork.edit.digest == head.digest
    assert view_labels(bench, fork.edit) == theirs
    started = bench.run(ran(conn, alice, trial(conn, plan, LINES, "crlf")))
    unscored = set(bench.unscored(started))

    scorer = component(doc)
    renamed: Labels = {("view", 0): "ddx", ("view", 1): "must not miss"}
    edited = bench.edit(fork.edit.thread, fork.edit.id, scorer, labels=renamed)
    assert (edited.what, edited.edit.digest) == ("a new version", head.digest)
    assert view_labels(bench, edited.edit) == {0: "ddx", 1: "must not miss"}
    assert bench.labels(head.digest) == {0: "ddx", 1: "must not miss"}
    assert set(bench.unscored(started)) == unscored

    thread, at = edited.edit.thread, edited.edit.id
    assert bench.edit(thread, at, scorer, labels=renamed).what == "unchanged"
    assert bench.edit(thread, at, scorer).what == "unchanged"

    assert view_labels(bench, threads.head(Rows(conn), origin)) == theirs
    archive = Bench(conn, _archive(conn), bench.inventory)
    assert archive.labels(head.digest) == theirs

    relabelled = bench.fork(origin, "relabelled", labels={("view", 1): "x"})
    assert view_labels(bench, relabelled.edit) == {1: "x"}
    one = component({**doc, "views": doc["views"][:1]})
    changed = bench.fork(origin, "changed", one)
    assert view_labels(bench, changed.edit) == {}


def test_a_scorer_digest_is_called_what_the_person_s_threads_called_it(
    bench: Bench,
) -> None:
    _, doc = _archive_s(bench, "list")
    first = component({**doc, "views": doc["views"][:1]})
    made = bench.new(first, "narrow", labels={("view", 0): "first"})
    second = component({**doc, "views": doc["views"][1:]})
    moved = bench.edit(made.edit.thread, made.edit.id, second)
    assert view_labels(bench, moved.edit) == {}
    assert bench.labels(first.digest) == {0: "first"}
    unseen = component({**doc, "views": doc["views"][::-1]})
    assert bench.labels(unseen.digest) == {}


def _renamed(conn: Connection, thread: int, labels: Labels) -> None:
    head = threads.head(Rows(conn), thread)
    _ = Catalog(conn).keep(head.digest, _archive(conn).id, thread, labels=labels)


def test_updating_from_an_origin_keeps_the_labels_of_the_views_it_keeps(
    conn: Connection, bench: Bench
) -> None:
    origin, doc = _archive_s(bench, "list")
    as_is = bench.fork(origin, "as is")
    one = component({**doc, "views": doc["views"][:1]})
    narrow = bench.fork(origin, "narrow", one, labels={("view", 0): "mine"})
    _renamed(conn, origin, {("view", 0): "ddx", ("view", 1): "dont-miss"})

    updated = bench.update(as_is.edit.thread, as_is.edit.id)
    assert updated.edit.digest == as_is.edit.digest
    assert view_labels(bench, updated.edit) == {0: "ddx", 1: "dont-miss"}
    kept = bench.update(narrow.edit.thread, narrow.edit.id)
    assert kept.edit.digest == one.digest
    assert view_labels(bench, kept.edit) == {0: "mine"}


def test_a_scorer_moves_on_to_a_raised_version_by_updating_from_its_origin(
    conn: Connection,
    alice: Person,
    bench: Bench,
    plan: Plan,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    origin, doc = _archive_s(bench, "whole")
    fork = bench.fork(origin, "my whole")
    monkeypatch.setitem(SCORERS, SHIPPED, Metrics(RAISED, metrics.score.metrics))
    raised = component({**doc, "version": RAISED})
    registry = bench.store.load(s.digest for s in raised.refs())
    _ = bench.store.add(registry, [registry.add(raised)])
    _ = Catalog(conn).keep(
        raised.digest, _archive(conn).id, origin, labels={("view", 0): "whole"}
    )

    made = trial(conn, plan, LINES, "crlf")
    started = bench.run(ran(conn, alice, made))
    [graded] = bench.score(started, [fork.edit.digest])
    assert graded.refused is not None
    assert f"metrics:score is at version {RAISED} in chatddx" in graded.refused

    updated = bench.update(fork.edit.thread, fork.edit.id)
    assert resolve(bench.store.get, updated.edit.digest, Scorer).version == RAISED
    assert view_labels(bench, updated.edit) == {0: "whole"}

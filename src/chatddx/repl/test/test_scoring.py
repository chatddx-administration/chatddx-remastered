import pytest
from pydantic import JsonValue

from chatddx.bench import Bench
from chatddx.catalog import Entry, EntryField, Subject
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Expectation
from chatddx.repl.commands import complete
from chatddx.repl.shell import Repl
from chatddx.repl.test.helpers import Say, cells, line_of, pattern, tagged
from chatddx.store import Catalog, People, Store
from chatddx.test.world import LINES, QWEN


# A new version of the expectation the person reads for a case, from their own thread.
def retarget(bench: Bench, case: str, data: JsonValue) -> None:
    catalog, store = Catalog(bench.conn), Store(bench.conn)
    digest = bench.family(case).case
    [thread] = [
        t
        for t in catalog.expectations_of(digest)
        if catalog.about(Subject(thread=t)).owner == bench.person.id
    ]
    held = resolve(store.get, catalog.head(thread).digest, Expectation)
    registry = store.load([held.digest])
    changed = registry.add(
        Expectation(
            case=held.case, expectation_schema=held.expectation_schema, data=data
        )
    )
    _ = store.add(registry, [changed])
    _ = catalog.edit(thread, changed, bench.person.id)


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_score_scores_the_runs_a_changed_expectation_leaves_and_sums_them_up(
    bench: Bench, say: Say
):
    _ = say(f"cell {LINES} {QWEN}", "run noted", "run noted 8")
    assert "nothing to score" in say("score")

    retarget(bench, "noted", {"diagnosis": {"pattern": "fake & diagnosis"}})
    written = say("score")

    assert written.count(f": {LINES} × {QWEN} × noted") == 2
    assert [row[:2] for row in cells(written)].count(["differential", "1"]) == 2
    assert ["lines", "text", "2", "@0", "0"] in cells(written)
    assert ["differential", "2", "1", "0"] in cells(written)
    assert "nothing to score" in say("score")


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_score_run_says_what_came_of_one_run(bench: Bench, say: Say):
    _ = say(f"cell {LINES} {QWEN}", "run noted")
    run = str(bench.runs()[0].run)[:8]

    written = say(f"score {run}")

    assert "scored already, as the scorings are now" in written
    assert "not listed" in written
    assert "no run of yours starts with 'zzzz'" in say("score zzzz")

    retarget(bench, "noted", {"diagnosis": {"pattern": "fake & diagnosis"}})
    written = say(f"score {run}")

    assert "scored already" not in written
    assert ["differential", "1"] in [row[:2] for row in cells(written)]


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_the_runs_left_to_score_complete(repl: Repl, bench: Bench, say: Say):
    _ = say(f"cell {LINES} {QWEN}", "run noted")
    run = str(bench.runs()[0].run)[:8]
    assert repl.completions()["score:run"] == []

    retarget(bench, "noted", {"diagnosis": {"pattern": "fake & diagnosis"}})
    names = repl.completions()

    assert names["score:run"] == [run]
    assert names["replay:run"] == [run]
    assert complete(names, "score ") == [run]
    assert complete(names, "replay ") == [run]

    _ = say("score")

    assert repl.completions()["score:run"] == []


def _dropped(bench: Bench, name: str) -> tuple[str, str]:
    case = bench.family(name).case
    [schema] = bench.expectation_schemas(case)
    catalog, person = Catalog(bench.conn), bench.person.id
    [mine] = bench.expectation_choices([case], schema)[case]
    catalog.note(Subject(thread=mine), Entry(field=EntryField.DELETED), person)
    return case, schema


@pytest.mark.slow
def test_take_takes_the_expectations_shared_for_the_cases_without_one_of_yours(
    bench: Bench, say: Say
):
    _ = _dropped(bench, "noted")
    shown = say("show case noted")
    assert "none of yours; shared by archive: take" in line_of(shown, "expectation")
    targets = tagged("targets")
    others = [id for id in targets if id != "noted"]

    written = say("take targets")
    assert f"take: {len(targets)} cases tagged targets, under targets" in written
    assert "1: noted" in line_of(written, "taken")
    assert f"{len(others)}: {' '.join(others)}" in line_of(written, "yours already")
    assert pattern("noted") in line_of(
        say("show case noted"), "expectation.diagnosis.pattern"
    )

    written = say("take targets")
    assert "none" in line_of(written, "taken")
    assert f"{len(targets)}: {' '.join(targets)}" in line_of(written, "yours already")


@pytest.mark.slow
def test_take_names_the_cases_shared_by_several_owners(bench: Bench, say: Say):
    case, schema = _dropped(bench, "noted")
    store, catalog = Store(bench.conn), Catalog(bench.conn)
    bob = People(bench.conn).add("bob", "Bob")
    registry = store.load([schema, case])
    theirs = registry.add(
        Expectation(case=case, expectation_schema=schema, data={"diagnosis": "x"})
    )
    _ = store.add(registry, [theirs])
    shared = catalog.create(theirs, bob.id).thread
    to_alice = Entry(field=EntryField.COLLABORATOR, person=bench.person.id)
    catalog.note(Subject(thread=shared), to_alice, bob.id)

    written = say("take targets")
    assert "none" in line_of(written, "taken")
    assert "noted (archive bob): take from OWNER" in line_of(written, "to choose from")

    written = say("take from bob targets")
    assert "under targets from bob" in written
    assert "1: noted" in line_of(written, "taken")
    assert bench.expectation(case, schema) == store.get(theirs)

    written = say("take from", "take from nobody", "take no-such-tag")
    assert "usage: take [from OWNER] [TAG...]" in written
    assert "no person 'nobody'" in written
    assert "no case tagged no-such-tag for alice" in written

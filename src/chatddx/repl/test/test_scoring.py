import pytest
from pydantic import JsonValue

from chatddx.catalog import Subject
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Expectation
from chatddx.repl.bench import Bench
from chatddx.repl.commands import complete
from chatddx.repl.shell import Repl
from chatddx.repl.test.sample import FREE_TEXT, QWEN, Say
from chatddx.store import Catalog, Store


def lines(written: str) -> list[list[str]]:
    return [line.split() for line in written.splitlines()]


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
def test_score_scores_the_runs_a_changed_expectation_leaves_and_sums_them_up(
    bench: Bench, say: Say
):
    _ = say(f"cell {FREE_TEXT} {QWEN}", "run Dutchfall11w", "run Dutchfall11w 8")
    assert "nothing to score" in say("score")

    retarget(bench, "Dutchfall11w", {"diagnosis": {"pattern": "fake & diagnosis"}})
    written = say("score")

    assert written.count(f": {FREE_TEXT} × {QWEN} × Dutchfall11w") == 2
    assert [row[:2] for row in lines(written)].count(["differential", "1"]) == 2
    assert ["free-text", "text", "2", "0", "0"] in lines(written)
    assert ["differential", "2", "1", "0"] in lines(written)
    assert "nothing to score" in say("score")


@pytest.mark.usefixtures("fake")
def test_score_run_says_what_came_of_one_run(bench: Bench, say: Say):
    _ = say(f"cell {FREE_TEXT} {QWEN}", "run Dutchfall11w")
    run = str(bench.reads.runs()[0].run)[:8]

    written = say(f"score {run}")

    assert "scored already, as the scorings are now" in written
    assert "not listed" in written
    assert "no run of yours starts with 'zzzz'" in say("score zzzz")

    retarget(bench, "Dutchfall11w", {"diagnosis": {"pattern": "fake & diagnosis"}})
    written = say(f"score {run}")

    assert "scored already" not in written
    assert ["differential", "1"] in [row[:2] for row in lines(written)]


@pytest.mark.usefixtures("fake")
def test_the_runs_left_to_score_complete(repl: Repl, bench: Bench, say: Say):
    _ = say(f"cell {FREE_TEXT} {QWEN}", "run Dutchfall11w")
    run = str(bench.reads.runs()[0].run)[:8]
    assert repl.completions()["score:run"] == []

    retarget(bench, "Dutchfall11w", {"diagnosis": {"pattern": "fake & diagnosis"}})
    names = repl.completions()

    assert names["score:run"] == [run]
    assert names["replay:run"] == [run]
    assert complete(names, "score ") == [run]
    assert complete(names, "replay ") == [run]

    _ = say("score")

    assert repl.completions()["score:run"] == []

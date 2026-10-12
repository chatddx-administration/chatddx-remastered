from uuid import UUID

import pytest

from chatddx.catalog import Subject
from chatddx.curation import Plan, load_cases
from chatddx.factors.base import resolve
from chatddx.factors.cases import Case
from chatddx.factors.scoring import Expectation, Scorer, Scoring
from chatddx.factors.trial import Execution, Trial
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.runner.run import Runner
from chatddx.runner.score import NO_EXPECTATION, score_run
from chatddx.runner.test.conftest import DELAY
from chatddx.runner.test.test_run import rows, trial
from chatddx.store import Catalog, Store
from chatddx.store.store import Connection
from chatddx.test.world import DATA, LINES, NATIVE, QWEN, TOOL_ANSWER, faked

pytestmark = pytest.mark.wip


def expectations(plan: Plan, made: Trial) -> tuple[str, ...]:
    schema = plan.named("expectation_schema", "targets").digest
    targets = load_cases(DATA)
    found: list[str] = []
    for ref in made.cases:
        case = resolve(plan.registry.get, ref, Case)
        data = targets[case.vignette.id].targets
        found.append(
            plan.registry.add(
                Expectation(case=ref, expectation_schema=schema, data=data)
            )
        )
    return tuple(found)


def ran(
    conn: Connection,
    inventory: Inventory,
    alice: Person,
    made: Trial,
    plan: Plan,
    execution: Execution | None = None,
) -> UUID:
    running = Runner(conn, inventory, alice).start(made, plan.registry, QWEN, execution)
    running.send()
    _ = running.finish()
    return running.run


def scorer(plan: Plan, name: str) -> Scorer:
    return resolve(plan.registry.get, plan.named("scorer", name).digest, Scorer)


@pytest.mark.usefixtures("fake")
@pytest.mark.parametrize(
    ("recipe", "scored_by"),
    [(LINES, "lines"), (NATIVE, "answer"), (TOOL_ANSWER, "list")],
)
def test_a_run_is_scored_through_every_view_of_its_scorer(
    conn: Connection,
    inventory: Inventory,
    alice: Person,
    plan: Plan,
    recipe: str,
    scored_by: str,
) -> None:
    made = trial(plan, recipe)
    run = ran(conn, inventory, alice, made, plan)
    scoring = Scoring(
        scorer=plan.named("scorer", scored_by).digest,
        expectations=expectations(plan, made),
    )
    score, findings = score_run(conn, run, scoring, plan.registry, alice)
    assert findings == []

    stored = Store(conn).score(score.started.score)
    assert stored == score
    assert stored.finished is not None and stored.finished.findings == ()
    views = len(scorer(plan, scored_by).views)
    assert len(stored.items) == len(Store(conn).run(run).items) * views == 4 * views
    details = [i.detail for i in stored.items]
    assert all(isinstance(d, dict) and d.get("reason") != "no answer" for d in details)
    about = Catalog(conn).about(Subject(score=score.started.score))
    assert about.owner == alice.id


@pytest.mark.usefixtures("fake")
def test_cases_without_an_expectation_get_no_value_and_are_noted(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    made = trial(plan, LINES)
    run = ran(conn, inventory, alice, made, plan)
    first, _ = expectations(plan, made)
    scoring = Scoring(
        scorer=plan.named("scorer", "lines").digest, expectations=(first,)
    )
    score, findings = score_run(conn, run, scoring, plan.registry, alice)
    assert [(f.code, f.message) for f in findings] == [
        (
            "score.no_expectation",
            "1 of the run's cases have no expectation in the scoring",
        )
    ]
    covered = resolve(plan.registry.get, first, Expectation).case
    uncovered = [i for i in score.items if i.key.case != covered]
    assert uncovered and all(
        (i.value, i.detail) == (None, NO_EXPECTATION) for i in uncovered
    )


@pytest.mark.slow
def test_an_answer_that_can_t_be_read_is_noted_and_scored_without_one(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    made = trial(plan, NATIVE, seeds=(7,))
    with faked(inventory, plan.registry.get, delay=DELAY * 10):
        run = ran(conn, inventory, alice, made, plan, Execution(timeout_s=0.2))
    scoring = Scoring(
        scorer=plan.named("scorer", "answer").digest,
        expectations=expectations(plan, made),
    )
    score, findings = score_run(conn, run, scoring, plan.registry, alice)
    assert findings == []
    assert score.finished is not None
    noted = score.finished.findings
    assert {f.code for f in noted} == {"answer.unread"}
    assert len(noted) == len(made.cases)
    assert all(
        f.message.endswith("the call ended with: stopped: no end after 0.2 s")
        for f in noted
    )
    assert all(
        isinstance(i.detail, dict) and i.detail.get("reason") == "no answer"
        for i in score.items
        if i.view == 0
    )


@pytest.mark.usefixtures("fake")
def test_scoring_is_refused_before_anything_is_written(
    conn: Connection, db: str, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    made = trial(plan, LINES)
    found = expectations(plan, made)
    running = Runner(conn, inventory, alice).start(made, plan.registry, QWEN)
    running.send()

    def refused(by: Scorer, error: type[Exception], match: str) -> None:
        scoring = Scoring(scorer=plan.registry.add(by), expectations=found)
        with pytest.raises(error, match=match):
            _ = score_run(conn, running.run, scoring, plan.registry, alice)

    free_text = scorer(plan, "lines")
    refused(free_text, ValueError, "hasn't finished")
    _ = running.finish()
    judged = free_text.model_copy(
        update={
            "views": tuple(
                v.model_copy(update={"judge": "sha256:" + "1" * 64})
                for v in free_text.views
            )
        }
    )
    refused(judged, NotImplementedError, "need a judge")
    refused(
        free_text.model_copy(update={"version": 2}),
        LookupError,
        "metrics:score is at version 1 in chatddx .*, not 2",
    )
    assert rows(db, "score_stage") == 0

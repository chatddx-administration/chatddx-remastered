from typing import Any, cast
from uuid import UUID

import pytest

from chatddx.catalog import Subject, read
from chatddx.curation import Plan, load_cases
from chatddx.factors.base import Finding, resolve
from chatddx.factors.cases import Case
from chatddx.factors.engine import model_of
from chatddx.factors.request import Skeleton
from chatddx.factors.scoring import (
    Expectation,
    Judge,
    JudgeEngine,
    Scorer,
    Scoring,
    View,
)
from chatddx.factors.trial import Execution, Trial
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.ledger import Endpoint, JudgeEndpoint, Score, check_score
from chatddx.runner.events import (
    ItemScored,
    JudgeAnswered,
    JudgeAsked,
    Noted,
    ScoreEvent,
    Streamed,
)
from chatddx.runner.gate import Refused
from chatddx.runner.run import Runner
from chatddx.runner.score import NO_EXPECTATION
from chatddx.runner.send import STOPPED, Halt, send
from chatddx.runner.test.helpers import DELAY, rows, trial
from chatddx.scorers import metrics
from chatddx.store import Rows, Store
from chatddx.store.store import Connection
from chatddx.test.world import DATA, LINES, NATIVE, QWEN, REMOTE, TOOL_ANSWER, faked


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


def score_run(
    conn: Connection,
    inventory: Inventory,
    alice: Person,
    run: UUID,
    scoring: Scoring,
    plan: Plan,
) -> tuple[Score, list[Finding]]:
    grading = Runner(conn, inventory, alice).score(run, scoring, plan.registry)
    grading.send()
    return grading.finish()


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
    score, findings = score_run(conn, inventory, alice, run, scoring, plan)
    assert findings == []

    stored = Store(conn).score(score.started.score)
    assert stored == score
    assert stored.finished is not None and stored.finished.findings == ()
    views = len(scorer(plan, scored_by).views)
    assert len(stored.items) == len(Store(conn).run(run).items) * views == 4 * views
    details = [i.detail for i in stored.items]
    assert all(isinstance(d, dict) and d.get("reason") != "no answer" for d in details)
    about = read.about(Rows(conn), Subject(score=score.started.score))
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
    score, findings = score_run(conn, inventory, alice, run, scoring, plan)
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
        run = ran(conn, inventory, alice, made, plan, Execution(timeout_s=0.1))
    scoring = Scoring(
        scorer=plan.named("scorer", "answer").digest,
        expectations=expectations(plan, made),
    )
    score, findings = score_run(conn, inventory, alice, run, scoring, plan)
    assert findings == []
    assert score.finished is not None
    noted = score.finished.findings
    assert {f.code for f in noted} == {"answer.unread"}
    assert len(noted) == len(made.cases)
    assert all(
        f.message.endswith("the call ended with: stopped: no end after 0.1 s")
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
            _ = Runner(conn, inventory, alice).score(
                running.run, scoring, plan.registry
            )

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
    refused(
        judged, LookupError, "view 0 names a judge, which first_mention doesn't read"
    )
    refused(
        free_text.model_copy(update={"version": metrics.score.version + 1}),
        LookupError,
        f"metrics:score is at version {metrics.score.version} in chatddx .*, "
        + f"not {metrics.score.version + 1}",
    )
    assert rows(db, "score_stage") == 0


NOTE = "$.notes[?@.author == 'carol'].comment"


def judged(plan: Plan, *views: View) -> Scorer:
    found = scorer(plan, "judged")
    return found.model_copy(update={"views": views}) if views else found


# Compromise: By weights, so that a judge a test copies finds its original's engine.
def scoring_of(plan: Plan, made: Trial, by: Scorer) -> Scoring:
    get = plan.registry.get
    serving = {model_of(e, get).digest: e for e in plan.engines.values()}
    engines = tuple(
        JudgeEngine(judge=j, engine=serving[resolve(get, j, Judge).model])
        for j in by.judges
    )
    return Scoring(
        scorer=plan.registry.add(by),
        expectations=expectations(plan, made),
        engines=engines,
    )


@pytest.mark.usefixtures("fake")
def test_a_judged_view_is_scored_from_its_judge_s_calls(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    made = trial(plan, LINES, cases=("noted", "crlf"), seeds=(7,))
    run = ran(conn, inventory, alice, made, plan)
    scoring = scoring_of(plan, made, judged(plan))
    grading = Runner(conn, inventory, alice).score(run, scoring, plan.registry)
    heard: list[ScoreEvent] = []
    grading.send(heard.append)
    score, findings = grading.finish()
    assert findings == []

    url = str(inventory.endpoint(QWEN).url)
    assert score.started.endpoints == tuple(
        JudgeEndpoint(
            judge=plan.named("judge", j).digest, endpoint=Endpoint(name=QWEN, url=url)
        )
        for j in ("verdict", "graded")
    )
    noted, crlf = (resolve(plan.registry.get, c, Case).digest for c in made.cases)
    by = {(i.key.case, i.view): i for i in score.items}
    assert [
        (by[(noted, v)].value, len(by[(noted, v)].judge_calls)) for v in (1, 2, 3)
    ] == [
        (1.0, 1),
        (1.0, 1),
        (0.5, 3),
    ]
    assert by[(noted, 3)].detail == {"seeds": [0.0, 0.5, 1.0]}
    assert [
        (by[(crlf, v)].value, by[(crlf, v)].detail, by[(crlf, v)].judge_calls)
        for v in (1, 2, 3)
    ] == [(None, {"reason": "no target"}, ())] * 3
    assert [e.item for e in heard if isinstance(e, ItemScored)] == list(score.items)
    asked = [e for e in heard if isinstance(e, JudgeAsked)]
    assert [(e.key.case, e.view, e.seed_index) for e in asked] == [
        (noted, 1, 0),
        (noted, 2, 0),
        (noted, 3, 0),
        (noted, 3, 1),
        (noted, 3, 2),
    ]
    assert {e.scorer for e in asked} == {scoring.scorer}
    answered = [e for e in heard if isinstance(e, JudgeAnswered)]
    assert [e.call for e in answered] == [
        c for v in (1, 2, 3) for c in by[(noted, v)].judge_calls
    ]
    assert [e.verdict for e in answered][2:] == [
        {"points": p, "why": "fake why"} for p in (0, 1, 2)
    ]
    assert any(isinstance(e, Streamed) for e in heard)
    stored = Store(conn).score(grading.score)
    assert (
        stored.items == score.items
        and stored.started.endpoints == score.started.endpoints
    )


@pytest.mark.usefixtures("fake")
def test_a_judge_call_that_names_another_model_is_noted(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    made = trial(plan, LINES, cases=("noted",), seeds=(7,))
    run = ran(conn, inventory, alice, made, plan)
    scoring = scoring_of(plan, made, judged(plan))
    score, _ = score_run(conn, inventory, alice, run, scoring, plan)
    [item] = [i for i in score.items if i.view == 1]
    [judged_call] = item.judge_calls
    response = cast(dict[str, Any], judged_call.call.response) | {"model": "other"}
    other = judged_call.model_copy(
        update={"call": judged_call.call.model_copy(update={"response": response})}
    )
    edited = Score(
        started=score.started,
        finished=score.finished,
        items=tuple(
            i.model_copy(update={"judge_calls": (other,)}) if i == item else i
            for i in score.items
        ),
    )
    store = Store(conn)
    loaded = store.load([store.run(run).started.trial, scoring.digest])
    assert [
        (f.code, f.message.split(", declared")[0])
        for f in check_score(edited, store.run(run), loaded)
        if f.code == "attestation.model"
    ] == [("attestation.model", "judge engine returned model 'other'")]


@pytest.mark.usefixtures("fake")
def test_a_judge_is_refused_before_anything_is_written(
    conn: Connection, db: str, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    made = trial(plan, LINES, cases=("noted",), seeds=(7,))
    run = ran(conn, inventory, alice, made, plan)
    remote = plan.named("judge", "remote").digest
    view = View(
        expectation=NOTE, metric="verdict", judge=remote, params={"at": "/meets"}
    )
    by_remote = scoring_of(plan, made, judged(plan, view))

    def refused(
        at: Inventory, error: type[Exception], match: str, scoring: Scoring = by_remote
    ) -> None:
        with pytest.raises(error, match=match):
            _ = Runner(conn, at, alice).score(run, scoring, plan.registry)

    unserved = inventory.model_copy(
        update={
            "endpoints": {n: e for n, e in inventory.endpoints.items() if n != REMOTE}
        }
    )
    refused(unserved, Refused, "no endpoint serves engine")
    refused(inventory, Refused, f"endpoint {REMOTE!r} isn't cleared for source test")
    cleared = inventory.model_copy(
        update={"cleared": inventory.cleared | {REMOTE: ("test",)}}
    )
    refused(cleared, Refused, r"needs the secret in \$CHATDDX_TEST_REMOTE")

    judge = resolve(plan.registry.get, plan.named("judge", "verdict").digest, Judge)
    skeleton = resolve(plan.registry.get, judge.skeleton, Skeleton)
    messages = [
        {"role": "user", "content": [{"slot": "vignette"}, {"slot": "completion"}]}
    ]
    reading = plan.registry.add(
        Skeleton.model_validate(skeleton.model_dump() | {"messages": messages})
    )
    reader = plan.registry.add(judge.model_copy(update={"skeleton": reading}))
    view = View(
        expectation=NOTE, metric="verdict", judge=reader, params={"at": "/meets"}
    )
    refused(
        inventory,
        Refused,
        "reads the vignette, which no judge is given",
        scoring_of(plan, made, judged(plan, view)),
    )
    assert rows(db, "score_stage") == 0


@pytest.mark.usefixtures("fake")
def test_a_halt_during_a_judge_s_calls_keeps_the_seeds_it_has(
    conn: Connection,
    inventory: Inventory,
    alice: Person,
    plan: Plan,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    made = trial(plan, LINES, cases=("noted",), seeds=(7,))
    run = ran(conn, inventory, alice, made, plan)
    graded = plan.named("judge", "graded").digest
    view = View(
        expectation=NOTE,
        metric="points",
        judge=graded,
        params={"at": "/points", "max": 2},
    )
    scoring = scoring_of(plan, made, judged(plan, view))
    grading = Runner(conn, inventory, alice).score(run, scoring, plan.registry)
    sent: list[int] = []
    halt = Halt()

    def halting(*args: Any, **kwargs: Any) -> Any:
        sent.append(len(sent))
        if len(sent) == 2:
            halt.set()
        return send(*args, **kwargs)

    monkeypatch.setattr("chatddx.runner.score.send", halting)
    heard: list[ScoreEvent] = []
    grading.send(heard.append, halt)
    score, findings = grading.finish()
    [item] = score.items
    assert [c.call.error for c in item.judge_calls] == [None, STOPPED]
    assert item.value == 0.0
    assert ("judge.incomplete", "view 0's value rests on 2 of 3 judge seeds") in [
        (f.code, f.message) for f in findings
    ]
    assert [n.finding.code for n in heard if isinstance(n, Noted)] == ["verdict.unread"]

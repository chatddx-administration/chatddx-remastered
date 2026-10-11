from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import JsonValue

from chatddx.catalog import Entry, EntryField, Subject
from chatddx.core.rig import rig
from chatddx.factors.base import Finding, resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.request import Skeleton
from chatddx.factors.scoring import Expectation, Scorer, Scoring
from chatddx.factors.trial import Trial
from chatddx.identity import Person
from chatddx.ledger import RunItem, Score, ScoreItem, ScoreStarted, check_score
from chatddx.scorers.answer import read
from chatddx.scorers.scorer import Scored, ScoreFunction, score
from chatddx.scorers.shipped import function
from chatddx.store import Catalog, Store
from chatddx.store.store import Connection

NO_EXPECTATION: JsonValue = {"reason": "no expectation"}


def _now() -> datetime:
    return datetime.now(UTC)


# Scores a finished run under a scoring: each item's answer, read from its last call,
# through every view of the scoring's scorer. `registry` holds the scoring's components;
# the run's come from the store.
def score_run(
    conn: Connection, run: UUID, scoring: Scoring, registry: Registry, by: Person
) -> tuple[Score, list[Finding]]:
    # Each row must land as it's written, so a score that dies leaves a log to read.
    if not conn.autocommit:
        raise ValueError("the scoring pass needs a connection in autocommit mode")
    store = Store(conn)
    ran = store.run(run)
    if ran.finished is None:
        raise ValueError(f"run {run} hasn't finished")
    _ = registry.add(scoring)
    scorer = resolve(registry.get, scoring.scorer, Scorer)
    if judged := [i for i, v in enumerate(scorer.views) if v.judge is not None]:
        raise NotImplementedError(f"views {judged} need a judge, which can't run yet")
    views = function(scorer)
    _ = store.add(registry, [scoring.digest])
    loaded = store.load([ran.started.trial, scoring.digest])
    trial = resolve(loaded.get, ran.started.trial, Trial)
    skeleton = resolve(loaded.get, trial.skeleton, Skeleton)
    expected: dict[str, JsonValue] = {}
    for ref in scoring.expectations:
        expectation = resolve(loaded.get, ref, Expectation)
        expected[expectation.case] = expectation.data

    started = ScoreStarted(
        score=uuid4(),
        run=run,
        at=_now(),
        rig=rig(),
        scorer_version=views.version,
        scoring=scoring.digest,
    )
    store.append(started)
    Catalog(conn).note(
        Subject(score=started.score),
        Entry(field=EntryField.OWNER, person=by.id),
        by.id,
    )
    items: list[ScoreItem] = []
    findings: list[Finding] = []
    for item in sorted(ran.items, key=lambda i: (i.key.case, i.key.replicate)):
        rows, noted = _scored(started.score, item, skeleton, scorer, views, expected)
        store.append(*rows)
        items.extend(rows)
        findings.extend(noted)
    log = Score(stages=(started,), items=tuple(items))
    finished = log.finish(_now(), findings)
    store.append(finished)
    score_log = Score(stages=(started, finished), items=log.items)
    return score_log, check_score(score_log, ran, loaded)


def _scored(
    score_id: UUID,
    item: RunItem,
    skeleton: Skeleton,
    scorer: Scorer,
    views: ScoreFunction,
    expected: dict[str, JsonValue],
) -> tuple[list[ScoreItem], list[Finding]]:
    last = item.calls[-1]
    answer = read(skeleton, last.response)
    findings: list[Finding] = []
    if answer.problem is not None:
        message = answer.problem
        if answer.value is None and last.error is not None:
            message += f"; the call ended with: {last.error}"
        findings.append(
            Finding(
                code="answer.unread" if answer.value is None else "answer.invalid",
                message=message,
                subject=str(item.key),
            )
        )
    if item.key.case in expected:
        results = score(scorer, views, answer.value, expected[item.key.case])
    else:
        results = [Scored(None, NO_EXPECTATION)] * len(scorer.views)
    rows = [
        ScoreItem(score=score_id, key=item.key, view=n, value=s.value, detail=s.detail)
        for n, s in enumerate(results)
    ]
    return rows, findings

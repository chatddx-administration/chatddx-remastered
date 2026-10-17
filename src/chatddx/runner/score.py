from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import JsonValue

from chatddx.catalog import Entry, EntryField, Subject
from chatddx.factors.base import Component, Finding, Resolver, resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.engine import served_model_name
from chatddx.factors.request import Skeleton, Slot
from chatddx.factors.scoring import Expectation, Judge, Scorer, Scoring
from chatddx.factors.trial import Execution, Trial
from chatddx.identity import Person
from chatddx.inventory import Inventory, url_at
from chatddx.ledger import (
    Endpoint,
    ItemKey,
    JudgeCall,
    JudgeEndpoint,
    Run,
    RunItem,
    Score,
    ScoreItem,
    ScoreStarted,
    check_score,
)
from chatddx.rig import rig
from chatddx.scorers.answer import read
from chatddx.scorers.scorer import Metrics, Scored, Verdicts, score_view
from chatddx.scorers.shipped import function
from chatddx.scorers.verdicts import asked
from chatddx.store import Catalog, Store
from chatddx.store.store import Connection

from . import gate, send as sending
from .run import Noted, Streamed

NO_EXPECTATION: JsonValue = {"reason": "no expectation"}


@dataclass(frozen=True)
class ItemScored:
    item: ScoreItem


@dataclass(frozen=True)
class JudgeAsked:
    key: ItemKey
    scorer: str
    view: int
    judge: str
    seed_index: int


@dataclass(frozen=True)
class JudgeAnswered:
    key: ItemKey
    view: int
    call: JudgeCall
    verdict: JsonValue | None


type Event = ItemScored | JudgeAsked | Streamed | JudgeAnswered | Noted


@dataclass(frozen=True)
class _Judging:
    judge: Judge
    skeleton: Skeleton
    model: str
    url: str
    secret: str | None


def _now() -> datetime:
    return datetime.now(UTC)


def _ignore(_: Event) -> None:
    pass


def judge_at(
    inventory: Inventory | None,
    get: Resolver,
    ref: str,
    cases: Iterable[str],
    named: str | None = None,
) -> tuple[Judge, Skeleton, str]:
    judge = resolve(get, ref, Judge)
    skeleton = resolve(get, judge.skeleton, Skeleton)
    if read_case := sorted(_slots(skeleton) & {"vignette", "appendices"}):
        raise ValueError(
            f"judge {ref} reads the {' and '.join(read_case)}, which no judge is given"
        )
    if inventory is None:
        raise ValueError("judged views need the World's inventory")
    try:
        name = named or inventory.serving(judge.engine)
    except LookupError as e:
        raise gate.Refused(str(e)) from None
    gate.bar(inventory, get, name, judge.engine, cases, False, "judge")
    return judge, skeleton, name


class Grader:
    def __init__(
        self, conn: Connection, inventory: Inventory | None, by: Person
    ) -> None:
        if not conn.autocommit:
            raise ValueError("the scoring pass needs a connection in autocommit mode")
        self._conn: Connection = conn
        self._inventory: Inventory | None = inventory
        self._by: Person = by

    def start(
        self,
        run: UUID,
        scoring: Scoring,
        registry: Registry,
        endpoints: Mapping[str, str] | None = None,
        execution: Execution | None = None,
    ) -> "Grading":
        execution = execution or Execution()
        store = Store(self._conn)
        ran = store.run(run)
        if ran.finished is None:
            raise ValueError(f"run {run} hasn't finished")
        if execution.concurrency > 1:
            raise ValueError("judge calls are sent one at a time yet")
        _ = registry.add(scoring)
        scorer = resolve(registry.get, scoring.scorer, Scorer)
        views = function(scorer)
        held = store.load([ran.started.trial])

        def get(digest: str) -> Component:
            return held.get(digest) if digest in held else registry.get(digest)

        trial = resolve(get, ran.started.trial, Trial)
        judging: dict[str, _Judging] = {}
        at: list[JudgeEndpoint] = []
        for ref in scorer.judges:
            named = (endpoints or {}).get(ref)
            judge, skeleton, name = judge_at(
                self._inventory, get, ref, trial.cases, named
            )
            assert self._inventory is not None
            secret = gate.admit(
                self._inventory, get, name, judge.engine, trial.cases, False, "judge"
            )
            url = url_at(self._inventory, get, name)
            judging[ref] = _Judging(
                judge, skeleton, served_model_name(judge.engine, get), url, secret
            )
            at.append(JudgeEndpoint(judge=ref, endpoint=Endpoint(name=name, url=url)))

        _ = store.add(registry, [scoring.digest])
        loaded = store.load([ran.started.trial, scoring.digest])
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
            execution=execution,
            endpoints=tuple(at),
        )
        store.append(started)
        Catalog(self._conn).note(
            Subject(score=started.score),
            Entry(field=EntryField.OWNER, person=self._by.id),
            self._by.id,
        )
        return Grading(
            store, ran, started, scorer, views, loaded, expected, judging, trial
        )


def _slots(skeleton: Skeleton) -> set[str]:
    return {s.slot for m in skeleton.messages for s in m.content if isinstance(s, Slot)}


class Grading:
    def __init__(
        self,
        store: Store,
        ran: Run,
        started: ScoreStarted,
        scorer: Scorer,
        views: Metrics,
        loaded: Registry,
        expected: dict[str, JsonValue],
        judging: dict[str, _Judging],
        trial: Trial,
    ) -> None:
        self._store: Store = store
        self._ran: Run = ran
        self._started: ScoreStarted = started
        self._scorer: Scorer = scorer
        self._views: Metrics = views
        self._loaded: Registry = loaded
        self._expected: dict[str, JsonValue] = expected
        self._judging: dict[str, _Judging] = judging
        self._trial: Trial = trial
        self._skeleton: Skeleton = resolve(loaded.get, trial.skeleton, Skeleton)
        self._scorer_ref: str = resolve(loaded.get, started.scoring, Scoring).scorer
        self._items: list[ScoreItem] = []
        self._findings: list[Finding] = []
        self._stopping: bool = False
        self._halt: sending.Halt = sending.Halt()
        self._finished: bool = False

    @property
    def score(self) -> UUID:
        return self._started.score

    @property
    def started(self) -> ScoreStarted:
        return self._started

    def halt(self) -> None:
        self._stopping = True
        self._halt.set()

    def send(self, on_event: Callable[[Event], None] | None = None) -> None:
        emit: Callable[[Event], None] = on_event or _ignore
        self._halt = sending.Halt()
        if self._stopping:
            self._halt.set()
        scored = {i.key for i in self._items}
        items = {i.key: i for i in self._ran.items}
        trial = self._trial
        schedule = self._started.execution.schedule(trial.cases, len(trial.seeds))
        for case, replicate in schedule:
            key = ItemKey(case=case, replicate=replicate)
            if self._stopping or self._finished:
                return
            if key not in items or key in scored:
                continue
            if self._grade(items[key], emit):
                self._stopping = True
                if self._halt.is_set():
                    return
                raise KeyboardInterrupt

    def finish(self) -> tuple[Score, list[Finding]]:
        if self._finished:
            raise ValueError(f"score {self.score} is finished")
        log = Score(stages=(self._started,), items=tuple(self._items))
        finished = log.finish(_now(), self._findings)
        self._store.append(finished)
        self._finished = True
        score = Score(stages=(self._started, finished), items=log.items)
        return score, check_score(score, self._ran, self._loaded)

    def _note(self, finding: Finding, emit: Callable[[Event], None]) -> None:
        self._findings.append(finding)
        emit(Noted(finding))

    def _grade(self, item: RunItem, emit: Callable[[Event], None]) -> bool:
        last = item.calls[-1]
        answer = read(self._skeleton, last.response)
        if answer.salvaged:
            message = "cut short, and read with its structure closed"
            if last.error is not None:
                message += f"; the call ended with: {last.error}"
            self._note(
                Finding(
                    level="info",
                    code="answer.salvaged",
                    message=message,
                    subject=str(item.key),
                ),
                emit,
            )
        if answer.problem is not None:
            message = answer.problem
            if answer.value is None and last.error is not None:
                message += f"; the call ended with: {last.error}"
            code = "answer.unread" if answer.value is None else "answer.invalid"
            self._note(Finding(code=code, message=message, subject=str(item.key)), emit)
        views = self._scorer.views
        stopped = False
        calls: dict[int, list[JudgeCall]] = {}
        results: dict[int, Scored] = {}
        if (data := self._expected.get(item.key.case)) is None:
            results = {i: Scored(None, NO_EXPECTATION) for i in range(len(views))}
        else:
            for i, view in enumerate(views):
                if view.judge is None:
                    results[i] = score_view(
                        self._scorer, self._views, i, answer.value, data
                    )
                    continue
                if stopped:
                    continue
                verdicts, calls[i], stopped = self._judged(
                    item.key, i, answer.value, data, emit
                )
                results[i] = (
                    verdicts
                    if isinstance(verdicts, Scored)
                    else score_view(
                        self._scorer, self._views, i, answer.value, data, verdicts
                    )
                )
        rows = [
            ScoreItem(
                score=self.score,
                key=item.key,
                view=i,
                value=results[i].value,
                detail=results[i].detail,
                judge_calls=tuple(calls.get(i, ())),
            )
            for i in sorted(results)
        ]
        self._store.append(*rows)
        self._items.extend(rows)
        for row in rows:
            emit(ItemScored(row))
        return stopped

    def _judged(
        self,
        key: ItemKey,
        index: int,
        answer: JsonValue | None,
        data: JsonValue,
        emit: Callable[[Event], None],
    ) -> tuple[Verdicts | Scored, list[JudgeCall], bool]:
        view = self._scorer.views[index]
        assert view.judge is not None
        judging = self._judging[view.judge]
        fills = asked(judging.judge, judging.skeleton, view, answer, data)
        if isinstance(fills, Scored):
            return fills, [], False
        verdicts: Verdicts = []
        calls: list[JudgeCall] = []
        for n, seed in enumerate(judging.judge.seeds):
            body = judging.skeleton.render(model=judging.model, seed=seed, fills=fills)
            emit(JudgeAsked(key, self._scorer_ref, index, view.judge, n))
            stopped = False
            try:
                call = sending.send(
                    judging.url,
                    body,
                    execution=self._started.execution,
                    secret=judging.secret,
                    on_delta=lambda delta: emit(Streamed(key, delta)),
                    halt=self._halt,
                )
            except sending.Stopped as e:
                call, stopped = e.call, True
            judged = JudgeCall(judge=view.judge, seed_index=n, call=call)
            calls.append(judged)
            verdict = read(judging.skeleton, call.response)
            emit(JudgeAnswered(key, index, judged, verdict.value))
            if verdict.problem is not None:
                message = f"view {index}, seed {n}: {verdict.problem}"
                if verdict.value is None and call.error is not None:
                    message += f"; the call ended with: {call.error}"
                code = "verdict.unread" if verdict.value is None else "verdict.invalid"
                self._note(Finding(code=code, message=message, subject=str(key)), emit)
            verdicts.append(verdict.value)
            if stopped:
                return verdicts, calls, True
        return verdicts, calls, False


def score_run(
    conn: Connection,
    run: UUID,
    scoring: Scoring,
    registry: Registry,
    by: Person,
    inventory: Inventory | None = None,
) -> tuple[Score, list[Finding]]:
    grading = Grader(conn, inventory, by).start(run, scoring, registry)
    grading.send()
    return grading.finish()

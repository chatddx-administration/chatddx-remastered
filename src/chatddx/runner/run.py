import queue
import threading
from collections.abc import Callable, Iterator
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import JsonValue

from chatddx.catalog import Entry, EntryField, Subject
from chatddx.core.rig import rig
from chatddx.factors.base import Finding, Fingerprint, StructuralError, resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Case, prepare_case
from chatddx.factors.engine import LocalEngine, RemoteEngine
from chatddx.factors.request import Skeleton, render
from chatddx.factors.trial import CanarySet, Execution, Trial
from chatddx.identity import Person
from chatddx.inventory import Inventory, url_of
from chatddx.ledger import (
    Call,
    CanaryCall,
    Endpoint,
    ItemKey,
    Run,
    RunItem,
    RunStarted,
    ToolRun,
    check_run,
)
from chatddx.ledger.run import PHASES, Phase
from chatddx.store import Catalog, Store
from chatddx.store.store import Connection

from . import gate, rounds, send as sending
from .rounds import Exchange, Toolbox
from .send import Delta


@dataclass(frozen=True)
class ItemStarted:
    key: ItemKey
    seed: int


@dataclass(frozen=True)
class Streamed:
    key: ItemKey
    delta: Delta


@dataclass(frozen=True)
class ToolRan:
    key: ItemKey
    run: ToolRun


@dataclass(frozen=True)
class ItemEnded:
    item: RunItem


@dataclass(frozen=True)
class CanaryEnded:
    call: CanaryCall


@dataclass(frozen=True)
class Noted:
    finding: Finding


type Event = ItemStarted | Streamed | ToolRan | ItemEnded | CanaryEnded | Noted


@dataclass(frozen=True)
class _Prepared:
    key: ItemKey
    vignette: Fingerprint
    body: dict[str, JsonValue]


def _now() -> datetime:
    return datetime.now(UTC)


def _ignore(_: Event) -> None:
    pass


def _streamed(
    key: ItemKey, emit: Callable[[Streamed], None]
) -> Callable[[Delta], None]:
    return lambda delta: emit(Streamed(key, delta))


def _ran(key: ItemKey, emit: Callable[[ToolRan], None]) -> Callable[[ToolRun], None]:
    return lambda run: emit(ToolRan(key, run))


class Runner:
    def __init__(self, conn: Connection, inventory: Inventory, by: Person) -> None:
        # Each row must land as it's written, so a run that dies leaves a log to read.
        if not conn.autocommit:
            raise ValueError("the runner needs a connection in autocommit mode")
        self._conn: Connection = conn
        self._inventory: Inventory = inventory
        self._by: Person = by

    def start(
        self,
        trial: Trial,
        registry: Registry,
        endpoint: str,
        execution: Execution | None = None,
        canaries: CanarySet | None = None,
        verify_at: tuple[Phase, ...] = PHASES,
    ) -> "Running":
        execution = execution or Execution()
        _ = registry.add(trial)
        canary_set = None if canaries is None else registry.add(canaries)
        gate.check(self._inventory, registry.get, endpoint, trial)
        toolbox = rounds.load(
            resolve(registry.get, trial.skeleton, Skeleton), registry.get
        )
        jobs = self._inventory.endpoint(endpoint).max_jobs
        if execution.concurrency > jobs:
            raise ValueError(
                f"endpoint {endpoint!r} takes {jobs} requests at once, the execution "
                + f"sends {execution.concurrency}"
            )
        secret = gate.secret(self._inventory, endpoint)
        url = url_of(self._inventory, registry.get, endpoint)
        started = RunStarted(
            run=uuid4(),
            at=_now(),
            rig=rig(),
            trial=trial.digest,
            execution=execution,
            canaries=canary_set,
            verify_at=verify_at,
            tool_code=() if toolbox is None else toolbox.code,
            endpoint=Endpoint(name=endpoint, url=url),
        )
        store = Store(self._conn)
        roots = [trial.digest] if canary_set is None else [trial.digest, canary_set]
        _ = store.add(registry, roots)
        store.append(started)
        Catalog(self._conn).note(
            Subject(run=started.run),
            Entry(field=EntryField.OWNER, person=self._by.id),
            self._by.id,
        )
        return Running(
            self._conn, self._inventory, registry, started, url, secret, toolbox
        )


class Running:
    def __init__(
        self,
        conn: Connection,
        inventory: Inventory,
        registry: Registry,
        started: RunStarted,
        url: str,
        secret: str | None,
        toolbox: Toolbox | None,
    ) -> None:
        self._store: Store = Store(conn)
        self._inventory: Inventory = inventory
        self._registry: Registry = registry
        self._started: RunStarted = started
        self._url: str = url
        self._secret: str | None = secret
        self._toolbox: Toolbox | None = toolbox
        self._items: list[RunItem] = []
        self._canaries: list[CanaryCall] = []
        self._findings: list[Finding] = []
        self._stopping: bool = False
        self._finished: bool = False

    @property
    def run(self) -> UUID:
        return self._started.run

    @property
    def started(self) -> RunStarted:
        return self._started

    # Ends `send` after the calls under way, without the end canaries.
    def stop(self) -> None:
        self._stopping = True

    # The start canaries go one at a time before the items, and the end canaries after
    # them, so they bracket the items whatever the concurrency.
    # A KeyboardInterrupt during a call records the call as stopped and is raised
    # again; one raised in `on_event` while a call streams counts as during the call.
    # Above concurrency 1, it hangs up every call in flight and records them as stopped;
    # another one while they hang up leaves them out of the log.
    def send(self, on_event: Callable[[Event], None] | None = None) -> None:
        emit: Callable[[Event], None] = on_event or _ignore
        self._probe("start", emit)
        items = self._prepared(emit)
        if self._started.execution.concurrency == 1:
            self._send_serially(items, emit)
        else:
            self._send_concurrently(items, emit)
        self._probe("end", emit)

    def _engine(self) -> LocalEngine | RemoteEngine:
        get = self._registry.get
        engine = get(resolve(get, self._started.trial, Trial).engine)
        assert isinstance(engine, LocalEngine | RemoteEngine)
        return engine

    def _probe(self, phase: Phase, emit: Callable[[Event], None]) -> None:
        started = self._started
        if started.canaries is None or phase not in started.verify_at:
            return
        canaries = resolve(self._registry.get, started.canaries, CanarySet).canaries
        model = self._engine().served_model_name
        sent = {(c.phase, c.canary) for c in self._canaries}
        for index, canary in enumerate(canaries):
            if self._stopping or self._finished:
                return
            if (phase, index) in sent:
                continue
            try:
                call = sending.send(
                    self._url,
                    canary.render(model=model),
                    execution=started.execution,
                    secret=self._secret,
                )
            except sending.Stopped as stopped:
                self._stopping = True
                self._probed(phase, index, stopped.call, emit)
                raise KeyboardInterrupt from None
            self._probed(phase, index, call, emit)

    def _probed(
        self, phase: Phase, index: int, call: Call, emit: Callable[[Event], None]
    ) -> None:
        record = CanaryCall(run=self.run, phase=phase, canary=index, call=call)
        self._store.append(record)
        self._canaries.append(record)
        emit(CanaryEnded(record))

    def _prepared(self, emit: Callable[[Event], None]) -> Iterator[_Prepared]:
        get = self._registry.get
        trial = resolve(get, self._started.trial, Trial)
        skeleton = resolve(get, trial.skeleton, Skeleton)
        engine = self._engine()
        execution = self._started.execution
        sent = {i.key for i in self._items}
        for case_ref, replicate in execution.schedule(trial.cases, len(trial.seeds)):
            key = ItemKey(case=case_ref, replicate=replicate)
            if self._stopping or self._finished:
                return
            if key in sent:
                continue
            seed = trial.seeds[replicate]
            emit(ItemStarted(key, seed))
            case = resolve(get, case_ref, Case)
            try:
                source = self._inventory.source(case.vignette.source)
                raw = source.fetch(case.vignette.id)
                prepared = prepare_case(
                    case, raw, get, skeleton.appendix_layout, trial.cleanup
                )
            except (LookupError, StructuralError) as e:
                self._note(
                    Finding(code="case.unreadable", message=str(e), subject=str(key)),
                    emit,
                )
                continue
            for finding in prepared.findings:
                self._note(finding, emit)
            body = render(
                skeleton,
                model=engine.served_model_name,
                seed=seed,
                fills=prepared.fills,
            )
            yield _Prepared(key, prepared.fingerprint, body)

    def _send_serially(
        self, items: Iterator[_Prepared], emit: Callable[[Event], None]
    ) -> None:
        for item in items:
            exchange = rounds.converse(
                self._url,
                item.body,
                self._toolbox,
                execution=self._started.execution,
                secret=self._secret,
                on_delta=_streamed(item.key, emit),
                on_tool=_ran(item.key, emit),
            )
            self._append(item.key, item.vignette, exchange, emit)
            if exchange.stopped:
                self._stopping = True
                raise KeyboardInterrupt

    # Calls go out on worker threads, and everything else stays on the caller's: the
    # events, the writes, and the stamp of when each item was sent, which keeps the
    # items in schedule order for `check_execution`.
    def _send_concurrently(
        self, items: Iterator[_Prepared], emit: Callable[[Event], None]
    ) -> None:
        execution = self._started.execution
        results: queue.SimpleQueue[Streamed | ToolRan | Future[Exchange]] = (
            queue.SimpleQueue()
        )
        halt = threading.Event()
        in_flight: dict[Future[Exchange], _Prepared] = {}
        pool = ThreadPoolExecutor(execution.concurrency, "chatddx-runner")

        def work(item: _Prepared, started_at: datetime) -> Exchange:
            return rounds.converse(
                self._url,
                item.body,
                self._toolbox,
                execution=execution,
                secret=self._secret,
                on_delta=_streamed(item.key, results.put),
                on_tool=_ran(item.key, results.put),
                halt=halt,
                started_at=started_at,
            )

        try:
            more = True
            while True:
                while more and len(in_flight) < execution.concurrency:
                    item = next(items, None)
                    if item is None:
                        more = False
                        break
                    future = pool.submit(work, item, _now())
                    in_flight[future] = item
                    future.add_done_callback(results.put)
                if not in_flight:
                    return
                done = results.get()
                if isinstance(done, Streamed | ToolRan):
                    emit(done)
                    continue
                item = in_flight.pop(done)
                self._append(item.key, item.vignette, done.result(), emit)
        except KeyboardInterrupt:
            halt.set()
            self._stopping = True
            while in_flight:
                done = results.get()
                if isinstance(done, Streamed | ToolRan):
                    continue
                item = in_flight.pop(done, None)
                if item is not None and done.exception() is None:
                    self._append(item.key, item.vignette, done.result(), emit)
            raise
        finally:
            halt.set()
            pool.shutdown(wait=False)

    def finish(self) -> list[Finding]:
        if self._finished:
            raise ValueError(f"run {self.run} is finished")
        run = Run(
            stages=(self._started,),
            items=tuple(self._items),
            canaries=tuple(self._canaries),
        )
        finished = run.finish(_now(), self._findings)
        self._store.append(finished)
        self._finished = True
        return check_run(
            Run(
                stages=(self._started, finished),
                items=run.items,
                canaries=run.canaries,
            ),
            self._registry,
        )

    def _note(self, finding: Finding, emit: Callable[[Event], None]) -> None:
        self._findings.append(finding)
        emit(Noted(finding))

    def _append(
        self,
        key: ItemKey,
        vignette: Fingerprint,
        exchange: Exchange,
        emit: Callable[[Event], None],
    ) -> None:
        item = RunItem(
            run=self.run,
            key=key,
            vignette=vignette,
            call=exchange.call,
            turns=exchange.turns,
        )
        self._store.append(item)
        self._items.append(item)
        emit(ItemEnded(item))

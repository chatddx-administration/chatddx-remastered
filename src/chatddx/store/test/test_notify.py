from collections.abc import Iterator
from uuid import uuid4

import psycopg
import pytest
from pydantic import JsonValue

from chatddx import settings
from chatddx.factors.base import resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Case
from chatddx.factors.test.sample import NOW, RIG, world
from chatddx.identity import Person
from chatddx.ledger import (
    CanaryCall,
    ItemKey,
    Run,
    RunItem,
    RunStarted,
    Score,
    ScoreItem,
    ScoreStarted,
)
from chatddx.store import People, Queue, Store
from chatddx.store.notify import (
    LIMIT,
    WORKERS,
    Assembler,
    Events,
    JobChanged,
    Rows,
    channel,
    listen,
    tell,
)
from chatddx.store.store import Connection

from .test_store import call


@pytest.fixture
def autocommit() -> bool:
    return True


@pytest.fixture
def listener(db: str) -> Iterator[Connection]:
    with psycopg.connect(settings.database(), dbname=db, autocommit=True) as c:
        yield c


def heard(conn: Connection) -> list[tuple[str, str]]:
    return [(n.channel, n.payload) for n in conn.notifies(timeout=0.2)]


@pytest.mark.slow
def test_a_run_s_rows_its_scores_included_are_read_in_the_order_written(
    conn: Connection, listener: Connection
) -> None:
    store, reg = Store(conn), Registry()
    ids = world(reg)
    _ = store.add(reg, [ids["trial"], ids["scoring"]])
    run, other, score = uuid4(), uuid4(), uuid4()
    listen(listener, channel(run))
    started = RunStarted(run=run, at=NOW, rig=RIG, trial=ids["trial"])
    vignette = resolve(reg.get, ids["case"], Case).vignette.fingerprint
    items = [
        RunItem(
            run=run,
            key=ItemKey(case=ids["case"], replicate=r),
            vignette=vignette,
            call=call("m"),
        )
        for r in (1, 0)
    ]
    canary = CanaryCall(run=run, phase="start", canary=0, call=call("m"))
    finished = Run(started=started, items=tuple(items), canaries=(canary,)).finish(NOW)
    score_started = ScoreStarted(
        score=score,
        run=run,
        at=NOW,
        rig=RIG,
        scorer_version=1,
        scoring=ids["scoring"],
    )
    scored = ScoreItem(score=score, key=items[0].key, view=0, value=1.0)
    score_finished = Score(started=score_started, items=(scored,)).finish(NOW)
    written = [
        started,
        items[0],
        canary,
        items[1],
        finished,
        score_started,
        scored,
        score_finished,
    ]
    store.append(RunStarted(run=other, at=NOW, rig=RIG, trial=ids["trial"]))
    for record in written:
        store.append(record)

    rows = store.rows_of(run)
    assert [r for _, r in rows] == written
    seqs = [s for s, _ in rows]
    assert seqs == sorted(seqs)
    assert [r for _, r in store.rows_of(run, seqs[4])] == written[5:]
    assert heard(listener) == [(channel(run), "rows")] * len(written)


@pytest.mark.slow
def test_the_queue_wakes_workers_and_tells_a_run_s_followers_how_its_job_stands(
    conn: Connection, listener: Connection
) -> None:
    store, reg = Store(conn), Registry()
    trial = world(reg)["trial"]
    _ = store.add(reg, [trial])
    run = uuid4()
    store.append(RunStarted(run=run, at=NOW, rig=RIG, trial=trial))
    alice: Person = People(conn).add("alice", "Alice")
    queue, worker = Queue(conn), uuid4()
    queue.enlist(worker)
    listen(listener, WORKERS, channel(run))

    job = queue.put(alice.id, run, "e", 1, False)
    assert heard(listener) == [(WORKERS, ""), (channel(run), "job queued")]
    claimed = queue.claim(worker, {"e": 1}, settings.WORKER_LOST)
    assert claimed is not None and claimed.id == job.id
    assert heard(listener) == []
    assert queue.requeue(job.id, worker, "paused")
    assert heard(listener) == [(WORKERS, ""), (channel(run), "job queued")]
    _ = queue.claim(worker, {"e": 1}, settings.WORKER_LOST)
    _ = queue.halt(run)
    queue.pause(alice.id, False)
    assert heard(listener) == [(WORKERS, "")] * 2
    assert queue.end(job.id, worker, "stopped")
    assert heard(listener) == [(WORKERS, ""), (channel(run), "job stopped")]


def test_events_are_packed_within_notify_s_limit_and_assembled_again(
    conn: Connection, listener: Connection
) -> None:
    small: list[tuple[str, JsonValue]] = [
        ("item.delta", {"text": "a" * 100, "at": i}) for i in range(150)
    ]
    big: list[tuple[str, JsonValue]] = [("judge.answered", {"text": "å" * 2000})]
    run = uuid4()
    listen(listener, channel(run))
    tell(conn, run, [*small, *big, *small[:2]])
    packed = [n.payload for n in listener.notifies(timeout=5, stop_after=6)]
    assert all(len(p.encode()) <= LIMIT for p in packed)
    assert [p[0] for p in packed] == ["[", "[", "[", "~", "~", "["]

    assembler = Assembler()
    told = [assembler.message("run.x", 7, p) for p in packed]
    assert told[3] is None
    said = [e for m in told if isinstance(m, Events) for e in m.said]
    assert said == [*small, *big, *small[:2]]
    assert assembler.message("run.x", 7, packed[4]) is None
    assert assembler.message("run.x", 7, "rows") == Rows()
    assert assembler.message("run.x", 7, "job under way") == JobChanged("under way")

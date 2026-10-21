import logging
import threading
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from datetime import timedelta
from typing import Any
from uuid import UUID

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from chatddx import settings
from chatddx.bench import Bench
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.store import Job, Queue, Store
from chatddx.store.notify import Assembler, Events, JobChanged, Rows, channel, listen
from chatddx.store.store import Connection
from chatddx.test.helpers import (
    alices_bench,
    autocommitted,
    curated_template,
    found_alice,
)
from chatddx.test.world import LINES, QWEN, faked
from chatddx.worker import Worker
from chatddx.worker.worker import LEFT

__all__ = ["alices_bench", "autocommitted", "curated_template", "found_alice"]

BEAT = timedelta(milliseconds=50)
LOST = timedelta(seconds=1)


@pytest.fixture
def conninfo(db: str) -> str:
    return make_conninfo(settings.database(), dbname=db)


# As the request starts a run, at an endpoint that answers, before it is queued.
def start(bench: Bench) -> UUID:
    variation = bench.variation(LINES)
    cases = [bench.family(name).case for name in ("crlf", "bom")]
    return bench.start(variation, QWEN, cases, (7,)).first.run


@contextmanager
def serving(
    conninfo: str,
    world: Inventory,
    beat: timedelta = BEAT,
    deadline: timedelta = settings.WORKER_DEADLINE,
    jobs: int = settings.WORKER_JOBS,
) -> Generator[Worker]:
    worker = Worker(conninfo, world, beat, LOST, deadline, jobs)
    stopping = threading.Event()
    thread = threading.Thread(target=worker.serve, args=(stopping,))
    thread.start()
    try:
        yield worker
    finally:
        stopping.set()
        worker.wake()
        thread.join(30)
        assert not thread.is_alive()


def latest(queue: Queue, job: Job) -> Job:
    return queue.placed([job.run])[job.run].job


def until(queue: Queue, job: Job, done: Callable[[Job], bool]) -> Job:
    deadline = time.monotonic() + 30
    while not done(found := latest(queue, job)):
        assert time.monotonic() < deadline, f"job {job.id} is still {found.status}"
        time.sleep(0.02)
    return found


def ended(job: Job) -> bool:
    return job.ended is not None


def test_a_worker_says_what_the_inventory_check_finds_as_it_starts(
    conninfo: str, world: Inventory, caplog: pytest.LogCaptureFixture
) -> None:
    unknown = "sha256:" + "0" * 64
    stray = world.endpoint(QWEN).model_copy(update={"engine": unknown})
    strayed = world.model_copy(update={"endpoints": world.endpoints | {"stray": stray}})
    with caplog.at_level(logging.INFO, "chatddx.worker"):
        with serving(conninfo, world):
            pass
        with serving(conninfo, strayed):
            pass

    assert [(r.levelno, r.getMessage()) for r in caplog.records] == [
        (
            logging.WARNING,
            f"[world warning] stray: endpoint.engine_unknown: {unknown} is not in "
            + "the store",
        )
    ]


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_queued_run_is_sent_finished_and_scored_and_scored_again_when_asked(
    conn: Connection,
    conninfo: str,
    world: Inventory,
    bench: Bench,
    alice: Person,
) -> None:
    queue, started = Queue(conn), start(bench)
    job = queue.put(alice.id, started, QWEN, 1, True)
    lines = next(e.digest for e, a in bench.threads("scorer") if a.name == "lines")
    with serving(conninfo, world) as worker:
        sent = until(queue, job, ended)
        again = queue.put(alice.id, started, QWEN, 0, True, [lines])
        scored = until(queue, again, ended)

    assert (sent.status, sent.why, sent.worker) == ("finished", None, worker.id)
    assert scored.status == "finished"
    run = Store(conn).run(started)
    assert len(run.items) == 2
    assert run.finished is not None and run.finished.findings == ()
    every = bench.scores_of(bench.run(started), every=True)
    assert {g.name for g in bench.scores_of(bench.run(started))} >= {"lines"}
    assert [g.name for g in every].count("lines") == 2


@pytest.mark.slow
def test_a_worker_wakes_to_a_queued_job_and_says_what_its_rows_don_t(
    conn: Connection, conninfo: str, world: Inventory, bench: Bench, alice: Person
) -> None:
    queue = Queue(conn)
    with (
        faked(world, Store(conn).get, delay=0.02),
        psycopg.connect(conninfo, autocommit=True) as listener,
    ):
        started = start(bench)
        name = channel(started)
        listen(listener, name)
        with serving(conninfo, world, beat=timedelta(minutes=5)):
            job = queue.put(alice.id, started, QWEN, 1, True)
            assert until(queue, job, ended).status == "finished"
        assembler = Assembler()
        heard = [
            m
            for n in listener.notifies(timeout=0.5)
            if (m := assembler.message(n.channel, n.pid, n.payload)) is not None
        ]

    said = [name for m in heard if isinstance(m, Events) for name, _ in m.said]
    assert said[0] == "item.started"
    assert {"item.delta", "run.scoring", "run.scored"} <= set(said)
    assert set(said) <= {
        "item.started",
        "item.delta",
        "item.tool",
        "run.scoring",
        "judge.asked",
        "judge.delta",
        "judge.answered",
        "run.scored",
    }
    assert heard[0] == JobChanged("queued") and heard[-1] == JobChanged("finished")
    assert Rows() in heard


def test_a_halt_stops_the_run_and_leaves_it_unscored(
    conn: Connection, conninfo: str, world: Inventory, bench: Bench, alice: Person
) -> None:
    queue = Queue(conn)
    with faked(world, Store(conn).get, delay=0.05):
        started = start(bench)
        job = queue.put(alice.id, started, QWEN, 1, True)
        with serving(conninfo, world):
            _ = until(queue, job, lambda j: j.status == "under way")
            _ = queue.halt(started)
            halted = until(queue, job, ended)

    assert halted.status == "stopped"
    run = Store(conn).run(started)
    assert run.finished is not None and len(run.items) < 2
    assert bench.scores_of(bench.run(started)) == []


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_run_halted_while_queued_is_finished_unsent_and_unscored(
    conn: Connection, conninfo: str, world: Inventory, bench: Bench, alice: Person
) -> None:
    queue, started = Queue(conn), start(bench)
    job = queue.put(alice.id, started, QWEN, 1, True)
    _ = queue.halt(started)
    with serving(conninfo, world):
        halted = until(queue, job, ended)

    assert halted.status == "stopped"
    run = Store(conn).run(started)
    assert run.finished is not None and run.items == ()
    assert bench.scores_of(bench.run(started)) == []


@pytest.mark.slow
def test_a_paused_owner_s_run_goes_back_to_the_queue_and_resumes_once_unpaused(
    conn: Connection, conninfo: str, world: Inventory, bench: Bench, alice: Person
) -> None:
    queue = Queue(conn)
    with faked(world, Store(conn).get, delay=0.02):
        started = start(bench)
        job = queue.put(alice.id, started, QWEN, 1, False)
        with serving(conninfo, world):
            _ = until(queue, job, lambda j: j.status == "under way")
            queue.pause(alice.id)
            held = until(queue, job, lambda j: j.status == "queued")
            assert held.why == "paused"
            assert Store(conn).run(started).finished is None
            queue.pause(alice.id, False)
            done = until(queue, job, ended)

    assert done.status == "finished"
    run = Store(conn).run(started)
    assert len(run.items) == 2 and run.finished is not None


@pytest.mark.slow
def test_a_stopped_worker_queues_its_run_again_for_the_next_to_resume(
    conn: Connection, conninfo: str, world: Inventory, bench: Bench, alice: Person
) -> None:
    queue = Queue(conn)
    with faked(world, Store(conn).get, delay=0.02):
        started = start(bench)
        job = queue.put(alice.id, started, QWEN, 1, False)
        with serving(conninfo, world):
            _ = until(queue, job, lambda j: j.status == "under way")
        left = latest(queue, job)
        assert (left.status, left.why) == ("queued", "its worker stopped")
        with serving(conninfo, world) as second:
            done = until(queue, job, ended)

    assert (done.status, done.worker) == ("finished", second.id)
    assert len(Store(conn).run(started).items) == 2


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_job_whose_worker_is_lost_is_claimed_and_its_run_resumed(
    conn: Connection,
    admin: Connection,
    conninfo: str,
    world: Inventory,
    bench: Bench,
    alice: Person,
) -> None:
    queue, started = Queue(conn), start(bench)
    job = queue.put(alice.id, started, QWEN, 1, False)
    ghost = Worker(conninfo, world).id
    queue.enlist(ghost)
    assert queue.claim(ghost, {QWEN: 4}, LOST) is not None
    with admin.transaction():
        _ = admin.execute(
            "UPDATE worker.job SET beat = now() - interval '1 minute' WHERE id = %s",
            (job.id,),
        )
    with serving(conninfo, world) as worker:
        done = until(queue, job, ended)

    assert (done.status, done.worker) == ("finished", worker.id)
    assert len(Store(conn).run(started).items) == 2


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_job_that_can_t_connect_is_lost_and_claimed_again(
    conn: Connection,
    conninfo: str,
    world: Inventory,
    bench: Bench,
    alice: Person,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    queue, started = Queue(conn), start(bench)
    job = queue.put(alice.id, started, QWEN, 1, False)
    connect, refused = psycopg.connect, threading.Event()

    def once_refused(*args: Any, **kwargs: Any) -> Connection:
        on_a_job = threading.current_thread().name.startswith("chatddx-job-")
        if on_a_job and not refused.is_set():
            refused.set()
            raise psycopg.OperationalError("too many connections for role")
        return connect(*args, **kwargs)

    monkeypatch.setattr(psycopg, "connect", once_refused)
    with serving(conninfo, world) as worker:
        done = until(queue, job, ended)

    assert refused.is_set()
    assert (done.status, done.worker) == ("finished", worker.id)
    assert len(Store(conn).run(started).items) == 2


@pytest.mark.slow
def test_a_scoring_by_some_scorers_tells_the_latest_score_of_each_as_it_is_over(
    conn: Connection, conninfo: str, world: Inventory, bench: Bench, alice: Person
) -> None:
    queue, variation = Queue(conn), bench.variation(LINES)
    lines = next(e.digest for e, a in bench.threads("scorer") if a.name == "lines")
    with faked(world, Store(conn).get):
        running = bench.start(variation, QWEN, [bench.family("crlf").case], (7,)).first
        running.send()
        _ = running.finish()
        _ = bench.score(bench.run(running.run))
    every = [g.name for g in bench.scores_of(bench.run(running.run))]
    with psycopg.connect(conninfo, autocommit=True) as listener:
        listen(listener, channel(running.run))
        with serving(conninfo, world):
            job = queue.put(alice.id, running.run, QWEN, 0, True, [lines])
            _ = until(queue, job, ended)
        assembler = Assembler()
        heard = [
            m
            for n in listener.notifies(timeout=0.5)
            if (m := assembler.message(n.channel, n.pid, n.payload)) is not None
        ]

    [told] = [
        data
        for m in heard
        if isinstance(m, Events)
        for name, data in m.said
        if name == "run.scored"
    ]
    assert isinstance(told, dict) and isinstance(told["scores"], list)
    assert len(every) > 1
    assert [s["name"] for s in told["scores"] if isinstance(s, dict)] == every


@pytest.mark.slow
def test_a_worker_takes_a_job_only_while_it_holds_fewer_than_it_may(
    conn: Connection, conninfo: str, world: Inventory, bench: Bench, alice: Person
) -> None:
    queue, variation = Queue(conn), bench.variation(LINES)
    lines = next(e.digest for e, a in bench.threads("scorer") if a.name == "lines")
    finished: list[UUID] = []
    with faked(world, Store(conn).get):
        for _ in range(2):
            running = bench.start(
                variation, QWEN, [bench.family("crlf").case], (7,)
            ).first
            running.send()
            _ = running.finish()
            finished.append(running.run)
    jobs = [queue.put(alice.id, run, QWEN, 0, True, [lines]) for run in finished]
    with serving(conninfo, world, jobs=1):
        first, second = (until(queue, job, ended) for job in jobs)

    assert (first.status, second.status) == ("finished", "finished")
    assert first.ended is not None and second.claimed is not None
    assert second.claimed >= first.ended


@pytest.mark.usefixtures("fake")
@pytest.mark.slow
def test_a_run_the_gate_now_refuses_fails_with_why(
    conn: Connection, conninfo: str, world: Inventory, bench: Bench, alice: Person
) -> None:
    queue, started = Queue(conn), start(bench)
    job = queue.put(alice.id, started, QWEN, 1, True)
    with serving(conninfo, world.model_copy(update={"cleared": {}})):
        failed = until(queue, job, ended)

    assert failed.status == "failed"
    assert failed.why is not None and "isn't cleared for source test" in failed.why
    assert Store(conn).run(started).finished is None


@pytest.mark.slow
def test_a_stopping_worker_cuts_its_scoring_short_at_its_deadline_and_keeps_what_it_scored(
    conn: Connection, conninfo: str, world: Inventory, bench: Bench, alice: Person
) -> None:
    queue = Queue(conn)
    variation = bench.variation(LINES)
    with faked(world, Store(conn).get):
        running = bench.start(variation, QWEN, [bench.family("noted").case], (7,)).first
        running.send()
        _ = running.finish()
    started = running.run
    names = {e.digest: a.name or "" for e, a in bench.threads("scorer")}

    with faked(world, Store(conn).get, delay=0.05):
        job = queue.put(alice.id, started, QWEN, 0, True)
        with serving(conninfo, world, deadline=timedelta(milliseconds=100)):
            held = until(queue, job, lambda j: len(j.scored) == 2)
            deadline = time.monotonic() + 30
            while len(Store(conn).scores_of(started)) < 3:
                assert time.monotonic() < deadline, "the judged scorer didn't start"
                time.sleep(0.02)
    left = latest(queue, job)
    assert (left.status, left.why, left.scored) == ("queued", LEFT, held.scored)
    assert sorted(names[s] for s in left.scored) == ["lines", "whole"]
    with faked(world, Store(conn).get), serving(conninfo, world):
        done = until(queue, job, ended)

    assert done.status == "finished"
    assert sorted(names[s] for s in done.scored) == ["judged", "lines", "whole"]
    every = [g.name for g in bench.scores_of(bench.run(started), every=True)]
    assert sorted(every) == ["judged", "judged", "lines", "whole"]
    assert {g.name for g in bench.scores_of(bench.run(started))} == {
        "judged",
        "lines",
        "whole",
    }
    assert bench.unscored(bench.run(started)) == []

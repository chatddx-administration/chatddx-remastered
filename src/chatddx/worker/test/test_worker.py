import threading
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from datetime import timedelta
from uuid import UUID

import psycopg
import pytest
from psycopg import sql
from psycopg.conninfo import make_conninfo

from chatddx import settings
from chatddx.bench import Bench
from chatddx.conftest import chosen
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.store import Job, People, Queue, Store
from chatddx.store.notify import Assembler, Events, JobChanged, Rows, channel
from chatddx.store.store import Connection
from chatddx.test.world import LINES, QWEN, faked
from chatddx.worker import Worker
from chatddx.worker.worker import LEFT

BEAT = timedelta(milliseconds=50)
LOST = timedelta(seconds=1)


@pytest.fixture
def template(request: pytest.FixtureRequest) -> str:
    return chosen(request, "curated")


@pytest.fixture
def autocommit() -> bool:
    return True


@pytest.fixture
def alice(conn: Connection) -> Person:
    found = People(conn).find("alice")
    assert found is not None
    return found


@pytest.fixture
def bench(conn: Connection, alice: Person, world: Inventory) -> Bench:
    return Bench(conn, alice, world)


@pytest.fixture
def conninfo(db: str) -> str:
    return make_conninfo(settings.database(), dbname=db)


# As the request starts a run, at an endpoint that answers, before it is queued.
def start(bench: Bench) -> UUID:
    variation = bench.configuration(LINES)
    cases = [bench.family(name).case for name in ("crlf", "bom")]
    return bench.start(variation, QWEN, cases, (7,)).first.run


@contextmanager
def serving(
    conninfo: str,
    world: Inventory,
    beat: timedelta = BEAT,
    deadline: timedelta = settings.WORKER_DEADLINE,
) -> Generator[Worker]:
    worker = Worker(conninfo, world, beat, LOST, deadline)
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


def until(queue: Queue, job: Job, done: Callable[[Job], bool]) -> Job:
    deadline = time.monotonic() + 30
    while not done(found := queue.job(job.id)):
        assert time.monotonic() < deadline, f"job {job.id} is still {found.status}"
        time.sleep(0.02)
    return found


def ended(job: Job) -> bool:
    return job.ended is not None


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
    every = bench.scores_of(started, every=True)
    assert {g.name for g in bench.scores_of(started)} >= {"lines"}
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
        _ = listener.execute(sql.SQL("LISTEN {}").format(sql.Identifier(name)))
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


@pytest.mark.slow
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
    assert bench.scores_of(started) == []


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
    assert bench.scores_of(started) == []


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
        left = queue.job(job.id)
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
            "UPDATE worker.worker SET seen = now() - interval '1 minute' WHERE id = %s",
            (ghost,),
        )
    with serving(conninfo, world) as worker:
        done = until(queue, job, ended)

    assert (done.status, done.worker) == ("finished", worker.id)
    assert len(Store(conn).run(started).items) == 2


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
    variation = bench.configuration(LINES)
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
    left = queue.job(job.id)
    assert (left.status, left.why, left.scored) == ("queued", LEFT, held.scored)
    assert sorted(names[s] for s in left.scored) == ["lines", "whole"]
    with faked(world, Store(conn).get), serving(conninfo, world):
        done = until(queue, job, ended)

    assert done.status == "finished"
    assert sorted(names[s] for s in done.scored) == ["judged", "lines", "whole"]
    every = [g.name for g in bench.scores_of(started, every=True)]
    assert sorted(every) == ["judged", "judged", "lines", "whole"]
    assert {g.name for g in bench.scores_of(started)} == {"judged", "lines", "whole"}
    assert bench.unscored(bench.run_by_id(started)) == []

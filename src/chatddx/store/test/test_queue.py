from collections.abc import Callable
from datetime import timedelta
from typing import LiteralString
from uuid import UUID, uuid4

import pytest
from psycopg import errors

from chatddx.factors.bundle import Registry
from chatddx.factors.test.sample import NOW, RIG, world
from chatddx.identity import Person
from chatddx.ledger import RunStarted
from chatddx.store import People, Queue, Store, UnderWay
from chatddx.store.queue import STATUSES, TAKEN_OUT, Held, Standing, Stopped
from chatddx.store.store import Connection

LOST = timedelta(seconds=10)


@pytest.fixture
def autocommit() -> bool:
    return True


@pytest.fixture
def alice(conn: Connection) -> Person:
    return People(conn).add("alice", "Alice")


@pytest.fixture
def runs(conn: Connection) -> Callable[[], UUID]:
    store, registry = Store(conn), Registry()
    trial = world(registry)["trial"]
    _ = store.add(registry, [trial])

    def started() -> UUID:
        run = uuid4()
        store.append(RunStarted(run=run, at=NOW, rig=RIG, trial=trial))
        return run

    return started


def enlisted(queue: Queue) -> UUID:
    worker = uuid4()
    queue.enlist(worker)
    return worker


def test_a_run_has_one_job_open_at_a_time(
    conn: Connection, alice: Person, runs: Callable[[], UUID]
) -> None:
    queue, run = Queue(conn), runs()
    job = queue.put(alice.id, run, "e", 1, True, ["b", "a", "a"])
    assert (job.status, job.scorers, job.worker, job.halt) == (
        "queued",
        ("a", "b"),
        None,
        False,
    )
    assert queue.open(run) == job == queue.job(job.id)
    with pytest.raises(UnderWay, match=f"run {run} has something under way"):
        _ = queue.put(alice.id, run, "e", 1, False)

    worker = enlisted(queue)
    claimed = queue.claim(worker, {"e": 1}, LOST)
    assert claimed is not None
    assert (claimed.id, claimed.status, claimed.worker) == (job.id, "under way", worker)
    assert queue.end(job.id, worker, "finished")
    assert queue.open(run) is None
    assert queue.job(job.id).status == "finished"
    again = queue.put(alice.id, run, "e", 0, True)
    assert [j.id for j in queue.jobs(alice.id)] == [again.id, job.id]
    with pytest.raises(LookupError, match="no job 0"):
        _ = queue.job(0)
    with pytest.raises(ValueError, match="not queued"):
        _ = queue.end(again.id, worker, "queued")


def test_claims_go_in_turn_within_each_endpoint_s_max_jobs(
    conn: Connection, alice: Person, runs: Callable[[], UUID]
) -> None:
    queue = Queue(conn)
    worker = enlisted(queue)
    first = queue.put(alice.id, runs(), "e", 2, False)
    second = queue.put(alice.id, runs(), "e", 1, False)
    elsewhere = queue.put(alice.id, runs(), "f", 1, False)
    max_jobs = {"e": 2, "f": 1}

    claimed = [queue.claim(worker, max_jobs, LOST) for _ in range(3)]
    assert [c and c.id for c in claimed] == [first.id, elsewhere.id, None]
    assert queue.end(first.id, worker, "finished")
    taken = queue.claim(worker, max_jobs, LOST)
    assert taken is not None and taken.id == second.id
    assert queue.waiting() == 2


def test_a_paused_owner_s_jobs_wait_unless_halted_or_at_an_unknown_endpoint(
    conn: Connection, alice: Person, runs: Callable[[], UUID]
) -> None:
    queue = Queue(conn)
    worker = enlisted(queue)
    held = queue.put(alice.id, runs(), "e", 1, False)
    queue.pause(alice.id)
    assert queue.paused(alice.id)
    assert queue.claim(worker, {"e": 1}, LOST) is None

    gone = queue.put(alice.id, runs(), "renamed", 1, False)
    taken = queue.claim(worker, {"e": 1}, LOST)
    assert taken is not None and taken.id == gone.id
    assert queue.halt(held.run).halt
    taken = queue.claim(worker, {"e": 1}, LOST)
    assert taken is not None and taken.id == held.id

    queue.pause(alice.id, False)
    assert not queue.paused(alice.id)
    with pytest.raises(LookupError, match="has nothing under way"):
        _ = queue.halt(uuid4())


def test_a_worker_s_beat_keeps_its_jobs_and_a_lost_one_is_claimed_again(
    conn: Connection, admin: Connection, alice: Person, runs: Callable[[], UUID]
) -> None:
    queue = Queue(conn)
    gone, here = enlisted(queue), enlisted(queue)
    job = queue.put(alice.id, runs(), "e", 1, False)
    assert queue.claim(gone, {"e": 1}, LOST) is not None
    assert queue.claim(here, {"e": 1}, LOST) is None
    assert queue.beat(gone, [job.id]) == [Held(job=job.id, halt=False, paused=False)]

    with admin.transaction():
        _ = admin.execute(
            "UPDATE worker.worker SET seen = now() - interval '1 minute' WHERE id = %s",
            (gone,),
        )
    taken = queue.claim(here, {"e": 1}, LOST)
    assert taken is not None and (taken.id, taken.worker) == (job.id, here)
    assert queue.beat(gone, [job.id]) == []
    assert not queue.end(job.id, gone, "finished")
    assert not queue.requeue(job.id, gone)

    queue.pause(alice.id)
    assert queue.beat(here, [job.id]) == [Held(job=job.id, halt=False, paused=True)]
    assert queue.requeue(job.id, here, "paused")
    requeued = queue.job(job.id)
    assert (requeued.status, requeued.why, requeued.worker) == (
        "queued",
        "paused",
        None,
    )


def test_the_database_keeps_a_job_to_how_it_stands(
    conn: Connection, admin: Connection, alice: Person, runs: Callable[[], UUID]
) -> None:
    queue = Queue(conn)
    job = queue.put(alice.id, runs(), "e", 1, False)

    def refused(update: LiteralString) -> None:
        with admin.transaction():
            _ = admin.execute(
                f"UPDATE worker.job SET {update} WHERE id = %s", (job.id,)
            )

    with pytest.raises(errors.CheckViolation):
        refused("status = 'under way'")
    with pytest.raises(errors.CheckViolation):
        _ = queue.put(alice.id, runs(), "e", 1, False, ["a"])
    with pytest.raises(errors.RaiseException, match="may change only how it stands"):
        refused("slots = 9")
    worker = enlisted(queue)
    assert queue.claim(worker, {"e": 1}, LOST) is not None
    with pytest.raises(errors.CheckViolation):
        refused("status = 'failed', ended = now()")
    assert queue.end(job.id, worker, "failed", "it broke")
    with pytest.raises(errors.RaiseException, match="has ended"):
        refused("why = 'another reason'")

    with pytest.raises(errors.InsufficientPrivilege), conn.transaction():
        _ = conn.execute("DELETE FROM worker.job")
    row = conn.execute(
        "SELECT has_schema_privilege('chatddx_reader', 'worker', 'USAGE')"
    ).fetchone()
    assert row == (False,)


@pytest.mark.slow
def test_statuses_match_the_database_check(admin: Connection) -> None:
    found = [
        str(d)
        for (d,) in admin.execute(
            """
            SELECT pg_get_constraintdef(oid) FROM pg_constraint
            WHERE conrelid = 'worker.job'::regclass AND contype = 'c'
            """
        )
        if "ARRAY" in str(d) and "'queued'" in str(d)
    ]
    [check] = found
    assert all(f"'{s}'" in check for s in STATUSES)
    assert check.count("'") == 2 * len(STATUSES)


def test_a_queued_job_is_placed_behind_what_its_endpoint_takes_first(
    conn: Connection, alice: Person, runs: Callable[[], UUID]
) -> None:
    queue, bob = Queue(conn), People(conn).add("bob", "Bob")
    worker = enlisted(queue)
    first, waiting, mine, elsewhere = runs(), runs(), runs(), runs()
    _ = queue.put(alice.id, first, "e", 1, False)
    assert queue.claim(worker, {"e": 1, "f": 1}, LOST) is not None
    _ = queue.put(bob.id, waiting, "e", 1, False)
    _ = queue.put(alice.id, mine, "e", 1, False)
    _ = queue.put(alice.id, elsewhere, "f", 1, False)

    placed = queue.placed([first, waiting, mine, elsewhere, uuid4()])
    assert {run: p.ahead for run, p in placed.items()} == {
        first: None,
        waiting: 1,
        mine: 2,
        elsewhere: 0,
    }
    assert placed[mine].job == queue.open(mine)
    queue.pause(bob.id)
    assert queue.placed([mine])[mine].ahead == 1
    queue.pause(alice.id)
    assert queue.placed([mine])[mine].ahead is None
    assert queue.standing(alice.id, LOST) == Standing(
        paused=True, queued=2, under_way=1, workers=1
    )
    assert queue.standing(bob.id, timedelta(0)) == Standing(
        paused=True, queued=1, under_way=0, workers=0
    )


def test_a_stop_takes_the_owner_s_queue_out_and_stopping_now_halts_the_rest(
    conn: Connection, alice: Person, runs: Callable[[], UUID]
) -> None:
    queue, bob = Queue(conn), People(conn).add("bob", "Bob")
    worker = enlisted(queue)
    sending, waiting, others = runs(), runs(), runs()
    _ = queue.put(alice.id, sending, "e", 1, True)
    assert queue.claim(worker, {"e": 1}, LOST) is not None
    held = queue.put(alice.id, waiting, "e", 1, True)
    _ = queue.put(bob.id, others, "e", 1, True)

    assert queue.stop(alice.id) == Stopped(taken_out=(waiting,), halting=())
    stopped = queue.job(held.id)
    assert (stopped.status, stopped.why, stopped.worker) == ("stopped", TAKEN_OUT, None)
    assert stopped.ended is not None
    under_way = queue.open(sending)
    assert under_way is not None and not under_way.halt
    assert queue.open(others) is not None

    assert queue.stop(alice.id, now=True) == Stopped(taken_out=(), halting=(sending,))
    assert queue.stop(alice.id, now=True) == Stopped(taken_out=(), halting=())
    halting = queue.open(sending)
    assert halting is not None and halting.halt
    assert [h.halt for h in queue.beat(worker, [halting.id])] == [True]
    _ = queue.put(alice.id, waiting, "e", 1, False)


def test_a_job_keeps_the_scorers_it_has_finished_when_it_is_queued_again(
    conn: Connection, admin: Connection, alice: Person, runs: Callable[[], UUID]
) -> None:
    queue, run = Queue(conn), runs()
    job = queue.put(alice.id, run, "e", 0, True, ["a", "b"])
    worker, other = enlisted(queue), enlisted(queue)
    assert not queue.scored(job.id, worker, "a")
    assert queue.claim(worker, {"e": 1}, LOST) is not None
    assert not queue.scored(job.id, other, "a")
    assert queue.scored(job.id, worker, "a")
    assert not queue.scored(job.id, worker, "a")
    assert queue.requeue(job.id, worker, "its worker stopped")
    assert queue.job(job.id).scored == ("a",)

    def refused(update: LiteralString, on: int = job.id) -> None:
        with admin.transaction():
            _ = admin.execute(f"UPDATE worker.job SET {update} WHERE id = %s", (on,))

    with pytest.raises(errors.RaiseException, match="keeps what it has scored"):
        refused("scored = '{}'")
    with pytest.raises(errors.CheckViolation):
        refused("scored = '{a,c}'")
    unscored = queue.put(alice.id, runs(), "e", 0, False)
    with pytest.raises(errors.CheckViolation):
        refused("scored = '{a}'", unscored.id)
    assert queue.claim(other, {"e": 1}, LOST) is not None
    assert queue.scored(job.id, other, "b")
    assert queue.end(job.id, other, "finished")
    assert queue.job(job.id).scored == ("a", "b")

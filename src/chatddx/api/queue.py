from fastapi import APIRouter

from chatddx import settings
from chatddx.bench import Bench
from chatddx.store import Queue

from . import schemas
from .people import BenchDep

router = APIRouter(tags=["queue"])


def _standing(bench: Bench) -> schemas.Queue:
    held = Queue(bench.conn).standing(bench.person.id, settings.WORKER_LOST)
    return schemas.Queue(
        paused=held.paused,
        queued=held.queued,
        under_way=held.under_way,
        workers=held.workers,
    )


@router.get("/queue")
def queue(bench: BenchDep) -> schemas.Queue:
    return _standing(bench)


@router.patch(
    "/queue",
    responses={
        200: {
            "description": "Paused: the person's jobs wait, and their runs under way "
            + "stop after the items being sent and are queued again; a scoring under "
            + "way goes on. Resumed: they are taken again."
        }
    },
)
def pause(bench: BenchDep, given: schemas.Paused) -> schemas.Queue:
    Queue(bench.conn).pause(bench.person.id, given.paused)
    return _standing(bench)


@router.post(
    "/queue/stop",
    responses={
        200: {
            "description": "The person's queued jobs ended stopped, their runs left "
            + "unfinished to be resumed; with `now`, their runs under way halted too."
        }
    },
)
def stop(bench: BenchDep, given: schemas.NewStop) -> schemas.Stopped:
    stopped = Queue(bench.conn).stop(bench.person.id, given.now)
    return schemas.Stopped(
        taken_out=list(stopped.taken_out), halting=list(stopped.halting)
    )

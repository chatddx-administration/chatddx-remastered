from fastapi import APIRouter

from chatddx import settings
from chatddx.bench import Bench
from chatddx.store import Queue

from . import schemas
from .people import BenchDep

router = APIRouter(tags=["queue"])


def standing(bench: Bench) -> schemas.Queue:
    held = Queue(bench.conn).standing(bench.person.id, settings.WORKER_LOST)
    return schemas.Queue(
        paused=held.paused,
        queued=held.queued,
        under_way=held.under_way,
        workers=held.workers,
    )


@router.get("/queue")
def queue(bench: BenchDep) -> schemas.Queue:
    return standing(bench)


@router.post(
    "/queue/pause",
    responses={
        200: {
            "description": "Paused: the person's jobs wait, and their runs under way "
            + "stop after the items being sent and are queued again; a scoring under "
            + "way goes on."
        }
    },
)
def pause(bench: BenchDep) -> schemas.Queue:
    Queue(bench.conn).pause(bench.person.id)
    return standing(bench)


@router.post("/queue/resume")
def resume(bench: BenchDep) -> schemas.Queue:
    Queue(bench.conn).pause(bench.person.id, False)
    return standing(bench)


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

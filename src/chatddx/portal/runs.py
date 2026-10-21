from collections.abc import Generator
from contextlib import contextmanager, suppress
from typing import Annotated
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import JsonValue

from chatddx.api import queue as api_queue, runs as api, schemas
from chatddx.api.state import refused
from chatddx.bench import Bench, NotFound
from chatddx.catalog import threads
from chatddx.catalog.language import language_of
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.response import parts
from chatddx.factors.trial import Trial, suggest_seeds
from chatddx.store import Queue, UnderWay

from .configurations import linked
from .pages import BenchDep, page
from .refine import viewed

PLAN = "management_plan_v1"
SHOWN = 50

router = APIRouter()


@router.get("/runs")
def runs(
    request: Request,
    bench: BenchDep,
    number: Annotated[int, Query(alias="page", ge=1)] = 1,
    left: bool = False,
) -> Response:
    found = api.runs(bench, limit=SHOWN + 1, offset=(number - 1) * SHOWN, unscored=left)
    return page(
        request,
        "runs.html",
        person=bench.person,
        runs=found[:SHOWN],
        number=number,
        more=len(found) > SHOWN,
        left=left,
        queue=api_queue.queue(bench),
    )


@router.get("/runs/compare")
def comparing(
    request: Request,
    bench: BenchDep,
    run: Annotated[list[UUID] | None, Query()] = None,
    by: str | None = None,
) -> Response:
    if not run:
        raise HTTPException(422, "pick the runs to compare on the runs page")
    compared = api.compared(bench, run)
    cases = [i.case for i in compared.items] + [c.case for c in compared.apart]
    picked = viewed(compared.views, by)
    at = next(
        (i for i, v in enumerate(compared.views) if f"{v.scorer}:{v.view}" == picked),
        None,
    )
    engines: dict[str, set[str]] = {}
    for r in compared.runs:
        if r.model is not None:
            engines.setdefault(r.model, set()).add(r.engine)
    grouped = sorted(h for h, held in engines.items() if len(held) > 1)
    return page(
        request,
        "compare.html",
        person=bench.person,
        compared=compared,
        titles={case: bench.title(case) for case in cases},
        by=picked,
        at=at,
        grouped=grouped,
        kept="?" + urlencode([("run", str(r)) for r in run]),
    )


@router.get("/runs/{run}")
def run(request: Request, bench: BenchDep, run: UUID) -> Response:
    # Accommodating for a job ending once its run's rows are written: asked before the run
    # is read.
    under_way = Queue(bench.conn).open(run) is not None
    shown = api.run(bench, run)
    skeleton = resolve(bench.store.get, shown.skeleton, Skeleton)
    left = (
        [] if under_way or shown.finished_at is None else bench.unscored(bench.run(run))
    )
    titles = {case: bench.title(case) for case in shown.cases}
    together = [
        (
            r.run,
            language_of(bench.rows, resolve(bench.store.get, r.trial, Trial).skeleton),
        )
        for r in bench.runs(started_with=shown.started_with or run)
        if r.run != run
    ]
    resumable = not under_way and shown.finished_at is None and shown.endpoint
    return page(
        request,
        "run.html",
        person=bench.person,
        run=shown,
        items=api.items(bench, run),
        titles=titles,
        engine=bench.title(shown.engine),
        configuration=_configuration(bench, shown.ran, shown.skeleton),
        plan=bench.answers(skeleton) == PLAN,
        scores=[(graded, _rows(graded)) for graded in shown.scores],
        said=_said,
        under_way=under_way,
        resumable=resumable,
        left=[bench.title(s) for s in left],
        together=sorted(together, key=lambda r: str(r[1])),
        live={"run": str(run), "titles": titles},
        island="run",
    )


# Policy: a press made while something is under way for its run, from a second tab, a
# stale page or a second click, counts as made: the page it leads back to says so.
@contextmanager
def pressed() -> Generator[None]:
    with refused(), suppress(UnderWay):
        yield


@router.post("/runs/{run}/halt")
def halting(bench: BenchDep, run: UUID) -> Response:
    _ = bench.run(run)
    # Policy: as with pressed, a run with nothing left under way is halted already.
    with suppress(LookupError):
        _ = Queue(bench.conn).halt(run)
    return RedirectResponse(f"/runs/{run}", 303)


@router.post("/runs/{run}/resume")
def resuming(bench: BenchDep, run: UUID) -> Response:
    started = bench.run(run)
    if run not in bench.store.finished([run]):
        with pressed():
            _ = bench.queue(bench.resume(started))
    return RedirectResponse(f"/runs/{run}", 303)


@router.post("/queue/pause")
def pausing(bench: BenchDep) -> Response:
    Queue(bench.conn).pause(bench.person.id)
    return RedirectResponse("/runs", 303)


@router.post("/queue/resume")
def unpausing(bench: BenchDep) -> Response:
    Queue(bench.conn).pause(bench.person.id, False)
    return RedirectResponse("/runs", 303)


@router.post("/queue/stop")
def stopping(bench: BenchDep, now: Annotated[bool, Form()] = False) -> Response:
    _ = Queue(bench.conn).stop(bench.person.id, now)
    return RedirectResponse("/runs", 303)


@router.post("/runs/{run}/scores")
def scoring(bench: BenchDep, run: UUID) -> Response:
    started = bench.run(run)
    if left := bench.unscored(started):
        with pressed():
            _ = bench.queue_scoring(started, left)
    return RedirectResponse(f"/runs/{run}", 303)


@router.post("/runs/{run}/again")
def running_again(bench: BenchDep, run: UUID) -> Response:
    before = bench.run(run)
    seeds = suggest_seeds(len(resolve(bench.store.get, before.trial, Trial).seeds))
    with refused(NotFound):
        running = bench.again(before, seeds)
    _ = bench.queue(running)
    return RedirectResponse(f"/runs/{running.run}", 303)


def _configuration(
    bench: Bench, ran: schemas.Ran | None, skeleton: str
) -> tuple[str, str] | None:
    if ran is None:
        return _version(bench, skeleton)
    try:
        tried = bench.variation(ran.configuration, ran.parts, ran.head)
    except LookupError:
        return _version(bench, skeleton)
    latest = threads.head(bench.rows, ran.configuration).id
    query = schemas.Varying.model_validate({p: d or "" for p, d in ran.parts.items()})
    given = linked(query, ran.head, latest).removesuffix("?")
    link = f"/configurations/{ran.configuration}{given}"
    if ran.head == latest:
        return link, tried.label
    return link, f"{tried.label}, an earlier version"


def _version(bench: Bench, skeleton: str) -> tuple[str, str] | None:
    heads = {e.thread: (e, a) for e, a in bench.threads("configuration")}
    held = [e for e in bench.rows.edits_holding([skeleton]) if e.thread in heads]
    if not held:
        return None
    found = min(
        held,
        key=lambda e: (
            heads[e.thread][1].owner != bench.person.id,
            heads[e.thread][0].id != e.id,
            -e.id,
        ),
    )
    title = bench.title(skeleton)
    if heads[found.thread][0].id == found.id:
        return f"/configurations/{found.thread}", title
    return (
        f"/configurations/{found.thread}?head={found.id}",
        f"{title}, an earlier version",
    )


def _rows(graded: schemas.Graded) -> list[tuple[str, int, list[float | None]]]:
    found: dict[tuple[str, int], dict[int, float | None]] = {}
    for item in graded.items:
        found.setdefault((item.case, item.replicate), {})[item.view] = item.value
    views = range(len(graded.labels))
    return [
        (case, at, [held.get(v) for v in views]) for (case, at), held in found.items()
    ]


def _said(call: JsonValue) -> list[tuple[str, str]]:
    match call:
        case {"response": dict() as response}:
            pass
        case _:
            return []
    return [
        (part.kind if part.name is None else f"tool call: {part.name}", part.text)
        for part in parts(response)
    ]

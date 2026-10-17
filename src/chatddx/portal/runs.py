from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Form, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import JsonValue

from chatddx.api import queue as api_queue, runs as api, schemas, scores as api_scores
from chatddx.bench import Bench
from chatddx.catalog import threads
from chatddx.catalog.language import language_of
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.response import parts
from chatddx.factors.trial import Trial
from chatddx.store import Queue

from .configurations import linked
from .pages import BenchDep, page

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
        queue=api_queue.standing(bench),
    )


@router.get("/runs/{run}")
def run(request: Request, bench: BenchDep, run: UUID) -> Response:
    # Asked before the run is read: a job ends once its run's rows are written.
    under_way = Queue(bench.conn).open(run) is not None
    shown = api.detail(bench, run)
    skeleton = resolve(bench.get, shown.skeleton, Skeleton)
    schema = skeleton.output_schema
    left = (
        []
        if under_way or shown.finished_at is None
        else bench.unscored(bench.run_by_id(run))
    )
    titles = {case: bench.title(case) for case in shown.cases}
    together = [
        (
            r.run,
            language_of(bench.rows, resolve(bench.get, r.trial, Trial).skeleton),
        )
        for r in bench.together(shown.started_with or run)
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
        plan=isinstance(schema, dict) and schema.get("title") == PLAN,
        scores=[(graded, _rows(graded)) for graded in shown.scores],
        said=_said,
        under_way=under_way,
        resumable=resumable,
        left=[bench.scorer_name(s) for s in left],
        together=sorted(together, key=lambda r: str(r[1])),
        live={"run": str(run), "titles": titles},
        island="run",
    )


@router.post("/runs/{run}/halt")
def halting(bench: BenchDep, run: UUID) -> Response:
    _ = api.halt(bench, run)
    return RedirectResponse(f"/runs/{run}", 303)


@router.post("/runs/{run}/resume")
def resuming(request: Request, bench: BenchDep, run: UUID) -> Response:
    _ = api.resume(request, Response(), bench, run, schemas.NewResume())
    return RedirectResponse(f"/runs/{run}", 303)


@router.post("/queue/pause")
def pausing(bench: BenchDep) -> Response:
    _ = api_queue.pause(bench)
    return RedirectResponse("/runs", 303)


@router.post("/queue/resume")
def unpausing(bench: BenchDep) -> Response:
    _ = api_queue.resume(bench)
    return RedirectResponse("/runs", 303)


@router.post("/queue/stop")
def stopping(bench: BenchDep, now: Annotated[bool, Form()] = False) -> Response:
    _ = api_queue.stop(bench, schemas.NewStop(now=now))
    return RedirectResponse("/runs", 303)


@router.post("/runs/{run}/scores")
def scoring(request: Request, bench: BenchDep, run: UUID) -> Response:
    left = bench.unscored(bench.run_by_id(run))
    asked = schemas.NewScoring(scorers=left or None)
    _ = api_scores.score_now(request, Response(), bench, run, asked)
    return RedirectResponse(f"/runs/{run}", 303)


@router.post("/runs/{run}/again")
def running_again(request: Request, bench: BenchDep, run: UUID) -> Response:
    said = api.again(request, Response(), bench, run, schemas.NewAgain(score=True))
    return RedirectResponse(f"/runs/{said.run}", 303)


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

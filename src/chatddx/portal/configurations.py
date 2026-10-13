from fastapi import APIRouter, Request, Response

from chatddx.api import runs as api_runs, threads as api
from chatddx.bench import PARTS
from chatddx.factors.request import Purpose

from .pages import BenchDep, page

router = APIRouter()


@router.get("/configurations")
def configurations(
    request: Request, bench: BenchDep, purpose: Purpose = "generation"
) -> Response:
    found = api.threads(bench, "configuration", purpose=purpose)
    return page(
        request,
        "configurations.html",
        person=bench.person,
        configurations=sorted(found, key=lambda t: (t.name or t.title).lower()),
        purpose=purpose,
    )


@router.get("/configurations/{thread}")
def configuration(request: Request, bench: BenchDep, thread: int) -> Response:
    variation = bench.variation(thread)
    shown = api.detail(bench, thread)
    return page(
        request,
        "configuration.html",
        person=bench.person,
        configuration=shown,
        versions=api.edits(bench, thread),
        parts=[api.part_of(bench, variation, part) for part in PARTS],
        runs=api_runs.runs(bench, reaching=shown.head.digest, limit=20),
    )

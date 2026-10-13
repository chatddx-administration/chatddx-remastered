from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Request, Response
from pydantic import JsonValue

from chatddx.api import runs as api, schemas
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton

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
    )


@router.get("/runs/{run}")
def run(request: Request, bench: BenchDep, run: UUID) -> Response:
    shown = api.detail(bench, run)
    skeleton = resolve(bench.get, shown.skeleton, Skeleton)
    schema = skeleton.output_schema
    held = bench.holder("configuration", shown.skeleton)
    return page(
        request,
        "run.html",
        person=bench.person,
        run=shown,
        items=api.items(bench, run),
        titles={case: bench.title(case) for case in shown.cases},
        engine=bench.title(shown.engine),
        configuration=None
        if held is None
        else (held[0].thread, bench.title(shown.skeleton)),
        plan=isinstance(schema, dict) and schema.get("title") == PLAN,
        scores=[(graded, _rows(graded)) for graded in shown.scores],
        said=_said,
        island="answers",
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
        case {"response": {"choices": [{"message": dict() as message}, *_]}}:
            pass
        case _:
            return []
    parts: list[tuple[str, str]] = []
    for key in ("reasoning_content", "reasoning"):
        if isinstance(text := message.get(key), str) and text:
            parts.append(("reasoning", text))
            break
    if isinstance(text := message.get("content"), str) and text:
        parts.append(("content", text))
    match message.get("tool_calls"):
        case list() as calls:
            for called in calls:
                match called:
                    case {
                        "function": {"name": str() as name, "arguments": str() as given}
                    }:
                        parts.append((f"tool call: {name}", given))
                    case _:
                        pass
        case _:
            pass
    return parts

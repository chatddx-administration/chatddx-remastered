import json
from typing import Annotated, Any
from urllib.parse import urlencode

from fastapi import APIRouter, Query, Request, Response
from pydantic import JsonValue

from chatddx import settings
from chatddx.api import (
    families as api_families,
    runs as api_runs,
    schemas,
    threads as api,
    world as api_world,
)
from chatddx.bench import Bench
from chatddx.factors.request import OPTIONAL_PARTS, RECIPE_PARTS, Purpose

from .pages import BenchDep, page

router = APIRouter()


@router.get("/configurations")
def configurations(
    request: Request, bench: BenchDep, purpose: Purpose = "generation"
) -> Response:
    found = api.threads(bench, "configuration", purpose=purpose)
    models = api_world.models(bench)
    props: dict[str, Any] = {
        "purpose": purpose,
        "me": bench.person.login,
        "optional": list(OPTIONAL_PARTS),
        "choices": {
            p: [t.model_dump(mode="json") for t in _choices(bench, p, models)]
            for p in RECIPE_PARTS
        },
    }
    return page(
        request,
        "configurations.html",
        person=bench.person,
        configurations=sorted(found, key=lambda t: (t.name or t.title).lower()),
        purpose=purpose,
        props=props,
        island="recipe",
    )


@router.get("/configurations/{thread}")
def configuration(
    request: Request,
    bench: BenchDep,
    thread: int,
    query: Annotated[schemas.Varying, Query()],
) -> Response:
    held = bench.variation(thread, None, query.head)
    purpose = "generation" if held.recipe is None else held.recipe.purpose
    models = api_world.models(bench)
    siblings = api.threads(bench, "configuration", purpose=purpose)
    look = api.variation(bench, thread, query)
    shown = api.thread(bench, thread)
    forked = None if shown.forked_from is None else bench.rows.edit(shown.forked_from)
    mine = shown.owner == bench.person.login
    follows = api.follows(bench, thread) if mine and not shown.deleted else None
    proposal = None if follows is None else follows.origin
    moved = None if follows is None else follows.moved
    changes = [
        (v.path.removeprefix("/recipe/"), _held(bench, v.base), _held(bench, v.fork))
        for v in ([] if proposal is None else proposal.varies)
    ]
    versions = api.edits(bench, thread)
    at = next(i for i, v in enumerate(versions) if v.id == look.head.id)
    runs = api_runs.runs(bench, reaching=look.skeleton, limit=20)
    families = api_families.families(bench)
    base = {
        p: None if held.recipe is None else getattr(held.recipe, p)
        for p in RECIPE_PARTS
    }
    props: dict[str, Any] = {
        "configuration": shown.model_dump(mode="json"),
        "me": bench.person.login,
        "versions": [v.model_dump(mode="json") for v in versions],
        "base": base,
        "optional": list(OPTIONAL_PARTS),
        "look": look.model_dump(mode="json"),
        "under": query.under,
        "tags": query.tag,
        "choices": {
            p: [t.model_dump(mode="json") for t in _choices(bench, p, models)]
            for p in RECIPE_PARTS
        },
        "configurations": [t.model_dump(mode="json") for t in siblings],
        "models": [m.name for m in models],
        "everyTag": sorted({t for f in families for t in f.tags}),
        "families": [f.model_dump(mode="json") for f in families],
        "itemsPerRun": settings.ITEMS_PER_RUN,
        "runs": [r.model_dump(mode="json") for r in runs],
    }
    return page(
        request,
        "configuration.html",
        person=bench.person,
        configuration=shown,
        origin=None if forked is None else forked.thread,
        proposal=proposal,
        moved=moved,
        changes=changes,
        versions=versions,
        at=at,
        look=look,
        runs=runs,
        links=[linked(query, v.id, versions[-1].id) for v in versions],
        props=props,
        island="variation",
    )


def _held(bench: Bench, value: JsonValue) -> str:
    if isinstance(value, str) and bench.rows.kind(value) is not None:
        return bench.title(value)
    return "—" if value is None else json.dumps(value)


def linked(query: schemas.Varying, head: int, latest: int) -> str:
    given: list[tuple[str, str | int]] = [
        (part, digest or "") for part, digest in query.given().items()
    ]
    if head != latest:
        given.append(("head", head))
    if query.under is not None:
        given.append(("under", query.under))
    given += [("tag", tag) for tag in query.tag]
    return "?" + urlencode(given) if given else "?"


def _choices(
    bench: Bench, part: str, models: list[schemas.Model]
) -> list[schemas.Thread]:
    found = api.threads(bench, part)
    if part != "model":
        return found
    served = {m.weights for m in models}
    return [t for t in found if t.head.digest in served]

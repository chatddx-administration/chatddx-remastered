from typing import Annotated, Any
from urllib.parse import urlencode

from fastapi import APIRouter, Query, Request, Response

from chatddx.api import (
    families as api_families,
    runs as api_runs,
    schemas,
    threads as api,
    world as api_world,
)
from chatddx.bench import OPTIONAL, PARTS, Bench
from chatddx.catalog import made_for
from chatddx.core import settings
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
def configuration(
    request: Request,
    bench: BenchDep,
    thread: int,
    query: Annotated[schemas.Varying, Query()],
) -> Response:
    held = bench.variation(thread, None, query.head)
    purpose = "generation" if held.recipe is None else held.recipe.purpose
    endpoints = api_world.endpoints(bench)
    siblings = api.threads(bench, "configuration", purpose=purpose)
    model, variants = _variants(bench, thread, siblings, endpoints)
    endpoint = query.endpoint or next(
        (e.name for e in endpoints if e.problem is None and e.model == model), None
    )
    look = api.variation(bench, thread, query.model_copy(update={"endpoint": endpoint}))
    shown = api.detail(bench, thread)
    versions = api.edits(bench, thread)
    at = next(i for i, v in enumerate(versions) if v.id == look.head.id)
    runs = api_runs.runs(bench, reaching=look.skeleton, limit=20)
    base = {p: None if held.recipe is None else getattr(held.recipe, p) for p in PARTS}
    props: dict[str, Any] = {
        "configuration": shown.model_dump(mode="json"),
        "me": bench.person.login,
        "versions": [v.model_dump(mode="json") for v in versions],
        "base": base,
        "optional": list(OPTIONAL),
        "look": look.model_dump(mode="json"),
        "endpoint": endpoint,
        "tags": query.tag,
        "choices": {
            p: [t.model_dump(mode="json") for t in api.threads(bench, p)] for p in PARTS
        },
        "configurations": [t.model_dump(mode="json") for t in siblings],
        "endpoints": [e.model_dump(mode="json") for e in endpoints],
        "variants": {e: t.model_dump(mode="json") for e, t in variants.items()},
        "everyTag": api_families.tags(bench),
        "families": [f.model_dump(mode="json") for f in api_families.families(bench)],
        "itemsPerRun": settings.ITEMS_PER_RUN,
        "runs": [r.model_dump(mode="json") for r in runs],
    }
    return page(
        request,
        "configuration.html",
        person=bench.person,
        configuration=shown,
        versions=versions,
        at=at,
        look=look,
        runs=runs,
        links=[_linked(query, v.id, versions[-1].id) for v in versions],
        props=props,
        island="variation",
    )


def _linked(query: schemas.Varying, head: int, latest: int) -> str:
    given: list[tuple[str, str | int]] = [
        (part, digest or "") for part, digest in query.given().items()
    ]
    if head != latest:
        given.append(("head", head))
    if query.endpoint is not None:
        given.append(("endpoint", query.endpoint))
    given += [("tag", tag) for tag in query.tag]
    return "?" + urlencode(given) if given else "?"


def _variants(
    bench: Bench,
    thread: int,
    siblings: list[schemas.Thread],
    endpoints: list[schemas.Endpoint],
) -> tuple[str | None, dict[str, schemas.Thread]]:
    models = {e.model for e in endpoints if e.model is not None}
    by_id = {t.id: t for t in siblings}
    shown = by_id.get(thread)
    made = None if shown is None else made_for(shown.name or "", models)
    if made is None:
        return None, {}
    base, language, model = made
    own = sorted(siblings, key=lambda t: t.owner != bench.person.login)
    fitting: dict[str, schemas.Thread] = {}
    for t in own:
        other = made_for(t.name or "", models)
        if other is not None and other[:2] == (base, language) and other[2] != model:
            _ = fitting.setdefault(str(other[2]), t)
    return model, {
        e.name: fitting[e.model]
        for e in endpoints
        if e.model is not None and e.model in fitting
    }

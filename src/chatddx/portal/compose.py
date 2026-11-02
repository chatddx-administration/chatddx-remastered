import json
from typing import Any
from urllib.parse import urlencode

from fastapi import APIRouter, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from pydantic import JsonValue, ValidationError

from chatddx.api import (
    schemas,
    threads as api,
)
from chatddx.bench import Bench, Handle, NotFound
from chatddx.factors.base import Component
from chatddx.factors.kinds import BY_KIND
from chatddx.factors.request import (
    CHUNK_PARTS,
    INSERTS_BY_KIND,
    OPTIONAL_PARTS,
    SLOTS_BY_PURPOSE,
    Recipe,
    texts,
)

from .pages import BenchDep, configurations, page
from .shelves import display_kind

router = APIRouter()


@router.get("/compose")
def composing(request: Request, bench: BenchDep) -> Response:
    listed = configurations(bench)
    if listed:
        return RedirectResponse(f"/compose/{listed[0].id}", 303)
    return page(request, "compose.html", person=bench.person, configuration=None)


@router.get("/compose/{thread}")
def compose(
    request: Request,
    bench: BenchDep,
    thread: int,
) -> Response:
    query = _varying(request)
    shown = api.thread(bench, thread)
    if shown.kind != "skeleton":
        raise NotFound.of(
            "no configuration %(thread)s for %(login)s",
            thread=thread,
            login=bench.person.login,
        )
    varied = bench.variation(thread, None, query.head)
    recipe = varied.recipe
    judged = recipe is not None and recipe.purpose == "judge"
    models = [h for h, at in bench.handles() if at is not None]
    look = api.variation(bench, thread, query)
    versions = api.edits(bench, thread)
    at = next(i for i, v in enumerate(versions) if v.id == look.head.id)
    mine = shown.owner == bench.person.login
    proposal = api.proposal(bench, thread) if mine and not shown.deleted else None
    purpose = "judge" if judged else "generation"
    props: dict[str, Any] = {
        "configuration": shown.model_dump(mode="json"),
        "me": bench.person.login,
        "versions": [v.model_dump(mode="json") for v in versions],
        "head": look.head.id,
        "varied": bool(query.given()),
        "optional": list(OPTIONAL_PARTS),
        "modelChoices": [
            t.model_dump(mode="json") for t in _choices(bench, "model", models)
        ],
        "drafted": _drafted(
            bench, bench.variation(thread, query.given(), query.head).varied
        ),
        "configurations": [
            t.model_dump(mode="json")
            for t in api.threads(bench, "configuration", purpose=purpose)
        ],
    }
    return page(
        request,
        "compose.html",
        person=bench.person,
        configuration=shown,
        configurations=configurations(bench),
        versions=versions,
        at=at,
        links=[linked(query, v.id, versions[-1].id) for v in versions],
        proposal=proposal,
        changes=[
            (
                display_kind(v.path.removeprefix("/recipe/")),
                _held(bench, v.base),
                _held(bench, v.fork),
            )
            for v in ([] if proposal is None else proposal.varies)
        ],
        props=props,
        island="compose",
    )


def _varying(request: Request) -> schemas.Varying:
    given: dict[str, Any] = {}
    for key, value in request.query_params.multi_items():
        if key == "tag":
            given.setdefault("tag", []).append(value)
        else:
            given[key] = value
    try:
        return schemas.Varying.model_validate(given)
    except ValidationError as e:
        errors = [{**error, "loc": ("query", *error["loc"])} for error in e.errors()]
        raise RequestValidationError(errors) from None


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


def _held(bench: Bench, value: JsonValue) -> str:
    if isinstance(value, str) and bench.rows.kind(value) is not None:
        return bench.title(value)
    return "—" if value is None else json.dumps(value)


def _drafted(bench: Bench, recipe: Recipe | None) -> dict[str, Any] | None:
    if recipe is None:
        return None
    chunks = {
        p: None if (d := getattr(recipe, p)) is None else _set(bench.store.get(d))
        for p in CHUNK_PARTS
    }
    into = chunks.pop("translations")
    return {
        "model": recipe.model,
        "chunks": chunks,
        "into": {} if into is None else into["into"],
        "texts": {p: list(t) for p, t in texts(recipe, bench.store.get).items()},
        "schemas": {
            p: BY_KIND[f"chunk.{p}"].model_json_schema()
            for p in CHUNK_PARTS
            if p != "translations"
        },
        "inserts": {
            p: sorted(INSERTS_BY_KIND[f"chunk.{p}"])
            for p in CHUNK_PARTS
            if f"chunk.{p}" in INSERTS_BY_KIND
        },
        "slots": {p: sorted(s) for p, s in SLOTS_BY_PURPOSE.items()},
    }


# Accommodating for the forms, which show a field that is set: a default left out is
# filled in again where it is read, to the same digest.
def _set(chunk: Component) -> dict[str, Any]:
    held = chunk.model_dump(mode="json")
    fields = type(chunk).model_fields
    return {
        k: v
        for k, v in held.items()
        if k == "kind"
        or getattr(chunk, k) != fields[k].get_default(call_default_factory=True)
    }


def _choices(bench: Bench, part: str, models: list[Handle]) -> list[schemas.Thread]:
    found = api.threads(bench, part)
    if part != "model":
        return found
    served = {m.weights for m in models}
    return [t for t in found if t.head.digest in served]

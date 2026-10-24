import json
from dataclasses import dataclass, field
from typing import Annotated, Any, cast, get_args
from urllib.parse import urlencode

from fastapi import APIRouter, Form, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from pydantic import JsonValue, ValidationError

from chatddx import settings
from chatddx.api import (
    families as api_families,
    runs as api_runs,
    schemas,
    threads as api,
    world as api_world,
)
from chatddx.api.state import refused
from chatddx.bench import Bench, Endpoint, Handle, NotFound
from chatddx.catalog import threads
from chatddx.factors.base import Invalid, StructuralError, resolve
from chatddx.factors.request import OPTIONAL_PARTS, RECIPE_PARTS, Recipe
from chatddx.factors.trial import Order, Trial
from chatddx.locale import pgettext, tr

from .pages import BenchDep, own_first, page, refusal_of
from .scoring import unit_in

router = APIRouter()

# Accommodating for the variation's query, whose schema refuses what it doesn't know: the
# Lab's own parameters are taken out of the address before it is read.
_FARING = ("handle", "family", "by")


@dataclass
class Column:
    skeletons: tuple[str, ...]
    handle: str | None
    why: str | None = None
    names: list[schemas.Kin] = field(default_factory=list[schemas.Kin])
    run: schemas.Run | None = None
    earlier: list[schemas.Run] = field(default_factory=list[schemas.Run])


@dataclass(frozen=True)
class _Starting:
    thread: schemas.Thread
    versions: list[schemas.Edit]
    trial: Trial
    endpoint: Endpoint | None
    refused: str | None


@router.get("/lab")
def labs(request: Request, bench: BenchDep) -> Response:
    listed = own_first(bench, api.threads(bench, "configuration", purpose="generation"))
    if listed:
        return RedirectResponse(f"/lab/{listed[0].id}", 303)
    return page(request, "lab.html", person=bench.person, configuration=None)


@router.get("/lab/run")
def beginning(
    request: Request,
    bench: BenchDep,
    trial: Annotated[list[int] | None, Query()] = None,
) -> Response:
    return page(
        request,
        "starting.html",
        person=bench.person,
        trials=[_starting(bench, t) for t in dict.fromkeys(trial or ())],
        orders=get_args(Order),
    )


@router.post("/lab/run")
def starting(
    bench: BenchDep,
    version: Annotated[list[str] | None, Form()] = None,
    concurrency: Annotated[str, Form()] = "",
    order: Annotated[str, Form()] = "",
    score: Annotated[bool, Form()] = False,
) -> Response:
    with refused():
        if order and order not in get_args(Order):
            raise Invalid.of(
                "no order %(order)s: the orders are %(orders)s",
                order=repr(order),
                orders=", ".join(get_args(Order)),
            )
        picked = [int(v) for v in version or () if v]
        if not picked:
            raise Invalid.of("pick a trial to run")
        runs = bench.start_trials(
            picked,
            int(concurrency) if concurrency.strip() else None,
            cast(Order, order) if order else None,
        )
    for running in runs:
        _ = bench.queue(running, score)
    return RedirectResponse(f"/runs/{runs[0].run}", 303)


@router.get("/lab/{thread}")
def lab(
    request: Request,
    bench: BenchDep,
    thread: int,
    handle: str | None = None,
    family: Annotated[list[int] | None, Query()] = None,
    by: str | None = None,
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
    models = api_world.models(bench)
    look = api.variation(bench, thread, query)
    versions = api.edits(bench, thread)
    at = next(i for i, v in enumerate(versions) if v.id == look.head.id)
    mine = shown.owner == bench.person.login
    follows = api.follows(bench, thread) if mine and not shown.deleted else None
    proposal = None if follows is None else follows.origin
    lineage = api.lineage(bench, thread)
    families = api_families.families(bench)
    runs = api_runs.runs(bench, reaching=look.skeleton, limit=20)
    base = {p: None if recipe is None else getattr(recipe, p) for p in RECIPE_PARTS}
    purpose = "judge" if judged else "generation"
    with refused(NotFound):
        forced = None if handle is None else bench.handle_named(handle)
    tags, picked = query.tag, family or []
    chosen = [
        f
        for f in families
        if (not tags and not picked) or f.id in picked or set(f.tags) & set(tags)
    ]
    fared = (
        None
        if judged
        else _fared(
            bench,
            thread,
            versions[at].id,
            lineage,
            chosen,
            forced,
            by,
            bool(tags or picked),
        )
    )
    props: dict[str, Any] = {
        "configuration": shown.model_dump(mode="json"),
        "judged": judged,
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
        "configurations": [
            t.model_dump(mode="json")
            for t in api.threads(bench, "configuration", purpose=purpose)
        ],
        "models": [m.name for m in models],
        "everyTag": sorted({t for f in families for t in f.tags}),
        "families": [f.model_dump(mode="json") for f in families],
        "itemsPerRun": settings.ITEMS_PER_RUN,
        "runs": [r.model_dump(mode="json") for r in runs],
    }
    ordered = _ordered(lineage, {} if fared is None else fared.mean_of)
    faring: list[tuple[str, str | int]] = [
        *([("handle", handle)] if handle else []),
        *(("family", f) for f in picked),
        *([("by", by)] if by else []),
    ]
    kept = [
        *([("handle", handle)] if handle else []),
        *(("tag", t) for t in query.tag),
        *(("family", f) for f in picked),
    ]
    return page(
        request,
        "lab.html",
        person=bench.person,
        configuration=shown,
        judged=judged,
        titles=_titles(bench, None if fared is None else fared.compared),
        translations=_translations(bench, recipe),
        versions=versions,
        at=at,
        links=[_also(linked(query, v.id, versions[-1].id), faring) for v in versions],
        varying=[
            *((p, d or "") for p, d in query.given().items()),
            *([("under", query.under)] if query.under is not None else []),
        ],
        origin=_origin(bench, shown.forked_from),
        proposal=proposal,
        changes=[
            (
                v.path.removeprefix("/recipe/"),
                _held(bench, v.base),
                _held(bench, v.fork),
            )
            for v in ([] if proposal is None else proposal.varies)
        ],
        moved=None if follows is None else follows.moved,
        lineage=[(k, depth) for k, depth in ordered if not k.deleted],
        gone=[k for k, _ in ordered if k.deleted],
        me=next(k for k in lineage if k.id == thread),
        fared=fared,
        units={}
        if fared is None
        else {key: unit_in(bench, v.scorer, v.view) for key, v, _ in fared.rows},
        handle=handle,
        handles=[m.name for m in models],
        every_tag=sorted({t for f in families for t in f.tags}),
        tags=query.tag,
        families=[f for f in families if f.id in picked],
        kept="?" + urlencode(kept) if kept else "",
        trials=[] if judged else _trials(bench, versions),
        orders=get_args(Order),
        props=props,
        island="lab",
    )


def _varying(request: Request) -> schemas.Varying:
    given: dict[str, Any] = {}
    for key, value in request.query_params.multi_items():
        if key == "tag":
            given.setdefault("tag", []).append(value)
        elif key not in _FARING:
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


def _also(link: str, more: list[tuple[str, str | int]]) -> str:
    return link if not more else link + ("" if link == "?" else "&") + urlencode(more)


def _held(bench: Bench, value: JsonValue) -> str:
    if isinstance(value, str) and bench.rows.kind(value) is not None:
        return bench.title(value)
    return "—" if value is None else json.dumps(value)


def _origin(bench: Bench, forked_from: int | None) -> int | None:
    found = None if forked_from is None else bench.rows.edit(forked_from)
    return None if found is None else found.thread


def _choices(
    bench: Bench, part: str, models: list[schemas.Model]
) -> list[schemas.Thread]:
    found = api.threads(bench, part)
    if part != "model":
        return found
    served = {m.weights for m in models}
    return [t for t in found if t.head.digest in served]


def _translations(bench: Bench, recipe: Recipe | None) -> tuple[int, str] | None:
    if recipe is None or recipe.translations is None:
        return None
    held = bench.holder(recipe.translations)
    return None if held is None else (held[0].thread, bench.title(recipe.translations))


# Policy: a trial is the configuration's when its skeleton is one of its versions, or
# compiled from the recipe of one into a language.
def _trials(bench: Bench, versions: list[schemas.Edit]) -> list[_Starting]:
    held = {v.digest for v in versions}
    recipes = [
        r
        for v in versions
        if (e := bench.rows.edit(v.id)) is not None
        and (r := threads.recipe(bench.rows, e)) is not None
    ]
    found: list[_Starting] = []
    for t in own_first(bench, api.threads(bench, "trial")):
        skeleton = resolve(bench.store.get, t.head.digest, Trial).skeleton
        compiled = bench.rows.compilations(skeleton)
        if skeleton in held or any(c.recipe in recipes for c in compiled):
            found.append(_starting(bench, t.id))
    return found


def _starting(bench: Bench, thread: int) -> _Starting:
    shown = api.thread(bench, thread)
    if shown.kind != "trial":
        raise NotFound.of(
            "no trial %(thread)s for %(login)s", thread=thread, login=bench.person.login
        )
    held = resolve(bench.store.get, shown.head.digest, Trial)
    versions = api.edits(bench, thread)
    try:
        at = bench.endpoint(bench.inventory.serving(held.engine))
    except LookupError:
        named = shown.name or shown.title
        why = tr("%(trial)s is out of date: update it on its page", trial=named)
        return _Starting(shown, versions, held, None, why)
    return _Starting(shown, versions, held, at, None)


@dataclass(frozen=True)
class Fared:
    columns: list[Column]
    compared: schemas.Compared | None
    rows: list[tuple[str, schemas.ComparedView, list[tuple[float | None, int] | None]]]
    by: str | None
    mean_of: dict[int, float | None]
    cases: int | None


def _fared(
    bench: Bench,
    thread: int,
    head: int,
    lineage: list[schemas.Kin],
    held: list[schemas.Family],
    forced: Handle | None,
    by: str | None,
    narrowed: bool,
) -> Fared:
    cases = [f.case for f in held]
    columns = _columns(bench, thread, head, lineage, forced, cases)
    ran = [c.run for c in columns if c.run is not None]
    compared = api_runs.compared(bench, [r.id for r in ran]) if ran else None
    views = [] if compared is None else compared.views
    sorted_by = viewed(views, by)
    counted = iter(range(len(ran)))
    at_run = [None if c.run is None else next(counted) for c in columns]
    rows = [(keyed(v), v, _fares(v, at_run)) for v in views]
    sorting = next((fares for key, _, fares in rows if key == sorted_by), None)
    by_column: list[float | None] = [
        None if fare is None else fare[0] for fare in sorting or [None for _ in columns]
    ]
    return Fared(
        columns,
        compared,
        rows,
        sorted_by,
        {k.id: m for c, m in zip(columns, by_column) for k in c.names},
        len(cases) if narrowed else None,
    )


# Policy: Configurations that send the set's cases as the same skeletons under the same
# handle share a column, as a fork that varies nothing does its origin's.
def _columns(
    bench: Bench,
    thread: int,
    head: int,
    lineage: list[schemas.Kin],
    forced: Handle | None,
    cases: list[str],
) -> list[Column]:
    found: dict[tuple[tuple[str, ...], str | None], Column] = {}
    shown = _column(bench, thread, head, forced, cases)
    found[(shown.skeletons, shown.handle)] = shown
    login = bench.person.login
    for k in sorted(lineage, key=lambda k: (k.id != thread, k.owner != login)):
        if k.deleted:
            continue
        column = _column(bench, k.id, None, forced, cases)
        found.setdefault((column.skeletons, column.handle), column).names.append(k)
    for column in found.values():
        column.run, column.earlier = _matched(bench, column, set(cases))
    return list(found.values())


def _column(
    bench: Bench, thread: int, head: int | None, forced: Handle | None, cases: list[str]
) -> Column:
    held = bench.variation(thread, None, head)
    weights = held.held("model")
    try:
        if forced is not None and weights is not None:
            held = bench.variation(thread, {"model": forced.weights}, head)
        handle = forced or (None if weights is None else bench.handle(weights))
        carried = bench.languages(held, cases)
    except (StructuralError, ValueError) as e:
        return Column((held.configuration.digest,), None, refusal_of(e))
    skeletons = sorted({c.skeleton.digest for c in carried if c.skeleton is not None})
    name = None if handle is None else handle.name
    behind = forced is None and handle is not None and handle.weights != weights
    return Column(
        tuple(skeletons),
        name,
        pgettext("a thread", "out of date") if behind else None,
    )


def _matched(
    bench: Bench, column: Column, cases: set[str]
) -> tuple[schemas.Run | None, list[schemas.Run]]:
    found = {
        r.id: r
        for s in column.skeletons
        for r in api_runs.runs(bench, reaching=s, limit=200)
        if (column.handle is None or r.model == column.handle) and set(r.cases) <= cases
    }
    under = sorted(found.values(), key=lambda r: r.at, reverse=True)
    latest = [r for r in under if r.latest]
    return next(iter(latest), None), [r for r in under if not r.latest]


def keyed(view: schemas.ComparedView) -> str:
    return f"{view.scorer}:{view.view}"


def viewed(views: list[schemas.ComparedView], by: str | None) -> str | None:
    if by in {keyed(v) for v in views}:
        return by
    valued = (v for v in views if any(x is not None for xs in v.values for x in xs))
    return next((keyed(v) for v in valued), None)


def _fares(
    view: schemas.ComparedView, at_run: list[int | None]
) -> list[tuple[float | None, int] | None]:
    return [
        None
        if i is None
        else (view.means[i], sum(x is not None for x in view.values[i]))
        for i in at_run
    ]


def _ordered(
    lineage: list[schemas.Kin], mean_of: dict[int, float | None]
) -> list[tuple[schemas.Kin, int]]:
    forks: dict[int | None, list[schemas.Kin]] = {}
    for k in lineage:
        forks.setdefault(k.origin, []).append(k)
    found: list[tuple[schemas.Kin, int]] = []

    def down(origin: int | None, depth: int) -> None:
        for k in sorted(
            forks.get(origin, []), key=lambda k: _higher(mean_of.get(k.id))
        ):
            found.append((k, depth))
            down(k.id, depth + 1)

    down(None, 0)
    return found


def _higher(mean: float | None) -> tuple[bool, float]:
    return (mean is None, -(mean or 0.0))


def _titles(bench: Bench, compared: schemas.Compared | None) -> dict[str, str]:
    apart = [] if compared is None else compared.apart
    return {c.case: bench.title(c.case) for c in apart}

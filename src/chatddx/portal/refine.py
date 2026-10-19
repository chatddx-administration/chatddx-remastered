from dataclasses import dataclass, field
from typing import Annotated
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse

from chatddx.api import (
    families as api_families,
    runs as api_runs,
    schemas,
    threads as api,
    world as api_world,
)
from chatddx.api.state import refused
from chatddx.bench import Bench, Handle, NotFound
from chatddx.factors.base import StructuralError
from chatddx.factors.request import RECIPE_PARTS, Recipe

from .pages import BenchDep, own_first, page

router = APIRouter()


@dataclass
class Column:
    skeletons: tuple[str, ...]
    handle: str | None
    said: str | None = None
    names: list[schemas.Kin] = field(default_factory=list[schemas.Kin])
    run: schemas.Run | None = None
    earlier: list[schemas.Run] = field(default_factory=list[schemas.Run])


@router.get("/refine")
def refining(request: Request, bench: BenchDep) -> Response:
    listed = own_first(bench, api.threads(bench, "configuration", purpose="generation"))
    if listed:
        return RedirectResponse(f"/refine/{listed[0].id}", 303)
    return page(request, "refine.html", person=bench.person, configuration=None)


@router.get("/refine/{thread}")
def refine(
    request: Request,
    bench: BenchDep,
    thread: int,
    model: str | None = None,
    tag: Annotated[list[str] | None, Query()] = None,
    family: Annotated[list[int] | None, Query()] = None,
    head: int | None = None,
    by: str | None = None,
) -> Response:
    shown = api.thread(bench, thread)
    if shown.kind != "skeleton":
        raise HTTPException(404, f"no configuration {thread} for {bench.person.login}")
    varied = bench.variation(thread, None, head)
    recipe = varied.recipe
    if recipe is not None and recipe.purpose == "judge":
        raise HTTPException(
            404, f"configuration {thread} is a judge's, and a judge isn't run on cases"
        )
    with refused(NotFound):
        forced = None if model is None else bench.handle_named(model)
    versions = api.edits(bench, thread)
    at = next(i for i, v in enumerate(versions) if v.id == varied.configuration.id)
    lineage = api.lineage(bench, thread)
    families = api_families.families(bench)
    tags, picked = tag or [], family or []
    held = [
        f
        for f in families
        if (not tags and not picked) or f.id in picked or set(f.tags) & set(tags)
    ]
    cases = [f.case for f in held]

    columns = _columns(bench, thread, versions[at].id, lineage, forced, cases)
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
    mean_of = {k.id: m for c, m in zip(columns, by_column) for k in c.names}
    query: list[tuple[str, str | int]] = [
        *([("model", model)] if model else []),
        *(("tag", t) for t in tags),
        *(("family", f) for f in picked),
    ]
    ordered = _ordered(lineage, mean_of)
    return page(
        request,
        "refine.html",
        person=bench.person,
        configuration=shown,
        recipe=None if recipe is None else recipe.model_dump(mode="json"),
        parts=[p for p in RECIPE_PARTS if recipe is not None and getattr(recipe, p)],
        titles=_titles(bench, recipe, compared),
        versions=versions,
        at=at,
        lineage=[(k, depth) for k, depth in ordered if not k.deleted],
        gone=[k for k, _ in ordered if k.deleted],
        me=next(k for k in lineage if k.id == thread),
        mean_of=mean_of,
        models=[m.name for m in api_world.models(bench) if m.problem is None],
        model=model,
        every_tag=sorted({t for f in families for t in f.tags}),
        tags=tags,
        families=[f for f in families if f.id in picked],
        cases=len(cases) if tags or picked else None,
        columns=columns,
        compared=compared,
        rows=rows,
        by=sorted_by,
        kept="?" + urlencode(query) if query else "",
        island="refine",
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
        return Column((held.configuration.digest,), None, str(e))
    skeletons = sorted({c.skeleton.digest for c in carried if c.skeleton is not None})
    name = None if handle is None else handle.name
    behind = forced is None and handle is not None and handle.weights != weights
    return Column(
        tuple(skeletons),
        name,
        f"its model is behind {name}: follow it" if behind else None,
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


def _titles(
    bench: Bench, recipe: Recipe | None, compared: schemas.Compared | None
) -> dict[str, str]:
    held = [] if recipe is None else [getattr(recipe, p) for p in RECIPE_PARTS]
    cases = [] if compared is None else [i.case for i in compared.items]
    cases += [] if compared is None else [c.case for c in compared.apart]
    return {d: bench.title(d) for d in [*held, *cases] if isinstance(d, str)}

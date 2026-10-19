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
from chatddx.bench import Bench
from chatddx.factors.request import RECIPE_PARTS, Recipe

from .pages import BenchDep, page

router = APIRouter()


@router.get("/refine")
def refining(request: Request, bench: BenchDep) -> Response:
    listed = _listed(bench)
    if listed:
        return RedirectResponse(f"/refine/{listed[0].id}", 303)
    return page(request, "refine.html", person=bench.person, configuration=None)


@router.get("/refine/{thread}")
def refine(
    request: Request,
    bench: BenchDep,
    thread: int,
    endpoint: str | None = None,
    language: str | None = None,
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
    versions = api.edits(bench, thread)
    at = next(i for i, v in enumerate(versions) if v.id == varied.configuration.id)
    lineage = api.lineage(bench, thread)
    endpoints = api_world.endpoints(bench)
    serving = [e for e in endpoints if recipe is not None and e.serves == recipe.model]
    chosen = endpoint or (serving[0].name if len(serving) == 1 else None)
    spec = next((e for e in endpoints if e.name == chosen), None)
    if chosen is not None and spec is None:
        raise HTTPException(422, f"no endpoint {chosen!r} in the World")
    families = api_families.families(bench)
    language = language or shown.language
    tags, picked = tag or [], family or []
    held = [
        f
        for f in families
        if (not tags and not picked) or f.id in picked or set(f.tags) & set(tags)
    ]
    cases = {f.case for f in held if language is None or f.language == language}
    narrowed = bool(tags or picked)

    columns = _columns(versions[at].digest, lineage, thread, bench.person.login)
    matched: list[schemas.Run | None] = []
    elsewhere: list[int] = []
    for skeleton, _ in columns:
        found = api_runs.runs(bench, reaching=skeleton, limit=200)
        on = [
            r
            for r in found
            if spec is not None
            and r.engine == spec.engine
            and (language is None or r.language == language)
            and (not narrowed or set(r.cases) <= cases)
        ]
        matched.append(on[0] if on else None)
        elsewhere.append(len(found) - len(on))
    ran = [r for r in matched if r is not None]
    compared = api_runs.compared(bench, [r.id for r in ran]) if ran else None
    views = [] if compared is None else compared.views
    sorted_by = viewed(views, by)
    means = _means(compared, matched, sorted_by)
    mean_of = {k.id: m for (_, names), m in zip(columns, means) for k in names}

    query: list[tuple[str, str | int]] = [
        *([("endpoint", chosen)] if chosen else []),
        *([("language", language)] if language else []),
        *(("tag", t) for t in tags),
        *(("family", f) for f in picked),
    ]
    kept = "?" + urlencode(query) if query else ""
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
        lineage=_ordered(lineage, mean_of),
        me=next(k for k in lineage if k.id == thread),
        mean_of=mean_of,
        endpoints=endpoints,
        endpoint=chosen,
        languages=sorted(
            {*shown.translated, *(f.language for f in families if f.language)}
            | {lang for lang in (language, shown.language) if lang}
        ),
        language=language,
        every_tag=sorted({t for f in families for t in f.tags}),
        tags=tags,
        families=[f for f in families if f.id in picked],
        cases=len(cases) if narrowed else None,
        columns=[(names, run) for (_, names), run in zip(columns, matched)],
        elsewhere=elsewhere,
        compared=compared,
        by=sorted_by,
        kept=kept,
        island="refine",
    )


def _listed(bench: Bench) -> list[schemas.Thread]:
    login = bench.person.login
    found = api.threads(bench, "configuration", purpose="generation")
    return sorted(found, key=lambda t: (t.owner != login, t.name or t.title))


# Policy: A fork that varies nothing holds its origin's skeleton, so it shares its column.
def _columns(
    skeleton: str, lineage: list[schemas.Kin], thread: int, me: str
) -> list[tuple[str, list[schemas.Kin]]]:
    held: dict[str, list[schemas.Kin]] = {skeleton: []}
    for k in sorted(lineage, key=lambda k: (k.id != thread, k.owner != me)):
        if not k.deleted:
            held.setdefault(k.head.digest, []).append(k)
    return list(held.items())


def viewed(views: list[schemas.ComparedView], by: str | None) -> str | None:
    keys = [f"{v.scorer}:{v.view}" for v in views]
    if by in keys:
        return by
    return next((k for k, v in zip(keys, views) if any(v.counts)), None)


def _means(
    compared: schemas.Compared | None,
    matched: list[schemas.Run | None],
    by: str | None,
) -> list[float | None]:
    if compared is None or by is None:
        return [None for _ in matched]
    [view] = [v for v in compared.views if f"{v.scorer}:{v.view}" == by]
    at = iter(view.means)
    return [None if r is None else next(at) for r in matched]


def _ordered(
    lineage: list[schemas.Kin], mean_of: dict[int, float | None]
) -> list[schemas.Kin]:
    forks: dict[int | None, list[schemas.Kin]] = {}
    for k in lineage:
        forks.setdefault(k.origin, []).append(k)
    found: list[schemas.Kin] = []

    def down(origin: int | None) -> None:
        for k in sorted(
            forks.get(origin, []), key=lambda k: _higher(mean_of.get(k.id))
        ):
            found.append(k)
            down(k.id)

    down(None)
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

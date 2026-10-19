from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from chatddx.api import families as api_families, schemas, threads as api
from chatddx.api.state import refused
from chatddx.bench import Bench
from chatddx.catalog.language import recipe_language
from chatddx.factors.base import resolve
from chatddx.factors.request import Purpose, Recipe, Toolset, translated, untranslated

from .pages import BenchDep, page

router = APIRouter()


@router.get("/translate")
def translating(request: Request, bench: BenchDep) -> Response:
    listed = _listed(bench, "generation")
    if listed:
        return RedirectResponse(f"/translate/{listed[0].id}", 303)
    return page(request, "translate.html", person=bench.person, configuration=None)


@router.get("/translate/{thread}")
def translate(
    request: Request,
    bench: BenchDep,
    thread: int,
    into: str | None = None,
    head: int | None = None,
) -> Response:
    varied = bench.variation(thread, None, head)
    recipe = varied.recipe
    families = {f.language for f in api_families.families(bench) if f.language}
    context: dict[str, Any] = {
        "person": bench.person,
        "configuration": api.thread(bench, thread),
        "head": head,
        "listed": [
            (t, _marks(bench, t, families)) for t in _listed(bench, "generation")
        ],
        "judges": _listed(bench, "judge"),
    }
    if recipe is None or recipe.purpose == "judge":
        return page(request, "translate.html", **context, recipe=recipe)
    own = recipe_language(bench.rows, recipe)
    offered = sorted(
        (set(translated(recipe, bench.store.get)) | families) - {own or ""}
    )
    into = into or next(iter(offered), None)
    if into is None:
        return page(request, "translate.html", **context, recipe=recipe, own=own)
    with refused():
        given = schemas.Translating.model_validate({"into": into, "head": head})
        made = api.translation(bench, thread, given)
    missing = len({t.text for t in made.texts if t.translation is None})
    props: dict[str, Any] = {
        "into": into,
        "language": own,
        "texts": [t.model_dump(mode="json") for t in made.texts],
        "unused": made.unused,
        "written": made.written,
        "request": made.request,
        "bodies": _bodies(bench, recipe),
        "parts": _parts(bench, recipe),
    }
    return page(
        request,
        "translate.html",
        **context,
        recipe=recipe,
        own=own,
        into=into,
        offered=sorted({*offered, into}),
        made=made,
        groups=_grouped(made.texts),
        missing=missing,
        parts=_parts(bench, recipe),
        translations=_translations(bench, recipe),
        props=props,
        island="translate",
    )


def _listed(bench: Bench, purpose: Purpose) -> list[schemas.Thread]:
    login = bench.person.login
    found = api.threads(bench, "configuration", purpose=purpose)
    return sorted(found, key=lambda t: (t.owner != login, t.name or t.title))


def _marks(bench: Bench, t: schemas.Thread, families: set[str]) -> dict[str, int]:
    recipe = bench.variation(t.id).recipe
    if recipe is None:
        return {}
    into = (set(t.translated) | families) - {t.language}
    get = bench.store.get
    return {
        language: len(untranslated(recipe, get, language)) for language in sorted(into)
    }


def _grouped(
    found: list[schemas.TranslatedText],
) -> list[tuple[str, list[schemas.TranslatedText]]]:
    groups: dict[str, list[schemas.TranslatedText]] = {}
    for t in found:
        groups.setdefault(t.part, []).append(t)
    return list(groups.items())


def _parts(bench: Bench, recipe: Recipe) -> dict[str, dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {
        "appendix_layout": {"title": "the appendix layout", "thread": None}
    }
    for part in ("instructions", "few_shot", "prompt", "output", "toolset"):
        if (digest := getattr(recipe, part)) is not None:
            found[part] = _held(bench, digest)
    return found


def _held(bench: Bench, digest: str) -> dict[str, Any]:
    held = bench.holder(digest)
    if held is None:
        return {"title": bench.title(digest), "thread": None}
    edit, about = held
    return {"title": about.name or bench.title(digest), "thread": edit.thread}


def _translations(bench: Bench, recipe: Recipe) -> dict[str, Any] | None:
    return None if recipe.translations is None else _held(bench, recipe.translations)


def _bodies(bench: Bench, recipe: Recipe) -> list[dict[str, Any]]:
    get = bench.store.get
    found = [{"part": "appendix_layout", "body": recipe.appendix_layout.model_dump()}]
    for part in ("instructions", "few_shot", "prompt", "output", "toolset"):
        if (digest := getattr(recipe, part)) is not None:
            found.append({"part": part, "body": get(digest).model_dump(mode="json")})
    if recipe.toolset is not None:
        found += [
            {"part": "toolset", "body": get(tool).model_dump(mode="json")}
            for tool in resolve(get, recipe.toolset, Toolset).tools
        ]
    return found

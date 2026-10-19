from typing import Any

from fastapi import APIRouter, Request, Response
from fastapi.responses import RedirectResponse

from chatddx.api import families as api_families, schemas, threads as api
from chatddx.api.state import refused
from chatddx.bench import Bench
from chatddx.bench.model import MODEL, PLACEHOLDERS
from chatddx.catalog.language import recipe_language
from chatddx.factors.base import resolve
from chatddx.factors.request import (
    Purpose,
    Recipe,
    Toolset,
    texts,
    translated,
    untranslated,
)

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
    shown = api.thread(bench, thread)
    context: dict[str, Any] = {
        "person": bench.person,
        "configuration": shown,
        "head": head,
        "listed": [
            (t, _marks(bench, t, families)) for t in _listed(bench, "generation")
        ],
        "judges": _listed(bench, "judge"),
    }
    if recipe is None or recipe.purpose == "judge":
        return page(request, "translate.html", **context, recipe=recipe, going=[])
    own = recipe_language(bench.rows, recipe)
    going = set(translated(recipe, bench.store.get)) - {own or ""}
    cased = families - going - {own or ""}
    context |= {
        "recipe": recipe,
        "own": own,
        "going": sorted(going),
        "cased": sorted(cased),
        "regional": _regional(own, going, families),
    }
    into = into or next(iter([*sorted(going), *sorted(cased)]), None)
    if into is None:
        return page(request, "translate.html", **context)
    with refused():
        given = schemas.Translating.model_validate({"into": into, "head": head})
        sent = api.translation(bench, thread, given)
    written = bench.skeleton(varied).render(model=MODEL, seed=None, fills=PLACEHOLDERS)
    props: dict[str, Any] = {
        "into": into,
        "language": own,
        # Accommodating for a discovered fact: tojson sorts an object's keys, and the
        # parts go in the order they are sent.
        "texts": list(texts(recipe, bench.store.get).items()),
        "written": written,
        "request": sent,
        "bodies": _bodies(bench, recipe),
        "parts": _parts(bench, recipe),
        "head": head,
        "configuration": {
            "thread": thread,
            "head": varied.configuration.id,
            "latest": varied.configuration.id == shown.head.id,
            "mine": shown.owner == bench.person.login,
            "owner": shown.owner,
            "name": shown.name or shown.title,
            "translations": recipe.translations,
        },
        "translations": None
        if recipe.translations is None
        else {
            **_held(bench, recipe.translations),
            "digest": recipe.translations,
            "body": bench.store.get(recipe.translations).model_dump(mode="json"),
        },
    }
    return page(
        request,
        "translate.html",
        **context,
        into=into,
        translations=_translations(bench, recipe),
        props=props,
        island="translate",
    )


def _regional(own: str | None, going: set[str], families: set[str]) -> list[str]:
    said: list[str] = []
    for language in sorted(families - going - {own or ""}):
        base = language.split("-")[0]
        if own is not None and own.split("-")[0] == base:
            said.append(
                f"Cases you see in {language} aren't sent as written, though it is "
                + f"written in {own}: a language's tag is compared whole."
            )
        if near := sorted(t for t in going if t.split("-")[0] == base):
            said.append(
                f"Cases you see in {language} aren't sent by its translations into "
                + f"{', '.join(near)}: a language's tag is compared whole, so they want "
                + f"translations into {language}."
            )
    return said


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
        return {
            "title": bench.title(digest),
            "thread": None,
            "head": None,
            "mine": False,
            "owner": None,
        }
    edit, about = held
    return {
        "title": about.name or bench.title(digest),
        "thread": edit.thread,
        "head": edit.id,
        "mine": about.owner == bench.person.id,
        "owner": None if about.owner is None else bench.login(about.owner),
    }


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

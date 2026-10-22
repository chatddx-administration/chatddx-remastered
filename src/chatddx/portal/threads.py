import json
from dataclasses import replace
from typing import Annotated, Any, cast
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import JsonValue
from starlette.datastructures import FormData

from chatddx import catalog
from chatddx.api import families, schemas, threads as api
from chatddx.api.state import refused
from chatddx.bench import KINDS, WRITTEN, Bench, NotFound, word_of
from chatddx.catalog import LANGUAGE_KINDS, Subject, read
from chatddx.factors.base import Component, Finding, language_tag, resolve
from chatddx.factors.kinds import BY_KIND
from chatddx.factors.request import RECIPE_PARTS, Recipe, Translations
from chatddx.factors.scoring import Expectation, Judge, Scorer
from chatddx.factors.trial import Trial, suggest_seeds
from chatddx.ledger import RunStarted

from .changes import changes
from .fields import Field, choices, fields, fresh, listed, parsed, purpose
from .pages import BenchDep, own_first, page, within
from .scoring import unshipped
from .translations import begun, posted, translating, written as translated

# Accommodating for configurations, which a person writes as recipes, not as components.
AUTHORED = WRITTEN | {"skeleton"}
BEGUN = [w for w in KINDS if set(KINDS[w]) & AUTHORED]

router = APIRouter()


async def _form(request: Request) -> FormData:
    return await request.form()


FormDep = Annotated[FormData, Depends(_form)]


@router.get("/library")
def library(
    request: Request,
    bench: BenchDep,
    kind: str = "instructions",
    tag: Annotated[list[str] | None, Query()] = None,
) -> Response:
    words = [*KINDS, "case"]
    if kind not in words:
        raise HTTPException(404, f"no kind {kind!r}: the kinds are {', '.join(words)}")
    found = [] if kind == "case" else listed(bench, kind)
    every = families.families(bench) if kind == "case" else []
    picked = set(tag or ())
    return page(
        request,
        "library.html",
        person=bench.person,
        listed=[(f"/library?kind={w}", w.replace("_", " "), w == kind) for w in words],
        word=kind,
        threads=own_first(bench, [t for t, _ in found]),
        purposes={t.id: p for t, p in found if p is not None},
        written=bool(set(KINDS.get(kind, ())) & AUTHORED),
        begun=kind in BEGUN,
        cases=sorted(
            (f for f in every if not picked or picked & set(f.tags)),
            key=lambda f: (f.owner != bench.person.login, f.name.lower()),
        ),
        tags=sorted({t for f in every for t in f.tags}),
        picked=picked,
        schemas=[
            (t.head.digest, t.name or t.title)
            for t in api.threads(bench, "expectation_schema")
        ]
        if kind == "case"
        else [],
        deleted=[
            (f"/threads/{t.id}", t.name or t.title, word_of(t.kind))
            for w in KINDS
            for t, _ in listed(bench, w, deleted=True)
        ]
        + [
            (f"/cases/{f.id}", f.name, "case")
            for f in families.families(bench, deleted=True)
        ],
    )


@router.get("/library/new")
def beginning(
    request: Request,
    bench: BenchDep,
    kind: str,
    configuration: int | None = None,
    into: str | None = None,
) -> Response:
    model = _begun(kind)
    if model is Translations:
        return _beginning_translations(request, bench, configuration, into)
    with refused(NotFound):
        found = _drawn(bench, model, fresh(model, _given(bench, request)))
    return page(
        request,
        "begun.html",
        person=bench.person,
        word=kind,
        action=f"{request.url.path}?{request.url.query}",
        fields=found,
        picked={
            f.name: choices(bench, f.kinds, f.value, purpose(model))
            for f in found
            if f.editable and f.kinds
        },
        titles={
            d: bench.title(d)
            for f in found
            if not f.editable and f.kinds
            for d in (f.value if isinstance(f.value, list) else [f.value])
            if isinstance(d, str)
        },
        languaged=model is not Recipe
        and model.model_fields["kind"].default in LANGUAGE_KINDS,
        labels=schemas.Labels().model_dump(mode="json") if model is Scorer else None,
    )


@router.post("/library/new")
def writing(
    request: Request,
    bench: BenchDep,
    kind: str,
    form: FormDep,
    into: str | None = None,
) -> Response:
    model = _begun(kind)
    name = str(form.get("name", "")).strip()
    with refused():
        if not name:
            raise ValueError(f"a new {kind.replace('_', ' ')} is named")
        if model is Translations:
            made = translated(None, into or "", posted(form))
            written = bench.new(made, name)
            return RedirectResponse(f"/threads/{written.edit.thread}", 303)
        made = model.model_validate(parsed(fresh(model, _given(bench, request)), form))
        language = str(form.get("language", "")).strip() or None
        labels = None
        if isinstance(made, Scorer):
            labels = schemas.Labels.model_validate_json(
                str(form.get("labels", "{}"))
            ).given()
        written = bench.new(
            cast(Component | Recipe, made),
            name,
            language if isinstance(made, Component) else None,
            labels,
        )
    return RedirectResponse(f"/threads/{written.edit.thread}", 303)


def _beginning_translations(
    request: Request, bench: Bench, configuration: int | None, into: str | None
) -> Response:
    entries = None
    if configuration is not None and into:
        with refused(NotFound):
            entries = begun(bench, configuration, language_tag(into))
    return page(
        request,
        "begun.html",
        person=bench.person,
        word="translations",
        action=f"{request.url.path}?{request.url.query}",
        configurations=[
            (t.id, t.name or t.title)
            for t in own_first(
                bench, api.threads(bench, "configuration", purpose="generation")
            )
        ],
        configuration=configuration,
        into=into,
        entries=entries,
    )


def _given(bench: Bench, request: Request) -> dict[str, str]:
    given = {
        k.removeprefix("f."): v
        for k, v in request.query_params.items()
        if k.startswith("f.")
    }
    if families := request.query_params.getlist("family"):
        held = [bench.family(int(f)).case for f in families]
        given["cases"] = json.dumps(list(dict.fromkeys(held)))
    return given


# Policy: a new trial is begun with what a start of a variation takes when none is
# given.
def _drawn(
    bench: Bench, model: type[Component] | type[Recipe], found: list[Field]
) -> list[Field]:
    if model is not Trial:
        return found
    cases = next(f.value for f in found if f.name == "cases")
    begun: dict[str, JsonValue] = {"seeds": list(suggest_seeds(1))}
    if isinstance(cases, list) and cases:
        begun["cleanup"] = list(bench.cleanup([str(c) for c in cases]))
    return [
        replace(f, value=begun[f.name], given=True)
        if f.editable and f.name in begun
        else f
        for f in found
    ]


def _begun(kind: str) -> type[Component] | type[Recipe]:
    if kind not in BEGUN:
        raise HTTPException(
            404, f"no {kind} is begun here: what is begun here is {', '.join(BEGUN)}"
        )
    if kind == "configuration":
        return Recipe
    return BY_KIND[KINDS[kind][0]]


@router.get("/threads/{thread}")
def thread_page(
    request: Request,
    bench: BenchDep,
    thread: int,
    version: int | None = None,
    into: str | None = None,
) -> Response:
    shown = api.thread(bench, thread)
    word = word_of(shown.kind)
    versions = api.edits(bench, thread)
    at = len(versions) if version is None else version
    if not 1 <= at <= len(versions):
        raise HTTPException(
            404, f"no version {at} of {word} {thread}: it has {len(versions)}"
        )
    edit = versions[at - 1]
    held = bench.store.get(edit.digest)
    before = None if at == 1 else bench.store.get(versions[at - 2].digest)
    origin = None
    if shown.forked_from is not None:
        found = bench.rows.edit(shown.forked_from)
        origin = None if found is None else found.thread
    mine = shown.owner == bench.person.login
    follows = api.follows(bench, thread) if mine and not shown.deleted else None
    latest = at == len(versions)
    gone = unshipped(held) if isinstance(held, Scorer) else None
    editable = mine and latest and not shown.deleted and gone is None
    body = held.model_dump(mode="json")
    words = None
    if isinstance(held, Translations):
        with refused():
            words = translating(bench, held, [v.digest for v in versions], into)
    written = editable and held.kind_name in WRITTEN and words is None
    found = fields(type(held), body, body.keys() if written else ())
    recipe = _recipe(bench, edit.id) if shown.kind == "skeleton" else None
    parts = (
        None
        if recipe is None
        else fields(Recipe, recipe, RECIPE_PARTS if editable else ())
    )
    every = [*found, *(parts or [])]
    titles = {site.digest: bench.title(site.digest) for site in held.refs()}
    titles |= {
        f.value: bench.title(f.value)
        for f in parts or []
        if f.kinds and isinstance(f.value, str)
    }
    return page(
        request,
        "thread.html",
        person=bench.person,
        thread=shown,
        word=word,
        versions=versions,
        at=at,
        fields=found,
        parts=parts,
        editable=any(f.editable for f in every),
        translating=words,
        translatable=editable and words is not None,
        picked={
            f.name: choices(bench, f.kinds, f.value, purpose(type(held)))
            for f in every
            if f.editable and f.kinds
        },
        titles=titles,
        languaged=written and held.kind_name in LANGUAGE_KINDS,
        labels=None
        if not written or not isinstance(held, Scorer)
        else (edit.labels or schemas.Labels()).model_dump(mode="json"),
        checked=_checked(bench, held)
        if held.kind_name in WRITTEN and not gone
        else None,
        changed=None
        if before is None
        else changes(before.model_dump(mode="json"), body),
        revertible=mine and not latest and not shown.deleted and shown.kind in AUTHORED,
        authored=shown.kind in AUTHORED,
        origin=origin,
        mine=mine,
        proposal=None if follows is None else follows.origin,
        moved=None if follows is None else follows.moved,
        unshipped=gone if latest and not shown.deleted else None,
        ran=_ran(bench, versions) if shown.kind == "trial" else None,
    )


def _ran(
    bench: Bench, versions: list[schemas.Edit]
) -> list[tuple[int, RunStarted, str]]:
    at = {v.digest: i for i, v in enumerate(versions, 1)}
    return [(at[r.trial], r, bench.described(r)) for r in bench.runs() if r.trial in at]


def _recipe(bench: Bench, edit: int) -> dict[str, JsonValue] | None:
    found = bench.rows.edit(edit)
    held = None if found is None else catalog.threads.recipe(bench.rows, found)
    return None if held is None else held.model_dump(mode="json")


def _checked(bench: Bench, held: Component) -> tuple[list[Finding], list[str]]:
    refused: list[str] = []
    if isinstance(held, Judge):
        try:
            _ = bench.judged(held)
        except ValueError as e:
            refused.append(str(e))
    try:
        return bench.check(held).findings, refused
    except (LookupError, ValueError) as e:
        return [], [*refused, str(e)]


def _back(thread: int, next: str | None) -> RedirectResponse:
    return RedirectResponse(within(next or f"/threads/{thread}"), 303)


@router.post("/threads/{thread}/said")
def saying(
    bench: BenchDep,
    thread: int,
    name: Annotated[str, Form()] = "",
    description: Annotated[str, Form()] = "",
    tags: Annotated[str, Form()] = "",
    shared: Annotated[str, Form()] = "",
) -> Response:
    given: dict[str, Any] = {
        "name": name.strip() or None,
        "description": description.strip() or None,
        "tags": _listed_words(tags),
        "collaborators": _listed_words(shared),
    }
    with refused(NotFound):
        _ = bench.say(Subject(thread=thread), **given)
    return _back(thread, None)


def _listed_words(given: str) -> list[str]:
    return sorted({w.strip() for w in given.split(",") if w.strip()})


@router.post("/threads/{thread}/delete")
def deleting(bench: BenchDep, thread: int) -> Response:
    with refused():
        _ = bench.say(Subject(thread=thread), deleted=True)
    return _back(thread, None)


@router.post("/threads/{thread}/restore")
def restoring(bench: BenchDep, thread: int) -> Response:
    with refused():
        _ = bench.say(Subject(thread=thread), deleted=False)
    return _back(thread, None)


@router.post("/threads/{thread}/leave")
def leaving(bench: BenchDep, thread: int) -> Response:
    word = word_of(api.thread(bench, thread).kind)
    with refused(NotFound):
        _ = bench.leave(Subject(thread=thread))
    return RedirectResponse(f"/library?kind={word}", 303)


@router.post("/threads/{thread}/edit")
def editing(bench: BenchDep, thread: int, form: FormDep) -> Response:
    shown = api.thread(bench, thread)
    held = bench.store.get(shown.head.digest)
    with refused():
        head = int(str(form.get("head", "")))
        if isinstance(held, Translations):
            into = str(form.get("into", ""))
            made = translated(held, into, posted(form))
            _ = bench.edit(thread, head, made)
            kept = f"?{urlencode({'into': into})}" if into in made.into else ""
            return _back(thread, f"/threads/{thread}{kept}")
        if shown.kind == "skeleton":
            recipe = _recipe(bench, shown.head.id)
            if recipe is None:
                raise ValueError(
                    f"configuration {thread} is written by hand: it has no recipe "
                    + "to pick parts of"
                )
            picked = parsed(fields(Recipe, recipe, RECIPE_PARTS), form)
            replaced = {p: picked.get(p) for p in RECIPE_PARTS}
            given = {p: d for p, d in replaced.items() if d != recipe.get(p)}
            variation = bench.variation(
                thread, cast(dict[str, str | None], given), head
            )
            _ = bench.edit(thread, head, variation)
            return _back(thread, None)
        body = held.model_dump(mode="json")
        made = type(held).model_validate(parsed(fields(type(held), body, body), form))
        language = str(form.get("language", "")).strip() or None
        labels = None
        if isinstance(made, Scorer):
            labels = schemas.Labels.model_validate_json(
                str(form.get("labels", "{}"))
            ).given()
        _ = bench.edit(
            thread,
            head,
            made,
            language=language if held.kind_name in LANGUAGE_KINDS else None,
            labels=labels,
        )
    return _back(thread, None)


@router.post("/threads/{thread}/revert")
def reverting(
    bench: BenchDep,
    thread: int,
    head: Annotated[int, Form()],
    edit: Annotated[int, Form()],
) -> Response:
    earlier = next((v for v in api.edits(bench, thread) if v.id == edit), None)
    if earlier is None:
        raise HTTPException(422, f"edit {edit} isn't a version of thread {thread}")
    held = (
        bench.variation(thread, None, edit)
        if api.thread(bench, thread).kind == "skeleton"
        else bench.store.get(earlier.digest)
    )
    labels = read.labels(bench.rows, edit) if isinstance(held, Scorer) else None
    with refused():
        _ = bench.edit(thread, head, held, labels=labels)
    return _back(thread, None)


@router.post("/threads/{thread}/fork")
def forking(bench: BenchDep, thread: int, name: Annotated[str, Form()]) -> Response:
    if not name.strip():
        raise HTTPException(422, "a fork is named")
    with refused():
        made = bench.fork(thread, name.strip())
    return RedirectResponse(f"/threads/{made.edit.thread}", 303)


@router.post("/threads/{thread}/follow")
def following(
    bench: BenchDep,
    thread: int,
    head: Annotated[int, Form()],
    next: Annotated[str | None, Form()] = None,
) -> Response:
    with refused():
        _ = bench.follow(thread, head)
    return _back(thread, next)


@router.post("/threads/{thread}/moved/follow")
def following_moved(
    bench: BenchDep,
    thread: int,
    head: Annotated[int, Form()],
    next: Annotated[str | None, Form()] = None,
) -> Response:
    with refused():
        _ = bench.follow_moved(thread, head)
    return _back(thread, next)


@router.post("/threads/{thread}/take")
def taking(
    bench: BenchDep, thread: int, next: Annotated[str | None, Form()] = None
) -> Response:
    with refused():
        made = bench.take_from(thread)
    return _back(made, next)


@router.post("/threads/{thread}/carry")
def carrying(
    bench: BenchDep,
    thread: int,
    head: Annotated[int, Form()],
    case: Annotated[str, Form()],
    next: Annotated[str | None, Form()] = None,
) -> Response:
    edit, _ = bench.thread(thread, "expectation")
    held = resolve(bench.store.get, edit.digest, Expectation)
    carried = Expectation(
        case=case, expectation_schema=held.expectation_schema, data=held.data
    )
    with refused():
        _ = bench.edit(thread, head, carried)
    return _back(thread, next)

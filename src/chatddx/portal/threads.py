from typing import Annotated, Any

from fastapi import APIRouter, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from chatddx.api import schemas, threads as api
from chatddx.api.state import refused
from chatddx.bench import KINDS, WRITTEN, Bench, NotFound, word_of
from chatddx.catalog import LANGUAGE_KINDS
from chatddx.factors.base import resolve
from chatddx.factors.cases import Appendix
from chatddx.factors.request import CHUNK_PARTS, Translations
from chatddx.factors.scoring import Expectation, ExpectationSchema

from .pages import BenchDep, own_first, page, within

WORDS = [w for w in KINDS if w != "configuration"]
# Policy: A translations chunk is begun on /translate, beside what it translates.
CHUNKS = [p for p in CHUNK_PARTS if p != "translations"]

router = APIRouter()


@router.get("/library")
def library(request: Request, bench: BenchDep, kind: str = "instructions") -> Response:
    if kind == "configuration":
        return RedirectResponse("/configurations", 303)
    if kind not in KINDS:
        raise HTTPException(404, f"no kind {kind!r}: the kinds are {', '.join(KINDS)}")
    deleted = [t for w in KINDS for t in api.threads(bench, w, deleted=True)]
    return page(
        request,
        "library.html",
        person=bench.person,
        listed=[("/configurations", "configurations", False)]
        + [(f"/library?kind={w}", w.replace("_", " "), w == kind) for w in WORDS],
        word=kind,
        threads=own_first(bench, api.threads(bench, kind)),
        written=bool(set(KINDS[kind]) & WRITTEN),
        begun=kind in CHUNKS,
        deleted=deleted,
        word_of=word_of,
    )


@router.get("/library/new")
def beginning(request: Request, bench: BenchDep, kind: str) -> Response:
    if kind not in CHUNKS:
        raise HTTPException(
            404, f"no {kind} is begun here: the chunks are {', '.join(CHUNKS)}"
        )
    editor = {
        "mode": "new",
        "name": "",
        "body": None,
        "language": None,
        **_chunk(bench, f"chunk.{kind}"),
    }
    return page(
        request,
        "begun.html",
        person=bench.person,
        word=kind,
        editor=editor,
        island="thread",
    )


@router.get("/threads/{thread}")
def thread_page(request: Request, bench: BenchDep, thread: int) -> Response:
    shown = api.thread(bench, thread)
    if shown.kind == "skeleton":
        return RedirectResponse(f"/configurations/{thread}", 303)
    versions = api.edits(bench, thread)
    bodies = {v.digest: bench.store.get(v.digest) for v in versions}
    titles = {
        site.digest: bench.title(site.digest)
        for held in bodies.values()
        for site in held.refs()
    }
    origin = None
    if shown.forked_from is not None:
        found = bench.rows.edit(shown.forked_from)
        origin = None if found is None else found.thread
    mine = shown.owner == bench.person.login
    proposal = None
    if mine and origin is not None and not shown.deleted:
        proposal = api.follows(bench, thread).origin
    held: dict[str, Any] = {
        "word": word_of(shown.kind),
        "versions": [
            {
                **v.model_dump(mode="json"),
                "body": bodies[v.digest].model_dump(mode="json"),
            }
            for v in versions
        ],
        "titles": titles,
        "editor": None if shown.deleted else _editor(bench, shown, mine),
    }
    return page(
        request,
        "thread.html",
        person=bench.person,
        thread=shown,
        word=word_of(shown.kind),
        versions=versions,
        head=bodies[shown.head.digest].model_dump(mode="json"),
        origin=origin,
        mine=mine,
        proposal=proposal,
        held=held,
        island="thread",
    )


def _editor(
    bench: Bench, shown: schemas.ThreadDetail, mine: bool
) -> dict[str, Any] | None:
    held = bench.store.get(shown.head.digest)
    given: dict[str, Any] = {
        "mode": "edit" if mine else "fork",
        "thread": shown.id,
        "head": shown.head.id,
        "name": shown.name or shown.title,
    }
    match held:
        case Appendix():
            return {
                **given,
                "kind": "appendix",
                "vignette": held.vignette.model_dump(mode="json"),
                "text": held.text,
            }
        case Expectation():
            schema = resolve(
                bench.store.get, held.expectation_schema, ExpectationSchema
            )
            return {
                **given,
                "kind": "expectation",
                "case": held.case,
                "schema": held.expectation_schema,
                "json_schema": schema.json_schema,
                "data": held.data,
            }
        case Translations():
            return {**given, "kind": "translations", "into": held.into}
        case _ if held.kind_name.removeprefix("chunk.") in CHUNKS:
            return {
                **given,
                **_chunk(bench, held.kind_name),
                "body": held.model_dump(mode="json"),
                "language": shown.language,
            }
        case _:
            return None


def _chunk(bench: Bench, kind: str) -> dict[str, Any]:
    tools = api.threads(bench, "tool") if kind == "chunk.toolset" else []
    return {
        "kind": "chunk",
        "chunk": kind,
        "languaged": kind in LANGUAGE_KINDS,
        "tools": [t.model_dump(mode="json") for t in tools],
        "me": bench.person.login,
    }


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
        _ = bench.say(thread, **given)
    return _back(thread, None)


def _listed_words(given: str) -> list[str]:
    return sorted({w.strip() for w in given.split(",") if w.strip()})


@router.post("/threads/{thread}/delete")
def deleting(bench: BenchDep, thread: int) -> Response:
    with refused():
        _ = bench.say(thread, deleted=True)
    return _back(thread, None)


@router.post("/threads/{thread}/restore")
def restoring(bench: BenchDep, thread: int) -> Response:
    with refused():
        _ = bench.say(thread, deleted=False)
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

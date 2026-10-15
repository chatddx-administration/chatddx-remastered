from typing import Annotated, Any

from fastapi import APIRouter, Form, HTTPException, Request, Response
from fastapi.responses import RedirectResponse

from chatddx.api import schemas, threads as api
from chatddx.bench import KINDS, WRITTEN, Bench, word_of
from chatddx.factors.base import resolve
from chatddx.factors.cases import Appendix
from chatddx.factors.scoring import Expectation, ExpectationSchema

from .pages import BenchDep, page, within

WORDS = [w for w in KINDS if w != "configuration"]

router = APIRouter()


def _listed(bench: Bench, found: list[schemas.Thread]) -> list[schemas.Thread]:
    login = bench.person.login
    return sorted(found, key=lambda t: (t.owner != login, (t.name or t.title).lower()))


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
        threads=_listed(bench, api.threads(bench, kind)),
        written=bool(set(KINDS[kind]) & WRITTEN),
        deleted=deleted,
        word_of=word_of,
    )


@router.get("/threads/{thread}")
def thread_page(request: Request, bench: BenchDep, thread: int) -> Response:
    shown = api.detail(bench, thread)
    if shown.kind == "skeleton":
        return RedirectResponse(f"/configurations/{thread}", 303)
    versions = api.edits(bench, thread)
    bodies = {v.digest: bench.get(v.digest) for v in versions}
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
        proposal = api.proposal(bench, thread)
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
    held = bench.get(shown.head.digest)
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
            schema = resolve(bench.get, held.expectation_schema, ExpectationSchema)
            return {
                **given,
                "kind": "expectation",
                "case": held.case,
                "schema": held.expectation_schema,
                "json_schema": schema.json_schema,
                "data": held.data,
            }
        case _:
            return None


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
        "tags": _listed_words(tags),
        "collaborators": _listed_words(shared),
    }
    if description.strip():
        given["description"] = description.strip()
    _ = api.say(bench, thread, schemas.Said(**given))
    return _back(thread, None)


def _listed_words(given: str) -> list[str]:
    return sorted({w.strip() for w in given.split(",") if w.strip()})


@router.post("/threads/{thread}/delete")
def deleting(bench: BenchDep, thread: int) -> Response:
    _ = api.delete(bench, thread)
    return _back(thread, None)


@router.post("/threads/{thread}/restore")
def restoring(bench: BenchDep, thread: int) -> Response:
    _ = api.say(bench, thread, schemas.Said.model_validate({"deleted": False}))
    return _back(thread, None)


@router.post("/threads/{thread}/fork")
def forking(
    request: Request,
    bench: BenchDep,
    thread: int,
    name: Annotated[str, Form()],
) -> Response:
    if not name.strip():
        raise HTTPException(422, "a fork is named")
    made = api.fork(
        request,
        Response(),
        bench,
        thread,
        schemas.NewFork.model_validate({"name": name.strip()}),
    )
    return RedirectResponse(f"/threads/{made.id}", 303)


@router.post("/threads/{thread}/follow")
def following(
    bench: BenchDep,
    thread: int,
    head: Annotated[int, Form()],
    next: Annotated[str | None, Form()] = None,
) -> Response:
    _ = api.follow(bench, thread, schemas.NewFollow(head=head))
    return _back(thread, next)


@router.post("/threads/{thread}/facts/follow")
def following_facts(
    bench: BenchDep,
    thread: int,
    head: Annotated[int, Form()],
    next: Annotated[str | None, Form()] = None,
) -> Response:
    _ = api.follow_facts(bench, thread, schemas.NewFollowFacts(head=head))
    return _back(thread, next)


@router.post("/threads/{thread}/take")
def taking(
    request: Request,
    bench: BenchDep,
    thread: int,
    next: Annotated[str | None, Form()] = None,
) -> Response:
    made = api.take(request, Response(), bench, thread, schemas.NewTake(replace=False))
    return _back(made.id, next)


@router.post("/threads/{thread}/carry")
def carrying(
    bench: BenchDep,
    thread: int,
    head: Annotated[int, Form()],
    case: Annotated[str, Form()],
    next: Annotated[str | None, Form()] = None,
) -> Response:
    _ = api.carry(bench, thread, schemas.NewCarry(head=head, case=case))
    return _back(thread, next)

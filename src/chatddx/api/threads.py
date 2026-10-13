from collections.abc import Generator
from contextlib import contextmanager
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response

from chatddx import catalog
from chatddx.bench import (
    KINDS,
    PARTS,
    Bench,
    Conflict,
    MovedOn,
    OverQuota,
    Reach,
    TriedVariation,
)
from chatddx.catalog.titles import describe
from chatddx.factors.base import Finding
from chatddx.factors.request import Purpose, Recipe
from chatddx.factors.trial import suggest_seeds
from chatddx.store import People
from chatddx.store.catalog import Rows

from . import schemas
from .people import BenchDep

router = APIRouter(tags=["threads"])


def login(bench: Bench, person: int | None) -> str | None:
    return None if person is None else bench.login(person)


def edit_of(bench: Bench, edit: catalog.Edit, kind: str | None = None) -> schemas.Edit:
    if kind is None:
        kind = bench.catalog.thread(edit.thread).kind
    labels = None
    if kind == "scorer":
        labels = schemas.Labels.of(bench.catalog.labels(edit.id))
    return schemas.Edit(
        id=edit.id,
        digest=edit.digest,
        compilation=edit.compilation,
        based_on=edit.based_on,
        by=bench.login(edit.by),
        at=edit.at,
        labels=labels,
    )


def thread_of(
    bench: Bench, kind: str, edit: catalog.Edit, about: catalog.About
) -> schemas.Thread:
    return schemas.Thread(
        id=edit.thread,
        kind=kind,
        name=about.name,
        title=bench.catalog.title(edit.thread),
        owner=login(bench, about.owner),
        tags=sorted(about.tags),
        head=edit_of(bench, edit, kind),
    )


@router.get("/threads")
def threads(
    bench: BenchDep,
    kind: Annotated[str, Query(description=f"one of {', '.join(KINDS)}")],
    name: str | None = None,
    owner: Annotated[str | None, Query(description="a login")] = None,
    tag: Annotated[list[str] | None, Query(description="any of these")] = None,
    deleted: Annotated[
        bool, Query(description="the person's own deleted threads instead")
    ] = False,
    purpose: Annotated[
        Purpose | None,
        Query(description="a configuration's, generation unless given"),
    ] = None,
    answers: Annotated[
        str | None,
        Query(description="a configuration's: the title of its answer's JSON Schema"),
    ] = None,
) -> list[schemas.Thread]:
    if kind not in KINDS:
        raise HTTPException(422, f"no kind {kind!r}: the kinds are {', '.join(KINDS)}")
    if purpose is not None and kind != "configuration":
        raise HTTPException(422, "only a configuration has a purpose")
    if answers is not None and kind != "configuration":
        raise HTTPException(422, "only a configuration answers")
    wanted = set(tag or ())
    found = {
        held: bench.deleted(held) if deleted else bench.visible(held)
        for held in KINDS[kind]
    }
    if kind == "configuration":
        found = {
            held: bench.purposed(heads, purpose or "generation")
            for held, heads in found.items()
        }
    if answers is not None:
        found = {held: bench.answering(heads, answers) for held, heads in found.items()}
    return [
        thread_of(bench, held, edit, about)
        for held, heads in found.items()
        for edit, about in heads
        if (name is None or about.name == name)
        and (owner is None or login(bench, about.owner) == owner)
        and (not wanted or wanted & about.tags)
    ]


def detail(bench: Bench, thread: int) -> schemas.ThreadDetail:
    edit, about = bench.thread_by_id(thread, deleted=True)
    found = bench.catalog.thread(thread)
    recipe = bench.catalog.recipe(thread)
    return schemas.ThreadDetail(
        **thread_of(bench, found.kind, edit, about).model_dump(),
        description=about.description,
        collaborators=sorted(bench.login(c) for c in about.collaborators),
        language=bench.catalog.language_of(edit.digest),
        forked_from=found.forked_from,
        recipe=None if recipe is None else recipe.model_dump(mode="json"),
        deleted=about.deleted,
    )


@router.get("/threads/{thread}")
def thread(bench: BenchDep, thread: int) -> schemas.ThreadDetail:
    return detail(bench, thread)


@router.get("/threads/{thread}/edits")
def edits(bench: BenchDep, thread: int) -> list[schemas.Edit]:
    _ = bench.thread_by_id(thread, deleted=True)
    kind = bench.catalog.thread(thread).kind
    return [edit_of(bench, e, kind) for e in bench.catalog.history(thread)]


@contextmanager
def refused() -> Generator[None]:
    try:
        yield
    except (Conflict, MovedOn, OverQuota):
        raise
    except ValueError as e:
        raise HTTPException(422, str(e)) from None


def part_of(bench: Bench, variation: TriedVariation, part: str) -> schemas.Part:
    held = variation.held(part)
    return schemas.Part(
        part=part,
        digest=held,
        title=None if held is None else bench.title(held),
        summary=None if held is None else describe(bench.get(held), bench.title),
        replaced=part in variation.parts,
    )


def reach_of(reach: Reach) -> schemas.Reach:
    return schemas.Reach(
        scorer=reach.thread,
        name=reach.scorer,
        view=reach.view,
        label=reach.label,
        offered=reach.offered,
        cases=reach.cases,
        missing=[f.id for f in reach.missing],
        choosing=[f.id for f in reach.choosing],
    )


@router.get("/threads/{thread}/variation")
def variation(
    bench: BenchDep, thread: int, query: Annotated[schemas.Varying, Query()]
) -> schemas.Variation:
    with refused():
        varied = bench.variation(thread, query.given())
        skeleton = bench.skeleton(varied)
    seed = suggest_seeds(1)[0] if query.seed is None else query.seed
    families = bench.families(query.tag)
    engine = findings = None
    if query.endpoint is not None:
        try:
            engine = bench.endpoint(query.endpoint)
        except LookupError as e:
            raise HTTPException(422, str(e)) from None
        findings = [
            schemas.Finding.of(f)
            for f in bench.findings(varied, engine, seed, families or None)
        ]
    parts = None
    if varied.recipe is not None:
        parts = [part_of(bench, varied, p) for p in PARTS]
    return schemas.Variation(
        head=edit_of(bench, varied.configuration, "skeleton"),
        skeleton=skeleton.digest,
        greedy=skeleton.greedy,
        parts=parts,
        seed=seed,
        request=bench.request(varied, engine, seed),
        findings=findings,
        reach=[reach_of(r) for r in bench.reach(varied, families)],
    )


def made(
    request: Request,
    response: Response,
    bench: Bench,
    thread: int,
    findings: list[Finding],
) -> schemas.MadeThread:
    response.headers["Location"] = request.app.url_path_for("thread", thread=thread)
    found = [schemas.Finding.of(f) for f in findings]
    return schemas.MadeThread(**detail(bench, thread).model_dump(), findings=found)


def configures(bench: Bench, thread: int) -> bool:
    found = Rows(bench.conn).thread(thread)
    return found is not None and found.kind in KINDS["configuration"]


def check_given(configuration: bool, given: schemas.NewFork | schemas.NewEdit) -> None:
    if configuration and (given.component is not None or given.language is not None):
        raise HTTPException(
            422, "a configuration is written with parts, not a component"
        )
    if not configuration and given.parts.given():
        raise HTTPException(422, "only a configuration has parts")
    if configuration and given.labels is not None:
        raise HTTPException(422, "only a scorer has labels")


@router.post("/threads", status_code=201)
def new(
    request: Request, response: Response, bench: BenchDep, given: schemas.NewThread
) -> schemas.MadeThread:
    with refused():
        held = (
            Recipe.model_validate(given.recipe)
            if given.component is None
            else bench.component(given.component)
        )
        labels = None if given.labels is None else given.labels.given()
        written = bench.new(held, given.name, given.language, labels)
    return made(request, response, bench, written.edit.thread, written.findings)


@router.post("/threads/{thread}/forks", status_code=201)
def fork(
    request: Request,
    response: Response,
    bench: BenchDep,
    thread: int,
    given: schemas.NewFork,
) -> schemas.MadeThread:
    configuration = configures(bench, thread)
    check_given(configuration, given)
    with refused():
        if configuration:
            varied = bench.variation(thread, given.parts.given())
            saved = bench.fork(varied, given.name)
            forked = saved.variation.configuration.thread
            findings = bench.linted(saved.digest)
        else:
            component = (
                None if given.component is None else bench.component(given.component)
            )
            labels = None if given.labels is None else given.labels.given()
            written = bench.fork_component(
                thread, given.name, component, given.language, labels
            )
            forked, findings = written.edit.thread, written.findings
    return made(request, response, bench, forked, findings)


@router.post(
    "/threads/{thread}/edits",
    status_code=201,
    responses={
        200: {"description": "Unchanged: it is the head already"},
        409: {"description": "The thread has moved on since the head the edit names"},
    },
)
def edit(
    response: Response, bench: BenchDep, thread: int, given: schemas.NewEdit
) -> schemas.MadeEdit:
    configuration = configures(bench, thread)
    check_given(configuration, given)
    with refused():
        if configuration:
            varied = bench.variation(thread, given.parts.given())
            saved = bench.edit(thread, varied, given.head)
            kept, what = saved.variation.configuration, saved.what
            findings, cases = bench.linted(saved.digest), {}
        else:
            if given.component is None:
                raise ValueError("an edit holds a component")
            component = bench.component(given.component)
            labels = None if given.labels is None else given.labels.given()
            written = bench.edit_component(
                thread, given.head, component, given.language, labels
            )
            kept, what, findings = written.edit, written.what, written.findings
            cases = written.cases
    if what == "unchanged":
        response.status_code = 200
    return schemas.MadeEdit(
        **edit_of(bench, kept).model_dump(),
        findings=[schemas.Finding.of(f) for f in findings],
        cases=cases,
    )


@router.post(
    "/threads/{thread}/takes",
    status_code=201,
    responses={
        409: {
            "description": "The person has their own expectation of the case under "
            + "that schema: replace it to take this one"
        }
    },
)
def take(
    request: Request,
    response: Response,
    bench: BenchDep,
    thread: int,
    given: schemas.NewTake,
) -> schemas.ThreadDetail:
    with refused():
        made = bench.take_from(thread, given.replace)
    response.headers["Location"] = request.app.url_path_for("thread", thread=made)
    return detail(bench, made)


@router.patch("/threads/{thread}")
def say(bench: BenchDep, thread: int, given: schemas.Said) -> schemas.ThreadDetail:
    if "description" in given.model_fields_set and given.description is None:
        raise HTTPException(422, "a description is replaced, never taken away")
    people = People(bench.conn)
    if missing := [c for c in given.collaborators or () if people.find(c) is None]:
        raise HTTPException(422, f"no person {missing[0]!r}")
    with refused():
        _ = bench.say(
            thread,
            name=given.name if "name" in given.model_fields_set else ...,
            description=given.description,
            tags=given.tags,
            collaborators=given.collaborators,
            deleted=given.deleted,
        )
    return detail(bench, thread)


@router.delete("/threads/{thread}", status_code=204)
def delete(bench: BenchDep, thread: int) -> Response:
    with refused():
        _ = bench.say(thread, deleted=True)
    return Response(status_code=204)


@router.get("/threads/{thread}/proposal")
def proposal(bench: BenchDep, thread: int) -> schemas.Proposal | None:
    with refused():
        found = bench.proposal(thread)
    if found is None:
        return None
    varied, held = found.variation, found.proposal
    recipe = isinstance(held, Recipe)
    return schemas.Proposal(
        base=edit_of(bench, varied.base),
        origin_head=edit_of(bench, varied.origin_head),
        varies=[
            schemas.Varied(path=path, base=base, fork=fork)
            for path, (base, fork) in varied.varies.items()
        ],
        recipe=held.model_dump(mode="json") if recipe else None,
        component=None if recipe else held.model_dump(mode="json"),
        digest=found.digest,
        compilation=found.compilation,
    )


@router.post(
    "/threads/{thread}/follows",
    status_code=201,
    responses={
        409: {"description": "The thread has moved on since the head the edit names"}
    },
)
def follow(bench: BenchDep, thread: int, given: schemas.NewFollow) -> schemas.MadeEdit:
    with refused():
        written = bench.follow(thread, given.head, given.language)
    return schemas.MadeEdit(
        **edit_of(bench, written.edit).model_dump(),
        findings=[schemas.Finding.of(f) for f in written.findings],
    )


@router.post(
    "/threads/{thread}/carries",
    status_code=201,
    responses={
        409: {"description": "The thread has moved on since the head the edit names"}
    },
)
def carry(bench: BenchDep, thread: int, given: schemas.NewCarry) -> schemas.MadeEdit:
    with refused():
        written = bench.carry(thread, given.head, given.case)
    return schemas.MadeEdit(
        **edit_of(bench, written.edit).model_dump(),
        findings=[schemas.Finding.of(f) for f in written.findings],
    )

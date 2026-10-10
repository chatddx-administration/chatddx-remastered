from collections.abc import Generator
from contextlib import contextmanager
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response

from chatddx import catalog
from chatddx.bench import KINDS, PARTS, Bench, Reach, TriedVariation
from chatddx.catalog.titles import describe
from chatddx.factors.trial import suggest_seeds

from . import schemas
from .people import BenchDep

router = APIRouter(tags=["threads"])


def login(bench: Bench, person: int | None) -> str | None:
    return None if person is None else bench.login(person)


def edit_of(bench: Bench, edit: catalog.Edit) -> schemas.Edit:
    return schemas.Edit(
        id=edit.id,
        digest=edit.digest,
        compilation=edit.compilation,
        based_on=edit.based_on,
        by=bench.login(edit.by),
        at=edit.at,
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
        head=edit_of(bench, edit),
    )


@router.get("/threads")
def threads(
    bench: BenchDep,
    kind: Annotated[str, Query(description=f"one of {', '.join(KINDS)}")],
    name: str | None = None,
    owner: Annotated[str | None, Query(description="a login")] = None,
    tag: Annotated[list[str] | None, Query(description="any of these")] = None,
) -> list[schemas.Thread]:
    if kind not in KINDS:
        raise HTTPException(422, f"no kind {kind!r}: the kinds are {', '.join(KINDS)}")
    wanted = set(tag or ())
    return [
        thread_of(bench, held, edit, about)
        for held in KINDS[kind]
        for edit, about in bench.visible(held)
        if (name is None or about.name == name)
        and (owner is None or login(bench, about.owner) == owner)
        and (not wanted or wanted & about.tags)
    ]


def detail(bench: Bench, thread: int) -> schemas.ThreadDetail:
    edit, about = bench.thread_by_id(thread)
    found = bench.catalog.thread(thread)
    recipe = bench.catalog.recipe(thread)
    return schemas.ThreadDetail(
        **thread_of(bench, found.kind, edit, about).model_dump(),
        description=about.description,
        collaborators=sorted(bench.login(c) for c in about.collaborators),
        language=bench.catalog.language_of(edit.digest),
        forked_from=found.forked_from,
        recipe=None if recipe is None else recipe.model_dump(mode="json"),
    )


@router.get("/threads/{thread}")
def thread(bench: BenchDep, thread: int) -> schemas.ThreadDetail:
    return detail(bench, thread)


@router.get("/threads/{thread}/edits")
def edits(bench: BenchDep, thread: int) -> list[schemas.Edit]:
    _ = bench.thread_by_id(thread)
    return [edit_of(bench, e) for e in bench.catalog.history(thread)]


# A variation the bench refuses: a digest that isn't a chunk of its part, a part that
# can't be taken out, or parts that don't compile together.
@contextmanager
def refused() -> Generator[None]:
    try:
        yield
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
        # Without a case tagged so, the pair's checks still apply.
        cases = [f.case for f in families] or None
        findings = [
            schemas.Finding.model_validate(f.model_dump())
            for f in bench.findings(varied, engine, seed, cases)
        ]
    parts = None
    if varied.recipe is not None:
        parts = [part_of(bench, varied, p) for p in PARTS]
    return schemas.Variation(
        head=edit_of(bench, varied.configuration),
        skeleton=skeleton.digest,
        greedy=skeleton.greedy,
        parts=parts,
        seed=seed,
        request=bench.request(varied, engine, seed),
        findings=findings,
        reach=[reach_of(r) for r in bench.reach(varied, families)],
    )


@router.post("/threads/{thread}/forks", status_code=201)
def fork(
    request: Request,
    response: Response,
    bench: BenchDep,
    thread: int,
    given: schemas.NewFork,
) -> schemas.ThreadDetail:
    with refused():
        saved = bench.fork(bench.variation(thread, given.parts.given()), given.name)
    made = saved.variation.configuration.thread
    response.headers["Location"] = request.app.url_path_for("thread", thread=made)
    return detail(bench, made)


@router.post(
    "/threads/{thread}/edits",
    status_code=201,
    responses={200: {"description": "Unchanged: it is the head already"}},
)
def edit(
    response: Response, bench: BenchDep, thread: int, given: schemas.NewEdit
) -> schemas.Edit:
    with refused():
        saved = bench.edit(thread, bench.variation(thread, given.parts.given()))
    if saved.what == "unchanged":
        response.status_code = 200
    return edit_of(bench, saved.variation.configuration)

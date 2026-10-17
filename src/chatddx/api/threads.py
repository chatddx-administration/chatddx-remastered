from collections.abc import Generator, Mapping
from contextlib import contextmanager
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response
from pydantic import JsonValue

from chatddx import catalog
from chatddx.bench import (
    KINDS,
    WRITTEN,
    Bench,
    Carried,
    Conflict,
    MovedOn,
    OverQuota,
    Reach,
    TriedVariation,
    Written,
    word_of,
)
from chatddx.catalog import read, titles
from chatddx.catalog.language import edit_languages
from chatddx.catalog.titles import describe
from chatddx.factors.base import Component, Finding, resolve
from chatddx.factors.facts import Landing
from chatddx.factors.kinds import BY_KIND
from chatddx.factors.request import (
    RECIPE_PARTS,
    Compilation,
    Purpose,
    Recipe,
    Translations,
)
from chatddx.factors.scoring import Expectation
from chatddx.factors.trial import suggest_seeds

from . import schemas
from .people import BenchDep

router = APIRouter(tags=["threads"])


def login(bench: Bench, person: int | None) -> str | None:
    return None if person is None else bench.login(person)


def edit_of(bench: Bench, edit: catalog.Edit, kind: str | None = None) -> schemas.Edit:
    if kind is None:
        kind = catalog.threads.thread(bench.rows, edit.thread).kind
    labels = None
    if kind == "scorer":
        labels = schemas.Labels.of(read.labels(bench.rows, edit.id))
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
    bench: Bench,
    kind: str,
    edit: catalog.Edit,
    about: catalog.About,
    languages: Mapping[int, str | None] | None = None,
) -> schemas.Thread:
    if languages is None:
        languages = edit_languages(bench.rows, [edit])
    return schemas.Thread(
        id=edit.thread,
        kind=kind,
        word=word_of(kind),
        name=about.name,
        title=titles.title(bench.rows, edit.thread),
        owner=login(bench, about.owner),
        tags=sorted(about.tags),
        language=languages[edit.id],
        translated=translated(bench, edit),
        head=edit_of(bench, edit, kind),
    )


def translated(bench: Bench, edit: catalog.Edit) -> list[str]:
    if edit.compilation is None:
        return []
    recipe = resolve(bench.store.get, edit.compilation, Compilation).recipe
    if recipe.translations is None:
        return []
    return list(resolve(bench.store.get, recipe.translations, Translations).into)


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
    if kind == "configuration":
        purpose = purpose or "generation"
    found = bench.threads(kind, deleted=deleted, purpose=purpose, answering=answers)
    shown = [
        (edit, about)
        for edit, about in found
        if (name is None or about.name == name)
        and (owner is None or login(bench, about.owner) == owner)
        and (not wanted or wanted & about.tags)
    ]
    languages = edit_languages(bench.rows, [edit for edit, _ in shown])
    [single] = KINDS[kind] if len(KINDS[kind]) == 1 else [None]
    return [
        thread_of(bench, single or bench.rows.kind(e.digest) or "", e, a, languages)
        for e, a in shown
    ]


def detail(bench: Bench, thread: int) -> schemas.ThreadDetail:
    edit, about = bench.thread(thread, deleted=True)
    found = catalog.threads.thread(bench.rows, thread)
    recipe = catalog.threads.recipe(bench.rows, edit)
    return schemas.ThreadDetail(
        **thread_of(bench, found.kind, edit, about).model_dump(),
        description=about.description,
        collaborators=sorted(bench.login(c) for c in about.collaborators),
        forked_from=found.forked_from,
        recipe=None if recipe is None else recipe.model_dump(mode="json"),
        deleted=about.deleted,
    )


@router.get("/threads/{thread}")
def thread(bench: BenchDep, thread: int) -> schemas.ThreadDetail:
    return detail(bench, thread)


@router.get("/threads/{thread}/edits")
def edits(bench: BenchDep, thread: int) -> list[schemas.Edit]:
    _ = bench.thread(thread, deleted=True)
    kind = catalog.threads.thread(bench.rows, thread).kind
    return [
        edit_of(bench, e, kind) for e in catalog.threads.history(bench.rows, thread)
    ]


@contextmanager
def refused() -> Generator[None]:
    try:
        yield
    except (Conflict, MovedOn, OverQuota):
        raise
    except ValueError as e:
        raise HTTPException(422, str(e)) from None


# A look is rendered and linted for the engine the run would go to; none when nothing
# serves the model, or a hand-written configuration names no endpoint.
def _engine_at(
    bench: Bench, varied: TriedVariation, endpoint: str | None
) -> str | None:
    try:
        return bench.at(varied, endpoint).engine
    except (LookupError, ValueError) as e:
        if endpoint is not None:
            raise HTTPException(422, str(e)) from None
        return None


def component_of(doc: Mapping[str, JsonValue]) -> Component:
    kind = doc.get("kind")
    if not isinstance(kind, str) or kind not in WRITTEN:
        raise ValueError(
            f"{kind!r} isn't a kind a person writes: the kinds are "
            + ", ".join(sorted(WRITTEN))
        )
    cls = BY_KIND[kind]
    if doc.get("v", cls.schema_version) != cls.schema_version:
        raise ValueError(f"{kind} is at v{cls.schema_version}, not v{doc['v']}")
    return cls.model_validate({k: v for k, v in doc.items() if k != "v"})


def part_of(
    bench: Bench, variation: TriedVariation, part: str, landed: Landing | None = None
) -> schemas.Part:
    held = variation.held(part)
    return schemas.Part(
        part=part,
        digest=held,
        title=None if held is None else bench.title(held),
        summary=None if held is None else describe(bench.store.get(held), bench.title),
        replaced=part in variation.parts,
        landed=None if landed is None else landed.level,
        nearest=[] if landed is None else list(landed.nearest),
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
        varied = bench.variation(thread, query.given(), query.head)
        skeleton = bench.skeleton(varied)
        landed = bench.landed(varied)
        engine = _engine_at(bench, varied, query.endpoint)
    seed = suggest_seeds(1)[0] if query.seed is None else query.seed
    families = bench.families(query.tag)
    carried: list[Carried] = []
    if families and skeleton.purpose != "judge":
        with refused():
            carried = bench.languages(varied, [f.case for f in families])
    findings = None
    if engine is not None:
        findings = [
            schemas.Finding.of(f)
            for f in bench.findings(varied, engine, seed, carried or None)
        ]
    family_of = {f.case: f.id for f in families}
    parts = None
    if varied.recipe is not None:
        parts = [part_of(bench, varied, p, landed.get(p)) for p in RECIPE_PARTS]
    held = bench.holder(skeleton.digest, varied.varied)
    return schemas.Variation(
        head=edit_of(bench, varied.configuration, "skeleton"),
        label=varied.label,
        skeleton=skeleton.digest,
        held_by=None if held is None else thread_of(bench, "skeleton", *held),
        greedy=skeleton.greedy,
        parts=parts,
        seed=seed,
        request=bench.request(varied, engine, seed),
        findings=findings,
        languages=[
            schemas.Carried(
                language=c.language,
                families=[family_of[case] for case in c.cases],
                translated=c.translated,
                skeleton=None if c.skeleton is None else c.skeleton.digest,
                refused=c.refused,
            )
            for c in carried
        ],
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
    found = bench.rows.thread(thread)
    return found is not None and found.kind in KINDS["configuration"]


def check_given(configuration: bool, given: schemas.NewFork | schemas.NewEdit) -> None:
    if configuration and (given.component is not None or given.language is not None):
        raise HTTPException(
            422, "a configuration is written with parts, not a component"
        )
    if not configuration and given.parts.given():
        raise HTTPException(422, "only a configuration has parts")
    if (
        not configuration
        and isinstance(given, schemas.NewFork)
        and given.head is not None
    ):
        raise HTTPException(
            422,
            "only a configuration is forked from an edit: another kind from a component",
        )
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
            else component_of(given.component)
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
        held = (
            bench.variation(thread, given.parts.given(), given.head)
            if configuration
            else None
            if given.component is None
            else component_of(given.component)
        )
        labels = None if given.labels is None else given.labels.given()
        written = bench.fork(thread, given.name, held, given.language, labels)
    return made(request, response, bench, written.edit.thread, written.findings)


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
            held = bench.variation(thread, given.parts.given())
        elif given.component is None:
            raise ValueError("an edit holds a component")
        else:
            held = component_of(given.component)
        labels = None if given.labels is None else given.labels.given()
        written = bench.edit(thread, given.head, held, given.language, labels)
    if written.what == "unchanged":
        response.status_code = 200
    return made_edit(bench, written)


def made_edit(bench: Bench, written: Written) -> schemas.MadeEdit:
    return schemas.MadeEdit(
        **edit_of(bench, written.edit).model_dump(),
        findings=[schemas.Finding.of(f) for f in written.findings],
        cases=written.cases,
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
    people = bench.people
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
    diverged, held = found.divergence, found.proposal
    recipe = isinstance(held, Recipe)
    return schemas.Proposal(
        base=edit_of(bench, diverged.base),
        origin_head=edit_of(bench, diverged.origin_head),
        varies=[
            schemas.Varied(path=path, base=base, fork=fork)
            for path, (base, fork) in diverged.varies.items()
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
    return made_edit(bench, written)


@router.get("/threads/{thread}/moved")
def moved(bench: BenchDep, thread: int) -> schemas.Moved | None:
    with refused():
        found = bench.moved(thread)
    if found is None:
        return None
    facts, model = found.facts, found.model
    return schemas.Moved(
        about=found.about,
        facts=None
        if facts is None or facts.head is None
        else edit_of(bench, facts.head, "facts"),
        compiled=None if facts is None else facts.digest,
        model=None
        if model is None or model.head is None
        else edit_of(bench, model.head, "model"),
        held=None if model is None else model.digest,
        digest=found.digest,
        compilation=found.compilation,
        refused=found.refused,
    )


@router.post(
    "/threads/{thread}/moved/follows",
    status_code=201,
    responses={
        409: {"description": "The thread has moved on since the head the edit names"}
    },
)
def follow_moved(
    bench: BenchDep, thread: int, given: schemas.NewFollowMoved
) -> schemas.MadeEdit:
    with refused():
        written = bench.follow_moved(thread, given.head)
    return made_edit(bench, written)


@router.post(
    "/threads/{thread}/carries",
    status_code=201,
    responses={
        409: {"description": "The thread has moved on since the head the edit names"}
    },
)
def carry(bench: BenchDep, thread: int, given: schemas.NewCarry) -> schemas.MadeEdit:
    edit, _ = bench.thread(thread)
    with refused():
        word = word_of(bench.rows.kind(edit.digest))
        if word != "expectation":
            raise ValueError(f"{word} {thread} isn't an expectation")
        held = resolve(bench.store.get, edit.digest, Expectation)
        carried = Expectation(
            case=given.case, expectation_schema=held.expectation_schema, data=held.data
        )
        written = bench.edit(thread, given.head, carried)
    return made_edit(bench, written)

from typing import Annotated

from fastapi import APIRouter, HTTPException, Query

from chatddx import catalog
from chatddx.bench import KINDS, Bench

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


@router.get("/threads/{thread}")
def thread(bench: BenchDep, thread: int) -> schemas.ThreadDetail:
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


@router.get("/threads/{thread}/edits")
def edits(bench: BenchDep, thread: int) -> list[schemas.Edit]:
    _ = bench.thread_by_id(thread)
    return [edit_of(bench, e) for e in bench.catalog.history(thread)]

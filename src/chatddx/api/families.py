from typing import Annotated

from fastapi import APIRouter, Query

from chatddx import bench as benches
from chatddx.bench import Ambiguous, Bench, NotFound
from chatddx.factors.base import Fingerprint, resolve
from chatddx.factors.cases import Case

from . import schemas
from .people import BenchDep
from .threads import login

router = APIRouter(tags=["families"])


def family_of(bench: Bench, family: benches.Family) -> schemas.Family:
    return schemas.Family(
        id=family.id,
        name=family.name,
        owner=login(bench, family.about.owner),
        tags=sorted(family.about.tags),
        language=family.about.language,
        case=family.case,
    )


def expected(bench: Bench, case: str, schema: str) -> schemas.Expected:
    try:
        held, ambiguous = bench.expectation(case, schema), None
    except Ambiguous as e:
        held, ambiguous = None, str(e)
    return schemas.Expected(
        expectation_schema=schema,
        title=bench.title(schema),
        expectation=None if held is None else held.digest,
        data=None if held is None else held.data,
        ambiguous=ambiguous,
    )


@router.get("/families")
def families(
    bench: BenchDep,
    tag: Annotated[list[str] | None, Query(description="any of these")] = None,
    name: str | None = None,
) -> list[schemas.Family]:
    return [
        family_of(bench, f)
        for f in bench.families(tag or ())
        if name is None or f.name == name
    ]


@router.get("/families/{family}")
def family(bench: BenchDep, family: int) -> schemas.FamilyDetail:
    found = bench.family_by_id(family)
    case = resolve(bench.get, found.case, Case)
    return schemas.FamilyDetail(
        **family_of(bench, found).model_dump(),
        description=found.about.description,
        collaborators=sorted(bench.login(c) for c in found.about.collaborators),
        appendices=list(case.appendices),
        expectations=[
            expected(bench, found.case, s)
            for s in bench.expectation_schemas(found.case)
        ],
    )


# Case-derived: the one place the API gives a vignette (agents/wip-api.md, A9).
@router.get("/families/{family}/vignette")
def vignette(bench: BenchDep, family: int) -> schemas.Vignette:
    found = bench.family_by_id(family)
    held = resolve(bench.get, found.case, Case).vignette
    try:
        raw = bench.inventory.source(held.source).fetch(held.id)
    except LookupError as e:
        raise NotFound(str(e)) from None
    keyed = held.fingerprint.key_id is not None
    return schemas.Vignette(
        source=held.source,
        id=held.id,
        text=raw.decode("utf-8-sig", errors="replace"),
        drifted=None if keyed else Fingerprint.of(raw) != held.fingerprint,
    )


@router.get("/tags")
def tags(bench: BenchDep) -> list[str]:
    return bench.tags()

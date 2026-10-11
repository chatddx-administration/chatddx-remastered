from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Request, Response

from chatddx import bench as benches
from chatddx.bench import Ambiguous, Bench, NotFound
from chatddx.factors.base import Fingerprint, resolve
from chatddx.factors.cases import Case

from . import schemas
from .people import BenchDep
from .threads import login, made, refused, thread_of

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
        shared=[
            thread_of(bench, "expectation", e, a) for e, a in bench.shared(case, schema)
        ],
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


@router.post("/families/{family}/appendices", status_code=201)
def appendix(
    request: Request,
    response: Response,
    bench: BenchDep,
    family: int,
    given: schemas.NewAppendix,
) -> schemas.MadeThread:
    with refused():
        written = bench.new(bench.appendix(family, given.text), given.name)
    return made(request, response, bench, written.edit.thread, written.findings)


def case_of(bench: Bench, case: str, default: str) -> schemas.FamilyCase:
    held = resolve(bench.get, case, Case)
    return schemas.FamilyCase(
        case=case,
        title=bench.title(case),
        appendices=list(held.appendices),
        default=case == default,
        expectations=[
            expected(bench, case, s) for s in bench.expectation_schemas(case)
        ],
    )


@router.get("/families/{family}/cases")
def cases(bench: BenchDep, family: int) -> list[schemas.FamilyCase]:
    found = bench.family_by_id(family)
    return [case_of(bench, c, found.case) for c in bench.cases(family)]


# A case another family holds is the body's fault, as one the person doesn't see is.
@router.post("/families/{family}/cases", status_code=201)
def case(bench: BenchDep, family: int, given: schemas.NewCase) -> schemas.FamilyCase:
    found = bench.family_by_id(family)
    try:
        with refused():
            if given.replacing is None:
                made = bench.case(family, given.appendices or [])
            elif bench.catalog.family(given.replacing) != family:
                raise ValueError(f"{given.replacing} isn't a case of family {family}")
            else:
                made = bench.replacement(given.replacing)
    except NotFound as e:
        raise HTTPException(422, str(e)) from None
    return case_of(bench, made, found.case)


# Case-derived: the one place the API gives a vignette.
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


# An owner the body names that doesn't exist is the body's fault, as a family not seen is.
@router.post("/takes")
def takes(bench: BenchDep, given: schemas.NewTakes) -> schemas.Taken:
    seen = {f.id: f for f in bench.families()}
    if missing := [f for f in given.families if f not in seen]:
        raise HTTPException(422, f"no case {missing[0]} for {bench.person.login}")
    cases = [seen[f].case for f in given.families]
    try:
        with refused():
            taken = bench.take(cases, given.expectation_schema, given.owner)
    except NotFound as e:
        raise HTTPException(422, str(e)) from None
    of = dict(zip(given.families, cases, strict=True))
    return schemas.Taken(
        taken={f: taken.taken[c] for f, c in of.items() if c in taken.taken},
        kept={f: taken.kept[c] for f, c in of.items() if c in taken.kept},
        choosing={f: taken.choosing[c] for f, c in of.items() if c in taken.choosing},
        missing=[f for f, c in of.items() if c in taken.missing],
    )


@router.get("/tags")
def tags(bench: BenchDep) -> list[str]:
    return bench.tags()

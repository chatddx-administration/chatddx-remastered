from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response

from chatddx import bench as benches, catalog
from chatddx.bench import Ambiguous, Bench, NotFound
from chatddx.factors.base import Fingerprint, resolve
from chatddx.factors.cases import Appendix, Case
from chatddx.store import fetch_vignette

from . import schemas
from .people import BenchDep
from .state import no_store, refused
from .threads import login, made, thread_of

router = APIRouter(tags=["families"])


def _family_of(bench: Bench, family: benches.Family) -> schemas.Family:
    return schemas.Family(
        id=family.id,
        name=family.name,
        owner=login(bench, family.about.owner),
        tags=sorted(family.about.tags),
        language=family.about.language,
        case=family.case,
    )


def _expected(bench: Bench, case: str, schema: str) -> schemas.Expected:
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


def _case_of(bench: Bench, case: str, default: str) -> schemas.FamilyCase:
    held = resolve(bench.store.get, case, Case)
    return schemas.FamilyCase(
        case=case,
        title=bench.title(case),
        appendices=list(held.appendices),
        default=case == default,
        expectations=[
            _expected(bench, case, s) for s in bench.expectation_schemas(case)
        ],
    )


@router.get("/families")
def families(
    bench: BenchDep,
    tag: Annotated[list[str] | None, Query(description="any of these")] = None,
    name: str | None = None,
) -> list[schemas.Family]:
    return [
        _family_of(bench, f)
        for f in bench.families(tag or ())
        if name is None or f.name == name
    ]


@router.get("/families/{family}")
def family(bench: BenchDep, family: int) -> schemas.FamilyDetail:
    found = bench.family(family)
    return schemas.FamilyDetail(
        **_family_of(bench, found).model_dump(),
        description=found.about.description,
        collaborators=sorted(bench.login(c) for c in found.about.collaborators),
        cases=[_case_of(bench, c, found.case) for c in found.cases],
    )


@router.post(
    "/families",
    status_code=201,
    responses={
        429: {"description": "The person has typed as many cases as a day takes"}
    },
)
def typed(
    request: Request, response: Response, bench: BenchDep, given: schemas.NewTyped
) -> schemas.Family:
    with refused():
        found = bench.type_case(
            given.text, name=given.name, language=given.language, source=given.source
        )
    response.headers["Location"] = request.app.url_path_for("family", family=found.id)
    return _family_of(bench, found)


@router.post("/families/{family}/appendices", status_code=201)
def appendix(
    request: Request,
    response: Response,
    bench: BenchDep,
    family: int,
    given: schemas.NewAppendix,
) -> schemas.MadeThread:
    with refused():
        held = Appendix(vignette=bench.family(family).vignette, text=given.text)
        written = bench.new(held, given.name)
    return made(request, response, bench, written.edit.thread, written.findings)


@router.post("/families/{family}/cases", status_code=201)
def case(bench: BenchDep, family: int, given: schemas.NewCase) -> schemas.FamilyCase:
    found = bench.family(family)
    with refused(NotFound):
        if given.replacing is None:
            made = bench.case(family, given.appendices or [])
        elif catalog.families.family_of(bench.rows, given.replacing) != family:
            raise ValueError(f"{given.replacing} isn't a case of family {family}")
        else:
            made = bench.replacement(given.replacing)
    return _case_of(bench, made, found.case)


@router.get("/families/{family}/vignette", dependencies=[Depends(no_store)])
def vignette(bench: BenchDep, family: int) -> schemas.Vignette:
    found = bench.family(family)
    held = resolve(bench.store.get, found.case, Case).vignette
    try:
        raw = fetch_vignette(bench.conn, bench.inventory, held)
    except LookupError as e:
        raise NotFound(str(e)) from None
    keyed = held.fingerprint.key_id is not None
    return schemas.Vignette(
        source=held.source,
        id=held.id,
        text=raw.decode("utf-8-sig", errors="replace"),
        drifted=None if keyed else Fingerprint.of(raw) != held.fingerprint,
    )


@router.post("/takes")
def takes(bench: BenchDep, given: schemas.NewTakes) -> schemas.Taken:
    seen = {f.id: f for f in bench.families()}
    if missing := [f for f in given.families if f not in seen]:
        raise HTTPException(422, f"no case {missing[0]} for {bench.person.login}")
    cases = [seen[f].case for f in given.families]
    with refused(NotFound):
        taken = bench.take(cases, given.expectation_schema, given.owner)
    of = dict(zip(given.families, cases, strict=True))
    return schemas.Taken(
        taken={f: taken.taken[c] for f, c in of.items() if c in taken.taken},
        kept={f: taken.kept[c] for f, c in of.items() if c in taken.kept},
        choosing={f: taken.choosing[c] for f, c in of.items() if c in taken.choosing},
        missing=[f for f, c in of.items() if c in taken.missing],
    )

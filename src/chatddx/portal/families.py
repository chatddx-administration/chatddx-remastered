from typing import Annotated

from fastapi import APIRouter, Form, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import JsonValue

from chatddx.api import families as api, schemas, threads
from chatddx.api.state import refused
from chatddx.factors.base import resolve
from chatddx.factors.cases import Appendix
from chatddx.factors.scoring import ExpectationSchema

from .pages import BenchDep, page

router = APIRouter()


@router.get("/families")
def families(
    request: Request,
    bench: BenchDep,
    tag: Annotated[list[str] | None, Query()] = None,
) -> Response:
    every = api.families(bench)
    picked = set(tag or ())
    return page(
        request,
        "families.html",
        person=bench.person,
        families=[f for f in every if not picked or picked & set(f.tags)],
        tags=sorted({t for f in every for t in f.tags}),
        picked=picked,
    )


@router.get("/families/{family}")
def family(request: Request, bench: BenchDep, family: int) -> Response:
    shown = api.family(bench, family)
    visible = [t.head.digest for t in threads.threads(bench, "expectation_schema")]
    cases = [
        c.model_copy(
            update={
                "expectations": c.expectations
                + [
                    schemas.Expected(
                        expectation_schema=d,
                        title=bench.title(d),
                        expectation=None,
                        data=None,
                        ambiguous=None,
                        shared=[],
                    )
                    for d in visible
                    if d not in {e.expectation_schema for e in c.expectations}
                ]
            }
        )
        for c in shown.cases
    ]
    current = bench.family(shown.id).vignette
    written = [
        t
        for t in threads.threads(bench, "appendix")
        if resolve(bench.store.get, t.head.digest, Appendix).vignette == current
    ]
    appendices = {a for c in cases for a in c.appendices} | {
        t.head.digest for t in written
    }
    login = bench.person.login
    own = {t.head.digest: t for t in threads.threads(bench, "expectation", owner=login)}
    carried: dict[str, list[tuple[str, schemas.Thread]]] = {}
    started: dict[str, JsonValue] = {}
    for c in cases:
        for e in c.expectations:
            if e.expectation not in own:
                continue
            if c.default:
                started[e.expectation_schema] = e.data
            else:
                carried.setdefault(e.expectation_schema, []).append(
                    (c.case, own[e.expectation])
                )
    editors = {
        (c.case, e.expectation_schema): {
            "mode": "new",
            "case": c.case,
            "schema": e.expectation_schema,
            "json_schema": resolve(
                bench.store.get, e.expectation_schema, ExpectationSchema
            ).json_schema,
            "data": started.get(e.expectation_schema),
            "name": f"expectation for {c.title}",
        }
        for c in cases
        for e in c.expectations
        if e.expectation is None and e.ambiguous is None
    }
    return page(
        request,
        "family.html",
        person=bench.person,
        family=shown,
        cases=cases,
        titles={a: bench.title(a) for a in appendices},
        written=written,
        own=own,
        carried=carried,
        editors=editors,
        island="thread",
    )


@router.post("/families/{family}/appendices")
def appending(
    bench: BenchDep,
    family: int,
    name: Annotated[str, Form()],
    text: Annotated[str, Form()],
) -> Response:
    if not name.strip():
        raise HTTPException(422, "an appendix is named")
    if not text:
        raise HTTPException(422, "an appendix holds a text")
    with refused():
        held = Appendix(vignette=bench.family(family).vignette, text=text)
        _ = bench.new(held, name.strip())
    return RedirectResponse(f"/families/{family}#appendices", 303)


@router.post("/families/{family}/cases")
def building(
    bench: BenchDep,
    family: int,
    appendix: Annotated[list[str] | None, Form()] = None,
) -> Response:
    if not appendix:
        raise HTTPException(422, "a case is built of one appendix or more")
    with refused():
        _ = bench.case(family, appendix)
    return RedirectResponse(f"/families/{family}#cases", 303)


@router.get("/families/{family}/vignette")
def vignette(request: Request, bench: BenchDep, family: int) -> Response:
    return page(
        request,
        "vignette.html",
        person=bench.person,
        family=api.family(bench, family),
        vignette=api.vignette(bench, family),
    )

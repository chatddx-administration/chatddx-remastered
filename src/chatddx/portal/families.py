from typing import Annotated

from fastapi import APIRouter, Query, Request, Response

from chatddx.api import families as api

from .pages import BenchDep, page

router = APIRouter()


@router.get("/families")
def families(
    request: Request,
    bench: BenchDep,
    tag: Annotated[list[str] | None, Query()] = None,
) -> Response:
    return page(
        request,
        "families.html",
        person=bench.person,
        families=api.families(bench, tag=tag),
        tags=api.tags(bench),
        picked=set(tag or ()),
    )


@router.get("/families/{family}")
def family(request: Request, bench: BenchDep, family: int) -> Response:
    shown = api.family(bench, family)
    cases = api.cases(bench, family)
    appendices = {a for c in cases for a in c.appendices}
    return page(
        request,
        "family.html",
        person=bench.person,
        family=shown,
        cases=cases,
        titles={a: bench.title(a) for a in appendices},
    )


@router.get("/families/{family}/vignette")
def vignette(request: Request, bench: BenchDep, family: int) -> Response:
    return page(
        request,
        "vignette.html",
        person=bench.person,
        family=api.family(bench, family),
        vignette=api.vignette(bench, family),
    )

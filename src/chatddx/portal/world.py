from fastapi import APIRouter, Request, Response

from chatddx.api import world as api

from .pages import BenchDep, page

router = APIRouter()


@router.get("/endpoints")
def endpoints(request: Request, bench: BenchDep) -> Response:
    return page(
        request,
        "endpoints.html",
        person=bench.person,
        endpoints=api.endpoints(bench),
        models=api.models(bench),
    )

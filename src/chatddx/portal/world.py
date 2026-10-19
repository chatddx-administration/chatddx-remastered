from fastapi import APIRouter, Request, Response

from chatddx.api import world as api

from .pages import BenchDep, page

router = APIRouter()


@router.get("/models")
def models(request: Request, bench: BenchDep) -> Response:
    return page(request, "models.html", person=bench.person, models=api.models(bench))

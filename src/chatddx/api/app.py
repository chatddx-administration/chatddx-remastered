from collections.abc import Callable, Mapping
from importlib import metadata
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic.json_schema import models_json_schema
from starlette.exceptions import HTTPException

from chatddx.bench import Ambiguous, Conflict, MovedOn, NotFound, OverQuota
from chatddx.facts import Facts
from chatddx.inventory import Inventory
from chatddx.runner.gate import Refused

from . import families, people, runs, scores, threads, world
from .schemas import EVENTS, Code, Error
from .state import AppState

STATUSES: dict[type[Exception], tuple[int, Code]] = {
    NotFound: (404, "not_found"),
    Ambiguous: (409, "ambiguous"),
    Conflict: (409, "conflict"),
    MovedOn: (409, "moved_on"),
    OverQuota: (429, "over_quota"),
    Refused: (422, "refused"),
}

CODES: dict[int, Code] = {
    401: "unauthenticated",
    403: "cross_site",
    404: "not_found",
    405: "not_allowed",
    409: "conflict",
    422: "refused",
    429: "over_quota",
}


def _answer(
    status: int, error: Error, headers: Mapping[str, str] | None = None
) -> JSONResponse:
    return JSONResponse(error.model_dump(mode="json"), status, headers)


def _status(status: int, code: Code) -> Callable[[Request, Exception], JSONResponse]:
    def handle(_: Request, e: Exception) -> JSONResponse:
        return _answer(status, Error(detail=str(e), code=code))

    return handle


def _http(_: Request, e: Exception) -> JSONResponse:
    assert isinstance(e, HTTPException)
    error = Error(detail=e.detail, code=CODES.get(e.status_code, "error"))
    return _answer(e.status_code, error, e.headers)


def _invalid(_: Request, e: Exception) -> JSONResponse:
    assert isinstance(e, RequestValidationError)
    return _answer(
        422, Error(detail=jsonable_encoder(e.errors()), code="unprocessable")
    )


def _with_models(made: FastAPI) -> Callable[[], dict[str, Any]]:
    described = made.openapi

    def openapi() -> dict[str, Any]:
        document = described()
        _, models = models_json_schema(
            [(model, "serialization") for model in (*EVENTS.values(), Error)],
            ref_template="#/components/schemas/{model}",
        )
        document["components"]["schemas"].update(models.get("$defs", {}))
        return document

    return openapi


def app(inventory: Inventory, facts: Facts, conninfo: str) -> FastAPI:
    made = FastAPI(
        title="chatddx",
        version=metadata.version("chatddx"),
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url=None,
    )
    made.state.chatddx = AppState(conninfo, inventory, facts)
    for module in (people, threads, families, world, runs, scores):
        made.include_router(module.router, prefix="/api")
    for error, (status, code) in STATUSES.items():
        made.add_exception_handler(error, _status(status, code))
    made.add_exception_handler(HTTPException, _http)
    made.add_exception_handler(RequestValidationError, _invalid)
    made.openapi = _with_models(made)
    return made

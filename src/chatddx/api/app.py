from collections.abc import Callable
from importlib import metadata
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic.json_schema import models_json_schema

from chatddx.bench import Ambiguous, Conflict, MovedOn, NotFound, OverQuota
from chatddx.facts import Facts
from chatddx.inventory import Inventory
from chatddx.runner.gate import Refused

from . import families, people, runs, threads, world
from .schemas import EVENTS
from .state import AppState

STATUSES: dict[type[Exception], int] = {
    NotFound: 404,
    Ambiguous: 409,
    Conflict: 409,
    MovedOn: 409,
    OverQuota: 429,
    Refused: 422,
}


def _status(status: int) -> Callable[[Request, Exception], JSONResponse]:
    def handle(_: Request, e: Exception) -> JSONResponse:
        return JSONResponse({"detail": str(e)}, status_code=status)

    return handle


# The data of a run's events, which no route's response names, among the schemas.
def _with_events(made: FastAPI) -> Callable[[], dict[str, Any]]:
    described = made.openapi

    def openapi() -> dict[str, Any]:
        document = described()
        _, events = models_json_schema(
            [(model, "serialization") for model in EVENTS.values()],
            ref_template="#/components/schemas/{model}",
        )
        document["components"]["schemas"].update(events.get("$defs", {}))
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
    for module in (people, threads, families, world, runs):
        made.include_router(module.router, prefix="/api")
    for error, status in STATUSES.items():
        made.add_exception_handler(error, _status(status))
    made.openapi = _with_events(made)
    return made

from collections.abc import Callable
from importlib import metadata

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from chatddx.bench import Ambiguous, NotFound
from chatddx.facts import Facts
from chatddx.inventory import Inventory
from chatddx.runner.gate import Refused

from . import people
from .state import AppState

# agents/wip-api.md, A10.
STATUSES: dict[type[Exception], int] = {NotFound: 404, Ambiguous: 409, Refused: 422}


def _status(status: int) -> Callable[[Request, Exception], JSONResponse]:
    def handle(_: Request, e: Exception) -> JSONResponse:
        return JSONResponse({"detail": str(e)}, status_code=status)

    return handle


def app(inventory: Inventory, facts: Facts, conninfo: str) -> FastAPI:
    made = FastAPI(
        title="chatddx",
        version=metadata.version("chatddx"),
        openapi_url="/api/openapi.json",
        docs_url="/api/docs",
        redoc_url=None,
    )
    made.state.chatddx = AppState(conninfo, inventory, facts)
    made.include_router(people.router, prefix="/api")
    for error, status in STATUSES.items():
        made.add_exception_handler(error, _status(status))
    return made

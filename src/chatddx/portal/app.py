from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException

from chatddx.api import app as api
from chatddx.core import settings
from chatddx.facts import Facts
from chatddx.inventory import Inventory

from . import configurations, families, pages, runs, world
from .assets import ROUTE, Assets


def app(
    inventory: Inventory, facts: Facts, conninfo: str, assets: Path | None = None
) -> FastAPI:
    made = api.app(inventory, facts, conninfo)
    made.state.assets = Assets(assets or settings.portal_assets())
    made.include_router(pages.router, include_in_schema=False)
    made.mount(
        ROUTE,
        StaticFiles(directory=made.state.assets.root, check_dir=False),
        name="static",
    )
    for error in (*api.STATUSES, HTTPException, RequestValidationError):
        made.add_exception_handler(error, pages.paged(made.exception_handlers[error]))
    made.add_exception_handler(pages.SignInFirst, pages.to_sign_in)
    for router in (runs.router, configurations.router, families.router, world.router):
        made.include_router(router, include_in_schema=False)
    return made

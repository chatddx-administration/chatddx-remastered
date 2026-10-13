from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from chatddx.api import app as api
from chatddx.core import settings
from chatddx.facts import Facts
from chatddx.inventory import Inventory

from . import pages
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
    made.add_exception_handler(pages.SignInFirst, pages.to_sign_in)
    return made

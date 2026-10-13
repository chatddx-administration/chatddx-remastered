from fastapi import FastAPI

from chatddx.api import app as api
from chatddx.facts import Facts
from chatddx.inventory import Inventory

from . import pages


def app(inventory: Inventory, facts: Facts, conninfo: str) -> FastAPI:
    made = api.app(inventory, facts, conninfo)
    made.include_router(pages.router, include_in_schema=False)
    made.add_exception_handler(pages.SignInFirst, pages.to_sign_in)
    return made

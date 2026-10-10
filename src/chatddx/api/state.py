from collections.abc import Iterator
from dataclasses import dataclass

import psycopg
from fastapi import Request

from chatddx.facts import Facts
from chatddx.inventory import Inventory
from chatddx.store.store import Connection


# What the app is made with, loaded once.
@dataclass(frozen=True)
class AppState:
    conninfo: str
    inventory: Inventory
    facts: Facts


def state(request: Request) -> AppState:
    held = request.app.state.chatddx
    assert isinstance(held, AppState)
    return held


# A connection of the request's own, in autocommit mode, as the runner needs.
def connection(request: Request) -> Iterator[Connection]:
    with psycopg.connect(state(request).conninfo, autocommit=True) as conn:
        yield conn

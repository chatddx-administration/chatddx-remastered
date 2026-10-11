from collections.abc import Iterator
from dataclasses import dataclass

import psycopg
from fastapi import Request

from chatddx.facts import Facts
from chatddx.inventory import Inventory
from chatddx.store.store import Connection


@dataclass(frozen=True)
class AppState:
    conninfo: str
    inventory: Inventory
    facts: Facts

    def connect(self) -> Connection:
        return psycopg.connect(self.conninfo, autocommit=True)


def state(request: Request) -> AppState:
    held = request.app.state.chatddx
    assert isinstance(held, AppState)
    return held


def connection(request: Request) -> Iterator[Connection]:
    with state(request).connect() as conn:
        yield conn

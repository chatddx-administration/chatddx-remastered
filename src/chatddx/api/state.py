from collections.abc import Iterator
from dataclasses import dataclass

import psycopg
from fastapi import Request, Response

from chatddx.facts import Facts
from chatddx.inventory import Inventory
from chatddx.store.store import Connection

from .listening import Listener


@dataclass(frozen=True)
class AppState:
    conninfo: str
    inventory: Inventory
    facts: Facts
    listener: Listener

    def connect(self) -> Connection:
        return psycopg.connect(self.conninfo, autocommit=True)


def state(request: Request) -> AppState:
    held = request.app.state.chatddx
    assert isinstance(held, AppState)
    return held


def connection(request: Request) -> Iterator[Connection]:
    with state(request).connect() as conn:
        yield conn


NO_STORE = {"Cache-Control": "no-store"}


def no_store(response: Response) -> None:
    response.headers.update(NO_STORE)

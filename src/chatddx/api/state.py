from collections.abc import Iterator
from dataclasses import dataclass, field

import psycopg
from fastapi import Request

from chatddx.facts import Facts
from chatddx.inventory import Inventory
from chatddx.store.store import Connection

from .jobs import Jobs


@dataclass(frozen=True)
class AppState:
    conninfo: str
    inventory: Inventory
    facts: Facts
    jobs: Jobs = field(default_factory=Jobs)

    def connect(self) -> Connection:
        return psycopg.connect(self.conninfo, autocommit=True)


def state(request: Request) -> AppState:
    held = request.app.state.chatddx
    assert isinstance(held, AppState)
    return held


def connection(request: Request) -> Iterator[Connection]:
    with state(request).connect() as conn:
        yield conn

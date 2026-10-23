from collections.abc import Generator, Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import psycopg
from fastapi import HTTPException, Request, Response

from chatddx.bench import Conflict, MovedOn, OverQuota
from chatddx.inventory import Inventory
from chatddx.store import UnderWay
from chatddx.store.store import Connection

from .listening import Listener


@dataclass(frozen=True)
class AppState:
    conninfo: str
    inventory: Inventory
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


class Refusing(HTTPException):
    def __init__(self, status: int, refused: Exception) -> None:
        super().__init__(status, str(refused))
        self.refused: Exception = refused


# Policy: what may be missing of what a request's body or query names is a 422, where
# what its path names is a 404.
@contextmanager
def refused(*named: type[Exception]) -> Generator[None]:
    try:
        yield
    except (Conflict, MovedOn, OverQuota, UnderWay):
        raise
    except (ValueError, *named) as e:
        raise Refusing(422, e) from None

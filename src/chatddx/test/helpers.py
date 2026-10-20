import time
from collections import defaultdict, deque
from collections.abc import Generator
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
from datetime import UTC, datetime
from typing import NamedTuple
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from chatddx import settings
from chatddx.bench import Bench
from chatddx.curation import Plan
from chatddx.factors.base import resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.request import Skeleton
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.store import People
from chatddx.store.store import Connection

PASSWORD = "correct horse battery staple"
SHIPPED = "chatddx.scorers.metrics:score"
ZERO = "sha256:" + "0" * 64
NOW = datetime(2026, 1, 1, tzinfo=UTC)
INSTRUCTION = (
    "You are assisting a physician in an emergency department. Read the case and give "
    + "your assessment."
)
TYPED = "A 54-year-old woman with sudden breathlessness after a long flight."


# A session closed a moment ago may still be ending on the server, and neither a
# template's copy nor DROP ... WITH (FORCE) waits for it: FORCE may not end a session
# of DB_USER's as DB_ADMIN.
def _settled(admin: Connection, name: str) -> None:
    for _ in range(500):
        row = admin.execute(
            "SELECT count(*) FROM pg_stat_activity WHERE datname = %s", (name,)
        ).fetchone()
        if row is None or row[0] == 0:
            return
        time.sleep(0.01)


# `admin` is a conninfo taken before any test runs, since tests point DB_NAME at
# their own database.
def create_database(admin: str, template: str | None = None) -> str:
    name = f"chatddx_test_{uuid4().hex[:12]}"
    create = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name))
    if template is not None:
        create += sql.SQL(" TEMPLATE {}").format(sql.Identifier(template))
    with psycopg.connect(admin, autocommit=True) as conn:
        if template is not None:
            _settled(conn, template)
        _ = conn.execute(create)
    return name


# A run's or a scoring's job outlives the request that started it, and may connect again
# between settling and dropping after its test has ended.
def drop_database(admin: str, name: str) -> None:
    drop = sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name))
    with psycopg.connect(admin, autocommit=True) as conn:
        for attempt in range(5):
            _settled(conn, name)
            try:
                _ = conn.execute(drop)
                return
            except psycopg.errors.InsufficientPrivilege:
                if attempt == 4:
                    raise


def connect(name: str, admin: bool = False) -> Connection:
    return psycopg.connect(settings.database(admin), dbname=name)


# Copies of a template are made ahead and dropped behind, on threads of their own, so
# that a test waits for its database only when they fall behind.
class Copies:
    AHEAD: int = 6

    def __init__(self) -> None:
        self.admin: str = settings.database(admin=True)
        self._threads: ThreadPoolExecutor = ThreadPoolExecutor(max_workers=3)
        self._ready: defaultdict[str, deque[Future[str]]] = defaultdict(deque)
        self._dropped: list[Future[None]] = []

    def take(self, template: str) -> str:
        ready = self._ready[template]
        while len(ready) <= self.AHEAD:
            ready.append(self._threads.submit(create_database, self.admin, template))
        return ready.popleft().result()

    def give_back(self, name: str) -> None:
        self._dropped.append(self._threads.submit(drop_database, self.admin, name))

    # Before the template itself is dropped.
    def forget(self, template: str) -> None:
        for made in self._ready.pop(template, deque()):
            self.give_back(made.result())

    def close(self) -> None:
        for template in list(self._ready):
            self.forget(template)
        self._threads.shutdown()
        for dropped in self._dropped:
            dropped.result()


# A template for the session, filled in the body of the `with`, from another or from nothing.
@contextmanager
def templated(copies: Copies, of: str | None = None) -> Generator[str]:
    name = create_database(copies.admin, template=of)
    try:
        yield name
    finally:
        copies.forget(name)
        drop_database(copies.admin, name)


class Loaded(NamedTuple):
    name: str
    said: list[str]


# A test parametrized indirectly with a template's name, as "ran", starts from it.
def chosen(request: pytest.FixtureRequest, otherwise: str) -> str:
    return request.getfixturevalue(getattr(request, "param", otherwise))


def skeleton(plan: Plan, recipe: str) -> Skeleton:
    return resolve(plan.registry.get, plan.named("recipe", recipe).digest, Skeleton)


# Accommodating for pytest, which takes the fixtures a conftest or a test module
# imports: these are the variants several of them take, each listed in its __all__ so
# that linters see the import used.
@pytest.fixture(name="template")
def curated_template(request: pytest.FixtureRequest) -> str:
    return chosen(request, "curated")


@pytest.fixture(name="autocommit")
def autocommitted() -> bool:
    return True


@pytest.fixture(name="alice")
def found_alice(conn: Connection) -> Person:
    found = People(conn).find("alice")
    assert found is not None
    return found


@pytest.fixture(name="alice")
def alice_with_password(conn: Connection) -> Person:
    people = People(conn)
    found = people.find("alice")
    assert found is not None
    people.set_password(found.id, PASSWORD)
    return found


@pytest.fixture(name="alice")
def added_alice(conn: Connection) -> Person:
    return People(conn).add("alice", "Alice")


@pytest.fixture(name="bob")
def added_bob(conn: Connection) -> Person:
    return People(conn).add("bob", "Bob")


@pytest.fixture(name="bench")
def found_alices_bench(conn: Connection, world: Inventory) -> Bench:
    alice = People(conn).find("alice")
    assert alice is not None
    return Bench(conn, alice, world)


@pytest.fixture(name="bench")
def alices_bench(conn: Connection, alice: Person, world: Inventory) -> Bench:
    return Bench(conn, alice, world)


@pytest.fixture(name="template")
def sampled_template(sampled: Loaded) -> str:
    return sampled.name


@pytest.fixture(name="reg")
def registry() -> Registry:
    return Registry()

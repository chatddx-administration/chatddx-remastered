import time
from collections import defaultdict, deque
from collections.abc import Generator, Iterator
from concurrent.futures import Future, ThreadPoolExecutor
from contextlib import contextmanager
from typing import Any, NamedTuple
from uuid import uuid4

import psycopg
import pytest
from argon2 import PasswordHasher
from psycopg import sql

from chatddx import settings
from chatddx.api.app import app
from chatddx.bench import Bench
from chatddx.curation import Plan, init, load_cases
from chatddx.facts import BUNDLED, Facts
from chatddx.identity import identity
from chatddx.inventory import Inventory, World
from chatddx.runner.test import tools as test_tools
from chatddx.scripted import RUNS, run, scripted_runs
from chatddx.store import People, Store, migrate
from chatddx.store.store import Connection
from chatddx.test.world import (
    CASES,
    SAMPLE,
    TEST,
    faked,
    free_world,
    world_facts,
    world_plan,
)


# The test World's tools are the runner's test tools (worlds/test/_data/factors.toml), shipped
# for the whole session so that planning takes their entry points.
@pytest.fixture(scope="session", autouse=True)
def shipped_test_tools() -> Iterator[None]:
    with pytest.MonkeyPatch.context() as patch:
        test_tools.shipped(patch)
        yield


# Passwords are hashed as cheaply as argon2 allows: the tests check what is hashed, not
# how hard it is to reverse.
@pytest.fixture(scope="session", autouse=True)
def cheap_hashing() -> Iterator[None]:
    hasher = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(identity, "_hasher", hasher)
        dummy = hasher.hash("dummy")
        patch.setattr(identity, "_dummy_hash", lambda: dummy)
        yield


# What a test writes needn't outlive a crash, so no commit waits for the WAL to reach the disk.
@pytest.fixture(scope="session", autouse=True)
def unsynced_commits() -> Iterator[None]:
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("PGOPTIONS", "-c synchronous_commit=off", prepend=" ")
        yield


# As src/chatddx/cli.py:_openapi makes it.
@pytest.fixture(scope="session")
def described() -> dict[str, Any]:
    return app(Inventory(), Facts.load(BUNDLED), "").openapi()


@pytest.fixture
def world() -> Inventory:
    return free_world()


@pytest.fixture
def fake(world: Inventory, conn: Connection) -> Iterator[None]:
    with faked(world, Store(conn).get):
        yield


# Module-scoped, as tests add to its registry.
@pytest.fixture(scope="module")
def plan() -> Plan:
    return world_plan()


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


@pytest.fixture(scope="session")
def copies() -> Iterator[Copies]:
    made = Copies()
    try:
        yield made
    finally:
        made.close()


# A template for the session, filled in the body of the `with`, from another or from nothing.
@contextmanager
def templated(copies: Copies, of: str | None = None) -> Generator[str]:
    name = create_database(copies.admin, template=of)
    try:
        yield name
    finally:
        copies.forget(name)
        drop_database(copies.admin, name)


@pytest.fixture(scope="session")
def migrated(copies: Copies) -> Iterator[str]:
    with templated(copies) as name:
        with connect(name, admin=True) as conn:
            _ = migrate(conn)
        yield name


@pytest.fixture(scope="session")
def curated(copies: Copies, migrated: str) -> Iterator[str]:
    with templated(copies, migrated) as name:
        with connect(name) as conn:
            alice = People(conn).add("alice", "Alice")
            source = World.load(TEST).inventory.listing()
            _ = init(conn, world_plan(), CASES, source, alice, giftbag=True)
        yield name


@pytest.fixture(scope="session")
def ran(copies: Copies, curated: str) -> Iterator[str]:
    with templated(copies, curated) as name:
        with psycopg.connect(settings.database(), dbname=name, autocommit=True) as conn:
            alice = People(conn).find("alice")
            assert alice is not None
            bench = Bench(conn, alice, free_world(), world_facts())
            for scripted in scripted_runs(TEST / RUNS):
                _ = run(bench, scripted)
        yield name


class Loaded(NamedTuple):
    name: str
    said: list[str]


@pytest.fixture(scope="session")
def sampled(copies: Copies, migrated: str) -> Iterator[Loaded]:
    world = SAMPLE.parent
    with templated(copies, migrated) as name:
        with connect(name) as conn:
            alice = People(conn).add("alice", "Alice")
            source = World.load(world).inventory.listing()
            plan = world_plan(world, SAMPLE)
            said = init(conn, plan, load_cases(SAMPLE), source, alice, giftbag=True)
        yield Loaded(name, said)


# A test parametrized indirectly with a template's name, as "ran", starts from it.
def chosen(request: pytest.FixtureRequest, otherwise: str) -> str:
    return request.getfixturevalue(getattr(request, "param", otherwise))


@pytest.fixture
def template(request: pytest.FixtureRequest) -> str:
    return chosen(request, "migrated")


@pytest.fixture
def db(copies: Copies, template: str) -> Iterator[str]:
    name = copies.take(template)
    try:
        yield name
    finally:
        copies.give_back(name)


@pytest.fixture
def autocommit() -> bool:
    return False


@pytest.fixture
def conn(db: str, autocommit: bool) -> Iterator[Connection]:
    with psycopg.connect(settings.database(), dbname=db, autocommit=autocommit) as c:
        yield c


@pytest.fixture
def admin(db: str) -> Iterator[Connection]:
    with connect(db, admin=True) as c:
        yield c


@pytest.fixture
def empty_db(copies: Copies) -> Iterator[str]:
    name = create_database(copies.admin)
    try:
        yield name
    finally:
        copies.give_back(name)


@pytest.fixture
def empty(empty_db: str) -> Iterator[Connection]:
    with connect(empty_db, admin=True) as c:
        yield c

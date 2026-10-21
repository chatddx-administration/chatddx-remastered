from collections.abc import Iterator
from typing import Any

import psycopg
import pytest
from argon2 import PasswordHasher

from chatddx import settings
from chatddx.api.app import app
from chatddx.bench import Bench
from chatddx.curation import Plan, init, load_cases
from chatddx.identity import identity
from chatddx.inventory import DirectorySource, Inventory, World
from chatddx.runner.test import tools as test_tools
from chatddx.scripted import RUNS, run, scripted_runs
from chatddx.store import People, Store, migrate
from chatddx.store.store import Connection
from chatddx.test.helpers import (
    Copies,
    Loaded,
    chosen,
    connect,
    create_database,
    templated,
)
from chatddx.test.world import (
    CASES,
    SAMPLE,
    TEST,
    faked,
    free_world,
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
    return app(Inventory(), "").openapi()


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


@pytest.fixture(scope="session")
def copies() -> Iterator[Copies]:
    made = Copies()
    try:
        yield made
    finally:
        made.close()


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
            source = World.load(TEST).inventory.source(kind=DirectorySource)
            _ = init(conn, world_plan(), CASES, source, alice, giftbag=True)
        yield name


@pytest.fixture(scope="session")
def ran(copies: Copies, curated: str) -> Iterator[str]:
    with templated(copies, curated) as name:
        with psycopg.connect(settings.database(), dbname=name, autocommit=True) as conn:
            alice = People(conn).find("alice")
            assert alice is not None
            bench = Bench(conn, alice, free_world())
            for scripted in scripted_runs(TEST / RUNS):
                _ = run(bench, scripted)
        yield name


@pytest.fixture(scope="session")
def sampled(copies: Copies, migrated: str) -> Iterator[Loaded]:
    world = SAMPLE.parent
    with templated(copies, migrated) as name:
        with connect(name) as conn:
            alice = People(conn).add("alice", "Alice")
            source = World.load(world).inventory.source(kind=DirectorySource)
            plan = world_plan(world, SAMPLE)
            said = init(conn, plan, load_cases(SAMPLE), source, alice, giftbag=True)
        yield Loaded(name, said)


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

import socket
import time
from collections import defaultdict, deque
from collections.abc import Iterator
from concurrent.futures import Future, ThreadPoolExecutor
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from argon2 import PasswordHasher
from psycopg import sql

from chatddx.core import settings
from chatddx.core.rig import rig
from chatddx.curation import Plan, init, load_cases, plan_factors
from chatddx.curation.plan import SAMPLE
from chatddx.facts import BUNDLED, Facts
from chatddx.identity import identity
from chatddx.inventory import Inventory, World
from chatddx.store import People, migrate
from chatddx.store.store import Connection

WORLDS = settings.PROJECT_ROOT / "worlds"
WORLD = WORLDS / "sample"


# The markers split the tests in two: what docs/ describes, and what agents/wip-*.md plans.
def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    unsplit = [
        item.nodeid
        for item in items
        if len({"solidified", "wip"} & {m.name for m in item.iter_markers()}) != 1
    ]
    if unsplit:
        raise pytest.UsageError(
            "each test is either solidified or wip: " + ", ".join(unsplit)
        )


# The sample data's per-model records are planned for the models its World's engines serve.
def sample_plan(data: Path = SAMPLE) -> Plan:
    return plan_factors(data, Facts.load(BUNDLED), rig(), more=[WORLD / "factors.toml"])


# Passwords are hashed as cheaply as argon2 allows: the tests check what is hashed, not
# how hard it is to reverse.
@pytest.fixture(scope="session", autouse=True)
def cheap_hashing() -> Iterator[None]:
    hasher = PasswordHasher(time_cost=1, memory_cost=8, parallelism=1)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(identity, "_hasher", hasher)
        patch.setattr(identity, "_DUMMY_HASH", hasher.hash("dummy"))
        yield


# The sample World, its endpoints on ports nothing else listens on.
def free_world(tmp_path: Path) -> Inventory:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = int(s.getsockname()[1])
    text = (WORLD / "inventory.toml").read_text()
    text = text.replace('path = "vignettes"', f'path = "{WORLD / "vignettes"}"')
    path = tmp_path / "inventory.toml"
    _ = path.write_text(
        text.replace("12099", str(port)).replace("12100", str(port + 1))
    )
    return Inventory.load(path)


# Module-scoped, as tests add to its registry.
@pytest.fixture(scope="module")
def plan() -> Plan:
    return sample_plan()


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


def drop_database(admin: str, name: str) -> None:
    with psycopg.connect(admin, autocommit=True) as conn:
        _settled(conn, name)
        _ = conn.execute(
            sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name))
        )


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


@pytest.fixture(scope="session")
def migrated(copies: Copies) -> Iterator[str]:
    name = create_database(copies.admin)
    try:
        with connect(name, admin=True) as conn:
            _ = migrate(conn)
        yield name
    finally:
        copies.forget(name)
        drop_database(copies.admin, name)


# The sample as init-data lands it from the sample World: the archive's threads and
# families, shared with alice, and her giftbag of forks. Loaded once, and copied for
# each test by the packages whose `template` it is.
@pytest.fixture(scope="session")
def curated(copies: Copies, migrated: str) -> Iterator[str]:
    name = create_database(copies.admin, template=migrated)
    try:
        with connect(name) as conn:
            alice = People(conn).add("alice", "Alice")
            cases = load_cases(SAMPLE)
            source = World.load(WORLD).inventory.source("sample")
            _ = init(conn, sample_plan(), cases, source, alice, giftbag=True)
        yield name
    finally:
        copies.forget(name)
        drop_database(copies.admin, name)


# What `db` is a copy of; packages whose tests start from the sample override it with
# `curated`.
@pytest.fixture
def template(migrated: str) -> str:
    return migrated


@pytest.fixture
def db(copies: Copies, template: str) -> Iterator[str]:
    name = copies.take(template)
    try:
        yield name
    finally:
        copies.give_back(name)


# Packages whose code commits as it writes, as the runner and the bench do, override it
# with True.
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

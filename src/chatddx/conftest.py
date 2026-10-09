import time
from collections.abc import Iterator
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from psycopg import sql

from chatddx.core import settings
from chatddx.core.rig import rig
from chatddx.facts import BUNDLED, Facts
from chatddx.seed import Plan, plan_factors
from chatddx.seed.plan import SAMPLE
from chatddx.store import migrate
from chatddx.store.store import Connection

WORLDS = settings.PROJECT_ROOT / "worlds"


# The sample data's per-model records are planned for the models its World's engines serve.
def sample_plan(factors: Path = SAMPLE / "factors.toml") -> Plan:
    return plan_factors(
        factors,
        Facts.load(BUNDLED),
        rig(),
        root=SAMPLE,
        more=[WORLDS / "sample" / "factors.toml"],
    )


# A session closed a moment ago may still be ending on the server, and neither a
# template's copy nor DROP ... WITH (FORCE) waits for it: FORCE may not end a session
# of DB_USER's as DB_ADMIN.
def _settled(admin: Connection, name: str) -> None:
    for _ in range(100):
        row = admin.execute(
            "SELECT count(*) FROM pg_stat_activity WHERE datname = %s", (name,)
        ).fetchone()
        if row is None or row[0] == 0:
            return
        time.sleep(0.05)


def create_database(template: str | None = None) -> str:
    name = f"chatddx_test_{uuid4().hex[:12]}"
    create = sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name))
    if template is not None:
        create += sql.SQL(" TEMPLATE {}").format(sql.Identifier(template))
    with psycopg.connect(settings.database(admin=True), autocommit=True) as admin:
        if template is not None:
            _settled(admin, template)
        _ = admin.execute(create)
    return name


def drop_database(name: str) -> None:
    with psycopg.connect(settings.database(admin=True), autocommit=True) as admin:
        _settled(admin, name)
        _ = admin.execute(
            sql.SQL("DROP DATABASE {} WITH (FORCE)").format(sql.Identifier(name))
        )


def connect(name: str, admin: bool = False) -> Connection:
    return psycopg.connect(settings.database(admin), dbname=name)


@pytest.fixture(scope="session")
def migrated() -> Iterator[str]:
    name = create_database()
    try:
        with connect(name, admin=True) as conn:
            _ = migrate(conn)
        yield name
    finally:
        drop_database(name)


@pytest.fixture
def db(migrated: str) -> Iterator[str]:
    name = create_database(template=migrated)
    try:
        yield name
    finally:
        drop_database(name)


@pytest.fixture
def conn(db: str) -> Iterator[Connection]:
    with connect(db) as c:
        yield c


@pytest.fixture
def admin(db: str) -> Iterator[Connection]:
    with connect(db, admin=True) as c:
        yield c


@pytest.fixture
def empty_db() -> Iterator[str]:
    name = create_database()
    try:
        yield name
    finally:
        drop_database(name)


@pytest.fixture
def empty(empty_db: str) -> Iterator[Connection]:
    with connect(empty_db, admin=True) as c:
        yield c

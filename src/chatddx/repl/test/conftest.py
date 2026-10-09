import socket
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from rich.console import Console

from chatddx.bench import Bench
from chatddx.conftest import connect, create_database, drop_database, sample_plan
from chatddx.core import settings
from chatddx.facts import BUNDLED, Facts
from chatddx.fake_vllm.served import Served
from chatddx.fake_vllm.server import serving
from chatddx.inventory import Inventory, start_up
from chatddx.repl.commands import handle
from chatddx.repl.shell import Repl
from chatddx.repl.test.sample import QWEN, WORLD, Say
from chatddx.seed import load_cases, seed
from chatddx.seed.plan import SAMPLE
from chatddx.store import People
from chatddx.store.store import Connection


# The sample as init-data lands it from the sample World: the archive's threads and
# families, shared with alice, and her giftbag of forks. Seeded once, and copied for
# each test.
@pytest.fixture(scope="session")
def seeded(migrated: str) -> Iterator[str]:
    name = create_database(template=migrated)
    try:
        with connect(name) as conn:
            alice = People(conn).add("alice", "Alice")
            cases = load_cases(SAMPLE / "cases.toml")
            source = Inventory.load(WORLD).source("sample")
            _ = seed(conn, sample_plan(), cases, source, alice, giftbag=True)
        yield name
    finally:
        drop_database(name)


@pytest.fixture
def db(seeded: str) -> Iterator[str]:
    name = create_database(template=seeded)
    try:
        yield name
    finally:
        drop_database(name)


@pytest.fixture
def conn(db: str) -> Iterator[Connection]:
    with psycopg.connect(settings.database(), dbname=db, autocommit=True) as c:
        yield c


# The sample World, its endpoints on ports nothing else listens on.
@pytest.fixture
def world(tmp_path: Path) -> Inventory:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = int(s.getsockname()[1])
    text = WORLD.read_text().replace(
        'path = "vignettes"', f'path = "{WORLD.parent / "vignettes"}"'
    )
    path = tmp_path / "inventory.toml"
    _ = path.write_text(
        text.replace("12099", str(port)).replace("12100", str(port + 1))
    )
    return Inventory.load(path)


# The fake vLLM serving the Qwen endpoint's engine, as its start-up says.
@pytest.fixture
def fake(world: Inventory, bench: Bench) -> Iterator[None]:
    startup = start_up(world, bench.get, QWEN)
    with serving([Served.of(startup.argv[0], startup.argv[1:])]):
        yield


@pytest.fixture
def bench(conn: Connection, world: Inventory) -> Bench:
    alice = People(conn).find("alice")
    assert alice is not None
    return Bench(conn, alice, world, Facts.load(BUNDLED))


@pytest.fixture
def repl(bench: Bench) -> Repl:
    return Repl(bench, Console(record=True, width=200), seed=7)


@pytest.fixture
def say(repl: Repl) -> Say:
    def said(*lines: str) -> str:
        for line in lines:
            assert handle(repl, line)
        return repl.console.export_text()

    return said

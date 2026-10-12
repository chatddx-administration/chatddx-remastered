import signal
import threading
import time
from pathlib import Path

import pytest

from chatddx.cli import main
from chatddx.conftest import WORLD, WORLDS, sample_plan
from chatddx.core.rig import rig
from chatddx.curation import Plan, plan_factors
from chatddx.curation.plan import SAMPLE
from chatddx.facts import BUNDLED, Facts
from chatddx.inventory import Inventory, World, served
from chatddx.store import Store
from chatddx.store.store import Connection
from chatddx.test.world import freed

pytestmark = pytest.mark.wip


# Pinned to the sample until this package's tests move to the test World.
@pytest.fixture(scope="module")
def plan() -> Plan:
    return sample_plan()


def stored(conn: Connection, plan: Plan, inventory: Inventory) -> None:
    engines = [endpoint.engine for endpoint in inventory.endpoints.values()]
    _ = Store(conn).add(plan.registry, engines)


# Asks each endpoint what it serves once it answers, then presses Ctrl-C.
def asking(inventory: Inventory, heard: dict[str, list[str]]) -> threading.Thread:
    def ask() -> None:
        try:
            for name, endpoint in inventory.endpoints.items():
                deadline = time.monotonic() + 5
                while name not in heard and time.monotonic() < deadline:
                    try:
                        heard[name] = served(str(endpoint.url), timeout=1)
                    except OSError:
                        time.sleep(0.01)
        finally:
            main_thread = threading.main_thread().ident
            assert main_thread is not None
            signal.pthread_kill(main_thread, signal.SIGINT)

    return threading.Thread(target=ask)


def test_each_endpoint_of_the_world_is_served_its_engine_till_ctrl_c(
    db: str,
    conn: Connection,
    plan: Plan,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    world = freed(tmp_path, WORLD)
    inventory = Inventory.load(world / "inventory.toml")
    stored(conn, plan, inventory)
    monkeypatch.setenv("DB_NAME", db)
    heard: dict[str, list[str]] = {}
    asker = asking(inventory, heard)
    asker.start()

    main(["fake-engines", "--world", str(world)])

    asker.join()
    assert heard == {
        name: [endpoint.engine] for name, endpoint in inventory.endpoints.items()
    }
    out = capsys.readouterr().out
    for endpoint in inventory.endpoints.values():
        assert f"as {endpoint.engine} at {str(endpoint.url).rstrip('/')}" in out


def test_only_a_fake_s_endpoint_whose_engine_is_stored_is_served(
    db: str, conn: Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DB_NAME", db)
    sample = WORLDS / "sample"
    with pytest.raises(SystemExit, match="is not in the store"):
        main(["fake-engines", "--world", str(sample)])
    with pytest.raises(SystemExit, match="fake-engines: .*nowhere@fake"):
        main(["fake-engines", "--world", str(sample), "nowhere@fake"])

    kompismoln = World.load(WORLDS / "kompismoln")
    facts = Facts.load(BUNDLED, *kompismoln.facts)
    planned = plan_factors(SAMPLE, facts, rig(), more=kompismoln.factors)
    stored(conn, planned, kompismoln.inventory)
    with pytest.raises(SystemExit, match="'qwen3-8b@pelle' runs in /nix/store/"):
        main(["fake-engines", "--world", str(kompismoln.path)])

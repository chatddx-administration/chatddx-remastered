import signal
import threading
import time
from pathlib import Path

import pytest

from chatddx.cli import main
from chatddx.curation import Plan
from chatddx.fake_vllm.served import CLOSURE
from chatddx.inventory import Inventory, World, served
from chatddx.store import Store
from chatddx.store.store import Connection
from chatddx.test.world import (
    GPT_OSS,
    MISTRAL,
    QWEN,
    QWEN_BARE,
    REMOTE,
    TEST,
    copied,
    edit,
    freed,
    world_plan,
)

pytestmark = pytest.mark.wip

FAKES = [QWEN, QWEN_BARE, GPT_OSS, MISTRAL]
NIX = "/nix/store/" + "0" * 32 + "-vllm"
MISTRAL_RUNTIME = """model = "mistral-7b"
hardware = { gpu = "none", compute_capability = [0, 0], vram_mib = 0, driver = "none" }
runtime = { version = "0.24.0+fake", closure = "chatddx fake-vllm" }"""


def stored(conn: Connection, plan: Plan, inventory: Inventory) -> None:
    engines = [endpoint.engine for endpoint in inventory.endpoints.values()]
    _ = Store(conn).add(plan.registry, engines)


# Asks each endpoint what it serves once it answers, then presses Ctrl-C.
def asking(
    inventory: Inventory, names: list[str], heard: dict[str, list[str]]
) -> threading.Thread:
    def ask() -> None:
        try:
            for name in names:
                endpoint = inventory.endpoint(name)
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
    world = freed(tmp_path)
    inventory = Inventory.load(world / "inventory.toml")
    stored(conn, plan, inventory)
    monkeypatch.setenv("DB_NAME", db)
    heard: dict[str, list[str]] = {}
    asker = asking(inventory, FAKES, heard)
    asker.start()

    main(["fake-engines", "--world", str(world), *FAKES])

    asker.join()
    assert heard == {name: [inventory.endpoint(name).engine] for name in FAKES}
    out = capsys.readouterr().out
    for name in FAKES:
        endpoint = inventory.endpoint(name)
        assert f"as {endpoint.engine} at {str(endpoint.url).rstrip('/')}" in out


def test_only_a_fake_s_endpoint_whose_engine_is_stored_is_served(
    db: str,
    conn: Connection,
    plan: Plan,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DB_NAME", db)
    with pytest.raises(SystemExit, match="is not in the store"):
        main(["fake-engines", "--world", str(TEST)])
    with pytest.raises(SystemExit, match="fake-engines: .*nowhere@fake"):
        main(["fake-engines", "--world", str(TEST), "nowhere@fake"])

    stored(conn, plan, World.load(TEST).inventory)
    with pytest.raises(SystemExit, match=f"{REMOTE!r} serves a .*not ours to start"):
        main(["fake-engines", "--world", str(TEST)])

    real = copied(tmp_path)
    edit(real / "factors.toml", MISTRAL_RUNTIME, MISTRAL_RUNTIME.replace(CLOSURE, NIX))
    was = World.load(TEST).inventory.endpoint(MISTRAL).engine
    planned = world_plan(real, real / "_data")
    edit(real / "endpoints.toml", was, planned.named("local_engine", MISTRAL).digest)
    stored(conn, planned, World.load(real).inventory)
    with pytest.raises(SystemExit, match=f"{MISTRAL!r} runs in {NIX}, not the fake"):
        main(["fake-engines", "--world", str(real), MISTRAL])

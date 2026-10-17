import shutil
import socket
from collections.abc import Generator
from contextlib import ExitStack, contextmanager
from pathlib import Path

from pydantic import HttpUrl

from chatddx import settings
from chatddx.curation import Plan, load_cases, plan_factors
from chatddx.factors.base import Resolver
from chatddx.facts import BUNDLED, Facts
from chatddx.fake_vllm.served import Served
from chatddx.fake_vllm.server import serving
from chatddx.inventory import Inventory, World, start_up
from chatddx.rig import rig

WORLDS = settings.PROJECT_ROOT / "worlds"
TEST = WORLDS / "test"
DATA = TEST / "_data"
SAMPLE = WORLDS / "sample" / "_data"
CASES = load_cases(DATA)

QWEN_MODEL = "Qwen/Qwen3-8B-AWQ"
GPT_OSS_MODEL = "openai/gpt-oss-20b"
MISTRAL_MODEL = "test/mistral-7b"
MODELS = (QWEN_MODEL, GPT_OSS_MODEL, MISTRAL_MODEL)

QWEN_ARTIFACT = "qwen3-8b-awq"
GPT_OSS_ARTIFACT = "gpt-oss-20b"
MISTRAL_ARTIFACT = "mistral-7b"
UNKNOWN_MODEL = "unknown"

QWEN = "qwen3@fake"
QWEN_BARE = "qwen3-bare@fake"
GPT_OSS = "gpt-oss@fake"
MISTRAL = "mistral@fake"
REMOTE = "unknown@remote"

LINES = "lines"
NATIVE = "native"
NATIVE_TOOLS = "native-tools"
TOOL_ANSWER = "tool-answer"
OFF = "off"
LINES_GUIDED = "lines-guided"
JUDGE = "judge"
CLINICIAN = "clinician"

# What loading the test World lints: the factors' lints, then the facts'.
FACTOR_LINTS = [
    *(
        f"[lint warning] model.local {name}: model.revision: revision 'fake' is not a "
        + "commit and can move"
        for name in ("qwen3-8b-awq", "gpt-oss-20b", "mistral-7b")
    ),
    *(
        f"[lint warning] engine.local {name}: engine.closure: closure 'chatddx "
        + "fake-vllm' is not a Nix store path"
        for name in (QWEN, QWEN_BARE, GPT_OSS, MISTRAL)
    ),
]
FACT_LINTS = [
    "[lint info] judge remote: facts.missing: no facts about 'test/unknown', so "
    + "model-level checks were skipped",
]
LINTS = [*FACTOR_LINTS, *FACT_LINTS]


def world_facts(world: Path = TEST) -> Facts:
    return Facts.load(BUNDLED, *World.load(world).facts)


def world_plan(world: Path = TEST, data: Path = DATA) -> Plan:
    return plan_factors(data, world_facts(world), rig(), World.load(world))


def free_ports(n: int) -> list[int]:
    with ExitStack() as stack:
        sockets = [stack.enter_context(socket.socket()) for _ in range(n)]
        for s in sockets:
            s.bind(("127.0.0.1", 0))
        return [int(s.getsockname()[1]) for s in sockets]


def _freed(inventory: Inventory) -> dict[str, HttpUrl]:
    ports = free_ports(len(inventory.endpoints))
    return {
        name: HttpUrl(f"http://127.0.0.1:{port}/v1/")
        for name, port in zip(inventory.endpoints, ports, strict=True)
    }


def free_world(world: Path = TEST) -> Inventory:
    inventory = Inventory.load(world / "inventory.toml")
    endpoints = dict(inventory.endpoints)
    for name, url in _freed(inventory).items():
        endpoints[name] = endpoints[name].model_copy(update={"url": url})
    return inventory.model_copy(update={"endpoints": endpoints})


# For the commands, which read a World from its directory.
def freed(to: Path, world: Path = TEST) -> Path:
    copy = copied(to, world)
    inventory = Inventory.load(world / "inventory.toml")
    for name, url in _freed(inventory).items():
        was = f'url = "{inventory.endpoint(name).url}"'
        for path in copy.glob("*.toml"):
            if was in (text := path.read_text()):
                _ = path.write_text(text.replace(was, f'url = "{url}"'))
    return copy


@contextmanager
def faked(
    world: Inventory, get: Resolver, endpoint: str = QWEN, delay: float = 0.0
) -> Generator[None]:
    startup = start_up(world, get, endpoint)
    with serving([Served.of(startup.argv[0], startup.argv[1:])], delay=delay):
        yield


def copied(to: Path, world: Path = TEST) -> Path:
    return shutil.copytree(world, to / world.name)


def edit(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    assert old in text, f"{path} doesn't hold {old!r}"
    _ = path.write_text(text.replace(old, new))

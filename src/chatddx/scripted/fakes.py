import os
import socket
from collections.abc import Sequence

from pydantic import HttpUrl

from chatddx.factors.base import Resolver, StructuralError
from chatddx.factors.engine import RemoteEngine, served_model_name
from chatddx.fake_vllm.served import CLOSURE, Refused, Served
from chatddx.inventory import Inventory, start_up


def fake_at(inventory: Inventory, get: Resolver, name: str) -> Served:
    try:
        engine = get(inventory.endpoint(name).engine)
    except StructuralError as e:
        raise LookupError(str(e)) from None
    if isinstance(engine, RemoteEngine):
        return _stand_in(inventory, get, engine, name)
    startup = start_up(inventory, get, name)
    if startup.closure != CLOSURE:
        raise LookupError(
            f"endpoint {name!r} runs in {startup.closure}, not the fake vLLM"
        )
    try:
        return Served.of(startup.argv[0], startup.argv[1:])
    except Refused as e:
        raise LookupError(f"{name} won't start: {e}") from None


# Accommodating for a hosted API, which parses tool calls, as the fake does under any
# parser.
def _stand_in(
    inventory: Inventory, get: Resolver, engine: RemoteEngine, name: str
) -> Served:
    spec = inventory.endpoint(name)
    if spec.url.host not in ("127.0.0.1", "localhost"):
        raise LookupError(f"endpoint {name!r} isn't on this machine")
    argv = ["--host", spec.url.host, "--port", str(spec.url.port)]
    argv += ["--enable-auto-tool-choice", "--tool-call-parser", "openai"]
    if spec.credential is not None:
        key = os.environ.get(spec.credential)
        if not key:
            raise LookupError(
                f"endpoint {name!r} asks for the key in {spec.credential}, which "
                + "isn't set"
            )
        argv += ["--api-key", key]
    return Served.of(served_model_name(engine.digest, get), argv)


# Policy: an endpoint whose engine the fake vLLM doesn't run is stood in for by one on a
# free port of this machine, named and parsing as the engine's own start-up has it, for
# runs that only need to be recorded as the engine's.
def standing_in(
    inventory: Inventory, get: Resolver
) -> tuple[Inventory, dict[str, Served], dict[str, str]]:
    """The inventory with each endpoint but those the fake vLLM serves as they are moved
    to a free port of this machine, the fakes that serve them all, and why each endpoint
    neither can be served is left out. Binds a socket for each port it takes."""
    endpoints = dict(inventory.endpoints)
    served: dict[str, Served] = {}
    refused: dict[str, str] = {}
    for name, spec in inventory.endpoints.items():
        try:
            served[name] = fake_at(inventory, get, name)
            continue
        except LookupError as e:
            why = str(e)
        try:
            startup = start_up(inventory, get, name)
            port = _free_port()
            argv = [*_without(startup.argv[1:], ("--host", "--port"))]
            argv += ["--host", "127.0.0.1", "--port", str(port)]
            served[name] = Served.of(startup.argv[0], argv)
        except (LookupError, Refused) as e:
            refused[name] = f"{why}; {e}"
            continue
        url = HttpUrl(f"http://127.0.0.1:{port}/v1/")
        endpoints[name] = spec.model_copy(update={"url": url})
    return inventory.model_copy(update={"endpoints": endpoints}), served, refused


def _without(argv: Sequence[str], names: tuple[str, ...]) -> list[str]:
    kept: list[str] = []
    skipping = False
    for arg in argv:
        if skipping:
            skipping = False
            continue
        if arg in names:
            skipping = True
            continue
        if arg.partition("=")[0] not in names:
            kept.append(arg)
    return kept


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])

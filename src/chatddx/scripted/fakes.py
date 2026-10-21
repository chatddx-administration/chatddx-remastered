import os

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

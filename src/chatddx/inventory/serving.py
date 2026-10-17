from chatddx.factors.base import (
    Digest,
    Frozen,
    Resolver,
    StructuralError,
    resolve,
)
from chatddx.factors.engine import LocalEngine, LocalModel, served_model_name

from .inventory import Inventory


class StartUp(Frozen):
    endpoint: str
    engine: Digest
    closure: str
    argv: tuple[str, ...]
    env: dict[str, str]


def start_up(inventory: Inventory, get: Resolver, name: str) -> StartUp:
    endpoint = inventory.endpoint(name)
    try:
        match get(endpoint.engine):
            case LocalEngine() as engine:
                revision = resolve(get, engine.model, LocalModel).revision
            case other:
                raise LookupError(
                    f"endpoint {name!r} serves a {other.kind_name}, not ours to start"
                )
    except StructuralError as e:
        raise LookupError(f"endpoint {name!r}: {e}") from None
    if endpoint.host is None:
        raise LookupError(f"endpoint {name!r} needs a host to start")
    host = inventory.hosts[endpoint.host]
    model = host.models.get(engine.model)
    if model is None:
        raise LookupError(
            f"host {endpoint.host!r} doesn't say where it keeps model {engine.model}"
        )
    template = host.templates.get(engine.chat_template)
    if template is None:
        raise LookupError(
            f"host {endpoint.host!r} doesn't say where it keeps chat template "
            + engine.chat_template
        )
    return StartUp(
        endpoint=name,
        engine=engine.digest,
        closure=engine.runtime.closure,
        argv=(
            model,
            "--revision",
            revision,
            "--served-model-name",
            served_model_name(engine.digest, get),
            "--chat-template",
            template,
            "--host",
            host.bind,
            "--port",
            str(endpoint.url.port),
            *engine.argv,
        ),
        env=engine.env,
    )

from collections.abc import Iterable

from chatddx.factors.base import Component, Finding, Resolver, StructuralError
from chatddx.factors.engine import LocalEngine, RemoteEngine

from .inventory import Inventory
from .serving import start_up


def _engine(
    get: Resolver, name: str, digest: str
) -> LocalEngine | RemoteEngine | Finding:
    try:
        engine = get(digest)
    except StructuralError as e:
        return Finding(code="endpoint.engine_unknown", message=str(e), subject=name)
    if not isinstance(engine, (LocalEngine, RemoteEngine)):
        return Finding(
            code="endpoint.not_engine",
            message=f"{digest} is a {engine.kind_name}, not an engine",
            subject=name,
        )
    return engine


def _endpoint(
    inventory: Inventory, get: Resolver, name: str, engine: Component
) -> Iterable[Finding]:
    match engine:
        case LocalEngine():
            try:
                _ = start_up(inventory, get, name)
            except LookupError as e:
                yield Finding(code="endpoint.unstartable", message=str(e), subject=name)
        case _:
            if (host := inventory.endpoint(name).host) is not None:
                yield Finding(
                    code="endpoint.remote_host",
                    message="it serves a remote engine, which no host of ours runs, but names "
                    + f"host {host!r}",
                    subject=name,
                )


# Policy: Checked as a process starts and before the World changes, as
# src/chatddx/bench/seen.py:Seen.served relies on it.
def broken(inventory: Inventory, get: Resolver) -> list[str]:
    serving: dict[str, list[str]] = {}
    for name, endpoint in inventory.endpoints.items():
        if not isinstance(engine := _engine(get, name, endpoint.engine), Finding):
            serving.setdefault(engine.model, []).append(name)
    return [
        f"endpoints {', '.join(sorted(names))} serve the same weights, which one "
        + "endpoint should"
        for names in serving.values()
        if len(names) > 1
    ]


def check(inventory: Inventory, get: Resolver) -> list[Finding]:
    findings: list[Finding] = []
    local: dict[str, LocalEngine] = {}
    for name, endpoint in inventory.endpoints.items():
        match _engine(get, name, endpoint.engine):
            case Finding() as f:
                findings.append(f)
            case engine:
                findings.extend(_endpoint(inventory, get, name, engine))
                if isinstance(engine, LocalEngine):
                    local[name] = engine

    at: dict[str, list[str]] = {}
    for name in local:
        at.setdefault(str(inventory.endpoint(name).url), []).append(name)
    for url, names in at.items():
        for name in names[1:]:
            findings.append(
                Finding(
                    code="endpoint.shared_url",
                    message=f"{url} is also the address of endpoint {names[0]!r}",
                    subject=name,
                )
            )

    for host_name, host in inventory.hosts.items():
        engines = [
            e for n, e in local.items() if inventory.endpoint(n).host == host_name
        ]
        models = set(host.models) - {e.model for e in engines}
        templates = set(host.templates) - {e.chat_template for e in engines}
        for what, unpinned in (("model", models), ("chat template", templates)):
            for key in sorted(unpinned):
                findings.append(
                    Finding(
                        level="info",
                        code="host.unpinned",
                        message=f"it says where it keeps {what} {key}, which none of "
                        + "its endpoints' engines pins",
                        subject=host_name,
                    )
                )

    for name, sources in inventory.cleared.items():
        for source in sources:
            if not inventory.source(source).sensitive:
                findings.append(
                    Finding(
                        level="info",
                        code="cleared.not_sensitive",
                        message=f"it is cleared for source {source!r}, which isn't "
                        + "sensitive and needs no clearance",
                        subject=name,
                    )
                )
    return findings

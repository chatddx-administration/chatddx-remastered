import json
import shlex
from dataclasses import dataclass

from fastapi import APIRouter, Request, Response

from chatddx.api import schemas, world as api
from chatddx.bench import Bench
from chatddx.catalog import About
from chatddx.factors.base import resolve
from chatddx.factors.engine import LocalEngine, Model, RemoteEngine, model_of
from chatddx.factors.facts import (
    LEVELS,
    ModelFacts,
    Refusal,
    SamplingValues,
    Writes,
)
from chatddx.inventory import DirectorySource, EndpointSpec, Inventory, Source, World
from chatddx.rig import rig

from .pages import BenchDep, page

router = APIRouter()


@dataclass(frozen=True)
class _Sourced:
    source: Source
    vignettes: int | None
    unread: str | None
    cleared: list[str]


@dataclass(frozen=True)
class Served:
    endpoint: schemas.Endpoint
    spec: EndpointSpec
    engine: int | None
    canaries: str | None


@dataclass(frozen=True)
class _Pinned:
    name: str
    thread: int
    about: About
    engine: LocalEngine | RemoteEngine
    weights: Model
    endpoint: str | None
    host: str | None
    template: str | None
    argv: str


@dataclass(frozen=True)
class _Held:
    name: str
    thread: int
    weights: Model
    endpoint: str | None
    host: str | None
    engine: _Pinned | None
    facts: int | None


@dataclass(frozen=True)
class _Said:
    name: str
    default: bool = False
    writes: str | None = None
    like: str | None = None
    refused: str | None = None
    nearest: str | None = None
    note: str | None = None


@dataclass(frozen=True)
class _Known:
    thread: int
    facts: ModelFacts
    handles: list[_Held]
    reasoning: list[_Said]
    sampled: list[str]
    sampling: list[tuple[str, dict[str, object]]]
    output: list[_Said]


@router.get("/world")
def world(request: Request, bench: BenchDep) -> Response:
    held = request.app.state.world
    assert isinstance(held, World)
    inventory = bench.inventory
    pinned = _pinned(bench)
    found = sorted(
        (
            (e.thread, resolve(bench.store.get, e.digest, ModelFacts))
            for e, _ in bench.threads("facts")
        ),
        key=lambda f: f[0],
    )
    handles = _handles(
        bench,
        {p.engine.digest: p for p in pinned},
        {f.model: t for t, f in found},
    )
    weighed = {h.weights.digest: h for h in handles}
    hosts = sorted(inventory.hosts.items())
    return page(
        request,
        "world.html",
        person=bench.person,
        world=held,
        files=[held.path / "inventory.toml", *held.engines, *held.facts],
        rig=rig(),
        handles=handles,
        known=sorted(
            (_known(t, f, handles) for t, f in found),
            key=lambda k: (not k.handles, k.facts.model),
        ),
        engines=pinned,
        endpoints=[_served(bench, inventory, e) for e in api.endpoints(bench)],
        serving={h.endpoint: h for h in handles if h.endpoint is not None},
        named={h.name: h for h in handles},
        hosts=hosts,
        weighed=weighed,
        pinning={
            sha: [p for p in pinned if _template(p.engine) == sha]
            for _, h in hosts
            for sha in h.templates
        },
        titles={d: bench.title(d) for _, h in hosts for d in h.models},
        sources=[_sourced(inventory, s) for _, s in sorted(inventory.sources.items())],
        judges=sorted(inventory.judges.items()),
        configurations=inventory.configurations,
    )


def _handles(
    bench: Bench, engines: dict[str, _Pinned], facts: dict[str, int]
) -> list[_Held]:
    found: list[_Held] = []
    for handle, at in bench.handles():
        weights = model_of(handle.weights, bench.store.get)
        found.append(
            _Held(
                handle.name,
                handle.thread,
                weights,
                None if at is None else at.name,
                None if at is None else at.spec.host,
                None if at is None else engines.get(at.engine),
                facts.get(weights.name),
            )
        )
    return sorted(found, key=lambda h: h.endpoint is None)


def _pinned(bench: Bench) -> list[_Pinned]:
    endpoints = sorted(bench.inventory.endpoints.items())
    found: list[_Pinned] = []
    for edit, about in bench.threads("engine"):
        engine = bench.store.get(edit.digest)
        assert isinstance(engine, LocalEngine | RemoteEngine)
        weights = model_of(edit.digest, bench.store.get)
        at = next(((n, s) for n, s in endpoints if s.engine == edit.digest), None)
        host = None if at is None else at[1].host
        sha = _template(engine)
        found.append(
            _Pinned(
                about.name or str(edit.thread),
                edit.thread,
                about,
                engine,
                weights,
                None if at is None else at[0],
                host,
                None
                if host is None or sha is None
                else bench.inventory.hosts[host].templates.get(sha),
                shlex.join(engine.argv) if isinstance(engine, LocalEngine) else "",
            )
        )
    return sorted(found, key=lambda p: (p.endpoint is None, p.name))


def _template(engine: LocalEngine | RemoteEngine) -> str | None:
    return engine.chat_template if isinstance(engine, LocalEngine) else None


def _known(thread: int, facts: ModelFacts, handles: list[_Held]) -> _Known:
    rows = [
        (level, values)
        for level in LEVELS
        if (values := _values(facts.sampling.recommended.get(level)))
    ]
    if given := _values(facts.sampling.generation_config):
        rows.append(("generation_config", given))
    return _Known(
        thread,
        facts,
        [h for h in handles if h.facts == thread],
        _reasoning(facts),
        [k for k in SamplingValues.model_fields if any(k in v for _, v in rows)],
        rows,
        _output(facts),
    )


def _values(values: SamplingValues | None) -> dict[str, object]:
    return {} if values is None else values.model_dump(exclude_none=True)


def _reasoning(facts: ModelFacts) -> list[_Said]:
    reasoning = facts.reasoning
    said: list[_Said] = []
    for level in LEVELS:
        match reasoning.fact(level):
            case None:
                continue
            case Refusal(refused=refused, nearest=nearest):
                said.append(
                    _Said(
                        level,
                        reasoning.default == level,
                        refused=refused,
                        nearest=nearest,
                    )
                )
            case Writes() as writes:
                said.append(
                    _Said(level, reasoning.default == level, writes=_sent(writes))
                )
            case other:
                said.append(_Said(level, reasoning.default == level, like=other))
    match reasoning.budget:
        case None:
            pass
        case Refusal(refused=refused):
            said.append(_Said("budget", refused=refused))
        case sent:
            said.append(_Said("budget", writes=sent))
    return said


# Dependency: what src/chatddx/factors/request.py:compile_request sends of a level's
# writes.
def _sent(writes: Writes) -> str:
    sent: dict[str, object] = {}
    if writes.effort is not None:
        sent["reasoning_effort"] = writes.effort
    if writes.chat_template_kwargs:
        sent["chat_template_kwargs"] = writes.chat_template_kwargs
    return json.dumps(sent, ensure_ascii=False) if sent else ""


def _output(facts: ModelFacts) -> list[_Said]:
    output = facts.output
    said: list[_Said] = []
    for contract, fact in (
        ("native", output.native),
        ("tool", output.tool),
        ("text", output.text),
    ):
        match fact:
            case None:
                continue
            case Refusal(refused=refused):
                said.append(
                    _Said(contract, output.default == contract, refused=refused)
                )
            case _:
                said.append(_Said(contract, output.default == contract, note=fact.note))
    return said


def _sourced(inventory: Inventory, source: Source) -> _Sourced:
    cleared = sorted(e for e, held in inventory.cleared.items() if source.name in held)
    if not isinstance(source, DirectorySource):
        return _Sourced(source, None, None, cleared)
    try:
        return _Sourced(source, len(source.ids()), None, cleared)
    except OSError as e:
        return _Sourced(source, None, str(e), cleared)


def _served(bench: Bench, inventory: Inventory, endpoint: schemas.Endpoint) -> Served:
    spec = inventory.endpoints[endpoint.name]
    held = bench.holder(endpoint.engine)
    return Served(
        endpoint,
        spec,
        None if held is None else held[0].thread,
        None if spec.canaries is None else bench.title(spec.canaries),
    )

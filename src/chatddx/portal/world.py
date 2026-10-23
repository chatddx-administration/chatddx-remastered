from dataclasses import dataclass

from fastapi import APIRouter, Request, Response

from chatddx.api import schemas, world as api
from chatddx.bench import Bench
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


@router.get("/world")
def world(request: Request, bench: BenchDep) -> Response:
    held = request.app.state.world
    assert isinstance(held, World)
    inventory = held.inventory
    hosts = sorted(inventory.hosts.items())
    return page(
        request,
        "world.html",
        person=bench.person,
        world=held,
        files=[held.path / "inventory.toml", *held.engines, *held.facts],
        rig=rig(),
        sources=[_sourced(inventory, s) for _, s in sorted(inventory.sources.items())],
        endpoints=[_served(bench, inventory, e) for e in api.endpoints(bench)],
        hosts=hosts,
        titles={d: bench.title(d) for _, h in hosts for d in h.models},
        judges=sorted(inventory.judges.items()),
        configurations=inventory.configurations,
        models=api.models(bench),
    )


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

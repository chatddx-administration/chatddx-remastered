from pathlib import Path

import pytest

from chatddx.curation import Plan
from chatddx.curation.plan import SAMPLE
from chatddx.factors.engine import LocalEngine
from chatddx.inventory import World, check, start_up
from chatddx.test.world import DATA, WORLDS, world_plan

pytestmark = pytest.mark.wip

DATA_SETS = {"test": DATA, "sample": SAMPLE, "kompismoln": SAMPLE}


@pytest.fixture(scope="module", params=sorted(DATA_SETS))
def each(request: pytest.FixtureRequest) -> tuple[World, Plan]:
    name = str(request.param)
    world: Path = WORLDS / name
    return World.load(world), world_plan(world, DATA_SETS[name])


def test_every_world_in_the_repository_is_checked() -> None:
    assert sorted(p.name for p in WORLDS.iterdir() if p.is_dir()) == sorted(DATA_SETS)


def test_each_endpoint_serves_the_engine_planned_under_its_name(
    each: tuple[World, Plan],
) -> None:
    world, plan = each
    engines = {r.name: r for r in plan.records if r.table.endswith("engine")}
    for name, endpoint in world.inventory.endpoints.items():
        engine = engines[name].digest
        assert endpoint.engine == engine, f"endpoint {name!r} serves {engine}"
        if isinstance(plan.registry.get(engine), LocalEngine):
            _ = start_up(world.inventory, plan.registry.get, name)
    assert check(world.inventory, plan.registry.get) == []

import json
from pathlib import Path

import pytest
from jsonschema.validators import validator_for

from chatddx.curation import Plan
from chatddx.curation.plan import SAMPLE
from chatddx.factors.base import resolve
from chatddx.factors.engine import LocalEngine
from chatddx.factors.lint import lint
from chatddx.factors.request import (
    SLOTS_BY_PURPOSE,
    Skeleton,
    SlotName,
    render,
    tool_calls,
)
from chatddx.factors.trial import Trial
from chatddx.fake_vllm.chat import Failure, accept, completion, instance, respond
from chatddx.fake_vllm.served import CLOSURE, Served
from chatddx.inventory import World, check, start_up
from chatddx.scorers.answer import read
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


# The lint says harmony and Mistral models take tools unconstrained where vLLM refuses others.
UNCONSTRAINED = ("harmony", "mistral")
FILLS: dict[SlotName, str] = {
    "vignette": "A 72-year-old man.",
    "appendices": "",
    "completion": "Sepsis",
    "expectation": '{"diagnosis": {"pattern": "sepsis"}}',
}


def test_each_fake_answers_each_skeleton_or_refuses_it_as_vllm_would(
    each: tuple[World, Plan],
) -> None:
    world, plan = each
    case = plan.registry.add(world.inventory.listing().cases()[0])
    fakes: dict[str, Served] = {}
    for name, endpoint in world.inventory.endpoints.items():
        engine = plan.registry.get(endpoint.engine)
        if isinstance(engine, LocalEngine) and engine.runtime.closure == CLOSURE:
            startup = start_up(world.inventory, plan.registry.get, name)
            fakes[endpoint.engine] = Served.of(startup.argv[0], startup.argv[1:])
    engines = list(fakes.values())
    for r in plan.records:
        if r.kind != "skeleton":
            continue
        skeleton = resolve(plan.registry.get, r.digest, Skeleton)
        fills: dict[SlotName, str] = {
            slot: FILLS[slot] for slot in SLOTS_BY_PURPOSE[skeleton.purpose]
        }
        for engine, served in fakes.items():
            pair = f"{r.name} on {served.model}"
            trial = Trial(skeleton=r.digest, engine=engine, cases=(case,), seeds=(7,))
            codes = {f.code for f in lint(plan.registry, [plan.registry.add(trial)])}
            request = render(skeleton, model=served.name, seed=7, fills=fills)
            if "vllm.thinking_budget_refused" in codes or (
                "vllm.tools_refused" in codes and served.family not in UNCONSTRAINED
            ):
                with pytest.raises(Failure):
                    _ = respond(accept(engines, request), request)
                continue
            response = completion(
                served, request, respond(accept(engines, request), request)
            )
            assert response["prompt_token_ids"], pair
            if "vllm.tools_refused" in codes or (
                skeleton.tools and tool_calls(response)
            ):
                continue
            answer = read(skeleton, response)
            assert (answer.problem, answer.value is None) == (None, False), pair


@pytest.mark.parametrize(
    "path",
    sorted({p for data in DATA_SETS.values() for p in data.glob("schemas/*.json")}),
    ids=lambda p: f"{p.parent.parent.name}/{p.stem}",
)
def test_what_the_fake_writes_holds_to_each_data_set_s_schemas(path: Path) -> None:
    schema = json.loads(path.read_text())
    assert not list(validator_for(schema)(schema).iter_errors(instance(schema)))

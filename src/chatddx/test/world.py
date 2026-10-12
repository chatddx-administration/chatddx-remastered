from pathlib import Path

from chatddx.core import settings
from chatddx.core.rig import rig
from chatddx.curation import Plan, plan_factors
from chatddx.facts import BUNDLED, Facts
from chatddx.inventory import World

WORLDS = settings.PROJECT_ROOT / "worlds"
TEST = WORLDS / "test"
DATA = TEST / "_data"


def world_plan(world: Path = TEST, data: Path = DATA) -> Plan:
    loaded = World.load(world)
    facts = Facts.load(BUNDLED, *loaded.facts)
    return plan_factors(data, facts, rig(), more=list(loaded.factors))

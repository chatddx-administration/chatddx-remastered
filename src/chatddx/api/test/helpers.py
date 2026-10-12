from chatddx.facts import BUNDLED, Facts
from chatddx.inventory import World
from chatddx.test.world import QWEN_MODEL, TEST

OFF = f"off ({QWEN_MODEL})"


def world_facts() -> Facts:
    return Facts.load(BUNDLED, *World.load(TEST).facts)

from collections.abc import Mapping

from chatddx.curation import DataCase
from chatddx.inventory.test.memory import MemorySource
from chatddx.test.world import CASES

__all__ = ["CASES", "appended", "vignettes"]


def vignettes(**changed: bytes) -> MemorySource:
    texts = {id: f"The vignette of {id}.".encode() for id in CASES}
    return MemorySource(name="test", vignettes={**texts, **changed})


# What loading the cases lands beside each case and its expectation: the appendices, the
# cases that send them, and those cases' expectations.
def appended(cases: Mapping[str, DataCase]) -> tuple[int, int, int]:
    return (
        sum(len(c.appendices) for c in cases.values()),
        sum(len(c.ordered) for c in cases.values()),
        sum(o.targets is not None for c in cases.values() for o in c.ordered),
    )

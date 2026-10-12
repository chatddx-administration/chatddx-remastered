from chatddx.inventory.test.memory import MemorySource
from chatddx.test.world import CASES

__all__ = ["CASES", "vignettes"]


def vignettes(**changed: bytes) -> MemorySource:
    texts = {id: f"The vignette of {id}.".encode() for id in CASES}
    return MemorySource(name="test", vignettes={**texts, **changed})

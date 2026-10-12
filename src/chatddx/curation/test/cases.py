from chatddx.curation import load_cases
from chatddx.inventory.test.memory import MemorySource
from chatddx.test.world import DATA

CASES = load_cases(DATA)


def vignettes(**changed: bytes) -> MemorySource:
    texts = {id: f"The vignette of {id}.".encode() for id in CASES}
    return MemorySource(name="test", vignettes={**texts, **changed})

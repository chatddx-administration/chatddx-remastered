from chatddx.curation import load_cases
from chatddx.curation.plan import SAMPLE
from chatddx.inventory.test.memory import MemorySource

CASES = load_cases(SAMPLE)
# What the tests of init-data's mechanics load, so they're quick; only
# test_init_data_loads_the_archive loads every case.
FEW = ("DutchFall10w", "Dutchfall11w", "casesfromedn1")
SOME = {id: CASES[id] for id in FEW}


def vignettes(**changed: bytes) -> MemorySource:
    texts = {id: f"The vignette of {id}.".encode() for id in CASES}
    return MemorySource(name="sample", vignettes={**texts, **changed})

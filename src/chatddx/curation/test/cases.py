import tempfile
from collections.abc import Mapping
from pathlib import Path

from chatddx.curation import DataCase
from chatddx.inventory import DirectorySource
from chatddx.test.world import CASES

__all__ = ["CASES", "TEXTS", "appended", "vignettes"]

TEXTS = {id: f"The vignette of {id}.".encode() for id in CASES}

_AT = tempfile.TemporaryDirectory(prefix="chatddx-vignettes-")


def vignettes(texts: Mapping[str, bytes] = TEXTS, **changed: bytes) -> DirectorySource:
    path = Path(tempfile.mkdtemp(dir=_AT.name))
    for id, text in {**texts, **changed}.items():
        _ = (path / f"{id}.txt").write_bytes(text)
    return DirectorySource(name="test", path=path)


# What loading the cases lands beside each case and its expectation: the appendices, the
# cases that send them, and those cases' expectations.
def appended(cases: Mapping[str, DataCase]) -> tuple[int, int, int]:
    return (
        sum(len(c.appendices) for c in cases.values()),
        sum(len(c.ordered) for c in cases.values()),
        sum(o.targets is not None for c in cases.values() for o in c.ordered),
    )

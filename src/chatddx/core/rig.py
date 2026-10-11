import os
from collections.abc import Mapping
from importlib import metadata
from typing import Protocol

from chatddx.factors.base import Code


def rig() -> Code:
    return Code(
        distribution="chatddx",
        version=metadata.version("chatddx"),
        revision=os.environ.get("CHATDDX_REVISION") or None,
    )


class Versioned(Protocol):
    @property
    def version(self) -> int: ...


def entry[T: Versioned](shipped: Mapping[str, T], entry_point: str, version: int) -> T:
    found = shipped.get(entry_point)
    running = _shown(rig())
    if found is None:
        raise LookupError(
            f"{entry_point} isn't shipped with {running}, only "
            + (", ".join(sorted(shipped)) or "nothing")
        )
    if found.version != version:
        raise LookupError(
            f"{entry_point} is at version {found.version} in {running}, not {version}"
        )
    return found


def _shown(code: Code) -> str:
    at = "" if code.revision is None else f" at {code.revision}"
    return f"{code.distribution} {code.version}{at}"

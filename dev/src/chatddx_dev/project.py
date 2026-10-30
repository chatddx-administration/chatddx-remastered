import os
import tomllib
from dataclasses import dataclass
from enum import IntEnum, StrEnum
from pathlib import Path

from chatddx.settings import PROJECT_ROOT

__all__ = ["PROJECT_ROOT"]

# Policy: where each package's top-level modules are, from the repository's root.
PACKAGES = {Path("src/chatddx"): "chatddx", Path("dev/src/chatddx_dev"): "chatddx_dev"}


class Stage(IntEnum):
    FELT = 1
    IMPLIED = 2
    MENTIONED = 3
    NAMED = 4
    ITEMIZED = 5
    PLANNED = 6
    DRAFTED = 7
    SOLIDIFIED = 8
    CEMENTED = 9
    PROTECTED = 10


class Class(StrEnum):
    DATAMODEL = "datamodel"
    UX = "ux"
    MACHINERY = "machinery"


@dataclass(frozen=True)
class Part:
    stage: Stage
    class_: Class
    doc: str | None
    code: tuple[str, ...]


_HELD = tomllib.loads((PROJECT_ROOT / "settings.toml").read_text())

PARTS = {
    name: Part(
        Stage[held["stage"].upper()],
        Class(held["class"]),
        held.get("doc"),
        tuple(held["code"]),
    )
    for name, held in _HELD["parts"].items()
}
STAMPED_FROM = {
    name: Stage[stage.upper()] for name, stage in _HELD["stamped_from"].items()
}

LEFT_OUT: list[str] = _HELD["index"]["left_out"]

COSTS_QUOTED: str = _HELD["costs"]["quoted"]
COSTS_QUOTED_IN: list[str] = _HELD["costs"]["quoted_in"]


def machine_class() -> str | None:
    return os.environ.get("MACHINE_CLASS") or None


def beside() -> int:
    """How many of dev/check.sh's other checks run beside this one, as it says."""
    return int(os.environ.get("CHATDDX_BESIDE") or 0)

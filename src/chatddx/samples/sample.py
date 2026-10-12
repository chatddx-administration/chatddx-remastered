import re
import tomllib
from pathlib import Path
from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from chatddx.fake_vllm.script import Script, Turn
from chatddx.fake_vllm.served import Refused

# As src/chatddx/curation/write.py titles a case that sends appendices.
WITH = re.compile(r"^(?P<family>.+?) with (?P<appendices>.+)$")


class Sample(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")

    name: str
    description: str
    configuration: str
    set: dict[str, str] = Field(default_factory=dict)
    endpoint: str
    cases: tuple[str, ...] = Field(min_length=1)
    seed: int = Field(default=7, ge=0)
    stop_after: int | None = Field(default=None, ge=1)
    unfinished: bool = False
    scored: bool = True
    turns: tuple[Turn, ...] = ()


def case_of(name: str) -> tuple[str, tuple[str, ...]]:
    found = WITH.match(name)
    if found is None:
        return name, ()
    names = tuple(n.strip() for n in found["appendices"].split(","))
    return found["family"], names


def load(path: Path) -> Sample:
    with path.open("rb") as f:
        data: dict[str, Any] = tomllib.load(f)
    turns = data.pop("turn", None)
    try:
        held = () if turns is None else Script.of({"turn": turns}, str(path)).turns
        return Sample.model_validate({**data, "name": path.stem, "turns": held})
    except (ValidationError, Refused) as e:
        raise ValueError(f"{path}: {e}") from None


def samples(directory: Path) -> list[Sample]:
    return [load(path) for path in sorted(directory.glob("*.toml"))]

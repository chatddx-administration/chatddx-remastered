from dataclasses import dataclass
from pathlib import Path
from typing import Self

from .inventory import Inventory


@dataclass(frozen=True)
class World:
    path: Path
    inventory: Inventory
    # Its factors and facts files: factors.toml and facts.toml, when it has them.
    factors: tuple[Path, ...] = ()
    facts: tuple[Path, ...] = ()

    @classmethod
    def load(cls, path: Path) -> Self:
        inventory = path / "inventory.toml"
        if not inventory.is_file():
            raise LookupError(f"{path} is no World: it holds no inventory.toml")
        return cls(
            path=path,
            inventory=Inventory.load(inventory),
            factors=tuple(p for p in [path / "factors.toml"] if p.is_file()),
            facts=tuple(p for p in [path / "facts.toml"] if p.is_file()),
        )

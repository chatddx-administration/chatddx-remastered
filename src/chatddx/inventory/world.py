import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Self

from .inventory import Inventory

_LOOPBACK = ("127.0.0.1", "localhost", "::1", "[::1]")


@dataclass(frozen=True)
class World:
    path: Path
    inventory: Inventory
    engines: tuple[Path, ...] = ()
    facts: tuple[Path, ...] = ()
    synthetic: int | None = None

    @classmethod
    def load(cls, path: Path) -> Self:
        inventory = path / "inventory.toml"
        if not inventory.is_file():
            raise LookupError(f"{path} is no World: it holds no inventory.toml")
        held = Inventory.load(inventory)
        return cls(
            path=path,
            inventory=held,
            engines=tuple(p for p in [path / "engines.toml"] if p.is_file()),
            facts=tuple(p for p in [path / "facts.toml"] if p.is_file()),
            synthetic=_synthetic(path / "synthetic.toml", held),
        )


# Policy: a World draws cases' scores only while it serves none but this machine's
# endpoints, so that no World that runs real models shows drawn scores among them.
def _synthetic(path: Path, inventory: Inventory) -> int | None:
    if not path.is_file():
        return None
    if away := sorted(
        name for name, e in inventory.endpoints.items() if e.url.host not in _LOOPBACK
    ):
        raise LookupError(
            f"{path}: a World draws scores only while its endpoints are on this "
            + f"machine, and {', '.join(away)} isn't"
        )
    with path.open("rb") as f:
        match tomllib.load(f).get("seed"):
            case int() as seed if not isinstance(seed, bool):
                return seed
            case _:
                raise LookupError(f"{path}: seed is to be a whole number")

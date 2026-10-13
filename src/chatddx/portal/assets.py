import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

MANIFEST = Path(".vite") / "manifest.json"
STYLES = "src/portal.css"
ROUTE = "/static"


@dataclass(frozen=True)
class Island:
    scripts: list[str]
    styles: list[str]


@dataclass(frozen=True)
class Assets:
    root: Path

    @property
    def built(self) -> bool:
        return (self.root / MANIFEST).is_file()

    def styles(self) -> list[str]:
        entry = self._manifest().get(STYLES)
        return [] if entry is None else [f"{ROUTE}/{entry['file']}"]

    def island(self, name: str) -> Island:
        manifest = self._manifest()
        entry = manifest.get(f"src/islands/{name}.ts")
        if entry is None:
            return Island([], [])
        return Island([f"{ROUTE}/{entry['file']}"], _styles(manifest, entry))

    def _manifest(self) -> dict[str, Any]:
        try:
            return json.loads((self.root / MANIFEST).read_text())
        except FileNotFoundError:
            return {}


def _styles(manifest: dict[str, Any], entry: dict[str, Any]) -> list[str]:
    found = [f"{ROUTE}/{css}" for css in entry.get("css", [])]
    for chunk in entry.get("imports", []):
        found += [s for s in _styles(manifest, manifest[chunk]) if s not in found]
    return found

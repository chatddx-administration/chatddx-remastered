from collections.abc import Mapping
from dataclasses import dataclass, field, replace

from chatddx.catalog import Edit
from chatddx.factors.request import RECIPE_PARTS, Recipe

PARTS = RECIPE_PARTS
OPTIONAL = tuple(p for p in PARTS if not Recipe.model_fields[p].is_required())


# A configuration, or a variation of it being tried: the configuration's head edit and
# recipe, under the name the person called it by, with the recipe parts replaced over it.
@dataclass(frozen=True)
class TriedVariation:
    configuration: Edit
    name: str
    recipe: Recipe | None = None
    # A chunk's digest, or None for an optional part taken out, with the name it was
    # set by.
    parts: Mapping[str, tuple[str | None, str]] = field(
        default_factory=dict[str, tuple[str | None, str]]
    )

    @property
    def label(self) -> str:
        return self.name + "".join(
            f"+{p}={self.parts[p][1]}" for p in PARTS if p in self.parts
        )

    def held(self, part: str) -> str | None:
        if part in self.parts:
            return self.parts[part][0]
        return None if self.recipe is None else getattr(self.recipe, part)

    def set(self, part: str, digest: str | None, name: str) -> "TriedVariation":
        if self.recipe is None:
            raise ValueError(f"{self.name} has no recipe to set its {part} in")
        if digest is None and part not in OPTIONAL:
            raise ValueError(
                f"a configuration always has a {part}: only {', '.join(OPTIONAL)} "
                + "can be taken out"
            )
        parts = {p: held for p, held in self.parts.items() if p != part}
        if getattr(self.recipe, part) != digest:
            parts[part] = (digest, name)
        return replace(self, parts=parts)

    @property
    def varied(self) -> Recipe | None:
        if self.recipe is None:
            return None
        changes = {p: digest for p, (digest, _) in self.parts.items()}
        return Recipe.model_validate(self.recipe.model_dump() | changes)

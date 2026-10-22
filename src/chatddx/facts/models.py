import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import Self

from pydantic import Field

from chatddx.factors.base import Frozen, Resolver
from chatddx.factors.engine import model_of
from chatddx.factors.facts import ModelFacts

BUNDLED = Path(__file__).with_name("models.toml")


class Facts(Frozen):
    models: dict[str, ModelFacts] = Field(default_factory=dict)

    # Policy: a World's facts about a model take the place of the bundled ones, as its
    # engines may serve the model otherwise, as with a shorter context.
    @classmethod
    def load(cls, *paths: Path) -> Self:
        models: dict[str, object] = {}
        found: dict[str, Path] = {}
        for path in paths:
            with path.open("rb") as f:
                data = tomllib.load(f)
            if set(data) - {"model"}:
                raise ValueError(f"{path}: facts have only 'model' tables")
            for name, values in data.get("model", {}).items():
                if found.get(name, BUNDLED) != BUNDLED:
                    raise ValueError(f"{name!r} has facts in more than one file")
                models[name] = {**values, "model": name}
                found[name] = path
        return cls.model_validate({"models": models})

    @classmethod
    def of(cls, found: Iterable[ModelFacts]) -> Self:
        return cls(models={f.model: f for f in found})

    def about(self, digest: str, get: Resolver) -> ModelFacts | None:
        return self.models.get(model_of(digest, get).name)

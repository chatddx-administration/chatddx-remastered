import tomllib
from collections.abc import Iterable
from pathlib import Path
from typing import Self

from pydantic import Field

from chatddx.factors.base import Frozen, Resolver
from chatddx.factors.facts import ModelFacts, model_name

BUNDLED = Path(__file__).with_name("models.toml")


class Facts(Frozen):
    models: dict[str, ModelFacts] = Field(default_factory=dict)

    @classmethod
    def load(cls, *paths: Path) -> Self:
        models: dict[str, object] = {}
        for path in paths:
            with path.open("rb") as f:
                data = tomllib.load(f)
            if set(data) - {"model"}:
                raise ValueError(f"{path}: facts have only 'model' tables")
            for name, values in data.get("model", {}).items():
                if name in models:
                    raise ValueError(f"{name!r} has facts in more than one file")
                models[name] = {**values, "model": name}
        return cls.model_validate({"models": models})

    @classmethod
    def of(cls, found: Iterable[ModelFacts]) -> Self:
        return cls(models={f.model: f for f in found})

    def about(self, engine: str, get: Resolver) -> ModelFacts | None:
        name = model_name(engine, get)
        return None if name is None else self.models.get(name)

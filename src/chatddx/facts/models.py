import tomllib
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Self

from pydantic import Field

from chatddx.factors.base import Component, Frozen, Resolver
from chatddx.factors.engine import (
    REASONING_FLAGS,
    LocalEngine,
    flag_names,
    flag_value,
    model_of,
    vllm_024,
)
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

    def served(self, engines: Mapping[str, Mapping[str, Component]]) -> Self:
        return type(self)(
            models={
                name: _narrowed(about, engines.get(name, {}))
                for name, about in self.models.items()
            }
        )

    def about(self, digest: str, get: Resolver) -> ModelFacts | None:
        return self.models.get(model_of(digest, get).name)


# Policy: facts are kept per model, so the engines serving one narrow them only where
# every one of them does, each a vLLM 0.24 whose flags say so.
def _narrowed(about: ModelFacts, engines: Mapping[str, Component]) -> ModelFacts:
    local = [e for e in map(vllm_024, engines.values()) if e is not None]
    if not engines or len(local) < len(engines):
        return about
    doc = about.model_dump()
    lengths = [_length(e) for e in local]
    if all(n is not None for n in lengths):
        served = max(n for n in lengths if n is not None)
        doc["context_length"] = min(served, about.context_length or served)
    if about.reasoning.budget == "thinking_token_budget" and not any(
        flag_names(e.argv) & REASONING_FLAGS for e in local
    ):
        names = sorted(engines)
        doc["reasoning"]["budget"] = {
            "refused": f"{', '.join(names)} serve{'s' if len(names) == 1 else ''} it "
            + "without --reasoning-parser or --reasoning-config, and vLLM 0.24 "
            + "refuses a thinking budget without one"
        }
    narrowed = ModelFacts.model_validate(doc)
    return about if narrowed.digest == about.digest else narrowed


def _length(engine: LocalEngine) -> int | None:
    value = flag_value(engine.argv, "--max-model-len")
    return int(value) if value is not None and value.isdecimal() else None

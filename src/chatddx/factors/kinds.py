import json
from typing import cast

from .base import Component, StructuralError
from .cases import Appendix, Case
from .engine import LocalEngine, ModelArtifact, RemoteEngine
from .facts import ModelFacts
from .request import (
    Compilation,
    FewShot,
    Instructions,
    Output,
    Passthrough,
    Prompt,
    Reasoning,
    Sampling,
    Skeleton,
    Tool,
    Toolset,
    Translations,
)
from .scoring import Expectation, ExpectationSchema, Judge, Scorer, Scoring
from .trial import CanarySet, Trial

# Every kind of component, and the only ones stored bytes are read as.
# src/chatddx/catalog/model.py:THREAD_KINDS threads all but cases and compilations.
KINDS: tuple[type[Component], ...] = (
    ModelArtifact,
    LocalEngine,
    RemoteEngine,
    ModelFacts,
    Instructions,
    FewShot,
    Prompt,
    Output,
    Sampling,
    Reasoning,
    Passthrough,
    Toolset,
    Translations,
    Tool,
    Skeleton,
    Compilation,
    Appendix,
    Case,
    Trial,
    CanarySet,
    ExpectationSchema,
    Expectation,
    Judge,
    Scorer,
    Scoring,
)


def _by_kind() -> dict[str, type[Component]]:
    found: dict[str, type[Component]] = {}
    for cls in KINDS:
        kind = cls.model_fields["kind"].default
        if kind in found:
            raise TypeError(f"duplicate component kind {kind!r}")
        found[kind] = cls
    return found


BY_KIND = _by_kind()


def parse_component(data: bytes) -> Component:
    loaded: object = json.loads(data)
    if not isinstance(loaded, dict):
        raise StructuralError("component is not a JSON object")
    doc = cast(dict[str, object], loaded)
    kind = doc.get("kind")
    cls = BY_KIND.get(kind) if isinstance(kind, str) else None
    if cls is None:
        raise StructuralError(f"unknown component kind {kind!r}")
    v = doc.pop("v", None)
    if v != cls.schema_version:
        raise StructuralError(f"{kind} v{v} is not readable by v{cls.schema_version}")
    return cls.model_validate(doc)

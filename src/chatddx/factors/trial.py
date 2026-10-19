import hashlib
import secrets
from collections.abc import Sequence
from typing import Annotated, Literal, override

from pydantic import AfterValidator, Field, JsonValue, field_validator, model_validator

from .base import (
    Component,
    Digest,
    Frozen,
    RefTo,
    Resolver,
    Settings,
    distinct,
    resolve,
)
from .cases import CaseRef, CleanupOp
from .engine import EngineRef
from .request import RUNTIME_KEYS, Skeleton, SkeletonRef

Order = Literal["case_major@1", "replicate_major@1", "shuffled@1"]


def _sorted(cases: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(sorted(cases))


class Trial(Component):
    kind: Literal["trial"] = "trial"
    skeleton: SkeletonRef
    engine: EngineRef
    cases: Annotated[
        tuple[CaseRef, ...], AfterValidator(distinct), AfterValidator(_sorted)
    ] = Field(min_length=1)
    cleanup: tuple[CleanupOp, ...] = ()
    seeds: Annotated[tuple[int, ...], AfterValidator(distinct)] = Field(min_length=1)

    @property
    def item_keys(self) -> list[tuple[str, int]]:
        return [(c, r) for c in self.cases for r in range(len(self.seeds))]

    @override
    def cross_check(self, get: Resolver) -> list[str]:
        skeleton = resolve(get, self.skeleton, Skeleton)
        if skeleton.purpose != "generation":
            return [f"trial uses a {skeleton.purpose} skeleton"]
        return []


def suggest_seeds(n: int) -> tuple[int, ...]:
    # 31 bits keeps seeds within a signed 32-bit int, which some servers require.
    return tuple(secrets.SystemRandom().sample(range(2**31), n))


TrialRef = Annotated[Digest, RefTo("trial")]


class Canary(Frozen):
    messages: tuple[dict[str, JsonValue], ...] = Field(min_length=1)
    body: Settings = Field(default_factory=dict)
    seed: int | None = None

    @field_validator("body")
    @classmethod
    def _no_runtime_keys(cls, body: dict[str, JsonValue]) -> dict[str, JsonValue]:
        if owned := body.keys() & RUNTIME_KEYS:
            raise ValueError(f"canary body may not set {sorted(owned)}")
        return body

    def render(
        self, *, model: str, return_token_ids: bool = True
    ) -> dict[str, JsonValue]:
        messages: list[JsonValue] = [dict(m) for m in self.messages]
        body: dict[str, JsonValue] = {"model": model, "messages": messages, **self.body}
        if self.seed is not None:
            body["seed"] = self.seed
        if return_token_ids:
            body["return_token_ids"] = True
        return body


class CanarySet(Component):
    kind: Literal["canary_set"] = "canary_set"
    canaries: tuple[Canary, ...] = Field(min_length=1)


CanarySetRef = Annotated[Digest, RefTo("canary_set")]


class Execution(Frozen):
    order: Order = "case_major@1"
    shuffle_seed: int | None = None
    concurrency: int = Field(default=1, ge=1)
    timeout_s: float | None = Field(default=None, gt=0)
    retries: int = Field(default=0, ge=0)
    whitespace_limit: int | None = Field(default=100, ge=1)

    @model_validator(mode="after")
    def _shuffle_seed(self) -> "Execution":
        if (self.order == "shuffled@1") != (self.shuffle_seed is not None):
            raise ValueError("shuffle_seed goes with shuffled order, and only with it")
        return self

    def schedule(self, cases: Sequence[str], replicates: int) -> list[tuple[str, int]]:
        if self.order == "replicate_major@1":
            return [(c, r) for r in range(replicates) for c in cases]
        items = [(c, r) for c in cases for r in range(replicates)]
        if self.order == "shuffled@1":
            items.sort(
                key=lambda cr: hashlib.sha256(
                    f"{self.shuffle_seed}:{cr[0]}:{cr[1]}".encode()
                ).digest()
            )
        return items

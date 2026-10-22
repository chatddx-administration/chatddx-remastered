from collections.abc import Iterable, Mapping, Sequence
from datetime import datetime
from typing import cast

from pydantic import Field, JsonValue, model_validator

from chatddx.factors.base import (
    Finding,
    Fingerprint,
    Frozen,
    canonical_bytes,
    sorted_keys,
)
from chatddx.factors.trial import Execution, Trial

from .record import ItemKey, UtcDatetime, in_order


class Attempt(Frozen):
    started_at: UtcDatetime
    finished_at: UtcDatetime
    status: int | None = None
    error: str | None = None

    @model_validator(mode="after")
    def _times(self) -> "Attempt":
        in_order(self.started_at, self.finished_at)
        return self


class Call(Frozen):
    request: Fingerprint
    started_at: UtcDatetime
    finished_at: UtcDatetime
    status: int | None = None
    response: dict[str, JsonValue] | None = None
    prompt_tokens: Fingerprint | None = None
    attempts: tuple[Attempt, ...] = Field(min_length=1)
    error: str | None = None

    @model_validator(mode="before")
    @classmethod
    def _prompt_tokens(cls, data: object) -> object:
        if not isinstance(data, dict):
            return data
        fields = cast(dict[str, object], data)
        response = fields.get("response")
        if not isinstance(response, dict) or "prompt_token_ids" not in response:
            return fields
        if fields.get("prompt_tokens") is not None:
            raise ValueError("prompt_tokens and prompt_token_ids both given")
        kept = cast(dict[str, JsonValue], response)
        ids = kept["prompt_token_ids"]
        return {
            **fields,
            "response": {k: v for k, v in kept.items() if k != "prompt_token_ids"},
            "prompt_tokens": Fingerprint.of(canonical_bytes(ids))
            if isinstance(ids, list)
            else None,
        }

    @model_validator(mode="after")
    def _times(self) -> "Call":
        in_order(self.started_at, self.finished_at)
        return self

    @property
    def returned_model(self) -> str | None:
        model = (self.response or {}).get("model")
        return model if isinstance(model, str) else None


def fingerprint_request(body: dict[str, JsonValue]) -> Fingerprint:
    return Fingerprint.of(canonical_bytes(sorted_keys(body)))


class ToolRun(Frozen):
    id: str
    name: str
    started_at: UtcDatetime
    finished_at: UtcDatetime
    result: str
    error: str | None = None

    @model_validator(mode="after")
    def _times(self) -> "ToolRun":
        in_order(self.started_at, self.finished_at)
        return self


class Turn(Frozen):
    tools: tuple[ToolRun, ...] = Field(min_length=1)
    call: Call | None = None


def attest_model(
    calls: Iterable[Call], want: str, who: str, subject: str
) -> list[Finding]:
    returned = {c.returned_model for c in calls if c.response is not None}
    findings = [
        Finding(
            code="attestation.model",
            message=f"{who} returned model {got!r}, declared {want!r}",
            subject=subject,
        )
        for got in sorted(m for m in returned - {want} if m is not None)
    ]
    if None in returned:
        findings.append(
            Finding(
                code="attestation.model",
                message=f"{who} returned no model name, declared {want!r}",
                subject=subject,
            )
        )
    return findings


def check_execution(
    execution: Execution,
    trial: Trial,
    calls: Sequence[Call],
    sent: Mapping[ItemKey, datetime],
) -> list[Finding]:
    findings: list[Finding] = []
    allowed = execution.retries + 1
    if over := sum(1 for c in calls if len(c.attempts) > allowed):
        findings.append(
            Finding(
                code="execution.retries",
                message=f"{over} calls took more than the {allowed} attempts allowed",
            )
        )
    limit = execution.timeout_s
    if limit is not None and (
        late := sum(
            1
            for c in calls
            for a in c.attempts
            if (a.finished_at - a.started_at).total_seconds() > limit
        )
    ):
        findings.append(
            Finding(
                code="execution.timeout",
                message=f"{late} attempt{'' if late == 1 else 's'} took longer than "
                + f"the {limit} s timeout",
            )
        )

    position = {
        ItemKey(case=c, replicate=r): n
        for n, (c, r) in enumerate(execution.schedule(trial.cases, len(trial.seeds)))
    }
    early = 0
    latest: datetime | None = None
    for key in sorted(sent.keys() & position.keys(), key=position.__getitem__):
        at = sent[key]
        if latest is not None and at < latest:
            early += 1
        latest = at if latest is None else max(latest, at)
    if early:
        findings.append(
            Finding(
                code="execution.order",
                message=f"{early} "
                + ("item was" if early == 1 else "items were")
                + " sent before items scheduled ahead of them",
            )
        )

    events = sorted(
        [(c.started_at, 1) for c in calls] + [(c.finished_at, -1) for c in calls]
    )
    in_flight = peak = 0
    for _, step in events:
        in_flight += step
        peak = max(peak, in_flight)
    if peak > execution.concurrency:
        findings.append(
            Finding(
                code="execution.concurrency",
                message=f"{peak} calls were in flight at once, declared "
                + f"{execution.concurrency}",
            )
        )
    return findings

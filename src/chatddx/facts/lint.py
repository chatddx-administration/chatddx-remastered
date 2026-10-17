from collections.abc import Collection, Iterable, Mapping

from pydantic import JsonValue

from chatddx.factors.base import Finding, resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.engine import model_of
from chatddx.factors.facts import (
    ContractFact,
    ModelFacts,
    Refusal,
    SamplingValues,
)
from chatddx.factors.lint import Languages, Reasons, lint
from chatddx.factors.request import Sampling, Skeleton
from chatddx.factors.scoring import Judge
from chatddx.factors.trial import Trial

from .models import Facts


def reasons(facts: Facts, registry: Registry) -> Reasons:
    def by_default(engine: str) -> bool | None:
        model = facts.about(engine, registry.get)
        return None if model is None else model.reasons_by_default()

    return by_default


def _model(subject: str, skeleton: Skeleton, model: ModelFacts) -> Iterable[Finding]:
    body = skeleton.body
    asked = (body.get("reasoning_effort"), body.get("chat_template_kwargs") or {})
    known = [
        (w.effort, w.chat_template_kwargs) for w in model.reasoning.realized().values()
    ]
    if asked != (None, {}) and asked not in known:
        yield Finding(
            code="facts.reasoning_unmatched",
            message="the configuration's reasoning settings match none of the model's "
            + "reasoning levels",
            subject=subject,
        )
    if "thinking_token_budget" in body and isinstance(model.reasoning.budget, Refusal):
        yield Finding(
            code="facts.budget_refused",
            message=model.reasoning.budget.refused,
            subject=subject,
        )
    match model.output.fact(skeleton.contract.kind):
        case Refusal(refused=reason):
            yield Finding(code="facts.output_refused", message=reason, subject=subject)
        case ContractFact(note=str() as note):
            yield Finding(
                level="info", code="facts.output_note", message=note, subject=subject
            )
        case _:
            pass


def _sampling(body: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    return {k: body[k] for k in SamplingValues.model_fields if k in body}


def _recommended(model: ModelFacts) -> list[dict[str, JsonValue]]:
    return [
        _sampling(Sampling.model_validate(v.model_dump(exclude_none=True)).body())
        for v in model.sampling.recommended.values()
    ]


def _sampled_for(
    subject: str, skeleton: Skeleton, name: str | None, facts: Facts
) -> Iterable[Finding]:
    asked = _sampling(skeleton.body)
    own = facts.models.get(name or "")
    if not asked or (own is not None and asked in _recommended(own)):
        return
    if others := sorted(
        other
        for other, model in facts.models.items()
        if other != name and asked in _recommended(model)
    ):
        yield Finding(
            code="facts.sampling_unmatched",
            message="the configuration's sampling is what the facts recommend for "
            + f"{', '.join(others)}, not for {name}",
            subject=subject,
        )


def _pair(c: Trial | Judge, registry: Registry, facts: Facts) -> Iterable[Finding]:
    name = model_of(c.engine, registry.get).name
    model = facts.about(c.engine, registry.get)
    skeleton = resolve(registry.get, c.skeleton, Skeleton)
    if model is None:
        yield Finding(
            level="info",
            code="facts.missing",
            message=f"no facts about {name!r}, so model-level checks were skipped",
            subject=c.digest,
        )
    else:
        yield from _model(c.digest, skeleton, model)
    yield from _sampled_for(c.digest, skeleton, name, facts)


def check_pairs(
    registry: Registry, facts: Facts, digests: Iterable[str] | None = None
) -> list[Finding]:
    findings: list[Finding] = []
    for d in registry if digests is None else digests:
        match registry.get(d):
            case Trial() | Judge() as c:
                findings.extend(_pair(c, registry, facts))
            case _:
                pass
    return findings


def lints(
    registry: Registry,
    facts: Facts,
    digests: Collection[str],
    languages: Languages | None = None,
) -> list[Finding]:
    found = lint(
        registry, digests, languages=languages, reasons=reasons(facts, registry)
    )
    return found + check_pairs(registry, facts, digests)

from typing import Annotated, Literal, Self, get_args

from pydantic import Field, StringConstraints, model_validator

from .base import Component, Digest, Frozen, RefTo, Resolver, Settings, resolve
from .engine import LocalEngine, ModelArtifact, RemoteEngine

Intent = Literal["off", "on", "minimal", "low", "medium", "high", "xhigh"]
Effort = Intent | Literal["default"]
INTENTS: tuple[Intent, ...] = get_args(Intent)


class Refused(ValueError):
    pass


class Refusal(Frozen):
    refused: Annotated[str, StringConstraints(min_length=1)]
    nearest: Intent | None = None


class Writes(Frozen):
    effort: Literal["none", "minimal", "low", "medium", "high"] | None = None
    chat_template_kwargs: Settings = Field(default_factory=dict)


ReasoningFact = Intent | Refusal | Writes


class Landing(Frozen):
    level: Intent
    writes: Writes
    nearest: tuple[str, ...] = ()


class ReasoningFacts(Frozen):
    default: Intent | None = None
    off: ReasoningFact | None = None
    on: ReasoningFact | None = None
    minimal: ReasoningFact | None = None
    low: ReasoningFact | None = None
    medium: ReasoningFact | None = None
    high: ReasoningFact | None = None
    xhigh: ReasoningFact | None = None
    budget: Literal["thinking_token_budget"] | Refusal | None = None

    def fact(self, intent: Intent) -> ReasoningFact | None:
        fact: ReasoningFact | None = getattr(self, intent)
        return fact

    def land(
        self, intent: Intent
    ) -> tuple[Intent, Refusal | Writes | None, tuple[str, ...]]:
        path: list[Intent] = []
        nearest: list[str] = []
        while True:
            if intent in path:
                raise ValueError(
                    f"{' -> '.join([*path, intent])}: the collapses go round"
                )
            path.append(intent)
            match self.fact(intent):
                case str() as collapsed:
                    intent = collapsed
                case Refusal(refused=reason, nearest=str() as near):
                    nearest.append(reason)
                    intent = near
                case fact:
                    return intent, fact, tuple(nearest)

    def resolve(self, effort: Effort) -> Landing:
        intent = self.default if effort == "default" else effort
        if intent is None:
            raise Refused("no default reasoning level is known")
        landed, fact, nearest = self.land(intent)
        match fact:
            case None:
                raise Refused(f"nothing is known about reasoning {landed!r}")
            case Refusal(refused=reason):
                raise Refused(reason)
            case Writes():
                return Landing(level=landed, writes=fact, nearest=nearest)

    def realized(self) -> dict[Intent, Writes]:
        return {i: f for i in INTENTS if isinstance(f := self.fact(i), Writes)}

    @model_validator(mode="after")
    def _collapses_land(self) -> Self:
        leads: dict[str, Intent] = {}
        for i in INTENTS:
            match self.fact(i):
                case str() as collapsed:
                    leads[i] = collapsed
                case Refusal(nearest=str() as near):
                    leads[i] = near
                case _:
                    pass
        if self.default is not None:
            leads["default"] = self.default
        for name, target in leads.items():
            if self.land(target)[1] is None:
                raise ValueError(
                    f"{name!r} collapses into {target!r}, which ends in no fact"
                )
        return self


class SamplingValues(Frozen):
    temperature: float | None = None
    top_p: float | None = None
    top_k: int | None = None
    min_p: float | None = None
    presence_penalty: float | None = None
    frequency_penalty: float | None = None
    repetition_penalty: float | None = None


class SamplingFacts(Frozen):
    recommended: dict[Intent, SamplingValues] = Field(default_factory=dict)
    generation_config: SamplingValues | None = None


class ContractFact(Frozen):
    note: str | None = None


class OutputFacts(Frozen):
    default: Literal["native", "tool", "text"] | None = None
    native: ContractFact | Refusal | None = None
    tool: ContractFact | Refusal | None = None
    text: ContractFact | Refusal | None = None

    def fact(
        self, kind: Literal["native", "tool", "text"]
    ) -> ContractFact | Refusal | None:
        fact: ContractFact | Refusal | None = getattr(self, kind)
        return fact


class ModelFacts(Component):
    kind: Literal["facts"] = "facts"
    model: str = Field(min_length=1)
    family: str | None = None
    parameters_b: float | None = None
    active_parameters_b: float | None = None
    quantization: str | None = None
    context_length: int | None = None
    licence: str | None = None
    reasoning: ReasoningFacts = ReasoningFacts()
    sampling: SamplingFacts = SamplingFacts()
    output: OutputFacts = OutputFacts()

    def check_budget(self) -> None:
        match self.reasoning.budget:
            case None:
                raise Refused("nothing is known about a thinking budget")
            case Refusal(refused=reason):
                raise Refused(reason)
            case _:
                pass

    def recommended(self, level: Intent) -> SamplingValues:
        values = self.sampling.recommended.get(level)
        if values is None:
            raise Refused(f"no sampling is recommended for reasoning {level!r}")
        return values

    def reasons_by_default(self) -> bool | None:
        try:
            landing = self.reasoning.resolve("default")
        except Refused:
            return None
        return landing.level != "off"


FactsRef = Annotated[Digest, RefTo("facts")]


def model_name(engine: str, get: Resolver) -> str | None:
    match get(engine):
        case LocalEngine(model=model):
            return resolve(get, model, ModelArtifact).repo
        case RemoteEngine(model=model):
            return model
        case _:
            return None

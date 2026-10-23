from typing import Annotated, Literal, Self, get_args

from pydantic import Field, StringConstraints, model_validator

from .base import Component, Digest, Frozen, RefTo, Settings, Worded

Level = Literal["off", "on", "minimal", "low", "medium", "high", "xhigh"]
Effort = Level | Literal["default"]
LEVELS: tuple[Level, ...] = get_args(Level)


class Refused(Worded, ValueError):
    pass


class Refusal(Frozen):
    refused: Annotated[str, StringConstraints(min_length=1)]
    nearest: Level | None = None


class Writes(Frozen):
    effort: Literal["none", "minimal", "low", "medium", "high"] | None = None
    chat_template_kwargs: Settings = Field(default_factory=dict)


ReasoningFact = Level | Refusal | Writes


class Landing(Frozen):
    level: Level
    writes: Writes
    nearest: tuple[str, ...] = ()


class ReasoningFacts(Frozen):
    default: Level | None = None
    off: ReasoningFact | None = None
    on: ReasoningFact | None = None
    minimal: ReasoningFact | None = None
    low: ReasoningFact | None = None
    medium: ReasoningFact | None = None
    high: ReasoningFact | None = None
    xhigh: ReasoningFact | None = None
    budget: Literal["thinking_token_budget"] | Refusal | None = None

    def fact(self, level: Level) -> ReasoningFact | None:
        fact: ReasoningFact | None = getattr(self, level)
        return fact

    def _land(
        self, level: Level
    ) -> tuple[Level, Refusal | Writes | None, tuple[str, ...]]:
        path: list[Level] = []
        nearest: list[str] = []
        while True:
            if level in path:
                raise ValueError(
                    f"{' -> '.join([*path, level])}: the collapses go round"
                )
            path.append(level)
            match self.fact(level):
                case str() as collapsed:
                    level = collapsed
                case Refusal(refused=reason, nearest=str() as near):
                    nearest.append(reason)
                    level = near
                case fact:
                    return level, fact, tuple(nearest)

    def landing(self, effort: Effort) -> Landing:
        level = self.default if effort == "default" else effort
        if level is None:
            raise Refused.of("no default reasoning level is known")
        landed, fact, nearest = self._land(level)
        match fact:
            case None:
                raise Refused.of(
                    "nothing is known about reasoning %(level)s", level=repr(landed)
                )
            case Refusal(refused=reason):
                raise Refused(reason)
            case Writes():
                return Landing(level=landed, writes=fact, nearest=nearest)

    def realized(self) -> dict[Level, Writes]:
        return {i: f for i in LEVELS if isinstance(f := self.fact(i), Writes)}

    @model_validator(mode="after")
    def _collapses_land(self) -> Self:
        leads: dict[str, Level] = {}
        for i in LEVELS:
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
            if self._land(target)[1] is None:
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
    recommended: dict[Level, SamplingValues] = Field(default_factory=dict)
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
                raise Refused.of("nothing is known about a thinking budget")
            case Refusal(refused=reason):
                raise Refused(reason)
            case _:
                pass

    def recommended(self, level: Level) -> SamplingValues:
        values = self.sampling.recommended.get(level)
        if values is None:
            raise Refused.of(
                "no sampling is recommended for reasoning %(level)s", level=repr(level)
            )
        return values

    def reasons_by_default(self) -> bool | None:
        try:
            landing = self.reasoning.landing("default")
        except Refused:
            return None
        return landing.level != "off"


FactsRef = Annotated[Digest, RefTo("facts")]

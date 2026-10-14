from collections.abc import Mapping
from datetime import datetime
from typing import Annotated, ClassVar, Literal, Self
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, JsonValue, model_validator

from chatddx import catalog, settings
from chatddx.bench import PARTS, Outcome
from chatddx.factors import base as factors
from chatddx.factors.cases import CleanupOp
from chatddx.factors.trial import Order
from chatddx.identity import Person, Role


class _Schema(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")


type Code = Literal[
    "unauthenticated",
    "cross_site",
    "not_found",
    "not_allowed",
    "ambiguous",
    "conflict",
    "moved_on",
    "refused",
    "unprocessable",
    "over_quota",
    "error",
]


class Error(_Schema):
    detail: str | list[JsonValue] = Field(
        description="why, or where a request doesn't validate"
    )
    code: Code


class SignIn(_Schema):
    login: str
    password: str


class Me(_Schema):
    id: int
    login: str
    name: str
    roles: list[Role]

    @classmethod
    def of(cls, person: Person) -> Self:
        return cls(
            id=person.id,
            login=person.login,
            name=person.name,
            roles=sorted(person.roles),
        )


class SignedIn(_Schema):
    token: str
    person: Me


class Labels(_Schema):
    views: list[str | None] = Field(
        default_factory=list[str | None], description="by position; null for none"
    )
    resources: list[str | None] = Field(
        default_factory=list[str | None], description="by position; null for none"
    )

    def given(self) -> catalog.Labels:
        parts: tuple[tuple[catalog.Part, list[str | None]], ...] = (
            ("view", self.views),
            ("resource", self.resources),
        )
        return {
            (part, position): label
            for part, labels in parts
            for position, label in enumerate(labels)
            if label is not None
        }

    @classmethod
    def of(cls, labels: Mapping[tuple[catalog.Part, int], str]) -> Self:
        def listed(part: catalog.Part) -> list[str | None]:
            held = {p: v for (k, p), v in labels.items() if k == part}
            return [held.get(p) for p in range(max(held, default=-1) + 1)]

        return cls(views=listed("view"), resources=listed("resource"))


class Edit(_Schema):
    id: int
    digest: str
    compilation: str | None
    based_on: int | None
    by: str
    at: datetime
    labels: Labels | None = Field(default=None, description="a scorer edit's")


class Thread(_Schema):
    id: int
    kind: str
    name: str | None
    title: str
    owner: str | None
    tags: list[str]
    language: str | None = Field(description="its head's")
    head: Edit


class ThreadDetail(Thread):
    description: str | None
    collaborators: list[str]
    forked_from: int | None
    recipe: JsonValue
    deleted: bool


class Said(_Schema):
    name: str | None = Field(
        None, description="null takes the name away, and the title takes over"
    )
    description: str | None = Field(None, description="replaced, never taken away")
    tags: list[str] | None = Field(None, description="its tags")
    collaborators: list[str] | None = Field(
        None, description="the logins it is shared with"
    )
    deleted: bool | None = None


type Chunk = Annotated[
    str | None,
    Field(description="a chunk's digest; empty or null takes an optional part out"),
]


class Parts(_Schema):
    instructions: Chunk = None
    few_shot: Chunk = None
    prompt: Chunk = None
    output: Chunk = None
    sampling: Chunk = None
    reasoning: Chunk = None
    passthrough: Chunk = None
    translations: Chunk = None
    toolset: Chunk = None

    def given(self) -> dict[str, str | None]:
        return {
            p: getattr(self, p) or None for p in PARTS if p in self.model_fields_set
        }


class Varying(Parts):
    head: int | None = Field(
        None,
        description="the edit it varies, by id: the configuration's head unless given",
    )
    endpoint: str | None = Field(None, description="to render and lint it for")
    tag: list[str] = Field(
        default_factory=list[str],
        description="the cases its reach is over: any of these, else every one",
    )
    seed: int | None = Field(None, description="drawn when not given")


type ComponentBody = Annotated[
    dict[str, JsonValue],
    Field(
        description="a component's JSON as GET /api/components/{digest} gives its "
        + "body, kind included"
    ),
]
type Language = Annotated[
    str | None,
    Field(description="the language of the text the component holds, such as 'sv'"),
]


class NewThread(_Schema):
    component: ComponentBody | None = None
    recipe: dict[str, JsonValue] | None = Field(
        None,
        description="for a new configuration: the recipe's parts by digest, its "
        + "purpose and its appendix layout, as a configuration's recipe reads",
    )
    name: str = Field(min_length=1)
    language: Language = None
    labels: Labels | None = Field(None, description="for a scorer")

    @model_validator(mode="after")
    def _one(self) -> Self:
        if (self.component is None) == (self.recipe is None):
            raise ValueError("a new thread holds a component or a recipe, not both")
        return self


class NewFork(_Schema):
    name: str = Field(min_length=1)
    head: int | None = Field(
        None,
        description="a configuration's: the edit it forks from, its head unless given",
    )
    parts: Parts = Parts()
    component: ComponentBody | None = Field(
        None, description="what the fork starts from in place of the head"
    )
    language: Language = None
    labels: Labels | None = Field(
        None, description="for a scorer; a scorer forked as it is keeps the head's"
    )


class NewEdit(_Schema):
    head: int = Field(description="the edit the change was made on: the head seen")
    parts: Parts = Parts()
    component: ComponentBody | None = None
    language: Language = None
    labels: Labels | None = Field(
        None,
        description="for a scorer; without them, the head's when the scorer is the "
        + "head's, else none",
    )


class Part(_Schema):
    part: str
    digest: str | None
    title: str | None
    summary: str | None
    replaced: bool


class Finding(_Schema):
    level: Literal["info", "warning"]
    code: str
    message: str
    subject: str | None

    @classmethod
    def of(cls, finding: factors.Finding) -> Self:
        return cls.model_validate(finding.model_dump())


class Varied(_Schema):
    path: str
    base: JsonValue
    fork: JsonValue


class Proposal(_Schema):
    base: Edit
    origin_head: Edit
    varies: list[Varied]
    recipe: JsonValue = Field(description="for a configuration, what it compiles from")
    component: JsonValue = Field(description="for another kind, its body")
    digest: str
    compilation: str | None


class NewFollow(_Schema):
    head: int = Field(description="the edit the change was made on: the head seen")
    language: Language = None


class MadeThread(ThreadDetail):
    findings: list[Finding]


class MadeEdit(Edit):
    findings: list[Finding]
    cases: dict[str, str] = Field(
        default_factory=dict,
        description="for an appendix: each case that held the old version, with its "
        + "replacement",
    )


class NewCarry(_Schema):
    head: int = Field(description="the edit the change was made on: the head seen")
    case: str = Field(description="another case of the expectation's family")


class Reach(_Schema):
    scorer: int
    name: str
    view: int
    label: str
    offered: bool
    cases: int
    missing: list[int]
    choosing: list[int]


class Variation(_Schema):
    head: Edit
    label: str = Field(description="its name, and the chunks it replaces")
    skeleton: str
    held_by: Thread | None = Field(
        description="the configuration whose head is the skeleton, the person's own first"
    )
    greedy: bool
    parts: list[Part] | None
    seed: int
    request: dict[str, JsonValue]
    findings: list[Finding] | None
    reach: list[Reach]


class Family(_Schema):
    id: int
    name: str
    owner: str | None
    tags: list[str]
    language: str | None
    case: str


class Expected(_Schema):
    expectation_schema: str
    title: str
    expectation: str | None
    data: JsonValue
    ambiguous: str | None
    shared: list[Thread] = Field(
        description="the expectation threads of others, shared with the person, they "
        + "could take"
    )


class NewTakes(_Schema):
    families: list[int] = Field(min_length=1, description="the cases, by family")
    expectation_schema: str
    owner: str | None = Field(None, description="a login: that owner's only")


class Taken(_Schema):
    taken: dict[int, int] = Field(description="the thread each was taken into")
    kept: dict[int, int] = Field(description="the person's own, left as it is")
    choosing: dict[int, list[int]] = Field(
        description="shared by several owners: the threads to choose from"
    )
    missing: list[int] = Field(description="none shared")


class NewTake(_Schema):
    replace: bool = Field(
        False,
        description="delete the person's own expectation of the case under that "
        + "schema, in the same write",
    )


class NewTyped(_Schema):
    text: str = Field(description="the case as typed, kept as written")
    name: str | None = None
    language: str | None = Field(None, description="the language it is typed in")
    source: str | None = Field(
        None,
        description="the database source it is kept in, when the World has several",
    )


class NewAppendix(_Schema):
    text: str = Field(min_length=1)
    name: str = Field(min_length=1)


class FamilyCase(_Schema):
    case: str
    title: str
    appendices: list[str]
    default: bool = Field(description="the case the family stands for")
    expectations: list[Expected]


class NewCase(_Schema):
    appendices: list[str] | None = Field(None, description="the appendices, in order")
    replacing: str | None = Field(
        None, description="or a case of the family left at an earlier vignette"
    )

    @model_validator(mode="after")
    def _one(self) -> Self:
        if (self.appendices is None) == (self.replacing is None):
            raise ValueError(
                "a case is built from appendices or replacing one, not both"
            )
        return self


class FamilyDetail(Family):
    description: str | None
    collaborators: list[str]
    appendices: list[str]
    expectations: list[Expected]


class Vignette(_Schema):
    source: str
    id: str
    text: str
    drifted: bool | None


class Endpoint(_Schema):
    name: str
    engine: str
    title: str | None
    model: str | None
    url: str | None
    host: str | None
    max_jobs: int
    credential: str | None
    cleared_for: list[str]
    takes_typed: bool = Field(
        description="whether a case typed into the World's database source can run "
        + "here: the source isn't sensitive, or the endpoint is cleared for it"
    )
    problem: str | None


class Model(_Schema):
    name: str
    facts: JsonValue
    endpoints: list[str]


class Component(_Schema):
    digest: str
    kind: str
    title: str
    body: JsonValue


class Kind(_Schema):
    kind: str
    word: str = Field(description="the bench's word for it, as GET /api/threads takes")
    written: bool = Field(description="whether a person writes it")
    json_schema: dict[str, JsonValue] = Field(
        description="its JSON Schema; a reference names the kinds it takes in x-kind"
    )


class Checked(_Schema):
    digest: str
    findings: list[Finding]


class Metric(_Schema):
    name: str
    measures: str
    params: dict[str, JsonValue] = Field(
        description="a JSON Schema for a view's params"
    )
    judged: bool = Field(
        description="whether it reads a judge's verdicts, so that its view names a judge"
    )
    unit: str | None = Field(
        default=None,
        description="what marks a value that isn't a score from 0 to 1, as @ an offset",
    )


class ScorerCode(_Schema):
    entry_point: str
    version: int
    metrics: list[Metric]
    params: dict[str, JsonValue] = Field(
        description="a JSON Schema for the scorer's own params, which every view shares"
    )


class Seeds(_Schema):
    seeds: list[int] | None = Field(
        default=None,
        min_length=1,
        max_length=settings.ITEMS_PER_RUN,
        description="the replicates' seeds",
    )
    replicates: int | None = Field(
        default=None,
        ge=1,
        le=settings.ITEMS_PER_RUN,
        description="or how many replicates, their seeds drawn",
    )

    @model_validator(mode="after")
    def _seeds_or_replicates(self) -> Self:
        if self.seeds is not None and self.replicates is not None:
            raise ValueError("a run takes seeds or replicates, not both")
        return self


class NewAgain(Seeds):
    score: bool = Field(
        True, description="under every scorer that applies, once it is finished"
    )


class NewRun(Seeds):
    configuration: int
    head: int | None = Field(
        None,
        description="the edit it varies, by id: the configuration's head unless given",
    )
    parts: Parts = Parts()
    endpoint: str
    families: list[int] | None = Field(None, description="the cases to run, by family")
    tags: list[str] | None = Field(
        None, description="or the cases of the families with any of these"
    )
    cases: list[str] | None = Field(
        None, description="or the cases themselves, each of a family's current ones"
    )
    cleanup: list[CleanupOp] | None = Field(
        None,
        description="the steps applied to each vignette, in order: its source's when "
        + "not given, and none for []",
    )
    concurrency: int | None = Field(
        None,
        ge=1,
        description="how many requests at once, up to the endpoint's max_jobs: the "
        + "endpoint's when not given",
    )
    order: Order | None = Field(
        None,
        description="the order the items are sent in, a shuffled one's seed drawn: the "
        + "endpoint's when not given",
    )
    score: bool = Field(
        True, description="under every scorer that applies, once it is finished"
    )

    @model_validator(mode="after")
    def _cases(self) -> Self:
        if [self.families, self.tags, self.cases].count(None) != 2:
            raise ValueError("a run takes one of families, tags or cases")
        return self


class Rig(_Schema):
    distribution: str
    version: str
    revision: str | None


class Unscored(_Schema):
    scorer: str
    name: str


class Run(_Schema):
    id: UUID
    at: datetime
    trial: str
    skeleton: str
    engine: str
    endpoint: str | None
    cases: list[str]
    seeds: list[int]
    described: str
    finished: bool
    unscored: list[Unscored] | None = Field(
        default=None,
        description="with `unscored`: the scorers it is left to be scored by",
    )


class Item(_Schema):
    case: str
    replicate: int
    outcome: Outcome
    prompt_tokens: int
    completion_tokens: int


class Answer(_Schema):
    value: JsonValue = Field(
        description="as read from the item's last call: what its schema holds, or text"
    )
    problem: str | None = Field(
        description="why it couldn't be read, or breaks its schema"
    )
    salvaged: bool = Field(
        description="a structured answer cut short, read with its structure closed"
    )


class ItemDetail(Item):
    why: str | None
    vignette: JsonValue
    call: JsonValue
    turns: JsonValue
    answer: Answer


class ScoredItem(_Schema):
    case: str
    replicate: int
    view: int
    value: float | None


class Graded(_Schema):
    scorer: str
    name: str
    score: UUID | None
    scoring: str | None
    at: datetime | None
    finished: bool
    labels: list[str]
    means: list[float | None]
    items: list[ScoredItem]
    refused: str | None


class ScoreItemDetail(ScoredItem):
    detail: JsonValue
    judge_calls: JsonValue


class ScoreItems(_Schema):
    items: list[ScoreItemDetail]
    findings: list[Finding]


class RunDetail(Run):
    rig: Rig
    finished_at: datetime | None
    noted: list[Finding]
    findings: list[Finding]
    items: list[Item]
    scores: list[Graded]


class RenderedAgain(_Schema):
    case: str
    replicate: int
    same: bool
    why: str | None


class NewScoring(_Schema):
    scorers: list[str] | None = Field(
        None, description="by digest; every scorer that applies when not given"
    )


class RunStartedData(_Schema):
    run: UUID
    trial: str
    skeleton: str
    endpoint: str | None
    cases: list[str]
    seeds: list[int]
    greedy: bool


class ItemStartedData(_Schema):
    case: str
    replicate: int
    seed: int


class ItemDeltaData(_Schema):
    case: str
    replicate: int
    kind: Literal["reasoning", "content", "tool_call"]
    text: str
    tokens: int


class ItemToolData(_Schema):
    case: str
    replicate: int
    tool: JsonValue


class ItemEndedData(Item):
    why: str | None


class CanaryEndedData(_Schema):
    phase: str
    canary: int
    call: JsonValue


class RunFinishedData(_Schema):
    findings: list[Finding]


class ScoringData(_Schema):
    scorers: list[Unscored]


class ScoreStartedData(_Schema):
    scorer: str
    name: str
    score: UUID
    labels: list[str]


class ScoreItemData(ScoredItem):
    score: UUID
    detail: JsonValue


class JudgeAskedData(_Schema):
    case: str
    replicate: int
    scorer: str
    view: int
    judge: str
    seed_index: int


class JudgeDeltaData(_Schema):
    case: str
    replicate: int
    kind: Literal["reasoning", "content", "tool_call"]
    text: str
    tokens: int


class JudgeAnsweredData(_Schema):
    case: str
    replicate: int
    view: int
    judge: str
    seed_index: int
    verdict: JsonValue
    call: JsonValue


class RunScoredData(_Schema):
    scores: list[Graded]


class ErrorData(_Schema):
    detail: str


class DoneData(_Schema):
    halted: bool | None = Field(
        description="whether it was halted; null when told from the ledger"
    )


EVENTS: dict[str, type[_Schema]] = {
    "run.started": RunStartedData,
    "item.started": ItemStartedData,
    "item.delta": ItemDeltaData,
    "item.tool": ItemToolData,
    "item.ended": ItemEndedData,
    "canary.ended": CanaryEndedData,
    "run.noted": Finding,
    "run.finished": RunFinishedData,
    "run.scoring": ScoringData,
    "score.started": ScoreStartedData,
    "judge.asked": JudgeAskedData,
    "judge.delta": JudgeDeltaData,
    "judge.answered": JudgeAnsweredData,
    "score.item": ScoreItemData,
    "score.noted": Finding,
    "run.scored": RunScoredData,
    "error": ErrorData,
    "done": DoneData,
}

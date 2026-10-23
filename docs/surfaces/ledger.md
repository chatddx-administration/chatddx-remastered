# `chatddx.ledger`

Written by `chatddx stamp write` from `src/chatddx/ledger/`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it:

```
## `<name>` `@<decorator>` `[<type parameters>]` `(<bases>)`
`<file>:<qualified name>`

* `<parameter or field>: <type> = <default>`
* ∟`<return type>`

Raises:
1. `<exception>`: `<arguments>` (from `<exception caught>`, through `<private helper>`, in a `ValidationError`)

Finds:
1. `<code>`: `<message>` (`<level>`, from `<exception caught>`, through `<private helper>`)
```

- A constant or a type alias is its definition instead of bullets; a class and its `__init__` leave out ∟, and a method its instance; `*`: the parameters after it are keyword-only, `/`: those before it positional-only.
- Raises and Finds are the function's own and its private helpers', in the order the code reaches them, each once, a `Whoops` left out; what a public function it calls raises is in that function's entry.
- Text is quoted, a value in it as `{<expression>}`, and an argument that isn't text is as written; a finding is a warning unless it gives its level.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

## `Attempt` `(Frozen)`
`src/chatddx/ledger/call.py:Attempt`

* `started_at: UtcDatetime`
* `finished_at: UtcDatetime`
* `status: int | None = None`
* `error: str | None = None`

## `attest_model`
`src/chatddx/ledger/call.py:attest_model`

* `calls: Iterable[Call]`
* `want: str`
* `who: str`
* `subject: str`
* ∟`list[Finding]`

Finds:
1. `attestation.model`: `"{who} returned model {got!r}, declared {want!r}"`
2. `attestation.model`: `"{who} returned no model name, declared {want!r}"`

## `Call` `(Frozen)`
`src/chatddx/ledger/call.py:Call`

* `request: Fingerprint`
* `started_at: UtcDatetime`
* `finished_at: UtcDatetime`
* `status: int | None = None`
* `response: dict[str, JsonValue] | None = None`
* `prompt_tokens: Fingerprint | None = None`
* `attempts: tuple[Attempt, ...] = Field(min_length=1)`
* `error: str | None = None`

Raises:
1. `ValueError`: `"prompt_tokens and prompt_token_ids both given"` (through `Call._prompt_tokens`, in a `ValidationError`)

## `Call.returned_model` `@property`
`src/chatddx/ledger/call.py:Call.returned_model`

* ∟`str | None`

## `CanaryCall` `(Record)`
`src/chatddx/ledger/run.py:CanaryCall`

* `schema_version: ClassVar[int] = 2`
* `sensitive: ClassVar[bool] = False`
* `run: UUID`
* `phase: Phase`
* `canary: int = Field(ge=0)`
* `call: Call`

## `check_execution`
`src/chatddx/ledger/call.py:check_execution`

* `execution: Execution`
* `trial: Trial`
* `calls: Sequence[Call]`
* `sent: Mapping[ItemKey, datetime]`
* ∟`list[Finding]`

Finds:
1. `execution.retries`: `"%(num)s calls took more than the %(allowed)s attempts allowed"`
2. `execution.timeout`: `"%(num)s attempt took longer than the %(limit)s s timeout" / "%(num)s attempts took longer than the %(limit)s s timeout"`
3. `execution.order`: `"%(num)s item was sent before items scheduled ahead of them" / "%(num)s items were sent before items scheduled ahead of them"`
4. `execution.concurrency`: `"%(num)s calls were in flight at once, declared %(declared)s"`

## `check_log`
`src/chatddx/ledger/record.py:check_log`

* `started: Stage`
* `finished: Stage | None`
* `ids: Iterable[UUID]`
* ∟`None`

Raises:
1. `StructuralError`: `"rows belong to different logs"`

## `check_run`
`src/chatddx/ledger/run.py:check_run`

* `run: Run`
* `registry: Registry`
* ∟`list[Finding]`

Raises:
1. `StructuralError`: `"canary calls in a run without canaries"`
2. `StructuralError`: `"canary calls not planned: {names}"`
3. `StructuralError`: `"duplicate canary calls"`
4. `StructuralError`: `"run items outside the trial: {sorted(map(str, stray))}"`
5. `StructuralError`: `"duplicate run items"`
6. `StructuralError`: `"{item.key}: tool rounds, but the skeleton has no tools"` (through `_rounds`)
7. `StructuralError`: `"{item.key}: more than {skeleton.max_rounds} rounds"` (through `_rounds`)
8. `StructuralError`: `"{item.key}: no tool named {r.name!r}"` (through `_rounds`)
9. `StructuralError`: `"{item.key}: a round runs tools for calls the response didn't make"` (through `_rounds`)
10. `StructuralError`: `"tool code recorded for tools the skeleton lacks: {stray}"` (through `_tool_code`)

Finds:
1. `run.incomplete`: `"%(num)s item missing" / "%(num)s items missing"`
2. `run.incomplete`: `"%(num)s canary call missing" / "%(num)s canary calls missing"`
3. `case.drift`: `"the vignette read differs from the case's"`
4. `call.failed`: `error`
5. `tools.stopped`: `"round %(round)s stopped after %(ran)s of %(num)s tool calls, before its call"` (through `_rounds`)
6. `tools.unanswered`: `"the last response still calls %(tools)s after %(rounds)s of %(num)s rounds"` (through `_rounds`)
7. `tools.code`: `"the code tool %(tool)s ran with isn't recorded"` (through `_tool_code`)
8. `tools.code`: `"tool %(tool)s ran at version %(ran)s of %(entry_point)s, not the version it pins (%(pinned)s)"` (through `_tool_code`)
9. `attestation.prompt_tokens`: `"%(num)s item has no prompt token fingerprint" / "%(num)s items have no prompt token fingerprint"`
10. `canary.phase`: `"%(num)s start canary calls hadn't finished when the first item was sent"` (through `_bracketed`)
11. `canary.phase`: `"%(num)s end canary calls started before the last item call finished"` (through `_bracketed`)

## `check_score`
`src/chatddx/ledger/score.py:check_score`

* `score: Score`
* `run: Run`
* `registry: Registry`
* ∟`list[Finding]`

Raises:
1. `StructuralError`: `"score does not belong to this run"`
2. `StructuralError`: `"duplicate score items"`
3. `StructuralError`: `"score item view {item.view} is out of range"`
4. `StructuralError`: `"score item {item.key} is not in the run"`
5. `StructuralError`: `"judge {jc.judge} is not view {item.view}'s judge"` (through `_judged`)
6. `StructuralError`: `"judge seed index {jc.seed_index} out of range"` (through `_judged`)
7. `StructuralError`: `"{item.key}: duplicate judge calls for view {item.view}"` (through `_judged`)

Finds:
1. `view.unreachable`: `"view %(view)s's output selector %(selector)s reaches nothing in the run's output schema"`
2. `judge.incomplete`: `"view %(view)s's value rests on %(called)s of %(num)s judge seeds"` (through `_judged`)
3. `score.scorer_code`: `"the scorer code ran at version %(ran)s of %(entry_point)s, not the version the scorer pins (%(pinned)s)"`
4. `score.run_unfinished`: `"the run hasn't finished"`
5. `score.run_unfinished`: `"the score started before the run finished"`
6. `score.no_expectation`: `"%(num)s of the run's cases have no expectation in the scoring"`
7. `score.incomplete`: `"%(num)s item missing" / "%(num)s items missing"`

## `check_seal`
`src/chatddx/ledger/record.py:check_seal`

* `log: Log`
* `subject: str`
* ∟`list[Finding]`

Finds:
1. `ledger.seal`: `"rows changed after the log was sealed"`

## `Endpoint` `(Frozen)`
`src/chatddx/ledger/run.py:Endpoint`

* `name: str`
* `url: str`

## `fingerprint_request`
`src/chatddx/ledger/call.py:fingerprint_request`

* `body: dict[str, JsonValue]`
* ∟`Fingerprint`

## `Finished` `(Protocol)`
`src/chatddx/ledger/record.py:Finished`

## `Finished.seal` `@property`
`src/chatddx/ledger/record.py:Finished.seal`

* ∟`str`

## `in_order`
`src/chatddx/ledger/record.py:in_order`

* `started: datetime`
* `finished: datetime`
* ∟`None`

Raises:
1. `ValueError`: `"finished before it started"`

## `ItemKey` `(Frozen)`
`src/chatddx/ledger/record.py:ItemKey`

* `case: CaseRef`
* `replicate: int = Field(ge=0)`

## `ItemKey.__hash__` `@override`
`src/chatddx/ledger/record.py:ItemKey.__hash__`

* ∟`int`

## `JudgeCall` `(Frozen)`
`src/chatddx/ledger/score.py:JudgeCall`

* `judge: JudgeRef`
* `seed_index: int = Field(ge=0)`
* `call: Call`

## `JudgeEndpoint` `(Frozen)`
`src/chatddx/ledger/score.py:JudgeEndpoint`

* `judge: JudgeRef`
* `endpoint: Endpoint`

## `Log` `(Protocol)`
`src/chatddx/ledger/record.py:Log`

## `Log.finished` `@property`
`src/chatddx/ledger/record.py:Log.finished`

* ∟`Finished | None`

## `Log.seal`
`src/chatddx/ledger/record.py:Log.seal`

* ∟`str`

## `Phase`
`src/chatddx/ledger/run.py:Phase`

`Phase = Literal["start", "end"]`

## `PHASES`
`src/chatddx/ledger/run.py:PHASES`

`PHASES: tuple[Phase, ...] = ("start", "end")`

## `Record` `(Frozen)`
`src/chatddx/ledger/record.py:Record`

* `sensitive: ClassVar[bool] = True`
* `schema_version: ClassVar[int] = 1`

## `Record.canonical` `@property`
`src/chatddx/ledger/record.py:Record.canonical`

* ∟`bytes`

## `Record.canonical_doc`
`src/chatddx/ledger/record.py:Record.canonical_doc`

* ∟`dict[str, JsonValue]`

## `Record.parse` `@classmethod`
`src/chatddx/ledger/record.py:Record.parse`

* `data: bytes | str`
* ∟`Self`

Raises:
1. `StructuralError`: `"{cls.__name__} is not a JSON object"`
2. `StructuralError`: `"{cls.__name__} v{v} is not readable by v{cls.schema_version}"`

## `Run` `(Frozen)`
`src/chatddx/ledger/run.py:Run`

* `started: RunStarted`
* `finished: RunFinished | None = None`
* `items: tuple[RunItem, ...] = ()`
* `canaries: tuple[CanaryCall, ...] = ()`

## `Run.finish`
`src/chatddx/ledger/run.py:Run.finish`

* `at: AwareDatetime`
* `findings: Sequence[Finding] = ()`
* ∟`RunFinished`

## `Run.seal`
`src/chatddx/ledger/run.py:Run.seal`

* ∟`str`

## `RunFinished` `(Record)`
`src/chatddx/ledger/run.py:RunFinished`

* `sensitive: ClassVar[bool] = False`
* `stage: Literal["finished"] = "finished"`
* `run: UUID`
* `at: UtcDatetime`
* `findings: tuple[Finding, ...] = ()`
* `seal: Digest`

## `RunItem` `(Record)`
`src/chatddx/ledger/run.py:RunItem`

* `schema_version: ClassVar[int] = 2`
* `run: UUID`
* `key: ItemKey`
* `vignette: Fingerprint`
* `call: Call`
* `turns: tuple[Turn, ...] = ()`

Raises:
1. `ValueError`: `"only the last round may lack its call"` (through `RunItem._unsent`, in a `ValidationError`)

## `RunItem.calls` `@property`
`src/chatddx/ledger/run.py:RunItem.calls`

* ∟`tuple[Call, ...]`

## `RunStarted` `(Record)`
`src/chatddx/ledger/run.py:RunStarted`

* `sensitive: ClassVar[bool] = False`
* `schema_version: ClassVar[int] = 2`
* `stage: Literal["started"] = "started"`
* `run: UUID`
* `at: UtcDatetime`
* `rig: Code`
* `trial: TrialRef`
* `execution: Execution = Execution()`
* `canaries: CanarySetRef | None = None`
* `verify_at: Annotated[tuple[Phase, ...], AfterValidator(_phase_order)] = Field(…)`
* `tool_code: Annotated[tuple[ToolCode, ...], AfterValidator(_by_tool)] = ()`
* `endpoint: Endpoint | None = None`

Raises:
1. `ValueError`: `"verify_at goes with a canary set"` (through `RunStarted._verify_at`, in a `ValidationError`)

## `Score` `(Frozen)`
`src/chatddx/ledger/score.py:Score`

* `started: ScoreStarted`
* `finished: ScoreFinished | None = None`
* `items: tuple[ScoreItem, ...] = ()`

## `Score.finish`
`src/chatddx/ledger/score.py:Score.finish`

* `at: AwareDatetime`
* `findings: Sequence[Finding] = ()`
* ∟`ScoreFinished`

## `Score.seal`
`src/chatddx/ledger/score.py:Score.seal`

* ∟`str`

## `ScoreFinished` `(Record)`
`src/chatddx/ledger/score.py:ScoreFinished`

* `stage: Literal["finished"] = "finished"`
* `score: UUID`
* `at: UtcDatetime`
* `findings: tuple[Finding, ...] = ()`
* `seal: Digest`

## `ScoreItem` `(Record)`
`src/chatddx/ledger/score.py:ScoreItem`

* `schema_version: ClassVar[int] = 2`
* `score: UUID`
* `key: ItemKey`
* `view: int = Field(ge=0)`
* `value: float | None = Field(allow_inf_nan=False)`
* `detail: JsonValue = None`
* `judge_calls: tuple[JudgeCall, ...] = ()`

## `ScoreStarted` `(Record)`
`src/chatddx/ledger/score.py:ScoreStarted`

* `sensitive: ClassVar[bool] = False`
* `schema_version: ClassVar[int] = 2`
* `stage: Literal["started"] = "started"`
* `score: UUID`
* `run: UUID`
* `at: UtcDatetime`
* `rig: Code`
* `scorer_version: int = Field(ge=1)`
* `scoring: ScoringRef`
* `execution: Execution = Execution()`
* `endpoints: tuple[JudgeEndpoint, ...] = ()`

## `seal_rows`
`src/chatddx/ledger/record.py:seal_rows`

* `started: Record`
* `**rows: Iterable[Record]`
* ∟`str`

## `Stage` `(Protocol)`
`src/chatddx/ledger/record.py:Stage`

## `Stage.at` `@property`
`src/chatddx/ledger/record.py:Stage.at`

* ∟`datetime`

## `ToolCode` `(Frozen)`
`src/chatddx/ledger/run.py:ToolCode`

* `tool: ToolRef`
* `version: int = Field(ge=1)`

## `ToolRun` `(Frozen)`
`src/chatddx/ledger/call.py:ToolRun`

* `id: str`
* `name: str`
* `started_at: UtcDatetime`
* `finished_at: UtcDatetime`
* `result: str`
* `error: str | None = None`

## `Turn` `(Frozen)`
`src/chatddx/ledger/call.py:Turn`

* `tools: tuple[ToolRun, ...] = Field(min_length=1)`
* `call: Call | None = None`

## `UtcDatetime`
`src/chatddx/ledger/record.py:UtcDatetime`

`UtcDatetime = Annotated[AwareDatetime, AfterValidator(_utc)]`

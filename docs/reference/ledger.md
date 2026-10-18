# `chatddx.ledger`

Written by `chatddx reference` from `src/chatddx/ledger/`: each public name, sorted, with its parameters or fields,
```
REFERENCE: REPLACE
replace the line below with these
---
`∟` its return type, what it raises and what it finds.
```
`∟` its return type, and what it raises.

- `*`: the parameters after it are keyword-only; `/`: those before it are positional-only. A function a
  class binds as an attribute is its method: its first parameter, the instance, is left out.
- Raises: the function's own `raise` statements and its private helpers' (through `<helper>`), in the order
  the code reaches them, each once. What the public functions it calls raise is in their own entries.
- A message is quoted, with the values of the code that raises it as `{expr}`; an argument that isn't text is
  as written, and from `<exception>` when it is the exception caught.
```
REFERENCE: ADD
add these lines here
---
- Finds: each `Finding` it makes, as `code`: message, followed as Raises are; a warning unless it says info.
```

## attest_model
`src/chatddx/ledger/call.py:attest_model`

* `calls: Iterable[Call]`
* `want: str`
* `who: str`
* `subject: str`
* ∟`list[Finding]`
```
REFERENCE: ADD
add these lines here
---

Finds:

1. `attestation.model`: "{who} returned model {got!r}, declared {want!r}"
2. `attestation.model`: "{who} returned no model name, declared {want!r}"
```

## Call `(Frozen)`
`src/chatddx/ledger/call.py:Call`

* `request: Fingerprint`
* `started_at: UtcDatetime`
* `finished_at: UtcDatetime`
* `status: int | None = None`
* `response: dict[str, JsonValue] | None = None`
* `prompt_tokens: Fingerprint | None = None`
* `attempts: int = Field(default=1, ge=1)`
* `error: str | None = None`

Raises:

1. `ValueError`: "prompt_tokens and prompt_token_ids both given" (through `Call._prompt_tokens`, in a `ValidationError`)

## Call.returned_model `@property`
`src/chatddx/ledger/call.py:Call.returned_model`

* ∟`str | None`

## CanaryCall `(Record)`
`src/chatddx/ledger/run.py:CanaryCall`

* `sensitive: ClassVar[bool] = False`
* `run: UUID`
* `phase: Phase`
* `canary: int = Field(ge=0)`
* `call: Call`

## check_execution
`src/chatddx/ledger/call.py:check_execution`

* `execution: Execution`
* `trial: Trial`
* `calls: Sequence[Call]`
* `sent: Mapping[ItemKey, datetime]`
* ∟`list[Finding]`

```
REFERENCE: ADD
add these lines here
---
Finds:

1. `execution.retries`: "{over} calls took more than the {allowed} attempts allowed"
2. `execution.order`: "{early} items were sent before items scheduled ahead of them"
3. `execution.concurrency`: "{peak} calls were in flight at once, declared {execution.concurrency}"

```
## check_log
`src/chatddx/ledger/record.py:check_log`

* `started: Stage`
* `finished: Stage | None`
* `ids: Iterable[UUID]`
* ∟`None`

Raises:

1. `StructuralError`: "rows belong to different logs"

## check_run
`src/chatddx/ledger/run.py:check_run`

* `run: Run`
* `registry: Registry`
* ∟`list[Finding]`

Raises:

1. `StructuralError`: "canary calls in a run without canaries"
2. `StructuralError`: "canary calls not planned: {names}"
3. `StructuralError`: "duplicate canary calls"
4. `StructuralError`: "run items outside the trial: {sorted(map(str, stray))}"
5. `StructuralError`: "duplicate run items"
6. `StructuralError`: "{item.key}: tool rounds, but the skeleton has no tools" (through `_rounds`)
7. `StructuralError`: "{item.key}: more than {skeleton.max_rounds} rounds" (through `_rounds`)
8. `StructuralError`: "{item.key}: no tool named {r.name!r}" (through `_rounds`)
9. `StructuralError`: "{item.key}: a round runs tools for calls the response didn't make" (through `_rounds`)
10. `StructuralError`: "tool code recorded for tools the skeleton lacks: {stray}" (through `_tool_code`)

```
REFERENCE: ADD
add these lines here
---
Finds:

1. `run.incomplete`: "{len(missing)} {what} missing"
2. `case.drift`: "the vignette read differs from the case's"
3. `call.failed`: error
4. `tools.stopped`: "round {len(item.turns)} stopped after {len(item.turns[-1].tools)} of {len(asked)} tool calls, before its call" (through `_rounds`)
5. `tools.unanswered`: "the last response still calls {', '.join(left)} after {len(item.turns)} of {skeleton.max_rounds} rounds" (through `_rounds`)
6. `tools.code`: message (through `_tool_code`)
7. `attestation.prompt_tokens`: "{unfingerprinted} items have no prompt token fingerprint"
8. `canary.phase`: message (through `_bracketed`)

```
## check_score
`src/chatddx/ledger/score.py:check_score`

* `score: Score`
* `run: Run`
* `registry: Registry`
* ∟`list[Finding]`

Raises:

1. `StructuralError`: "score does not belong to this run"
2. `StructuralError`: "duplicate score items"
3. `StructuralError`: "score item view {item.view} is out of range"
4. `StructuralError`: "score item {item.key} is not in the run"
5. `StructuralError`: "judge {jc.judge} is not view {item.view}'s judge" (through `_judged`)
6. `StructuralError`: "judge seed index {jc.seed_index} out of range" (through `_judged`)
7. `StructuralError`: "{item.key}: duplicate judge calls for view {item.view}" (through `_judged`)

```
REFERENCE: ADD
add these lines here
---
Finds:

1. `view.unreachable`: "view {i}'s output selector {view.output!r} reaches nothing in the run's output schema"
2. `judge.incomplete`: "view {item.view}'s value rests on {called} of {declared} judge seeds" (through `_judged`)
3. `score.scorer_code`: "the scorer code ran at version {ran} of {scorer.entry_point}, not the version the scorer pins ({scorer.version})"
4. `score.run_unfinished`: "the run hasn't finished" if ended is None else 'the score started before the run finished'
5. `score.no_expectation`: "{len(uncovered)} of the run's cases have no expectation in the scoring"
6. `score.incomplete`: "{len(missing)} items missing"

```
## check_seal
`src/chatddx/ledger/record.py:check_seal`

* `log: Log`
* `subject: str`
* ∟`list[Finding]`
```
REFERENCE: ADD
add these lines here
---

Finds:

1. `ledger.seal`: "rows changed after the log was sealed"
```

## Endpoint `(Frozen)`
`src/chatddx/ledger/run.py:Endpoint`

* `name: str`
* `url: str`

## fingerprint_request
`src/chatddx/ledger/call.py:fingerprint_request`

* `body: dict[str, JsonValue]`
* ∟`Fingerprint`

## Finished `(Protocol)`
`src/chatddx/ledger/record.py:Finished`

## Finished.seal `@property`
`src/chatddx/ledger/record.py:Finished.seal`

* ∟`str`

## in_order
`src/chatddx/ledger/record.py:in_order`

* `started: datetime`
* `finished: datetime`
* ∟`None`

Raises:

1. `ValueError`: "finished before it started"

## ItemKey `(Frozen)`
`src/chatddx/ledger/record.py:ItemKey`

* `case: CaseRef`
* `replicate: int = Field(ge=0)`

## ItemKey.__hash__ `@override`
`src/chatddx/ledger/record.py:ItemKey.__hash__`

* ∟`int`

## JudgeCall `(Frozen)`
`src/chatddx/ledger/score.py:JudgeCall`

* `judge: JudgeRef`
* `seed_index: int = Field(ge=0)`
* `call: Call`

## JudgeEndpoint `(Frozen)`
`src/chatddx/ledger/score.py:JudgeEndpoint`

* `judge: JudgeRef`
* `endpoint: Endpoint`

## Log `(Protocol)`
`src/chatddx/ledger/record.py:Log`

## Log.finished `@property`
`src/chatddx/ledger/record.py:Log.finished`

* ∟`Finished | None`

## Log.seal
`src/chatddx/ledger/record.py:Log.seal`

* ∟`str`

## Phase
`src/chatddx/ledger/run.py:Phase`

* `Phase = Literal["start", "end"]`

## PHASES
`src/chatddx/ledger/run.py:PHASES`

* `PHASES: tuple[Phase, ...] = ("start", "end")`

## Record `(Frozen)`
`src/chatddx/ledger/record.py:Record`

* `sensitive: ClassVar[bool] = True`
* `schema_version: ClassVar[int] = 1`

## Record.canonical `@property`
`src/chatddx/ledger/record.py:Record.canonical`

* ∟`bytes`

## Record.canonical_doc
`src/chatddx/ledger/record.py:Record.canonical_doc`

* ∟`dict[str, JsonValue]`

## Record.parse `@classmethod`
`src/chatddx/ledger/record.py:Record.parse`

* `data: bytes | str`
* ∟`Self`

Raises:

1. `StructuralError`: "{cls.__name__} is not a JSON object"
2. `StructuralError`: "{cls.__name__} v{v} is not readable by v{cls.schema_version}"

## Run `(Frozen)`
`src/chatddx/ledger/run.py:Run`

* `started: RunStarted`
* `finished: RunFinished | None = None`
* `items: tuple[RunItem, ...] = ()`
* `canaries: tuple[CanaryCall, ...] = ()`

## Run.finish
`src/chatddx/ledger/run.py:Run.finish`

* `at: AwareDatetime`
* `findings: Sequence[Finding] = ()`
* ∟`RunFinished`

## Run.seal
`src/chatddx/ledger/run.py:Run.seal`

* ∟`str`

## RunFinished `(Record)`
`src/chatddx/ledger/run.py:RunFinished`

* `sensitive: ClassVar[bool] = False`
* `stage: Literal["finished"] = "finished"`
* `run: UUID`
* `at: UtcDatetime`
* `findings: tuple[Finding, ...] = ()`
* `seal: Digest`

## RunItem `(Record)`
`src/chatddx/ledger/run.py:RunItem`

* `run: UUID`
* `key: ItemKey`
* `vignette: Fingerprint`
* `call: Call`
* `turns: tuple[Turn, ...] = ()`

Raises:

1. `ValueError`: "only the last round may lack its call" (through `RunItem._unsent`, in a `ValidationError`)

## RunItem.calls `@property`
`src/chatddx/ledger/run.py:RunItem.calls`

* ∟`tuple[Call, ...]`

## RunStarted `(Record)`
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

1. `ValueError`: "verify_at goes with a canary set" (through `RunStarted._verify_at`, in a `ValidationError`)

## Score `(Frozen)`
`src/chatddx/ledger/score.py:Score`

* `started: ScoreStarted`
* `finished: ScoreFinished | None = None`
* `items: tuple[ScoreItem, ...] = ()`

## Score.finish
`src/chatddx/ledger/score.py:Score.finish`

* `at: AwareDatetime`
* `findings: Sequence[Finding] = ()`
* ∟`ScoreFinished`

## Score.seal
`src/chatddx/ledger/score.py:Score.seal`

* ∟`str`

## ScoreFinished `(Record)`
`src/chatddx/ledger/score.py:ScoreFinished`

* `stage: Literal["finished"] = "finished"`
* `score: UUID`
* `at: UtcDatetime`
* `findings: tuple[Finding, ...] = ()`
* `seal: Digest`

## ScoreItem `(Record)`
`src/chatddx/ledger/score.py:ScoreItem`

* `score: UUID`
* `key: ItemKey`
* `view: int = Field(ge=0)`
* `value: float | None = Field(allow_inf_nan=False)`
* `detail: JsonValue = None`
* `judge_calls: tuple[JudgeCall, ...] = ()`

## ScoreStarted `(Record)`
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

## seal_rows
`src/chatddx/ledger/record.py:seal_rows`

* `started: Record`
* `**rows: Iterable[Record]`
* ∟`str`

## Stage `(Protocol)`
`src/chatddx/ledger/record.py:Stage`

## Stage.at `@property`
`src/chatddx/ledger/record.py:Stage.at`

* ∟`datetime`

## ToolCode `(Frozen)`
`src/chatddx/ledger/run.py:ToolCode`

* `tool: ToolRef`
* `version: int = Field(ge=1)`

## ToolRun `(Frozen)`
`src/chatddx/ledger/call.py:ToolRun`

* `id: str`
* `name: str`
* `started_at: UtcDatetime`
* `finished_at: UtcDatetime`
* `result: str`
* `error: str | None = None`

## Turn `(Frozen)`
`src/chatddx/ledger/call.py:Turn`

* `tools: tuple[ToolRun, ...] = Field(min_length=1)`
* `call: Call | None = None`

## UtcDatetime
`src/chatddx/ledger/record.py:UtcDatetime`

* `UtcDatetime = Annotated[AwareDatetime, AfterValidator(_utc)]`

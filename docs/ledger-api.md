# Ledger API

Reference for the `chatddx.ledger` package and the `ledger` database schema. It was written from
`src/chatddx/ledger/*`, `docs/ledger.md` and `src/chatddx/store/migrations/000{4,5,6}-*-ledger.sql`. What the ledger
is and why it is shaped this way is in `docs/ledger.md`; this file says what each name accepts, returns and raises.
Factor types it uses (`Code`, `Fingerprint`, `Finding`, `Execution`, `Registry`, …) are in `docs/factors-api.md`.

Paths are relative to `src/chatddx/ledger/` unless they start with `src/` or `docs/`.

## Contents
- [Package](#package)
- [Conventions](#conventions)
- [record.py](#recordpy): `Record`, `ItemKey`, times, canonical form, seal
- [call.py](#callpy): `Call`, fingerprints, `ToolRun`, `Turn`, execution checks
- [run.py](#runpy): run records, `Run`, `check_run`, `compare_prompt_tokens`
- [score.py](#scorepy): score records, `Score`, `check_score`
- [Finding codes](#finding-codes)
- [Database: schema `ledger`](#database-schema-ledger)
- [Known gaps](#known-gaps)
- [Beyond docs/ledger.md](#beyond-docsledgermd)

## Package

`chatddx.ledger` re-exports `Call`, `CanaryCall`, `Endpoint`, `ItemKey`, `JudgeCall`, `Record`, `Run`,
`RunFinished`, `RunItem`, `RunStarted`, `Score`, `ScoreFinished`, `ScoreItem`, `ScoreStarted`, `ToolCode`, `ToolRun`,
`Turn`, `check_run`, `check_score`, `compare_prompt_tokens`, `fingerprint_prompt_tokens` and `fingerprint_request`.
Everything else (`Phase`, `PHASES`, `UtcDatetime`, the stage unions, the helpers in `record.py` and
`call.py:check_execution`) is imported by path.

| Module | Builds on |
| --- | --- |
| `record.py` | `chatddx.factors.base`, `chatddx.factors.cases` |
| `call.py` | `record.py`, `chatddx.factors.trial` |
| `run.py` | `call.py`, `record.py`, `chatddx.factors.{bundle,cases,engine,request,trial}` |
| `score.py` | `run.py`, `call.py`, `record.py`, `chatddx.factors.{bundle,request,scoring,select,trial}` |

The package imports no chatddx package but `chatddx.factors`, and no third-party package but pydantic.

## Conventions

**Models.** Every model derives from `chatddx.factors.base.Frozen`: frozen, `extra="forbid"`, tuples for sequences.
Building one validates it. The seven row types derive from `Record`; `ItemKey`, `Call`, `ToolRun`, `Turn`,
`ToolCode`, `Endpoint`, `JudgeCall` are parts of rows, and `Run` and `Score` are logs put back together from rows.
Only records have `v`, `canonical` and `parse`.

| Record | Module | `stage` | `case_derived` | Table |
| --- | --- | --- | --- | --- |
| `RunStarted` | `run.py` | `"started"` | no | `ledger.run_stage` |
| `RunItem` | `run.py` | | yes | `ledger.run_item` |
| `CanaryCall` | `run.py` | | no | `ledger.canary_call` |
| `RunFinished` | `run.py` | `"finished"` | no | `ledger.run_stage` |
| `ScoreStarted` | `score.py` | `"started"` | no | `ledger.score_stage` |
| `ScoreItem` | `score.py` | | yes | `ledger.score_item` |
| `ScoreFinished` | `score.py` | `"finished"` | no | `ledger.score_stage` |

**Errors.**

| Exception | When |
| --- | --- |
| `pydantic.ValidationError` | A record or log breaks its own rules: a naive time, a call, tool run or log that finishes before it starts, stages out of order, rows of different logs, a duplicate phase or tool, `verify_at` without canaries, a tool run without `result`, a round without tools, a round without its call before an item's last round, an infinite or NaN score value. Rules written as validators raise `ValueError` or `StructuralError`, which pydantic wraps. |
| `chatddx.factors.base.StructuralError` (a `ValueError`) | `Record.parse` of another version or of JSON that isn't an object; `check_run`, `check_score` and `compare_prompt_tokens` when the rows don't fit the components, or a component is missing or of the wrong kind (`resolve`, `Registry.get`). |
| `json.JSONDecodeError` | `Record.parse` of bytes that aren't JSON. |
| `AssertionError` | `check_run` when the trial's engine isn't `engine.local` or `engine.remote`; a checked registry rules it out. |

**Findings.** All findings the package returns are warnings (`Finding.level` left at `"warning"`). The checks return
them and store nothing; the runner keeps the ones it saw while running in the finished row (`RunFinished.findings`,
`ScoreFinished.findings`). Every code is listed under "Finding codes".

**Ids.** Runs and scores are identified by a `UUID` the writer picks; nothing in the package makes one. Components
are referred to by digest (`TrialRef`, `CaseRef`, `CanarySetRef`, `ToolRef`, `ScoringRef`, `JudgeRef`: a `Digest`
annotated with the kind it may point to).

**Item-key subjects.** Findings about an item have `subject=str(key)`, pydantic's rendering of an `ItemKey`:
`case='sha256:…' replicate=0`.

## record.py

### `UtcDatetime`
`Annotated[AwareDatetime, AfterValidator(_utc)]`. A naive time is refused (`ValidationError`, type
`timezone_aware`); an aware one is converted to UTC, so `02:00+02:00` is kept as `00:00Z` and written as
`"…T00:00:00Z"`. Every time field in the package has this type. `Run.finish` and `Score.finish` take a plain
`AwareDatetime`, which the finished row converts.

### `class Record(Frozen)`
The base of every row type.

| Member | Description |
| --- | --- |
| `case_derived: ClassVar[bool] = True` | Whether the type may hold content produced from a vignette. A subclass that holds none sets it to `False`. |
| `schema_version: ClassVar[int] = 1` | Written as `v`. Bump it when an existing field's meaning or default changes; an added field with a backward-compatible default needs no bump. |
| `canonical_doc() -> dict[str, JsonValue]` | The canonical JSON document, `v` included. |
| `canonical -> bytes` | `canonical_bytes(canonical_doc())`. Not cached. |
| `parse(data: bytes \| str) -> Self` (classmethod) | Reads canonical text back. `json.JSONDecodeError` when it isn't JSON, `StructuralError("<Class> is not a JSON object")` when it isn't an object, `StructuralError("<Class> v<v> is not readable by v<schema_version>")` when `v` is missing or another version, `ValidationError` for bad fields (a finished row parsed as `RunStarted`, for one). |

### Canonical form
As for components (`docs/factors-api.md`, "Canonical form"):
- `canonical_bytes`: compact JSON, non-ASCII kept, NaN refused, UTF-8.
- In every model, fields are sorted by name and optional fields equal to their default are left out. `stage` is
  always kept. Required fields are always kept, even when `None`, as `ScoreItem.value` is.
- `v` is added at the top level only.
- JSON data keeps its key order: `Call.response`, `ScoreItem.detail`.
- Times are UTC with `Z`; UUIDs are lowercase and hyphenated.

`RunStarted(run=UUID(int=1), at=…, rig=Code(distribution="chatddx", version="0"), trial=d)` is written as

```json
{"at":"2026-01-01T00:00:00Z","rig":{"distribution":"chatddx","version":"0"},"run":"00000000-0000-0000-0000-000000000001","stage":"started","trial":"sha256:…","v":1}
```

### `class ItemKey(Frozen)`
Which request of a run an item is.

| Field | Type | Default |
| --- | --- | --- |
| `case` | `CaseRef` | required |
| `replicate` | `int`, ≥ 0 | required; the seed's position among the trial's seeds |

Hashable, by `(case, replicate)`. Rendered by `str()` as `case='sha256:…' replicate=0`.

### Seal
`seal_rows(started: Record, **rows: Iterable[Record]) -> str` builds one document

```text
{"<group>": [canonical_doc of each row, sorted by canonical bytes], …, "started": started.canonical_doc()}
```

with its keys sorted, and returns `sha256_digest(canonical_bytes(doc))`: `sha256:` and 64 hex digits. `Run.seal()`
passes the groups `items` and `canaries`, and `Score.seal()` the group `items`. A group is present even when empty
(`[]`). Judge calls are inside score items, and tool rounds inside run items, so the seal covers them. The finished
row isn't part of it.

### Internal helpers

| Function | Returns / raises |
| --- | --- |
| `in_order(started, finished) -> None` | `ValueError("finished before it started")` when `finished < started`. Equal times pass. |
| `check_log(stages, order, ids) -> None` | `StructuralError` when the stage names aren't a prefix of `order` (`"stages [...] do not follow (...)"`) or the ids differ (`"rows belong to different logs"`); `in_order` between the first stage and each later one. |
| `check_seal(log, subject) -> list[Finding]` | `[ledger.seal]` when the log has a finished row whose seal differs from `log.seal()`, else `[]`. |
| `code_name(code: Code) -> str` | `"<distribution> <version>[ <revision>]"`, for messages. |

## call.py

### `class Call(Frozen)`
One exchange with an engine: an item's first request, a tool round's request, a canary or a judge request.

| Field | Type | Default |
| --- | --- | --- |
| `request` | `Fingerprint` | required; `fingerprint_request` of the body sent |
| `started_at` | `UtcDatetime` | required; with retries, the first attempt's start |
| `finished_at` | `UtcDatetime` | required; with retries, the last attempt's end. Not before `started_at`. |
| `status` | `int \| None` | `None`; the HTTP status, if a response came |
| `response` | `dict[str, JsonValue] \| None` | `None`; the parsed body, meant to be stored without `prompt_token_ids` (not enforced) |
| `prompt_tokens` | `Fingerprint \| None` | `None`; from `fingerprint_prompt_tokens` |
| `attempts` | `int`, ≥ 1 | `1` |
| `error` | `str \| None` | `None` |

| Property | Returns |
| --- | --- |
| `returned_model -> str \| None` | `response["model"]` when it is a string, else `None`. |
| `system_fingerprint -> str \| None` | `response["system_fingerprint"]` when it is a string, else `None`. Nothing compares it. |

### `fingerprint_request(body: dict[str, JsonValue], key: tuple[str, bytes] | None = None) -> Fingerprint`
`Fingerprint.of(canonical_bytes(sorted_keys(body)), key)`: top-level keys sorted, nested key order kept. With
`key = (key_id, secret)` the fingerprint is HMAC-SHA-256.

### `fingerprint_prompt_tokens(response: dict[str, JsonValue], key: tuple[str, bytes] | None = None) -> tuple[dict[str, JsonValue], Fingerprint | None]`
Returns the response without its top-level `prompt_token_ids`, and `Fingerprint.of(canonical_bytes(ids), key)` when
`ids` is a list. When it is missing or not a list, the key is still dropped and the fingerprint is `None`.

### `class ToolRun(Frozen)`
One tool the runner ran for a tool call in a response.

| Field | Type | Default |
| --- | --- | --- |
| `id` | `str` | required; the id of the tool call it answers |
| `name` | `str` | required; the tool name the call gave |
| `started_at`, `finished_at` | `UtcDatetime` | required; `finished_at` not before `started_at` |
| `result` | `str` | required; the text sent back to the model |
| `error` | `str \| None` | `None`; why the tool failed. `result` is then what the model was told instead. |

The arguments aren't kept: they are in the previous call's response.

### `class Turn(Frozen)`
A tool round.

| Field | Type | Default |
| --- | --- | --- |
| `tools` | `tuple[ToolRun, ...]`, at least one | required |
| `call` | `Call \| None` | `None`; the request sent with the results, or none when the run stopped before it. Only an item's last turn may lack one (`RunItem`). |

### `check_execution(execution: Execution, trial: Trial, calls: Sequence[Call], sent: Mapping[ItemKey, datetime]) -> list[Finding]`
Internal; `check_run` and `check_score` call it. `calls` are the calls to count; `sent` says when each item was sent.

| Code | When |
| --- | --- |
| `execution.retries` | Some calls have `attempts > execution.retries + 1`. One finding, with the count. |
| `execution.order` | Taking the items of `sent` in `execution.schedule(trial.cases, len(trial.seeds))` order, some were sent before the latest send time of the items ahead of them. Items outside the schedule are ignored. One finding, with the count. |
| `execution.concurrency` | The peak number of calls in flight exceeds `execution.concurrency`. A call ending at the instant another starts doesn't overlap it. One finding, with the peak. |

## run.py

### Names

| Name | Value |
| --- | --- |
| `Phase` | `Literal["start", "end"]` |
| `PHASES` | `("start", "end")`, in run order |
| `RunStage` | `RunStarted \| RunFinished`, discriminated by `stage` |
| `RUN_STAGES` | `("started", "finished")` |

### `class ToolCode(Frozen)`
The version of a tool's entry point the runner ran it at: `tool: ToolRef`, `version: int` (from 1).

### `class Endpoint(Frozen)`
The World inventory's endpoint a run's calls went to (`docs/inventory.md`, "Endpoints"): `name: str`, `url: str`.
Neither is checked.

### `class RunStarted(Record)`, stage `started`
Opens a run with its recorded factors. Not case-derived. `schema_version` 2: `tool_code` holds versions.

| Field | Type | Default |
| --- | --- | --- |
| `stage` | `Literal["started"]` | `"started"` |
| `run` | `UUID` | required |
| `at` | `UtcDatetime` | required |
| `rig` | `Code` | required; the rig's code |
| `trial` | `TrialRef` | required |
| `execution` | `Execution` | `Execution()` |
| `canaries` | `CanarySetRef \| None` | `None` |
| `verify_at` | `tuple[Phase, ...]`, at least one | `("start", "end")`. Duplicates refused; sorted into run order. Must stay at the default when `canaries` is `None` (`"verify_at goes with a canary set"`). |
| `tool_code` | `tuple[ToolCode, ...]` | `()`. One entry per tool: a repeated `tool` is refused; sorted by `tool`. |
| `endpoint` | `Endpoint \| None` | `None` |

### `class RunItem(Record)`
One request of the trial and what came back. Case-derived.

| Field | Type | Default |
| --- | --- | --- |
| `run` | `UUID` | required |
| `key` | `ItemKey` | required |
| `vignette` | `Fingerprint` | required; the vignette as read from its source |
| `call` | `Call` | required; the first request |
| `turns` | `tuple[Turn, ...]` | `()`; the tool rounds |

`calls -> tuple[Call, ...]`: `call`, then each turn's call, when it has one. A turn without a call before the last is
refused: `only the last round may lack its call`.

### `class CanaryCall(Record)`
One canary of the run's set, sent at one phase. Not case-derived.

| Field | Type | Default |
| --- | --- | --- |
| `run` | `UUID` | required |
| `phase` | `Phase` | required |
| `canary` | `int`, ≥ 0 | required; the canary's position in the set |
| `call` | `Call` | required |

### `class RunFinished(Record)`, stage `finished`
Closes a run. Not case-derived.

| Field | Type | Default |
| --- | --- | --- |
| `stage` | `Literal["finished"]` | `"finished"` |
| `run` | `UUID` | required |
| `at` | `UtcDatetime` | required |
| `findings` | `tuple[Finding, ...]` | `()`; what the runner saw while running |
| `seal` | `Digest` | required |

### `class Run(Frozen)`
A run's log put back together from its rows.

| Field | Type | Default |
| --- | --- | --- |
| `stages` | `tuple[RunStage, ...]`, at least one | required; `(started,)` or `(started, finished)` |
| `items` | `tuple[RunItem, ...]` | `()` |
| `canaries` | `tuple[CanaryCall, ...]` | `()` |

Building one runs `check_log`: the stages must be `started` then optionally `finished`, the finished row not earlier
than the started one, and every row's `run` the same (`ValidationError`). It doesn't check items or canary calls
against anything else; `check_run` does.

| Member | Description |
| --- | --- |
| `started -> RunStarted` | The first stage. |
| `finished -> RunFinished \| None` | The finished stage, if any. |
| `seal() -> str` | `seal_rows(started, items=items, canaries=canaries)`. |
| `finish(at: AwareDatetime, findings: Sequence[Finding] = ()) -> RunFinished` | A finished row for this run with the current seal. It doesn't check `at` against the started row, or whether the run is finished already. |

### `check_run(run: Run, registry: Registry) -> list[Finding]`
Compares the run with what its started row declared. Resolves the trial, the canary set if any, each item's case,
the skeleton, its tools and the engine through `registry`.

Raises `StructuralError`:

| Message | When |
| --- | --- |
| `canary calls in a run without canaries` | Any canary call when `canaries` is `None`. |
| `canary calls not planned: ['<phase>/<position>', …]` | A phase not in `verify_at`, or a position not in the set. |
| `duplicate canary calls` | Two calls for the same phase and position. |
| `run items outside the trial: […]` | An item key whose case isn't in `trial.cases` or whose replicate is ≥ `len(trial.seeds)`. |
| `duplicate run items` | Two items with the same key. |
| `<key>: tool rounds, but the skeleton has no tools` | An item with turns on a skeleton without tools. |
| `<key>: more than <max_rounds> rounds` | More turns than `skeleton.max_rounds`. |
| `<key>: no tool named '<name>'` | A tool run whose name isn't a tool of the skeleton, and which has no `error`. |
| `<key>: a round runs tools for calls the response didn't make` | A turn's set of `(id, name)` differs from the previous call's tool calls (`chatddx.factors.request.tool_calls`), leaving out calls to the answer function of a `tool` contract; for a turn without a call, it has one the previous call didn't make. |
| `tool code recorded for tools the skeleton lacks: […]` | A `tool_code` entry for a tool not in `skeleton.tools`. |

Returns findings, in this order:
1. `ledger.seal`, subject the run id;
2. `run.incomplete` when finished: one for missing items, one for missing planned canary calls;
3. `case.drift` for each item whose `vignette` differs from its case's `vignette.fingerprint`;
4. `call.failed` for each item whose last call has an `error`, subject the item key, then for each canary call with
   one, subject `<phase>/<position>`; the message is the error. Earlier calls of an item can't have one: a failed call
   ends its rounds;
5. `tools.unanswered` for each item whose last call still has tool calls other than the answer function's, or
   `tools.stopped` when its last turn has no call (skeletons with tools only);
6.  `tools.code` for each tool of the skeleton whose version isn't recorded or isn't the one `Tool.version` pins;
7.  `attestation.model` for each item: one per distinct wrong model name, and one when some call has a response but no
    model name. The declared name is the engine's `served_model_name`: a local engine's digest, a remote engine's
    `model`. Calls without a response aren't checked;
8.  `attestation.prompt_tokens` when some items have a call, failed calls included, without `prompt_tokens`;
9.  `execution.*` over every item call and canary call, an item counting as sent when its first call starts;
10. `canary.phase`: start-phase calls that finish after the first item call starts, and end-phase calls that start
    before the last item call, tool rounds included, finishes. One finding per phase. Nothing when there are no items.

Canary calls get neither the model check nor the prompt-token check. Timeouts aren't checked.

### `compare_prompt_tokens(a: Run, b: Run, registry: Registry) -> list[Finding]`
Raises `StructuralError("the runs build their prompts from different <fields>")` when the two trials differ in
`skeleton`, `engine` or `cleanup`. Otherwise returns `attestation.prompt_tokens_drift`, subject the item key, for
each item of `a` whose first call has `prompt_tokens`, matched by key with an item of `b` whose first call has them
too, where the two differ. Later calls aren't compared; items of `b` missing from `a` and vice versa are skipped.

## score.py

### Names
`ScoreStage` is `ScoreStarted | ScoreFinished`, discriminated by `stage`; `SCORE_STAGES` is `("started",
"finished")`.

### `class JudgeCall(Frozen)`

| Field | Type | Default |
| --- | --- | --- |
| `judge` | `JudgeRef` | required |
| `seed_index` | `int`, ≥ 0 | required; the seed's position among the judge's seeds |
| `call` | `Call` | required |

### `class ScoreStarted(Record)`, stage `started`
Not case-derived. `schema_version` 2. Its `scorer_code: Code` is `scorer_version: int` (from 1): the version of the
scorer's entry point the scoring pass ran.

| Field | Type | Default |
| --- | --- | --- |
| `stage` | `Literal["started"]` | `"started"` |
| `score` | `UUID` | required |
| `run` | `UUID` | required; the run it grades |
| `at` | `UtcDatetime` | required |
| `rig` | `Code` | required |
| `scoring` | `ScoringRef` | required |
| `execution` | `Execution` | `Execution()`; for the judge calls |
| `scorer_version` | `int`, ≥ 1 | required; the version of the scorer's entry point that ran |
| `endpoints` | `tuple[JudgeEndpoint, ...]` | `()`; each judge's endpoint, `JudgeEndpoint(judge: JudgeRef, endpoint: Endpoint)` |

### `class ScoreItem(Record)`
One run item graded by one view. Case-derived.

| Field | Type | Default |
| --- | --- | --- |
| `score` | `UUID` | required |
| `key` | `ItemKey` | required; the run item |
| `view` | `int`, ≥ 0 | required; the view's position among the scorer's views |
| `value` | `float \| None`, finite | required; `None` when the item couldn't be scored. Infinity and NaN are refused. |
| `detail` | `JsonValue` | `None`; whatever the scorer writes |
| `judge_calls` | `tuple[JudgeCall, ...]` | `()` |

### `class ScoreFinished(Record)`, stage `finished`
Not case-derived. Fields as `RunFinished`, with `score: UUID` in place of `run`.

### `class Score(Frozen)`
A score's log put back together from its rows.

| Field | Type | Default |
| --- | --- | --- |
| `stages` | `tuple[ScoreStage, ...]`, at least one | required |
| `items` | `tuple[ScoreItem, ...]` | `()` |

Validated as `Run` is, by `score`. Members `started`, `finished`, `seal()` (`seal_rows(started, items=items)`) and
`finish(at, findings=())` behave as `Run`'s.

### `check_score(score: Score, run: Run, registry: Registry) -> list[Finding]`
Compares the score with its scoring and its run. Resolves the scoring, its scorer, the scorer's judges, the run's
trial, its skeleton and every expectation of the scoring. "The run's items" below are `run.items`, not the trial's.

Raises `StructuralError`:

| Message | When |
| --- | --- |
| `score does not belong to this run` | `score.started.run != run.started.run`. |
| `duplicate score items` | Two items with the same key and view. |
| `score item view <view> is out of range` | `view ≥ len(scorer.views)`. |
| `score item <key> is not in the run` | A key that isn't one of the run's items. |
| `judge <digest> is not view <view>'s judge` | A judge call whose judge isn't its view's `judge`; so any judge call on a view without a judge. |
| `judge seed index <i> out of range` | `seed_index ≥ len(judge.seeds)`. |
| `<key>: duplicate judge calls for view <view>` | Two judge calls with the same `seed_index` in one item. |

Returns findings, in this order:
1. `view.unreachable` for each view whose `output` selector can't reach anything in the run skeleton's
   `output_schema` (`chatddx.factors.select.reaches`), subject the scorer digest;
2. `judge.incomplete` for each item with a value whose view's judge was called with fewer distinct seeds than it has;
   then `attestation.model` for each item's judge calls, per judge: one per distinct wrong model name, and one when
   some call has a response but no model name, against the judge engine's `served_model_name`;
3. `score.scorer_code` when `scorer_version` isn't the version `Scorer.version` pins;
4. `score.run_unfinished` when the run has no finished row, or finished after the score started;
5. `ledger.seal`, subject the score id;
6. `score.no_expectation` when some cases of the run's items have no expectation in the scoring. One finding, with
   the number of cases;
7. `score.incomplete` when the score is finished and some pairs of a run item and a view have no score item;
8. `execution.*` over every judge call, with the run's trial's schedule; an item counts as sent when its earliest
   judge call, over all its views, starts. Items without judge calls are left out of the order.

## Finding codes

All are warnings. Item-key subjects are `str(ItemKey)`.

| Code | Reported by | Subject | Message |
| --- | --- | --- | --- |
| `run.incomplete` | `check_run` | none | `<n> items missing`, `<n> canary calls missing` |
| `case.drift` | `check_run` | item key | `the vignette read differs from the case's` |
| `call.failed` | `check_run` | item key, or `<phase>/<position>` for a canary call | the call's `error` |
| `tools.unanswered` | `check_run` | item key | `the last response still calls <names> after <k> of <max_rounds> rounds` |
| `tools.stopped` | `check_run` | item key | `round <r> stopped after <k> of <n> tool calls, before its call` |
| `tools.code` | `check_run` | tool digest | `the code tool '<name>' ran with isn't recorded`, or `tool '<name>' ran at version <v> of <entry point>, not the version it pins (<v>)` |
| `attestation.model` | `check_run`, `check_score` | item key | `engine returned model '<got>', declared '<want>'`, or `engine returned no model name, declared '<want>'`; for a judge call, `judge engine returned …` |
| `attestation.prompt_tokens` | `check_run` | none | `<n> items have no prompt token fingerprint` |
| `canary.phase` | `check_run` | none | `<n> start canary calls hadn't finished when the first item was sent`, `<n> end canary calls started before the last item call finished` |
| `execution.retries` | `check_run`, `check_score` | none | `<n> calls took more than the <retries + 1> attempts allowed` |
| `execution.order` | `check_run`, `check_score` | none | `<n> items were sent before items scheduled ahead of them` |
| `execution.concurrency` | `check_run`, `check_score` | none | `<peak> calls were in flight at once, declared <concurrency>` |
| `ledger.seal` | `check_run`, `check_score` | run or score id | `rows changed after the log was sealed` |
| `attestation.prompt_tokens_drift` | `compare_prompt_tokens` | item key | `the engine read different prompt tokens for the same item` |
| `view.unreachable` | `check_score` | scorer digest | `view <i>'s output selector '<output>' reaches nothing in the run's output schema` |
| `judge.incomplete` | `check_score` | item key | `view <v>'s value rests on <called> of <declared> judge seeds` |
| `score.scorer_code` | `check_score` | score id | `the scorer code ran at version <v> of <entry point>, not the version the scorer pins (<v>)` |
| `score.run_unfinished` | `check_score` | score id | `the run hasn't finished`, or `the score started before the run finished` |
| `score.no_expectation` | `check_score` | score id | `<n> of the run's cases have no expectation in the scoring` |
| `score.incomplete` | `check_score` | none | `<n> items missing` |

`docs/ledger.md`, "Findings", also lists `answer.unread` and `answer.invalid` (subject the item key). The scoring
pass reports them into `ScoreFinished.findings`; this package doesn't produce them. `case.drift` is also reported by
`chatddx.factors.cases.prepare_case`, and `view.unreachable` by `chatddx.factors.lint.lint` for a view's expectation
selector.

## Database: schema `ledger`

Created by `0004-t0-ledger.sql`, roles in `0005-t1-ledger.sql`, consistency checks and insert-only triggers in
`0006-t2-ledger.sql` (`docs/migrations.md`, "ledger"). `src/chatddx/store/store.py:Store.append` writes it, and
`Store.run` and `Store.score` read it back through `Record.parse`, `Run` and `Score`.

Every table has `payload text NOT NULL`, the record's `canonical` text and the source of truth, and
`doc jsonb NOT NULL`, its `jsonb` copy for queries. The 0006 CHECK on every table requires `doc = payload::jsonb` and
every key column to equal its value in `doc`. Item rows and canary calls reference their log's started row through a
`stage` column that can only be `'started'`, so the foreign key can point at it.

### `ledger.run_stage`
`RunStarted` and `RunFinished` rows.

| Column | Type | Holds |
| --- | --- | --- |
| `run` | `uuid NOT NULL` | `run` |
| `stage` | `text NOT NULL`, `'started'` or `'finished'` | `stage` |
| `trial` | `text`, FK → `factor.component` | `RunStarted.trial`; `NULL` for a finished row (CHECK: not `NULL` exactly when `stage = 'started'`) |
| `payload`, `doc` | | as above |

Primary key `(run, stage)`. CHECK (0006): `run = (doc->>'run')::uuid`, `stage = doc->>'stage'`,
`trial IS NOT DISTINCT FROM doc->>'trial'`.

### `ledger.run_item`
`RunItem` rows.

| Column | Type | Holds |
| --- | --- | --- |
| `run` | `uuid NOT NULL` | `run` |
| `stage` | `text NOT NULL DEFAULT 'started'`, CHECK `= 'started'` | constant |
| `"case"` | `text NOT NULL`, FK → `factor.component` | `key.case` |
| `replicate` | `integer NOT NULL` | `key.replicate` |
| `payload`, `doc` | | as above |

Primary key `(run, "case", replicate)`. FK `(run, stage)` → `run_stage`. CHECK (0006): `run`,
`"case" = doc #>> '{key,case}'`, `replicate = (doc #>> '{key,replicate}')::integer`.

### `ledger.canary_call`
`CanaryCall` rows.

| Column | Type | Holds |
| --- | --- | --- |
| `run` | `uuid NOT NULL` | `run` |
| `stage` | `text NOT NULL DEFAULT 'started'`, CHECK `= 'started'` | constant |
| `phase` | `text NOT NULL` | `phase` |
| `canary` | `integer NOT NULL` | `canary` |
| `payload`, `doc` | | as above |

Primary key `(run, phase, canary)`. FK `(run, stage)` → `run_stage`. CHECK (0006): `run`, `phase = doc->>'phase'`,
`canary = (doc->>'canary')::integer`. There is no column, and so no foreign key, for the run's canary set.

### `ledger.score_stage`
`ScoreStarted` and `ScoreFinished` rows.

| Column | Type | Holds |
| --- | --- | --- |
| `score` | `uuid NOT NULL` | `score` |
| `stage` | `text NOT NULL`, `'started'` or `'finished'` | `stage` |
| `run` | `uuid` | `ScoreStarted.run`; `NULL` for a finished row |
| `run_stage` | `text`, CHECK `= 'started'` | `'started'` for a started row, so the FK can point at the run's started row |
| `scoring` | `text`, FK → `factor.component` | `ScoreStarted.scoring`; `NULL` for a finished row |
| `payload`, `doc` | | as above |

Primary key `(score, stage)`. FK `(run, run_stage)` → `run_stage`. CHECK (0004): `stage = 'started'` exactly when
`run`, `run_stage` and `scoring` are all set. CHECK (0006): `score`, `stage`, `run IS NOT DISTINCT FROM
(doc->>'run')::uuid`, `scoring IS NOT DISTINCT FROM doc->>'scoring'`.

### `ledger.score_item`
`ScoreItem` rows.

| Column | Type | Holds |
| --- | --- | --- |
| `score` | `uuid NOT NULL` | `score` |
| `stage` | `text NOT NULL DEFAULT 'started'`, CHECK `= 'started'` | constant |
| `"case"` | `text NOT NULL`, FK → `factor.component` | `key.case` |
| `replicate` | `integer NOT NULL` | `key.replicate` |
| `view` | `integer NOT NULL` | `view` |
| `payload`, `doc` | | as above |

Primary key `(score, "case", replicate, view)`. FK `(score, stage)` → `score_stage`. CHECK (0006): `score`, `"case"`,
`replicate`, `view = (doc->>'view')::integer`.

### Insert-only (`0006`)
On every table, the triggers `insert_only` (BEFORE UPDATE OR DELETE, per row) and `insert_only_truncate` (BEFORE
TRUNCATE, per statement) call `factor.refuse_change()`, which raises `<schema>.<table> is insert-only`.

### Roles (`0005`)
PUBLIC loses all access to the schema and its tables. `chatddx_writer` gets `USAGE` and `SELECT, INSERT` on existing
tables and, through default privileges, on tables created later. `chatddx_reader` gets nothing, because `run_item` and
`score_item` hold case-derived records; the other tables sit beside them so each log stays in one schema.

### What the database checks, and what it doesn't
It checks that `doc` and the key columns agree with `payload`, that keys are unique (the same keys `check_run` and
`check_score` refuse duplicates of), that an item or canary call has its log's started row, that a score's started
row has its run's started row, that the trial, scoring and cases are stored components, and that nothing changes.

It doesn't
- parse or validate records, read `v`, or require canonical text;
- require a finished row to have a started row: the stage tables have no foreign key between stages;
- check the kind of a referenced component: `trial`, `scoring` and `"case"` may point at any component;
- tie a score item to a run item, or check `phase`, `canary`, `replicate` or `view` ranges;
- check seals, times, or anything `check_run` and `check_score` check.

## Known gaps
From `docs/ledger.md`, "Open design issues", where they concern this API:
- `Execution.timeout_s` isn't checked: a call's times span all its attempts.
- Nothing rebuilds a request to compare with `Call.request`.
- Canary outputs aren't compared between phases or runs.
- Canary calls and judge calls get no model check and no prompt-token check.
- `Call.system_fingerprint` is never compared.
- The finished row is outside the seal: its `at` and `findings` can change without `ledger.seal`.
- `Call` accepts a response that still holds `prompt_token_ids`.
- Records don't travel in a `Bundle`.
- Findings have no mechanism of their own beyond the finished rows and the check functions.

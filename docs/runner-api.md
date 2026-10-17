# Runner API

Reference for the `chatddx.runner` package. It was written from `src/chatddx/runner/*` and `docs/runner.md`. What a
run and a score do and why is in `docs/runner.md`; this file says what each name accepts, returns and raises. Types
from other packages are in their API docs: factors (`Trial`, `Execution`, `Skeleton`, `Judge`, `Scoring`, `Registry`,
`Finding`, …) in `docs/factors-api.md`, records (`Call`, `RunItem`, `ScoreItem`, `JudgeCall`, …) and the checks in
`docs/ledger-api.md`, `Inventory` in `docs/inventory-api.md`, `Store` and `Catalog` in `docs/store-api.md`.

Paths are relative to `src/chatddx/runner/` unless they start with `src/` or `docs/`.

## Contents
- [Package](#package)
- [Conventions](#conventions)
- [wire.py](#wirepy): HTTP and server-sent events
- [send.py](#sendpy): one call, `Halt`
- [gate.py](#gatepy): refusing an endpoint
- [prepare.py](#preparepy): an item's request
- [rounds.py](#roundspy): tools and rounds
- [run.py](#runpy): `Runner`, `Running`, run events
- [score.py](#scorepy): `Grader`, `Grading`, `judge_at`, `score_run`
- [Finding codes](#finding-codes)
- [Known gaps](#known-gaps)

## Package
`chatddx/runner/__init__.py` is empty: every name is imported by its module's path.

| Module | Builds on |
| --- | --- |
| `wire.py` | the standard library's `urllib` |
| `send.py` | `wire.py`, `chatddx.factors.{base,response,trial}`, `chatddx.ledger` |
| `gate.py` | `wire.py`, `chatddx.factors.{base,cases,engine,request,trial}`, `chatddx.inventory` |
| `prepare.py` | `chatddx.factors.{base,cases,engine,request,trial}`, `chatddx.inventory`, `chatddx.ledger`, `chatddx.store` |
| `rounds.py` | `send.py`, `chatddx.factors.{base,request,response,trial}`, `chatddx.ledger`, `chatddx.rig`, `chatddx.tools.shipped` |
| `run.py` | `gate.py`, `prepare.py`, `rounds.py`, `send.py`, `chatddx.{catalog,factors,identity,inventory,ledger,rig,store}` |
| `score.py` | `gate.py`, `send.py`, `run.py` (`Noted`), `chatddx.{catalog,factors,identity,inventory,ledger,rig,scorers,store}` |

Third-party packages: pydantic, and jsonschema in `rounds.py`. No HTTP client: `wire.py` uses `urllib`.

The bench is the caller (`src/chatddx/bench/runs.py`, `src/chatddx/bench/seen.py`), for the repl and the API.

## Conventions
**Three steps.** `Runner.start` and `Grader.start` check everything that can be checked, then write the start row and
the owner entry, and return `Running` or `Grading`. `send` sends and writes each item as it's done. `finish` writes
the finished row and returns what the ledger's check finds. Nothing is written when `start` raises.

**Connections.** `Runner` and `Grader` take a psycopg connection in autocommit mode, so each row is written as it
comes and a send that stops keeps what it wrote.

**Threads.** Everything happens on the caller's thread, except an item's calls and tools in a run above concurrency
1. `halt` is the one method meant to be called from another thread.

**Events.** `send(on_event)` calls `on_event` on the caller's thread as things happen. `None` ignores them.

**Errors.**

| Exception | When |
| --- | --- |
| `gate.Refused` | `Runner.start`, `Grader.start` and `judge_at` refuse an endpoint (see "gate.py"). |
| `ValueError` | A connection not in autocommit mode; a concurrency above the endpoint's `max_jobs`; a run that hasn't finished; judge calls above concurrency 1; a judge reading the case; judges without an inventory; `finish` called twice. |
| `LookupError` | Tool or scorer code that isn't shipped, or not at its pinned version (`chatddx.rig.entry`); a scorer whose views don't fit its code (`chatddx.scorers.shipped.function`); a component, endpoint or source that doesn't exist. |
| `pydantic.ValidationError` | A record the runner builds breaks its rules, as `verify_at` without a canary set. |
| `KeyboardInterrupt` | Raised again by `send` once the calls an interrupt stopped are written. |
| `send.Stopped` | Raised by `send.send` only; `rounds.converse`, `Running` and `Grading` catch it. |

**Findings.** All findings the runner notes are warnings but `answer.salvaged`, which is info. They are emitted as
`Noted` while sending and kept in the finished row (`RunFinished.findings`, `ScoreFinished.findings`). `finish`
returns the ledger check's findings, not these. Codes are under "Finding codes".

## wire.py

### `type Chunk = dict[str, JsonValue]`
One parsed event of a stream.

### `class Rejected(Exception)`
An HTTP error status, or an error in a stream. `status: int`, `body: dict[str, JsonValue] | None` (the body, when it
is a JSON object). Its message is `HTTP <status>: <message>`, the message being the body's `error.message`, its
`message`, its `error` when that is a string, the first 200 characters of its JSON, or `no body`.

### `class Unfinished(ConnectionError)`
A stream that ended before `[DONE]`.

### `request(url, body, secret=None) -> urllib.request.Request`
A `POST` to `<url>/chat/completions` (a trailing slash on `url` dropped), the body as JSON, with
`Accept: text/event-stream`, and `Authorization: Bearer <secret>` when `secret` is given.

### `post(url, body, *, secret=None, timeout=None) -> Stream`
Sends the request and returns once the response's headers are in. `timeout` bounds connecting and each read. Raises
`Rejected` for an HTTP error status, and `OSError` (`urllib.error.URLError`, `TimeoutError`, …) when the connection
fails.

### `served(url, *, secret=None, timeout=None) -> list[str]`
GETs `<url>/models` (a trailing slash on `url` dropped), with `Authorization: Bearer <secret>` when `secret` is
given, and returns `str(entry["id"])` for each entry of the response's `data` (`[]` when `data` is missing or empty;
`"None"` for an entry without `id`). Raises `OSError` when the server can't be reached, times out or answers with an
HTTP error (`urllib.error.URLError`, `HTTPError`); `json.JSONDecodeError` for a body that isn't JSON;
`AttributeError` for JSON that isn't an object, or an entry that isn't.

### `class Stream`
An open response.

| Member | Description |
| --- | --- |
| `status: int` | The response's HTTP status. |
| `__iter__() -> Iterator[Chunk]` | The chunks, as `chunks` reads them. |
| `interrupt()` | Shuts the connection down, from any thread, so a read under way ends with an error. Idempotent; does nothing after `close`. |
| `close()` | Closes the response. `Stream` is a context manager that closes on exit. |

### `events(lines: Iterable[bytes]) -> Iterator[str]`
The `data` fields of each server-sent event, joined by newlines. Other fields are ignored.

### `chunks(lines: Iterable[bytes]) -> Iterator[Chunk]`
Each event's data parsed as a JSON object, up to `[DONE]`. Raises `ValueError` `a chunk that isn't a JSON object:
<data>` (the first 200 characters), `Rejected(200, chunk)` for a chunk with an `error`, and `Unfinished` `the stream
ended before [DONE]`.

### `assemble(chunks: Iterable[Chunk]) -> dict[str, JsonValue]`
The completion the chunks add up to, as an unstreamed request would have had it: `id`, `object`
(`"chat.completion"`), `created`, `model`, one choice, `usage`, `system_fingerprint` and `prompt_token_ids`, each when
a chunk had it. The choice holds the message (`role`, every string field of the deltas joined, `tool_calls` merged
by index), `finish_reason`, `stop_reason` when given, and `token_ids` joined. Only choice 0 is read.

## send.py

### Names
`STREAM` is what `send` adds to a body: `{"stream": True, "stream_options": {"include_usage": True}}`. `STOPPED` is
`"stopped"`.

### `class Delta`
A piece of what a call streams: `kind: Literal["reasoning", "content", "tool_call"]`, `text: str`, `tokens: int`,
the call's completion tokens so far, counted by a chunk's `token_ids`, or one a delta when it has none. A chunk's
reasoning is read once, under `reasoning`, else `reasoning_content` (`chatddx.factors.response.REASONING`).

### `class Stopped(Exception)`
A call stopped by an interrupt or a halt. `call: Call` is the call as it stood, with `error` `"stopped"`.

### `class Halt`
Stops the calls that watch it, from any thread.

| Member | Description |
| --- | --- |
| `set()` | Sets it, and interrupts every stream it watches. |
| `is_set() -> bool` | |
| `wait(timeout: float) -> bool` | Waits up to `timeout` seconds; `True` once it is set. |
| `watching(stream)` | A context manager that interrupts `stream` when the halt is set, or at once when it is already set. |

### `send(url, body, *, execution=None, secret=None, on_delta=None, key=None, backoff=1.0, halt=None, started_at=None) -> Call`
Sends `body` streaming and returns the call. `Call.request` is `fingerprint_request(body, key)`, taken before
`STREAM` is added, and `Call.response` the assembled completion, its `prompt_token_ids` moved to
`Call.prompt_tokens` (`docs/ledger-api.md`, "call.py"). `started_at` defaults to now, `execution` to `Execution()`.
`on_delta` is called with each `Delta`.

A connection that fails (`OSError`), or a 429 or 5xx, is tried again after `backoff * 2 ** (n - 1)` seconds, `n`
the attempt that failed, up to `execution.retries` times. `Call.attempts` counts the attempts.

| Outcome | `status` | `error` | `response` |
| --- | --- | --- | --- |
| The stream ended at `[DONE]` | the status | `None` | the completion |
| An error status not tried again | the status | `HTTP <status>: <message>` | the error body, or `None` |
| A connection that failed, out of attempts | `None` | `<exception type>: <message>` | `None` |
| `execution.whitespace_limit` whitespace content tokens in a row | the status | `stopped: nothing but whitespace for <n> tokens` | what came |
| `execution.timeout_s` passed since the stream started | the status | `stopped: no end after <timeout_s> s` | what came |
| An error in the stream | the status | `<exception type>: <message>`, as `Unfinished: the stream ended before [DONE]` or `TimeoutError: timed out` | what came |

The cutoffs are checked as chunks come. A `KeyboardInterrupt` while sending, or `halt` set, raises `Stopped`, its
call with `error` `"stopped"` and what came; `halt` also ends the pause between attempts. A halt can't end a call
waiting for the response's headers.

## gate.py

### `class Refused(Exception)`
The endpoint may not get the request.

### `check(inventory, get, endpoint, trial, timeout=10.0) -> str | None`
`admit` for `trial.engine`, `trial.cases`, whether the trial's skeleton has tools, and `whose` `"trial"`.

### `admit(inventory, get, endpoint, engine, cases, tools, whose, timeout=10.0) -> str | None`
`bar`, then `secret`, then confirms the endpoint: the server at its `url` (`wire.served`, with the secret and
`timeout`) must list the name `engine` is served under, `served_model_name(engine, get)`. Returns the secret, or
`None` when the endpoint has no credential.

### `bar(inventory, get, endpoint, engine, cases, tools, whose) -> None`
Refuses what holds for as long as the World is as it is. `admit` adds what may pass later. The bench uses `bar`
through `judge_at`, to tell a scorer that will never apply from one that may (`docs/runner.md`, "What applies to a
run").

### `secret(inventory, endpoint) -> str | None`
The value of the environment variable the endpoint's `credential` names, or `None` when it names none.

### Refusals
`Refused`, in the order they're checked:

| Message | Raised by |
| --- | --- |
| an endpoint, source or case that doesn't exist (the `LookupError`'s message) | `bar` |
| `endpoint '<name>' serves engine <digest>, the <whose>'s is <digest>` | `bar` |
| `endpoint '<name>' isn't cleared for source <names>, which is sensitive` | `bar` |
| `the configuration's tools would get content from source <names>, which is sensitive, and tools can't be cleared yet` | `bar` |
| `endpoint '<name>' needs the secret in $<VARIABLE>, which isn't set` | `secret` |
| `endpoint '<name>' can't be confirmed: <reason>`, the reason `served_model_name`'s `StructuralError` or `wire.served`'s `OSError` | `admit` |
| `endpoint '<name>' can't be confirmed: it serves <listed names, joined by ", ", or 'nothing'> at <url>, not <served name>` | `admit` |

## prepare.py

### `class PreparedItem`
A run item ready to send: `key: ItemKey`, `seed: int`, `vignette: Fingerprint` (the vignette as read),
`body: dict[str, JsonValue]` (the rendered request), `findings: tuple[Finding, ...]` (from preparing the case).

### `class Items(conn, inventory, get, trial)`
Prepares a trial's items. `trial` is a digest.

| Member | Description |
| --- | --- |
| `trial: Trial`, `skeleton: Skeleton` | Resolved once. |
| `case(case: str, layout: AppendixLayout) -> Prepared` | Fetches the case's vignette (`chatddx.store.fetch_vignette`) and prepares it (`chatddx.factors.cases.prepare_case`) with the trial's cleanup. |
| `item(key: ItemKey) -> PreparedItem` | `case` with the skeleton's appendix layout, then `Skeleton.render` for the trial's engine's `served_model_name` and the replicate's seed. |

Raises `LookupError` (a vignette or source that can't be found, a replicate out of range) and `StructuralError`
(a case that can't be prepared). `Running` notes either as `case.unreadable`; the bench's `rendered_again` uses
`Items` to show a request as it was sent.

## rounds.py

### `class ToolStopped(Exception)`
A tool stopped by an interrupt while it ran. `run: ToolRun` is its run, with `result` `error: stopped` and `error`
`"stopped"`.

### `class Toolbox`
A skeleton's tools, loaded. `functions: Mapping[str, Callable]` and `parameters: Mapping[str, Validator]` by tool
name, `answer: str | None` (the answer tool's name, when the contract is a `ToolOutput`), `max_rounds: int`,
`code: tuple[ToolCode, ...]` (each tool's digest and the version of its code).

| Member | Description |
| --- | --- |
| `pending(call: Call) -> tuple[ToolCall, ...]` | The tool calls of the call's response; none when the call has an error or no response, or calls the answer tool. |
| `run(call: ToolCall) -> ToolRun` | Runs one tool call. An error becomes the run's `error`, and its `result` is `error: <error>`. A `KeyboardInterrupt` raises `ToolStopped`. |

`run`'s errors:

| Error | When |
| --- | --- |
| `no tool named '<name>'` | The call names no tool of the skeleton. |
| `the arguments aren't JSON: <reason>` | |
| `the arguments aren't an object` | |
| `the arguments don't fit the parameters: <message>` | The most relevant jsonschema error against the tool's `parameters`. |
| `the tool returned <type>, not text` | |
| `<exception type>: <message>` | The tool raised. |

### `load(skeleton: Skeleton, get: Resolver) -> Toolbox | None`
`None` when the skeleton has no `max_rounds`. Each tool's code is looked up in `chatddx.tools.shipped.TOOLS` at the
version the tool pins. Raises `LookupError` `<entry point> isn't shipped with <rig>, only <entry points>` or `<entry
point> is at version <v> in <rig>, not <pinned>`.

### `class Exchange`
An item's calls: `call: Call` (the first), `turns: tuple[Turn, ...] = ()` (the rounds), `stopped: bool = False`.

### `converse(url, body, toolbox, *, execution, secret, on_delta, on_tool, halt=None, started_at=None) -> Exchange`
Sends `body`, then, while `toolbox` has pending calls and fewer than `max_rounds` rounds were made, runs them in order
(`on_tool` with each run), and sends the next request (`chatddx.factors.request.next_request`). Never raises
`Stopped`: a stopped call ends the exchange with `stopped=True`. When stopped:

| When | Kept |
| --- | --- |
| A `Stopped` on the first call | the first call |
| `halt` set before a round's next tool runs, or after its last | the rounds before, and the tools of this round that ran, without a call |
| An interrupt inside a tool (`ToolStopped`) | the rounds before, and the tools of this round that ran, the stopped one last, without a call |
| Another `KeyboardInterrupt` while a round's tools run | the rounds before, and the tools of this round that ran, without a call |
| A `Stopped` on a round's call | the rounds before, and this round with its stopped call |

## run.py

### Events
`type Event = ItemStarted | Streamed | ToolRan | ItemEnded | CanaryEnded | Noted`, frozen dataclasses:

| Event | Fields | When |
| --- | --- | --- |
| `ItemStarted` | `key: ItemKey`, `seed: int` | An item is prepared and about to be sent. |
| `Streamed` | `key`, `delta: Delta` | A piece of an item's call. |
| `ToolRan` | `key`, `run: ToolRun` | A tool ran. |
| `ItemEnded` | `item: RunItem` | An item is written. |
| `CanaryEnded` | `call: CanaryCall` | A canary call is written. |
| `Noted` | `finding: Finding` | A finding (see "Finding codes"). |

### `class Runner(conn, inventory, by: Person)`
Raises `ValueError` `the runner needs a connection in autocommit mode`.

### `Runner.start(trial, registry, endpoint, execution=None, canaries=None, verify_at=PHASES) -> Running`
In order:
1. adds `trial` and `canaries` to `registry`;
2. `gate.check`, for the secret;
3. `rounds.load`;
4. refuses an `execution.concurrency` above the endpoint's `max_jobs`: `ValueError` `endpoint '<name>' takes <n>
   requests at once, the execution sends <m>`;
5. builds `RunStarted` with a new id, `rig()` (chatddx at its installed version, with
   `CHATDDX_REVISION` as its revision when set), `execution` (default `Execution()`), the canary set, `verify_at`, the
   toolbox's `code` and `Endpoint(name, url)`; `verify_at` other than `PHASES` without a canary set
6. stores the trial and the canary set with what they refer to (`Store.add`), appends `RunStarted`, and notes `by` as
   the run's owner in the catalog.

### `Runner.resume(run: UUID) -> Running`
A `Running` for an unfinished run, holding the items and canary calls its log holds, so that `send` sends only what
it lacks. In order:
1. reads the run's log (`Store.run`, whose `LookupError` it raises), and refuses a finished one, `ValueError` `run
   <id> is finished`, and one sent to no endpoint, `ValueError` `run <id> was sent to no endpoint, so it can't resume`;
2. loads the trial and the canary set with what they refer to (`Store.load`);
3. `gate.check`, `rounds.load` and the endpoint's `max_jobs`, as `start` does, under the run's execution;
4. refuses an endpoint whose URL is another now: `ValueError` `endpoint '<name>' is at <url> now, and run <id> was
   sent to <url>`.

The finish notes `run.resumed` (see "Finding codes"), unless the log holds nothing and `rig()` is the rig that
started the run. Two `Running`s of one run collide on the ledger's key for an item; whoever resumes keeps it to one.

### `class Running`

| Member | Description |
| --- | --- |
| `run: UUID` | |
| `started: RunStarted` | |
| `stop()` | No more items start; the ones under way finish. |
| `halt()` | `stop`, and stops the calls under way, from any thread. |
| `send(on_event=None)` | Sends the start phase's canaries, the items, and the end phase's canaries (see below). |
| `finish() -> list[Finding]` | Writes `RunFinished` with the noted findings, and returns `check_run` of the run (`docs/ledger-api.md`). A second call raises `ValueError` `run <id> is finished`. |

`send` sends the items in `execution.schedule` order, skipping items and canary calls already written, and sends
nothing once the run is stopping or finished. A case `Items.item` can't prepare is noted `case.unreadable` and
skipped; one prepared emits `ItemStarted` and its findings. Canaries are sent one at a time; the items at concurrency
1 on the caller's thread, above it on a pool of `execution.concurrency` threads, a new item only once another is done.
Each item is written as `RunItem` when its exchange ends.

A stopped call stops the run. After a halt, `send` returns once the calls under way are written; after an interrupt,
it raises `KeyboardInterrupt` then. Another interrupt while they're written leaves them out. A worker's exception is
raised once the other calls are halted and written.

## score.py

### Names
`NO_EXPECTATION` is `{"reason": "no expectation"}`, the detail of every score item of a case the scoring has no
expectation for.

`type Event = ItemScored | JudgeAsked | Streamed | JudgeAnswered | Noted`, frozen dataclasses:

| Event | Fields | When |
| --- | --- | --- |
| `ItemScored` | `item: ScoreItem` | Each score item written. |
| `JudgeAsked` | `key`, `scorer`, `view`, `judge`, `seed_index` | Before a judge call is sent. |
| `Streamed` | `key`, `delta: Delta` | A piece of the judge call under way, as the runner's. |
| `JudgeAnswered` | `key`, `view`, `call: JudgeCall`, `verdict` | A judge call ended; `verdict` is its answer as read, or `None`. |
| `Noted` | `finding` | A finding noted. |

### `judge_at(inventory, get, ref, cases, named=None) -> tuple[Judge, Skeleton, str]`
The judge `ref`, its skeleton, and the endpoint its calls go to: `named`, or the one endpoint serving the judge's
engine (`Inventory.serving`, which `src/chatddx/bench/seen.py:Seen.at` uses for a run).

| Raises | Message |
| --- | --- |
| `ValueError` | `judge <digest> reads the <vignette and/or appendices>, which no judge is given`, when its skeleton has either slot |
| `ValueError` | `judged views need the World's inventory`, when `inventory` is `None` |
| `gate.Refused` | `no endpoint serves engine <digest>`, or `<names> serve engine <digest>; name the one to use`: `Inventory.serving`'s `LookupError`, without `named` |
| `gate.Refused` | as `gate.bar` |

### `class Grader(conn, inventory: Inventory | None, by: Person)`
Raises `ValueError` `the scoring pass needs a connection in autocommit mode`. The inventory is needed only by judged
views.

### `Grader.start(run, scoring, registry, endpoints=None, execution=None) -> Grading`
`endpoints` maps a judge's digest to the endpoint its calls go to, for an engine more than one endpoint serves. In
order:
1. reads the run: `LookupError` `run <id> is not in the store` (`Store.run`), `ValueError` `run <id> hasn't
   finished`;
2. `ValueError` `judge calls are sent one at a time yet` for an `execution.concurrency` above 1;
3. adds `scoring` to `registry`, and finds its scorer's code (`chatddx.scorers.shipped.function`, `LookupError`);
4. for each of the scorer's judges, `judge_at` and `gate.admit`, for the run's cases;
5. stores the scoring, appends `ScoreStarted` with a new id, `rig()`, the code's version, `execution` (default
   `Execution()`) and each judge's `JudgeEndpoint`, and notes `by` as the score's owner.

### `class Grading`

| Member | Description |
| --- | --- |
| `score: UUID` | |
| `started: ScoreStarted` | |
| `halt()` | Stops the judge call under way and the scoring, from any thread. |
| `send(on_event=None)` | Grades the run's items in `execution.schedule` order, skipping those already graded (see below). |
| `finish() -> tuple[Score, list[Finding]]` | Writes `ScoreFinished` with the noted findings, and returns the score and `check_score` (`docs/ledger-api.md`). A second call raises `ValueError` `score <id> is finished`. |

For each run item, `send` reads the answer from its last call (`chatddx.scorers.answer.read`, by the run skeleton's
contract), noting `answer.unread` or `answer.invalid`, and writes one `ScoreItem` per view, together:
- with no expectation for the case, every view's value is `None` with `NO_EXPECTATION`;
- an unjudged view is `score_view` of the answer;
- a judged view is `chatddx.scorers.verdicts.asked` first: when it gives a `Scored`, as for no answer, that is the
  item. Otherwise each of the judge's seeds renders the judge skeleton with the fills, for the judge engine's
  `served_model_name`, and sends it as a `JudgeCall`; its verdict is read by the judge skeleton's contract, noting
  `verdict.unread` or `verdict.invalid`. The view is `score_view` with the verdicts, one per seed sent, `None` for a
  seed without one.

A stopped judge call keeps that view's verdicts so far, leaves out the item's judged views after it, writes the item,
and stops the scoring: `send` returns after a halt, and raises `KeyboardInterrupt` after an interrupt.

### `score_run(conn, run, scoring, registry, by, inventory=None) -> tuple[Score, list[Finding]]`
`Grader.start`, `send` and `finish`, with the default endpoints and execution.

## Finding codes
Noted while sending, in the finished row. What `check_run` and `check_score` find is in `docs/ledger-api.md`, "Finding
codes".

| Code | Noted by | Subject | Message |
| --- | --- | --- | --- |
| `case.unreadable` | `Running.send` | item key | the `LookupError` or `StructuralError` preparing it |
| `case.drift` | `Running.send`, from `prepare_case` | item key | as `docs/factors-api.md` has it |
| `answer.unread` | `Grading.send` | item key | the problem reading it, as `no response`, `no content`, `the content isn't JSON: <reason>`, with `; the call ended with: <error>` when the call has one |
| `answer.invalid` | `Grading.send` | item key | how the answer breaks the run skeleton's `output_schema` |
| `verdict.unread` | `Grading.send` | item key | `view <i>, seed <n>: <problem>`, with `; the call ended with: <error>` when the call has one |
| `verdict.invalid` | `Grading.send` | item key | `view <i>, seed <n>: <problem>` |
| `answer.salvaged` | `Grading.send` | item key | `cut short, and read with its structure closed`, with `; the call ended with: <error>` when the call has one; level `info` |
| `run.resumed` | `Runner.resume` | none | `resumed after <n> of <m> items`, level `info`, when the log holds something; a warning with ` by <rig>, where <rig> started it` when another rig resumes it than started it |

## Known gaps
From `docs/runner.md`, "Open design issues", where they concern this API:
- A halt can't end a call waiting for its response's headers.
- `Toolbox.run` has no time limit.
- Canary calls emit no `Streamed`.
- `send.send` takes a `key`, but nothing in the package passes one.
- `Grader.start` refuses judge calls above concurrency 1, and confirms every judge's endpoint, even when no item
  needs a judge.
- `send` again after a worker's exception isn't tested.

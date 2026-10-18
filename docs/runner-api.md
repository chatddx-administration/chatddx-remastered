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
- [Package](#package)
- [Conventions](#conventions)
- [wire.py]: HTTP and server-sent events
- [send.py](#sendpy): one call, `Halt`
- [gate.py](#gatepy): refusing an endpoint
- [prepare.py]: an item's request, and a run's rendered again
- [outcome.py](#outcomepy): how an item ended, and the tokens it used
- [rounds.py]: tools and rounds
- [events.py](#eventspy): what a run and a score say as they go
- [run.py](#runpy): `Runner`, `Running`
- [score.py](#scorepy): `Grading`, `judge_at`
- [Finding codes](#finding-codes)

## Package
`chatddx.runner` re-exports `Runner`, `Running`, `Grading`, `Halt`, `Refused` and `judge_at`; the events,
`RunEvent`, `ScoreEvent`, `ItemStarted`, `Streamed`, `ToolRan`, `ItemEnded`, `CanaryEnded`, `Noted`, `ItemScored`,
`JudgeAsked` and `JudgeAnswered`, with `Delta`; what an edge reads of a run the runner wrote, `outcome`, `Outcome`,
`usage`, `used` and `rendered_again`; and `STOPPED` and `NO_EXPECTATION`. Edges import from `chatddx.runner`, never by
path. The rest is how the package is built: its own tests reach it by path, and so do tests that stand in for a piece
of it (`monkeypatch.setattr("chatddx.runner.run.send", …)`).

| Module | Builds on |
| --- | --- |
| `wire.py` | the standard library's `urllib` |
| `send.py` | `wire.py`, `chatddx.factors.{base,response,trial}`, `chatddx.ledger` |
| `gate.py` | `wire.py`, `chatddx.factors.{base,cases,engine,request,scoring,trial}`, `chatddx.inventory` |
| `outcome.py` | `send.py`, `chatddx.factors.{request,response}`, `chatddx.ledger`, `chatddx.scorers.answer` |
| `prepare.py` | `chatddx.factors.{base,cases,engine,request,trial}`, `chatddx.inventory`, `chatddx.ledger`, `chatddx.store` |
| `rounds.py` | `send.py`, `chatddx.factors.{base,request,response,trial}`, `chatddx.ledger`, `chatddx.rig`, `chatddx.tools.shipped` |
| `events.py` | `send.py`, `chatddx.factors.base`, `chatddx.ledger` |
| `score.py` | `events.py`, `gate.py`, `send.py`, `chatddx.{catalog,factors,identity,inventory,ledger,rig,scorers,store}` |
| `run.py` | `events.py`, `gate.py`, `prepare.py`, `rounds.py`, `score.py`, `send.py`, `chatddx.{catalog,factors,identity,inventory,ledger,rig,store}` |

Third-party packages: pydantic, and jsonschema in `rounds.py`. No HTTP client: `wire.py` uses `urllib`.

The bench is the caller (`src/chatddx/bench/runs.py`, `src/chatddx/bench/seen.py`), for the repl and the API.

## Conventions
**Three steps.** `Runner.start` and `Runner.score` check everything that can be checked, then write the start row and
the owner entry, and return `Running` or `Grading`. `send` sends and writes each item as it's done. `finish` writes
the finished row and returns what the ledger's check finds. Nothing is written when `start` raises.

**Connections.** `Runner` takes a psycopg connection in autocommit mode, so each row is written as it comes and a send
that stops keeps what it wrote.

**Threads.** Everything happens on the caller's thread, except an item's calls and tools in a run above concurrency
1. `Halt.set` is the one call meant for another thread: once it is set, a `send` given the halt stops at once, before
or while it sends, and one `Halt` can be given to several sends in turn.

**Events.** `send(on_event)` calls `on_event` on the caller's thread as things happen. `None` ignores them.

**Errors.**

| Exception | When |
| --- | --- |
| `Refused` | `Runner.start`, `Runner.resume`, `Runner.score` and `judge_at` refuse an endpoint, or a judge that reads the case (see "gate.py"). |
| `ValueError` | A connection not in autocommit mode; a concurrency above the endpoint's `max_jobs`; a run that hasn't finished; judge calls above concurrency 1; `finish` called twice. |
| `LookupError` | Tool or scorer code that isn't shipped, or not at its pinned version (`chatddx.rig.entry`); a scorer whose views don't fit its code (`chatddx.scorers.shipped.function`); a component, endpoint or source that doesn't exist. |
| `pydantic.ValidationError` | A record the runner builds breaks its rules, as `verify_at` without a canary set. |
| `KeyboardInterrupt` | Raised again by `send` once the calls an interrupt stopped are written. |

**Findings.** All findings the runner notes are warnings but `answer.salvaged`, which is info. They are emitted as
`Noted` while sending and kept in the finished row (`RunFinished.findings`, `ScoreFinished.findings`). `finish`
returns the ledger check's findings, not these. Codes are under "Finding codes".

## send.py

| `watching(interrupt: Callable[[], None])` | A context manager that calls `interrupt` when the halt is set, or at once when it is already set: a stream's `interrupt`, or another halt's `set`. |

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

### `send(url, body, *, execution=None, secret=None, on_delta=None, backoff=1.0, halt=None, started_at=None) -> Call`
Sends `body` streaming and returns the call. `Call.request` is `fingerprint_request(body)`, taken before `STREAM` is
added, and `Call.response` the assembled completion, which the call keeps without its `prompt_token_ids`, their
fingerprint in `Call.prompt_tokens` (`docs/ledger-api.md`, "call.py"). `started_at` defaults to now, `execution` to
`Execution()`. `on_delta` is called with each `Delta`.

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

### `admit(inventory, get, endpoint, trial, judge=None, timeout=10.0) -> str | None`
`bar`, then the secret the endpoint's `credential` names, then confirms the endpoint: the server at its `url`
(`wire.served`, with the secret and `timeout`) must list the name the engine is served under,
`served_model_name(engine, get)`, the engine being the judge's when one is given, else the trial's. Returns the
secret, or `None` when the endpoint has no credential.

### `bar(inventory, get, endpoint, trial, judge=None) -> None`
Refuses what holds for as long as the World is as it is, for the trial's cases. `admit` adds what may pass later.
`judge_at` uses it to tell a scorer that will never apply from one that may (`docs/runner.md`, "What applies to a
run").

### Refusals
`Refused`, in the order they're checked:

| Message | Raised by |
| --- | --- |
| `judge <digest> reads the <vignette and/or appendices>, which no judge is given`, for a judge whose skeleton has either slot | `bar` |
| an endpoint, source or case that doesn't exist (the `LookupError`'s message) | `bar` |
| `endpoint '<name>' serves engine <digest>, the <whose>'s is <digest>` | `bar` |
| `endpoint '<name>' isn't cleared for source <names>, which is sensitive` | `bar` |
| `the configuration's tools would get content from source <names>, which is sensitive, and tools can't be cleared yet` | `bar` |
| `endpoint '<name>' needs the secret in $<VARIABLE>, which isn't set` | `admit` |
| `endpoint '<name>' can't be confirmed: <reason>`, the reason `served_model_name`'s `StructuralError` or `wire.served`'s `OSError` | `admit` |
| `endpoint '<name>' can't be confirmed: it serves <listed names, joined by ", ", or 'nothing'> at <url>, not <served name>` | `admit` |

## outcome.py

### `type Outcome = Literal["stopped", "errored", "unread", "completed", "invalid", "valid", "salvaged"]`

### `outcome(skeleton: Skeleton, item: RunItem) -> tuple[Outcome, str | None]`
How an item ended, by its last call read through `chatddx.scorers.answer.read`, and why, when there is something to
say. The first that holds:
1. `stopped`: the call's error is the runner's `STOPPED`, or the item's last turn has no call, since its tools ran and
   the request after them was never sent.
2. `errored`, with the call's error, or `unread`, with why the answer couldn't be read: there is no answer.
3. `salvaged`, with what the schema refused, else the call's error: the answer was read from a structured answer cut
   short, its structure closed.
4. `completed`, with the call's error: the skeleton has no `output_schema`.
5. `invalid`, with the call's error, else what the schema refused; or `valid`, with the call's error.

### `usage(item: RunItem) -> tuple[int, int]`
The prompt and completion tokens of all the item's calls, summed.

### `used(call: Call) -> tuple[int, int]`
The prompt and completion tokens of one call, from its response's `usage`; a count that isn't an `int` is 0. Without
`usage`, as a stream cut short ends before it, the completion tokens are the `token_ids` its first choice holds, and
the prompt tokens 0.

## events.py
Frozen dataclasses. `type RunEvent = ItemStarted | Streamed | ToolRan | ItemEnded | CanaryEnded | Noted` and
`type ScoreEvent = ItemScored | JudgeAsked | Streamed | JudgeAnswered | Noted`; the tables below, `Event` read as
`RunEvent` under run.py and as `ScoreEvent` under score.py.

### ScoreEvent
`type Event = ItemScored | JudgeAsked | Streamed | JudgeAnswered | Noted`, frozen dataclasses:

| Event | Fields | When |
| --- | --- | --- |
| `ItemScored` | `item: ScoreItem` | Each score item written. |
| `JudgeAsked` | `key`, `scorer`, `view`, `judge`, `seed_index` | Before a judge call is sent. |
| `Streamed` | `key`, `delta: Delta` | A piece of the judge call under way, as the runner's. |
| `JudgeAnswered` | `key`, `view`, `call: JudgeCall`, `verdict` | A judge call ended; `verdict` is its answer as read, or `None`. |
| `Noted` | `finding` | A finding noted. |

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

### `Runner.score(run, scoring, registry, execution=None) -> Grading`
Starts the scoring pass: what it checks and writes is under score.py.

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
| `send(on_event=None, halt=None)` | Sends the start phase's canaries, the items, and the end phase's canaries (see below); `halt`, once set from any thread, stops the calls under way, and no more start. A run halted once is stopped for good. |
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

### `judge_at(inventory, get, trial: Trial, judge: str) -> str`
The endpoint the judge's calls go to: the one serving its engine (`Inventory.serving`), barred as `gate.bar` bars it
for the trial's cases.

| Raises | Message |
| --- | --- |
| `Refused` | `no endpoint serves engine <digest>`, or `<names> serve engine <digest>; name the one to use`: `Inventory.serving`'s `LookupError` |
| `Refused` | as `gate.bar`, for a judge |

### `Runner.score(run, scoring, registry, execution=None) -> Grading`
In order:
1. reads the run: `LookupError` `run <id> is not in the store` (`Store.run`), `ValueError` `run <id> hasn't
   finished`.
2. `ValueError` `judge calls are sent one at a time yet` for an `execution.concurrency` above 1.
3. adds `scoring` to `registry`, and finds its scorer's code (`chatddx.scorers.shipped.function`, `LookupError`);
4. `judge_at` and `gate.admit`, for each judge.
5. stores the scoring, appends `ScoreStarted` with a new id, `rig()`, the code's version, `execution` (default
   `Execution()`) and each judge's `JudgeEndpoint`, and notes `by` as the score's owner.

### `class Grading`

| Member | Description |
| --- | --- |
| `score: UUID` | |
| `started: ScoreStarted` | |
| `send(on_event=None, halt=None)` | Grades the run's items in `execution.schedule` order, skipping those already graded (see below); `halt`, once set from any thread, stops the judge call under way and the scoring. |
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

## Testing
- `test_outcome.py`: each outcome but `salvaged`, which `src/chatddx/repl/test/test_running.py` reads, and usage.
  Without a database.

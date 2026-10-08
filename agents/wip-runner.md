# The runner: work in progress

The runner sends a trial's requests to an engine and writes what happened to the ledger. It strings together
pieces that already existed:
- `render`, `Trial`, `Execution` and `prepare_case`;
- the ledger records, `Store` and the catalog;
- the World inventory with `url_of` and `confirm`;
- the fake vLLM.

This file split off from `agents/wip-repl.md`, which is parked. The repl is the runner's first caller, not its only
one: a portal, a worker and `chatddx samples` (`agents/wip-sample-data.md`, "Left behind") would call it too.

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
Phases 0–6 are done (`src/chatddx/runner/`). A trial runs at an endpoint, in the execution's order and up to its
concurrency, with tool rounds and between its canaries, and leaves a finished run log and its owner entry, and
`check_run` comes back clean. The scoring pass is built too (see "The scoring pass"): a finished run is scored under
a scoring, and `check_score` comes back clean.

It was checked:
- by the tests in `src/chatddx/runner/test/`;
- by hand: the `chatddx fake-vllm --runaway` process, started from `worlds/sample/inventory.toml`'s gpt-oss endpoint,
  ran three cases on `plan (openai/gpt-oss-20b)`. Each call was cut at 100 tokens of whitespace, the fake heard each
  hang-up, and the run recorded its endpoint and cutoff.
- by hand, for phase 4: the `chatddx fake-vllm --delay 0.01` process, started from the qwen endpoint, ran 4 cases × 2
  seeds shuffled at concurrency 4. The run took 1.0 s for 3.9 s of calls, and `check_run` came back clean. A SIGINT
  0.3 s in hung up the 4 calls in flight, the fake heard 4 hang-ups, and the 4 were recorded as stopped.
- by hand, for phase 5: on the same process, 3 cases × 2 seeds at concurrency 2, with the free-text recipe and a
  toolset of the test tools `lookup` and `broken`, gave 2 rounds per item and 12 tool runs, the failing tool's error
  recorded, and a clean `check_run`. `plan-web` was refused on the sensitive sample, and ran without a round on the
  sample declared not sensitive.
- by hand, for phase 6: on the same process, 3 cases × 2 seeds at concurrency 3 with a set of two canaries. Both
  start canaries finished before the first item call, both end canaries started after the last, and `check_run` came
  back clean.
- by hand, for the scoring pass: on the same process, the `plan` recipe on 3 cases, scored by the sample's `plan`
  scorer with the cases' targets. Every answer was read; the fake's diagnoses aren't in the targets, so the views gave
  0 ("not listed"), and `dont-miss` none ("no target").

Next: what's left of "Left" (see "Afterwards").

**Real engines aren't cleared yet.** `worlds/kompismoln/inventory.toml` has no `[cleared]` table, so the gate refuses
`pelle` and `malborg` for the sample. Clearing them is a human's statement to make.

## Decided
- **Clearance (wip-repl D1).** An interim list in the World inventory says which sources an endpoint is cleared
  for. A database grant can replace it later (`agents/wip-clearance.md`, "Open", 2).
- **Streaming (D2).** Streaming happens only on the wire. `Call.request` fingerprints `render`'s body, and the stream
  is reassembled into the completion that `Call.response` holds.
- **Seeds (D3).** `seed none` is dropped.
- **Dependencies (D4).** The runner uses none of `rich`, Typer, pydantic-ai or httpx, and speaks HTTP through the
  stdlib.
- **R1–R10, as recommended.**
  - R7 with a reservation from the user: `max_tokens` is the more beaten path. They hold:
    - `Sampling.max_output_tokens` is that path, and it stays: it goes in the skeleton and bounds every answer;
    - `Execution.whitespace_limit` bounds only a runaway, and saves the time one burns till its tokens run out;
    - `whitespace_limit = None` turns the cutoff off for a run.
  - If the cutoff turns out not to earn its place, removing it is a one-field change.

## What was built
### Phase 0: outside `runner/`
- **R4.** `RemoteEngine.served_model_name` returns `model`, so `check_run`, `confirm` and the runner read one name
  (`factors/engine.py`).
- **R1.** `Inventory.cleared` and `cleared_for` (`inventory/inventory.py`). The table is read only from the
  inventory's own file and checked against its endpoints and sources. `worlds/sample/inventory.toml` clears both fake
  endpoints for `sample`.
- **R3.** `RunStarted.endpoint` (`ledger/run.py:Endpoint`): the endpoint's name and URL, left out by default.
- **R7.** `Execution.whitespace_limit`, 100 by default (`factors/trial.py`).
- **Test helpers.**
  - The database fixtures moved from `store/test/conftest.py` to `src/chatddx/conftest.py`.
  - The fake in a thread is `chatddx.fake_vllm.server.serving`, used by the fake's own tests, the inventory's and
    the runner's.
  - `sample_plan` is defined once, in `src/chatddx/conftest.py`, and the runner's tests use it.

### Phase 1: `wire.py`
- **`post`** sends to `/v1/chat/completions` and returns a `Stream` of parsed SSE chunks. Closing the stream hangs
  up.
- **`Rejected`** holds an error answer's status and body. An error sent in place of a chunk is one too, with status
  200.
- **`assemble`** adds the chunks up to the unstreamed completion. On the fake, the result is the same for text, a
  schema, a named tool and required tools. The tests compare everything but `id`, `created` and the keys that come
  back as nulls.

### Phase 2: `send.py`
`send(url, body, execution=, secret=, on_delta=, key=, backoff=, halt=, started_at=)` returns a `Call`:
- **The body.** `stream` and `stream_options.include_usage` are added after fingerprinting.
- **What's kept.** The prompt token ids become a fingerprint and leave the response.
- **Retries** only where no answer came back: a connection failure, a 429 or a 5xx. Backoff is exponential. An answer
  cut short is an answer, and isn't tried again.
- **Cut short**, keeping what came:
  - after `whitespace_limit` tokens of whitespace in a row;
  - when `timeout_s` has passed since the stream started, with the socket's timeout as a backstop.
- **A KeyboardInterrupt** hangs up and raises `Stopped`, which carries the call so far, with `error = "stopped"`.
  So does setting `halt`, for a call on another thread (phase 4).
- **`Delta` events** carry reasoning, content or tool-call text and the running token count, from each chunk's
  `token_ids`.

### Phase 3: `gate.py` and `run.py`
**`gate.check`** refuses before anything is written:
- an endpoint serving another engine than the trial's (a check the plan hadn't listed);
- a sensitive source the endpoint isn't cleared for;
- tools on a sensitive source;
- an endpoint that `confirm` can't confirm.

**`gate.secret`** reads the variable an endpoint's `credential` names (R5) and refuses when it isn't set. The secret
goes only into the `Authorization` header; a test checks that no stored row holds it.

**`Runner(conn, inventory, by)`** refuses a connection that isn't in autocommit mode (R6). `.start(trial, registry,
endpoint, execution)`:
1. Runs the gate, then refuses a `concurrency` above the endpoint's `max_jobs` (phase 4).
2. Loads the skeleton's tools (phase 5).
3. `Store.add`s the trial's closure, and the canary set's (phase 6).
4. Appends `RunStarted`, with `rig()`, the execution, the canary set and its phases, the tools' code and the
   endpoint. The row is built before anything is written, so phases without a canary set are refused first.
5. Writes the run's owner entry.

**`Running.send(on_event)`** sends the items in `Execution.schedule` order:
- each item is `fetch`, `prepare_case`, `render` with `engine.served_model_name`, then `send`, then appending a
  `RunItem`;
- a case that can't be read is a `case.unreadable` finding, and the run goes on (R8);
- `stop()` ends after the item under way;
- a KeyboardInterrupt during a call appends that item as stopped and is raised again (R9).

**`Running.finish()`** appends `RunFinished` with the findings the runner saw, then returns `check_run`'s.

**Changed from the plan: events go to a callback** (`on_event`), not to an iterator. A KeyboardInterrupt raised
while the caller handles an event then lands inside the runner's call, which records it. With a generator, it would
land in the caller's frame while the runner sat suspended at a `yield`. The events are `ItemStarted`, `Streamed`
(a `Delta` with its item's key, since phase 4), `ToolRan` (phase 5), `ItemEnded`, `CanaryEnded` (phase 6) and
`Noted`.

### Phase 4: order and concurrency
- **Order.** The runner tests run every order at concurrency 1 and 3, and check that items start in
  `Execution.schedule`'s order and that `check_run` stays quiet.
- **Concurrency above 1** (`run.py:Running._send_concurrently`). Calls go out on a thread pool of `concurrency`
  workers. Everything else stays on the caller's thread: preparing each item, the events, the writes, and the stamp
  of when each item was sent, which `send` takes as `started_at`. A worker's deltas and its finished call come back
  through a queue. `check_execution` stays quiet for two reasons:
  - items are stamped in schedule order, so `execution.order` doesn't fire, even when a worker starts late;
  - an item is sent only once a finished call has come back, so `execution.concurrency` doesn't fire.
- **Above `max_jobs`**, `Runner.start` refuses before anything is written. It's a `ValueError` like the tools refusal,
  not a gate `Refused`, which is kept for clearance.
- **Stopping.** `stop()` lets the calls in flight finish. A KeyboardInterrupt can't reach a worker, so the runner sets
  `send`'s `halt`. Each call then hangs up at its next chunk or in its backoff, and is recorded as stopped before the
  interrupt is raised again. Another KeyboardInterrupt while they hang up leaves them out of the log. A worker's
  unexpected exception is raised on the caller's thread, from its future.
- **Concurrency 1** keeps the serial path: a KeyboardInterrupt there hangs up at once, even mid-read.
- **Events carry the item's key** (`Streamed`), since deltas of items in flight interleave. That changed the serial
  path's events too, so a caller sees one shape whatever the concurrency.

### Phase 5: tool rounds
In `rounds.py`, which `run.py` calls for every item, with tools or without:
- **`load(skeleton, get)`** finds each tool's function with `core/rig.py:entry`, so a tool that pins other code than
  the running chatddx, or names nothing to call, is refused before anything is written. Each tool's code goes in
  `RunStarted.tool_code` as the running code.
- **`converse`** sends an item's first call, then a round per response that calls tools, up to `max_rounds`. A
  round runs the tools in the calls' order, then sends their results through `next_request`, and is recorded as a
  `Turn`. The rounds end in any of these cases, and `check_run` notes what a last response still calls
  (`tools.unanswered`):
  - a response calls no tool;
  - a response calls the answer tool;
  - a call has no whole answer (an error or a cutoff), whose tool calls may be cut short.
- **`Toolbox.run`** calls a tool with the call's arguments as keyword arguments, and wants text back. The model is
  told `error: …` in place of a result, and the error is recorded, when the call names no tool of the skeleton, the
  arguments aren't a JSON object that fits the tool's `parameters`, or the tool raises or returns anything but text.
  A failing tool doesn't stop the run.
- **Stopping.** A KeyboardInterrupt or a halt keeps the rounds that have a call. A round stopped while its tools run
  has none, so its tools are left out (see "Left"). Above concurrency 1, an item's rounds run on its worker, and a
  halt is also checked before a round's tools.
- **`ToolRan`** carries the item's key and the `ToolRun`, after each tool.
- **The gate keeps refusing tools on a sensitive source.** The tests run on the sample with its source declared not
  sensitive, and with tools that don't leave the host (`runner/test/tools.py`).
- **`plan-web` runs without a round on the fake.** A native contract with tools sends `tool_choice: auto` beside a
  `response_format`, which then holds the whole answer (G8; `docs/vllm.md`, item 10).

### The scoring pass
- **`chatddx.scorers.answer.read(skeleton, response)`** reads the answer a scorer scores, by the skeleton's contract
  (wip-repl D5, a take; see below): a native answer is the content as JSON, a tool answer the answer tool's
  arguments, and a text answer the content, or, when the output has a schema, the JSON in it (the whole text, else
  the last fenced block that is JSON, else the last JSON object or array). It returns the value, or none with why,
  and where the value breaks the output schema. No truncated structure is salvaged.
- **`runner/score.py:score_run(conn, run, scoring, registry, by)`** scores a finished run. It refuses before writing
  a run that hasn't finished, a view with a judge, and a scorer whose code can't run (`scorers/scorer.py:function`).
  It stores the scoring, then reads the run's trial and the scoring back from the store. Each item's answer is read
  from its last call, after any tool rounds, and goes through every view (`scorers/scorer.py:score`). It writes
  `ScoreStarted`, the items of each run item in one transaction, then `ScoreFinished` and the score's owner entry,
  and returns `check_score`'s findings.
- **What the pass notes** in `ScoreFinished`: `answer.unread`, for an answer that can't be read, with the call's
  error when it has one; and `answer.invalid`, for an answer that breaks the output schema. An invalid answer is
  still scored.
- **A case without an expectation** gets its items with no value and `{"reason": "no expectation"}`, so the score is
  complete. `check_score` now warns about it (`score.no_expectation`), since any writer's score can be checked for it.
- **Where the reading lives.** D5's take was that scorer entry points call the reader, so the scorer's code pins it.
  Interface version 1 hands the entry point what the view's selectors pick, not the response, so the pass calls the
  reader instead. It is still pinned: only the running chatddx can score (`core/rig.py:entry`), and the reader is
  part of it.

### Phase 6: canaries
- **`Canary.render(model=)`** (`factors/trial.py`) makes a canary's request as `render` makes a skeleton's: its
  messages and body, the model, the seed when the canary has one, and `return_token_ids`.
- **`Runner.start(..., canaries=, verify_at=)`** takes a canary set and the phases to send it at, both phases by
  default. The set is stored with the trial, so `check_run` can resolve it from the store.
- **`Running.send`** sends the start canaries before the first item and the end canaries after the last, one at a
  time on the caller's thread, so they bracket the items whatever the concurrency and `canary.phase` stays quiet.
  Each is recorded as a `CanaryCall`, followed by a `CanaryEnded` event.
- **Stopping.** A KeyboardInterrupt during a canary records it as stopped. A stopped run sends no end canaries, and
  `check_run` counts them as missing (`run.incomplete`).
- **No clearance**, since canaries aren't case-derived, but they go only where the run goes: the gate, `confirm`
  included, has passed by then.

## Left
### From phase 5
- **A round stopped while its tools run is left out of the log.** A `Turn` needs its call, so tools that ran
  without one can't be recorded, even one that reached a third party, such as a web search. Two ways out:
  - `Turn.call` becomes optional, a change to what stored rows may hold;
  - the runner sends the round's call anyway and hangs it up at once, as a halt does now.

  This needs a decision.
- **Tools have no time limit of their own.** `web_search` gives up after 10 s, and a halt waits for a tool that's
  running.
- **The tool interface isn't versioned**, unlike the scorer's (`scorers/scorer.py`, version 1): keyword arguments in,
  text out.
- **The answer tool called beside a toolset tool** ends the item, and `check_run` notes the toolset call
  (`tools.unanswered`). The fake never does that, so no test covers it on the wire.

### From phase 6
- **No canary set is seeded.** The sample data has none, so a caller brings its own. Seeding one would take a
  `canary_set` table in the data set's `factors.toml` (`agents/wip-seed.md`).
- **Canary outputs aren't compared** (`docs/chatddx.md`, "Possible design issues", and its proposed amendment on
  what counts as the same output).
- **Canary calls stream without events**, since `Streamed` carries an item key.

### Afterwards
- **What the scoring pass leaves to its caller** is in the reads for a person (`agents/wip-repl.md`, phase 3):
  `Reads.scorers`, `Reads.scoring` (D8) and `Reads.outstanding` (`src/chatddx/store/reads.py`).
- **Judged views**, refused until judges run: the judge calls, recorded as `JudgeCall`s, and the scorer interface's
  next version (`agents/wip-sample-data.md`, "Free-text expectations").
- **`chatddx samples`** back on the runner.
- **A runner finding for reasoning that wasn't heeded**, like the old `bench/outcome.py:unheeded`.
- **Resuming.** `resume(run)` would append an unfinished log's missing items: `Running.send` already skips items
  that are in.
- **A summary of failed calls.** `check_run` says nothing about `Call.error`. A run whose every call was cut short
  checks clean, and only the items show it. A UI can count them, or the runner could note them.
- **`max_jobs` across runs.** Each run is held to its endpoint's `max_jobs`, but two runs on one endpoint can send
  twice that between them. vLLM queues what's over `--max-num-seqs` rather than refusing it, so the cost is batching
  that the runs' `execution` doesn't show.
- **A halted call waits for its next chunk.** An engine that stalls mid-stream, under an execution with no
  `timeout_s`, keeps its worker waiting after a KeyboardInterrupt, until a second one. Shutting the worker's socket
  down from the caller's thread would end the wait, but `wire.Stream` doesn't offer that yet.

## Still open from elsewhere
- **`return_token_ids` on remote engines** (`docs/factors.md`, "Proposed amendments"): a non-vLLM API may refuse
  it. `render` sends it for every engine.
- **Concurrent writers** (`docs/catalog.md`, "Concurrent writers"). The runner writes only its own run's rows and one
  owner entry.

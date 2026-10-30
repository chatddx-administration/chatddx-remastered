# Ledger

The ledger is the rig's account of what happened in the cage, "what was planned, what was sent and what came back"
(docs/chatddx.md, "Purpose"). Each run and each score is a log: records written as it goes, never changed, sealed when
it finishes, and checked against the factors it names.

`src/chatddx/ledger/` holds the records and the checks, and nothing else. The runner makes the records
(`src/chatddx/runner/run.py`, `src/chatddx/runner/score.py`), and the store writes and reads them
(`src/chatddx/store/store.py:Store.append`, `src/chatddx/store/store.py:Store.run`,
`src/chatddx/store/store.py:Store.score`) in schema `ledger`, whose tables, grants and triggers are in
docs/migrations.md, "ledger".

A log names the factors by digest and keeps no copy of them, and keeps a vignette or a request only as a fingerprint.
What it keeps whole is what can't be made again: the responses, the tools' results, the times and the values.

## How it works

### Logs and records

The records of a run's log and of a score's log:

| Record                                      | Holds                                                                                                                                                            | Sensitive |
| ------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------- |
| `src/chatddx/ledger/run.py:RunStarted`      | What the run was set to do: the trial, its execution, the canary set and the phases it probes at, the version of each tool's code, the endpoint, the rig's build | no        |
| `src/chatddx/ledger/run.py:RunItem`         | One case's replicate: the fingerprint of the vignette as read, the first call, and each tool round                                                               | yes       |
| `src/chatddx/ledger/run.py:CanaryCall`      | One canary's call, at the start or the end                                                                                                                       | no        |
| `src/chatddx/ledger/run.py:RunFinished`     | The findings the runner noted as it went, and the seal                                                                                                           | no        |
| `src/chatddx/ledger/score.py:ScoreStarted`  | What the score was set to do: the run, the scoring, the version of the scorer's code, its execution, each judge's endpoint, the rig's build                      | no        |
| `src/chatddx/ledger/score.py:ScoreItem`     | How one view graded one run item: its value, the scorer's detail, and each judge call                                                                            | yes       |
| `src/chatddx/ledger/score.py:ScoreFinished` | The findings the scoring pass noted as it went, and the seal                                                                                                     | yes       |

- An item is named by its `src/chatddx/ledger/record.py:ItemKey`, the case's digest and the replicate's index; a score's
  item by the key and the view's index. A score names its run, and a run may have many scores.
- `src/chatddx/ledger/run.py:Run` and `src/chatddx/ledger/score.py:Score` gather one log's records. They refuse rows of
  another log, and a finish before the start (`src/chatddx/ledger/record.py:check_log`), and nothing more: what a log
  should hold is the checks' (see "Checks").
- A log is only added to: the tables refuse to change or remove a row. A log that hasn't finished has no finish record,
  and a resumed run goes on adding to the same log.

### Calls and tool rounds

A `src/chatddx/ledger/call.py:Call` is one exchange with an engine: an item's, a round's, a canary's or a judge's.

- `request` is a fingerprint of the body, not the body, and of the body as made, without the stream options
  `src/chatddx/runner/send.py:send` adds: the body can be made again from the factors and the vignette, and its
  fingerprint set beside the one kept, as `src/chatddx/runner/prepare.py:rendered_again` does.
  `src/chatddx/ledger/call.py:fingerprint_request` sorts the body's keys, and only its own: the order within a JSON
  schema is part of what the model reads.
- `response` is the response as it came back, but its `prompt_token_ids`: the call keeps a fingerprint of them in
  `prompt_tokens` instead, which is how a prompt read can be compared without keeping it.
- `started_at` and `finished_at` span all the call's attempts, and `attempts` holds each one's times, status and error;
  `status` and `error` tell how the call went, and an error stands for why nothing, or not all, came back.

`RunItem.turns` are the item's tool rounds, each a `src/chatddx/ledger/call.py:Turn`: the tools the previous response
called, each run as a `src/chatddx/ledger/call.py:ToolRun` with its result and, if it failed, its error; then the call
that sent their results. A round stopped while its tools ran has no call, and only the last round may. `RunItem.calls`
is the first call and each round's, in order, so the item's answer is in the last one.

### Canonical form and versions

A record is kept as its canonical form (`src/chatddx/ledger/record.py:Record.canonical`), with `v`, its kind's schema
version, added; the store keeps these bytes as `payload`. Times are in UTC whatever offset they came with, and fields at
their default are left out, so adding a field with a default leaves earlier records' bytes, and their seals, as they
were. `src/chatddx/ledger/record.py:Record.parse` reads the bytes back and refuses another version (docs/backlog.md,
"Old versions readable").

### The seal

`Run.seal` and `Score.seal` hash the start record and every item and canary call record, sorted by their canonical
bytes, so the order rows are written or read in doesn't change it (`src/chatddx/ledger/record.py:seal_rows`). The finish
record, made by `Run.finish` or `Score.finish`, keeps it, and is the one row the seal doesn't cover.
`src/chatddx/ledger/record.py:check_seal` hashes the rows again: rows added, lost or read differently since the finish
give `ledger.seal`.

### Checks

`src/chatddx/ledger/run.py:check_run` and `src/chatddx/ledger/score.py:check_score` set a log beside the factors it
names, which the registry they are given must hold: for a run its trial and its canary set if it has one, for a score
its scoring and the run's trial, each with what it references. They give one of two things:

- A refusal, `StructuralError`, for a log the runner can't have written: canary calls not planned or repeated, items
  outside the trial or repeated, tool rounds that don't follow from the response before them or exceed the skeleton's
  rounds, tool code recorded for tools the skeleton lacks; a score of another run, items repeated, out of range or not
  in the run, judge calls by another judge than the view's, past the judge's seeds or repeated. A registry without what
  the log names refuses too. The messages are in docs/surfaces/ledger.md.
- Findings, for what the log shows didn't go as it was set to (see "Codes").

They read only the logs and the registry they are given, so they find the same whenever they run, and a log can be
checked before it finishes: what is missing and the seal are looked at only once it has. The findings a finish record
keeps are another kind, those the runner noted as it went, which can't be found again from the log (docs/glossary.md,
"Running" and "Scoring"). Who checks and when is in docs/glossary.md, "Checking a run" and "Checking a score".

### Sensitive records

`src/chatddx/ledger/record.py:Record.sensitive` marks the records with sensitive content in them: a run item (the
responses, the arguments the model gave tools and what the tools returned, and an engine's error, which may echo the
request), a score item (the judges' responses and the scorer's detail), and a score's finish (findings that may quote an
answer or an engine's error). Start records, a run's finish and canary calls are not. A vignette and a request are kept
only as fingerprints, but what came back may quote either. Who may read the ledger is in docs/migrations.md, "ledger",
and what is to come of it in docs/parts/clearance.md.

## Usage

Check a stored run, as the API does when it shows one (`src/chatddx/api/runs.py`):

```python
from chatddx.ledger import check_run
from chatddx.store import Store

store = Store(conn)
run = store.run(run_id)
started = run.started
roots = [started.trial, *([] if started.canaries is None else [started.canaries])]
for f in check_run(run, store.load(roots)):
    print(f.code, f.subject, f.message, sep=" | ")
```

For the sample World's scripted run `several`, whose engine answers one item with a 503 and cuts another short:

```
call.failed | case='sha256:41179e0c…' replicate=0 | HTTP 503: the engine is loading
call.failed | case='sha256:edd8df06…' replicate=0 | Unfinished: the stream ended before [DONE]
attestation.model | case='sha256:41179e0c…' replicate=0 | engine returned no model name, declared 'sha256:da96724f…'
attestation.prompt_tokens | None | 1 items have no prompt token fingerprint
```

Write a run's log, as the runner does (`src/chatddx/runner/run.py`), where `trial` and `case` are components in
`registry`, and `call` is what `src/chatddx/runner/send.py:send` returned:

```python
from datetime import UTC, datetime
from uuid import uuid4

from chatddx.ledger import Endpoint, ItemKey, Run, RunItem, RunStarted, check_run
from chatddx.rig import rig

_ = store.add(registry, [trial.digest])
started = RunStarted(
    run=uuid4(),
    at=datetime.now(UTC),
    rig=rig(),
    trial=trial.digest,
    endpoint=Endpoint(name="qwen3-8b@pelle", url=url),
)
store.append(started)
item = RunItem(
    run=started.run,
    key=ItemKey(case=case.digest, replicate=0),
    vignette=case.vignette.fingerprint,
    call=call,
)
store.append(item)
run = Run(started=started, items=(item,))
finished = run.finish(datetime.now(UTC))
store.append(finished)
findings = check_run(run.model_copy(update={"finished": finished}), registry)
```

What the item is kept as, its `payload`, pretty-printed:

```json
{
  "call": {
    "finished_at": "2026-09-29T00:00:03Z",
    "prompt_tokens": { "hex": "e5ecffe8…" },
    "request": { "hex": "5b7291b7…" },
    "response": { "model": "sha256:7607630d…", "choices": [] },
    "started_at": "2026-09-29T00:00:00Z",
    "status": 200
  },
  "key": { "case": "sha256:dff4379a…", "replicate": 0 },
  "run": "6f1c2d3e-0000-4000-8000-000000000001",
  "v": 1,
  "vignette": { "hex": "88c4e960…" }
}
```

`attempts` is left out at its default of 1, and so is each fingerprint's `alg` is left out at its default.
`RunItem.parse(item.canonical)` gives the item back. Leaving an item out of the finished run:

```python
run = store.run(started.run)
fewer = run.model_copy(update={"items": run.items[1:]})
[f.code for f in check_run(fewer, registry)][:2]  # ['ledger.seal', 'run.incomplete']
```

Check a score, as the scoring pass does when it finishes (`src/chatddx/runner/score.py`):

```python
from chatddx.ledger import check_score

score = store.score(score_id)
run = store.run(score.started.run)
findings = check_score(
    score, run, store.load([run.started.trial, score.started.scoring])
)
```

Look at a run's items in the database, as the writer:

```sql
SELECT "case", replicate, doc->'call'->>'error' AS error
FROM ledger.run_item WHERE run = '…' ORDER BY seq;
```

## Codes

Every finding the checks make is a warning. What each code means is in docs/glossary.md, "Checking a run" and "Checking
a score", and its message in docs/surfaces/ledger.md; below is what each one looks at. A subject is a run's or a score's
id, an item's key as `case='sha256:…' replicate=0`, or a component's digest.

### Checking a run

| Code                        | Subject                                | From                                         | Looks at                                                                                                                                                                               |
| --------------------------- | -------------------------------------- | -------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ledger.seal`               | run                                    | `src/chatddx/ledger/record.py:check_seal`    | the finish record's seal, against the rows hashed again                                                                                                                                |
| `run.incomplete`            |                                        | `src/chatddx/ledger/run.py:check_run`        | once finished, the rows, against the trial's item keys and the canary calls planned, each canary at each phase of `RunStarted.verify_at`; a finding for items and one for canary calls |
| `case.drift`                | item                                   | `src/chatddx/ledger/run.py:check_run`        | the fingerprint of the vignette the item read, against the case's                                                                                                                      |
| `call.failed`               | item, or a canary call's `phase/index` | `src/chatddx/ledger/run.py:check_run`        | an item's last call and each canary call, for an error, which is the message                                                                                                           |
| `tools.stopped`             | item                                   | `src/chatddx/ledger/run.py:check_run`        | a last round stopped before its call, for tool calls of the response before it that it didn't run                                                                                      |
| `tools.unanswered`          | item                                   | `src/chatddx/ledger/run.py:check_run`        | the item's last response, for tools it still calls, the answer tool aside                                                                                                              |
| `tools.code`                | tool                                   | `src/chatddx/ledger/run.py:check_run`        | the version each of the skeleton's tools pins, against the one `RunStarted.tool_code` recorded; one not recorded is a finding too                                                      |
| `attestation.model`         | item                                   | `src/chatddx/ledger/call.py:attest_model`    | the model each of the item's responses names, against the :Served model name of the trial's engine; a response that names none is a finding of its own                                 |
| `attestation.prompt_tokens` |                                        | `src/chatddx/ledger/run.py:check_run`        | each item's calls, for a prompt-token fingerprint; one finding counts the items with a call that lacks it                                                                              |
| `execution.retries`         |                                        | `src/chatddx/ledger/call.py:check_execution` | each call's attempts, canary calls included, against the attempts `Execution.retries` allows                                                                                           |
| `execution.timeout`         |                                        | `src/chatddx/ledger/call.py:check_execution` | each attempt's times, canary calls included, against the run's `Execution.timeout_s`                                                                                                   |
| `execution.order`           |                                        | `src/chatddx/ledger/call.py:check_execution` | when each item's first call started, against the order of `Execution.schedule`                                                                                                         |
| `execution.concurrency`     |                                        | `src/chatddx/ledger/call.py:check_execution` | the most calls in flight at once, canary calls included, against `Execution.concurrency`                                                                                               |
| `canary.phase`              |                                        | `src/chatddx/ledger/run.py:check_run`        | start canary calls' finish, against the first item call's start; end canary calls' start, against the last item call's finish                                                          |

### Checking a score

| Code                    | Subject | From                                         | Looks at                                                                                                         |
| ----------------------- | ------- | -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `view.unreachable`      | scorer  | `src/chatddx/ledger/score.py:check_score`    | each view's output selector, against the output schema of the run's skeleton                                     |
| `judge.incomplete`      | item    | `src/chatddx/ledger/score.py:check_score`    | the judge calls a judged view's value rests on, against the judge's seeds; not when the item has no value        |
| `attestation.model`     | item    | `src/chatddx/ledger/call.py:attest_model`    | the model each judge's responses name, against the :Served model name of the engine the scoring gives that judge |
| `score.scorer_code`     | score   | `src/chatddx/ledger/score.py:check_score`    | `ScoreStarted.scorer_version`, against the version the scorer pins                                               |
| `score.run_unfinished`  | score   | `src/chatddx/ledger/score.py:check_score`    | the score's start, against the run's finish                                                                      |
| `ledger.seal`           | score   | `src/chatddx/ledger/record.py:check_seal`    | the finish record's seal, against the rows hashed again                                                          |
| `score.no_expectation`  | score   | `src/chatddx/ledger/score.py:check_score`    | the run's cases, against the cases of the scoring's expectations                                                 |
| `score.incomplete`      |         | `src/chatddx/ledger/score.py:check_score`    | once finished, the rows, against each run item under each view                                                   |
| `execution.retries`     |         | `src/chatddx/ledger/call.py:check_execution` | each judge call's attempts, against the attempts the score's `Execution.retries` allows                          |
| `execution.order`       |         | `src/chatddx/ledger/call.py:check_execution` | when each item's first judge call started, against the order of the score's `Execution.schedule`                 |
| `execution.concurrency` |         | `src/chatddx/ledger/call.py:check_execution` | the most judge calls in flight at once, against the score's `Execution.concurrency`                              |

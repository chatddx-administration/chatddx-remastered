# Worker API

Reference for the `chatddx.worker` package: each name's signature, what it does and what it raises. What the worker
is and why it is shaped this way is in docs/worker.md. The queue it works, `Queue`, the `worker` schema and what goes
through `NOTIFY` are in docs/store-api.md; the events it says are the API's (docs/api-api.md, "events.py").

Paths are relative to `src/chatddx/worker/` unless they start with `src/` or `docs/`.

## Contents
- [Package](#package)
- [worker.py](#workerpy): `Worker`, `PAUSED`, `LEFT`
- [publish.py](#publishpy): `Publisher`, `EVERY`
- [Settings](#settings)
- [The command](#the-command)
- [Tests](#tests)

## Package
`chatddx.worker` re-exports `Worker`; everything else is imported by path. `src/chatddx/cli.py` and
`src/chatddx/api/app.py` import `Worker`.

| Module | Builds on |
| --- | --- |
| `publish.py` | psycopg, pydantic, `chatddx.api.{schemas,events}`, `chatddx.bench`, `chatddx.runner.run`, `chatddx.store.{notify,store}` |
| `worker.py` | `publish.py`, psycopg, `chatddx.settings`, `chatddx.api.{schemas,events}`, `chatddx.bench`, `chatddx.facts`, `chatddx.inventory`, `chatddx.ledger`, `chatddx.runner.run`, `chatddx.store` |

The worker says a run's events as the API's models have them (`chatddx.api.events`, `chatddx.api.schemas`), which
build on pydantic only.

## worker.py

| Name | Value |
| --- | --- |
| `PAUSED` | `"paused"`: why a job is queued again when its owner pauses. |
| `LEFT` | `"its worker stopped"`: why a job is queued again when its worker stops. |

### `class Worker(conninfo, inventory, facts, beat=settings.WORKER_BEAT, lost=settings.WORKER_LOST, deadline=settings.WORKER_DEADLINE)`
A worker with an `id` of its own (`uuid4`), for the World's inventory and facts, on connections to `conninfo` in
autocommit mode.

| Member | Does |
| --- | --- |
| `serve(stopping: threading.Event) -> None` | Enlists, listens on `WORKERS`, and until `stopping` is set and it holds nothing: beats, claims every job that fits each endpoint's `max_jobs`, and waits for a notification, `wake`, or `beat`. Once `stopping` is set it claims nothing, leaves its jobs, and after `deadline` cuts their scorings short. |
| `wake() -> None` | Wakes `serve` from its wait, as when it is to stop; nothing while it isn't serving. |
| `id: UUID` | |

A beat (`Queue.beat`) halts a job asked to halt, leaves one whose owner has paused, why `PAUSED`, and one another
worker took over. Each job claimed is worked on a thread named `chatddx-job-<id>`, which isn't a daemon, with two
connections of its own, one for a `Bench` of the job's owner and one for its `Publisher`:
- an unfinished run: `Bench.resume`, `Running.send` with `Publisher.run_event`, and `Running.finish`; or, left
  meanwhile and not halted, the job is queued again (`Queue.requeue`) with why it was left;
- when the job scores and isn't halted: `run.scoring`, with the scorers of `Bench.scorers_for` the job names (all
  when it names none) but those it has scored; `Bench.score` of each in turn, with `Publisher.scoring_event` and the
  job's `ScoreHalt`, and `Queue.scored` of each that finished unhalted; then `run.scored`, the scores sorted by name.
  Cut short at the deadline and not halted, the job is queued again with why `LEFT`, and nothing says `run.scored`;
- the job ends stopped when halted, else finished (`Queue.end`). An `Exception` within ends it failed, with the
  exception's message, else its type's name, as why, and is logged.

A halt reaches a run as `Running.halt`, a leave as `Running.stop`, and both reach a scoring as `ScoreHalt.set`; one that
comes before the run is resumed is applied as it is.

## publish.py

| Name | Value |
| --- | --- |
| `EVERY` | 0.1: the seconds deltas wait to go out together. |

### `class Publisher(conn: Connection, run: UUID)`
Says a run's events that aren't rows on its channel (`chatddx.store.notify.channel`), on `conn`.

| Member | Does |
| --- | --- |
| `run_event(event: chatddx.runner.run.Event) -> None` | `put` of `chatddx.api.events.said_of(event)`; on `ItemEnded`, drops the item's deltas still held. |
| `scoring_event(event: chatddx.bench.ScoringEvent) -> None` | `put` of `chatddx.api.events.judged_of(event)`. |
| `put(said: Named) -> None` | An `item.delta` or `judge.delta` is held, merged into the last held of its event, case and replicate when of the same kind; held deltas go out once `EVERY` has passed since the last went out, or they hold `LIMIT` characters. Any other event goes out at once, after what is held. |
| `close() -> None` | What is held goes out. |

What goes out is packed by `chatddx.store.notify.payloads` and sent with `pg_notify` in one transaction. A
`psycopg.Error` is logged, and the publisher says nothing more.

## Settings
In `chatddx.settings`:

| Name | Value |
| --- | --- |
| `WORKER_BEAT` | 1 s: how often a worker beats. |
| `WORKER_LOST` | 10 s: how long a worker goes unseen before its jobs are claimed again, and a worker is counted as seen. |
| `WORKER_DEADLINE` | 60 s: how long a stopping worker's scorings go on; within the stop timeout of the service that runs it. |

## The command
`chatddx worker [--world DIR] [--facts PATH]…` (`src/chatddx/cli.py:_worker`): the World, from `--world` or
`CHATDDX_WORLD`, and the bundled facts, the World's and those given, as `chatddx api` takes them. It logs at INFO,
prints the worker's id and the World as it starts, and serves `settings.database()` until SIGTERM or SIGINT sets its
stopping event and wakes it; then it prints that what it held is queued again.

`chatddx portal` runs one in its process (`src/chatddx/api/app.py:app`, `worker=True`); `chatddx api` runs none.

## Tests
`test/`, against the `curated` template, in autocommit mode:

| Module | Holds |
| --- | --- |
| `test_worker.py` | The worker on a thread (`serving`, beating every 50 ms, lost after a second) against the fake vLLM: a queued run sent, finished and scored, then scored again; woken by a queued job under a five-minute beat, and saying what its rows don't; halted while sending and while queued; paused and resumed; stopped and resumed by another worker; claimed again once its worker is lost; refused by the gate as it resumes; and cut short at its deadline mid-scoring, another worker scoring what was left. |
| `test_publish.py` | Deltas going out together, merged by item and kind, an ended item's left unsaid, and another event going out at once. |

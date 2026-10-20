# Worker

The worker sends and scores the runs queued for it, outside the request that asked for them, so that a run outlives the
process that started it, and is followed and halted from any. It strings together pieces documented elsewhere: the queue
(docs/modules/store.md), the bench that queues runs and scorings and, with the runner, sends and scores
them (docs/modules/bench.md, docs/modules/runner.md), the ledger's rows a run is told by (docs/modules/ledger.md), and
the API, and the portal, that ask for runs, and tell their events (docs/modules/api.md, "Runs").

```
AGENT: REPLACE
`docs/reference/` is `docs/surfaces/` now.
---
This document describes what the worker does and why. Names, signatures and errors are in docs/surfaces/worker.md, and
its settings in `src/chatddx/settings.py`.
```
This document describes what the worker does and why. Names, signatures and errors are in docs/reference/worker.md, and
its settings in `src/chatddx/settings.py`.

## A job

A job is what the worker is asked to do: take a started run to its finish, and score it when asked, or score a finished
run again. The request starts the runs, a run per language its cases are sent in (docs/modules/api.md, "Starting one").

A run has at most one job queued or under way. A job is queued, under way, finished, stopped or failed, and says why
when a failure, a pause or a stop put it there. The queue is updated in place; what the run did is the ledger's, read
from there and not copied into the job.

A job holds as many slots at its run's endpoint as the run's concurrency, from its claim until it ends, its scoring
included; a scoring alone holds none. It keeps the scorers it has finished, so that a job queued again mid-scoring
scores what is left.

## Claiming

Jobs are taken in queue order, the time they were queued and then their id, whoever owns them. A job is taken when its
slots fit within its endpoint's capacity, counting the jobs under way there, and its owner hasn't paused. A job asked to
halt is taken whatever its slots, to be halted, and so is one at an endpoint the inventory doesn't name, which fails at
the gate. Claims take turns, so that several workers count an endpoint's slots alike, and a claimed job is locked, so
that two workers never take the same one.

A job under way whose worker hasn't been seen for a while is claimed again, and its run resumed: lost isn't a status.

## Working a job

Each job runs on a thread of its own, with a bench for the job's owner. An unfinished run is resumed, sent and finished;
then, when the job scores, the run is scored scorer by scorer, under every scorer that applies to it or the ones the job
names, but those the job has finished. A job whose work fails ends failed, with why: a run the gate refuses as it
resumes fails so.

The worker beats, marking itself and its jobs as seen, and hearing for each whether it is to halt and whether its owner
has paused. It is woken at once when a job is queued, halted, ended or queued again, or an owner pauses or resumes, so
that it claims and halts without waiting for its next beat. On a beat:

- **A halt** hangs the run's calls up and finishes it unscored, or stops its scoring.
- **A pause** stops the run after the items under way, leaves it unfinished, and queues the job again.
- **A job another worker took over** is let go, as a run stopped and not ended.

## What it says as it happens

A run is told by its rows as they land (docs/modules/api.md, "Its events"). The worker says on the run's channel what
the rows don't, listed there, and when the scoring is over, each scorer's score or why it gave none. Deltas go out
together, a tenth of a second's at a time, merged by item and kind, and an item's deltas still held when its row lands
go unsaid. What it says goes through `NOTIFY`, packed to keep within its payloads' size (src/chatddx/store/notify.py). A
worker that can't say it goes on without: the rows still land.

## Stopping

A stopping worker takes no more jobs. Its runs stop after the items under way and their jobs are queued again. Its
scorings go on until a deadline after it was asked to stop, then are halted and their jobs queued again, to score what
is left: the scorer halted is scored again from its start, and its partial score stays beside the whole one. The next
claim resumes what was queued again. The deadline is the worker's own, so the service that runs it is to give it longer
to stop.

## A person's queue

A person sees how their queue stands: whether it is paused, how many of their jobs are queued and under way, and how
many workers have been seen lately, whoever's jobs they hold. They pause it and resume it. They stop it in two presses:
the first takes what is queued out, each job ended stopped and its run left unfinished, while the runs under way go on;
the second halts those too. A run left unfinished with nothing queued or under way for it, as one taken out of the queue
or one whose job failed, is resumed by its owner: queued again, it sends what it lacks.

Each run says its latest job, and while it is queued, how many jobs at its endpoint are under way or to be taken before
it. The portal's runs page shows the person's queue with its controls, and each run's job.

## Where it runs

`chatddx worker` serves the queue for a World until it is stopped. `chatddx run`, a convenience for development, runs a
worker in its own process.

A worker logs the inventory check's findings as it starts (docs/modules/inventory.md, "Reaching an engine").

## Elsewhere

- **The queue's tables and writes**: docs/modules/store.md; src/chatddx/store/queue.py, and the `worker`
  schema's migrations (docs/migrations.md).
- **A run's events**, numbered by its rows: docs/modules/api.md, "Its events"; docs/modules/ledger.md, "Storage".
- **Resuming a run**: docs/modules/runner.md, "Resuming".
- **The portal's runs page**: agents/wip-portal.md.

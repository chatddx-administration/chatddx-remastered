# The worker: work in progress

The worker runs trials outside the request that asked for them, so that a run outlives a closed tab, a client that
goes away, and a restarted app. The portal needs it before it can start runs (`agents/wip-portal.md`), and the batch
planner hands it what it plans (`agents/wip-batch.md`). This file plans it, and the port of what the old worker did.

"The old worker" is chatddx-administration/chatddx at 504792c: `src/chatddx/worker/` (`models.py`, `queue.py`,
`worker.py`, `control.py`, `cli.py`, about 950 lines), with the portal's **Status** page
(`src/chatddx/django/portal/status.py`, `templates/portal/batch/status_panel.html`) and its manual's "Status"
(`docs/portal.md`). Old permalink base:
https://github.com/chatddx-administration/chatddx/blob/504792cbeb09508f2c52912be29a3d8809d2fa1d/

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **Decided: the worker and the batch planner are planned apart**, as this file and `agents/wip-batch.md`. They meet
   at one contract (see "The contract"), which is a take.
2. **The problem** (see "Why"): a run started over HTTP runs in the request and halts when the client goes away
   (`agents/wip-bench.md`, "Takes the API is built on", A6, W1). Right for a program, wrong for a browser tab.
3. **Decided: the queue is updated in place** (K2), an exception to "nothing is updated", as identity's people and
   sessions are.
4. **Open, as takes** (see "Options"): K1, where it runs; K3, how events reach a page; K4, the unit it schedules; K5,
   which runs go through it.
5. **What it needs below it first** (see "Below the worker"): resuming a run, and `Bench.start` taking an execution.

## Why
- **The API runs a trial in the request** (`agents/wip-bench.md`, "Takes the API is built on", A6, W1):
  `POST /api/runs` streams, or waits for the record. A client that goes away halts the run
  (`src/chatddx/runner/run.py:Running.halt`), and it is recorded as stopped.
- **In a browser that is a closed tab, a reload, or a laptop going to sleep.** For a portal page that starts a batch
  of a hundred cases, it stops the batch.
- **A long request holds a thread and a connection** for as long as the run lasts (`agents/wip-api.md`,
  "Outstanding", "Open").
- **The orchestrator runs in Kubernetes** (`docs/chatddx.md`, "Target stack"): an app is restarted at each deploy, and
  may run as several replicas. A run held by one process is lost with it, and unseen from the others.

## The old worker
### What it was
- **`chatddx worker serve`** (or `run`, until the queue is empty): a process apart from Django's, polling the database
  every second (`worker.py:POLL`).
- **A job was a trial**: a cell, one case and one seed (`worker/models.py:JobModel`), with the batch's id, the
  configuration, stack and slice branches it was planned from, a status, a reason, its tokens, and when it was queued,
  started, last beat and finished. Statuses: stored, queued, running, completed, errored, aborted, stopped, skipped and
  lost. Jobs were updated in place.
- **Slots per stack**: a stack's `max_jobs`, read from its head when the worker looked (`queue.py:slots`), shared by
  every run on it. The worker filled free slots in queue order (`in_turn`: queued time, then id), across owners.
- **Claiming**: `select_for_update(skip_locked=True)` on the next queued job, then set running (`worker.py:_taken`).
- **Running**: each job a `Sending` on a thread of a `Relay`, a bench and a scoring cached per owner
  (`worker.py:_bench`); scored when it ended.
- **Heartbeats**: every half second the running jobs' tokens and `beat` were written, and the worker's own `seen`
  (`WorkerStateModel`). A job whose beat was older than `LOST` became lost (`queue.py:lose`); a worker unseen for ten
  seconds was "not running at all" on the status page (`control.py:ALIVE`).
- **Controls per owner** (`ControlsModel`, `control.py`): pause, which held the owner's queue once the jobs running
  ended; resume; and stop, pressed once to take the queue out and let the running jobs finish, twice ("stop now") to
  stop those too.
- **What a batch asked of it** (`queue.py`): `put` its trials, queued or stored for later; `resume` what didn't
  complete; `rerun` all of it.
- **The status page**, every second: what the worker was at, how many cases were ahead per stack, the progress bar,
  the cases running with their time and tokens, what is up next, and the ten taken up last.

### What changes in remastered
- **A trial holds every case** (`docs/chatddx.md`, glossary, "Trial"), where the old one held one. A batch is a few
  long runs, one per variation, rather than many short jobs. Fairness between owners, pausing and stopping act on runs,
  unless the worker schedules a run's items (K4).
- **Concurrency is the run's.** The runner sends a run's items up to its execution's concurrency, and refuses an
  execution above its endpoint's `max_jobs` (`src/chatddx/runner/run.py:Runner.start`). The old worker's slots were
  its own.
- **Nothing is updated** in the factors, the ledger and the catalog (`docs/store.md`). Identity is an exception: it
  updates people and keeps sessions. The queue is another (K2).
- **A run's rows land as they are written**, so its progress can be read from the ledger, from any process.
- **No bench caches an owner for long**: a bench is built per request or session (`agents/wip-bench.md`, S5). The
  worker builds one per run.
- **The gate refuses before anything is written** (`src/chatddx/runner/gate.py`): asking can check it, and so can
  starting, since the World can change in between.

## The contract
What edges and the planner hand the worker, and what they get back. Take:
1. **The unit asked for**: a trial at an endpoint, for an owner, scored afterwards or not, and the batch it came from
   if any (`agents/wip-batch.md`). That is `Bench.start` followed by `Bench.score` (`src/chatddx/bench/view.py`), and
   what `POST /api/runs` asks today (`agents/wip-api.md`, "Runs").
2. **How its runs are found**: by trial digest and owner (`Bench.runs`; `GET /api/runs?trial=`), or through a kept
   batch (`agents/wip-batch.md`, "Kept batches").
3. **The surface an edge calls**: queue, which gives the job's id; stop; and the events, by item from the ledger, with
   deltas where they can be had (K3). A job's state is the queue's; what its run did is the ledger's, read from there
   and not copied.

Why apart from the planner:
- **One narrow seam.** The planner decides which trials; the worker decides when and where they run.
- **Each is useful without the other.** The planner serves the repl's `batch` and the portal's confirmation page; the
  worker serves single runs from the API and the portal, and sample runs.
- **Different kinds of work.** The planner is pure over the bench; the worker is processes, concurrency and failure.
- **The old project fused them, and it cost**: `queue.put(owner, batch, trials)` took a batch's id, each `JobModel`
  pointed at a `BatchModel`, and a batch's state was its jobs' state.

## Options
### K1. Where it runs
- **W2. In the app's process**, beside the request (`agents/wip-bench.md`, "Takes the API is built on", A6): a
  thread per run, kept in memory. Small, but runs end with the process, and replicas don't see each other's.
- **W3. A process of its own**, `chatddx worker`, reading what is asked from the store. Survives the app's restarts,
  serves every replica.
- **W3, also runnable in the app's process**: the same worker, started as a thread by `chatddx api --worker` and by
  the tests, reading the same store.

Take: the last. One implementation; W2 isn't built and thrown away. What is asked is in the store either way, so even
in-process a closed tab doesn't stop a run.

### K2. The queue
Decided: **a table of jobs updated in place**, an exception to "nothing is updated" (`docs/chatddx.md`, "Work in
progress"; `docs/store.md`), as identity's people and sessions are. Take, for its shape:
- **A schema of its own** (`worker`), with migrations at every tier (`docs/store.md`, "Tiers") and the writer's
  grants to update it. Tier 2 keeps the factors, the ledger and the catalog append-only, and leaves the queue out, as
  it leaves identity.
- **A job**: the owner, the trial and endpoint, whether to score, the batch it came from if any
  (`agents/wip-batch.md`), its status (queued, under way, finished, stopped, failed, lost), why, the run it started,
  and when it was queued, claimed, last beat and ended.
- **Claimed** with `SELECT … FOR UPDATE SKIP LOCKED`, as the old worker claimed (`worker.py:_taken`).
- **Controls per owner** (paused, stopping), and **workers** (id, last seen), updated in place too: a job whose worker
  is gone is lost.
- **What the ledger holds isn't copied**: tokens, items and the finish are read from the run.

### K3. How events reach a page
- **E1. Read the ledger**: a page or the API polls the run's rows. Works from any process; item by item; no deltas.
- **E2. E1, woken by `LISTEN`/`NOTIFY`**: the worker notifies when an item starts or ends, and the API reads the rows
  then. No polling, and still from any process.
- **E3. E2, with deltas through `NOTIFY`**: a completion as it is written, batched to keep within `NOTIFY`'s payload
  limit (8,000 bytes). The deltas are case-derived, and pass through the database, which holds the ledger already.

Take: E2, then E3 when the portal's run island wants to show a completion as it is written. Swift waits for one
answer, which E2 gives (`agents/wip-portal.md`, "Swift").

### K4. The unit it schedules
- **Runs.** A run is sent whole by one worker, up to its own concurrency. A long run holds its endpoint's slots until
  it ends, and pause and stop act at the run's next item (`Running.stop`) or at once (`Running.halt`).
- **Items.** The worker hands out a run's items, so owners take turns item by item, as the old jobs did. It needs
  several processes writing one run's log, which the runner doesn't do: one `Running` sends one run.

Take: runs, with `max_jobs` shared by the runs on one endpoint through their executions (see "Below the worker").

### K5. Which runs go through it
- **Every run started over HTTP**, the portal's and the API's: one path. `POST /api/runs` answers 202 and its id
  (W2's shape in `agents/wip-bench.md`, "Takes the API is built on", A6), and the stream is
  `GET /api/runs/{id}/events`.
- **Batches only**, single runs staying in the request.

Take: every run started over HTTP. The repl keeps running in its own process, where Ctrl-C halts a run as it should.
`max_jobs` then isn't held between the repl's runs and the worker's (see "Open").

## Below the worker
Moved here from `agents/wip-runner.md` ("Afterwards"), since the worker is their first caller:
- **Resuming.** `resume(run)` would append an unfinished log's missing items: `Running.send` already skips items that
  are in. The worker resumes what it lost, and what a stop or a pause left unfinished.
- **`max_jobs` across runs.** Each run is held to its endpoint's `max_jobs`, but two runs on one endpoint can send
  twice that between them. vLLM queues what's over `--max-num-seqs` rather than refusing it, so the cost is batching
  that the runs' `execution` doesn't show. The worker can hold them to it between them: a run's execution is given
  at its start (`Runner.start(…, execution)`), refused above the endpoint's `max_jobs`, and recorded in `RunStarted`,
  so the worker can give each run its share. `Bench.start` passes no execution yet, so a run gets `Execution()`'s.

Still the runner's, and met here:
- **A halted call waits for its next chunk** (`agents/wip-runner.md`, "Afterwards"): an engine that stalls mid-stream
  keeps a halted run's worker thread waiting, under an execution with no `timeout_s`.

## The plan
Assuming the takes.
0. **Below the worker**: resuming (`src/chatddx/runner/`), and `Bench.start` taking an execution.
1. **The queue**: the `worker` schema, its jobs, controls and workers, at every tier; the store's reads and writes
   for them; tests on the store. The exception is proposed in `docs/store.md` and `docs/chatddx.md`; once the
   migrations land, `docs/migrations.md` gets a `worker` section, and its "identity, the one mutable schema" changes.
2. **The worker**: `src/chatddx/worker/`, a loop that claims jobs, builds a bench per run, starts, sends, finishes and
   scores, beats, and finds what is lost; `chatddx worker`. Tests run it in a thread against the fake vLLM, as the
   repl's tests serve the fake (`src/chatddx/repl/test/conftest.py:fake`).
3. **The API**: `POST /api/runs` queues a job and answers 202; `GET /api/runs/{id}/events` streams from the ledger
   (E2); `POST /api/runs/{id}/stop`. The person's jobs and their state (`GET /api/jobs`, or under runs).
4. **Controls**: pause, resume and stop for an owner, and the status a portal page shows.
5. **E3**, when the portal's run island needs deltas.

## Open
- **The repl beside the worker**: the repl's runs don't count against the worker's shares of `max_jobs`. The repl
  could ask the worker too, and follow the events.
- **Fairness between owners**: queue order, or turns per owner, per endpoint.
- **Jobs that can't start**: an endpoint the gate refuses when the worker comes to it. Failed, with why, as the old
  "skipped".
- **A run lost mid-way**: resumed by the next claim, or left unfinished and shown so.
- **Deployment**: one worker or several, and whether each is a Kubernetes Deployment of its own.

## Moved here
- From `agents/wip-portal.md`: "Below the UI", 1, runs that outlive the request, and the worker's part of "The batch
  planner and the worker".
- From `agents/wip-runner.md`, "Afterwards": "Resuming" and "`max_jobs` across runs".
- From `agents/wip-api.md` at 100a078, "Open": "Long requests".

# The worker: work in progress

The worker runs trials outside the process that asked for them, so that a run outlives a restarted app and is seen,
followed and halted from every replica. A run started over HTTP already outlives a closed tab and a client that goes
away: it is a job in the app's process (`docs/api.md`, "Where it runs"), which the portal starts and watches runs on
(`agents/wip-portal.md`, R10). The worker takes the jobs' place with the API as it is, and runs what the batch
planner plans (`agents/wip-batch.md`). This file plans it, and the port of what the old worker did. Nothing of it is
built: no `worker` schema, no `src/chatddx/worker/`, no resuming.

"The old worker" is chatddx-administration/chatddx at 504792c: `src/chatddx/worker/` (`models.py`, `queue.py`,
`worker.py`, `control.py`, `cli.py`, about 950 lines), with the portal's **Status** page
(`src/chatddx/django/portal/status.py`, `templates/portal/batch/status_panel.html`) and its manual's "Status"
(`docs/portal.md`). Old permalink base:
https://github.com/chatddx-administration/chatddx/blob/504792cbeb09508f2c52912be29a3d8809d2fa1d/

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **Decided: the worker and the batch planner are planned apart**, as this file and `agents/wip-batch.md`. They meet
   at one contract (see "The contract"), which is a take.
2. **The problem** (see "Why"): what the app has under way for a run, the run or a scoring of it, is a job in its
   process (decided: `docs/api.md`, "Where it runs"). It ends with the process, and other replicas don't see it.
3. **Decided: the queue is updated in place** (K2), an exception to "nothing is updated", as identity's people and
   sessions are. `docs/store.md` ("The queue") and `docs/chatddx.md` ("Work in progress") describe it already, though
   no migration makes it yet.
4. **Decided** (see "Options"): K1, one worker, also runnable in the app's process; K3, events read from the ledger
   and woken by `LISTEN`/`NOTIFY` (E2); K4, it schedules runs; K5, every run started over HTTP goes through it. E3,
   deltas through `NOTIFY`, is still a take, and the API's events need deltas (see K3).
5. **What it needs below it first** (see "Below the worker"): resuming a run, and `Bench.start` taking an execution
   and a canary set.
6. **Open: where a run starts** (K6): in the request, as `docs/api.md` has it, or in the worker, as "The contract"
   has it. Take: in the request.

## Why
- **A run is a job in the app's process**: `POST /api/runs` answers 202 and the run's path, the run is sent on a
  thread of its own (`src/chatddx/api/jobs.py`), followed by `GET /api/runs/{id}/events` and halted by
  `POST /api/runs/{id}/halt`. Scoring again (`POST /api/runs/{id}/scores`) and running again
  (`POST /api/runs/{id}/again`) are jobs too. A server that stops waits for them, and a killed one leaves them
  unfinished (`docs/api.md`, "Outstanding", "Serving").
- **The orchestrator runs in Kubernetes** (`docs/chatddx.md`, "Target stack"): an app is restarted at each deploy, and
  may run as several replicas. A job held by one process is lost with it, and another replica tells its run from the
  ledger without its deltas, and can't halt it.

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
  its own. Until the worker shares `max_jobs` between runs, a run's concurrency stays 1 (`agents/wip-portal.md`, R9).
  Judge calls reach endpoints too, one at a time (`docs/runner.md`, "Smaller issues").
- **Nothing is updated** in the factors, the ledger and the catalog (`docs/store.md`). Identity is an exception: it
  updates people and keeps sessions. The queue is another (K2).
- **A run's rows land as they are written**, so its progress can be read from the ledger, from any process
  (`docs/api.md`, "Its events": a run with nothing in the app's process is told from the ledger).
- **No bench caches an owner for long**: a bench is built per request or session (`agents/wip-bench.md` at d5ebf52,
  S5). The worker builds one per run.
- **The gate tells lasting refusals from passing ones** (`docs/runner.md`, "The gate"; `src/chatddx/runner/gate.py`):
  `bar` refuses for as long as the World is as it is, and asks nothing of the network; `admit` adds a secret that
  isn't set and an endpoint that can't be confirmed, which may pass later. Queueing can call `bar`, and claiming
  `admit`, since the World can change in between.
- **Runs are limited** by the bench: runs a day per person and items per run (`settings.RUNS_PER_DAY`,
  `ITEMS_PER_RUN`; `src/chatddx/bench/runs.py`), counted from the runs started in the catalog.

## The contract
What edges and the planner hand the worker, and what they get back. Take:
1. **The unit asked for**: a trial at an endpoint, for an owner, scored afterwards or not, and the batch it came from
   if any (`agents/wip-batch.md`). That is `Bench.start` followed by `Bench.score` (`src/chatddx/bench/runs.py`), and
   what `POST /api/runs` asks today (`docs/api.md`, "Runs"). Whether the worker or the request starts the run is K6.
   Scoring a run again is a unit of its own: a run and the scorers it is left to, as `POST /api/runs/{id}/scores`
   asks.
2. **How its runs are found**: by trial digest and owner (`Bench.runs`; `GET /api/runs?trial=`), or through a kept
   batch (`agents/wip-batch.md`, "Kept batches").
3. **The surface an edge calls**: queue, which gives the job's id; halt; and the events, by item from the ledger, with
   deltas (K3). A job's state is the queue's; what its run did is the ledger's, read from there and not copied.

Why apart from the planner:
- **One narrow seam.** The planner decides which trials; the worker decides when and where they run.
- **Each is useful without the other.** The planner serves the repl's `batch` and the portal's confirmation page; the
  worker serves single runs from the API and the portal, and sample runs.
- **Different kinds of work.** The planner is pure over the bench; the worker is processes, concurrency and failure.
- **The old project fused them, and it cost**: `queue.put(owner, batch, trials)` took a batch's id, each `JobModel`
  pointed at a `BatchModel`, and a batch's state was its jobs' state.

## Options
### K1. Where it runs
- **W2. In the app's process**, beside the request (`agents/wip-api.md` at 100a078, "A6. Where a run runs"): a
  thread per run, kept in memory. Small, but runs end with the process, and replicas don't see each other's.
- **W3. A process of its own**, `chatddx worker`, reading what is asked from the store. Survives the app's restarts,
  serves every replica.
- **W3, also runnable in the app's process**: the same worker, started as a thread by `chatddx portal`, which starts
  everything the portal needs (`agents/wip-portal.md`, "P3b, concretely"), by `chatddx api --worker` and by the tests,
  reading the same store.

Decided: the last. One implementation; W2 isn't built and thrown away. What is asked is in the store either way, so
even in-process a closed tab doesn't stop a run.

Since: W2 is built in W3's HTTP shape (`docs/api.md`, "Where it runs"), so a closed tab doesn't stop a run already.
The worker takes the place of `src/chatddx/api/jobs.py`, and the API stays as it is.

### K2. The queue
Decided: **a table of jobs updated in place**, an exception to "nothing is updated" (`docs/chatddx.md`, "Work in
progress"; `docs/store.md`, "The queue"), as identity's people and sessions are. Take, for its shape:
- **A schema of its own** (`worker`), with migrations at every tier (`docs/store.md`, "Tiers") and the writer's
  grants to update it, which `docs/store.md` ("Roles and connections") names already. Tier 2 keeps the factors, the
  ledger and the catalog append-only, and leaves the queue out, as it leaves identity.
- **A job**: the owner, what it does (a run, scored or not, or a scoring of a run), the trial and endpoint or the run
  and scorers, the batch it came from if any (`agents/wip-batch.md`), its status (queued, under way, finished,
  stopped, failed, lost), why, the run it started, and when it was queued, claimed, last beat and ended.
- **Claimed** with `SELECT … FOR UPDATE SKIP LOCKED`, as the old worker claimed (`worker.py:_taken`).
- **Controls per owner** (paused, stopping), and **workers** (id, last seen), updated in place too: a job whose worker
  is gone is lost.
- **What the ledger holds isn't copied**: tokens, items and the finish are read from the run.

### K3. How events reach a page
- **E1. Read the ledger**: a page or the API polls the run's rows. Works from any process; item by item; no deltas.
  Built, as what the API tells a run with nothing in its process (`src/chatddx/api/runs.py:_told`).
- **E2. E1, woken by `LISTEN`/`NOTIFY`**: the worker notifies when an item starts or ends, and the API reads the rows
  then. No polling, and still from any process.
- **E3. E2, with deltas through `NOTIFY`**: a completion as it is written, batched to keep within `NOTIFY`'s payload
  limit (8,000 bytes). The deltas are case-derived, and pass through the database, which holds the ledger already.

Decided: E2. Take: E3 with it. The API's events hold deltas (`item.delta`, `judge.delta`, kept until their item or
call ends, `docs/api.md`, "Its events"), the home page shows the model thinking or writing with its tokens so far, and
the run's island unfolds an item's text as it streams (`agents/wip-portal.md`, "Swift", R3). Without deltas from the
worker, the API wouldn't stay as it is.

### K4. The unit it schedules
- **Runs.** A run is sent whole by one worker, up to its own concurrency. A long run holds its endpoint's slots until
  it ends, and pause and stop act at the run's next item (`Running.stop`) or at once (`Running.halt`).
- **Items.** The worker hands out a run's items, so owners take turns item by item, as the old jobs did. It needs
  several processes writing one run's log, which the runner doesn't do: one `Running` sends one run.

Decided: runs, with `max_jobs` shared by the runs on one endpoint through their executions (see "Below the worker").

### K5. Which runs go through it
- **Every run started over HTTP**, the portal's and the API's: one path. `POST /api/runs` answers 202 and the run's
  path, and the stream is `GET /api/runs/{id}/events`, as built in the app's process (`docs/api.md`, "Its events").
- **Batches only**, single runs staying in the request.

Decided: every run started over HTTP, and with them what else the app runs as a job: scoring again and running again.
The repl keeps running in its own process, where Ctrl-C halts a run as it should. `max_jobs` then isn't held between
the repl's runs and the worker's (see "Open").

### K6. Where a run starts
`docs/api.md` ("Runs", "Starting one") has the run started within the request: whatever refuses it does so before
anything is sent, and the 202 carries `run.started`'s data and the run's path. "The contract" above has the worker
start it instead: the unit is `Bench.start` followed by `Bench.score`, the queue gives a job's id, and a job records
the run it started. Both can't hold.
- **A. The request starts the run, the worker sends it.** `Bench.start` writes `RunStarted` in the request, and the
  gate's `bar` and `admit` refuse there; the job queued is the started run, and the worker claims it and sends it,
  as it resumes what it lost. The API stays as `docs/api.md` has it.
- **B. The worker starts the run.** The request queues a job and answers with it; a refusal the request can't foresee
  (an unset secret, an endpoint that doesn't answer) becomes the job's failure (see "Open", "Jobs that can't start"),
  and `docs/api.md`'s "Starting one" changes.

Take: A. It keeps the API's contract and its refusals up front, the worker sends only what resuming already needs
it to send, and a started run is in the ledger before anything is queued. The contract's first point then reads "a
run started at an endpoint, scored afterwards or not".

## Below the worker
Moved here from the runner's plan (`docs/runner.md`, "Elsewhere"), since the worker is their first caller:
- **Resuming.** `resume(run)` would append an unfinished log's missing items. `Running.send` skips the items its own
  instance has sent (`src/chatddx/runner/run.py:_prepared`), so resuming loads the stored log's items into a
  `Running` first. The worker resumes what it lost, and what a stop or a pause left unfinished.
- **`max_jobs` across runs.** Each run is held to its endpoint's `max_jobs`, but two runs on one endpoint can send
  twice that between them. vLLM queues what's over `--max-num-seqs` rather than refusing it, so the cost is batching
  that the runs' `execution` doesn't show. The worker can hold them to it between them: a run's execution is given
  at its start (`Runner.start(…, execution)`), refused above the endpoint's `max_jobs`, and recorded in `RunStarted`,
  so the worker can give each run its share. `Bench.start` passes no execution yet, so a run gets `Execution()`'s
  (`docs/bench.md`, "Outstanding").
- **Canary sets.** `Runner.start(…, canaries)` takes one, and both data sets hold one, but `Bench.start` passes none,
  so no run started over HTTP sends one (`docs/scripted.md`, "Smaller issues"). `docs/api.md` ("Not covered") leaves
  canary sets, with an execution's settings, to the batch planner and the worker; the run's start is where one is
  given, so `Bench.start` takes it with the execution. Which set a run gets, the World's or the person's pick, is
  open.

Still the runner's, and met here:
- **A call still waiting for its engine to answer at all** waits on after a halt, under an execution with no timeout;
  only a stream can be shut down (`docs/runner.md`, "What a stop leaves out"). A halted run's worker thread waits
  with it.

## The plan
On the decisions above, and the takes left.
0. **Below the worker**: resuming (`src/chatddx/runner/`), and `Bench.start` taking an execution and a canary set.
1. **The queue**: the `worker` schema, its jobs, controls and workers, at every tier; the store's reads and writes
   for them; tests on the store. `docs/store.md` and `docs/chatddx.md` describe it already; once the migrations land,
   `docs/migrations.md` gets a `worker` section, and its "identity, the one mutable schema" changes.
2. **The worker**: `src/chatddx/worker/`, a loop that claims jobs, builds a bench per run, starts, sends, finishes and
   scores, beats, and finds what is lost; `chatddx worker`. Tests run it in a thread against the fake vLLM, as the
   API's run tests run their jobs (`src/chatddx/conftest.py:fake`, `src/chatddx/api/test/test_runs.py`).
3. **The API**: `POST /api/runs`, `/again` and `/scores` queue a job and answer 202 as now, a run started in the
   request before its job is queued (K6, a take);
   `GET /api/runs/{id}/events` streams from the ledger, woken by the worker, with its deltas (E2, E3);
   `POST /api/runs/{id}/halt`. The person's jobs and their state (`GET /api/jobs`, or under runs).
4. **Controls**: pause, resume and stop for an owner, and the status a portal page shows.

## Open
- **The repl beside the worker**: the repl's runs don't count against the worker's shares of `max_jobs`. The repl
  could ask the worker too, and follow the events.
- **Fairness between owners**: queue order, or turns per owner, per endpoint.
- **Jobs that can't start**, under K6's B: `bar` refuses when a job is queued; an endpoint `admit` refuses when the
  worker comes to it is failed, with why, as the old "skipped", or waits for the secret or the server.
- **Quotas**: whether a queued job counts against `RUNS_PER_DAY`, or only a run it started, as the bench counts now.
- **A run lost mid-way**: resumed by the next claim, or left unfinished and shown so.
- **Deployment**: one worker or several, and whether each is a Kubernetes Deployment of its own.

## Moved here
- From `agents/wip-portal.md`: "Below the UI", 1, runs that outlive the request, and the worker's part of "The batch
  planner and the worker".
- From the runner's plan, since solidified as `docs/runner.md`: "Resuming" and "`max_jobs` across runs".
- From `agents/wip-api.md` at 100a078, "Open": "Long requests".

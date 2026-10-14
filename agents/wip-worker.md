# The worker: work in progress

The worker runs trials outside the process that asked for them, so that a run outlives a restarted app and is seen,
followed and halted from every replica. A run started over HTTP already outlives a closed tab and a client that goes
away: it is a job in the app's process (`docs/api.md`, "Where it runs"), which the portal starts and watches runs on
(`agents/wip-portal.md`, R10). The worker takes the jobs' place with the API as it is. This file plans it, and the
port of what the old worker did. Steps 0 to 2 are built (see "Built"): what it stands on, the queue and the worker,
`chatddx worker`. Nothing queues runs yet: the API's runs stay jobs in the app's process until step 3.

"The old worker" is chatddx-administration/chatddx at 504792c: `src/chatddx/worker/` (`models.py`, `queue.py`,
`worker.py`, `control.py`, `cli.py`, about 950 lines), with the portal's **Status** page
(`src/chatddx/django/portal/status.py`, `templates/portal/batch/status_panel.html`) and its manual's "Status"
(`docs/portal.md`). Old permalink base:
https://github.com/chatddx-administration/chatddx/blob/504792cbeb09508f2c52912be29a3d8809d2fa1d/

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **Decided: there is no batch.** An edge asks the worker for runs, one at a time; variations started together are
   a run each (`agents/wip-portal.md`, "Comparing variations"). What an edge hands it is "The contract", a take.
2. **The problem** (see "Why"): what the app has under way for a run, the run or a scoring of it, is a job in its
   process (decided: `docs/api.md`, "Where it runs"). It ends with the process, and other replicas don't see it.
3. **Decided: the queue is updated in place** (K2), an exception to "nothing is updated", as identity's people and
   sessions are. Built: schema `worker` (`src/chatddx/store/migrations/0019-t0-worker.sql` to `0021`).
4. **Decided** (see "Options"): K1, one worker, also runnable in the app's process; K3, events read from the ledger
   and woken by `LISTEN`/`NOTIFY` (E2), with deltas through `NOTIFY` (E3); K4, it schedules runs; K5, every run
   started over HTTP goes through it; K6, a run starts in the request and the worker sends it (A).
5. **Decided: a run lost mid-way is resumed** by the next claim.
6. **Built: steps 0 to 2** (see "Built"): resuming a run and what a run starts with; the queue; the worker.
7. **Next: step 3**, the API through the worker, once E3's details are settled; then step 4, the controls a person
   and a page use (see "The plan" and "Open").

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
- **A trial holds every case** (`docs/chatddx.md`, glossary, "Trial"), where the old one held one. Variations
  started together are a few long runs, one per variation, rather than many short jobs. Fairness between owners,
  pausing and stopping act on runs, unless the worker schedules a run's items (K4).
- **No batch.** The old `queue.put(owner, batch, trials)` took a batch's id, each `JobModel` pointed at a
  `BatchModel`, and a batch's state was its jobs' state. A job here is a run, found by its trial and owner as any run
  is (`agents/wip-portal.md`, "Comparing variations").
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
What edges hand the worker, and what they get back. Take:
1. **The unit asked for**: a run started at an endpoint, for an owner, scored afterwards or not. The request starts it
   with `Bench.start` (K6), as `POST /api/runs` does today (`docs/api.md`, "Runs"); the worker sends it, finishes it
   and scores it with `Bench.score` (`src/chatddx/bench/runs.py`). Scoring a run again is a unit of its own: a run and
   the scorers it is left to, as `POST /api/runs/{id}/scores` asks.
2. **How its runs are found**: by trial digest and owner (`Bench.runs`; `GET /api/runs?trial=`), as any run is.
3. **The surface an edge calls**: queue, which gives the job's id; halt; and the events, by item from the ledger, with
   deltas (K3). A job's state is the queue's; what its run did is the ledger's, read from there and not copied.

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
progress"; `docs/store.md`, "The queue"), as identity's people and sessions are. Built in this shape (see "Built"),
which was a take:
- **A schema of its own** (`worker`), with migrations at every tier (`docs/store.md`, "Tiers") and the writer's
  grants to update it, which `docs/store.md` ("Roles and connections") names already. Tier 2 keeps the factors, the
  ledger and the catalog append-only, and leaves the queue out, as it leaves identity.
- **A job**: the owner, the started run, its endpoint and the slots it holds there, whether to score and by which
  scorers, its status (queued, under way, finished, stopped, failed), why, whether it is to halt, its worker, and when
  it was queued, claimed, last beat and ended. One job queued or under way per run. A job takes a run to its finish,
  and scores it when asked, so scoring a finished run again is a job too.
- **Claimed** with `SELECT … FOR UPDATE SKIP LOCKED`, as the old worker claimed (`worker.py:_taken`).
- **Controls per owner** (paused), and **workers** (id, last seen), updated in place too. "Lost" isn't a status: a
  job under way whose worker hasn't been seen for `settings.WORKER_LOST` is claimed again. Stopping is step 4's.
- **What the ledger holds isn't copied**: tokens, items and the finish are read from the run.

### K3. How events reach a page
- **E1. Read the ledger**: a page or the API polls the run's rows. Works from any process; item by item; no deltas.
  Built, as what the API tells a run with nothing under way in its process, a finished one included
  (`src/chatddx/api/runs.py:_told`).
- **E2. E1, woken by `LISTEN`/`NOTIFY`**: the worker notifies when an item starts or ends, and the API reads the rows
  then. No polling, and still from any process.
- **E3. E2, with deltas through `NOTIFY`**: a completion as it is written, batched to keep within `NOTIFY`'s payload
  limit (8,000 bytes). The deltas are case-derived, and pass through the database, which holds the ledger already.

Decided: E2, and E3 with it. The API's events hold deltas (`item.delta`, `judge.delta`, kept until their item or
call ends, `docs/api.md`, "Its events"), the home page shows the model thinking or writing with its tokens so far, and
the run's island unfolds an item's text as it streams (`agents/wip-portal.md`, "Swift", R3). Without deltas from the
worker, the API wouldn't stay as it is.

### K4. The unit it schedules
- **Runs.** A run is sent whole by one worker, up to its own concurrency. A long run holds its endpoint's slots until
  it ends, and pause and stop act at the run's next item (`Running.stop`) or at once (`Running.halt`).
- **Items.** The worker hands out a run's items, so owners take turns item by item, as the old jobs did. It needs
  several processes writing one run's log, which the runner doesn't do: one `Running` sends one run.

Decided: runs, with `max_jobs` shared by the runs on one endpoint through their executions. Built: a job holds as
many slots at its endpoint as its run's concurrency, and a claim fits it within the endpoint's `max_jobs`, counting
the jobs under way there.

### K5. Which runs go through it
- **Every run started over HTTP**, the portal's and the API's: one path. `POST /api/runs` answers 202 and the run's
  path, and the stream is `GET /api/runs/{id}/events`, as built in the app's process (`docs/api.md`, "Its events").
- **Runs started together only**, a single run staying in the request.

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
  (an unset secret, an endpoint that doesn't answer) becomes the job's failure, as the old "skipped", and
  `docs/api.md`'s "Starting one" changes.

Decided: A. It keeps the API's contract and its refusals up front, the worker sends only what resuming already
needs it to send, and a started run is in the ledger before anything is queued. A queued job is a started run, so it
counts against `settings.RUNS_PER_DAY` as any run does, and the gate's refusals come before it is queued.

## Below the worker
Built, as step 0:
- **Resuming.** `Runner.resume(run)` loads an unfinished log's items and canary calls into a `Running`, which sends
  only what the log lacks (`src/chatddx/runner/run.py`). The gate, the endpoint's `max_jobs` and its URL are checked
  again, a finished run is refused, and the finish notes `run.resumed`: how many items the log held, and a warning
  when another rig resumes it than started it. `Bench.resume` resumes a run of the person's own. Two processes
  resuming one run collide on `ledger.run_item`'s key; the queue's claim keeps it to one.
- **What a run starts with.** `Bench.start` takes seeds, the replicates, cleanup steps, an execution and a canary set
  by digest, and `settings.ITEMS_PER_RUN` counts cases times seeds. `Bench.again` keeps a run's cleanup, execution and
  canary set under new seeds.

Not built:
- **`max_jobs` beside the worker.** The worker keeps the runs it sends within an endpoint's `max_jobs` (see K4), but
  the repl's runs, the API's jobs in the app's process and judge calls don't count. vLLM queues what's over
  `--max-num-seqs` rather than refusing it, so the cost is batching that the runs' `execution` doesn't show.
- **The edges still pass one seed**, no cleanup, the default execution and no canary set: the repl, the API and the
  scripted runs. `POST /api/runs` taking seeds and cleanup steps is the API's (`docs/api.md`, "Not covered"), and the
  portal's run form follows (`agents/wip-portal.md`, "Comparing variations", C3). Which canary set a run gets, the
  World's or the person's pick, and whether cleanup is picked at a run's start or carried by the configuration, are
  open.

Still the runner's, and met here:
- **A call still waiting for its engine to answer at all** waits on after a halt, under an execution with no timeout;
  only a stream can be shut down (`docs/runner.md`, "What a stop leaves out"). A halted run's worker thread waits
  with it.

## Built
- **Step 0**: see "Below the worker".
- **Step 1, the queue.** Schema `worker` at every tier: `worker`, `job` and `control`, the writer's SELECT, INSERT and
  UPDATE without DELETE, the reader's nothing, and at tier 2 checks on how a job stands and a trigger that keeps what
  it was asked to do (`src/chatddx/store/migrations/0019-t0-worker.sql` to `0021`). `Queue`
  (`src/chatddx/store/queue.py`): `put`, `job`, `open`, `jobs`, `halt`, `pause`, `paused`, and the worker's `enlist`,
  `claim`, `beat`, `end`, `requeue` and `waiting`. Claims take turns under an advisory lock, so that slots are counted
  alike by several workers. Tests: `src/chatddx/store/test/test_queue.py`. `docs/` has suggestions for it.
- **Step 2, the worker** (`src/chatddx/worker/worker.py`, `chatddx worker`). `Worker.serve(stopping)` enlists, then
  beats every `settings.WORKER_BEAT` and claims what fits; each job runs on a thread of its own, with a connection and
  a bench of its own: the run resumed (`Bench.resume`, since the request started it), sent and finished, then scored
  when asked (`Bench.score`). On a beat:
  - a halt hangs the run's calls up, finishes it unscored, or stops its scoring; the job ends stopped;
  - an owner who paused has the run stop after its items under way, left unfinished, and the job queued again, why
    `paused`; unpausing lets the next claim resume it. A scoring under way goes on;
  - a job another worker took over is let go, as a run stopped and not ended.
  A job that raises ends failed, with why: a run the gate refuses now fails so. A stopping worker stops its runs after
  the items under way and queues them again, why `its worker stopped`, and waits for its scorings. Tests:
  `src/chatddx/worker/test/test_worker.py`, the worker on a thread against the fake vLLM.
- **Resuming a run with nothing written** by the rig that started it notes nothing, since the worker sends every run
  the request started so (`src/chatddx/runner/run.py:_resumed`).

## The plan
On the decisions above, and the takes left.
0. **Below the worker**, built: resuming (`src/chatddx/runner/`), and `Bench.start` taking seeds, cleanup steps, an
   execution and a canary set.
1. **The queue**, built (see "Built").
2. **The worker**, built (see "Built").
3. **The API**: `POST /api/runs`, `/again` and `/scores` queue a job and answer 202 as now, a run started in the
   request before its job is queued (K6);
   `GET /api/runs/{id}/events` streams from the ledger, woken by the worker, with its deltas (E2, E3);
   `POST /api/runs/{id}/halt`. The person's jobs and their state (`GET /api/jobs`, or under runs).
4. **Controls**: pause, resume and stop for an owner, and the status a portal page shows.

## Open
- **The repl beside the worker**: the repl's runs don't count against the worker's shares of `max_jobs`. The repl
  could ask the worker too, and follow the events.
- **Fairness between owners**: queue order, or turns per owner, per endpoint.
- **A resumed run the gate refuses**: the World changed while it waited, as a clearance withdrawn or a secret unset.
  Built: the job fails, with why, and the run is left unfinished. Left queued until it passes is the other way.
- **E3's details**, for step 3:
  - **A stream joined mid-item.** The API keeps an item's deltas until it ends, so a stream joined while it streams
    gets its text so far. Under E3 a replica has only the deltas sent since it listened: the worker could notify an
    item's text so far now and then, or a stream joined mid-item gets the text once the item ends.
  - **One numbering of events.** A job in the app's process numbers its deltas with the rest, and the ledger's
    telling doesn't (`src/chatddx/api/jobs.py:replayed`), so an id from one isn't a place in the other. Under E3
    every replica tells every run, and an id has to mean the same in each.
  - **`NOTIFY`'s queue.** A payload waits in the database's notification queue, kept on disk (`pg_notify/`), until
    every listener has read it, and a listener that stops reading holds the queue up for all. Deltas are
    case-derived, so they pass through the database that holds the ledger's completions already; nothing new is
    stored.
- **Deployment**: one worker or several, and whether each is a Kubernetes Deployment of its own. Several take turns
  to claim, so either works; `chatddx portal` and `chatddx api --worker` starting one on a thread (K1) come with
  step 3, when the API queues runs.
- **A stopping worker waits for its scorings**, which judges can make long, beyond a Kubernetes grace period. A
  scoring halted instead finishes its score with what it has, and the next claim would score again.
- **Slots while scoring**: a job holds its run's slots until it ends, its scoring too, while the judges' calls go to
  their own endpoints.
- **A job at an endpoint the inventory lost** is claimed and fails at the gate, rather than waiting.

## Moved here
- From `agents/wip-portal.md`: "Below the UI", 1, runs that outlive the request, and the worker's part of "The batch
  planner and the worker".
- From the runner's plan, since solidified as `docs/runner.md`: "Resuming" and "`max_jobs` across runs".
- From `agents/wip-api.md` at 100a078, "Open": "Long requests".
- From `agents/wip-batch.md`, removed when the batch was dropped: seeds and cleanup steps for `Bench.start`.
- Settled with K6's A: "Jobs that can't start" (a job is a started run) and "Quotas" (a run counts as it starts).

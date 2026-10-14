# The worker: work in progress

The worker runs trials outside the process that asked for them, so that a run outlives a restarted app and is seen,
followed and halted from every replica. This file plans it, and the port of what the old worker did. Steps 0 to 4 are
built (see "Built"): what it stands on, the queue, the worker, `chatddx worker`, the API through it, its runs,
scorings and halts queued and its events told from the ledger's rows, woken by `NOTIFY`, with the worker's deltas; and
a person's controls of their queue, with each run's job on the runs page.

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
6. **Built: steps 0 to 4** (see "Built"): resuming a run and what a run starts with; the queue; the worker; the API
   through the worker; controls and status.
7. **Decided: what's next** (see "What's next, decided"), but T4, the repl beside the worker. R1 to R5, T1 to T3, C1,
   C3, W1, and C2 as far as queue order goes, are built. Next to build: W2, then the NixOS module (see "The plan").

## Why
Until step 3:
- **A run was a job in the app's process**: `POST /api/runs` answers 202 and the run's path, the run is sent on a
  thread of its own (`src/chatddx/api/jobs.py`, since gone), followed by `GET /api/runs/{id}/events` and halted by
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

Since, decided (W1): `chatddx portal`, a convenience for development, runs a basic worker in its process, and
`chatddx api` runs none: a deployment runs the HTTP server, the API and the worker as separate systemd services on
NixOS.

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
  Built before step 3 as what the API told a run with nothing under way in its process.
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
  the repl's runs and judge calls don't count. vLLM queues what's over
  `--max-num-seqs` rather than refusing it, so the cost is batching that the runs' `execution` doesn't show.
- **The repl and the scripted runs pass one seed**, and take the rest from the inventory (R1 to R4, built). No
  World's endpoint names a canary set yet: a scripted run's turns would have to answer its canaries too.

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
- **Step 3, the API through the worker** (T1 to T3, R5, W1):
  - **The ledger's rows counted.** `ledger.seq`, one sequence, numbers every row of every ledger table as it is
    written (`src/chatddx/store/migrations/0022-t0-ledger-seq.sql`, `0023`), and `Store.rows_of(run, after)` reads a
    run's rows and its scores' after a number, in order. `Store.append` notifies the run's channel, `run.<id>`, with
    `rows` in the transaction that writes them, so any writer wakes those following the run, the repl's included.
  - **The queue notifies.** `put`, `halt`, `pause`, `end` and `requeue` wake the workers on `worker`, and `put`, `end`
    and `requeue` tell the run's channel how its job stands (`job <status>`); `Queue.last` is a run's latest job. The
    worker waits on `worker` between beats, so it claims a job and sees a halt at once, and on a socket pair, which
    `Worker.wake` writes to, so it stops at once and sees a job thread end.
  - **The worker publishes** what a run's rows don't say (`src/chatddx/worker/publish.py`), on a connection of its own
    per job: an item started, its deltas and tool runs, the scoring starting, judges asked, their deltas and answers,
    and the scoring over. Deltas wait up to `EVERY` (0.1 s) and go out merged by item and kind; an item's deltas still
    held when its row lands go unsaid. Payloads are packed to stay under `NOTIFY`'s 8,000 bytes, and cut in parts when
    one event doesn't fit (`src/chatddx/store/notify.py`).
  - **The API** starts a run in the request and queues it (`POST /api/runs`, `/again`), queues a scoring
    (`/scores`, 409 while the run has a job open) and halts through the queue (`/halt`). `GET /api/runs/{id}/events`
    (`src/chatddx/api/telling.py`) listens on the run's channel before it reads, tells the rows after `Last-Event-ID`,
    each row's last event carrying its number, then, while a job is open, what the worker says and the rows as they
    land, and ends with the latest scores unless told them, the job's failure, and `done`. A stream joined mid-item is
    told the item started and each tool run once (T2). One listening connection per app process fans out to its
    streams (`src/chatddx/api/listening.py`), woken through a socket pair to listen at once; a stream that falls
    1,000 messages behind drops them and reads the ledger again.
  - **Where the worker runs.** `app(..., worker=True)` runs one on a thread for the app's lifespan: `chatddx portal`
    does, and the tests; `chatddx api` doesn't. `src/chatddx/api/jobs.py` is gone, and `settings.ITEMS_PER_RUN` is
    1,000. The portal's run page asks the queue whether a job is open before it reads the run, since a job ends
    once its run's rows are written, and the run's island makes an item per case and seed.
  - Tests: `src/chatddx/store/test/test_notify.py`, `src/chatddx/worker/test/test_publish.py`, a worker woken by a
    queued job under a five-minute beat (`test_worker.py`), `src/chatddx/api/test/test_telling.py`, and the API's runs
    and scores tests rewritten: ids are rows' numbers, another app tells a run's rows alike, and a test that looks for
    what isn't a row pauses the owner's queue until its stream listens (`test_runs.py:joined`).
- **Step 4, controls and status** (C1, C3; C2 as built):
  - **The queue.** `Queue.stop(owner, now)`: the first press ends the owner's queued jobs stopped, why `taken out of
    the queue`, their runs left unfinished, and the runs under way go on; `now` asks their jobs under way to halt too,
    as a run's halt does (C1's take). `Queue.standing(owner, lost)`: paused, how many queued and under way, and the
    workers seen within `lost`. `Queue.placed(runs)`: each run's latest job, and while it is queued, how many jobs at
    its endpoint are under way or are to be taken before it (owners who paused left out); none while its owner has
    paused (`src/chatddx/store/queue.py`).
  - **The API.** `GET /api/queue`, `POST /api/queue/pause`, `/resume` and `/stop` (`now`)
    (`src/chatddx/api/queue.py`); a run, listed or read, says its latest job (`Run.job`); and
    `POST /api/runs/{id}/resume` queues an unfinished run with nothing open for it again, refused as a run is started,
    so that a run taken out of the queue, or whose job failed, is sent on.
  - **The runs page** says how the person's queue stands, warns when nothing queued is taken for want of a worker,
    and has Pause or Resume, and Stop while something is queued, else Stop now while something is under way: the old
    two presses, told apart by what is left. Each run's row says its job, and a run's page says it too and offers
    Resume for an unfinished run with nothing open (`src/chatddx/portal/runs.py`, `templates/runs.html`).
  - Tests: `src/chatddx/store/test/test_queue.py`, `src/chatddx/api/test/test_queue.py`, and
    `src/chatddx/portal/test/test_running.py`.

## The plan
On the decisions above.
0. **Below the worker**, built: resuming (`src/chatddx/runner/`), and `Bench.start` taking seeds, cleanup steps, an
   execution and a canary set.
1. **The queue**, built (see "Built").
2. **The worker**, built (see "Built").
R. **What a run is started with** (R1 to R4), built: the inventory's cleanup per source
   (`src/chatddx/inventory/sources.py:Source.cleanup`), and canary set and default execution per endpoint
   (`inventory.py:EndpointSpec`), which `Bench.start` takes unless given; `POST /api/runs` taking seeds or replicates,
   cleanup, a concurrency and an order, `/again` seeds or replicates, and `run.started` giving the seeds; the
   variation's island taking a replicates count. The island doesn't offer cleanup, a concurrency or an order yet.
3. **The API through the worker** (T1 to T3, R5, W1), built (see "Built"): the ledger's rows counted; `POST /api/runs`, `/again` and
   `/scores` queue a job and answer 202 as now, the run started in the request (K6); `GET /api/runs/{id}/events` from
   the ledger, woken by the worker, with its deltas through `NOTIFY`; `POST /api/runs/{id}/halt` through the queue;
   `chatddx portal` running a worker in its process; `src/chatddx/api/jobs.py` gone.
4. **Controls and status** (C1 to C3), built (see "Built"): pause, resume and the two presses of stop for an owner,
   and the runs page's status.
5. **A stopping worker's deadline** (W2), with the scorers a job has finished kept.
6. **A NixOS module** running the HTTP server, the API and the worker as systemd services (W1).

## What's next, decided
Decided by the user, item by item; T4 is the one take left. T for step 3, the API through the worker; R for what a
run is started with over HTTP, which doesn't wait on the worker; C for step 4; W for running the worker.

### Step 3
- **T1. Event ids. Decided, built: by the ledger's rows.** A run's events are numbered by its rows, in the order they were
  written, and what isn't a row (deltas, an item started, a judge asked) carries no id, as `docs/ledger.md`
  ("Telling a run as it was written") has it. It needs a column counting the ledger's rows as they land, at tier 0,
  and ends `src/chatddx/api/jobs.py:replayed`'s workaround. The others were a counter the worker keeps per run, lost
  when it restarts, and no ids at all.
- **T2. A stream joined mid-item. Decided, built: its text from when it joined**, and the whole once the item ends. The
  others were the worker answering a join with the text so far, and the worker notifying each item's text now and
  then.
- **T3. `NOTIFY`. Decided, built: a channel per run**, deltas batched to stay under 8,000 bytes, and one listening connection
  per app process fanning out to its streams, so a stream that stops reading holds up nothing.
- **T4. The repl beside the worker.** Open. (a) As now: it sends in its own process, where Ctrl-C halts, and its runs
  don't count against `max_jobs`. (b) It queues its runs and follows their events. (c) It sends in its own process but
  holds slots in the queue, as a worker claiming its own job. Take: (a), and (c) once endpoints are shared and busy.

### What a run is started with
- **R1. Seeds. Decided: `seeds`, or `replicates` drawn** when none are given. `run.started` gives the seeds, and
  `/again` draws as many as the run had unless given. The variation's island gets a replicates count beside its seed,
  and says that a greedy skeleton's replicates send the same request, measuring the engine's nondeterminism.
- **R2. Cleanup. Decided: each source's, in the inventory, and the request may override it.** Ops write a source's
  steps, since CRLF, a BOM or NFC are a source's quirks; a run takes its cases' sources' steps, in `CleanupOp`'s order,
  unless its request gives its own, `[]` for none. So runs on one source agree unless a researcher varies it.
- **R3. Canary set. Decided: each endpoint's, in the inventory**, by digest, so every run at an endpoint probes it
  alike and runs can be compared.
- **R4. Execution. Decided: each endpoint's default in the inventory** (a timeout, retries), the request choosing a
  concurrency up to `max_jobs` and an order. R9 ("Concurrency stays 1", `agents/wip-portal.md`) ends with step 3.
- **R5. The limits. Decided, built: `settings.ITEMS_PER_RUN` is raised to 1,000** once runs are queued (step 3), as a run no
  longer ties up a request; it counts cases times seeds.

### Step 4
- **C1. Stop. Decided, built: the old two presses.** The first takes the owner's queue out: their queued jobs end stopped,
  and the runs under way go on. The second stops those too. Take, for what a stop leaves: a run taken out of the
  queue is left unfinished, so that it can be queued again and resumed; one stopped under way is halted, as a run's
  halt is. Built as the take has it, with `POST /api/runs/{id}/resume` to queue such a run again.
- **C2. Fairness between owners. Decided: queue order, as built, then turns per owner at each endpoint** once people
  wait on each other. Turns aren't built.
- **C3. Where the status shows. Decided, built: on the runs page**: each run's job and why, how many are ahead at its
  endpoint, and pause, resume and stop.

### Running the worker
- **W1. Where. Decided, built but the NixOS module:** `chatddx portal`, a convenience for development, runs a basic worker in its own process. A
  deployment runs the HTTP server, the API and the worker as separate systemd services on NixOS: `chatddx worker` is
  one of them, and `chatddx api` starts no worker. The flake has no NixOS module yet.
- **W2. A stopping worker's scorings. Decided: up to a deadline**, within the service's stop timeout, then the
  scorings are halted and the job queued again to score what is left. What is left needs the scorers a job has
  finished kept with it, since a job's scorers are fixed: a column of its own, updated in place.
- **W3. Slots while scoring. Decided: as built**, a job holds its run's slots until it ends.
- **W4. A run the gate refuses as it resumes. Decided: as built**, the job fails, with why.

## Open
T4 is open (see "What's next, decided"). Beside it:
- **The rows' order is their writer's.** `ledger.seq` gives numbers as rows are inserted, and a stream reads the rows
  after the last it told; a row committed after one with a higher number would be missed until the stream starts
  again. One writer per run keeps the two orders alike: the queue holds one job open per run, the runner and the
  scoring pass write a log's rows one transaction after another. A repl scoring a run while the worker writes it
  doesn't.
- **What isn't a row is told only to those listening** (T2): `run.scoring` when the scoring starts, a judge asked, an
  item started, so a stream that joins after them misses them, and a test that looks for them pauses the owner's queue
  until its stream listens. Notes along the way (`run.noted`, `score.noted`) are told with the finish row that holds
  them, not as they happen.
- **A connection per stream**, held while it is open, beside the one listening connection per process, and two per
  job a worker holds (`docs/api.md`, "Serving", has a suggestion).
- **A stopping app's worker waits for its scorings** (W2 isn't built), so `chatddx portal` and a test's app stopping
  mid-scoring wait for it.
- **`NOTIFY`'s queue** (T3): a payload waits in the database's notification queue, kept on disk (`pg_notify/`), until
  every listener has read it, and a listener that stops reading holds the queue up for all. Deltas are case-derived,
  so they pass through the database that holds the ledger's completions already; nothing new is stored.
- **Several workers** take turns to claim, so one or several work alike.
- **What W1's HTTP server is**: the portal's pages served apart from the API, or a proxy in front of both. The
  portal is one app with the API today (`agents/wip-portal.md`, "P3b, concretely"), and its `__Host-` cookie wants one
  host for both.
- **What C1's second press leaves**: built as the take has it, a halted run, finished, so it can't be resumed; leaving
  it unfinished instead would mean its calls under way are recorded as stopped and its items aren't sent again.
- **"Ahead" counts jobs, not items**: a run of 1,000 items ahead counts as one, as a run of one does. The workers
  seen are counted for anyone's jobs, not the person's endpoints.
- **A job at an endpoint the inventory lost** is claimed and fails at the gate, rather than waiting.

## Moved here
- From `agents/wip-portal.md`: "Below the UI", 1, runs that outlive the request, and the worker's part of "The batch
  planner and the worker".
- From the runner's plan, since solidified as `docs/runner.md`: "Resuming" and "`max_jobs` across runs".
- From `agents/wip-api.md` at 100a078, "Open": "Long requests".
- From `agents/wip-batch.md`, removed when the batch was dropped: seeds and cleanup steps for `Bench.start`.
- Settled with K6's A: "Jobs that can't start" (a job is a started run) and "Quotas" (a run counts as it starts).

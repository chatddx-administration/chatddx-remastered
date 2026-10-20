# Error handling: work in progress

How errors are raised, caught and told, by who they are for and when they can be known (`AGENTS.md`, "Errors").
"Decided" means the user said so; "Take" is the agent's recommendation and still open.

## The model
Decided: three classes.
1. **Crash at startup.** The database is largely immutable, so some errors can be ruled out by a check: if it passes
   as a process starts, they can't occur while it runs. Such a check crashes the start.
2. **Raw to stderr and the edge.** Runtime errors for developers and ops, the unexpected included, are printed to
   stderr and/or forwarded to the edge as they are.
3. **Part of the UX.** Runtime errors for researchers and clinicians tell them what to do. Telling a researcher that
   something is ops' to mend is acceptable only when it couldn't have been fully anticipated at startup.

Decided:
- A thread is never deleted: deleting it says `deleted`, and it keeps what it holds.
- Shipped code isn't kept forever: a release may drop or bump a scorer's, a tool's or a kind's version that stored
  components pin. A planned garbage collect may ease this. Until then, a component pinning code the running chatddx
  doesn't ship is a state, told to researchers (class 3), not a crash.
- Raw errors go to stderr and the edge even when they may carry sensitive content, for now
  (`agents/wip-clearance.md`, "Before real patient data", 13).

Take, refining the model:
- **What a startup check guarantees.** Only what nothing changes while the process runs: the code, settings and the
  environment, the inventory, the built frontend, the migrations, and the store, which is append-only and checks
  every component it is given. The catalog changes at runtime: `init-data` is an operator's command beside the live
  services, with no restart after it (`agents/wip-deploy.md`), and an owner may delete and restore any thread of
  theirs, the archive's model threads included (`src/chatddx/bench/saying.py:say`). A check on catalog state holds
  only when every writer of it refuses what the check rules out; what gets through anyway falls to class 2.
- **Class 1 has two moments**: the tests, for what the code alone decides (a registry covering its `Literal`, as
  `src/chatddx/factors/cases.py:_OPS` and `CleanupOp`, which nothing ties together today), and startup, for what the
  code, the World and the store decide together.
- **Class 1 lets catches go, class 2 needs no code.** What startup ruled out isn't caught at runtime; if it happens
  anyway, it surfaces uncaught, which is class 2.
- **One failure can be both 2 and 3.** An endpoint that goes down under a run is ops' to mend (stderr) and ends a
  researcher's run, who is told so.
- **Types.** A refusal (class 3) is a `ValueError`, which `src/chatddx/api/state.py:refused` answers as a 422, so a
  class 2 error must not be one, or it reads as a refusal: a developer's `ValueError` (an unpacking, say) reaches a
  researcher as one today.

Open:
- The user's class 3 names "ops and clinicians", where the sentence before puts ops' runtime errors in class 2; read
  here as researchers and clinicians.
- A `@sensitive` decorator on every function that may handle sensitive content, so that its errors are handled
  otherwise (suggested by the user; `agents/wip-clearance.md`, "Before real patient data", 13).
- `docs/chatddx.md`, "Findings": a finding is anything declared that doesn't match what was observed, and
  `endpoint.model_shared` and `endpoint.engine_unknown` are findings today, though class 1 would crash a start on
  them. The doc may want a line on which findings stop a start.

## Findings at 36ba74d
### The way from a judge to its engine
| Error | Depends on | Class | Then |
|---|---|---|---|
| Several endpoints serve one handle's weights (`Inventory.serving`) | the inventory | 1 | a finding (`endpoint.model_shared`) the worker logs and init-data prints; the portal never checks; researchers told "ops' to mend" |
| No endpoint serves a live handle's weights | the inventory and the model threads | 1, if init-data refuses to leave a handle unserved and restoring a model thread does too | checked nowhere; told at runtime |
| Weights under several model threads (`Seen.handle`) | the model threads | 1, with the same refusals | checked nowhere |
| Weights under no live handle | the model threads; the archive deleting one causes it | a deleted handle still holds its weights (Decided), so a state: class 3 | told "ops' to mend" at runtime |
| Behind its handle | the researcher's choice | 3 | as it should be |
| A scorer of code that isn't shipped | the stored scorers and `SCORERS` | 3, as shipped code isn't kept forever (Decided) | crashed (`src/chatddx/portal/scoring.py:code_of`) |

The catches: `src/chatddx/portal/scoring.py:_judges` (silent), `src/chatddx/api/scores.py:judge_asked` (a
placeholder model), `src/chatddx/bench/seen.py:judging` (lints without the runtime pair), `Seen._applies` (the
scorer left out), `Seen.unscored` (left to score), `src/chatddx/portal/threads.py:_judge` (told), and step 2b's
`Seen.latest` and `Seen.under` (silent), `GET /api/models`, the look, Refine and the repl (told, "ops' to mend").

### Elsewhere
Class 1 candidates, each depending only on what is fixed once a process starts:
1. **An endpoint's secret isn't set** (`src/chatddx/runner/gate.py:_secret`): found as a run is admitted, a 422
   "refused", a failed job in the worker. The portal and the workers are separate processes, so the portal can take
   a run that a worker without the variable fails at every resume.
2. **An endpoint's engine isn't in the store** (`Seen.endpoint`): researchers told "load its World with init-data";
   the inventory check finds it, only logged and printed.
3. **An endpoint's canary set isn't in the store** (`src/chatddx/bench/runs.py`, at a run's start): a 422; checked
   nowhere.
4. **Vignette sources**: a stored case whose source isn't in the inventory (`gate.py:bar`, `bench/runs.py:_cleanup_of`)
   or a directory source whose path is missing or unreadable (`src/chatddx/inventory/sources.py`), a 422, a 500 or
   a `case.unreadable` finding per item; no database source, or several, for typed cases
   (`src/chatddx/bench/cases.py`), a 422, which `Inventory.takes_typed` swallows.
5. **A database not migrated**: nothing checks as a process starts; the portal answers its first query with a 500,
   and the worker crashes at start only by accident. `src/chatddx/store/migrate.py:pending` exists.
6. **The frontend not built**: a warning at start (`src/chatddx/cli.py:_unbuilt`), then unstyled pages.
7. **The inventory check refuses nowhere**: `chatddx portal` and `api` never run it, the worker logs it, init-data
   prints it and exits 0, import-engine prints it and writes anyway.
8. Already class 1: a missing setting (`src/chatddx/settings.py`) and an invalid inventory crash a start with a
   traceback.

Class 3 by the decision on shipped code, crashing or refused raw today: stored tools a release no longer ships
(`src/chatddx/runner/rounds.py`, a `LookupError` as a run starts), and stored components of a kind or version the
running code can't read (`src/chatddx/factors/kinds.py:parse_component`); Judge and Scorer are at version 2, so a
database holding version 1 judges fails at each read.

A bug: `nix/module.nix` gives `chatddx portal` and `chatddx worker` `--facts`, which neither takes
(`src/chatddx/cli.py`), so both services fail to start whenever `services.chatddx.facts` is set.

## Built: step 1, the way from a judge to its engine
- **Class 1** (`src/chatddx/bench/handles.py:broken`, `src/chatddx/inventory/check.py:broken`): weights held by several
  model threads, deleted ones counted, and weights served at several endpoints. `chatddx portal`, `api`, `run`,
  `worker`, `repl` and `scripted-runs` don't start on them (`src/chatddx/cli.py:_held`); init-data checks before it
  commits and refuses, writing nothing; the engine import refuses to write. `endpoint.model_shared` is no longer a
  finding. Only init-data writes model threads, and a restore can't add a holder of weights, as deleted threads are
  counted, so neither can turn up while a process runs.
- **Not class 1, as planned**: a live handle no endpoint serves. init-data keeps the archive's threads of other
  Worlds, saying they're "not in the data", so a database may hold handles this World doesn't serve; that is a state,
  not a broken World. An endpoint whose engine isn't stored stays a finding: before init-data, the store is empty,
  and a deployment starts its services before init-data (`nix/test.nix`).
- **Class 3** (`src/chatddx/bench/seen.py:Seen.served`): a deleted handle ("model X is deleted: pick another"), as a
  thread is never deleted and keeps its weights; one no endpoint here serves ("no endpoint here serves model X: pick
  another"); and behind, as it was. `Seen.handle` counts deleted threads, and `Handle.deleted` says it. A scorer of
  code that isn't shipped at its version has no editor, its page saying so (`src/chatddx/portal/scoring.py:unshipped`),
  no composer on Review, and no measures in its views there.
- **Class 2**: what can't be caught is raised as a `LookupError`, not a `ValueError`, so that it isn't answered as a
  refusal: `Seen.handle` for weights held by other than one thread. The catches of it went: `_judges`,
  `judge_asked`, `judging`, `Seen.latest`, `Seen.under`, `GET /api/models`, the look, the repl. The API and the portal
  answer what isn't caught raw, a 500 with its type and message (`src/chatddx/api/app.py:_raw`), and uvicorn prints
  its traceback to stderr.
- **Pruned**: `Model.problem` of `GET /api/models`, which lists the handles served here, each with its engine; the
  Models page's problem, and the portal's filters on it.
- **Tests**: `test_init.py`, init-data refusing and writing nothing, and `api` and `worker` not starting;
  `test_serving.py` and `test_o11n.py`, the inventory's half; `test_world.py`, a model not served here, and a World
  broken under a running app answered raw; `test_seen.py`, a deleted handle; `test_library.py`, a scorer of code
  not shipped; the serve commands' tests run on a test database, as they check it now.

### What step 1 leaves
- **A stored model held by no thread** isn't checked: only init-data stores models, each with its thread. Naming one
  raises raw.
- **The rest of "Elsewhere"**: secrets, canary sets, sources, migrations, the frontend, tools and kinds.
- **`Seen.served` still catches** the inventory's `LookupError`, as the "none" it can only be, several being ruled out
  at start; an inventory method telling who serves weights would spare the catch.

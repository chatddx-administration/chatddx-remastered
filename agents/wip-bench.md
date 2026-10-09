# The bench: work in progress

The bench is what one person works with: the threads, families and runs they see, the World's endpoints, and the cell
they build up. It sits over the store, the catalog, the runner and the scoring pass. It was built for the repl
(`agents/wip-repl.md`, phase 3 and "Built: 4a"), and moved out of it so that what it is can be decided apart from the
shell.

"The old bench" is chatddx-administration/chatddx at 504792c: `src/chatddx/bench/`. Old permalink base:
https://github.com/chatddx-administration/chatddx/blob/504792cbeb09508f2c52912be29a3d8809d2fa1d/

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. Phase 0 is done: the bench is a root-level package, `src/chatddx/bench/` (see "Phase 0").
2. Phase 1 waits for the user's word: what the bench is (see "Phase 1"). The options are B1–B4. The take is B3, a
   person-scoped view with a boundary.
3. The sub-decisions S1–S7 follow from that choice; each option settles them differently.

## Phase 0: out of the repl
Done.
- `src/chatddx/repl/bench.py` moved to `src/chatddx/bench/bench.py` unchanged. `src/chatddx/bench/__init__.py` exports
  its public names, as `chatddx.store` does.
- The repl, its tests and `src/chatddx/cli.py` import from `chatddx.bench`. The bench imported nothing from the shell,
  so nothing else changed, and the same 433 tests pass.
- The bench has no tests of its own. The repl's tests cover it (`src/chatddx/repl/test/conftest.py`, `bench`).

## What the bench is now
`Bench(conn, person, inventory, facts)` (`src/chatddx/bench/bench.py`), with the values `Cell`, `Family`, `Reach`,
`Graded` and `Saved`.

The plan (`agents/wip-repl.md`, phase 3) called it "a person-scoped layer, the old `Bench`'s role. It holds the cell,
names, completions and lookups, and nothing in it is UI." Completions ended up in the shell instead
(`src/chatddx/repl/shell.py:Repl`). Each step of the shell added to it:
- 4a: the person's lookups (threads by name, families and their cases, the expectation they read);
- 4a: the cell's skeleton, either the stored head or `compile_request` on the recipe with the parts set;
- 4a: the provisional trial's lints, each scorer view's reach and coverage, and `save`;
- 4b: `start` and `score`;
- 4c: `described`, `rendered_again`, `scores_of`, `scored_by`, `unscored` and `outstanding`.

It holds a connection, the person, the World inventory, the facts, and caches of logins and of the model each engine
serves. There is one per repl process (`src/chatddx/cli.py:_repl`), and the shell holds it rather than being one
(`Repl.bench`), unlike the old `Repl(Bench)`.

The bench's parts, by what each one needs:

| Part | Methods and values | Needs the person |
|---|---|---|
| Person-scoped reads | `threads`, `names`, `thread`, `holder`, `families`, `family`, `tags`, `expectation`, `scorers`, `run`, `scored_by`, `unscored`, `outstanding`. Most of them wrap `Reads` | yes |
| Person-agnostic helpers | `get`, `title`, `about`, `login`, `model`, `endpoint`, `labels`, `trial`, `described`, `rendered_again` | no |
| The cell | `Cell` (the configuration's head edit and recipe, the parts set over it, the endpoint and its engine); `configuration`, `chunk`, `skeleton`, `findings`, `reach` | for finding names, and `reach` for expectations |
| Writes for the person | `save` (a thread or a new edit, and a compilation), `start` (through `Runner`), `score` (through `score_run`) | yes: they write owner entries |
| Shell vocabulary | `KINDS` ("what the shell calls each kind of thread"), `NONE`, `SEEDS` and `drawn_seed` ("so the prompt stays readable"), and messages such as "picked by the endpoint in the cell" | no |

`scores_of` and `owner` sit on the edge between the first two parts. `scores_of` names each scorer by the thread the
person sees, and `owner` gives "" for the person's own.

## The landscape
### Layers today
```
edges     repl, cli                     to come: portal, API, worker, export, `chatddx samples`
            │   ╲ reaches through bench.store, bench.catalog, bench.reads, bench.inventory, bench.facts
bench     Bench, Cell
            │
services  runner: Runner, score_run     seed: init-data
            │
store     Store, Catalog, People, Rows, Reads(conn, person)
            │
model     factors, ledger, catalog's rules, identity, facts, inventory, scorers
```

This is the import graph between top-level packages, without tests:
- `bench`: catalog, core, factors, facts, identity, inventory, ledger, runner, store.
- `repl`: bench, catalog, factors, facts, inventory, ledger, runner, scorers. The repl doesn't import `store`, and
  reaches the store only through the bench's attributes.
- `runner`: catalog, core, factors, identity, inventory, ledger, scorers, store.
- `seed`: catalog, core, factors, facts, identity, inventory, scorers, store.
- `store`: catalog, core, factors, identity, ledger.
- `cli`: bench, repl, seed, store, and others.

### Who takes a person
Several layers already take a person:
- **The catalog's rules** take a person id: `src/chatddx/catalog/model.py:About.shows` (live, and owned or shared) and
  `src/chatddx/catalog/threads.py:expectation_for`. `Catalog.visible`, `visible_families`, `expectation_for` and
  `involving` pass it through (`src/chatddx/store/catalog.py`).
- **`src/chatddx/store/reads.py:Reads(conn, person)`**, the store's person-scoped lookup. It is what the store offers
  in "Looking things up for someone" (`docs/store.md`). The same doc doubts it under "Known gaps": "Person-scoped
  lookup may not belong in the store. `Reads` is mostly policy based on other modules' rules, which contradicts 'the
  store answers which rows exist; the modules decide what they mean'."
- **The runner** takes the person who will own the run or score: `src/chatddx/runner/run.py:Runner(conn, inventory,
  by)` and `src/chatddx/runner/score.py:score_run(…, person)`.
- **`Bench(conn, person, inventory, facts)`**.

`Reads` is the clearest example of what may belong in the bench. Everything in it answers what this person sees, and
the bench is its only caller outside `src/chatddx/store/test/test_reads.py`.

### How the repl uses the bench
The repl calls the bench's methods: `title` 12 times, `skeleton` 8, `get`, `endpoint` and `model` 5 each, and most of
the rest once or twice. It also goes around them through the bench's attributes, about 30 times:
- the person-scoped reads: `bench.reads.runs` (4), `bench.reads.scorers` and `bench.reads.reaching`;
- the store: `bench.store.run` (3), `bench.store.finished`, `bench.catalog.title` (2) and `bench.catalog.recipe`;
- the World and the facts: `bench.inventory.*` (7) and `bench.facts.models` (2);
- the person: `bench.person.login` and `bench.person.id` (6).

It also calls into the data model with `bench.get` 6 times, through `resolve` and `url_of`. The repl's tests open
`Store(bench.conn)` and `Catalog(bench.conn)` to check what was written.

So the bench is now a person-scoped view with helpers attached. It isn't a facade: nothing stops an edge from going
around it, and the repl does so through the bench itself.

### Rules held twice
- **The expectation a person reads for a case.** `Bench.expectation` takes the head of the person's first own thread,
  else of the first shared one, in any schema. `src/chatddx/catalog/threads.py:expectation_for` keeps only heads in
  the scorer's expectation schema, and refuses when there are several to choose from. `show case` reads the first
  rule, and `score` the second.
- **What is left to score.** `Bench.unscored` works it out per run and `Reads.outstanding` per scorer, and only the
  bench's answer is used (`docs/store.md`, "Known gaps"). This was a take in 4c, still open: the bench works per run
  because `score RUN` needs one run's answer, and because a run whose case has several expectations to choose from is
  then skipped for that scorer, rather than stopping the listing. `Reads.outstanding` could go, or `unscored` could
  move to `Reads`.
- **Finding things by name.**
  - `Reads.thread` finds a thread by its whole name, then as `OWNER/NAME`. On top of that, `Bench.thread` adds
    per-model names and the shell's kinds.
  - `Bench.family` finds a family on its own, own first, without `OWNER/NAME`.

### The old bench
- **Bound to a person**, by login: `Bench(identity_name, transport=None, own=())` (`src/chatddx/bench/bench.py`,
  `Bench`). It held no connection (Django held it) and no cell, and kept caches of names and models.
- **One per caller.** The API built one per request (`src/chatddx/django/api/runs.py`, `registry.py`), and so did the
  portal, narrowed with `own` (`src/chatddx/django/portal/owners.py:bench_of`). The worker cached one per owner
  (`src/chatddx/worker/worker.py`). The repl had one per process and subclassed it (`src/chatddx/repl/shell.py`,
  `Repl(Bench)`).
- **What came with it:**
  - `cell.py`: the immutable `Cell`;
  - `plan.py`: crossing a cell with variations into a batch, `Plan.of(bench, …)`;
  - `sending.py`: `Sending(bench, trial, …)`, a run's events, then `bench.recorded`;
  - `outcome.py`: pure functions;
  - `held.py`: the runs, jobs and scores that hold a configuration. It imported the worker's model.
- **What it enforced.**
  - `ready` refused a configuration that was neither the person's nor the archive's: `NotOwn`, "save it as your own
    first", 403 in the API.
  - It refused a missing secret (`NoSecret`), and a cell whose stack or configuration had changed since it was
    planned (`Drifted`, in `cell_read`).
  - It narrowed visibility on top of the store's rule: `SHARED_BY` kept configurations to the person's own and the
    archive's, and `own` kept only the person's own rows.
- **Never a facade.** Every edge but `dev/samples` went around it to the Django models:
  - the portal, in 19 of 27 files, with its own `get_queryset`s and `readable()` checks: 80 imports from `repo` and
    `history`, and 30 `.objects.` lines;
  - the API in 7 of 8 files, and the repl in 9 of 11;
  - the worker's queue throughout, and `logs/export.py` entirely.
- **The cost was rules copied.** The old `docs/datamodel.md`
  ([L93-L104](https://github.com/chatddx-administration/chatddx/blob/504792cbeb09508f2c52912be29a3d8809d2fa1d/docs/datamodel.md#L93-L104)):
  "whether an identity may read a row, a trail's name for an identity and who else holds a fingerprint were each
  re-implemented in the portal, the API, the repl and the bench: five copies of the versions list, three of the name.
  They are the store's now […] and the apps ask it."

  The fix moved the rules down into the store, not up into a facade. Remastered's `Reads` descends from that fix, and
  `docs/store.md` now doubts it.

How the old bench maps onto remastered:

| old (504792c) | remastered | notes |
|---|---|---|
| `Cell`, `set` a slice (`bench/cell.py:Cell.set`) | `Cell.set`: swap a recipe part, then `compile_request` to an unsaved skeleton | shown by `Catalog.title_of` |
| `save` (`bench/bench.py:Bench.save`) | `Bench.save`: a fork of the skeleton thread, or a new thread, plus name and owner entries | no "yours now too": digests aren't owned |
| "save it as your own first" (`NotOwn`) | dropped: any digest can be run without a thread | |
| `Ready`, `resolve`, `ready` | the compiled skeleton, plus the lints on a provisional trial (`Bench.findings`) | warnings, never refusals (`docs/chatddx.md`, "Compromises") |
| trial: cell × case × seed (`bench.py:Trial`) | `Trial`: skeleton, engine, cases, cleanup, seeds (`Bench.trial`) | `run` is 1 case and 1 seed; `batch` is n cases and 1 seed |
| `Sending`, `Outcome` (`bench/sending.py`, `outcome.py`) | runner events, `Call.error` | |
| `outcome.py:unheeded` | nothing yet | `agents/wip-runner.md`, "Afterwards" |
| `cell_read`, `Drifted` | `Bench.rendered_again`: whether a run's first requests render the same now | |
| `secret`, `NoSecret` | an endpoint's `credential`, only a name | refused for now (`agents/wip-repl.md`, "Left out") |
| `Plan`, `crossed` (`bench/plan.py`), `held` (`bench/held.py`) | not ported: the portal's (`agents/wip-repl.md`, "Left out") | `Reads.reaching` and `Bench.scored_by` cover the repl's part of `held` |

### Forces
- **Authorization is a convenience, not a protection** (`docs/identity.md`, "Authorization"). What a person sees
  decides what is relevant to show them. Protection comes from clearance, enforced by the runner's gate
  (`src/chatddx/runner/gate.py`), and from the database's grants. So no option needs a facade for safety. A facade is
  about having one place for each rule, and one API that every edge shares.
- **Z1 isn't written.** Z1 maps roles to the kinds each role sees, and it needs the portal's views to mean anything
  (`docs/identity.md`, "Open"). It goes wherever the person-scoped reads go.
- **Edges to come.**
  - The portal, per request, and an API.
  - A worker, long-lived and serving many owners.
  - An export of scores, and `chatddx samples`.
  - The CLI's ops commands (`migrate`, `person`, `init-data`, `import-engine`). These don't act for one person: seeding
    writes as the archive (`src/chatddx/seed/write.py:_Seeder`).
- **One synchronous connection.** The store is synchronous and the bench holds one connection, so a portal would build
  a bench per request, as the old one did.
- **The store's principle**: "The store answers which rows exist; the modules decide what they mean" (`docs/store.md`,
  "What the store does").
- **Errors are the shell's.** The bench raises `LookupError` and `ValueError` worded for the shell ("for alice",
  "picked by the endpoint in the cell"). An API maps errors to status codes, as the old one did with `NotFound`,
  `Ambiguous` and the subclasses of `NotReady`.

## Phase 1: what the bench is
### B1. Helpers
The bench is a set of functions, or small stateless classes, that ease what edges do with the data model. They
compile a cell, lint it, rebuild a run's request and describe a run. Each takes what it needs (`conn`, `person`,
`inventory`) as arguments. Person-scoped reads stay in the store (`Reads`) or move to the catalog.

For:
- the smallest surface;
- no wrapper around what an edge can ask the store for itself;
- nothing to keep in step.

Against:
- It repeats the old project's outcome: nothing owns "what a person sees", so each edge puts it together itself and
  the rules get copied.
- The three rules held twice (see "Rules held twice") have no home.
- Every call takes the person.

What changes: `Bench` breaks up into modules (`cell.py`, `runs.py`, …), and the repl holds the connection and the
person itself.

### B2. Facade, named rig
Every interaction an edge has with the data model, reads and writes alike, goes through the facade. Edges import
`chatddx.rig` and the value types, and nothing from `chatddx.store`. A test over the import graph checks that, or
import-linter's layers contract.

For:
- one place for each rule, and for Z1;
- one API that every edge shares, typed errors included;
- edges can be tested against the facade alone;
- a seam for a later remote API, say between the portal and a worker.

Against:
- Its surface is everything every edge needs, and most of it passes calls through: `store.run`, `catalog.title`,
  `catalog.recipe`, `inventory.endpoints`. The old portal alone made 80 imports from the models.
- It tends to grow into the object everything depends on.
- The ops commands don't act for one person, so they need a facade that isn't person-scoped, or an exemption.
- The old project never got there.

The name. "Rig" is already taken three times:
- The glossary's Rig is the whole of chatddx: "the chatddx software that builds cages from factors, runs and scores
  inside them and records what happened" (`docs/chatddx.md`).
- `src/chatddx/core/rig.py:rig()` is the code running now, and `entry` finds a pinned entry point in it.
- `rig` is a field of every `RunStarted` and `ScoreStarted` (`src/chatddx/ledger/run.py`, `score.py`). It is in the
  canonical form of stored records, so it can't be renamed.

`chatddx.rig` works if `core/rig.py` is renamed, say to `core/code.py` with `running()` and `entry()`. The ledger
field keeps its name, read as "the rig's code". The name fits the glossary, since the facade would be the rig as the
edges see it. But "the rig" would then mean both the system and its front door, unless the glossary changes.

What changes:
- Each reach-through in the repl becomes a facade method: about 30 calls, and about 15 methods.
- `Reads` moves in.
- The repl's tests check writes through the facade, or keep `Store(conn)` for tests only.

### B3. A person-scoped view, with a boundary
The bench is what one person sees and does. Built for a person, it answers everything whose answer depends on who is
asking, and it writes on their behalf: `save`, `start` and `score`, with their owner entries.

The boundary for edges: what depends on the person goes through the bench. What doesn't may be read straight from the
store and the World, such as a component by digest, a title, a run's log by id, the inventory and the facts.

For:
- It is what the bench already is, and what the old one was.
- Each rule held twice gets one home.
- It settles the gap in `docs/store.md` by moving `Reads` into the bench.
- Its surface is small.
- It matches "authorization is a convenience": it decides what is relevant to show, and Z1 joins it.

Against:
- The boundary is a convention, harder to check than B2's, since reaching through for person-agnostic reads stays
  allowed.
- The person-agnostic helpers (`described`, `rendered_again`, `title`) need a home: in the bench as conveniences, or
  in the modules they read.

What changes:
- `Reads` moves into `chatddx.bench`, with its tests from `src/chatddx/store/test/test_reads.py`.
- `unscored` and `outstanding` become one.
- `Bench.expectation` follows `expectation_for`'s rule, or says why it differs.
- The repl calls `bench.runs()` rather than `bench.reads.runs()`.
- The shell's vocabulary moves to the repl (S3).

### B4. A workbench, with a separate view
The bench is the person's work in progress: the `Cell` and what builds it (compile, lint, reach, save, start), as the
old `Bench`, `cell.py` and `plan.py` were together. Person-scoped reads go to a separate view, `Reads` wherever it
lives, which the workbench uses.

For:
- The bench is named after what it does: a bench is where things are built up.
- A portal's variation editor and the repl would share it.
- Reads and composition stay apart.

Against:
- There are two person-scoped objects where one would do, and edges hold both.

### Sub-decisions
- **S1. Where `Reads` lives**: the store, as now; the bench (B3); or the catalog, next to the rules it applies.
- **S2. Where `Cell` lives**: the bench, or the repl. The cell isn't the shell's alone: a variation being tried in the
  portal is a cell too (`docs/chatddx.md`, "Intended evolution of configurations").
- **S3. The shell's vocabulary** (`KINDS`, `NONE`, `SEEDS` and `drawn_seed`, and how messages are worded) moves to the
  repl. `PARTS` and `OPTIONAL` are the recipe's, and could come from `src/chatddx/factors/request.py:Recipe`.
- **S4. Errors**: typed exceptions, such as `NotFound` and `Ambiguous`, that subclass `LookupError`, so the repl keeps
  catching what it catches and an API can map them.
- **S5. State**: the caches of logins and models make a bench last one session. That suits a request or a repl. A
  long-lived worker would rebuild it, where the old worker cached one per owner.
- **S6. Tests of its own**, in `src/chatddx/bench/test/`, on the seeded sample. The seeded fixture would then be held
  three times: in `src/chatddx/store/test/test_reads.py`, `src/chatddx/repl/test/conftest.py` and here. So it moves to
  `src/chatddx/conftest.py` (`agents/wip-repl.md`, "Left from 4a").
- **S7. The name**: `bench`, `rig` (B2, see "The name"), or another.

### Take
B3, for these reasons:
- It is what the bench already is, and what the old one was, so the code changes are small and local.
- The old project's problem was rules copied, not edges going around a facade. B3 gives each rule a home without
  making edges route person-agnostic reads through methods that only pass them on.
- Authorization is a convenience, so what a facade enforces buys no protection.
- B2 can still come later, since a B3 bench is the person-scoped half of a facade. If the portal shows that the
  boundary doesn't hold, add the person-agnostic half and the import check then, and name it rig then.

On the sub-decisions:
- S1 and S2: the bench.
- S3: the repl.
- S4: yes.
- S5: per session.
- S6: yes.
- S7: keep `bench`, since "rig" is taken until B2.

Once decided, phase 2 builds it in this order: `Reads` and its tests, one `unscored`, one expectation rule, the
vocabulary, typed errors, then the bench's own tests.

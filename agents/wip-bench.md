# The bench: work in progress

The bench is what one person sees and does: the threads, families and runs they see, the World's endpoints, the
variation they are trying, and what is written on their behalf. It sits over the store, the catalog, the runner and the
scoring pass. It was built for the repl (`agents/wip-repl.md`, phase 3 and "Built: 4a"), and moved out of it so that
what it is could be decided apart from the shell.

"The old bench" is chatddx-administration/chatddx at 504792c: `src/chatddx/bench/`. Old permalink base:
https://github.com/chatddx-administration/chatddx/blob/504792cbeb09508f2c52912be29a3d8809d2fa1d/

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **Decided: B3**, a person-scoped view, split between `identity` and the bench (see "Decided").
2. **Phase 2 has started** (see "Phase 2"). Steps 1–5 are done: the visibility predicate in `identity`, `Reads` in the
   bench, one rule for what is left to score, one rule for the expectation a case is held to, and the bench's own
   tests.
3. **The reconciliation of "cell"** waits on the user's word on the names (see "'Cell', translated"). Steps 7 and 8
   come after it, since they touch the same code.

## Decided
- **B3**: the bench is a person-scoped view (see "Phase 1" for the options). The split:
  - `identity/` holds the pure rules: the map from role to kinds (Z1, `docs/identity.md`, "Authorization") and the
    predicate for "may this person see this". They are data and functions with no store access, so `identity` stays a
    leaf.
  - `bench/` is the view that applies those rules to what is in the store and the World. It also holds the variation
    being tried at an endpoint (see "'Cell', translated") and the writes made for the person.
- **The two rules for the expectation a case is held to** were to be made one if that could be done cleanly, and
  otherwise looked at more deeply. It was clean (phase 2, step 4).
- **"Cell" isn't a term of remastered**, and isn't to be used in code or docs. Its translation comes first, then a
  reconciliation, scheduled below.

## "Cell", translated
"Cell" is the old chatddx's term: `bench/cell.py:Cell(configuration, name, variations, stack)`, a configuration with
slices swapped in, on a stack. It leaked into remastered with the repl's port.

In remastered's terms, it is **a variation being tried, at an endpoint**:
- **A variation being tried** (`docs/chatddx.md`, "Intended evolution of configurations"; `docs/catalog.md`,
  "Configurations and variations"). It is a configuration's recipe with recipe parts replaced; with none replaced, it
  is the configuration's head itself. Compiled, it is a skeleton nobody has saved, "just a digest". Saved, it becomes an
  edit of the person's thread, or a fork (`Bench.save`).
- **An endpoint** (`docs/inventory.md`, "Endpoints"): where an engine is served. The engine is a factor, and the
  endpoint is the World's.
- Together they give the skeleton and the engine that a trial pairs (`docs/facts.md`, "Checking pairs"). `run` and
  `batch` add the cases and the seed, and that makes the trial.

Field by field:

| `Cell` (`src/chatddx/bench/bench.py`) | In remastered's terms |
|---|---|
| `configuration: Edit` | the head of the configuration, a skeleton thread, that the variation is based on |
| `name` | the configuration's name, as the person addressed it |
| `recipe` | the configuration's recipe (`Catalog.recipe`) |
| `parts` | the recipe parts replaced, each with the name of the chunk thread it was taken from: what the variation varies (`docs/catalog.md`, "Forks") |
| `varied` | the variation's recipe |
| `label` | a short title for the variation, `NAME+PART=CHUNK`, where the catalog would give the long one of a variation nobody saved (`docs/catalog.md`, "Smaller issues") |
| `endpoint`, `engine` | the endpoint, and the engine it serves |

There is one tension. `docs/chatddx.md` calls variations "a supported portal workflow, not an object in the code".
`Cell` holds the variation being tried as a value (its base, its recipe, and the parts with the names they were set
by), because the repl shows the names and `save` forks from the base. A value in the bench isn't a catalog object, but
the reconciliation should keep it a plain value.

### The reconciliation
Scheduled; it waits on the user's word on the names. It renames:
- **Code**, about 280 uses in `src/` and none in `docs/`:
  - `Cell` and its members (`using`, `on`, `set`, `held`, `varied`, `label`);
  - `Repl.cell`, the repl's `cell CONFIGURATION ENDPOINT` command and its help, and the prompt;
  - messages such as "the cell has no endpoint" and "a case isn't in the cell";
  - the bench's `cell` parameters;
  - test names such as `test_the_prompt_shows_the_cell`.
- **Agents' files**: `agents/wip-repl.md` (28 uses). `agents/wip-repl-manual.md` is the old manual copied unchanged,
  and stays that way, since it is what the cross-check reads. The new manual (`docs/repl.md`, proposed) won't use the
  word.

The options for names:
- **R1. Two values, as the translation has it.** The variation being tried is one value, and the endpoint is held
  beside it (`Repl.endpoint`). The bench's methods take what they need, and the engine comes from the endpoint
  (`Bench.endpoint`). The repl's `cell X Y` goes, since `use X` and `on Y` do the same, or it becomes `use X on Y`. The
  value can't be called `Variation`: that is the catalog's (`src/chatddx/catalog/model.py:Variation`, what a saved
  fork varies from its base). It could be `TriedVariation`, held in variables named `variation`.
- **R2. One value, `Pair`**, after the skeleton and engine that a trial pairs (`docs/facts.md`, "Checking pairs"),
  with the variation it came from and the endpoint. The repl's command becomes `pair X Y`. The term exists already,
  but a pair with one side missing reads oddly, and the repl holds one most of the time.
- Names ruled out: `Variation`, which is taken, and `Draft`, since "draft" names JSON Schema drafts in
  `src/chatddx/factors/lint.py`.

Take: R1 with `TriedVariation`. It follows the translation, adds no combined concept the docs don't have, and leaves
`use` and `on` as the repl's ways to choose.

## Phase 0: out of the repl
Done (fdee878).
- `src/chatddx/repl/bench.py` moved to `src/chatddx/bench/bench.py` unchanged. `src/chatddx/bench/__init__.py` exports
  its public names, as `chatddx.store` does.
- The repl, its tests and `src/chatddx/cli.py` import from `chatddx.bench`. The bench imported nothing from the shell,
  so nothing else changed, and the same 433 tests passed.

## What the bench was at phase 0
`Bench(conn, person, inventory, facts)` (`src/chatddx/bench/bench.py`), with the values `Cell`, `Family`, `Reach`,
`Graded` and `Saved`.

The plan (`agents/wip-repl.md`, phase 3) called it "a person-scoped layer, the old `Bench`'s role. It holds the
[variation being tried], names, completions and lookups, and nothing in it is UI." Completions ended up in the shell
instead (`src/chatddx/repl/shell.py:Repl`). Each step of the shell added to it:
- 4a: the person's lookups (threads by name, families and their cases, the expectation they read);
- 4a: the skeleton of the variation being tried: the stored head, or `compile_request` on the recipe with the parts
  replaced;
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
| The variation being tried, at an endpoint | `Cell`; `configuration`, `chunk`, `skeleton`, `findings`, `reach` | for finding names, and `reach` for expectations |
| Writes for the person | `save` (a thread or a new edit, and a compilation), `start` (through `Runner`), `score` (through `score_run`) | yes: they write owner entries |
| Shell vocabulary | `KINDS` ("what the shell calls each kind of thread"), `NONE`, `SEEDS` and `drawn_seed` ("so the prompt stays readable"), and the wording of messages | no |

`scores_of` and `owner` sit on the edge between the first two parts. `scores_of` names each scorer by the thread the
person sees, and `owner` gives "" for the person's own.

## The landscape, at phase 1
How things stood when B3 was chosen. Phase 2 changes it (see "Phase 2").

### Layers
```
edges     repl, cli                     to come: portal, API, worker, export, `chatddx samples`
            │   ╲ reaches through bench.store, bench.catalog, bench.reads, bench.inventory, bench.facts
bench     Bench
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
- **The catalog's rules** take a person id: `src/chatddx/catalog/model.py:About.shows` (live, and owned or shared) and
  `src/chatddx/catalog/threads.py:expectation_for`. `Catalog.visible`, `visible_families`, `expectation_for` and
  `involving` pass it through (`src/chatddx/store/catalog.py`).
- **`Reads(conn, person)`**, the store's person-scoped lookup, offered in "Looking things up for someone"
  (`docs/store.md`). The same doc doubted it under "Known gaps": "Person-scoped lookup may not belong in the store.
  `Reads` is mostly policy based on other modules' rules, which contradicts 'the store answers which rows exist; the
  modules decide what they mean'." The bench was its only caller outside its tests.
- **The runner** takes the person who will own the run or score: `src/chatddx/runner/run.py:Runner(conn, inventory,
  by)` and `src/chatddx/runner/score.py:score_run(…, person)`.
- **`Bench(conn, person, inventory, facts)`**.

### How the repl uses the bench
The repl calls the bench's methods: `title` 12 times, `skeleton` 8, `get`, `endpoint` and `model` 5 each, and most of
the rest once or twice. It also goes around them through the bench's attributes, about 30 times:
- the person-scoped reads: `bench.reads.runs` (4), `bench.reads.scorers` and `bench.reads.reaching`;
- the store: `bench.store.run` (3), `bench.store.finished`, `bench.catalog.title` (2) and `bench.catalog.recipe`;
- the World and the facts: `bench.inventory.*` (7) and `bench.facts.models` (2);
- the person: `bench.person.login` and `bench.person.id` (6).

It also calls into the data model with `bench.get` 6 times, through `resolve` and `url_of`. The repl's tests open
`Store(bench.conn)` and `Catalog(bench.conn)` to check what was written.

So the bench was a person-scoped view with helpers attached. It wasn't a facade: nothing stopped an edge from going
around it, and the repl did so through the bench itself.

### Rules held twice
All three are resolved in phase 2, or have a step scheduled.
- **The expectation a person reads for a case.** `Bench.expectation` took the head of the person's first own thread,
  else of the first shared one, in any schema. `src/chatddx/catalog/threads.py:expectation_for` keeps only heads in
  the scorer's expectation schema, and refuses when there are several to choose from. `show case` read the first rule,
  and `score` the second. Made one in step 4.
- **What is left to score.** `Bench.unscored` worked it out per run and `Reads.outstanding` per scorer, and only the
  bench's answer was used (`docs/store.md`, "Known gaps"). The bench works per run because `score RUN` needs one run's
  answer, and because a run whose case has several expectations to choose from is then skipped for that scorer, rather
  than stopping the listing. Made one in step 3.
- **Finding things by name.**
  - `Reads.thread` finds a thread by its whole name, then as `OWNER/NAME`. On top of that, `Bench.thread` adds
    per-model names and the shell's kinds.
  - `Bench.family` finds a family on its own, own first, without `OWNER/NAME`.

  Still open; see "Phase 2", "Open".

### The old bench
- **Bound to a person**, by login: `Bench(identity_name, transport=None, own=())` (`src/chatddx/bench/bench.py`,
  `Bench`). It held no connection (Django held it) and no work in progress, and kept caches of names and models.
- **One per caller.** The API built one per request (`src/chatddx/django/api/runs.py`, `registry.py`), and so did the
  portal, narrowed with `own` (`src/chatddx/django/portal/owners.py:bench_of`). The worker cached one per owner
  (`src/chatddx/worker/worker.py`). The repl had one per process and subclassed it (`src/chatddx/repl/shell.py`,
  `Repl(Bench)`).
- **What came with it:**
  - `cell.py`: the immutable value of what is being tried (see "'Cell', translated");
  - `plan.py`: crossing what is being tried with variations into a batch, `Plan.of(bench, …)`;
  - `sending.py`: `Sending(bench, trial, …)`, a run's events, then `bench.recorded`;
  - `outcome.py`: pure functions;
  - `held.py`: the runs, jobs and scores that hold a configuration. It imported the worker's model.
- **What it enforced.**
  - `ready` refused a configuration that was neither the person's nor the archive's: `NotOwn`, "save it as your own
    first", 403 in the API.
  - It refused a missing secret (`NoSecret`), and work in progress whose stack or configuration had changed since it
    was planned (`Drifted`, in `cell_read`).
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

  The fix moved the rules down into the store, not up into a facade. Remastered's `Reads` descends from that fix.

How the old bench maps onto remastered:

| old (504792c) | remastered | notes |
|---|---|---|
| `Cell`, `set` a slice (`bench/cell.py:Cell.set`) | `Cell.set` (to be renamed): replace a recipe part, then `compile_request` to an unsaved skeleton | shown by `Catalog.title_of` |
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
  (`src/chatddx/runner/gate.py`), and from the database's grants. So no option needs a facade for safety.
- **Z1 isn't written.** Z1 maps roles to the kinds each role sees, and it needs the portal's views to mean anything
  (`docs/identity.md`, "Open").
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
Decided: B3. The options were:
- **B1. Helpers.** Stateless functions; person-scoped reads stay in the store. It is the smallest, but nothing owns
  "what a person sees", so rules get copied again, as they were in the old project.
- **B2. A facade, named rig.** Every edge goes through it, checked by an import test. It gives one place for each rule
  and one API for every edge, but its surface is everything every edge needs, most of it passing calls through, and the
  ops commands need an exemption. "Rig" is already the glossary's name for the whole of chatddx
  (`docs/chatddx.md`), `src/chatddx/core/rig.py:rig()`, and a field of every `RunStarted` and `ScoreStarted` that
  can't be renamed.
- **B3. A person-scoped view, with a boundary.** What depends on who is asking goes through the bench, and what doesn't
  may be read straight from the store and the World. Chosen.
- **B4. A workbench, with a separate view.** The bench is the work in progress, and person-scoped reads are a second
  object. Two person-scoped objects where one would do.

B2 can still come later, since a B3 bench is the person-scoped half of a facade.

Sub-decisions:
- **S1. Where `Reads` lives**: the bench. Done in step 2.
- **S2. Where the variation being tried lives**: the bench (decided).
- **S3. The shell's vocabulary** (`KINDS`, `NONE`, `SEEDS` and `drawn_seed`, and how messages are worded) moves to
  the repl. `PARTS` and `OPTIONAL` are the recipe's, and could come from `src/chatddx/factors/request.py:Recipe`.
  Take; step 7.
- **S4. Typed errors**, such as `NotFound` and `Ambiguous`, that subclass `LookupError`, so the repl keeps catching
  what it catches and an API can map them. Take; step 8.
- **S5. State**: the caches of logins and models make a bench last one session. That suits a request or a repl. A
  long-lived worker would rebuild it. Take; nothing to build.
- **S6. Tests of its own.** Done in step 5.
- **S7. The name**: `bench`, since B3 isn't the facade "rig" was proposed for.

## Phase 2: B3
### Done
1. **The visibility predicate is `identity`'s**: `src/chatddx/identity/identity.py:sees(person, owner,
   collaborators)`, the owner or a collaborator. `src/chatddx/catalog/model.py:About.shows` adds that what is shown
   is live, and calls it. So the catalog now imports `chatddx.identity` as well as `chatddx.factors`, which
   `docs/catalog-api.md` rules out; an amendment is proposed there. Tested in
   `src/chatddx/identity/test/test_identity.py`, and through the catalog's visibility tests.
2. **`Reads` is the bench's**: `src/chatddx/store/reads.py` moved to `src/chatddx/bench/reads.py`, and its tests to
   `src/chatddx/bench/test/test_reads.py`. `chatddx.store` no longer exports it, and `chatddx.bench` does. Amendments
   are proposed in `docs/store.md` and `docs/store-api.md`.
3. **One rule for what is left to score**: `Reads.outstanding` is gone, unused since 4c. `Bench.unscored` (per run) and
   `Bench.outstanding` (the person's finished runs, with what each is left to be scored by) are the one answer. The
   test that pinned "a changed expectation leaves a run to score again" now pins it on `Bench.unscored`
   (`src/chatddx/bench/test/test_bench.py`).
4. **One rule for the expectation a case is held to**: `Catalog.expectation_for`, the one scoring uses.
   - `Bench.expectation(case, schema)` is the expectation it picks for the person under that schema. It raises a
     `LookupError` when there are several to choose from.
   - `Bench.expectation_schemas(case)` gives the schemas of the expectations the person sees for a case.
   - `show case` shows the expectation under each of those schemas, labelled by the schema's title when there is more
     than one, or why there is none to show: "has expectations to choose from". With the sample's one schema, it
     shows what it showed before.
   - `Bench.reach` reads expectations through `Bench.expectation` too.

   Tests: `src/chatddx/bench/test/test_bench.py`, and
   `src/chatddx/repl/test/test_inspecting.py:test_show_case_says_when_scoring_has_expectations_to_choose_from`.
5. **The bench's own tests**, in `src/chatddx/bench/test/`, on the seeded sample. The seeded fixture is defined once,
   session-scoped, as `src/chatddx/conftest.py:seeded` (with `WORLD`, the sample World's inventory). The bench's tests
   and the repl's copy it for each test. That settles "the seeded sample fixture is defined twice"
   (`agents/wip-repl.md`, "Left from 4a").

### Next
6. **The reconciliation of "cell"** (see "The reconciliation"), once the user has chosen names.
7. **The shell's vocabulary to the repl** (S3). This comes after step 6, since `Cell.set`'s refusal names `none`.
8. **Typed errors** (S4).
9. **Z1**: the map from role to kinds goes in `identity`, once the portal's views give it meaning. `sees` then takes
   the person's roles and the kind.

### Open
- **`Reads` and `Bench`, one class or two.** `Bench` wraps most of `Reads`, and the repl reaches `bench.reads`
  directly. Both are the bench's now, so this only decides the bench's own shape. Take: fold `Reads` into `Bench`
  after step 6, so that the reach-through `bench.reads.*` becomes `bench.*`.
- **Where the rule is applied to the catalog's rows.** `catalog/threads.py:visible`, `catalog/families.py:visible`
  and `catalog/threads.py:expectation_for` apply the visibility rule to the catalog's rows, inside the catalog.
  `docs/catalog.md` lists "what a person sees" and "the expectation a person scores a case against" as the catalog's,
  and the bench calls them. Take: leave them there. The rule itself is `identity`'s, the catalog applies it to its own
  rows, and the bench applies it to everything else.
- **Finding things by name** is still split between `Reads.thread` and `Bench.family` (see "Rules held twice").
  `OWNER/NAME` for families would make them one. Take: do it with the fold.

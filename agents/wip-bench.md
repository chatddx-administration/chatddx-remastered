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
2. **Phase 2** (see "Phase 2"): steps 1–11 are done. Step 12, Z1, waits for the portal.
3. **Decided: K2 with R1** (see "Keeping 'cell' or not"). "Cell" is the repl's word only, and the bench speaks of a
   `TriedVariation` and an endpoint. A test keeps the word out of the code outside `src/chatddx/repl/`.
4. **The bench's modules** are `errors.py`, `outcome.py`, `variation.py` and `view.py` (see "Modules"). There is no
   `bench/bench.py`.
5. **The API's phase 0** added to the bench: lookups by id, a variation from an id and digests, `fork` and `edit`,
   `Ambiguous` for several expectations, and `outcome.py` (`agents/wip-api.md`, "Phase 0: built").
6. **Next: writes for authoring.** The bench writes configurations (`save`, `fork`, `edit`), runs (`start`) and
   scores (`score`), and nothing else. The portal is where chunks, appendices and expectations are written
   (`docs/chatddx.md`, "Requirements"; `agents/wip-portal.md`), for the person, so the writes are the bench's (B3).
   Curation writes them only as the archive, from a data set's files (`src/chatddx/curation/write.py`). Not planned
   yet; what the docs already ask of them:
   - **Chunks** of every part (`PARTS`, `src/chatddx/bench/variation.py`): a new thread, or an edit of one the person
     owns, as `fork` and `edit` are for configurations. A new version is offered the previous version's language
     (`docs/catalog.md`, "Languages").
   - **Appendices**, bound to one vignette and stored as written, with CRLF normalized before they are digested
     (`docs/factors.md`, "Appendix"); and the cases that order them in a family.
   - **Expectations**, one case's reference answer, held to an expectation schema (`docs/factors.md`, "Expectation"),
     and read back through `Bench.expectation`.
   - Beside them: a scorer's labels carried to its next edit (`docs/catalog.md`, "Scorer labels"), and deleting
     (`docs/catalog.md`, "Deleting").

## Decided
- **B3**: the bench is a person-scoped view (see "Phase 1" for the options). The split:
  - `identity/` holds the pure rules: the map from role to kinds (Z1, `agents/wip-identity.md`, "Authorization")
    and the predicate for "may this person see this". They are data and functions with no store access, so `identity`
    stays a leaf.
  - `bench/` is the view that applies those rules to what is in the store and the World. It also holds the variation
    being tried at an endpoint (see "'Cell', translated") and the writes made for the person.
- **The two rules for the expectation a case is held to** were to be made one if that could be done cleanly, and
  otherwise looked at more deeply. It was clean (phase 2, step 4).
- **"Cell" isn't a term of remastered**, and isn't to be used in code or docs. Its translation comes first, then a
  reconciliation. The user later reopened this: whether "cell" is worth keeping between the bench and the edges, as
  long as it stays out of the data model. Decided: K2 with R1 (see "Keeping 'cell' or not"), built in phase 2, step 6.

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

Field by field, for the bench's former `Cell`. It is now the bench's `TriedVariation`, and the repl's own `Cell`
holds one beside the endpoint and its engine (phase 2, step 6):

| The former `Cell` | In remastered's terms |
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
by), because the repl shows the names and `save` forks from the base. A value in the bench isn't a catalog object.
`TriedVariation` stays a plain value.

## Keeping "cell" or not
Decided: K2 with R1 (see "Options"). Built in phase 2, step 6.

### Where it was
- **The repl**: the `cell CONFIGURATION ENDPOINT` command, `Repl.cell`, about ten help texts ("put a configuration in
  the cell", "run a case on the cell", "save the cell's configuration as your own"), and messages such as "the cell
  has no endpoint" and "a case isn't in the cell". The prompt shows what the cell holds, but not the word:
  `alice plan+reasoning=off×qwen3-8b-awq@fake #7>`.
- **The bench**: the value `Cell`, and the `cell` parameters of `configuration`, `chunk`, `skeleton`, `findings`,
  `reach`, `save` and `start`.
- **Nowhere below the bench.** The factors, the ledger, the catalog, the store, the runner and the scorers never name
  it, and nothing stored is one. `save` stores a skeleton thread's edit and a compilation, `start` a `Trial`, and
  scoring a `Scoring`. The cell's label isn't stored either.
- **Nowhere in `docs/`.** In `agents/`: `agents/wip-repl.md` (28 uses), and `agents/wip-repl-manual.md`, the old
  manual, which stays as it is.
- In all, about 280 uses in `src/`: about 130 in the repl's code, 45 in the bench, and 105 in the repl's tests.

### What it holds, and the words the docs have for it
A cell is a configuration, or a variation of it being tried, together with an endpoint. Either side can be missing.
The docs name each side, but not the two together:
- **Configuration** and **variation** (`docs/catalog.md`, "Configurations and variations") name the skeleton's side
  only.
- **Endpoint** and **engine** name the other side.
- **Pair** (`docs/facts.md`, "Checking pairs") is a trial's skeleton and engine, and is used for checking them.
- **Trial** adds the cases, the cleanup and the seeds.

### Is it a good word?
For it:
- It is one short word for what the repl shows and acts on all the time.
- No remastered term names the two sides together.
- Repl users know it.
- It can't be mistaken for any term in the code, since none is like it.

Against it:
- It doesn't say what it holds: the user doesn't see the connection, and a newcomer won't either.
- The docs, and so a portal built from them, speak of configurations, variations, endpoints and trials. "Cell" would
  be a fourth word for a combination of two of those.
- The word's everyday meanings sit right next to it. The repl prints tables, whose cells its tests read
  (`src/chatddx/repl/test/test_inspecting.py:row_names`). Scores are to be exported and analysed in Python
  (`docs/chatddx.md`, "On the table"), where a cell is a spreadsheet's or a notebook's.
- A cell can hold only an endpoint, or only a configuration, which the word doesn't suggest.
- It is a clinical word too: the sample's cases speak of "basal cell carcinoma" and "hepatocellular carcinoma"
  (`src/chatddx/data/sample/cases.toml`), which the guard's test met at once.

### How it would spread
Today it is held between the bench and one edge. It would spread through:
- **The bench's API.** Every edge to come (the portal, an API) builds on the bench, and would take `Cell` with it,
  into forms, routes and resources.
- **A stored title.** `docs/catalog.md` ("Smaller issues") proposes "an entry on the run" so that an unsaved
  variation's runs get a shorter title. Stored from the cell's label, it would carry the repl's notation into the
  catalog.
- **An export** whose unit is "the runs of a cell".
- **Docs** for the bench or the repl that use it.

### Options
- **K1. Keep it between the bench and the edges, as now.** `Cell` stays the bench's value and the repl's word. Define it
  in the bench's doc and in the repl's manual as "a configuration, or a variation of it being tried, and the endpoint
  it runs on". Guard the data model (see "The guard"). This costs nothing now, but every edge to come learns the word
  from the bench.
- **K2. Keep it in the repl only.** The repl's command, help, messages, manual and its own state (`Repl.cell`) say
  "cell". The bench speaks the docs' terms: the variation being tried as one value, and the endpoint beside it (R1
  below). The repl translates, so repl users keep their habit, and the portal and an API start from the docs' terms. It
  costs renaming the bench's 45 uses and the repl's calls into it.
- **K3. Drop it everywhere.** That was the earlier decision. The repl's `cell X Y` becomes `use X on Y`, perhaps with
  `cell` kept as a hidden alias for a while. It costs about 280 renames, and repl users relearn.

Names for the bench's value, under K2 and K3:
- **R1. Two values.** The variation being tried is one value, and the endpoint is held beside it. The bench's methods
  take what they need, and the engine comes from the endpoint (`Bench.endpoint`). The value can't be called
  `Variation`, which is the catalog's (`src/chatddx/catalog/model.py:Variation`, what a saved fork varies from its
  base). It could be `TriedVariation`, held in variables named `variation`.
- **R2. One value, `Pair`**, after the skeleton and engine that a trial pairs, with the variation it came from and the
  endpoint. The term exists already, but a pair with one side missing reads oddly.
- Ruled out: `Variation`, which is taken, and `Draft`, since "draft" names JSON Schema drafts in
  `src/chatddx/factors/lint.py`.

### The guard
Whichever option is chosen, the word stays out of the data model:
- Nothing below the bench names it. A test can check this by grepping the packages under the bench for the word, under
  K1, or every package but `chatddx.repl`, under K2. Built for K2:
  `src/chatddx/repl/test/test_vocabulary.py`, over code only (`.py` and `.sql`), since clinical data says "cell".
- Nothing stored is one: a run's title, if one is ever stored, is a title (`docs/catalog.md`, "Titles"), not a label
  in the repl's notation.
- Docs below the edges don't use it.

### Take
K2 with R1. The word's value is the repl's: a habit, a terse command, help that reads short. Its cost is spreading
through the bench to edges that don't exist yet, whose users would learn it from scratch. K2 keeps the value and stops
the spread at the cheapest point, since the bench is shared by every edge. The guard is then simple: "cell" appears
nowhere outside `src/chatddx/repl/`.

## Modules
`src/chatddx/bench/`, since phase 2, step 11:

| Module | Holds | Builds on |
|---|---|---|
| `errors.py` | `NotFound`, `Ambiguous` | nothing |
| `outcome.py` | `outcome`, `usage`: how a run's item ended, and the tokens it used, a pure function each | `chatddx.factors.request`, `chatddx.ledger`, `chatddx.runner.send`, `chatddx.scorers.answer` |
| `variation.py` | `PARTS`, `OPTIONAL`, `TriedVariation`: the variation being tried, a plain value | `chatddx.catalog`, `chatddx.factors.request` |
| `view.py` | `Bench`, the person's view: what they see, the variations they try, and what is written for them; `KINDS`, and what `Bench` returns: `Family`, `Reach`, `Graded`, `Saved` | `errors.py`, `variation.py`, the store, the catalog, the factors, the facts, the inventory, the ledger and the runner |

`__init__.py` re-exports them, so edges import from `chatddx.bench` and never by path.

Why this layout:
- **No `bench/bench.py`.** It repeated the package's name and said nothing about what it held. Most packages here
  name modules by what they hold (`catalog/threads.py`, `runner/send.py`, `ledger/run.py`). `identity/identity.py`,
  `inventory/inventory.py` and `store/store.py` repeat their package's name as `bench/bench.py` did; that is
  happenstance, not a convention.
- **`variation.py` is pure.** `TriedVariation` touches neither the store nor a person. It is tested without a
  database (`src/chatddx/bench/test/test_variation.py`), and an edge can hold one without a bench.
- **`Bench` stays one class in one module.** Its lookups, the variations it tries, and runs and scores call each
  other through `self`: `configuration` and `chunk` use `thread`; `findings`, `reach`, `save` and `start` use
  `skeleton`; `score` and `unscored` use `scorers_for` and `scoring`; `reach`, `score` and `scores_of` use `labels`.
  Splitting the class by concern would take mixins, which hide where a method lives, or functions taking a bench,
  which give edges a second surface beside `bench.*`. At 615 lines, `view.py` is about the size of
  `fake_vllm/chat.py` (609), and shorter than `factors/request.py` (961).
- **"View"** because B3 made the bench a person-scoped view. It also writes for the person (`save`, `start`,
  `score`), but only through what the view finds.

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
All three are resolved in phase 2.
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

  Made one in step 11.

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
| `Plan`, `crossed` (`bench/plan.py`), `held` (`bench/held.py`) | not ported: `Plan` and `crossed` are the batch planner's (`agents/wip-batch.md`), `held` the portal's (`agents/wip-portal.md`) | `Bench.reaching` and `Bench.scored_by` cover the repl's part of `held` |

### Forces
- **Authorization is a convenience, not a protection** (`agents/wip-identity.md`, "Authorization"). What a person sees
  decides what is relevant to show them. Protection comes from clearance, enforced by the runner's gate
  (`src/chatddx/runner/gate.py`), and from the database's grants. So no option needs a facade for safety.
- **Z1 isn't written.** Z1 maps roles to the kinds each role sees, and it needs the portal's views to mean anything
  (`agents/wip-identity.md`, "Open").
- **Edges to come.**
  - The portal, per request, and an API.
  - A worker, long-lived and serving many owners.
  - An export of scores, and `chatddx samples`.
  - The CLI's ops commands (`migrate`, `person`, `init-data`, `import-engine`). These don't act for one person: seeding
    writes as the archive (`src/chatddx/curation/write.py:_Init`).
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
  Done in step 7, except `KINDS`, which turned out not to be the shell's.
- **S4. Typed errors**, such as `NotFound` and `Ambiguous`, that subclass `LookupError`, so the repl keeps catching
  what it catches and an API can map them. Done in step 8.
- **S5. State**: the caches of logins and models make a bench last one session. That suits a request or a repl. A
  long-lived worker would rebuild it. Take; nothing to build.
- **S6. Tests of its own.** Done in step 5.
- **S7. The name**: `bench`, since B3 isn't the facade "rig" was proposed for.

## Phase 2: B3
### Done
1. **The visibility predicate is `identity`'s**: `src/chatddx/identity/identity.py:sees(person, owner,
   collaborators)`, the owner or a collaborator. `src/chatddx/catalog/model.py:About.shows` adds that what is shown
   is live, and calls it. So the catalog now imports `chatddx.identity` as well as `chatddx.factors`, which
   `docs/catalog-api.md` now says (a3431e1); `model.py`'s row in its table is proposed. Tested in
   `src/chatddx/identity/test/test_identity.py`, and through the catalog's visibility tests.
2. **`Reads` is the bench's**: `src/chatddx/store/reads.py` moved to `src/chatddx/bench/reads.py`, and its tests to
   `src/chatddx/bench/test/test_reads.py`. `chatddx.store` no longer exports it. It was then folded into `Bench`
   (step 9).
   `docs/store.md` and `docs/store-api.md` dropped it (a3431e1); what they said is kept in "Material for the bench's
   docs".
3. **One rule for what is left to score**: `Reads.outstanding` is gone, unused since 4c. `Bench.unscored` (per run) and
   `Bench.outstanding` (the person's finished runs, with what each is left to be scored by) are the one answer. The
   test that pinned "a changed expectation leaves a run to score again" now pins it on `Bench.unscored`
   (`src/chatddx/bench/test/test_view.py`).
4. **One rule for the expectation a case is held to**: `Catalog.expectation_for`, the one scoring uses.
   - `Bench.expectation(case, schema)` is the expectation it picks for the person under that schema. It raises a
     `LookupError` when there are several to choose from.
   - `Bench.expectation_schemas(case)` gives the schemas of the expectations the person sees for a case.
   - `show case` shows the expectation under each of those schemas, labelled by the schema's title when there is more
     than one, or why there is none to show: "has expectations to choose from". With the sample's one schema, it
     shows what it showed before.
   - `Bench.reach` reads expectations through `Bench.expectation` too.

   Tests: `src/chatddx/bench/test/test_view.py`, and
   `src/chatddx/repl/test/test_inspecting.py:test_show_case_says_when_scoring_has_expectations_to_choose_from`.
5. **The bench's own tests**, in `src/chatddx/bench/test/`, on the seeded sample. The seeded fixture is defined once,
   session-scoped, as `src/chatddx/conftest.py:seeded` (with `WORLD`, the sample World's inventory). The bench's tests
   and the repl's copy it for each test. That settles "the seeded sample fixture is defined twice"
   (`agents/wip-repl.md`, "Left from 4a").

6. **"Cell" is the repl's** (K2 with R1).
   - The bench's `Cell` is now `src/chatddx/bench/variation.py:TriedVariation`: the configuration's head edit, the name
     it was called by, its recipe, and the parts replaced over it. It always has a configuration. It has no endpoint,
     and lost `using` and `on`.
   - The bench's methods take what they need: `configuration(name, engine)`, `chunk(part, name, engine)`,
     `skeleton(variation)`, `findings(variation, engine, seed, cases)`, `reach(variation, families)`,
     `save(variation, name)`, which returns `Saved.variation`, and `start(variation, endpoint, cases, seed)`, which
     finds the engine from the endpoint.
   - The repl's own `Cell` (`src/chatddx/repl/shell.py`) holds a `TriedVariation`, the endpoint and its engine, with
     `trying` and `on`. The repl's commands, help, messages and tests keep the word.
   - `src/chatddx/cli.py`'s help for `chatddx repl` no longer says it.
   - The guard: `src/chatddx/repl/test/test_vocabulary.py`.
   - Tests: `src/chatddx/bench/test/test_view.py` covers the per-model pick and compiling a variation;
     `src/chatddx/bench/test/test_variation.py` covers replacing parts, taking one back, and the refusals.
7. **The shell's vocabulary is the repl's**: `NONE`, `SEEDS`, `MAX_SEED` and `drawn_seed` moved to
   `src/chatddx/repl/shell.py`. `set PART none` is the repl's: it hands the bench no digest, and `Bench.chunk` no
   longer knows the word. A part a configuration always has is refused as one that "can be taken out" only if it is
   optional, rather than "can be none". `KINDS` stays: its words (configuration, the recipe's parts, engine and the
   rest) are the docs', not the shell's, and its comment now says what it maps.
8. **Typed errors**: `src/chatddx/bench/errors.py`, `NotFound` and `Ambiguous`, both `LookupError`s, exported by
   `chatddx.bench`.
   - `NotFound` is raised for a thread, family, run or endpoint's engine that the person doesn't see, or the store
     doesn't hold. It carries `per_model`: the per-model threads under a name, when no model was given to pick one.
   - `Ambiguous` is raised for a name or id prefix that matches several, and by `save` when the person has several
     configurations of that name (a `ValueError` before).
   - The repl words the hint itself: when `per_model` is set, `handle` adds ", picked by the endpoint in the cell"
     (`src/chatddx/repl/commands.py:_said`).
   - Not typed: what the catalog raises, such as `expectation_for`'s "has expectations to choose from", which passed
     through `Bench.expectation` and `Bench.scoring` as a plain `LookupError` (see step 10). Since the API's phase 0,
     the bench raises `Ambiguous` for it.

9. **`Reads` is folded into `Bench`** (decided, the take on "one class or two"). `Bench.runs`, `run`, `reaching`,
   `scorers_for` (`Reads.scorers`, renamed since `Bench.scorers` lists the scorers the person sees) and `scoring` are
   the bench's own. The repl calls `bench.runs()` rather than `bench.reads.runs()`, and `src/chatddx/bench/reads.py`
   is gone.
10. **Decided, nothing to build:**
    - The catalog keeps applying the visibility rule to its own rows (`catalog/threads.py:visible`,
      `catalog/families.py:visible`, `catalog/threads.py:expectation_for`), as `docs/catalog.md` says it decides
      "what a person sees". The rule itself is `identity`'s, and the bench applies it to everything else.
    - The catalog's own `LookupError`s stay untyped until an API needs to tell an ambiguous expectation from a
      missing one. `Bench.expectation` and `Bench.scoring` would then raise `Ambiguous` for it. Done for the API
      (`agents/wip-api.md`, "Phase 0: built", step 5); the catalog's error stays untyped.
11. **One rule for finding things by name**: `Bench._named`. A name is matched whole first, then read as
    `OWNER/NAME`; the person's own wins, else the one shared with them; several raise `Ambiguous`, none `NotFound`.
    `Bench.thread` uses it for threads, and `Bench.family` for families, which can now be found as
    `archive/Dutchfall11w`. The repl's `show case`, `run` and the rest take `OWNER/NAME` for a case with it.
    Then the modules were laid out (see "Modules"): `bench.py` became `view.py`, and `TriedVariation` moved to
    `variation.py`. The tests followed: `test_view.py` and `test_variation.py`.

### Next
12. **Z1**: the map from role to kinds goes in `identity`, once the portal's views give it meaning. `sees` then takes
    the person's roles and the kind.

## Material for the bench's docs
Taken out of `docs/store.md` ("Looking things up for someone") and `docs/store-api.md` ("reads.py") at a3431e1, when
`Reads` left the store. It is updated to the code as it is now: `outstanding` is gone (phase 2, step 3), what is left
to score is `Bench.unscored`'s, and `Reads` is folded into `Bench` (step 9).

### Looking things up for someone
The bench offers a simple lookup scoped to one person: live runs they own, and live threads and families they own or
collaborate on, which lets a person refer to things loosely. A thread or a family is found by its name, matched whole
first and only then read as an owner and a name, since names may hold a slash. Runs are found by the start of their
id, or by a component their trial is built on.

For a run, the bench also tells:
- which scorers can grade its answers;
- which scoring it would be scored under now, from the expectations the catalog picks for the person;
- which of those scorers have no score of it under that scoring, so that a run whose expectations changed after it
  was scored is due again (`Bench.unscored`).

Like authorization, this decides what is relevant to show, not who may read what (`agents/wip-identity.md`,
"Authorization").

### What `Bench` looks up for the person
`Bench(conn: Connection, person: Person, inventory: Inventory, facts: Facts)` (`src/chatddx/bench/view.py`). Its
lookups go through `Catalog`, `Store` and `People`:

| Method | Returns / raises |
| --- | --- |
| `threads(word: str) -> list[tuple[Edit, About]]` | `Catalog.visible(kind, person.id)` for each kind `KINDS[word]` names: the heads of the live threads the person owns or collaborates on, in thread id order. |
| `thread(word: str, name: str, model: str \| None = None) -> tuple[Edit, str]` | The thread called `name` among them, or else its one variant `model` may use, `NAME (LANGUAGE)`, `NAME (MODEL)` or `NAME (LANGUAGE, MODEL)` (`chatddx.catalog.variants_for`), with the name that found it; several languages raise `Ambiguous`. See below. `NotFound` carries the per-model names when no model was given. |
| `families(tags=()) -> list[Family]` | The live families the person owns or collaborates on that have a case, with any of `tags`, by name. |
| `family(name: str) -> Family` | The family called `name`, as below; one without a name is called `family ID`. |
| `runs() -> list[RunStarted]` | The runs whose entries ever named the person as owner or collaborator, and whose `About` now has the person as owner and isn't deleted; newest first. A collaborator on a run doesn't see it. |
| `run(prefix: str \| None = None) -> RunStarted` | The latest of `runs()`, or the one whose id, as `str(UUID)`, starts with `prefix`. `NotFound("<login> has no runs")`, `NotFound("no run of yours starts with '<prefix>'")` or `Ambiguous("<n> runs of yours start with '<prefix>'")`. |
| `thread_by_id(id: int, word: str \| None = None) -> tuple[Edit, About]` | The head of thread `id`, and its `About`, when the person sees it and, with `word`, it is of a kind `KINDS[word]` names. Else `NotFound("no <word or 'thread'> <id> for <login>")`. |
| `family_by_id(id: int) -> Family` | Family `id`, when the person sees it and it has a case. Else `NotFound("no case <id> for <login>")`. |
| `run_by_id(run: UUID) -> RunStarted` | The run, when it is live and the person owns it, as `runs()` keeps them. Else `NotFound("no run <id> of yours")`. |
| `reaching(digest: str) -> list[RunStarted]` | The runs of `runs()` whose trial's closure holds `digest` (`Store.reaching(digest, "trial")`), newest first. |
| `scorers_for(run: RunStarted) -> list[tuple[Edit, About]]` | The visible scorer threads whose head's every view has an `output` selector that reaches the run's skeleton's `output_schema` (`chatddx.factors.select.reaches`), the check `check_score` warns about as `view.unreachable`. |
| `scoring(run: RunStarted, scorer: str) -> Scoring \| None` | The scoring the run would be scored under now: `Scoring(scorer, expectations)`, with, for each of the trial's cases in order, the expectation `Catalog.expectation_for(case, person.id, <the scorer's expectation_schema>)` picks, cases without one left out. `None` when no case has one. `Ambiguous` when the person has several expectations to choose from for a case. Nothing is stored. |
| `unscored(run: RunStarted) -> list[str]` | The scorers of `scorers_for(run)` with no score of the run under `scoring(run, scorer)`, so a run whose expectations changed after it was scored is due again. Scorers whose scoring can't be built are left out. |

A thread or a family is found by name among those the person sees (`Bench._named`):
1. those the person owns: exactly one is returned, several raise;
2. when they own none, all of them: exactly one is returned, several raise.

When nothing has the whole name and it holds `/`, it is read as `<login>/<rest>`, and when a person has that login,
step 2 runs over theirs named `<rest>`. A whole name wins over `OWNER/NAME`, since names may hold a slash, as
`plan (Qwen/Qwen3-8B-AWQ)` does. Several raise `Ambiguous("<word> '<name>' names <n>; name one as OWNER/NAME")`;
none raises `NotFound("no <word> '<name>' for <login>")`.

`scorers_for`, `scoring` and `unscored` resolve the run's trial, its skeleton and the scorers through `Store.get`
(`StructuralError` when one isn't stored or is of another kind).

`runs` shows only the runs the person owns now; collaborating on a run shows nothing.

# Objects: work in progress

At first factors and components were the same thing. Then exceptions turned up: execution settings are a factor but
not a component, and canary sets, compilations and now batches (`agents/wip-batch.md`) are components but not factors.
This file follows that split to its end, where how something is stored is a layer of its own and "factor" is a label
for what something means to the research. It also says why, for now, the kinds stay together.

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **Two questions, one package** (see "Two questions"): `chatddx.factors` decides both how a thing is stored and
   whether it is a factor.
2. **Keep the kinds together for now** (see "The pragmatic take"): every kind stays in `chatddx.factors`, batches
   too, and the package reads as "the factors, and the objects built alongside them". Take.
3. **Decided, built: the kinds are written down** (see "Kinds written down"): `src/chatddx/factors/kinds.py:KINDS`
   replaces self-registration.
4. **When to split** (see "The split"): the day an object kind has to import something above `factors`. Until then,
   the split is the plan for that day.
5. **Open**: the name (see "Naming"), and declaring `kind` as a class keyword (see "Kinds written down").

## Two questions
| How it is stored | What it is to the research |
| --- | --- |
| object: immutable, content-addressed, identified by its digest | factor: pinned, recorded or observed (`docs/factors.md`, "What a factor is") |
| record: append-only, a log sealed per run or score (`docs/ledger.md`) | instrument: measures observed factors without changing an output (canary sets) |
| state: rows updated in place (people; the worker's queue, `agents/wip-worker.md`, K2) | provenance: says how another object was made (compilations) |
| World: outside the store (`docs/inventory.md`) | work: what is run together (batches) |

Pinned factors are all objects, which is why the two looked the same. The exceptions run both ways:
- Execution settings are a recorded factor held in records (`src/chatddx/ledger/run.py:RunStarted.execution`).
- Canary sets, compilations and batches are objects that aren't factors (`docs/factors.md`, "Not factors").

## What exists today
- `src/chatddx/factors/base.py` and `bundle.py` define no factor kind: `Digest`, `Sha256Hex`, `Settings`, canonical
  form (`canonical_bytes`, `sorted_keys`, `sha256_digest`), `Frozen`, `Component` with versions, references
  (`RefTo`, `iter_refs`) and `cross_check`, `Resolver`, `resolve`, `StructuralError`, `Fingerprint`, `Code`,
  `Finding`, `Registry` and `Bundle`.
- 34 modules outside `factors` import from them, most of them for the general-purpose parts:
  - `ledger/record.py` seals records with `canonical_bytes` and `sha256_digest` without the records being components;
  - `inventory/` uses `Frozen` and `Digest`;
  - `core/rig.py` uses `Code`;
  - `runner/` and `importers/o11n.py` use `Finding` and `Registry`.
- What docs/ says about these dependencies:
  - "Factors depend on nothing else in chatddx" (`docs/factors.md`, introduction).
  - The ledger imports no chatddx package but `chatddx.factors` (`docs/ledger-api.md`).
  - The catalog imports no chatddx package but `chatddx.factors` and `chatddx.identity` (`docs/catalog-api.md`).
- All 24 kinds are defined in `factors` and listed in `factors/kinds.py:KINDS`, which is all `parse_component`
  reads.

## The pragmatic take
Take: keep every kind in `factors`, and put batches there too (`factors/batch.py`, beside `trial.py`; the batch's
section in `docs/factors.md` already sits under "Trials"). Don't extract the object layer, don't move kinds,
and don't rename the schema. The reasons:
- **Reproducibility needs the set of kinds to stay closed.** What the research needs from this layer is that digests
  never change, and that a bundle still loads offline years from now. With every kind in one package, every reader
  knows every kind. The split would have to rebuild that (see "Every kind in one place"), and it adds a new way to
  fail: a reader that forgot an import gets "unknown component kind" when it loads a bundle.
- **Nothing forces the move.** None of the non-factor kinds needs anything above `factors`:
  - canary sets use `RUNTIME_KEYS` (`factors/request.py`);
  - compilations use `Recipe` and `Code`;
  - a batch holds digests and an endpoint's name, which is just a string.

  The only cost of keeping them together is vocabulary, and `docs/factors.md` already says "Being a factor and being
  a component are separate questions".
- **The split's cost lands now, in the wrong places.** About 35 import sites in solidified code would change, the
  human-written docs would need reorganising through proposals, and the schema would need a migration. All of that
  while the batch planner, the worker and the portal are in flight.
- **When to revisit**: the day an object kind has to import something above `factors`, such as a run in the ledger or
  a person. That is when "The split" pays for itself.

## Kinds written down
Decided, built:
- `src/chatddx/factors/kinds.py:KINDS` lists every kind in the order of `docs/factors-api.md`'s "Component kinds"
  table. `BY_KIND` maps each kind name to its class and refuses a kind listed twice. `parse_component` moved there
  from `base.py`, and reads only the kinds `KINDS` lists.
- `Component` no longer registers its subclasses (`base.py:Component.__pydantic_init_subclass__`). It only refuses a
  `kind` without a literal default.
- `src/chatddx/factors/test/test_factors.py:test_every_kind_defined_is_written_down` checks that every component class
  the package defines is in `KINDS`. A kind someone forgot to list then fails a test, instead of failing when stored
  bytes are read back. A kind defined only in a test is no longer read back, and no longer needs undoing.
- `src/chatddx/store/test/test_catalog.py:test_kinds_and_fields_match_the_database` compares `THREAD_KINDS` with
  `BY_KIND`.
- Described in `docs/factors-api.md`, "kinds.py".

Why the tag stays: the class is visible in Python, but not in the stored bytes. `kind` does three jobs:
1. **Reading bytes back.** Stored JSON and bundles have to say what they are, as git's object header and OCI's media
   type do.
2. **Telling digests apart.** `kind` is part of the canonical bytes. Without it, an empty reasoning chunk and an
   all-defaults sampling chunk would both be `{"v": 1}` and share a digest, so the store would hold one row for two
   different things.
3. **A stable name, independent of Python.** Renaming or moving a class changes no digest, because the tag stays the
   same. The store relies on it too: the `kind` column, the catalog's `(digest, kind)` foreign keys, and
   `factor.check_ref` (`0003-t2-factor.sql`).

What is smelly is where it's declared: an instance field (`kind: Literal["trial"] = "trial"`) on every component
class, when it's class metadata. Take: declare it as a class keyword, `class Trial(Component, kind="trial")`.
- The serializer would add `kind` to the canonical form, and `parse_component` would strip it before validating, so
  the bytes and digests stay the same. A test pinning a few known digests would guard that.
- Pydantic passes a class keyword like this to `__init_subclass__` while still applying config keywords such as
  `frozen` (checked).
- It's cosmetic, so do it when the component classes are being touched anyway.
- The other `kind` fields, output contracts (`native`, `tool`, `text`), the inventory's `directory` source and the
  runner's delta kinds, are pydantic discriminators inside a value. They stay fields.

## The split
The plan for when "When to revisit" comes true. Nothing below is built.

### The object layer
`src/chatddx/objects/` would hold what `base.py` and `bundle.py` hold.
- **It depends on nothing in chatddx.** That rules out `chatddx.core`: `core/rig.py` imports `Code`, and
  `core/settings.py` reads the environment.
- **It defines no kinds.**
- **The packages built on it**: `factors` (its kinds), and the ledger, catalog, inventory, runner, store and edges
  (for the general-purpose parts).
- **It removes false dependencies rather than adding one.** Today the ledger and the inventory depend on `factors`
  only to get canonical JSON. The rule "factors depend on nothing" becomes "objects depend on nothing and define no
  kinds"; `factors` stays the lowest of the packages that mean something to the research.
- **Records aren't objects.** They are identified by their run and stage and sealed together (`docs/ledger.md`,
  "Seal"). The layer gives both canonical form; only objects get digests.
- **Imports change in one go**, with no re-exports from `chatddx.factors`, since this repository is its only user.
- **Tests**: the base and bundle tests in `src/chatddx/factors/test/test_factors.py` use factor kinds (skeletons,
  engines, outputs) as their examples. They stay there, or move to the new package with a kind defined only in the
  tests. Either way they stay `solidified`, since `docs/factors.md` describes them until `docs/objects.md` takes
  over.

### Naming
The usual name for an immutable, typed thing referred to by a hash of its content is an *object*:
- Git has typed objects (blob, tree, commit, tag) in an object database.
- Nix has store objects.
- OCI calls the bytes blobs, refers to them by the same `sha256:<hex>` digest this project uses, and types them by a
  media type, much as a kind does here.
- Merkle-DAG writing says node or block.

In Python, `Object` reads badly beside the built-in `object`, which is probably why "component" was chosen. "Component"
also suggests being part of a trial's closure, and compilations and batches are part of no closure. Options:
- **A**: `chatddx.objects`, with `Object` and the `object` schema. Take.
- **B**: `chatddx.objects`, keeping `Component` as the class name and `component` for the tables.

Open: a question for the user.

### Homes
| Kind | Is | Home | What moving it costs |
| --- | --- | --- | --- |
| trial, skeleton, chunks, cases, engines, scorings… | pinned factors | `factors`, as now | nothing |
| Execution | a recorded factor, not an object | `factors`, as now | nothing |
| canary set | an instrument | `ledger` | `catalog/titles.py` titles canary sets, so the catalog imports the ledger. Its SQL already points at the ledger's (`catalog.entry` → `ledger.run_stage`). |
| compilation | provenance | `catalog` | `compiled()` moves with it, while `compile_request` stays in `factors/request.py`. Every user (`catalog/{threads,titles,read}.py`, `store/{catalog,store}.py`, `curation/plan.py`, `bench/view.py`) sits at or above the catalog. |
| batch | work | a package of its own below the catalog, e.g. `chatddx.batch` | The catalog threads and titles batches (`agents/wip-batch.md`, "Kept batches"), and the store reads them, so the type can't live in the bench, which sits above both. The planner (`Bench.plan`, `bench/plan.py`) stays in the bench, and the worker's jobs name a batch by digest (`agents/wip-worker.md`, "The contract"). This is the same split as a trial in `factors` and its running in `runner`. |

Execution settings stay inside the start records of runs and scores (`ledger/run.py:RunStarted`,
`ledger/score.py:ScoreStarted`) either way. "Execution settings as a component" (`docs/factors.md`, "Potential design
improvements") is a storage choice only. The settings would be an object that the start record references by digest,
as `RunStarted.canaries` references a canary set, and they would stay outside the trial's digest. Execution stays a
recorded factor either way.

### Every kind in one place
Three readers need every kind:
- reading stored bytes back: `factors/kinds.py:KINDS`, behind `parse_component`, which the store and bundles use;
- the catalog's thread kinds (`catalog/model.py`, repeated in `store/migrations/0012-t2-catalog.sql`);
- the catalog's titles (`catalog/titles.py`).

`KINDS` can list only kinds its package can import. Once a kind lives above `factors`, the list has to move to the
lowest package that can import every package defining kinds, and whatever reads arbitrary objects (the store and the
bundle loader) has to go through it. A reader that imports only `factors` would then fail with "unknown component
kind" on a bundle holding a compilation. The kinds stay a closed set either way. The alternative, letting each kind
supply its own title, needs catalog reads (a title names its base's thread), so every kind would have to take a
catalog reader.

### The store
- **The schema.** `factor.component` and `factor.component_ref` hold every object. Once the `factor` schema holds
  nothing that is only about factors, one tier-0 migration renames it: `ALTER SCHEMA factor RENAME TO object`, plus the
  tables (option A). The foreign keys from `ledger` (trial, case, scoring) and `catalog` (edits, compilations, labels,
  languages) follow the rename, since Postgres binds them to the tables themselves rather than their names. Tier-1
  grants and tier-2 checks and triggers move with the schema.
- **`refuse_change`.** `factor.refuse_change()` is the insert-only trigger function every schema calls
  (`0003-t2-factor.sql`, called from `0006-t2-ledger.sql` and `0012-t2-catalog.sql`). It moves with the schema. Open:
  whether a function every schema uses belongs there.
- **Migration files** that were already applied keep their names. Rename the SQL in `store/store.py`,
  `store/catalog.py` and the store's tests.

### Docs
To propose when built:
- **New pages**: `docs/objects.md` and `docs/objects-api.md`. They take over the general sections of
  `docs/factors.md` under "How components work" ("Canonical form and digest", "Versions", "References and checks",
  "Errors and findings", "Registries and bundles", "Fingerprints", "Code", "Storage"). They also take the `base.py`,
  `bundle.py` and `kinds.py` sections and "Database: schema `factor`" from `docs/factors-api.md`.
- **`docs/factors.md`, "What a factor is"**: pinned factors are held as objects (`docs/objects.md`). The paragraphs
  on canary sets and compilations move to `docs/ledger.md` and `docs/catalog.md` if those kinds move. The proposed
  "Batch" section moves to the batch package's doc.
- **Dependency statements**: `docs/factors.md` ("depend on nothing else in chatddx"), `docs/ledger-api.md` and
  `docs/catalog-api.md` name `chatddx.objects`.
- **Glossary and migrations**: `docs/chatddx.md`'s "Digest", "Kind", "Bundle" and "Canonical form" refer to objects,
  and `docs/migrations.md`'s "factor" section follows the schema.

## The plan
Now, assuming "The pragmatic take":
1. **The kinds written down.** Built.
2. **The batch kind in `factors/batch.py`**, listed in `KINDS` and `THREAD_KINDS`, with the batch planner
   (`agents/wip-batch.md`, "The plan", 4).
3. **Optional**: `kind` as a class keyword, when the component classes are being touched anyway.

When the split is forced:
1. **The object layer**: move `base.py` and `bundle.py`, change the imports, move their tests, and write the
   proposals. No behaviour changes.
2. **`KINDS` moves up**, before any kind leaves `factors`.
3. **Homes**: the kind that forced the split first. Canary sets to the ledger and compilations to the catalog are
   optional.
4. **The schema rename**, once only objects are left in `factor`. It depends on step 1, not on step 3.

## Open
- The name, should the split happen (see "Naming").
- `kind` as a class keyword (see "Kinds written down").
- Whether canary sets and compilations ever move.
- Where `refuse_change` lives.
- Whether execution settings become an object, which this plan doesn't decide.

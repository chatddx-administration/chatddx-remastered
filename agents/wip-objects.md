# Objects: work in progress

At first factors and components were the same thing. Then exceptions turned up: execution settings are a factor but
not a component, and canary sets, compilations and now batches (`agents/wip-batch.md`) are components but not factors.
This file follows that split to its end: how something is stored becomes a layer of its own, and "factor" becomes a
label for what something means to the research.

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **Two questions, one package** (see "Two questions"): `chatddx.factors` decides both how a thing is stored and
   whether it is a factor.
2. **The object layer** (see "The object layer"): move `factors/base.py` and `factors/bundle.py` into a root-level
   package that defines no kinds and depends on nothing in chatddx. Behaviour stays the same; only imports change. Take.
3. **Homes** (see "Homes"): batches need a package of their own, below the catalog. Canary sets could move to the
   ledger and compilations to the catalog, but that move is optional. Execution stays where it is. Take.
4. **Every kind in one place** (see that section): the price of moving kinds out of `factors`. Take: one module that
   imports every package defining kinds.
5. **Open**: the name (see "Naming"), and renaming the `factor` schema (see "The store").

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
  form (`canonical_bytes`, `sorted_keys`, `sha256_digest`), `Frozen`, `Component` with its kind registry, versions,
  references (`RefTo`, `iter_refs`) and `cross_check`, `Resolver`, `resolve`, `parse_component`, `StructuralError`,
  `Fingerprint`, `Code`, `Finding`, `Registry` and `Bundle`.
- 34 modules outside `factors` import from them, most of them for the general-purpose parts:
  - `ledger/record.py` seals records with `canonical_bytes` and `sha256_digest` without the records being components;
  - `inventory/` uses `Frozen` and `Digest`;
  - `core/rig.py` uses `Code`;
  - `runner/` and `importers/o11n.py` use `Finding` and `Registry`.
- What docs/ says about these dependencies:
  - "Factors depend on nothing else in chatddx" (`docs/factors.md`, introduction).
  - The ledger imports no chatddx package but `chatddx.factors` (`docs/ledger-api.md`).
  - The catalog imports no chatddx package but `chatddx.factors` and `chatddx.identity` (`docs/catalog-api.md`).
- Kinds register themselves when their class is defined (`base.py:Component.__pydantic_init_subclass__`), and
  `factors/__init__.py` imports every module that defines one. So importing `chatddx.factors` is enough for
  `parse_component`, `Registry.add_raw`, `Bundle.load` and `Store.get` to read any kind.

## The object layer
Take: `src/chatddx/objects/` holds what `base.py` and `bundle.py` hold.
- **It depends on nothing in chatddx.** That rules out `chatddx.core`: `core/rig.py` imports `Code`, and
  `core/settings.py` reads the environment.
- **It defines no kinds.**
- **The packages built on it**: `factors` (all its kinds), and the ledger, catalog, inventory, runner, store and
  edges (for the general-purpose parts).
- **It removes false dependencies rather than adding one.** Today the ledger and the inventory depend on `factors`
  only to get canonical JSON. The rule "factors depend on nothing" becomes "objects depend on nothing and define no
  kinds"; `factors` stays the lowest of the packages that mean something to the research.
- **Records aren't objects.** They are identified by their run and stage and sealed together (`docs/ledger.md`,
  "Seal"). The layer gives both canonical form; only objects get digests.
- **Imports change in one go.** Take: no re-exports from `chatddx.factors`, since this repository is its only user.
- **Tests**: the base and bundle tests in `src/chatddx/factors/test/test_factors.py` use factor kinds (skeletons,
  engines, outputs) as their examples. They stay there, or move to the new package with a kind defined only in the
  tests. Either way they stay `solidified`, since `docs/factors.md` describes them until `docs/objects.md` takes
  over.

## Naming
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

## Homes
| Kind | Is | Home | What moving it costs |
| --- | --- | --- | --- |
| trial, skeleton, chunks, cases, engines, scorings… | pinned factors | `factors`, as now | nothing |
| Execution | a recorded factor, not an object | `factors`, as now | nothing |
| canary set | an instrument | `ledger` | `catalog/titles.py` titles canary sets, so the catalog imports the ledger. Its SQL already points at the ledger's (`catalog.entry` → `ledger.run_stage`). |
| compilation | provenance | `catalog` | `compiled()` moves with it, while `compile_request` stays in `factors/request.py`. Every user (`catalog/{threads,titles,read}.py`, `store/{catalog,store}.py`, `curation/plan.py`, `bench/view.py`) sits at or above the catalog. |
| batch | work | a package of its own below the catalog, e.g. `chatddx.batch` | The catalog threads and titles batches (`agents/wip-batch.md`, "Kept batches"), and the store reads them, so the type can't live in the bench, which sits above both. The planner (`Bench.plan`, `bench/plan.py`) stays in the bench, and the worker's jobs name a batch by digest (`agents/wip-worker.md`, "The contract"). This is the same split as a trial in `factors` and its running in `runner`. |

Execution settings stay inside the start records of runs and scores (`ledger/run.py:RunStarted`,
`ledger/score.py:ScoreStarted`). "Execution settings as a component" (`docs/factors.md`, "Potential design
improvements") becomes a storage choice only. The settings would be an object that the start record references by
digest, as `RunStarted.canaries` references a canary set, and they would stay outside the trial's digest. Execution
stays a recorded factor either way.

## Every kind in one place
Three readers need every kind:
- reading stored bytes back: the kind registry behind `parse_component`, which the store and bundles use;
- the catalog's thread kinds (`catalog/model.py`, repeated in `store/migrations/0012-t2-catalog.sql`);
- the catalog's titles (`catalog/titles.py`).

Once kinds live outside `factors`, importing `chatddx.factors` no longer registers all of them. A process that reads
a bundle holding a compilation without importing the catalog then fails with "unknown component kind". This is why
everything drifted into `factors`.

Take: one module imports every package that defines kinds, and whatever reads arbitrary objects, the store and the
bundle loader, goes through it. The kinds stay a closed set. The alternative, letting each kind supply its own title,
needs catalog reads (a title names its base's thread), so every kind would have to take a catalog reader.

## The store
- **The schema.** `factor.component` and `factor.component_ref` hold every object. Once the `factor` schema holds
  nothing that is only about factors, one tier-0 migration renames it: `ALTER SCHEMA factor RENAME TO object`, plus the
  tables (option A). The foreign keys from `ledger` (trial, case, scoring) and `catalog` (edits, compilations, labels, languages)
  follow the rename, since Postgres binds them to the tables themselves rather than their names. Tier-1 grants and
  tier-2 checks and triggers move with the schema.
- **`refuse_change`.** `factor.refuse_change()` is the insert-only trigger function every schema calls
  (`0003-t2-factor.sql`, called from `0006-t2-ledger.sql` and `0012-t2-catalog.sql`). It moves with the schema. Open:
  whether a function every schema uses belongs there.
- **Migration files** that were already applied keep their names. Rename the SQL in `store/store.py`,
  `store/catalog.py` and the store's tests.

## Docs
To propose when built:
- **New pages**: `docs/objects.md` and `docs/objects-api.md`. They take over the general sections of
  `docs/factors.md` under "How components work" ("Canonical form and digest", "Versions", "References and checks",
  "Errors and findings", "Registries and bundles", "Fingerprints", "Code", "Storage"). They also take the `base.py`
  and `bundle.py` sections and "Database: schema `factor`" from `docs/factors-api.md`.
- **`docs/factors.md`, "What a factor is"**: pinned factors are held as objects (`docs/objects.md`). The paragraphs
  on canary sets and compilations move to `docs/ledger.md` and `docs/catalog.md` if those kinds move. The proposed
  "Batch" section moves to the batch package's doc.
- **Dependency statements**: `docs/factors.md` ("depend on nothing else in chatddx"), `docs/ledger-api.md` and
  `docs/catalog-api.md` name `chatddx.objects`.
- **Glossary and migrations**: `docs/chatddx.md`'s "Digest", "Kind", "Bundle" and "Canonical form" refer to objects,
  and `docs/migrations.md`'s "factor" section follows the schema.

## The plan
Assuming the takes.
1. **The object layer**: move `base.py` and `bundle.py`, change the imports, move their tests, and write the
   proposals. No behaviour changes.
2. **The kinds index**, before any kind leaves `factors`.
3. **Batch's package**, with the batch planner (`agents/wip-batch.md`, "The plan", 4).
4. **Optional**: canary sets to the ledger, compilations to the catalog.
5. **The schema rename**, once only objects are left in `factor`. It depends on step 1, not on 3 or 4.

## Open
- The name (see "Naming").
- Whether canary sets and compilations move at all.
- Where `refuse_change` lives.
- Whether execution settings become an object, which this plan doesn't decide.

# Seed: work in progress

The reworks waiting for `chatddx.seed` (`src/chatddx/seed/`) and its commands, `chatddx init-data` and
`chatddx wipe-data` (`src/chatddx/cli.py`). There's no draft doc yet. What the commands do today is in
`agents/wip-sample-data.md` ("init-data"); this file doesn't repeat it.

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## The package today
- `plan.py`: `plan_factors` reads a data set's `factors.toml` (and `--factors` files) into components, with the
  data set's own extensions: references by name, `json_schema_path`, `from_facts`, `fork_of`, and `tags`,
  `description` and `label` as catalog entries. It's pure. `load_cases` reads `cases.toml`. `SAMPLE` locates the
  sample data set.
- `write.py`: `seed` writes a plan to the store and the catalog for the `archive` person, shares it with a user and
  gives the giftbag forks; `wipe` takes them back.
- `world.py`: `endpoints`, init-data's line per World endpoint.

## Decided
- **The name changes**, so "seed" stops meaning two things (see "The name").
- **Facts are bundled** (`src/chatddx/facts/models.toml`): init-data loads them by default, and `--facts` adds more
  files beside them.
- **The fake engines are the sample World's** (`worlds/sample/factors.toml`), so seeding another World no longer
  seeds them. Seeding the sample takes `--factors worlds/sample/factors.toml`. Without it, the plan has 18 records
  and reports every `from_facts` record as skipped, since no planned engine serves a model.
- **Worlds live in `worlds/<name>/`**: `worlds/sample/` and `worlds/kompismoln/` (`docs/inventory.md`).

## Decided this run (the user, 2026-10-09)
Implemented in this order, each its own commit; the doc is `docs/curation.md` once all are in.
1. **Name: `chatddx.curation`**: the package manages the store's authored content: it loads (`init`), wipes
   (`wipe`) and repairs (`repair`) it now, and import, export and verification are its business later. `_Seeder`
   becomes `_Init`; the commands keep their names. `SAMPLE` moves with it. "Seed" stays the sampler's word.
2. **`--world DIR`**, for init-data and the repl: a World directory, read as `inventory.toml` plus, when present,
   `factors.toml` (init-data) and `facts.toml` (both, beside the bundled facts). `--vignettes` goes; `--factors` and
   `--facts` stay for more files.
3. **`CHATDDX_WORLD`** in `chatddx.core.settings` is the default `--world`; `.env-example` sets `worlds/sample`.
4. **One inventory check pass now**: the inventory checked against the engines returns findings; init-data prints
   them and `world.py` goes. No reason to defer but touching a solidified package; docs/inventory.md gets proposed
   amendments.
5. **Repairs**: init-data surveys the source and says renamed or changed rather than missing; `chatddx repair-data`
   applies `Catalog.repair` to the archive's families the survey finds renamed or changed, `--dry-run` to list them.
6. **Tags**: a re-run withdraws a tag the archive gave that the data no longer lists; tags people gave stay.
7. **Leftovers**: archive threads and families the data set no longer names are reported, not deleted. A garbage
   collection as the admin that deletes everything unreferenced came up: an open issue for the doc.
8. **Chunk languages**: a text-bearing record takes `language`, and `factors.toml` may set a top-level default; both
   are written on the digest (`Catalog.language`). The planner checks them. In the sample only the six outputs with
   guidance and `toolset.web` carry text (`prompt.case` is slots only, `output.raw` has none).
9. **Cases by language**: `cases-<lang>.toml`, whose language is its cases' families'; a case's own `language` key
   goes (notes keep theirs); every `cases-*.toml` is read, and an id in two files is refused. The sample is
   `cases-en.toml` (79) and `cases-sv.toml` (20).
- Done before these: lint checks an expectation schema once per lint, and the mechanics tests seed three cases
  (02532fc).

## The name
"Seed" is already the sampler's word: a trial's `seeds`, a replicate is "one seed of a trial", `suggest_seeds`,
`render(…, seed=)`, a judge's seeds, and `docs/factors.md` ("Greedy sampling and seeds"). A package that "seeds the
sample" puts "the seeded engines" next to "the engine's seeds" in the same docs and output.

Candidates:
- **`chatddx.data`.** The commands already say `init-data`, `wipe-data` and `--data`, and `src/chatddx/data/`
  already holds the sample data set, so the package and its data would share one name: `plan.py`, `write.py` and
  `sample/` in one place, with `SAMPLE` beside them. Against it: "data" is broad, and could be read as all data.
- **`chatddx.datasets`.** Says exactly what it handles: a data set, authored content written to the store, apart
  from a World. Longer, and its directory would still be `src/chatddx/data/sample/` unless that moves too.
- **`chatddx.stock`** ("stock the archive"): a verb no other part of the rig uses, but not obvious to a reader.
- **`chatddx.provision`**: familiar from ops, which suggests hosts and engines, the World's business.
- **`chatddx.bootstrap`**: suggests a one-off, while init-data is re-run to validate and update.
- Ruled out: `chatddx.load`, which `Store.load`, `Facts.load` and `Inventory.load` already use, and
  `chatddx.ingest` or anything with "import", which is the World importers' word (`chatddx import-engine`).

The act needs a word too, for prose and function names. "Land" is taken: the facts say a reasoning level lands
where its collapses end (`ReasoningFacts.land`). The commands' own verbs are free: `seed` becomes `init` and `wipe`
stays, matching `init-data` and `wipe-data`, and `_Seeder` becomes `_Init`.

Take: `chatddx.data`, with `init` and `wipe`.

What the rename touches beyond the package: `docs/catalog.md` ("Names"), `docs/factors.md` (three citations of
`src/chatddx/seed/`), `docs/facts.md` ("The seeder is the only caller today"), `docs/inventory.md` ("Sources",
"Reaching an engine"), and the tests that import `SAMPLE` from `chatddx.seed.plan` in five packages.

## Reworks
1. **A World directory as input.** init-data takes a World as two flags, `--world FILE` for the inventory and
   `--factors FILE` for its engines, or `--vignettes DIR` for a source without a World. Take: `--world DIR` takes a
   World directory and reads its `inventory.toml` and, when present, its `factors.toml`. Seeding the sample becomes
   `init-data USER --world worlds/sample`. `--factors` stays for more files. With `CHATDDX_WORLD` (proposed in
   `docs/inventory.md`) as the default, a deployment would need no flag at all.
2. **`--vignettes DIR`.** Take: keep it until the World input lands, then drop it. A World that is only a source is
   two lines of TOML.
3. **The data set's format** is written down only in `src/chatddx/data/sample/factors.toml`'s header and
   `agents/wip-sample-data.md` ("The sample data now"). It needs a doc of its own when the package is solidified:
   the tables, the extensions above, `code` defaulting to the running chatddx, and `cases.toml` (tags, language,
   targets).
4. **A World's facts.** A World may serve a model the bundled facts don't know, such as a remote Gemma. Take: a World
   directory may hold a `facts.toml` that the World input loads beside the bundled ones; a model may still have
   facts in only one file.
5. **Endpoint lines are a check of their own.** `world.py` repeats what `start_up` and `url_of` check. It goes when
   the inventory has one check pass (`docs/inventory.md`, "Checks happen when an entry is used"), and init-data
   prints that pass's findings.
6. **Test helpers.** `src/chatddx/conftest.py:sample_plan` now plans the sample with the sample World's engines in
   one place (it was defined twice, and planned inline five more times). `SAMPLE` still lives in
   `chatddx.seed.plan`; after the rename it belongs to the data package.
7. **Still open from the sample data** (`agents/wip-sample-data.md`, "init-data"): a renamed vignette shows as
   missing (a `repair` command), tags and collaborators are only ever added on a re-run, the seeded chunks have no
   language (G18), and what `wipe-data` takes back.

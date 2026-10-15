# Variations: work in progress

What a variation is across the docs and the code, where its meanings part, and what solidifying it took. Split from
`agents/wip-variants.md`, which keeps the variants, the threads made per language and model, and which variant a
variation belongs to. Checked against the code at fcef71a, and its quotes again at f7fd2b0, once configurations and
requests were settled. "Decided" means the user said so; "Take" is the agent's.

## Where it stands
Decided: the takes, W1, R2 and the one on purpose and appendix layout, and this file before `agents/wip-variants.md`.
They are built, and the docs have them as suggestions (`AGENT:` blocks naming this file), which wait to be written
in; then this file goes. What was built:
1. **The words**: `catalog.Variation` is `catalog.Divergence`, `threads.variation` and `Catalog.variation` are
   `divergence`, and `Proposed.variation` is `Proposed.divergence`. The repl's `configurations` says `differs` for a
   part whose chunk differs between a name's variants. "Variation" keeps two types, `bench.TriedVariation` and its
   look, `api.schemas.Variation`, which are one thing.
2. **What a run records of what it ran**: two entry fields on a run, `varied`, the configuration's edit, and
   `replaced`, a part and its chunk or none, one per part replaced (`src/chatddx/catalog/model.py`,
   `catalog/threads.py:check_varied`, `src/chatddx/store/migrations/0026-t2-catalog-run-variation.sql`). The bench
   writes them with the run's name as it starts (`src/chatddx/bench/runs.py:start`), running again carries them
   (`again`), `Bench.ran` reads them, the API's `Run.ran` gives them, and a run's page links the variation as it was
   tried (`src/chatddx/portal/runs.py:_configuration`), else a version holding its skeleton, as before. Runs from
   before have none, and are linked as before.
3. **Purpose and appendix layout**: as they are. A variation replaces the nine parts; the docs say why, and that the
   appendix layout becomes a part when someone wants to vary it (`docs/bench.md`, "Outstanding").
4. **A configuration's proposal on its page**, to its owner, with what the fork keeps by part, and following, which
   comes back to the page (`src/chatddx/portal/configurations.py`, `threads.py:following`'s `next`).
5. **Tests**: `src/chatddx/store/test/test_catalog.py:test_a_run_says_what_it_varied` and the entry shape held to
   `RECIPE_PARTS`; `bench/test/test_runs.py:test_a_run_says_what_it_varied_and_running_again_too`;
   `api/test/test_runs.py`'s `ran`; `portal/test/test_running.py:test_a_run_links_the_variation_it_ran`,
   `test_varying.py:test_a_fork_follows_its_origin_from_its_page` and
   `test_a_run_links_the_version_it_ran_else_one_holding_its_skeleton`.

## Where the word comes from
In the old chatddx a configuration's parts were *slices*: instruction, output, coercion, reasoning, sampling and
toolset. A slice's alternatives were its *variations*: `set reasoning off` set the variation `off`, a chunk, and
compiling turned it into settings for the model of the stack the configuration was paired with
(`docs/repl.md` and `docs/research/a-new-datamodel.md` at 504792c in chatddx-administration/chatddx). The label
`NAME+PART=CHUNK` is from then. Remastered kept the cell, the parts and the label, and a variation became a
configuration with parts replaced, where it was a part's alternative.

## Variation: one idea, two definitions, three types
The idea: a configuration seen as recipe parts replaced over a version of a configuration. The docs define it two ways:
- **Kept, of any kind.** `docs/catalog.md` ("Configurations and variations", "Terms"): "a fork, of any kind, together
  with what it changes from the version it came from". `docs/curation.md`'s `fork_of` uses it so: a record "that this
  one is a variation of".
- **Tried, of a configuration.** `docs/bench.md`, `docs/api.md`, `docs/repl.md` and `agents/wip-portal.md`: "a
  configuration with recipe parts replaced over it, or none, that nobody has saved".

`docs/chatddx.md` ("Intended evolution of configurations") has a variation replace "one or more of the recipe's
parts", and holds both as stages of one thing: "a variation being tried is just a digest, saving it will make it a
configuration of its own", which a fork or an edit is. It also says variations are "not an object in the code". The
code has three types of that name:
- **`catalog.Variation`** (`src/chatddx/catalog/model.py`; `catalog/threads.py:variation`): a fork's base, its origin's
  head, and what it `varies`, derived from stored edits. Compared by whole recipes (`purpose` and `appendix_layout`
  too) when both are compiled, else by the component's fields. Read by following (`bench/following.py`), titles
  (`catalog/titles.py`) and `GET /api/threads/{id}/proposal`.
- **`bench.TriedVariation`** (`src/chatddx/bench/variation.py`): an edit, the name it was called by, and the nine parts
  replaced over it, a plain value. What `Bench.variation`, the repl's cell, scripted runs, `NewRun`, a configuration's
  forks and edits, and the `variation` island hold.
- **`api.schemas.Variation`**: a look at a `TriedVariation`, a response with no id.

Where they part:
- **Kept or tried.** A `TriedVariation` loses its parts when it is saved (`Saved.variation`, "with nothing replaced");
  what was replaced is known afterwards only if the save was a fork, as the catalog's `varies`. A save that is an edit
  is no variation in the catalog's sense, and a run of an unsaved one keeps only its label, as the run's name
  (`agents/wip-portal.md`, "What the variation being tried leaves").
- **Compared with what.** The catalog compares a fork's head with its base, which moves when a proposal is followed,
  and any field of the recipe; the bench compares with the edit it was built on, and replaces the nine parts.
- **Compiled by which code.** Varying a part compiles the whole recipe with the running code
  (`src/chatddx/bench/seen.py:Seen.skeleton`), so after a change to the compiler a variation can differ from the edit
  it was built on where nothing was replaced, and the catalog's `varies`, which compares recipes, says nothing of it.
- **Kinds.** The catalog's is of any kind, a chunk's fork too; everywhere else a variation is a configuration's.
- **Same identifiers.** `bench.variation()` gives a `TriedVariation` and `catalog.variation()` a `catalog.Variation`;
  `Saved.variation` and `Proposed.variation` are one of each (`bench/model.py`); `TriedVariation.varied` is a `Recipe`.
- **"Varies"** is what a fork changes from its base in the catalog, and in the repl's `configurations` table a part
  whose chunk differs between a name's variants (`repl/listing.py:_alike`), which is no variation at all.

`docs/factors.md` speaks of runs of one trial as "a second source of variation": plain English, and no conflict.

## How it differs
- A **configuration** is what is kept: a thread with an id, an owner, a name and versions, each a request with its
  recipe (`docs/catalog.md`, "Configurations and variations").
- A **variation** is a directed, deliberate change: this configuration is that one with these parts replaced. It is
  what a researcher varies to measure it, and a fork records it.
- A **variant** is a sameness: this configuration is that one made for another language or model
  (`agents/wip-variants.md`).

They cross where init-data makes a variation per variant, and where an edge picks a variation's variant for an
endpoint's model; both are `agents/wip-variants.md`'s ("They cross"; L).

Other things the check turned up:
- **A configuration's page never offered its proposal.** The thread page that does redirects a skeleton to
  `/configurations/{id}` (`src/chatddx/portal/threads.py:thread_page`), which showed the variation being tried only.
  Built (4 above).
- **What a fork varies is compared by recipe**, so what the running code compiles differently isn't in it ("Compiled
  by which code" above). Suggested as an open issue in `docs/catalog.md`, "Smaller issues".

## The work, as it was planned
Solidifying (`AGENTS.md`, "Staging") means built, described in `docs/`, and this file removed. Here that is:
1. **The words** (see W): one definition of variation in every doc, as suggestions, and the identifiers that follow
   it: the catalog's `Variation` named after what it is, a fork compared with its base, and with it
   `Proposed.variation`; the repl's "varies" renamed.
2. **What a run records of what it ran** (see R): its trial, so its skeleton, and its variation's label as its name;
   not the configuration, the edit or the parts set (`src/chatddx/ledger/run.py:RunStarted`). A run's page links any
   configuration with an edit that holds its skeleton (`src/chatddx/portal/runs.py:_version`).
3. **Purpose and appendix layout** are a configuration's, and the catalog's `varies` compares them, but a variation
   replaces the nine parts only, so only a new configuration from a recipe sets them. Take: the appendix layout as a
   part a variation can replace, when someone wants to vary it; the purpose never, since a judge configuration is no
   use at a run.
4. **A configuration's proposal on its page**, as the thread page offers it.
5. **Tests** for each.

## Options

### W. The words
- **W1. Keep both, defined against each other.** A variation is a configuration with parts replaced over a version of
  another, tried or kept; a variant is a thread made for a language or a model. The catalog's type is renamed after
  what it is, a fork compared with its base, so that one word names one type, and the repl's "varies" becomes
  "differs". "Configuration" stays the thread; the cell holds a variation of one. The cheapest, but the distinction
  stays a convention: in plain English the two words are near-synonyms.
- **W2. Rename "variant"**, while it is rebuilt anyway, to a word that doesn't share a stem with "variation", such as
  "adaptation", so that "a variation of a variant" is never written. Costs the docs and the repl's manual.
- **W3. One word**: a variant as a variation along the language and model axes. A variant isn't a change from a base,
  and nobody chooses one to measure it, so this blurs the distinction rather than drawing it.

Take: W1. "Variant" has kept one meaning; what drifted is "variation" (two definitions, three types). W2 if the
solidified docs still read awkwardly.

### R. What a run records of what it ran
- **R1. As now**: the trial, and the variation's label as the run's name.
- **R2. Entries on the run**, as its name is: the configuration, the edit it varied and the parts set, so that a run
  of an unsaved variation links the configuration it came from. New entry fields, a tier-2 migration.
- **R3. The run's start record**: the same, sealed with the run, in a new version of the record.

Take: R2. What a person called a run belongs to the catalog, as its name does, and the ledger keeps what ran; a run
of a trial nobody varied has no entries to write.

## Left
- **The suggestions** in `docs/` written in, or answered; then this file goes.
- **W2**, if the solidified docs still read awkwardly with both words.

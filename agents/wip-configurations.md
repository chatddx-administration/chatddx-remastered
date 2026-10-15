# Configurations: work in progress

What a configuration is in the factors, the catalog, the bench, its edges and the data sets, where the meanings part,
what is decided and built, and what is left before variations and variants build on it (`agents/wip-variants.md`).
Checked against the code at fcef71a, and against the old chatddx's `docs/repl.md`, `docs/portal.md` and
`docs/research/a-new-datamodel.md` (chatddx-administration/chatddx at 504792c). "Decided" means the user said so;
"Take" is the agent's and still open.

## Decided
- **I2. A configuration's versions are requests with their recipes.** A skeleton thread, whose edits are written when
  their skeleton or their recipe differs from the head's. Refined while building it: the head's recipe compiled by
  other code is no new version, since the compiler's code carries `CHATDDX_REVISION` (`src/chatddx/rig.py:rig`), so
  init-data would otherwise give every configuration it loads a version at each deploy, and every fork of one a
  proposal that changes nothing. Take: as built; the compilation by the new code is still stored, beside the edit, when
  the bench or init-data compiles it.
- **M1. A configuration is made for a model by its chunks**, as before: what it sends changes only by an edit, and its
  siblings for other models are variants (`agents/wip-variants.md`, V).
- **H1. Hand-written skeletons are configurations without a recipe**: only the store writes one, and nothing varies it.
- **J1. Judge configurations are the same kind, told apart by purpose**, and listed apart at every edge.
- **W1. "Configuration" at the edges, "skeleton" below**: the API gives the word beside the kind, and the titles and
  findings people read say configuration.

## Built
- **I2**: `catalog.threads.holds` decides when keeping writes nothing, and `Catalog.keep` asks it; a configuration's
  language is its own edit's recipe's (`catalog.language.edit_languages`, `Catalog.edit_languages`), which the API's
  threads give; and the look's `held_by` is a configuration whose head has the variation's recipe too
  (`Bench.holder(word, digest, recipe)`), so the island's "This is X already" and where a save goes agree with what
  saving does. Tests: `store/test/test_catalog.py:test_a_skeleton_thread_keeps_each_recipe_of_its_request`,
  `catalog/test/test_language.py:test_an_edit_is_in_the_language_of_its_own_recipe`,
  `bench/test/test_seen.py:test_a_new_recipe_of_the_same_request_is_a_new_version`.
- **J1**: the repl's `configurations` lists judge configurations in a table of their own, headed "judge
  configurations" (`src/chatddx/repl/listing.py`;
  `repl/test/test_listing.py:test_judge_configurations_are_listed_apart`).
- **W1**: `Thread.word` in the API (`chatddx.bench.word_of`, moved from the portal); a configuration without a stored
  compilation is titled "generation configuration 1a2b3c"; `facts.reasoning_unmatched` and `facts.sampling_unmatched`
  say "the configuration's". `frontend/openapi.json` follows.
- **The "a fork" link** on a configuration's page opens the thread it was forked from, not the thread whose id is the
  edit's (`src/chatddx/portal/configurations.py`;
  `portal/test/test_varying.py:test_a_fork_links_the_configuration_it_was_forked_from`).
- **The docs**: suggestions, as rule one has it, in `docs/chatddx.md`, `catalog.md`, `catalog-api.md`, `bench.md`,
  `bench-api.md`, `api.md`, `api-api.md`, `repl.md`, `repl-api.md`, `repl-manual.md`, `facts-api.md` and
  `factors.md`.

## Left
- **The suggestions** wait for a human to write them in.
- **Errors and refusals still say skeleton**, as W1 named titles and findings only: the cross-checks ("trial uses a
  judge skeleton", "judge uses a generation skeleton"), the gate ("the skeleton's tools would get content from source
  …"), `check_language` ("a compiled skeleton's language comes from its recipe") and the repl's `show configuration`,
  which prints a skeleton's fields. Take: the gate's too, as people read it at a run; the cross-checks stay the
  factors' own.
- **A skeleton's language without an edit** still votes over every compilation of it: a trial's, a judge's, and a
  stored skeleton's lints (`Bench.linted`). Take: as is; a trial has no edit to ask.
- **The configuration page never offers a proposal** (see "Where the meanings parted at fcef71a").
- **What a run records of its configuration** (8 below), with variations (`agents/wip-variants.md`).
- **What holds a configuration** (9 below), the portal's.
- **Purpose and appendix layout** can't be varied (6 below). Take: the appendix layout as a part a variation can
  replace, when someone wants to vary it; the purpose never, since a judge configuration is no use at a run.
- **Then variations and variants**, on this (`agents/wip-variants.md`).

## Where the word comes from
In the old chatddx a configuration was "what to ask and how … A configuration names no model" (`docs/repl.md` at
504792c, "A few words first"). Its parts were *slices*: instruction, output, coercion, reasoning, sampling and toolset.
A slice's alternatives were its *variations*: `set reasoning off` set the variation `off`, and compiling turned it into
settings for the model of the stack the configuration was paired with, `compile(configuration, case, stack facts,
seed)` (`docs/research/a-new-datamodel.md` at 504792c, "2.4 Compile"). The research note behind it asked for "settings
that can be varied one at a time and compared across models … each setting lives in one place and means the same thing
whatever it is paired with". A configuration could extend another and follow it.

Remastered kept the cell, the parts and the label `NAME+PART=CHUNK`, and took the model out of compiling: facts "never
reach the wire themselves but write literal chunks before compilation so no digest depends on them" (`docs/facts.md`).
So a sampling or reasoning chunk is written for one model, init-data writes one per model, and a configuration that
uses one is made per model: that is where per-model variants come from. Per-language ones come from texts written per
language. And a variation became a configuration with parts replaced, where it was a part's alternative.

## What a configuration was at fcef71a

### In the factors
The word isn't used, except for "the judge skeleton, as a configuration of purpose `judge`" (`docs/factors.md`,
"Judge"). Three things make one:
- **A recipe**: a purpose, an appendix layout and the nine parts (`src/chatddx/factors/request.py:Recipe`). It isn't a
  component, has no digest, and is kept only in a compilation. Principal author: researchers.
- **A compilation**: the recipe, the skeleton it compiled to, and the compiler's code. Provenance, not a factor:
  nothing refers to one.
- **A skeleton**: the frozen request: purpose, messages with their slots, body, contract, appendix layout and tools.
  It has no name, language, model or recipe. Principal author: none. Trials and judges pin it.

Compiling depends on the chunks, their translations, the output's schema ops and the code; not on the facts, the model
or the engine, which comes in when rendering. Two recipes can compile to one skeleton
(`src/chatddx/catalog/test/test_language.py`), and one recipe compiles to another skeleton when the code changes.

### In the catalog
"A configuration is a skeleton thread" (`docs/catalog.md`, "Terms"). Each edit holds a skeleton, and may name a
compilation of that very skeleton, which the database enforces. There is no configuration kind, and
`docs/catalog-api.md` says skeleton throughout.

### In the bench and its edges
"Configuration" is the bench's word for the kind `skeleton` (`src/chatddx/bench/model.py:KINDS`). Nobody writes a
skeleton (`WRITTEN` leaves it out). A configuration is made:
- **from a recipe**, compiled by the running code, with no origin (`Bench.new`; `POST /api/threads` with a recipe);
- **by keeping a variation**, as a fork or an edit (`src/chatddx/bench/configurations.py`; the repl's `save`, the
  API's forks and edits);
- **by following a proposal**, compiled by the running code (`src/chatddx/bench/following.py`);
- **by init-data**, a thread for each language and model a data set's `[recipe.X]` is made in, and by the giftbag,
  a fork of each (`src/chatddx/curation/plan.py`, `write.py`). The sample makes 31 from 10 records.

It is listed by purpose (`Bench.purposed`) and by the title of its answer's JSON Schema (`Bench.answering`). The API
takes `kind=configuration`, refuses `kind=skeleton`, and gives `"kind": "skeleton"` back; titles, lints and errors say
skeleton. The portal has `/configurations`, with the judges' apart, and `/configurations/{id}`, the variation island's
page. The repl's cell holds a variation of one.

### What it holds and what it doesn't
It holds what to ask and how: the parts, the purpose and the appendix layout, so the request. It doesn't hold the
engine or its model, the endpoint, the cases, the seeds, the text cleanup, the execution or the canaries: those are
the trial's, the run's or the edge's. Its language is voted by its recipe's chunks (`docs/catalog.md`, "Languages").
Its model is in its chunks, and only its name says which (`agents/wip-variants.md`). A judge configuration is one of
purpose `judge`, and a judge pins its skeleton with an engine and seeds.

## Where the meanings parted at fcef71a
What is built since is marked so.

1. **Pinned factors, or a skeleton thread.** `docs/chatddx.md` ("Intended evolution of configurations") calls a
   configuration "a set of pinned factors kept on a skeleton thread". But a trial pins the skeleton, and the chunks a
   variation replaces are pinned by no trial: the recipe is provenance (`docs/factors.md`, "Recipe and compilation").
2. **What people write, or what is kept.** Researchers write recipes, and the catalog versions skeletons:
   - a recipe that compiles to the head's skeleton writes nothing: `Catalog.keep` answers "unchanged"
     (`src/chatddx/store/catalog.py`), and init-data does the same, so a configuration's versions needn't hold the
     recipe a person chose. Built: a new recipe is a new version (I2);
   - varying one part compiles the whole recipe with the running code (`src/chatddx/bench/seen.py:Seen.skeleton`), so
     after a change to the compiler a variation can differ from its edit where nothing was replaced, and the catalog's
     `varies`, which compares recipes, says nothing of it;
   - a configuration's language is voted by every compilation of its skeleton, whichever thread kept it
     (`src/chatddx/catalog/language.py:language_of`), and its title takes its edit's compilation, else the first
     stored (`src/chatddx/catalog/titles.py`). Built: the API gives its edit's recipe's language (I2);
   - a configuration is found by its request: `held_by` names the threads whose head is the skeleton, and a run's page
     links any thread with an edit that holds it (`src/chatddx/portal/runs.py:_version`), so two configurations can
     hold one request and either is shown. Built: `held_by` asks for the recipe too (I2); a run's page doesn't.
3. **Three levels.** A skeleton thread, a name that stands for its variants (`plan`), and what an edge holds, a
   variation of one (`agents/wip-variants.md`, "Configuration: three levels").
4. **The model.** The old configuration named no model. Today's names none either, but its chunks make it one model's,
   and only its name says which.
5. **Hand-written skeletons** are configurations to the catalog, with no recipe: nothing can vary one, and it is titled
   "generation skeleton 1a2b3c". No edge or data set writes one, only the store (`docs/factors.md`, "Skeleton
   provenance", whose take is to keep them). Decided: H1; built: titled "generation configuration 1a2b3c" (W1).
6. **Purpose and appendix layout** are a configuration's, and the catalog's `varies` compares them, but a variation
   replaces the nine parts only, so only a new configuration from a recipe sets them.
7. **Judge configurations** are listed apart by the API and the portal, and among the rest by the repl
   (`docs/bench.md`, "Outstanding"). Built: apart in the repl too (J1).
8. **A run** records its trial, so its skeleton, and is named by its variation's label. Which configuration and which
   edit it ran isn't recorded (`src/chatddx/ledger/run.py:RunStarted`), so a run of an unsaved variation links none
   (`agents/wip-portal.md`, "What the variation being tried leaves").
9. **What holds a configuration**, and which configurations use a component, need queries the catalog doesn't have
   (`agents/wip-portal.md`, "Open").

Other things the check turned up:
- **The configuration page's "a fork" link** takes the edit it was forked from as a thread's id
  (`src/chatddx/portal/templates/configuration.html`, `configuration.forked_from`), so it opens whatever thread has that
  number; the thread page resolves the edit first (`src/chatddx/portal/threads.py:thread_page`). Built: fixed.
- **The configuration page never offers a proposal**, since the thread page that does redirects a skeleton to it
  (`agents/wip-variants.md`).

## Options
Kept as they were put; the decisions are above.

### I. What a configuration's versions are
- **I1. Requests**, as now: a skeleton thread, the recipe each edit's provenance. Matches what trials pin, and keeps 2
  above.
- **I2. Requests with their recipes.** Still a skeleton thread, but an edit is written when its compilation differs
  from the head's even if its skeleton doesn't, so a configuration's versions hold every recipe chosen and the code
  that compiled it. Its language and title then read its own edits' compilations, not every compilation of its
  skeleton. Changes `Catalog.keep`, init-data, the catalog's languages and titles, and their tests; no migration.
- **I3. Recipes.** A recipe becomes a component with a digest, a configuration a thread of recipes, and its skeleton
  what the recipe compiles to, recorded by a compilation that names the recipe. What researchers write is what is
  versioned and varied. Costs a new kind (tiers 0 to 2), compilations of another shape, every reader of a
  configuration's skeleton going through its compilation, and a home for hand-written skeletons.

Decided: I2, with the refinement above.

### M. Whether a configuration is made for a model
- **M1. By its chunks**, as now: a configuration that uses a per-model chunk is made for that model, and its siblings
  for other models are variants (`agents/wip-variants.md`, V). What a configuration sends changes only by an edit.
- **M2. For none, as the old chatddx's.** The parts that depend on the model are asked for as levels and
  recommendations (`reasoning: off`, `sampling: recommended`), and texts by a name they have in every language. A
  configuration is compiled for a model and a language when it is paired with an engine and cases, the facts writing
  the literal chunks then, and the compilation keeps them. Per-model and per-language variants become compilations,
  a variation means the same on every model, and picking by the cases' language falls out. But compiling then takes
  the facts and a model; a corrected fact changes what a configuration sends next without an edit of it, though
  trials still pin what was sent; and it needs I3. The most change: factors, catalog, curation, bench and every edge.

Decided: M1.

### H. Hand-written skeletons
- **H1. Configurations without a recipe**, as now: only the store writes one, and nothing varies it.
- **H2. Not configurations**: every edit of a skeleton thread names a compilation, which the database could require.
- **H3. Written at the bench**, as a component, for a judge prompt written whole.

Decided: H1.

### J. Judge configurations
- **J1. The same kind, told apart by purpose**, and listed apart at every edge, the repl's `configurations` too.
- **J2. A kind of their own.**

Decided: J1.

### W. The word in the code
- **W1. "Configuration" at the edges, "skeleton" below**, as now, with the API giving the word beside the kind, and
  the titles and findings people read saying configuration.
- **W2. "Configuration" everywhere for the thread**, the catalog's docs and code included, and "skeleton" for the
  component only.

Decided: W1.

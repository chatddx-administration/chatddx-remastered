# Configurations: work in progress

What a configuration is in the factors, the catalog, the bench, its edges and the data sets, where the meanings part,
and options for settling it before variations and variants build on it (`agents/wip-variants.md`). Checked against the
code at fcef71a, and against the old chatddx's `docs/repl.md`, `docs/portal.md` and
`docs/research/a-new-datamodel.md` (chatddx-administration/chatddx at 504792c). Nothing below is built. "Decided"
means the user said so; "Take" is the agent's and still open.

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

## What a configuration is today

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

## Where the meanings part
1. **Pinned factors, or a skeleton thread.** `docs/chatddx.md` ("Intended evolution of configurations") calls a
   configuration "a set of pinned factors kept on a skeleton thread". But a trial pins the skeleton, and the chunks a
   variation replaces are pinned by no trial: the recipe is provenance (`docs/factors.md`, "Recipe and compilation").
2. **What people write, or what is kept.** Researchers write recipes, and the catalog versions skeletons:
   - a recipe that compiles to the head's skeleton writes nothing: `Catalog.keep` answers "unchanged"
     (`src/chatddx/store/catalog.py`), and init-data does the same, so a configuration's versions needn't hold the
     recipe a person chose;
   - varying one part compiles the whole recipe with the running code (`src/chatddx/bench/seen.py:Seen.skeleton`), so
     after a change to the compiler a variation can differ from its edit where nothing was replaced, and the catalog's
     `varies`, which compares recipes, says nothing of it;
   - a configuration's language is voted by every compilation of its skeleton, whichever thread kept it
     (`src/chatddx/catalog/language.py:language_of`), and its title takes its edit's compilation, else the first
     stored (`src/chatddx/catalog/titles.py`);
   - a configuration is found by its request: `held_by` names the threads whose head is the skeleton, and a run's page
     links any thread with an edit that holds it (`src/chatddx/portal/runs.py:_version`), so two configurations can
     hold one request and either is shown.
3. **Three levels.** A skeleton thread, a name that stands for its variants (`plan`), and what an edge holds, a
   variation of one (`agents/wip-variants.md`, "Configuration: three levels").
4. **The model.** The old configuration named no model. Today's names none either, but its chunks make it one model's,
   and only its name says which.
5. **Hand-written skeletons** are configurations to the catalog, with no recipe: nothing can vary one, and it is titled
   "generation skeleton 1a2b3c". No edge or data set writes one, only the store (`docs/factors.md`, "Skeleton
   provenance", whose take is to keep them).
6. **Purpose and appendix layout** are a configuration's, and the catalog's `varies` compares them, but a variation
   replaces the nine parts only, so only a new configuration from a recipe sets them.
7. **Judge configurations** are listed apart by the API and the portal, and among the rest by the repl
   (`docs/bench.md`, "Outstanding").
8. **A run** records its trial, so its skeleton, and is named by its variation's label. Which configuration and which
   edit it ran isn't recorded (`src/chatddx/ledger/run.py:RunStarted`), so a run of an unsaved variation links none
   (`agents/wip-portal.md`, "What the variation being tried leaves").
9. **What holds a configuration**, and which configurations use a component, need queries the catalog doesn't have
   (`agents/wip-portal.md`, "Open").

Other things the check turned up:
- **The configuration page's "a fork" link** takes the edit it was forked from as a thread's id
  (`src/chatddx/portal/templates/configuration.html`, `configuration.forked_from`), so it opens whatever thread has that
  number; the thread page resolves the edit first (`src/chatddx/portal/threads.py:thread_page`).
- **The configuration page never offers a proposal**, since the thread page that does redirects a skeleton to it
  (`agents/wip-variants.md`).

## Options

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

Take: I2. It keeps what researchers chose and the code that made the request, without a new kind, and trials keep
pinning skeletons. I3 if a configuration should be a recipe through and through, as M2 needs.

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

Take: M1. It keeps remastered's rule that what a configuration sends changes only by an edit, which is what lets a
study cite one; comparing across models comes from recording which configurations belong together
(`agents/wip-variants.md`, V). M2 if a configuration should be the unit compared across models by construction, and
facts may move what it sends.

### H. Hand-written skeletons
- **H1. Configurations without a recipe**, as now: only the store writes one, and nothing varies it.
- **H2. Not configurations**: every edit of a skeleton thread names a compilation, which the database could require.
- **H3. Written at the bench**, as a component, for a judge prompt written whole.

Take: H1, as `docs/factors.md` takes it, until someone needs to write one.

### J. Judge configurations
- **J1. The same kind, told apart by purpose**, and listed apart at every edge, the repl's `configurations` too.
- **J2. A kind of their own.**

Take: J1. A judge configuration is compiled, kept and varied as any other; only what reads it differs.

### W. The word in the code
- **W1. "Configuration" at the edges, "skeleton" below**, as now, with the API giving the word beside the kind, and
  the titles and findings people read saying configuration.
- **W2. "Configuration" everywhere for the thread**, the catalog's docs and code included, and "skeleton" for the
  component only.

Take: W1. The catalog is generic over kinds, and the word is the bench's.

## The work ahead
Once I and M are settled:
1. **The definition**, as suggestions: `docs/chatddx.md` ("Intended evolution of configurations": "a set of pinned
   factors kept on a skeleton thread"), `docs/catalog.md` ("Configurations and variations", "Recipes", "Terms") and
   `docs/factors.md` ("Recipe and compilation", "Judge").
2. **I2**: `Catalog.keep`'s "unchanged" and init-data's, the catalog's languages and titles by an edit's own
   compilation, their tests, and `docs/catalog-api.md`.
3. **The smaller things**: the "a fork" link, the repl listing judge configurations apart, and the word beside the
   kind in the API (W1).
4. **Then variations and variants** on the configuration settled here (`agents/wip-variants.md`), with what a run
   records of the configuration and the variation it ran (8 above).

## Questions for the user
- **I and M**: I2 and M1, or the old chatddx's shape, I3 and M2?
- **Pinned factors**: is the skeleton what a configuration pins, as the factors have it, or should its recipe's
  chunks be pinned too, by what runs it?
- **H and J**: H1 and J1?

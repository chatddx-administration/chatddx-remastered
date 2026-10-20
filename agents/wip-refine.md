# Refine: work in progress

A page in the portal where a researcher evolves configurations: a configuration and its lineage, the variations being
tried over it, run on the same cases at the same engine, and their scores side by side, so that the successful are
kept, the unsuccessful deleted and a configuration with several successful variations branched out
(`docs/chatddx.md`, "Intended evolution of configurations"). It is to a configuration's lineage what `/review` is to a
case (`agents/wip-review.md`) and `/translate` to a configuration's languages (`agents/wip-translators-view.md`).

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **It can be done.** The catalog models the workflow without objects of its own: forks, a fork's base, what it
   varies, proposals, titles and what a run varied (`docs/catalog.md`, "Configurations and variations"). What is
   missing is the page, the chunk editors, a few reads from the API, and a look over a chunk nobody has stored.
2. **Decided: the takes on E1 to E8** (see "The landscape"), the name, Refine, and the chunk editors first, apart
   from Refine. The order of the steps is suggested, and the agent's to change (see "Steps").
3. **Decided: the set's language is its cases'**, so that a variation's start over it is one run, never a run per
   language (see "What the docs hold it to").
4. **Steps 1, 2 and 2b are built** (see "Built"); what they leave is in each step's "What step N leaves". Step 1 is
   `agents/wip-portal.md`'s 5c ("Authoring", W1), and steps 2 and 3 build its C1 and C2 ("Comparing variations").
5. **Decided: researchers see model handles**, such as `qwen3-8b`, never engines, endpoints or a model's proper name;
   ops map each handle to one engine and one endpoint, and a handle always means its latest engine (`docs/chatddx.md`,
   "Target stack"; `docs/inventory.md`, "Endpoints"). Step 2b brings the project and the page there (see "Steps").

## What the researcher is here to do
From `docs/chatddx.md` ("Intended evolution of configurations", "Roles mentioned"):
- **Hand-edit chunks**: instructions, few-shot examples, prompts, outputs, sampling, reasoning, passthrough and
  toolsets. Translations are the translator's (`agents/wip-translators-view.md`), tools the developers'.
- **Try variations**: a configuration with parts replaced, seen before it runs.
- **Run them over the same cases under their model handles**, and read their scores side by side.
- **Keep the successful** as configurations, a fork or a new version of their own, and **delete the unsuccessful**.
- **Branch out** a configuration with several successful variations, and **delete** the configurations that don't
  work out.
- **Follow** what moved on under a configuration: its origin, its facts and model, and its chunks.

## What exists to build on
| To do | Built below the page | In the portal now | Missing |
|---|---|---|---|
| Try a variation | the look, `GET /api/threads/{id}/variation` | `/configurations/{id}`, `Variation.svelte`: a picker per part, lints, reach, the request | nothing |
| Hand-edit a chunk | new, fork, edit; `POST /api/components/check` | an editor per kind on its thread's page, and a new one from the Library (step 1) | nothing |
| A configuration from a recipe | `POST /api/threads` with `recipe`; `POST /api/recipes/check` | a form on `/configurations` (step 1) | nothing |
| A look over a chunk as typed | parts are taken by digest only; translations as typed are the one exception (`Translating.entries`, `POST /api/threads/{id}/translation`) | none | a part given whole (step 4) |
| Run variations | `POST /api/runs`, the worker | one variation at a time, from its page | several, over one set (step 3) |
| Read their scores | `GET /api/runs/{id}/scores`; `GET /api/runs/compared` | a run's page; Refine and `/runs/compare` (step 2) | nothing |
| Keep one | fork, edit, save by name | Save on the variation's page | a chunk and its configuration saved together, built for a judge only (`frontend/src/lib/scorer/rewriting.ts`; step 4) |
| A configuration's lineage | `GET /api/threads/{id}/lineage` (step 2) | Refine's lineage drawer (step 2); **Follow its origin** on a configuration's page | nothing |
| Delete | the `deleted` entry; `POST /threads/{id}/delete` takes any thread | **Restore** in the Library | **Delete** on a configuration (step 5) |
| Follow a chunk that moved on | `catalog.threads.behind` lists it | nothing | the bench follows facts and the model only (step 5) |

## What the docs hold it to
- **One hardware class per handle**: ops never expose a handle on two (`docs/chatddx.md`, "Target stack"), and
  comparing across handles is fine. Each column runs under its own model's handle, or under the one `model=` forces
  on every column.
- **Runs aren't pooled by the trial's digest alone**: a trial pins neither the execution nor what was observed
  (`docs/backlog.md`, "Aggregation"). The page shows means over shared items, with their count, and pools nothing.
- **No stored batch** (`agents/wip-portal.md`, "Comparing variations", decided): what goes together is the page's
  address, never a record.
- **A person's runs are their own** (`src/chatddx/bench/seen.py:Seen.runs`), **scored against the expectations they
  hold** (`docs/bench.md`, "What a person is scored against"): a researcher who holds none has empty columns.
- **A start is a run per language** (`docs/bench.md`, "Translations"), and comparing languages is comparing case sets:
  the set's language is its cases', never picked. A set whose tags or families pick cases in several languages is
  refused, to be narrowed. A variation whose translations don't cover its cases runs nothing over the set, and says so.
- **Judged views cost judge calls**, through the worker (`docs/runner.md`, "Judges").

## The page
A sketch, at a wide screen, in the review's layout: two columns are the main actors, the configuration being varied
and how its variations fare; the lineage is a drawer at the left, folded to a rail.

```
┌▲┬ lines-instructed · v3 of 3 ◀ ▶ ──────────┬ tag sample · seed 7 ───────────────────────────────────────┐
│L│ instructions  clinician            ✎     │              lines-instructed  +prompt=terse  lines-guided │
│i│ prompt        case        ▾        ✎     │ lines first  0.80 (9)          0.70 (9)       —            │
│n│ output        lines       ▾        ✎     │       recall 0.60 (9)          0.65 (9)       —            │
│e│ sampling      greedy      ▾        ✎     │                                                            │
│a│ model         gpt-oss-20b ▾        ✎     │ only here: 1 case                                          │
│g│ ▸ the request · lints · reach            │ only here: 1 case                                          │
│e│ [Try it]  tried: +prompt=terse           │ [Run 1 not run]  [Score 1 left]                            │
│ │ [Save] a fork of yours, "lines-terse"    │                                                            │
└─┴──────────────────────────────────────────┴────────────────────────────────────────────────────────────┘
```

- **Lineage**, a drawer at the left: the configuration's origin, up to the first, and every fork below it, indented
  by descent. Each says its label, what it varies from its base, whether it is behind, and its mean under the view
  sorted by; deleted ones are folded apart. Picking one makes it the configuration being varied.
- **The configuration**: its recipe part by part, a picker per part as the variation's page has, and, from step 4,
  each part's editor in place (✎). Under it the request, the lints and each scorer view's reach, folded; **Try it**,
  which adds the variation to the trying list; and saving, with the line saying where it goes.
- **How they fare**: a column per variation, the configuration's own first, then the trying list, then the forks;
  a row per scorer view with its mean over the items the columns share and their count; what isn't run or isn't
  scored, with **Run** and **Score**. A column's mean is over its runs at its handle's latest engine; its runs on
  earlier engines, or under a retired handle, are folded away under the handle, accessible and out of the mean.

The address keeps what is set: `/refine/{configuration}?model=…&tag=…&family=…&seed=…&head=…&try=…`, a `try` per
variation tried, its parts as `PART:DIGEST` joined by commas. `model=` is optional: a handle forced on every column,
each otherwise under its own model's. `/refine` leads to the person's first configuration, as `/translate` does, and
the nav says Refine.

## The landscape
Decided: the take on each.

### E1. What the page is around
- **(a)** One configuration and its lineage, the variation tried in the middle.
- **(b)** An experiment: a set of cases, an endpoint and scorers, with variations of several configurations. It brings
  back a stored grouping, which was decided against.
- **(c)** One part across configurations, which needs a reverse lookup the catalog doesn't have (`agents/wip-portal.md`,
  "What holds a configuration").

Take: (a). The workflow is per configuration, and the catalog organises configurations by lineage.

### E2. What makes two variations comparable
- **(a)** Runs picked by hand, side by side (C1, `/runs/compare?run=…`).
- **(b)** A set kept in the address: the cases by tag or family, a seed, and optionally a handle forced on every
  column. Each variation is matched to its runs by skeleton and handle, at the handle's latest engine; one without
  a run offers **Run**. Runs on the handle's earlier engines are grouped under it and folded away.
- **(c)** Every run of each skeleton, whatever its cases, which "Aggregation" rules out.

Take: (b), with (a) reachable from the runs page.

### E3. Several variations at once
- **(a)** Several chunks picked for one part, a run each, one part at a time (C2).
- **(b)** A trying list: each variation tried joins a list kept in the address, and the list is run together.
- **(c)** Every combination, the explosion `docs/chatddx.md` avoids.

Take: (b), with (a) as a way to fill the list.

### E4. Editing a chunk where it is tried
- **(a)** On the chunk's own page, saved, then picked: two places.
- **(b)** In place: the look takes a part given whole, as it takes translations as typed, and nothing is stored until
  the variation runs, which stores what it ran without a thread, or is saved: the chunk as a version of the person's
  own or a fork, then the configuration holding it, as a judge's texts are saved.
- **(c)** In place, each change saved as a version of the chunk: writes as it is typed, and versions pile up.

Take: (b).

### E5. Showing the lineage
- **(a)** A tree, drawn as an indented list: each with its label, what it varies, whether it is behind, its means on
  the set, and **Delete** or **Restore**.
- **(b)** A flat leaderboard of every version and fork.
- **(c)** Links only.

Take: (a), sorted within a level by a view.

### E6. What "successful" is read from
- **(a)** Every view of every scorer that applies, a row each: its mean over the shared items, with their count.
- **(b)** One view picked as the yardstick.
- **(c)** A stored objective.

Take: (a), sorted by a view as in (b); nothing beyond means until "Aggregation" is planned.

### E7. Deleting
- Configurations: **Delete** in the lineage and on the configuration's page.
- An unsaved variation is a digest: nothing to delete, and its runs stay in the ledger.
  - **(a)** The page shows the runs of what is on the trying list or saved only.
  - **(b)** A catalog entry that hides a run, which nothing writes yet (`agents/wip-portal.md`, C4).
  - **(c)** All of them.

Take: (a).

### E8. Where it sits
- **(a)** `/configurations/{id}` grows into it.
- **(b)** A page of its own beside it, in the review's layout, the configuration's page staying the plain read.

Take: (b), `/refine/{configuration}`.

## Steps
Each step leaves the portal whole. Step 2 doesn't depend on step 1, and the two can be built side by side.

### Step 1: the chunk editors, on the threads' pages
`agents/wip-portal.md`'s 5c, under its W4 to W9: a form per kind built from shared pieces, checked as it is typed by
`POST /api/components/check`, saving said where it goes, and a conflict shown with what was typed kept.
- **An editor per chunk kind**, in `frontend/src/lib/editors/`, picked by `src/chatddx/portal/threads.py:_editor` as
  the appendix's, the expectation's and the translations' are:
  - instructions: its role, and its text in `TextSegments.svelte` (moved from `lib/scorer/` to `lib/editors/`), with
    the inserts the kind allows (`src/chatddx/factors/request.py:INSERTS_BY_KIND`);
  - prompt: its purpose, and its segments, slots and inserts as chips;
  - few-shot: its messages, each a role and a text, added, removed and moved;
  - output: its contract (native, a tool with its name and description, or text), its JSON Schema as a JSON field the
    server checks, its schema ops, and its guidance as a text;
  - sampling: recommended or not, and a field per setting, `stop` as a list, the key for the token limit;
  - reasoning: a level, or an effort, a budget and `chat_template_kwargs` as a settings table;
  - passthrough: its body, as a settings table;
  - toolset: its tools picked among the shipped ones, its guidance and its rounds.
- **A new chunk** from the Library, per kind: **Write a new one**, an empty form of that kind, saved as a new thread.
- **A new configuration from a recipe**, on `/configurations`: a picker per part among the chunks the person sees, a
  model, a purpose and an appendix layout, checked as it is picked, and saved by `POST /api/threads` with `recipe`.
  `POST /api/components/check` takes components only: it gains a recipe, compiled as a new configuration's is, with
  nothing written.
- **Tests**: `src/chatddx/portal/test/test_library.py`, each kind's editor props; vitest for each form's component as
  built from what is typed, and its canonical form where a kind has one (`texts.ts:textOf`); and a browser test: a
  prompt edited on its page, saved as a version, and a configuration made from a recipe holding it.

### Step 2: the API's reads, and the page read only
- **The API**, suggested to `docs/api.md` as `AGENT` blocks:
  - `GET /api/threads/{id}/lineage`: the first origin and every fork below it, each with its thread, label, owner,
    base, what it varies (`catalog.threads.divergence`), whether it is behind, and whether it is deleted.
  - `GET /api/runs/compared?run=…`: runs side by side over the items they share: each scorer view's value per item
    and run, each view's mean per run over the shared items, their count, and the cases only some of them hold.
    Sensitive in nothing it gives, as a run's scores aren't.
- **The page** (`src/chatddx/portal/refine.py`, `templates/refine.html`): the lineage, the configuration with its
  versions stepped through, and how they fare on the set, the configuration's own and each fork's latest runs by
  skeleton and handle, at each handle's latest engine, compared by `GET /api/runs/compared`.
  Nothing is written from it yet.
- **`/runs/compare?run=…`** (C1), the same table over runs picked on the runs page.
- **Tests**: the test World's scripted runs gain runs to compare, over the same cases at `qwen3@fake`: `lines`, and
  `lines` with a part set, and `lines-guided`, a fork, named in `src/chatddx/test/world.py`
  (`agents/wip-portal.md`, "Comparing variations", Open: none of them sets a part yet); `test_threads.py` and
  `test_runs.py` for the API's; `src/chatddx/portal/test/test_refining.py` for the page's.

### Step 2b: model handles, and the set by them
Decided by the user, after step 2 (see "Start with this", 5): what a researcher sees of models, engines and
endpoints, and Refine's set in those terms.
- **A handle** is the name of a model's thread, such as `qwen3-8b`: the weights a recipe pins are a version of it, and
  new weights put under it by ops make its configurations behind their model (`docs/catalog.md`, "What has moved on").
  Take: nothing new is stored; the World names its model records by handle, as the test World does already.
- **Resolving a handle**: its thread's head, the weights it holds now, served by exactly one endpoint, whose engine is
  the handle's latest. None or several is ops' error: the inventory check reports weights served at several endpoints
  at init-data, as a worker starts and at the engine import, and a researcher's run, look or scoring is refused saying
  it is ops'. A configuration whose weights are behind its handle is refused until followed; a hand-written one runs
  under the handle named (see "Taken from the backlog", "Picking an endpoint for a model").
- **The World**: the inventory's `configurations` and `[judge]` name handles. The engine import names a server's
  model by the server's name, the handle ops give it, and its endpoint and engine server@host as now. The sample's
  and kompismoln's models are renamed to their handles, and the test World's bare Qwen3 gets weights of its own,
  `qwen3-8b-bare`, as two endpoints serving one model's weights are now ops' error.
- **The API**: `endpoint` gives way to `model`, a handle, in the look and in a start, for a hand-written configuration
  only; the look says the handle it runs under, or why it can't run; a run says its handle and whether it ran at its
  latest engine; running again runs under the run's handle; `GET /api/models` lists the handles, each with what refuses
  it, if anything. `GET /api/endpoints` stays, the World's for ops.
- **The portal**: no endpoint is picked or shown to a researcher. The variation page's endpoint picker goes, the home
  page's, the review's run form's and the judge form's pick a handle, runs show their handle, and the nav's Endpoints
  becomes Models.
- **Refine's set**: `/refine/{configuration}?model=…&tag=…&family=…`, no `endpoint=` or `language=`; columns by
  skeleton and handle, each under its own model's handle unless `model=` forces one on every column; a column's mean
  over its runs at the handle's latest engine, and its runs on earlier engines, or under a retired handle, folded away
  under the handle, accessible.
- **`/runs/compare`**: runs show their handle; runs under one handle on different engines are said to be grouped
  under it rather than like for like.
- **Kept**: scripted runs name endpoints, as they are the fake's (`docs/scripted.md`); the repl was kept so too, and
  then brought to handles (see "Built", step 2b). A person's judge picks a handle and pins its latest engine, until
  "Judges name a model" changes the judge's kind, since built (`agents/wip-judge-handle.md`).
- **Tests**: the inventory check's finding; loading by handle; the bench's resolving, refusals and running again;
  the API's look, start, runs and models; the portal's pages; the import's naming; vitest for the variation page's
  logic without endpoints.

### Step 3: the trying list, and running it
- **Try it** adds the variation looked at to the list, in the address. Several chunks picked for one part fill it with
  one variation each (C2). Each tried variation is a column, said **not run** until it is.
- **Run**: a confirmation from a look per variation (`GET /api/threads/{id}/variation`): the runs it starts, what each
  sets, what the gate refuses and why, the cases, and each scorer view's reach; then a `POST /api/runs` per variation
  over the set, one run each. A variation that replaces the model runs under its handle, a column like any other, and
  with `model=` every column runs under that handle. A handle that doesn't resolve is refused as ops' error, and
  weights the handle no longer holds are behind, to be followed first.
- **While they run**: each column follows its runs (`frontend/src/lib/runs/`), and the comparison reloads once they
  are done. **Score** queues what is left to score.
- **Save** a tried variation: a fork, or a version of the person's own, as the variation's page saves it, which then
  joins the lineage.
- **Tests**: vitest for the list kept in the address (`frontend/src/lib/refine/`); a browser test on the test World
  with its fake: two variations tried, run together, compared, and one saved as a fork.

### Step 4: the editors in place
- **The API**: a part given whole, beside by digest, in the look and in a run: `POST /api/threads/{id}/variation`,
  taking what `Varying` takes with any part as a digest or a chunk, and `NewRun.parts` likewise. A run stores the
  chunk it was given, without a thread, as it stores what it runs.
- **On the page**: each part's editor from step 1 opens in place, and the look follows what is typed, as the
  translator's page follows its entries. A variation tried with a part typed is kept in the page, not the address,
  until it runs, when the address names the chunk's digest.
- **Saving**: the chunk as a version of the person's own, or a fork, or a new thread, then the configuration that
  holds it, as an edit or a fork (`rewriting.ts:rewritten`, generalised from a judge's texts to every part).
- **Related**: `docs/backlog.md`, "A run names the skeleton its look gave", matters most for a part typed in place.
  Take: moved into this plan when step 4 starts.
- **Tests**: the API's look and run with a part given whole, the run storing it; a browser test: a prompt changed in
  place, the request following, run, and saved with the configuration.

### Step 5: delete, follow and notes
- **Delete and restore** in the lineage and on the configuration's page, through `POST /threads/{id}/delete` and
  `/restore`.
- **Follow its origin** from the lineage, as the configuration's page offers it.
- **Following a part that moved on** (see "Taken from the backlog"): the bench follows each recipe part that moved on,
  not only `/facts` and `/recipe/model` (`src/chatddx/bench/following.py:_moved`), offered per part in the lineage and
  on the configuration's page. The lineage takes back the references of each head whose threads have moved on, pruned
  until a page reads them (step 2, "Reduced").
- **Notes** (see "Taken from the backlog", decided): an edit carries an optional note, a new column of `catalog.edit`
  (a migration, `docs/migrations.md`); the API's edits and forks take it, saving offers it, and the versions show it
  with who wrote the version and when. Who changed an entry, a label or a language, and when, are shown where they
  are shown now.
- **Tests**: the catalog's and the bench's for following a chunk and for notes; the API's; the page's.

## Built

### Step 1: the chunk editors, and a configuration from a recipe
- **The API**, suggested to `docs/api.md` as an `AGENT` block: `POST /api/recipes/check`
  (`src/chatddx/api/world.py:check_recipe`), a recipe checked as making a configuration of it would make it, with
  nothing written: each part a stored chunk of that part and the model a stored model
  (`src/chatddx/bench/components.py:_stored_parts`, which `new` shares), compiled against the facts about its model
  now, giving the digest of the skeleton and its lints. `Bench.check` takes a recipe. A route of its own rather than
  `POST /api/components/check` taking one, since a recipe has no kind to tell it from a component by.
- **An editor per chunk kind** (`frontend/src/lib/editors/ChunkEditor.svelte`, a form per kind in
  `frontend/src/lib/editors/chunk/`) on the thread's page of every chunk but a translations chunk
  (`src/chatddx/portal/threads.py:_editor`, `_chunk`), as planned, with these differences:
  - `TextSegments.svelte` is imported from `lib/scorer/`, where the judge's texts have it, rather than moved;
  - a settings table, shared by passthrough and reasoning (`SettingsTable.svelte`), reads a value as JSON where it is
    JSON and else as a text, and shows a text that would read as JSON quoted;
  - a toolset's tools are offered one per digest, as the variation's pickers offer them
    (`frontend/src/lib/variation/logic.ts:choicesOf`), since a giftbag's forks share their origins' digests;
  - **As JSON**, beside every form, edits the whole chunk, for what a form doesn't say.

  A text kind's language is offered from the head's, and sent with the save (`writing.ts:saved` takes a language). A
  number or a schema that doesn't read is sent as typed, and the check refuses it with why (`chunks.ts:numberOf`).
- **A new chunk** from the Library: **Write a new one** on each chunk kind's tab but translations', to
  `/library/new?kind=…` (`threads.py:beginning`, `templates/begun.html`), an empty form of the kind
  (`chunks.ts:blank`), saved as a new thread.
- **A new configuration from a recipe**, on `/configurations` for the purpose shown
  (`frontend/src/islands/Recipe.svelte`, `frontend/src/lib/editors/recipe.ts`): a picker per part, each offered as the
  variation's pickers offer them (`frontend/src/lib/variation/logic.ts:choicesOf`), the appendix layout folded, checked
  once its required parts are picked, and saved by name, leading to its page.
- **Tests**: `src/chatddx/api/test/test_kinds.py`, a recipe checked and refused;
  `src/chatddx/portal/test/test_library.py`, a chunk's editor props, the Library's new chunk, and the recipe form's
  props; vitest for `chunks.ts` and `recipe.ts`; `test_browser.py`, alice's prompt changed on its page, a sampling
  chunk written from the Library, and a configuration made from a recipe of both; and by hand on the sample World in
  Chromium, each kind's form holding its chunk as it is ("Nothing to save: it holds this already").

#### What step 1 leaves
- **A newline as a stop sequence** isn't typed in the sampling form, which takes one a line; **As JSON** takes it.
- **An insert's before and after texts** aren't shown by the text editor, as for a judge's texts; **As JSON** shows
  them.
- **The recipe form's prompt picker** lists every prompt, whatever its purpose; the check refuses one made for the
  other.
- **A recipe that compiles to a skeleton a configuration holds already** isn't said so by the form.
- **A toolset's tool at an earlier version** is kept and shown by its digest; the tools offered are the latest.

### Step 2: the API's reads, and the page read only
- **The API**, suggested to `docs/api.md` as `AGENT` blocks:
  - `GET /api/threads/{id}/lineage` (`src/chatddx/api/threads.py:lineage`, `Bench.lineage` in
    `src/chatddx/bench/following.py`), as planned, with each thread's `origin` to draw it by. Its origin has moved on
    only when the person sees the origin, and a deleted thread is there only for its owner.
  - `GET /api/runs/compared?run=…` (`src/chatddx/api/runs.py:compared`), up to twenty runs, as planned: the items
    every trial holds, by case and replicate (`src/chatddx/factors/trial.py:Trial.item_keys`, which the ledger's
    expected items read too), each view's values per run and item and its mean per run, under each run's latest score
    under each scorer, and cases by digest, as the runs give them.
- **The page** (`src/chatddx/portal/refine.py`, `templates/refine.html`; the `refine` island remembers the drawer):
  - **Its columns**: the version shown, then each other configuration of its lineage, the person's own first.
    Configurations holding one skeleton share a column ("lines-instructed = archive/lines-instructed"), since a fork
    that varies nothing holds its origin's; a deleted one has none.
  - **A column's run** is the person's latest reaching its skeleton (`GET /api/runs?reaching=`) at the set's
    endpoint's engine, in the set's language, and, when tags or families narrow the set, over its cases only.
  - **The set**: the endpoint, the one serving the model when only one does, else picked; the language, the
    configuration's own unless picked; tags from a form, and families from the address. Step 2b replaces the set and
    the columns by handle.
  - **The lineage** is sorted within a level by the view `by` names (`scorer:view`), by default the first with a
    value, each configuration with its column's mean.
  - A judge configuration isn't found here: a judge isn't run on cases.
- **`/runs/compare?run=…`** (C1; `src/chatddx/portal/runs.py:comparing`, `templates/compare.html`): the runs ticked
  on the runs page or a configuration's page (`macros.html:runs_table`, whose checkboxes join a form of their own), a
  mean per view and run, and, under the view `by` names, each item; runs at different engines or in different
  languages are said not to be like for like, which step 2b changes.
- **Tests**: the test World's scripted runs gain `instructed`, `instructed-greedy` and `guided`
  (`src/chatddx/test/world.py:COMPARED`), over `crlf` and `bom` at `qwen3@fake`, `lines-instructed`'s lineage rather
  than `lines`', which has no fork; each answers both cases alike, since a run doesn't send its cases in the order a
  scripted run lists them. `test_threads.py`, a lineage; `test_runs.py`, runs compared; `test_scripted_runs.py`, the
  three; `src/chatddx/portal/test/test_refining.py`, Refine and comparing runs; and by hand in Chromium on `ran`.

#### What step 2 leaves
- **The set's seed** isn't held: step 3 runs with it, and runs are matched without it, their replicates by index.
- **A variation's runs** aren't a configuration's column: a column is found by the configuration's skeleton, and the
  trying list (step 3) shows a variation's.
- **Families** narrow the set from the address only; the form offers tags.
- **Means only**, over the shared items, as "Aggregation" (`docs/backlog.md`) waits.
- **A lineage costs a few queries per thread**: its title and what it varies.

#### Reduced
A pass over the branch against main (`agents/reduce.md`):
- **Pruned**: the lineage's `depth`, which the page counts from the origins, and `behind`, which no page read and step
  5 brings back; the counts of `GET /api/runs/compared`, counted from its values; the runs Refine counted as gone
  elsewhere.
- **Consolidated**: `Bench.check` and `new` match on the component; the portal's own-first sorting
  (`src/chatddx/portal/pages.py:own_first`), its `named` and `mean` macros (`macros.html`), the editors' field class
  (`frontend/src/lib/utils.ts:FIELD`), the recipe's parts (`logic.ts:PARTS`, with the optional parts from the
  server), and a chunk's language and tools given with its editor (`src/chatddx/portal/threads.py:_chunk`).
- **Kept**: Refine's set and the matching of a column's run stay in the page rather than `GET /api/runs`.

After step 2b, the set it left out: the note on a set over several languages pruned, as language stays silent and
the comparison's items show what isn't shared; a column's reasons it can't be worked out and that its weights are
behind one `said`; a column that can't be worked out matched as any, finding nothing (`src/chatddx/portal/refine.py`).

### Step 2b: model handles, and the set by them
- **Handles** (`src/chatddx/bench/model.py:Handle`; `src/chatddx/bench/seen.py`): `Seen.handle`, the one live model
  thread holding the weights at any version; `Seen.handle_named`; `Seen.served`, the one endpoint serving the
  handle's weights now, through `Inventory.serving`, whose refusals now say they are ops' to mend; `Seen.latest`;
  `Seen.under`, a run's engine's handle and whether it is the latest. `Seen.at` takes an endpoint only from the repl
  and scripted runs, refuses weights behind their handle ("follow it first"), and runs a hand-written configuration
  under the handle named. A run is described by its handle (`Seen.described`).
- **Running again** (`src/chatddx/bench/runs.py:again`): under the run's handle at its latest engine, refused as
  ops' error or as behind.
- **The World**: `configurations` and `[judge]` name handles, resolved as the data set is planned
  (`src/chatddx/curation/plan.py`, `under`), no longer checked as the inventory loads; the inventory check's
  `endpoint.model_shared` for weights served at several endpoints, at init-data, as a worker starts and at the import
  (`src/chatddx/inventory/check.py`). The import names a server's model by the server's name, once for a handle on
  several hosts, and refuses other weights under it (`src/chatddx/importers/o11n.py:engines_toml`). The Worlds'
  models are renamed to handles, and the test World's bare Qwen3 has `qwen3-8b-bare`, a revision of its own.
- **The API**, unlike the plan, names the handle `under` in the look and in a start, as the look's query already has
  `model`, the recipe part: the look says `model`, the handle it runs under, or `problem`; a run says `model` and
  `latest`; `GET /api/models` lists the handles with their weights, latest engine, whether a typed case runs under
  them and what refuses them.
- **The portal**: the variation page picks a handle for a hand-written configuration only and says what it runs
  under; the home page, the review's run form and the judge form pick a handle; the composer, the runs tables, a
  run's page and `/runs/compare` show a run's handle, "an earlier engine" when it is; the nav's Endpoints is Models
  (`/models`, `src/chatddx/portal/world.py`).
- **Refine** (`src/chatddx/portal/refine.py`): `model=` forces a handle on every column; a column is the skeletons a
  configuration sends the set's cases as, a language each (`Seen.languages`), under its handle; its run is the
  latest at the handle's latest engine, and its earlier engines' runs are folded under it; a column says why it can't
  be worked out, or that its weights are behind its handle.
- **`/runs/compare`** says when runs under one handle ran at different engines, grouped under it.
- **Tests**: `test_serving.py`, the check's finding; `test_judges.py`, `test_plan.py`, judges and configurations by
  handle; `test_o11n.py`, a handle on two hosts; `test_seen.py`, running again; `test_world.py`, the handles and a
  shared model's; the API's, the portal's and the repl's tests without endpoints; vitest for the variation's address.
- **The repl**, after step 2b (`src/chatddx/repl/`), suggested to `docs/repl.md` as `AGENT` blocks: the cell is
  dropped. The shell holds a variation (`Repl.variation`) that runs under its model's handle, at the endpoint the
  handle resolves to, and `under MODEL`, the API's `under`, names the handle a hand-written configuration runs under
  (`Repl.under`), kept while hand-written configurations are used. `on` and `cell` are gone, so the model changes by
  `set model` only, which compiles first and refuses a model that refuses a pick. A change says
  `variation: LABEL × HANDLE`, or why it can't run, and lints only what can run; the prompt reads nothing from the
  store; runs are titled by handle, as `Seen.described` titles them; `reasoning` heads each model by the handles served
  under it. The test that held every package but the repl to the word "cell" went with it. Tests:
  `src/chatddx/repl/test/`, a hand-written configuration run under a handle among them.

#### What step 2b leaves
- **Scripted runs** name endpoints.
- **A retired handle reads as ops' error**: no endpoint serving its weights is said alike either way.
- **A set over several languages** is neither said nor refused: its columns' runs in different languages share no
  items, which the comparison's items show; step 3 refuses a start over it.
- **A Refine column compiles its configuration's translations** to find its skeletons, each time the page is shown.
- **The Models page shows facts as they are**, a model's proper name among them.

## Open
- **Others' runs**: a person compares their own runs only. A collaborator's runs of a shared configuration aren't
  offered.
- **How many runs a confirmation starts before it warns**, with `settings.RUNS_PER_DAY` runs a day
  (`agents/wip-portal.md`, "Comparing variations", Open).
- **Several runs of one variation on the set**: the latest is compared and the others folded; whether replicates in
  separate runs ever pool waits for "Aggregation".

## Taken from the backlog

### Edit history: who, when and why
Who changed an entry, a label or a language, and when, shown; and why an edit was made, kept.

Decided: an edit may carry an optional note, stored with it as a commit message is; what changed stays derived from the
references.

- **Who changed an entry or a language isn't shown.** Every row records who wrote it and when, but for these only
  what holds now is shown.
- When an entry, a label or a language was written isn't given, nor who wrote a label or a language:
  `Reader.entries` gives an entry's writer only.
- **Why an edit was made isn't stored.** It can be worked out by comparing consecutive versions' references.
- Why an edit was made isn't stored.

### Following a part that moved on
A configuration offered the new version of a chunk of its recipe, as it is offered its facts' and its model's.

- **Only the facts and the model are followed.** The catalog lists every part of a configuration's recipe whose
  thread has moved on (`src/chatddx/catalog/threads.py:behind`), but the bench follows `/facts` and `/recipe/model`
  only (`src/chatddx/bench/following.py:_moved`), so a new version of a chunk, a translator's translations among them,
  reaches a configuration only by a variation that picks it, saved.

### Picking an endpoint for a model
Built by step 2b: a handle resolves to exactly one endpoint, or it is ops' error.

Decided: a handle resolves to exactly one endpoint, or it is ops' error, so no run waits for an endpoint to be named,
the variation page's endpoint picker goes, and a judge's handle resolves as a run's: a handle that resolves to no
endpoint or several is reported at init-data, as a worker starts and at the engine import, and refused to a
researcher as ops' error. It replaces the decision that a run is refused until its endpoint is named, and the one
that a look for no endpoint gives the model's findings alone.

- **A look that can't run has no findings**, and says why (`problem`); the repl's `show` shows no lints either.
- **A model that moved on is followed to its head whether or not an endpoint serves it**; `at` says so afterwards.

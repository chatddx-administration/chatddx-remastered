# Refine: plan

A page in the portal where a researcher evolves configurations: a configuration and its lineage, the variations being
tried over it, run on the same cases at the same engine, and their scores side by side, so that the successful are
kept, the unsuccessful deleted and a configuration with several successful variations branched out
(`docs/chatddx.md`, "Intended evolution of configurations"). It is to a configuration's lineage what `/review` is to a
case (`agents/wip-olofs-view.md`) and `/translate` to a configuration's languages (`agents/wip-translators-view.md`).

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **It can be done.** The catalog models the workflow without objects of its own: forks, a fork's base, what it
   varies, proposals, titles and what a run varied (`docs/catalog.md`, "Configurations and variations"). What is
   missing is the page, the chunk editors, a few reads from the API, and a look over a chunk nobody has stored.
2. **Decided: the takes on E1 to E8** (see "The landscape"), the name, Refine, and the chunk editors first, apart
   from Refine. The order of the steps is suggested, and the agent's to change (see "Steps").
3. **Nothing is built.** Step 1 is `agents/wip-portal.md`'s 5c ("Authoring", W1), and steps 2 and 3 build its C1 and
   C2 ("Comparing variations").

## What the researcher is here to do
From `docs/chatddx.md` ("Intended evolution of configurations", "Roles mentioned"):
- **Hand-edit chunks**: instructions, few-shot examples, prompts, outputs, sampling, reasoning, passthrough and
  toolsets. Translations are the translator's (`agents/wip-translators-view.md`), tools the developers'.
- **Try variations**: a configuration with parts replaced, seen before it runs.
- **Run them over the same cases at the same engine**, and read their scores side by side.
- **Keep the successful** as configurations, a fork or a new version of their own, and **delete the unsuccessful**.
- **Branch out** a configuration with several successful variations, and **delete** the configurations that don't
  work out.
- **Follow** what moved on under a configuration: its origin, its facts and model, and its chunks.

## What exists to build on
| To do | Built below the page | In the portal now | Missing |
|---|---|---|---|
| Try a variation | the look, `GET /api/threads/{id}/variation` | `/configurations/{id}`, `Variation.svelte`: a picker per part, lints, reach, the request | nothing |
| Hand-edit a chunk | new, fork, edit; `POST /api/components/check` | a chunk's thread page, read only; `TextSegments.svelte` for a judge's texts | an editor per part (step 1) |
| A configuration from a recipe | `POST /api/threads` with `recipe` | none | a form (step 1) |
| A look over a chunk as typed | parts are taken by digest only; translations as typed are the one exception (`Translating.entries`, `POST /api/threads/{id}/translation`) | none | a part given whole (step 4) |
| Run variations | `POST /api/runs`, the worker | one variation at a time, from its page | several, over one set (step 3) |
| Read their scores | `GET /api/runs/{id}/scores`, a run at a time | a run's page | runs side by side (step 2) |
| Keep one | fork, edit, save by name | Save on the variation's page | a chunk and its configuration saved together, built for a judge only (`frontend/src/lib/scorer/rewriting.ts`; step 4) |
| A configuration's lineage | `catalog.threads.forks`, `origin`, `divergence`, `proposal` | "Forked from", and **Follow its origin** | the forks, which the API doesn't give (step 2) |
| Delete | the `deleted` entry; `POST /threads/{id}/delete` takes any thread | **Restore** in the Library | **Delete** on a configuration (step 5) |
| Follow a chunk that moved on | `catalog.threads.behind` lists it | nothing | the bench follows facts and the model only (step 5) |

## What the docs hold it to
- **No comparison across hardware**: each hardware class is its own cage (`docs/chatddx.md`, "Target stack"). A
  variation that replaces the model goes to the endpoint serving it, another engine.
- **Runs aren't pooled by the trial's digest alone**: a trial pins neither the execution nor what was observed
  (`docs/backlog.md`, "Aggregation"). The page shows means over shared items, with their count, and pools nothing.
- **No stored batch** (`agents/wip-portal.md`, "Comparing variations", decided): what goes together is the page's
  address, never a record.
- **A person's runs are their own** (`src/chatddx/bench/seen.py:Seen.runs`), **scored against the expectations they
  hold** (`docs/bench.md`, "What a person is scored against"): a researcher who holds none has empty columns.
- **A start is a run per language** (`docs/bench.md`, "Translations"), so a set of cases in two languages gives a
  variation two runs (see "Open").
- **Judged views cost judge calls**, through the worker (`docs/runner.md`, "Judges").

## The page
A sketch, at a wide screen, in the review's layout: two columns are the main actors, the configuration being varied
and how its variations fare; the lineage is a drawer at the left, folded to a rail.

```
┌▲┬ lines-instructed · v3 of 3 ◀ ▶ ──────────┬ on qwen3@fake · tag sample · seed 7 ──────────────────────┐
│L│ instructions  clinician            ✎     │              lines-instructed  +prompt=terse  lines-guided │
│i│ prompt        case        ▾        ✎     │ lines first  0.80 (9)          0.70 (9)       —            │
│n│ output        lines       ▾        ✎     │       recall 0.60 (9)          0.65 (9)       —            │
│e│ sampling      greedy      ▾        ✎     │ in sv        2 runs folded                                 │
│a│ ▸ the request · lints · reach            │ only here: 1 case                                         │
│g│ [Try it]  tried: +prompt=terse           │ [Run 1 not run]  [Score 1 left]                           │
│e│ [Save] a fork of yours, "lines-terse"    │                                                           │
└─┴──────────────────────────────────────────┴───────────────────────────────────────────────────────────┘
```

- **Lineage**, a drawer at the left: the configuration's origin, up to the first, and every fork below it, indented
  by descent. Each says its label, what it varies from its base, whether it is behind, and its mean under the view
  sorted by; deleted ones are folded apart. Picking one makes it the configuration being varied.
- **The configuration**: its recipe part by part, a picker per part as the variation's page has, and, from step 4,
  each part's editor in place (✎). Under it the request, the lints and each scorer view's reach, folded; **Try it**,
  which adds the variation to the trying list; and saving, with the line saying where it goes.
- **How they fare**: a column per variation, the configuration's own first, then the trying list, then the forks;
  a row per scorer view with its mean over the items the columns share and their count; the runs in another language,
  at another engine or over other cases folded apart; what isn't run or isn't scored, with **Run** and **Score**.

The address keeps what is set: `/refine/{configuration}?endpoint=…&tag=…&family=…&seed=…&head=…&try=…`, a `try` per
variation tried, its parts as `PART:DIGEST` joined by commas. `/refine` leads to the person's first configuration, as
`/translate` does, and the nav says Refine.

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
- **(b)** A set kept in the address: an endpoint, the cases by tag or family, and a seed. Each variation is matched to
  its runs by skeleton at the set's engine; one without a run offers **Run**.
- **(c)** Every run of each skeleton, whatever its cases, which "Aggregation" rules out.

Take: (b), with (a) reachable from the runs page. Runs at another engine than the set's endpoint's are listed apart.

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
  skeleton (`Seen.runs(reaching=…)`) at the set's endpoint's engine, compared by `GET /api/runs/compared`. Nothing is
  written from it yet.
- **`/runs/compare?run=…`** (C1), the same table over runs picked on the runs page.
- **Tests**: the test World's scripted runs gain runs to compare, over the same cases at `qwen3@fake`: `lines`, and
  `lines` with a part set, and `lines-guided`, a fork, named in `src/chatddx/test/world.py`
  (`agents/wip-portal.md`, "Comparing variations", Open: none of them sets a part yet); `test_threads.py` and
  `test_runs.py` for the API's; `src/chatddx/portal/test/test_refining.py` for the page's.

### Step 3: the trying list, and running it
- **Try it** adds the variation looked at to the list, in the address. Several chunks picked for one part fill it with
  one variation each (C2). Each tried variation is a column, said **not run** until it is.
- **Run**: a confirmation from a look per variation (`GET /api/threads/{id}/variation`): the runs it starts, what each
  sets, what the gate refuses and why, the cases, and each scorer view's reach; then a `POST /api/runs` per variation
  over the set, a run per language each. A variation that replaces the model runs at the endpoint serving it, and its
  column is apart.
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
  on the configuration's page.
- **Notes** (see "Taken from the backlog", decided): an edit carries an optional note, a new column of `catalog.edit`
  (a migration, `docs/migrations.md`); the API's edits and forks take it, saving offers it, and the versions show it
  with who wrote the version and when. Who changed an entry, a label or a language, and when, are shown where they
  are shown now.
- **Tests**: the catalog's and the bench's for following a chunk and for notes; the API's; the page's.

## Open
- **Others' runs**: a person compares their own runs only. A collaborator's runs of a shared configuration aren't
  offered.
- **How many runs a confirmation starts before it warns**, with `settings.RUNS_PER_DAY` runs a day
  (`agents/wip-portal.md`, "Comparing variations", Open).
- **Several runs of one variation on the set**: the latest is compared and the others folded; whether replicates in
  separate runs ever pool waits for "Aggregation".
- **The set's cases in two languages**: the page folds the runs in a language other than the configuration's own
  apart; a column per variation and language, or the set held to one language, would do instead.

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

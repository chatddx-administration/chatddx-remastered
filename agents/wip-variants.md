# Variants: work in progress

What a variant is in the catalog today, why it rests on names alone, what recording it would take, and which variant
a variation belongs to. What a variation is, is `agents/wip-variations.md`'s, which is to be started first (see its
"Start here"). Checked against the code at fcef71a, and its quotes again at f7fd2b0, once configurations and requests
were settled. Nothing of the options below is built: a variant is still known by its name only. "Decided" means the
user said so; "Take" is the agent's and still open.

## Where variants come from
In the old chatddx a configuration was "what to ask and how … A configuration names no model" (`docs/repl.md` at
504792c in chatddx-administration/chatddx, "A few words first"), and compiling turned its parts into settings for the
model of the stack it was paired with, `compile(configuration, case, stack facts, seed)`
(`docs/research/a-new-datamodel.md` at 504792c, "2.4 Compile"). The research note behind it asked for "settings that
can be varied one at a time and compared across models … each setting lives in one place and means the same thing
whatever it is paired with". A configuration could extend another and follow it.

Remastered took the model out of compiling: facts "never reach the wire themselves but write literal chunks before
compilation so no digest depends on them" (`docs/facts.md`). So a sampling or reasoning chunk is written for one
model, init-data writes one per model, and a configuration that uses one is made per model: that is where per-model
variants come from. Per-language ones come from texts written per language.

Decided, when configurations were settled: a configuration is made for a model by its chunks, so what it sends changes
only by an edit, and its siblings for other models are variants. Put aside: a configuration for no model, its
model-dependent parts asked for as levels and recommendations (`reasoning: off`, `sampling: recommended`) and its
texts by a name they have in every language, compiled for a model and a language when paired with an engine and
cases. Variants would have become compilations and a variation would mean the same on every model, but a corrected
fact would change what a configuration sends without an edit of it, and it needed recipes as components of their own.

## The words

### Variant: one meaning, read from names
Every doc that defines it agrees: a thread made for a language, a model or both, from one record of a data set, and
named after them (`docs/curation.md` and `docs/repl.md`, "Terms"). The record, such as `[recipe.plan]` with its
description and tags, is what the variants are of, and the catalog has nothing that stands for it. The shadcn
components' `variant` prop is a styling word and unrelated. Whether the word stays is `agents/wip-variations.md`'s
(W).

### Configuration: three levels
- **A skeleton thread**, its versions requests with their recipes (`docs/catalog.md`, "Terms").
  `plan (en, Qwen/Qwen3-8B-AWQ)` is one, and the sample makes 31 of them from 10 recipes.
- **A name that stands for its variants**, as people pick one: the repl's `use plan` and its `configurations`, "a row
  per configuration name and language"; the home page, where "picking an endpoint picks the configuration made for its
  model" (`agents/wip-portal.md`, "The home page").
- **What an edge holds**: "the configuration is a variation of a configuration thread" (`docs/repl.md`, "The cell"),
  and `TriedVariation` is "a configuration, or a variation of it being tried" (`docs/bench-api.md`).

### They cross
A variant is a sameness: this configuration is that one made for another language or model. It is meant to hold the
research question fixed, since the request follows the case's language (`docs/catalog.md`, "Languages") and sampling
and reasoning follow the model's facts. Only names record it. A variation is a deliberate change
(`agents/wip-variations.md`), and the two cross.

Init-data makes a variation per variant: `plan-shown (en, Qwen/Qwen3-8B-AWQ)` forks `plan (en, Qwen/Qwen3-8B-AWQ)`,
and nothing but its name ties it to `plan-shown (en, mistralai/…)`. And the edges disagree on which variant a
variation belongs to:
- **The repl holds it by names.** The cell keeps the configuration's name as given and each part by the name it was set
  by, and picks both again for a new endpoint's model (`src/chatddx/repl/choosing.py:_again`). Its variation is the
  name's, `plan+reasoning=off`, whatever the model.
- **The API, the portal and the catalog hold it by digest.** It is one variant's, labelled from the parts' titles:
  `plan (en, Qwen/Qwen3-8B-AWQ)+reasoning=off (Qwen/Qwen3-8B-AWQ)`. So one variation gets another run name by edge,
  and the island's link to "the configuration made for this endpoint's model" drops what was picked
  (`frontend/src/islands/Variation.svelte`).
- **Saved, it is one thread's.** `save plan-off` on a Mistral endpoint makes a new version of the person's `plan-off`
  made on Qwen, rather than a variant of it.

## Variants, checked against the code
The earlier version of this file holds, with these corrections:
- **Init-data** names texts `NAME (LANGUAGE)`, even when they are written in one language only, per-model chunks
  `NAME (MODEL)` and recipes `NAME (LANGUAGE, MODEL)`, and takes each part of a recipe made for (L, M) by trying
  (L, M), (L), (M) and neither, in that order (`src/chatddx/curation/plan.py:_named`, `_pick`). Judges keep plain
  names; a judge takes its recipe's variant for the model the World's endpoint for it serves.
- **The bench** reads names with the engine's model only, not every model the facts know
  (`src/chatddx/bench/seen.py:Seen.thread`), and `NotFound.per_model` lists names by a string prefix, not by
  `made_for`. Scripted runs read names through it too (`src/chatddx/scripted/run.py`).
- **The repl's** `configurations` table groups by base, language and owner, with the models in a column
  (`src/chatddx/repl/listing.py:_grouped`); its names know the facts' models (`shell.py:_per_model`).
- **The island** takes any trailing parenthesis as what a chunk is made for, so `clinician (sv)` makes a group `sv`
  beside the models' groups, and a title ending in `(earlier)` makes one too
  (`frontend/src/lib/variation/logic.ts:madeFor`). The home page takes any configuration whose name holds the
  endpoint's model, as a substring (`frontend/src/islands/Home.svelte:fitting`).
- **The API** parses no names, but gives every listed thread its language, a configuration's its head's recipe's,
  and the word for its kind (`src/chatddx/api/threads.py:thread_of`); the portal's templates show the language and
  the frontend doesn't read it.
- **Any name that looks like one is one**, and `NAME LANGUAGE` is looser: any last word of two or three small letters
  reads as a language when the whole name isn't found, so `plan for icu` is `plan for` in `icu`
  (`catalog/variants.py:language_of`). Alice's `native (sv, …)` being a variant is tested
  (`src/chatddx/bench/test/test_seen.py`).
- **Each reader knows other models**: the bench the engine's, the repl the facts', the configuration page the
  endpoints', init-data the served models the facts know, and the frontend none.
- **Renaming breaks it** for the archive's threads, which only the archive can rename; a person who renames a giftbag
  fork stops it being a variant, and init-data leaves it alone.
- **The model, in part.** The facts tell which models' recommendation a skeleton's sampling is, which may be several,
  not which model a sampling chunk was made for (`src/chatddx/facts/lint.py:_sampled_for`); greedy says nothing.
- **Nothing records a model or a variant.** Entries are name, description, tag, owner, collaborator, deleted and
  language, and a language entry is a family's only. A component's language is kept on its digest
  (`catalog.language`), for the kinds that hold text; sampling and reasoning have none.

Other things the check turned up:
- **Two functions are named `language_of`**: the catalog's, of a digest, and `catalog/variants.py`'s, of a name, which
  is the one `chatddx.catalog` exports.

## The work ahead
Solidifying (`AGENTS.md`, "Staging") means built, described in `docs/`, and this file removed. Here that is:
1. **Recording a variant** (see V): the catalog's model, its migrations, init-data writing it, and every reader above
   reading it in place of the name: the bench's `Seen.thread` and `NotFound.per_model`, the repl's completion, listing
   and cell, scripted runs, the API's threads and their filters (`chatddx openapi > frontend/openapi.json`), the
   configuration page, the island's pickers and the home page. `catalog/variants.py` goes, or keeps only what names a
   variant for people.
2. **Which variant a variation belongs to** (see L): whether every edge holds a variation by names, as the repl does,
   and what saving one keeps.
3. **Picking by the cases' language** (see P), at every edge.
4. **Loaded stores**: the names init-data already wrote, and people's giftbag forks under them, moved onto what is
   recorded when init-data runs again.
5. **Tests**: those that read variants today (`catalog/test/test_variants.py`, `bench/test/test_seen.py`,
   `repl/test/test_choosing.py`, `test_listing.py`, `test_commands.py`, `portal/test/test_varying.py`,
   `curation/test/test_plan.py`, `test_judges.py`, `test_init.py`, `test/test_sample.py`,
   `frontend/src/lib/variation/logic.test.ts`), and `nix/test.nix`, which finds a configuration by its whole name.
6. **The smaller things**: the island's link to another model's variant keeping what was picked, and one label for one
   variation whatever the edge.

## Options

### V. What records a variant
- **A. Names, guarded.** Qualifiers are read only on the archive's threads and their forks. Cheap; a person's
  `draft (sv)` stops being a variant; renames and grouping stay as they are.
- **B. Entries naming what it is a variant of, and its model**, written by init-data and by the bench; the language
  read from the catalog, where it already is. Names become people's. A text value needs a tier-2 migration only (the
  entry fields' check); a variant-of that names a thread needs a column, tier 0 too.
- **B2. The name is the group, the model an entry.** Variants share their record's plain name, `plan`, and are told
  apart by their language, which the catalog records for texts and votes for configurations, and a `model` entry, as
  appendices share names and are told apart by their vignettes. Init-data names threads plainly and writes the model
  on per-model ones, and recognises its records by kind, name, language and model. The bench picks by (name, model,
  language) among the person's own, else the shared, as names already pick; `save plan-off` on a Mistral endpoint keeps
  Mistral's variant of `plan-off` rather than a new version of Qwen's. One new entry field, at tier 2; renaming the
  group renames each variant.
- **C. Derived** from compilations, languages and the facts. No new data, but a heuristic, a walk over every
  configuration, and the facts can name several models for one sampling, or none.
- **D. A handle per group**, as cases have families: the record as a catalog subject with its own name, description,
  tags and owner, and each variant bound to it with its model. It matches the data set's record one to one, and what
  people mean by a configuration when they pick one; the most machinery: a table and its tiers, the catalog's
  functions and the API's.

The model is kept on the thread, not on the digest as a language is: two models' recommended sampling can be one
chunk, one digest made for both.

Take: B2. It records the one thing the catalog can't know, the model, uses what it records already, the language, and
keeps the name as people's handle on the group, which is how the repl, the home page and the island speak of it. D if
a group needs its own description, sharing or deleting.

### L. Which variant a variation belongs to
- **L1. A thread's**, as the API, the portal and the catalog have it. The repl's picking again stays the cell's
  convenience.
- **L2. A group's.** A variation is a name with parts set by name (`plan+reasoning=off`), picked per model and
  language when it runs, and saving it keeps a variant for every model its parts have one for, as init-data's
  `fork_of` does. One save makes several threads, whose versions then go their own ways.
- **L3. Tried as a group's, kept as a thread's.** Every edge holds a variation by names and picks it for the endpoint,
  as the repl's cell does: the island picks again itself, or the API takes parts by name beside digests. Saving keeps
  the variant for the endpoint's model and the variation's language under the name given, which with B2 is the group.

Take: L3. The repl does it already, picking by the cases' language (P1) needs it, and one save keeps one thread.

### P. Picking by the cases' language
- **P1. A run per language**, each under the variation's variant in that language; a language it has no variant in is
  said and left out.
- **P2. Refused**: cases in several languages are asked for apart.
- **P3. As now**: the configuration's language, and `language.mixed` warns.

Take: P1, in the bench, so that every edge has it: a variation and its cases give the runs to start. The docs lean to
it (`docs/catalog.md`, "Languages"; `docs/repl.md`, "Outstanding"; `docs/curation.md`, "Picking a variant by the
case's language").

### S. Where the solidified docs go
- **S1. In the docs that speak of them**: recording in `docs/catalog.md`, making in `docs/curation.md`, picking in
  `docs/bench.md`, and the code in `docs/catalog-api.md`.
- **S2. `docs/variants.md`**, a module of its own.

Take: S1. In the code it is `chatddx.catalog.variants`, part of the catalog, and its readers are in every layer.

## Questions for the user
- **The takes** B2, L3, P1 and S1.
- **Whose variants?** Are variants only what a data set makes, or may a person make their own, such as a Swedish
  variation of their configuration?
- **Forks.** Should a person's fork of a variant stay a variant of the same thing, made for the same model, as a
  giftbag fork is today by its name?
- **Names for people.** Under B2 a variant's name is its group's, and the lists show its language and model beside
  it. Under B, should init-data still write them into the name, for people to read?

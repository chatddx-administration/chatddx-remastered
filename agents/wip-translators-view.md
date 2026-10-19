# The translators' view: work in progress

A page in the portal where a translator carries a configuration into another language: its texts beside their
translations, what is missing and what no longer has a source, the request in both languages, and saving the
translations with a version of the configuration that holds them. It is to configurations what `/review` is to cases
(`agents/wip-review.md`).

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **It can be done.** Translations are a chunk like any other (`docs/factors.md`, "Translations"), which the bench
   writes as any thread (`docs/bench.md`, "Writes for the person"), and the variation page already picks one as a part.
   What is missing is a way to see which texts a configuration holds and which of them its translations leave out,
   an editor for a translations chunk (5c's, `agents/wip-portal.md`, "Authoring"), and the page around them.
2. **Decided: the takes on T1 to T11** (see "The landscape"), and F1 (a) (see "Found on the way").
3. **Steps 1 to 4 are built** (see "Built"); what is left is in each step's "What step N leaves".

## What the translator is here to do
- **See what a configuration holds to translate**: its instructions, few-shot examples, prompt, the output's guidance
  and the titles and descriptions of its schema, the descriptions of its tools and its answer function, and its
  appendix layout, each text in its place.
- **Translate them**, into a language its translations cover or a new one, and **vet** what is there: the sample's
  Swedish was drafted, not written by a translator (`docs/backlog.md`, "The data's stage, said in code").
- **Keep up with the source**: a translation is keyed by its source text, so a source edited since leaves its
  translation unused and the text untranslated (`docs/backlog.md`, "Languages").
- **See what it makes**: the request as written and as translated, side by side.

## What exists to build on
| To do | Built below the page | In the portal now | Missing |
|---|---|---|---|
| The texts of a recipe | `chatddx.factors.request:texts`, by part, in order | none | a route (step 1) |
| What its translations leave out | the compilation's refusal, listing every text | the variation page's languages, over cases | per configuration, whatever its cases (step 1) |
| The request translated | `compile_request(…, into)` | none | with translations as typed (step 1) |
| A translations chunk | new, fork, edit; `POST /api/components/check` | its thread's page, read only | the entries' editor (step 3) |
| Saving texts and a configuration together | the bench's writes | `frontend/src/lib/scorer/rewriting.ts:rewritten`, for a judge's texts | for translations (step 3) |
| Running it in a language | `POST /api/runs`, a run per language | the variation page | nothing (T7) |

Data sets do this already when they load: `texts-<language>.toml` groups its entries by the record they translate,
refuses an entry whose text that record doesn't hold, and init-data prints `[untranslated]` per recipe
(`src/chatddx/curation/plan.py`).

## The page
A sketch, at a wide screen, in the review's layout: two columns are the main actors, the configurations and the
request are drawers at the sides, folded to a rail.

```
┌▲┬ written in en ─────────────────────────┬ into sv ─────────────────── 2 missing ┬R┐
│C│ instructions · clinician                │                                       │e│
│o│ You are assisting a physician in an …   │ Du bistår en läkare på en …           │q│
│n│ output · lines                          │                                       │u│
│f│ List the plausible diagnoses, one per…  │ [                             ] ✗     │e│
│i│ layout                                  │                                       │s│
│g│ ⏎⏎Appendices:⏎                          │ ⏎⏎Bilagor:⏎                           │t│
│s│ ── not used here (1) ── List the plau…  │ Lista de tänkbara diagnoserna, …  ↑   │ │
│2│ [Save] a new version of yours, and of lines-guided                              │ │
└─┴─────────────────────────────────────────┴───────────────────────────────────────┴─┘
```

- **Configurations**, a drawer at the left: the generation configurations the person sees, each marked per language
  its translations go into, or its families' languages are in, as complete or by how many texts are missing. Judge
  configurations are listed apart (T11).
- **The texts**: by part, each in its place, the translation beside it, a missing one empty and marked, and the
  entries no text of the configuration uses listed after them, each offered for the missing text it is closest to.
- **Request**, a drawer at the right: the request as written and as translated, a text without a translation as
  written, marked.

The address keeps what is picked: `/translate/{configuration}?into=sv&head=EDIT`.

## The landscape
Questions that change what is built, each with its options. Decided: the take on each.

### T1. Who translates
`docs/chatddx.md` ("Roles mentioned") names no translators; `docs/factors.md` ("Translations") names researchers, as
translators, the principal authors of translations.
- **(a)** Researchers, as `docs/factors.md` says; Z1 later says which panes a role sees.
- **(b)** A Translators role, suggested to `docs/chatddx.md` for a human to write.
- **(c)** Clinicians too, who may know the medical terms best.

Decided: (a). The address and the page's title name the activity, not a person: `/translate`, "Translate".

### T2. What the page is around
- **(a)** A configuration and a language: what is missing and what is unused is relative to a recipe.
- **(b)** A translations chunk's thread page. Which texts it should cover needs every configuration that holds it, a
  reverse lookup the catalog doesn't have (`agents/wip-portal.md`, "Open", "What holds a configuration").
- **(c)** (a) as the page, and its editor of entries reused as a translations chunk's `/threads/{id}` editor, as the
  review built 5d's editors for the thread pages.

Decided: (c).

### T3. What a row is
A text is a string as compiling translates it: a segment between slots and inserts, each title and description of a
schema, a tool's description, a part of the appendix layout.
- **(a)** A table by part, each text in its place: segments with their slots and inserts as chips, a schema's text
  under its property's path, few-shot examples by turn; whitespace shown (⏎ ·), and a warning where a translation's
  leading or trailing whitespace differs from its source's, as the layout's `"\n\nAppendices:\n"` depends on it.
- **(b)** The request as rendered, with the texts editable in place.

Decided: (a). Each text's place is found by the page in the chunks' JSON, so `chatddx.factors.request`, solidified,
keeps its translating functions as they are; `texts` gives the part and the order.

### T4. A source changed under its translation
- **(a)** The missing texts, and apart from them the entries no text of the recipe uses, carried over by hand.
- **(b)** As (a), and each missing text offered the closest unused entry, with what differs word by word, marked to
  be checked (gettext's fuzzy entries).
- **(c)** Translations keyed by place rather than text, against `docs/factors.md`'s gettext model.

Decided: (b). Unused entries are kept on saving unless removed, since a chunk can serve several configurations: the
sample's `sample` holds the texts of ten chunks, and one recipe names it. With it, a lint on a configuration whose
translations leave a text untranslated, whatever cases are given, which closes `docs/backlog.md`'s "Languages",
"Translations are keyed by their source text" (see "Built").

### T5. Saving, and whose configuration is translated
- **(a)** As a judge's texts are saved (`rewriting.ts:rewritten`): the translations as a version of the person's own,
  a fork, or a new thread, then the configuration as a version or a fork that holds them; the line says where both go.
  A researcher takes a translator's work by picking the chunk, others' offered as `owner/name`.
- **(b)** The translations alone, and a configuration following a part that has moved on (F3).
- **(c)** The archive's: vetted in the portal, exported back to `texts-<language>.toml` (`docs/backlog.md`,
  "Exporting data sets").

Decided: (a) now; (b) suggested to the backlog; (c) stays there.

### T6. Seeing what it makes
- **(a)** A route that stores nothing: a configuration, the translations into a language as typed, and the language
  in; the request translated out (reduced from its texts, the unused entries and the request as written too). One
  implementation, `compile_request`, and nothing sensitive, as no case is in it.
- **(b)** The substitution ported to TypeScript, as `texts.ts:asked` placed guidance.

Decided: (a), built in step 1.

### T7. Trying it on cases
- **(a)** The review's run form, on the families in the language.
- **(b)** The variation page, which runs a configuration in every language its cases are in already.

Decided: (b) first. Vignettes aren't translated, so comparing languages is comparing case sets, and there is no case
to compare an answer with across them.

### T8. The languages offered
The languages the translations go into, then the families' languages the person sees that they don't, then any tag.
A regional tag isn't covered by its language's (`docs/backlog.md`, "Languages": `Seen.languages` compares tags
whole), so families tagged `sv-SE` want `sv-SE` translations, which the page says where it happens. A configuration
whose own language is unknown is said so; correcting the language of one's own chunks (decided in
`docs/backlog.md`, "Languages") can ride along.

### T9. A few-shot answer in JSON
- **(a)** One row, edited as JSON, checked that its keys and its fixed values are as the source's.
- **(b)** Translated by its texts when compiled, a change to the factors (`docs/backlog.md`, "Translating JSON few-shot
  answers").

Decided: (a). The sample's few-shot answers aren't JSON.

### T10. Drafts from a model
A draft asked of an endpoint holds no case, so nothing sensitive, but it is an exchange outside the ledger, and what it
drafts is guessed. Decided: not now.

### T11. Judges
- **(a)** Generation configurations only; judge configurations listed apart, saying a judge runs in no language (F2).
- **(b)** A judge in a language: the judge's form compiles its configuration into it, and the judge pins that
  skeleton.

Decided: (a).

## Found on the way
- **F1. A translated schema's title hid the plan.** The sample's Swedish translates `management_plan_v1` to
  `handläggningsplan_v1`, and a run's page and the review's record drew an answer as a management plan only when the
  run's skeleton's schema was titled `management_plan_v1`. Options: (a) decide by the title as written, from the
  run's compilation's recipe; (b) the compiler leaves a schema's root title untranslated, a change to the factors and
  the data. Decided: (a), built in step 1.
- **F2. A judge's translations are never used**: nothing compiles a judge configuration into a language, so the
  sample's Swedish of `output.verdict` and `output.grade` is unreachable. Suggested to `docs/backlog.md`, "Languages".
- **F3. A configuration doesn't follow its translations' new version**: the bench follows a configuration's facts and
  model only. Suggested to `docs/backlog.md` as "Following a part that moved on" (T5 b).

## Backlog nearby
Ride along, moved here:
- **`docs/backlog.md`, "Languages"**: translations an edit detached, closed by the lint of step 1 and the page's
  unused entries (T4).
- **`docs/backlog.md`, "Titles"**: a translated skeleton's title doesn't say its language, closed by step 4.

Related, staying in the backlog: "Translating JSON few-shot answers" (T9 b), "Exporting data sets" (T5 c), "The
data's stage, said in code" (vetting the sample's Swedish), "Edit history: who, when and why" (a translator's note on
an edit), "Languages" (regional tags, correcting a wrong language, judges and languages) and "Missing tests" (the
texts of `lines-guided` translated into sv, which step 1's tests read).

## Steps
1. **What a configuration is in a language**, built (see "Built"): the route of T6, the lint of T4, and F1.
2. **The page, read only**, built (see "Built"): `/translate/{configuration}`, the configurations' drawer with their
   marks, the texts in their places, the unused entries, and the request both ways.
3. **Writing**, built (see "Built"): the entries' editor, the closest unused entry offered, checked as typed, and
   saving as T5 (a); the translations chunk's thread page uses the same editor.
4. **A new language**, the languages offered (T8), and a translated skeleton titled with its language, built (see
   "Built").

Tests, as the review's: the pages by `TestClient` on `ran`; the routes in the API's tests; vitest for the page's logic;
and a browser test of a translator's flow on the test World: `lines-guided`'s Swedish, a text left out by an edit of
its instructions, carried over from its unused entry, saved, and the variation page running its Swedish cases again.

## Built
### Step 1: what a configuration is in a language
- **The bench**: `Seen.translation`, a variation's skeleton translated into a language by its translations or by
  entries given as typed, a text without a translation left as written. Refused for a hand-written configuration, and
  into its own language.
- **The lint**: `translations.missing`, on a configuration's look (`src/chatddx/bench/seen.py:missing`): for each
  language its cases are in and can't be sent, how many are left out and why, and for each other language its
  translations go into and leave a text untranslated, whatever cases are given, why, as compiling into it says.
- **The API**: `POST /api/threads/{thread}/translation` (`src/chatddx/api/threads.py:translation`), a variation as
  the look takes it, a language and the entries into it as typed in; the request translated, with placeholders for
  the case and the model, out. Nothing is stored, and nothing in it is sensitive.
- **F1**: `Seen.answers`, the title of a skeleton's answer's schema as written: a translated skeleton's is its
  compilation's recipe's. A run's page and the review draw a management plan by it.
- **Tests**: `src/chatddx/bench/test/test_translating.py` and `src/chatddx/api/test/test_translating.py`, on the test
  World's `lines-guided` and its Swedish.

#### What step 1 leaves
- **The lint needs an endpoint**, as every lint of a look does: a look rendered for none has no findings
  (`agents/wip-refine.md`, "Picking an endpoint for a model"). The route needs none.
- **A judge configuration isn't linted** for its translations, which nothing uses (F2).
- **A text two parts hold** is listed under each, with one entry for both.

### Step 2: the page, read only
- **`/translate`** opens the person's first generation configuration, their own first; **`/translate/{configuration}`**
  takes `into` and `head` (`src/chatddx/portal/translate.py`, `templates/translate.html`). Translate is second in the
  nav, after Review.
  - **Configurations**, a drawer: the generation configurations the person sees, each marked per language its
    translations go into or a family they see is in, ✓ or the number of texts missing (`untranslated`); judge
    configurations apart, linking their pages, as a judge runs in no language (T11).
  - **The texts**: written in its language, its translations' thread, and the languages offered, those its
    translations go into and its families' (step 4 adds a new one); by part, each text beside its translation or
    marked missing; the entries no text of it holds after them, folded when there are more than five.
  - **Request**, a drawer: the request as written and as translated, side by side, message by message, and the rest of
    the request folded.
  - A hand-written configuration, a judge's, and one with no language to go into each say so instead.
- **The island** (`frontend/src/islands/translate.ts`, `frontend/src/lib/translate/`): each text's places, found in its
  part's chunks' JSON, the toolset's tools included (`translate.ts:places`): a few-shot turn, a schema's property
  path, the answer tool's description, an insert's surroundings, the layout's; whitespace shown at a text's edges and
  each line's end (`visible`), and a translation whose edges aren't its source's said so (`unlike`); and in the
  translated request, each text without a translation marked where it is sent (`marked`). The server gives the texts
  by part, in the order they are sent, and the translations chunk; what each text is translated as and which entries
  are unused the island works out (`translate.ts:entriesInto`, `unusedOf`). Without scripts the page says where the
  entries are, on the translations' thread page.
- **Shared with the review**: its panes and drawers are macros (`templates/macros.html`: `pane`, `drawer`, `rail`,
  `upright`, `opened`), and a drawer is remembered per viewer by `frontend/src/lib/drawers.ts:remembered`.
- **Tests**: `src/chatddx/portal/test/test_translating.py` on `curated`; `frontend/src/lib/translate/translate.test.ts`;
  and by hand on the sample World in Chromium, light, dark and narrow: about 0.14 s a page, marks included.

#### What step 2 leaves
- **Marking is by the text**: an untranslated text is marked wherever it occurs in the translated request, so a title
  that is also a `$defs` name, as `IndividualDiagnosis` is in the sample's plan, is marked as the name too.
- **The marks count every text for a configuration without translations**, as for one whose translations miss them:
  `plan` shows `sv 34`.
- **A chunk shared by several configurations**: what is unused is unused by the configuration shown, and may be another
  one's; the sample's `sample` shows 50 to `free-text-guided`, folded.

### Step 3: writing
- **The texts, edited in place** (`frontend/src/lib/translate/Texts.svelte`, a row each by `Entry.svelte`): each
  translation a field that grows with what it holds, an empty one marked; and how many are missing, as typed.
- **The closest unused entry** (T4 b, `translate.ts:closest`): a missing text is offered the unused entry of the text
  most like it, at least half its words in common, with what differs word by word; starting from it fills the field and
  says to check it, until the field is changed.
- **Unused entries are kept** unless left out, each with **Leave it out**, as another configuration may use them.
- **Checked as typed**, a moment after each change: the translations as they would be saved, by
  `POST /api/components/check` (`translate.ts:entriesOf`, `translationsOf`: what is typed, the unused kept, and the
  chunk's other languages as they are), and the request translated with what is typed, by
  `POST /api/threads/{thread}/translation`, which the request drawer follows (`live.svelte.ts`).
- **Saving** (T5 a, `frontend/src/lib/translate/saving.ts:saved`), by `frontend/src/lib/editors/writing.ts:written`,
  which every editor's saving goes through since the second reduction: the
  translations as a version of the person's own, a fork of another's, or a new thread named after the configuration
  when none holds them; then the configuration holding them, as a version of the person's own at its latest, else a
  fork from the edit shown; a part already held isn't written again. The line says where both go
  (`translate.ts:savedTo`), and the page reloads into what was saved.
- **A translations chunk's page** edits its entries, language by language, each kept or left out, checked as typed
  and saved as any thread is (`frontend/src/lib/translate/TranslationsEditor.svelte`; `src/chatddx/portal/threads.py`).
- **Tests**: `test_translating.py`, what the page and a translations thread's page are given to save with;
  `translate.test.ts`, the closest entry, what is saved and where it goes; and `test_browser.py`, `lines-guided`'s
  instructions edited, their Swedish started from the unused entry, changed, saved, and its Swedish cases sent
  translated again.

#### What step 3 leaves
- **Saving is two writes, not one**: if the configuration's is refused after the translations', their version stays,
  the person's own and unused, as a judge's texts do (`agents/wip-review.md`, "What step 6 leaves").
- **A conflict is said, not resolved**: when a thread has moved on since the page loaded, saving is refused and what
  was typed stays on the page, but nothing offers the version after the latest, as `Saving` does for one thread.
- **A JSON few-shot answer** is one entry, edited as text: nothing checks yet that its keys and fixed values are its
  source's (T9 a).
- **A new language** is step 4's: the editor writes into the languages offered.

### Step 4: languages
- **The languages offered** (T8, `src/chatddx/portal/translate.py`): those its translations go into, solid, then those
  only the cases the person sees are in, dashed, then any other by its tag, typed beside them ("Translate into it"),
  which opens the page in it with every text missing; saving writes it into the translations beside the others
  (`translate.ts:translationsOf`). A tag that isn't one, or the configuration's own, is refused with the error page.
- **A regional tag said where it happens** (`_regional`): cases the person sees in `sv-SE` are said not to be sent by
  translations into `sv`, and cases in `en-GB` not to be sent as written by a configuration written in `en`, since a
  tag is compared whole (`Seen.languages`).
- **An unknown own language is said so**, with why: its texts' chunks have none, or not the same one.
- **A translated skeleton's title says its language** (`src/chatddx/catalog/titles.py:_derive`): its recipe's
  description, then ", in sv", suggested to `docs/catalog.md` as an `AGENT` block; what `docs/backlog.md`'s "Titles"
  held of it moved here.
- **Tests**: `test_translating.py`, the languages offered, a new one, and the regional notes; and
  `src/chatddx/catalog/test/test_titles.py`, a translated configuration titled with its language.

#### What step 4 leaves
- **Correcting a language** (`docs/backlog.md`, "Languages": decided, a person may correct the language of a text only
  their own threads hold) didn't ride along: it is a write of the bench's, and the page only says when a
  configuration's own is unknown.
- **The drawer's marks** cover the languages its translations go into and its cases are in, not one typed: a new
  language shows there once saved.

### Reduced again
After step 4, by the user's pick of five from what the steps had added:
- `missingOf`, unused since step 3, gone.
- The translation route gives the translated request alone; `Seen.translation` gives the skeleton; the bench's
  `Translation` and the API's `TranslatedText` and `Translation` gone, and the page works out the rest from the
  texts and the chunk it is given.
- One write: `writing.ts:written`, a version of the person's own, a fork, or a new thread, which `saved`, a judge's
  texts and translations all go through; `rewriting.ts`'s own gone.
- No page drawn twice: the server no longer draws the texts and the request beneath the island.
- One code: `translations.incomplete` folded into `translations.missing`, both messages ending in the refusal
  compiling gives, suggested to `docs/bench.md`.

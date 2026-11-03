## Compose

Compose is where researchers write a configuration from its building blocks, its texts and settings, the evolution of
configurations (`docs/chatddx.md`, "Intended evolution of configurations").

Drafted: `/compose/{id}` (`src/chatddx/portal/compose.py`; `src/chatddx/portal/test/test_compose.py`) is where a
configuration is written and saved, and `/compose` leads to the first in the list. In its address is the variation's
query (`schemas.Varying`, its parts, `head`, `under`, `tag`).

- **Configurations**, always shown: the person's own of generation, by name, as Review runs a case under
  (`src/chatddx/portal/pages.py:configurations`), each fork under the one it was forked from where that is listed too,
  as Review's branches are (`src/chatddx/portal/compose.py:_forks`); no archive's.

- **The configuration**: its name, with **Show in the Library** across from it, as Review's case is; its versions by
  link; **Update** it where it is behind what it was made from; and its island (`frontend/src/islands/compose.ts`),
  which writes its chunks in place rather than picking them:

  - **Its texts**: a tab in its own language with the chunks that hold text, an output's and a toolset's guidance among
    them, and a tab for each language it is translated into, one at a time (`frontend/src/lib/compose/Texts.svelte`). As
    a text is typed, `POST /api/threads/{id}/drafts` says the texts the draft holds and carries each translation over to
    the text it changed into, in place and in order (`src/chatddx/factors/request.py:remapped`).
    - **Translating**: a language's tab pairs the prose, its instructions, few-shot messages, prompt and guidances, a
      row per text between its slots and inserts, the text on the left, editable, and its translation on the right, the
      text its placeholder (`frontend/src/lib/compose/Paired.svelte`). The slots and inserts are the text's, laid out on
      both sides and changed in its own tab. A translation carried over to a text that changed is marked to be looked
      over till it is typed in or said to read right, held by the page alone; one shared with another part says so
      (`frontend/src/lib/compose/Said.svelte`).
    - **Schemas and tools**, folded: the answer's schema and the tools as they are, beside a list of the texts they
      hold, to translate; neither is changed there. What else holds text, the appendices' layout, is listed below it.
    - Its settings are left out while translating.

  - **Its settings**: the chunks that hold no text, by what each decides rather than by its fields
    (`frontend/src/lib/compose/Settings.svelte`), with what the model's facts work out of them
    (`src/chatddx/portal/compose.py:_facts`):
    - **Model**, picked, saying whether its facts work out thinking levels and recommended sampling.
    - **The answer**, the output's contract: JSON, a tool call or text, a contract its facts refuse saying why, its
      default marked; the schema the first two need, and that text may have, to read JSON out of it.
    - **Thinking**, the reasoning: as the model does (none), by level, saying where the level lands, or by hand, with an
      effort and chat template arguments; a thinking token budget either way, unless its facts refuse one.
    - **Sampling**: recommended for the level thinking lands at, the values it recommends as placeholders, or the
      engine's; the values given in place of them, max output tokens and stop sequences.
    - **Tools**, by name and description, the person's own or the Archive's, offered only once there are any.
    - **Advanced**, folded: the passthrough, the key for max output tokens and the schema's inlined references.

  - **What it sends**: a column of its own (`frontend/src/lib/compose/Preview.svelte`), brought in by **What it sends**
    as Review's Measuring is, the configurations sliding out to the left and it in from the right, and after the rest
    below `xl`; `frontend/src/portal.css`'s `[data-slides]` moves both pages' columns. It is compiled as it is first
    shown, as it shows another language's tab than it was compiled in and as **Update** is pressed, which is enabled
    once what it would compile has changed. As read: the messages, each run of text that was put in from another part
    tinted and named on hover, a text not yet translated being the text as it was, marked so; a slot as its chip and the
    appendices as two placeholders laid out by the appendix layout; then the model, the rest of the body as it lands,
    the tools offered and how the answer is held. As sent: the body, without a seed or `return_token_ids`, its texts'
    line breaks breaking its lines. Both are marked against what the version drafted on sends in the same language, as
    saved, once anything differs from it: a message changed word by word in its runs, one added or taken out whole, and
    the body by line; saving makes the next to mark against (`frontend/src/lib/compose/diffing.ts`). What can't be
    compiled says why above the last that could, dimmed. `POST /api/threads/{id}/previews`
    (`src/chatddx/bench/composing.py:preview`) compiles the draft with `src/chatddx/factors/request.py:traced`, of which
    `compile_request` is the skeleton alone. While it is open, the texts and their translations sit side by side only
    where the column leaves room for it.

  - **Save**: `POST /api/threads/{id}/saves` (`src/chatddx/bench/composing.py:compose`) writes, in one transaction, each
    chunk that changed to the thread its own came from, a version where that is the person's and else a fork under its
    name, and then the configuration, as a version or a fork; a fork of the configuration forks the chunks it changes. A
    chunk held by no thread starts one named after the configuration and the part. Saved under a new name, it can be
    **independent of this one** instead: forked from nothing, each chunk it changes starting a thread named after it.
    Tags stay the Library's.

  - **Run**, beside Save, offered where the World names a baseline tag: saves what there is to save, as Save does, then
    `POST /compose/{id}/runs` (`src/chatddx/portal/compose.py:running_in_compose`) brings the configuration it saved
    into to a whole baseline, as Review's Run brings a case to a whole gathering. Its state is how the baseline stands,
    told in no words: enabled while something is behind that a run mends, marked to run again where the baseline is
    whole, and disabled while it is under way; a refusal, or its being out of date, is told among its findings.

## The baseline

A configuration's baseline sets it on the World's baseline cases, so that what a variation of it changes has something
to be measured against: the bare case of each family tagged with the World's baseline tag
(`src/chatddx/api/standing.py:baseline_cases`). It is a gathering as Review's are, through the same pipeline
(docs/parts/review.md, "Gatherings"), in the baseline's shape, a replicate and its seed repeated (`BASELINE`), over the
baseline cases rather than one. Each language the cases are sent in is a run of its own, and a case in a language the
configuration has no translations into is left out unsaid while any other is sent; it is said among the baseline's
findings once it has run, as a translation that fails to compile is, at the top of the configuration pane. A change to
an expectation or a scorer that a view reads puts it behind as not scored as things are now, which Run mends by scoring
again alone (`src/chatddx/portal/test/test_running.py`).

## How it fared

Drafted: below the page, read once scrolled near and again while its baseline is under way, how the configuration fared
on the baseline cases (`frontend/src/lib/compose/Breakdown.svelte`), from `GET /api/threads/{id}/breakdown`
(`src/chatddx/api/breakdown.py`; `src/chatddx/bench/breakdown.py:breakdown`), by field and view:

- **Its versions**, a column each in the order saved, the versions that compile to one skeleton being one, by its
  digest, so that a version run again, or saved again as it was, adds to the same: each baseline gathering a point
  linking to its runs, ringed where it isn't scored as things are now, and the mean over every replicate of every case
  with its 95% interval, the version open marked. Its difference from the one before, case by case on the cases both
  sent, is its Δ, on hover and among the numbers. A gathering's repeat adds no draw of its own, its seed being its
  replicate's.
- **Its peers**, beside it: the latest baseline of this configuration and of each of the person's others that shares the
  view.
- **The numbers**, folded: each view's estimate and Δ by version; and by version, how far each repeat's values were from
  its replicate's and how many answered alike to the letter (≡), the exception rather than the norm, its failed items,
  tokens and time, and the languages its cases went in, pooled by case otherwise.

It says what it can in numbers, symbols and words the portal already has, so that it adds little to translate.

Run takes the version open, an earlier one among them, when there is nothing to save, its baseline being that of the
latest start of what that version compiles to; on a baseline whole as things are now it runs again, drawing seeds anew,
another draw for each case.

What it reads of a run or a score that finished is held as rows (`src/chatddx/bench/observed.py:observed`): a run's
items as whether they failed, how long they took, the tokens they answered in and a digest of what they answered, and a
score's values, without a version; what a run isn't scored by as things are now, while the catalog stands and the run's
scores are the same.

A judge's configuration is written and saved there too.

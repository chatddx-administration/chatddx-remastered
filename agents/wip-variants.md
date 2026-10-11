# Variants: work in progress

What a variant is in the catalog today, why it rests on names alone, and what recording it would take. Written after
init-data started making recipes per language (`docs/curation.md`, "Texts") and the naming moved to
`chatddx.catalog.variants`. "Decided" means the user said so; "Take" is the agent's and still open.

## What a variant is today
A variant is something made for a language, a model or both: a text written in a texts file (`management-plan (en)`),
a chunk written from a model's facts (`recommended (Qwen/Qwen3-8B-AWQ)`), or a recipe made per language and model
(`plan (en, Qwen/Qwen3-8B-AWQ)`). It is a thread like any other. Only its name says it's a variant, of what, and
for what:
- init-data names it `NAME (LANGUAGE)`, `NAME (MODEL)` or `NAME (LANGUAGE, MODEL)`
  (`src/chatddx/catalog/variants.py:variant_name`, `src/chatddx/curation/plan.py:_named`);
- the bench reads the name back to find the variant a plain name means for the engine's model, and refuses one made
  in several languages (`variants.py:made_for`, `variants_for`; `src/chatddx/bench/seen.py:Seen.thread`);
- the repl offers the plain name beside the variants in completion (`src/chatddx/repl/shell.py:_per_model`).

## Why names alone are fragile
- **Any name that looks like one is one.** A person who saves a configuration as `draft (sv)` has made, as far as the
  bench is concerned, the Swedish variant of `draft`; `ward round (am)` reads as Amharic. `made_for` can only check
  that a qualifier looks like a language tag (`catalog/model.py:LANGUAGE`) or is a model the facts know.
- **Nothing checks the name against the thing.** A text's language is also kept on its digest (`catalog.language`),
  and a configuration's comes from its recipe's chunks (`catalog/language.py:language_of`), but nothing compares
  them with the language in the name. Nor is the model in the name compared with the one its chunks were written
  for.
- **Renaming breaks it.** A name entry is the only record, so renaming `plan (en, Qwen/Qwen3-8B-AWQ)` makes it no
  variant, or the variant of something else, and init-data then makes a new thread under the old name.
- **What belongs together is a string prefix.** `plan (en, …)` and `plan (sv, …)` are sibling threads with no link
  in the catalog: neither is a fork of the other, and nothing says they are the same configuration in two languages.
- **Forks follow by accident.** A giftbag fork takes its origin's name (`src/chatddx/curation/write.py:_Init.giftbag`),
  so it is a variant too, which is right; a variation saved under a new name isn't, which may not be.
- **It blocks picking by language.** The bench picks by the engine's model only. Once the data set has texts in two
  languages, `cell plan qwen3-8b-awq@fake` is ambiguous, where the cell's cases could say which.

## What the catalog already knows without names
- **Language.** Texts carry their language on the digest (init-data writes it from the texts file), a compiled
  skeleton's is voted by its recipe's chunks, and a case's is its family's (`docs/catalog.md`, "Languages").
- **Model, in part.** The facts can tell which model's recommendation a sampling chunk is
  (`src/chatddx/facts/lint.py:_sampled_for`, `facts.sampling_unmatched`), and a reasoning chunk written from facts
  is a model's way of asking for a level. Sampling that is no model's recommendation, such as greedy, says nothing,
  so a configuration's model can't always be derived.
- **Grouping: nothing.** Forks link a thread to its origin, and a compilation links a skeleton to its recipe, but no
  record says "these threads are one thing made several ways".

## Options
- **A. Names, guarded.** Keep the name as the record, and read qualifiers only on threads the archive owns, or their
  forks. Cheap; a person's `draft (sv)` stops being a variant. Renames and grouping stay as they are.
- **B. Recorded.** An entry on the thread naming what it is a variant of, with the language and the model it was made
  for, written by init-data (and by the bench when a person makes one). Names become people's again, and the bench
  picks by (variant of, model, cases' language) with no parsing. Needs a new entry field or fields: a tier-0 and a
  tier-2 migration, since entry fields are mirrored in the database (`docs/migrations.md`, catalog, tier 2).
- **C. Derived.** Group configurations whose recipes differ only in per-language texts and per-model chunks, from
  their compilations, the catalog's languages and the facts. No new data, but it's a heuristic, costs a walk over
  every configuration, and can't place a greedy configuration by model.
- **D. A family of variants**, as cases have families: a handle that each variant is bound to. The most explicit, and
  the most machinery for what B gets with entries.

Take: B, with the language read from the catalog where it already is, and the model recorded, since it can't always
be derived. A guards nothing that B doesn't, and C and D cost more for less.

## Questions for the user
- **Whose variants?** Are variants only what a data set makes, or may a person make their own, such as a Swedish
  variation of their configuration?
- **Forks.** Should a person's fork of a variant stay a variant of the same thing, as a giftbag fork is today by its
  name?
- **Mixed batches**: moved to `agents/wip-batch.md` (P3).
- **Names for people.** With variants recorded, should init-data still put the language and model in the name, for
  people to read, or drop them and let the portal show them?

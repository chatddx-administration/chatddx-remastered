# Curation: work in progress

Reworks of the data set format after `docs/curation.md` was written. "Decided" means the user said so; "Take" is the
agent's and still open.

## Decided (2026-10-09)
- `family_of` reads only the bindings to a vignette's id or content (77736ff).
- **Two kinds of chunk text.** Instructions, prompts, few-shot and translations are written in a language, as cases
  are: they live in `texts-<lang>.toml` beside `cases-<lang>.toml`, which gives them their language, and may not name
  one. Outputs and toolsets hold text too, but it is translated by code (translations chunks), so they stay in
  `factors.toml` and take `language` as now (their own, or the file's). Sampling, reasoning, passthrough and the rest
  have no language.
- **Layout**: `factors.toml`, `texts-<lang>.toml`, `cases-<lang>.toml`, files they load.
- **A recipe per language.** The same name in several texts files is the same chunk in other languages. A recipe
  naming one is made once per language that has every text it names, like per-model records: `case (sv)`,
  `plan (sv, Qwen/Qwen3-8B-AWQ)`.
- **Translations translate only output and toolset text** (and the recipe's appendix layout); instructions, prompts
  and few-shot are written in their language and pass through. A change to compilation: docs/factors.md gets a
  proposal.
- **A chunk without text** (the sample's `prompt.case`, slots only) stays in `factors.toml`, without a language, and
  serves every language.

## Take: how translations meet per-language recipes
A recipe's languages are those whose texts files have every language-bound record it names (instructions, prompt,
few-shot, translations). In the language its outputs and toolset are written in, it needs no translations and is
made without them; in any other, it needs its translations there, and is skipped and reported without them. A recipe
naming nothing language-bound is made once, unsuffixed, as now.

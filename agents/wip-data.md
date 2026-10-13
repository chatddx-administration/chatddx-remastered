# Data: work in progress

How the repository's data is laid out and read: a World (`worlds/<name>/`), its data set (`_data/`) and its scripted
runs (`_runs/`), as init-data, the engine import, the repl and `chatddx scripted-runs` read them. The files are hard to
grok, and the rules that govern them are partly conventions. This file plans turning the conventions into rules,
where the structure is accidental, and leaving it alone where it maps the machinery.

"Decided" means the user said so. "Take" is the agent's recommendation and still open. D1–D6 are decided and built;
D2 holds two takes settled while building.

## Start with this
The take: the data set is a fair picture of machinery that really is complex; the World and the seam between World
and data set are where the accidental complexity lives. One principle covers it (see "The principle"), and six takes
apply it (D1–D6). None of them moves a stored digest.

Order, cheapest and least contested first:
1. D5, the names: built.
2. D4, content tests out of curation: built.
3. D6 and D1, the World's `engines.toml` and no init-data `--factors`: built.
4. D2, judges bound by the World: built.
5. D3, translations grouped by record: built.

## The principle
Each file is written by one kind of author and holds only what that author decides.

| File | Author | Holds |
| --- | --- | --- |
| `inventory.toml` | ops, by hand | sources, clearance, and which endpoint judges each judge |
| `endpoints.toml` | the engine import (by hand for fakes), included | endpoints and hosts |
| `engines.toml` | the engine import (by hand for fakes) | models, local engines, remote engines |
| `facts.toml` | whoever adds a model the bundled facts don't know | facts about models |
| `vignettes/` | the source's owner | a directory source's vignettes, when git may hold them |
| `_data/` | researchers and clinicians | the data set |
| `_runs/` | developers | scripted runs |

Since D1 and D2 this holds by rule: the engines are the World's, and so is which engine judges a data set's judge.

## What holds now
- **Finding a World's files** (`src/chatddx/inventory/world.py:World.load`, `src/chatddx/cli.py`): `inventory.toml` is
  required; `engines.toml` and `facts.toml` are taken by name when present; `include` names the files of endpoints and
  hosts; a source's `path` names its vignettes; `_data/` is init-data's default `--data`, and `_runs/` is `chatddx
  scripted-runs`'. The leading `_` marks what the World doesn't read.

## Takes
### D1. The World's engines file
Decided, and built as the take had it. The World's `factors.toml` was the data set's namespace by another name:
`plan_factors` merged it in, either file could hold any table, and every World's held exactly the engine tables.
- The World's file is `engines.toml` (`World.engines`), and it holds only `model`, `local_engine` and `remote_engine`;
  a data set's `factors.toml` refuses those tables. `plan_factors(data, facts, compiler, engines=…)` says which file a
  table belongs in when it's in the other (`src/chatddx/curation/plan.py`, `DATA_TABLES`;
  `curation/test/test_plan.py:test_engines_are_the_world_s_and_only_engines_are`).
- `chatddx import-engine` writes `--engines` (was `--factors`), with `importers/o11n.py:engines_toml`.
- The three Worlds' files were renamed with git, and Kompismoln's `endpoints.toml` header names `engines.toml`, as
  the import now writes it.
- AGENT suggestions in `docs/curation.md` ("Factors", "The World", "Loading"), `docs/inventory.md` ("Worlds",
  "Importing from a host"), `docs/inventory-api.md` and README.
- Digests: none moved. The records are the same; only the file and the rule changed.

### D2. Judges bound by the World
Decided, and built as the take had it. A data set's `[judge.<name>]` named a World's engine by name, so Kompismoln
skipped the sample's `verdict`, `graded` and `notes` and had nowhere to name judges of its own: its engines file is the
import's, and a judge of its own named `verdict` would have clashed with the data set's.
- A data set's judge keeps what researchers author, `recipe`, `seeds`, `fill` and `language`, and refuses an `engine`.
  The World's inventory binds each judge to an endpoint, as `[cleared]` clears one, read only from its own file:
  `[judge] verdict = "qwen3-8b@pelle"`; a binding to no endpoint is refused when the inventory loads
  (`src/chatddx/inventory/inventory.py:Inventory.judges`).
- `plan_factors(data, facts, compiler, world)` takes the World, its engines and its inventory: a judge's engine is the
  planned engine its bound endpoint serves (`src/chatddx/curation/plan.py`; `curation/test/test_judges.py`).
- The three Worlds bind their judges: the sample's and the test World's as their data sets named them before, and
  Kompismoln's `verdict` to `qwen3-8b@pelle` and `graded` to `gpt-oss-20b@malborg`, so `notes` is planned there too.
- AGENT suggestions in `docs/curation.md` ("Factors", "The World"), `docs/inventory.md` (a "Judges" section, includes,
  loading's checks, the terms) and `docs/inventory-api.md`.
- Digests: none moved. A judge's component is unchanged, and its engine is the one its data set named before.

Two takes, settled while building and open to being overturned:
- **Scoring doesn't read the binding.** The scoring pass still finds the one endpoint that serves the judge's engine
  (`runner/score.py:_serving`), so "A judge's endpoint can't be named" (`docs/bench.md`, "Outstanding") stays as it
  is. A binding is by name, and a judge a person writes over the bench names its engine itself and has no binding;
  reading the binding when scoring would treat the World's judges and people's apart.
- **A judge the World doesn't bind is skipped, not refused**, and reported, as a judge on an unknown engine was, so a
  World can load a data set without binding its judges. A binding for a judge the data set doesn't have is reported.

### D3. Translations grouped by record
Decided, and built with groups per record only. Translations were a flat map from a text, exactly as a chunk holds it,
to its translation: `worlds/sample/_data/texts-sv.toml` held 51 entries in one table, far from the records they come
from; a TOML key can't span lines, so a paragraph of guidance was one line of `\n\n`; and nothing noticed an entry no
text used any more.
- A translations record may write its entries in `of`, grouped by the record whose texts they translate, an output, a
  toolset or a recipe (its appendix layout), each entry a `text` and its `translation`, multi-line strings allowed:
  ```toml
  [[translations.sample.of."output.management-plan-shown"]]
  text = """
  Fill in the management plan for the case.
  ...
  """
  translation = """
  Fyll i handläggningsplanen för fallet.
  ...
  """
  ```
- Planning flattens the groups into the same `entries`, and refuses an entry whose record doesn't hold its text (the
  record's variants in other languages than the translations'), a group naming no output, toolset or recipe, a text
  translated two ways, and `of` beside `entries` (`src/chatddx/curation/plan.py`, `grouped`, `texts_of`;
  `curation/test/test_plan.py`). Translations are planned after toolsets for it. A text several records hold, such as
  a shared schema's, is written once, under the first that holds it.
- Both data sets' translations are grouped: the sample's 51 entries under eight records, the test World's two under
  `output.lines` and `recipe.lines-guided`.
- Digests: none moved; every planned record of the three Worlds has the digest it had (checked before and after).
- An AGENT suggestion in `docs/curation.md` ("Factors").
- Not built: a command that appends a recipe's missing pairs, as gettext's msgmerge does, once translating grows.

### D4. Content out of curation
Decided, and built as the take had it: curation is code for any data set; the sample is content, and curation knows
nothing of it. `curation/test/` held three modules that tested content, not curation.
- `test_sample.py`, `test_worlds.py` and `test_the_test_world.py` are in `src/chatddx/test/`, beside the Worlds' paths
  and the names tests share (`src/chatddx/test/world.py`), with their marks. The root conftest's fixtures reach them
  there. `curation/test/` tests curation.
- `docs/curation.md` has AGENT suggestions: its "Tests" lists the three apart, and its examples drop the sample's
  counts ("six outputs" had gone stale), which the sample's own tests pin. `docs/inventory.md` and `docs/vllm.md` have
  suggestions for the new path.
- The alternative home, beside the content (`worlds/sample/test_sample.py`, with `worlds` in pytest's `testpaths`),
  would have needed the root conftest's fixtures brought there.

### D5. Names
Decided, and built as the take had it. "Sample" named three things: the sample World, its data set, and the runs
answered by the fake from a script, which any World can hold. Now it names the first two.
- `SampleCase` is `DataCase`; init-data refuses with "a data set needs exactly one expectation schema", and its help
  says it loads a data set, not the sample data.
- The runs answered by a script are *scripted runs*: `chatddx.scripted` (`ScriptedRun`, `scripted_runs`, in
  `read.py`), the command `chatddx scripted-runs`, whose lines start `[scripted run NAME]`, and
  `agents/wip-scripted.md`. `_runs/` stays. README, `docs/repl-manual.md`, `docs/repl-api.md` and `docs/inventory.md`
  have AGENT suggestions.
- "Staged runs" was the other name: it says what they're for, where "scripted" says how they're answered.
- Digests: none moved; nothing stored names either.

### D6. init-data's `--factors`
Decided, and built: dropped. With D1, the World's engines come from the World and everything else from the data set,
and a file of more factors would have been a way around the rule. Nothing used it. `--facts` stays: facts are about
models, not a factor of either side.

## The layout it leaves
```
worlds/<name>/
  inventory.toml   sources, clearance, judges bound to endpoints, include = ["endpoints.toml"]
  endpoints.toml   endpoints and hosts
  engines.toml     models, local engines, remote engines
  facts.toml       facts about models the bundled facts don't know
  vignettes/       a directory source's vignettes, when git may hold them
  _data/
    factors.toml       chunks without text, tools, the expectation schema, scorers, judges, recipes, canary sets
    texts-<lang>.toml  chunks that hold text, in that language; translations grouped by record
    cases-<lang>.toml  cases in that language, with tags, targets, appendices and the cases that send them
    schemas/           the JSON files the factors load
  _runs/           scripted runs
```

## What stays
- **The data set's split** into `factors.toml`, `texts-<lang>.toml`, `cases-<lang>.toml` and `schemas/`. It follows
  real distinctions: whether a record holds text the model reads, which language it is in, and a record or a case.
- **The machinery**: variants per language and per model, forks, `from_facts`, shipped-code pins, one expectation
  schema. These are the rules of the factors, not of the files.
- **`include`** for what the import rewrites whole, and the leading `_` for what the World doesn't read.

## Open
- **Where this file goes.** Every take is built. What stays true, the principle and the layout it leaves, belongs in
  `docs/inventory.md` ("Worlds") and `docs/curation.md` ("Data sets") once their suggestions are in; then this file can
  go, as `agents/wip-sample-data.md` did.

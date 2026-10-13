# Data: work in progress

How the repository's data is laid out and read: a World (`worlds/<name>/`), its data set (`_data/`) and its scripted
runs (`_runs/`), as init-data, the engine import, the repl and `chatddx scripted-runs` read them. The files are hard to
grok, and the rules that govern them are partly conventions. This file plans turning the conventions into rules,
where the structure is accidental, and leaving it alone where it maps the machinery.

"Decided" means the user said so. "Take" is the agent's recommendation and still open. D1, D4, D5 and D6 are decided
and built; the rest are takes.

## Start with this
The take: the data set is a fair picture of machinery that really is complex; the World and the seam between World
and data set are where the accidental complexity lives. One principle covers it (see "The principle"), and six takes
apply it (D1–D6). None of them moves a stored digest.

Order, cheapest and least contested first:
1. D5, the names: built.
2. D4, content tests out of curation: built.
3. D6 and D1, the World's `engines.toml` and no init-data `--factors`: built.
4. D2, judges bound by the World. Next: it makes planning read the World's inventory too.
5. D3, translations grouped by source.

## The principle
Each file is written by one kind of author and holds only what that author decides.

| File | Author | Holds |
| --- | --- | --- |
| `inventory.toml` | ops, by hand | sources, clearance, and, with D2, which endpoint judges each judge |
| `endpoints.toml` | the engine import (by hand for fakes), included | endpoints and hosts |
| `engines.toml` | the engine import (by hand for fakes) | models, local engines, remote engines |
| `facts.toml` | whoever adds a model the bundled facts don't know | facts about models |
| `vignettes/` | the source's owner | a directory source's vignettes, when git may hold them |
| `_data/` | researchers and clinicians | the data set |
| `_runs/` | developers | scripted runs |

Since D1 the engines are the World's by rule. A judge's engine is still the data set's choice (D2).

## What holds now
- **Finding a World's files** (`src/chatddx/inventory/world.py:World.load`, `src/chatddx/cli.py`): `inventory.toml` is
  required; `engines.toml` and `facts.toml` are taken by name when present; `include` names the files of endpoints and
  hosts; a source's `path` names its vignettes; `_data/` is init-data's default `--data`, and `_runs/` is `chatddx
  scripted-runs`'. The leading `_` marks what the World doesn't read.
- **Judges cross the seam.** A data set's `[judge.<name>]` names a World's `engine` by name, its `recipe`, `seeds`,
  `fill`, and optionally `language`. A World without that engine skips the judge and every scorer whose views name it.
  So init-data with Kompismoln skips the sample's `verdict`, `graded` and `notes`, and Kompismoln has nowhere to name
  judges of its own: its engines file is the import's, and a judge of its own named `verdict` would clash with the
  data set's. The scoring pass then finds the one endpoint that serves the judge's engine
  (`src/chatddx/runner/score.py:judge_at`, `_serving`); with two, the judge's scorer is barred (`docs/bench.md`,
  "Outstanding": "A judge's endpoint can't be named").
- **Translations** (`src/chatddx/factors/request.py:Translations`, `compile_request`) are a flat map from a text,
  exactly as a chunk holds it, to its translation. A recipe's missing texts fail its compile, listed. Nothing notices
  an entry that no text uses. `worlds/sample/_data/texts-sv.toml` holds 51 entries in one table, far from the
  outputs, the toolset and the schema files they come from; a TOML key can't span lines, so a paragraph of guidance
  is one line of `\n\n`, and one changed English word re-keys the whole paragraph.

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
Take: a judge's engine is the World's choice, as a trial's endpoint is. The data set keeps what researchers author,
`[judge.<name>]` with `recipe`, `seeds`, `fill` and `language`, and no `engine`. The World's hand-written
`inventory.toml` binds each judge to an endpoint, as `[cleared]` clears one:
```toml
[judge]
verdict = "qwen3-8b@pelle"
graded = "gpt-oss-20b@malborg"
```
- Planning takes the World's inventory beside its engines: the judge's engine is the bound endpoint's, which must be an
  engine the World plans. A judge the World binds no endpoint for is skipped and reported, as a judge with no engine
  is now, with the scorers whose views name it.
- The scoring pass sends a judge's calls to its bound endpoint, which answers "A judge's endpoint can't be named".
- Like `[cleared]`, the binding is a person's statement, read only from the inventory's own file, never an include.
- Digests: a judge's component is unchanged (`skeleton`, `engine`, `seeds`, `fill`), and its engine digest is the
  same when the bound endpoint serves the engine the data set named before. Judges and judged scorers already differ
  per World.
- With it, Kompismoln binds the sample's judges to pelle and malborg, and the sample's `notes` is planned there too.

### D3. Translations grouped by source
Take: keep the mechanism, a flat map from text to translation (structure can't drift, and a missing text fails the
compile with a list); change how it is written. Entries are pairs, grouped by where the text comes from, and planning
flattens them into the same `entries`:
```toml
[[translations.sample.of."output.management-plan-shown"]]
text = """Fill in the management plan for the case.

Answer with a JSON object that matches this JSON Schema, and nothing else:

"""
translation = """Fyll i handläggningsplanen för fallet.

Svara med ett JSON-objekt som följer detta JSON Schema, och inget annat:

"""
```
- A group names a record that holds text the translations reach (`output.<name>`, `toolset.<name>`) and holds texts of
  that record (`src/chatddx/factors/request.py:own_texts`). An entry whose text its group's record doesn't hold is
  refused when planned, so a stale entry is found.
- A text held by several records (a schema shared by `plan`, `plan-shown` and `plan-prompted`) is written once, under
  any one of them; the same text written twice must have the same translation.
- Missing texts still fail the compile of the recipe that needs them.
- Later, if translating grows: a command that appends the missing pairs to a texts file, as gettext's msgmerge does.
- Digests: none move; the component is the same flat map.

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
    texts-<lang>.toml  chunks that hold text, in that language; translations grouped by source
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

## What each take touches
| Take | Code | Data | Tests | Docs (AGENT suggestions) |
| --- | --- | --- | --- | --- |
| D2 | `inventory/inventory.py`, `curation/plan.py`, `runner/score.py`, `bench` | judges lose `engine`; three inventories gain `[judge]` | `curation/test/test_judges.py`, the runner's and the bench's judge tests | `docs/inventory.md`; `docs/curation.md` "Factors"; `docs/runner.md` "Judges"; `docs/bench.md` "Outstanding" |
| D3 | `curation/plan.py` | both `texts-sv.toml` | `test_sample.py`, curation's | `docs/curation.md` "Texts"; `docs/factors.md` "Translations" |

## Open
- **D2, reading the binding when scoring.** The scoring pass holds a judge by digest, and the binding is by name. It
  can read the judge's name from its thread, or keep finding the endpoint that serves the judge's engine and use the
  binding only to plan. The first names the endpoint; the second leaves two endpoints of one engine ambiguous.
- **D2, a judge bound in no World.** The test World's `remote` judge, cleared for nothing, would be bound to
  `unknown@remote` as now; whether an unbound judge is an error or a skip, as an unknown engine is now.
- **D3, the groups.** Records only, or schema files too (`schemas/management_plan_v1.json`), which would group a shared
  schema's texts once. And the recipe's appendix layout, which translations reach too (`request.py:TRANSLATED`).

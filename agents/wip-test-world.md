# The test World: work in progress

The tests run on the sample today: its data set (`src/chatddx/data/sample/`) and its World (`worlds/sample/`). The
sample is live data with work queued on it (`agents/wip-sample-data.md`: the real engines, judges from Olof's notes,
maybe revised targets, sample runs), and it exercises only part of what a data set and a World can say. This file
plans a World built for the tests, `worlds/test/`, and moving every test onto it but the sample's own.

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Decided
- **A test World, `worlds/test/`, with its data set inside it, at `worlds/test/_data/`.**
- **The sample keeps one test module**, `src/chatddx/curation/test/test_sample.py`, with what is true of the sample
  alone. What should hold for every World is checked on all of them (see "What stays on the sample").
- **Names say what they exercise**, not what the sample called them.
- **The test World's tools are the test tools** (`src/chatddx/runner/test/tools.py`). The root conftest ships them
  for the whole session, as `runner/test/conftest.py:shipped_tools` does for the runner's tests now, so planning
  takes their entry points.
- **The bugs found on the way are fixed separately**, before the tests move (see "Fixes before the move").

### Why `_data`
A World is what lies outside chatddx: its sources, engines, hosts and facts about models. A data set is chatddx's
own authored content, loaded into the archive. The test World holds one only because its cases name the World's
vignettes, and other Worlds may copy that, so the name sets a precedent:
- the leading `_` marks an entry that `World.load` (`src/chatddx/inventory/world.py`) doesn't read and the World
  doesn't own;
- `data` is `init-data`'s `--data` and `docs/curation.md`'s "data set". Plain `data` would read as the World's
  own data, which its vignettes are. `bootstrap` and `starter_kit` name a single use, but a data set is loaded again
  to update it. `demo` names a purpose it doesn't have.

Loading it stays explicit: `chatddx init-data alice --world worlds/test --data worlds/test/_data --source test`.

## Principles
1. **Every record is read by a test.** The table under "What it exercises" names, for each record, the test that
   reads it. A record no test reads isn't added.
2. **Counts come from the data.** A test derives what it counts from the plan, the cases or the inventory. Literal
   counts, skip lines and lint lines appear only in the test World's own test.
3. **What `curated` loads holds no mistakes.** Its only findings are the ones the design calls for. Broken data
   (an invalid expectation, an unreachable view, a misplaced clearance) is an edit a test makes to a copy of the
   World, as `changed()` in `src/chatddx/curation/test/test_init.py` does to the sample now.
4. **The test World's own test pins its design**: the records per table, the skip lines, the lint lines, the World's
   findings, and that each endpoint names the digest of the engine planned under its name. A change to the World
   fails there first, with the new values in the message. It is `test_init_data_loads_the_archive`
   (`src/chatddx/curation/test/test_init.py`), moved off the sample.
5. **Names are spelled once.** One module holds the names tests use: endpoints, recipes, cases and tags. It
   replaces `QWEN`, `PLAN` and `FREE_TEXT` in `src/chatddx/conftest.py`, `bench/test/sample.py`,
   `repl/test/sample.py` and `runner/test/conftest.py`.
6. **Tests don't pin layout by accident.** Repl tests that pin column widths through the length of a scorer's name
   (`repl/test/test_inspecting.py`, `test_reviewing.py`, `test_running.py`) match on cells instead.

## Layout
```
worlds/test/
  inventory.toml   sources, clearances, and include = ["endpoints.toml"]
  endpoints.toml   endpoints and the host
  factors.toml     models, local engines, the remote engine
  facts.toml       facts about the made-up Mistral-family model
  vignettes/       nine files, each with a property of its own
  _data/
    factors.toml   chunks without text, tools, the expectation schema, scorers, recipes
    texts-en.toml
    texts-sv.toml
    cases-en.toml  six cases
    cases-sv.toml  three cases
    schemas/       answer.json, list.json, verdict.json, targets.json
```

The ports are 12201–12204, so the test World's fakes and the sample's (12099, 12100) can run side by side by hand.

## What it exercises
"Today" is what reaches the feature now: the sample, Kompismoln, synthetic data in a test, or nothing.

### The World
| Record | Exercises | Today | Read by |
|---|---|---|---|
| `[source.test]`, sensitive directory | the cases' vignettes; the tool gate's refusal | the sample | most tests |
| `[source.typed]`, database | typed cases | the sample | `api/test/test_typed.py`, `bench/test/test_typed.py` |
| `include = ["endpoints.toml"]` | includes | Kompismoln | the test World's own test |
| `qwen3@fake`: Qwen/Qwen3-8B-AWQ, reasoning and tool parsers, `max_jobs = 4` | the workhorse | the sample | most tests |
| `gpt-oss@fake`: openai/gpt-oss-20b, harmony | harmony; `facts.output_note`; reasoning the facts refuse | the sample | repl choosing, runner, fake vLLM |
| `qwen3-bare@fake`: the same model, no reasoning parser, no tool flags, `max_jobs = 1` | two engines on one model; `vllm.grammar_before_reasoning`, `vllm.tools_refused`, `vllm.thinking_budget_refused`; a clearance for `test` and not for `typed` | nothing | new pair-lint and gate tests |
| `mistral@fake`: the made-up `test/mistral-7b`, facts from the World's `facts.toml` | a World's facts; the fake's Mistral family; a model whose facts refuse reasoning | nothing (World facts only in `test_init.py`'s synthetic gemma) | new planning and fake tests |
| `unknown@remote`: a remote engine on `https://remote.invalid/v1/`, a model no facts know, `credential = "CHATDDX_TEST_REMOTE"`, cleared for nothing | remote engines; `facts.missing`; `schema.ref_unverified`; the gate's "isn't cleared" and "needs the secret" | synthetic only | new pair-lint and gate tests |
| `[host.fake]`: one template, three model locations | start-ups | the sample | `inventory/test/test_serving.py`, `fake_engines` |
| `facts.toml`: `test/mistral-7b`, plus a model no engine serves | "no planned engine serves it" | synthetic only | the test World's own test |

The remote endpoint is never reached: `.invalid` resolves nowhere, so it stays at planning, lints and the gate.
The made-up Mistral model keeps facts written for the tests from being read as facts about a real model.

### The data set
Outputs, each in `texts-en.toml` unless it holds no text:

| Output | Contract | Exercises |
|---|---|---|
| `native` | native, `answer.json` with `$defs`/`$ref` | constrained answers; `schema.ref_unverified` on the remote |
| `native-inlined` | the same with `schema_ops = ["inline_refs@1"]` | the inlined schema; no `schema.ref_unverified` |
| `prompted` | text with `answer.json` and the `schema` insert | an unconstrained schema shown in the guidance |
| `tool-answer` | tool, `list.json`, with a description | a named `tool_choice`; a second output shape |
| `tool-answer-bare` | tool, `list.json`, no description, no guidance | the contract's minimum |
| `lines` | text, guidance | free text; `lines@1` |
| `raw` | text, no guidance (in `factors.toml`) | `language.unknown`, with the prompt `case` |

Recipes. A recipe whose sampling is `recommended` is made per model; the others are made once:

| Recipe | Parts beyond `case` and the output | Exercises |
|---|---|---|
| `native` | `recommended` | the per-model recipe; `facts.sampling_unmatched` across models |
| `native-tools` | a fork of `native`, toolset `lookup` | `vllm.native_tools_uncallable`; the tool gate |
| `native-inlined` | `greedy` | see the outputs |
| `prompted` | `greedy` | reading an answer out of text |
| `tool-answer` | `greedy` | the answer tool |
| `tool-answer-tools` | `greedy`, toolset `lookup` | `tool_choice: required`, the answer tool offered last, a tool that fails |
| `lines` | `recommended` | free text per model |
| `lines-tools` | `greedy`, toolset `lookup` | text after tool rounds |
| `lines-guided` | instructions `clinician` (developer role, `output_guidance` insert), few-shot `worked-example` (one exchange), passthrough `min-tokens`, translations `sv`, `appendix_layout` | made in en and sv; a translated output |
| `lines-instructed` | instructions `clinician`, no translations | `[skipped]`: "needs translations in sv" |
| `headed` | instructions `clinician`; the prompt `headed`, which holds text and a `tool_guidance` insert and exists in en only; toolset `lookup` | the toolset's guidance placed in the prompt; `[skipped]`: "it has no prompt in sv" |
| `raw` | `greedy` | `language.unknown` |
| `reasoned` | `recommended`, reasoning `high` | reasoning in a skeleton; `facts.reasoning_unmatched`; `[skipped]`: "the facts refuse its reasoning" for `test/mistral-7b` |
| `budgeted` | `greedy`, reasoning `on-budget` | `vllm.thinking_budget_refused` on `qwen3-bare@fake`; `facts.budget_refused`; skipped where the facts refuse a budget |
| `clamped` | sampling `near-greedy` (temperature 0.005) | `vllm.temperature_clamped` |
| `judge` | purpose `judge`; the prompt `judge` with the `completion` and `expectation` slots; output `verdict` | a judge skeleton, for the judge tests in `scorers/test/test_scorers.py` |

Other records:
- **Sampling**: `recommended` (`from_facts`), `greedy` and `near-greedy`. The bench's and repl's tests swap in
  `greedy`, as they swap in the sample's now.
- **Reasoning**: `off`, `on` and `high` from the facts, and `on-budget` with a budget. The repl's choosing tests
  swap in `off` and `on`.
- **Tools**: `lookup` and `broken` from the test tools, in the toolset `lookup` with `max_rounds = 2` and guidance.
- **Expectation schema**: `targets`, the sample's kinds (diagnosis, warning or false, disposition, dont_miss,
  notes), requiring `diagnosis`, with no other properties allowed.
- **Scorers**, one per output shape, as the sample has them:
  - `answer`: differential, warning, disposition, and dont-miss over the diagnoses marked critical;
  - `list`: differential and dont-miss;
  - `lines`: text, differential (`lines@1`) and dont-miss;
  - `whole`: text.

### The cases
Nine vignettes, each named for what it carries:

| Case | Language | Vignette | Targets |
|---|---|---|---|
| `crlf` | en | CRLF throughout, a final bare LF, like the sample's Dutch cases | diagnosis, warning, disposition |
| `bom` | en | a UTF-8 BOM | diagnosis |
| `whitespace` | en | trailing spaces and a tab, a run of blank lines | diagnosis |
| `matched` | en | plain | a diagnosis pattern the fake's answers match (`fake & diagnosis*`), so a score isn't 0 |
| `dont-miss` | en | plain | `dont_miss`, `warning = false`, a disposition with text and no pattern |
| `noted` | en | plain | notes by carol, in Swedish, one with an `answer` and one without |
| `svenska` | sv | å, ä, ö in NFC | diagnosis |
| `nfd` | sv | the same letters decomposed (NFD) | diagnosis |
| `mislabeled` | sv | English text | diagnosis |

Every case has a tag. Two tags overlap, and one tag holds only English cases, which the tests of tag unions and
`language.mixed` need. The tags are set when the World is built.

Kept out of the World and made by the tests that need them:
- a vignette that isn't UTF-8;
- renamed and changed vignettes, through `MemorySource` (`src/chatddx/inventory/test/memory.py`) or a copy;
- an invalid expectation, an invalid expectation schema, a second expectation schema;
- a view that reaches nothing (`view.unreachable`);
- `cleared.not_sensitive`, `endpoint.remote_host`, `endpoint.shared_url`, `host.unpinned` and
  `endpoint.engine_unknown`.

## The harness
- **One module for what the tests share** (take: `src/chatddx/test/world.py`): the World's paths, `world_plan(world,
  data)`, and the names. `world_plan` generalizes `sample_plan`.
- **`curated` loads the test World** for alice with her giftbag.
- **`free_world` rewrites the parsed inventory**, giving each local endpoint a free port and each directory source
  an absolute path. Today it replaces the strings `12099`, `12100` and `path = "vignettes"` in the file.
- **`edited(world, …)`**: a copy of the World with text edits, for the broken data above.
- **One `world` fixture.** Today the root one returns an `Inventory` and curation's returns a `Path`.
- **The curation tests' `few` and `FEW` go.** The test World is already small enough to load whole.

While the tests move, both templates exist: the sample's, under a new name, for the packages not yet moved, and
the test World's `curated`. The sample's template goes when the last package has moved.

## The move
In this order, with `pytest` green after each package and one commit per package:
1. **inventory**: `test_serving.py`'s World tests.
2. **fake_vllm**: `free_world` users. The "every skeleton" test becomes generic (see "What stays on the sample").
3. **scorers**: `test_answer.py` and the second half of `test_scorers.py`. The sample's targets-schema and notes
   tests go to the sample module.
4. **runner**: `CASES`, the `insensitive()` override (`runner/test/test_run.py`), and `test_score.py`'s
   `load_cases(SAMPLE)`.
5. **curation**: `test_init.py`, `test_plan.py`, `test_repair.py`, `test_giftbag.py`, `test_pins.py`.
   `test_init_data_loads_the_archive` becomes the test World's own test.
6. **bench**: `sample.py` (`SOURCE` hard-codes `worlds/sample/vignettes`), `test_seen.py`, `test_outcome.py`
   (the exact `diagnoses.json` error), `test_scorers.py`, `test_writes.py`.
7. **api**: `test_world.py` (exact endpoints and values), `test_variations.py` (reach and lint properties),
   `test_runs.py`, `test_scorers.py`, `test_families.py`.
8. **repl**: last and largest. `test_listing.py`, `test_inspecting.py`, `test_running.py`, `test_reviewing.py`
   and `test_scoring.py` pin the sample's counts (99, 20, 30, 49, 50), its texts and its column widths.

Then **new tests** for what only the test World reaches: the pair lints and gate refusals on `qwen3-bare@fake`,
`mistral@fake` and `unknown@remote`, the World's facts, the Mistral fake, a score that isn't 0, `dont_miss` reach,
and the vignette quirks under the cleanup ops. Every row of "What it exercises" ends up read.

Some tests assert what is true of the sample by chance. They are rewritten to assert the test World's design:
- "no case has a `dont_miss`" (`api/test/test_variations.py`, `repl/test/test_inspecting.py`);
- "no recipe uses reasoning" (`repl/test/test_listing.py`);
- "every fake answer misses every pattern";
- "`DutchFall10w` sorts first" (`curation/test/test_init.py`, `repl/test/test_listing.py`).

## What stays on the sample
`src/chatddx/curation/test/test_sample.py`, the sample's pins:
- **Vignettes**: they are 7893656's (now `test_the_sample_world_holds_the_vignettes_at_7893656`).
- **Cases**: 79 English and 20 Swedish, and the language of `casesfromedn1` and `Dutchfall11w`.
- **Records**: the English and Swedish sets, the eight recipes per model, and the translations' coverage (the
  module's two tests now).
- **Targets**: every target reads; the targets schema's rules; Olof's notes on three cases, as written (from
  `scorers/test/test_scorers.py`).
- **Kompismoln**: it takes the sample's vignettes (`inventory/test/test_inventory.py`).

`src/chatddx/curation/test/test_worlds.py` runs the checks that should hold for every World in `worlds/` (test,
sample, Kompismoln), each with its data set:
- it plans and loads. Each World's exact skips and lints are pinned by its own test: the test World's in
  `test_init.py`, the sample's in `test_sample.py`;
- each endpoint names the digest of the engine planned under its name (now `test_serving.py`'s sample-only test);
- `init-data --world` binds each endpoint and seeds no other World's fakes (now in `test_init_data_command`);
- every skeleton is answered as its contract asks by each fake endpoint (now
  `test_it_answers_every_sample_skeleton…`);
- the fake's instances hold to the data set's schemas (now `test_what_it_writes_holds_to_the_sample_s_schemas`).

## Fixes before the move
Found while surveying, each fixed and tested on its own:
- **`init-data --source typed` ends in a traceback.** In `src/chatddx/cli.py:_init_data`, `source.ids()` runs outside
  the `try`, and `DatabaseSource.ids` raises `LookupError`.
- **`free-text-guided (sv, …)` is planned as a fork of nothing.** In `src/chatddx/curation/plan.py:plan_factors`,
  `base()` gives `None` when the origin has no variant in the fork's language, and says nothing. Either the fork
  takes the origin's variant in another language, or it is reported. That's a question for the user.
- **`scorer.revision` is documented but never raised**: in `docs/factors-api.md` (lint table) and
  `docs/curation.md` ("Loading", step 7). Suggest removing it from the docs (AGENT: REMOVE), or implement it.
- **Drift in `agents/wip-sample-data.md`**:
  - the Kompismoln commands with `--world …/inventory.toml --factors …/factors.toml`, and "seeding the sample takes
    `--factors worlds/sample/factors.toml`", both from before `--world DIR`;
  - `docs/ledger.md:JudgeCall`, which is `src/chatddx/ledger/score.py:JudgeCall`.
- **Drift in the sample's own files**:
  - `worlds/sample/inventory.toml`'s header names `cases.toml`;
  - `src/chatddx/data/sample/factors.toml`'s header says "without a `code`" where the key is `version`.

## Docs, when it's done
- `docs/curation.md`, "Tests" and "Data sets": AGENT suggestions for the test World and `_data`.
- `docs/inventory.md`, "Worlds": an AGENT suggestion for the third World and the `_data` convention.
- `agents/wip-sample-data.md`: the tests no longer use the sample, except `test_sample.py` and `test_worlds.py`.
- Timings before and after: 600 tests in 58.6 s before. Loading the whole sample in `curated` took 2.7 s of it.

## Open
- **A consequence of the test tools.** The test World loads only where they are shipped, which is under pytest.
  `chatddx init-data` by hand refuses its toolset. Take: accept that. The test World is for the tests, and the
  sample is for hand use.
- **Should `init-data` take `--data` from the World's `_data/` when there is one?** It would make the convention
  part of `World` and save each caller from spelling it out, `test_worlds.py` included. Take: not now. Revisit
  if a second World carries a data set.
- **The plan's size.** Every curation test writes every record, so a bigger plan makes curation slower. The design
  above plans roughly what the sample does (some 60 records). Take: count the records once the World is built, and
  cut recipes if it plans many more.
- **Making the remote engine reachable.** Take: not in this run. Its base URL is in its digest, so a free port per
  test would mean a new engine per test.

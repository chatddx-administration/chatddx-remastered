# The test World: work in progress

The tests ran on the sample: its data set (`worlds/sample/_data/`) and its World (`worlds/sample/`). The sample is
curated for preliminary calibration, with work queued on it (judges from Olof's notes, maybe revised targets:
`agents/wip-judges.md`), and it exercised only part of what a data set and a World can say. This file plans a World
built for the tests, `worlds/test/`, and moving every test onto it but the sample's own.

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Where it stands
- The fixes found on the way are in (see "Fixes before the move").
- **The World is built**: `worlds/test/` and `worlds/test/_data/`, as "What it exercises" lists them. It plans 68
  records, 24 of them skeletons, with the 12 skips and 7 lint warnings it is built to give, and loads cleanly with a
  giftbag in 1.6 s.
- **The harness is built** (see "The harness").
- **The move is done.** Every test runs on the test World but the sample's own (see "What stays on the sample"):
  620 pass, 522 of them in the quick run, which takes 23 s. The whole run took 59-69 s before the move and 62-65 s
  after, on a machine whose runs spread wider than that.
- Next: **the tests of what only the test World reaches** (see "Not read yet"), so that every row of "What it
  exercises" is read, as principle 1 asks.

Found on the way:
- **`qwen3@fake` and `gpt-oss@fake` are the sample's fake engines**: a name is no part of a digest, and their
  fields are the same, so a store loaded with both Worlds holds one engine under two names.
- **The fakes refuse what the `vllm.*` lints predict.** `test_worlds.py` checks it on every skeleton and fake
  endpoint of every World: `qwen3-bare@fake` and `mistral@fake` refuse a thinking budget, `qwen3-bare@fake` refuses
  every request with tools, and `mistral@fake` answers tool requests in text.
- **The API lets a person make a configuration that is the archive's under another name.** Alice's hand-made recipe
  of clinician, case, lines and greedy compiled to `lines-instructed (en)`'s skeleton, and was saved as a thread of
  her own with no finding; an expectation the same as one she holds is refused. `api/test/test_writes.py` now makes
  one that is new.
- **`reasoned (en, Qwen/Qwen3-8B-AWQ)` shows its reasoning as `on (Qwen/Qwen3-8B-AWQ)`**: for Qwen3 `high` collapses
  to `on`, the two chunks have one digest, and a title picks one name.
- **Many `slow` tests aren't slow any more**: 40 of the 98 marked take under 0.2 s a call now, most of them 0.14-0.19 s,
  and two unmarked ones that the move didn't touch, `api/test/test_people.py::test_the_api_describes_itself` and
  `api/test/test_variations.py::test_a_request_names_the_recipe_s_parts`, take 0.26-0.28 s. The markers are as they
  were (see "Open").

## Decided
- **A test World, `worlds/test/`, with its data set inside it, at `worlds/test/_data/`.**
- **The sample keeps one test module**, `src/chatddx/test/test_sample.py`, with what is true of the sample
  alone. What should hold for every World is checked on all of them (see "What stays on the sample").
- **Names say what they exercise**, not what the sample called them.
- **The test World's tools are the test tools** (`src/chatddx/runner/test/tools.py`). The root conftest ships them
  for the whole session, as `runner/test/conftest.py:shipped_tools` does for the runner's tests now, so planning
  takes their entry points. So the test World loads only under pytest: `chatddx init-data` by hand refuses its
  toolset. The sample is for hand use.
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

Loading it stays explicit: `chatddx init-data alice --world worlds/test --data worlds/test/_data`. Its one directory
source is the default `--source`.

Since the sample's data set moved to `worlds/sample/_data/`, init-data takes a World's `_data/` when `--data` names
none (`docs/curation.md`, "Data sets"), so `--data` can be left out here too; the test World still loads only under
pytest.

## Principles
1. **Every record is read by a test.** The table under "What it exercises" names, for each record, the test that
   reads it. A record no test reads isn't added.
2. **Counts come from the data.** A test derives what it counts from the plan, the cases or the inventory. Literal
   counts, skip lines and lint lines appear only in the test World's own test.
3. **What `curated` loads holds no mistakes.** Its only findings are the ones the design calls for. Broken data
   (an invalid expectation, an unreachable view, a misplaced clearance) is an edit a test makes to a copy of the
   World (`copied` and `edit` in `src/chatddx/test/world.py`).
4. **The test World's own test pins its design**: the records per table, the skip lines, the lint lines and the
   World's findings (`src/chatddx/test/test_the_test_world.py`), and `test_worlds.py` that each endpoint
   names the digest of the engine planned under its name. A change to the World fails there first, with the new
   values in the message.
5. **Names are spelled once.** `src/chatddx/test/world.py` holds the names tests share: models, endpoints, the
   recipes most tests run, and the cases. Case and tag ids are written as they are, since each says what it is.
   Helpers one package's tests share stay in its `test/helpers.py`.
6. **Tests don't pin layout by accident.** Repl tests that pin column widths through the length of a scorer's name
   (`repl/test/test_inspecting.py`, `test_reviewing.py`, `test_running.py`) match on cells instead.

## Layout
```
worlds/test/
  inventory.toml   sources, clearances, judge bindings, and include = ["endpoints.toml"]
  endpoints.toml   endpoints and the host
  engines.toml     models, local engines, the remote engine
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
| `mistral@fake`: the made-up `test/mistral-7b`, facts from the World's `facts.toml`, no tool flags, `max_jobs = 2` | a World's facts; the fake's Mistral family, which sends tools unconstrained; facts that refuse reasoning and the tool contract (`facts.output_refused`) | nothing (World facts only in `test_init.py`'s synthetic gemma) | new planning and fake tests |
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
| `lines` | text, guidance | free text; `lines@1` |
| `raw` | text, no guidance (in `factors.toml`) | `language.unknown`, with the prompt `case` |
| `verdict` | native, `verdict.json`, whose `meets` has the examples `true` and `false` | a judge's output; seeds that disagree on the fake |
| `grade` | native, `grade.json`: `points` 0–2, with three examples, and `why` | a judge's verdict on a scale |

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
| `lines-guided` | a fork of `lines-instructed`, `greedy`; instructions `clinician` (developer role, `output_guidance` insert), few-shot `worked-example` (one exchange), passthrough `min-tokens`, translations `guided`, `appendix_layout` | made in en and sv; a translated output and appendix layout; a fork across languages, `lines-guided (sv)` of `lines-instructed (en)` |
| `lines-instructed` | `greedy`, instructions `clinician`, no translations | `[skipped]`: "needs translations in sv" |
| `headed` | `greedy`, instructions `clinician`; the prompt `headed`, which holds text and a `tool_guidance` insert and exists in en only; toolset `lookup` | the toolset's guidance placed in the prompt; `[skipped]`: "it has no prompt in sv" |
| `raw` | `greedy` | `language.unknown` |
| `reasoned` | `recommended`, reasoning `high` | reasoning in a skeleton; `facts.reasoning_unmatched`; `[skipped]`: "the facts refuse its reasoning" for `test/mistral-7b` |
| `budgeted` | `greedy`, reasoning `on-budget` | `vllm.thinking_budget_refused` on `qwen3-bare@fake`; `facts.budget_refused`; skipped where the facts refuse a budget |
| `clamped` | sampling `near-greedy` (temperature 0.005) | `vllm.temperature_clamped` |
| `judge` | purpose `judge`; the prompt `judge` with the `completion` and `expectation` slots; output `verdict` | a judge skeleton, for the judge tests in `scorers/test/test_scorers.py` |
| `judge-graded` | purpose `judge`, the prompt `judge`, output `grade`, `recommended` | a sampled judge's skeleton, made per model |

Judges (`agents/wip-judges.md`, "The test World's additions"), read by `curation/test/test_judges.py`:
- `verdict`: `judge` on `qwen3@fake`, seed 1;
- `graded`: `judge-graded`'s variant for Qwen3 on `qwen3@fake`, seeds 1, 2 and 3;
- `remote`: `judge` on `unknown@remote`, which gives `facts.missing`, and which the gate is to refuse.

The scorer `judged` (`chatddx.scorers.metrics:score`, schema `targets`): a pattern view, the differential line by
line, beside three judged views over carol's note: `note-comment` and `note-answer` under `verdict`, and
`note-graded` under `graded`. Read by `runner/test/test_score.py`, and listed wherever a `lines` run's scorers are.
The scorer `judged-remote` judges carol's comment on `remote`, and applies to no run, since `unknown@remote` is cleared
for nothing (`bench/test/test_seen.py`).

Other records:
- **Sampling**: `recommended` (`from_facts`), `greedy` and `near-greedy`. The bench's and repl's tests swap in
  `greedy`, as they swap in the sample's now.
- **Reasoning**: `off`, `on` and `high` from the facts, and `on-budget` with a budget. The repl's choosing tests
  swap in `off` and `on`.
- **Tools**: `lookup` and `broken` from the test tools, in the toolset `lookup` with `max_rounds = 2` and guidance.
- **Expectation schema**: `targets`, the sample's kinds (diagnosis, warning or false, disposition, dont_miss,
  notes), requiring `diagnosis`, with no other properties allowed.
- **Tags** on recipes: `structured`, `text`, `tools`, `reasoning` and `judge`.
- **A canary set**, `probe`: one seeded probe, read by `curation/test/test_tables.py`.
- **An appendix and a case that sends it**: `whitespace`'s `labs`, and `whitespace with labs`, held to targets of its
  own; read by `curation/test/test_tables.py`, and counted by the curation tests that count what a load lands.
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
| `matched` | en | plain | diagnosis, warning and disposition patterns the fake's answers match (`fake & diagnosis*`), so a score isn't 0 |
| `dont-miss` | en | plain | `dont_miss`, `warning = false`, a disposition with text and no pattern |
| `noted` | en | plain | notes in Swedish, carol's with an `answer` and dave's without |
| `svenska` | sv | å, ä, ö in NFC | diagnosis |
| `nfd` | sv | the same letters decomposed (NFD) | diagnosis |
| `mislabeled` | sv | English text | diagnosis |

Every case has a tag: `bytes` (crlf, bom, whitespace, nfd), `targets` (crlf, matched, dont-miss, noted), and
`swedish` (noted, svenska, nfd, mislabeled). They overlap, and `targets` holds only English cases, which the tests of
tag unions and `language.mixed` need.

Kept out of the World and made by the tests that need them:
- a vignette that isn't UTF-8;
- renamed and changed vignettes, through `MemorySource` (`src/chatddx/inventory/test/memory.py`) or a copy;
- an invalid expectation, an invalid expectation schema, a second expectation schema;
- a view that reaches nothing (`view.unreachable`);
- `cleared.not_sensitive`, `endpoint.remote_host`, `endpoint.shared_url`, `host.unpinned` and
  `endpoint.engine_unknown`.

## The harness
Built (`src/chatddx/test/world.py`, `src/chatddx/conftest.py`):
- **A module for what the tests import, the conftest for fixtures.** pytest loads a conftest itself, to give the
  tests under it fixtures and hooks; it isn't meant to be imported. The tests import helpers from the root conftest
  today (`from chatddx.conftest import …`), which works only because it sits inside the package. So what they import
  goes in a plain module, `src/chatddx/test/world.py`: the Worlds' paths, the names tests share (models, endpoints,
  the recipes most tests run), `world_plan`, `free_world`, `freed`, `faked`, `copied` and `edit`. The conftest keeps
  the fixtures built on them.
- **`world_plan(world, data)`** plans a data set with a World's engines and facts, as init-data does, and
  `world_facts(world)` gives those facts; `test_sample.py`'s `sample_plan` is `world_plan` of the sample.
- **`curated` loads the test World** for alice with her giftbag, and `plan`, `world` and `fake` are the test World's.
- **`free_world` rewrites the parsed inventory**, giving each local endpoint a free port of its own; it used to replace
  the strings `12099`, `12100` and `path = "vignettes"` in a copy of the file. `freed` writes such a copy, for the
  commands, which read a World from its directory.
- **`copied` and `edit`**: a copy of a World, `_data` included, and a text edit of one of its files, for the broken
  data above.
- **The root conftest ships the test tools** for the session.

`connect` and the other database helpers are still imported from the root conftest; what the tests import of the
Worlds comes from `src/chatddx/test/world.py`. While the tests moved, the sample's template was `curated_sample` and
each package not yet moved pinned its fixtures to the sample; both went with the last package.

## The move
Done, a package at a time with `pytest` green after each: inventory, fake_vllm, scorers, runner, curation, then
bench, api and repl, which three subagents moved side by side. curation's `few`, `FEW` and its own `world` fixture
went, its tests loading the test World's nine cases whole, and the packages' `sample.py` helper modules became
`helpers.py` (bench, repl) and `cases.py` (curation).

The tests that asserted what was true of the sample by chance assert the test World's design now:
- the cases without a `dont_miss` are the ones missing from its reach (`api/test/test_variations.py`,
  `repl/test/test_inspecting.py`), derived from the data;
- the configurations table shows a reasoning column (`repl/test/test_listing.py`);
- a batch over `targets` scores `matched`'s hit (`repl/test/test_running.py`);
- counts, tags, languages and case names come from the data set, and rows are matched by cell, not padding.

### Not read yet
What only the test World reaches, and no test reads yet:
- the gate's refusals on `qwen3-bare@fake` (not cleared for `typed`) and `unknown@remote` (cleared for nothing, and
  its secret unset);
- the pair lints asserted by code: `vllm.tools_refused`, `vllm.thinking_budget_refused` and
  `vllm.grammar_before_reasoning` on `qwen3-bare@fake`, `vllm.temperature_clamped` (`clamped`),
  `facts.output_refused` (`tool-answer` on `mistral@fake`), `facts.missing` and `schema.ref_unverified` on
  `unknown@remote` and its absence for `native-inlined`, `facts.reasoning_unmatched` and `facts.budget_refused`
  (Qwen's `reasoned` and `budgeted` on `gpt-oss@fake`), and `language.unknown` (`raw`). `test_worlds.py` uses the
  `vllm.*` ones to tell refusals apart but asserts none;
- the judge skeleton, which `scorers/test/test_scorers.py`'s judge tests could use instead of a synthetic one;
- the toolset's guidance placed in `headed`'s prompt, `lines-guided (sv)`'s translated output and appendix
  layout ("Bilagor:"), and the passthrough;
- the vignettes' quirks under the cleanup ops (`prepare_case` with `newlines.lf@1`, `unicode.nfc@1`, `strip@1`,
  `blank_lines.collapse@1`).

## What stays on the sample
`src/chatddx/test/test_sample.py`, the sample's pins, `solidified` (`docs/curation.md`, "Tests"):
- **Vignettes**: they are 7893656's (`test_the_sample_world_holds_the_vignettes_at_7893656`).
- **Cases**: 79 English and 20 Swedish, and the language of `casesfromedn1` and `Dutchfall11w`.
- **Records**: the English and Swedish sets, the nine recipes per model and `judge (en)`, and the translations'
  coverage.
- **Targets**: the targets schema's rules and Olof's notes on three cases, as written.
- **A load**: with only its eleven skips (the reasoning Mistral Small and harmony refuse) and its fakes' lints,
  `plan-shown` varying `plan`'s output.
- **Kompismoln**: it takes the sample's vignettes.

`src/chatddx/test/test_worlds.py` checks every World in `worlds/` (test, sample, Kompismoln) with its data set,
and fails when a new World isn't given one:
- each endpoint names the digest of the engine planned under its name, and the World's check finds nothing;
- init-data binds each World's endpoints and leaves the others' engines out;
- every target's pattern reads;
- each fake endpoint answers each skeleton as its contract asks, or refuses it exactly when a `vllm.*` lint says
  vLLM would;
- what the fake writes holds to each data set's schemas.

## Fixes before the move
Found while surveying, each to be talked through with the user and then fixed and tested on its own:
- **Done (decided): `init-data --source typed` ended in a traceback.** A database source lists nothing now:
  `ListingSource` (`src/chatddx/inventory/sources.py`) holds `ids`, `fetch` and `cases`, `init` and `repair` take one,
  and `Inventory.listing` refuses a database source. `--source` defaults to the World's only listing source, for
  init-data and repair-data alike. The docs have AGENT suggestions.
- **Done (decided): `free-text-guided (sv, …)` was planned as a fork of nothing.** A variant now forks its origin in
  the origin's one language when it has no variant in the variant's (`src/chatddx/curation/plan.py:plan_factors`,
  `base`), so `free-text-guided (sv, …)` forks `free-text (en, …)`. An origin written in several languages, none the
  variant's, is refused. A variant whose origin has none for its model is loaded as no fork and reported, as is one
  made without a model whose origin is made per model. A re-run of init-data reports a held thread whose origin
  differs from the data's (`src/chatddx/curation/write.py:_Init.forked`, `Catalog.origin`), since an origin is set
  only when a thread is created; archives loaded before this keep their Swedish variants unforked, and say so.
- **Done (decided): `scorer.revision` was documented but never raised.** It went with `Scorer` v2, as
  `agents/wip-authoring.md` ("Lints") decided, and two docs lagged: `docs/factors-api.md` and `docs/curation.md` have
  AGENT suggestions dropping it. `test_init.py`'s `revision` fixture, which kept the lint quiet, went too.

## Docs
- `docs/curation.md`, "Data sets" and "Tests", and `docs/inventory.md`, "Worlds": AGENT suggestions for the test
  World and `_data`.

## Open
- **The plan's size.** Every curation test writes every record, so a bigger plan makes curation slower. Built, it
  plans 68 records to the sample's 60 (24 skeletons to 18), with 9 cases to 99. Take: keep it; its own load is
  quicker than the sample's, and the curation tests drop to it from loading the sample's records.
- **Making the remote engine reachable.** Its URL is its endpoint's now, not part of its digest, so `free_world`
  could give it a free port as it does the fakes. Take: not until a test needs a remote engine to answer.
- **The `slow` markers.** AGENTS.md marks a test whose call takes 0.2 s or more. 40 marked tests are under it now and
  two unmarked ones over it (see "Where it stands"), most within a run's noise. Take: re-mark by a few timed runs
  rather than one, once the new tests are in.
- **`another_expectation` is imported across packages**: from `bench/test/helpers.py` by the API's and the repl's
  tests, as from `bench/test/sample.py` before. Take: leave it; it builds on the bench they all drive.

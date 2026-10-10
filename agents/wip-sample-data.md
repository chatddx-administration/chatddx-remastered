# Sample data: work in progress

"The sample data" is the old chatddx inventory: chatddx-administration/chatddx at 7893656, with
`src/chatddx/data/inventory.toml`, `giftbag-inventory.toml` and the vignettes in `src/chatddx/data/cases/`. It is
hand-edited into remastered's shape, with no adapter, and spreads over remastered's channels: factors, cases,
catalog, and the World inventory (`docs/inventory.md`). The word "inventory" keeps its glossary meaning.
The vignettes are copied into `worlds/sample/` (see "The sample data now").
Permalink base: https://github.com/chatddx-administration/chatddx/blob/7893656c143154e0421af0a85298177c347502e3/

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

This file also holds what `docs/sample-data.md` said, so that doc can go. The gaps found while porting (G1–G18) are
all fixed but one. Each is condensed to where its result is described now and what is still open. The full
write-ups are in git history: `git show 79ec890:agents/wip-sample-data.md`.

## Start with this
The endgame is parity with the old `init-data`. Everything is in but the real engines: the configurations and cases,
the tool and scorers, and the two fake engines with their endpoints (see "Engines and endpoints"). What's left, in
order:

### 1. Import the real engines from their hosts' reports (decision 4A)
The old `qwen3-8b-awq@pelle`, `qwen3-8b-awq@malborg` and `gpt-oss-20b@malborg` get seeded from values read on the
hosts, not guessed. Most of the old data for them was guessed, malborg's vLLM 0.13.0 among it, and a guess in an
engine lands in its digest, which is its served name and the key of every trial. Today pelle serves `qwen3-8b` and
malborg `gpt-oss-20b` (Kompismoln/org f05f153, `hosts/*/configuration.nix`); malborg no longer serves Qwen.

The hosts run vLLM through o11n's `o11n.vllm` (Kompismoln/o11n, `nixos/vllm.nix`), each server in a NixOS
container, and its report endpoint (`o11n.vllm.report`, `nixos/vllm-report.py`) gives what an import needs. That
replaced the planned `import-engine` run on a host, which would have read `nvidia-smi` and `/proc` itself.

1. **Settled by o11n and org** (the user's, through o11n 2a874df and org 6528f10):
   - **Which chat template each engine runs**: the file `chatTemplate` names, now required. vLLM then reads it for
     every request, and the report hashes it and compares it with the model's own. Pelle's is `tokenizer_config.json`'s
     template (same text, plus a trailing newline); malborg's is the repo's own `chat_template.jinja`, which vLLM
     doesn't read for gpt-oss (it renders with Harmony), so its hash pins nothing.
   - **Malborg's Harmony date**: `VLLM_SYSTEM_START_DATE = "2026-10-07"`, in the engine's env and digest.
   - **The report endpoints**: enabled on both hosts, at `pelle.km:12008` and `malborg.km:12008`.
   - **Where the real World lives**: `worlds/kompismoln/` (`docs/inventory.md`, "Worlds"),
     with the factors `import-engine` writes in `worlds/kompismoln/factors.toml`. `init-data --world
     worlds/kompismoln/inventory.toml --factors worlds/kompismoln/factors.toml` seeds the sample with them, and
     `src/chatddx/curation/test/test_init.py:test_init_data_command` checks that it binds each endpoint and seeds no fake.
   - **What a model's files are**: every file of the snapshot at the pinned commit, as the report hashes them, with a
     snapshot that holds only what vLLM needs. A list of only what vLLM reads would have to follow vLLM's loaders per
     version and model, and missing a file means missing a change: with `--generation-config auto` (the default)
     `generation_config.json` sets the sampling of every request that doesn't
     (https://github.com/vllm-project/vllm/blob/v0.24.0/vllm/config/model.py#L1400-L1470). gpt-oss's repo also has
     `original/` and `metal/`, the weights in other formats, which vLLM never reads: it takes the root's
     `*.safetensors` listed in the index
     (https://github.com/vllm-project/vllm/blob/v0.24.0/vllm/model_executor/model_loader/default_loader.py#L208-L232).
     Malborg's cache was downloaded again without them (52d728b): the other files' hashes are the same, and the model's
     digest went from `c642e8` to `1c249b`, the engine's from `9a5ca7` to `598792`. vLLM then wouldn't start: given a
     model ID offline, it resolves it with huggingface_hub, which refuses a snapshot missing any file of its commit
     (`docs/vllm.md`, proposed item 23). o11n now gives vLLM the snapshot's directory (Kompismoln/o11n 84612b2), and
     `import-engine` records that directory as the host's location for the model. The digests don't change.
2. **Decided since:**
   - **Decision 1, B**: `from_facts` records are written for the models the planned engines serve and the
     facts know (`src/chatddx/curation/plan.py:plan_factors`, which plans models and engines first). A served model
     without facts and a known model without an engine are reported as skipped. The sample's seeding is unchanged:
     its engines serve the two models the facts know. With it came `facts.sampling_unmatched`, a pair lint for a
     skeleton whose sampling was written for another model (`src/chatddx/facts/lint.py:_sampled_for`); `docs/facts.md`
     has proposed amendments for both.
3. **Done: `chatddx import-engine`** (`docs/inventory.md`, "Importing from a host"). The digests it writes are the
   ones init-data loads.
4. **Imported** (chatddx-remastered 5760e10), and every value checks out: the digests recompute, the lints are clean,
   and `start_up` gives o11n's command line. But the runtime root was named after its server and built with the host's
   package set, so the closures differed between the hosts for the same packages and would have moved with every
   update of o11n's nixpkgs. Fixed in o11n b84e960 (`vllm-runtime`, from the container's package set) and imported
   again (973dd61): both hosts now report the same runtime root.
5. **Seeded and checked** (52d728b). `init-data alice --world worlds/kompismoln/inventory.toml --factors
   worlds/kompismoln/factors.toml` creates the two models and engines, their lints are clean, and each World endpoint
   serves the engine it names: `qwen3-8b@pelle` `sha256:a6845f87…`, `gpt-oss-20b@malborg` `sha256:598792a2…`. With o11n
   84612b2 deployed, importing again (9eab37a) changed only `worlds/kompismoln/endpoints.toml`'s model locations, from
   repo IDs to snapshot directories; the factors and digests stayed the same.
6. **Served under their digests.** Each engine's digest is first in its server's `servedModelNames` (responses carry
   the first name), and the import of 9eab37a reports no `endpoint.served_name`: both servers answer under their
   digests, so `confirm` passes. The served names aren't part of the digest, and the import changed none.
7. **Optionally, check against Hugging Face** (4B as a check, not a source), offline. huggingface_hub keeps the
   commit's file listing from the download (`<repo>/trees/<commit>.json`): the hub's SHA-256 for each LFS file and
   the git blob hash for the rest. The report could compare every hashed file with it, with no network.

### 2. Then the small parity items
- Done (decided): `init-data` creates USER when missing, named by the login and without roles, as the old one did;
  `chatddx person add` and `person password` remain for the rest.
- Done (decided): `chatddx wipe-data USER` deletes what USER owns and unshares what they collaborate on, a
  `deleted` entry and a collaborator entry with `present` false, each written only when it changes something
  (`src/chatddx/curation/write.py:wipe`). The person and the archive stay; `wipe-data archive` is refused. Kept to a
  minimum on repeated `init-data`/`wipe-data`: no thread is created again, `init-data --giftbag` restores the forks
  `wipe` deleted rather than forking anew, and a cycle writes one entry per gift and per share
  (`src/chatddx/curation/test/test_init.py:test_wipe_data_deletes_and_unshares_and_init_data_gives_it_back`).
- Done (decided): the old target format's `dont_miss`, `warning = false` and `text`, which no case used, are in
  `targets.json` and the sample's scorers, to show how an output, a view and a scorer meet
  (`src/chatddx/scorers/test/test_scorers.py`, the three tests after `sample_scorer`):
  - `dont_miss`, the diagnosis an answer mustn't miss, is read by a `dont-miss` view (`mentions`) in three scorers:
    the plan's reads only the diagnoses the plan marks critical (`$.diagnoses[?@.critical == true].diagnosis`, the
    old `critical` view), while the list's and the free text's (`lines@1`) read any diagnosis named;
  - `warning = false`, the only target that may be false, is met by a plan whose nullable `acute_warning` is null;
  - a target is `text`, `pattern` or both. The pattern views leave a words-only target unscored ("the target has
    words, for a judge, but no pattern"), and a judged view would read `/diagnosis/text`. No sample view is judged,
    since `score` refuses a scorer with one until judges can run.

### After parity
The free-text expectations' judges (see "Parked", "Free-text expectations"), and the runner, which runs trials
without tools on the fake engines (`agents/wip-runner.md`).

## Decided
- Seed now: chunks, recipes (as compiled skeleton threads), cases with their families, an expectation schema and
  expectations.
- Deferred: scorings (old D9), which come from a separate runtime-data pipe. The `init-data` command and the
  compiler's `Code` (old C8) are done. Engines and models were deferred too, until their locations and values were
  decided, and so were scorers, until it was decided where their code lives.
- Tools and scorers pin chatddx's own code, as compilations record their compiler: `Code` from `rig()` and an
  `entry_point` in chatddx. Packaging entry points can come later, for tools and scorers together.
- Engine locations live in the World inventory (decision 2A): endpoints and hosts (`docs/inventory.md`). A remote
  engine keeps `base_url` in its digest.
- Engine values come from the hosts (decision 4A), with the fake engines first, whose values are ours (4D). No
  placeholders.
- The scorer interface, version 1, is the old one fed through remastered's views: the entry point takes a view's
  metric, the items its output selector picks (none without an answer), the items its expectation selector picks,
  and the params, and gives a value and a detail.
- Base the sample data on 7893656. Quirks found while tweaking it, such as 13d317d's rename and the
  `DutchFall10w`/`Dutchfall*` spelling, are welcome stress tests.
- Olof's comments on the cases (13d317d, 504792c) are the foundation for a free-text expectation scored by
  judges. They're in the sample as `targets.notes`, and the vignettes stay on 7893656 (see "Parked", "Free-text
  expectations").
- `max_tokens` is dropped from sampling.
- Instructions: the hand edit changes the mechanism but keeps the spirit; remastered must support the same things
  (G3).
- The vignette files are a fake-sensitive source (G11). Fingerprints are over the raw bytes.
- The expectation schema is hand-written into the new sample data.
- The `# guessed` markers on targets are dropped on import, and the data is treated as live.
- The sample data lives in the repo (`src/chatddx/data/sample/`), with the vignettes named by the World inventory.
- The 99 vignettes are copied into the repo and kept under VCS. They aren't sensitive, but are treated as if they
  were.
- Model-dependent chunks come per model, from the facts.
- Re-runs are created, validated or updated, keyed by kind, name and the archive as owner.
- The giftbag is forks.
- Flags were renamed after first use: the old `--inventory` (what to seed) is `--data`, the World inventory is
  `--world` so "inventory" isn't read in its old sense, and `--vignettes DIR` replaces the World file with a plain
  directory.

## The sample data now
`src/chatddx/data/sample/` holds:
- `factors.toml`: chunks and recipes, from the old slices and configurations. Its header comment gives the format.
  Tables are kinds, keys are component fields, and references name records. On top of that, `json_schema_path`
  loads a JSON file, `from_facts` writes a chunk per model, `fork_of` seeds a record as a fork, and `tags` and
  `description` are catalog entries.
- `cases-en.toml` and `cases-sv.toml`: the 99 cases by language, 79 and 20, each with its tags and targets, without
  the `# guessed` markers.
- `schemas/`: the two output schemas and the hand-written `targets.json`.

`factors.toml` also holds the old tool, toolset, `plan-web` and scorers (see "Tools and scorers"). The two sample
models' facts are bundled with chatddx (`src/chatddx/facts/models.toml`), and the old fake stacks' models and engines
are the sample World's (`worlds/sample/factors.toml`, see "Engines and endpoints").

The vignettes aren't in it: they're a fake-sensitive source, so they stay out of the package. `worlds/sample/` holds
them as a World would:
- `inventory.toml` is the sample World inventory (`docs/inventory.md`, "Worlds"), and
  `factors.toml` its fake engines.
- `vignettes/` has the 99 files of 7893656's `src/chatddx/data/cases`, byte for byte (their git blob hashes match the
  old repo's). 30 of them mix CRLF and LF line endings, so `.gitattributes` marks the directory `-text` to keep git
  from converting them.
- `src/chatddx/curation/test/test_init.py:test_the_sample_world_holds_the_vignettes_at_7893656` pins their ids, checks
  that they decode as UTF-8, and pins one fingerprint over all their fingerprints, so leaving 7893656 takes a
  deliberate edit.

`init-data` takes the World from `--world DIR`, or `CHATDDX_WORLD`, which `.env-container` and `.env-devshell` set to `worlds/sample`.

### What changed in the hand edit
- `instruction.ddx` and `instruction.bare` collapse into `prompt.case`; bare is the same prompt with `output.raw`.
- `reasoning.default` is no chunk: a recipe without a reasoning chunk leaves reasoning to the model. No recipe uses
  one, so the reasoning chunks are seeded as threads of their own.
- `sampling.recommended-4k` is gone with `max_tokens`.
- `configuration.plan-web` is `recipe.plan-web`, a fork of `plan` with `toolset.web`. Its tool's code is the old
  `chatddx.runtime.tools.web_search`, ported to the standard library as `chatddx.tools.web_search`.
- The four old scorers are views of four scorers, one per output shape (see "Tools and scorers").
- `coercion.*` is folded into outputs (G4, G5), and `extends` became `fork_of` (G9).
- `dont_miss`, a target kind in the old schema (`src/chatddx/repo/entities/case/pydantic.py:22`) and in
  `docs/clinical-input.md`, is in `targets.json`, with `warning = false` and a target's `text` (see "Then the small
  parity items"). No case has one.

### init-data
What `init-data`, `repair-data` and `wipe-data` do is `docs/curation.md`'s (`chatddx.curation`). The history of the
parity checks stays here.

The old checkout's vignettes were checked in a scratch database:
- the first run created 236 records and 136 giftbag forks;
- a re-run validated all 236 and kept every fork;
- against the 13d317d checkout, 230 were validated, the renamed `DutchFall10w` was missing, and `Dutchfall11w` and
  `casesfromedn1` needed repair. That matches G13's survey;
- against 504792c, the head of `new-datamodel` on 2026-10-05, 228 were validated: `Dutchfall1w` needs repair too;
- through `--world worlds/sample/inventory.toml`, on a database seeded from the 7893656 checkout, all 236 were
  validated and every fork kept;
- once the tools and scorers were added, the same database got the tool, the toolset, 4 scorers and the 2 `plan-web`
  skeletons created, with the tool, toolset and skeletons forked for alice, and a re-run validated everything;
- once the fake engines were added, it got their 2 models and 2 engines created, and both sample endpoints reported
  the engine they serve.

Tests: `src/chatddx/curation/test/`.

## Engines and endpoints
Decisions 2A and 4D, done. Endpoints, hosts, the sample World, start-ups and `confirm` are `docs/inventory.md`'s.
The sample's side:
- **init-data** takes `model`, `local_engine` and `remote_engine` tables, and resolves every reference by name in
  one place (`REFERENCES` in `src/chatddx/curation/plan.py`). Engines aren't gifted, as the old giftbag gave no stacks.
- **The fake engines** (`worlds/sample/factors.toml`): the old fake stacks' models and flags. Since they're the
  sample World's, seeding another World doesn't seed them, and seeding the sample takes `--factors
  worlds/sample/factors.toml`. Every value is ours and says what it
  is: the real repo, so its facts apply, with revision `fake` and one empty file for no weights; no GPU; the runtime
  `0.24.0+fake` run by `chatddx fake-vllm` rather than a Nix closure; an empty chat template. So `init-data`'s lints
  give each fake model `model.revision` and each fake engine `engine.closure`, four warnings on every run.
- **The sample World** has an endpoint per fake engine, since vLLM serves one model a process.
- **init-data** ends with the inventory check's findings (`src/chatddx/inventory/check.py`; `docs/inventory.md`,
  "Reaching an engine").

## Tools and scorers
Where tool and scorer code lives is settled (see "Decided"):
- **Code.** A `tool` or `scorer` record without a `code` pins the running chatddx, the `Code` compilations record as
  their compiler (`src/chatddx/curation/plan.py:plan_factors`). `src/chatddx/core/rig.py:entry` finds an entry point's
  function, and runs only the running chatddx: other pinned code is refused, not run unpinned. Planning refuses an
  entry point that names nothing, and a view whose metric the scorer's code doesn't know (`Metrics.names`). Since the
  code is part of a tool's and a scorer's digest, a new version or `CHATDDX_REVISION` makes new ones, and the
  toolset and `plan-web` skeletons with them.
- **Scorer interface, version 1** (`src/chatddx/scorers/scorer.py`). An entry point is a `ScoreFunction`: it takes a
  view's `metric`, the items its output selector picks (`None` without an answer), the items its expectation
  selector picks, and the scorer's params under the view's. It returns `Scored(value, detail)`, what a `ScoreItem`
  keeps. `score(scorer, run, answer, data)` applies every view; `function(scorer)` finds and checks the entry point.
- **The pattern scorers** (`src/chatddx/scorers/patterns.py`): the old matcher and `reciprocal_rank`,
  `first_mention` and `mentions`, unchanged in what they find, behind `score`, a `Metrics` of the three. A target is
  the expectation selector's one item: a target object with a `pattern`, a pattern, or `false` (nothing expected).
  No target, or one that doesn't read, gives no value, with the reason in the detail. A null output item names
  nothing, so a plan's `acute_warning: null` is no warning. The old aggregates are in `aggregate.py`.
- **The sample's scorers.** The old scorers each read a named view of whichever output had it. Here selectors bind a
  scorer to a shape, so there are four, with the old view names as catalog labels (`Catalog.label`):
  - `plan`: `differential` (`reciprocal_rank`), `warning`, `disposition` and `dont-miss` (`mentions`), the last
    over the diagnoses the plan marks critical;
  - `diagnoses`: `differential` and `dont-miss`;
  - `free-text`: `text` (`first_mention`, the whole text), `differential` and `dont-miss` (lines);
  - `raw`: `text`. No sample configuration uses `output.raw`, as in the old inventory.
- **The tool.** `chatddx.tools.web_search` is the old tool on `urllib`, with the old record's name, description and
  parameters, in `toolset.web` with its guidance. It sends the model's query to DuckDuckGo, a third party, so the
  clearance hard block must cover it (`agents/wip-clearance.md`, "Tools"). The runner runs tools, and its gate
  refuses them on a sensitive source, the sample's included.
- **init-data** writes the labels, gives USER a fork of the tool as the old giftbag did (scorers stay the
  archive's), and lints the scorers on landing.
- **Tests**: `src/chatddx/scorers/test/`, `src/chatddx/tools/test/`, and `src/chatddx/curation/test/test_init.py`. One
  test builds an answer of each sample configuration's shape and checks that every view of the scorer reading it
  picks something.

## The fake vLLM
`src/chatddx/fake_vllm/` is the old fake (`src/chatddx/dev/fake_vllm.py` at 7893656), ported to vLLM 0.24 and to
how remastered names engines. `chatddx fake-vllm [--delay S] [--runaway] MODEL [vllm serve's flags]` serves it.
Items are `docs/vllm.md`'s; 13–20 are among its proposed amendments.
- **`served.py`**: what `vllm serve MODEL` with its flags sets up (`Served.of`). Flags are read as vLLM reads them:
  `_` for `-`, the last one wins, `--config=FILE` is ignored, and `--config FILE` is refused because the fake can't
  read YAML. It reads `--served-model-name` (so an engine is served by its digest), `--max-model-len`,
  `--reasoning-parser`, `--reasoning-config`, `--enable-auto-tool-choice`, `--tool-call-parser`,
  `--default-chat-template-kwargs`, `--fingerprint-mode`/`--fingerprint-value`, `--host` and `--port`. It won't
  start where vLLM won't (`--enable-auto-tool-choice` without a parser). How the model behaves comes from its name:
  Qwen3, gpt-oss (Harmony), Mistral, or none of these.
- **`chat.py`**: one request in, one response or stream out. `accept` refuses what vLLM 0.24 refuses, with its
  status, type and message: an unknown model (404), a bad `tool_choice`, tools without a parser (items 5 and 19),
  Harmony's efforts (item 17), and a thinking budget without reasoning set up (item 7). `respond` decides:
  - whether the model reasons: Qwen3 unless `enable_thinking` is false, which `reasoning_effort: none` and the
    server's default kwargs also set (item 16); gpt-oss always; and no model when a grammar holds the answer from
    its first token without `--reasoning-parser` (item 6);
  - where the reasoning goes: separated, left out (`include_reasoning: false`), or in the content without a parser;
  - what it answers: a named tool's call (finishing `stop`); under `required`, each toolset tool once and then the
    answer tool, which the compiler offers last; under `auto`, each tool once and then text, but nothing called when
    a `response_format` holds the answer (item 10); a document for a `response_format` or a schema shown in the
    system message; else three fake diagnoses, rotated by the seed unless the temperature is exactly 0 (items 2, 3),
    with the clamp logged as vLLM logs it.
  `completion` and `stream` give `prompt_token_ids` and `token_ids` only when asked (item 1), the served name as
  `model`, and `system_fingerprint` (item 15). A token is a word, and its id is a CRC of it, so the ids change with
  the prompt.
- **`server.py`**: `/v1/chat/completions`, `/v1/models` (item 14), `/version` (`0.24.0+fake`) and `/health`, with a
  delay between streamed tokens. A client that hangs up mid-stream is heard from the socket and logged.
- **Tests**: `src/chatddx/fake_vllm/test/`. They pin each behaviour above. They also render every sample skeleton
  for both sample models, served as the old inventory served them, and check each answer against its contract and
  schema, and they run a tool round through `next_request`.
- **Checked against vLLM v0.24.0's source.** This found that item 5 is imprecise: `required` and named tool choices
  need both tool flags, like `auto`. `docs/vllm.md` has proposed amendments for that and for items 13–20.

Left behind:
- the httpx transport (`FakeTransport`): the runner speaks HTTP through the stdlib (`src/chatddx/runner/wire.py`),
  and its tests run the real fake server;
- `chatddx samples` and `src/chatddx/dev/samples/` (`typical`, `broken`, `rich`): runs for the old history. The
  runner exists now; see "Sample runs".

Not faked yet:
- abbreviated flags aren't expanded, and bare arguments aren't refused: the fake can't tell a flag that takes a
  value from one that doesn't;
- `n` > 1, `stop`, `logprobs`, `echo`, `structured_outputs`, `chat_template`, `return_prompt_text` and
  `prompt_logprobs` are ignored, and so are the sampling settings beyond the temperature;
- a prompt longer than the context, or a `max_tokens` past it, isn't refused;
- the answer's JSON doesn't vary with the seed;
- unchecked against vLLM: gpt-oss without any parser answers `analysis…assistantfinal…`, taking Harmony's markers to
  be special tokens skipped in detokenizing; and Harmony with a tool parser but no reasoning parser still separates
  the reasoning;
- nothing yet runs the factors' `vllm.*` lints and the fake on the same cases, which would catch the two drifting
  apart.

## Sample runs
Not built. Everything here is a take.

### The old ones
`chatddx samples OWNER` (`src/chatddx/dev/samples/` at 504792c, 7ab7808) made three runs to look at, each answered by a
script rather than by the fake's own answers:
- **typical**: `plan` on `qwen3-8b-awq@fake`, `DutchFall10w`: thought through once and answered in one go, held to
  the plan's schema.
- **broken**: `plan-web` on `qwen3-8b-awq@fake`, `Dutchfall11w`: the search fails (503), the next call has an argument
  `web_search` doesn't take, and the server goes away halfway through the plan.
- **rich**: `plan-web` on `gpt-oss-20b@fake` with reasoning high and the tool contract, `Dutchfall14w`: thinking
  before every step, four rounds of searches, two made at once, an argument of the wrong type, a search that finds
  nothing, a word to the user beside the calls, and the answer through the answer tool.

Each script (`*.toml`) named a configuration, a stack, a case, a seed and what the cell set, then the turns: reasoning,
content, tool calls, and whether the server broke off after. Its `web` table canned what each search found. The runs
went through the old bench and `Sending` with an injected httpx transport (`Scripted`) and a patched `httpx2.get`, so
everything but the model's words and the web was genuine. Five tests checked them (`src/chatddx/dev/tests/test_samples.py`).

### Who they are for
Every edge: the repl's `replay` and `runs`, the API's runs and items, and the portal's run pages all want runs that
are genuine records of what can go wrong, without a real engine. So they aren't the repl's (`agents/wip-repl.md`, "Left
out"), nor the portal's.

### Where they belong
Take, by piece:
- **The scripts**: `worlds/sample/runs/*.toml`, beside the vignettes. Their reasoning and answers paraphrase the
  vignettes, so they are case-derived. The sample World's source is declared sensitive, as a real one would be, and
  kept out of the package (`worlds/sample/inventory.toml`); the scripts go with it.
- **Answering from a script**: the fake vLLM, as `serving(…, script=…)` and `chatddx fake-vllm --script PATH`. It
  answers each chat request with the script's next turn, streamed as `chat.py` streams, and can go away before the
  finish. The fake is to grow as sample data needs it (`AGENTS.md`, "Environment"), and stays a leaf: it reads a
  script, not the bench.
- **The web**: patched in the process that runs the tools, as before: `web_search` reaches DuckDuckGo through
  `urllib.request.urlopen` (`src/chatddx/tools/web_search.py`), and the tools run in the runner's process. A setting for
  the search URL would let the fake serve the web instead, but nothing else needs one.
- **The driver**: `src/chatddx/samples/`, an edge over the bench, as `agents/wip-bench.md` ("The landscape, at phase
  1") lists it. For each script: the variation (`Bench.configuration`, `Bench.variation`), the scripted fake served in
  a thread at the endpoint's address, `Bench.start` with the case and seed, `Running.send`, `Running.finish` and
  `Bench.score`.
- **For hand use**: `chatddx samples LOGIN [--sample NAME]`, after `init-data`. It serves the scripted fake itself, so
  no fake needs to be running.
- **For tests**: a session-scoped `sampled` database in `src/chatddx/conftest.py`, made from `curated` with alice's
  sample runs in it, and copied for each test as `curated` is. The repl's, the API's and the portal's tests read
  genuine runs without running them each time.

### To settle while porting
- **The scripts' names are the old ones.** Configurations are per-model variants now (`plan (en, Qwen/Qwen3-8B-AWQ)`),
  what the cell set is a recipe's parts (the coercion is the output's contract), and endpoints replace stacks.
- **The turns must hold to remastered's contracts**: an answer through the answer tool, which the compiler offers last
  under `required`, and what vLLM 0.24 does with reasoning and tools (`docs/vllm.md`). The fake's own checks
  (`accept`) still apply to the request.
- **A batch sample**, several cases in one run, once the portal's batch pages need one.
- **Scores**: each sample is scored under every scorer that applies, so the scores are genuine too.

## Old → new

| old entity | records | new home | open |
|---|---|---|---|
| machine, os | 3, 3 | `LocalEngine.hardware`, `.runtime` (inline) | fake done; pelle, malborg by the import |
| llm | 2 | `ModelArtifact` (fakes seeded); its facts in `src/chatddx/facts/models.toml` (G1) | the real artifacts, by the import |
| serving, stack | 5, 5 | `LocalEngine` + World inventory endpoint and host | fake done; pelle, malborg by the import |
| client | 2 | `Code` on `RunStarted`, written per run | dropped |
| tool, toolset | 1, 1 | `tool` + `chunk.toolset` (G8), code in `chatddx.tools` | clearance |
| instruction | 2 | `chunk.instructions` + `chunk.prompt` (G3) | |
| output | 4 | `chunk.output`; views go to scorers (G4, G6, G7) | |
| coercion | 5 | `chunk.output` contract (G4, G5) | |
| reasoning | 9 | `chunk.reasoning`, written from the facts (G1, G2) | |
| sampling | 5 | `chunk.sampling`, `recommended` written from the facts (G1) | |
| configuration | 7 | `Recipe` → skeleton thread + `Compilation` (G9) | |
| case | 99 | `case` + family (tags, language) + `expectation`, with Olof's notes (G11–G14) | judges for the notes |
| scorer | 4 | views of 4 `scorer`s, one per output shape, code in `chatddx.scorers` | aggregates, scorings |

## Gaps
Each gap was tagged [maybe fix remastered]: the sample data needed something remastered lacked.

### Request
- **G1. Model facts.** Fixed: `chatddx.facts`, typed in code with values in TOML, applied when chunks are written
  and keyed by model name (`docs/facts.md`).
- **G2. Reasoning levels.** Fixed with G1: the old levels are facts per model, with writes, collapses, refusals, a
  default and a budget (`docs/facts.md`, "Reasoning"). Open: `xhigh` can't be written (`docs/facts.md`).
- **G3. Placing chunk-supplied text.** Fixed: the `output_guidance` and `tool_guidance` inserts, in the
  instructions or the prompt (`docs/factors.md`, "How chunks affect each other"). In the sample, `instruction.ddx`
  became `prompt.case`, with the guidance as the system message.
- **G4. Showing the schema in the prompt.** Fixed: the `schema` insert in an output's guidance (`docs/factors.md`,
  "Output"). "native (shown)" and "prompted" are outputs in `factors.toml`. The old composition was checked against
  pydantic-ai 2.41.0's `TemplateStr`, and the sample's guidance compiles to the identical system text.
- **G5. The tool contract has no description.** Fixed: `ToolOutput.description` (`docs/factors.md`, "Output").
- **G6. Views.** Fixed: an RFC 9535 subset beside JSON Pointers, and a `lines@1` split (`docs/factors.md`, "View").
  The old views, translated for the scorers to come:
  - differential `$.diagnoses[*].diagnosis`;
  - warning `$.acute_warning`;
  - disposition `$.management.disposition`;
  - critical `$.diagnoses[?@.critical == true].diagnosis`, since the old `[?(@.critical)]` meant "is true" and
    RFC 9535's `[?@.critical]` means "exists";
  - diagnoses `$.diagnoses[*]`;
  - free text: the empty selector with `lines@1` (old `lines`), or no split (old `whole`).

  Unlike the old `read`, nulls are kept.
- **G7. JSON key order was lost in storage.** Fixed: only field names and settings are sorted (`docs/factors.md`,
  "Canonical form and digest"). Bytes written before the fix keep their digests, but recompiling the same recipe now
  gives a new skeleton digest.
- **G8. Tools.** Fixed in shape (`docs/factors.md`, "Tool", "Toolset", "Tool rounds"; `docs/ledger.md`, "Turn and
  ToolRun"; `agents/wip-clearance.md`, "Tools"). Still open:
  - the loop is the runner's (`src/chatddx/runner/rounds.py`), and runs only on sources that aren't sensitive until
    tools can be cleared;
  - `plan-web` can't call its tool on vLLM 0.24: a native contract with tools sends `tool_choice: auto` beside a
    `response_format`, which then constrains the whole answer (`docs/vllm.md`, item 10). `vllm.native_tools_uncallable`
    will flag it once it's paired with a vLLM engine, and the fake vLLM answers it by the schema, calling nothing;
  - `schema.ref_unverified` doesn't look at toolset tools' parameters;
  - gpt-oss with `required` (`docs/facts.md`);
  - a turn after a response that already called the answer tool isn't rejected by `check_run`, though the runner
    ends the item there.
- **G9. Variations.** Fixed: a variation is a fork, and the catalog proposes re-applying it when its origin moves
  (`docs/catalog.md`, "Configurations and variations"). The sample's `extends` became `fork_of`.
- **G10. Skeleton × engine compatibility.** Fixed: the runtime lints (`docs/factors.md`, "Lints"; `docs/vllm.md`,
  items 5–8), the facts' checks (`docs/facts.md`, "Checking pairs"), and `--config` forbidden in argv. Still open:
  OpenAI's API is reported to reject function parameters whose root isn't `type: object`. That's unverified, and a
  candidate lint for tool contracts on `engine.remote`.
- **G15. Sent schemas are not prepared.** Closed, no change: vLLM 0.24 constrains `$defs` and `$ref` as written
  (`docs/vllm.md`, item 4).
- **G16. An inline path for engines that don't resolve `$ref`.** Fixed: `Output.schema_ops` with `inline_refs@1`
  (`docs/factors.md`, "Output"). On `management_plan_v1.json` it gives exactly the old code's inlined schema. Which
  engines need it is only linted (`schema.ref_unverified`).

### Cases
- **G11. Vignette sources.** Fixed: `chatddx.inventory`'s `[source.<name>]` tables (`docs/inventory.md`, "Sources")
  and `prepare_case` (`docs/factors.md`, "Preparing a case"). Sensitivity is declared, not enforced
  (`agents/wip-clearance.md`).
- **G12. Case language.** Fixed: a `language` entry on each family (`docs/catalog.md`, "Languages"). The sample has
  79 `en` and 20 `sv`.
- **G13. Repairs.** Fixed: `Catalog.survey` and `Catalog.repair` (`docs/catalog.md`, "Families and repairs"). On the
  13d317d checkout, the survey found exactly the two changed vignettes and the rename. Still open:
  - trials aren't re-keyed by a repair; `behind` proposes the new cases to their owners;
  - a repair rebuilds only the cases at the family's current binding, not older ones.
- **G14. Expectation data isn't validated.** Fixed with lints (`docs/factors.md`, "Lints"). The hand-written targets
  schema passes all 99 cases' targets, and `init-data` lints what it lands (see "init-data"). Still open:
  - `Output.json_schema` goes to the engine unchecked, and the same validator could give it an
    `output.schema_invalid`.

### Catalog
- **G17. Configurations are named, but nothing names them.** Fixed the other way round: names are optional, and an
  unnamed thing is shown by a title (`docs/catalog.md`, "Names", "Titles"). Still open:
  - titles are rebuilt from names that change, so an export for publication should freeze them;
  - "every configuration using output X" needs a reverse query that isn't written yet.

### Language
- **G18. One language per trial.** Fixed, with the language implicit in what's sent: a translations chunk, languages
  kept on families and digests, and `language.mixed`/`language.unknown` (`docs/factors.md`, "Translations";
  `docs/catalog.md`, "Languages"). Also decided: a model that answers in another language than it was prompted in
  loses the score, and mixing is a warning, not a hard block.
  - Done: the sample's text-bearing chunks are `en`, from its `factors.toml`, so the 20 Swedish cases' trials are
    `language.mixed` until a Swedish translations chunk exists (`docs/curation.md`, "Languages").
  - Still open: few-shot assistant examples that are JSON answers are translated as one text, so the translator
    edits the JSON by hand.
  - Side effects of the implicit language, which no doc covers yet:
    - **Not everything the model reads is ours.** Chat templates add English: default system prompts, harmony's
      channel instructions, tool-call scaffolding. Reasoning traces are often English whatever the prompt.
    - **Structure stays English.** Property names, enum values and tool names aren't translated. That keeps scoring
      language-neutral.
    - **Budgets aren't neutral.** The same text takes different numbers of tokens in Swedish and English, which
      confounds a comparison between languages.
    - **Scorers that need the language** (stemming, synonyms, ontologies) should get it from the expectation data
      or their resources, which are factors, not from the catalog at scoring time.
    - **Languages can be wrong, and they change.** Nothing checks one against the text, and analyses split by
      language should freeze them at export.

## Parked
The deferred work. Settle "Start with this" first.

### Engines and models
The fake engines are seeded and located (see "Engines and endpoints"); the real ones wait on the import (see "Start
with this"). Still open:
- Hardware:
  - `gpu_count` is missing (`docs/factors.md`, "Smaller issues");
  - CPU, RAM, location, GPU uuid and machine id have no home.
- Runtime: `Runtime.closure` is o11n's runtime root for the real engines (see "Start with this"), and the fakes'
  `chatddx fake-vllm`.
- No split between args in the digest and recorded-only args (`performance`). `max-num-seqs` affects batching. An
  endpoint now decides `--host` and `--port`; the rest of the old `performance` args would land in `argv`.
- Endpoints: see `docs/inventory.md`, "Open design issues".
- Model specs (family, size, quantization, context length, licence) are held by the facts, descriptive only
  (`docs/facts.md`).

### Scorers
The scorers are seeded (see "Tools and scorers"). Still open:
- parsing a response into the answer a scorer reads is `chatddx.scorers.answer.read`, which the scoring pass calls
  before the scorer (`agents/wip-runner.md`, "The scoring pass"). A truncated structure isn't salvaged;
- free-text parsing beyond `lines@1` (G6);
- the old scorers' aggregates (`metrics = ["mean", "stderr"]`): the functions are ported
  (`src/chatddx/scorers/aggregate.py`), but no factor says which apply. Summing up over runs is analysis, which
  doesn't change a score;
- views with a judge: `score` refuses them until judges can run;
- a check that views agree with the output schema (old `prove`): reachability is done (G6); item types are open;
- scorings (old D9).

### Free-text expectations
Decided: Olof's comments on the cases are the foundation for a free-text expectation that judges score.
- **What's there.** Olof, a clinician, added comments to the end of three vignettes in the old repo after 7893656:
  `Dutchfall11w` and `casesfromedn1` in 13d317d (2026-09-28), and `Dutchfall1w` in 504792c (2026-10-04). Each is a
  block headed "Olof comments" or "Olof kommenterar", in Swedish even for an English vignette: their reading of the
  case, what to do, and the disposition. `Dutchfall11w` and `casesfromedn1` end in a "Chatddx:" block too, the short
  answer they'd want ChatDDx to give. 13d317d also renamed `DutchFall10w` to `Dutchfall10w`, with the same bytes.
- **Done (decided): the comments are expectation data**, not vignette text, since a vignette and its appendices are
  sent to the model. They're `notes` in the targets (`src/chatddx/data/sample/schemas/targets.json`,
  `src/chatddx/data/sample/cases-*.toml`), as the user decided:
  1. **Kept apart.** A note's `comment` is the reading of the case, its optional `answer` the "Chatddx:" block, so a
     judge can be given either.
  2. **The targets schema is extended**, rather than a schema of its own: `notes` is an optional list beside the
     targets, so a case keeps one expectation, which pattern views and judged views read side by side. A target's
     `text` stays words per kind.
  3. **Kept as written**, in Swedish, with `language = "sv"` on each note, checked as the catalog checks a family's
     language (`src/chatddx/catalog/model.py:LANGUAGE`). Only the headings, line endings and trailing spaces were
     dropped; the text before each heading is the 7893656 vignette, word for word.
  4. **The author is a field** on the note (`author = "Olof"`).

  The vignettes stay as they were at 7893656, so no case needs a repair. A judged view picks a note's text with
  `$.notes[?@.author == 'Olof'].comment` (or `.answer`), and `Judge.fills` puts it in the `expectation` slot
  (`src/chatddx/scorers/test/test_scorers.py:test_a_judge_reads_a_case_s_notes_beside_the_targets_the_patterns_read`).
  The fake vLLM writes a schema's first `examples` value, so its notes hold to the language pattern (`docs/vllm.md`,
  proposed amendments). Re-running `init-data` updates the targets schema, the four scorers that consume it and all
  99 expectations, as their digests pin the schema's.
- **Next, in order:**
  1. a judge-purpose prompt: what a judge is asked about an answer, given a note, and how it scores. It needs Olof.
     Open: the `comment`, the `answer` or both (as two views); whether the `vignette` slot goes in; and how a
     Swedish note is read against an English answer (G18), in the prompt or by translating once into an
     expectation of its own;
  2. a judge in the sample: the skeleton, an engine (a real one; the fakes for tests), seeds, and a scorer whose
     views name it. A judge engine falls under the clearance rule (`agents/wip-clearance.md`);
  3. running judges: the scorer interface's next version for judged views, and the judge calls, recorded per score
     item (`docs/ledger.md:JudgeCall`). `score` refuses judged views until then, and the calls go with the runner.
- **They can disagree with the targets.** On `Dutchfall11w`, Olof leads with shock, most likely sepsis, and uses
  ultrasound (RUSH) to rule out other causes, with blood cultures and broad empirical antibiotics. The targets,
  guessed before their markers were dropped, have AAA or dissection as the diagnosis. `Dutchfall1w` and
  `casesfromedn1` roughly agree with theirs. Open: whether the targets get revised from the notes.

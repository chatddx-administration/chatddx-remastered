# The engine as a part: work in progress

What it takes to make the engine one more part of a configuration, as researchers see it, with what depends on the model
worked out from the facts when a configuration is compiled. Replaces `agents/wip-variants.md` (at d417267), whose
question, how to record which model a configuration is made for, this answers by making the model a part rather than a
name. Checked against the code once variations were built. Stage 1 is built (see "Built"), but for the NixOS test;
stage 2 isn't. "Decided" means the user said so; "Take" is the agent's and still open.

## Decided
- **For a researcher the engine is just another part.** They swap it as they swap a sampling chunk and expect the rest
  to follow, to the nearest setting the new model allows, so that runs over several models are roughly comparable. A
  configuration made for some models only is what they don't want.
- **The engine as a recipe part** (option 1 of the spectrum below), in two stages: the engine now, the language next.
  Large refactors are affordable.
- **"A configuration is made for a model by its chunks" is reversed**, decided when configurations were settled (M1).
- **The takes F1, N1, S1 and D1, and O2** (see "Options"): no store has data worth keeping, so stores are dropped and
  loaded again, and migrations are edited in place rather than added to.
- **A level the model can't honour lands on the nearest it can**, gpt-oss's `off` on `low`, to set the precedent for
  the feature; whether a particular level is refused or lands on its nearest is a line of its model's facts, simple to
  change either way (see "Nearest").
- **An engine served at several endpoints** is refused rather than picked, for a run as for a judge, unless the endpoint
  is named; written up as unlikely, for both, and linked in the docs (see "Several endpoints").
- **A thinking budget a model refuses stays refused**; a budget has no nearest.
- **The inventory names the endpoint whose engine a data set's configurations are made for** at its top:
  `configurations = "qwen3-8b-awq@pelle"`.

## Where it comes from
In the old chatddx a configuration named no model: the stack was a slice of the cell, and compiling turned
`reasoning default` and `sampling recommended` into settings for whatever model the cell held, folding a level where
the model's description said so and refusing the cell otherwise (`docs/repl.md` and `docs/research/a-new-datamodel.md`
at 504792c in chatddx-administration/chatddx). Remastered kept the facts that do the folding (`docs/facts.md`) but
applied them when a data set is loaded: `[reasoning.off] from_facts = { effort = "off" }` became one literal chunk per
model, every recipe that used one was made per model, and the model was known only by the names init-data wrote,
`plan (en, Qwen/Qwen3-8B-AWQ)` (`src/chatddx/curation/plan.py:plan_factors`, `_component`, `_recipe`).

The literal request was right, and stays: a trial pins exactly what is sent, and no fact changes it. Applying the facts
at load time was the mistake. It turned a research-time operation, swap the model and work the rest out again, into a
data-loading one, and hid the model in names that every edge then parsed: the bench
(`src/chatddx/bench/seen.py:Seen.thread`, `NotFound.per_model`), the repl (`repl/shell.py:_per_model`,
`repl/listing.py`, `repl/choosing.py:_again`), the portal (`portal/configurations.py:_variants`), the frontend
(`frontend/src/lib/variation/logic.ts:madeFor`, `islands/Home.svelte:fitting`) and the NixOS test. The sample's 10
recipes make 31 configurations, listed 62 times with the giftbag, and a variation tried on one model is lost on
switching to another. Configurations "for no model" were put aside then because a corrected fact would change what a
configuration sends without an edit of it; keeping the facts in the store, as versions, answers that.

### The spectrum, as it was weighed
1. **The engine a recipe part**, the facts stored, sampling and reasoning chunks holding intents. Decided.
2. **Configurations for no model**, the engine bound per run, as the old chatddx's. A configuration would hold no one
   request, and everything that reads "its skeleton" would change.
3. **Per-model chunks recording what they stand for**, re-resolved by the bench when the engine is swapped. Keeps
   literal chunks, at the cost of machinery 1 removes.
4. **Variant groups recorded**, the engine swap picking a sibling (`agents/wip-variants.md` at d417267, B2). Only
   what init-data made per model exists.
5. **Names as they are**, the edges re-resolving by name as the repl's cell does.

## Built
Stage 1, as designed below, with these details the design left open:
- **Facts come from the store** wherever the bench reads them (`Seen.facts`, the live heads of the `facts` threads,
  read when asked); `--facts` stays on init-data alone, and `Bench`, `api.app`, `portal.app` and `Worker` take none.
- **A look needs no endpoint.** It renders and lints a configuration with a recipe for its engine, so `findings` is
  always a list then; an endpoint named must serve that engine, and only a hand-written configuration needs one. Its
  parts say where an intent landed (`Part.landed`, `Part.nearest`; `Seen.landed`).
- **Where a run goes**: `Seen.at(variation, endpoint)`, the endpoint serving the variation's engine
  (`Inventory.serving`), refused for none or several unless one is named, and refused for one named that serves another
  engine. The judges' `runner/score.py:judge_at` uses `Inventory.serving` too.
- **Judges** compile their recipe with the engine the World binds them to; a compilation that differs from the
  recipe's own is stored without a thread (`Plan.compilations`).
- **The repl**: the cell's engine is its configuration's engine part; `on ENDPOINT`, `use` and `cell` put the
  endpoint's engine in it and keep every pick; `set engine NAME` swaps it and leaves an endpoint that serves another;
  the prompt and `cell:` show the endpoint named or derived. A level the new engine's model refuses is said as the cell
  changes, as a note rather than a failure, and the cell changes anyway so that `set reasoning` can mend it, where
  `_again` kept the cell as it was.
- **The portal**: the engine picker lists the engines the World's endpoints serve; the endpoint picker shows only for a
  hand-written configuration or an engine served at several endpoints. The home page runs the configuration it picks
  with its engine set to the endpoint's (`parts.engine`).
- **Scripted runs** set the engine to the scripted endpoint's.
- **Docs**: suggestions in the docs this touches (item 13).

Outstanding:
- **The NixOS test** (`nix/test.nix`) still finds `plan (en, Qwen/Qwen3-8B-AWQ)` and names its endpoint; it wants
  `plan (en)`, and can leave the endpoint to be derived. Left for the user, who'll get back to it.
- **`Seen.facts` is read on every access**, several times a look; cheap at today's sizes (a facts thread per model),
  and the place to cache per request if it shows.
- **Following corrected facts** isn't built at an edge, as following a chunk that moved on isn't: the catalog says a
  configuration is behind its facts (`behind`, `/facts`), but no edge reads `behind`, and a configuration with nothing
  replaced is its stored skeleton (`Seen.skeleton`), so an edit with the same recipe writes nothing. Following wants a
  variation that recompiles against the current facts, and an edge that offers it where `behind` names `/facts`.
- **A trial's engine and its skeleton's** aren't tied by the factors: a trial may pair a skeleton compiled for one
  model with an engine of another. The bench never does (a run takes its recipe's engine, `Seen.at`), and the facts'
  pairing lints catch a sampling or level meant for another model; a hand-made trial or a run again on a trial made
  before is where it can happen. Take: a lint, `trial.engine_unmatched`, from the skeleton's compilation when it has
  one.

## Stage 1: the engine

### What a researcher sees
`plan` is one configuration. Its parts are its texts, its output, `sampling: recommended`, `reasoning: off` and
`engine: qwen3-8b-awq@pelle`. Picking another engine on the variation page is a variation like any other,
`plan+engine=gpt-oss-20b@pelle`: every other pick stays, the request is worked out for gpt-oss, and what the model
can't do is said before anything runs, as is a level that lands on its nearest: `reasoning: off → low on
gpt-oss-20b, which always reasons`. Saving it keeps one configuration with that engine. The endpoint is where the
engine is served, found from it. Names carry no model.

### Design
1. **Facts are components.** A kind `facts`: a model's name, the repository a local engine's model comes from or the
   model a remote engine names, and what `ModelFacts` holds today (reasoning levels and their collapses and refusals,
   recommended sampling per level, output contracts, specs). `ModelFacts` and its resolving (`land`, `resolve`,
   `reasoning_chunk`, `sampling_chunk`) move into `chatddx.factors`, since compiling needs them and the factors depend
   on no other package; `chatddx.facts` keeps reading facts files, for init-data, and the lints. A `facts` thread per
   model, the archive's, written by init-data from the files as engines are; nobody writes facts at the bench, as
   nobody writes engines. Correcting a fact is a new version of its thread. A refused level may name its nearest (see
   "Nearest").
2. **Intent chunks.** `Reasoning` gains `level` (a reasoning level or `default`), with `thinking_token_budget`
   allowed beside it, and none of the literal fields. `Sampling` gains `recommended`, with any literal field beside it
   overriding the recommendation, as `sampling_chunk(**overrides)` does today. A recommended sampling follows the
   recipe's reasoning level, the model's default when the reasoning part is literal or absent, which fixes the old
   chatddx's coupling bug of a non-thinking request on thinking-mode sampling (`docs/research/a-new-datamodel.md` at
   504792c in chatddx-administration/chatddx, "Reasoning"). Literal chunks stay: greedy, or a hand-tuned sampling.
3. **The recipe names its engine; the compilation names its facts.** `Recipe.engine`, an engine's digest, which every
   recipe has, and `Compilation.facts`, the facts compiled against, none for a model without facts; the compilation's
   version goes up, and nothing reads the old one, since stores are loaded again. `compile_request(recipe, get,
   facts)` resolves the intents with the facts of the engine's model, lands each level where they say, and refuses
   what they refuse; an intent on an engine whose model has no facts doesn't compile. The skeleton stays the literal
   request, so two engines of one model compile a recipe to one skeleton, and trials, judges, runs and scores pin
   exactly what they pin today. `Compilation.cross_check`: its facts are of the recipe's engine's model.
4. **The catalog.** `facts` is a thread kind (`0012`'s `thread_kind_check`, edited in place). What has moved on also
   looks at a configuration's head's compilation's facts, so a corrected fact makes every configuration compiled against
   the old one behind, and following compiles it against the new; `holds` ignores the facts, as it ignores the compiler,
   so recompiling to the same skeleton writes nothing. A title names the engine and describes an intent by what it asks:
   "ddx · case · management-plan · recommended · off on qwen3-8b-awq@pelle". `catalog/variants.py` loses models;
   languages stay in names until stage 2.
5. **The bench.** `PARTS` gains `engine`, which can't be taken out. A variation compiles against the current facts of
   its engine's model, as it compiles with the running code, and a look says, for each intent, what it asked and where
   it landed. A run's trial takes the recipe's engine and goes to the endpoint serving it (see "Several endpoints"); an
   endpoint named that serves another engine is refused before the gate does. A hand-written skeleton runs where the
   endpoint says, as today. `Seen.thread` and `NotFound.per_model` lose the model; `Bench.chunk` and
   `Bench.configuration` take plain names. `Bench`'s facts come from the store, so the `Facts` passed to it today
   (`cli.py`, `worker/worker.py`, `api/state.py`, `api/telling.py`, `portal/app.py`, `conftest.py`) goes. A judge's
   engine is its configuration's.
6. **Runs.** `replaced` entries take the engine (`0026`'s pattern and `catalog.check_varied`, edited in place for
   `engine.local` and `engine.remote`). Nothing in the ledger changes.
7. **Curation.** A `from_facts` record becomes one intent chunk named plainly (`off`, `recommended`). A recipe is made
   once per language, with the engine of the endpoint the World names for configurations (see D), and a judge's
   recipe with the engine of the endpoint the World binds it to. Facts are loaded as threads. The per-model loop of
   `plan_factors`, planning engines first, `_component`'s expansion and `_recipe`'s per-model crossing go. A recipe the
   facts refuse on that engine is skipped and reported, as today.
8. **Loaded stores** are dropped and loaded again (O2); nothing reads what they held.
9. **The API.** `Parts.engine`; a look's and a run's `endpoint` become optional, derived from the engine; a look's
   `Part` says where an intent landed; a `facts` word for threads; `chatddx openapi > frontend/openapi.json`.
10. **The portal.** The engine is a row of the parts table, its picker the engines the World's endpoints serve; the
    endpoint picker, the "made for this endpoint's model" link and the `variants` prop go, and the pickers lose their
    model groups. The home page picks a configuration and an endpoint, and runs the configuration with its engine set
    to the endpoint's. The configurations list has one row per recipe and language.
11. **The repl.** `on ENDPOINT` sets the engine part and keeps every pick; `set engine NAME`; `_again` goes;
    `configurations` drops its models column; `reasoning` tabulates the stored facts.
12. **Lints.** `facts.reasoning_unmatched` and `facts.sampling_unmatched` can't fire on a compiled intent; they stay
    for literal chunks and hand-written skeletons, read from the stored facts.
13. **Docs**, as suggestions: `docs/factors.md` (recipe, compilation, sampling, reasoning, the facts kind, what
    compiling depends on), `docs/facts.md` (stored, versioned, applied when compiling), `docs/curation.md` ("Per
    model" goes), `docs/catalog.md` (facts threads, what has moved on, titles), `docs/bench.md`, `docs/api.md`,
    `docs/repl.md`, `docs/inventory.md` (D), `docs/migrations.md`, and the `*-api.md` docs.
14. **Tests**: those that read variants by model (`catalog/test/test_variants.py`, `bench/test/test_seen.py`,
    `repl/test/test_choosing.py`, `test_listing.py`, `test_commands.py`, `portal/test/test_varying.py`,
    `curation/test/test_plan.py`, `test_judges.py`, `test_init.py`, `test/test_sample.py`,
    `frontend/src/lib/variation/logic.test.ts`), every `world_facts()` caller, the test World's data set, and
    `nix/test.nix`, which finds `plan (en, Qwen/Qwen3-8B-AWQ)` by name. New: compiling intents per model, a level
    landing on its nearest and one refused (the test World keeps a plain refusal), a fact corrected making
    configurations behind and following it, an engine swapped keeping the other picks, a run at a derived endpoint
    and one refused for an engine at two.

### Nearest
A refused level may name the level it lands on instead:
`off = { refused = "always reasons: vLLM rejects reasoning_effort = none for harmony", nearest = "low" }`. Landing
follows it as it follows a collapse, but says it is a nearest, with the reason, so a look, a run's page and a title
can say `off → low`. A collapse says the two levels are one request (Qwen3's `low` is its `on`); a nearest says they
aren't, and the model can't be asked for the first. Taking `nearest` out makes the level a refusal again, and adding
it back the nearest, so the choice per model and level is one line of its facts, and a new version of them, which
makes the configurations compiled against them behind.

The precedent: every level the shipped facts and the sample World's refuse gets its nearest: gpt-oss's `off` and
`minimal` land on `low`, its `xhigh` on `high`, and Mistral Small's `on` on `off`, with minimal to xhigh, which
collapse into its `on`. A thinking budget a model refuses has no nearest, and stays refused, since a budget isn't a
level.

### Several endpoints
A run goes to the endpoint serving its engine, and a judge's calls to the endpoint serving the judge's engine
(`docs/runner.md`, "Judges"). When several serve it, neither is picked: the run, or the scoring, is refused until the
endpoint is named. The judges' rule is `src/chatddx/runner/score.py:_serving`, which moves to the inventory to serve
both. It probably won't happen: an engine is a server we run on one host, or an API, and a World serving one at two
endpoints would be serving the same model on identical machines, a load balancer's job rather than the World's. Both
are written up together as such in `docs/bench.md`, "Outstanding", and linked from `docs/runner.md`, "Judges",
as suggestions.

### What gets simpler, and what harder
Simpler: one configuration per recipe and language; no model in any name and no name parsed for one; a variation
survives a swap of model; runs over several models are one variation each, differing in one part; init-data plans
without a model loop; a corrected fact reaches configurations through what has moved on, visibly; two pairing lints
stop applying to compiled configurations; judges take their engine from their configuration.

Harder: a new kind and its tiers; chunks of two shapes, literal and intent; compiling depends on the facts, so a
variation of an old configuration can differ from it where nothing was replaced (as it can after a change to the
compiler, `docs/catalog.md`, "Smaller issues"); refusals come when an engine is picked, at every edge; the facts are
read from the store wherever they are read today.

## Stage 2: the language (outline)
Decided: people mark cases with a language, and are told when a trial is about to run without translations into it;
otherwise they see little of languages. Take: translations cover every text, instructions, few-shot and prompts too,
so a configuration is written in one language and carries a translations chunk per other language; a run over cases in
several languages is a run per language, each under the configuration's translations into it, and a language it has
none for is said and left out. Per-language threads and `catalog/variants.py` then go. Planned in full once stage 1 is
built.

## Options

### F. Where the facts are pinned
- **F1. In the compilation**, beside the compiler: provenance, as the compiler's code is. Recompiling against
  corrected facts to the same skeleton writes nothing.
- **F2. In the recipe**, as a part set from the engine. A corrected fact that changes nothing sent is a new version of
  every configuration compiled against it.

Decided: F1. The facts are how a configuration is compiled, not something a researcher picks.

### N. A level the model can't honour
- **N1. As the facts say.** A level collapses into another, lands on its nearest, or is refused, as the facts author
  says per model (see "Nearest"). What a run asked for is in its compilation's recipe, and what it landed on follows
  from its facts, so both can be shown.
- **N2. A rule in code**: the nearest level the model honours, in the order off, minimal, low, medium, high, xhigh,
  for every refusal.

Decided: N1, with every refusal landing on its nearest as the precedent. Whether `off` on a model that always reasons
is comparable to `low` is a research judgement, per model.

### S. What a recommended sampling follows
- **S1. The recipe's reasoning level.**
- **S2. The model's default level**, as `[sampling.recommended] from_facts = { effort = "default" }` writes it today.

Decided: S1, the coupling the old note asked for; S2 is a literal chunk away.

### D. The engine of a data set's configurations
- **D1. One the World names**: a top-level key in `inventory.toml`, beside `[judge]`, naming the endpoint whose engine
  configurations are made for: `configurations = "qwen3-8b-awq@pelle"`.
- **D2. The first endpoint** the inventory lists.
- **D3. Every engine the World serves**: a configuration per engine, which is what this removes.

Decided: D1, as the World binds judges.

### O. Configurations stored before
- **O1. Kept readable**: the new fields default, so an old recipe has no engine and runs where the endpoint says;
  init-data deletes the archive's per-model threads when it runs again.
- **O2. Rebuilt**: stores loaded before are dropped and loaded again, as for v1 scorers (`docs/migrations.md`,
  `0017`).

Decided: O2. No store holds anything worth keeping, so migrations are edited in place too.

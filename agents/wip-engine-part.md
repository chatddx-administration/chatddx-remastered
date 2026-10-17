# The model as a part: work in progress

A solution to the variants problem: configurations made per model and per language, their model and language carried
in their names and parsed back at every edge. Here a configuration is one recipe, whose model and translations are
parts like any other; what depends on the model is worked out from stored facts when the recipe is compiled, and what
depends on the language when a case is sent. The engine is the trial's: the endpoint serving the model. Built first
with the engine as the part, reviewed ("Review"), and rebuilt with the model as the part ("The model as the part",
decided M1, R1 and Q1); the sections below describe it as it stands.

## What a researcher sees
`plan` is one configuration. Its parts are its texts, its output, `sampling: recommended`, `reasoning: off` and
`model: qwen3-8b@pelle`. Picking another model on the variation page is a variation like any other,
`plan+model=gpt-oss-20b@malborg`: every other pick stays, the request is worked out for gpt-oss, and what the model
can't do is said before anything runs, as is a level that lands on its nearest: `reasoning: off → low on
gpt-oss-20b, which always reasons`. Saving it keeps one configuration with that model. The endpoint is where the
model is served, found from it, and named when several serve it.

A configuration with translations, such as the sample's `free-text-guided`, runs over cases in whatever languages:
each case is sent in its own language, the configuration's own as written, the others translated. Before anything
runs, the variation's page says in which languages it runs, with how many cases each, and which cases it can't run,
with why: `Left out: 3 cases in de, as free-text-guided has no translations into de.` Names carry neither a model nor
a language, and nothing asks for a language but a typed case.

## Facts
- **Facts are components**, kind `facts` (`src/chatddx/factors/facts.py:ModelFacts`): a model's name and what is known
  about it that a request doesn't say, its reasoning levels and their collapses, refusals and nearest levels, the
  sampling its makers recommend per level, its output contracts and specs. A `facts` thread per model, the archive's,
  written by init-data from the bundled facts file and the World's `facts.toml`, for each model an engine of the World
  serves; nobody writes facts at the bench, as nobody writes engines. Correcting a fact is a new version of its thread.
- **The bench reads them from the store** (`Seen.facts`, the live heads of the `facts` threads, read when asked);
  `chatddx.facts` reads facts files, for init-data and the lints, and `--facts` is init-data's alone.

## Intents
- **Reasoning** holds a `level` (a reasoning level or `default`), with `thinking_token_budget` allowed beside it, and
  none of the literal fields. **Sampling** may be `recommended`, any literal field beside it overriding the
  recommendation. A recommended sampling follows the recipe's reasoning level as it landed, the model's default when
  the reasoning part is literal or absent.
- **Literal chunks stay**, greedy or a hand-tuned sampling, and a configuration of them is for any model.

### Nearest
A refused level may name the level it lands on instead:
`off = { refused = "always reasons: vLLM rejects reasoning_effort = none for harmony", nearest = "low" }`. Landing
follows it as it follows a collapse, but says it is a nearest, with the reason, so a look, a run's page and a title
can say `off → low`. A collapse says the two levels are one request (Qwen3's `low` is its `on`); a nearest says they
aren't, and the model can't be asked for the first. Whether a level is refused or lands on its nearest is one line of
its model's facts, and a new version of them, which makes the configurations compiled against them behind.

Every level the bundled facts and the sample World's refuse has its nearest: gpt-oss's `off` and `minimal` land on
`low`, its `xhigh` on `high`, and Mistral Small's `on` on `off`. The test World keeps a plain refusal (test/mistral-7b's
`on`). A thinking budget a model refuses has no nearest, and stays refused: a budget isn't a level.

## The recipe and its compilation
- **A model is a component for every engine.** A local engine references a `model.local` component (`LocalModel`,
  `ModelArtifact` of kind `model` before) as before; a remote engine references a `model.remote` component
  (`RemoteModel`: provider and name) rather than naming its model, so `ModelRef` covers both kinds. Both have a
  `name`, the facts' key; `model_of(digest, get)` gives the model a model or an engine names, and
  `served_model_name(engine, get)` takes an engine's digest: a local engine's digest, a remote engine's model's name.
- **The recipe names its model** (`Recipe.model`, a `ModelRef`, required), and **the compilation names its facts**
  (`Compilation.facts`), only where they work something out, so a literal configuration is never behind its facts.
  `compile_request(recipe, get, facts=None, into=None)` resolves the intents with the facts of the recipe's model,
  lands each level where they say, and refuses what they refuse; an intent on a model with no facts doesn't compile.
  The skeleton stays the literal request, so a recipe compiles to one skeleton wherever its model is served, and
  trials, judges, runs and scores pin exactly what is sent, the engine among them.
- **What has moved on** looks at a configuration's head's compilation's facts too, and flags them only when compiling
  against the newer facts changes the skeleton; and at its recipe's model, flagged whenever its thread moved on, as to
  a new revision of the weights (R1). Whoever sees a configuration sees what moved on and what following keeps
  (`Bench.moved`, `GET /api/threads/{thread}/moved`, the configuration page); its owner follows both as one edit, the
  recipe with the model's head compiled against the current facts about it (`Bench.follow_moved`,
  `POST /api/threads/{thread}/moved/follows`). Facts that now refuse what it asks are said, not followed.
- **A title** names the model last and describes an intent by what it asks: `recommended sampling`, `reasoning off`.

### Several endpoints
A run goes to the endpoint serving its model (`Inventory.serving`, `Seen.at`), and a judge's calls to the
endpoint serving the judge's engine (`Inventory.serving`, `runner/score.py:judge_at`): a judge pins its engine as a
trial does, and init-data remakes it for the World's endpoints. When none serves the model, or several do and none is
named, the run is refused; an endpoint named that serves another model is refused before the gate is asked. A
hand-written configuration names no model, so it needs an endpoint named, and its trial takes that endpoint's engine.
Several endpoints serving one model is likely, unlike one engine: the test World serves Qwen3 with and without its
parsers (`qwen3@fake`, `qwen3-bare@fake`), so a run of a Qwen3 configuration there names its endpoint, and a look
rendered for neither has no findings until one is picked. The repl's cell on no endpoint shows none, and `run` says
which to name.

## Languages
- **A translations chunk holds every language** it translates into: `Translations(into: {sv: {...}, de: {...}})`,
  one part of the recipe; a language added is a new version of the chunk. It names its languages itself, so the
  catalog keeps no language row for it. Every text is translated: instructions, few-shot, prompt, output, toolset and
  the appendix layout.
- **A configuration is written in one language**, its own, its texts' vote (`catalog/language.py:recipe_language`,
  translations not voting), and its translations carry it into others. `compile_request(..., into=sv)` compiles it
  with every text translated: a text without a translation there, or no translations into it, is a `StructuralError`
  (`no translation into sv for 'Fill in the plan.'`). `Compilation.into` says the language compiled into, none for
  the recipe as written; a skeleton's language is its compilations' `into`, else their recipe's.
- **A translation differs by its texts only**: an unvaried configuration is translated against the facts its own
  compilation pinned (`Seen.compiled_with`). A translated skeleton is compiled when a look or a run needs it, and its
  compilation is stored when a run is (`keep_compilation(seen, variation, into)`), so a translated run's skeleton has
  a language.

### A start per language
Starting a variation groups its cases by their family's language (`Seen.languages -> list[Carried]`): the
configuration's own goes as written, a language its translations cover goes translated, and a case of a language it
can't be sent in is left out and said. Each group is a run of its own, a trial of one skeleton, so trials, the ledger
and scoring are as for one language. All of a start's runs carry the variation's label as their name, the later ones
a `with` entry naming the first (`Entry.started_with`; `0026`), and they begin in one transaction, so a run the gate
refuses leaves none of them begun. The quota is checked for all of them first. `bench.start -> Started`: each run with
its language, and the cases left out; every case left out is `no case can be sent`, a refusal.
`Seen.together(first)` is a start's runs; `GET /api/runs?with=` and a run's page read it. Running again is one run,
in its run's language. Judges stay in their configuration's language: a judge reads a Swedish note against an answer
in either language, as its instructions say.

### A case of no language
A case of no language goes as written, linted `language.unknown`, rather than left out: only a family loaded without
one has none, as a typed case is given one where it is typed (`type_case`'s `language` is required). When a
configuration's own language is unknown, a case of a language its translations don't cover goes as written too:
nothing says it isn't the configuration's language.

## Data sets
- **A texts file** holds what is written in its language: text records, and translations records whose entries
  translate into it, grouped by the record whose texts they translate
  (`[translations.sample.of."instructions.clinician"]`) or given flat (`entries`). A text record is written once; a
  translations record of one name in several texts files is one chunk, into each of their languages.
- **A recipe is made once**, named plainly, for the model of the endpoint the World names for configurations
  (`inventory.toml`'s `configurations = "qwen3-8b-awq@pelle"`); a recipe the facts refuse for that model is skipped and
  said. Loading says, per recipe, the languages its translations can't carry it into
  (`[untranslated] recipe asked: no translation into sv for 'You are an emergency physician.'`), and makes it all the
  same. A judge's recipe is compiled for the model of the endpoint the World binds the judge to, its compilation
  stored without a thread (`Plan.compilations`), and the judge keeps that endpoint's engine. Facts are loaded as
  threads, one per model served that the facts know. A remote model is a `[remote_model.*]` record of `engines.toml`
  (provider, name), which a `[remote_engine.*]` record names as a local engine names its `[local_model.*]`.
- **The Worlds**: the sample's and the test World's Swedish instructions and worked examples are translations of their
  English ones. In the sample only `free-text-guided` names them, and in the test World only `lines-guided`; every
  other configuration leaves Swedish cases out.

## The edges
- **The bench**: `PARTS` holds `model`, which can't be taken out; `Seen.at(variation, endpoint)` says where a run goes,
  `Seen.model_of(engine)` which model an engine serves and `Seen.model_at(endpoint)` which an endpoint does, each the
  model itself;
  a look says, for each intent, what it asked and where it landed (`Seen.landed`), the languages it runs in, and lints
  each language's trial, a language left out being `translations.missing`.
- **The API**: `Parts.model`; `Endpoint.serves`, the model an endpoint's engine serves; a look's and a run's
  `endpoint` are optional, derived from the model; a look is rendered and linted for the endpoint's engine, or for
  none when nothing serves the model or several do unnamed; a look's `Part` says where an intent landed, and its
  `languages` where its cases go; `POST /api/runs` answers with every run it started and the cases left out; a run
  says its `language` and the run it was `started_with`; `Thread.translated`; `GET /api/threads/{thread}/moved` and
  `POST .../moved/follows` (`Moved`, `NewFollowMoved`).
- **The portal**: the model is a row of the parts table, its picker the models the World's endpoints serve; the
  endpoint picker shows for a hand-written configuration or a model served at several endpoints. The variation page
  says where it runs and what is left out; a configuration's page says what it was compiled for has moved on, and its
  owner follows it; a run's page links the runs started with it; the home page runs the configuration it picks with
  its model set to the endpoint's, and asks the language a case is written in.
- **The repl** (Q1): `on ENDPOINT`, `use` and `cell` put the endpoint's model in the cell's configuration and keep
  every pick, a variation only when it differs; `set model NAME` swaps it, named as its thread is, and unsets an
  endpoint serving another. The engine the cell is rendered and linted for is the endpoint's, else the one serving the
  configuration's model (`Repl.engine`). A level the new model refuses is said as the cell changes, as a note, and
  the cell changes anyway so that `set reasoning` can mend it. `configurations` lists a row per configuration with
  its languages; `show` lists the languages before the lints; `run tag` runs a start's runs in turn, and a Ctrl-C
  that stops one stops the ones after it.
- **Scripted runs** set the model to the scripted endpoint's, and keep one run each: their cases are sent in one
  language.
- **Lints**: `trial.engine_unmatched` and `judge.engine_unmatched`, a skeleton every compilation of which was worked
  out for another model than the engine serves; `facts.reasoning_unmatched` and `facts.sampling_unmatched` for literal
  chunks and hand-written skeletons; `language.mixed` for a trial made by hand, since the bench makes none.

## Stores loaded before
The migrations are edited in place: `0012` (the `facts` and `model.remote` thread kinds, `chunk.translations` out of
the language kinds) and `0026` (`replaced` entries naming a model, the `with` entry). A store loaded before is dropped
and loaded again, as its compilations, translations and remote engines are of versions nothing reads. The Worlds'
`endpoints.toml` name remote engines by their new digests.

## Outstanding
- **The docs** describe the engine as the part; the suggestions written in above each statement say what the model
  as the part changes, and `docs/repl-manual.md`'s transcripts want recording again.
- **The review's must-fix items** that aren't this build's: names tests share spelled as literals, and four comments
  in `curation/plan.py:plan_factors`.
- **`Seen.thread`'s `name` is undescribed.** The doc fixes that took out the `variants_for` lines in docs/bench-api.md,
  "`thread(word, name)`", took the item's first line too, so `OWNER/NAME` is said only as a qualified name.
- **The repl's `runs` doesn't show a start**: a translated run says its language, the own language's run of the same
  start says none, and nothing says the two were started together; `GET /api/runs?with=` and a run's page do.
- **A language refused on a compiled skeleton is said to come from its recipe** (`catalog/language.py:check_language`,
  `0012`'s `language_compiled`, the bench's `COMPILED_LANGUAGE`); a translated skeleton's comes from its compilation.
- **A translated skeleton's title doesn't say its language**: it has no thread, so it is titled by its recipe.
- **A start holds a transaction open while the gate confirms its endpoint**, once per language, a few seconds at most
  against an endpoint that answers; the price of a start that begins whole or not at all.
- **The variation page knows the languages of the families its look is over**, its tags; a family picked beyond them
  goes as its language's, or is said as "if it can be" when the look didn't see its language.
- **`Seen.facts` is read on every access**, several times a look; cheap at today's sizes (a facts thread per model),
  and the place to cache per request if it shows.
- **A look for a model several endpoints serve** has no findings until an endpoint is named, where the engine part gave
  it the recipe's engine's. The variation page shows the picker; the repl's `show` shows no lints.
- **A model that moved on and is served nowhere** is followed to its head whether or not an endpoint serves it; `at`
  says so afterwards.

## The model as the part
Written up as an alternative to the engine as the part, on the review's asking, and then decided and built: M1, R1 and
Q1, with the `configurations` key kept as an endpoint, whose engine's model the recipes are made for. The sections
above describe it as built; what follows is the write-up as it was weighed, with its options' decisions.

### What a researcher sees
`plan`'s parts are its texts, its output, `sampling: recommended`, `reasoning: off` and `model: Qwen/Qwen3-8B-AWQ`.
Picking another model is a variation, `plan+model=openai/gpt-oss-20b`, worked out as the engine swap is today. Where
it runs is found from the model: the endpoint serving an engine of it, named when several do. A vLLM upgrade, a flag
or a chat template changed on an endpoint changes nothing a researcher sees; a new revision of the weights does, as it
should, since the model is another. `plan` runs on Qwen3-8B wherever the World serves it, and at the repl `use plan`
on an endpoint serving another model swaps the model, said, as it swaps the engine today.

### Design
1. **A model is a component for every engine.** A local engine already references one (`ModelArtifact`, kind `model`:
   repo, revision, files; `engines.toml`'s `[local_model.*]`). A remote engine's model is a name (`RemoteEngine.model`); it
   gets a component of its own, kind `model.remote`, a provider and a name, which `RemoteEngine.model` references as
   `LocalEngine.model` does, so that `ModelRef` covers both and `model_name` reads a model rather than an engine. The
   facts stay keyed by the name: the artifact's `repo`, the remote model's name.
2. **`Recipe.model`** (a `ModelRef`, required) replaces `Recipe.engine`, and `RECIPE_PARTS` ends in `model`.
   `compile_request` resolves the intents with the facts of the recipe's model; `Compilation.facts` and `cross_check`
   mean what they mean now. The skeleton is unchanged: two engines of one model compiled one skeleton already.
3. **Where a run goes.** `Seen.at(variation, endpoint)`: the endpoints whose engine's model is the recipe's
   (`Seen.model` per endpoint, cached for the connection); one serves it, so it goes there; none, or several and none
   named, is refused as today; a named endpoint serving another model is refused before the gate. The trial takes
   that endpoint's engine, as a hand-written skeleton's does today, so the ledger pins the server as it does now.
   `Inventory.serving` needs the store to read a model from an engine, so it takes a `model_of` callable, or moves to
   the bench; `runner/score.py:judge_at` gives it `get`.
4. **The catalog and runs.** `replaced` entries take `model=` (`0026` in place: `check_varied` with `model` and
   `model.remote`); `0012`'s thread kinds gain `model.remote`; `KINDS["model"]` too. A title names the model last:
   "… · reasoning off on Qwen/Qwen3-8B-AWQ".
5. **Curation.** A recipe is made for a model: `inventory.toml`'s `configurations` names a model of `engines.toml`
   rather than an endpoint, or stays an endpoint and its engine's model is taken; a judge's recipe takes the model of
   the endpoint the World binds it to. Remote models are records of `engines.toml` (`[remote_model.*]`), or inlined in
   a remote engine's record and planned from it. Facts are loaded as now.
6. **The edges.** The variation page's model picker lists the models the World's endpoints serve, and its endpoint
   picker shows only when several serve the model. The home page sets the model to the endpoint's. The repl's `on`,
   `use` and `cell` set the model to the endpoint's, a variation only when it differs; `set model NAME`. Scripted
   runs set the model to their endpoint's. `Parts.model` at the API.
7. **Lints.** `trial.engine_unmatched` and `judge.engine_unmatched` stay what they are; the trial's engine's model is
   also checked against the recipe's, which `Seen.at` already guarantees for runs the bench starts.

### What it changes from the built solution
- **Nothing a server does to a configuration.** The engine's digest covers runtime, argv, env, chat template and
  model files, and every saved configuration names one; an endpoint changed leaves them naming an engine nothing
  serves ("Consequences of the design"). A model's digest covers the weights, which change rarely and mean something
  when they do.
- **The edges override less.** The repl and the home page put the session's endpoint's model in, which is a change
  only when the model differs; across servers of one model, every edge agrees. The `configurations` key names what
  the recipes are for, a model, rather than a place.
- **The engine is the trial's alone**, where the ledger has it; the recipe holds what to ask and of which model,
  and nothing of where.
- **A new kind** and its tiers, a `RemoteEngine` that references rather than names, a `serving` that needs the store.
- **The same everywhere else**: facts as components, intents and nearest levels, the compilation pinning its facts,
  following them, translations, a start per language, the `with` entry.

### Cost
The places the engine part touched: 17 files outside tests read the recipe's engine, most as a rename and a kind
check, with the work in `Seen.at`'s derivation, `model_name`, the remote model's component and records, and the
migrations edited in place. The data sets' `configurations` key and the test World's remote engine change shape.
Smaller than stage 1 was, and reachable from the built solution as a follow-up with one more drop and reload, which
O2 allows while no store holds data worth keeping and the deploy (`agents/wip-deploy.md`) hasn't closed it.

### Options

#### M. What the model part is
- **M1. A model component for both kinds**: `model` as it is, `model.remote` new. One new kind; the facts' key is
  read from either.
- **M2. The facts thread's digest** (F2): a correction that changes nothing sent is a new version of every
  configuration; rejected before for that.
- **M3. A name**, the facts' key itself: the one part without a digest, which `iter_refs`, `replaced`'s shape and
  `TriedVariation.set`'s kind check all assume.
- **M4. A coarser component**, a model's identity (its repo name) apart from its artifact, so that a revision of the
  weights isn't a new model. Never stale, and the facts are keyed by it already; but the artifact would reference
  it, a kind more than M1, and a configuration would say less than it does today.

Decided: M1. A revision of the weights is a change a researcher should see.

#### R. A revision of the weights
Under M1 a configuration names an artifact, and a World that moves to a new revision leaves it naming one nothing
serves: the engine part's staleness, rarely.
- **R1. Flagged as behind**, with following to the artifact of the same repo the World serves, as corrected facts
  are followed. The same mechanism would serve the built solution for a stale engine, more often.
- **R2. Refused until picked again**, as the built solution refuses a stale engine.

Decided: R1; `behind` flags `/recipe/model` whenever its thread moved on, and `follow_moved` follows it with the facts.

#### Q. `use` on an endpoint serving another model
- **Q1. The model swaps** to the endpoint's, said as a variation, as the engine does today.
- **Q2. The cell moves** to an endpoint serving the configuration's model, when one does.

Decided: Q1; the cell is a session on an endpoint, and Q2 is `on` typed for you.

### Weighing
The two agree on everything but what the recipe pins: the built solution pins what the rig runs on, this one what
the research question is about, which is what the facts, the lints, the landings and the skeleton are keyed by. The
built one is cheaper now by one component kind, and this one cheaper each time an engine changes, which in a rig
that upgrades vLLM and tunes flags is often. Take: this one, if the deploy leaves room for one more reload; else the
built one with R1 for a stale engine, and this as the follow-up.

### What building it found
- **Several endpoints serving one model is the ordinary case**, not the unlikely one it was for engines: the test
  World's Qwen3 is served with and without its parsers. The decided refusal stands, so a run there names its endpoint,
  and the API tests do; a look rendered for no endpoint has no findings. A World-level preference among them, such
  as the `configurations` endpoint, was not built: it would pick silently.
- **A remote model is a record** of `engines.toml`, `[remote_model.*]`, as a local engine's model is.
- **The `configurations` key stays an endpoint**: the data sets, the judges' binding and the facts loaded per served
  model all read endpoints.
- **The lint `trial.engine_unmatched` keeps its meaning**: it fires only where facts were pinned, not for a literal
  recipe's model, which `Seen.at` already holds a run to.

## Review
A read of the branch with the engine as the part, before the model replaced it, by a session that didn't build it: the
code against this document and against
`agents/wip-variants.md` as main holds it, the suite and the static checks, and a second reader over curation and the
edges. "Take" is the reviewer's.

### Checked
- `pytest -n 4`: 862 passed, 3 skipped. ruff, its formatter and basedpyright are clean. `chatddx openapi` matches
  `frontend/openapi.json`. `pnpm --dir frontend check`, `test` and `build` pass.
- What this document claims is tested where it matters: an engine swap keeping every other pick and working the rest
  out (`src/chatddx/bench/test/test_seen.py`); facts corrected flagging a configuration only where they reach it, and
  following them, refused when they now refuse (`bench/test/test_following.py`); a start over English and Swedish
  cases making two runs, the second translated and `started_with` the first, cases left out and said, the quota
  checked for all of them, and a gate refusal partway beginning none (`bench/test/test_runs.py`).
- No name is read for a model or a language anywhere: `catalog/variants.py` is gone and nothing imports what it
  exported; the frontend's `madeFor` and `fitting` are gone; the only regular expressions left over names are the
  language tag's and the entry shapes'.
- Rule one of documentation held: the agent's commits add suggestions to `docs/` and remove one of their own; the
  doc fixes are the user's. No docstring was added, and the new comments link code or say why, but for four (below).
- Two engines of one model compile a recipe to one skeleton: `compile_request` reads the engine for its model only,
  and the skeleton holds no engine.

### Must fix before merge
- **`nix/test.nix` fails twice**, not once; "Outstanding" names the first: it looks up
  `plan (en, Qwen/Qwen3-8B-AWQ)`, and it reads `["run"]` from what `POST /api/runs` answers, which is `StartedRuns`.
- **Names tests share are spelled as literals**: `lines-guided` is in six test files over five packages, `judge` and
  `clinician` likewise, and `src/chatddx/test/world.py` gained only `LINES`, `NATIVE`, `NATIVE_TOOLS`, `TOOL_ANSWER`
  and `OFF` (`AGENTS.md`, "Testing").
- **Four comments in `src/chatddx/curation/plan.py:plan_factors` say what the code does** (the records by name, the
  translations' bodies, a record tried and not planned, the texts a translations record may translate), which
  `AGENTS.md` says to take out.

### Smaller
- `curation/plan.py:plan_factors`: when the configurations endpoint's engine has no engine file in the data set,
  every recipe is skipped as "the World names no endpoint configurations are made for"; it names one, whose engine
  the data set doesn't hold.
- `repl/shell.py:Repl.prompt` reads the store on every render, to derive the endpoint, where the prompt read nothing
  before; a connection dropped surfaces at the prompt, outside `handle`'s catch.
- `api/threads.py:thread_of` reads a compilation per configuration listed, for `translated`.
- A case tagged `en-GB` on an `en` configuration is left out as untranslatable (`Seen.languages` compares tags
  whole); before, it ran with `language.mixed`.
- A start's runs all go to one endpoint, and the gate confirms it once per language inside the transaction
  ("Outstanding"); confirming it once, before the transaction, removes most of what the transaction holds open.

### Consequences of the design
Not bugs: what the solution does to the model, each with how it can be managed.
- **The engine part pins a server, not a model.** `LocalEngine`'s digest covers runtime, argv, env, chat template and
  model files. A vLLM upgrade or a flag changed on an endpoint leaves every saved configuration naming an engine
  nothing serves: the API and the variation page refuse to run it until the engine is picked again, and unlike
  corrected facts nothing flags it as behind. Manageable: an engine no endpoint serves flagged as behind, followed to
  the endpoint's engine of the same model, as facts are; or the recipe naming the model ("The model as the part").
- **Which engine a configuration runs on depends on the edge.** The repl's `use`, `on` and `cell`, and the home page,
  put the session's endpoint's engine in; the API and the variation page honour the stored one. The run records the
  swap in `replaced`, so this is a milder form of the edges' old disagreement, but the same shape. Manageable by saying
  it: at the repl and the home page a configuration is run *at* an endpoint, as a variation.
- **A variation compiles against the current facts, a configuration against the facts it pinned**
  (`Seen.compiled_with`). After a correction, `plan+prompt=x` sends another sampling than `plan`, without that being
  picked, where `agents/wip-variations.md` promised a variation differs in what was replaced. Manageable: a variation
  whose engine isn't replaced compiles against the configuration's pinned facts, one whose engine is replaced against
  the new model's current ones.
- **The archive's configurations can't follow corrected facts**: only an owner may, and the archive is nobody at the
  bench (`test_following.py` shows them flagged and stops there). Manageable: init-data follows the facts for the
  threads it wrote when it runs again; a decision, then a few lines.
- **Translations are keyed by their source text, for every text now.** Editing an instruction detaches its
  translations, and the next start leaves those cases out, said in the look and in the answer. Manageable as is; a
  lint on a configuration whose translations no longer cover a text of its own would close it.
- **Migrations edited in place and stores reloaded** (O2) is open while no store holds data worth keeping. The
  deploy (`agents/wip-deploy.md`) closes it; this should land before, and be the last to use it.

### Take: how far it is a natural conclusion of the design
Where it is:
- **It restores the old chatddx's premise with the remastered invariant kept.** A configuration names no model and
  is compiled for what it is paired with, as the research note asked (each setting "means the same thing whatever
  it is paired with"), and the skeleton is still the literal request, so a trial pins what is sent. Moving the facts
  from load time to compile time corrects one choice; it isn't a new design. Nearest levels (N1) are that premise
  made honest: `off` on a model that always reasons means `low`, said and recorded, rather than a sibling thread
  that silently didn't exist.
- **Facts as components is what the catalog does to every input**: pinned by digest, versioned, behind when moved
  on, followed as an edit. Pinning them on the compilation beside the compiler (F1) is the move the compilation
  already made for code.
- **The engine as a part costs no mechanism**: `TriedVariation.set`, `replaced` entries, forks and titles take it as
  they take a chunk, which is why a swap keeps every other pick for free.
- **It removes a layer rather than adding one**: 31 threads from 10 recipes, init-data's per-model loop, a name
  grammar read at five edges and in the NixOS test, and a variation lost on switching models. A solution that deletes
  `catalog/variants.py` instead of feeding it is the stronger sign of fit.

Where it isn't:
- **The configuration is server-bound where the rest of the design is model-keyed.** Facts, lints, landings and the
  skeleton are per model; the engine part alone is per server, and it sits in the recipe beside what to ask. Before,
  where a request goes was the trial's and the run's; now the recipe holds a piece of it, and `inventory.toml`'s
  `configurations` key puts an operational choice into the research data for the same reason. The edges overriding
  the engine is the design pushing back.
- **Compiling is no longer a function of the recipe alone.** `Compilation` records the facts and `into`, so
  provenance is whole, but "what a configuration sends changes only by an edit", decided when configurations were
  settled, is now "or by a correction, flagged and followed", and for a variation not even that. Literal chunks keep
  the old guarantee available per configuration, which is the right escape hatch.
- **A start isn't a subject.** Its runs are tied by a `with` entry and found by a scan (`Seen.together`); the group
  that a run over mixed-language cases forms is known by an entry, as variants were known by a name, one level up.
  Small today, and the same shape.

### Take: whether the consequences are manageable
Yes, and none asks for the approach to be undone. Two shape what a configuration *is* and are worth settling before
more is built on it: the server-bound engine, and which facts a variation compiles against. The rest are a lint, a
decision for init-data, a sentence in the docs, or a cache later.

### Take: whether an alternative should be made and weighed first
Not against the approach. Recording variants (`agents/wip-variants.md`, B2) keeps the per-model threads and turns
name-reading at every edge into entry-reading at every edge, and never gives a variation that survives a swap. The
reversal was right, and the spectrum's options 2 to 5 were dismissed for reasons that hold.

Against one part of it, yes, on paper and now: **the recipe naming a model rather than an engine**, the engine
staying the trial's, picked per run as the endpoint serving the model. It is what the facts and the lints are keyed
by; it removes the staleness, the `configurations` key and the overriding edges, and `replaced` need record no
engine. What stops it is real: a remote engine's model is a name, not a component, so a model part would be the one
recipe part without a digest, or would need a component standing for a remote model. That is a page to weigh, not a
build: the two differ in one part's kind and in `Seen.at`'s derivation, and the one is reached from the other as a
follow-up. It should be weighed before this lands rather than after, because O2 is what makes changing a part's
kind cheap, and the deploy closes it. Written up above as "The model as the part".

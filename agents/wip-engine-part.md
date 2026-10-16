# The engine as a part: work in progress

A solution to the variants problem: configurations made per model and per language, their model and language carried
in their names and parsed back at every edge. Here a configuration is one recipe, whose engine and translations are
parts like any other; what depends on the model is worked out from stored facts when the recipe is compiled, and what
depends on the language when a case is sent. Built, but for the NixOS test (see "Outstanding").

## What a researcher sees
`plan` is one configuration. Its parts are its texts, its output, `sampling: recommended`, `reasoning: off` and
`engine: qwen3-8b-awq@pelle`. Picking another engine on the variation page is a variation like any other,
`plan+engine=gpt-oss-20b@pelle`: every other pick stays, the request is worked out for gpt-oss, and what the model
can't do is said before anything runs, as is a level that lands on its nearest: `reasoning: off → low on
gpt-oss-20b, which always reasons`. Saving it keeps one configuration with that engine. The endpoint is where the
engine is served, found from it.

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
- **The recipe names its engine** (`Recipe.engine`, an engine's digest, required), and **the compilation names its
  facts** (`Compilation.facts`), only where they work something out, so a literal configuration is never behind its
  facts. `compile_request(recipe, get, facts=None, into=None)` resolves the intents with the facts of the engine's
  model, lands each level where they say, and refuses what they refuse; an intent on an engine whose model has no facts
  doesn't compile. The skeleton stays the literal request, so two engines of one model compile a recipe to one
  skeleton, and trials, judges, runs and scores pin exactly what is sent.
- **What has moved on** looks at a configuration's head's compilation's facts too, and flags them only when compiling
  against the newer facts changes the skeleton. Whoever sees a configuration sees its corrected facts and what
  following them keeps (`Bench.corrected`, `GET /api/threads/{thread}/facts`, the configuration page); its owner
  follows them as an edit of the same recipe compiled against them (`Bench.follow_facts`,
  `POST /api/threads/{thread}/facts/follows`). Facts that now refuse what it asks are said, not followed.
- **A title** names the engine last and describes an intent by what it asks: `recommended sampling`, `reasoning off`.

### Several endpoints
A run goes to the endpoint serving its engine, and a judge's calls to the endpoint serving the judge's engine
(`Inventory.serving`; `Seen.at`, `runner/score.py:judge_at`). When none serves it, or several do and none is named,
the run, or the scoring, is refused; an endpoint named that serves another engine is refused before the gate is
asked. A hand-written configuration names no engine, so it needs an endpoint named, and its trial takes that
endpoint's engine. Several endpoints serving one engine would be the same model served on identical machines, a load
balancer's job rather than the World's.

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
- **A recipe is made once**, named plainly, with the engine of the endpoint the World names for configurations
  (`inventory.toml`'s `configurations = "qwen3-8b-awq@pelle"`); a recipe the facts refuse on that engine is skipped and
  said. Loading says, per recipe, the languages its translations can't carry it into
  (`[untranslated] recipe asked: no translation into sv for 'You are an emergency physician.'`), and makes it all the
  same. A judge's recipe is compiled with the engine of the endpoint the World binds the judge to, its compilation
  stored without a thread (`Plan.compilations`). Facts are loaded as threads, one per model served that the facts know.
- **The Worlds**: the sample's and the test World's Swedish instructions and worked examples are translations of their
  English ones. In the sample only `free-text-guided` names them, and in the test World only `lines-guided`; every
  other configuration leaves Swedish cases out.

## The edges
- **The bench**: `PARTS` holds `engine`, which can't be taken out; `Seen.at(variation, endpoint)` says where a run goes;
  a look says, for each intent, what it asked and where it landed (`Seen.landed`), the languages it runs in, and lints
  each language's trial, a language left out being `translations.missing`.
- **The API**: `Parts.engine`; a look's and a run's `endpoint` are optional, derived from the engine; a look's `Part`
  says where an intent landed, and its `languages` where its cases go; `POST /api/runs` answers with every run it
  started and the cases left out; a run says its `language` and the run it was `started_with`; `Thread.translated`.
- **The portal**: the engine is a row of the parts table, its picker the engines the World's endpoints serve; the
  endpoint picker shows only for a hand-written configuration or an engine served at several endpoints. The variation
  page says where it runs and what is left out; a run's page links the runs started with it; the home page runs the
  configuration it picks with its engine set to the endpoint's, and asks the language a case is written in.
- **The repl**: the cell's engine is its configuration's engine part; `on ENDPOINT`, `use` and `cell` put the
  endpoint's engine in it and keep every pick; `set engine NAME` swaps it. A level the new engine's model refuses is
  said as the cell changes, as a note, and the cell changes anyway so that `set reasoning` can mend it.
  `configurations` lists a row per configuration with its languages; `show` lists the languages before the lints;
  `run tag` runs a start's runs in turn, and a Ctrl-C that stops one stops the ones after it.
- **Scripted runs** set the engine to the scripted endpoint's, and keep one run each: their cases are sent in one
  language.
- **Lints**: `trial.engine_unmatched` and `judge.engine_unmatched`, a skeleton every compilation of which was worked
  out for another model than the engine serves; `facts.reasoning_unmatched` and `facts.sampling_unmatched` for literal
  chunks and hand-written skeletons; `language.mixed` for a trial made by hand, since the bench makes none.

## Stores loaded before
The migrations are edited in place: `0012` (the `facts` thread kind, `chunk.translations` out of the language kinds) and
`0026` (`replaced` entries naming an engine, the `with` entry). A store loaded before is dropped and loaded again, as
its compilations and translations are of versions nothing reads.

## Outstanding
- **The NixOS test** (`nix/test.nix`) still finds `plan (en, Qwen/Qwen3-8B-AWQ)` and names its endpoint, and reads
  the run from the top of what `POST /api/runs` answers, which is `StartedRuns` now; it wants `plan`, can leave the
  endpoint to be derived, and takes the first of `runs`.
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

## Review
A read of the branch before merge, by a session that didn't build it: the code against this document and against
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
  the endpoint's engine of the same model, as facts are; or the recipe naming the model (see the last take).
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
recipe part without a digest, or would need a component standing for a remote model. That is a page to write and a
day to weigh, not a build: the two differ in one part's kind and in `Seen.at`'s derivation, and the one is reached
from the other as a follow-up. It should be weighed before this lands rather than after, because O2 is what makes
changing a part's kind cheap, and the deploy closes it.

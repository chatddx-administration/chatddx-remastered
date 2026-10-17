# Bench API

Reference for the `chatddx.bench` package: each name's signature, what it returns and what it raises. What the bench
is and why it is shaped this way is in docs/bench.md. The types it passes through are in docs/catalog-api.md (`Edit`,
`About`, `Subject`, `Kept`), docs/factors-api.md (`Component`, `Registry`, `Skeleton`, `Recipe`, `Trial`, `Case`,
`Scorer`, `Scoring`, `Expectation`, `Finding`, `StructuralError`, `ModelFacts`, `Landing`, `Model`), docs/ledger-api.md
(`RunStarted`, `Run`, `ItemKey`, `Score`), docs/store-api.md (`Store`, `People`, `Rows`, `Connection`),
docs/inventory-api.md (`Inventory`, `EndpointSpec`), docs/facts-api.md (`Facts`, `lints`), docs/identity-api.md
(`Person`, `preferred`, `sees`, `owns`, `collaborates`) and docs/runner-api.md (`Runner`, `Running`, `Grading`,
`Halt`, `ScoreEvent`, `Refused`, `judge_at`).

Paths are relative to `src/chatddx/bench/` unless they start with `src/`, `docs/` or `agents/`.

## Contents
- [Package](#package)
- [Conventions](#conventions)
- [errors.py](#errorspy): `NotFound`, `Ambiguous`, `Conflict`, `MovedOn`, `OverQuota`
- [variation.py](#variationpy): `TriedVariation`
- [model.py](#modelpy): `KINDS` and the other constants, and the values the bench returns
- [seen.py](#seenpy): `Seen`, what the person sees, and the functions the writes share
- [bench.py](#benchpy): `Bench`, the `Seen` with the writes bound
- The writes: [configurations.py](#configurationspy), [components.py](#componentspy), [cases.py](#casespy),
  [taking.py](#takingpy), [saying.py](#sayingpy), [following.py](#followingpy), [runs.py](#runspy)
- [Tests](#tests)

## Package
`chatddx.bench` re-exports `Ambiguous`, `Conflict`, `MovedOn`, `NotFound`, `OverQuota`, `TriedVariation`, `KINDS`,
`WRITTEN`, `word_of`, `Bench`, `Carried`, `Checked`, `Endpoint`, `Family`, `Graded`, `Moved`, `Proposed`, `Reach`,
`Started`, `Taken`, `Written`, `ScorerStarted` and `ScoringEvent`. Edges import from `chatddx.bench`,
never by path; tests import their helpers from `chatddx.bench.test.helpers`.

The modules, and the ones each builds on:
- `errors.py`: `NotFound`, `Ambiguous`, `Conflict`, `OverQuota`, and `MovedOn`, the catalog's.
- `variation.py`: `TriedVariation`: the variation being tried, a plain value.
- `model.py`: the constants and the values the bench returns; on `variation.py`.
- `seen.py`: `Seen`, and the functions the writes share; on `errors.py`, `model.py` and `variation.py`.
- `configurations.py`: `save`, `kept`, `keep_compilation`; on `errors.py`, `model.py`, `seen.py` and `variation.py`.
- `components.py`: `check`, `new`, `fork`, `edit`, `bound`, `keep_language`; on `configurations.py`, `errors.py`,
  `model.py`, `seen.py` and `variation.py`.
- `cases.py`: `case`, `replacement`, `type_case`; on `errors.py`, `model.py` and `seen.py`.
- `taking.py`: `take`, `take_from`; on `errors.py`, `model.py` and `seen.py`.
- `saying.py`: `say`; on `errors.py`, `model.py` and `seen.py`.
- `following.py`: `proposal`, `follow`, `moved`, `follow_moved`; on `components.py`, `errors.py`, `model.py` and
  `seen.py`.
- `runs.py`: `start`, `again`, `resume`, `score`, `REFUSALS`, `ScorerStarted`, `ScoringEvent`; on
  `configurations.py`, `errors.py`, `model.py`, `seen.py` and `variation.py`.
- `bench.py`: `Bench`; on `seen.py` and the writes.

Outside the package, the bench builds on the store, the catalog, `chatddx.identity`, the World, the facts, the runner
and the scoring pass, and holds no SQL.

- **By name or by id.** `thread`, `family`, `run` and `variation` take a name, a `str`, or an id: an `int`, a
  `UUID` for a run. A name is matched whole first, then as `OWNER/NAME`; an id only among what the person sees.
- **Words.** A method that takes `word` takes a key of `KINDS`; another raises `KeyError`.
- **What the person sees.** The catalog takes no person: it gives every thread and expectation with its `About`, and
  the bench keeps what the person `chatddx.identity.sees` (live, and owned or shared), what they `owns` (live, and
  owned) and what they `collaborates` on (live, shared with them and not their own). Of several the person sees, their
  own are taken when they own any, else all of them (`chatddx.identity.preferred`).
- **Messages** name the person by login and the thing by the word for it, for a person to read; nothing in the bench
  is UI.

**Errors.**
- `NotFound` and `Ambiguous`, both `LookupError`s: what the person sees or names.
- `ValueError`: a refused write or variation. `Conflict`, a write the person must say they want, `MovedOn`, an edit
  made on a head that moved on, and `OverQuota`, more than a day takes, are `ValueError`s too.
- `StructuralError`, a `ValueError`: from `Store.get` and `resolve`, when a digest isn't stored or is of another kind.
- The errors of the catalog, the inventory, the runner and its gate pass through unless an entry says otherwise.

## errors.py

### `class NotFound(LookupError)`
Nothing the person sees goes by that name or id.

### `class Ambiguous(LookupError)`
More than one thing the person sees goes by that name or id, or a case has several expectations of theirs to choose
from.

### `MovedOn`
`chatddx.catalog.MovedOn`, re-exported: an edit named a head that isn't the thread's head any more.

### `class OverQuota(ValueError)`
The person has written or started as much as a day takes: typed cases (`chatddx.settings.TYPED_PER_DAY`) or runs
(`RUNS_PER_DAY`); or a run would hold more items than one takes (`ITEMS_PER_RUN`).

### `class Conflict(ValueError)`
The write would undo what the person has unless they say so: taking an expectation when they own one of its case under
its schema, without replacing it.

## variation.py

### `OPTIONAL: tuple[str, ...]`
The parts `Recipe` doesn't require, which a variation can take out.

### `class TriedVariation`
A frozen dataclass: a configuration, or a variation of it being tried.
- `configuration: Edit`: the configuration's edit.
- `name: str`: the name the person called it by.
- `recipe: Recipe | None = None`: its recipe; `None` for a configuration without a compilation.
- `parts: Mapping[str, tuple[str | None, str]] = {}`: for each part replaced, a chunk's digest, or a model's digest for
  `model`, or `None` for one taken out, and the name it was set by.

#### `label: str` (property)
`name`, then `+PART=NAME` for each replaced part, in `RECIPE_PARTS` order.

#### `held(part: str) -> str | None`
The digest the part holds: the replaced one, `None` when it was taken out; else the recipe's; else `None`.

#### `set(part: str, digest: str | None, name: str) -> TriedVariation`
A copy with `part` set to `digest`, by `name`. Setting a part to the recipe's own digest takes it out of `parts`.
- Raises `ValueError("<name> has no recipe to set its <part> in")` without a recipe.
- Raises `ValueError("a configuration always has a <part>: only <OPTIONAL_PARTS> can be taken out")`, `an engine`
  for the engine, for `None` and a part not in `OPTIONAL_PARTS`.

#### `varied: Recipe | None` (property)
The recipe with `parts` replaced over it, validated as a `Recipe`; `None` without a recipe.

## model.py

### Constants
- `KINDS: dict[str, tuple[str, ...]]`: the thread kinds each word names. `configuration` is `skeleton`, each chunk
  part, of `CHUNK_PARTS`, is `chunk.<part>`, `engine` is `engine.local` and `engine.remote`, and `tool`, `scorer`,
  `judge`, `expectation`, `appendix`, `expectation_schema`, `canary_set`, `model` and `facts` are their own kind.
- `WRITTEN: frozenset[str]`: the kinds a person writes as components: `chunk.<part>` for each of `CHUNK_PARTS`,
  `expectation`, `appendix`, `scorer` and `judge`.
- `LABELLED: tuple[Part, ...]`: `("view", "resource")`, the parts of a scorer that have labels.
- `COMPILED_LANGUAGE: str`: `"a compiled configuration's language comes from its recipe"`, what `new` and `follow`
  refuse a language with.
- `PLACEHOLDERS: dict[SlotName, str]`: what stands in for each slot of a request rendered to be looked at:
  `‹vignette›`, `‹appendices›`, `‹completion›`, `‹expectation›`.
- `SAVED: dict[Kept, …]`: what `Saved.what` and `Written.what` call each of the store's `Kept`: `created`,
  `a new version` for `edited`, and `unchanged`.
- `word_of(kind: str | None) -> str`: the word in `KINDS` that names `kind`, `configuration` for `skeleton`;
  `thread` for `None` and a kind no word names.

### Values
Frozen dataclasses that `Bench` returns.

#### `class Endpoint`
The World's endpoint, its engine in the store.
- `name: str`
- `spec: EndpointSpec`: as the inventory declares it.
- `model: Model`: the model its engine serves (`chatddx.factors.engine.model_of`). Its `name` is what the facts are
  keyed by, its `digest` what a recipe names.
- `engine: str` (property): `spec.engine`.

#### `class Family`
- `id: int`
- `about: About`
- `vignette: Vignette`: its current one, that of its latest binding.
- `cases: tuple[str, ...]`: the stored cases of `vignette`, the bare one first, then by digest; never empty.
- `case: str` (property): `cases[0]`, its default case.
- `name: str` (property): `about.name`, else `family <id>`.

#### `class Reach`
What a scorer's view can hold a variation to, over some families.
- `thread: int`: the scorer's thread.
- `scorer: str`: its name.
- `view: int`: the view's position.
- `label: str`
- `offered: bool`: whether the variation's output offers what the view reads.
- `cases: int`: how many families were asked about.
- `missing: list[Family]`: those with no expectation the view picks something from.
- `choosing: list[Family]`: those with several expectations to choose from.
- `have: int` (property): `cases` less the missing and those to choose from.

#### `class Graded`
A run's score under one scorer, or why there is none.
- `name: str`: the scorer's, as the person calls it.
- `scorer: Scorer`
- `labels: dict[int, str]`: its view labels, by position.
- `score: Score | None = None`
- `findings: list[Finding] = []`
- `refused: str | None = None`: why it wasn't scored.
- `label(view: int) -> str`: the view's label, else `view <view>`.

#### `class Proposed`
- `divergence: Divergence`: the catalog's, with the base, the origin's head and what the fork varies.
- `proposal: Recipe | Component`
- `digest: str`: the component's, or the compiled skeleton's.
- `compilation: str | None`: for a recipe.

#### `class Moved`
What a configuration was compiled for that has since moved on and what following it would keep. Made by `moved`,
stored by `follow_moved`.

- `facts: Behind | None`: the catalog's `/facts` entry when the facts that was compiled against were corrected
  where they change what it sends: the facts compiled against as `digest`, and the facts thread's head as `head`.
  `None` when they're already correct.
- `model: Behind | None`: the catalog's `/recipe/model` entry when the model thread has moved on: the
  model held as `digest`, and its thread's head as `head`. `None` when it's unmoved.
- `about: str`: the name of the model the recipe names, as the facts name it; the model's head's name when the
  model moved on.
- `digest: str | None`: the skeleton the head's recipe, with the model's head where it moved on, compiles to against
  the current facts about it. `None` when the facts refuse it.
- `compilation: str | None`: that compilation's digest, naming the facts it was compiled against. `None` as for
  `digest`.
- `refused: str | None`: why compiling is refused: the current facts refuse what the recipe asks, or can't work it
  out. `None` when `digest` and `compilation` are set.

#### `class Written`
- `edit: Edit`: what was kept.
- `what: Literal["created", "a new version", "unchanged"]`
- `findings: list[Finding]`: `seen.py:linted` of its digest, a configuration's skeleton among them.
- `cases: dict[str, str] = {}`: for an appendix's edit, each case that held the old version, and its replacement.

#### `class Checked`
- `digest: str`: the component's, as a write would store it.
- `findings: list[Finding]`

#### `class Taken`
By case digest:
- `taken: dict[str, int]`: the thread each was taken into.
- `kept: dict[str, int]`: the person's own.
- `choosing: dict[str, list[int]]`: the shared threads offered, when there are several.
- `missing: list[str]`: the cases with none shared.

#### `class Carried`
A language a variation's cases are sent in, or left out of.
- `language: str | None`: the cases' language; `None` for the configuration's own when it is unknown.
- `cases: list[str]`: the cases, by digest, in the order given.
- `skeleton: Skeleton | None = None`: what they are sent as, the configuration's skeleton or its translation; `None`
  when they are left out.
- `translated: bool = False`: whether `skeleton` is a translation.
- `refused: str | None = None`: why they are left out.

#### `class Started`
What `start` started.
- `runs: list[tuple[Carried, Running]]`: a run per language, those sent as written first.
- `left_out: list[Carried]`: the languages left out, each with its cases and why.
- `first: Running` (property): the first run, which the others were started with.

## seen.py
### `class Seen`
`Seen(conn: Connection, person: Person, inventory: Inventory)`: what the person sees. It writes nothing. What the
writes share is in "seen.py's functions", below.

#### `expectation_choices(cases: Sequence[str], schema: str) -> dict[str, dict[int, str]]`
For each case, the threads of `threads.expecting(rows, cases, schema)` the person `owns`, each with its head digest;
`{}` for none. What `expectation` and `scoring` pick from. It refuses nothing.

#### `worded(thread: int) -> tuple[Edit, About, str]`
`thread_by_id(thread, <word>)` and the word, where `<word>` is the word in `KINDS` for the thread's kind, else
`thread`.

### People

#### `login(person: int | None) -> str`
The person's login, or `nobody` for `None`.
- Raises `People.get`'s `LookupError` for an unknown id.

### Threads

#### `threads(word: str, *, deleted: bool = False, purpose: Purpose | None = None, answering: str | None = None) -> list[tuple[Edit, About]]`
The heads of `threads.heads(rows, kind)` the person `sees`, each with its `About`, for each kind `KINDS[word]` names,
in that order, then in thread id order.
- `deleted`: their own deleted ones instead.
- `purpose`: only the configurations whose skeleton has it, `generation` or `judge`.
- `answering`: only the configurations whose answer's JSON Schema is titled so.

Raises `ValueError("only a configuration has a purpose and an answer: <word>")` for `purpose` or `answering` and
another word.

#### `thread(found: int | str, word: str | None = None, *, deleted: bool = False) -> tuple[Edit, About]`
The head of the thread the person sees that `found` names, and its `About`.
- `word`: only a thread of a kind `KINDS[word]` names; any kind for `None`.
- `deleted`: also the person's own deleted thread, by id.

By name, of the threads called `found`, the person's own are taken when they own any, else all of them; when none is
called `found`, the same among those whose qualified name it is. Raises:
- `Ambiguous("<word> '<name>' names a <kind> and a <kind>")`, for a name held in two of the word's kinds.
- `Ambiguous("<word> '<name>' names <n>; name one as OWNER/NAME")`
- `NotFound("no <word> '<name>' for <login>")`, and `NotFound("no <word> <id> for <login>")` by id; `thread` for no
  word.

#### `holder(digest: str, recipe: Recipe | None = None) -> tuple[Edit, About] | None`
A thread the person sees whose head is `digest`, with `recipe` when it is given, their own if any, the lowest; `None`
when none is.

#### `title(digest: str) -> str`
What the person calls `digest`: the name of a thread they see whose head it is, their own first, else
`titles.title_of`.

### Components and the World

#### `facts: Facts` (property)
The facts about each model, from the store: the head of every live `facts` thread, whoever owns it, through
`Facts.of`, so that of two about one model the later edit wins. Read each time, so that a fact corrected while the
bench lasts is used.

#### `endpoint(name: str) -> Endpoint`
The World's endpoint `name`, with the model its engine serves, cached.
- Raises `NotFound` with the inventory's message for an unknown endpoint.
- Raises `NotFound("endpoint '<name>' serves engine <short>, which isn't in the store: load its World with
  init-data")`.

### Families and expectations

#### `families(tags: Iterable[str] = ()) -> list[Family]`
The families the person sees that have a case, by name. A family's case is the bare case of its current vignette when
it is stored, else the first stored case of that vignette.
- `tags`: only those with any of them.

#### `family(found: int | str) -> Family`
The family the person sees that `found` names, by name as `thread` finds a thread, with `case` as the word, or by id,
when it has a case.
- Raises `NotFound("no case <id> for <login>")` by id.

#### `case_titled(title: str) -> tuple[Family, str]`
The family and the case `title` names: a family's name, for its default case; or `FAMILY with APPENDIX, …`, for the
case of its current vignette with those appendices the person sees, in order.
- Raises `NotFound("no appendix <names> of <family>")`.
- Raises `NotFound("no case <title> for <login>")` for a case that isn't stored.

#### `expectation_schemas(case: str) -> list[str]`
The schemas of the expectations of `case` the person sees, shared ones included, sorted, without repeats.

#### `expectation(case: str, schema: str) -> Expectation | None`
The person's own expectation of `case` under `schema`: `seen.py:picked`, or `None`.
- Raises `Ambiguous("case <case> has expectations to choose from, in threads <t1>, <t2>, …")`.

#### `shared(case: str, schema: str) -> list[tuple[Edit, About]]`
The heads of `threads.expecting(rows, [case], schema)` the person `collaborates` on, each with its `About`, in thread
id order: what they could take.

### The variation being tried

#### `variation(configuration: int | str, parts: Mapping[str, str | None] | None = None, head: int | None = None) -> TriedVariation`
The configuration `thread(configuration, "configuration")` finds, with `parts` replaced, each named by its `title`,
or `none` for one taken out. Found by name, it is called by that name, without the person's own `<login>/`; by id,
by its thread's name, else its title.
- `parts`: part → chunk digest, a model's digest for `model`, or `None` to take the part out.
- `head`: an earlier edit of the configuration to start from.

Raises:
- `thread`'s `NotFound`.
- `NotFound("no edit <head> of configuration <configuration>")`
- `ValueError("no part '<part>': the parts are <RECIPE_PARTS>")`
- `ValueError("<digest> isn't a stored chunk of <part>")`, or `ValueError("<digest> isn't a stored model")` for
  `model`.
- `TriedVariation.set`'s.

#### `variation(configuration: int, parts: Mapping[str, str | None] | None = None, head: int | None = None) -> TriedVariation`
The configuration `thread_by_id(configuration, "configuration")` finds, with `parts` replaced.
- `parts`: part → chunk digest, an engine's digest for `engine`, or `None` to take the part out.
- `head`: an earlier edit of the configuration to start from.

Raises:
- `thread_by_id`'s `NotFound`.
- `NotFound("no edit <head> of configuration <configuration>")`
- `ValueError("no part '<part>': the parts are <PARTS>")`
- `ValueError("<digest> isn't a stored chunk of <part>")`, or `ValueError("<digest> isn't a stored engine")` for
  `engine`.
- `TriedVariation.set`'s.

#### `at(variation: TriedVariation, endpoint: str | None) -> Endpoint`
The endpoint the variation runs at: the one named, or the one serving its recipe's model.

Raises `ValueError`:
- `"<label> names no model: name the endpoint to send it to"` for a hand-written configuration and no endpoint;
- `"no endpoint serves model <title>"` when none serves the recipe's model;
- `"<names> serve model <title>; name the one to use"` when several do and none is named;
- `"endpoint '<name>' serves another model than <label>'s, <title>"` for a named endpoint serving another model.

#### `skeleton(variation: TriedVariation, into: str | None = None) -> Skeleton`
Takes a `variation` and a language, or `None`, and returns the request it sends. With nothing replaced and no `into`,
the configuration's own skeleton, resolved from the store; otherwise the varied recipe compiled with the running
code, against `seen.py:compiled_with`, the facts about its model (the configuration's pinned facts for an unvaried
one, the current facts for a varied one), and into `into` when given, every text translated. Nothing is stored.

Raises `StructuralError`:
- `"<label> has no translations into <into>"` for `into` on a configuration with no recipe;
- what `compile_request` raises: `"no translations into <into>"` and
  `"no translation into <into> for '<text>'"` when the recipe's translations don't carry it there, and a level or
  recommended sampling the facts refuse, or can't work out for a model without facts, as `"<model>: <why>"`.

#### `landed(variation: TriedVariation) -> dict[str, Landing]`
Where the varied recipe's intents land, by part: `reasoning` for a reasoning level, `sampling` for a recommended
sampling, each the level the engine's model is asked for, with `nearest`, why, when the facts land it on its nearest
(`chatddx.factors.request.landings`). Against the facts its compilation names when nothing is replaced, else
`facts_for` its engine. `{}` without a recipe; no key for a part that holds no intent.
- Raises `landings`' `StructuralError` for what the facts refuse.

#### `own_language(variation: TriedVariation) -> str | None`
The language the variation is written in: its varied recipe's (`language.recipe_language`, its texts' vote), or,
without a recipe, its skeleton's (`language.language_of`).

#### `translated(recipe: Recipe | None) -> list[str]`
The languages the recipe's translations carry it into, sorted; `[]` without a recipe or translations.

#### `languages(variation: TriedVariation, cases: Sequence[str]) -> list[Carried]`
`cases` grouped by the language each is sent in, a `Carried` each. First the cases sent as written, with
`skeleton(variation)`, in its own language: its varied recipe's (`language.recipe_language`), else its skeleton's
(`language.language_of`); those in it and those of no language. Then each other language, sorted: translated, with
`skeleton(variation, language)`; or left out, `refused` `<label> has no translations into <language>` when the
translations hold none, else the compile's `StructuralError`. When its own language is `None`, a case of a language
the translations don't hold goes as written too. A case's language is its family's. Nothing is stored.
- Raises `skeleton(variation)`'s errors for the cases sent as written.

#### `request(variation: TriedVariation, engine: str | None, seed: int) -> dict[str, JsonValue]`
The request rendered from the skeleton with `PLACEHOLDERS` for its slots and `seed`.
- `engine`: whose `served` model the request carries; `‹model›` without one.

#### `findings(variation: TriedVariation, engine: str, seed: int, carried: Sequence[Carried] | None = None) -> list[Finding]`
`lints` of the variation's trials on `engine`; for a judge configuration, of a `Judge` of its skeleton on `engine`,
whatever `carried`.
- `carried`: what `languages` gave for the cases to lint over: a trial for each language that sends some, its
  skeleton in that language, their findings without repeats; and for each language left out a
  `translations.missing` warning, subject the configuration's digest, `<n> cases are in <language>, and left out:
  <why>` (`1 case is` for one). `[]` for none. Without it, the first case of the families the person sees, and `[]`
  when there is none.

#### `scorers(run: RunStarted | None = None) -> list[tuple[Edit, About, Scorer]]`
`threads("scorer")`, each with its scorer.
- `run`: only those whose scorer applies to it: the run's skeleton offers each of its views, as `reach` has it, and
  the World lets each of its judges score the trial's cases (`chatddx.runner.judge_at`).

#### `labels(scorer: str) -> dict[int, str]`
What a scorer digest's views are called for the person: the view labels of the head `holder(scorer)` gives, else
of the latest edit that held it in a scorer thread they see, their own first; `{}` when none did.

#### `reach(variation: TriedVariation, families: list[Family]) -> list[Reach]`
A `Reach` for each view of each of `scorers()`, by the scorer's thread name, else its title, over `families`; `[]`
for a judge configuration. A view is `offered` when it reaches the skeleton's `output_schema`, or, for a view of the
whole answer, when there is none. A view not offered has no `missing` and no `choosing`.

### Runs and scores
The run's trial, skeleton and scorers are resolved through `Store.get`, which raises `StructuralError` for one that
isn't stored or is of another kind.

#### `runs(*, reaching: str | None = None, scored_by: str | None = None, started_with: UUID | None = None) -> list[RunStarted]`
The live runs the person owns, newest first. A collaborator on a run doesn't see it.
- `reaching`: only those whose trial holds the digest in its closure, or whose skeleton was compiled from a recipe
  that does.
- `scored_by`: only those with a score under a scoring that holds the digest in its closure: its scorer, an
  expectation, the expectation schema or a judge.
- `started_with`: only the run and those started with it.

#### `run(found: UUID | str | None = None) -> RunStarted`
By id, the run, when it has started and the person owns it, live; by a `str`, the one of `runs()` whose id starts
with it; with neither, the latest of `runs()`.
- Raises `NotFound("no run <id> of yours")`.
- Raises `NotFound("<login> has no runs")`.
- Raises `NotFound("no run of yours starts with '<prefix>'")`.
- Raises `Ambiguous("<n> runs of yours start with '<prefix>'")`.

#### `described(run: RunStarted) -> str`
`<run's name, else skeleton's title> × <endpoint, else engine's title> × <case's title, else "<n> cases">[, in
<language>, translated] (seed <seeds>)`, the language when every compilation of the run's skeleton is one into it.

#### `scoring(run: RunStarted, scorer: str) -> Scoring | None`
The scoring the run would be scored under now: for each of the trial's cases in order, `picked` of
`expectation_choices` under the scorer's expectation schema, cases without one left out. `None` when no case has one.
Nothing is stored.
- Raises `Ambiguous` when a case has several to choose from.

#### `unscored(run: RunStarted) -> list[str]`
The scorers of `scorers(run)` without a whole score of the run under `seen.py:scoring`, and those whose scoring
raises `Ambiguous`. A score is whole when it has finished, holds an item for each of the run's items and each of the
scorer's views, and no judge call of it was stopped.

#### `outstanding() -> list[tuple[RunStarted, list[str]]]`
Each finished run of `runs()`, newest first, with its `unscored`, when there are any.

#### `scores_of(run: RunStarted, every: bool = False) -> list[Graded]`
The latest score of the run under each scorer that scored it, by the scorer's `title`.
- `every`: every score of the run, newest first.

#### `score_of(run: RunStarted, score: UUID) -> Graded`
Score `score` of `run`, latest or not.
- Raises `NotFound("no score <score> of run <run>")`.

#### `score_of(run: UUID, score: UUID) -> Graded`
Score `score` of `run`, latest or not.
- Raises `run_by_id`'s `NotFound`.
- Raises `NotFound("no score <score> of run <run>")`.

#### `scorer_name(scorer: str) -> str`
What the person calls a scorer digest: the name of `holder("scorer", scorer)`, else its title.

#### `scored_by(digest: str) -> list[RunStarted]`
The runs of `runs()` with a score under a scoring that holds `digest` in its closure: its scorer, an expectation, the
expectation schema or a judge.

#### `rendered_again(run: Run) -> dict[ItemKey, str | None]`
For each item, whether its first request, rendered again from the trial and the vignette at its source, is what was
sent: `None` when it is, else why not:
- `the vignette at the source isn't the one sent`;
- `the request renders otherwise now`;
- the message of the `LookupError` or `StructuralError` that fetching or preparing the case raised.

### seen.py's functions
Each takes the `Seen` first, but `check_scorer`. Besides those below: `choices(seen, cases, schema)`, the old
`expectation_choices`; `picked(seen, cases, schema)`, `threads.picked` of each, its `LookupError` as `Ambiguous`;
`scoring(seen, run, scorer)`, the old `Seen.scoring`; `labels_of(seen, edit)`; `worded(seen, thread)`;
`compiled_with(seen, variation)`; `trial(seen, skeleton, engine, cases, seeds, cleanup=())`; and `left_out`.

#### `compiled(recipe: Recipe, facts: ModelFacts | None | Literal["current"] = "current", into: str | None = None) -> tuple[Registry, Compilation]`
The recipe compiled by the running code against `facts`, `facts_for` its engine for `"current"`, and into `into` when
it is given (`chatddx.factors.request.compiled`), in a registry with what it refers to and those facts, which the
compilation names. Nothing is stored.

#### `linted(digest: str) -> list[Finding]`
`lints` of the stored component, with `language.language_of` over `rows` for languages; a trial or a judge with its
skeleton's compilations (`add_compilations`).

#### `add_compilations(registry: Registry, skeleton: str) -> None`
Adds each stored compilation of `skeleton`, and the facts it names, to `registry`, where the factors' lint reads them.
`findings` adds them for a configuration with no recipe; one with a recipe pairs its own engine, so has none to
check. `components.py:check` adds them for a judge.

#### `check_kind(seen: Seen, thread: int, word: str, held: Component | TriedVariation) -> None`
- Raises `ValueError("<word> <thread> holds <kind> components, not <kind>")`, a variation's kind being `skeleton`.

#### `check_expecting(expectation: Expectation, thread: int | None, then: str = "edit that one") -> None`
- Raises `ValueError("<login> has their own expectation of <case's title> under <schema's title>, in thread <t>:
  <then>")` when the person owns an expectation thread of its case and schema other than `thread`.

#### `check_scorer(scorer: Scorer) -> None`
- Raises `ValueError` with `chatddx.scorers.shipped.problems` joined by `; `, for a scorer the running code could
  never score with.

#### `trial(skeleton: Skeleton, engine: str, cases: list[str], seeds: Sequence[int], cleanup: tuple[CleanupOp, ...] = ()) -> tuple[Registry, Trial]`
A `Trial` of the skeleton, the engine, the cases, the cleanup steps and the seeds, and a registry holding it with
what it refers to.

#### `labels_of(edit: Edit) -> dict[int, str]`
The view labels the edit of a scorer thread was written with, by position.

## bench.py

### `class Bench(Seen)`
`@final`. The `Seen`, with each write bound as a method of the same name: `save` from `configurations.py`; `new`,
`fork`, `edit` and `check` from `components.py`; `case`, `replacement` and `type_case` from `cases.py`; `take` and
`take_from` from `taking.py`; `say` from `saying.py`; `proposal`, `follow`, `moved` and `follow_moved` from
`following.py`; and `start`, `again`, `resume` and `score` from `runs.py`.

## configurations.py
A configuration's writes, `save` here and `fork` and `edit` in components.py, keep the skeleton's edit through
`Catalog.keep`, in one transaction, and, for a variation with parts replaced, the compilation of its skeleton by the
running code, as the edit's compilation; otherwise the edit keeps the configuration's. They come back as `Written`,
with `seen.py:linted` of the skeleton.

### `save(variation: TriedVariation, name: str) -> Written`
`edit` of the person's one live configuration named `name`, on its head, else `fork` of `variation.configuration`.
- Raises `Ambiguous("<login> has <n> configurations named '<name>'")`.

### `fork(variation: TriedVariation, name: str) -> Saved`
A new configuration of the person's own named `name`, forked from `variation.configuration`.

### `edit(thread: int, variation: TriedVariation, head: int) -> Saved`
A new version of `thread`, named by its name or else its title; `unchanged` when its head is the skeleton already,
with the same recipe (`Catalog.keep`).

- `head`: the head the person saw.

Raises:
- `thread_by_id`'s `NotFound`.
- `NotFound("no configuration <thread> of yours")`
- `MovedOn`

### `keep_compilation(variation: TriedVariation, into: str | None = None) -> str | None`
For a variation with parts replaced, or translated `into` a language, the compilation of its skeleton by the running
code, against `Seen.compiled_with`, stored; its digest. `None` otherwise.

## components.py
`new`, `fork` and `edit` write a component, in one transaction, with its references, which must be stored; its
language, through `keep_language`; and its edit through `Catalog.keep`. A configuration's, a recipe or a variation,
is written as configurations.py says. An appendix is `bound` first; an appendix's edit also stores, as
`Written.cases`, each case that held the old version at the same vignette, with the new version in its place. An
expectation's edit keeps to its family: the case it is moved to, as carrying moves it, must be of the family the
old one is of. They raise, and leave nothing written:
- `ValueError("<case> isn't a case of the family <old case> is of")` for an expectation's edit.
- `bound`'s, `check_scorer`'s and `check_expecting`'s.

### `check(component: Component) -> Checked`
The component as a write would store it, with its lints. Nothing is written.
- Raises `ValueError("a person doesn't write <kind> components")`, the registry check's `StructuralError`, and
  `bound`'s and `check_scorer`'s.

### `new(component: Component | Recipe, name: str, language: str | None = None, labels: Labels | None = None) -> Written`
`component` as a new thread of the person's own named `name`.
- `component`: a `Recipe` is compiled by the running code and kept as a configuration.
- `labels`: a scorer's view and resource labels.

For a recipe, raises:
- `ValueError(COMPILED_LANGUAGE)` for a language.
- `ValueError("only a scorer's views and resources have labels")` for labels.
- `ValueError("<digest> isn't a stored chunk of <part>")`, or `ValueError("<digest> isn't a stored engine")` for
  `engine`.
- the compiler's errors, the facts' refusals among them (`seen.py:compiled`).

### `fork(thread: int, name: str, held: Component | TriedVariation | None = None, language: str | None = None, labels: Labels | None = None) -> Written`
A new thread of the person's own named `name`, forked from the head of `thread`, holding `held`, else the head; for a
configuration, forked from the edit the variation varies, else from the head as it is. A scorer forked as it is,
without labels, keeps the head's.
- Raises `thread`'s `NotFound("no <word> <thread> for <login>")`, and `check_kind`'s.
- Raises `ValueError("<label> isn't a variation of configuration <thread>")`.
- Raises `ValueError(COMPILED_LANGUAGE)` and `ValueError("only a scorer's views and resources have labels")` for a
  configuration given a language or labels.

### `edit(thread: int, head: int, held: Component | TriedVariation, language: str | None = None, labels: Labels | None = None) -> Written`
`held` as a new version of `thread`; `unchanged` when it is the head already, for a configuration with the same
recipe (`Catalog.keep`), and, for a scorer given labels, they are the head's. A scorer edited without labels keeps
none, unless it is the head's, which is then `unchanged`. A configuration takes any variation, of it or another.

Raises:
- `thread`'s `NotFound`.
- `NotFound("no <word> <thread> of yours")` for a thread the person sees but doesn't own.
- `check_kind`'s, and `fork`'s for a configuration given a language or labels.
- `MovedOn` when the head isn't `head`.

### `bound(appendix: Appendix) -> Appendix`
The appendix with its line endings LF.
- Raises `ValueError("an appendix is bound to the current vignette of a case you see")`.

### `keep_language(digest: str, language: str) -> None`
The language written for `digest` when it has none; nothing when it has the same.
- Raises `ValueError("<title> is in <language> already: a text's language is the same wherever it is held")`.

## cases.py

### `case(family: int, appendices: Sequence[str]) -> str`
The digest of a `Case` of `family`'s current vignette with `appendices`, in order, stored. Nothing is written in the
catalog.
- Raises `NotFound("no appendix <digest> for <login>")` for an appendix no thread the person sees holds.
- Raises the store's check for an appendix of another vignette.

### `replacement(case: str) -> str`
The digest of `case`, left at an earlier vignette of its family, rebound to the current one and stored with its
rebound appendices: `families.replacement`'s, of a case of a family the person sees.
- Raises `NotFound("no case <case> for <login>")`.
- Raises `ValueError("<case> is at its family's current vignette already")`.

### `type_case(text: str, *, language: str, name: str | None = None, source: str | None = None) -> Family`
The family of a case the person typed: the text kept in a database source, its case stored, and its family adopted by
id alone, owned by the person, in one transaction.
- `language`: the language it is written in, an entry about the family.
- `name`: an entry about the family.
- `source`: the database source to keep it in; the World's one when not given.

Raises, before writing:
- `ValueError("a typed case holds text")`
- `ValueError("a typed case may not hold U+0000, which can't be stored")`
- `ValueError("a typed case holds at most <TYPED_TEXT_LIMIT> characters, not <n>")`
- `ValueError("a name can't be empty: none leaves the case unnamed")`
- `language_tag`'s `ValueError`.
- `OverQuota("<login> has typed <n> cases in the last day, as many as a day takes")`
- `ValueError` with `Inventory.source`'s message, for a source that isn't there or isn't a database source, or, with
  none named, none or several of the World's database sources (docs/inventory-api.md, "inventory.py").

### `carry(thread: int, head: int, case: str) -> Written`
`edit_component` of the expectation `thread` onto `case`, with the same schema and data.
- Raises `ValueError("<word> <thread> isn't an expectation")`.
- Raises `ValueError("<case> isn't a case of the family <old case> is of")`.

### Finding cases by their titles

#### `appendices_of(family: int) -> dict[str, str]`
The named appendices the person sees of the current vignette of `family`, each name with its head's digest.
- Raises `family_by_id`'s `NotFound`.

#### `case_titled(title: str) -> tuple[Family, str]`
The family and the case `title` names: a family's name, for its default case; or `FAMILY with APPENDIX, …`, for the
case of its current vignette with those appendices, in order.
- Raises `NotFound("no appendix <names> of <family>")`.
- Raises `NotFound("no case <title> for <login>")` for a case that isn't stored.

#### `case_titles() -> list[str]`
The titles of the cases that send appendices, sorted.

## taking.py
Taking forks with `Catalog.create(head.digest, person.id, forked_from=head.id, name=about.name)`, so the fork keeps the
shared thread's name and the catalog checks its one-expectation rule.

### `take(cases: Iterable[str], schema: str, owner: str | None = None) -> Taken`
For each of `cases`, once, in order, in one transaction: the person's own expectation under `schema` is kept, the
lowest thread of several; else, of those shared with them, one is forked into a thread of their own, several are to
choose from, and none is missing.
- `owner`: only those shared by this login.

Raises:
- `ValueError("<schema> isn't a stored expectation schema")`
- `NotFound("no person '<owner>'")`

### `take_from(thread: int, replace: bool = False) -> int`
The id of thread `thread`, an expectation the person sees, forked into a thread of their own.
- `replace`: delete the person's own of its case and schema in the same transaction.

Raises:
- `thread_by_id`'s `NotFound`.
- `ValueError("expectation <thread> is yours already")`
- `Conflict("<login> has their own expectation of <case's title> under <schema's title>, in thread <t>: replace it to
  take this one")`, without `replace`.

## saying.py

### `say(thread: int, *, name: str | None | EllipsisType = ..., description: str | None = None, tags: Collection[str] | None = None, collaborators: Collection[str] | None = None, deleted: bool | None = None) -> About`
What is said of `thread`, a thread the person owns, deleted or not, and the `About` afterwards. Each entry that changes
what holds is written, in one transaction.
- `name`: `None` takes it away; `...` leaves it.
- `description`: `None` leaves it.
- `tags`, `collaborators`: the whole set, logins for collaborators; `None` leaves it.
- `deleted`: `True` deletes, `False` restores; `None` leaves it.

Raises, before writing:
- `NotFound("no <word> <thread> of yours")`
- `ValueError("<word> <thread> is deleted: restore it to say more of it")`
- `ValueError("a name can't be empty: none takes it away")`
- `ValueError("a tag can't be empty")`
- `NotFound("no person '<login>'")`
- `ValueError("<word> <thread> is yours: it is shared with others")` for the person's own login.
- `Seen.check_expecting`'s, ending `delete that one to restore this`, for restoring a second expectation of a case and
  schema.

## following.py

### `proposal(thread: int) -> Proposed | None`
What following the origin of `thread`, a thread the person sees, would keep. `None` when `thread` isn't a fork or its
origin hasn't moved on, when the origin's thread isn't one the person `sees`, and when the catalog proposes nothing.
Nothing is stored.
- Raises `NotFound("no <word> <thread> for <login>")`.
- Raises `ValueError("<word> <thread>'s changes don't fit its origin's head: …")`.

### `follow(thread: int, head: int, language: str | None = None) -> Written`
The proposal kept as a new version of `thread`, based on the origin's head; `what` is `a new version`, also when the
digest is the head's. A scorer keeps the labels of whichever side's views and resources the proposal keeps.

Raises:
- `thread_by_id`'s `NotFound`.
- `NotFound("no <word> <thread> of yours")`
- `ValueError("<word> <thread> has nothing to follow")`
- `ValueError(COMPILED_LANGUAGE)`
- `ValueError("<kind> components have no language of their own")`
- `Seen.check_expecting`'s and `Seen.check_scorer`'s.
- `MovedOn`

### `moved(thread: int) -> Moved | None`
`None` when the head has no compilation or `behind` names neither `/facts` nor `/recipe/model`.

### `follow_moved(thread: int, head: int) -> Written`
the head's recipe, with the model's head where it moved on, compiled
against the current facts about it, kept as a new version with its compilation; refused as
`ValueError("configuration <thread> was compiled for nothing that has moved on")` and
`ValueError("configuration <thread> can't follow <what> <model>: <why>")`.

Raises:
- `thread_by_id`'s `NotFound`.
- `NotFound("no configuration <thread> of yours")`
- `ValueError("configuration <thread> has no corrected facts to follow")`
- `ValueError("configuration <thread> can't follow the facts about <model>: <why>")`
- `MovedOn`

## runs.py

### `REFUSALS`
`(LookupError, TypeError, ValueError, NotImplementedError, Refused)`: what `score` takes as a scorer refused.

### `start(variation: TriedVariation, endpoint: str | None, cases: list[str], seeds: Sequence[int], cleanup: Sequence[CleanupOp] | None = None, execution: Execution | None = None, canaries: str | None = None) -> Started`

A run of the variation for each language `Seen.languages(variation, cases)` sends cases in, in its order, at the
`Endpoint` `Seen.at(variation, endpoint)` gives, over that language's cases with `seeds`, its replicates, its cleanup
steps, its execution and the canary set stored under the digest `canaries`; the languages left out are
`Started.left_out`.

Raises, before any run starts:
- `ValueError("<label> is a judge configuration: a judge is asked as runs are scored, and isn't run on cases")`
- `ValueError("no case can be sent: <why>; …")`, each language's, when every case is left out
- `OverQuota("a run holds at most <ITEMS_PER_RUN> items, not <n>")`, a language's cases times the seeds
- `OverQuota("<login> has started <n> runs in the last day, as many as a day takes")` for one run, and
  `OverQuota("<login> has started <n> runs in the last day, and a day takes <RUNS_PER_DAY>, not <m> more")` for several
- `Seen.languages`' and `Seen.at`'s.

As each run starts, `resolve`'s for `canaries`, the runner's and its gate's, and the runner's `ValueError` for a
connection not in autocommit mode; a later run's leaves none of the runs before it begun.

### `again(run: RunStarted, seeds: Sequence[int]) -> Running`
The run's trial run again at its endpoint with `seeds`, its engine, cleanup, execution and canary set kept, as `start`
runs a variation, named by the run's name, else its skeleton's title, and saying what the run said it varied. It is one
run, in the run's language, and is started alone: it has no `with` entry. The gate refuses an endpoint that serves
another engine now (`Refused("endpoint '<name>' serves engine <digest>, the trial's is <digest>")`).

### `resume(run: RunStarted) -> Running`
A run of the person's own resumed by the runner (docs/runner-api.md, `Runner.resume`).

### `score(run: RunStarted, scorers: Collection[str] | None = None, on_event: Callable[[ScoringEvent], None] | None = None, halt: Halt | None = None) -> list[Graded]`
The run scored by the scoring pass under each of `scorers_for(run)`, as `scoring` builds it now, by name.
- `scorers`: only these digests.
- `on_event`: given a `ScorerStarted` as each scorer's score starts, then the scoring pass's events as they come
  (docs/runner-api.md, "score.py").
- `halt`: once set, from any thread, the scorer under way is halted and finished with what it has, and those not
  started are refused as `stopped`.

It raises nothing for a scorer that can't score: that is a `Graded` with `refused`, either `none of the run's cases has
an expectation` or the message of one of `REFUSALS`. One raised while it sends is refused after its score is
finished with what it has. A `KeyboardInterrupt` is taken as `halt`, and isn't raised again.

### `class ScorerStarted`
A frozen dataclass.
- `scorer: str`: the digest.
- `name: str`: as `score` names it.
- `score: UUID`

### `type ScoringEvent = ScoreEvent | ScorerStarted`
`ScoreEvent` is `chatddx.runner.ScoreEvent`.

## Tests
In `src/chatddx/bench/test/`. The repl's and the API's tests reach the bench too, through their own fixtures over the
same test World.
- `conftest.py`: `template` is `curated`, the test World as init-data lands it, with alice's giftbag, copied for each
  test; `autocommit` is on; `alice` is the test World's person, `bob` a new one with nothing; `bench` is alice's, on
  the test World's inventory.
- `helpers.py`: `SOURCE`, the test World's vignette source; `trial(conn, plan, recipe, *ids)`, a stored trial of one
  of its recipes on `QWEN`, seed 7, over its cases of those vignette ids; `ran(conn, by, made, finished=True)`, a run
  of it recorded without sending; `another_expectation(bench, case, data)`, a second expectation of the person's own
  for the case, left by two writers at once; `component(doc)`, a component from its JSON; `owned(bench, case,
  schema)`, the person's own expectation threads; `view_labels(bench, edit)`; `varying(bench, run)`, what a run says
  it varied.
- `test_seen.py`: what a person sees, by name, `OWNER/NAME` and id; variations; runs and what reaches a digest; what is
  left to score; the expectation a case is held to, and several to choose from; scorers that apply, judged or not;
  a run's scores; judge configurations; a swapped model keeping every other pick, where its intents land, on their
  nearest or not, and a level its model refuses; a hand-written configuration on another model than its skeleton is
  worked out for; a configuration found by its name; saving, forking and editing; taking.
- `test_runs.py`: a run's seeds, cleanup, execution and canaries, kept when it runs again; what it varied; a run at
  the endpoint serving its model, or one named, refused for an endpoint serving another model and for a model two
  endpoints serve; its items, cases times seeds; resuming one's own; the sources' cleanup and the endpoint's canaries
  and execution; a start of a run per language, one translated and started with the first, the cases left out, a start
  that can send none refused, and the day's quota over several runs.
- `test_writes.py`: configurations from recipes; chunks and expectations, new, edited and forked, with their
  languages; what is refused; an expectation's lints and the one-expectation rule; judges, and a judge on another model
  than its skeleton is worked out for.
- `test_cases.py`: appendices, cases of them, and an appendix's edit storing a replacement; carrying an expectation;
  refusals; a late case's replacement after a repair; cases found by title.
- `test_typed.py`: a typed case with its family, name and language; the same text typed twice; refusals and the day's
  quota; a typed case run on the fake vLLM.
- `test_following.py`: a configuration following its model to a new version
- `test_scorers.py`: a scorer of the person's own, with its labels, the runs it applies to and its lints; refusals;
  forks and their labels; following; a scorer refused once a deploy raises its version.
- `test_said.py`: names, descriptions, tags and collaborators; refusals; deleting, listing and finding deleted
  threads, and restoring under the one-expectation rule.
- `test_variation.py`: replacing parts, taking a part back, and only an optional part taken out. Without a database.

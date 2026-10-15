# Bench API

Reference for the `chatddx.bench` package: each name's signature, what it returns and what it raises. What the bench
is and why it is shaped this way is in docs/bench.md. The types it passes through are in docs/catalog-api.md (`Edit`,
`About`, `Subject`, `Kept`), docs/factors-api.md (`Component`, `Registry`, `Skeleton`, `Recipe`, `Trial`, `Case`,
`Scorer`, `Scoring`, `Expectation`, `Finding`, `StructuralError`, `ModelFacts`, `Landing`), docs/ledger-api.md
(`RunStarted`, `Run`, `RunItem`, `ItemKey`, `Call`, `Score`), docs/store-api.md (`Store`, `People`, `Rows`,
`Connection`), docs/inventory-api.md (`Inventory`), docs/facts-api.md (`Facts`, `lints`), docs/identity-api.md
(`Person`, `preferred`, `sees`, `owns`, `collaborates`) and docs/runner-api.md (`Runner`, `Running`, `Grader`,
`Grading`, `Event`, `Refused`, `judge_at`, `Items`).

Paths are relative to `src/chatddx/bench/` unless they start with `src/`, `docs/` or `agents/`.

## Contents
- [Package](#package)
- [Conventions](#conventions)
- [errors.py](#errorspy): `NotFound`, `Ambiguous`, `Conflict`, `MovedOn`, `OverQuota`
- [outcome.py](#outcomepy): `Outcome`, `outcome`, `usage`, `used`
- [variation.py](#variationpy): `PARTS`, `OPTIONAL`, `TriedVariation`
- [model.py](#modelpy): `KINDS` and the other constants, and the values the bench returns
- [seen.py](#seenpy): `Seen`, what the person sees, and the checks the writes share
- [bench.py](#benchpy): `Bench`, the `Seen` with the writes bound
- The writes: [configurations.py](#configurationspy), [components.py](#componentspy), [cases.py](#casespy),
  [taking.py](#takingpy), [saying.py](#sayingpy), [following.py](#followingpy), [runs.py](#runspy)
- [Tests](#tests)

## Package
`chatddx.bench` re-exports `Ambiguous`, `Conflict`, `MovedOn`, `NotFound`, `OverQuota`, `Outcome`, `outcome`, `usage`,
`used`, `OPTIONAL`, `PARTS`, `TriedVariation`, `KINDS`, `WRITTEN`, `Bench`, `Family`, `Graded`, `Proposed`, `Reach`,
`Saved`, `Taken`, `Written`, `ScoreHalt`, `ScorerStarted` and `ScoringEvent`. Edges import from `chatddx.bench`,
never by path; tests import their helpers from `chatddx.bench.test.helpers`.

The modules, and the ones each builds on:
- `errors.py`: `NotFound`, `Ambiguous`, `Conflict`, `OverQuota`, and `MovedOn`, the catalog's.
- `outcome.py`: `Outcome`, `outcome`, `usage`, `used`: how a run's item ended, and the tokens it used.
- `variation.py`: `PARTS`, `OPTIONAL`, `TriedVariation`: the variation being tried, a plain value.
- `model.py`: the constants and the values the bench returns; on `variation.py`.
- `seen.py`: `Seen`; on `errors.py`, `model.py` and `variation.py`.
- `configurations.py`: `save`, `fork`, `edit`, `keep_compilation`; on `errors.py`, `model.py`, `seen.py` and
  `variation.py`.
- `components.py`: `component`, `check`, `new`, `fork_component`, `edit_component`, `bound`, `keep_language`; on
  `errors.py`, `model.py`, `seen.py` and `variation.py`.
- `cases.py`: `appendix`, `case`, `replacement`, `type_case`, `carry`, `appendices_of`, `case_titled`, `case_titles`,
  `WITH`; on `components.py`, `errors.py`, `model.py` and `seen.py`.
- `taking.py`: `take`, `take_from`; on `errors.py`, `model.py` and `seen.py`.
- `saying.py`: `say`; on `errors.py`, `model.py` and `seen.py`.
```
AGENT: replace
`corrected` and `follow_facts`. The item.
---
- `following.py`: `proposal`, `follow`, `corrected`, `follow_facts`; on `components.py`, `errors.py`, `model.py` and
  `seen.py`.
```
- `following.py`: `proposal`, `follow`; on `components.py`, `errors.py`, `model.py` and `seen.py`.
- `runs.py`: `start`, `again`, `score`, `REFUSALS`, `ScorerStarted`, `ScoringEvent`, `ScoreHalt`; on
  `configurations.py`, `errors.py`, `model.py`, `seen.py` and `variation.py`.
- `bench.py`: `Bench`; on `seen.py` and the writes.

Outside the package, the bench builds on the store, the catalog, `chatddx.identity`, the World, the facts, the runner
and the scoring pass, and holds no SQL.

Organisational principles:
- **Modules are named by what they hold**, as `catalog/threads.py` and `runner/send.py` are: what the person sees in
  `seen.py`, each write in the module named for what it writes, as docs/bench.md gives each a section, and `Bench` in
  `bench.py`.
- **`variation.py`, `outcome.py` and `model.py` are pure.** None touches the store or a person, so they are tested
  without a database, and an edge can hold a `TriedVariation` without a bench.
- **`Seen` writes nothing, and each write takes one.** A write reaches another only by importing its module, so the
  imports say which builds on which: `cases.py` on `components.py`, since carrying is an edit and an appendix is bound
  as it is written; `following.py` on `components.py`, for a text's language; `runs.py` on `configurations.py`, for a
  started variation's compilation.
- **`Bench` binds the writes as its own methods**, so an edge calls `bench.*` for everything, and a write's home is
  the module its binding names. No mixins hide where a method lives, and the functions aren't a second surface, since
  edges import from `chatddx.bench` alone.
- **"Seen"**, what the person sees, rather than "view", which a scorer's views are already
  (`chatddx.factors.scoring.View`). The bench writes for the person only through what `Seen` finds.

## Conventions
- **One person, one connection.** `Bench(conn, person, inventory)` keeps them as `conn`, `person` and `inventory`,
  with a `Store`, a `Catalog`, `Rows` and `People` on the connection as `store`, `catalog`, `rows` and `people`. Edges
  read through these what doesn't depend on the person. `start` and `score` need `conn` in autocommit mode.
- **Writes** are functions of the module that holds them, with a `Seen` as their first parameter, which `Bench` binds,
  so an edge calls `bench.take(cases, schema)`. Below, a write's signature is as `Bench` gives it.
- **Caches.** The login of each person id and the model each engine serves are cached for the bench's life; the facts
  aren't, and `facts` reads them from the store each time.
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

## outcome.py

### `type Outcome = Literal["stopped", "errored", "unread", "completed", "invalid", "valid", "salvaged"]`

### `outcome(skeleton: Skeleton, item: RunItem) -> tuple[Outcome, str | None]`
How an item ended, by its last call read through `chatddx.scorers.answer.read`, and why, when there is something to
say. The first that holds:
1. `stopped`: the call's error is the runner's `STOPPED`, or the item's last turn has no call, since its tools ran and
   the request after them was never sent.
2. `errored`, with the call's error, or `unread`, with why the answer couldn't be read: there is no answer.
3. `salvaged`, with what the schema refused, else the call's error: the answer was read from a structured answer cut
   short, its structure closed.
4. `completed`, with the call's error: the skeleton has no `output_schema`.
5. `invalid`, with the call's error, else what the schema refused; or `valid`, with the call's error.

### `usage(item: RunItem) -> tuple[int, int]`
The prompt and completion tokens of all the item's calls, summed.

### `used(call: Call) -> tuple[int, int]`
The prompt and completion tokens of one call, from its response's `usage`; a count that isn't an `int` is 0. Without
`usage`, as a stream cut short ends before it, the completion tokens are the `token_ids` its first choice holds, and
the prompt tokens 0.

## variation.py

### `PARTS: tuple[str, ...]`
`chatddx.factors.request.RECIPE_PARTS`, the recipe's parts in order: the nine chunk parts, `CHUNK_PARTS`, then
`engine`.

### `OPTIONAL: tuple[str, ...]`
The parts `Recipe` doesn't require, which a variation can take out.

### `class TriedVariation`
A frozen dataclass: a configuration, or a variation of it being tried.
- `configuration: Edit`: the configuration's edit.
- `name: str`: the name the person called it by.
- `recipe: Recipe | None = None`: its recipe; `None` for a configuration without a compilation.
- `parts: Mapping[str, tuple[str | None, str]] = {}`: for each part replaced, a chunk's digest, or an engine's for
  `engine`, or `None` for one taken out, and the name it was set by.

#### `label: str` (property)
`name`, then `+PART=NAME` for each replaced part, in `PARTS` order.

#### `held(part: str) -> str | None`
The digest the part holds: the replaced one, `None` when it was taken out; else the recipe's; else `None`.

#### `set(part: str, digest: str | None, name: str) -> TriedVariation`
A copy with `part` set to `digest`, by `name`. Setting a part to the recipe's own digest takes it out of `parts`.
- Raises `ValueError("<name> has no recipe to set its <part> in")` without a recipe.
- Raises `ValueError("a configuration always has a <part>: only <OPTIONAL> can be taken out")`, `an engine` for the
  engine, for `None` and a part not in `OPTIONAL`.

#### `varied: Recipe | None` (property)
The recipe with `parts` replaced over it, validated as a `Recipe`; `None` without a recipe.

## model.py

### Constants
- `KINDS: dict[str, tuple[str, ...]]`: the thread kinds each word names. `configuration` is `skeleton`, each chunk
  part, of `CHUNK_PARTS`, is `chunk.<part>`, `engine` is `engine.local` and `engine.remote`, and `tool`, `scorer`,
  `judge`, `expectation`, `appendix`, `expectation_schema`, `canary_set`, `model` and `facts` are their own kind.
  `PARTS` is `chunk.<part>`, `engine` is `engine.local` and `engine.remote`, and `tool`, `scorer`, `judge`,
  `expectation`, `appendix`, `expectation_schema`, `canary_set` and `model` are their own kind.
- `WRITTEN: frozenset[str]`: the kinds a person writes as components: `chunk.<part>` for each of `CHUNK_PARTS`,
  `expectation`, `appendix`, `scorer` and `judge`.
- `LABELLED: tuple[Part, ...]`: `("view", "resource")`, the parts of a scorer that have labels.
- `COMPILED_LANGUAGE: str`: `"a compiled configuration's language comes from its recipe"`, what `new` and `follow`
  refuse a language with.
- `PLACEHOLDERS: dict[SlotName, str]`: what stands in for each slot of a request rendered to be looked at:
  `‹vignette›`, `‹appendices›`, `‹completion›`, `‹expectation›`.
- `SAVED: dict[Kept, …]`: what `Saved.what` and `Written.what` call each of the catalog's `Kept`: `created`,
  `a new version` for `edited`, and `unchanged`.
- `word_of(kind: str) -> str`: the word in `KINDS` that names `kind`, `configuration` for `skeleton`.

### Values
Frozen dataclasses that `Bench` returns.

#### `class Family`
- `id: int`
- `about: About`
- `case: str`: its default case.
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

#### `class Saved`
- `name: str`
- `digest: str`: the skeleton's.
- `what: Literal["created", "a new version", "unchanged"]`
- `variation: TriedVariation`: the saved configuration, with nothing replaced.

#### `class Proposed`
- `divergence: Divergence`: the catalog's, with the base, the origin's head and what the fork varies.
- `proposal: Recipe | Component`
- `digest: str`: the component's, or the compiled skeleton's.
- `compilation: str | None`: for a recipe.

```
AGENT: add
`Corrected`, what following a configuration's facts would keep. A class before `Written`.
---
#### `class Corrected`
- `behind: Behind`: the catalog's `/facts` entry, with the facts compiled against and the facts thread's head.
- `model: str`: the model the facts are about.
- `digest: str | None`: the skeleton the head's recipe compiles to against the corrected facts.
- `compilation: str | None`: its compilation.
- `refused: str | None`: why the corrected facts refuse what the recipe asks; `digest` and `compilation` are then
  `None`.
```
#### `class Written`
- `edit: Edit`: what was kept.
- `what: Literal["created", "a new version", "unchanged"]`
- `findings: list[Finding]`: `Seen.linted` of its digest.
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

## seen.py

### `class Seen`
`Seen(conn: Connection, person: Person, inventory: Inventory)`: what the person sees, and the checks the writes share.
It writes nothing.

### People

#### `login(person: int | None) -> str`
The person's login, or `nobody` for `None`.
- Raises `People.get`'s `LookupError` for an unknown id.

#### `owner(about: About) -> str`
`""` when it is the person's own, deleted or not, else the owner's `login`.

### Threads

#### `visible(kind: str) -> list[tuple[Edit, About]]`
The heads of `Catalog.heads(kind)` the person `sees`, each with its `About`, in thread id order.

#### `threads(word: str) -> list[tuple[Edit, About]]`
`visible(kind)` for each kind `KINDS[word]` names, in that order.

#### `names(word: str) -> list[str]`
The names of `threads(word)`, sorted, without repeats.

#### `thread(word: str, name: str) -> tuple[Edit, str]`
The head of the thread `name` names among `threads(word)`, and the name that found it.
- `name`: a thread's name, or `<owner's login>/NAME`. A name nothing goes by is read as its one variant,
  `NAME (LANGUAGE)` (`chatddx.catalog.variants_for`), in the language the name ends in, as `NAME LANGUAGE` or
  `NAME (LANGUAGE)`, if any.

Of the threads called `name`, the person's own are taken when they own any, else all of them; when none is called
`name`, the same among those whose qualified name it is. Raises:
- `Ambiguous("<word> '<name>' is made in more than one language: <names>; name one as '<base> <language>' or …")`
- `Ambiguous("<word> '<name>' names a <kind> and a <kind>")`, for a name held in two of the word's kinds.
- `Ambiguous("<word> '<name>' names <n>; name one as OWNER/NAME")`
- `NotFound("no <word> '<name>' for <login>")`

#### `thread_by_id(id: int, word: str | None = None, *, deleted: bool = False) -> tuple[Edit, About]`
The head of thread `id`, and its `About`, when the person sees it.
- `word`: only a thread of a kind `KINDS[word]` names.
- `deleted`: also the person's own deleted thread.

Raises `NotFound("no <word or 'thread'> <id> for <login>")`.

#### `deleted(kind: str) -> list[tuple[Edit, About]]`
The heads of `Catalog.heads(kind)` that are deleted and the person's own, each with its `About`, in thread id order.

#### `about(thread: int) -> About`
`Catalog.about` of the thread.

#### `holder(word: str, digest: str, recipe: Recipe | None = None) -> tuple[Edit, About] | None`
The first of `threads(word)` whose head is `digest`, with `recipe` when it is given, of the person's own if any;
`None` when none is.

#### `worded(thread: int) -> tuple[Edit, About, str]`
`thread_by_id(thread, <word>)` and the word, where `<word>` is the word in `KINDS` for the thread's kind, else
`thread`.

### Components and the World

#### `get(digest: str) -> Component`
`Store.get`.

#### `title(digest: str | None) -> str`
`Catalog.title_of`, or `—` for `None`.

#### `model(engine: str) -> str | None`
The model the engine serves, as the facts name it (`chatddx.factors.facts.model_name`): a local engine's model's
repository, a remote engine's model.

#### `facts: Facts` (property)
The facts about each model, from the store: the head of every live `facts` thread, whoever owns it, through
`Facts.of`, so that of two about one model the later edit wins. Read each time, so that a fact corrected while the
bench lasts is used.

#### `facts_for(engine: str) -> ModelFacts | None`
The `facts` about the model the engine serves, or `None` for a model they don't know.

#### `served(engine: str) -> str`
The engine's `served_model_name`, the model a request to it carries.
- Raises `StructuralError("<digest> is a <kind>, not an engine")`.

#### `endpoint(name: str) -> str`
The digest of the engine the World's endpoint serves.
- Raises the inventory's `LookupError` for an unknown endpoint.
- Raises `NotFound("endpoint '<name>' serves engine <short>, which isn't in the store: load its World with
  init-data")`.

### Families and expectations

#### `families(tags: Iterable[str] = ()) -> list[Family]`
The families the person sees that have a case, by name. A family's case is the bare case of its current vignette when
it is stored, else the first stored case of that vignette.
- `tags`: only those with any of them.

#### `family(name: str) -> Family`
The one of `families()` that `name` names, found as `thread` finds a thread by name, with `case` as the word.

#### `family_by_id(id: int) -> Family`
Family `id`, when the person sees it and it has a case.
- Raises `NotFound("no case <id> for <login>")`.

#### `tags() -> list[str]`
The tags of the families the person sees, sorted, without repeats.

#### `current(family: int) -> Vignette`
The vignette of `family`'s latest binding.

#### `cases(family: int) -> list[str]`
The stored cases of `family`'s current vignette, the bare one first, then by digest.
- Raises `family_by_id`'s `NotFound`.

#### `expectation_schemas(case: str) -> list[str]`
The schemas of the expectations of `case` the person sees, shared ones included, sorted, without repeats.

#### `expectation_choices(cases: Sequence[str], schema: str) -> dict[str, dict[int, str]]`
For each case, the threads of `Catalog.expecting(cases, schema)` the person `owns`, each with its head digest; `{}` for
none. What `expectation` and `scoring` pick from. It refuses nothing.

#### `expectation(case: str, schema: str) -> Expectation | None`
The person's own expectation of `case` under `schema`: `picked` of `expectation_choices`, or `None`.
- Raises `Ambiguous("case <case> has expectations to choose from, in threads <t1>, <t2>, …")`.

#### `shared(case: str, schema: str) -> list[tuple[Edit, About]]`
The heads of `Catalog.expecting([case], schema)` the person `collaborates` on, each with its `About`, in thread id
order: what they could take.

### The variation being tried

#### `configuration(name: str) -> TriedVariation`
The configuration `thread("configuration", name)` finds, with nothing replaced, named without the person's own
`<login>/`.

#### `chunk(part: str, name: str) -> str`
The digest of the head `thread(part, name)` finds.

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

#### `at(variation: TriedVariation, endpoint: str | None) -> tuple[str, str]`
Where the variation runs: the endpoint's name and the engine's digest. For a configuration with a recipe, its engine,
at `endpoint`, or without one at the one endpoint serving it (`Inventory.serving`); for one without, `endpoint` and
the engine it serves (`endpoint(name)`). Raises:
- `ValueError("<label> names no engine: name the endpoint to send it to")`, for a configuration without a recipe and
  no `endpoint`.
- `ValueError("no endpoint serves engine <title>")`, and `ValueError("<names> serve engine <title>; name the one to
  use")`, without `endpoint`: `Inventory.serving`'s.
- `ValueError("endpoint '<endpoint>' serves another engine than <label>'s, <title>")`
- `endpoint(name)`'s.

#### `skeleton(variation: TriedVariation) -> Skeleton`
The configuration's head when nothing is replaced or it has no recipe; else the varied recipe compiled against
`facts_for` its engine.
- Raises the compiler's errors, the facts' refusals among them (`StructuralError`).

#### `landed(variation: TriedVariation) -> dict[str, Landing]`
Where the varied recipe's intents land, by part: `reasoning` for a reasoning level, `sampling` for a recommended
sampling, each the level the engine's model is asked for, with `nearest`, why, when the facts land it on its nearest
(`chatddx.factors.request.landings`). Against the facts its compilation names when nothing is replaced, else
`facts_for` its engine. `{}` without a recipe; no key for a part that holds no intent.
- Raises `landings`' `StructuralError` for what the facts refuse.

#### `request(variation: TriedVariation, engine: str | None, seed: int) -> dict[str, JsonValue]`
The request rendered from the skeleton with `PLACEHOLDERS` for its slots and `seed`.
- `engine`: whose `served` model the request carries; `‹model›` without one.

#### `trial(skeleton: Skeleton, engine: str, cases: list[str], seeds: Sequence[int], cleanup: tuple[CleanupOp, ...] = ()) -> tuple[Registry, Trial]`
A `Trial` of the skeleton, the engine, the cases, the cleanup steps and the seeds, and a registry holding it with
what it refers to.

#### `findings(variation: TriedVariation, engine: str, seed: int, families: list[Family] | None = None) -> list[Finding]`
`lints` of the variation's trial on `engine`; for a judge configuration, of a `Judge` of its skeleton on `engine`,
whatever `families`.
- `families`: the cases to lint over, each in its family's language, the skeleton in its recipe's; `[]` for none.
  Without them, the first case of the families the person sees, and `[]` when there is none.

#### `purposed(found: Iterable[tuple[Edit, About]], purpose: Purpose) -> list[tuple[Edit, About]]`
The configurations of `found` whose skeleton has `purpose`, `generation` or `judge`.

#### `answering(found: Iterable[tuple[Edit, About]], title: str) -> list[tuple[Edit, About]]`
The configurations of `found` whose answer's JSON Schema is titled `title`.

#### `scorers() -> list[tuple[Edit, About, Scorer]]`
`threads("scorer")`, each with its scorer, by the thread's name, else its title.

#### `labels(scorer: str) -> dict[int, str]`
What a scorer digest's views are called for the person: `labels_of` the head `holder("scorer", scorer)` gives, else
of the latest edit that held it in a scorer thread they see, their own first; `{}` when none did.

#### `labels_of(edit: Edit) -> dict[int, str]`
The view labels the edit of a scorer thread was written with, by position.

#### `reach(variation: TriedVariation, families: list[Family]) -> list[Reach]`
A `Reach` for each view of each of `scorers()`, over `families`; `[]` for a judge configuration. A view is `offered`
when it reaches the skeleton's `output_schema`, or, for a view of the whole answer, when there is none. A view not
offered has no `missing` and no `choosing`.

### Runs and scores
The run's trial, skeleton and scorers are resolved through `Store.get`, which raises `StructuralError` for one that
isn't stored or is of another kind.

#### `runs() -> list[RunStarted]`
The live runs the person owns, newest first. A collaborator on a run doesn't see it.

#### `run(prefix: str | None = None) -> RunStarted`
The latest of `runs()`, or the one whose id, as `str(UUID)`, starts with `prefix`.
- Raises `NotFound("<login> has no runs")`.
- Raises `NotFound("no run of yours starts with '<prefix>'")`.
- Raises `Ambiguous("<n> runs of yours start with '<prefix>'")`.

#### `run_by_id(run: UUID) -> RunStarted`
The run, when it has started and the person owns it, live.
- Raises `NotFound("no run <id> of yours")`.

#### `ran(run: UUID) -> tuple[Edit, dict[str, str | None]] | None`
What the run says it varied: the configuration's edit, and each part replaced over it, its chunk's digest or `None`
for a part taken out (`About.varied`, `About.replaced`); `None` for a run that says nothing, as one the runner
started from a trial alone.

#### `reaching(digest: str) -> list[RunStarted]`
The runs of `runs()` whose trial holds `digest` in its closure, or whose skeleton was compiled from a recipe that
does, newest first.

#### `described(run: RunStarted) -> str`
`<run's name, else skeleton's title> × <endpoint, else engine's title> × <case's title, else "<n> cases"> (seed
<seeds>)`.

#### `scorers_for(run: RunStarted) -> list[tuple[Edit, About]]`
The threads of `threads("scorer")` whose scorer applies to the run: the run's skeleton offers each of its views, as
`reach` has it, and the World lets each of its judges score the trial's cases (`chatddx.runner.score.judge_at`).

#### `scoring(run: RunStarted, scorer: str) -> Scoring | None`
The scoring the run would be scored under now: for each of the trial's cases in order, `picked` of
`expectation_choices` under the scorer's expectation schema, cases without one left out. `None` when no case has one.
Nothing is stored.
- Raises `Ambiguous` when a case has several to choose from.

#### `unscored(run: RunStarted) -> list[str]`
The scorers of `scorers_for(run)` without a whole score of the run under `scoring(run, scorer)`, and those whose
`scoring` raises `Ambiguous`. A score is whole when it has finished, holds an item for each of the run's items and
each of the scorer's views, and no judge call of it was stopped.

#### `outstanding() -> list[tuple[RunStarted, list[str]]]`
Each finished run of `runs()`, newest first, with its `unscored`, when there are any.

#### `scores_of(run: UUID, every: bool = False) -> list[Graded]`
The latest score of the run under each scorer that scored it, by `scorer_name`.
- `every`: every score of the run, newest first.

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

### Checks the writes share

#### `compiled(recipe: Recipe) -> tuple[Registry, Compilation]`
The recipe compiled by the running code against `facts_for` its engine, in a registry with what it refers to and
those facts, which the compilation names. Nothing is stored.

```
AGENT: replace
A trial's or judge's skeleton's compilations go beside it, for `trial.engine_unmatched` and `judge.engine_unmatched`. The entry, and `add_compilations` after it.
---
#### `linted(digest: str) -> list[Finding]`
`lints` of the stored component, with `Catalog.language_of` for languages; a trial or a judge with its skeleton's
compilations (`add_compilations`).

#### `add_compilations(registry: Registry, skeleton: str) -> None`
Adds each stored compilation of `skeleton`, and the facts it names, to `registry`, where the factors' lint reads them.
`findings` adds them for a configuration with no recipe; one with a recipe pairs its own engine, so has none to
check. `components.py:check` adds them for a judge.
```
#### `linted(digest: str) -> list[Finding]`
`lints` of the stored component, with `Catalog.language_of` for languages.

#### `check_kind(thread: int, word: str, component: Component) -> None`
- Raises `ValueError("<word> <thread> holds <kind> components, not <kind>")`.

#### `check_expecting(expectation: Expectation, thread: int | None, then: str = "edit that one") -> None`
- Raises `ValueError("<login> has their own expectation of <case's title> under <schema's title>, in thread <t>:
  <then>")` when the person owns an expectation thread of its case and schema other than `thread`.

#### `check_scorer(scorer: Scorer) -> None`
- Raises `ValueError` with `chatddx.scorers.shipped.problems` joined by `; `, for a scorer the running code could
  never score with.

## bench.py

### `class Bench(Seen)`
`@final`. The `Seen`, with each write bound as a method of the same name: `save`, `fork` and `edit` from
`configurations.py`; `component` (a static method), `check`, `new`, `fork_component` and `edit_component` from
`components.py`; `appendix`, `case`, `replacement`, `type_case`, `carry`, `appendices_of`, `case_titled` and
`case_titles` from `cases.py`; `take` and `take_from` from `taking.py`; `say` from `saying.py`; `proposal` and
`follow` from `following.py`; and `start`, `again` and `score` from `runs.py`.

## configurations.py
`fork`, `edit` and `save` write the skeleton's edit through `Catalog.keep`, in one transaction, and, for a variation
with parts replaced, the compilation of its skeleton by the running code, as the edit's compilation; otherwise the edit
keeps the configuration's.

### `save(variation: TriedVariation, name: str) -> Saved`
`edit` of the person's one live configuration named `name`, on its head, else `fork`.
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

### `keep_compilation(variation: TriedVariation) -> str | None`
For a variation with parts replaced, the compilation of its skeleton by the running code, stored; its digest. `None`
otherwise.

## components.py
`new`, `fork_component` and `edit_component` write, in one transaction, the component with its references, which must
be stored; its language, through `keep_language`; and its edit through `Catalog.keep`. An appendix is `bound` first;
an appendix's edit also stores, as `Written.cases`, each case that held the old version at the same vignette, with the
new version in its place. They raise, and leave nothing written:
- `ValueError("a person doesn't write <kind> components")` for a kind not in `WRITTEN`.
- `ValueError("<kind> components have no language of their own")`
- `ValueError("only a scorer's views and resources have labels")`
- `bound`'s, `Seen.check_scorer`'s and `Seen.check_expecting`'s.
- `StructuralError("not in the store: […]")` for references that aren't stored.
- `keep_language`'s, and `Catalog.keep`'s, its label checks among them.

### `component(doc: Mapping[str, JsonValue]) -> Component`
Takes no `Seen`. The component `doc` holds, as `GET /api/components` gives its body: of the model its `kind` names,
with `v`, when given, its schema version.

Raises:
- `ValueError("<kind!r> isn't a kind a person writes: the kinds are …")`
- `ValueError("<kind> is at v<n>, not v<v>")`
- the model's `ValidationError`.

### `check(component: Component) -> Checked`
The component as a write would store it, with its lints. Nothing is written.
- Raises `ValueError("a person doesn't write <kind> components")`, the registry check's `StructuralError`, and
  `bound`'s and `Seen.check_scorer`'s.

### `new(component: Component | Recipe, name: str, language: str | None = None, labels: Labels | None = None) -> Written`
`component` as a new thread of the person's own named `name`.
- `component`: a `Recipe` is compiled by the running code and kept as a configuration.
- `labels`: a scorer's view and resource labels.

For a recipe, raises:
- `ValueError(COMPILED_LANGUAGE)` for a language.
- `ValueError("only a scorer's views and resources have labels")` for labels.
- `ValueError("<digest> isn't a stored chunk of <part>")`, or `ValueError("<digest> isn't a stored engine")` for
  `engine`.
- the compiler's errors, the facts' refusals among them (`Seen.compiled`).

### `fork_component(thread: int, name: str, component: Component | None = None, language: str | None = None, labels: Labels | None = None) -> Written`
A new thread of the person's own named `name`, forked from the head of `thread`, holding `component`, else the head. A
scorer forked as it is, without labels, keeps the head's.
- Raises `thread_by_id`'s `NotFound("no <word> <thread> for <login>")`, and `Seen.check_kind`'s.

### `edit_component(thread: int, head: int, component: Component, language: str | None = None, labels: Labels | None = None) -> Written`
`component` as a new version of `thread`; `unchanged` when it is the head already and, for a scorer given labels,
they are the head's. A scorer edited without labels keeps none, unless it is the head's, which is then `unchanged`.

Raises:
- `thread_by_id`'s `NotFound`.
- `NotFound("no <word> <thread> of yours")` for a thread the person sees but doesn't own.
- `Seen.check_kind`'s.
- `MovedOn` when the head isn't `head`.

### `bound(appendix: Appendix) -> Appendix`
The appendix with its line endings LF.
- Raises `ValueError("an appendix is bound to the current vignette of a case you see")`.

### `keep_language(digest: str, language: str) -> None`
The language written for `digest` when it has none; nothing when it has the same.
- Raises `ValueError("<title> is in <language> already: a text's language is the same wherever it is held")`.

## cases.py

### `appendix(family: int, text: str) -> Appendix`
An appendix of `text`, `bound` to the current vignette of `family`. Nothing is stored.
- Raises `family_by_id`'s `NotFound`.

### `case(family: int, appendices: Sequence[str]) -> str`
The digest of a `Case` of `family`'s current vignette with `appendices`, in order, stored. Nothing is written in the
catalog.
- Raises `NotFound("no appendix <digest> for <login>")` for an appendix no thread the person sees holds.
- Raises the store's check for an appendix of another vignette.

### `replacement(case: str) -> str`
The digest of `case`, left at an earlier vignette of its family, rebound to the current one and stored with its
rebound appendices.
- Raises `NotFound("no case <case> for <login>")`.
- Raises `ValueError("<case> is at its family's current vignette already")`.

### `type_case(text: str, *, name: str | None = None, language: str | None = None, source: str | None = None) -> Family`
The family of a case the person typed: the text kept in a database source, its case stored, and its family adopted by
id alone, owned by the person, in one transaction.
- `name`, `language`: entries about the family.
- `source`: the database source to keep it in; the World's one when not given.

Raises, before writing:
- `ValueError("a typed case holds text")`
- `ValueError("a typed case may not hold U+0000, which can't be stored")`
- `ValueError("a typed case holds at most <TYPED_TEXT_LIMIT> characters, not <n>")`
- `ValueError("a name can't be empty: none leaves the case unnamed")`
- `language_tag`'s `ValueError`.
- `ValueError("'<source>' isn't a database source of the World's")`
- `ValueError("the World has no database source to type cases into")`
- `ValueError("name the source to type into: …")`
- `OverQuota("<login> has typed <n> cases in the last day, as many as a day takes")`

### `takes_typed(endpoint: str) -> bool`
Whether a case typed into the World's database source can run at `endpoint`: the source isn't sensitive, or the
endpoint is cleared for it. False when the World has no database source, or more than one.

### `carry(thread: int, head: int, case: str) -> Written`
`edit_component` of the expectation `thread` onto `case`, with the same schema and data.
- Raises `ValueError("<word> <thread> isn't an expectation")`.
- Raises `ValueError("<case> isn't a case of the family <old case> is of")`.

### Finding cases by their titles
For an edge that names cases as a person reads them, `FAMILY with APPENDIX, …`, as
`chatddx.catalog.titles.describe_case` writes them (`WITH`).

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

```
AGENT: add
`corrected` and `follow_facts`. Two entries at the end of following.py.
---
### `corrected(thread: int) -> Corrected | None`
What following the facts of `thread`, a configuration the person sees, would keep: its head's recipe compiled by
`Seen.compiled`, against the facts as they are stored now. `None` when the head has no compilation, or the catalog's
`behind` names no `/facts`. Nothing is stored.
- Raises `thread_by_id`'s `NotFound`.

### `follow_facts(thread: int, head: int) -> Written`
The head's recipe, compiled against the corrected facts, kept as a new version of `thread` with its compilation;
`what` is `a new version`, and the findings are `linted`'s of the skeleton. Its base doesn't change.

Raises:
- `thread_by_id`'s `NotFound`.
- `NotFound("no configuration <thread> of yours")`
- `ValueError("configuration <thread> has no corrected facts to follow")`
- `ValueError("configuration <thread> can't follow the facts about <model>: <why>")`
- `MovedOn`
```
## runs.py

### `REFUSALS`
`(LookupError, TypeError, ValueError, NotImplementedError, Refused)`: what `score` takes as a scorer refused.

### `start(variation: TriedVariation, endpoint: str | None, cases: list[str], seeds: Sequence[int], cleanup: Sequence[CleanupOp] | None = None, execution: Execution | None = None, canaries: str | None = None) -> Running`

The variation run where `Seen.at(variation, endpoint)` says, over `cases` with `seeds`, its replicates, its cleanup
steps, its execution and the canary set stored under the digest `canaries`. Once the run has started, its `name`
entry, `variation.label`, its `varied` entry, `variation.configuration`, and a `replaced` entry for each part
replaced, the engine among them, are written in one transaction (docs/catalog-api.md, "Entry"). Not given: the steps
the cases' sources ask for, in `CleanupOp`'s order (`()` for none); the endpoint's execution and canary set, from the
inventory. The compilation of a varied skeleton is stored once the run has started.

Raises:
- `ValueError("<label> is a judge configuration: a judge is asked as runs are scored, and isn't run on cases")`
- `OverQuota("a run holds at most <ITEMS_PER_RUN> items, not <n>")`, the cases times the seeds
- `OverQuota("<login> has started <n> runs in the last day, as many as a day takes")`
- `Seen.at`'s, `resolve`'s for `canaries`, the runner's and its gate's; the runner's `ValueError` for a
  connection not in autocommit mode.

### `again(run: RunStarted, seeds: Sequence[int]) -> Running`
The run's trial run again at its endpoint with `seeds`, its engine, cleanup, execution and canary set kept, as `start`
runs a variation, named by the run's name, else its skeleton's title, and saying what the run said it varied. The gate
refuses an endpoint that serves another engine now (`Refused("endpoint '<name>' serves engine <digest>, the trial's
is <digest>")`).

### `resume(run: UUID) -> Running`
A run of the person's own resumed by the runner (docs/runner-api.md, `Runner.resume`); another's is `NotFound`, as
`run_by_id` has it.

### `score(run: RunStarted, scorers: Collection[str] | None = None, on_event: Callable[[ScoringEvent], None] | None = None, halt: ScoreHalt | None = None) -> list[Graded]`
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

### `type ScoringEvent = Event | ScorerStarted`
`Event` is `chatddx.runner.score.Event`.

### `class ScoreHalt`
A halt for `score` that another thread sets.
- `set() -> None`
- `is_set() -> bool`
- `watching(grading: Grading)`: a context manager under which `set` halts that `Grading`, at once if it was set
  already.

## Tests
In `src/chatddx/bench/test/`. The repl's and the API's tests reach the bench too, through their own fixtures over the
same test World.
- `conftest.py`: `template` is `curated`, the test World as init-data lands it, with alice's giftbag, copied for each
  test; `autocommit` is on; `alice` is the test World's person, `bob` a new one with nothing; `bench` is alice's, on
  the test World's inventory.
- `helpers.py`: `SOURCE`, the test World's vignette source; `trial(conn, plan, recipe, *ids)`, a stored trial of one
  of its recipes on `QWEN`, seed 7, over its cases of those vignette ids; `ran(conn, by, made, finished=True)`, a run
  of it recorded without sending; `another_expectation(bench, case, data)`, a second expectation of the person's own
  for the case, left by two writers at once.
```
AGENT: replace
A hand-written configuration on another model. The item.
---
- `test_seen.py`: what a person sees, by name, `OWNER/NAME` and id; variations; runs and what reaches a digest; what is
  left to score; the expectation a case is held to, and several to choose from; scorers that apply, judged or not;
  a run's scores; judge configurations; a swapped engine keeping every other pick, where its intents land, on their
  nearest or not, and a level its model refuses; a hand-written configuration on another model than its skeleton is
  worked out for; names per language; saving, forking and editing; taking.
```
- `test_seen.py`: what a person sees, by name, `OWNER/NAME` and id; variations; runs and what reaches a digest; what is
  left to score; the expectation a case is held to, and several to choose from; scorers that apply, judged or not;
  a run's scores; judge configurations; a swapped engine keeping every other pick, where its intents land, on their
  nearest or not, and a level its model refuses; names per language; saving, forking and editing; taking.
- `test_runs.py`: a run's seeds, cleanup, execution and canaries, kept when it runs again; what it varied; a run at
  the endpoint serving its engine, or one named, refused for an endpoint serving another engine and for an engine two
  endpoints serve; its items, cases times seeds; resuming one's own; the sources' cleanup and the endpoint's canaries
  and execution.
```
AGENT: replace
The judge on another model. The item.
---
- `test_writes.py`: configurations from recipes; chunks and expectations, new, edited and forked, with their
  languages; what is refused; an expectation's lints and the one-expectation rule; judges, and a judge on another model
  than its skeleton is worked out for.
```
- `test_writes.py`: configurations from recipes; chunks and expectations, new, edited and forked, with their
  languages; what is refused; an expectation's lints and the one-expectation rule; judges.
- `test_cases.py`: appendices, cases of them, and an appendix's edit storing a replacement; carrying an expectation;
  refusals; a late case's replacement after a repair; cases found by title.
- `test_typed.py`: a typed case with its family, name and language; the same text typed twice; refusals and the day's
  quota; a typed case run on the fake vLLM.
```
AGENT: replace
Following facts. The item.
---
- `test_following.py`: a configuration and a taken expectation following the archive; nothing to follow, another's
  thread, a head that moved on, a language for a compiled configuration, and an origin no longer shared; a
  configuration following its corrected facts, a correction that doesn't reach it, and one that refuses it.
```
- `test_following.py`: a configuration and a taken expectation following the archive; nothing to follow, another's
  thread, a head that moved on, a language for a compiled configuration, and an origin no longer shared.
- `test_scorers.py`: a scorer of the person's own, with its labels, the runs it applies to and its lints; refusals;
  forks and their labels; following; a scorer refused once a deploy raises its version.
- `test_said.py`: names, descriptions, tags and collaborators; refusals; deleting, listing and finding deleted
  threads, and restoring under the one-expectation rule.
- `test_variation.py`: replacing parts, taking a part back, and only an optional part taken out. Without a database.
- `test_outcome.py`: each outcome but `salvaged`, which `src/chatddx/repl/test/test_running.py` reads, and usage.
  Without a database.

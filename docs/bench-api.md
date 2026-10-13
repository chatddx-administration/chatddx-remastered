# Bench API

Reference for the `chatddx.bench` package. It was written from `src/chatddx/bench/*` and docs/bench.md. What the bench
is and why it is shaped this way is in docs/bench.md; this file says what each name accepts, returns and raises. The
types it passes through are in docs/catalog-api.md (`Edit`, `About`, `Subject`, `Kept`), docs/factors-api.md
(`Component`, `Registry`, `Skeleton`, `Recipe`, `Trial`, `Case`, `Scorer`, `Scoring`, `Expectation`, `Finding`,
`StructuralError`), docs/ledger-api.md (`RunStarted`, `Run`, `RunItem`, `ItemKey`, `Call`, `Score`), docs/store-api.md
(`Store`, `People`, `Rows`, `Connection`), docs/inventory-api.md (`Inventory`), docs/facts-api.md (`Facts`, `lints`),
agents/wip-identity.md (`Person`, `preferred`) and docs/runner-api.md (`Runner`, `Running`, `Grader`, `Grading`,
`Event`, `Refused`, `judge_at`, `Items`).

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

| Module | Holds | Builds on |
| --- | --- | --- |
| `errors.py` | `NotFound`, `Ambiguous`, `Conflict`, `OverQuota`; `MovedOn`, the catalog's | `chatddx.catalog` |
| `outcome.py` | `Outcome`, `outcome`, `usage`, `used`: how a run's item ended, and the tokens it and each call used | `chatddx.factors.request`, `chatddx.ledger`, `chatddx.runner.send`, `chatddx.scorers.answer` |
| `variation.py` | `PARTS`, `OPTIONAL`, `TriedVariation`: the variation being tried, a plain value | `chatddx.catalog`, `chatddx.factors.request` |
| `model.py` | `KINDS`, `WRITTEN`, `LABELLED`, `COMPILED_LANGUAGE`, `PLACEHOLDERS`, `SAVED`; `Family`, `Reach`, `Graded`, `Saved`, `Proposed`, `Taken`, `Written` | `variation.py`, `chatddx.catalog`, `chatddx.factors.{base,request,scoring}`, `chatddx.ledger` |
| `seen.py` | `Seen`: what the person sees, and the checks the writes share | `errors.py`, `model.py`, `variation.py`, `chatddx.catalog` (and its `threads` and `titles`), `chatddx.core.rig`, `chatddx.factors.{base,bundle,cases,engine,request,scoring,trial}`, `chatddx.facts`, `chatddx.identity`, `chatddx.inventory`, `chatddx.ledger`, `chatddx.runner.{gate,prepare,score,send}`, `chatddx.scorers.shipped`, `chatddx.store` |
| `configurations.py` | `save`, `fork`, `edit`, `keep_compilation` | `errors.py`, `model.py`, `seen.py`, `variation.py` |
| `components.py` | `component`, `new`, `fork_component`, `edit_component`, `bound`, `keep_language` | `errors.py`, `model.py`, `seen.py`, `variation.py`, `chatddx.catalog`, `chatddx.factors.{base,cases,kinds,request,scoring}` |
| `cases.py` | `appendix`, `case`, `replacement`, `type_case`, `carry`, `appendices_of`, `case_titled`, `case_titles`, `WITH` | `components.py`, `errors.py`, `model.py`, `seen.py`, `chatddx.catalog` (and its `families`), `chatddx.core.settings`, `chatddx.factors.{base,bundle,cases,scoring}`, `chatddx.inventory`, `chatddx.store.Texts` |
| `taking.py` | `take`, `take_from` | `errors.py`, `model.py`, `seen.py`, `chatddx.catalog`, `chatddx.factors.{base,scoring}` |
| `saying.py` | `say` | `errors.py`, `model.py`, `seen.py`, `chatddx.catalog`, `chatddx.factors.scoring` |
| `following.py` | `proposal`, `follow` | `components.py`, `errors.py`, `model.py`, `seen.py`, `chatddx.catalog`, `chatddx.factors.{bundle,request,scoring}` |
| `runs.py` | `start`, `score`, `REFUSALS`, `ScorerStarted`, `ScoringEvent`, `ScoreHalt` | `configurations.py`, `model.py`, `seen.py`, `variation.py`, `chatddx.factors.{base,scoring}`, `chatddx.ledger`, `chatddx.runner.{gate,run,score,send}` |
| `bench.py` | `Bench` | `seen.py` and the writes |

Why it is laid out so:
- **Modules are named by what they hold**, as `catalog/threads.py` and `runner/send.py` are: what the person sees in
  `seen.py`, each write in the module named for what it writes, as docs/bench.md gives each a section, and `Bench` in
  `bench.py`.
- **`variation.py`, `outcome.py` and `model.py` are pure.** None touches the store or a person, so they are tested
  without a database, and an edge can hold a `TriedVariation` without a bench.
- **`Seen` writes nothing, and each write takes one.** A write reaches another only by importing its module, so the
  imports say which builds on which: `cases.py` on `components.py`, since carrying is an edit and an appendix is bound
  as it is written; `following.py` on `components.py`, for a text's language; `runs.py` on `configurations.py`, for a
  started variation's compilation. The other writes build on the `Seen` alone.
- **`Bench` binds the writes as its own methods**, so an edge calls `bench.*` for everything, and a write's home is
  the module its binding names. It is the store's `Catalog` over `chatddx.catalog`'s functions without the passing
  through: no mixins hide where a method lives, and the functions aren't a second surface, since edges import from
  `chatddx.bench` alone.
- **"Seen"**, what the person sees, rather than "view", which a scorer's views are already
  (`chatddx.factors.scoring.View`). The bench writes for the person only through what `Seen` finds.

## Conventions

**One person, one connection.** `Bench(conn, person, inventory, facts)`, the `Seen`'s, keeps them as `conn`, `person`,
`inventory` and `facts`, with a `Store`, a `Catalog`, `Rows` and `People` on the connection as `store`, `catalog`,
`rows` and `people`. Edges read through these what doesn't depend on the person. `start` and `score` need `conn` in
autocommit mode: `start` raises the runner's `ValueError` otherwise, and `score` gives each scorer refused with the
scoring pass's.

**Writes.** Each write is a function of the module that holds it, with a `Seen` as its first parameter, which
`Bench` binds, so an edge calls `bench.take(cases, schema)`. Below, a write's signature is as `Bench` gives it.

**Caches.** The login of each person id and the model each engine serves are cached for the bench's life.

**Words.** A method that takes `word` takes a key of `KINDS`; another raises `KeyError`.

**What the person sees.** A thread or family the person sees is one whose `About.shows(person.id)`: live, and owned
or shared. Their own is `About.owned_by(person.id)`: live, and owned. Of several the person sees, their own are
taken when they own any, else all of them (`chatddx.identity.preferred`).

**Errors.** `NotFound` and `Ambiguous`, both `LookupError`s, are raised for what the person sees or names. A refused
variation is a `ValueError`, and so are `Conflict`, a write the person must say they want, `MovedOn`, an edit made on a
head that moved on, and `OverQuota`, more than a day takes. `StructuralError`, a `ValueError`, comes from `Store.get`
and `resolve` when a digest isn't stored or is of another kind. The errors of the catalog, the inventory, the runner
and its gate pass through unless an entry says otherwise. Messages name the person by login and the thing by the word
for it, for a person to read; nothing in the bench is UI.

## errors.py

### `class NotFound(LookupError)`
`NotFound(message: str, per_model: Iterable[str] = ())`. Nothing the person sees goes by that name or id. `per_model`,
a `tuple[str, ...]`, holds the names of the threads made per model under the name, when no model was given to pick
one by.

### `class Ambiguous(LookupError)`
More than one thing the person sees goes by that name or id, or a case has several expectations of theirs to choose
from.

### `MovedOn`
`chatddx.catalog.MovedOn`, a `ValueError`, re-exported: an edit named a head that isn't the thread's head any more
(`chatddx.catalog.threads.check_head`).

### `class OverQuota(ValueError)`
The person has written as much of something as a day takes: typed cases (`chatddx.core.settings.TYPED_PER_DAY`).

### `class Conflict(ValueError)`
The write would undo what the person has unless they say so: taking an expectation when they own one of its case under
its schema, without replacing it.

## outcome.py

### `type Outcome = Literal["stopped", "errored", "unread", "completed", "invalid", "valid", "salvaged"]`

### `outcome(skeleton: Skeleton, item: RunItem) -> tuple[Outcome, str | None]`
How an item ended, by its last call, read through `chatddx.scorers.answer.read`, and why when there is something to
say:
1. `"stopped"`, `None`, when the call's error is the runner's `STOPPED`, or when the item's last turn has no call: its
   tools ran, and the request after them was never sent;
2. without an answer: `"errored"` with the call's error, else `"unread"` with why the answer couldn't be read;
3. with one read from a structured answer cut short, its structure closed (`Answer.salvaged`): `"salvaged"`, with what
   the schema refused, or else the call's error;
4. with another: `"completed"`, with the call's error, when the skeleton has no `output_schema`;
5. else `"invalid"`, with the call's error or else what the schema refused, or `"valid"`, with the call's error.

### `usage(item: RunItem) -> tuple[int, int]`
The prompt and completion tokens of all the item's calls, each as `used` gives them, summed.

### `used(call: Call) -> tuple[int, int]`
The prompt and completion tokens of one call, from its response's `usage`. A count that isn't an `int` is 0. A
response without `usage`, as a stream cut short ends before it, gives the completion's `token_ids` its first choice
holds, and no prompt tokens.

## variation.py

### `PARTS: tuple[str, ...]` and `OPTIONAL: tuple[str, ...]`
`PARTS` is `chatddx.factors.request.RECIPE_PARTS`, the recipe's parts in order. `OPTIONAL` is those `Recipe` doesn't
require, the parts a variation can take out.

### `class TriedVariation`
A frozen dataclass: a configuration, or a variation of it being tried.

| Field | Type | Default |
| --- | --- | --- |
| `configuration` | `Edit` | the configuration's head edit |
| `name` | `str` | the name the person called it by |
| `recipe` | `Recipe \| None` | `None`, for a configuration without a compilation |
| `parts` | `Mapping[str, tuple[str \| None, str]]` | empty: for each part replaced, a chunk's digest or `None` for one taken out, and the name it was set by |

| Member | Description |
| --- | --- |
| `label: str` (property) | `name`, then `+PART=NAME` for each replaced part, in `PARTS` order. |
| `held(part: str) -> str \| None` | The digest the part holds: the replaced one, `None` when it was taken out; else the recipe's; else `None`. |
| `set(part: str, digest: str \| None, name: str) -> TriedVariation` | A copy with `part` set to `digest`, by `name`. Setting a part to the recipe's own digest takes it out of `parts`. `ValueError("<name> has no recipe to set its <part> in")` without a recipe; `ValueError("a configuration always has a <part>: only <OPTIONAL> can be taken out")` for `None` and a part not in `OPTIONAL`. |
| `varied: Recipe \| None` (property) | The recipe with `parts` replaced over it, validated as a `Recipe`; `None` without a recipe. |

## model.py

### Constants

| Name | Value |
| --- | --- |
| `KINDS: dict[str, tuple[str, ...]]` | The thread kinds each word names: `configuration` is `skeleton`, each part of `PARTS` is `chunk.<part>`, `engine` is `engine.local` and `engine.remote`, and `tool`, `scorer`, `judge`, `expectation`, `appendix`, `expectation_schema`, `canary_set` and `model` are their own kind. |
| `WRITTEN: frozenset[str]` | The kinds a person writes as components: `chunk.<part>` for each of `PARTS`, `expectation`, `appendix`, `scorer` and `judge`. |
| `LABELLED: tuple[Part, ...]` | `("view", "resource")`, the parts of a scorer that have labels. |
| `COMPILED_LANGUAGE: str` | `"a compiled configuration's language comes from its recipe"`, what `new` and `follow` refuse a language with. |
| `PLACEHOLDERS: dict[SlotName, str]` | What stands in for each slot of a request rendered to be looked at: `‹vignette›`, `‹appendices›`, `‹completion›`, `‹expectation›`. |
| `SAVED: dict[Kept, ...]` | What `Saved.what` and `Written.what` call each of the catalog's `Kept`: `created`, `a new version` for `edited`, and `unchanged`. |

### Values
Frozen dataclasses that `Bench` returns.

| Class | Fields | Members |
| --- | --- | --- |
| `Family` | `id: int`, `about: About`, `case: str` | `name`: `about.name`, else `family <id>` |
| `Reach` | `thread: int` (the scorer's), `scorer: str` (its name), `view: int`, `label: str`, `offered: bool`, `cases: int`, `missing: list[Family]`, `choosing: list[Family]` | `have`: `cases` less the missing and those to choose from |
| `Graded` | `name: str`, `scorer: Scorer`, `labels: dict[int, str]`, `score: Score \| None = None`, `findings: list[Finding] = []`, `refused: str \| None = None` | `label(view: int) -> str`: the view's label, else `view <view>` |
| `Saved` | `name: str`, `digest: str` (the skeleton's), `what: "created" \| "a new version" \| "unchanged"`, `variation: TriedVariation` (the saved configuration, with nothing replaced) | |
| `Proposed` | `variation: Variation` (the catalog's: base, origin's head, what the fork varies), `proposal: Recipe \| Component`, `digest: str` (the component's, or the compiled skeleton's), `compilation: str \| None` (for a recipe) | |
| `Written` | `edit: Edit` (what was kept), `what: "created" \| "a new version" \| "unchanged"`, `findings: list[Finding]` (`linted` of its digest), `cases: dict[str, str]` (for an appendix's edit, each case that held the old version and its replacement; else empty) | |
| `Taken` | By case digest: `taken: dict[str, int]`, the thread each was taken into; `kept: dict[str, int]`, the person's own; `choosing: dict[str, list[int]]`, the shared threads offered, when there are several; `missing: list[str]`, the cases with none shared | |

## seen.py

### `class Seen`
`Seen(conn: Connection, person: Person, inventory: Inventory, facts: Facts)`: what the person sees, and the checks the
writes share. It writes nothing.

#### People

| Method | Returns / raises |
| --- | --- |
| `login(person: int \| None) -> str` | The person's login, `nobody` for `None`. `People.get`'s `LookupError` for an unknown id. |
| `owner(about: About) -> str` | `""` when the person owns it, else the owner's `login`. |

#### Threads

| Method | Returns / raises |
| --- | --- |
| `visible(kind: str) -> list[tuple[Edit, About]]` | `Catalog.visible(kind, person.id)`: the heads of the live threads of `kind` the person owns or collaborates on, in thread id order. |
| `threads(word: str) -> list[tuple[Edit, About]]` | `visible(kind)` for each kind `KINDS[word]` names, in that order. |
| `names(word: str) -> list[str]` | The names of `threads(word)`, sorted, without repeats. |
| `thread(word: str, name: str, model: str \| None = None) -> tuple[Edit, str]` | The head of the thread `name` names, and the name that found it, as below. |
| `thread_by_id(id: int, word: str \| None = None, *, deleted: bool = False) -> tuple[Edit, About]` | The head of thread `id`, and its `About`, when the person sees it, or with `deleted` when it is their own and deleted, and, with `word`, it is of a kind `KINDS[word]` names. Else `NotFound("no <word or 'thread'> <id> for <login>")`. |
| `deleted(kind: str) -> list[tuple[Edit, About]]` | The heads of the person's own deleted threads of `kind`, with their `About`s, in thread id order: `Catalog.heads(kind, deleted=True)` kept by owner. |
| `about(thread: int) -> About` | `Catalog.about` of the thread. |
| `holder(word: str, digest: str) -> tuple[Edit, About] \| None` | The first of `threads(word)` whose head is `digest`, of the person's own if any; `None` when none is. |
| `worded(thread: int) -> tuple[Edit, About, str]` | `thread_by_id(thread, <word>)`, where `<word>` is the word in `KINDS` for the thread's kind, with that word, else `thread`. |

`thread` looks among the threads of each kind `KINDS[word]` names, where each named thread is called both `NAME` and,
qualified, `<owner's login>/NAME` (`_qualified`, which gives nothing for a thread without a name or an owner):
1. A name nothing is called is replaced by its one variant `model` may use, `NAME (LANGUAGE)`, `NAME (MODEL)` or
   `NAME (LANGUAGE, MODEL)` (`chatddx.catalog.variants_for`), in the language the name ends in, as `NAME LANGUAGE`
   or `NAME (LANGUAGE)` (`chatddx.catalog.language_of`), else in any; several raise `Ambiguous("<word> '<name>' is
   made in more than one language: <names>; name one as '<base> <language>' or …")`.
2. A name that threads of two of the word's kinds hold, as a local and a remote engine can, raises
   `Ambiguous("<word> '<name>' names a <kind> and a <kind>")`.
3. A name no kind holds raises `NotFound("no <word> '<name>' for <login>")`, followed by `; per model: <names>` when
   threads are made per model under it, in its language when it names one. Without `model`, those names are its
   `per_model`.
4. Otherwise the thread is found by name among those of its kind, as `_named` finds it:
   - among the threads called `name`: the person's own when they own any, else all of them;
   - when none is called `name`, among those whose qualified name it is, the same way;
   - exactly one is returned; several raise `Ambiguous("<word> '<name>' names <n>; name one as OWNER/NAME")`, none
     `NotFound("no <word> '<name>' for <login>")`.

#### Components and the World

| Method | Returns / raises |
| --- | --- |
| `get(digest: str) -> Component` | `Store.get`. |
| `title(digest: str \| None) -> str` | `Catalog.title_of`, or `—` for `None`. |
| `model(engine: str) -> str \| None` | The model the engine serves, as the facts name it (`chatddx.facts.model_name`). |
| `served(engine: str) -> str` | The engine's `served_model_name`, the model a request to it carries. `StructuralError("<digest> is a <kind>, not an engine")` for another component. |
| `endpoint(name: str) -> str` | The digest of the engine the World's endpoint serves. The inventory's `LookupError` for an unknown endpoint; `NotFound("endpoint '<name>' serves engine <short>, which isn't in the store: load its World with init-data")` when the engine isn't stored. |

#### Families and expectations

| Method | Returns / raises |
| --- | --- |
| `families(tags: Iterable[str] = ()) -> list[Family]` | The families the person sees that have a case, with any of `tags`, or all without; by name. A family's case is the case of its current binding's vignette alone, when it is stored, else the first stored case of that vignette. |
| `family(name: str) -> Family` | The one of `families()` that `name` names, found among them as `thread` finds one among a kind's threads (its step 4), with `case` as the word. |
| `family_by_id(id: int) -> Family` | Family `id`, when the person sees it and it has a case. Else `NotFound("no case <id> for <login>")`. |
| `tags() -> list[str]` | The tags of the families the person sees, sorted, without repeats. |
| `current(family: int) -> Vignette` | The vignette of `family`'s latest binding. |
| `cases(family: int) -> list[str]` | The stored cases bound to the current vignette of `family` (`family_by_id`'s `NotFound`) (`Rows.bound_to`), the bare one first, then by digest. |
| `expectation_schemas(case: str) -> list[str]` | The schemas of the heads of the expectation threads of `case` the person sees, sorted, without repeats. Shared ones count here. |
| `expectation(case: str, schema: str) -> Expectation \| None` | The expectation `Catalog.expectations_for([case], person.id, schema)` picks: the head of the person's own live thread, or `None`. `Ambiguous` with the catalog's message, `case <case> has expectations to choose from, in threads <t1>, <t2>, …`, when there are several. |
| `shared(case: str, schema: str) -> list[tuple[Edit, About]]` | `Catalog.expectations_shared([case], person.id, schema)`: the heads of the live expectation threads of `case` under `schema` the person sees and doesn't own, in thread id order, each with its `About`. What they could take. |

#### The variation being tried

| Method | Returns / raises |
| --- | --- |
| `configuration(name: str, engine: str \| None = None) -> TriedVariation` | The configuration `thread("configuration", name, model(engine))` finds, with nothing replaced: its head, the name that found it without the person's own `<login>/`, and `Catalog.recipe` of its thread. |
| `chunk(part: str, name: str, engine: str \| None = None) -> str` | The digest of the head `thread(part, name, model(engine))` finds. |
| `variation(configuration: int, parts: Mapping[str, str \| None] \| None = None) -> TriedVariation` | The configuration `thread_by_id(configuration, "configuration")` finds, under its name or else its title, with each of `parts` replaced by the chunk of that digest, or taken out for `None`, labelled by the chunk's title. `ValueError("no part '<part>': the parts are <PARTS>")`, `ValueError("<digest> isn't a stored chunk of <part>")`, and `TriedVariation.set`'s. |
| `skeleton(variation: TriedVariation) -> Skeleton` | The configuration's head when nothing is replaced or it has no recipe; else `compile_request` of the varied recipe, with its errors. |
| `request(variation: TriedVariation, engine: str \| None, seed: int) -> dict[str, JsonValue]` | The request `render` makes of the skeleton with `PLACEHOLDERS` for its slots, `seed`, and `served(engine)` as the model, or `‹model›` without an engine. |
| `trial(skeleton: Skeleton, engine: str, cases: list[str], seed: int) -> tuple[Registry, Trial]` | A `Trial` of the skeleton, the engine, the cases and the one seed, and a registry holding it with everything it refers to, loaded from the store. Nothing is stored. |
| `findings(variation: TriedVariation, engine: str, seed: int, families: list[Family] \| None = None) -> list[Finding]` | For a judge configuration, `lints` of a `Judge` of its skeleton on `engine` with `seed`, built for the look and stored nowhere, whatever `families`. Otherwise `lints` of the variation's trial on `engine`. Without `families`, over the first case of the families the person sees, and `[]` when there is none. With them, over their cases, with each case's language its family's, the skeleton's its recipe's (`Catalog.recipe_language`), and any other's `Catalog.language_of`; `[]` for no families. |
| `scorers() -> list[tuple[Edit, About, Scorer]]` | `threads("scorer")`, each with its head resolved, by the thread's name, or else its title, as `score` and `scores_of` order theirs. |
| `purposed(found: Iterable[tuple[Edit, About]], purpose: Purpose) -> list[tuple[Edit, About]]` | The configurations of `found` whose head's skeleton has `purpose`, `generation` or `judge`, read from their heads alone (`Rows.components`). |
| `labels(scorer: str) -> dict[int, str]` | What a scorer digest's views are called for the person: `labels_of` the head `holder("scorer", scorer)` gives, else of the latest edit that held it in a scorer thread they see (`Rows.edits_holding`), their own threads first; `{}` when none did. |
| `labels_of(edit: Edit) -> dict[int, str]` | The view labels the edit of a scorer thread was written with (`Catalog.labels`), by the view's position. |
| `reach(variation: TriedVariation, families: list[Family]) -> list[Reach]` | `[]` for a judge configuration. Otherwise a `Reach` for each view of each of `scorers()`, named by the thread's name or else its title, and labelled by `labels_of` its head. `offered` as `View.offered_by` the skeleton's `output_schema` has it: a view with an `output` selector when it reaches the schema (`chatddx.factors.select.reaches`), and a view of the whole answer when there is no schema. For an offered view, `choosing` holds the families whose case has several expectations of the person's own under the scorer's schema, and `missing` the others whose case has none or whose expectation gives the view no items (`chatddx.factors.scoring.View.expectation_items`); both are empty for a view not offered. |

#### Runs and scores

| Method | Returns / raises |
| --- | --- |
| `runs() -> list[RunStarted]` | The runs the person owns and that aren't deleted, newest first, from the subjects whose entries ever named them (`Catalog.involving`). A collaborator on a run doesn't see it. |
| `run(prefix: str \| None = None) -> RunStarted` | The latest of `runs()`, or the one whose id, as `str(UUID)`, starts with `prefix`. `NotFound("<login> has no runs")`, `NotFound("no run of yours starts with '<prefix>'")` or `Ambiguous("<n> runs of yours start with '<prefix>'")`. |
| `run_by_id(run: UUID) -> RunStarted` | The run, when it has started and the person owns it, live. Else `NotFound("no run <id> of yours")`. |
| `reaching(digest: str) -> list[RunStarted]` | The runs of `runs()` whose trial's closure holds `digest` (`Store.reaching(digest, "trial")`), or the skeleton of a compilation whose closure holds it (`Store.reaching(digest, "compilation")`), newest first: a skeleton holds what a chunk sets rather than the chunk, so a chunk reaches its runs through what compiled them. |
| `described(run: RunStarted) -> str` | `<skeleton's title> × <endpoint, or the engine's title> × <the case's title, or "<n> cases"> (seed <seeds>)`. |
| `scorers_for(run: RunStarted) -> list[tuple[Edit, About]]` | The threads of `threads("scorer")` whose head applies to the run: each of its views is offered by the run's skeleton's `output_schema`, as `reach` has it, and each of its judges passes `chatddx.runner.score.judge_at` for the trial's cases, which refuses with a `ValueError` or `Refused` a judge the World bars. Stricter than `check_score`'s `view.unreachable`: a view of the whole answer reaches a structured output, but isn't offered by it. |
| `scoring(run: RunStarted, scorer: str) -> Scoring \| None` | The scoring the run would be scored under now: `Scoring(scorer, expectations)`, with, for each of the trial's cases in order, the expectation `Catalog.expectations_for(cases, person.id, <the scorer's expectation_schema>)` picks for it, cases without one left out. `None` when no case has one. `Ambiguous` when a case has several to choose from. Nothing is stored. |
| `unscored(run: RunStarted) -> list[str]` | The scorers of `scorers_for(run)` with no whole score of the run under `scoring(run, scorer)`, so a run whose expectations changed since it was scored is due again, and those whose `scoring` raises `Ambiguous`, which `score` refuses. A scorer without a scoring isn't one. A score is whole when it has finished, holds an item for each of the run's items and each of the scorer's views, and no judge call of it was stopped: a score that was stopped or never finished leaves the run to score. |
| `outstanding() -> list[tuple[RunStarted, list[str]]]` | Each finished run of `runs()`, newest first, with its `unscored`, when there are any. |
| `scores_of(run: UUID, every: bool = False) -> list[Graded]` | The latest score of the run under each scorer that scored it, by `scorer_name`; with `every`, every score of the run, newest first. |
| `score_of(run: UUID, score: UUID) -> Graded` | Score `score` of `run`, latest or not, after `run_by_id(run)`'s `NotFound`; `NotFound("no score <score> of run <run>")` for one that isn't the run's. |
| `scorer_name(scorer: str) -> str` | What the person calls a scorer digest: the name of `holder("scorer", scorer)`, else its title. |
| `scored_by(digest: str) -> list[RunStarted]` | The runs of `runs()` with a score under a scoring whose closure holds `digest` (`Store.reaching(digest, "scoring")`): its scorer, an expectation, the expectation schema, a judge. |
| `rendered_again(run: Run) -> dict[ItemKey, str \| None]` | For each item, whether its first request, rendered again from the trial and the vignette at its source, is what was sent: `None` when it is; `the vignette at the source isn't the one sent`; `the request renders otherwise now`; or the message of the `LookupError` or `StructuralError` fetching or preparing the case raised. |

`scorers_for`, `scoring`, `unscored`, `outstanding`, `scores_of`, `scored_by` and `described` resolve the run's
trial, its skeleton and the scorers through `Store.get` (`StructuralError` when one isn't stored or is of another
kind).

#### Checks the writes share

| Method | Returns / raises |
| --- | --- |
| `compiled(recipe: Recipe) -> tuple[Registry, Compilation]` | The recipe compiled by the running code (`chatddx.factors.request.compiled` with `rig()`), in a registry with what it refers to, loaded from the store; nothing is stored. The compiler's errors. |
| `linted(digest: str) -> list[Finding]` | `lints` of the stored component alone, with `Catalog.language_of` for languages. |
| `check_kind(thread: int, word: str, component: Component) -> None` | `ValueError("<word> <thread> holds <kind> components, not <kind>")` for a component of another kind than the thread's. |
| `check_expecting(expectation: Expectation, thread: int \| None, then: str = "edit that one") -> None` | `ValueError("<login> has their own expectation of <case's title> under <schema's title>, in thread <t>: <then>")` when the person owns a live expectation thread of its case and schema other than `thread`, `<t>` the lowest id of them. |
| `check_scorer(scorer: Scorer) -> None` | `ValueError` of `chatddx.scorers.shipped.problems` joined by `; `, when it finds any: a scorer the running code could never score with, such as `<entry point> isn't shipped with …`, `<entry point> is at version <n> in …, not <v>`, `… knows no metric …` and `view <i>'s params for <metric> …`. |

## bench.py

### `class Bench(Seen)`
`@final`. The `Seen`, with each write below bound as a method of the same name: `save`, `fork` and `edit` from
`configurations.py`; `component` (as a static method), `new`, `fork_component` and `edit_component` from
`components.py`; `appendix`, `case`, `replacement`, `type_case` and `carry` from `cases.py`, with its reads
`appendices_of`, `case_titled` and `case_titles`; `take` and `take_from` from `taking.py`; `say` from `saying.py`;
`proposal` and `follow` from `following.py`; and `start` and `score` from `runs.py`.

## configurations.py

| Write | Returns / raises |
| --- | --- |
| `save(variation: TriedVariation, name: str) -> Saved` | `edit` of the person's one live configuration named `name` (`Catalog.find`), on the head it finds, else `fork`. `Ambiguous("<login> has <n> configurations named '<name>'")` for several. |
| `fork(variation: TriedVariation, name: str) -> Saved` | A new configuration of the person's own, named `name`, forked from `variation.configuration`. |
| `edit(thread: int, variation: TriedVariation, head: int) -> Saved` | A new version of `thread`, a configuration the person owns whose head was edit `head` when they saw it, named by its name or else its title; `unchanged` when the skeleton is its head already. `thread_by_id`'s `NotFound`, `NotFound("no configuration <thread> of yours")` for one the person sees but doesn't own, and `MovedOn` when the head isn't `head` any more. |
| `keep_compilation(variation: TriedVariation) -> str \| None` | For a variation with parts replaced, the compilation of its skeleton by the running code (`Seen.compiled`), stored; its digest. `None` otherwise. |

`fork`, `edit` and `save` write, in one transaction, the skeleton's edit through `Catalog.keep` (`forked_from` the
varied edit, for a fork), and, for a variation with parts replaced, the compilation of its skeleton by the running code
(`keep_compilation`), which is the edit's compilation; otherwise the edit keeps the configuration's. The returned
`Saved.variation` is the saved configuration, with `Catalog.recipe` of its thread. `start` stores that compilation
too, after the run has started.

## components.py

| Write | Returns / raises |
| --- | --- |
| `component(doc: Mapping[str, JsonValue]) -> Component` | Takes no `Seen`. The component `doc` holds, as `GET /api/components` gives its body: of the model `BY_KIND[doc["kind"]]`, with `v`, when given, its schema version. `ValueError("<kind!r> isn't a kind a person writes: the kinds are …")` for a kind not in `WRITTEN`, `ValueError("<kind> is at v<n>, not v<v>")`, and the model's `ValidationError`. |
| `new(component: Component \| Recipe, name: str, language: str \| None = None, labels: Labels \| None = None) -> Written` | `component` as a new thread of the person's own named `name`, without an origin, a scorer with `labels`. A `Recipe` is compiled by the running code (`Seen.compiled`) and kept with `Catalog.create(skeleton, compilation=…)` in one transaction, `what` `"created"`: `ValueError(COMPILED_LANGUAGE)` for a language, `ValueError("only a scorer's views and resources have labels")` for labels, `ValueError("<digest> isn't a stored chunk of <part>")` for a part that isn't, and the compiler's errors, such as `StructuralError("generation prompt in a judge recipe")`. |
| `fork_component(thread: int, name: str, component: Component \| None = None, language: str \| None = None, labels: Labels \| None = None) -> Written` | A new thread of the person's own named `name`, forked from the head of `thread`, a thread they see (`NotFound("no <word> <thread> for <login>")`), holding `component`, else the head. A scorer forked as it is, with no labels given, keeps the head's (`Catalog.labels`). |
| `edit_component(thread: int, head: int, component: Component, language: str \| None = None, labels: Labels \| None = None) -> Written` | `component` as a new version of `thread`, which the person owns (`NotFound("no <word> <thread> of yours")`) and whose head was `head` (`MovedOn`); `unchanged` when it is the head already, which for a scorer given labels means its labels too. A scorer edited without labels keeps none, unless it is the head's, which is then `unchanged`. |
| `bound(appendix: Appendix) -> Appendix` | The appendix with its line endings LF, when it is bound to the current vignette of a family the person sees; else `ValueError("an appendix is bound to the current vignette of a case you see")`. |
| `keep_language(digest: str, language: str) -> None` | The language written for `digest` through `Catalog.language` where it has none, `ValueError("<title> is in <language> already: a text's language is the same wherever it is held")` where it has another, and nothing where it has the same. |

`new`, `fork_component` and `edit_component` write through `_written`. The forks and edits first refuse a component
of another kind than the thread's (`Seen.check_kind`), where `<word>` is the thread's kind's word in `KINDS`, else
`thread`. `_written` refuses, before anything is stored: a kind not in `WRITTEN` (`ValueError("a person doesn't write
<kind> components")`), a language for a kind not in `LANGUAGE_KINDS` (`ValueError("<kind> components have no language
of their own")`), labels for anything but a scorer (`ValueError("only a scorer's views and resources have labels")`),
a scorer the running code could never score with (`Seen.check_scorer`), and an expectation of a case and schema the
person owns one of in another thread (`Seen.check_expecting`). An appendix is then passed through `bound`. Then, in
one transaction: the component with the closure of its references, which `Store.load` must find stored
(`StructuralError("not in the store: […]")` otherwise) and `Store.add` checks; its language, when given, through
`keep_language`; `Catalog.keep`, with `forked_from` the head's edit for a fork, `head` for an edit, and the labels,
which it checks against the scorer's positions (`ValueError("<digest> has no <part> at position <n>")`,
`ValueError("the label of <part> <n> is empty")`); and, for an appendix's edit, each case `Store.reaching` finds
holding the old head at the same vignette, stored with the new version in its place (`_replaced`), as
`Written.cases`. `findings` are `linted` after the transaction.

## cases.py

| Write | Returns / raises |
| --- | --- |
| `appendix(family: int, text: str) -> Appendix` | An appendix of `text` bound to the current vignette of `family` (`family_by_id`'s `NotFound`), through `bound`; nothing stored. |
| `case(family: int, appendices: Sequence[str]) -> str` | A `Case` of `family`'s current vignette with `appendices` in order, stored with `Store.add`, whose check refuses an appendix bound to another vignette. `NotFound("no appendix <digest> for <login>")` for one no thread the person sees holds (`Catalog.containing`). Nothing is written in the catalog. |
| `replacement(case: str) -> str` | `case`, of a family the person sees and left at an earlier vignette, rebound to the current one (`families.rebind_case`) and stored with its rebound appendices. `NotFound("no case <case> for <login>")` for a case of no family; `ValueError("<case> is at its family's current vignette already")`. |
| `type_case(text: str, *, name: str \| None = None, language: str \| None = None, source: str \| None = None) -> Family` | The text kept in `source`, else the inventory's one `DatabaseSource` (`Texts.add`, a new id), its `Case` with the fingerprint of its UTF-8 bytes stored, and its family adopted by id alone (`Catalog.adopt(by_content=False)`), owned by the person, with a `name` and a `language` entry when given; all in one transaction. Refused before writing: `ValueError("a typed case holds text")` for blank text, `ValueError("a typed case may not hold U+0000, which can't be stored")`, `ValueError("a typed case holds at most <TYPED_TEXT_LIMIT> characters, not <n>")`, `ValueError("a name can't be empty: none leaves the case unnamed")`, `language_tag`'s `ValueError`, `ValueError("'<source>' isn't a database source of the World's")`, `ValueError("the World has no database source to type cases into")` or `ValueError("name the source to type into: …")`, and `OverQuota("<login> has typed <n> cases in the last day, as many as a day takes")` once `Texts.typed_since` a day ago reaches `TYPED_PER_DAY`. |
| `carry(thread: int, head: int, case: str) -> Written` | `edit_component` of the expectation `thread` onto `case`, with the same schema and data. `ValueError("<word> <thread> isn't an expectation")`, and `ValueError("<case> isn't a case of the family <old case> is of")`. |

Beside the writes, `cases.py` finds cases by their titles, as `chatddx.catalog.titles.describe_case` writes them,
`FAMILY with APPENDIX, …` (`WITH`), for an edge that names cases as a person reads them:

| Read | Returns / raises |
| --- | --- |
| `appendices_of(family: int) -> dict[str, str]` | The named appendices the person sees bound to the current vignette of `family` (`family_by_id`'s `NotFound`), each name with its head's digest. |
| `case_titled(title: str) -> tuple[Family, str]` | The family and the case `title` names: a family's name, for its default case, found as `Seen.family` finds it; or `FAMILY with APPENDIX, …`, the case of the family's current vignette with those appendices, by name, in order. `NotFound("no appendix <names> of <family>")` for a name `appendices_of` doesn't hold, and `NotFound("no case <title> for <login>")` for a case that isn't stored. |
| `case_titles() -> list[str]` | The titles of the cases that send appendices, sorted: of each family the person sees whose default is its bare case and that has an appendix the person sees, every case but that one. |

## taking.py

| Write | Returns / raises |
| --- | --- |
| `take(cases: Iterable[str], schema: str, owner: str \| None = None) -> Taken` | For each of `cases`, once, in order: the person's own live thread of it under `schema` is kept, the lowest id of several; else, of `shared(case, schema)`, `owner`'s only when given, one is forked into a thread of their own, several are to choose from and none is missing. One transaction. `ValueError("<schema> isn't a stored expectation schema")`; `NotFound("no person '<owner>'")`. |
| `take_from(thread: int, replace: bool = False) -> int` | Thread `thread`, an expectation the person sees, forked into a thread of their own; its id. `thread_by_id(thread, "expectation")`'s `NotFound`; `ValueError("expectation <thread> is yours already")`. When they own one of its case under its schema: `Conflict("<login> has their own expectation of <case's title> under <schema's title>, in thread <t>: replace it to take this one")`, unless `replace`, which deletes each of theirs in the same transaction. |

`take` and `take_from` fork with `Catalog.create(head.digest, person.id, forked_from=head.id, name=about.name)`, so the
fork keeps the shared thread's name and the catalog checks its one-expectation rule.

## saying.py

| Write | Returns / raises |
| --- | --- |
| `say(thread: int, *, name: str \| None \| EllipsisType = ..., description: str \| None = None, tags: Collection[str] \| None = None, collaborators: Collection[str] \| None = None, deleted: bool \| None = None) -> About` | What holds of `thread` afterwards, `...` and `None` leaving a field as it is; the `About` afterwards. See below. |

`say` finds the thread by its owner alone, deleted or not: `NotFound("no <word> <thread> of yours")` otherwise, where
`<word>` is its kind's word in `KINDS`, else `thread`. It refuses, before writing anything: more said of a deleted
thread that isn't restored (`ValueError("<word> <thread> is deleted: restore it to say more of it")`), an empty name
(`ValueError("a name can't be empty: none takes it away")`) or tag (`ValueError("a tag can't be empty")`), a login
nobody has (`NotFound("no person '<login>'")`), the person's own login among the collaborators
(`ValueError("<word> <thread> is yours: it is shared with others")`), and restoring an expectation thread where the
person owns another of its case and schema (`Seen.check_expecting`, ending `delete that one to restore this`). Then, in
one transaction and in this order, the entries that change what holds: restoring, the name (one without a value to
take it away), the description, a tag entry for each tag added or withdrawn, a collaborator entry for each person
added or withdrawn, and deleting.

## following.py

| Write | Returns / raises |
| --- | --- |
| `proposal(thread: int) -> Proposed \| None` | What following the origin of `thread`, a thread the person sees (`NotFound("no <word> <thread> for <login>")`), would keep. `None` when `Catalog.variation` gives none or one that hasn't `moved`, when the origin's thread isn't one the person `shows`, and when `Catalog.proposal` is `None`. A recipe is compiled by the running code (`Seen.compiled`), nothing stored. `ValueError("<word> <thread>'s changes don't fit its origin's head: …")` wraps a `ValueError` of the proposal or its compiling. |
| `follow(thread: int, head: int, language: str \| None = None) -> Written` | The proposal kept, in one transaction: stored with the closure of its references, `language` through `keep_language`, and `Catalog.edit(thread, digest, compilation=…, based_on=<origin's head>, head=head)`. `what` is `"a new version"`, also when the digest is the head's. `NotFound("no <word> <thread> of yours")` for one the person doesn't own, `ValueError("<word> <thread> has nothing to follow")` without a proposal, `ValueError("a compiled configuration's language comes from its recipe")`, `ValueError("<kind> components have no language of their own")`, `check_expecting`'s, `check_scorer`'s, and `MovedOn`. A scorer keeps the labels of whichever side's views, and resources, the proposal keeps (`_followed_labels`): the fork head's for a part `Variation.varies`, else the origin head's. |

## runs.py

| Write | Returns / raises |
| --- | --- |
| `start(variation: TriedVariation, endpoint: str, cases: list[str], seed: int) -> Running` | The variation's trial on the engine `endpoint(endpoint)` gives, started by a `Runner` for the person at that endpoint, under the default execution. Nothing is sent until `Running.send`. `ValueError("<label> is a judge configuration: a judge is asked as runs are scored, and isn't run on cases")` before anything else; `endpoint`'s errors, the runner's and its gate's. |
| `score(run: RunStarted, scorers: Collection[str] \| None = None, on_event: Callable[[ScoringEvent], None] \| None = None, halt: ScoreHalt \| None = None) -> list[Graded]` | The run scored by the scoring pass (`Grader.start`, `Grading.send(on_event)`, `Grading.finish`) under each of `scorers_for(run)`, or those of them whose digest is in `scorers`, as `scoring` builds it now, by name. `on_event` is given a `ScorerStarted` as each scorer's score starts, then the scoring pass's events as they come (docs/runner-api.md, "score.py"). A `halt` set, from any thread, refuses the scorers not started as `stopped`, and halts the one under way (`Grading.halt`), whose score is finished with what it has. A judge's calls go to the endpoint the scoring pass picks, as no endpoint is named. A scorer that can't score it is a `Graded` with `refused`: `none of the run's cases has an expectation`, or the message of one of `REFUSALS`, a `LookupError` (`Ambiguous` among them), `TypeError`, `ValueError` (the scoring pass's for a connection not in autocommit mode among them), `NotImplementedError` or `Refused`, raised on the way; one raised while it sends is refused after its score is finished with what it has. A `KeyboardInterrupt` stops the scoring: the score under way is finished with what it has and given, and each scorer after it is refused as `stopped`; the interrupt isn't raised again. |

| Name | Is |
| --- | --- |
| `ScorerStarted` | A frozen dataclass: `scorer`, the digest, `name`, as `score` names it, and `score`, the score's id. |
| `ScoringEvent` | `chatddx.runner.score.Event \| ScorerStarted`. |
| `ScoreHalt` | A halt for `score` that another thread sets: `set()`, `is_set()`, and `watching(grading)`, a context manager under which `set` halts that `Grading`, at once if it was set already. |

## Tests
In `src/chatddx/bench/test/`, all marked `solidified`.

| Module | Covers |
| --- | --- |
| `conftest.py` | `template` is `curated`, the test World as init-data lands it, with alice's giftbag, copied for each test; `autocommit` is on; `alice` is the test World's person, `bob` a new one with nothing; `bench` is alice's, on the test World's inventory and its facts beside the bundled ones (`chatddx.test.world.world_facts`). |
| `helpers.py` | `SOURCE`, the test World's vignette source; `trial(conn, plan, recipe, *ids)`, a stored trial of one of its recipes on `QWEN` (`chatddx.test.world`), with seed 7, over its cases of those vignette ids; `ran(conn, by, made, finished=True)`, a run of it recorded without sending; `another_expectation(bench, case, data)`, a second expectation of the person's own for the case, left by two writers at once. |
| `test_seen.py` | What a person sees, by name, `OWNER/NAME` and id; a variation from ids and digests; runs and what reaches a digest; what is left to score, and again after an expectation changes; the expectation a case is held to, own only; several to choose from refused by `expectation` and `scoring`, kept by `unscored` and `outstanding`, refused by `score` and listed apart by `reach`; a view of the whole answer offered by a text output only; a judged scorer applying where the World lets its judges run, and refused by `score` where it may pass later; a run's scores read the latest, every one or one by id, and not by another; a judge configuration listed apart, linted as a judge, with no reach, and not run; a scoring saying each score it starts, and a halt set before it refusing every scorer as stopped, with nothing written; per-model and per-language names; a variation compiled, and its request with placeholders; saving, forking and editing, a configuration's edit refused on a head that moved on; taking expectations for many cases, kept, to choose from, missing and by owner, and taking one thread, replacing the person's own only when told. |
| `test_writes.py` | A recipe of the person's own made into a configuration, its language and request, and what doesn't compile; writing chunks and expectations: new, edited and forked, as they are or changed, with their languages; what is refused, from kinds and versions to a language a text has already; an expectation's lints, and the person's one expectation per case and schema. Over the test World's `clinician` instructions. A judge written over a judge configuration, forked and edited, with its lints, and one over a generation configuration refused. |
| `test_cases.py` | An appendix built with LF line endings, a case of it listed after the bare one, and an appendix's edit storing a replacement; an expectation carried onto another case of its family, and not onto another family's; appendices and cases refused; a late case's replacement after a repair; a case found by its title, its family's name or `FAMILY with APPENDIX, …`. |
| `test_typed.py` | A typed case kept with its case, its family, its name and language, and fetched back; the same text typed twice; what can't be typed, and the day's quota; a typed case run on the fake vLLM. |
| `test_following.py` | A configuration following the archive's move with its own change on top, recompiled and based on the origin's head; a taken expectation following the archive's correction, with its lints; nothing to follow, another's thread, a head that moved on, a language for a compiled configuration, and an origin no longer shared. |
| `test_scorers.py` | A scorer of the person's own over shipped code, with its labels, the runs it applies to, and an unreachable view's lint; scorers refused, from code not shipped to params the schemas refuse, and labels refused; a fork keeping the archive's labels and renaming its own views, with nothing left to score again and the archive's labels as they were; the labels of a digest no head holds; following, with the labels of the views it keeps; a scorer refused once a deploy raises its version, moving on by following. |
| `test_said.py` | Saying names, descriptions, tags and collaborators, and nothing written when nothing changes; refusals, with nothing written; deleting, the deleted threads listed and found by id, and restoring, held to one expectation per case and schema. |
| `test_variation.py` | Replacing parts, taking a part back by setting the configuration's own chunk, and only an optional part taken out. Without a database. |
| `test_outcome.py` | Each outcome by an item's last call and the skeleton's output, but `salvaged`, which the repl's tests read (`src/chatddx/repl/test/test_running.py`), a turn whose call was never sent among them; usage over every call, and a stream cut short counted by the token ids it streamed. Without a database. |

The repl's and the API's tests reach the bench too, through their own fixtures over the same test World.

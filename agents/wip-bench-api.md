# Bench package

A candidate for `docs/bench-api.md`, beside `agents/wip-bench.md`, the candidate for `docs/bench.md`; below, those two
names mean these two files until they move.

Reference for the `chatddx.bench` package. It was written from `src/chatddx/bench/*` and docs/bench.md. What the bench
is and why it is shaped this way is in docs/bench.md; this file says what each name accepts, returns and raises. The
types it passes through are in docs/catalog-api.md (`Edit`, `About`, `Subject`, `Kept`), docs/factors-api.md
(`Component`, `Registry`, `Skeleton`, `Recipe`, `Trial`, `Case`, `Scorer`, `Scoring`, `Expectation`, `Finding`,
`StructuralError`), docs/ledger-api.md (`RunStarted`, `Run`, `RunItem`, `ItemKey`, `Score`), docs/store-api.md
(`Store`, `People`, `Rows`, `Connection`), docs/inventory-api.md (`Inventory`), docs/facts-api.md (`Facts`, `lints`),
agents/wip-identity.md (`Person`, `sees`, `preferred`) and agents/wip-runner.md (`Runner`, `Running`, `score_run`).

Paths are relative to `src/chatddx/bench/` unless they start with `src/`, `docs/` or `agents/`.

## Contents
- [Package](#package)
- [Conventions](#conventions)
- [errors.py](#errorspy): `NotFound`, `Ambiguous`, `Conflict`, `MovedOn`
- [outcome.py](#outcomepy): `Outcome`, `outcome`, `usage`
- [variation.py](#variationpy): `PARTS`, `OPTIONAL`, `TriedVariation`
- [view.py](#viewpy): `Bench`, `KINDS`, and the values `Bench` returns
- [Tests](#tests)
- [Beyond docs/bench.md](#beyond-docsbenchmd)

## Package

`chatddx.bench` re-exports `Ambiguous`, `Conflict`, `MovedOn`, `NotFound`, `Outcome`, `outcome`, `usage`, `OPTIONAL`,
`PARTS`, `TriedVariation`, `KINDS`, `WRITTEN`, `Bench`, `Family`, `Graded`, `Reach`, `Saved`, `Taken` and `Written`.
Edges import from `chatddx.bench`, never by path; tests import their helpers from `chatddx.bench.test.sample`.

| Module | Holds | Builds on |
| --- | --- | --- |
| `errors.py` | `NotFound`, `Ambiguous`, `Conflict`; `MovedOn`, the catalog's | `chatddx.catalog` |
| `outcome.py` | `Outcome`, `outcome`, `usage`: how a run's item ended, and the tokens it used | `chatddx.factors.request`, `chatddx.ledger`, `chatddx.runner.send`, `chatddx.scorers.answer` |
| `variation.py` | `PARTS`, `OPTIONAL`, `TriedVariation`: the variation being tried, a plain value | `chatddx.catalog`, `chatddx.factors.request` |
| `view.py` | `Bench`; `KINDS`, `WRITTEN`, `PLACEHOLDERS`; `Family`, `Reach`, `Graded`, `Saved`, `Taken`, `Written` | `errors.py`, `variation.py`, `chatddx.catalog` (and its `threads` and `titles`), `chatddx.core.rig`, `chatddx.factors.{base,bundle,cases,engine,request,scoring,select,trial}`, `chatddx.facts`, `chatddx.identity`, `chatddx.inventory`, `chatddx.ledger`, `chatddx.runner.{run,score}`, `chatddx.store` |

Why it is laid out so:
- **Modules are named by what they hold**, as `catalog/threads.py` and `runner/send.py` are. There is no
  `bench/bench.py`.
- **`variation.py` and `outcome.py` are pure.** Neither touches the store or a person, so they are tested without a
  database, and an edge can hold a `TriedVariation` without a bench.
- **`Bench` is one class in one module.** Its methods call each other through `self`: `configuration` and `chunk` use
  `thread`; `findings`, `reach`, `request`, `start` and the writes use `skeleton`; `score` and `unscored` use
  `scorers_for` and `scoring`; `reach`, `score` and `scores_of` use `labels`. Splitting it by concern would take mixins,
  which hide where a method lives, or functions taking a bench, which give edges a second surface beside `bench.*`.
- **"View"**, since the bench is a person-scoped view. It also writes for the person, but only through what the view
  finds.

## Conventions

**One person, one connection.** `Bench(conn, person, inventory, facts)` keeps them as `conn`, `person`, `inventory` and
`facts`, with a `Store` and a `Catalog` on the connection as `store` and `catalog`. Edges read through these what
doesn't depend on the person. `start` and `score` need `conn` in autocommit mode: the runner and the scoring pass
raise `ValueError` otherwise.

**Caches.** The login of each person id and the model each engine serves are cached for the bench's life.

**Words.** A method that takes `word` takes a key of `KINDS`; another raises `KeyError`.

**What the person sees.** A thread or family the person sees is one whose `About.shows(person.id)`: live, and owned
or shared. Their own is `About.owned_by(person.id)`: live, and owned. Of several the person sees, their own come
first (`chatddx.identity.preferred`).

**Errors.** `NotFound` and `Ambiguous`, both `LookupError`s, are raised for what the person sees or names. A refused
variation is a `ValueError`, and so are `Conflict`, a write the person must say they want, and `MovedOn`, an edit made
on a head that moved on. `StructuralError`, a
`ValueError`, comes from `Store.get` and `resolve` when a digest isn't stored or is of another kind. The errors of the
catalog, the inventory, the runner and its gate pass through unless an entry says otherwise. Messages name the person by
login and the thing by the word for it, for a person to read; nothing in the bench is UI.

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

### `class Conflict(ValueError)`
The write would undo what the person has unless they say so: taking an expectation when they own one of its case under
its schema, without replacing it.

## outcome.py

### `type Outcome = Literal["stopped", "errored", "unread", "completed", "invalid", "valid"]`

### `outcome(skeleton: Skeleton, item: RunItem) -> tuple[Outcome, str | None]`
How an item ended, by its last call, read through `chatddx.scorers.answer.read`, and why when there is something to
say:
1. `"stopped"`, `None`, when the call's error is the runner's `STOPPED`;
2. without an answer: `"errored"` with the call's error, else `"unread"` with why the answer couldn't be read;
3. with one: `"completed"`, with the call's error, when the skeleton has no `output_schema`;
4. else `"invalid"`, with the call's error or else what the schema refused, or `"valid"`, with the call's error.

### `usage(item: RunItem) -> tuple[int, int]`
The prompt and completion tokens of all the item's calls, summed from each response's `usage`. A response without
`usage`, or a count that isn't an `int`, adds nothing.

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

## view.py

### Constants

| Name | Value |
| --- | --- |
| `KINDS: dict[str, tuple[str, ...]]` | The thread kinds each word names: `configuration` is `skeleton`, each part of `PARTS` is `chunk.<part>`, `engine` is `engine.local` and `engine.remote`, and `tool`, `scorer`, `judge`, `expectation`, `expectation_schema`, `canary_set` and `model` are their own kind. |
| `WRITTEN: frozenset[str]` | The kinds a person writes as components: `chunk.<part>` for each of `PARTS`, and `expectation`. |
| `PLACEHOLDERS: dict[SlotName, str]` | What stands in for each slot of a request rendered to be looked at: `‹vignette›`, `‹appendices›`, `‹completion›`, `‹expectation›`. |

### Values
Frozen dataclasses that `Bench` returns.

| Class | Fields | Members |
| --- | --- | --- |
| `Family` | `id: int`, `about: About`, `case: str` | `name`: `about.name`, else `family <id>` |
| `Reach` | `thread: int` (the scorer's), `scorer: str` (its name), `view: int`, `label: str`, `offered: bool`, `cases: int`, `missing: list[Family]`, `choosing: list[Family]` | `have`: `cases` less the missing and those to choose from |
| `Graded` | `name: str`, `scorer: Scorer`, `labels: dict[int, str]`, `score: Score \| None = None`, `findings: list[Finding] = []`, `refused: str \| None = None` | `label(view: int) -> str`: the view's label, else `view <view>` |
| `Saved` | `name: str`, `digest: str` (the skeleton's), `what: "created" \| "a new version" \| "unchanged"`, `variation: TriedVariation` (the saved configuration, with nothing replaced) | |
| `Written` | `edit: Edit` (what was kept), `what: "created" \| "a new version" \| "unchanged"`, `findings: list[Finding]` (`linted` of its digest) | |
| `Taken` | By case digest: `taken: dict[str, int]`, the thread each was taken into; `kept: dict[str, int]`, the person's own; `choosing: dict[str, list[int]]`, the shared threads of several owners; `missing: list[str]`, the cases with none shared | |

### `class Bench`
`Bench(conn: Connection, person: Person, inventory: Inventory, facts: Facts)`.

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
| `thread_by_id(id: int, word: str \| None = None) -> tuple[Edit, About]` | The head of thread `id`, and its `About`, when the person sees it and, with `word`, it is of a kind `KINDS[word]` names. Else `NotFound("no <word or 'thread'> <id> for <login>")`. |
| `about(thread: int) -> About` | `Catalog.about` of the thread. |
| `holder(word: str, digest: str) -> tuple[Edit, About] \| None` | The first of `threads(word)` whose head is `digest`, of the person's own if any; `None` when none is. |

`thread` looks among the threads of each kind `KINDS[word]` names, where each named thread is called both `NAME` and,
qualified, `<owner's login>/NAME` (`_qualified`, which gives nothing for a thread without a name or an owner):
1. A name nothing is called is replaced by its one variant `model` may use, `NAME (LANGUAGE)`, `NAME (MODEL)` or
   `NAME (LANGUAGE, MODEL)` (`chatddx.catalog.variants_for`); several raise `Ambiguous("<word> '<name>' is made in
   more than one language: <names>")`.
2. A name that threads of two of the word's kinds hold, as a local and a remote engine can, raises
   `Ambiguous("<word> '<name>' names a <kind> and a <kind>")`.
3. A name no kind holds raises `NotFound("no <word> '<name>' for <login>")`, followed by `; per model: <names>` when
   threads are made per model under it. Without `model`, those names are its `per_model`.
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
| `findings(variation: TriedVariation, engine: str, seed: int, families: list[Family] \| None = None) -> list[Finding]` | `lints` of the variation's trial on `engine`. Without `families`, over the first case of the families the person sees, and `[]` when there is none. With them, over their cases, with each case's language its family's, the skeleton's its recipe's (`Catalog.recipe_language`), and any other's `Catalog.language_of`; `[]` for no families. |
| `scorers() -> list[tuple[Edit, About, Scorer]]` | `threads("scorer")`, each with its head resolved. |
| `labels(scorer: str) -> dict[int, str]` | The scorer's view labels (`Catalog.labels`), by the view's position. |
| `reach(variation: TriedVariation, families: list[Family]) -> list[Reach]` | A `Reach` for each view of each of `scorers()`, named by the thread's name or else its title. `offered` when the view's `output` selector reaches the skeleton's `output_schema` (`chatddx.factors.select.reaches`). For an offered view, `choosing` holds the families whose case has several expectations of the person's own under the scorer's schema, and `missing` the others whose case has none or whose expectation gives the view no items (`View.expectation_items`); both are empty for a view not offered. |

#### Writes for the person

| Method | Returns / raises |
| --- | --- |
| `save(variation: TriedVariation, name: str) -> Saved` | `edit` of the person's one live configuration named `name` (`Catalog.find`), on the head it finds, else `fork`. `Ambiguous("<login> has <n> configurations named '<name>'")` for several. |
| `fork(variation: TriedVariation, name: str) -> Saved` | A new configuration of the person's own, named `name`, forked from `variation.configuration`. |
| `edit(thread: int, variation: TriedVariation, head: int) -> Saved` | A new version of `thread`, a configuration the person owns whose head was edit `head` when they saw it, named by its name or else its title; `unchanged` when the skeleton is its head already. `thread_by_id`'s `NotFound`, `NotFound("no configuration <thread> of yours")` for one the person sees but doesn't own, and `MovedOn` when the head isn't `head` any more. |
| `start(variation: TriedVariation, endpoint: str, cases: list[str], seed: int) -> Running` | The variation's trial on the engine `endpoint(endpoint)` gives, started by a `Runner` for the person at that endpoint. Nothing is sent until `Running.send`. `endpoint`'s errors, the runner's and its gate's. |
| `component(doc: Mapping[str, JsonValue]) -> Component` | The component `doc` holds, as `GET /api/components` gives its body: of the model `BY_KIND[doc["kind"]]`, with `v`, when given, its schema version. `ValueError("<kind!r> isn't a kind a person writes: the kinds are …")` for a kind not in `WRITTEN`, `ValueError("<kind> is at v<n>, not v<v>")`, and the model's `ValidationError`. |
| `new(component: Component, name: str, language: str \| None = None) -> Written` | `component` as a new thread of the person's own named `name`, without an origin. |
| `fork_component(thread: int, name: str, component: Component \| None = None, language: str \| None = None) -> Written` | A new thread of the person's own named `name`, forked from the head of `thread`, a thread they see (`NotFound("no <word> <thread> for <login>")`), holding `component`, else the head. |
| `edit_component(thread: int, head: int, component: Component, language: str \| None = None) -> Written` | `component` as a new version of `thread`, which the person owns (`NotFound("no <word> <thread> of yours")`) and whose head was `head` (`MovedOn`); `unchanged` when it is the head already. |
| `linted(digest: str) -> list[Finding]` | `lints` of the stored component alone, with `Catalog.language_of` for languages. |
| `take(cases: Iterable[str], schema: str, owner: str \| None = None) -> Taken` | For each of `cases`, once, in order: the person's own live thread of it under `schema` is kept, the lowest id of several; else, of `shared(case, schema)`, `owner`'s only when given, one is forked into a thread of their own, several are to choose from and none is missing. One transaction. `ValueError("<schema> isn't a stored expectation schema")`; `NotFound("no person '<owner>'")`. |
| `take_from(thread: int, replace: bool = False) -> int` | Thread `thread`, an expectation the person sees, forked into a thread of their own; its id. `thread_by_id(thread, "expectation")`'s `NotFound`; `ValueError("expectation <thread> is yours already")`. When they own one of its case under its schema: `Conflict("<login> has their own expectation of <case's title> under <schema's title>, in thread <t>: replace it to take this one")`, unless `replace`, which deletes each of theirs in the same transaction. |
| `score(run: RunStarted, scorers: Collection[str] \| None = None) -> list[Graded]` | The run scored by `score_run` under each of `scorers_for(run)`, or those of them whose digest is in `scorers`, as `scoring` builds it now. A scorer that can't score it is a `Graded` with `refused`: `none of the run's cases has an expectation`, or the message of a `LookupError` (`Ambiguous` among them), `TypeError` or `NotImplementedError` raised on the way. |

`fork`, `edit` and `save` write, in one transaction, the skeleton's edit through `Catalog.keep` (`forked_from` the
varied edit, for a fork), and, for a variation with parts replaced, the compilation of its skeleton by the running code
(`compiled` with `rig()`), which is the edit's compilation; otherwise the edit keeps the configuration's. The returned
`Saved.variation` is the saved configuration, with `Catalog.recipe` of its thread. `start` stores that compilation too,
after the run has started.

`new`, `fork_component` and `edit_component` write through `_written`, which refuses, before anything is stored: a
kind not in `WRITTEN` (`ValueError("a person doesn't write <kind> components")`), a language for a kind not in
`LANGUAGE_KINDS` (`ValueError("<kind> components have no language of their own")`), and an expectation of a case and
schema the person owns one of in another thread (`ValueError("<login> has their own expectation of <case> under
<schema>, in thread <t>: edit that one")`). The forks and edits refuse a component of another kind than the thread's,
`ValueError("<word> <thread> holds <kind> components, not <kind>")`, where `<word>` is the thread's kind's word in
`KINDS`, else `thread`. Then, in one transaction: the component with the closure of its references, which
`Store.load` must find stored (`StructuralError("not in the store: […]")` otherwise) and `Store.add` checks; its
language, when given, through `Catalog.language` where the digest has none, `ValueError("<title> is in <language>
already: a text's language is the same wherever it is held")` where it has another, and nothing where it has the same;
and `Catalog.keep`, with `forked_from` the head's edit for a fork and `head` for an edit. `findings` are `linted`
after the transaction.

`take` and `take_from` fork with `Catalog.create(head.digest, person.id, forked_from=head.id, name=about.name)`, so the
fork keeps the shared thread's name and the catalog checks its one-expectation rule.

#### Runs and scores

| Method | Returns / raises |
| --- | --- |
| `runs() -> list[RunStarted]` | The runs the person owns and that aren't deleted, newest first, from the subjects whose entries ever named them (`Catalog.involving`). A collaborator on a run doesn't see it. |
| `run(prefix: str \| None = None) -> RunStarted` | The latest of `runs()`, or the one whose id, as `str(UUID)`, starts with `prefix`. `NotFound("<login> has no runs")`, `NotFound("no run of yours starts with '<prefix>'")` or `Ambiguous("<n> runs of yours start with '<prefix>'")`. |
| `run_by_id(run: UUID) -> RunStarted` | The run, when it has started and the person owns it, live. Else `NotFound("no run <id> of yours")`. |
| `reaching(digest: str) -> list[RunStarted]` | The runs of `runs()` whose trial's closure holds `digest` (`Store.reaching(digest, "trial")`), newest first. |
| `described(run: RunStarted) -> str` | `<skeleton's title> × <endpoint, or the engine's title> × <the case's title, or "<n> cases"> (seed <seeds>)`. |
| `scorers_for(run: RunStarted) -> list[tuple[Edit, About]]` | The threads of `threads("scorer")` whose head's every view reaches the run's skeleton's `output_schema`: the check `check_score` warns about as `view.unreachable`. |
| `scoring(run: RunStarted, scorer: str) -> Scoring \| None` | The scoring the run would be scored under now: `Scoring(scorer, expectations)`, with, for each of the trial's cases in order, the expectation `Catalog.expectations_for(cases, person.id, <the scorer's expectation_schema>)` picks for it, cases without one left out. `None` when no case has one. `Ambiguous` when a case has several to choose from. Nothing is stored. |
| `unscored(run: RunStarted) -> list[str]` | The scorers of `scorers_for(run)` with no score of the run under `scoring(run, scorer)`, so a run whose expectations changed since it was scored is due again, and those whose `scoring` raises `Ambiguous`, which `score` refuses. A scorer without a scoring isn't one. |
| `outstanding() -> list[tuple[RunStarted, list[str]]]` | Each finished run of `runs()`, newest first, with its `unscored`, when there are any. |
| `scores_of(run: UUID) -> list[Graded]` | The latest score of the run under each scorer that scored it, by name: the name of `holder("scorer", scorer)`, else the scorer's title. |
| `scored_by(scorer: str) -> list[RunStarted]` | The runs of `runs()` with a score under a scoring of `scorer`. |
| `rendered_again(run: Run) -> dict[ItemKey, str \| None]` | For each item, whether its first request, rendered again from the trial and the vignette at its source, is what was sent: `None` when it is; `the vignette at the source isn't the one sent`; `the request renders otherwise now`; or the message of the `LookupError` or `StructuralError` fetching or preparing the case raised. |

`scorers_for`, `scoring`, `unscored`, `outstanding`, `scores_of`, `scored_by` and `described` resolve the run's
trial, its skeleton and the scorers through `Store.get` (`StructuralError` when one isn't stored or is of another
kind).

## Tests
In `src/chatddx/bench/test/`, all marked `wip`.

| Module | Covers |
| --- | --- |
| `conftest.py` | `template` is `curated`, the sample as init-data lands it, copied for each test; `autocommit` is on; `alice` is the sample's person, `bob` a new one with nothing; `bench` is alice's, on the sample World's inventory and the bundled facts. |
| `sample.py` | `SOURCE`, `FREE_TEXT`, `PLAN` and `QWEN`; `trial(conn, plan, recipe, *ids)`, a stored trial of a sample recipe on some of the sample's cases; `ran(conn, by, made, finished=True)`, a run of it recorded without sending; `another_expectation(bench, case, data)`, a second expectation of the person's own for the case, left by two writers at once. |
| `test_view.py` | What a person sees, by name, `OWNER/NAME` and id; a variation from ids and digests; runs and what reaches a digest; what is left to score, and again after an expectation changes; the expectation a case is held to, own only; several to choose from refused by `expectation` and `scoring`, kept by `unscored` and `outstanding`, refused by `score` and listed apart by `reach`; per-model and per-language names; a variation compiled, and its request with placeholders; saving, forking and editing, a configuration's edit refused on a head that moved on; taking expectations for many cases, kept, to choose from, missing and by owner, and taking one thread, replacing the person's own only when told. |
| `test_writes.py` | Writing chunks and expectations: new, edited and forked, as they are or changed, with their languages; what is refused, from kinds and versions to a language a text has already; an expectation's lints, and the person's one expectation per case and schema. Over the sample's `clinician` instructions. |
| `test_variation.py` | Replacing parts, taking a part back by setting the configuration's own chunk, and only an optional part taken out. Without a database. |
| `test_outcome.py` | Each outcome by an item's last call and the skeleton's output, and usage over every call. Without a database. |

The repl's and the API's tests reach the bench too, through their own fixtures over the same sample.

## Beyond docs/bench.md
Behavior described here that `docs/bench.md` doesn't state, or states otherwise:
- `thread` raises `Ambiguous` for a name that threads of two of a word's kinds hold, and a variant is looked for only
  when no thread is called the name itself.
- `configuration` drops the person's own `<login>/` from the name it was found by, and keeps another owner's.
- `holder` takes the first in thread id order of the kinds' order, among the person's own if any.
- `families` and `family_by_id` leave out a family whose current vignette has no stored case; `tags` doesn't.
- `expectation_schemas` counts shared expectations, while `expectation` reads only the person's own, so a schema can
  be listed with no expectation under it.
- `findings` without families lints over one case only, and nothing at all when the person sees no case.
- `score` turns a `LookupError`, `TypeError` or `NotImplementedError` into a refusal, but not a `ValueError`, such as
  the scoring pass's for a connection not in autocommit mode.
- `unscored` doesn't list a scorer under which no case of the run has an expectation.
- `login` gives `nobody` for a subject without an owner.
- `_language` compares with `Catalog.language_of`, which is a chunk's own language, so the refusal is about the
  digest's language, not the thread's history.
- `edit_component` checks the kind after ownership, so another's thread of another kind is `NotFound`, not a
  `ValueError`.
- `take` keeps the lowest-numbered of a person's own threads when they have several, and `take_from` with `replace`
  deletes each of them.
- `take` with an owner leaves a case missing when only others share one, and `NotFound` is for an owner with no login,
  not one sharing nothing.

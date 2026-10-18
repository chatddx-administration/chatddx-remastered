# `chatddx.bench`

Written by `chatddx reference` from `src/chatddx/bench/`: each public name's signature and what it raises.

## `add_compilations(seen: Seen, registry: Registry, skeleton: str) -> None`
`src/chatddx/bench/seen.py:add_compilations`
- raises what `store.Store.compilations`, `store.Store.get` raise

## `class Ambiguous(LookupError)`
`src/chatddx/bench/errors.py:Ambiguous`

## `@final class Bench(Seen)`
`src/chatddx/bench/bench.py:Bench`

### `Bench.again(run: RunStarted, seeds: Sequence[int]) -> Running`
`src/chatddx/bench/runs.py:again`
- raises `ValueError("run <run.run> was sent to no endpoint, so it can't run again")`
- raises `NotFound("no case <missing[0]> for <seen.person.login>")`
- raises `OverQuota("a run holds at most <settings.ITEMS_PER_RUN> items, not <items>")`
- raises `OverQuota("<said>, as many as a day takes")`
- raises `OverQuota("<said>, and a day takes <settings.RUNS_PER_DAY>, not <len(runs)> more")`
- raises what `Seen.families`, `Seen.title`, `catalog.Entry`, `catalog.Subject`, `catalog.families.family_of`, `factors.base.resolve`, `runner.Runner`, `runner.Runner.start`, `store.Catalog.note`, `trial` raise

### `Bench.case(family: int, appendices: Sequence[str]) -> str`
`src/chatddx/bench/cases.py:case`
- raises `NotFound("no appendix <digest> for <seen.person.login>")`
- raises what `Seen.family`, `catalog.Subject`, `factors.cases.Case`, `store.Store.add`, `store.Store.load` raise

### `Bench.check(component: Component) -> Checked`
`src/chatddx/bench/components.py:check`
- raises `ValueError("a person doesn't write <kind> components")`
- raises what `add_compilations`, `bound`, `check_scorer`, `factors.Registry.check`, `factors.Registry.closure`, `facts.lints`, `store.Store.load` raise

### `Bench.edit(thread: int, head: int, held: Component | TriedVariation, language: str | None = None, labels: Labels | None = None) -> Written`
`src/chatddx/bench/components.py:edit`
- raises `NotFound("no <word> <thread> of yours")`
- raises `ValueError("a compiled configuration's language comes from its recipe")`
- raises `ValueError("only a scorer's views and resources have labels")`
- raises `ValueError("a person doesn't write <kind> components")`
- raises `ValueError("<kind> components have no language of their own")`
- raises `ValueError("<new.case> isn't a case of the family <old.case> is of")`
- raises what `bound`, `catalog.families.family_of`, `catalog.threads.head`, `check_expecting`, `check_kind`, `check_scorer`, `factors.base.resolve`, `factors.cases.Case`, `keep_language`, `kept`, `linted`, `store.Catalog.keep`, `store.Store.add`, `store.Store.load`, `worded` raise

### `Bench.follow(thread: int, head: int, language: str | None = None) -> Written`
`src/chatddx/bench/following.py:follow`
- raises `NotFound("no <word> <thread> of yours")`
- raises `ValueError("<word> <thread> has nothing to follow")`
- raises `ValueError("a compiled configuration's language comes from its recipe")`
- raises `ValueError("<kind> components have no language of their own")`
- raises `ValueError("<word> <thread>'s changes don't fit its origin's head: <e>")`
- raises what `catalog.Subject`, `catalog.threads.divergence`, `catalog.threads.head`, `catalog.threads.proposal`, `catalog.threads.thread`, `check_expecting`, `check_scorer`, `keep_language`, `linted`, `store.Catalog.edit`, `store.Store.add`, `worded` raise

### `Bench.follow_moved(thread: int, head: int) -> Written`
`src/chatddx/bench/following.py:follow_moved`
- raises `NotFound("no configuration <thread> of yours")`
- raises `ValueError("configuration <thread> was compiled for nothing that has moved on")`
- raises `ValueError("configuration <thread> can't follow <_what(made)> <made.about>: <made.refused>")`
- raises what `Seen.thread`, `catalog.threads.behind`, `factors.base.resolve`, `factors.engine.model_of`, `linted`, `store.Catalog.edit`, `store.Store.add` raise

### `Bench.fork(thread: int, name: str, held: Component | TriedVariation | None = None, language: str | None = None, labels: Labels | None = None) -> Written`
`src/chatddx/bench/components.py:fork`
- raises `ValueError("<held.label> isn't a variation of configuration <thread>")`
- raises `ValueError("a compiled configuration's language comes from its recipe")`
- raises `ValueError("only a scorer's views and resources have labels")`
- raises `ValueError("a person doesn't write <kind> components")`
- raises `ValueError("<kind> components have no language of their own")`
- raises `ValueError("<new.case> isn't a case of the family <old.case> is of")`
- raises what `Seen.variation`, `bound`, `catalog.families.family_of`, `catalog.threads.head`, `check_expecting`, `check_kind`, `check_scorer`, `factors.base.resolve`, `factors.cases.Case`, `keep_language`, `kept`, `linted`, `store.Catalog.keep`, `store.Store.add`, `store.Store.get`, `store.Store.load`, `worded` raise

### `Bench.moved(thread: int) -> Moved | None`
`src/chatddx/bench/following.py:moved`
- raises what `Seen.thread`, `catalog.threads.behind`, `factors.base.resolve`, `factors.engine.model_of` raise

### `Bench.new(component: Component | Recipe, name: str, language: str | None = None, labels: Labels | None = None) -> Written`
`src/chatddx/bench/components.py:new`
- raises `ValueError("<digest> isn't a stored <what>")`
- raises `ValueError("a person doesn't write <kind> components")`
- raises `ValueError("<kind> components have no language of their own")`
- raises `ValueError("only a scorer's views and resources have labels")`
- raises `ValueError("<new.case> isn't a case of the family <old.case> is of")`
- raises `ValueError("a compiled configuration's language comes from its recipe")`
- raises what `bound`, `catalog.families.family_of`, `catalog.threads.head`, `check_expecting`, `check_scorer`, `compiled`, `factors.base.resolve`, `factors.cases.Case`, `keep_language`, `linted`, `store.Catalog.create`, `store.Catalog.keep`, `store.Store.add`, `store.Store.load` raise

### `Bench.proposal(thread: int) -> Proposed | None`
`src/chatddx/bench/following.py:proposal`
- raises `ValueError("<word> <thread>'s changes don't fit its origin's head: <e>")`
- raises what `catalog.Subject`, `catalog.threads.divergence`, `catalog.threads.proposal`, `worded` raise

### `Bench.queue(running: Running, score: bool = True) -> Job`
`src/chatddx/bench/runs.py:queue`
- raises what `store.Queue.put` raises

### `Bench.queue_scoring(run: RunStarted, scorers: Collection[str] | None = None) -> list[str]`
`src/chatddx/bench/runs.py:queue_scoring`
- raises `ValueError("run <run.run> hasn't finished")`
- raises `ValueError("scorer <missing[0]> doesn't apply to run <run.run>")`
- raises `ValueError("no scorer applies to run <run.run>")`
- raises what `Seen.scorers`, `store.Queue.put` raise

### `Bench.replacement(case: str) -> str`
`src/chatddx/bench/cases.py:replacement`
- raises `NotFound("no case <case> for <seen.person.login>")`
- raises what `Seen.family`, `catalog.families.family_of`, `catalog.families.replacement`, `store.Store.add` raise

### `Bench.resume(run: RunStarted) -> Running`
`src/chatddx/bench/runs.py:resume`
- raises what `runner.Runner`, `runner.Runner.resume` raise

### `Bench.save(variation: TriedVariation, name: str) -> Written`
`src/chatddx/bench/configurations.py:save`
- raises `Ambiguous("<seen.person.login> has <len(mine)> configurations named <name!r>")`
- raises what `catalog.threads.find`, `catalog.threads.head`, `kept` raise

### `Bench.say(thread: int, *, name: str | None | EllipsisType = ..., description: str | None = None, tags: Collection[str] | None = None, collaborators: Collection[str] | None = None, deleted: bool | None = None) -> About`
`src/chatddx/bench/saying.py:say`
- raises `NotFound("no <word> <thread> of yours")`
- raises `ValueError("<word> <thread> is deleted: restore it to say more of it")`
- raises `ValueError("a name can't be empty: none takes it away")`
- raises `ValueError("a tag can't be empty")`
- raises `ValueError("<word> <thread> is yours: it is shared with others")`
- raises `NotFound("no person <login!r>")`
- raises what `catalog.Entry`, `catalog.Subject`, `catalog.threads.head`, `check_expecting`, `store.Catalog.note`, `store.People.find`, `store.Store.get` raise

### `Bench.score(run: RunStarted, scorers: Collection[str] | None = None, on_event: Callable[[ScoringEvent], None] | None = None, halt: Halt | None = None) -> list[Graded]`
`src/chatddx/bench/runs.py:score`
- raises what `Seen.scorers`, `catalog.titles.title`, `runner.Grading.finish` raise

### `Bench.start(variation: TriedVariation, endpoint: str | None, cases: list[str], seeds: Sequence[int], cleanup: Sequence[CleanupOp] | None = None, execution: Execution | None = None, canaries: str | None = None) -> Started`
`src/chatddx/bench/runs.py:start`
- raises `ValueError("<variation.label> is a judge configuration: a judge is asked as runs are scored, and isn't run on cases")`
- raises `NotFound("no case <missing[0]> for <seen.person.login>")`
- raises `ValueError("no case can be sent: <"; ".join(c.refused or "" for c in left_out)>")`
- raises `OverQuota("a run holds at most <settings.ITEMS_PER_RUN> items, not <items>")`
- raises `OverQuota("<said>, as many as a day takes")`
- raises `OverQuota("<said>, and a day takes <settings.RUNS_PER_DAY>, not <len(runs)> more")`
- raises what `Seen.at`, `Seen.families`, `Seen.languages`, `Seen.skeleton`, `catalog.Entry`, `catalog.Subject`, `factors.base.resolve`, `inventory.Inventory.source`, `keep_compilation`, `runner.Runner`, `runner.Runner.start`, `store.Catalog.note`, `store.Store.load`, `trial` raise

### `Bench.take(cases: Iterable[str], schema: str, owner: str | None = None) -> Taken`
`src/chatddx/bench/taking.py:take`
- raises `ValueError("<schema> isn't a stored expectation schema")`
- raises `NotFound("no person <owner!r>")`
- raises what `catalog.threads.expecting`, `store.Catalog.create`, `store.People.find` raise

### `Bench.take_from(thread: int, replace: bool = False) -> int`
`src/chatddx/bench/taking.py:take_from`
- raises `ValueError("expectation <thread> is yours already")`
- raises `Conflict("<seen.person.login> has their own expectation of <seen.title(case)> under <seen.title(schema)>, in thread <mine[0]>: replace it to take this one")`
- raises what `Seen.thread`, `Seen.title`, `catalog.Entry`, `catalog.Subject`, `choices`, `factors.base.resolve`, `store.Catalog.create`, `store.Catalog.note` raise

### `Bench.type_case(text: str, *, language: str, name: str | None = None, source: str | None = None) -> Family`
`src/chatddx/bench/cases.py:type_case`
- raises `ValueError("a typed case holds text")`
- raises `ValueError("a typed case may not hold U+0000, which can't be stored")`
- raises `ValueError("a typed case holds at most <settings.TYPED_TEXT_LIMIT> characters, not <len(text)>")`
- raises `ValueError("a name can't be empty: none leaves the case unnamed")`
- raises `ValueError(str(e))`
- raises `OverQuota("<seen.person.login> has typed <typed> cases in the last day, as many as a day takes")`
- raises what `Seen.family`, `catalog.Entry`, `catalog.Subject`, `factors.cases.Case`, `store.Catalog.adopt`, `store.Catalog.note`, `store.Store.add` raise

## `bound(seen: Seen, appendix: Appendix) -> Appendix`
`src/chatddx/bench/components.py:bound`
- raises `ValueError("an appendix is bound to the current vignette of a case you see")`
- raises what `catalog.Subject`, `factors.cases.Appendix` raise

## `@dataclass(frozen=True) class Carried`
`src/chatddx/bench/model.py:Carried`
- `language: str | None`
- `cases: list[str]`
- `skeleton: Skeleton | None = None`
- `translated: bool = False`
- `refused: str | None = None`

## `check_expecting(seen: Seen, expectation: Expectation, thread: int | None, then: str = "edit that one") -> None`
`src/chatddx/bench/seen.py:check_expecting`
- raises `ValueError("<seen.person.login> has their own expectation of <seen.title(case)> under <seen.title(schema)>, in thread <others[0]>: <then>")`
- raises what `Seen.title`, `choices` raise

## `check_kind(seen: Seen, thread: int, word: str, held: Component | TriedVariation) -> None`
`src/chatddx/bench/seen.py:check_kind`
- raises `ValueError("<word> <thread> holds <kind> components, not <given>")`
- raises what `catalog.threads.thread` raises

## `check_scorer(scorer: Scorer) -> None`
`src/chatddx/bench/seen.py:check_scorer`
- raises `ValueError("; ".join(found))`

## `@dataclass(frozen=True) class Checked`
`src/chatddx/bench/model.py:Checked`
- `digest: str`
- `findings: list[Finding]`

## `choices(seen: Seen, cases: Sequence[str], schema: str) -> dict[str, dict[int, str]]`
`src/chatddx/bench/seen.py:choices`
- raises what `catalog.threads.expecting` raises

## `compiled(seen: Seen, recipe: Recipe, facts: ModelFacts | None | Literal["current"] = "current", into: str | None = None) -> tuple[Registry, Compilation]`
`src/chatddx/bench/seen.py:compiled`
- raises what `factors.request.compiled`, `facts.Facts.about`, `store.Store.load` raise

## `COMPILED_LANGUAGE = "a compiled configuration's language comes from its recipe"`
`src/chatddx/bench/model.py:COMPILED_LANGUAGE`

## `compiled_with(seen: Seen, variation: TriedVariation) -> ModelFacts | None`
`src/chatddx/bench/seen.py:compiled_with`
- raises what `factors.base.resolve`, `facts.Facts.about` raise

## `class Conflict(ValueError)`
`src/chatddx/bench/errors.py:Conflict`

## `@dataclass(frozen=True) class Endpoint`
`src/chatddx/bench/model.py:Endpoint`
- `name: str`
- `spec: EndpointSpec`
- `model: Model`
- `engine: str`, a property

## `@dataclass(frozen=True) class Family`
`src/chatddx/bench/model.py:Family`
- `id: int`
- `about: About`
- `vignette: Vignette`
- `cases: tuple[str, ...]`
- `case: str`, a property
- `name: str`, a property

## `@dataclass(frozen=True) class Graded`
`src/chatddx/bench/model.py:Graded`
- `name: str`
- `scorer: Scorer`
- `labels: dict[int, str]`
- `score: Score | None = None`
- `findings: list[Finding] = field(default_factory=list[Finding])`
- `refused: str | None = None`

### `Graded.label(view: int) -> str`

## `keep_compilation(seen: Seen, variation: TriedVariation, into: str | None = None) -> str | None`
`src/chatddx/bench/configurations.py:keep_compilation`
- raises what `compiled`, `compiled_with`, `store.Store.add` raise

## `keep_language(seen: Seen, digest: str, language: str) -> None`
`src/chatddx/bench/components.py:keep_language`
- raises `ValueError("<seen.title(digest)> is in <held> already: a text's language is the same wherever it is held")`
- raises what `Seen.title`, `catalog.language.language_of`, `store.Catalog.language` raise

## `kept(seen: Seen, variation: TriedVariation, thread: int | None, name: str | None, head: int | None = None) -> Written`
`src/chatddx/bench/configurations.py:kept`
- raises what `Seen.skeleton`, `keep_compilation`, `linted`, `store.Catalog.keep` raise

## `KINDS: dict[str, tuple[str, ...]]`
`src/chatddx/bench/model.py:KINDS`

## `LABELLED: tuple[Part, ...] = ("view", "resource")`
`src/chatddx/bench/model.py:LABELLED`

## `labels_of(seen: Seen, edit: Edit) -> dict[int, str]`
`src/chatddx/bench/seen.py:labels_of`

## `left_out(carried: Carried, subject: str) -> Finding`
`src/chatddx/bench/seen.py:left_out`

## `linted(seen: Seen, digest: str) -> list[Finding]`
`src/chatddx/bench/seen.py:linted`
- raises what `add_compilations`, `factors.Registry.get`, `facts.lints`, `store.Store.load` raise

## `@dataclass(frozen=True) class Moved`
`src/chatddx/bench/model.py:Moved`
- `facts: Behind | None`
- `model: Behind | None`
- `about: str`
- `digest: str | None`
- `compilation: str | None`
- `refused: str | None`

## `NONE = "none"`
`src/chatddx/bench/seen.py:NONE`

## `class NotFound(LookupError)`
`src/chatddx/bench/errors.py:NotFound`

## `class OverQuota(ValueError)`
`src/chatddx/bench/errors.py:OverQuota`

## `picked(seen: Seen, cases: Sequence[str], schema: str) -> dict[str, str | None]`
`src/chatddx/bench/seen.py:picked`
- raises `Ambiguous(str(e))`
- raises what `choices` raises

## `PLACEHOLDERS: dict[SlotName, str]`
`src/chatddx/bench/model.py:PLACEHOLDERS`

## `@dataclass(frozen=True) class Proposed`
`src/chatddx/bench/model.py:Proposed`
- `divergence: Divergence`
- `proposal: Recipe | Component`
- `digest: str`
- `compilation: str | None`

## `@dataclass(frozen=True) class Reach`
`src/chatddx/bench/model.py:Reach`
- `thread: int`
- `scorer: str`
- `view: int`
- `label: str`
- `offered: bool`
- `cases: int`
- `missing: list[Family]`
- `choosing: list[Family]`
- `have: int`, a property

## `REFUSALS = (LookupError, TypeError, ValueError, NotImplementedError, Refused)`
`src/chatddx/bench/runs.py:REFUSALS`

## `SAVED: dict[Kept, Literal["created", "a new version", "unchanged"]]`
`src/chatddx/bench/model.py:SAVED`

## `@dataclass(frozen=True) class ScorerStarted`
`src/chatddx/bench/runs.py:ScorerStarted`
- `scorer: str`
- `name: str`
- `score: UUID`

## `scoring(seen: Seen, run: RunStarted, scorer: str) -> Scoring | None`
`src/chatddx/bench/seen.py:scoring`
- raises what `factors.base.resolve`, `factors.scoring.Scoring`, `picked` raise

## `type ScoringEvent = ScoreEvent | ScorerStarted`
`src/chatddx/bench/runs.py:ScoringEvent`

## `class Seen`
`src/chatddx/bench/seen.py:Seen`
- `conn: Connection`
- `person: Person`
- `inventory: Inventory`
- `store: Store`
- `catalog: Catalog`
- `rows: Rows`
- `people: People`
- `facts: Facts`, a property
  - raises what `catalog.threads.heads`, `factors.base.resolve`, `store.Rows.components` raise

### `Seen(conn: Connection, person: Person, inventory: Inventory)`

### `Seen.at(variation: TriedVariation, endpoint: str | None) -> Endpoint`
- raises `ValueError("<variation.label> names no model: name the endpoint to send it to")`
- raises `ValueError(str(e))`
- raises `ValueError("endpoint <endpoint!r> serves another model than <variation.label>'s, <self.title(model)>")`
- raises what `Seen.endpoint`, `Seen.title` raise

### `Seen.case_titled(title: str) -> tuple[Family, str]`
- raises `NotFound("no appendix <', '.join(missing)> of <family.name>")`
- raises `NotFound("no case <title> for <self.person.login>")`
- raises what `Seen.family`, `catalog.threads.heads`, `factors.base.resolve`, `factors.cases.Case` raise

### `Seen.described(run: RunStarted) -> str`
- raises what `Seen.title`, `catalog.Subject`, `factors.base.resolve`, `store.Store.compilations` raise

### `Seen.endpoint(name: str) -> Endpoint`
- raises `NotFound(str(e))`
- raises `NotFound("endpoint <name!r> serves engine <short(spec.engine)>, which isn't in the store: load its World with init-data")`
- raises what `factors.engine.model_of` raises

### `Seen.expectation(case: str, schema: str) -> Expectation | None`
- raises what `factors.base.resolve`, `picked` raise

### `Seen.expectation_schemas(case: str) -> list[str]`
- raises what `catalog.threads.expecting`, `factors.base.resolve` raise

### `Seen.families(tags: Iterable[str] = ()) -> list[Family]`
- raises what `catalog.Subject`, `factors.cases.Case` raise

### `Seen.family(found: int | str) -> Family`
- raises `NotFound("no case <found> for <self.person.login>")`
- raises `NotFound("no <word> <name!r> for <self.person.login>")`
- raises `Ambiguous("<word> <name!r> names <len(several)>; name one as OWNER/NAME")`
- raises what `Seen.families`, `Seen.login`, `catalog.Subject`, `factors.cases.Case` raise

### `Seen.findings(variation: TriedVariation, engine: str, seed: int, carried: Sequence[Carried] | None = None) -> list[Finding]`
- raises what `Seen.families`, `Seen.skeleton`, `add_compilations`, `catalog.language.languages_of`, `factors.scoring.Judge`, `facts.lints`, `store.Store.load`, `trial` raise

### `Seen.holder(digest: str, recipe: Recipe | None = None) -> tuple[Edit, About] | None`
- raises what `catalog.Subject`, `catalog.threads.recipe` raise

### `Seen.labels(scorer: str) -> dict[int, str]`
- raises what `Seen.holder`, `Seen.threads` raise

### `Seen.landed(variation: TriedVariation) -> dict[str, Landing]`
- raises what `compiled_with`, `factors.request.landings`, `store.Store.load` raise

### `Seen.languages(variation: TriedVariation, cases: Sequence[str]) -> list[Carried]`
- raises what `Seen.families`, `Seen.skeleton`, `catalog.language.language_of`, `catalog.language.languages_of`, `catalog.language.recipe_language`, `factors.base.resolve` raise

### `Seen.login(person: int | None) -> str`
- raises what `store.People.get` raises

### `Seen.outstanding() -> list[tuple[RunStarted, list[str]]]`
- raises what `Seen.runs`, `Seen.unscored` raise

### `Seen.reach(variation: TriedVariation, families: list[Family]) -> list[Reach]`
- raises what `Seen.scorers`, `Seen.skeleton`, `catalog.titles.title`, `choices`, `factors.base.resolve`, `store.Rows.components` raise

### `Seen.request(variation: TriedVariation, engine: str | None, seed: int) -> dict[str, JsonValue]`
- raises what `Seen.skeleton`, `factors.engine.served_model_name`, `factors.request.Skeleton.render` raise

### `Seen.run(found: UUID | str | None = None) -> RunStarted`
- raises `NotFound("no run <found> of yours")`
- raises `NotFound("<self.person.login> has no runs")`
- raises `NotFound("no run of yours starts with <found!r>")`
- raises `Ambiguous("<len(several)> runs of yours start with <found!r>")`
- raises what `Seen.runs`, `catalog.Subject` raise

### `Seen.runs(*, reaching: str | None = None, scored_by: str | None = None, started_with: UUID | None = None) -> list[RunStarted]`
- raises what `catalog.Subject`, `factors.base.resolve`, `store.Rows.involving` raise

### `Seen.score_of(run: RunStarted, score: UUID) -> Graded`
- raises `NotFound("no score <score> of run <run.run>")`
- raises what `Seen.labels`, `Seen.title`, `factors.base.resolve`, `store.Store.score` raise

### `Seen.scorers(run: RunStarted | None = None) -> list[tuple[Edit, About, Scorer]]`
- raises what `Seen.threads`, `factors.base.resolve` raise

### `Seen.scores_of(run: RunStarted, every: bool = False) -> list[Graded]`
- raises what `Seen.labels`, `Seen.title`, `factors.base.resolve`, `store.Store.score` raise

### `Seen.shared(case: str, schema: str) -> list[tuple[Edit, About]]`
- raises what `catalog.threads.expecting` raises

### `Seen.skeleton(variation: TriedVariation, into: str | None = None) -> Skeleton`
- raises `factors.StructuralError("<variation.label> has no translations into <into>")`
- raises what `compiled_with`, `factors.base.resolve`, `factors.request.compile_request`, `store.Store.load` raise

### `Seen.thread(found: int | str, word: str | None = None, *, deleted: bool = False) -> tuple[Edit, About]`
- raises `NotFound("no <word or 'thread'> <found> for <self.person.login>")`
- raises `NotFound("no <what> <name!r> for <self.person.login>")`
- raises `Ambiguous("<what> <name!r> names a <' and a '.join(several)>")`
- raises `NotFound("no <word> <name!r> for <self.person.login>")`
- raises `Ambiguous("<word> <name!r> names <len(several)>; name one as OWNER/NAME")`
- raises what `Seen.login`, `catalog.Subject`, `catalog.threads.head`, `catalog.threads.heads` raise

### `Seen.threads(word: str, *, deleted: bool = False, purpose: Purpose | None = None, answering: str | None = None) -> list[tuple[Edit, About]]`
- raises `ValueError("only a configuration has a purpose and an answer: <word>")`
- raises what `catalog.threads.heads`, `factors.base.resolve`, `store.Rows.components` raise

### `Seen.title(digest: str) -> str`
- raises what `catalog.Subject`, `catalog.titles.title_of` raise

### `Seen.unscored(run: RunStarted) -> list[str]`
- raises what `Seen.scorers`, `scoring`, `store.Store.run`, `store.Store.score` raise

### `Seen.variation(configuration: int | str, parts: Mapping[str, str | None] | None = None, head: int | None = None) -> TriedVariation`
- raises `NotFound("no edit <head> of configuration <edit.thread>")`
- raises `ValueError("no part <part!r>: the parts are <', '.join(RECIPE_PARTS)>")`
- raises `ValueError("<digest> isn't a stored <what>")`
- raises what `Seen.thread`, `Seen.title`, `TriedVariation.set`, `catalog.threads.recipe`, `catalog.titles.title` raise

## `@dataclass(frozen=True) class Started`
`src/chatddx/bench/model.py:Started`
- `runs: list[tuple[Carried, Running]]`
- `left_out: list[Carried]`
- `first: Running`, a property

## `@dataclass(frozen=True) class Taken`
`src/chatddx/bench/model.py:Taken`
- `taken: dict[str, int]`
- `kept: dict[str, int]`
- `choosing: dict[str, list[int]]`
- `missing: list[str]`

## `trial(seen: Seen, skeleton: Skeleton, engine: str, cases: list[str], seeds: Sequence[int], cleanup: tuple[CleanupOp, ...] = ()) -> tuple[Registry, Trial]`
`src/chatddx/bench/seen.py:trial`
- raises what `factors.trial.Trial`, `store.Store.load` raise

## `@dataclass(frozen=True) class TriedVariation`
`src/chatddx/bench/variation.py:TriedVariation`
- `configuration: Edit`
- `name: str`
- `recipe: Recipe | None = None`
- `parts: Mapping[str, tuple[str | None, str]]`
- `label: str`, a property
- `varied: Recipe | None`, a property

### `TriedVariation.held(part: str) -> str | None`

### `TriedVariation.set(part: str, digest: str | None, name: str) -> "TriedVariation"`
- raises `ValueError("<self.name> has no recipe to set its <part> in")`
- raises `ValueError("a configuration always has <'an' if part[0] in 'aeiou' else 'a'> <part>: only <', '.join(OPTIONAL_PARTS)> can be taken out")`

## `WITH = re.compile(r"^(?P<family>.+?) with (?P<appendices>.+)$")`
`src/chatddx/bench/seen.py:WITH`

## `word_of(kind: str | None) -> str`
`src/chatddx/bench/model.py:word_of`

## `worded(seen: Seen, thread: int) -> tuple[Edit, About, str]`
`src/chatddx/bench/seen.py:worded`
- raises what `Seen.thread` raises

## `WRITTEN: frozenset[str]`
`src/chatddx/bench/model.py:WRITTEN`

## `@dataclass(frozen=True) class Written`
`src/chatddx/bench/model.py:Written`
- `edit: Edit`
- `what: Literal["created", "a new version", "unchanged"]`
- `findings: list[Finding]`
- `cases: dict[str, str] = field(default_factory=dict)`

# `chatddx.bench`

Written by `chatddx stamp write` from `src/chatddx/bench/`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it:

```
## `<name>` `@<decorator>` `[<type parameters>]` `(<bases>)`
`<file>:<qualified name>`

* `<parameter or field>: <type> = <default>`
* ∟`<return type>`

Raises:
1. `<exception>`: `<arguments>` (from `<exception caught>`, through `<private helper>`, in a `ValidationError`)

Finds:
1. `<code>`: `<message>` (`<level>`, from `<exception caught>`, through `<private helper>`)
```

- A constant or a type alias is its definition instead of bullets; a class and its `__init__` leave out ∟, and a method its instance; `*`: the parameters after it are keyword-only, `/`: those before it positional-only.
- Raises and Finds are the function's own and its private helpers', in the order the code reaches them, each once, a `Whoops` left out; what a public function it calls raises is in that function's entry.
- Text is quoted, a value in it as `{<expression>}`, and an argument that isn't text is as written; a finding is a warning unless it gives its level.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

## `add_compilations`
`src/chatddx/bench/seen.py:add_compilations`

* `seen: Seen`
* `registry: Registry`
* `skeleton: str`
* ∟`None`

## `Ambiguous` `(LookupError)`
`src/chatddx/bench/errors.py:Ambiguous`

## `Bench` `@final` `(Seen)`
`src/chatddx/bench/bench.py:Bench`

## `Bench.again`
`src/chatddx/bench/runs.py:again`

Begins a run of the run's skeleton and cases under other seeds, at its handle's
latest endpoint, and sends nothing.

Stores the run's trial, start record and entries once the gate has confirmed the
endpoint with a request to it.

Heads-up: the gate's `Refused` passes through.

* `run: RunStarted`
* `seeds: Sequence[int]`
* ∟`Running`

Raises:
1. `ValueError`: `"run {run.run} was sent to no endpoint, so it can't run again"`
2. `NotFound`: `"no case {missing[0]} for {seen.person.login}"`
3. `ValueError`: `"run {run.run} ran weights {handle.name} no longer holds: run its configuration, followed, instead"`
4. `OverQuota`: `"a run holds at most {settings.ITEMS_PER_RUN} items, not {items}"` (through `_begun`)
5. `OverQuota`: `"{said}, as many as a day takes"` (through `_begun`)
6. `OverQuota`: `"{said}, and a day takes {settings.RUNS_PER_DAY}, not {len(runs)} more"` (through `_begun`)

## `Bench.case`
`src/chatddx/bench/cases.py:case`

* `family: int`
* `appendices: Sequence[str]`
* ∟`str`

Raises:
1. `NotFound`: `"no appendix {digest} for {seen.person.login}"`

## `Bench.check`
`src/chatddx/bench/components.py:check`

* `component: Component | Recipe`
* ∟`Checked`

Raises:
1. `ValueError`: `"{digest} isn't a stored {what}"` (through `_stored_parts`)
2. `ValueError`: `"a person doesn't write {component.kind_name} components"`
3. `NotFound`: `"no case {missing[0]} for {seen.person.login}"` (through `_carried`)
4. `ValueError`: `"a trial's cases are in one language, not in {' and '.join(known)}"` (through `_carried`)
5. `ValueError`: `"{seen.title(trial.skeleton)} has no translations into {into}, its cases' language"` (through `_carried`)

## `Bench.edit`
`src/chatddx/bench/components.py:edit`

* `thread: int`
* `head: int`
* `held: Component | TriedVariation`
* `language: str | None = None`
* `labels: Labels | None = None`
* ∟`Written`

Raises:
1. `NotFound`: `"no {word} {thread} of yours"`
2. `ValueError`: `"a compiled configuration's language comes from its recipe"` (through `_configured`)
3. `ValueError`: `"only a scorer's views and resources have labels"` (through `_configured`)
4. `ValueError`: `"a person doesn't write {kind} components"` (through `_written`)
5. `ValueError`: `"{kind} components have no language of their own"` (through `_written`)
6. `ValueError`: `"{new.case} isn't a case of the family {old.case} is of"` (through `_written`)
7. `NotFound`: `"no case {missing[0]} for {seen.person.login}"` (through `_written`)
8. `ValueError`: `"a trial's cases are in one language, not in {' and '.join(known)}"` (through `_written`)
9. `ValueError`: `"{seen.title(trial.skeleton)} has no translations into {into}, its cases' language"` (through `_written`)

## `Bench.follow`
`src/chatddx/bench/following.py:follow`

* `thread: int`
* `head: int`
* `language: str | None = None`
* ∟`Written`

Raises:
1. `NotFound`: `"no {word} {thread} of yours"`
2. `ValueError`: `"{word} {thread}'s changes don't fit its origin's head: {e}"` (from `ValueError`, through `_proposed`)
3. `ValueError`: `"{word} {thread} has nothing to follow"`
4. `ValueError`: `"a compiled configuration's language comes from its recipe"`
5. `ValueError`: `"{kind} components have no language of their own"`

## `Bench.follow_moved`
`src/chatddx/bench/following.py:follow_moved`

* `thread: int`
* `head: int`
* ∟`Written`

Raises:
1. `NotFound`: `"no configuration {thread} of yours"`
2. `ValueError`: `"configuration {thread} was compiled for nothing that has moved on"`
3. `ValueError`: `"configuration {thread} can't follow {_what(made)} {made.about}: {made.refused}"`

## `Bench.fork`
`src/chatddx/bench/components.py:fork`

* `thread: int`
* `name: str`
* `held: Component | TriedVariation | None = None`
* `language: str | None = None`
* `labels: Labels | None = None`
* ∟`Written`

Raises:
1. `ValueError`: `"{held.label} isn't a variation of configuration {thread}"`
2. `ValueError`: `"a compiled configuration's language comes from its recipe"` (through `_configured`)
3. `ValueError`: `"only a scorer's views and resources have labels"` (through `_configured`)
4. `ValueError`: `"a person doesn't write {kind} components"` (through `_written`)
5. `ValueError`: `"{kind} components have no language of their own"` (through `_written`)
6. `ValueError`: `"{new.case} isn't a case of the family {old.case} is of"` (through `_written`)
7. `NotFound`: `"no case {missing[0]} for {seen.person.login}"` (through `_written`)
8. `ValueError`: `"a trial's cases are in one language, not in {' and '.join(known)}"` (through `_written`)
9. `ValueError`: `"{seen.title(trial.skeleton)} has no translations into {into}, its cases' language"` (through `_written`)

## `Bench.leave`
`src/chatddx/bench/saying.py:leave`

Takes the person out of what they see of a thread or a family shared with them,
by an entry of their own, until its owner shares it with them again.

Reads the subject's entries before and after, and writes one entry.

* `subject: Subject`
* ∟`About`

Raises:
1. `NotFound`: `"no {_what(seen, subject)} shared with {seen.person.login}"`

## `Bench.lineage`
`src/chatddx/bench/following.py:lineage`

* `thread: int`
* ∟`list[Kin]`

## `Bench.moved`
`src/chatddx/bench/following.py:moved`

* `thread: int`
* ∟`Moved | None`

## `Bench.new`
`src/chatddx/bench/components.py:new`

* `component: Component | Recipe`
* `name: str`
* `language: str | None = None`
* `labels: Labels | None = None`
* ∟`Written`

Raises:
1. `ValueError`: `"a compiled configuration's language comes from its recipe"` (through `_configured`)
2. `ValueError`: `"only a scorer's views and resources have labels"` (through `_configured`)
3. `ValueError`: `"{digest} isn't a stored {what}"` (through `_stored_parts`)
4. `ValueError`: `"a person doesn't write {kind} components"` (through `_written`)
5. `ValueError`: `"{kind} components have no language of their own"` (through `_written`)
6. `ValueError`: `"{new.case} isn't a case of the family {old.case} is of"` (through `_written`)
7. `NotFound`: `"no case {missing[0]} for {seen.person.login}"` (through `_written`)
8. `ValueError`: `"a trial's cases are in one language, not in {' and '.join(known)}"` (through `_written`)
9. `ValueError`: `"{seen.title(trial.skeleton)} has no translations into {into}, its cases' language"` (through `_written`)

## `Bench.proposal`
`src/chatddx/bench/following.py:proposal`

* `thread: int`
* ∟`Proposed | None`

Raises:
1. `ValueError`: `"{word} {thread}'s changes don't fit its origin's head: {e}"` (from `ValueError`, through `_proposed`)

## `Bench.queue`
`src/chatddx/bench/runs.py:queue`

* `running: Running`
* `score: bool = True`
* ∟`Job`

## `Bench.queue_scoring`
`src/chatddx/bench/runs.py:queue_scoring`

* `run: RunStarted`
* `scorers: Collection[str] | None = None`
* ∟`list[str]`

Raises:
1. `ValueError`: `"run {run.run} hasn't finished"`
2. `ValueError`: `"scorer {missing[0]} doesn't apply to run {run.run}"`
3. `ValueError`: `"no scorer applies to run {run.run}"`

## `Bench.replacement`
`src/chatddx/bench/cases.py:replacement`

* `case: str`
* ∟`str`

Raises:
1. `NotFound`: `"no case {case} for {seen.person.login}"`

## `Bench.resume`
`src/chatddx/bench/runs.py:resume`

* `run: RunStarted`
* ∟`Running`

## `Bench.save`
`src/chatddx/bench/configurations.py:save`

* `variation: TriedVariation`
* `name: str`
* ∟`Written`

Raises:
1. `Ambiguous`: `"{seen.person.login} has {len(mine)} configurations named {name!r}"`

## `Bench.say`
`src/chatddx/bench/saying.py:say`

Writes what holds of the thread or family itself in one transaction.
`...` leaves a name or a description as it is and `None` takes it away.

Reads the subject's entries before and after, a person per collaborator, and for a
restored expectation thread the person's expectations of its case and schema.

Heads-up:
- Only families take language.
- An expectation thread is refused while the person owns another of its case and
  schema.

* `subject: Subject`
* `*`
* `name: str | None | EllipsisType = ...`
* `description: str | None | EllipsisType = ...`
* `tags: Collection[str] | None = None`
* `collaborators: Collection[str] | None = None`
* `deleted: bool | None = None`
* `language: str | None = None`
* ∟`About`

Raises:
1. `NotFound`: `"no {what} of yours"`
2. `ValueError`: `"{what} is deleted: restore it to say more of it"`
3. `ValueError`: `"a name can't be empty: none takes it away"`
4. `ValueError`: `"a description can't be empty: none takes it away"`
5. `ValueError`: `"a tag can't be empty"`
6. `NotFound`: `"no person {login!r}"` (through `_sharing`)
7. `ValueError`: `"{what} is yours: it is shared with others"`

## `Bench.score`
`src/chatddx/bench/runs.py:score`

Scores the run under each scorer that applies, or each of those given, one after
another in the calling thread.

Sends each judged view's requests to its judge's endpoint once the gate has confirmed
it with a request to it, and writes each score's records as it goes.

Heads-up: a scorer refused is returned with why in `Graded.refused`, not raised, and
so is each one after a halt or an interrupt, as stopped.

* `run: RunStarted`
* `scorers: Collection[str] | None = None`
* `on_event: Callable[[ScoringEvent], None] | None = None`
* `halt: Halt | None = None`
* ∟`list[Graded]`

## `Bench.start`
`src/chatddx/bench/runs.py:start`

Begins a run for each language the cases are sent in, and sends nothing.

Compiles the variation into each language, and stores each run's trial, start record
and entries, and the compilations of what it begins, in one transaction, which holds
while the gate confirms the endpoint with a request to it for each run.

Heads-up: the gate's `Refused` passes through.

* `variation: TriedVariation`
* `endpoint: str | None`
* `cases: list[str]`
* `seeds: Sequence[int]`
* `cleanup: Sequence[CleanupOp] | None = None`
* `execution: Execution | None = None`
* `canaries: str | None = None`
* ∟`Started`

Raises:
1. `ValueError`: `"{variation.label} is a judge configuration: a judge is asked as runs are scored, and isn't run on cases"`
2. `NotFound`: `"no case {missing[0]} for {seen.person.login}"`
3. `ValueError`: `"no case can be sent: {"; ".join(c.refused or "" for c in left_out)}"`
4. `OverQuota`: `"a run holds at most {settings.ITEMS_PER_RUN} items, not {items}"` (through `_check_quota`)
5. `OverQuota`: `"{said}, as many as a day takes"` (through `_check_quota`)
6. `OverQuota`: `"{said}, and a day takes {settings.RUNS_PER_DAY}, not {len(runs)} more"` (through `_check_quota`)

## `Bench.start_trials`
`src/chatddx/bench/runs.py:start_trials`

Begins a run of each trial version at the endpoint serving its engine, and sends
nothing.

Stores each run's start record and entries in one transaction, which holds while the
gate confirms the endpoint with a request to it for each run.

Heads-up: the gate's `Refused` passes through.

* `versions: Sequence[int]`
* `concurrency: int | None = None`
* `order: Order | None = None`
* ∟`list[Running]`

Raises:
1. `NotFound`: `"no trial version {id} for {seen.person.login}"`
2. `ValueError`: `"a start runs one trial or more"`
3. `NotFound`: `"no case {missing[0]} for {seen.person.login}"`
4. `OverQuota`: `"a run holds at most {settings.ITEMS_PER_RUN} items, not {items}"` (through `_check_quota`)
5. `OverQuota`: `"{said}, as many as a day takes"` (through `_check_quota`)
6. `OverQuota`: `"{said}, and a day takes {settings.RUNS_PER_DAY}, not {len(runs)} more"` (through `_check_quota`)
7. `ValueError`: `"no endpoint here serves the engine of {name}: follow its handle"`

## `Bench.take`
`src/chatddx/bench/taking.py:take`

* `cases: Iterable[str]`
* `schema: str`
* `owner: str | None = None`
* ∟`Taken`

Raises:
1. `ValueError`: `"{schema} isn't a stored expectation schema"`
2. `NotFound`: `"no person {owner!r}"`

## `Bench.take_from`
`src/chatddx/bench/taking.py:take_from`

* `thread: int`
* `replace: bool = False`
* ∟`int`

Raises:
1. `ValueError`: `"expectation {thread} is yours already"`
2. `Conflict`: `"{seen.person.login} has their own expectation of {seen.title(case)} under {seen.title(schema)}, in thread {mine[0]}: replace it to take this one"`

## `Bench.type_case`
`src/chatddx/bench/cases.py:type_case`

* `text: str`
* `*`
* `language: str`
* `name: str | None = None`
* `source: str | None = None`
* ∟`Family`

Raises:
1. `ValueError`: `"a typed case holds text"`
2. `ValueError`: `"a typed case may not hold U+0000, which can't be stored"`
3. `ValueError`: `"a typed case holds at most {settings.TYPED_TEXT_LIMIT} characters, not {len(text)}"`
4. `ValueError`: `"a name can't be empty: none leaves the case unnamed"`
5. `ValueError`: `str(e)` (from `LookupError`)
6. `OverQuota`: `"{seen.person.login} has typed {typed} cases in the last day, as many as a day takes"`

## `bound`
`src/chatddx/bench/components.py:bound`

* `seen: Seen`
* `appendix: Appendix`
* ∟`Appendix`

Raises:
1. `ValueError`: `"an appendix is bound to the current vignette of a case you see"`

## `broken`
`src/chatddx/bench/handles.py:broken`

* `rows: Rows`
* `inventory: Inventory`
* ∟`list[str]`

## `Carried` `@dataclass(frozen=True)`
`src/chatddx/bench/model.py:Carried`

* `language: str | None`
* `cases: list[str]`
* `skeleton: Skeleton | None = None`
* `translated: bool = False`
* `refused: str | None = None`

## `check_expecting`
`src/chatddx/bench/seen.py:check_expecting`

* `seen: Seen`
* `expectation: Expectation`
* `thread: int | None`
* `then: str = "edit that one"`
* ∟`None`

Raises:
1. `ValueError`: `"{seen.person.login} has their own expectation of {seen.title(case)} under {seen.title(schema)}, in thread {others[0]}: {then}"`

## `check_kind`
`src/chatddx/bench/seen.py:check_kind`

* `seen: Seen`
* `thread: int`
* `word: str`
* `held: Component | TriedVariation`
* ∟`None`

Raises:
1. `ValueError`: `"{word} {thread} holds {kind} components, not {given}"`

## `check_scorer`
`src/chatddx/bench/seen.py:check_scorer`

* `scorer: Scorer`
* ∟`None`

Raises:
1. `ValueError`: `"; ".join(found)`

## `Checked` `@dataclass(frozen=True)`
`src/chatddx/bench/model.py:Checked`

* `digest: str`
* `findings: list[Finding]`

## `choices`
`src/chatddx/bench/seen.py:choices`

* `seen: Seen`
* `cases: Sequence[str]`
* `schema: str`
* ∟`dict[str, dict[int, str]]`

## `compiled`
`src/chatddx/bench/seen.py:compiled`

* `seen: Seen`
* `recipe: Recipe`
* `facts: ModelFacts | None | Literal["current"] = "current"`
* `into: str | None = None`
* ∟`tuple[Registry, Compilation]`

## `COMPILED_LANGUAGE`
`src/chatddx/bench/model.py:COMPILED_LANGUAGE`

`COMPILED_LANGUAGE = "a compiled configuration's language comes from its recipe"`

## `compiled_with`
`src/chatddx/bench/seen.py:compiled_with`

* `seen: Seen`
* `variation: TriedVariation`
* ∟`ModelFacts | None`

## `Conflict` `(ValueError)`
`src/chatddx/bench/errors.py:Conflict`

## `Endpoint` `@dataclass(frozen=True)`
`src/chatddx/bench/model.py:Endpoint`

* `name: str`
* `spec: EndpointSpec`
* `model: Model`

## `Endpoint.engine` `@property`
`src/chatddx/bench/model.py:Endpoint.engine`

* ∟`str`

## `Family` `@dataclass(frozen=True)`
`src/chatddx/bench/model.py:Family`

* `id: int`
* `about: About`
* `vignette: Vignette`
* `cases: tuple[str, ...]`

## `Family.case` `@property`
`src/chatddx/bench/model.py:Family.case`

* ∟`str`

## `Family.name` `@property`
`src/chatddx/bench/model.py:Family.name`

* ∟`str`

## `Graded` `@dataclass(frozen=True)`
`src/chatddx/bench/model.py:Graded`

* `name: str`
* `scorer: Scorer`
* `labels: dict[int, str]`
* `score: Score | None = None`
* `findings: list[Finding] = field(default_factory=list[Finding])`
* `refused: str | None = None`

## `Graded.label`
`src/chatddx/bench/model.py:Graded.label`

* `view: int`
* ∟`str`

## `Handle` `@dataclass(frozen=True)`
`src/chatddx/bench/model.py:Handle`

* `name: str`
* `thread: int`
* `weights: str`
* `deleted: bool = False`

## `judging`
`src/chatddx/bench/seen.py:judging`

* `seen: Seen`
* `judge: Judge`
* `registry: Registry`
* ∟`dict[str, str]`

## `keep_compilation`
`src/chatddx/bench/configurations.py:keep_compilation`

* `seen: Seen`
* `variation: TriedVariation`
* `into: str | None = None`
* ∟`str | None`

## `keep_language`
`src/chatddx/bench/components.py:keep_language`

* `seen: Seen`
* `digest: str`
* `language: str`
* ∟`None`

Raises:
1. `ValueError`: `"{seen.title(digest)} is in {held} already: a text's language is the same wherever it is held"`

## `kept`
`src/chatddx/bench/configurations.py:kept`

* `seen: Seen`
* `variation: TriedVariation`
* `thread: int | None`
* `name: str | None`
* `head: int | None = None`
* ∟`Written`

## `Kin` `@dataclass(frozen=True)`
`src/chatddx/bench/model.py:Kin`

* `edit: Edit`
* `about: About`
* `origin: int | None`
* `divergence: Divergence | None`
* `moved_on: bool`

## `KINDS`
`src/chatddx/bench/model.py:KINDS`

`KINDS: dict[str, tuple[str, ...]] = {…}`

## `LABELLED`
`src/chatddx/bench/model.py:LABELLED`

`LABELLED: tuple[Part, ...] = ("view", "resource")`

## `labels_of`
`src/chatddx/bench/seen.py:labels_of`

* `seen: Seen`
* `edit: Edit`
* ∟`dict[int, str]`

## `linted`
`src/chatddx/bench/seen.py:linted`

* `seen: Seen`
* `digest: str`
* ∟`list[Finding]`

## `missing`
`src/chatddx/bench/seen.py:missing`

* `seen: Seen`
* `variation: TriedVariation`
* `carried: Sequence[Carried]`
* ∟`list[Finding]`

Finds:
1. `translations.missing`: `refused` (through `_missing`)
2. `translations.missing`: `"{cases} in {carried.language}, and left out: {refused}"` (through `_missing`)

## `MODEL`
`src/chatddx/bench/model.py:MODEL`

`MODEL = "‹model›"`

## `Moved` `@dataclass(frozen=True)`
`src/chatddx/bench/model.py:Moved`

* `facts: Behind | None`
* `model: Behind | None`
* `about: str`
* `digest: str | None`
* `compilation: str | None`
* `refused: str | None`

## `NONE`
`src/chatddx/bench/seen.py:NONE`

`NONE = "none"`

## `NotFound` `(LookupError)`
`src/chatddx/bench/errors.py:NotFound`

## `OverQuota` `(ValueError)`
`src/chatddx/bench/errors.py:OverQuota`

## `picked`
`src/chatddx/bench/seen.py:picked`

* `seen: Seen`
* `cases: Sequence[str]`
* `schema: str`
* ∟`dict[str, str | None]`

Raises:
1. `Ambiguous`: `str(e)` (from `LookupError`)

## `PLACEHOLDERS`
`src/chatddx/bench/model.py:PLACEHOLDERS`

`PLACEHOLDERS: dict[SlotName, str] = {…}`

## `Proposed` `@dataclass(frozen=True)`
`src/chatddx/bench/model.py:Proposed`

* `divergence: Divergence`
* `proposal: Recipe | Component`
* `digest: str`
* `compilation: str | None`

## `Reach` `@dataclass(frozen=True)`
`src/chatddx/bench/model.py:Reach`

* `thread: int`
* `scorer: str`
* `view: int`
* `label: str`
* `offered: bool`
* `cases: int`
* `missing: list[Family]`
* `choosing: list[Family]`

## `Reach.have` `@property`
`src/chatddx/bench/model.py:Reach.have`

* ∟`int`

## `REFUSALS`
`src/chatddx/bench/runs.py:REFUSALS`

`REFUSALS = (LookupError, TypeError, ValueError, NotImplementedError, Refused)`

## `SAVED`
`src/chatddx/bench/model.py:SAVED`

`SAVED: dict[Kept, Literal['created', 'a new version', 'unchanged']] = {…}`

## `ScorerStarted` `@dataclass(frozen=True)`
`src/chatddx/bench/runs.py:ScorerStarted`

* `scorer: str`
* `name: str`
* `score: UUID`

## `scoring`
`src/chatddx/bench/seen.py:scoring`

* `seen: Seen`
* `run: RunStarted`
* `scorer: str`
* ∟`Scoring | None`

## `ScoringEvent`
`src/chatddx/bench/runs.py:ScoringEvent`

`type ScoringEvent = ScoreEvent | ScorerStarted`

## `Seen`
`src/chatddx/bench/seen.py:Seen`

* `conn: Connection`
* `person: Person`
* `inventory: Inventory`
* `store: Store`
* `catalog: Catalog`
* `rows: Rows`
* `people: People`

## `Seen.__init__`
`src/chatddx/bench/seen.py:Seen.__init__`

* `conn: Connection`
* `person: Person`
* `inventory: Inventory`

## `Seen.answers`
`src/chatddx/bench/seen.py:Seen.answers`

* `skeleton: Skeleton`
* ∟`str | None`

## `Seen.at`
`src/chatddx/bench/seen.py:Seen.at`

* `variation: TriedVariation`
* `endpoint: str | None = None`
* `model: str | None = None`
* ∟`Endpoint`

Raises:
1. `ValueError`: `"endpoint {endpoint!r} serves another model than {variation.label}'s, {self.title(weights)}"`
2. `ValueError`: `"{variation.label} names no model: name the one to run it under"`
3. `ValueError`: `"{variation.label} runs under its model's handle: set its model instead"`
4. `ValueError`: `"{variation.label}'s model is behind {handle.name}, which holds other weights now: follow it first"`

## `Seen.case_titled`
`src/chatddx/bench/seen.py:Seen.case_titled`

* `title: str`
* ∟`tuple[Family, str]`

Raises:
1. `NotFound`: `"no appendix {', '.join(missing)} of {family.name}"`
2. `NotFound`: `"no case {title} for {self.person.login}"`

## `Seen.cleanup`
`src/chatddx/bench/seen.py:Seen.cleanup`

* `cases: Sequence[str]`
* ∟`tuple[CleanupOp, ...]`

## `Seen.described`
`src/chatddx/bench/seen.py:Seen.described`

* `run: RunStarted`
* ∟`str`

## `Seen.endpoint`
`src/chatddx/bench/seen.py:Seen.endpoint`

* `name: str`
* ∟`Endpoint`

Raises:
1. `NotFound`: `str(e)` (from `LookupError`)
2. `NotFound`: `"endpoint {name!r} serves engine {short(spec.engine)}, which isn't in the store: load its World with init-data"`

## `Seen.expectation`
`src/chatddx/bench/seen.py:Seen.expectation`

* `case: str`
* `schema: str`
* ∟`Expectation | None`

## `Seen.expectation_schemas`
`src/chatddx/bench/seen.py:Seen.expectation_schemas`

* `case: str`
* ∟`list[str]`

## `Seen.facts` `@property`
`src/chatddx/bench/seen.py:Seen.facts`

* ∟`Facts`

## `Seen.families`
`src/chatddx/bench/seen.py:Seen.families`

* `tags: Iterable[str] = ()`
* `*`
* `deleted: bool = False`
* ∟`list[Family]`

## `Seen.family`
`src/chatddx/bench/seen.py:Seen.family`

* `found: int | str`
* `*`
* `deleted: bool = False`
* ∟`Family`

Raises:
1. `NotFound`: `"no {word} {name!r} for {self.person.login}"` (through `Seen._named`)
2. `Ambiguous`: `"{word} {name!r} names {len(several)}; name one as OWNER/NAME"` (through `Seen._named`)
3. `NotFound`: `"no case {found} for {self.person.login}"`

## `Seen.findings`
`src/chatddx/bench/seen.py:Seen.findings`

* `variation: TriedVariation`
* `engine: str`
* `seed: int`
* `carried: Sequence[Carried] | None = None`
* ∟`list[Finding]`

## `Seen.handle`
`src/chatddx/bench/seen.py:Seen.handle`

* `weights: str`
* ∟`Handle`

Raises:
1. `RuntimeError`: `"{short(weights)} is held by {len(held)} model threads, not one: fix boot-check src/chatddx/bench/handles.py:broken"`

## `Seen.handle_named`
`src/chatddx/bench/seen.py:Seen.handle_named`

* `name: str`
* ∟`Handle`

## `Seen.holder`
`src/chatddx/bench/seen.py:Seen.holder`

* `digest: str`
* `recipe: Recipe | None = None`
* ∟`tuple[Edit, About] | None`

## `Seen.judged`
`src/chatddx/bench/seen.py:Seen.judged`

* `judge: Judge`
* ∟`Endpoint`

Raises:
1. `ValueError`: `"{self.title(judge.digest)}: its model is behind {handle.name}, which holds other weights now: follow it first"`

## `Seen.labels`
`src/chatddx/bench/seen.py:Seen.labels`

* `scorer: str`
* ∟`dict[int, str]`

## `Seen.landed`
`src/chatddx/bench/seen.py:Seen.landed`

* `variation: TriedVariation`
* ∟`dict[str, Landing]`

## `Seen.languages`
`src/chatddx/bench/seen.py:Seen.languages`

* `variation: TriedVariation`
* `cases: Sequence[str]`
* ∟`list[Carried]`

## `Seen.latest`
`src/chatddx/bench/seen.py:Seen.latest`

* `handle: Handle`
* ∟`str | None`

## `Seen.login`
`src/chatddx/bench/seen.py:Seen.login`

* `person: int | None`
* ∟`str`

## `Seen.outstanding`
`src/chatddx/bench/seen.py:Seen.outstanding`

* ∟`list[tuple[RunStarted, list[str]]]`

## `Seen.reach`
`src/chatddx/bench/seen.py:Seen.reach`

* `variation: TriedVariation`
* `families: list[Family]`
* ∟`list[Reach]`

## `Seen.request`
`src/chatddx/bench/seen.py:Seen.request`

* `variation: TriedVariation`
* `engine: str | None`
* `seed: int`
* ∟`dict[str, JsonValue]`

## `Seen.run`
`src/chatddx/bench/seen.py:Seen.run`

* `found: UUID | str | None = None`
* ∟`RunStarted`

Raises:
1. `NotFound`: `"no run {found} of yours"`
2. `NotFound`: `"{self.person.login} has no runs"`
3. `NotFound`: `"no run of yours starts with {found!r}"`
4. `Ambiguous`: `"{len(several)} runs of yours start with {found!r}"`

## `Seen.runs`
`src/chatddx/bench/seen.py:Seen.runs`

* `*`
* `reaching: str | None = None`
* `scored_by: str | None = None`
* `started_with: UUID | None = None`
* ∟`list[RunStarted]`

## `Seen.score_of`
`src/chatddx/bench/seen.py:Seen.score_of`

* `run: RunStarted`
* `score: UUID`
* ∟`Graded`

Raises:
1. `NotFound`: `"no score {score} of run {run.run}"`

## `Seen.scorers`
`src/chatddx/bench/seen.py:Seen.scorers`

* `run: RunStarted | None = None`
* ∟`list[tuple[Edit, About, Scorer]]`

## `Seen.scores_of`
`src/chatddx/bench/seen.py:Seen.scores_of`

* `run: RunStarted`
* `every: bool = False`
* ∟`list[Graded]`

## `Seen.served`
`src/chatddx/bench/seen.py:Seen.served`

* `handle: Handle`
* ∟`Endpoint`

Raises:
1. `ValueError`: `"model {handle.name} is deleted: pick another"`
2. `ValueError`: `"no endpoint here serves model {handle.name}: pick another"`

## `Seen.shared`
`src/chatddx/bench/seen.py:Seen.shared`

* `case: str`
* `schema: str`
* ∟`list[tuple[Edit, About]]`

## `Seen.skeleton`
`src/chatddx/bench/seen.py:Seen.skeleton`

* `variation: TriedVariation`
* `into: str | None = None`
* ∟`Skeleton`

Raises:
1. `StructuralError`: `"{variation.label} has no translations into {into}"`

## `Seen.thread`
`src/chatddx/bench/seen.py:Seen.thread`

* `found: int | str`
* `word: str | None = None`
* `*`
* `deleted: bool = False`
* ∟`tuple[Edit, About]`

Raises:
1. `NotFound`: `"no {word} {name!r} for {self.person.login}"` (through `Seen._named_thread`)
2. `Ambiguous`: `"{word} {name!r} names {len(several)}; name one as OWNER/NAME"` (through `Seen._named_thread`)
3. `NotFound`: `"no {what} {name!r} for {self.person.login}"` (through `Seen._named_thread`)
4. `Ambiguous`: `"{what} {name!r} names a {' and a '.join(several)}"` (through `Seen._named_thread`)
5. `NotFound`: `"no {word or 'thread'} {found} for {self.person.login}"`

## `Seen.threads`
`src/chatddx/bench/seen.py:Seen.threads`

* `word: str`
* `*`
* `deleted: bool = False`
* `purpose: Purpose | None = None`
* `answering: str | None = None`
* ∟`list[tuple[Edit, About]]`

Raises:
1. `ValueError`: `"only a configuration has a purpose and an answer: {word}"`

## `Seen.title`
`src/chatddx/bench/seen.py:Seen.title`

* `digest: str`
* ∟`str`

## `Seen.under`
`src/chatddx/bench/seen.py:Seen.under`

* `engine: str`
* ∟`tuple[Handle | None, bool]`

## `Seen.unscored`
`src/chatddx/bench/seen.py:Seen.unscored`

* `run: RunStarted`
* ∟`list[str]`

## `Seen.variation`
`src/chatddx/bench/seen.py:Seen.variation`

* `configuration: int | str`
* `parts: Mapping[str, str | None] | None = None`
* `head: int | None = None`
* ∟`TriedVariation`

Raises:
1. `NotFound`: `"no edit {head} of configuration {edit.thread}"`
2. `ValueError`: `"no part {part!r}: the parts are {', '.join(RECIPE_PARTS)}"`
3. `ValueError`: `"{digest} isn't a stored {what}"`

## `Started` `@dataclass(frozen=True)`
`src/chatddx/bench/model.py:Started`

* `runs: list[tuple[Carried, Running]]`
* `left_out: list[Carried]`

## `Started.first` `@property`
`src/chatddx/bench/model.py:Started.first`

* ∟`Running`

## `Taken` `@dataclass(frozen=True)`
`src/chatddx/bench/model.py:Taken`

* `taken: dict[str, int]`
* `kept: dict[str, int]`
* `choosing: dict[str, list[int]]`
* `missing: list[str]`

## `trial`
`src/chatddx/bench/seen.py:trial`

* `seen: Seen`
* `skeleton: Skeleton`
* `engine: str`
* `cases: list[str]`
* `seeds: Sequence[int]`
* `cleanup: tuple[CleanupOp, ...] = ()`
* ∟`tuple[Registry, Trial]`

## `TriedVariation` `@dataclass(frozen=True)`
`src/chatddx/bench/variation.py:TriedVariation`

* `configuration: Edit`
* `name: str`
* `recipe: Recipe | None = None`
* `parts: Mapping[str, tuple[str | None, str]] = field(…)`

## `TriedVariation.held`
`src/chatddx/bench/variation.py:TriedVariation.held`

* `part: str`
* ∟`str | None`

## `TriedVariation.label` `@property`
`src/chatddx/bench/variation.py:TriedVariation.label`

* ∟`str`

## `TriedVariation.set`
`src/chatddx/bench/variation.py:TriedVariation.set`

* `part: str`
* `digest: str | None`
* `name: str`
* ∟`"TriedVariation"`

Raises:
1. `ValueError`: `"{self.name} has no recipe to set its {part} in"`
2. `ValueError`: `"a configuration always holds its {part}"`

## `TriedVariation.varied` `@property`
`src/chatddx/bench/variation.py:TriedVariation.varied`

* ∟`Recipe | None`

## `WITH`
`src/chatddx/bench/seen.py:WITH`

`WITH = re.compile(r"^(?P<family>.+?) with (?P<appendices>.+)$")`

## `word_of`
`src/chatddx/bench/model.py:word_of`

* `kind: str | None`
* ∟`str`

## `worded`
`src/chatddx/bench/seen.py:worded`

* `seen: Seen`
* `thread: int`
* ∟`tuple[Edit, About, str]`

## `WRITTEN`
`src/chatddx/bench/model.py:WRITTEN`

`WRITTEN: frozenset[str] = frozenset(…)`

## `Written` `@dataclass(frozen=True)`
`src/chatddx/bench/model.py:Written`

* `edit: Edit`
* `what: Literal["created", "a new version", "unchanged"]`
* `findings: list[Finding]`
* `cases: dict[str, str] = field(default_factory=dict)`

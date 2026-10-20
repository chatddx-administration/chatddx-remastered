# `chatddx.store`

Written by `chatddx reference` from `src/chatddx/store/`; how to read it is in [docs/reference/README.md](README.md).

## Assembler
`src/chatddx/store/notify.py:Assembler`

## Assembler.__init__
`src/chatddx/store/notify.py:Assembler.__init__`

## Assembler.message
`src/chatddx/store/notify.py:Assembler.message`

* `channel: str`
* `pid: int`
* `payload: str`
* ∟`Message | None`

## Catalog
`src/chatddx/store/catalog.py:Catalog`

## Catalog.__init__
`src/chatddx/store/catalog.py:Catalog.__init__`

* `conn: Connection`

## Catalog.adopt
`src/chatddx/store/catalog.py:Catalog.adopt`

* `case: str`
* `by: int`
* `*`
* `owner: int | None = None`
* `by_content: bool = True`
* ∟`int`

## Catalog.create
`src/chatddx/store/catalog.py:Catalog.create`

* `digest: str`
* `by: int`
* `*`
* `compilation: str | None = None`
* `forked_from: int | None = None`
* `name: str | None = None`
* `owner: int | None = None`
* `labels: Labels | None = None`
* ∟`Edit`

## Catalog.edit
`src/chatddx/store/catalog.py:Catalog.edit`

* `thread: int`
* `digest: str`
* `by: int`
* `*`
* `compilation: str | None = None`
* `based_on: int | None = None`
* `head: int | None = None`
* `labels: Labels | None = None`
* ∟`Edit`

## Catalog.keep
`src/chatddx/store/catalog.py:Catalog.keep`

* `digest: str`
* `by: int`
* `thread: int | None`
* `*`
* `name: str | None = None`
* `compilation: str | None = None`
* `forked_from: int | None = None`
* `head: int | None = None`
* `labels: Labels | None = None`
* ∟`tuple[Edit, Kept]`

## Catalog.language
`src/chatddx/store/catalog.py:Catalog.language`

* `digest: str`
* `value: str`
* `by: int`
* ∟`None`

## Catalog.note
`src/chatddx/store/catalog.py:Catalog.note`

* `subject: Subject`
* `entry: Entry`
* `by: int`
* ∟`None`

## Catalog.repair
`src/chatddx/store/catalog.py:Catalog.repair`

* `family: int`
* `by: int`
* `*`
* `id: str | None = None`
* `fingerprint: Fingerprint | None = None`
* ∟`RepairPlan`

## channel
`src/chatddx/store/notify.py:channel`

* `run: UUID`
* ∟`str`

## Connection
`src/chatddx/store/store.py:Connection`

* `Connection = psycopg.Connection[TupleRow]`

## ENDED
`src/chatddx/store/queue.py:ENDED`

* `ENDED: tuple[Status, ...] = ("finished", "stopped", "failed")`

## Events `@dataclass(frozen=True)`
`src/chatddx/store/notify.py:Events`

* `said: Said`

## fetch_vignette
`src/chatddx/store/texts.py:fetch_vignette`

* `conn: Connection`
* `inventory: Inventory`
* `vignette: Vignette`
* ∟`bytes`

## Held `@dataclass(frozen=True)`
`src/chatddx/store/queue.py:Held`

* `job: int`
* `halt: bool`
* `paused: bool`

## JOB
`src/chatddx/store/notify.py:JOB`

* `JOB = "job "`

## Job `@dataclass(frozen=True)`
`src/chatddx/store/queue.py:Job`

* `id: int`
* `owner: int`
* `run: UUID`
* `endpoint: str`
* `slots: int`
* `score: bool`
* `scorers: tuple[str, ...] | None`
* `scored: tuple[str, ...]`
* `status: Status`
* `why: str | None`
* `halt: bool`
* `worker: UUID | None`
* `queued: datetime`
* `claimed: datetime | None`
* `beat: datetime | None`
* `ended: datetime | None`

## JobChanged `@dataclass(frozen=True)`
`src/chatddx/store/notify.py:JobChanged`

* `status: str`

## Kept
`src/chatddx/store/catalog.py:Kept`

* `Kept = Literal["created", "edited", "unchanged"]`

## LIMIT
`src/chatddx/store/notify.py:LIMIT`

* `LIMIT = 7900`

## listen
`src/chatddx/store/notify.py:listen`

* `conn: psycopg.Connection[TupleRow]`
* `*channels: str`
* ∟`None`

## Message
`src/chatddx/store/notify.py:Message`

* `type Message = Rows | JobChanged | Events`

## migrate
`src/chatddx/store/migrate.py:migrate`

* `conn: psycopg.Connection`
* `tier: int = TOP_TIER`
* ∟`list[str]`

## Migration `@dataclass(frozen=True)`
`src/chatddx/store/migrate.py:Migration`

* `name: str`
* `tier: int`
* `path: Path`

## pending
`src/chatddx/store/migrate.py:pending`

* `conn: psycopg.Connection`
* `tier: int = TOP_TIER`
* ∟`list[Migration]`

## People
`src/chatddx/store/people.py:People`

## People.__init__
`src/chatddx/store/people.py:People.__init__`

* `conn: Connection`

## People.add
`src/chatddx/store/people.py:People.add`

* `login: str`
* `name: str`
* `roles: Iterable[Role] = ()`
* ∟`Person`

## People.authenticate
`src/chatddx/store/people.py:People.authenticate`

* `login: str`
* `password: str`
* ∟`Person | None`

## People.close_session
`src/chatddx/store/people.py:People.close_session`

* `token: str`
* ∟`None`

## People.find
`src/chatddx/store/people.py:People.find`

* `login: str`
* ∟`Person | None`

## People.get
`src/chatddx/store/people.py:People.get`

* `id: int`
* ∟`Person`

Raises:
1. `LookupError`: "no person with id {id}"

## People.open_session
`src/chatddx/store/people.py:People.open_session`

* `id: int`
* `ttl: timedelta = settings.SESSION_TTL`
* ∟`str`

## People.session
`src/chatddx/store/people.py:People.session`

* `token: str`
* ∟`Person | None`

## People.set_password
`src/chatddx/store/people.py:People.set_password`

* `id: int`
* `password: str`
* ∟`None`

## People.update
`src/chatddx/store/people.py:People.update`

* `id: int`
* `*`
* `name: str | None = None`
* `roles: Iterable[Role] | None = None`
* `active: bool | None = None`
* ∟`Person`

Raises:
1. `LookupError`: "no person with id {id}"

## Placed `@dataclass(frozen=True)`
`src/chatddx/store/queue.py:Placed`

* `job: Job`
* `ahead: int | None`

## Queue
`src/chatddx/store/queue.py:Queue`

## Queue.__init__
`src/chatddx/store/queue.py:Queue.__init__`

* `conn: Connection`

## Queue.beat
`src/chatddx/store/queue.py:Queue.beat`

* `worker: UUID`
* `jobs: Collection[int]`
* ∟`list[Held]`

## Queue.claim
`src/chatddx/store/queue.py:Queue.claim`

* `worker: UUID`
```
SIGN-OFF: REPLACE
replace the line below with these
---
* `capacity: Mapping[str, int]`
```
* `max_jobs: Mapping[str, int]`
* `lost: timedelta`
* ∟`Job | None`

## Queue.end
`src/chatddx/store/queue.py:Queue.end`

* `job: int`
* `worker: UUID`
* `status: Status`
* `why: str | None = None`
* ∟`bool`

Raises:
1. `ValueError`: "a job ends {', '.join(ENDED)}, not {status}"

## Queue.enlist
`src/chatddx/store/queue.py:Queue.enlist`

* `worker: UUID`
* ∟`None`

## Queue.halt
`src/chatddx/store/queue.py:Queue.halt`

* `run: UUID`
* ∟`Job`

Raises:
1. `LookupError`: "run {run} has nothing under way"

## Queue.open
`src/chatddx/store/queue.py:Queue.open`

* `run: UUID`
* ∟`Job | None`

## Queue.pause
`src/chatddx/store/queue.py:Queue.pause`

* `owner: int`
* `paused: bool = True`
* ∟`None`

## Queue.placed
`src/chatddx/store/queue.py:Queue.placed`

* `runs: Collection[UUID]`
* ∟`dict[UUID, Placed]`

## Queue.put
`src/chatddx/store/queue.py:Queue.put`

* `owner: int`
* `run: UUID`
* `endpoint: str`
* `slots: int`
* `score: bool`
* `scorers: Collection[str] | None = None`
* ∟`Job`

Raises:
1. `UnderWay`: "run {run} has something under way"

## Queue.requeue
`src/chatddx/store/queue.py:Queue.requeue`

* `job: int`
* `worker: UUID`
* `why: str | None = None`
* ∟`bool`

## Queue.scored
`src/chatddx/store/queue.py:Queue.scored`

* `job: int`
* `worker: UUID`
* `scorer: str`
* ∟`bool`

## Queue.standing
`src/chatddx/store/queue.py:Queue.standing`

* `owner: int`
* `lost: timedelta`
* ∟`Standing`

## Queue.stop
`src/chatddx/store/queue.py:Queue.stop`

* `owner: int`
* `now: bool = False`
* ∟`Stopped`

## ROWS
`src/chatddx/store/notify.py:ROWS`

* `ROWS = "rows"`

## catalog.Rows
`src/chatddx/store/catalog.py:Rows`

## notify.Rows `@dataclass(frozen=True)`
`src/chatddx/store/notify.py:Rows`

## catalog.Rows.__init__
`src/chatddx/store/catalog.py:Rows.__init__`

* `conn: Connection`

## catalog.Rows.bindings
`src/chatddx/store/catalog.py:Rows.bindings`

* `families: Collection[int]`
* ∟`list[Binding]`

## catalog.Rows.bindings_in
`src/chatddx/store/catalog.py:Rows.bindings_in`

* `source: str`
* ∟`list[Binding]`

## catalog.Rows.bindings_sharing
`src/chatddx/store/catalog.py:Rows.bindings_sharing`

* `vignette: Vignette`
* ∟`list[Binding]`

## catalog.Rows.bound_to
`src/chatddx/store/catalog.py:Rows.bound_to`

* `vignettes: Collection[Vignette]`
* `kind: str`
* ∟`list[tuple[str, Vignette]]`

## catalog.Rows.compilations
`src/chatddx/store/catalog.py:Rows.compilations`

* `skeleton: str`
* ∟`list[Compilation]`

## catalog.Rows.components
`src/chatddx/store/catalog.py:Rows.components`

* `digests: Collection[str]`
* ∟`list[tuple[str, Component]]`

## catalog.Rows.edit
`src/chatddx/store/catalog.py:Rows.edit`

* `id: int`
* ∟`Edit | None`

## catalog.Rows.edits
`src/chatddx/store/catalog.py:Rows.edits`

* `threads: Collection[int]`
* ∟`list[Edit]`

## catalog.Rows.edits_holding
`src/chatddx/store/catalog.py:Rows.edits_holding`

* `digests: Collection[str]`
* ∟`list[Edit]`

## catalog.Rows.entries
`src/chatddx/store/catalog.py:Rows.entries`

* `subjects: Collection[Subject]`
* ∟`list[tuple[Subject, Entry, int]]`

## catalog.Rows.expectations
`src/chatddx/store/catalog.py:Rows.expectations`

* `cases: Collection[str]`
* ∟`list[str]`

## catalog.Rows.families
`src/chatddx/store/catalog.py:Rows.families`

* ∟`list[int]`

## catalog.Rows.get
`src/chatddx/store/catalog.py:Rows.get`

* `digest: str`
* ∟`Component`

## catalog.Rows.involving
`src/chatddx/store/catalog.py:Rows.involving`

* `person: int`
* ∟`list[Subject]`

## catalog.Rows.kind
`src/chatddx/store/catalog.py:Rows.kind`

* `digest: str`
* ∟`str | None`

## catalog.Rows.labels
`src/chatddx/store/catalog.py:Rows.labels`

* `edits: Collection[int]`
* ∟`list[tuple[int, Part, int, str]]`

## catalog.Rows.languages
`src/chatddx/store/catalog.py:Rows.languages`

* `digests: Collection[str]`
* ∟`list[tuple[str, str]]`

## catalog.Rows.runs_started
`src/chatddx/store/catalog.py:Rows.runs_started`

* `person: int`
* `since: datetime`
* ∟`int`

## catalog.Rows.thread
`src/chatddx/store/catalog.py:Rows.thread`

* `id: int`
* ∟`Thread | None`

## catalog.Rows.threads
`src/chatddx/store/catalog.py:Rows.threads`

* `kind: str`
* ∟`list[Thread]`

## catalog.Rows.threads_forked_from
`src/chatddx/store/catalog.py:Rows.threads_forked_from`

* `edits: Collection[int]`
* ∟`list[Thread]`

## Said
`src/chatddx/store/notify.py:Said`

* `type Said = list[tuple[str, JsonValue]]`

## Standing `@dataclass(frozen=True)`
`src/chatddx/store/queue.py:Standing`

* `paused: bool`
* `queued: int`
* `under_way: int`
* `workers: int`

## Status
`src/chatddx/store/queue.py:Status`

* `Status = Literal["queued", "under way", "finished", "stopped", "failed"]`

## STATUSES
`src/chatddx/store/queue.py:STATUSES`

* `STATUSES: tuple[Status, ...] = get_args(Status)`

## Stopped `@dataclass(frozen=True)`
`src/chatddx/store/queue.py:Stopped`

* `taken_out: tuple[UUID, ...]`
* `halting: tuple[UUID, ...]`

## Store
`src/chatddx/store/store.py:Store`

## Store.__init__
`src/chatddx/store/store.py:Store.__init__`

* `conn: Connection`

## Store.add
`src/chatddx/store/store.py:Store.add`

* `registry: Registry`
* `roots: Iterable[str]`
* ∟`list[str]`

## Store.append
`src/chatddx/store/store.py:Store.append`

* `*records: Record`
* ∟`None`

Raises:
1. `TypeError`: "no table for {type(record).__name__}"

## Store.compilations
`src/chatddx/store/store.py:Store.compilations`

* `skeleton: str`
* ∟`list[Compilation]`

## Store.finished
`src/chatddx/store/store.py:Store.finished`

* `runs: Collection[UUID]`
* ∟`set[UUID]`

## Store.get
`src/chatddx/store/store.py:Store.get`

* `digest: str`
* ∟`Component`

Raises:
1. `StructuralError`: "{digest} is not in the store"

## Store.load
`src/chatddx/store/store.py:Store.load`

* `roots: Iterable[str]`
* ∟`Registry`

Raises:
1. `StructuralError`: "not in the store: {missing}"

## Store.reaching
`src/chatddx/store/store.py:Store.reaching`

* `digest: str`
* `kind: str`
* ∟`list[str]`

## Store.rows_of
`src/chatddx/store/store.py:Store.rows_of`

* `run: UUID`
* `after: int = 0`
* ∟`list[Written]`

## Store.run
`src/chatddx/store/store.py:Store.run`

* `run: UUID`
* ∟`Run`

Raises:
1. `LookupError`: "{log} {key} is not in the store" (through `Store._stages`)
2. `StructuralError`: "{log} {key} has no started row" (through `Store._stages`)

## Store.score
`src/chatddx/store/store.py:Store.score`

* `score: UUID`
* ∟`Score`

Raises:
1. `LookupError`: "{log} {key} is not in the store" (through `Store._stages`)
2. `StructuralError`: "{log} {key} has no started row" (through `Store._stages`)

## Store.scores_of
`src/chatddx/store/store.py:Store.scores_of`

* `run: UUID`
* ∟`list[ScoreStarted]`

## Store.started
`src/chatddx/store/store.py:Store.started`

* `runs: Collection[UUID]`
* ∟`list[RunStarted]`

## TAKEN_OUT
`src/chatddx/store/queue.py:TAKEN_OUT`

* `TAKEN_OUT = "taken out of the queue"`

## tell
`src/chatddx/store/notify.py:tell`

* `conn: psycopg.Connection[TupleRow]`
* `run: UUID`
* `said: Iterable[tuple[str, JsonValue]]`
* ∟`None`

## Texts
`src/chatddx/store/texts.py:Texts`

## Texts.__init__
`src/chatddx/store/texts.py:Texts.__init__`

* `conn: Connection`

## Texts.add
`src/chatddx/store/texts.py:Texts.add`

* `source: str`
* `text: str`
* `by: int`
* ∟`str`

## Texts.get
`src/chatddx/store/texts.py:Texts.get`

* `source: str`
* `id: str`
* ∟`bytes`

Raises:
1. `LookupError`: "no case {id!r} in source {source!r}"

## Texts.typed_since
`src/chatddx/store/texts.py:Texts.typed_since`

* `by: int`
* `since: datetime`
* ∟`int`

## TOP_TIER
`src/chatddx/store/migrate.py:TOP_TIER`

* `TOP_TIER = 2`

## UnderWay `(ValueError)`
`src/chatddx/store/queue.py:UnderWay`

## unlisten
`src/chatddx/store/notify.py:unlisten`

* `conn: psycopg.Connection[TupleRow]`
* `*channels: str`
* ∟`None`

## WORKERS
`src/chatddx/store/notify.py:WORKERS`

* `WORKERS = "worker"`

## Written
`src/chatddx/store/store.py:Written`

* `type Written = tuple[int, Record]`

# API package

A candidate for `docs/api-api.md`, beside `agents/wip-api.md`, the candidate for `docs/api.md`; below, those two
names mean these two files until they move.

Reference for the `chatddx.api` package. It was written from `src/chatddx/api/*` and docs/api.md. What the API is and
why it is shaped this way is in docs/api.md. The HTTP interface itself, its paths, parameters, bodies and statuses,
is the OpenAPI document the app serves at `/api/openapi.json`, with pages at `/api/docs`, and isn't repeated here;
this file says how the package builds it: what each name does, accepts, returns and raises. The types it passes
through are the bench's (agents/wip-bench-api.md), the runner's (docs/runner-api.md), and those in
docs/catalog-api.md, docs/ledger-api.md, docs/store-api.md, docs/inventory-api.md and docs/facts-api.md.

Paths are relative to `src/chatddx/api/` unless they start with `src/`, `docs/` or `agents/`.

## Contents
- [Package](#package)
- [Conventions](#conventions)
- [app.py](#apppy): `app`, `STATUSES`
- [state.py](#statepy): `AppState`, `state`, `connection`
- [people.py](#peoplepy): sessions, the same-origin check, the bench per request
- [schemas.py](#schemaspy): the request and response models, and `EVENTS`
- [threads.py](#threadspy): threads, variations, forks and edits
- [families.py](#familiespy): families, vignettes and tags
- [world.py](#worldpy): endpoints, models, components and the scoring code shipped
- [runs.py](#runspy): starting a run, its thread and its stream; reading runs
- [events.py](#eventspy): the runner's events as the stream's
- [The command](#the-command)
- [Tests](#tests)
- [Beyond docs/api.md](#beyond-docsapimd)

## Package

`chatddx.api` re-exports nothing; its modules are imported by path. `src/chatddx/cli.py` imports `app.py:app`.

| Module | Builds on |
| --- | --- |
| `state.py` | psycopg, `chatddx.{facts,inventory,store}` |
| `schemas.py` | `chatddx.bench`, `chatddx.catalog`, `chatddx.factors.base`, `chatddx.identity` |
| `people.py` | `schemas.py`, `state.py`, `chatddx.bench`, `chatddx.core.settings`, `chatddx.identity`, `chatddx.store` |
| `threads.py` | `schemas.py`, `people.py`, `chatddx.bench`, `chatddx.catalog`, `chatddx.factors.{base,request,trial}`, `chatddx.store` |
| `families.py` | `schemas.py`, `people.py`, `threads.py`, `chatddx.bench`, `chatddx.factors.{base,cases}`, `chatddx.store` |
| `world.py` | `schemas.py`, `people.py`, `chatddx.bench`, `chatddx.inventory`, `chatddx.scorers.{scorer,shipped}`, `chatddx.store.catalog` |
| `events.py` | `schemas.py`, `chatddx.bench`, `chatddx.factors.request`, `chatddx.ledger`, `chatddx.runner.run`, `chatddx.scorers.aggregate` |
| `runs.py` | `schemas.py`, `events.py`, `people.py`, `state.py`, `threads.py`, `chatddx.bench`, `chatddx.factors.{base,request,trial}`, `chatddx.identity`, `chatddx.ledger`, `chatddx.runner.run` |
| `app.py` | every module above but `events.py`, `chatddx.bench`, `chatddx.facts`, `chatddx.inventory`, `chatddx.runner.gate` |

The modules that serve build on FastAPI; `schemas.py` and `events.py` need only pydantic, and `app.py` its JSON
schemas too. The package holds no SQL: it reads through the bench, the store's `Store` and `Rows`, and `People`.

## Conventions

**Handlers.** Every route is a plain `def`, which FastAPI runs on its thread pool, but `runs.py:start`, which is
`async`, so that it can stream and hear its client go away; it does its blocking work through `run_in_threadpool`.

**A bench per request.** `people.py:bench`, as `BenchDep`, builds a `Bench` for the person the request acts for, on the
request's connection (`state.py:connection`), in autocommit mode and closed when the request is done with it. A run gets
a connection of its own (`runs.py:_start`).

**Who it depends on.** What depends on the person is asked of the bench. What doesn't is the same for everyone: the
endpoints and models (`world.py`), a component by its digest, and the scoring code the running chatddx ships, read
from the World, the facts and the store through the bench's reads that take no person (`Bench.endpoint`, `title`,
`model`, `get`), or straight (`Rows`, `chatddx.scorers.shipped.SCORERS`).

**People by login.** Owners, collaborators and an edit's author are given as logins (`Bench.login`); a subject with
no owner has `None` (`threads.py:login`).

**Errors.** `app.py:STATUSES` maps the bench's `NotFound`, `Ambiguous`, `Conflict`, `MovedOn` and `OverQuota`, and
the gate's `Refused`, wherever they are raised, with the message as the detail. What else a route means it raises as
an `HTTPException` where it catches it: `threads.py:refused`, around every write, every variation built and a
proposal, turns a `ValueError` into a 422, letting a `Conflict`, a `MovedOn` and an `OverQuota` through, and a route
turns a `LookupError` about what its query or body names into a 422. Nothing maps `ValueError` or `LookupError`
wholesale, so one a route doesn't catch is a 500.

**Models.** Every request and response model derives from `schemas.py:_Schema`: frozen, `extra="forbid"`. A body
field a model doesn't name is a 422, and so is a query parameter where the query is a model (`Varying`); elsewhere a
query parameter a route doesn't name is ignored. Components,
recipes, facts, calls, tool runs and fingerprints are given as the JSON they dump to, not as models of their own.

**Case-derived places.** `families.py:vignette`, `runs.py:items` and a run's stream are the only routes that give
case-derived content.

## app.py

### `STATUSES: dict[type[Exception], int]`
`NotFound` 404, `Ambiguous` 409, `Conflict` 409, `MovedOn` 409, `OverQuota` 429, `Refused` 422. Each is answered
`{"detail": str(error)}`.

### `app(inventory: Inventory, facts: Facts, conninfo: str) -> FastAPI`
A FastAPI app titled `chatddx`, versioned as the installed package is, with its OpenAPI document at
`/api/openapi.json`, its pages at `/api/docs` and no ReDoc. `state.chatddx` holds an `AppState` of what it was made
with. The routers of `people.py`, `threads.py`, `families.py`, `world.py` and `runs.py` are mounted under `/api`, the
handlers of `STATUSES` are added, and `openapi` is `_with_events`.

### `_with_events(made: FastAPI) -> Callable[[], dict[str, Any]]`
FastAPI's own `openapi`, with the model of each event in `schemas.py:EVENTS` added to `components.schemas`, as
pydantic's `models_json_schema` gives them in serialization mode, with references as `#/components/schemas/{model}`.
They are added on every call, to the document FastAPI keeps.

## state.py

### `class AppState`
A frozen dataclass of what the app is made with, loaded once: `conninfo: str`, `inventory: Inventory`,
`facts: Facts`.

#### `connect() -> Connection`
A new connection to `conninfo` in autocommit mode, as the runner needs.

### `state(request: Request) -> AppState`
The app's `AppState`.

### `connection(request: Request) -> Iterator[Connection]`
A dependency: a connection for the request, closed when the request is done with it.

## people.py

| Name | Value |
| --- | --- |
| `COOKIE` | `"__Host-chatddx-session"`: the prefix has a browser keep the cookie to this host, over HTTPS, for every path. |
| `SAFE` | `GET`, `HEAD` and `OPTIONS`: the methods `same_origin` lets through. |
| `ConnDep` | `Annotated[Connection, Depends(connection)]`. |
| `BenchDep` | `Annotated[Bench, Depends(bench)]`. |

`_bearer` (`HTTPBearer`) and `_cookie` (`APIKeyCookie`) refuse nothing themselves (`auto_error=False`), and put both
ways of signing in among the OpenAPI document's security schemes.

### `class Session`
A frozen dataclass: `person: Person`, `token: str`.

### `_unsigned(detail: str = "sign in first") -> HTTPException`
A 401 with `detail`, and `WWW-Authenticate: Bearer`.

### `same_origin(request: Request) -> None`
Lets a method in `SAFE` through. Otherwise, where the request has `Sec-Fetch-Site`, it must be `same-origin` or
`none`; else, where it has `Origin`, its host and port must be the request's `Host`; with neither, it passes. Raises
`HTTPException(403, "a browser's request must come from this site's pages")`.

### `session(request, conn, bearer, cookie) -> Session`
A dependency: the session of the bearer token, else of the cookie, which must pass `same_origin` first.
`People.session` gives the person. Raises `_unsigned()` without a token, and `_unsigned("the session has ended: sign
in again")` for one `People.session` doesn't know.

### `signed_in(held: Session) -> Person`
A dependency: the session's person.

### `bench(request, conn, person) -> Bench`
A dependency: `Bench(conn, person, inventory, facts)`, with the app's inventory and facts.

### Routes

| Route | Does |
| --- | --- |
| `sign_in`, `POST /session` | `same_origin`, then `People.authenticate`; `_unsigned("wrong login or password")` when it gives no one. `People.open_session`, and the token set as `COOKIE`: `Max-Age` `settings.SESSION_TTL` in seconds, `Secure`, `HttpOnly`, `SameSite=Lax`, `Path=/`. 201. |
| `sign_out`, `DELETE /session` | `People.close_session` of the session's token, and the cookie deleted with the same attributes. 204. |
| `me`, `GET /me` | `Me.of` the person. |

## schemas.py
The models' fields are in the OpenAPI document. Besides them:

| Name | Is |
| --- | --- |
| `_Schema` | The base of every model: frozen, `extra="forbid"`. |
| `Me.of(person: Person) -> Me` | The person, with their roles sorted. |
| `Finding.of(finding: chatddx.factors.base.Finding) -> Finding` | The same finding, field for field. |
| `Chunk` | `str \| None`, a chunk's digest, described for the OpenAPI document. |
| `Parts` | A `Chunk` field for each recipe part, in `chatddx.bench.PARTS`' order. |
| `Parts.given() -> dict[str, str \| None]` | The parts the request gave, by `model_fields_set`: each its digest, or `None` where it was empty or null. A part not given isn't a key. |
| `Varying(Parts)` | A variation's query: the parts, `endpoint`, `tag` (a list, empty by default) and `seed`. |
| `Labels` | What a scorer edit calls its views and resources: `views` and `resources`, each a list by position with `null` for none. |
| `Labels.given() -> chatddx.catalog.Labels` | The labels by part and position, the nulls left out. |
| `Labels.of(labels: Mapping[tuple[Part, int], str]) -> Labels` | The lists, each as long as its last label's position. |
| `Edit` | An edit, with `labels` for a scorer's (`None` for any other kind). |
| `NewThread` | A new thread's body: `component`, a component's JSON with its `kind`, or `recipe`, a recipe's JSON as a configuration's `recipe` reads; `name`, not empty; `language`; and `labels`, for a scorer. Its validator raises `ValueError("a new thread holds a component or a recipe, not both")` unless exactly one is given. |
| `NewFork`, `NewEdit` | A fork's body, `name` (not empty), and `parts` for a configuration or `component`, `language` and `labels` for another kind; and an edit's, `head` (required), with the same. |
| `MadeThread(ThreadDetail)`, `MadeEdit(Edit)` | What a write answers: the thread or the edit, with `findings`; an edit also with `cases`, each case an appendix's edit replaced and its replacement. |
| `Varied`, `Proposal` | A path a fork varies, with the base's and the fork's values; and what following would keep: `base` and `origin_head` (edits), `varies`, `recipe` for a configuration or `component` for another kind, `digest` and `compilation`. |
| `NewFollow` | A follow's body: `head` (required) and `language`. |
| `NewTyped` | A typed case's body: `text`, and `name`, `language` and `source`, each optional. |
| `NewAppendix` | An appendix's body: `text` and `name`, neither empty. |
| `FamilyCase` | A case of a family: `case`, `title`, `appendices`, `default` (the case the family stands for) and `expectations`, as `FamilyDetail`'s. |
| `NewCase` | A case's body: `appendices` in order, or `replacing`, a case of the family; its validator raises `ValueError("a case is built from appendices or replacing one, not both")` unless exactly one is given. |
| `NewCarry` | A carry's body: `head` and `case`. |
| `Said` | What is said about a thread: `name`, `description`, `tags`, `collaborators` (logins) and `deleted`, each optional; a field not given stays as it is (`model_fields_set`), and a null `name` takes the name away. |
| `NewTakes`, `Taken` | A take's body for many cases, `families` (not empty), `expectation_schema` and `owner`, and its answer, `chatddx.bench.Taken` keyed by family id. |
| `NewTake` | A take's body for one thread, `replace`. |
| `Metric`, `ScorerCode` | Scoring code the running chatddx ships: its `entry_point`, `version`, `metrics` (each its `name`, what it `measures`, a JSON Schema for a view's `params`, whether it is `judged`, reading a judge's verdicts, and the `unit` that marks a value that isn't a score from 0 to 1, if any) and a JSON Schema for the scorer's own `params`. |
| `NewRun` | A run's body. Its validator raises `ValueError("a run takes one of families, tags or cases")` unless exactly one of `families`, `tags` and `cases` is given, which FastAPI answers 422. |
| `EVENTS: dict[str, type[_Schema]]` | Each event of a run's stream, by name, and the model of its data, in the order a stream can send them; `run.noted`'s is `Finding`. |

`test/test_variations.py:test_a_request_names_the_recipe_s_parts` holds `Parts`' fields to `PARTS`, and a
variation's query parameters to them with `endpoint`, `tag` and `seed`.

## threads.py

| Name | Does |
| --- | --- |
| `login(bench, person: int \| None) -> str \| None` | `None` for no one, else `Bench.login`. |
| `edit_of(bench, edit: catalog.Edit, kind: str \| None = None) -> schemas.Edit` | The edit, with its author's login, and for a scorer thread's its labels (`Catalog.labels`). `kind` is the thread's, looked up with `Catalog.thread` when not given. |
| `thread_of(bench, kind: str, edit, about) -> schemas.Thread` | A thread from its head and `About`, titled by `Catalog.title`. |
| `detail(bench, thread: int) -> schemas.ThreadDetail` | `Bench.thread_by_id(thread, deleted=True)` (`NotFound`), so the person's own deleted thread too, with `deleted`, `Catalog.thread` for its kind and `forked_from`, `Catalog.recipe` dumped, or `None` without a compilation, and `Catalog.language_of` of the head's digest. |
| `refused() -> Generator[None]` | A context manager: a `ValueError` within, other than a `Conflict`, a `MovedOn` or an `OverQuota`, is raised as `HTTPException(422)` with its message. Those three pass to `STATUSES`. |
| `made(request, response, bench, thread: int, findings) -> schemas.MadeThread` | `detail` of the thread with the findings, and `Location` its path. |
| `configures(bench, thread: int) -> bool` | Whether the thread, read without a person, is a configuration's. |
| `check_given(configuration: bool, given) -> None` | `HTTPException(422, "a configuration is written with parts, not a component")` for a component or a language given a configuration, `HTTPException(422, "only a configuration has parts")`, or `HTTPException(422, "only a scorer has labels")` for labels given a configuration. |
| `part_of(bench, variation: TriedVariation, part: str) -> schemas.Part` | The part's digest (`TriedVariation.held`), its title (`Bench.title`), what it holds (`catalog.titles.describe`), and whether the variation replaced it. A part not held has `None` for each. |
| `reach_of(reach: chatddx.bench.Reach) -> schemas.Reach` | The bench's reach, with the scorer's thread as `scorer`, its name as `name`, the missing families by id, and those with expectations to choose from as `choosing`. |

| Route | Does |
| --- | --- |
| `threads`, `GET /threads` | `HTTPException(422, "no kind '<kind>': the kinds are …")` for a word not in `KINDS`. `Bench.visible` of each kind the word names, or with `deleted` `Bench.deleted`, kept by `name` (whole), `owner` (a login) and any of `tag`. |
| `thread`, `GET /threads/{thread}` | `detail`. |
| `edits`, `GET /threads/{thread}/edits` | `Bench.thread_by_id(thread, deleted=True)`, then `Catalog.history`. |
| `variation`, `GET /threads/{thread}/variation` | Within `refused()`: `Bench.variation(thread, query.given())` and `Bench.skeleton`. The seed is `suggest_seeds(1)[0]` unless given. `Bench.families(query.tag)`. With an endpoint: `Bench.endpoint`, whose `LookupError` is `HTTPException(422)`, and `Bench.findings(variation, engine, seed, families or None)`. `Bench.request(variation, engine, seed)` and `Bench.reach(variation, families)`. `parts` is `None` for a variation without a recipe. |
| `say`, `PATCH /threads/{thread}` | `HTTPException(422, "a description is replaced, never taken away")` for a null `description`, and `HTTPException(422, "no person '<login>'")` for a collaborator nobody is (`People.find`). Within `refused()`: `Bench.say`, with `...` for a `name` not given. 200, `detail`. |
| `proposal`, `GET /threads/{thread}/proposal` | Within `refused()`: `Bench.proposal`. `null` when there is none. |
| `follow`, `POST /threads/{thread}/follows` | Within `refused()`: `Bench.follow(thread, head, language)`. 201 with the edit's `edit_of` and findings. |
| `carry`, `POST /threads/{thread}/carries` | Within `refused()`: `Bench.carry(thread, head, case)`. 201 with the edit's `edit_of` and findings. |
| `delete`, `DELETE /threads/{thread}` | Within `refused()`: `Bench.say(thread, deleted=True)`. 204, also when it was deleted already. |
| `new`, `POST /threads` | Within `refused()`: `Bench.new(Bench.component(component), name, language, labels.given())`, or with `Recipe.model_validate(recipe)`. 201, `made`. |
| `fork`, `POST /threads/{thread}/forks` | `check_given`. Within `refused()`, for a configuration: `Bench.fork(Bench.variation(thread, parts), name)`, with `Bench.linted` of its skeleton; else `Bench.fork_component(thread, name, component, language, labels.given())`. 201, `made`, with `Location` the new thread's path (`url_path_for("thread")`). |
| `edit`, `POST /threads/{thread}/edits` | `check_given`. Within `refused()`, for a configuration: `Bench.edit(thread, Bench.variation(thread, parts), head)`, with `Bench.linted`; else `ValueError("an edit holds a component")` without one, and `Bench.edit_component(thread, head, component, language, labels.given())`. 201 with the edit's `edit_of` and findings, or 200 when it is `"unchanged"`. |
| `take`, `POST /threads/{thread}/takes` | Within `refused()`: `Bench.take_from(thread, replace)`. 201, with `Location` the new thread's path, and its `detail`. |

## families.py

| Name | Does |
| --- | --- |
| `family_of(bench, family: chatddx.bench.Family) -> schemas.Family` | The family, its owner's login and its tags sorted. |
| `expected(bench, case: str, schema: str) -> schemas.Expected` | `Bench.expectation(case, schema)`, titled by `Bench.title(schema)`. Its `Ambiguous` is given as `ambiguous`, its message, with `expectation` and `data` `None`. `shared` is `Bench.shared(case, schema)`, each by `thread_of`. |
| `case_of(bench, case: str, default: str) -> schemas.FamilyCase` | The case, its title, its appendices, whether it is `default`, and `expected` under each of `Bench.expectation_schemas(case)`. |

| Route | Does |
| --- | --- |
| `families`, `GET /families` | `Bench.families(tag)`, kept by `name` (whole). |
| `family`, `GET /families/{family}` | `Bench.family_by_id` (`NotFound`); the case's appendices; `expected` for each of `Bench.expectation_schemas(case)`. |
| `vignette`, `GET /families/{family}/vignette` | `Bench.family_by_id`, then `chatddx.store.fetch_vignette` of the case's vignette, whose `LookupError` is raised as `NotFound`. The text is decoded as UTF-8, a byte-order mark dropped and what can't be decoded replaced. `drifted` is whether `Fingerprint.of` the bytes differs from the case's, or `None` for a keyed fingerprint. |
| `takes`, `POST /takes` | `HTTPException(422, "no case <id> for <login>")` for a family not among `Bench.families()`. Within `refused()`: `Bench.take` of the families' cases, whose `NotFound` for the owner is `HTTPException(422)`. 200, with each family given its case's outcome. |
| `typed`, `POST /families` | Within `refused()`, which lets `OverQuota` through to `STATUSES`: `Bench.type_case`. 201, with `Location` the family's path, and `family_of`. |
| `appendix`, `POST /families/{family}/appendices` | Within `refused()`: `Bench.new(Bench.appendix(family, text), name)`. 201, `made`. |
| `cases`, `GET /families/{family}/cases` | `Bench.family_by_id` (`NotFound`), then `case_of` each of `Bench.cases(family)`. |
| `case`, `POST /families/{family}/cases` | `Bench.family_by_id` (`NotFound`, 404). Within `refused()`: `Bench.case(family, appendices)`, or, for `replacing`, `ValueError("<case> isn't a case of family <family>")` unless `Catalog.family` gives this one, then `Bench.replacement`. Their `NotFound` is the body's: 422. 201, `case_of`. |
| `tags`, `GET /tags` | `Bench.tags`. |

## world.py

| Name | Does |
| --- | --- |
| `endpoint_of(bench, name: str, spec: EndpointSpec) -> schemas.Endpoint` | The spec as the inventory declares it, with `Bench.endpoint`, `Bench.title`, `Bench.model` and `url_of`; a `LookupError` from any of them is given as `problem`, its message, with what comes after it `None`: `title`, `model` and `url` for an engine that isn't stored, `url` alone for one `url_of` can't tell. |

| Route | Does |
| --- | --- |
| `endpoints`, `GET /endpoints` | `endpoint_of` each of the inventory's endpoints, by name. |
| `endpoint`, `GET /endpoints/{name}` | `Inventory.endpoint`, whose `LookupError` is raised as `NotFound`, then `endpoint_of`. |
| `models`, `GET /models` | Each model the facts know or an endpoint serves, by name, with its facts dumped or `None`, and the endpoints serving it (`Bench.model` of `Bench.endpoint`, skipping an endpoint whose engine isn't stored). |
| `component`, `GET /components/{digest}` | `Rows.kind`; `NotFound("no component <digest> in the store")` when it is `None`. The kind, `Bench.title` and `Bench.get` dumped. |
| `scorer_code`, `GET /scorer-code` | Each of `chatddx.scorers.shipped.SCORERS` by entry point, its metrics by name; an entry point that publishes no schema for the scorer's own params gives `NO_PARAMS`, which allows none. Signed in, as every route here. |

## runs.py

| Name | Value |
| --- | --- |
| `STREAM` | `"text/event-stream"`. |
| `HEARD` | `0.5`: how often, in seconds, a request waiting for its run asks whether its client is still there. |
| `Put` | `Callable[[Named \| None], None]`: what the run's thread hands each event to; `None` ends the run's events. |
| `_Started` | A frozen dataclass of a started run: its `bench`, `running` (`Running`), `skeleton`, and `said`, the `run.started` event's data. |

### `streamed(accept: str | None) -> bool`
Whether one of the media types `Accept` lists is `STREAM`, its parameters left aside.

### `_families(bench, given: schemas.NewRun) -> list[Family]`
With `tags`: `Bench.families(tags)`, or `HTTPException(422, "no case tagged <tags joined by ' or '> for <login>")`
when there are none. With `families`: the families of `Bench.families()` with those ids, in the order given without
repeats; `HTTPException(422, "a run takes at least one case")` for none, and
`HTTPException(422, "no case <id> for <login>")` for the first id the person doesn't see.

### `_cases(bench, given: schemas.NewRun) -> list[str]`
Without `cases`, each of `_families`' cases. With them: the cases in the order given without repeats;
`HTTPException(422, "a run takes at least one case")` for none, and `HTTPException(422, "no case <case> for <login>")`
for the first that isn't among `Bench.cases` of a family of `Bench.families()`.

### `_start(held: AppState, person: Person, given: schemas.NewRun) -> _Started`
On a connection of its own (`AppState.connect`), a `Bench` for the person; within `refused()`, `Bench.variation` and
`Bench.skeleton`; then `Bench.endpoint`. A `LookupError` from those, `NotFound` among them, is raised as
`HTTPException(422)` with its message. The cases of `_cases`; the seed, `suggest_seeds(1)[0]` unless given; and,
within `refused()`, `Bench.start`, whose `Refused` passes to `STATUSES`. The connection is closed when any of this
raises, and is the run's thread's otherwise.

### `_send(started: _Started, score: bool, put: Put) -> None`
The run's thread. `Running.send`, with each event put as `event_of(skeleton, event)`; a `KeyboardInterrupt` from it,
for a call stopped other than by a halt, as a runaway answer is, ends the sending. Then `Running.finish`, put as
`run.finished`, and, unless `score` is false, `Bench.score`, put as `run.scored`; the scoring pass's events aren't
passed on, and nothing halts it. Any `Exception` is logged and put
as `error`, `"run <id> failed: <error>"`. Last, whatever happened, the connection is closed and `None` put.

### `_stream(running: Running, events: asyncio.Queue[Named | None]) -> AsyncIterator[str]`
Each event as `sse` gives it, until `None`. On leaving, `Running.halt`, which ends a run whose client went away and
changes nothing for one that ended.

### `_drained(events) -> str | None` and `_ended(request, running, events) -> str | None`
`_ended` drains the events on a task of their own (`_drained`), and while that runs, asks `Request.is_disconnected`
every `HEARD`; the first time it is, `Running.halt`. It gives the last `error` event's detail, or `None`.

### `start`, `POST /runs`
`_start`, on the thread pool, for the request's person. The run's events go through an `asyncio.Queue`, `run.started`
first; the thread puts them with `call_soon_threadsafe`, and drops them once the loop is closed. The thread, named
`chatddx-run-<id>`, isn't a daemon. `Location` is the run's path (`url_path_for("run")`).
- When `streamed(accept)`: a `StreamingResponse` of `_stream`, 201, with `Location`, `Cache-Control: no-cache` and
  `X-Accel-Buffering: no`.
- Otherwise `_ended`; an `error` is raised as `HTTPException(500)` with its detail; else 201, with `Location` and
  `detail` of the run, on the thread pool with the request's bench.

The route's 201 names `STREAM` among its content types, and its description names the events.

### `run_of(bench, started: RunStarted, finished: bool) -> schemas.Run` and `detail(bench, run: UUID) -> schemas.RunDetail`
`run_of` is the run as listed: its trial's parts, its endpoint's name, and `Bench.described`. `detail` adds, from
`Bench.run_by_id` (`NotFound`) and `Store.run`: the rig; the finish's time and findings as `noted`; `check_run`'s
findings over the trial and canary set `Store.load` gives; each item's `item_of`; and `graded_of` each of
`Bench.scores_of`.

| Route | Does |
| --- | --- |
| `runs`, `GET /runs` | `Bench.runs`, kept by `trial`, then by the runs of `Bench.reaching(reaching)` and `Bench.scored_by(scored_by)`; the page `[offset:offset + limit]`, `limit` from 1 to 200 and 20 by default; `Store.finished` for the page. |
| `run`, `GET /runs/{run}` | `detail`. |
| `items`, `GET /runs/{run}/items` | `Bench.run_by_id`, then each of `Store.run`'s items: `item_of`, with the outcome's why, and the vignette's fingerprint, the call and the turns dumped. |
| `rendered_again`, `GET /runs/{run}/rendered-again` | `Bench.run_by_id`, then `Bench.rendered_again` of `Store.run`: each item's key, and why it renders otherwise, or `None`. |

A run is named by a `UUID`, so anything else in its place is a 422.

## events.py

| Name | Does |
| --- | --- |
| `Named` | `tuple[str, BaseModel]`: an event's name, one of `EVENTS`, and its data. |
| `sse(name: str, data: BaseModel) -> str` | `event: <name>`, `data: <the data as JSON>` and a blank line. The JSON holds no newline. |
| `item_of(skeleton, item: RunItem) -> schemas.Item` | The item's key, the word of `chatddx.bench.outcome`, and `chatddx.bench.usage`. |
| `graded_of(graded: chatddx.bench.Graded) -> schemas.Graded` | The scorer's digest and name, the score's id, each view's label (`Graded.label`) and the `mean` of its values that aren't `None` (else `None`), each score item's value, and why it gave none. Neither the score items' detail nor the scoring's findings. |
| `event_of(skeleton, event: chatddx.runner.run.Event) -> Named` | The runner's event as the stream's, below. |

| Runner's event | Stream's | Data |
| --- | --- | --- |
| `ItemStarted` | `item.started` | the key, and the seed |
| `Streamed` | `item.delta` | the key, and the delta's kind, text and tokens so far |
| `ToolRan` | `item.tool` | the key, and the tool run dumped |
| `ItemEnded` | `item.ended` | `item_of`, and the outcome's why |
| `CanaryEnded` | `canary.ended` | the phase, the canary's index, and the call dumped |
| `Noted` | `run.noted` | `Finding.of` |

`run.started`, `run.finished`, `run.scored` and `error` are `runs.py`'s.

## The command
`chatddx api [--world DIR] [--facts PATH]… [--bind HOST:PORT]` (`src/chatddx/cli.py:_api`): the World, from `--world`
or `CHATDDX_WORLD`; the bundled facts, the World's and those given; and `--bind`, else `settings.host()` (`HOST`,
`localhost:8000` when unset), split at its last colon, with brackets stripped from an IPv6 host. One that isn't
`HOST:PORT` is `SystemExit("api: bind to HOST:PORT, not '<bind>'")`. `uvicorn.run` serves `app(world.inventory, facts,
settings.database())`.

## Tests
`test/`, marked wip.

| Module | Holds |
| --- | --- |
| `conftest.py` | `template` is `curated`, the test World as init-data lands it; `autocommit`; `alice`, with `PASSWORD`; `served`, the app on the test World's inventory and facts (`chatddx.test.world.world_facts`); `client`, a `TestClient` over `https://testserver`; `signed`, the client with alice's bearer; `bob`, his bearer's header; `bench`, alice's; and the helpers `sign_in` and `bearer`. |
| `test_people.py` | Signing in and out by bearer and cookie, the same-origin check, validation, the statuses, the OpenAPI document and the command. |
| `test_threads.py`, `test_families.py`, `test_world.py` | The reads, taking expectations, and what bob doesn't see of threads and families; that every read needs a session. |
| `test_writes.py` | A configuration made from a recipe, and what is refused of one; chunks and expectations written new, edited and forked; what is refused, and with which status; an expectation's findings. |
| `test_cases.py` | A family's cases, an appendix written for it, a case built of it and replaced by the appendix's edit, and an expectation carried onto the replacement; cases refused; a run naming a case that isn't one. |
| `test_typed.py` | A typed case answered as a family, its vignette read back, and bob not seeing it; what can't be typed, and 429 past the day's quota. |
| `test_following.py` | A fork with nothing to follow, then a proposal once the archive's configuration moved on, a stale head, following, and nothing proposed after. |
| `test_scorers.py` | The scoring code shipped, as pickers read it; a scorer of the archive's forked with its labels, a view renamed by an edit and the history's labels, and one written new; scorers refused, and labels given where nothing has them. |
| `test_said.py` | Saying what holds of a thread, sharing it with bob and taking it back; refusals; deleting, listing and reading the deleted thread, and restoring it; a session needed. |
| `test_variations.py` | Looks, forks and edits; that a look's queries don't grow with its cases, counted on the test's database (the fixtures create the next test's meanwhile). |
| `test_runs.py` | Runs, over its own `served` on `world`, the test World on free ports; `listening`, the app under uvicorn on a thread, for the two tests of a client going away. No test reads a judged view's score through the API; `src/chatddx/runner/test/test_score.py` and the repl's tests do. |

`src/chatddx/conftest.py` holds what the repl's tests share with these: `world`, the test World's inventory on free
ports (`chatddx.test.world.free_world`), and `fake`, `faked` on the test's store. `chatddx.test.world.faked(world, get,
endpoint=QWEN, delay=0.0)` is the fake vLLM serving an endpoint's engine as its start-up says, `delay` seconds a
token.

## Beyond docs/api.md
Behavior described here that `docs/api.md` doesn't state, or states otherwise:
- `endpoint_of` keeps an endpoint's title and model when only its URL can't be told.
- `check_given` refuses a language given a configuration as it refuses a component.
- `Ambiguous` maps to 409, though no route lets one through: `expected` gives it as `ambiguous`, and `Bench.score`
  as a refusal.
- `GET /api/runs` ignores a parameter it doesn't name, `unscored` among them.

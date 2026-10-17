# API package

Reference for the `chatddx.api` package. It was written from `src/chatddx/api/*` and docs/api.md. What the API is and
why it is shaped this way is in docs/api.md. The HTTP interface itself, its paths, parameters, bodies and statuses,
is the OpenAPI document the app serves at `/api/openapi.json`, with pages at `/api/docs`, and isn't repeated here;
this file says how the package builds it: what each name does, accepts, returns and raises. The types it passes
through are the bench's (docs/bench-api.md), the runner's (docs/runner-api.md), and those in
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
- [runs.py](#runspy): starting a run, its events and halting it; reading runs
- [scores.py](#scorespy): scoring a run, its scores and a score's items
- [telling.py](#tellingpy): a run's events, from the ledger's rows and what the worker says
- [listening.py](#listeningpy): the app's one listening connection, fanning out to its streams
- [queue.py](#queuepy): a person's queue, paused, resumed and stopped
- [events.py](#eventspy): the runner's and the scoring pass's events as a run's events
- [The command](#the-command)
- [Tests](#tests)

## Package
`chatddx.api` re-exports nothing; its modules are imported by path. `src/chatddx/cli.py` imports `app.py:app`.

The modules, and what each builds on:
- `listening.py`: psycopg, `chatddx.store.notify`.
- `state.py`: `listening.py`, psycopg, `chatddx.{inventory,store}`.
- `schemas.py`: `chatddx.catalog`, `chatddx.factors.{base,cases,request,trial}`, `chatddx.identity`,
  `chatddx.runner`, `chatddx.settings`.
- `people.py`: `schemas.py`, `state.py`, `chatddx.bench`, `chatddx.identity`, `chatddx.settings`, `chatddx.store`.
- `threads.py`: `schemas.py`, `people.py`, `chatddx.bench`, `chatddx.catalog`,
  `chatddx.factors.{base,facts,kinds,request,scoring,trial}`.
- `families.py`: `schemas.py`, `people.py`, `state.py`, `threads.py`, `chatddx.bench`, `chatddx.factors.{base,cases}`,
  `chatddx.store`.
- `world.py`: `schemas.py`, `people.py`, `threads.py`, `chatddx.bench`, `chatddx.factors.kinds`, `chatddx.inventory`,
  `chatddx.scorers.{scorer,shipped}`.
- `events.py`: `schemas.py`, `chatddx.bench`, `chatddx.catalog`, `chatddx.factors.{base,request,scoring,trial}`,
  `chatddx.ledger`, `chatddx.runner`, `chatddx.scorers.aggregate`.
- `queue.py`: `schemas.py`, `people.py`, `chatddx.bench`, `chatddx.settings`, `chatddx.store`.
- `runs.py`: `schemas.py`, `events.py`, `people.py`, `state.py`, `telling.py`, `threads.py`, `chatddx.bench`,
  `chatddx.catalog`, `chatddx.factors.{base,request,trial}`, `chatddx.ledger`, `chatddx.runner`,
  `chatddx.scorers.answer`, `chatddx.store`.
- `scores.py`: `schemas.py`, `events.py`, `people.py`, `state.py`, `chatddx.store`.
- `app.py`: every module above but `events.py` and `telling.py`, `chatddx.bench`, `chatddx.inventory`,
  `chatddx.runner.gate`, `chatddx.store`, `chatddx.worker`.
- `telling.py`: `schemas.py`, `events.py`, `listening.py`, `state.py`, `chatddx.bench`,
  `chatddx.factors.{base,bundle,request,scoring,trial}`, `chatddx.identity`, `chatddx.ledger`, `chatddx.store`.

The modules that serve build on FastAPI, `telling.py` among them for its thread pool; `schemas.py`, `events.py` and
`listening.py` don't, and `chatddx.worker` publishes a run's events with `events.py`. The package holds no SQL: it
reads through the bench, the store's `Store`, `Rows` and `Queue`, and `People`, and listens through
`chatddx.store.notify`.

## Conventions

**Handlers.** Every route is a plain `def`, which FastAPI runs on its thread pool, but `runs.py:events`, which is
`async`, so that it can stream; it does its blocking work through `run_in_threadpool`.

**A bench per request.** `people.py:bench`, as `BenchDep`, builds a `Bench` for the person the request acts for, on the
request's connection (`state.py:connection`), in autocommit mode and closed when the request is done with it. A stream
gets a connection of its own (`telling.py:told`), closed when it ends.

**Jobs.** What a request asks to be run or scored is a job in the store's queue (`chatddx.store.Queue`;
docs/worker.md), which a worker takes: `chatddx worker`, or the one `app` runs on a thread of its own when made
with `worker=True`. A stream reads the run's rows, and hears what the worker says and the rows as they land through
the app's one `listening.py:Listener`.

**Who it depends on.** What depends on the person is asked of the bench. What doesn't is the same for everyone: the
endpoints and models (`world.py`), a component by its digest, and the scoring code the running chatddx ships, read
from the World and the store, the facts among the store's: through the bench's `endpoint` and `facts`, its `store`
and `rows`, or straight (`chatddx.scorers.shipped.SCORERS`).

**People by login.** Owners, collaborators and an edit's author are given as logins (`Bench.login`); a subject with
no owner has `None` (`threads.py:login`).

**Errors.** `app.py:STATUSES` maps the bench's `NotFound`, `Ambiguous`, `Conflict`, `MovedOn` and `OverQuota`, and
the gate's `Refused`, wherever they are raised, with the message as the detail and a code of its own. An
`HTTPException`, a route's or Starlette's, has the code `app.py:CODES` gives its status, and a request that doesn't
validate is `unprocessable`.

What else a route means it raises as an `HTTPException` where it catches it: `threads.py:refused`, around every write,
every variation built and a proposal, turns a `ValueError` into a 422, letting a `Conflict`, a `MovedOn` and an
`OverQuota` through, and a route turns a `LookupError` about what its query or body names into a 422.

Nothing maps `ValueError` or `LookupError` wholesale, so one a route doesn't catch is a 500.

**Models.** Every request and response model derives from `schemas.py:_Schema`: frozen, `extra="forbid"`. A body
field a model doesn't name is a 422, and so is a query parameter where the query is a model (`Varying`); elsewhere a
query parameter a route doesn't name is ignored. Components, recipes, facts, calls, tool runs and fingerprints are
given as the JSON they dump to, not as models of their own.

**Sensitive places.** `families.py:vignette`, `runs.py:items`, `scores.py:items` and a run's stream are the only
routes that give sensitive content, and each says `Cache-Control: no-store`: the first three through
`state.py:no_store`, the stream with `state.py:NO_STORE` among its headers.

**Routes.** Each module's routes are given under "Routes" as `name`, `METHOD /path`, the path under `/api`: what the
route does, and what it answers.

## app.py

### `STATUSES: dict[type[Exception], tuple[int, Code]]`
`NotFound` 404 `not_found`, `Ambiguous` 409 `ambiguous`, `Conflict` 409 `conflict`, `MovedOn` 409 `moved_on`,
`OverQuota` 429 `over_quota`, `Refused` 422 `refused`, and the queue's `UnderWay` 409 `conflict`. Each is answered
`Error(detail=str(error), code=code)`.

`app` mounts the routers of `people.py`, `threads.py`, `families.py`, `world.py`, `runs.py`, `scores.py` and
`queue.py`.

### `CODES: dict[int, Code]`
The code of an `HTTPException`, a route's or Starlette's own, by its status: 401 `unauthenticated`, 403 `cross_site`,
404 `not_found`, 405 `not_allowed`, 409 `conflict`, 422 `refused` and 429 `over_quota`; any other is `error`. Its
headers are kept, as a 401's `WWW-Authenticate`.

### `app(inventory: Inventory, conninfo: str, worker: bool = False) -> FastAPI`
A FastAPI app titled `chatddx`, versioned as the installed package is, with its OpenAPI document at
`/api/openapi.json`, its pages at `/api/docs` and no ReDoc. `state.chatddx` holds an `AppState` of what it was made
with, and a `Listener` of `conninfo`. Its lifespan runs a `chatddx.worker.Worker` on a thread named `chatddx-worker`
when `worker`, and as it ends stops the worker, waiting for it, then the listener.

The routers of `people.py`, `threads.py`, `families.py`, `world.py`, `runs.py` and `scores.py` are mounted under
`/api`; the handlers of `STATUSES` are added, one of `HTTPException` by `CODES`, and one of `RequestValidationError`,
answered 422 with FastAPI's list of where as the detail and `unprocessable`; and `openapi` is `_with_models`.

### `_with_models(made: FastAPI) -> Callable[[], dict[str, Any]]`
FastAPI's own `openapi`, with the model of each event in `schemas.py:EVENTS`, and `schemas.py:Error`, added to
`components.schemas`, as pydantic's `models_json_schema` gives them in serialization mode, with references as
`#/components/schemas/{model}`. They are added on every call, to the document FastAPI keeps.

## state.py

### `class AppState`
A frozen dataclass of what the app is made with, loaded once: `conninfo: str`, `inventory: Inventory`, and
`listener: Listener`.

#### `connect() -> Connection`
A new connection to `conninfo` in autocommit mode, as the runner needs.

### `state(request: Request) -> AppState`
The app's `AppState`.

### `connection(request: Request) -> Iterator[Connection]`
A dependency: a connection for the request, closed when the request is done with it.

### `NO_STORE`
`{"Cache-Control": "no-store"}`.

### `no_store(response: Response) -> None`
A dependency of the sensitive routes: `NO_STORE` among the response's headers.

## people.py

### Constants
- `COOKIE`: `"__Host-chatddx-session"`: the prefix has a browser keep the cookie to this host, over HTTPS, for every
  path.
- `SAFE`: `GET`, `HEAD` and `OPTIONS`: the methods `same_origin` lets through.
- `ConnDep`: `Annotated[Connection, Depends(connection)]`.
- `BenchDep`: `Annotated[Bench, Depends(bench)]`.

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
A dependency: `Bench(conn, person, inventory)`, with the app's inventory.

### `keep_cookie(response: Response, token: str) -> None`
The token set as `COOKIE`: `Max-Age` `settings.SESSION_TTL` in seconds, `Secure`, `HttpOnly`, `SameSite=Lax`,
`Path=/`.

### `drop_cookie(response: Response) -> None`
`COOKIE` deleted with the same attributes.

### Routes

#### `sign_in`, `POST /session`
`same_origin`, then `People.authenticate`; `_unsigned("wrong login or password")` when it gives no one.
`People.open_session`, and the token set as `COOKIE`: `Max-Age` `settings.SESSION_TTL` in seconds, `Secure`,
`HttpOnly`, `SameSite=Lax`, `Path=/`. 201.

#### `sign_out`, `DELETE /session`
`People.close_session` of the session's token, and the cookie deleted with the same attributes. 204.

#### `me`, `GET /me`
`Me.of` the person.

## schemas.py
The models' fields are in the OpenAPI document. Besides them:

### `_Schema`
The base of every model: frozen, `extra="forbid"`.

### `Code`
The codes of `app.py:STATUSES` and `app.py:CODES`, `unprocessable` and `error`.

### `Error`
A refusal's body: `detail`, a string or a list of where a request doesn't validate, and `code`.

### `Me.of(person: Person) -> Me`
The person, with their roles sorted.

### `Finding.of(finding: chatddx.factors.base.Finding) -> Finding`
The same finding, field for field.

### `Chunk`
`str | None`, a chunk's digest, described for the OpenAPI document.

### `ModelDigest`
`str | None`, a model's digest, described for the OpenAPI document as one that can't be taken out.

### `Parts`
A `Chunk` field for each chunk part, and `model`, a `ModelDigest`, in `chatddx.factors.request.RECIPE_PARTS`' order.

#### `given() -> dict[str, str | None]`
The parts the request gave, by `model_fields_set`: each its digest, or `None` where it was empty or null. A part not
given isn't a key.

### `Varying(Parts)`
A variation's query: the parts, `head` (an edit id, the configuration's head unless given), `endpoint` (to render and
lint for: the one a hand-written configuration needs, else checked against the engine), `tag` (a list, empty by
default) and `seed`.

### `Labels`
What a scorer edit calls its views and resources: `views` and `resources`, each a list by position with `null` for
none.

#### `given() -> chatddx.catalog.Labels`
The labels by part and position, the nulls left out.

#### `of(labels: Mapping[tuple[Part, int], str]) -> Labels`
The lists, each as long as its last label's position.

### `Edit`
An edit, with `labels` for a scorer's (`None` for any other kind).

### `NewThread`
A new thread's body: `component`, a component's JSON with its `kind`, or `recipe`, a recipe's JSON as a
configuration's `recipe` reads; `name`, not empty; `language`; and `labels`, for a scorer. Its validator raises
`ValueError("a new thread holds a component or a recipe, not both")` unless exactly one is given.

### `NewFork`, `NewEdit`
A fork's body, `name` (not empty), and `head`, the edit it forks from, and `parts` for a configuration or
`component`, `language` and `labels` for another kind; and an edit's, `head` (required), with the same.

### `MadeThread(ThreadDetail)`, `MadeEdit(Edit)`
What a write answers: the thread or the edit, with `findings`; an edit also with `cases`, each case an appendix's edit
replaced and its replacement.

### `Varied`, `Proposal`
A path a fork varies, with the base's and the fork's values; and what following would keep: `base` and `origin_head`
(edits), `varies`, `recipe` for a configuration or `component` for another kind, `digest` and `compilation`.

### `NewFollow`
A follow's body: `head` (required) and `language`.

### `Moved`, `NewFollowMoved`
What following would keep: `about` (the model's name), `facts` (the facts' head, an `Edit`, when they moved),
`compiled` (the facts compiled against), `model` (the model's head, when it moved), `held` (the model held), `digest`,
`compilation` and `refused`. `NewFollowMoved`: `head` (required).

### `NewTyped`
A typed case's body: `text` and `language`, required, and `name` and `source`, each optional.

### `NewAppendix`
An appendix's body: `text` and `name`, neither empty.

### `FamilyCase`
A case of a family: `case`, `title`, `appendices`, `default` (the case the family stands for) and `expectations`, as
`FamilyDetail`'s.

### `NewCase`
A case's body: `appendices` in order, or `replacing`, a case of the family; its validator raises
`ValueError("a case is built from appendices or replacing one, not both")` unless exactly one is given.

### `NewCarry`
A carry's body: `head` and `case`.

### `Said`
What is said about a thread: `name`, `description`, `tags`, `collaborators` (logins) and `deleted`, each optional; a
field not given stays as it is (`model_fields_set`), and a null `name` takes the name away.

### `NewTakes`, `Taken`
A take's body for many cases, `families` (not empty), `expectation_schema` and `owner`, and its answer,
`chatddx.bench.Taken` keyed by family id.

### `NewTake`
A take's body for one thread, `replace`.

### `Metric`, `ScorerCode`
Scoring code the running chatddx ships: its `entry_point`, `version`, `metrics` (each its `name`, what it `measures`,
a JSON Schema for a view's `params`, whether it is `judged`, reading a judge's verdicts, and the `unit` that marks a
value that isn't a score from 0 to 1, if any) and a JSON Schema for the scorer's own `params`.

### `NewRun(Seeds)`
A run's body, with `head`, the edit it varies, the configuration's head unless given; `endpoint`, where to send it,
the one serving its engine unless given, and needed by a hand-written configuration; `cleanup`, the steps, else the
sources'; `concurrency` and `order`, else the endpoint's. Its validator raises
`ValueError("a run takes one of families, tags or cases")` unless exactly one of `families`, `tags` and `cases` is
given, which FastAPI answers 422.

### `Run`
A run as listed, with `language`, its skeleton's (`language.language_of`); `started_with`, the first run of its start
(`About.started_with`), else `None`; `ran`, a `Ran`, else `None`; `unscored`, its scorers left as `Unscored`
(`scorer`, `name`), when the listing asked for them, else `None`; and `job`, its latest job as a `RunJob`, else
`None`.

### `StartedRuns`, `LeftOut`
What a start answers: `runs`, a `RunStartedData` per language its cases are sent in, in the order started; and
`left_out`, a `LeftOut` per language left out, its `language`, `cases` and `why`. `RunStartedData`, `run.started`'s
data, says the `language` it is sent in.

### `Carried`
A language of a look, `Variation.languages`: `language`, null for the configuration's own when it is unknown;
`families`, by id; `translated`; `skeleton`, the digest they are sent as, null when left out; and `refused`, why they
are left out.

### `Ran`
What a run ran: its `configuration`, `head`, the edit it varied, and `parts`, each part replaced over it, by its
chunk's digest or `null` for a part taken out.

### `Graded`
A score under one scorer: the scorer and its name, the score's id, its `scoring`, when it started (`at`) and whether
it `finished`, each view's label and mean, each item's value, or why it was refused.

### `ScoreItemDetail`, `ScoreItems`
A score item with its `detail` and `judge_calls` as their JSON; and a score's items with its `findings`.

### `EVENTS: dict[str, type[_Schema]]`
Each event of a run's events, by name, and the model of its data, in the order they can come; `run.noted` and
`score.noted` have `Finding`, and `done` `DoneData`, whose `halted` is `None` when told from the ledger.

### `NewScoring`
A scoring's body: `scorers`, by digest, or none for every scorer that applies.

### `Answer`
What was read, why it couldn't be or breaks its schema, and whether it was salvaged.

### `NewAgain(Seeds)`
Running again's body: the seeds or replicates, as many as the run had, drawn, when neither is given; and `score`.

### `Seeds`
`seeds`, at least one, or `replicates`, from 1 to `settings.ITEMS_PER_RUN`. Its validator raises
`ValueError("a run takes seeds or replicates, not both")`.

### `RunJob`
A run's job: its `status`, `why`, `halt`, `ahead` (`chatddx.store.queue.Placed`), `queued` and `ended`.

### `NewResume`
Resuming's body: `score`.

### `NewStop`
A stop's body: `now`, the second press.

### `Queue`
A person's queue: `paused`, `queued`, `under_way` and `workers` (`chatddx.store.queue.Standing`).

### `Stopped`
What a stop did: the runs `taken_out` of the queue, and those `halting`.

### Tests
`test/test_variations.py:test_a_request_names_the_recipe_s_parts` holds `Parts`' fields to `RECIPE_PARTS`, and a
variation's query parameters to them with `endpoint`, `tag` and `seed`.

## threads.py

### `login(bench, person: int | None) -> str | None`
`None` for no one, else `Bench.login`.

### `edit_of(bench, edit: catalog.Edit, kind: str | None = None) -> schemas.Edit`
The edit, with its author's login, and for a scorer thread's its labels (`read.labels`). `kind` is the thread's,
looked up with `threads.thread` when not given.

### `thread_of(bench, kind: str, edit, about, languages=None) -> schemas.Thread`
A thread from its head and `About`, titled by `titles.title`, with the word `chatddx.bench.word_of` gives its kind, in
the language `languages` gives its head by id, else `language.edit_languages` of it; and `translated`.

### `translated(bench, edit) -> list[str]`
The languages the translations of the edit's compilation's recipe carry it into, sorted; `[]` without a compilation
or translations.

### `detail(bench, thread: int) -> schemas.ThreadDetail`
`Bench.thread(thread, deleted=True)` (`NotFound`), so the person's own deleted thread too, with `deleted`,
`threads.thread` for its kind and `forked_from`, and `threads.recipe` of the head dumped, or `None` without a
compilation.

### `refused() -> Generator[None]`
A context manager: a `ValueError` within, other than a `Conflict`, a `MovedOn` or an `OverQuota`, is raised as
`HTTPException(422)` with its message. Those three pass to `STATUSES`.

### `made(request, response, bench, thread: int, findings) -> schemas.MadeThread`
`detail` of the thread with the findings, and `Location` its path.

### `made_edit(bench, written: Written) -> schemas.MadeEdit`
The edit's `edit_of`, the findings and the cases it replaced.

### `configures(bench, thread: int) -> bool`
Whether the thread, read without a person, is a configuration's.

### `check_given(configuration: bool, given) -> None`
`HTTPException(422, "a configuration is written with parts, not a component")` for a component or a language given a
configuration, `HTTPException(422, "only a configuration has parts")`, or
`HTTPException(422, "only a scorer has labels")` for labels given a configuration.

### `component_of(doc: Mapping[str, JsonValue]) -> Component`
The component `doc` holds, as `GET /api/components` gives its body: of the model its `kind` names, with `v`, when
given, its schema version.
- Raises `ValueError("<kind!r> isn't a kind a person writes: the kinds are …")`.
- Raises `ValueError("<kind> is at v<n>, not v<v>")`.
- Raises the model's `ValidationError`.

### `part_of(bench, variation: TriedVariation, part: str, landed: Landing | None = None) -> schemas.Part`
The part's digest (`TriedVariation.held`), its title (`Bench.title`), what it holds (`catalog.titles.describe`), and
whether the variation replaced it; with `landed`, a reasoning level's or a recommended sampling's landing, as
`Bench.landed` gives it, its level as `landed` and its reasons as `nearest`. A part not held has `None` for each.

### `reach_of(reach: chatddx.bench.Reach) -> schemas.Reach`
The bench's reach, with the scorer's thread as `scorer`, its name as `name`, the missing families by id, and those
with expectations to choose from as `choosing`.

### Routes

#### `threads`, `GET /threads`
… `Bench.threads(kind, deleted=…, purpose=…, answering=answers)`, a configuration's purpose `generation` unless given,
kept by `name` (whole), `owner` (a login) and any of `tag`; `language.edit_languages` of the kept heads, given to
`thread_of`, each with its word's kind, or its head's (`Rows.kind`) for `model` and `engine`.

#### `thread`, `GET /threads/{thread}`
`detail`.

#### `edits`, `GET /threads/{thread}/edits`
`Bench.thread(thread, deleted=True)`, then `threads.history`.

#### `variation`, `GET /threads/{thread}/variation`
Within `refused()`: `Bench.variation(thread, query.given(), query.head)`, `Bench.skeleton` and `Bench.landed`; the
engine is that of the `Endpoint` `Bench.at(varied, endpoint)` gives, `None` when it refuses and no endpoint is given;
a `LookupError` or `ValueError` from it with `endpoint` given is `HTTPException(422)`.
- `languages` are, within `refused()`, `Bench.languages` of the cases of `Bench.families(tag)`, each with its families
  by id and its skeleton's digest; `[]` for a judge configuration or no families.
- `findings` are `Bench.findings` at the engine, given those languages, or over one case when there are none, and
  `None` without an engine.
- `parts` are `part_of` each of `RECIPE_PARTS` with its landing, `None` without a recipe.
- `request` is `Bench.request` at the engine.
- … `label` is `TriedVariation.label`, and `held_by` is `thread_of` of `Bench.holder(skeleton, varied)`, `varied` the
  variation's recipe (`TriedVariation.varied`), or `None`.

#### `say`, `PATCH /threads/{thread}`
`HTTPException(422, "a description is replaced, never taken away")` for a null `description`, and
`HTTPException(422, "no person '<login>'")` for a collaborator nobody is (`People.find`). Within `refused()`:
`Bench.say`, with `...` for a `name` not given. 200, `detail`.

#### `proposal`, `GET /threads/{thread}/proposal`
Within `refused()`: `Bench.proposal`. `null` when there is none.

#### `follow`, `POST /threads/{thread}/follows`
Within `refused()`: `Bench.follow(thread, head, language)`. 201, `made_edit`.

#### `moved`, `GET /threads/{thread}/moved`
Within `refused()`: `Bench.moved`. `null` when nothing has moved on.

#### `follow_moved`, `POST /threads/{thread}/moved/follows`
Within `refused()`: `Bench.follow_moved(thread, head)`. 201, `made_edit`.

#### `carry`, `POST /threads/{thread}/carries`
`Bench.thread(thread)` (`NotFound`). Within `refused()`: `ValueError("<word> <thread> isn't an expectation")` for a
thread of another word, then `Bench.edit(thread, head, …)` of an `Expectation` of the case with the head's schema and
data, which the bench holds to the expectation's family. 201, `made_edit`.

#### `delete`, `DELETE /threads/{thread}`
Within `refused()`: `Bench.say(thread, deleted=True)`. 204, also when it was deleted already.

#### `new`, `POST /threads`
Within `refused()`: `Bench.new(component_of(component), name, language, labels.given())`, or with
`Recipe.model_validate(recipe)`. 201, `made`.

#### `fork`, `POST /threads/{thread}/forks`
`check_given`, which also raises
`HTTPException(422, "only a configuration is forked from an edit: another kind from a component")` for a `head` given
another kind. Within `refused()`: `Bench.fork(thread, name, held, language, labels.given())`, `held` being
`Bench.variation(thread, parts, head)` for a configuration, else the `component_of` the component, or `None`. 201,
`made` with its findings.

#### `edit`, `POST /threads/{thread}/edits`
`check_given`. Within `refused()`: `Bench.edit(thread, head, held, language, labels.given())`, `held` being
`Bench.variation(thread, parts)` for a configuration; else `ValueError("an edit holds a component")` without one, and
its `component_of`. 201, `made_edit`, or 200 when it is `"unchanged"`.

#### `take`, `POST /threads/{thread}/takes`
Within `refused()`: `Bench.take_from(thread, replace)`. 201, with `Location` the new thread's path, and its `detail`.

## families.py

### `family_of(bench, family: chatddx.bench.Family) -> schemas.Family`
The family, its owner's login and its tags sorted.

### `expected(bench, case: str, schema: str) -> schemas.Expected`
`Bench.expectation(case, schema)`, titled by `Bench.title(schema)`. Its `Ambiguous` is given as `ambiguous`, its
message, with `expectation` and `data` `None`. `shared` is `Bench.shared(case, schema)`, each by `thread_of`.

### `case_of(bench, case: str, default: str) -> schemas.FamilyCase`
The case, its title, its appendices, whether it is `default`, and `expected` under each of
`Bench.expectation_schemas(case)`.

### Routes

#### `families`, `GET /families`
`Bench.families(tag)`, kept by `name` (whole).

#### `family`, `GET /families/{family}`
`Bench.family` (`NotFound`); the case's appendices; `expected` for each of `Bench.expectation_schemas(case)`.

#### `vignette`, `GET /families/{family}/vignette`
`Bench.family` (`NotFound`), then `chatddx.store.fetch_vignette` of the case's vignette, whose `LookupError` is raised
as `NotFound`. The text is decoded as UTF-8, a byte-order mark dropped and what can't be decoded replaced. `drifted`
is whether `Fingerprint.of` the bytes differs from the case's, or `None` for a keyed fingerprint.

#### `takes`, `POST /takes`
`HTTPException(422, "no case <id> for <login>")` for a family not among `Bench.families()`. Within `refused()`:
`Bench.take` of the families' cases, whose `NotFound` for the owner is `HTTPException(422)`. 200, with each family
given its case's outcome.

#### `typed`, `POST /families`
Within `refused()`, which lets `OverQuota` through to `STATUSES`: `Bench.type_case`. 201, with `Location` the family's
path, and `family_of`.

#### `appendix`, `POST /families/{family}/appendices`
Within `refused()`: `Bench.new` of an `Appendix` of the family's vignette (`Bench.family`) and the text, which the
bench binds, and `name`. 201, `made`.

#### `cases`, `GET /families/{family}/cases`
`Bench.family` (`NotFound`), then `case_of` each of its `cases`.

#### `case`, `POST /families/{family}/cases`
`Bench.family` (`NotFound`, 404). Within `refused()`: `Bench.case(family, appendices)`, or, for `replacing`,
`ValueError("<case> isn't a case of family <family>")` unless `families.family_of` gives this one, then
`Bench.replacement`. Their `NotFound` is the body's: 422. 201, `case_of`.

#### `tags`, `GET /tags`
The tags of `Bench.families()`, sorted, without repeats.

## world.py

### `endpoint_of(bench, name: str, spec: EndpointSpec) -> schemas.Endpoint`
The spec as the inventory declares it, its `url` among it, with the `Endpoint` `Bench.endpoint` gives: the title of
its engine (`Bench.title`), and its model, `model` its name and `serves` its digest; and `Inventory.takes_typed`. A
`LookupError` from `Bench.endpoint` is given as `problem`, its message, with `title`, `model` and `serves` `None`.

### Routes

#### `endpoints`, `GET /endpoints`
`endpoint_of` each of the inventory's endpoints, by name.

#### `endpoint`, `GET /endpoints/{name}`
The inventory's spec, else `NotFound("no endpoint '<name>' in the inventory")`, then `endpoint_of`.

#### `models`, `GET /models`
Each model the stored facts know (`Bench.facts`, the live heads of the `facts` threads) or an endpoint serves, by
name, with its facts dumped or `None`, and the endpoints serving it (the `model` of `Bench.endpoint`, skipping an
endpoint whose engine isn't stored).

#### `component`, `GET /components/{digest}`
`Rows.kind`; `NotFound("no component <digest> in the store")` when it is `None`. The kind, `Bench.title` and
`Store.get` dumped.

#### `kinds`, `GET /kinds`
A `Kind` for each kind in `chatddx.bench.KINDS`: its word, whether it is in `WRITTEN`, and
`BY_KIND[kind].model_json_schema()`.

#### `check`, `POST /components/check`
Within `refused()`: `Bench.check(component_of(body))`, a `LookupError` as `HTTPException(422)`. The digest and its
findings.

#### `scorer_code`, `GET /scorer-code`
Each of `chatddx.scorers.shipped.SCORERS` by entry point, its metrics by name; an entry point that publishes no schema
for the scorer's own params gives `NO_PARAMS`, which allows none. Signed in, as every route here.

## runs.py

### Constants
- `STREAM`: `"text/event-stream"`.
- `EVENTS`: the events' names, each in backquotes, joined by commas, for the routes' descriptions.

### `_families(bench, given: schemas.NewRun) -> list[Family]`
With `tags`: `Bench.families(tags)`, or `HTTPException(422, "no case tagged <tags joined by ' or '> for <login>")`
when there are none. With `families`: the families of `Bench.families()` with those ids, in the order given without
repeats; `HTTPException(422, "a run takes at least one case")` for none, and
`HTTPException(422, "no case <id> for <login>")` for the first id the person doesn't see.

### `_cases(bench, given: schemas.NewRun) -> list[str]`
Without `cases`, each of `_families`' cases. With them: the cases in the order given without repeats;
`HTTPException(422, "a run takes at least one case")` for none, and `HTTPException(422, "no case <case> for <login>")`
for the first that isn't among the `cases` of a family of `Bench.families()`.

### `_seeds(given: schemas.Seeds, replicates: int) -> tuple[int, ...]`
The seeds given, else `suggest_seeds` of the replicates asked, else of `replicates`.

### `_execution(held: Execution, given: schemas.NewRun) -> Execution | None`
`None` when the request gives neither a concurrency nor an order, so that `Bench.start` takes the endpoint's. Else
`held`, the endpoint's execution, with them in place, validated: a shuffled order keeps the endpoint's shuffle seed
when the endpoint shuffles, and draws one otherwise.

### `_new(bench, given: schemas.NewRun) -> Started`
Within `refused()`, `Bench.variation`, then the `Endpoint` `Bench.at(variation, given.endpoint)` gives: the endpoint
given, which must serve the variation's model, else the one serving it, and the one given for a hand-written
configuration. A `LookupError` from those, `NotFound` among them, is raised as `HTTPException(422)` with its message,
and a `ValueError` is a 422 through `refused()`. The cases of `_cases`; and, within `refused()`, `Bench.start` at that
endpoint with `_seeds(given, 1)`, the cleanup given and `_execution` of its spec's execution, whose `Refused` passes
to `STATUSES`.

### `_repeated(bench, run: UUID, given: schemas.NewAgain) -> Running`
`Bench.run` (`NotFound`); each case of the run's trial of a family of `Bench.families()`, else
`HTTPException(422, "no case <case> for <login>")`; and, within `refused()`, `Bench.again` of the run with
`_seeds(given, <the trial's seeds>)`, whose `Refused` passes to `STATUSES`.

### `_queued(request, response, bench, running: Running, score: bool) -> schemas.RunStartedData`
`Queue.put` of the started run for the person, at its endpoint, holding as many slots as its execution's concurrency,
and scoring it or not; `Location` the run's path (`url_path_for("run")`). Returns `run.started`'s data,
`events.py:started_of` the run, its trial and skeleton, and the skeleton's language (`language.language_of`).

### `job_of(placed: Placed | None) -> schemas.RunJob | None`
A job as `Queue.placed` places it, or `None`.

### `run_of(bench, started, finished, unscored=None, placed=None) -> schemas.Run`
The run as listed: its trial's parts, its skeleton's language (`language.language_of`), from its `About` the first
run of its start (`started_with`) and what it ran (`varied`, the edit, and `replaced`), its endpoint's name,
`Bench.described`, the scorers of `unscored`, each by its digest and `Bench.title`, or `None`, and `job_of(placed)`.

### `detail(bench, run: UUID) -> schemas.RunDetail`
`run_of`, and from `Bench.run` (`NotFound`) and `Store.run`: the rig; the finish's time and findings as `noted`;
`check_run`'s findings over the trial and canary set `Store.load` gives; each item's `item_of`; and `graded_of` each
of `Bench.scores_of` the run; and its job as `Queue.placed` places it.

### Routes
A run is named by a `UUID`, so anything else in its place is a 422.

#### `start`, `POST /runs`
`_new(bench, given)`, then `_queued` each of its runs, in order, each a job of its own. 202, with `Location` the first
run's path, and a `StartedRuns`: each run's `run.started` data, and each language left out, with its cases and why.

#### `again`, `POST /runs/{run}/again`
`Bench.run` (`NotFound`), then `_repeated(bench, run, given)` and `_queued`. 202, with `Location` the run's path and
`run.started`'s data.

#### `resume`, `POST /runs/{run}/resume`
`Bench.run` (`NotFound` for a run not the person's), then within `refused()` `Bench.resume` of it
(`"run <run> is finished"` and the gate's refusals, 422), then `_queued` with `score`. 202, with `Location` the run's
path and `run.started`'s data; `UnderWay` while the run has a job open (409).

#### `events`, `GET /runs/{run}/events`
`async`. `Bench.run` (`NotFound`), then `telling.py:told` for the person, after the `Last-Event-ID` header's id, else
from the first row. A `StreamingResponse` of `STREAM`, with `NO_STORE` and `X-Accel-Buffering: no`; its description
names the events.

#### `halt`, `POST /runs/{run}/halt`
`Bench.run` (`NotFound`), then `Queue.halt`, whose `LookupError` is
`HTTPException(409, "run <run> has nothing under way")`. 204.

#### `runs`, `GET /runs`
`Bench.runs(reaching=…, scored_by=…, started_with=…)`, `started_with` the query's `with`, kept by `trial`, then with
`unscored` by those of `Bench.outstanding`, each with its scorers left; the page `[offset:offset + limit]`, `limit`
from 1 to 200 and 20 by default; `Store.finished` and `Queue.placed` for the page.

#### `run`, `GET /runs/{run}`
`detail`.

#### `items`, `GET /runs/{run}/items`
`Bench.run` (`NotFound`), then each item of `Store.run`: its `item_of`, the outcome's why
(`chatddx.runner.outcome.outcome`), its vignette, call and turns dumped, and its `answer`,
`chatddx.scorers.answer.read` of its last call's response. Sensitive.

#### `rendered_again`, `GET /runs/{run}/rendered-again`
`Bench.run` (`NotFound`), then `chatddx.runner.prepare.rendered_again` of `Store.run`: each item's case and replicate,
whether its first request renders the same now (`same`), and why not.

## scores.py

### Routes

#### `score_now`, `POST /runs/{run}/scores`
`Bench.run` (`NotFound`); `HTTPException(422)`: `"run <run> hasn't finished"`,
`"scorer <digest> doesn't apply to run <run>"` for the first of `scorers` that doesn't, and
`"no scorer applies to run <run>"`. `Queue.put` of a job scoring the run by the scorers `events.py:scoring_of` gives,
at the run's endpoint, `""` for none, holding no slots; `UnderWay` while the run has one queued or under way (409).
202, with `Location` the run's scores' path and `run.scoring`'s data.

#### `scores`, `GET /runs/{run}/scores`
`graded_of` each of `Bench.scores_of(Bench.run(run), every)` (`NotFound`), `every` being the query's `all`: the latest
under each scorer by name, or every score, newest first.

#### `score`, `GET /runs/{run}/scores/{score}`
`graded_of` of `Bench.score_of(Bench.run(run), score)`: `NotFound` for a run that isn't the person's and a score that
isn't the run's.

#### `items`, `GET /runs/{run}/scores/{score}/items`
`Bench.score_of(Bench.run(run), score)`, then each of its score's items with its detail and judge calls dumped, and
its finish's findings, none when it hasn't finished. Sensitive.

## queue.py

### `standing(bench) -> schemas.Queue`
`Queue.standing` of the person, workers counted as seen within `settings.WORKER_LOST`.

### Routes

#### `queue`, `GET /queue`
`standing`.

#### `pause`, `POST /queue/pause`
`Queue.pause` of the person, then `standing`.

#### `resume`, `POST /queue/resume`
`Queue.pause(person, False)`, then `standing`.

#### `stop`, `POST /queue/stop`
`Queue.stop` of the person, `now` as given: the runs taken out and those halting.

## telling.py

### `KEEP_ALIVE`
15.0: the seconds a stream goes without an event before it is told `: keep-alive`, and asks the queue again whether
the run has a job open.

### `class Telling(bench, run: UUID, after: int)`
What one stream has told of a run, from `Bench.run` (`NotFound`) and the trial, skeleton and canary set `Store.load`
gives. `last` is the number of the last row told, `after` to begin with.

#### `rows() -> list[str]`
Each of `Store.rows_of(run, last)` as its events, as `sse` gives them, the last the row tells with the row's number as
its id; `last` moved on.

#### `said(said) -> list[str]`
What the worker said, each event validated by its model in `schemas.EVENTS`: an item's events after it was told ended
are dropped; `item.started` is told before the first of an item's deltas and tools when the stream didn't hear it;
each `item.tool` counted.

#### `tail(job: Job | None) -> list[str]`
`run.scored` of `Bench.scores_of` the run unless the stream was told one after the last score row it told, and the run
has a score; `error` when the job failed, `"job <id> for run <run> failed: <why>"`; and `done`, `halted` the job's
`halt`, `None` without a job.

#### The rows' events
- `RunStarted`: `run.started`, `events.py:started_of`, with `language.language_of` the trial's skeleton as its
  language.
- `CanaryCall`: `canary.ended`, `canary_of`.
- `RunItem`: `item.started` unless told, `item.tool` for each tool run past those told, `item.ended`.
- `RunFinished`: `run.noted` for each finding it holds, then `run.finished` with `check_run` of `Store.run`.
- `ScoreStarted`: `score.started`, `score_started_of` the scoring's scorer.
- `ScoreItem`: `score.item`, `score_item_of`.
- `ScoreFinished`: `score.noted` for each finding it holds; none for none.

### `told(held: AppState, person: Person, run: UUID, after: int) -> AsyncIterator[str]`
On a connection of its own, closed when the stream ends or is left, and a `Bench` for the person: listening for the
run (`Listener.heard`) before reading anything, so that no row lands unheard in between, a `Telling`'s rows; then,
while `Queue.open` gives a job, what is heard, each batch in order: the rows read again for `Rows` and `Lagged`, a
batch of them read once, `Telling.said` for `Events`, and `Queue.open` asked again after a `JobChanged` or `Lagged`;
`: keep-alive` after `KEEP_ALIVE` seconds without any. Then the rows that landed meanwhile and `Telling.tail` of the
run's latest job, `Queue.placed`'s. Its blocking work runs through `run_in_threadpool`.

## listening.py

### Constants
- `AGAIN`: 1.0: the seconds the listener waits after losing its connection, and at most for anything to happen.
- `BEHIND`: 1000: the messages a stream may hold unread before they are dropped for one `Lagged`.
- `Lagged`: what a stream is told when it fell behind or the listener lost its connection: it reads the rows again,
  and asks the queue again.
- `Heard`: `chatddx.store.notify.Message | Lagged`.

### `class Hearing(loop)`
What one stream hears, put on its loop by the listener. `put(heard)` keeps it, or, with `BEHIND` held, drops them all
for `Lagged`; `next(timeout) -> list[Heard]` gives everything held, waiting up to `timeout` seconds for something
(`TimeoutError`).

### `class Listener(conninfo: str)`
The app's one listening connection, on a daemon thread named `chatddx-listener`, started by the first stream.
`heard(run)`, an async context manager, gives a `Hearing` once the connection listens on the run's channel, and lets
it go as the stream ends; a `socket.socketpair` wakes the thread to listen at once. The thread waits on the
connection and the socket together (`select`), listens on the channels its streams follow and stops listening on the
rest, and puts each message `chatddx.store.notify.Assembler` gives back to each `Hearing` of its channel. A lost
connection is made again after `AGAIN` seconds, and every stream told `Lagged`. `stop()` ends the thread and waits for
it; a later stream starts it again.

## events.py

### `Named`
`tuple[str, BaseModel]`: an event's name, one of `EVENTS`, and its data.

### `sse(name: str, data: BaseModel, id: int | None = None) -> str`
`id: <id>` when given, `event: <name>`, `data: <the data as JSON>` and a blank line. The JSON holds no newline.

### `item_of(skeleton, item: RunItem) -> schemas.Item`
The item's key, the word of `chatddx.runner.outcome.outcome`, and `chatddx.runner.outcome.usage`.

### `graded_of(graded: chatddx.bench.Graded) -> schemas.Graded`
The scorer's digest and name, the score's id, scoring, start and whether it finished, each view's label
(`Graded.label`) and the `mean` of its values that aren't `None` (else `None`), each score item's value, and why it
gave none. Neither the score items' detail nor the scoring's findings.

### `scoring_of(bench, run, scorers) -> schemas.ScoringData`
The scorers of `Bench.scorers(run)`, or those of them in `scorers`, by digest and the thread's name, else its title.

### `started_of(started, trial, skeleton, language) -> schemas.RunStartedData`
The run, its trial's digest, skeleton, cases and seeds, the language its request is sent in, the endpoint's name, and
the skeleton's `greedy`.

### `item_started_of(case, replicate, seed)`, `tool_of(case, replicate, tool)`, `item_ended_of(skeleton, item)`, `canary_of(call)`, `score_item_of(item)`
- `item_started_of`: `item.started`.
- `tool_of`: `item.tool` with the tool run dumped.
- `item_ended_of`: `item.ended`, `item_of` and the outcome's why.
- `canary_of`: `canary.ended`, the phase, the canary's index and the call dumped.
- `score_item_of`: `score.item`, the score, the key, the view, the value and the detail.

### `score_started_of(bench, scorer, score) -> Named`
`score.started`: the scorer, its `Bench.title`, the score, and its views' labels (`Bench.labels`, else `view <i>`).

### `said_of(event: chatddx.runner.RunEvent) -> Named | None`
What the worker publishes of the runner's event; `None` for the rest, which rows tell:
- `ItemStarted`, as `item.started`: the key, and the seed.
- `Streamed`, as `item.delta`: the key, and the delta's kind, text and tokens so far.
- `ToolRan`, as `item.tool`: the key, and the tool run dumped.

### `judged_of(event: chatddx.bench.ScoringEvent) -> Named | None`
What the worker publishes of the scoring's event; `None` for the rest:
- `JudgeAsked`, as `judge.asked`: the key, the scorer, the view, the judge and the seed's index.
- `Streamed`, as `judge.delta`: the key, and the delta's kind, text and tokens so far.
- `JudgeAnswered`, as `judge.answered`: the key, the view, the call's judge and seed index, the verdict, and the call
  dumped.

The worker publishes `run.scoring` and `run.scored` itself (`src/chatddx/worker/worker.py`); `error` and `done` are
`telling.py`'s.

## The command
`chatddx api [--world DIR] [--bind HOST:PORT]` (`src/chatddx/cli.py:_api`): the World, from `--world` or
`CHATDDX_WORLD`; and `--bind`, else `settings.host()` (`HOST`, `localhost:8000` when unset), split at its last colon,
with brackets stripped from an IPv6 host. One that isn't `HOST:PORT` is `SystemExit("api: bind to HOST:PORT, not
'<bind>'")`. `uvicorn.run` serves `app(world.inventory, settings.database())`.

`chatddx portal` takes the same arguments and serves `chatddx.portal.app.app` the same way, its `SystemExit` saying
`portal:` (`src/chatddx/cli.py:_portal`). `chatddx run` takes them and `--watch`, and serves it with a worker in its
process (`worker=True`), saying `run:` (`src/chatddx/cli.py:_run`; agents/wip-portal.md).

`chatddx api` and `chatddx portal` run none: `chatddx worker` runs beside them (docs/worker.md, "Where it runs";
docs/worker-api.md, "The command").

## Tests
In `src/chatddx/api/test/`.
- `conftest.py`: `template` is `curated`, the test World as init-data lands it; `autocommit`; `alice`, with
  `PASSWORD`; `served`, the app on the test World's inventory, with a worker; `listening`, `served` by uvicorn on a
  thread; `client`, a `TestClient` over `https://testserver`; `signed`, the client with alice's bearer; `bob`, his
  bearer's header; `bench`, alice's; and the helpers `sign_in` and `bearer`.
- `test_people.py`: signing in and out by bearer and cookie, the same-origin check, validation, the statuses and codes
  (incl. Starlette's), the OpenAPI document and the command.
- `test_threads.py`, `test_families.py`, `test_world.py`: the reads, configurations by purpose, taking expectations,
  and what bob doesn't see of threads and families; that every read needs a session.
- `test_writes.py`: a configuration made from a recipe, and what is refused of one; chunks and expectations written
  new, edited and forked; a judge written over a judge configuration, and one over a generation configuration
  refused; what is refused, and with which status; an expectation's findings.
- `test_kinds.py`: the kinds with their JSON Schemas and what their references take; a component checked as a write
  would store it, with nothing written, the lints said, and what a write would refuse refused.
- `test_cases.py`: a family's cases, an appendix written for it, a case built of it and replaced by the appendix's
  edit, and an expectation carried onto the replacement; cases refused; a run naming a case that isn't one.
- `test_typed.py`: a typed case answered as a family, its vignette read back, and bob not seeing it; what can't be
  typed, among it a case without a language or in one that isn't a tag, and 429 past the day's quota.
- `test_following.py`: a fork with nothing to follow, then a proposal once the archive's configuration moved on, a
  stale head, following, and nothing proposed after; a configuration's corrected facts, none for bob, a stale head,
  following them, and none after.
- `test_scorers.py`: the scoring code shipped, as pickers read it; a scorer of the archive's forked with its labels, a
  view renamed by an edit and the history's labels, and one written new; scorers refused, and labels given where
  nothing has them.
- `test_said.py`: saying what holds of a thread, sharing it with bob and taking it back; refusals; deleting, listing
  and reading the deleted thread, and restoring it; a session needed.
- `test_variations.py`: looks, forks and edits; a look rendered and linted for its engine without an endpoint, and the
  same with its endpoint named; a look's languages, as written, translated and left out, each language's trial
  linted, and translations lacking a text leaving their language out rather than refusing the look; an engine
  swapped, a level landing on its nearest and the sampling following it, and an engine taken out or an endpoint
  serving another refused; a judge configuration looked at as a judge, with no reach; that a look's queries don't
  grow with its cases, counted on the test's database (the fixtures create the next test's meanwhile).
- `test_runs.py`: runs, over its own `served` on `world`, the test World on free ports, with a worker, each at the
  endpoint serving its engine: accepted and told by their events, numbered by their rows, which stream as they come,
  go on after an id, and are told alike by an app with no worker; a job in the queue until scored; a start of a run
  per language, listed by `with`, and the cases it leaves out; refused, among them an endpoint named that serves
  another engine, an engine taken out and a start that can send none of its cases... `joined` follows a run from
  before its job is claimed, the owner's queue paused until the stream has told its first row.
- `test_scores.py`: a judged run's scores, the latest and every one, one by id, and its items with their judge calls;
  the run scored again when asked, with the scoring's events after the run's rows; what bob can't read; the runs left
  to score with their scorers, and one leaving the listing once scored; a scoring refused for a run unfinished, a
  scorer that doesn't apply and a run with a job open, and halted; a session needed.
- `test_telling.py`: a stream joined mid-item told the item started and each tool once, and nothing of it once it
  ended; the listener fanning a run's messages out to two streams, again on another loop, and a stream that falls
  behind told `Lagged`.
- `test_queue.py`: a paused queue holding a run, which a stop takes out, left unfinished, and which resumes once the
  queue does; a finished run's and bob's resume refused; stopping, then stopping now, halting a run under way.

`src/chatddx/conftest.py` holds what the repl's tests share with these: `world`, the test World's inventory on free
ports (`chatddx.test.world.free_world`), and `fake`, `faked` on the test's store. `chatddx.test.world.faked(world, get,
endpoint=QWEN, delay=0.0)` is the fake vLLM serving an endpoint's engine as its start-up says, `delay` seconds a
token.

`chatddx openapi` prints the API's OpenAPI document, of an app made with an empty inventory, since it doesn't change
it (`src/chatddx/cli.py:_openapi`). `frontend/openapi.json` keeps it.

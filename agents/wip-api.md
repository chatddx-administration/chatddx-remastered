# The API: work in progress

The API is the bench's second edge, after the repl and before the portal (`agents/wip-bench.md`). It covers what a
person sees and does, over HTTP, for programs rather than for someone at a terminal. This file plans its port from the
old project.

"The old API" is chatddx-administration/chatddx at 504792c: `src/chatddx/django/api/` and its tests. Its manual,
`docs/api.md`, was removed at 7db5dac ("project-wide clean up") and is read here at 7db5dac^. Old permalink base:
https://github.com/chatddx-administration/chatddx/blob/504792cbeb09508f2c52912be29a3d8809d2fa1d/

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **Known going in** (the user):
   - The old API speaks of the cell throughout. "Cell" is the repl's word only (`agents/wip-bench.md`, K2 with R1),
     and the API doesn't take it. The guard already covers a new package:
     `src/chatddx/repl/test/test_vocabulary.py` checks every package but `chatddx.repl`. See "Where it says 'cell'".
   - The old API followed the repl's interface too closely. The commit that made it says so: "Remake the API on the
     new datamodel: the repl over HTTP, streamed" (110f9a5). See "Where it follows the repl" for each surprise and
     what replaces it.
2. **Decisions**, in the order they block (see "Options"): A1, who it is for; A2, the framework; A3, signing in.
   A4–A12 shape the endpoints. Decided so far: A9, S3.
3. **The plan** (see "The plan") assumes the takes. Its phase 0 is below the edges and needs none of A1–A3, so it can
   start first.

## The old API
### Where it came from
- It started as the "ChatDDX Swift API" (`src/chatddx/django/api.py` before 110f9a5): `POST /diagnose` took free-text
  `symptoms` and an agent's name and returned a differential, for a Svelte client ("swift mvp", 7c7ac74; "client:
  svelte-adapter node", 8e89253). A request without a session acted as `guest`. `/api/auth/` (452062d) answered 200 or
  401 for a session, for a proxy's forward auth (`src/chatddx/django/urls.py`).
- At 110f9a5 it was remade as the repl over HTTP: "Every repl command has its endpoint". The swift client's free text
  survived as `RunIn.vignette`, and the guest survived too.
- At 504792c it is Django with django-ninja, mounted at `/api/`: 8 modules of about 1,400 lines, and about 1,470 lines
  of tests. No client in the repository calls it; `agents/vllm.md` cites `/api/runs/{run}/exchange` once, as where the
  raw bytes could be read.

### Modules
| Module | Holds |
|---|---|
| `__init__.py` | the `NinjaAPI`, `GET /me`, and the error mapping: `NotFound`, `BranchNotFoundError` → 404; `Ambiguous`, `AmbiguousBranchError` → 409; `NotReady` by subclass (`Incomplete` 400, `NotOwn` 403, `NoSecret` 409); `CellRefused` → 422 with its refusals. It also adds the `Event` union to the OpenAPI document |
| `identity.py` | `Identified`: the Django session's user, or `guest`, made the first time it is met (`ensure_identity`); a CSRF check on a session's unsafe requests, none for the guest |
| `registry.py` | four routes per entity, for all 16 (`repo/entity_names.py`): the list (`?tag=`), one by name (`?owner=`), its versions, and the identity's runs with it |
| `cell.py` | the cell read from query or body parameters (`held`); `GET /cell` (`show`), `GET /reasoning`, `GET /scorers`, `POST /cell/save`, and `GET /cell/{entity}` for 12 entities |
| `runs.py` | `POST /runs`, `POST /batch`, `GET /runs`, `/runs/{run}`, `/runs/{run}/messages`, `/runs/{run}/exchange`, `POST /scores`, `GET /trials/{trial}` |
| `sending.py` | a run through the old bench's `Sending`, as server-sent events over WSGI or ASGI; the seed's rules; `Batch` |
| `showing.py` | Django models turned into schemas |
| `schemas.py` | the ninja schemas, the 8 events among them |

### Endpoints
Each old endpoint, the repl command it mirrored (`docs/api.md`, "The shell's commands"), and what it maps to now.

| Old endpoint | Repl command | Remastered |
|---|---|---|
| `GET /me` | — | `Bench.person` |
| `GET /registry/{entity}` `?tag=` | `configurations`, `stacks`, `cases` | `Bench.threads(word)`, `Bench.families(tags)`, `Inventory.endpoints` |
| `GET /registry/{entity}/{name}` `?owner=` | `show ENTITY NAME` | `Bench.thread`, `Bench.family`, and runs through `Bench.reaching` |
| `GET /registry/{entity}/{name}/versions` | — | `Catalog.history` |
| `GET /registry/{entity}/{name}/runs` | — | `Bench.reaching` |
| `GET /cell` `?configuration&stack&<slice>…&tag` | `show`, `show tag TAG…` | `Bench.skeleton`, `findings`, `reach`; the request rendered with placeholders is the repl's (`src/chatddx/repl/inspecting.py:_show_cell`) |
| `GET /cell/{entity}` | `show ENTITY` | the part's digest in the variation (`TriedVariation.held`) |
| `GET /reasoning` | `reasoning` | `Facts`, as `src/chatddx/repl/inspecting.py:reasoning` reads them |
| `GET /scorers` | `scorers` | `Bench.scorers`, and `reaches` against the variation's output schema |
| `POST /cell/save` | `save NAME` | `Bench.save` |
| `POST /runs` (`stream` true by default) | `run CASE [SEED]` | `Bench.start` with one case, `Running.send`, `Running.finish`, `Bench.score` |
| `POST /batch` | `batch TAG…` | the same, with the tagged cases |
| `GET /runs` `?limit&offset` | `runs [COUNT]` | `Bench.runs` |
| `GET /runs/{run}`, by id or prefix | `replay [RUN]` | `Bench.run(prefix)`, `Store.run`, `Bench.scores_of` |
| `GET /runs/{run}/messages`, `/exchange` | — | responses are in `RunItem.call`; requests are kept only as fingerprints, and rendered again by `Bench.rendered_again` |
| `POST /scores` `{run?}` | `score [RUN]` | `Bench.outstanding`, `Bench.score` |
| `GET /trials/{trial}`, by id or prefix | — | a trial is a component (`Store.get`), and its runs are among `Bench.runs` |

### Streaming
- `text/event-stream`, unless the body said `"stream": false`; then the response waited for the run's record.
- pydantic-ai's events, named by their `event_kind` (`part_start`, `part_delta`, `part_end`, `function_tool_call`,
  `function_tool_result`), came between the API's own, named by their `type`: `batch`, `run`, `answer`, `checked`,
  `error`, `scores`, `recorded` and `summary`.
- Runs ran in the request's thread and were written down as they went. A client that went away stopped the run,
  which was recorded as stopped, and stopped the batch (`tests/test_streaming.py`, over WSGI and ASGI).

### What it enforced
- `NotOwn`: another's configuration ran only once saved as one's own (403). Dropped in remastered: any digest runs
  without a thread (`agents/wip-bench.md`, "The old bench").
- `NoSecret` (409): a stack's `credential` named one of the identity's secrets. In remastered the credential names an
  environment variable (`src/chatddx/runner/gate.py:secret`).
- A seed on greedy sampling was refused (422), and `"none"` ran unseeded. In remastered see D3 (`agents/wip-repl.md`):
  `seed none` is gone, and a greedy skeleton gets a notice.

## Where it says "cell"
- Every module but `identity.py` and `registry.py`: `cell.py` (64 uses), `schemas.py` (`CellIn`, `CellOut`, 6),
  `sending.py` (6), `__init__.py` (`CellRefused`, "the cell is refused on its stack"), `runs.py` and `showing.py`
  (one each). In the tests, `test_cell.py` (37) and a few in three others.
- The paths `/cell`, `/cell/save` and `/cell/{entity}`, the OpenAPI tag `cell`, the operation ids `cell_{entity}`, the
  summaries ("The cell's {entity}…"), and the messages ("the cell is empty", "the cell has no configuration", "the cell
  has no stack").

None of it carries over. In remastered the cell is two things held apart (K2 with R1): the variation being tried
(`src/chatddx/bench/variation.py:TriedVariation`) and the endpoint. A request names both where it needs them (A5). The
paths go (see "Where it follows the repl"), and the messages are the bench's.

The guard's pattern, `(?<!ex)cell`, also matches "cancelled". Say "stopped", which is the runner's word anyway.

## Where it follows the repl
What would surprise someone who knows HTTP but not the repl, and what replaces it in "The plan":
1. **A command as a resource.** `GET /cell` is `show`: it names no resource and is built from a dozen parameters.
   `GET /cell/{entity}` is `show ENTITY`: the same thread `/registry/{entity}/{name}` gives, reached through the
   cell's parameters instead. Replaced by a configuration's `variation` (A5).
2. **Two endpoints for one thing.** `POST /runs` and `POST /batch` mirror `run` and `batch`. In remastered both are
   one trial and one run, of one case or of several (`agents/wip-repl.md`, "Built: 4b"). Replaced by `POST /runs`
   with `cases` or `tags`.
3. **A body flag picks the response's type.** `"stream": true` was the default, so a `POST` answered with an event
   stream unless told otherwise. HTTP says this with `Accept` (A7).
4. **A POST that acts on everything.** `POST /scores` without `run` scored every outstanding run, as `score` does.
   Replaced by scoring one run at a time, and a listing of what is left to score (A8).
5. **Ids by prefix.** `/runs/{run}` and `/trials/{trial}` took the first letters of an id, as the prompt shows them,
   and gave 409 when several matched. Such a URL can name another run tomorrow. Replaced by whole ids (A4).
6. **Names in paths.** `/registry/{entity}/{name}?owner=`. Names needn't be unique (`docs/catalog.md`, "Names"), they
   hold slashes and spaces (`plan (en, Qwen/Qwen3-8B-AWQ)`), and they change. Replaced by ids, with names as filters
   (A4).
7. **Lookups that guess.** A name meant the person's own thread, else a shared one; in remastered, a per-model name
   is also picked by the endpoint's model (`Bench.thread`, `Bench.configuration(name, engine)`). That is handy at a
   prompt. In a request the answer depends on another parameter, and on what else happens to share the name.
8. **The repl's seed.** A seed drawn below 100,000, "so the prompt stays readable", and `"none"`. Replaced by a seed
   from the trial's whole range (`src/chatddx/factors/trial.py:suggest_seeds`).
9. **Paths named after commands.** `/reasoning` and `/scorers`. The first returned `reasoning`'s screen: every
   reasoning variation on every stack. Replaced by `/models` (the facts) and scorers as threads.
10. **A read with a side effect.** `GET /me` set the CSRF cookie.
11. **Save as an upsert by name.** `POST /cell/save {name}` made a new version of your configuration of that name, or
    else a new configuration. Which of the two you got depended on what you had already named that way (A11).
12. **A guest.** Without a session a request acted as `guest`, and could run (A3).
13. **Status codes by exception type.** A `ValueError` from anywhere became 400 or 422, depending on the endpoint
    (A10).

## What remastered offers it
### The bench
- `Bench(conn, person, inventory, facts)`, one per caller and built per request, as the old one was
  (`agents/wip-bench.md`, "Forces" and S5).
- It finds things by name: `thread(word, name, model)`, `family(name)`, `configuration(name, engine)` and
  `chunk(part, name, engine)`. **Nothing finds a thread or a family by id** among what the person sees.
- It takes values: `skeleton`, `findings`, `reach`, `save` and `start` take a `TriedVariation`; `score`,
  `scorers_for`, `scoring` and `unscored` take a `RunStarted`.
- It lists: `threads(word)`, `families(tags)`, `tags()`, `runs()`, `reaching(digest)`, `scored_by(scorer)`,
  `outstanding()` and `scores_of(run)`.
- Its errors are `NotFound` and `Ambiguous` (`src/chatddx/bench/errors.py`). The catalog's "has expectations to choose
  from" stays a plain `LookupError` "until an API needs to tell an ambiguous expectation from a missing one"
  (`agents/wip-bench.md`, phase 2, step 10). This port is that API.
- `Bench.owner` gives "" for the person's own, which is the repl's way of showing it. The API gives a login.

### What the repl holds that an API needs too
These are rules rather than presentation, and they live under `src/chatddx/repl/`:
- `render.py:outcome`: an item's outcome (stopped, errored, unread, completed, invalid or valid), from its last call
  and `chatddx.scorers.answer.read`. The old API's `checked` event said the same.
- `render.py:usage`: the tokens an item used, from its responses' `usage`.
- `inspecting.py:PLACEHOLDERS`, `_abridged` and `_served_name`: the request rendered for showing.
- `reviewing.py:_outcomes`: a count of each outcome over a run's items.
- `inspecting.py:reasoning`: what the facts say per model and level.

The seed's range is the repl's too (`shell.py:MAX_SEED`, `drawn_seed`, `running.py:_seed_of`), but the API needs
only the trial's range. Left where they are, the outcome and the rendered request would be copied into the API, the
way the old project copied its rules into every edge (`agents/wip-bench.md`, "The old bench").

### The runner
- It is synchronous, and `Runner` refuses a connection that isn't in autocommit mode. `Running.send(on_event)` calls
  back on the caller's thread.
- `Running.stop()` ends a run after the calls under way. Hanging up a call in flight takes a KeyboardInterrupt on a
  serial run (`src/chatddx/runner/run.py:_send_serially`). A concurrent run passes a `halt` event to its calls
  (`src/chatddx/runner/send.py:send`, `rounds.py:converse`), but nothing outside `_send_concurrently` can set it. A
  server's request thread never gets a KeyboardInterrupt, so today **a client that goes away can't hang up the call
  under way**.
- A halted call still waits for its next chunk (`agents/wip-runner.md`, "Afterwards").
- The gate refuses a run before anything is written (`src/chatddx/runner/gate.py:Refused`).

### Identity
- `People.authenticate(login, password)`, `open_session(id)`, which gives a token, `session(token)`, which gives the
  person or None, `close_session` and `purge_sessions` (`src/chatddx/store/people.py`). Sessions last
  `settings.SESSION_TTL`, 12 hours.
- There is no guest, and no web framework, so nothing sets a cookie or checks CSRF, and nothing limits login attempts.
  Those belong to the framework's layer (`agents/wip-identity.md`, "Open").
- Roles exist, but nothing checks them (Z1 waits for the portal).

### Dependencies and setup
- There is no web framework. Where HTTP is spoken it is the stdlib: `src/chatddx/fake_vllm/server.py` serves with
  `ThreadingHTTPServer`, and `src/chatddx/runner/wire.py` is the client. D4 kept dependencies few, and `rich` is
  imported only under `chatddx.repl` (`agents/wip-repl.md`).
- `chatddx repl` loads the World and the facts once, and connects in autocommit mode (`src/chatddx/cli.py:_repl`). A
  server would load them at start and connect per request.
- `.env-example` has `HOST=localhost:8000`, which nothing reads.

### Sensitivity
- Vignettes are fetched from the World's sources and never stored. The case-derived records (completions, tool
  arguments and results, and the scorer's detail) are in schema `ledger` (`agents/wip-clearance.md`, "Completions
  derived from vignettes"). No policy says where they may be shown.
- The repl shows them at the terminal: `show case` prints the vignette, and `run` streams the completion.
- An API sends them over the network to whatever calls it. Clearance's takes count a database and an export target
  as endpoints to vet, but say nothing either way about an edge's client.

## Forces
- **B3.** The bench is the shared surface for what depends on who is asking. What doesn't may be read straight from
  the store and the World.
- **Authorization is a convenience.** Protection is clearance, enforced by the gate, and the database's grants.
- **One synchronous connection per bench.** A run holds it, and a thread, for as long as it lasts.
- **The docs' words**: configuration, variation, part, chunk, endpoint, engine, family and case, trial, run, score.
  Not cell, stack, slice, branch, trail or registry.
- **Stable ids.** Threads and families have integers, runs and scores UUIDs, components digests, and endpoints their
  names in the inventory. Names are for people and needn't be unique.
- **The portal comes next.** It will want a framework, cookies and CSRF. The API shouldn't choose otherwise without a
  reason.

## Options
### A1. Who it is for
- **C1. Programs**: scripts, notebooks for analysis and export (`docs/chatddx.md`, "On the table"), CI. Tokens, JSON,
  and an OpenAPI document.
- **C2. A browser client**, like the swift one: sessions in cookies, CSRF, CORS, and `EventSource`, which can only
  GET.
- **C3. The portal's backend.** The user named the portal a consumer of the bench of its own, so this isn't the plan.

Take: C1 now, keeping C2 possible: one sign-in serves both (A3), and W2 lets a run be followed by GET (A6).

### A2. The framework
- **F1. The stdlib** (`http.server`, as the fake vLLM uses). No dependency, but routing, validation errors, OpenAPI,
  cookies and CSRF are written by hand, and Python's docs say `http.server` isn't meant for production.
- **F2. FastAPI** (on Starlette, served by uvicorn). Pydantic models are the request and response types, as pydantic
  is everywhere here already, and the OpenAPI document comes from them; the old API served `/api/docs` and tested it.
  Plain `def` handlers run in a thread pool, which suits the synchronous bench and runner. Tests use `TestClient`,
  which needs httpx. It adds fastapi and uvicorn, and httpx for tests.
- **F3. Django with django-ninja**, as before. It brings sessions, CSRF, and an admin a portal could use. But
  remastered has no Django models, its store is psycopg, its people and sessions are its own, and Django's settings
  and apps would carry none of that.
- **F4. Litestar** or the like: F2's shape, less widely used.

Take: F2, imported only under `chatddx.api` as `rich` is only under `chatddx.repl`, perhaps as an optional dependency
group. Settle it together with the portal's framework. If the portal goes to Django, ninja takes the same pydantic
schemas, and little but the routing changes.

### A3. Signing in
- `POST /api/session {login, password}` → `People.authenticate`, then `open_session`. It returns the token and also
  sets it as an `HttpOnly`, `SameSite=Strict` cookie. `DELETE /api/session` closes it, and `GET /api/me` gives the
  person.
- A request carries the token as `Authorization: Bearer …` (programs) or as the cookie (browsers). A cookie's unsafe
  requests get a CSRF check; a bearer's don't need one.
- There is no guest: without a valid session, 401.
- When Keycloak arrives, a proxy authenticates and hands over the login (`agents/wip-identity.md`, the take on
  Keycloak). Sign-in is skipped, and the login maps to `person.login`.
- Not covered: personal tokens for scripts that run longer than a session (a table and a migration), and login rate
  limiting.

Take: as above. Add personal tokens when a script needs one.

### A4. How things are named
- **N1. By id** in paths: `/threads/{id}`, `/families/{id}`, `/runs/{uuid}`, `/components/{digest}` and
  `/endpoints/{name}`. Names are filters on lists, and a list returns every match. Nothing guesses. Variants per
  language or model are threads under their full names, until `agents/wip-variants.md` records them.
- **N2. By name**, as the repl does: `OWNER/NAME`, a per-model pick, and 409 when several match.

Take: N1, with whole ids only, since prefixes are the repl's. The bench gains lookups by id among what the person
sees (phase 0).

### A5. The variation being tried
This is the old cell taken apart (K2 with R1): a configuration with parts replaced, and an endpoint beside it.
- **V1. Stated in each request.** `configuration` is a skeleton thread's id and means its head. `parts` is
  `{PART: DIGEST}`, with `null` taking an optional part out. `endpoint` is given where it matters. The bench builds a
  `TriedVariation` from them. Nothing is stored until a run or a save, as in the repl. Responses give the compiled
  skeleton's digest.
- **V2. A digest.** `POST /skeletons {configuration, parts}` compiles the skeleton and stores it with its
  compilation; everything else takes `skeleton: DIGEST`. That makes "a variation being tried is just a digest"
  (`docs/chatddx.md`) literal, and the reads become cacheable GETs. But every variation looked at is stored, in an
  append-only store with no garbage collector. `save` would also need the base it forks from passed again.
- **V3. A variation held on the server**, which the client creates and patches. That is the cell as server state, the
  repl over HTTP again. Rejected.

Take: V1, with parts given by digest rather than by name: a recipe holds digests, and `GET /threads?kind=reasoning`
gives each head's. Accept `skeleton` beside it later, if a client wants to run a digest it already holds.

The base can move between a look and a run, since `configuration` means the head when the request comes. The run
records the skeleton it ran. If that isn't enough, `edit` (an edit's id) can stand in for `configuration`.

### A6. Where a run runs
- **W1. In the request**, as the old API and the repl do. The response is the stream, or it waits for the record. The
  runner sends on a thread of its own, and its events reach the response through a queue. A client that goes away
  halts the run (this needs a halt, phase 0), and the run is finished and scored whether anyone is listening or not.
- **W2. In the API's process, beside the request.** `POST /runs` returns 202 with the run's id, `GET
  /runs/{id}/events` streams it (a GET, so `EventSource` works), and `POST /runs/{id}/stop` stops it. Runs end with
  the process, and an unfinished run stays unfinished, since resuming isn't built (`agents/wip-runner.md`,
  "Afterwards").
- **W3. A worker**, to come (`agents/wip-bench.md`, "Forces"). It needs a queue, which the append-only store has no
  place for.

Take: W1 now, shaped so that W2 can follow: the events stay the same, and a run's record can always be read back,
since its rows land as they are written.

### A7. The stream
- It is asked for with `Accept: text/event-stream`. Otherwise `POST /runs` answers 201, with `Location`, once the run
  is finished and scored. There is no body flag.
- The events follow the runner's (`src/chatddx/runner/run.py:Event`), and each one's data is a JSON object:

| Event | From | Holds |
|---|---|---|
| `run.started` | `Running.started` | the run's id, trial, skeleton, endpoint, cases, seed, and whether it is greedy |
| `item.started` | `ItemStarted` | case, replicate, seed |
| `item.delta` | `Streamed` | case, replicate, kind (`reasoning`, `content`, `tool_call`), text, tokens so far |
| `item.tool` | `ToolRan` | case, replicate, the tool run |
| `item.ended` | `ItemEnded` | the item, its outcome and its usage (phase 0) |
| `canary.ended` | `CanaryEnded` | the canary call |
| `run.noted` | `Noted` | a finding |
| `run.finished` | `Running.finish` | `check_run`'s findings |
| `run.scored` | `Bench.score` | each scorer's score, or why it gave none |
| `error` | — | a failure after the stream began |

Take: as above. The gate's refusals come before the stream starts, as a 422.

### A8. Scoring
- **After a run**, at once, under every scorer that applies, as the repl does (`Bench.score`). `"score": false` leaves
  it to later.
- **Never at once**, only through `POST /runs/{id}/scores`.
- **What is left to score**: `GET /runs?unscored=true` lists the person's finished runs with the scorers each is left
  to be scored by (`Bench.outstanding`). The client scores each one; there is no request that scores everything.

Take: score at once, with the opt-out, because what a client most wants after a run is how it scored. Plus the
listing.

### A9. Case-derived content over HTTP
- **S1. As the repl shows it.** Vignettes, completions, tool runs and the scorer's detail go to whoever signed in.
- **S2. Never.** Outcomes, fingerprints and score values only. Such an API can't show an answer.
- **S3. S1, but in their own places.** The vignette at `/families/{id}/vignette`, items at `/runs/{id}/items`, and
  deltas only in the stream; nothing else carries any. When clearance gets a policy for edges, it gates those few
  places.

Decided: S3. The question is raised in `agents/wip-clearance.md` ("Open", 6): an edge that shows case-derived content
is a destination too.

### A10. Errors
| Raised | Status |
|---|---|
| no session, or an expired one | 401 |
| `NotFound`, which includes a thread of another kind than the route takes | 404 |
| `Ambiguous` | 409 |
| `gate.Refused` | 422, as the old cell's refusals were |
| a request that doesn't validate, or a variation the bench refuses: `TriedVariation.set`'s `ValueError`, or a digest that isn't a chunk of that part | 422 |

Bodies are `{"detail": "…"}`, FastAPI's shape. `ValueError` isn't mapped wholesale: each route catches the errors it
means.

### A11. Saving
- **K1. `save` as it is now**: a new version of your configuration of that name, or else a fork.
- **K2. Two requests.** `POST /threads/{id}/forks {name, parts}` forks configuration `id` (201, with `Location`).
  `POST /threads/{id}/edits {parts}` adds a version to a configuration you own: 201, or 200 with "unchanged" when the
  digest is already its head. The bench gets `fork` and `edit`, and the repl's `save NAME` picks between them as it
  does now.

Take: K2.

### A12. Paths
The API is mounted at `/api/`, as before. The OpenAPI document is at `/api/openapi.json` and its pages at `/api/docs`.
There's no version in the path until a second version exists.

## The plan
This assumes the takes.

### Endpoints
| Request | Does | Built on |
|---|---|---|
| `POST /api/session` | signs in: the token, and the cookie | `People.authenticate`, `open_session` |
| `DELETE /api/session` | signs out | `People.close_session` |
| `GET /api/me` | the person: id, login, name, roles | `Bench.person` |
| `GET /api/threads?kind=WORD&name=&owner=&tag=` | the threads the person sees of the kinds `WORD` names (`KINDS`): id, kind, name, title, owner, tags, and the head's edit and digest | `Bench.threads` |
| `GET /api/threads/{id}` | one: its name, description, owner, collaborators and tags, its head and title, and for a configuration its recipe | a lookup by id (new); `Catalog.recipe`, `Catalog.title` |
| `GET /api/threads/{id}/edits` | its versions, the head last | `Catalog.history` |
| `GET /api/threads/{id}/variation?PART=DIGEST…&endpoint=&tag=…&seed=` | a configuration with parts replaced: its skeleton's digest; whether it is greedy; each part's digest, title and description; the request rendered with placeholders; the lints at `endpoint`; and each scorer view's reach over the cases with any of the tags. With nothing replaced, the configuration itself | `Bench.skeleton`, `findings`, `reach` |
| `POST /api/threads/{id}/forks` | `{name, parts}`: a configuration of your own | `Bench.fork` (new) |
| `POST /api/threads/{id}/edits` | `{parts}`: a new version of your configuration | `Bench.edit` (new) |
| `GET /api/families?tag=…&name=` | the cases the person sees: id, name, tags, language, the case's digest | `Bench.families` |
| `GET /api/families/{id}` | one, with the expectation under each schema | a lookup by id (new); `Bench.expectation_schemas`, `Bench.expectation` |
| `GET /api/families/{id}/vignette` | the vignette, fetched from the World | `Inventory.source(…).fetch` |
| `GET /api/tags` | the tags on the families the person sees | `Bench.tags` |
| `GET /api/endpoints` | each endpoint: its engine and the engine's title, the model, URL, `max_jobs`, and the sources it is cleared for | `Inventory`, `Bench.model`, `url_of` |
| `GET /api/endpoints/{name}` | one | as above |
| `GET /api/models` | what the facts know of each model: reasoning levels, default, budget, sampling; and the endpoints serving it | `Facts` |
| `GET /api/components/{digest}` | the component, and its title | `Store.get`, `Catalog.title_of` |
| `POST /api/runs` | `{configuration, parts, endpoint, cases or tags, seed?, score?}`: a run, streamed when `Accept` asks for it | `Bench.start`, `Running.send`, `Running.finish`, `Bench.score` |
| `GET /api/runs?limit=&offset=&trial=&reaching=&scored_by=&unscored=` | the person's runs, newest first | `Bench.runs`, `reaching`, `scored_by`, `outstanding` |
| `GET /api/runs/{id}` | its start and finish, findings, what ran (`described`), each item's outcome and usage, and the latest score under each scorer | `Bench.run`, `Store.run`, `Bench.described`, `Bench.scores_of` |
| `GET /api/runs/{id}/items` | its items: calls, responses, turns and tool runs | `Store.run` |
| `GET /api/runs/{id}/rendered-again` | for each item, whether its first request renders now as it was sent | `Bench.rendered_again` |
| `GET /api/runs/{id}/scores` | the latest score under each scorer | `Bench.scores_of` |
| `POST /api/runs/{id}/scores` | `{scorers?}`: scores it now | `Bench.score` |

Dropped from the old API:
- `/registry/*` and `/cell*`, replaced by `/threads`, `/families` and `variation`;
- `/batch` and `/scores`, replaced by `/runs`;
- `/reasoning`, replaced by `/models`;
- `/scorers`: a scorer is a thread, and `variation` gives its reach;
- `/trials/{trial}`: a trial is a component, and `runs?trial=` gives its runs;
- `/runs/{run}/messages` and `/exchange`, replaced by `items` and `rendered-again`.

### Modules
`src/chatddx/api/`:

| Module | Holds |
|---|---|
| `app.py` | `app(world, facts)`: the routers and the error handlers, with the World and the facts loaded once |
| `people.py` | signing in, the person a request acts for, the CSRF check on cookies, and a bench per request on a connection in autocommit mode |
| `schemas.py` | the request and response models |
| `threads.py`, `families.py`, `world.py`, `runs.py` | the routes: `world.py` has endpoints, models and components |
| `events.py` | the runner's events as server-sent events |

On the command line it is `chatddx api [--world DIR] [--facts PATH …] [--bind ADDRESS]`, served by uvicorn. `--bind`
could default to `HOST`, which would give that variable a reader.

### Phases
0. **Below the edges.** None of this needs a framework.
   1. Move an item's outcome and usage out of `src/chatddx/repl/render.py`, and the request rendered for showing out
      of `src/chatddx/repl/inspecting.py`, into the bench. The old bench had `bench/outcome.py`. The repl calls them
      there.
   2. Lookups by id among what the person sees: a thread, a family, and a run by its whole id. Anything else is
      `NotFound`.
   3. A variation from a configuration's id and `{PART: DIGEST or None}`. Each digest must be a chunk of that part
      (`Rows.kind`).
   4. `Bench.fork` and `Bench.edit`, with `Bench.save` composing them for the repl (A11).
   5. Typed catalog errors: "has expectations to choose from" raised as `Ambiguous` through `Bench.expectation` and
      `Bench.scoring` (`agents/wip-bench.md`, phase 2, step 10).
   6. In the runner, `Running.halt()`, which can be called from another thread and hangs up the calls in flight, on
      serial runs too. `send` takes a `halt` already.

   Tests: the bench's (`src/chatddx/bench/test/`) and the runner's, with the repl's passing unchanged.
1. **The app.** The dependency (A2), `app.py`, `people.py`, `/session`, `/me`, the error mapping, `/api/docs` and
   `chatddx api`. Tests with `TestClient`: 401 without a session; a bearer and a cookie both work; a cookie's POST
   needs its CSRF check; the error bodies; the OpenAPI document is served.
2. **Reads**: threads, families and the vignette, tags, endpoints, models and components.
3. **Variations**: `variation`, `forks` and `edits`.
4. **Runs.** `POST /runs` as JSON and as a stream, halted when the client goes away; the listing and its filters; one
   run, its items, and `rendered-again`. The tests serve the sample World with the fake vLLM in a thread
   (`src/chatddx/repl/test/conftest.py:fake`, moved where both packages can use it).
5. **Scores**: a run's scores, scoring it, and `unscored`.
6. **Docs.** Material for a `docs/api.md` kept here, as `agents/wip-bench.md` keeps material for the bench's, and
   a proposal for `agents/wip-identity.md` (the framework and signing in).

The tests live in `src/chatddx/api/test/` and use the seeded sample (`src/chatddx/conftest.py:seeded`), as the bench's
and the repl's do. The guard needs no change.

## Left out
- **Free-text vignettes** (`RunIn.vignette`, the swift client's `symptoms`). A case is a source's vignette, by id,
  fetched from the World and never stored. Running pasted text would take a source that holds it.
- **`/api/auth/`** for a proxy's forward auth. Once Keycloak is in front, that is the proxy's job.
- **Endpoints with a credential.** As in the repl, the secret comes from an environment variable
  (`src/chatddx/runner/gate.py:secret`), not from the person's secrets.
- **Scoring every outstanding run in one request** (A8).
- **"Run N of trial X"**, which the repl says after a run. `runs?trial=` gives the count.
- **Judges**: judged views show as "not yet", as in the repl.

## Open
- **A stream through a proxy** needs buffering off. The old API sent `Cache-Control: no-cache` and
  `X-Accel-Buffering: no`.
- **Long requests.** A batch of hundreds of cases is a request that lasts minutes, holding a connection and a thread.
  If that hurts, move to W2.
- **`Bench.runs` reads every run the person owns**, and the listing pages afterwards. Page in the store once that is
  slow.
- **Concurrent writers.** Two requests can save the same name at once (`docs/catalog.md`, "Concurrent writers").
- **Drift** between a look and a run (A5).
- **Variants.** A client finds `plan (en, Qwen/Qwen3-8B-AWQ)` by its full name. Option B in `agents/wip-variants.md`
  would let it filter by model and language instead.
- **An unsaved variation's runs are titled by their recipe** (`agents/wip-repl.md`, "Left from 4c"), in the API as
  in the repl.

## Surprises
- `.env-example`'s `HOST=localhost:8000` is read by nothing in `src/`.
- The "cell" guard's pattern matches "cancelled" (`src/chatddx/repl/test/test_vocabulary.py:CELL`).
- The old `docs/api.md` is missing at 504792c; it was removed at 7db5dac.

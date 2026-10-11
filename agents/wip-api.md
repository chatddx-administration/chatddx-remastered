# API

A candidate for `docs/api.md`. Its reference is `agents/wip-api-api.md`, a candidate for `docs/api-api.md`; below,
those two names mean these two files until they move. What is still open is in "Outstanding", at the end, which
stays behind when they do. The plan this was rewritten from, with the old API's survey and the options weighed, is
`agents/wip-api.md` at 100a078.

The API is a person's view of the rig and runner over HTTP:
They see the threads and families they own or that are shared with them, the World's endpoints and models, and
their own runs. They try a configuration with parts replaced, fork it or add a version to their own, and run it,
answered as JSON or as a stream of events.

The endpoints are in the OpenAPI document the API serves, at `/api/openapi.json`, with pages at `/api/docs`.
This document describes what the API does and why it is shaped like it is.

The API builds on the bench, which is what one person sees and does whatever the edge (agents/wip-bench.md), and on
the runner, which sends a run and records it as it goes (agents/wip-runner.md), over the store, the catalog and the
World. It is the bench's second edge, after the repl and before the portal (agents/wip-portal.md).

## How it is shaped
### Who it is for
Programs, such as scripts, notebooks for analysis and export, and CI, and browsers, the portal among them where it is
interactive. A session is carried either way, as a bearer token or as a cookie, and the checks a cookie needs are
there from the start rather than added later.

### HTTP's shape, not the repl's
The API before this one was the repl over HTTP, an endpoint per command. This one is shaped by what someone who knows
HTTP but not the repl expects:
- **Resources, not commands.** What the repl's `show` prints is a configuration's variation; a run of one case and a
  batch of many are both a run, made by one request.
- **Ids, not names.** Things are named by stable ids in paths, and names are filters on lists. Nothing guesses: no
  `OWNER/NAME`, no pick by model, no prefix of an id (see "Ids").
- **Headers say what HTTP says with them.** `Accept` asks for a stream; there is no body flag for it.
- **No guest.** A request without a session is refused.
- **Statuses by meaning.** A refusal's status says what was wrong with the request, not which exception raised it
  (see "Errors").

### What it rests on
- **The bench is the surface for what depends on who is asking**: what a person sees, finds and owns. What doesn't
  depend on them is read straight from the store and the World: a component by its digest, the endpoints and the
  models.
- **What a person sees is a convenience, not protection.** It decides what is relevant to show them. Protection is
  clearance, which the runner's gate enforces, and the database's grants (agents/wip-clearance.md).
- **The docs' words**: configuration, variation, part, chunk, endpoint, engine, family and case, trial, run, score. The
  repl's "cell" is the repl's alone, and a test holds every package but the repl to that.

## Serving
`chatddx api [--world DIR] [--facts PATH …] [--bind HOST:PORT]` serves the API with uvicorn, on FastAPI and Starlette.
It loads the World and the facts once, and binds to `HOST` from the environment unless told otherwise. Each request
gets a database connection of its own, in autocommit mode, as the runner needs, and a bench for the person it acts
for. The API is mounted at `/api/`, and there's no version in the path until a second version exists.

A deployment serves it behind TLS: the session cookie is only ever sent over HTTPS, or to `localhost`.

## Signing in
A person signs in with a login and a password, and gets a token for a session that lasts 12 hours. The answer also
sets the token as a cookie, `__Host-chatddx-session`: `HttpOnly`, `Secure`, `SameSite=Lax`, for every path of this
host, and as long as the session lasts. A wrong login is refused with the same answer as a wrong password. Signing
out ends the session the request acts in and drops the cookie, and `/api/me` says who the person is.

Every other request acts in the session of its `Authorization: Bearer` token, else of its cookie. Without either, or
with one that has ended, it is refused with `WWW-Authenticate: Bearer`.

### Requests from other sites
A browser sends the cookie with requests from any page, so a cookie's request that changes something must come from
this site's own pages, and so must signing in, which a forged sign-in would abuse. Where the browser sends
`Sec-Fetch-Site`, it must be `same-origin` or `none`; else `Origin`, where it is sent, must name this host. A request
with neither header isn't a browser's on another page's behalf, and passes. A bearer's requests aren't checked, since
no browser adds a bearer by itself.

The check stands in for a CSRF token, which would need one stored per session.

## Ids
Threads and families are named by their integer ids, runs by their whole UUIDs, components by their digests, and
endpoints by their names in the inventory. Names are for people: they needn't be unique, they hold slashes and
spaces, as `plan (en, Qwen/Qwen3-8B-AWQ)` does, and they change. So a list takes a name as a filter and returns
every match, and a path takes an id. An id's prefix, handy at a prompt, could name another run tomorrow, so only
whole ids are taken.

A configuration made per language or model is a thread under its full name, until variants are recorded as such
(agents/wip-variants.md).

## What a person sees
- **Threads** of a kind, by the word the repl uses for it: configuration, each part, tool, scorer, judge,
  expectation, expectation schema, canary set, model or engine. A thread gives its kind, name, title, owner, tags and
  head, and on its own also its description, collaborators, language, the edit it was forked from, and for a
  configuration its recipe. Its versions come oldest first.
- **Families**, each with the case of its current vignette, filtered by tag or name. A family on its own adds its
  description and collaborators, the case's appendices, and, under each expectation schema the person sees, the
  expectation its case is scored against: their own, so a schema under which they only see shared ones has none
  (`agents/wip-bench.md`, "What a person is scored against"). Several to choose from don't fail the request; that
  schema says so instead. Each schema also lists the expectation threads shared with the person they could take.
- **A family's vignette**, fetched from the World's source, and whether it still is the text the case was made from
  (unknown under a keyed fingerprint). It is case-derived (see "Case-derived content").
- **Tags** on the families the person sees.
- **Endpoints**: each one's engine and the engine's title, the model it serves, its URL and host, how many requests
  it takes at once, its credential's name, and the sources it is cleared for. One whose engine isn't stored, or whose
  URL can't be told, says why rather than failing the listing.
- **Models**: what the facts know of each, and the endpoints serving it.
- **Components**: any stored component by its digest, with its kind and title. These are the same for everyone.

A thread, family or run the person doesn't see is "not found", the same as one that doesn't exist. Their own deleted
threads are listed apart, and each can still be read by its id, with its versions, so that it can be restored.

## Trying a variation
A configuration's variation is the configuration with some of its parts replaced. A request states it whole each
time: the configuration's id, and each part to replace with the digest of a chunk of that part, or with nothing, to
take an optional part out. Nothing is stored by looking. The configuration means its head when the request comes, so
a variation looked at and one run moments later can differ if the configuration moved in between; each run records
the skeleton it ran.

A look at a variation gives:
- the head it was built on, the digest of the skeleton it compiles to, and whether its sampling is greedy;
- each part's chunk, its title and what it holds, and whether it was replaced;
- the request it would send, with placeholders for the case and, without an endpoint, for the model;
- a seed, drawn from the trial's whole range unless one is given, and given back so a run can send the same;
- at an endpoint, the lints of it as a trial over the cases with any of the given tags, else over every case the
  person sees; where no case has the tags, the checks that need no case still apply;
- for each view of each scorer, whether the variation's output offers what the view reads, which families have no
  expectation it picks something from, and which have several to choose from.

A case with expectations to choose from is listed apart, as `choosing`, rather than as one without
(`agents/wip-bench.md`, "What a person is scored against"). An unsaved variation is linted in its recipe's
language, since the language of a skeleton otherwise comes from its stored compilations, which it hasn't got yet.

A variation the bench refuses is unprocessable: a digest that isn't a stored chunk of its part, a part that can't be
taken out, parts that don't compile together, or a parameter the request doesn't know, so that a misspelt part is
refused rather than ignored. A look's queries don't grow with the number of cases it is over.

## Forking and editing
Keeping a variation is two requests, rather than one save by name as the repl's `save NAME` is, which makes a new
version of the person's configuration of that name if there is one, and a new configuration otherwise:
- **Fork** any configuration the person sees, with parts replaced and a name, into a new configuration of their own.
  Names needn't be unique, so forking twice under one name makes two configurations.
- **Edit** a configuration of their own, with parts replaced over its head: a new version, or nothing when the
  variation is the head already, which is answered as such. Another's configuration can't be edited, and is "not
  found" as "no configuration N of yours".

Chunks and expectations are written the same way, with a component where a configuration takes parts, as its JSON
as a component's own request gives it (`agents/wip-bench.md`, "Components"):
- **New**: a component, a name, and the language of its text when it has one, as a thread of the person's own; or a
  recipe, by the chunks' digests for its parts, its purpose and its appendix layout, made into a new configuration
  of their own with no origin.
- **Fork** any thread of those kinds the person sees, from its head or from a component given in its place.
- **Edit** a thread of their own with a component.

Every edit names the head it was made on, and is a conflict when the thread has moved on since, so a change made on
an older version never undoes what came after it. What is written comes back with what the lints say of it, such as
an expectation whose data its schema refuses, which is written all the same.

## What is said about a thread
Its owner says what holds of a thread in one request, giving only what changes: its name, or none so that its title
shows; its description; its tags and who it is shared with, each as the whole list, people by login; and whether it
is deleted (`agents/wip-bench.md`, "What is said about a thread"). Deleting is also a request of its own. What holds
afterwards comes back. A deleted thread is restored before anything else is said of it. Another's thread is "not
found" as "no configuration N of yours"; a login that names nobody, an empty name or tag, and taking a description
away are unprocessable.

## Appendices and cases
A family lists its cases at its current vignette, its default first, each with its appendices and the expectation
it is scored against under each schema (`agents/wip-bench.md`, "Appendices and cases"). The person writes an
appendix for a family from its text, and builds a case from appendices they see, in order, or stores the replacement
of a case a repair left at an earlier vignette. An appendix's new version, written as any edit, answers with each case
it replaced. An expectation is carried onto another case of its family by an edit of its own, which names the head
it was made on.

## Following an origin
A fork whose origin has moved on has a proposal: what following would keep, with the base, the origin's head, what
the fork varies, and for a configuration the recipe it compiles from (`agents/wip-bench.md`, "Following an
origin"). Asking for it gives nothing when there is none. Following is an edit of the person's own fork, which names
the head it was made on and comes back with what the lints say. Following a fork with nothing to follow, or whose
changes no longer fit, is unprocessable.

## Taking expectations
A person is scored against their own expectations only, so they take the shared ones (`agents/wip-bench.md`,
"Taking"):
- **For many cases**, by family, under one schema, from any owner or one named. The answer says, for each family,
  whether its case was taken, and into which thread, or was kept as theirs, has several owners' to choose from, or
  has none shared. Nothing of theirs changes, so the request is safe to repeat. A family the person doesn't see, or an
  owner who doesn't exist, is unprocessable.
- **One thread**, an expectation shared with them, into a thread of their own. When they have their own of its case
  under its schema, it is a conflict unless the request says to replace theirs, which deletes it in the same write.

## Runs
### Starting one
A run is a configuration's variation, at an endpoint, on the cases of some families, picked by id or by tag, or on
cases named by digest, each one of a family's current cases, with one seed, drawn from the trial's whole range unless
given. A family stands for its default case, because a family is what the person sees and picks; a case with
appendices is named. The run gives back the cases' digests.

The run is started within the request, so whatever refuses it does so before anything is sent. The gate refuses an
endpoint that doesn't serve the trial's engine, isn't cleared for a sensitive source among the cases', or lacks its
secret; tools that would get a sensitive source's content; and an endpoint that doesn't answer. The request is
refused too for anything its body names that the person doesn't see (a configuration, an endpoint, a family), and
for tags no case has.

### Where it runs
A started run is sent on a thread of its own, with a database connection of its own, and is then finished and scored
under every scorer that applies to it, unless asked not to be. That happens whether or not anyone is still
listening. Its rows land as they are written, so it can be read back at any point.

### The stream
A request that asks for `text/event-stream` gets the run's events as they come; otherwise it is answered with the run
once it is finished and scored. Both are answered 201, with the run's path as `Location`, and a stream is sent
unbuffered and uncached so a proxy passes it on as it comes. Each event's data is one line of JSON, and their models are
among the OpenAPI document's schemas.

| Event | When | Holds |
| --- | --- | --- |
| `run.started` | first | the run, its trial and skeleton, the endpoint, the cases, the seed, and whether sampling is greedy |
| `item.started` | an item is about to be sent | its case and replicate, and its seed |
| `item.delta` | a chunk of an answer streams in | its case and replicate, the kind (reasoning, content or a tool call), the text, and the tokens so far |
| `item.tool` | a tool has run for a call | its case and replicate, and the tool run |
| `item.ended` | an item is recorded | its case and replicate, its outcome and why, and its tokens |
| `canary.ended` | a canary call is recorded | the phase, which canary, and the call |
| `run.noted` | something was noted along the way, such as a case that couldn't be read | a finding |
| `run.finished` | the run is recorded as finished | what checking it found |
| `run.scored` | it is scored | each scorer's score, or why it gave none |
| `error` | the run failed after the stream began | why |

An item's outcome is stopped, errored, unread, completed, invalid or valid, by its last call and the answer read from
it.

### Going away
A client that goes away halts its run: a stream's at once, and a request waiting for its answer within half a
second. The calls under way are hung up and recorded as stopped, and the run is finished and scored as always.

### Reading runs
- **A person's runs**, newest first, a page at a time, filtered by trial, by a digest their trial is built on, or by
  a scorer that scored them. Each says what ran: its trial, skeleton, engine, endpoint, cases, seeds, and a line
  saying it as people read it.
- **A run** adds when it started and finished, the rig it ran on, what it noted as it went, what checking it finds
  now, each item's outcome and tokens, and its latest score under each scorer.
- **A run's items**: each call as it was recorded, with its response and tool rounds, and why the item ended as it
  did. They are case-derived.
- **Whether each item renders again** as it was sent: only a request's fingerprint is kept, so the request is
  rendered again from the trial and the source, and compared.

Only the person's own runs are seen; a collaborator on a run doesn't see it.

## Scoring
A run is scored as soon as it is finished, under every scorer that applies, because how it scored is what a client
most wants after a run; a request can ask for it to be left. A score gives each item's value under each view, and
each view's mean over the items, or why the scorer gave none.

## Case-derived content
What is made from a vignette is shown to whoever signed in, but only in its own places, so that a policy for edges
can gate those few when clearance has one (agents/wip-clearance.md):
- a family's vignette;
- a run's items;
- a run's stream: the deltas, the tool runs, and why each item ended.

Nothing else carries any. Why an item ended can quote the answer, since checking it against a schema names the value
it refused, so it is in the items and the stream only. For the same reason a score gives values but neither the
scorer's detail nor the scoring's findings.

## Errors
A refusal's body is `{"detail": "…"}`, except where a request doesn't validate: then it lists where.

| Status | When |
| --- | --- |
| 401 | No session, one that has ended, or a wrong login or password. |
| 403 | A cookie's request that changes something, or a sign-in, from another site's page. |
| 404 | What the path names isn't there or isn't seen by the person, a thread is of another kind than the route takes, a source doesn't hold a vignette, or a configuration to edit isn't the person's. |
| 409 | Taking an expectation the person has their own of, without saying to replace it; an edit or a follow whose head has moved on. |
| 422 | A request that doesn't validate or names a field it shouldn't; a kind that isn't one; a variation the bench refuses; a query or body naming what the person doesn't see; tags no case has; the gate's refusal of a run; taking an expectation that is the person's already; a component the bench refuses, or parts for what isn't a configuration and a component for what is; what is said of a thread that the bench refuses, or of a deleted one; following with nothing to follow; a case of appendices or a replacement the bench refuses; carrying an expectation outside its family; a run naming a case that isn't a current one of a family the person sees. |
| 500 | A run that failed on its thread, for a request waiting for its answer. |

An edit that changes nothing is answered 200 with the head; what is made is answered 201; a deletion 204.

## Not covered
- **Free-text vignettes.** A case is a source's vignette, fetched from the World and never stored. A typed text
  becomes a source of its own (agents/wip-portal.md, "Typed cases").
- **A proxy's forward auth**: once a proxy authenticates, that is its job.
- **A person's secrets.** An endpoint's credential comes from an environment variable, as in the repl.
- **Scoring every outstanding run in one request.** A client scores one run at a time.
- **"Run N of trial X"**, which the repl says after a run. A run's trial lists its runs.

## Tests
The tests start from the sample as `chatddx init-data` lands it, with alice signed in by a bearer token and bob for
what isn't his to see. They speak to the app through Starlette's test client over HTTPS, since the cookie is only
sent over it. Runs are sent to the fake vLLM serving the sample World on ports nothing else uses.

The test client runs a streamed response to its end whether or not its reader hangs up, so the tests of going away
serve the app with uvicorn on a thread, and speak to it over a socket.

## Terms

| Term | Meaning |
| --- | --- |
| Session | A person signed in: a token, carried as a bearer or as a cookie, for 12 hours. |
| Look | Asking for a configuration's variation: what it would send, its lints and its reach, with nothing stored. |
| Parts | The chunks a variation replaces over a configuration, each by its digest, or nothing to take it out. |
| Head | A configuration's latest version, which a request's variation is built on. |
| Fork | A new configuration of one's own, made from one the person sees. |
| Edit | A new version of a configuration of one's own. |
| Take | A fork of an expectation shared with the person, so that it counts. |
| Saying | Writing what holds of a thread: its name, description, tags, collaborators, and whether it is deleted. |
| Reach | Of a scorer's view: whether a variation's output offers what it reads, and which cases have an expectation it picks from. |
| Run | A variation sent at an endpoint on some cases with one seed, recorded as it goes. |
| Item | One case's request in a run, with its calls. |
| Outcome | How an item ended: stopped, errored, unread, completed, invalid or valid. |
| Event | One step of a run, as its stream tells it. |
| Halt | Ending a run's sending early, hanging up the calls under way. |
| Case-derived | Made from a vignette, or quoting what was: the vignette, answers, tool runs. |

## Outstanding
What is still open, carried over from the plan. It doesn't move to `docs/`.

### Start with this
0. **Go through open items, reiterate and confirm design decisions**
1. **Scoring.**
   - A run's latest score under each scorer, on its own (`Bench.scores_of`).
   - Scoring a run now, under all its scorers or some (`Bench.score`), one run at a time.
   - The person's finished runs, each with the scorers it is left to be scored by (`Bench.outstanding`, as
     `runs?unscored=true`).
   - Where a score's detail and the scoring's findings show, if anywhere: both can quote the answer, so a place for
     them is case-derived, and the ledger marks the scoring's findings otherwise (see "Surprises").
   - A case with expectations to choose from: decided since, with what keeps a person from having several
     (`agents/wip-bench.md`, "What a person is scored against"). The look lists such a case as `choosing`, scoring still
     refuses the run under that scorer, and `Bench.outstanding` lists the run with that scorer, so `runs?unscored=true`
     would too.
2. **Docs.** These two files, for `docs/api.md` and `docs/api-api.md`. Then:
   - a proposal for `agents/wip-identity.md`: the framework, and signing in as built;
   - what the API's work changed in the bench: done, in `agents/wip-bench.md` and `agents/wip-bench-api.md`.
3. **Takes** the API is built on still wait for a word (below).

### Takes the API is built on
A take was the agent's recommendation, built on but not decided. The labels are the plan's, as other plans cite
them; A1 (programs and browsers alike), A2 (FastAPI), A3 (signing in) and A9 (case-derived content in its own
places) were decided.
- **A4. Ids in paths**, names as filters, whole ids only (N1), rather than names and owners as the repl takes them,
  with a pick by model and 409 when several match (N2).
- **A5. A variation stated in each request** (V1), rather than a skeleton compiled and stored first and named by its
  digest (V2), or a variation held on the server and patched (V3, rejected: the cell again). Later, if wanted: a
  skeleton's digest beside a configuration, for a client that holds one, and an edit's id in place of a
  configuration, should drift matter.
- **A6. A run runs in the request** (W1). W2 runs it in the app's process beside the request: `POST /api/runs`
  answers 202 with the run's id, `GET /api/runs/{id}/events` streams it (a GET, so a browser's `EventSource` can
  follow it), and `POST /api/runs/{id}/stop` stops it; runs end with the process. W3 is a worker with a queue, which
  `agents/wip-worker.md` takes, runnable in the app's process too. The events stay the same either way.
- **A7. The stream** asked for with `Accept`, with the events in "The stream".
- **A8. Scoring at once**, with the opt-out, and a listing of what is left to score, rather than scoring only when
  asked; no request scores everything.
- **A10. The statuses** in "Errors".
- **A11. Fork and edit as two requests** (K2), rather than save as an upsert by name (K1). The repl's `save NAME`
  picks between them by name, as before.
- **A12. Paths**: mounted at `/api/`, without a version.

### Open
Signing in:
- **A cookie over plain HTTP** isn't kept: a `Secure`, `__Host-` cookie needs HTTPS, or `localhost`.
- **`Origin` against `Host`.** A proxy that rewrites `Host` would fail the `Origin` check for a browser that sends no
  `Sec-Fetch-Site`, though today's browsers all send it. If it bites: the public origin as a setting.
- **No limit on login attempts**, and **no personal tokens** for scripts that run longer than a session (a table and a
  migration).
- **Keycloak.** Once it is in front, a proxy authenticates and hands over the login, which maps to `person.login`,
  and signing in is skipped (agents/wip-identity.md).
- **Roles aren't checked**; that waits for the portal.

Serving:
- **A connection per request**, opened and closed each time; a pool (`psycopg_pool`) when that costs. A run answered
  as JSON holds two for as long as it lasts: the request's and its own.
- **A person's runs are all read**, and paged afterwards (`Bench.runs`). Page in the store once that is slow.

Variations:
- **A part given twice in a query**: the last one counts.
- **An edit has no precondition**: done, as the head's edit in the body (agents/wip-authoring.md, A10).
- **Concurrent writers.** Two requests can save the same name at once (docs/catalog.md, "Concurrent writers").
- **Variants.** A client finds `plan (en, Qwen/Qwen3-8B-AWQ)` by its full name; agents/wip-variants.md's option B
  would let it filter by model and language instead.
- **An unsaved variation's runs are titled by their whole recipe**, in the API as in the repl (docs/catalog.md, "A
  variation nobody saved has a long title").

Runs:
- **Reaching a chunk finds no run.** Filtering runs by a chunk's digest lists nothing, since a compiled skeleton
  holds what the chunk sets rather than a reference to it; the compilation refers to both. The repl's `show reasoning
  NAME` says "no runs of yours" the same way (`Bench.reaching`). Reaching through compilations would find them.
- **A quiet stream sends nothing**, as while it waits for a slow first token, and a proxy's read timeout would cut
  it. A comment line now and then would keep it open.
- **`Accept` is read by media type alone**, so `text/event-stream;q=0` still asks for a stream.
- **A run outlives a server that stops**, which waits for its requests. A killed one leaves the run unfinished, as
  resuming isn't built; requests that last as long as a run are agents/wip-worker.md's ("Why").
- **Judges**: judged views show as "not yet", as in the repl.

### Surprises
- `ScoreFinished` is marked as not case-derived (`src/chatddx/ledger/score.py`, `case_derived = False`), but its
  findings hold `answer.invalid` messages, which can quote the answer's values
  (`src/chatddx/scorers/answer.py:_breaks`).
- Starlette's test client doesn't tell the app that a client hung up: it runs a streamed response to its end.
- The "cell" guard's pattern matches "cancelled" (`src/chatddx/repl/test/test_vocabulary.py:CELL`). Say "stopped",
  which is the runner's word anyway.

### Seen once
- On a container just started, the first two full runs each ended with a setup error in a test the API doesn't touch
  (`src/chatddx/store/test/test_catalog.py::test_changed_vignettes_are_repaired`, then
  `src/chatddx/repl/test/test_running.py::test_ctrl_c_stops_a_run_as_it_streams_and_it_is_recorded_as_stopped`);
  the runs after were clean. The message wasn't kept. The likeliest cause is the test databases' race, which
  `src/chatddx/conftest.py:_settled` waits out for at most 5 s.

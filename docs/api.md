# API

The API and its sibling, the repl, are the rig's control plane.

The endpoints are in the OpenAPI document the API serves, at `/api/openapi.json`, with pages at `/api/docs`.
This document describes what the API does and why it is shaped like it is.

It serves programs, such as scripts, notebooks for analysis and export, and CI, and browsers, the portal among them
where it is interactive. A session is carried either way, as a bearer token or as a cookie, and the checks a cookie
needs are there from the start rather than added later.

- **The bench is the surface for what depends on who is asking**: what a person sees, finds and owns. What doesn't
  depend on them is the same for everyone, read from the store and the World, if through the bench's reads that take
  no person: a component by its digest, the endpoints and the models.
- **What a person sees is a convenience, not protection.** It decides what is relevant to show them. Protection is
  clearance, which the runner's gate enforces, and the database's grants (agents/wip-clearance.md).
- **The docs' words**: configuration, variation, part, chunk, endpoint, engine, family and case, trial, run, score. The
  repl's "cell" is the repl's alone, and a test holds every package but the repl to that.

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

```
AGENT: replace
agents/wip-engine-part.md replaces agents/wip-variants.md: the model becomes a part, not a name. The paragraph.
---
A configuration made per language or model is a thread under its full name, until the engine is a part of it and the
model leaves its name (agents/wip-engine-part.md).
```
A configuration made per language or model is a thread under its full name, until variants are recorded as such
(agents/wip-variants.md).

## What a person sees
- **Threads** gives its kind and the word for it, name, title, owner, tags, language and head, and on its own also
  its description, collaborators, the edit it was forked from, whether it is deleted, and for a configuration its
  recipe. A configuration's language is its head's recipe's.
  Its versions come oldest first. Configurations are listed by purpose, those that give answers unless the judges'
  are asked for, since a judge configuration is no use at a run.
  A configuration can also be asked for by what it answers: the title of its answer's JSON Schema, such as
  `management_plan_v1`.
- **Families**, each with the case of its current vignette, filtered by tag or name. A family on its own adds its
  description and collaborators, the case's appendices, and, under each expectation schema the person sees, the
  expectation its case is scored against: their own, so a schema under which they only see shared ones has none
  (`docs/bench.md`, "What a person is scored against"). Several to choose from don't fail the request; that
  schema says so instead. Each schema also lists the expectation threads shared with the person they could take.
- **A family's vignette**, fetched from the World's source, and whether it still is the text the case was made from
  (unknown under a keyed fingerprint). It is sensitive (see "Sensitive content").
- **Tags** on the families the person sees.
- **Endpoints**: each one's engine and the engine's title, the model it serves, its URL and host, how many requests
  it takes at once, its credential's name, the sources it is cleared for, and whether a typed case can run there. One
  whose engine isn't stored, or whose URL can't be told, says why rather than failing the listing.
- **Models**: what the facts know of each, and the endpoints serving it.
- **Components**: any stored component by its digest, with its kind and title; and the kinds of component, each
  with the bench's word for it, whether a person writes it, and its JSON Schema, in which a reference names the kinds
  it takes (`x-kind`). These are the same for everyone.

A thread, family or run the person doesn't see is "not found", the same as one that doesn't exist. Their own deleted
threads are listed apart, and each can still be read by its id, with its versions, so that it can be restored.

## Trying a variation
A configuration's variation is the configuration with some of its parts replaced. A request states it whole each
time and nothing is stored by looking.

The latest configuration means its head when the request comes (unless an edit is given) so a variation looked at and
one run moments later can differ if the configuration moved in between; each run records the skeleton it ran.

A look at a variation gives:
- the edit it was built on, its label (`NAME+PART=CHUNK`, `docs/bench.md`, "The variation being tried"), the digest
  of the skeleton it compiles to, the configuration whose head is that skeleton with the variation's recipe, the
  person's own first, and whether its sampling is greedy.
- each part's chunk, its title and what it holds, and whether it was replaced.
- the request it would send, with placeholders for the case and, without an endpoint, for the model.
- a seed, drawn from the trial's whole range unless one is given, and given back so a run can send the same.
- at an endpoint, the lints of it as a trial over the cases with any of the given tags, else over every case the
  person sees; where no case has the tags, over one case the person sees, without the cases' languages.
- for each view of each scorer, whether the variation's output offers what the view reads, which families have no
  expectation it picks something from, and which have several to choose from.

A case with expectations to choose from is listed apart, as `choosing`, rather than as one without
(`docs/bench.md`, "What a person is scored against"). An unsaved variation is linted in its recipe's
language, since the language of a skeleton otherwise comes from its stored compilations, which it hasn't got yet.

A variation the bench refuses is unprocessable: a digest that isn't a stored chunk of its part, a part that can't be
taken out, parts that don't compile together, or a parameter the request doesn't know, so that a misspelt part is
refused rather than ignored. A look's queries don't grow with the number of cases it is over.

## Checking a component
A component of a kind a person writes is checked as a write would store it, and nothing is written: its rules, its
references, which must be stored, the rules that take several components, and a scorer's code and parameters. It
gives back the digest it would have and what the lints say of it, or is refused as the write would be. An edge checks
what a person types as they type it.

## Forking and editing
Keeping a variation is two requests, rather than one save by name as the repl's `save NAME` is, which makes a new
version of the person's configuration of that name if there is one, and a new configuration otherwise:
- **Fork** any configuration the person sees, with parts replaced and a name, into a new configuration of their own,
  from its head or from an earlier edit of it given; an edit of another configuration is "not found".
- **Edit** a configuration of their own, with parts replaced over its head: a new version, or nothing when the
  variation is the head already, which is answered as such. Another's configuration can't be edited, and is "not
  found" as "no configuration N of yours".

Chunks, appendices, expectations and scorers are written the same way, with a component where a configuration takes
parts, as its JSON as a component's own request gives it, and a scorer with the labels of its views and resources
(`docs/bench.md`, "Components" and "Scorers"). A judge is written the same way, over a judge configuration,
an engine and its seeds:
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
is deleted (`docs/bench.md`, "What is said about a thread"). Deleting is also a request of its own. What holds
afterwards comes back. A deleted thread is restored before anything else is said of it. Another's thread is "not
found", as "no expectation N of yours" for an expectation; a login that names nobody, an empty name or tag, and
taking a description away are unprocessable.

## Typed cases
A person types a case: its text, and a name and a language if they like. It is kept as written, in the World's
database source, with its case and a family of their own, which comes back as a family does (`docs/bench.md`,
"Typed cases"); its vignette is then read as any family's. A text is held to a length and a person to a number of texts
a day: past the day's is 429.

## Appendices and cases
A family lists its cases at its current vignette, its default first, each with its appendices and the expectation
it is scored against under each schema (`docs/bench.md`, "Appendices and cases"). The person writes an
appendix for a family from its text, and builds a case from appendices they see, in order, or stores the replacement
of a case a repair left at an earlier vignette. An appendix's new version, written as any edit, answers with each case
it replaced. An expectation is carried onto another case of its family by an edit of its own, which names the head
it was made on.

## Following an origin
A fork whose origin has moved on has a proposal: what following would keep, with the base, the origin's head, what
the fork varies, and for a configuration the recipe it compiles from (`docs/bench.md`, "Following an
origin"). Asking for it gives nothing when there is none. Following is an edit of the person's own fork, which names
the head it was made on and comes back with what the lints say. Following a fork with nothing to follow, or whose
changes no longer fit, is unprocessable.

## Taking expectations
A person is scored against their own expectations only, so they take the shared ones (`docs/bench.md`,
"Taking"):
- **For many cases**, by family, under one schema, from any owner or one named. The answer says, for each family,
  whether its case was taken, and into which thread, or was kept as theirs, has several shared to choose from, or
  has none shared. Nothing of theirs changes, so the request is safe to repeat, and it is answered 200 whatever it
  took. A family the person doesn't see, or an owner who doesn't exist, is unprocessable.
- **One thread**, an expectation shared with them, into a thread of their own. When they have their own of its case
  under its schema, it is a conflict unless the request says to replace theirs, which deletes it in the same write.

## Runs
### Starting one
Runs are started within their request, so whatever refuses them does so before anything is sent.

Any person can start at most `settings.RUNS_PER_DAY` runs a day, and a run holds at most `settings.ITEMS_PER_RUN` items.

The run gives back the cases' digests, and is named by the variation's label, `NAME+PART=CHUNK`. Listed or read, a
run says what it ran (`ran`): the configuration, the edit the variation was built on and the parts replaced over it,
or nothing for a run started from a trial alone (docs/catalog.md, "What a run ran").

The gate refuses an endpoint that doesn't serve the trial's engine, isn't cleared for a sensitive source among the
cases', or lacks its secret; tools that would get a sensitive source's content; and an endpoint that doesn't answer.

Once started, it is queued for the worker, and answered 202 with what `run.started` holds, and the run's path as
`Location`.

A run is sent under its endpoint's execution (docs/inventory.md, "Endpoints"), with the concurrency, up to the
endpoint's `max_jobs`, and the order the request gives, a shuffled order's seed drawn; with its endpoint's canary set;
and with the cleanup steps the request gives, else those its cases' sources ask for (docs/inventory.md, "Sources").

### Where it runs
A started run is queued as a job in the store, and a worker sends it, finishes it and scores it under every scorer
that applies to it, unless asked not to be. A job outlives the process that queued it, and is followed and halted from
any

### Its events
`GET /api/runs/{id}/events` tells the run's rows, its scores' included, in the order they were written; then, while a
job for the run is queued or under way, what the worker says as it happens and the rows as they land; and ends with
`done`. Each event's data is one line of JSON, whose models are among the OpenAPI document's schemas.

The last event a row tells has the row's number as its `id`, so that a stream asked for after an id is told the rows
after it, in any process, after a restart, and across a scoring again. What isn't a row has no id, and is told only
to the streams listening as it happens: an item about to be sent, its deltas and tool runs before it is recorded, a
scoring starting, a judge asked, its deltas and its answer, and the scoring over.

A stream that joins mid-item is told that the item started, its text from when it joined, and each tool run once;
its whole answer is the item's once it is recorded. Deltas go out together, a tenth of a second's at a time.

A stream joined after its run's job ended, or for a run no job took, is told the rows, the latest scores as
`run.scored`, and `done`.

| Event | When | Holds |
| --- | --- | --- |
| `run.started` | first | the run, its trial and skeleton, the endpoint, the cases, the seeds, and whether sampling is greedy |
| `item.started` | an item is about to be sent, or a stream first hears of it | its case and replicate, and its seed |
| `item.delta` | a chunk of an answer streams in | its case and replicate, the kind (reasoning, content or a tool call), the text, and the tokens so far |
| `item.tool` | a tool has run for a call | its case and replicate, and the tool run |
| `item.ended` | an item is recorded | its case and replicate, its outcome and why, and its tokens |
| `canary.ended` | a canary call is recorded | the phase, which canary, and the call |
| `run.noted` | the run is recorded as finished, before `run.finished` | a finding noted along the way, such as a case that couldn't be read |
| `run.finished` | the run is recorded as finished | what checking it found |
| `run.scoring` | a scoring starts, after the run or asked for | the scorers it is to score by |
| `score.started` | a scorer's score starts | the scorer, its name, the score and its views' labels |
| `judge.asked` | a judge is sent an item's view, for one seed | the case and replicate, the scorer, the view, the judge and the seed's index |
| `judge.delta` | a chunk of the judge's answer streams in | the case and replicate, and as `item.delta` |
| `judge.answered` | the judge's call is recorded | the case and replicate, the view, the judge, the seed's index, the verdict read, and the call |
| `score.item` | a score item is written | the score, the case and replicate, the view, its value and detail |
| `score.noted` | a scorer's score is recorded as finished | a finding of the scoring pass, such as an answer its schema refuses |
| `run.scored` | the scoring is over; or before `done`, from the ledger, for a stream that wasn't told it | each scorer's score, or why it gave none; from the ledger, the latest scores |
| `error` | before `done`, when the run's last job failed | why |
| `done` | last | whether the run's last job was asked to halt, `null` for a run no job took |

An item's outcome is stopped, errored, unread, salvaged, completed, invalid or valid, by its last call and the answer
read from it; salvaged is a structured answer cut short, read with its structure closed.

### Running again
Running again draws new seeds.

### Halting
A halt goes through the queue, and reaches the job's worker wherever it is.
It cancels the calls under way, record them as stopped and the run is finished unscored.

### Reading runs
- **A person's runs**, newest first, a page at a time, filtered by trial, by a digest their trial is built on, by
  a scorer that scored them, or to those left to score, each with the scorers it is left to be scored by. Each says
  what ran: its trial, skeleton, engine, endpoint, cases, seeds, and a line saying it as people read it; and its
  latest job: how it stands and why, whether it was asked to halt, and while it is queued, how many jobs at its
  endpoint are under way or are to be taken before it, none while its owner has paused.
- **A run** adds when it started and finished, the rig it ran on, what it noted as it went, what checking it finds
  now, each item's outcome and tokens, and its latest score under each scorer.
- **A run's scores**: the latest under each scorer, or every one, newest first, or one by its id. A score says its
  scoring, when it started and whether it finished, each item's value under each view, and each view's mean.
- **A score's items**: each item's detail and judge calls, and the findings of the score. They are sensitive.
- **A run's items**: each call as it was recorded, with its response and tool rounds, why the item ended as it did,
  and its answer as read from its last call, as the scorers read it, with why it couldn't be read or breaks its schema.
  They are sensitive.
- **Whether each item renders again** as it was sent: only a request's fingerprint is kept, so the request is
  rendered again from the trial and the source, and compared.

Only the person's own runs are seen; a collaborator on a run doesn't see it.

## Scoring
A run is scored as soon as it is finished by default but a request can ask for it to be left with `"score": false`.
A judged view is scored as any other, its judge's calls sent to the one endpoint that serves the judge's engine.
The scores come in `run.scored`, and with the run when it is read: each item's value under each view.
Also each view's mean over the items, or why the scorer gave none.
A judged view's value is the mean over the seeds whose verdicts were read.

A finished run is scored again when asked, under every scorer that applies or some, queued as a run is: answered 202
with the scorers it is to score by, it goes on whoever listens, and its events are the run's, after its rows.

## Sensitive content
What is made from a vignette is shown to whoever signed in, but only in its own places, so that a policy for edges
can gate those few when clearance has one (agents/wip-clearance.md):
- a family's vignette;
- a run's items;
- a score's items, with their detail and judge calls, and the score's findings;
- a run's events: the deltas, the tool runs, why each item ended, and the scoring's items, judge calls and
  findings.

Each is sent with `Cache-Control: no-store`, so that a browser keeps none of it.

Nothing else should carry any, but why a job failed can quote what it was sending, and is served with the runs
(agents/wip-clearance.md, "Before real patient data" 10). Why an item ended can quote the answer, since checking it
against a schema names the value it refused, so it is in the items and the events only. For the same reason a score
gives values, and its detail, judge calls and findings are its items'.

## Errors
A refusal's body is `{"detail": "…", "code": "…"}`. The detail says why, or, where a request doesn't validate, lists
where. The code says what it is:

| Code | Status | When |
| --- | --- | --- |
| `unauthenticated` | 401 | No session, one that has ended, or a wrong login or password. |
| `cross_site` | 403 | A cookie's request that changes something, or a sign-in, from another site's page. |
| `not_found` | 404 | What the path names isn't there, or isn't the person's to see. |
| `not_allowed` | 405 | A method the path doesn't take. |
| `ambiguous` | 409 | Several where the bench is asked for one. |
| `conflict` | 409 | Taking an expectation the person has their own of, without saying to replace it; scoring a run with something under way, and halting one with nothing under way. |
| `moved_on` | 409 | An edit, a follow or a carry whose head has moved on. |
| `unprocessable` | 422 | A request that doesn't validate, or names a field it shouldn't; the detail lists where. |
| `refused` | 422 | What the API, the bench or the gate refuses: the rest of 422. |
| `over_quota` | 429 | A person who has typed as many cases as a day takes. |
| `error` | any other | |

The OpenAPI document holds the body as the schema `Error`.

An edit that changes nothing is answered 200 with the head; what is made is answered 201; a deletion and a halt 204;
a run or a scoring started 202. What fails once it is under way is an `error` event, not a status. A take for
many cases is answered 200, whatever it took, and a carry 201, even when the expectation is on that case already.

## Not covered
- **A vignette in a run's request.** A run takes cases; a text to run is typed first, and kept in the World's
  database source as a case of its own (see "Typed cases").
- **A proxy's forward auth**: once a proxy authenticates, that is its job.
- **A person's secrets.** An endpoint's credential comes from an environment variable, as in the repl.
- **Scoring every outstanding run in one request.** A client scores one run at a time (see "Scoring").
- **"Run N of trial X"**, which the repl says after a run. A run's trial lists its runs.

## Tests
The tests start from the test World (`worlds/test`; docs/inventory.md, "Worlds") as `chatddx init-data` lands it, with
alice signed in by a bearer token and bob for what isn't his to see. They speak to the app through Starlette's test
client over HTTPS, since the cookie is only sent over it. Runs are sent to the fake vLLM serving the test World's
endpoints on ports nothing else uses.

The app the tests serve runs a worker in its process, as `chatddx run` does. What isn't a row is told only to a
stream listening as it happens, so a test that looks for it pauses alice's queue, starts the run, reads the stream's
first row, by when it listens, and then lets the worker take the job.

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
| Run | A variation sent at an endpoint on some cases with some seeds, recorded as it goes. |
| Item | One case's replicate in a run: its first request and each tool round's, each a call. |
| Outcome | How an item ended: stopped, errored, unread, salvaged, completed, invalid or valid. |
| Event | One step of what is under way for a run, as its events tell it. |
| Job | What the app has under way for a run: the run, or a scoring of it, with its events. |
| Halt | Ending what is under way for a run early: its sending, hanging up the calls under way, or its scoring. |

## Outstanding
Left for later, each with what holds and the take on it, the agent's recommendation, which waits for a word. The
bench's are in docs/bench.md, "Outstanding".

### Takes the API is built on
Built as the takes of the plan at 100a078 had them, and not confirmed since. Decided there: who it is for, kept open;
FastAPI and uvicorn; signing in; and sensitive content in places of its own. Decided since: where a run runs and
its events (see "Where it runs" and "Its events").
- **Ids**: a path takes a whole id, and a name is a filter on a list, which gives every match.
- **The variation**: stated whole in each request, the configuration by id and its parts by digest, with nothing
  stored by looking. A run may come to name the skeleton its look gave, and be refused when the variation compiles to
  another by then, as an edit names its head.
- **Scoring**: at once after a run, with an opt-out, and the runs left to score listed.
- **Errors**: the bench's errors mapped by class, and what else a route means caught where it means it, each answered
  with a code beside its detail (see "Errors").
- **Keeping a variation**: a fork and an edit, two requests, rather than a save by name.
- **Paths**: under `/api/`, with no version until there is a second.

### Serving
- **A connection per request**, about 2.6 ms each over the Unix socket, opened and closed each time; one for each
  stream while it is open, and one per process listening for them all; and two for each job a worker holds. A pool
  (`psycopg_pool`) for requests and streams when a measurement says so.
- **A query parameter a route doesn't name is ignored**, unless the query is a model (`Varying`), so a misspelt filter
  on `GET /api/runs` or `GET /api/threads` gives everything, and a part given twice in a variation's query counts the
  last. Take: one check for every route that refuses a parameter the route doesn't declare, and a scalar given twice.
- **A person's runs are all read**, filtered and then paged, and with `unscored`, what is left of each is worked out
  first. Take: as is until slow, then paging by a cursor, the last run's start.

### Signing in
- **A cookie over plain HTTP** isn't kept: a `Secure`, `__Host-` cookie needs HTTPS, or `localhost`, and a bearer works
  everywhere. Take: as is.
- **`Origin` against `Host`.** A proxy that rewrites `Host` would fail the `Origin` check for a browser that sends no
  `Sec-Fetch-Site`, though today's browsers all send it. Take: as is; the public origin as a setting if it bites.
- **No limit on sign-ins, and no personal tokens.** Each sign-in costs an argon2 verification, a fraction of a second
  of CPU, and a script running longer than a session signs in again. Personal tokens were decided for when a script
  needs one. Take: neither, until Keycloak is in front, which limits sign-ins itself, or a script needs a token.
- **Keycloak.** How it hands the app a login isn't decided. Take: a proxy in front, such as oauth2-proxy, passes the
  login in a header the app believes from it alone, mapped onto `person.login` (docs/identity.md, "Take, for when
  Keycloak arrives"), and Keycloak's own tokens as bearers for scripts when they come.
- **Roles aren't checked**; Z1 shapes what each role is shown, with the portal (docs/bench.md, "Outstanding").

### Variations
```
AGENT: replace
agents/wip-engine-part.md replaces agents/wip-variants.md: the model becomes a part, not a name. The item.
---
- **Variants.** A client finds `plan (en, Qwen/Qwen3-8B-AWQ)` by its full name. Take: so until the engine is a part
  (agents/wip-engine-part.md), when it finds `plan (en)`, and the engine is one of its parts.
```
- **Variants.** A client finds `plan (en, Qwen/Qwen3-8B-AWQ)` by its full name. Take: so until variants are recorded
  (agents/wip-variants.md, option B), then filters by what a thread is a variant of, its model and its language.
### Writes
- **Carrying answers 201 even when nothing changes**: an expectation carried onto the case it is of already is kept
  `unchanged`, which an edit answers 200. Take: 200, as an edit.

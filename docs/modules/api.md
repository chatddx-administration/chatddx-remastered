# API

The API is the rig's canonical public control plane and server for the portal's islands.

A session is scoped to a person and is carried as a bearer token or cookie. The bench (docs/modules/bench.md), and
identitiy (docs/modules/identity.md) provide the operational and declarative person-scoped functionality respectively.

## Authentication

A person signs in with a login and a password, and gets a token and a cookie-setter, `__Host-chatddx-session`:
`HttpOnly`, `Secure`, `SameSite=Lax`, for every path of this host, and as long as the session lasts. A wrong login is
refused with the same answer as a wrong password. Signing out ends the session the request acts in and drops the cookie.

```
curl -sS -X POST http://chatddx.com/api/session \
  -H 'Content-Type: application/json' \
  -d '{"login": "alice", "password": "…"}'
{"token":"<token>","person":{"id":1,"login":"alice","name":"alice","roles":[]}}
```

```
H="Authorization: Bearer <token>" curl -sS -H "$H" http://chatddx.com/api/me
{"id":1,"login":"alice","name":"alice","roles":[]}
```

Every other request requires a session from a valid `Authorization: Bearer` token or cookie, and is otherwise refused
with `WWW-Authenticate: Bearer`.

### Requests from other sites

A browser sends the cookie with requests from any page, so a cookie's request that changes something must come from this
site's own pages, and so must signing in, which a forged sign-in would abuse. Where the browser sends `Sec-Fetch-Site`,
it must be `same-origin` or `none`; else `Origin`, where it is sent, must name this host. A request with neither header
isn't a browser's on another page's behalf, and passes. A bearer's requests aren't checked, since no browser adds a
bearer by itself.

The check stands in for a CSRF token, which would need one stored per session.

## Forking and editing

Keeping a variation is two requests.

- **Fork** any configuration the person sees, with parts replaced and a name, from its head or from an earlier edit of
  it given; an edit of another configuration is "not found".
- **Edit** a configuration of their own, with parts replaced over its head: a new version, or nothing when the variation
  is the head already, which is answered as such. Another's configuration can't be edited, and is "not found" as "no
  configuration N of yours".

Chunks, appendices, expectations and scorers are written the same way, with a component where a configuration takes
parts, as its JSON as a component's own request gives it, and a scorer with the labels of its views and resources
(`docs/modules/bench.md`, "Components" and "Scorers"). A judge is written the same way, over a judge configuration, an
engine and its seeds:

Every edit names the head it was made on, and is a conflict when the thread has moved on since
(`docs/modules/catalog.md`, "Threads and edits"). What is written comes back with what the lints say of it, such as an
expectation whose data its schema refuses, which is written all the same.

## What is said about a thread

Its owner says what holds of a thread or a family in one request, giving only what changes (docs/modules/bench.md, "What
is said about a thread"), and of a family its language too. What holds afterwards comes back. Another's thread or family
is "not found", as "no expectation N of yours" for an expectation, and what the bench refuses there is unprocessable.
Its owner reads a thread or a family they deleted, and lists those apart.

A collaborator leaves a thread or a family shared with them in a request of its own, answered with nothing, as it is no
longer theirs to read; one that isn't shared with them is "not found".

## Typed cases

A person types a case (`docs/modules/bench.md`, "Typed cases"); a case typed without a language is unprocessable. The
family made with it comes back as a family does, and a text past the day's quota is 429.

## Appendices and cases

A family gives its cases at its current vignette, its default first, each with its appendices and the expectation it is
scored against under each schema (`docs/modules/bench.md`, "Appendices and cases"). The person writes appendices, builds
cases, stores replacements and carries expectations (`docs/modules/bench.md`, "Appendices and cases"). An appendix's new
version, written as any edit, answers with each case it replaced, and a carried expectation's edit names the case and
the head it was made on.

## Following

A fork whose origin has moved on has a proposal: what following would keep (`docs/modules/bench.md`, "Following an
origin"). A configuration whose facts or model have moved on has what following them would keep, or why the facts now
refuse it (docs/modules/catalog.md, "What has moved on"). One request asks for both, each nothing when there is none.
Following either is an edit of the person's own thread, which names the head it was made on and comes back with what the
lints say; only following an origin takes a language. Following a thread with nothing to follow, or whose changes no
longer fit, is unprocessable.

A thread's lineage is its first origin and every fork below it, as far as the person sees them, each with its origin,
its base and what it varies, whether its origin has moved on since, and whether it is deleted, which only its owner
sees.

## Taking expectations

A person is scored against their own expectations only, so they take the shared ones (`docs/modules/bench.md`,
"Taking"):

- **For many cases**, by family, under one schema, from any owner or one named. The answer says, for each family,
  whether its case was taken, and into which thread, or why not. It only adds, so it is answered 200 whatever it took. A
  family the person doesn't see, or an owner who doesn't exist, is unprocessable.
- **One thread**, an expectation shared with them, into a thread of their own, or a conflict when they have their own of
  its case under its schema, unless the request says to replace theirs.

## Runs

### Starting one

Runs are started within their request, so whatever refuses them does so before anything is sent.

A start is a run per language its cases are sent in (`docs/modules/bench.md`, "Translations"), and the answer says which
cases were left out and why.

Any person can start at most `settings.RUNS_PER_DAY` runs a day, and a run holds at most `settings.ITEMS_PER_RUN` items;
a start's runs are held to both before any of them starts, each counting as a run.

Each run gives back its cases' digests and its language, and is named by the variation's label, `NAME+PART=CHUNK`.
Listed or read, a run says what it ran (`ran`; docs/modules/catalog.md, "What a run ran"); the runs of a start say the
same. A run also says the first run of its start (`started_with`), null for the first and for a run started alone, and
`GET /api/runs?with=RUN` lists a start's runs, the first among them.

A run goes under its variation's handle (docs/modules/bench.md, "The model"); a hand-written configuration names no
model, so a start names the handle it runs under (`under`). What the bench refuses there, and a handle named for a
configuration with a model part, as one it runs under already, are refused before the gate is asked.

Then the gate decides (docs/modules/runner.md, "The gate").

Once started, each run is queued for the worker as a job of its own, and the start is answered 202 with `runs`, what
each run's `run.started` holds, those sent as written first, and `left_out`, each language left out with its cases and
why; `Location` is the first run's path.

A run is sent under its endpoint's execution and canary set (docs/modules/inventory.md, "Endpoints"), with the
concurrency and the order the request gives, a shuffled order's seed drawn, and with the cleanup steps the request gives
(docs/modules/inventory.md, "Sources").

Trials' versions are started as one start (`POST /api/runs/trials`): a run each, in the order given, at the endpoint
serving its engine, under its execution with the concurrency and the order the request gives, named by its trial, and
queued as a start of a variation's runs are.

### Its events

`GET /api/runs/{id}/events` tells the run's rows, its scores' included, in the order they were written; then, while a
job for the run is queued or under way, what the worker says as it happens and the rows as they land; and ends with
`done`. Each event's data is one line of JSON, whose models are among the OpenAPI document's schemas.

The last event a row tells has the row's number as its `id`, so that a stream asked for after an id is told the rows
after it, in any process, after a restart, and across a scoring again. What isn't a row has no id, and is told only to
the streams listening as it happens: an item about to be sent, its deltas and tool runs before it is recorded, a scoring
starting, a judge asked, its deltas and its answer, and the scoring over.

A stream that joins mid-item is told that the item started, its text from when it joined, and each tool run once; its
whole answer is the item's once it is recorded. Deltas go out in batches (docs/modules/worker.md, "What it says as it
happens").

A stream joined after its run's job ended, or for a run no job took, is told the rows, the latest scores as
`run.scored`, and `done`.

| Event            | When                | Holds                                                                      |
| ---------------- | ------------------- | -------------------------------------------------------------------------- |
| `run.started`    | first               | the run, endpoint, cases, seeds, and whether sampling is greedy            |
| `item.started`   | before item is sent | its case, replicate, and its seed                                          |
| `item.delta`     | chunk streamed      | its case, replicate, the kind, text, and the tokens so far                 |
| `item.tool`      | on tool call        | its case, replicate, and the tool run                                      |
| `item.ended`     | an item is recorded | its case, replicate, its outcome and why, and its tokens                   |
| `canary.ended`   | canary is recorded  | the phase, which canary, and the call                                      |
| `run.noted`      | run is about done   | a finding noted along the way, such as a case that couldn't be read        |
| `run.finished`   | run is recorded     | what checking it found                                                     |
| `run.scoring`    | a scoring starts    | the scorers it is to score by                                              |
| `score.started`  | a score starts      | the scorer, its name, the score and its views' labels                      |
| `judge.asked`    | item to judge       | the case, replicate, scorer, view, judge and the seed's index              |
| `judge.delta`    | chunk streamed      | the case, replicate, and as `item.delta`                                   |
| `judge.answered` | call is recorded    | the case, replicate, view, judge, seed's index, verdict read, and the call |
| `score.item`     | score written       | the score, the case and replicate, the view, its value and detail          |
| `score.noted`    | about done          | a finding of the scoring pass, such as an answer its schema refuses        |
| `run.scored`     | scoring is over     | each scorer's latest score, or why this scoring gave none                  |
| `error`          | before `done`       | why                                                                        |
| `done`           | last                | whether the run's last job was asked to halt, `null` for a run no job took |

### Running again

Running again runs the run's skeleton over its cases in its one language, under its handle, and so at the handle's
latest engine, as a run of its own rather than one of the start it was made in, with new seeds or its own. Its handle is
refused as a variation's is (docs/modules/bench.md, "The model").

### Reading runs

- **A person's runs**, newest first by trial's digest or by a scorer that scored them
- **A run** adds when it started and finished, the rig it ran on, what it noted as it went, what checking it finds now,
  each item's outcome and tokens, and its latest score under each scorer.

Only the person's own runs are seen; a collaborator on a run doesn't see it.

## Scoring

A run is scored as soon as it is finished by default but a request can ask for it to be left with `"score": false`.

A finished run is scored again when asked, under every scorer that applies or some, queued as a run is: answered 202
with the scorers it is to score by, it goes on whoever listens, and its events are the run's, after its rows.

### Trying a scorer

A scorer as it is written, and the data of an expectation, are tried on the items of a case in some of the person's
runs: each item's answer, read as the scoring pass reads it, is scored under each view, and each view gives its value
and detail, with nothing stored and nothing sent. A view its judge scores isn't tried, since its judge would be sent the
answer: it says so, with no value, and is scored once the scorer is saved and the runs scored again. A scorer the
running code can't score with is refused as a write of it is. The values are sensitive, as a score's items are.

### What a judge is asked

A stored judge's first request, as the scoring pass renders it, with the expectation slot filled by what a view picks of
an expectation's data the request gives, the answer as a placeholder, and the case's slots as placeholders too, which
the scoring pass refuses a judge for reading. Nothing is sent and nothing stored, and nothing in it is sensitive.

## Sensitive content

What is made from a vignette is shown to whoever signed in, but only in its own places, so that a policy for clients can
gate those few when clearance has one (agents/wip-clearance.md):

- a family's vignette;
- a run's items;
- a score's items, with their detail and judge calls, and the score's findings;
- a run's events: the deltas, the tool runs, why each item ended, and the scoring's items, judge calls and findings.

Each is sent with `Cache-Control: no-store`, so that a browser keeps none of it.

## Errors

A refusal's body is `{"detail": "…", "code": "…"}`. The detail says why, or, where a request doesn't validate, lists
where. The code says what it is:

| Code              | Status | When                                                                                   |
| ----------------- | ------ | -------------------------------------------------------------------------------------- |
| `unauthenticated` | 401    | No session, one that has ended, or a wrong login or password.                          |
| `cross_site`      | 403    | A cookie's request that changes something, or a sign-in, from another site's page.     |
| `not_found`       | 404    | What the path names isn't there, or isn't the person's to see.                         |
| `not_allowed`     | 405    | A method the path doesn't take.                                                        |
| `ambiguous`       | 409    | Several where the bench is asked for one.                                              |
| `conflict`        | 409    | scoring still running, and halting non-running, taking owned, unsaved expectation      |
| `moved_on`        | 409    | An edit or a follow whose head has moved on.                                           |
| `unprocessable`   | 422    | A request that doesn't validate, or names a field it shouldn't; the detail lists where |
| `refused`         | 422    | What the API, the bench or the gate refuses: the rest of 422.                          |
| `over_quota`      | 429    | total runs exceeds daily quota, a run of more items than one takes                     |
| `error`           | 500    | An error for developers or ops, raw: its type and message.                             |

The OpenAPI document holds the body as the schema `Error`.

An edit that changes nothing is answered 200 with the head; what is made is answered 201; signing out and a halt 204; a
run or a scoring started 202. What fails once it is under way is an `error` event, not a status. A take for many cases
is answered 200, whatever it took.

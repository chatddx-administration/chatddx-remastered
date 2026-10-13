# API: open items

The API's items left open in `agents/wip-bench.md`, "Outstanding", one by one: what holds today, the options, and a
take for each. Written from the code at the correction pass before `docs/api.md`, and from `agents/wip-api.md` at
100a078, whose options A4–A12 are restated here, since they were built as their takes had them and never confirmed.

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## In short

| Item | Today | Take |
| --- | --- | --- |
| O1. Scoring a finished run | no route | `POST /api/runs/{id}/scores`, JSON or a stream as a run is |
| O2. A run's scores on their own | only inside the run | `GET /api/runs/{id}/scores`, the latest per scorer |
| O3. What is left to score | `unscored` is ignored | `GET /api/runs?unscored=true`, each run with its scorers left |
| O4. The scoring's events | none; the stream is quiet | all of them, as the repl shows them |
| O5. Detail, judge calls, score findings | nowhere | a case-derived route of a score's items |
| O6. Naming a judge's endpoint | one endpoint per judge engine, or none | as is, until a World serves an engine twice |
| O7. Writing judges | configurations only | `judge` written as any component, configurations by purpose |
| O8. A4, ids | whole ids | confirm |
| O9. A5, the variation | stated in each request | confirm |
| O10. A6, where a run runs | in its request | confirm for now; the worker decides after |
| O11. A7, the stream | by `Accept`, on `POST` | keep-alives and event ids now; a `GET` with the worker |
| O12. A8, scoring at once | at once, with an opt-out | confirm; O1–O3 finish it |
| O13. A10, errors | `detail` only; 409 means three things | a `code` beside `detail` |
| O14. A11, keeping a variation | fork and edit | confirm |
| O15. A12, paths | `/api/`, no version | confirm |
| O16. A cookie over plain HTTP | not kept, but on localhost | as is |
| O17. `Origin` against `Host` | `Host` | as is; a setting if it bites |
| O18. Login attempts, personal tokens | neither | neither, until Keycloak or a script needs one |
| O19. Keycloak | not decided | a trusted proxy's header, wip-identity's take |
| O20. Roles | not checked | Z1, with the portal |
| O21. A connection per request | about 2.6 ms each | as is, until measured |
| O22. Query parameters a route doesn't name | ignored | refused, for every route |
| O23. A part given twice | the last counts | refused, with O22 |
| O24. Variants | by full name | wait for agents/wip-variants.md's B |
| O25. An unsaved variation's title | its whole recipe | the label as the run's name |
| O26. A quiet stream | nothing sent | a comment every 15 s |
| O27. Going away, and scoring | the scoring goes on | halt it too, once O1 exists |
| O28. `Accept` | media type only | honour `q=0` |
| O29. A server that stops | the run outlives it, or is left unfinished | the worker's resuming |
| O30. A person's runs are all read | paged afterwards | as is, until slow |
| O31. Carrying, unchanged | 201 | 200, as an edit |

## Scoring
These are what `agents/wip-bench.md`, "Start with this", 1, lists: the API's scoring past the run that started it.

### O1. Scoring a finished run
Today a run is scored as its thread finishes it, unless its request says `"score": false`. Nothing scores it later,
so over HTTP a run stays unscored when it was started so, when a scorer was refused (a judge's endpoint not
answering, its secret unset, a case with expectations to choose from), when an expectation changed since, or when a
deploy raised a scorer's version. The bench has it: `Bench.score(run, scorers, on_event)`, which the repl's `score`
calls.

A scoring can be long: a judged view sends a call per case, view and seed, one at a time, under the default
execution, so with no timeout. The run's machinery fits it as it is: a thread of its own, events through a queue,
JSON or a stream by `Accept`, and a halt when the client goes away (`api/runs.py:_send`, `_stream`, `_ended`). The
worker's take moves every run started over HTTP to a worker answering 202 (agents/wip-worker.md, K5), and a scoring
would follow it there.

- **a. JSON only.** `POST /api/runs/{id}/scores`, with the scorers by digest or none for every one that applies,
  answered once scored, on the thread pool. Smallest; a long judged scoring holds a request, with nothing to show.
- **b. As a run is.** a, and a stream when `Accept` asks, on the same thread, queue and halt as `POST /api/runs`,
  with the scoring's events (O4). One shape for the two long things.
- **c. 202 and read back.** The scoring's id, and its scores read by `GET` when they are there. Needs something to
  own the scoring after the request: the worker.

An unfinished run is refused before anything is sent (422), rather than as a refusal per scorer, which is how
`Grader.start` says it today. A scorer that can't score the run gives why, as in `run.scored`.

Take: b. c comes with the worker, for runs and scorings alike.

### O2. A run's scores on their own
`Bench.scores_of` gives the latest score under each scorer that scored a run, named as the person's view names the
scorer. `GET /api/runs/{id}` carries them, with every item and what checking the run finds, which is more than a
client asking for scores wants. The ledger keeps every score; nothing reads an older one.

- **a. The latest.** `GET /api/runs/{id}/scores`, as `run.scored` gives them.
- **b. a, and any one.** `GET /api/runs/{id}/scores/{score}`, older ones included, for a client comparing a scoring
  with an earlier one.
- **c. Nothing new.** The run's detail is enough.

Take: a; b's route when a client needs the history.

### O3. What is left to score
`Bench.outstanding` gives each finished run of the person's with the scorers it is left to be scored by, a run with a
case that has expectations to choose from among them. Each run costs a resolve of its trial, every scorer's reach and
judges, the scoring as it would be built now, and its stored scores: about 40 ms a run under the sample's five
scorers, measured on two runs, so a person with hundreds of runs waits seconds. Today `GET /api/runs?unscored=true`
is ignored, and gives every run (O22).

- **a. A filter on the runs.** `GET /api/runs?unscored=true`, each run with `unscored`, its scorers left, by digest
  and name; paged after the work, as the runs are paged now (O30).
- **b. A route of its own**, `GET /api/runs/unscored`, the bench's shape: runs and scorers.
- **c. A field on every page.** `unscored` worked out for the runs of a page only: cheap per page, but a client
  looking for what is left reads every page.

Take: a; its cost goes with O30's.

### O4. The scoring's events
`Grading.send` gives, as it goes: a score item written (`ItemScored`: the item's value and detail), a judge asked
(`JudgeAsked`: the key, the scorer, the view, the judge and the seed's index), the judge's answer as it streams
(`Streamed`), the judge answered (`JudgeAnswered`: the call and the verdict read), and a finding (`Noted`)
(`src/chatddx/runner/score.py`). The repl shows them all (docs/repl.md, "Scoring"). The API passes none on, so after
`run.finished` the stream says nothing until `run.scored`, however many judge calls are sent.

A judge reads the completion, so its answer, as it streams and as a verdict, is case-derived, and a score item's
detail can quote the answer. The stream is a case-derived place already (agents/wip-api.md, "Case-derived content";
decided at 100a078 as A9, S3).

- **a. All of them**, as the runner's are: `score.item`, `judge.asked`, `judge.delta`, `judge.answered` and
  `score.noted`, between `run.finished` and `run.scored`, and in O1's stream.
- **b. Progress only.** `judge.asked`, and `score.item` with its value: no detail, no verdict, no deltas.
- **c. None**, and a keep-alive while it is scored (O26).

Take: a. The stream carries case-derived content already, and one set of events serves O1 too.

### O5. Where a score's detail, its judge calls and its findings show
A score item holds its detail (what was read, `no target`, each seed's value) and its judge calls (each call with its
response); the score's finish holds the findings, such as `answer.invalid`, which can quote the answer's values. The
API gives values and means only (`api/events.py:graded_of`), so a judged view says neither what each seed gave nor
what the judge said. The ledger marks a score's records as not case-derived (`ScoreFinished.case_derived`,
`src/chatddx/ledger/score.py`), which the findings contradict.

- **a. A route of a score's items**, case-derived: `GET /api/runs/{id}/scores/{score}/items`, each with its detail
  and judge calls, and the score's findings beside them.
- **b. In the run's items.** `GET /api/runs/{id}/items` gives each item its latest scores' detail and judge calls:
  one case-derived place per run, but two ledgers in one answer, and only the latest score of each scorer.
- **c. Never.** Values only; a client wanting more uses the repl.

Take: a, and `ScoreFinished` marked case-derived, as a suggestion to docs/ledger.md, so the ledger and the API agree.

### O6. Naming a judge's endpoint
The scoring pass takes an endpoint per judge (`Grader.start(…, endpoints)`), else the one endpoint serving the
judge's engine, and refuses when there is none or several (`runner/score.py:judge_at`). The bench names none, and
counts a judge with several endpoints as barred by the World, so its scorer doesn't apply (`Seen._applies`). No
World serves an engine at two endpoints today.

- **a. As is.** One endpoint per judge engine is the World's to keep.
- **b. Named.** O1's request names an endpoint per judge, and a judge with several endpoints keeps its scorer
  applying, as what may pass later does, its refusal saying to name one.
- **c. Picked.** The bench picks among several by clearance and `max_jobs`.

Take: a, until a World serves an engine twice; then b.

## Judges

### O7. Writing judges
Researchers write judges (decided: agents/wip-authoring.md, "Scorers and judges"). A judge is a skeleton of purpose
`judge`, an engine, seeds and a fill rule, `text@1` being the only one (`factors/scoring.py:Judge`), and a scorer's
view names one by digest, so a person's scorer can already name the archive's judges. A configuration of purpose
`judge` can already be made, forked and edited (`POST /api/threads` with a recipe of that purpose). The judge itself
can't: `judge` isn't in `chatddx.bench.WRITTEN`. `Judge.cross_check` refuses a skeleton of another purpose or with
tools, and the scoring pass refuses what the World bars.

Judge configurations are listed among the others. A look at one lints it as a trial and finds nothing, and a run of
one is refused only as its trial is stored, after the gate, as `<digest>: trial uses a judge skeleton`.

- **a. The component only.** `judge` joins `WRITTEN`: new, forked and edited as any component,
  `{"kind": "judge", "skeleton", "engine", "seeds", "fill"}`, with a judge's lints (`chatddx.facts.lints` takes
  judges already). Configurations stay mixed.
- **b. a, and configurations by purpose.** `GET /api/threads?kind=configuration&purpose=judge`, generation by
  default; a run refusing a judge configuration before the gate, in the person's words; and a look at one at an
  endpoint linted as a judge on its engine, a `Judge` built for the look as a trial is, with no reach.
- **c. A word of its own**, `judge_configuration`. `KINDS` maps words to kinds, and both are `skeleton`, so the word
  would read each head's purpose anyway: b with a different spelling.

Take: b, with purpose as a filter rather than a word.

## Takes the API is built on
`agents/wip-bench.md`, "Takes the API is built on", lists them; each is built as its take had it.

### O8. A4, ids
A path takes a whole id, and a name is a filter on a list, which gives every match (N1). Names hold slashes and
spaces, and needn't be unique; a run's id prefix, as the repl takes, could name another run tomorrow.
- **N1**, as built.
- **N2. Names in paths**, `OWNER/NAME`, a per-model pick, and 409 when several match, as the repl reads them.
- **N1, and a find**: a route that turns a name into the one id it means, or 409.

Take: confirm N1. A find is a client's loop over the list.

### O9. A5, the variation
Stated whole in each request: the configuration by id, meaning its head when the request comes, and its parts by
digest (V1). A look and a run moments later can compile differently if the configuration moved between them; the
run records the skeleton it ran.
- **V1**, as built.
- **V2. A digest**: a look stores the skeleton and its compilation, and everything else takes the digest. Every
  variation looked at is stored, in a store with no garbage collector.
- **V1, and a precondition**: a run may name the skeleton its look gave, and is refused 409 when the variation
  compiles to another now, as an edit names its head.

Take: confirm V1; the precondition when a client meets a moved head.

### O10. A6, where a run runs
In its request, on a thread of its own, halted when the client goes away (W1). A browser tab closed halts it; a
server killed leaves it unfinished (O29). The worker's takes are a worker process, also runnable in the app (W3), and
every run started over HTTP going through it (agents/wip-worker.md, K1 and K5), which would answer `POST /api/runs`
with 202 and stream from a `GET`.
- **W1**, as built.
- **W2. Beside the request**, in the app's process, followed by a `GET`; ends with the process.
- **W3. The worker.**

Take: confirm W1 for now. The worker's K5 then decides whether `POST /api/runs` keeps W1 for programs.

### O11. A7, the stream
Asked for by `Accept: text/event-stream` on `POST /api/runs`, with the runner's events, one line of JSON each.
`EventSource` only `GET`s, so a browser reads it through `fetch` and a reader, with no reconnecting. Events have no
`id:`, so nothing resumes; a quiet stream may be cut (O26); `q=0` isn't heard (O28).
- **As built.**
- **As built, and sturdier**: keep-alive comments (O26) and an `id:` per event, the event's position in the run.
- **A `GET`**, `/api/runs/{id}/events`, replaying the run from the ledger and then following it: W2's or W3's shape,
  needing the worker's events through the database (agents/wip-worker.md, K3).

Take: the sturdier stream now, the `GET` with the worker.

### O12. A8, scoring at once
A run is scored as it finishes, under every scorer that applies, unless asked not to be; the listing of what is left
isn't built.
- **At once, with an opt-out, and the listing**, as A8 had it.
- **Never at once**: a client asks for it (O1).

Take: confirm A8; O1–O3 build the rest.

### O13. A10, errors
`app.py:STATUSES` maps the bench's errors by class, routes catch what else they mean, and a body is
`{"detail": "…"}`. 409 means three things (`Ambiguous`, which no route lets through today, `Conflict` and `MovedOn`),
and 422 a great many; a client tells them apart by reading the message. A `ValueError` no route catches is a 500, so
a bug shows.
- **As built.**
- **A `code` beside `detail`**: `moved_on`, `conflict`, `ambiguous`, `over_quota`, `refused`, `not_found` and
  `unprocessable`, from the class; validation errors keep FastAPI's shape.
- **Problem details** (RFC 9457), `application/problem+json` with `type`, `title`, `status` and `detail`.

Take: a `code`. It is what a portal needs to offer the head an edit moved on to without parsing a sentence, and it
costs a field.

### O14. A11, keeping a variation
A fork and an edit, two requests (K2), where the repl's `save NAME` picks between them by name. Forking twice under
one name makes two configurations, as names needn't be unique.
- **K2**, as built.
- **K1**, a save by name beside them.

Take: confirm K2.

### O15. A12, paths
Under `/api/`, the OpenAPI document at `/api/openapi.json` and its pages at `/api/docs`; the document's version is
the installed package's.
- **As built**, a version in the path when there is a second.
- **`/api/v1/`** now.

Take: confirm.

## Signing in

### O16. A cookie over plain HTTP
The session cookie is `__Host-chatddx-session`, `Secure`. Browsers keep a `Secure` cookie from `http://localhost`,
so development works; another host over plain HTTP doesn't get it, and a bearer works everywhere.
- **As is.**
- **A setting** that drops `Secure` and the prefix, for development only.

Take: as is.

### O17. `Origin` against `Host`
Without `Sec-Fetch-Site`, a cookie's request that changes something must send an `Origin` whose host is the
request's `Host` (`api/people.py:same_origin`). Every browser in use sends `Sec-Fetch-Site`, so only an old one behind
a proxy that rewrites `Host` would be refused.
- **As is.**
- **The public origin as a setting**, compared in place of `Host`.
- **`X-Forwarded-Host`**, trusted when a proxy sets it, and forgeable when none does.

Take: as is; the setting if it bites.

### O18. Login attempts and personal tokens
Nothing limits sign-ins. Each verifies an argon2 hash, an unknown login against a dummy one so that it takes as long,
at a fraction of a second of CPU each, so a burst of them also loads the server. Sessions last 12 hours; a script
running longer signs in again. Decided at 100a078 (A3): personal tokens when a script needs one.
- **Limits**: none until Keycloak, which has its own; a backoff per login, kept in a table updated in place, as
  sessions are, with a migration; or one per client address, in memory, which holds in one process only.
- **Tokens**: none; tokens of their own, named, revocable and longer-lived, bearer only, in a table with a migration;
  or a longer session for a bearer's sign-in.

Take: neither, until Keycloak is in front or a script needs a token.

### O19. Keycloak
How Keycloak hands the app a login isn't decided. agents/wip-identity.md takes it that Keycloak, or a proxy in front
such as oauth2-proxy, authenticates, and the app maps the username onto `person.login`; logins are lowercase for it.
- **A trusted proxy's header**, as oauth2-proxy's `X-Auth-Request-User`, believed only from the proxy.
- **Keycloak's tokens**: the app checks access tokens as bearers against Keycloak's keys, and signs browsers in with
  OIDC itself.
- **Both**: the proxy for browsers, tokens for scripts.

Take: the proxy's header, as wip-identity has it, with Keycloak's tokens for scripts when they come; nothing to
build before Keycloak is there.

### O20. Roles aren't checked
A person has roles (admin, clinician, developer, ops, researcher), and the bench checks ownership only. Z1 would map
roles to the kinds each sees, as a convenience rather than a protection (agents/wip-identity.md).
- **Ownership only**, as now.
- **Z1** for what is shown.
- **Roles refusing writes**, which agents/wip-authoring.md, A11, rejects: forms are shaped by role, nothing refused.

Take: Z1, with the portal.

## Serving

### O21. A connection per request
Each request opens a connection and closes it: about 2.6 ms over the Unix socket here. A run answered as JSON holds
two while it lasts, the request's and its own; PostgreSQL takes 100 by default.
- **As is.**
- **A pool** (`psycopg_pool`, a new dependency) for requests, runs keeping their own.

Take: as is, until a measurement says otherwise.

### O22. Query parameters a route doesn't name
FastAPI ignores them, but where the query is a model with `extra="forbid"` (`Varying`). So `GET /api/runs?unscored=true`
gives every run, and a misspelt filter on a list gives everything.
- **As is.**
- **A model per list route**, as `Varying` is.
- **One check for every route**: a dependency refusing a parameter the route doesn't declare, and a scalar given
  twice (O23).

Take: one check for every route, so a misspelling is a 422 wherever it is made.

## Variations

### O23. A part given twice in a query
The last one counts.
- **As is.**
- **Refused**, with O22's check.

Take: refused, with O22.

### O24. Variants
A client finds `plan (en, Qwen/Qwen3-8B-AWQ)` by its full name; the repl finds it by `plan` and the endpoint's model.
agents/wip-variants.md weighs how variants are recorded, and takes B: an entry naming what a thread is a variant of,
for which language and model.
- **Full names**, as now.
- **Filters once B is built**: `variant_of`, `model` and `language` on `GET /api/threads`.
- **Filters now**, parsing names as the bench does (`chatddx.catalog.variants_for`).

Take: full names until B; filters on names now would build on what B replaces.

### O25. An unsaved variation's runs are titled by their whole recipe
A run's title is its skeleton's, and a skeleton nobody saved is titled by its recipe in full (docs/catalog.md, "A
variation nobody saved has a long title"). The variation's label, `NAME+PART=CHUNK`, isn't stored.
- **As is.**
- **The label as the run's name**: a name entry on the run's subject as it starts, which the catalog takes for any
  subject, and which `described` reads first.
- **A shorter title** for an unsaved skeleton, worked out from compilations: its nearest configuration and what
  differs. The catalog's to decide.

Take: the label as the run's name; small, and the repl gains it too.

## Runs

### O26. A quiet stream
A stream sends nothing while an engine takes its time with the first token, or while the run is scored, and a proxy
cuts a connection that is quiet too long: nginx's `proxy_read_timeout` is 60 s by default. `X-Accel-Buffering: no`
is sent already.
- **Comment lines**, `: keep-alive`, every 15 s, which event readers skip.
- **A `heartbeat` event** among the stream's events.
- **The proxy's configuration**, left to whoever deploys it.

Take: comment lines.

### O27. Going away halts the run, not its scoring
A client that goes away halts its run, which is then finished and scored as always; the scoring's judge calls are all
sent (`Grading.halt` has no caller in the API).
- **As is.** Scoring costs less to finish than to redo, and nothing could redo it over HTTP.
- **Halted too**, once O1 exists: the score finishes with what it has, and the run is left to score.
- **Unjudged scorers only** after a halt.

Take: as is until O1, then halted too.

### O28. `Accept` is read by media type alone
`text/event-stream;q=0` still asks for a stream.
- **As is.**
- **`q` heard**: a media type at `q=0` isn't asked for.

Take: heard; small.

### O29. A server that stops
A run outlives a server that stops gracefully, which waits for its threads; a killed one leaves the run unfinished,
and checking it says so (`run.incomplete`). Nothing resumes a run (agents/wip-worker.md, "Below the worker").
- **As is.**
- **Finished at start-up**: runs left unfinished are finished as they are. No record says which process sent a run,
  so another replica's run under way would be finished too.
- **Resumed**, by the worker.

Take: resumed, with the worker.

### O30. A person's runs are all read
`GET /api/runs` reads every run of the person's, filters, and then pages (`Bench.runs`): 3.7 ms for two runs here.
O3's listing works out what is left of each run before paging.
- **As is.**
- **Paged in the store**, by limit and offset, with the filters in SQL.
- **Paged by a cursor**, the last run's start, which holds while runs are added.

Take: as is, until slow; then a cursor.

## Writes

### O31. Carrying answers 201 even when nothing changes
An expectation carried onto the case it is of already is kept `unchanged`, which an edit answers 200, but
`POST /api/threads/{id}/carries` always answers 201.
- **200 when unchanged**, as an edit.
- **As is.**

Take: 200.

## Not here
- **Two saves of one name at once** is the repl's `save`; the API's forks make a configuration per request by
  design.
- **The worker and the batch planner**: agents/wip-worker.md and agents/wip-batch.md, which O10, O11 and O29 wait on.
- **A policy for edges** that gates case-derived places: agents/wip-clearance.md.

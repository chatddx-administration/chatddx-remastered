# API

A candidate for `docs/api.md`. Its reference is `agents/wip-api-api.md`, a candidate for `docs/api-api.md`; below,
those two names mean these two files until they move. What is still open is in `agents/wip-bench.md`, "Outstanding",
with the bench's. The plan this was rewritten from, with the old API's survey and the options weighed, is
`agents/wip-api.md` at 100a078.

The API and its sibling, the repl, are the rig's control plane. The API reaches every write the bench makes; what it
doesn't do yet is in "Not covered", and in `agents/wip-bench.md`, "Outstanding".

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

A configuration made per language or model is a thread under its full name, until variants are recorded as such
(agents/wip-variants.md).

## What a person sees
- **Threads** of a kind, by the bench's word for it: configuration, each part, tool, scorer, judge, expectation,
  appendix, expectation_schema, canary_set, model or engine. A thread gives its kind, name, title, owner, tags and
  head, and on its own also its description, collaborators, language, the edit it was forked from, whether it is
  deleted, and for a configuration its recipe. Its versions come oldest first. Configurations are listed by purpose,
  those that give answers unless the judges' are asked for, since a judge configuration is no use at a run.
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
  person sees; where no case has the tags, over one case the person sees, without the cases' languages;
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

Chunks, appendices, expectations and scorers are written the same way, with a component where a configuration takes
parts, as its JSON as a component's own request gives it, and a scorer with the labels of its views and resources
(`agents/wip-bench.md`, "Components" and "Scorers"). A judge is written the same way, over a judge configuration,
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
is deleted (`agents/wip-bench.md`, "What is said about a thread"). Deleting is also a request of its own. What holds
afterwards comes back. A deleted thread is restored before anything else is said of it. Another's thread is "not
found", as "no expectation N of yours" for an expectation; a login that names nobody, an empty name or tag, and
taking a description away are unprocessable.

## Typed cases
A person types a case: its text, and a name and a language if they like. It is kept as written, in the World's
database source, with its case and a family of their own, which comes back as a family does (`agents/wip-bench.md`,
"Typed cases"); its vignette is then read as any family's. A text is held to a length and a person to a number of texts
a day: past the day's is 429.

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
  whether its case was taken, and into which thread, or was kept as theirs, has several shared to choose from, or
  has none shared. Nothing of theirs changes, so the request is safe to repeat, and it is answered 200 whatever it
  took. A family the person doesn't see, or an owner who doesn't exist, is unprocessable.
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
for tags no case has, and for a judge configuration, which is asked as runs are scored rather than run on cases.
Once started, it is answered 202 with what `run.started` holds, and the run's path as `Location`.

A run is sent under the default execution, with no timeout, and with no canary set or text cleanup.

### Where it runs
A started run is sent on a thread of its own, with a database connection of its own, and is then finished and scored
under every scorer that applies to it, unless asked not to be, whether or not anyone is listening. It is in the app's
process for now: what the app has under way for a run, the run or a scoring of it, is a job, which keeps its events
until another job of the run takes its place, and ends with the process. The worker is to take its place with the API
as it is (agents/wip-worker.md). Its rows land as they are written, so a run can be read back at any point.

### Its events
`GET /api/runs/{id}/events` streams what is under way for the run, from its start, and then as it comes, ending with
`done`; it is sent unbuffered and uncached, so a proxy passes it on as it comes. Each event has an `id`, its place in
the job, and its data is one line of JSON, whose models are among the OpenAPI document's schemas. A stream asked for
with `Last-Event-ID`, as `EventSource` asks again, goes on after it. A delta is kept until its item or judge call has
ended, so a stream joined late has every event but the deltas of what ended before it joined. A run with nothing in
the app's process, as one started before it or elsewhere, is told from the ledger: its items as they ended, with no
deltas or judge calls, its finish, its latest scores, and `done`.

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
| `run.scoring` | a scoring starts, after the run or asked for | the scorers it is to score by |
| `score.started` | a scorer's score starts | the scorer, its name, the score and its views' labels |
| `judge.asked` | a judge is sent an item's view, for one seed | the case and replicate, the scorer, the view, the judge and the seed's index |
| `judge.delta` | a chunk of the judge's answer streams in | the case and replicate, and as `item.delta` |
| `judge.answered` | the judge's call is recorded | the case and replicate, the view, the judge, the seed's index, the verdict read, and the call |
| `score.item` | a score item is written | the score, the case and replicate, the view, its value and detail |
| `score.noted` | the scoring pass noted something, such as an answer its schema refuses | a finding |
| `run.scored` | the scoring is over | each scorer's score, or why it gave none |
| `error` | what was under way failed | why |
| `done` | last | whether it was halted, `null` when told from the ledger |

An item's outcome is stopped, errored, unread, salvaged, completed, invalid or valid, by its last call and the answer
read from it; salvaged is a structured answer cut short, read with its structure closed.

### Halting
A person halts what is under way for a run of theirs: the calls under way are hung up and recorded as stopped, the
run is finished, and it isn't scored, so it is left to score; a scoring under way finishes the score it is on with
what it has, and the scorers after it are refused as stopped. Leaving a stream halts nothing. A halt with nothing
under way is a conflict.

### Reading runs
- **A person's runs**, newest first, a page at a time, filtered by trial, by a digest their trial is built on, by
  a scorer that scored them, or to those left to score, each with the scorers it is left to be scored by. Each says
  what ran: its trial, skeleton, engine, endpoint, cases, seeds, and a line saying it as people read it.
- **A run** adds when it started and finished, the rig it ran on, what it noted as it went, what checking it finds
  now, each item's outcome and tokens, and its latest score under each scorer.
- **A run's scores**: the latest under each scorer, or every one, newest first, or one by its id. A score says its
  scoring, when it started and whether it finished, each item's value under each view, and each view's mean.
- **A score's items**: each item's detail and judge calls, and the findings of the score. They are case-derived.
- **A run's items**: each call as it was recorded, with its response and tool rounds, and why the item ended as it
  did. They are case-derived.
- **Whether each item renders again** as it was sent: only a request's fingerprint is kept, so the request is
  rendered again from the trial and the source, and compared.

Only the person's own runs are seen; a collaborator on a run doesn't see it.

## Scoring
A run is scored as soon as it is finished, under every scorer that applies, because how it scored is what a client
most wants after a run; a request can ask for it to be left, with `"score": false`. A judged view is scored as any
other, its judge's calls sent to the one endpoint that serves the judge's engine. The scores come in `run.scored`, and
with the run when it is read: each item's value under each view, and each view's mean over the items, or why the
scorer gave none. A judged view's value is the mean over the seeds whose verdicts were read.

A finished run is scored again when asked, under every scorer that applies or some, as a run is sent: answered 202
with the scorers it is to score by, it goes on whoever listens, and its events are the run's. The runs left to score
are listed, each with the scorers it is left to be scored by (see "Reading runs"), and what each seed gave and the
judge said is in the score's items. An unfinished run, a scorer that doesn't apply, and a run nothing applies to are
refused, and so is a run with something under way.

## Case-derived content
What is made from a vignette is shown to whoever signed in, but only in its own places, so that a policy for edges
can gate those few when clearance has one (agents/wip-clearance.md):
- a family's vignette;
- a run's items;
- a score's items, with their detail and judge calls, and the score's findings;
- a run's events: the deltas, the tool runs, why each item ended, and the scoring's items, judge calls and
  findings.

Nothing else carries any. Why an item ended can quote the answer, since checking it against a schema names the value
it refused, so it is in the items and the events only. For the same reason a score gives values, and its detail,
judge calls and findings are its items'.

## Errors
A refusal's body is `{"detail": "…"}`, except where a request doesn't validate: then it lists where.

| Status | When |
| --- | --- |
| 401 | No session, one that has ended, or a wrong login or password. |
| 403 | A cookie's request that changes something, or a sign-in, from another site's page. |
| 404 | What the path names isn't there or isn't seen by the person, a thread is of another kind than the route takes, a source doesn't hold a vignette, or a thread to edit, follow, carry or say something of isn't the person's. |
| 409 | Taking an expectation the person has their own of, without saying to replace it; an edit, a follow or a carry whose head has moved on; scoring a run with something under way, and halting one with nothing under way. |
| 422 | A request that doesn't validate or names a field it shouldn't; a kind that isn't one, or a purpose for what isn't a configuration; a variation the bench refuses; a query or body naming what the person doesn't see; tags no case has; the gate's refusal of a run; taking an expectation that is the person's already; a component the bench refuses, or parts for what isn't a configuration and a component for what is; what is said of a thread that the bench refuses, or of a deleted one; following with nothing to follow; a case of appendices or a replacement the bench refuses; carrying an expectation outside its family; a run naming a case that isn't a current one of a family the person sees; a run of a judge configuration; scoring a run that hasn't finished, by a scorer that doesn't apply to it, or one nothing applies to. |
| 429 | A person who has typed as many cases as a day takes. |

An edit that changes nothing is answered 200 with the head; what is made is answered 201; a deletion and a halt 204;
a run or a scoring started 202. What fails once it is under way is an `error` event, not a status. A take for
many cases is answered 200, whatever it took, and a carry 201, even when the expectation is on that case already.

## Not covered
- **A vignette in a run's request.** A run takes cases; a text to run is typed first, and kept in the World's
  database source as a case of its own (see "Typed cases").
- **A trial beyond one seed**: replicates, an execution's settings, canary sets and text cleanup are the batch
  planner's and the worker's (agents/wip-batch.md, agents/wip-worker.md).
- **A proxy's forward auth**: once a proxy authenticates, that is its job.
- **A person's secrets.** An endpoint's credential comes from an environment variable, as in the repl.
- **Scoring every outstanding run in one request.** A client scores one run at a time (see "Scoring").
- **"Run N of trial X"**, which the repl says after a run. A run's trial lists its runs.

## Tests
The tests start from the test World (`worlds/test`, agents/wip-test-world.md) as `chatddx init-data` lands it, with
alice signed in by a bearer token and bob for what isn't his to see. They speak to the app through Starlette's test
client over HTTPS, since the cookie is only sent over it. Runs are sent to the fake vLLM serving the test World's
endpoints on ports nothing else uses.

The test client runs a streamed response to its end whether or not its reader hangs up, so the tests of halting
and of leaving a stream serve the app with uvicorn on a thread, and speak to it over a socket.

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
| Outcome | How an item ended: stopped, errored, unread, salvaged, completed, invalid or valid. |
| Event | One step of what is under way for a run, as its events tell it. |
| Job | What the app has under way for a run: the run, or a scoring of it, with its events. |
| Halt | Ending what is under way for a run early: its sending, hanging up the calls under way, or its scoring. |
| Case-derived | Made from a vignette, or quoting what was: the vignette, answers, tool runs. |

## Outstanding
What is still open of the API, from the takes it is built on to its smaller issues, is in `agents/wip-bench.md`,
"Outstanding", with the bench's. It doesn't move to `docs/`.

# API

The API and its sibling, the repl, are the rig's control plane.

The endpoints are in the OpenAPI document the API serves, at `/api/openapi.json`, with pages at `/api/docs`. This
document describes what the API does and why it is shaped like it is.

It serves programs, such as scripts, notebooks for analysis and export, and CI, and browsers, the portal among them
where it is interactive. A session is carried either way, as a bearer token or as a cookie, and the checks a cookie
needs are there from the start rather than added later.

```
AGENT: replace
Said in docs/modules/bench.md ("What a bench is not"), which has an edge read what takes no person where it
is, not through the bench's reads as here; settle which holds before applying.
---
- **The bench is the surface for what depends on who is asking**: what a person sees, finds and owns. What doesn't
  depend on them is the same for everyone, and is read where it is (docs/modules/bench.md, "What a bench is not").
```
- **The bench is the surface for what depends on who is asking**: what a person sees, finds and owns. What doesn't
  depend on them is the same for everyone, read from the store and the World, if through the bench's reads that take no
  person: a component by its digest, the endpoints, and the models by their handles.
```
AGENT: replace
Kept at docs/modules/identity.md ("Authorization"), which owns it; that the runner's gate enforces clearance
is only here, and stays.
---
- **What a person sees is a convenience, not protection** (docs/modules/identity.md, "Authorization"); the runner's gate
  enforces clearance.
```
- **What a person sees is a convenience, not protection.** It decides what is relevant to show them. Protection is
  clearance, which the runner's gate enforces, and the database's grants (agents/wip-clearance.md).
- **The docs' words**: configuration, variation, part, chunk, endpoint, engine, family and case, trial, run, score.

## Signing in

```
AGENT: dedupe
Its "lasts 12 hours", "A wrong login is refused…" and "Signing out ends the session" are also in
docs/modules/identity.md ("Authentication"), which suits them best.
---
```
A person signs in with a login and a password, and gets a token for a session that lasts 12 hours. The answer also sets
the token as a cookie, `__Host-chatddx-session`: `HttpOnly`, `Secure`, `SameSite=Lax`, for every path of this host, and
as long as the session lasts. A wrong login is refused with the same answer as a wrong password. Signing out ends the
session the request acts in and drops the cookie, and `/api/me` says who the person is.

Every other request acts in the session of its `Authorization: Bearer` token, else of its cookie. Without either, or
with one that has ended, it is refused with `WWW-Authenticate: Bearer`.

### Requests from other sites

A browser sends the cookie with requests from any page, so a cookie's request that changes something must come from this
site's own pages, and so must signing in, which a forged sign-in would abuse. Where the browser sends `Sec-Fetch-Site`,
it must be `same-origin` or `none`; else `Origin`, where it is sent, must name this host. A request with neither header
isn't a browser's on another page's behalf, and passes. A bearer's requests aren't checked, since no browser adds a
bearer by itself.

The check stands in for a CSRF token, which would need one stored per session.

## Ids

```
AGENT: dedupe
From "Names are for people". Also in docs/modules/catalog.md ("Names"), which suits it best; the slash is also in
docs/modules/bench.md ("Finding things by name").
---
```
Threads and families are named by their integer ids, runs by their whole UUIDs, components by their digests, and
endpoints by their names in the inventory. Names are for people: they needn't be unique, they may hold spaces, and
slashes, as `Qwen/Qwen3-8B-AWQ` does, and they change. So a list takes a name as a filter and returns every match, and a
path takes an id. An id's prefix, handy at a prompt, could name another run tomorrow, so only whole ids are taken.

```
AGENT: dedupe
docs/modules/bench.md ("Translations") suits it best, though only this and docs/modules/repl.md ("Names")
say the name carries neither a language nor a model.
---
```
A configuration is one thread whatever the languages it runs in, under a name that carries none, `plan`; its model is a
part, and its name carries no model either.

## What a person sees

```
AGENT: dedupe
From "A configuration's language is its head's recipe's". Also in docs/modules/catalog.md ("Languages"), which
suits it best. What it is translated into is said only here.
---
```
- **Threads** gives its kind and the word for it, name, title, owner, tags, language, the languages it is translated
  into (`translated`) and head, and on its own also its description, collaborators, the edit it was forked from, whether
  it is deleted, and for a configuration its recipe. A configuration's language is its head's recipe's, its own, and it
  is translated into the languages its head's translations hold; any other kind into none.
```
AGENT: dedupe
From "Several to choose from": docs/modules/bench.md ("One expectation per case and schema") suits it best;
also docs/modules/api.md ("Trying a variation"), which points there.
---
```
```
AGENT: dedupe
From "its cases at its current vignette": docs/modules/bench.md ("Appendices and cases") suits it best; also in
docs/modules/bench.md ("What a person sees") and docs/modules/api.md ("Appendices and cases").
---
```
- **Families**, each with the case of its current vignette, filtered by tag or name. A family on its own adds its
  description and collaborators, and its cases at its current vignette, the one it stands for first, each with its
  appendices and, under each expectation schema the person sees, the expectation it is scored against: their own, so a
  schema under which they only see shared ones has none (`docs/modules/bench.md`, "What a person is scored against").
  Several to choose from don't fail the request; that schema says so instead. Each schema also lists the expectation
  threads shared with the person they could take.
- **A family's vignette**, fetched from the World's source, and whether it still is the text the case was made from
  (unknown under a keyed fingerprint). It is sensitive (see "Sensitive content").
- **Endpoints**: each one's engine and the engine's title, the model it serves, its URL and host, how many requests it
  takes at once, its credential's name, the sources it is cleared for, and whether a typed case can run there. One whose
  engine isn't stored, or whose URL can't be told, says why rather than failing the listing.
- **Models**: what the stored facts say of each, the head of its `facts` thread, so a corrected fact shows at once; and
  the endpoints serving it. A `facts` thread is listed as any thread is, under the word `facts`.
- **Components**: any stored component by its digest, with its kind and title; and the kinds of component, each with the
  bench's word for it, whether a person writes it, and its JSON Schema, in which a reference names the kinds it takes
  (`x-kind`). These are the same for everyone.

```
AGENT: dedupe
From "Their own deleted threads": docs/modules/bench.md ("What a person sees", "Their own deleted threads")
suits it best; "with its versions" is this place's own.
---
```
```
AGENT: dedupe
Its first sentence repeats docs/modules/bench.md ("Errors"), `NotFound`, which suits it best; also
docs/modules/api.md ("Errors"), `not_found`.
---
```
A thread, family or run the person doesn't see is "not found", the same as one that doesn't exist. Their own deleted
threads are listed apart, and each can still be read by its id, with its versions, so that it can be restored.

## Trying a variation

```
AGENT: replace
Kept at docs/modules/bench.md ("The variation being tried"), which says what a variation is and that looking
writes nothing.
---
A request states a configuration's variation whole each time (docs/modules/bench.md, "The variation being tried").
```
A configuration's variation is the configuration with some of its parts replaced. A request states it whole each time
and nothing is stored by looking.

```
AGENT: replace
From "a variation with parts replaced": restates docs/modules/bench.md ("The variation being tried"), which suits
it best. Keeps that a look and a run can differ, and what a run records.
---
The latest configuration means its head when the request comes (unless an edit is given), and a variation with parts
replaced is compiled then (docs/modules/bench.md, "The variation being tried"), so a variation looked at and one run
moments later can differ if the configuration or the facts moved in between; each run records the skeleton it ran, and
its compilation the facts.
```
The latest configuration means its head when the request comes (unless an edit is given), and a variation with parts
replaced is compiled against the facts about its model as they are stored then, so a variation looked at and one run
moments later can differ if the configuration or the facts moved in between; each run records the skeleton it ran, and
its compilation the facts.

A look at a variation gives:

- the edit it was built on, its label (`NAME+PART=CHUNK`, `docs/modules/bench.md`, "The variation being tried"), the
  digest of the skeleton it compiles to, the configuration whose head is that skeleton with the variation's recipe, the
  person's own first, and whether its sampling is greedy.
```
AGENT: dedupe
From "A reasoning level, and a recommended sampling": repeats docs/modules/bench.md ("The variation being
tried"), which suits it best; also docs/modules/repl.md ("Looking"). `landed` and `nearest` are the API's.
---
```
- each part's chunk, its title and what it holds, and whether it was replaced; the model is a part too, by its digest. A
  reasoning level, and a recommended sampling, also say the level the model is asked for (`landed`), and why the level
  asked for landed on its nearest instead, when it did (`nearest`; docs/modules/facts.md).
```
AGENT: dedupe
docs/modules/bench.md ("The variation being tried", "the request it would send") suits it best; `under` is
this place's own.
---
```
- the request it would send, with placeholders for the case and, for a hand-written configuration looked at without a
  handle (`under`), for the model.
```
AGENT: replace
Why a variation can't run is the bench's; kept here: the fields.
---
- the handle it runs under (`model`), or why it can't run (`problem`; docs/modules/bench.md, "The model").
```
- the handle it runs under (`model`), or why it can't run (`problem`): its handle is deleted, or no endpoint here serves
  it, and another is to be picked; its model is behind its handle; or it names no model and no handle is given.
- Translations (`docs/modules/bench.md`, "Translations")

A case with expectations to choose from is listed apart, as `choosing`, rather than as one without
(`docs/modules/bench.md`, "What a person is scored against"). An unsaved variation is linted in the language each trial
is sent in, its own as written or the one it is translated into, since the language of a skeleton otherwise comes from
its stored compilations, which it hasn't got yet.

A variation the bench refuses is unprocessable: a digest that isn't a stored chunk of its part, or a stored model; a
part that can't be taken out, the model among them; parts that don't compile together, among them a reasoning level or a
recommended sampling that the facts about the model refuse, or that a model without facts can't work out; a handle named
for a hand-written configuration that isn't one; or a parameter the request doesn't know, so that a misspelt part is
refused rather than ignored. A look's queries don't grow with the number of cases it is over.

## Translations

See docs/modules/bench.md, "Translations".

## Checking a component

A component of a kind a person writes is checked as a write would store it, and nothing is written: its rules, its
references, which must be stored, the rules that take several components, and a scorer's code and parameters. It gives
back the digest it would have and what the lints say of it, or is refused as the write would be. A client checks what a
person types as they type it.

A recipe is checked as making a configuration of it would make it, and nothing is written: each part a stored chunk of
that part and the model a stored model, compiled against the facts about its model as they are now. It gives back the
digest of the skeleton it compiles to and what the lints say of it, or is refused as making it would be.

## Picking

Selectors are applied to a document the request gives: each a JSON Pointer, or a JSONPath query of the subset a view
takes (docs/modules/factors.md, "View"), picks what it does in the document's order, or says why it doesn't read.
Nothing is read from the store and nothing is written, so a client shows what a view would pick from an expectation as
it is typed, with the same selection the scoring pass makes.

## Forking and editing

```
AGENT: replace
Forking, editing and saving by name are docs/modules/bench.md ("Configurations")'s; the two requests and
what they answer are the API's own and stay.
---
Keeping a variation is two requests, rather than one save by name as the repl's `save NAME` is (`docs/modules/bench.md`,
"Configurations"):

- **Fork** any configuration the person sees, with parts replaced and a name, from its head or from an earlier edit of
  it given; an edit of another configuration is "not found".
- **Edit** a configuration of their own, with parts replaced over its head: a new version, or nothing when the variation
  is the head already, which is answered as such. Another's configuration can't be edited, and is "not found" as "no
  configuration N of yours".
```
Keeping a variation is two requests, rather than one save by name as the repl's `save NAME` is, which makes a new
version of the person's configuration of that name if there is one, and a new configuration otherwise:

- **Fork** any configuration the person sees, with parts replaced and a name, into a new configuration of their own,
  from its head or from an earlier edit of it given; an edit of another configuration is "not found".
- **Edit** a configuration of their own, with parts replaced over its head: a new version, or nothing when the variation
  is the head already, which is answered as such. Another's configuration can't be edited, and is "not found" as "no
  configuration N of yours".

Chunks, appendices, expectations and scorers are written the same way, with a component where a configuration takes
parts, as its JSON as a component's own request gives it, and a scorer with the labels of its views and resources
(`docs/modules/bench.md`, "Components" and "Scorers"). A judge is written the same way, over a judge configuration, an
engine and its seeds:

```
AGENT: dedupe
These three items: docs/modules/bench.md ("Components"), cited above, suits them best; also in
docs/modules/bench.md ("Writes for the person", "One set of writes for every kind."). The fields are the API's.
---
```
- **New**: a component, a name, and the language of its text when it has one, as a thread of the person's own; or a
  recipe, by the chunks' digests for its parts and the digest of its model, its purpose and its appendix layout, made
  into a new configuration of their own with no origin.
- **Fork** any thread of those kinds the person sees, from its head or from a component given in its place.
- **Edit** a thread of their own with a component.

```
AGENT: dedupe
From "What is written comes back": also in docs/modules/bench.md ("Writes for the person", "What was written
comes back with its lints"), which suits it best.
---
```
```
AGENT: replace
The refusal's reason is docs/modules/catalog.md ("Threads and edits")'s; the conflict is the API's own and
stays.
---
Every edit names the head it was made on, and is a conflict when the thread has moved on since
(`docs/modules/catalog.md`, "Threads and edits"). What is written comes back with what the lints say of it, such as an
expectation whose data its schema refuses, which is written all the same.
```
Every edit names the head it was made on, and is a conflict when the thread has moved on since, so a change made on an
older version never undoes what came after it. What is written comes back with what the lints say of it, such as an
expectation whose data its schema refuses, which is written all the same.

## What is said about a thread

```
AGENT: replace
The rule is the bench's write, which this cites already; kept here: the request, what comes back and the
statuses.
---
Its owner says what holds of a thread in one request, giving only what changes (docs/modules/bench.md, "What is said
about a thread"). What holds afterwards comes back. Another's thread is "not found", as "no expectation N of yours" for
an expectation, and what the bench refuses there is unprocessable.
```
Its owner says what holds of a thread in one request, giving only what changes: its name, or none so that its title
shows; its description; its tags and who it is shared with, each as the whole list, people by login; and whether it is
deleted (`docs/modules/bench.md`, "What is said about a thread"). What holds afterwards comes back. A deleted thread is
restored before anything else is said of it. Another's thread is "not found", as "no expectation N of yours" for an
expectation; a login that names nobody, an empty name or tag, and taking a description away are unprocessable.

## Typed cases

```
AGENT: replace
Typed cases are docs/modules/bench.md ("Typed cases")'s, which this paragraph already cites; the 422 for a
missing language, the family coming back and the 429 are the API's own and stay.
---
A person types a case (`docs/modules/bench.md`, "Typed cases"); a case typed without a language is unprocessable. The
family made with it comes back as a family does, and a text past the day's quota is 429.
```
A person types a case: its text, the language it is written in, and a name if they like; a case typed without a language
is unprocessable, since a configuration is sent in its case's language. It is kept as written, in the World's database
source, with its case and a family of their own, which comes back as a family does (`docs/modules/bench.md`, "Typed
cases"); its vignette is then read as any family's. A text is held to a length and a person to a number of texts a day:
past the day's is 429.

## Appendices and cases

```
AGENT: replace
From "The person writes an appendix": building a case, a new version, carrying and replacing are told in
docs/modules/bench.md ("Appendices and cases"), which suits them best; what the requests carry stays here.
---
A family gives its cases at its current vignette, its default first, each with its appendices and the expectation it is
scored against under each schema (`docs/modules/bench.md`, "Appendices and cases"). The person writes appendices, builds
cases, stores replacements and carries expectations (`docs/modules/bench.md`, "Appendices and cases"). An appendix's new
version, written as any edit, answers with each case it replaced, and a carried expectation's edit names the case and
the head it was made on.
```
```
AGENT: dedupe
Up to "its default first": docs/modules/bench.md ("Appendices and cases") suits it best; also in
docs/modules/bench.md ("What a person sees") and docs/modules/api.md ("What a person sees").
---
```
A family gives its cases at its current vignette, its default first, each with its appendices and the expectation it is
scored against under each schema (`docs/modules/bench.md`, "Appendices and cases"). The person writes an appendix for a
family from its text, and builds a case from appendices they see, in order, or stores the replacement of a case a repair
left at an earlier vignette. An appendix's new version, written as any edit, answers with each case it replaced. An
expectation is carried onto another case of its family by an edit of its own naming that case, which names the head it
was made on.

## Following

```
AGENT: replace
What a proposal holds restates docs/modules/bench.md ("Following an origin"), which suits it best and is cited.
Keeps the request: both followings at once, the head, the lints, the language and what is unprocessable.
---
A fork whose origin has moved on has a proposal: what following would keep (`docs/modules/bench.md`, "Following an
origin"). A configuration whose facts or model have moved on has what following them would keep, or why the facts now
refuse it (docs/modules/catalog.md, "What has moved on"). One request asks for both, each nothing when there is none.
Following either is an edit of the person's own thread, which names the head it was made on and comes back with what the
lints say; only following an origin takes a language. Following a thread with nothing to follow, or whose changes no
longer fit, is unprocessable.
```
A fork whose origin has moved on has a proposal: what following would keep, with the base, the origin's head, what the
fork varies, and for a configuration the recipe it compiles from (`docs/modules/bench.md`, "Following an origin"). A
configuration whose facts or model have moved on has what following them would keep, or why the facts now refuse it
(docs/modules/catalog.md, "What has moved on"). One request asks for both, each nothing when there is none. Following
either is an edit of the person's own thread, which names the head it was made on and comes back with what the lints
say; only following an origin takes a language. Following a thread with nothing to follow, or whose changes no longer
fit, is unprocessable.

A thread's lineage is its first origin and every fork below it, as far as the person sees them, each with its origin,
its base and what it varies, whether its origin has moved on since, and whether it is deleted, which only its owner
sees.

## Taking expectations

A person is scored against their own expectations only, so they take the shared ones (`docs/modules/bench.md`,
"Taking"):

```
AGENT: replace
Restates docs/modules/bench.md ("Taking"), which suits it best and which the sentence above points to.
Keeps the request, the answer and its statuses; what is left and why, and what replacing does, are the bench's.
---
- **For many cases**, by family, under one schema, from any owner or one named. The answer says, for each family,
  whether its case was taken, and into which thread, or why not. It only adds, so it is answered 200 whatever it took. A
  family the person doesn't see, or an owner who doesn't exist, is unprocessable.
- **One thread**, an expectation shared with them, into a thread of their own, or a conflict when they have their own of
  its case under its schema, unless the request says to replace theirs.
```
- **For many cases**, by family, under one schema, from any owner or one named. The answer says, for each family,
  whether its case was taken, and into which thread, or was kept as theirs, has several shared to choose from, or has
  none shared. Nothing of theirs changes, so the request is safe to repeat, and it is answered 200 whatever it took. A
  family the person doesn't see, or an owner who doesn't exist, is unprocessable.
- **One thread**, an expectation shared with them, into a thread of their own. When they have their own of its case
  under its schema, it is a conflict unless the request says to replace theirs, which deletes it in the same write.

## Runs

### Starting one

Runs are started within their request, so whatever refuses them does so before anything is sent.

```
AGENT: replace
States the rule docs/modules/bench.md ("Translations") is cited for, which suits it best (see the insert there).
Keeps that the answer says what was left out and why.
---
A start is a run per language its cases are sent in (`docs/modules/bench.md`, "Translations"), and the answer says which
cases were left out and why.
```
A start is a run per language its cases are sent in (`docs/modules/bench.md`, "Translations"): the cases in the
configuration's own language, and those in none, as written, and those in each language its translations cover
translated, each a run of its own. The cases of a language they can't carry it into are left out, and the answer says
which and why; a start that can send none of its cases is refused.

Any person can start at most `settings.RUNS_PER_DAY` runs a day, and a run holds at most `settings.ITEMS_PER_RUN` items;
a start's runs are held to both before any of them starts, each counting as a run.

```
AGENT: replace
Kept at docs/modules/catalog.md ("What a run ran"), which this already points to; the `ran` field stays.
---
Each run gives back its cases' digests and its language, and is named by the variation's label, `NAME+PART=CHUNK`.
Listed or read, a run says what it ran (`ran`; docs/modules/catalog.md, "What a run ran"); the runs of a start say the
same. A run also says the first run of its start (`started_with`), null for the first and for a run started alone, and
`GET /api/runs?with=RUN` lists a start's runs, the first among them.
```
Each run gives back its cases' digests and its language, and is named by the variation's label, `NAME+PART=CHUNK`.
Listed or read, a run says what it ran (`ran`): the configuration, the edit the variation was built on and the parts
replaced over it, or nothing for a run started from a trial alone (docs/modules/catalog.md, "What a run ran"); the runs
of a start say the same. A run also says the first run of its start (`started_with`), null for the first and for a run
started alone, and `GET /api/runs?with=RUN` lists a start's runs, the first among them.

```
AGENT: replace
Where a run goes and when its handle is refused is the bench's, which this cites already; kept here: `under`,
the refusal only the API has, and that it comes before the gate.
---
A run goes under its variation's handle (docs/modules/bench.md, "The model"); a hand-written configuration names no
model, so a start names the handle it runs under (`under`). What the bench refuses there, and a handle named for a
configuration with a model part, as one it runs under already, are refused before the gate is asked.
```
A run goes under its variation's handle, to the one endpoint the handle resolves to, and its trial takes the handle's
latest engine; a hand-written configuration names no model, so a start names the handle it runs under (`under`). A
handle that resolves to no endpoint or several is refused as ops' error, a variation whose weights its handle no longer
holds as behind its model, and a handle named for a configuration with a model part as one it runs under already, all
before the gate is asked (docs/modules/bench.md, "The model").

```
AGENT: replace
Kept at docs/modules/runner.md ("The gate"), which lists the refusals in order; this said "doesn't answer"
where the gate checks that the server lists the engine's name.
---
Then the gate decides (docs/modules/runner.md, "The gate").
```
The gate refuses an endpoint that doesn't serve the trial's engine, isn't cleared for a sensitive source among the
cases', or lacks its secret; tools that would get a sensitive source's content; and an endpoint that doesn't answer.

Once started, each run is queued for the worker as a job of its own, and the start is answered 202 with `runs`, what
each run's `run.started` holds, those sent as written first, and `left_out`, each language left out with its cases and
why; `Location` is the first run's path.

```
AGENT: replace
Restates docs/modules/inventory.md ("Endpoints") and docs/modules/inventory.md ("Sources"), which suit it best and
are cited: the capacity, the canary set, where cleanup comes from. Keeps what the request gives and the drawn seed.
---
A run is sent under its endpoint's execution and canary set (docs/modules/inventory.md, "Endpoints"), with the
concurrency and the order the request gives, a shuffled order's seed drawn, and with the cleanup steps the request gives
(docs/modules/inventory.md, "Sources").
```
A run is sent under its endpoint's execution (docs/modules/inventory.md, "Endpoints"), with the concurrency, up to the
endpoint's capacity, and the order the request gives, a shuffled order's seed drawn; with its endpoint's canary set; and
with the cleanup steps the request gives, else those its cases' sources ask for (docs/modules/inventory.md, "Sources").

### Where it runs

```
AGENT: replace
What a worker does with a job is told in docs/modules/worker.md ("A job"), and that it outlives its process in
docs/modules/worker.md ("Worker"); they suit it best. "unless asked not to be" and how it is followed stay.
---
A started run is queued as a job (docs/modules/worker.md, "A job"), and scored under every scorer that applies to it
unless asked not to be. It is followed and halted from any process: its events are told from the store (see "Its
events"), and a halt goes through the queue (see "Halting").
```
```
AGENT: dedupe
Its "and scores it under every scorer that applies to it, unless asked not to be" repeats docs/modules/api.md
("Scoring"), which suits it best.
---
```
A started run is queued as a job in the store, and a worker sends it, finishes it and scores it under every scorer that
applies to it, unless asked not to be. A job outlives the process that queued it, and is followed and halted from any
process: its events are told from the store (see "Its events"), and a halt goes through the queue (see "Halting").

### Its events

`GET /api/runs/{id}/events` tells the run's rows, its scores' included, in the order they were written; then, while a
job for the run is queued or under way, what the worker says as it happens and the rows as they land; and ends with
`done`. Each event's data is one line of JSON, whose models are among the OpenAPI document's schemas.

The last event a row tells has the row's number as its `id`, so that a stream asked for after an id is told the rows
after it, in any process, after a restart, and across a scoring again. What isn't a row has no id, and is told only to
the streams listening as it happens: an item about to be sent, its deltas and tool runs before it is recorded, a scoring
starting, a judge asked, its deltas and its answer, and the scoring over.

```
AGENT: replace
From "Deltas go out together": how deltas are batched is told in
docs/modules/worker.md ("What it says as it happens"), which suits it best, as the worker batches them.
---
A stream that joins mid-item is told that the item started, its text from when it joined, and each tool run once; its
whole answer is the item's once it is recorded. Deltas go out in batches (docs/modules/worker.md, "What it says as it
happens").
```
A stream that joins mid-item is told that the item started, its text from when it joined, and each tool run once; its
whole answer is the item's once it is recorded. Deltas go out together, a tenth of a second's at a time.

A stream joined after its run's job ended, or for a run no job took, is told the rows, the latest scores as
`run.scored`, and `done`.

| Event            | When                                                                                     | Holds                                                                                                                           |
| ---------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------- |
| `run.started`    | first                                                                                    | the run, its trial and skeleton, the language it is sent in, the endpoint, the cases, the seeds, and whether sampling is greedy |
| `item.started`   | an item is about to be sent, or a stream first hears of it                               | its case and replicate, and its seed                                                                                            |
| `item.delta`     | a chunk of an answer streams in                                                          | its case and replicate, the kind (reasoning, content or a tool call), the text, and the tokens so far                           |
| `item.tool`      | a tool has run for a call                                                                | its case and replicate, and the tool run                                                                                        |
| `item.ended`     | an item is recorded                                                                      | its case and replicate, its outcome and why, and its tokens                                                                     |
| `canary.ended`   | a canary call is recorded                                                                | the phase, which canary, and the call                                                                                           |
| `run.noted`      | the run is recorded as finished, before `run.finished`                                   | a finding noted along the way, such as a case that couldn't be read                                                             |
| `run.finished`   | the run is recorded as finished                                                          | what checking it found                                                                                                          |
| `run.scoring`    | a scoring starts, after the run or asked for                                             | the scorers it is to score by                                                                                                   |
| `score.started`  | a scorer's score starts                                                                  | the scorer, its name, the score and its views' labels                                                                           |
| `judge.asked`    | a judge is sent an item's view, for one seed                                             | the case and replicate, the scorer, the view, the judge and the seed's index                                                    |
| `judge.delta`    | a chunk of the judge's answer streams in                                                 | the case and replicate, and as `item.delta`                                                                                     |
| `judge.answered` | the judge's call is recorded                                                             | the case and replicate, the view, the judge, the seed's index, the verdict read, and the call                                   |
| `score.item`     | a score item is written                                                                  | the score, the case and replicate, the view, its value and detail                                                               |
| `score.noted`    | a scorer's score is recorded as finished                                                 | a finding of the scoring pass, such as an answer its schema refuses                                                             |
| `run.scored`     | the scoring is over; or before `done`, from the ledger, for a stream that wasn't told it | each scorer's score, or why it gave none; from the ledger, the latest scores                                                    |
| `error`          | before `done`, when the run's last job failed                                            | why                                                                                                                             |
| `done`           | last                                                                                     | whether the run's last job was asked to halt, `null` for a run no job took                                                      |

```
AGENT: dedupe
Also in docs/modules/repl.md ("Outcomes"), which suits it best as the only full list, and, for salvaged, in
docs/modules/factors.md ("Scorer").
---
```
An item's outcome is stopped, errored, unread, salvaged, completed, invalid or valid, by its last call and the answer
read from it; salvaged is a structured answer cut short, read with its structure closed.

### Running again

```
AGENT: replace
When a handle is refused, as ops' error or as behind, is the bench's.
---
Running again runs the run's skeleton over its cases in its one language, under its handle, and so at the handle's
latest engine, as a run of its own rather than one of the start it was made in, with new seeds or its own. Its handle is
refused as a variation's is (docs/modules/bench.md, "The model").
```
Running again runs the run's skeleton over its cases in its one language, under its handle, and so at the handle's
latest engine, as a run of its own rather than one of the start it was made in, with new seeds or its own. It is refused
as ops' error when the handle no longer resolves, and as behind when the handle holds other weights than the run's.

### Halting

```
AGENT: dedupe
From "It cancels the calls under way": docs/modules/worker.md ("Working a job", "A halt") suits it best, which
also has a halt stop a scoring.
---
```
A halt goes through the queue, and reaches the job's worker wherever it is. It cancels the calls under way, record them
as stopped and the run is finished unscored.

### Reading runs

- **A person's runs**, newest first by trial's digest or by a scorer that scored them
- **A run** adds when it started and finished, the rig it ran on, what it noted as it went, what checking it finds now,
  each item's outcome and tokens, and its latest score under each scorer.
```
AGENT: dedupe
Its first sentence: also in docs/modules/bench.md ("Runs and scores", "A run's scores"), which suits it best.
---
```
- **A run's scores**: the latest under each scorer, or every one, newest first. A score says its scoring, when it
  started and whether it finished, each item's value under each view, and each view's mean.
```
AGENT: dedupe
"They are sensitive." here and in the next item ("A run's items") is also in docs/modules/api.md ("Sensitive
content"), which suits it best; point there as "A family's vignette" does.
---
```
- **A score's items**: each item's detail and judge calls, or those of one case, and the findings of the score. They are
  sensitive.
- **A run's items**: or those of one case: each call as it was recorded, with its response and tool rounds, why the item
  ended as it did, and its answer as read from its last call, as the scorers read it, with why it couldn't be read or
  breaks its schema. They are sensitive.
```
AGENT: dedupe
"only a request's fingerprint is kept, so the request is rendered again": docs/modules/runner.md ("Sending")
suits it best; also docs/modules/repl.md ("Looking back") and docs/backlog.md ("Attestation within a run").
---
```
- **Whether each item renders again** as it was sent: only a request's fingerprint is kept, so the request is rendered
  again from the trial and the source, and compared.
- **Runs compared**, in the order given: the items every one of their trials holds, by case and replicate, each view's
  value per run and item, under each scorer that scored one of them, each view's mean per run over those items, and the
  cases only some of them hold.

```
AGENT: dedupe
Also in docs/modules/bench.md ("What a person sees", "Their own runs"), which suits it best.
---
```
Only the person's own runs are seen; a collaborator on a run doesn't see it.

## Scoring

A run is scored as soon as it is finished by default but a request can ask for it to be left with `"score": false`.

```
AGENT: dedupe
From "each item's value under each view": repeats docs/modules/api.md ("Reading runs", "A run's scores"),
which suits it best.
---
```
A judged view is scored as any other, its judge's calls sent to the endpoint its handle resolves to, at the engine the
scoring pins. The scores come in `run.scored`, and with the run when it is read: each item's value under each view. Also
each view's mean over the items, or why the scorer gave none.

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

```
AGENT: dedupe
From "Why an item ended can quote the answer": the reason repeats docs/modules/ledger.md ("Sensitive
records"), which suits it best; where the API serves them stays.
---
```
Nothing else should carry any, but why a job failed can quote what it was sending, and is served with the runs
(agents/wip-clearance.md, "Before real patient data" 10). Why an item ended can quote the answer, since checking it
against a schema names the value it refused, so it is in the items and the events only. For the same reason a score
gives values, and its detail, judge calls and findings are its items'.

## Errors

A refusal's body is `{"detail": "…", "code": "…"}`. The detail says why, or, where a request doesn't validate, lists
where. The code says what it is:

| Code              | Status | When                                                                                                                                                             |
| ----------------- | ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `unauthenticated` | 401    | No session, one that has ended, or a wrong login or password.                                                                                                    |
| `cross_site`      | 403    | A cookie's request that changes something, or a sign-in, from another site's page.                                                                               |
| `not_found`       | 404    | What the path names isn't there, or isn't the person's to see.                                                                                                   |
| `not_allowed`     | 405    | A method the path doesn't take.                                                                                                                                  |
| `ambiguous`       | 409    | Several where the bench is asked for one.                                                                                                                        |
| `conflict`        | 409    | Taking an expectation the person has their own of, without saying to replace it; scoring a run with something under way, and halting one with nothing under way. |
| `moved_on`        | 409    | An edit or a follow whose head has moved on.                                                                                                                     |
| `unprocessable`   | 422    | A request that doesn't validate, or names a field it shouldn't; the detail lists where.                                                                          |
| `refused`         | 422    | What the API, the bench or the gate refuses: the rest of 422.                                                                                                    |
| `over_quota`      | 429    | A person who has typed as many cases, or started as many runs, as a day takes; a run of more items than one takes.                                               |
| `error`           | 500    | An error for developers or ops, raw: its type and message.                                                                                                       |

The OpenAPI document holds the body as the schema `Error`.

```
AGENT: dedupe
From "A take for many cases". Also in docs/modules/api.md ("Taking expectations"), which suits it best, giving why.
---
```
An edit that changes nothing is answered 200 with the head; what is made is answered 201; signing out and a halt 204; a
run or a scoring started 202. What fails once it is under way is an `error` event, not a status. A take for many cases
is answered 200, whatever it took.

## Not covered

- **A vignette in a run's request.** A run takes cases; a text to run is typed first, and kept in the World's database
  source as a case of its own (see "Typed cases").
- **A proxy's forward auth**: once a proxy authenticates, that is its job.
- **A person's secrets.** An endpoint's credential comes from an environment variable, as in the repl.
- **Scoring every outstanding run in one request.** A client scores one run at a time (see "Scoring").
- **"Run N of trial X"**, which the repl says after a run. A run's trial lists its runs.

## Tests

```
AGENT: dedupe
Its first sentence: also in docs/modules/bench.md ("Tests"), which suits it best, being the same `curated`
fixture. The bearer token is said only here.
---
```
The tests start from the test World (`worlds/test`; docs/modules/inventory.md, "Worlds") as `chatddx init-data` lands
it, with alice signed in by a bearer token and bob for what isn't his to see. They speak to the app through Starlette's
test client over HTTPS, since the cookie is only sent over it. Runs are sent to the fake vLLM serving the test World's
endpoints on ports nothing else uses.

```
AGENT: replace
From "What isn't a row": that it is told only to a stream listening as it happens is said in
docs/modules/api.md ("Its events"), which suits it best.
---
The app the tests serve runs a worker in its process, as `chatddx run` does. A test that looks for what isn't a row (see
"Its events") pauses alice's queue, starts the run, reads the stream's first row, by when it listens, and then lets the
worker take the job.
```
The app the tests serve runs a worker in its process, as `chatddx run` does. What isn't a row is told only to a stream
listening as it happens, so a test that looks for it pauses alice's queue, starts the run, reads the stream's first row,
by when it listens, and then lets the worker take the job.

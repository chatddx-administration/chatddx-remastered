# Bench

A candidate for `docs/bench.md`. Its reference is `agents/wip-bench-api.md`, a candidate for `docs/bench-api.md`;
below, those two names mean these two files until they move. "Outstanding", at the end, stays behind when they do.

The bench is what one person sees and does, whatever the edge they reach it through: the threads, families and runs
they see, the World's endpoints, the variation they are trying, and what is written in their name. Its edges are the
repl (agents/wip-repl.md), the API (agents/wip-api.md) and the portal to come (agents/wip-portal.md). This document
describes what the bench does and why it is shaped like it is. Names, signatures and errors are in docs/bench-api.md.

The bench builds on the store, the catalog, the World, the facts, the runner and the scoring pass, and holds no SQL of
its own.

`bench` is the *operational* layer of "The person-scoped cake". Consult docs/chatddx.md's "The person-scoped cake"
before adding functionality to the bench.

## Not bench
- A facade, and nothing checks that an edge goes through it.
- Authorization, what the bench shows is what is relevant to show a person, not who may read what.

## How the bench works

### A person-scoped view
Everything that depends on who is asking goes through the bench; what doesn't is read straight from the store,
the World and the facts. An edge asks the bench which runs are the person's and which thread a name means to them, but reads a component
by its digest, or an endpoint's limits, from where they are kept.

### One person, one connection
A connection lasts as long as its caller, and caches logins and the model each engine serves for that long.

Each write is made in one transaction, so one that is refused leaves nothing behind. Starting and scoring are the
exception: the runner and the scoring pass write each row as it lands, so that a run or a score that dies leaves a log
to read, and they need the bench's connection in autocommit mode.

## What a person sees
- **Threads** they own or collaborate on, while they are live. A kind of thread is asked for by the word for it:
  configuration, each recipe part, tool, scorer, judge, expectation, appendix, expectation schema, canary set, model
  or engine.
- **Families** they own or collaborate on, while they are live. A family stands for its case: the one its current
  vignette makes alone, else the first that holds the vignette. A family without a case isn't shown.
- **Their own deleted threads**, listed apart and found by id, so that they can be read and restored. Nothing else
  finds them: not names, not lists, not what is run or scored against.
- **Their own runs**, while they are live. Being a collaborator on a run shows nothing.
- **The World's endpoints**, which are everyone's, and read from the World. The bench gives the engine an endpoint
  serves, once that engine is in the store.

### Finding things by name
A thread or a family is found by its name, matched whole first, since names may hold a slash, as
`plan (Qwen/Qwen3-8B-AWQ)` does; only when nothing has the whole name is it read as `OWNER/NAME`. Among those it
names, the person's own win, else the ones shared with them. Several raise `Ambiguous`, which asks for `OWNER/NAME`;
none raises `NotFound`.

A thread made per model or per language is found by its plain name too: `NAME (MODEL)`, `NAME (LANGUAGE)` or
`NAME (LANGUAGE, MODEL)`, the one the model an engine serves may use (src/chatddx/catalog/variants.py). Without an
engine, a name that only per-model threads have isn't found, and the error names them, so that an edge can say the
endpoint picks one. A name made in several languages is ambiguous.

### Finding things by id
By id, a thread, a family or a run is found only among what the person sees, and a thread only among the kinds its
word names. A run is also found by the start of its id, among their own, as a person at a prompt types it; an edge
that names things by id can take whole ids only, since a start could name another run tomorrow (agents/wip-api.md,
"Ids").

## What a person is scored against
A person is scored against their own expectation of a case, under the scorer's expectation schema. One shared with
them is there to read and to take, by forking it, and counts once they have. So nothing someone else shares, edits,
restores or hands over changes what a person is scored against, and a correction made upstream reaches them as a
proposal (see "Following an origin") rather than under them.

A person who only sees shared expectations has none. `chatddx init-data` gives its user forks of the archive's when
asked to (the giftbag, docs/curation.md), keeping any expectation of their own for a case and schema rather than
failing on the rule below; anyone else takes them.

### Taking
Taking an expectation forks it: a thread of the person's own, from the shared one's head. Forking changes no digest, so
what they are scored against is the shared expectation until either thread moves on, and a correction made to the
origin reaches them as a proposal. A person can take:
- **for many cases at once**, under one schema and in one transaction, an expectation for each case they have none of
  their own for, from any owner or one named. The cases left are named, each with why: theirs is kept, or several
  owners share one, or nobody does.
- **one thread**, an expectation shared with them, which, when they have their own of its case under its schema, is a
  conflict unless they say to replace theirs. Replacing deletes theirs and forks the shared one in one transaction.

Taking for many cases only adds, so it is safe to offer as one button and to repeat: taking again after more cases
were shared adds the new ones, nothing a person was scored against changes, and no run is left to score again.
Replacing can undo their own corrections, and leaves every run scored against what it replaced to score again, so it
is a choice made case by case. It deletes and forks rather than editing theirs onto the shared head, since an edit
would keep the origin they forked first, and proposals would keep coming from it.

What a person could take for a case are the live expectation threads of it under the schema that are shared with them
and not their own.

### One expectation per case and schema
A person owns at most one live expectation thread per case and expectation schema. The catalog refuses what would make
two: a second thread, an edit that moves another onto that case and schema, naming them the owner of another, or a
restore (src/chatddx/catalog/threads.py:check_expectation). The bench refuses the same before it writes, worded as the
person reads it.

The database doesn't repeat the rule (docs/catalog.md, "Concurrent writers"), so two writers at the same moment can
still leave a person two to choose from. Then nothing picks one, and each place says so:
- scoring refuses the run under that scorer, naming the threads;
- what is left to score keeps the scorer, so the run stays listed until one of the two goes;
- a variation's reach lists the case apart from those that have no expectation;
- the case's expectation under that schema says it has expectations to choose from.

## The variation being tried
A variation being tried is a configuration with recipe parts replaced (docs/catalog.md, "Configurations and
variations"): the configuration's head edit and recipe, the name the person called it by, and the parts replaced over
it, each by a chunk's digest, or by nothing for an optional part taken out, with the name it was set by. With nothing
replaced, it is the configuration's head itself. It is a plain value, not a catalog object: variations are "a
supported portal workflow, not an object in the code" (docs/chatddx.md), and an unsaved one is just a digest. An edge
holds it beside the endpoint it is to run at.

Looking at a variation writes nothing. What an unsaved skeleton was compiled from is stored when it is saved or
started, by the running code (docs/catalog.md, "Recipes").

Its label, `NAME+PART=CHUNK`, is a short title for it, where the catalog would give the long one of a variation nobody
saved (docs/catalog.md, "Titles"). Neither is stored.

For a variation, the bench gives:
- **its skeleton**: the stored head when nothing is replaced, else the varied recipe compiled, a skeleton nobody has
  saved;
- **the request it would send**, with placeholders for the slots, and for the model without an engine;
- **its lints**, as a trial on an engine: the pair's checks, over any one case since they read none, and with
  families, the languages of their cases too. An unsaved variation is linted in its recipe's language, since a
  skeleton's language otherwise comes from its stored compilations;
- **its reach**: for each view of each scorer the person sees, whether the variation's output offers what the view
  reads, and which of the given families have no expectation it picks something from, or several to choose from.

## Writes for the person
The bench writes, in the person's name: configurations, chunks, appendices, expectations, scorers, typed cases, what
is said about a thread, runs and scores. Tools, expectation schemas, engines, models and canary sets are developers'
and ops', written through data sets (docs/chatddx.md, "Requirements"), and a scoring is built when a run is scored
rather than written by hand.

What every write has in common:
- **One set of writes for every kind.** A thread is made new, forked from one the person sees, or edited when it is
  theirs, whatever its kind: the catalog's writes are generic over kinds, and what differs between kinds is what a
  component is, which its model checks. A configuration takes a variation where another kind takes a component.
- **An edit names the head it was made on**, configurations included, and is refused as `MovedOn` when the thread has
  moved on since, so that a change made on an older version doesn't undo what came after it unseen. Saving by name
  names the head it found. The catalog checks it while it holds the thread, so it holds with several writers too.
- **Nothing is written that is there already.** An edit that is its thread's head already writes nothing, and says
  so; saying what holds of a thread writes only what changes.
- **What was written comes back with its lints**, and no write refuses on one: an expectation whose data its schema
  refuses is written, and said so (docs/factors.md, "Lints"). Refusals are the components' own rules, the store's and
  the catalog's, and the few the bench adds, below.
- **Some refusals come before the write**, in the person's words, where the database or the catalog would refuse
  later in theirs: a component of another kind than the thread's, a second expectation of the person's own for a
  case and schema.

### Configurations
- **Forking** keeps a variation as a new configuration of the person's own, forked from the edit it varies.
- **Editing** keeps it as a new version of a configuration the person owns.
- **Saving** by name is one of the two: a new version of the person's own configuration of that name, else a fork.
  Several of their own by that name are refused.
- **Making one from a recipe** of the person's own, by the chunks' digests for each part, its purpose and its appendix
  layout: compiled by the running code and kept as a new configuration with no origin. Each part must be a stored
  chunk of that part, and the recipe must compile. Its language comes from its recipe, so none is given.

A configuration is kept with the compilation that makes it: for a variation with parts replaced, or a recipe, the one
the running code compiles; otherwise the configuration's own.

### Components
A person writes the kinds of chunk a recipe's parts take, appendices, expectations and scorers, each from its JSON as
the store gives it:
- **new**, as a thread of the person's own, with a name;
- **a fork** of a thread they see, from its head or from a component given in its place;
- **an edit** of a thread they own.

What a component refers to must be stored already, so a toolset can't bring a tool of its own.

### Languages
A text is written with its language when the person gives one, and only a text can have one. A language belongs to
the text, wherever it is held: it is kept on the digest, and the latest wins, so a person giving one to a text someone
else holds too would change it for them. So the bench writes one only where the text has none, and refuses one that
differs from what it has; the person writes another text, or leaves it. A fork that changes nothing keeps its
language, being the same digest.

The bench doesn't carry the previous version's language over by itself: an edge offers it, and the person keeps it or
changes it (docs/catalog.md, "Languages").

### Scorers
A scorer names scoring code the running chatddx ships, by its entry point and the version it pins, and the views the
person writes over it: each picks from an answer and from an expectation, and names a metric the code publishes, with
parameters only where the code publishes a schema for them. A scorer the running code could never score with is
refused as it is written: code it doesn't ship, at a version it doesn't ship, a metric it doesn't publish, or
parameters its schemas refuse. The scoring pass refuses it the same way. A view that can't pick anything from the
scorer's expectation schema is written, and said so.

It is a refusal rather than a lint because what the code ships is also a protection: a scorer names code to run, and
one written over the API names its own, so only code on the shipped list runs (src/chatddx/scorers/shipped.py,
src/chatddx/core/rig.py:entry).

A scorer pins a version of its code rather than the running chatddx, so a deploy changes no scorer unless it raises a
version. One that does leaves the scorers pinned to the earlier version refused until they move on: the archive's when
`init-data` runs again, a person's by following its origin, or by an edit.

What a scorer's views and resources are called belongs to the edit they are written with, by its writer. A fork of a
scorer as it is keeps its origin's labels unless given others, and renaming a view is a new edit of the same scorer, so
no score and no run left to score changes with it, and no one else's labels do. Labels on the digest would let anyone
who forks a scorer unchanged rename its views for everyone who sees it, the archive's included. A scorer edited
without labels has none, since its positions may have moved, unless it is the head's, which is then nothing new.

A scorer digest is called what the person's view calls it: the labels of the head that holds it, their own first, else
of the latest edit that held it in a thread they see. Following an origin keeps the labels of whichever side's views
the proposal keeps.

### Appendices and cases
A family stands for one case, the one its current vignette makes alone, else the first that holds it, and lists all
of its cases at its current vignette, that one first. What is run and scored is a case, so a run can name cases, each
one of a family's current ones.

An appendix is written like any other component, but always bound to the current vignette of a family the person
sees, and with its line endings made LF before it is digested, since browsers send CRLF: the bench does it for every
edge. The bench builds one from a family and a text. A case is built from a family and appendices the person sees, in
order, at its current vignette, and stored. Nothing is written in the catalog, since a case belongs to its family by
its vignette (docs/catalog.md, "Families and repairs"), and an appendix bound to another vignette is refused by the
case's own rule.

A new version of an appendix stores each case that held the old one at that vignette again, with the new one in its
place, so the new cases are there to pick, and says which replaced which. No expectation moves with them, since an
appendix can change the right answer (docs/factors.md, "Case"). Carrying one is a write of its own: the person's
expectation, edited onto another case of its family with the same data, as a clinician's word that it still holds
there.

A case left at an earlier vignette by a repair is offered a replacement (docs/catalog.md, "What has moved on"), which
the bench stores when asked. An appendix's edit replaces only the cases at its own vignette, since one at an earlier
vignette awaits that replacement instead.

### Typed cases
A case can be typed rather than fetched from a directory: the text is kept in the database, in a source of the
`database` kind (agents/wip-portal.md, "Typed cases"), under a new id and never changed, and its case and a family of
the person's own are written with it, all at once, named and in a language when they say so. It runs as any case: a
vignette is fetched from its source, a directory's file or a database source's text, wherever the bench, the runner
and the edges read one (src/chatddx/store/texts.py:fetch_vignette).

A text is held to a length, may not hold U+0000, which can't be stored, and a person to a number of texts a day, as
set in `chatddx.core.settings`; over the quota is `OverQuota`. A typed text never moves, so its family is adopted by
id alone, and the same text typed twice is two cases and two families (docs/catalog.md, "Families and repairs").

### What is said about a thread
Only its owner says what holds of a thread, as only they edit it: a collaborator may fork it, but not rename, share or
delete it. One write says what is to hold afterwards, any of: the name, or none so the title takes over; the
description, which is replaced but never taken away; the tags and the collaborators, each as the whole set, the
collaborators by login; and whether it is deleted. Only what changes what holds is written, all at once, so saying
the same again writes nothing. A form shows the whole thread and sends it back; a write per field would ask the edge to
tell what changed, and leave half a change when one of several fails.

A deleted thread is restored before anything else is said of it, and nothing else is said of one that stays deleted.
Restoring is held to the catalog's rules, so a second expectation of the person's own for a case and schema is
refused. A thread isn't shared with its owner, a name and a tag aren't empty, and a login that names nobody is
refused. Handing a thread over to another owner isn't offered.

### Following an origin
When a fork's origin has moved on, the catalog proposes the origin's head with the fork's changes on top
(docs/catalog.md, "Forks"). The bench shows what following would keep before it is followed: the base and the origin's
head, what the fork varies, the proposal, and the digest it comes to, a recipe compiled by the running code, so that an
edge can tell a fork it wouldn't change. Nothing is proposed when the origin hasn't moved on, or when the person no
longer sees it, deleted or unshared, since its head is then not theirs to read.

Following keeps the proposal as an edit of the person's own fork, based on the origin's head and naming the head
they saw. It does so even when the proposal holds what the fork's head holds already, since otherwise the fork would
keep being compared with its old base, and keep proposing. A configuration is kept with the compilation that makes it,
and a text takes a language as an edit does; a compiled configuration takes none. Changes that no longer fit the
origin's head are refused, saying so.

Any kind the person owns a fork of is followed, since a proposal holds only the origin's head and the fork's own
changes, which are stored already. That is how a correction to the archive's expectations reaches the person's taken
ones, and a scorer pinned again by a deploy reaches the person's fork of it.

## Runs and scores
- **Starting** runs a variation at an endpoint, on some cases with one seed, through the runner
  (agents/wip-runner.md). The runner's gate refuses what clearance forbids before anything is sent, and nothing is
  sent until the edge sends it, so the edge decides how a run is shown as it goes.
- **A person's runs** are their own, newest first, found by the start of their id, or by a component their trial is
  built on.
- **A run is described** as the repl's `run` and `batch` say it: the configuration, where it ran, its case or how many,
  and the seed.
- **A scorer applies** to a run when every one of its views reaches the run's output schema.
- **A run's scoring** under a scorer is built now, from the expectation each of its cases is scored against. Cases
  without one are left out, and a run whose cases have none has no scoring under that scorer.
- **Scoring** scores a finished run under each scorer that applies to it, or some of them, through the scoring pass.
  A scorer that can't score the run gives why instead, and the others score it all the same.
- **What is left to score** of a run is each scorer that applies, under which some of its cases have an expectation,
  and that has no whole score of the run under the scoring built now, so a changed expectation leaves the run to
  score again. A score is whole when it finished, scored every item under every view, and none of its judge calls was
  stopped, so a scoring that was stopped leaves the run to score too. What is left of the person's is each finished
  run with what it is left to be scored by.
- **Stopping a scoring**, as Ctrl-C does, finishes the score under way with what it has, and the scorers after it
  aren't scored.
- **A run's scores** are the latest under each scorer that scored it, each named by the thread the person sees holding
  that scorer, their own first.
- **Rendering again**: only a request's fingerprint is kept, so whether a run's first requests would be sent the same
  now is told by rendering them again from the trial and the vignette at its source.

## Errors
The bench's errors are told apart by their class, so that an edge can answer each its own way:

| Error | Is a | For |
| --- | --- | --- |
| `NotFound` | `LookupError` | what the person doesn't see, or the store doesn't hold |
| `Ambiguous` | `LookupError` | a name, an id's start or a case's expectations that give several |
| `Conflict` | `ValueError` | a write that would undo what the person has unless they say so: taking one thread when they have their own of its case under its schema |
| `MovedOn` | `ValueError`, the catalog's | an edit made on a head that isn't the head any more |
| `OverQuota` | `ValueError` | more of something than a day takes |
| any other `ValueError` | | what the bench refuses: an unknown part, a digest that isn't a stored chunk of its part, or a part that can't be taken out; a component that isn't one, or of a kind the person doesn't write; a scorer the code can't score with; taking an expectation of one's own; and the rest, each worded for what was wrong |

The messages are worded for a person, without the edge's terms; an edge adds its own hint where it has one, as the
repl does for a name its endpoint would pick a model for. The API answers `NotFound` with 404, `Ambiguous`, `Conflict`
and `MovedOn` with 409, `OverQuota` with 429, and the other refusals with 422 (agents/wip-api.md, "Errors").

## Tests
The tests start from the sample as `chatddx init-data` lands it from the sample World, with alice and her giftbag; bob
is added with nothing. The database is made once a session and copied for each test (`src/chatddx/conftest.py`,
`curated`). The variation and an item's outcome are tested without a database.

A person can only come to own two expectations of a case under one schema through two writers at once, so that is how
the tests make them: one restores the person's thread while the other starts a new one, each passing the catalog's
check before the other has written.

## Terms

| Term | Meaning |
| --- | --- |
| Bench | What one person sees and does, whatever the edge. |
| Edge | What a person reaches the bench through: the repl, the API, the portal to come. |
| Sees | Owns or collaborates on, while it is live. |
| Own | Owned by the person, while it is live. |
| Word | What a kind of thread is asked for by: configuration, a recipe part, engine and the rest. |
| Variation being tried | A configuration with recipe parts replaced over it, or none, that nobody has saved. |
| Label | Of a variation: its short title, `NAME+PART=CHUNK`, not stored. Of a scorer: what an edit calls one of its views or resources. |
| Reach | Of a scorer's view: whether a variation's output offers what it reads, and which cases have an expectation it picks from. |
| Taking | Forking a thread shared with the person to make it their own, as an expectation must be to count. |
| To choose from | A case with several expectations of the person's own under one schema, which nothing picks between. |
| Carrying | Editing an expectation onto another case of its family, with the same data. |
| Saying | Writing what holds of a thread: its name, description, tags, collaborators, and whether it is deleted. |
| Following | Keeping the catalog's proposal as an edit of the person's fork, based on its origin's head. |
| Typed case | A case whose vignette is a text the person typed, kept in a database source. |
| Left to score | Of a finished run: a scorer that applies and has no score of it under the scoring built now. |
| Cell | The repl's word for a variation being tried together with an endpoint. |

## Outstanding
What is still open of the bench and of its edges, the API's included (agents/wip-api.md). It doesn't move to `docs/`.
The plans they were built from, with the options weighed for each decision and the survey of the old project, are
`agents/wip-bench.md` at d5ebf52 and `agents/wip-api.md` at 100a078.

### Start with this
0. **Go through open items, reiterate and confirm design decisions.**
1. **Scoring in the API**, which has no requests of its own yet: a run is scored as it finishes, and its scores come
   with it (agents/wip-api.md, "Scoring"). Still to do:
   - a run's latest score under each scorer, on its own (`Bench.scores_of`);
   - scoring a run now, under all its scorers or some (`Bench.score`), one run at a time;
   - the person's finished runs, each with the scorers it is left to be scored by (`Bench.outstanding`, as
     `runs?unscored=true`), a run with a case that has expectations to choose from among them, as
     `Bench.outstanding` lists it;
   - where a score's detail and the scoring's findings show, if anywhere: both can quote the answer, so a place for
     them is case-derived, and the ledger marks the scoring's findings otherwise (see "Surprises").
2. **Adopting the docs**: this file and `agents/wip-bench-api.md`, as `docs/bench.md` and `docs/bench-api.md`, and
   `agents/wip-api.md` and `agents/wip-api-api.md`, as `docs/api.md` and `docs/api-api.md`.
3. **A low-level manual for the bench**, made from `agents/wip-authoring.md`.
4. **Judges** are the one write for authoring left (agents/wip-authoring.md, S6, phase 9), waiting for the scoring
   pass to send judge requests. The portal's authoring and swift wait on the rest, which is built.
5. **Takes** the bench and the API are built on still wait for a word (below).

### Open
The bench:
- **Z1**: the map from roles to the kinds each role sees goes in `identity` once the portal's views give it meaning
  (agents/wip-identity.md, "Open"). `sees` then takes the person's roles and the kind.
- **An execution for `Bench.start`**, which passes none, so a run gets `Execution()`'s; the worker needs it
  (agents/wip-worker.md, "Below the worker").
- **A person's runs are all read**, and paged afterwards, in the API too (`Bench.runs`). Page in the store once that
  is slow.
- **Two saves of one name at once** can both create a configuration, in the repl's `save` as in the API's forks
  (`docs/catalog.md`, "Concurrent writers").
- **`Catalog.expectation_for`**, for one case, has callers in tests only.
- **What the old bench had and this one doesn't**: what a run left unheeded (`outcome.py:unheeded`;
  agents/wip-runner.md, "Afterwards"); a batch's plan, crossing variations into one (agents/wip-batch.md); and what holds a configuration, the portal's
  (agents/wip-portal.md), whose part for the repl `Bench.reaching` and `Bench.scored_by` cover.

Signing in, in the API:
- **A cookie over plain HTTP** isn't kept: a `Secure`, `__Host-` cookie needs HTTPS, or `localhost`.
- **`Origin` against `Host`.** A proxy that rewrites `Host` would fail the `Origin` check for a browser that sends no
  `Sec-Fetch-Site`, though today's browsers all send it. If it bites: the public origin as a setting.
- **No limit on login attempts**, and **no personal tokens** for scripts that run longer than a session (a table and a
  migration).
- **Keycloak.** Once it is in front, a proxy authenticates and hands over the login, which maps to `person.login`,
  and signing in is skipped (agents/wip-identity.md).
- **Roles aren't checked**; that waits for the portal.

Serving the API:
- **A connection per request**, opened and closed each time; a pool (`psycopg_pool`) when that costs. A run answered
  as JSON holds two for as long as it lasts: the request's and its own.

Variations, in the API:
- **A part given twice in a query**: the last one counts.
- **Variants.** A client finds `plan (en, Qwen/Qwen3-8B-AWQ)` by its full name; agents/wip-variants.md's option B
  would let it filter by model and language instead.
- **An unsaved variation's runs are titled by their whole recipe**, in the API as in the repl (docs/catalog.md, "A
  variation nobody saved has a long title").

Runs, in the API:
- **Reaching a chunk** found no run, since a compiled skeleton holds what the chunk sets rather than a reference to
  it. `Bench.reaching` reaches through the compilations now, which refer to both, and `Bench.scored_by` finds the runs
  scored with what a scoring holds: an expectation, the expectation schema, a judge.
- **A quiet stream sends nothing**, as while it waits for a slow first token, and a proxy's read timeout would cut
  it. A comment line now and then would keep it open.
- **`Accept` is read by media type alone**, so `text/event-stream;q=0` still asks for a stream.
- **A run outlives a server that stops**, which waits for its requests. A killed one leaves the run unfinished, as
  resuming isn't built; requests that last as long as a run are agents/wip-worker.md's ("Why").
- **Judges**: judged views show as "not yet", as in the repl.

# Bench

A candidate for `docs/bench.md`. Its reference is `agents/wip-bench-api.md`, a candidate for `docs/bench-api.md`;
below, those two names mean these two files until they move. What is still open is in "Outstanding", at the end, which
stays behind when they do. The plan this was rewritten from, with its phases, the options weighed for each decision
and the survey of the old bench, is `agents/wip-bench.md` at d5ebf52. What was decided after it, what a person is
scored against, is described here.

The bench is what one person sees and does, whatever the edge: the threads, families and runs they see, the World's
endpoints, the variation they are trying, and what is written on their behalf. Its edges are the repl
(agents/wip-repl.md) and the API (agents/wip-api.md), with the portal to come (agents/wip-portal.md). It sits over the
store, the catalog, the World, the facts, the runner and the scoring pass, and holds no SQL of its own.

This document describes what the bench does and why it is shaped like it is. Names, signatures and errors are in
docs/bench-api.md.

## A person-scoped view
What depends on who is asking goes through the bench; what doesn't may be read straight from the store, the World and
the facts. An edge asks the bench which runs are the person's, and which thread a name means to them, but reads a
component by its digest, or an endpoint's limits, from where they are kept.

The bench isn't a facade, and nothing checks that an edge goes through it. What it is for is that each rule about a
person has one place, so that the edges don't copy it: in the old chatddx, what a person may read and what a name
means to them were written again in the portal, the API, the repl and the bench.

A bench is made for one person and one connection, and lasts as long as its caller: a request in the API, a process in
the repl. It caches logins and the model each engine serves for that long.

What the bench shows decides what is relevant to show a person, not who may read what (agents/wip-identity.md,
"Authorization"). Protection comes from clearance, which the runner's gate enforces (src/chatddx/runner/gate.py), and
from the database's grants.

## Who decides what
Three packages hold rules about a person, each its own part of them:
- **Identity** holds the rules, as pure functions with no store access: who sees a subject, its owner and its
  collaborators (`sees`), and that a person's own comes before what is shared with them (`preferred`). The map from
  roles to the kinds each role sees is to go beside them (see "Outstanding", "Z1").
- **The catalog** applies them to its own rows, and adds that only live subjects count: `About.shows` is live and
  seen, `About.owned_by` live and owned. It answers what docs/catalog.md says it answers, such as the threads and
  families a person sees and the expectation they are scored against, and refuses the writes its rules forbid.
- **The bench** applies them to everything else: names, runs, the variation being tried, the writes made for the
  person, and the errors an edge tells apart.

## What a person sees
- **Threads and families** they own or collaborate on, while they are live. A kind of thread is asked for by the word
  for it: configuration, each recipe part, tool, scorer, judge, expectation schema, canary set, model or engine. A
  family stands for its case: the one its current vignette makes alone, else the first that holds the vignette. A
  family without a case isn't shown.
- **Their own runs**, while they are live. Being a collaborator on a run shows nothing.
- **The World's endpoints** are everyone's, and read from the World. The bench gives the engine an endpoint serves,
  once that engine is in the store.

### Finding things by name
A thread or a family is found by its name, matched whole first, since names may hold a slash, as
`plan (Qwen/Qwen3-8B-AWQ)` does; only when nothing has the whole name is it read as `OWNER/NAME`. Among those it
names, the person's own win, else the ones shared with them. Several raise `Ambiguous`, which asks for `OWNER/NAME`;
none raises `NotFound`.

A thread made per model or per language is found by its plain name too: `NAME (MODEL)`, `NAME (LANGUAGE)` or
`NAME (LANGUAGE, MODEL)`, the one the model an engine serves may use (src/chatddx/catalog/variants.py). Without an
engine, a name that only per-model threads have isn't found, and the error names them, so that an edge can say the
endpoint picks one. A name made in several languages is ambiguous.

By id, a thread, a family or a run is found only among what the person sees. A run is also found by the start of its
id, among their own.

## What a person is scored against
A person is scored against their own expectation of a case, under the scorer's expectation schema. One shared with
them is there to read and to take, by forking it, and counts once they have. So nothing someone else shares, edits,
restores or hands over changes what a person is scored against, and a correction made upstream reaches them as a
proposal ("What has moved on", docs/catalog.md) rather than under them.

A person who only sees shared expectations has none. `chatddx init-data` gives its user forks of the archive's when
asked to (the giftbag, docs/curation.md), keeping any expectation of their own for a case and schema rather than
failing on the rule below; otherwise they take them.

### Taking
Taking an expectation forks it: a thread of the person's own, from the shared one's head. Forking changes no digest, so
what they are scored against is the shared expectation until either thread moves on, and a correction made to the
origin reaches them as a proposal. A person can take:
- **for many cases at once**, under one schema and in one transaction, an expectation for each case they have none of
  their own for, from any owner or one named. The cases left are named, each with why: theirs is kept, or several
  owners share one, or nobody does. Nothing they have is changed, so taking again only adds what was shared since.
- **one thread**, an expectation shared with them, which, when they have their own of its case under its schema, is a
  conflict unless they say to replace theirs. Replacing deletes theirs and forks the shared one in one transaction.

What a person could take for a case are the live expectation threads of it under the schema that are shared with them
and not their own.

A person owns at most one live expectation thread per case and expectation schema. The catalog refuses what would make
two: a second thread, an edit that moves another onto that case and schema, naming them the owner of another, or a
restore (src/chatddx/catalog/threads.py:check_expectation). The database doesn't repeat the rule, so two writers at
the same moment can still leave a person two to choose from. Then nothing picks one, and each place says so:
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
The bench writes configurations, chunks, expectations, runs and scores for the person, and nothing else:
- **Forking** keeps a variation as a new configuration of the person's own, forked from the edit it varies.
- **Editing** keeps it as a new version of a configuration the person owns. Nothing is written when it is the head
  already.
- **Saving** by name is one of the two: a new version of the person's own configuration of that name, else a fork.
  Several of their own by that name are refused.
- **Writing a component**, a chunk or an expectation, from its JSON as the store gives it: new, as a thread of the
  person's own with a name; a fork of a thread they see, from its head or from a component given in its place; or an
  edit of a thread they own (see "Components").
- **Starting** runs the variation at an endpoint, on some cases with one seed, through the runner
  (agents/wip-runner.md). Nothing is sent until the edge sends it.
- **Scoring** scores a finished run under each scorer that applies to it, or some of them, as each scoring would be
  built now, through the scoring pass.
- **Taking** forks expectations shared with the person, for many cases or one thread (see "Taking").

An unsaved skeleton has what it was compiled from stored, by the running code, when it is saved or started
(docs/catalog.md, "Recipes"). The runner and the scoring pass write each row as it lands, so starting and scoring need
the bench's connection in autocommit mode.

Every edit names the head the person made it on, configurations included, and is refused as `MovedOn` when the
thread has moved on since, so that a change made on an older version doesn't undo what came after it unseen. Saving by
name names the head it found. The catalog checks it while it holds the thread, so it holds with several writers too.

Appendices, cases, families, scorers and judges aren't written by the bench yet (see "Outstanding").

### Components
A person writes the kinds of chunk a recipe's parts take, and expectations. A configuration is written as a variation,
and the other kinds come with their own writes or are written by curation alone: a scorer, for one, names code to run,
which only a published list will hold (agents/wip-authoring.md, S1). A component of another kind than the thread's is
refused before the database would refuse it, and so is a second expectation of the person's own for a case and schema,
worded as the person reads it.

Each write gives what it kept and what the lints say of the component: an expectation whose data its schema refuses is
written, and said so. The person's referenced components must be stored already, so a toolset can't bring a tool of
its own.

A text is written with its language, when the person gives one, and only a text can have one. A language belongs to
the text, wherever it is held, so the bench writes one only where the text has none, and refuses one that differs from
what it has; a fork that changes nothing keeps its language.

## Runs and scores
- A person's runs are their own, newest first, found by the start of their id, or by a component their trial is built
  on.
- A run is described as the repl's `run` and `batch` say it: the configuration, where it ran, its case or how many,
  and the seed.
- A scorer applies to a run when every one of its views reaches the run's output schema.
- A run's scoring under a scorer is built now, from the expectation each of its cases is scored against. Cases
  without one are left out, and a run whose cases have none has no scoring.
- What is left to score of a run is each scorer that applies and has no score of it under the scoring built now, so a
  changed expectation leaves the run to score again. What is left of the person's is each finished run with what it is
  left to be scored by.
- A run's scores are the latest under each scorer that scored it, each named by the thread the person sees holding
  that scorer, their own first.
- Only a request's fingerprint is kept, so whether a run's first requests would be sent the same now is told by
  rendering them again from the trial and the vignette at its source.

## Errors
The bench's errors are `LookupError`s an edge can tell apart: `NotFound`, for what the person doesn't see or the store
doesn't hold, and `Ambiguous`, for a name, an id's start or a case's expectations that give several. A variation the
bench refuses is a `ValueError`: an unknown part, a digest that isn't a stored chunk of its part, a part that can't be
taken out. So are a component that isn't one, or of a kind the person doesn't write, and taking an expectation of
one's own. `Conflict`, a `ValueError` too, is a write that would undo what the person has unless they say so: taking
one thread when they have their own of its case under its schema. `MovedOn`, the catalog's and a `ValueError`, is an
edit made on a head that isn't the head any more. The messages are worded for a person, without the edge's terms; an
edge adds its own hint where it has one, as the repl does for a name its endpoint would pick a model for. The API
answers `NotFound` with 404, `Ambiguous`, `Conflict` and `MovedOn` with 409, and the other refusals with 422
(agents/wip-api.md, "Errors").

## "Cell"
"Cell" is the repl's word for a variation being tried together with an endpoint (agents/wip-repl.md). The bench and
everything below it speak of the variation and the endpoint, and nothing stored is one: a run's title, if one is ever
stored, is a title, not a label in the repl's notation.

The word is kept to the repl because every edge builds on the bench, and the docs speak of configurations, variations,
endpoints and trials: a fourth word for two of them would tell the portal's users nothing, and its everyday meanings
sit close, from a table's cells to the sample's "basal cell carcinoma". `src/chatddx/repl/test/test_vocabulary.py`
keeps it out of the code outside `src/chatddx/repl/`; it reads code only, since clinical data says "cell".

## Tests
The tests start from the sample as `chatddx init-data` lands it from the sample World, with alice and her giftbag; bob
is added with nothing. The database is made once a session and copied for each test (`src/chatddx/conftest.py`,
`curated`). The variation and the outcome are tested without a database.

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
| Label | A variation's short title, `NAME+PART=CHUNK`. Not stored. |
| Reach | Of a scorer's view: whether a variation's output offers what it reads, and which cases have an expectation it picks from. |
| Taking | Forking a thread shared with the person to make it their own, as an expectation must be to count. |
| To choose from | A case with several expectations of the person's own under one schema, which nothing picks between. |
| Left to score | Of a finished run: a scorer that applies and has no score of it under the scoring built now. |
| Cell | The repl's word for a variation being tried together with an endpoint. |

## Outstanding
What is still open. It doesn't move to `docs/`.

### Start with this
1. **Adopting the docs.** This file and `agents/wip-bench-api.md`, as `docs/bench.md` and `docs/bench-api.md`.
2. **Writes for authoring** (below), planned in `agents/wip-authoring.md`. The portal's authoring and swift wait on
   them. Taking expectations and writing chunks and expectations, its phases 1 and 2, are built.

### Writes for authoring
Planned in `agents/wip-authoring.md`: chunks, recipes, appendices and the cases that order them, expectations, what is
said about a thread, and following an origin. Taking expectations is built ("Taking"), and the giftbag keeps a
person's own; so are writing chunks and expectations, and an edit's head ("Writes for the person").

### Takes
A take is the agent's recommendation, built on but not decided.
- **S5. A bench lasts one session.** Its caches of logins and models make it last as long as a request or a repl. A
  long-lived worker would build one per run, or per owner, rather than keep one (agents/wip-worker.md). Nothing to
  build.
- **The database doesn't repeat the expectation rule.** It reads the latest owner, deletion and head of every
  expectation thread of a case, as the rule that no two families share a vignette reads bindings, and that one isn't
  repeated either (`docs/catalog.md`, "Concurrent writers"). A trigger would need a lock per owner to hold. The
  refusals in "What a person is scored against" cover the race.
- **No pick for every "several".** Where none, one or several are told apart, a `match` says what each means
  (`src/chatddx/catalog/threads.py:picked`, `Bench._named`), and "several" isn't the same there: two threads of one
  name are two things to refer to, while two threads of one head are one answer.
- **Curation keeps its own check.** `_Init.put` finds the archive's one expectation thread for a case to edit, in any
  schema and deleted or not. That is how it recognises its thread, which the catalog's rule doesn't replace. Its other
  owner checks that count deleted subjects too, the giftbag's and `src/chatddx/curation/repair.py`'s, recognise the
  archive's records the same way, rather than decide what a person sees.
- **`About.owned_by` compares owners itself**, beside `sees` in `identity`. It is one comparison, so a function in
  `identity` for it would only add a name.
- **A facade can still come later.** A bench every edge goes through, checked by an import test, would give one API
  for every edge, but most of it would pass calls through, and the ops commands would need an exemption. This bench is
  the person-scoped half of one. "Rig", the name once proposed for it, is the glossary's name for the whole of chatddx
  (`docs/chatddx.md`) and a field of every `RunStarted` and `ScoreStarted`.

### Open
- **Z1**: the map from roles to the kinds each role sees goes in `identity` once the portal's views give it meaning
  (agents/wip-identity.md, "Open"). `sees` then takes the person's roles and the kind.
- **An execution for `Bench.start`**, which passes none, so a run gets `Execution()`'s; the worker needs it
  (agents/wip-worker.md, "Below the worker").
- **A person's runs are all read**, and paged afterwards (agents/wip-api.md, "Open").
- **Two saves of one name at once** can both create a configuration (`docs/catalog.md`, "Concurrent writers";
  agents/wip-api.md, "Open").
- **`Catalog.expectation_for`**, for one case, has callers in tests only.
- **What the old bench had and this one doesn't**: what a run left unheeded (`outcome.py:unheeded`;
  agents/wip-runner.md, "Afterwards"); an endpoint's secret, refused for now (agents/wip-repl.md, "Left out"); a
  batch's plan, crossing variations into one (agents/wip-batch.md); and what holds a configuration, the portal's
  (agents/wip-portal.md), whose part for the repl `Bench.reaching` and `Bench.scored_by` cover.

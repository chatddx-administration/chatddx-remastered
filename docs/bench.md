# Bench

The bench is what one person sees and does, whatever the edge they reach it through: the threads, families and runs
they see, the World's endpoints, the variation they are trying, and what is written in their name. Its edges are the
repl (docs/repl.md), the API (docs/api.md) and the portal to come (agents/wip-portal.md). This document
describes what the bench does and why it is shaped like it is. Names, signatures and errors are in docs/bench-api.md.

The bench builds on the store, the catalog, the World, the facts, the runner and the scoring pass, and holds no SQL of
its own.

`bench` is the *operational* layer of person-scoped functionality. When adding functionality, express rules as pure
functions in `identity` and utilize them here.

## What a bench is not
- A facade, and nothing checks that an edge goes through it.
- Authorization, what the bench shows is what is relevant to show a person, not who may read what.

## How the bench works

### One person, one connection
A connection lasts as long as its caller, and caches logins and the model each engine serves for that long. The facts
about models aren't cached: they are read from the store each time they are asked for, so that a fact corrected while
a connection lasts is used at once.

Each write is made in one transaction, so one that is refused leaves nothing behind. Starting and scoring are the
exception: the runner and the scoring pass write each row as it lands, so that a run or a score that dies leaves a log
to read, and they need the bench's connection in autocommit mode.

## What a person sees
- **Threads** they own or collaborate on, while they are live. A kind of thread is asked for by the word for it:
  configuration, each recipe part, the engine among them, tool, scorer, judge, expectation, appendix, expectation
  schema, canary set, model or facts.
- **Families** they own or collaborate on, while they are live. A family stands for its case: the one its current
  vignette makes alone, else the first that holds the vignette. A family without a case isn't shown.
- **Their own deleted threads**, listed apart and found by id, so that they can be read and restored. Nothing else
  finds them: not names, not lists, not what is run or scored against.
- **Their own runs**, while they are live. Being a collaborator on a run shows nothing.
- **The World's endpoints**, which are everyone's, and read from the World. The bench gives the engine an endpoint
  serves, once that engine is in the store.

### Finding things by name
A thread or a family is found by its name, matched whole first, since names may hold a slash, as the facts
`Qwen/Qwen3-8B-AWQ` do; only when nothing has the whole name is it read as `OWNER/NAME`. Among those it names, the
person's own win, else the ones shared with them. Several raise `Ambiguous`, which asks for `OWNER/NAME`; none raises
`NotFound`.

A thread made per language is found by its plain name too, `NAME (LANGUAGE)` (src/chatddx/catalog/variants.py), when
it is made in one language alone. A name made in several languages is ambiguous, unless it names one, as
`NAME LANGUAGE` or `NAME (LANGUAGE)`.

### Finding things by id
By id, a thread, a family or a run is found only among what the person sees, and a thread only among the kinds its
word names. A run is also found by the start of its id, among their own, as a person at a prompt types it; an edge
that names things by id can take whole ids only, since a start could name another run tomorrow (docs/api.md,
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
  are shared with them to choose from, or none is.
- **one thread**, an expectation shared with them, which, when they have their own of its case under its schema, is a
  conflict unless they say to replace theirs. Replacing deletes theirs and forks the shared one in one transaction.

Replacing is a delete and a fork rather than an edit of theirs onto the shared head, since their thread would keep the
origin it was forked from, and keep proposing from it. Taking for many cases never replaces: it would reset every
case to the shared heads, the person's own corrections included, and leave every run scored against what it replaced
to score again.

Taking for many cases only adds, so it is safe to offer as one button and to repeat: taking again after more cases
were shared adds the new ones, and nothing a person was scored against changes. A run that holds a newly taken case
is left to score again, since its scoring now holds that case too.

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
Variation is a configuration with recipe parts replaced (docs/catalog.md, "Configurations and variations"):
a configuration's edit's recipe, the name the person called it by, and the parts replaced over it with the name it was
set by. With nothing replaced, it is the configuration itself.

It is a plain value and an unsaved one is just a digest. It runs at the endpoint serving its engine (see "The engine"),
so an edge needs an endpoint beside it only for a hand-written configuration, which has no engine part, or an engine
several endpoints serve.

A variation replaces the recipe's ten parts, its nine chunks and its engine, and nothing else. The engine can't be
taken out. A configuration's purpose and appendix layout are set when it is made from a recipe (see
"Configurations"): the purpose for good, since a judge configuration is no use where a run's is wanted, and the
appendix layout until someone wants to vary it, when it becomes a part.

Looking at a variation writes nothing. What an unsaved skeleton was compiled from, its recipe and the facts about its
engine's model, is stored when it is saved or started, by the running code (docs/catalog.md, "Recipes").

Its label, `NAME+PART=CHUNK`, is a short title for it, where the catalog would give the long one of a variation nobody
saved (docs/catalog.md, "Titles"). Neither is stored.

For a variation, the bench gives:
- **its skeleton**: the stored edit it varies when nothing is replaced, the head unless an earlier edit was named,
  else the varied recipe compiled against the facts about its engine's model as they are stored now, a skeleton nobody
  has saved;
- **the request it would send**, with placeholders for the slots, and for the model without an engine;
- **where its intents landed**: for a reasoning level and a recommended sampling, the level the engine's model is
  asked for, and why, when the facts land it on its nearest; read from the facts its compilation was compiled against
  when nothing is replaced;
- **its lints**, as a trial on an engine: the pair's checks, over any one case since they read none, and with
  families, the languages of their cases too. An unsaved variation is linted in its recipe's language, since a
  skeleton's language otherwise comes from its stored compilations;
- **its reach**: for each view of each scorer the person sees, whether the variation's output offers what the view
  reads, and which of the given families have no expectation it picks something from, or several to choose from.

A judge configuration, one whose purpose is `judge`, is looked at as the judge it would make on the engine: its lints
are the judge's, it reads no case, and it has no reach, as no scorer reads what a judge answers. It isn't run on cases:
starting it is refused. An edge lists configurations by purpose (`Bench.purposed`), since a judge configuration is no
use where a run's is wanted.

An edge also lists configurations by what they answer (`Bench.answering`): the title of their answer's JSON Schema, as
a page that shows management plans offers only the configurations that answer one.

### The engine
The engine is a part like any other: swapping it keeps every other pick, and what depends on the model is worked out
again for the new engine's. A reasoning level and a recommended sampling are intents rather than settings: compiling
resolves them with the facts about the engine's model as they are stored then (docs/facts.md), lands each level where
the facts say, on its nearest when the model can't be asked for it, and refuses what they refuse, and any intent on a
model they don't know. So a variation is refused for its engine as it is looked at, before anything runs.

A run goes to the endpoint serving its variation's engine. An endpoint named must serve that engine, and one that
serves another is refused before the gate would refuse it. An engine no endpoint serves is refused, and so is one
several serve, unless one of them is named (see "Outstanding"). A hand-written configuration has no engine part, and
runs at the endpoint named.

## Writes for the person
The bench writes, in the person's name: configurations, chunks, appendices, expectations, scorers, judges, typed
cases, what is said about a thread, runs and scores. Tools, expectation schemas, engines, models, the facts about
models and canary sets are developers' and ops', written through data sets and facts files (docs/chatddx.md,
"Requirements"; docs/facts.md), and a scoring is built when a run is scored rather than written by hand.

What every write has in common:
- **One set of writes for every kind.** A thread is made new, forked from one the person sees, or edited when it is
  theirs, whatever its kind: the catalog's writes are generic over kinds, and what differs between kinds is what a
  component is, which its model checks. A configuration takes a variation where another kind takes a component.
- **An edit names the head it was made on**, configurations included, and is refused as `MovedOn` when the thread has
  moved on since, so that a change made on an older version doesn't undo what came after it unseen. Saving by name
  names the head it found. The catalog checks it while it holds the thread, so it holds with several writers too.
- **Nothing is written that is there already.** An edit that is its thread's head already writes nothing, and says
  so; for a configuration, a head with the same recipe (docs/catalog.md, "Recipes"). Saying what holds of a thread
  writes only what changes.
- **What was written comes back with its lints**, and no write refuses on one: an expectation whose data its schema
  refuses is written, and said so (docs/factors.md, "Lints"). A component does, whether new, forked, edited, followed
  or carried, and so does a configuration made from a recipe or followed. A variation saved, forked or edited comes
  back as what was saved, and an edge lints its skeleton itself (`Bench.linted`), as the API does. Taking, saying and
  and building cases give back what they made. Refusals are the components' own rules, the store's and the catalog's,
  and the few the bench adds, below.
- **Some refusals come before the write**, in the person's words, where the database or the catalog would refuse
  later in theirs: a component of another kind than the thread's, a second expectation of the person's own for a
  case and schema.

### Configurations
- **Forking** keeps a variation as a new configuration of the person's own, forked from the edit it varies.
- **Editing** keeps it as a new version of a configuration the person owns.
- **Saving** by name is one of the two: a new version of the person's own configuration of that name, else a fork.
  Several of their own by that name are refused.
- **Making one from a recipe** of the person's own, by the chunks' digests for each part and an engine's, its purpose
  and its appendix layout: compiled by the running code against the facts about the engine's model, and kept as a new
  configuration with no origin. Each part must be a stored chunk of that part, the engine a stored engine, and the
  recipe must compile: an intent the facts refuse doesn't, nor one on a model they don't know. Its language comes
  from its recipe, so none is given.

A configuration is kept with the compilation that makes it: for a variation with parts replaced, or a recipe, the one
the running code compiles; otherwise the configuration's own.

### Components
A person writes the kinds of chunk a recipe's parts take, appendices, expectations, scorers and judges, each from its
JSON as the store gives it:
- **new**, as a thread of the person's own, with a name;
- **a fork** of a thread they see, from its head or from a component given in its place;
- **an edit** of a thread they own.

What a component refers to must be stored already, so a toolset can't bring a tool of its own, and a judge is written
over a judge configuration already kept, which its own rule holds it to (docs/factors.md, "Judge").

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
src/chatddx/rig.py:entry).

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
of its cases at its current vignette, that one first. What is run and scored is a case, so a run names cases rather
than families. The bench starts a run on any stored cases; the edges offer only the current ones of the families the
person sees.

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
set in `chatddx.settings`; over the quota is `OverQuota`. A typed text never moves, so its family is adopted by
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
head, what the fork varies, the proposal, and the digest it comes to, a recipe compiled by the running code against
the facts as they are stored now, so that an edge can tell a fork it wouldn't change. Nothing is proposed when the
origin hasn't moved on, or when the person no longer sees it, deleted or unshared, since its head is then not theirs
to read.

Following keeps the proposal as an edit of the person's own fork, based on the origin's head and naming the head
they saw. It does so even when the proposal holds what the fork's head holds already, since otherwise the fork would
keep being compared with its old base, and keep proposing. A configuration is kept with the compilation that makes it,
and a text takes a language as an edit does; a compiled configuration takes none. Changes that no longer fit the
origin's head are refused, saying so.

Any kind the person owns a fork of is followed, since a proposal holds only the origin's head and the fork's own
changes, which are stored already. That is how a correction to the archive's expectations reaches the person's taken
ones, and a scorer pinned again by a deploy reaches the person's fork of it.

```
AGENT: add
Following corrected facts (`Bench.corrected`, `Bench.follow_facts`). A section before this heading.
---
### Following its facts
A configuration is behind its facts when the facts about its engine's model were corrected where they change what it
sends (docs/catalog.md, "What has moved on"). The bench shows what following them would keep, to anyone who sees the
configuration: the model, the facts it was compiled against and the facts thread's head that corrects them, and the
skeleton its recipe compiles to against them with the running code, or why the corrected facts refuse what it asks.

Following them keeps its recipe, compiled against the facts as they are stored now, as an edit of the person's own
configuration, naming the head they saw; the recipe, and so what a fork varies, doesn't change. Facts that now
refuse what it asks are said rather than followed, so that a part set in its place mends it first. A configuration
with nothing behind has nothing to follow, and only its owner follows it; the archive's follow when init-data loads
the corrected facts.

Following an origin compiles against the facts as they are stored then, so a fork following its origin follows its
facts too.
```
## Runs and scores
- **Starting** runs a variation at the endpoint serving its engine, or the one named (see "The engine"), on some
  cases with some seeds, through the runner (docs/runner.md), under an execution. As it starts, the run is named by
  the variation's label and says what it varied: the edit it was built on and the parts replaced over it, its engine
  among them (docs/catalog.md, "What a run ran"). Running again keeps a run's cleanup, execution, canary set, name
  and what it varied under new seeds.
- **Resuming** a run of the person's own that isn't finished sends what its log lacks (docs/runner.md, "Resuming").
- **A person's runs** are their own, newest first, found by the start of their id, or by a component their trial is
  built on.
- **A run is described** as the repl's `run` and `run tag` say it: the run's name, else the configuration, where it
  ran, its case or how many, and the seed.
- **A scorer applies** to a run when the run's output offers what each of its views reads, a view of the whole answer
  only a text answer, and the World lets each of its judges run (docs/runner.md, "What applies to a run").
- **A run's scoring** under a scorer is built now, from the expectation each of its cases is scored against. Cases
  without one are left out, and a run whose cases have none has no scoring under that scorer.
- **Scoring** scores a finished run under each scorer that applies to it, or some of them, through the scoring pass.
  A scorer that can't score the run gives why instead, and the others score it all the same. A judged view's calls go
  to the one endpoint serving its judge's engine, as the bench names none (docs/runner.md, "Judges"). The scoring
  pass's events, each item scored and each judge call, go to the edge as they come, when it asks for them, after a
  word that each scorer's score has started. Another thread can halt it, as a second Ctrl-C does in the repl.
- **What is left to score** of a run is each scorer that applies, under which some of its cases have an expectation,
  and that has no whole score of the run under the scoring built now, so a changed expectation leaves the run to
  score again. A score is whole when it finished, scored every item under every view, and none of its judge calls was
  stopped, so a scoring that was stopped leaves the run to score too. What is left of the person's is each finished
  run with what it is left to be scored by.
- **Stopping a scoring**, as Ctrl-C does, finishes the score under way with what it has, and the scorers after it
  aren't scored.
- **A run's scores** are the latest under each scorer that scored it, each named by the thread the person sees holding
  that scorer, their own first; or every score of the run, newest first; or one by its id.
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
| `OverQuota` | `ValueError` | more of something than a day takes, or a run of more items than one takes |
| any other `ValueError` | | what the bench refuses: an unknown part, a digest that isn't a stored chunk of its part or a stored engine, or a part that can't be taken out, the engine among them; an endpoint that serves another engine than the variation's, and an engine no endpoint, or several, serve; an intent the facts about the engine's model refuse, or a model they don't know; a component that isn't one, or of a kind the person doesn't write; a scorer the code can't score with; taking an expectation of one's own; and the rest, each worded for what was wrong |

The messages are worded for a person, without the edge's terms; an edge adds its own hint where it has one. The API
answers `NotFound` with 404, `Ambiguous`, `Conflict` and `MovedOn` with 409, `OverQuota` with 429, and the other
refusals with 422 (docs/api.md, "Errors").

## Tests
The tests start from the test World (`worlds/test`; docs/inventory.md, "Worlds") as `chatddx init-data` lands it, with
alice and her giftbag; bob is added with nothing. The database is made once a session and copied for each test
(`src/chatddx/conftest.py`, `curated`). The variation and an item's outcome are tested without a database.

A person can only come to own two expectations of a case under one schema through two writers at once, so that is how
the tests make them: one restores the person's thread while the other starts a new one, each passing the catalog's
check before the other has written.

## Terms

```
AGENT: add
A row after `Following`.
---
| Following its facts | Keeping a configuration's recipe, compiled against the facts corrected since, as an edit of the person's own. |
```
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
| To choose from | A case with several expectations of the person's own under one schema or several shared with them. |
| Left to score | Scorers that applies in finished run that has no whole score of it under the scoring built now. |
| Carrying | Editing an expectation onto another case of its family, with the same data. |
| Saying | Writing what holds of a thread: its name, description, tags, collaborators, and whether it is deleted. |
| Following | Keeping the catalog's proposal as an edit of the person's fork, based on its origin's head. |
| Typed case | A case whose vignette is a text the person typed, kept in a database source. |
| Cell | The repl's word for a variation being tried together with the endpoint it runs at, named or found from its engine. |

## Outstanding
Left for later. The API's are in docs/api.md, "Outstanding". The plan the bench was built from, with the options
weighed for each decision and the survey of the old project, is `agents/wip-bench.md` at d5ebf52; the writes for
the person were planned in `agents/wip-authoring.md` at b6f76b8. Its takes were built and still wait for a word:
- one set of writes for every kind people author, with builders only for appendices and cases, a case built only of
  appendices the person sees, and no write refused on a lint ("Writes for the person", "Appendices and cases");
- a family's cases are those at its current vignette; an appendix's edit replaces only the cases at its own
  vignette; carrying keeps to the expectation's family ("Appendices and cases");
- a language is written only where a text has none ("Languages");
- one write says what holds of a thread; a collaborator can't leave a share, and a thread isn't handed over ("What
  is said about a thread");
- only an origin the person sees is followed, always by an edit, for every kind ("Following an origin");
- the head an edit names is checked under its thread's advisory lock (docs/catalog.md, "Concurrent writers");
- ownership only, roles unchecked (docs/identity.md);
- the shipped lists kept in code, versions as integers from 1, an edit keeping the head's labels only when its scorer
  is the head's, and following taking each part's labels from the side whose part it keeps ("Scorers"); no resources
  offered;
- configurations listed by purpose, in the API.

- **A low-level manual for the bench**, made from `agents/wip-authoring.md` at b6f76b8.
- **Correcting a wrong language** stays curation's: the bench refuses a language that differs from the text's own.
  What a person may correct, such as a text only their own threads hold, is open.
- **Leaving a share**: a collaborator can't take a shared thread out of what they see; only the owner can. Whether
  a collaborator may withdraw themselves, an entry the catalog would hold as any other, is open.
- **Z1**: the map from roles to the kinds each role sees goes in `identity` once the portal's views give it meaning
  (docs/identity.md, "Z1: what each role is shown"). `sees` then takes the person's roles and the kind.
- **An engine served at several endpoints** isn't picked from them, for a judge's calls or for a run: the scoring or
  the run is refused until the endpoint is named. `Bench.score` names none, so a judge whose engine two endpoints
  serve bars its scorer, in the repl and the API alike (docs/repl.md, "What the repl doesn't reach"; docs/runner.md,
  "Judges"). It probably won't happen: a World serving one engine at two endpoints serves one model on identical
  machines, a load balancer's job. Decided: as it is, until a World does; then the scoring names an endpoint per
  judge, as a run names its own.
- **The facts are read from the store each time they are asked for** (`Seen.facts`), several times a look. That is
  cheap with a facts thread per model; cache them per request if it shows.
- **A person's runs are all read**, and paged afterwards, in the API too (`Bench.runs`), and what is left to score is
  worked out for each of them, about 40 ms a run under five scorers. Page in the store once that is slow.
- **The archive's configuration saved under another name** is saved with no finding: a hand-made recipe that is a
  shared configuration's, compiled to its skeleton, becomes a thread of the person's own, and only a look's `held_by`
  says so (docs/api-api.md, "threads.py"). An expectation the same as one the person holds is refused.
- **Two saves of one name at once** can both create a configuration, in the repl's `save` (`docs/catalog.md`,
  "Concurrent writers").
- **Taking counts shared threads, not owners**: a case with two threads shared by one owner is to choose from, and
  naming that owner doesn't pick between them. Only two writers at once can leave an owner two (see "One expectation
  per case and schema").
- **The appendix layout as a part** a variation replaces, when someone wants to vary it. It is a value rather than a
  chunk, so a part would hold one where the others hold a digest, at every edge.
- **What the old bench had and this one doesn't**: what a run left unheeded (the old `outcome.py:unheeded`;
  docs/runner.md, "Smaller issues"); the old crossing of variations, which the portal is to start as several runs
  (agents/wip-portal.md, "Comparing variations"); and what holds a configuration, the portal's
  (agents/wip-portal.md), whose part for the repl `Bench.reaching` and `Bench.scored_by` cover.

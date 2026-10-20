# Bench

The bench is what one person sees and does, whatever edge they reach it through. The threads, families and runs they
see, the World's endpoints, the variation they are trying, and what is written in their name. Its edges are the repl
(docs/modules/repl.md), the API (docs/modules/api.md) and the portal (agents/wip-portal.md).

```
AGENT: REPLACE
`docs/reference/` is `docs/surfaces/` now.
---
This document describes what the bench does and why it is shaped like it is. Names, signatures and errors are in
`docs/surfaces/bench.md`.
```
This document describes what the bench does and why it is shaped like it is. Names, signatures and errors are in
`docs/reference/bench.md`.

The bench builds on the store, the catalog, the World, the facts, the runner and the scoring pass, and holds no SQL of
its own.

`bench` is the _operational_ layer of person-scoped functionality. When adding functionality, express rules as pure
functions in `identity` and utilize them here.

The bench is not for authorization, what the bench shows is what is relevant to show a person, not who may read what.

## How the bench works

### One person, one connection

A connection lasts as long as its caller, and caches logins and the model each engine serves for that long. The facts
about models aren't cached: they are read from the store each time they are asked for, so that a fact corrected while a
connection lasts is used at once.

Each write is made in one transaction, so one that is refused leaves nothing behind. Starting and scoring are the
exception: the runner and the scoring pass write each row as it lands, so that a run or a score that dies leaves a log
to read, and they need the bench's connection in autocommit mode.

## What a person sees

- **Threads** they own or collaborate on, while they are live. A kind of thread is asked for by the word for it:
  configuration, each recipe part, the model among them, tool, scorer, judge, expectation, appendix, expectation schema,
  canary set, model or facts.

- **Families** they own or collaborate on, while they are live. A family stands for its case: the one its current
  vignette makes alone, else the first, by digest, that holds the vignette, and holds that vignette and its cases. A
  family without a case isn't shown.

- **Their own deleted threads**, listed apart and found by id, so that they can be read and restored. Nothing else finds
  them: not names, not lists, not what is run or scored against.
- **Their own runs**, while they are live. Being a collaborator on a run shows nothing.
- **The World's endpoints**, which are everyone's, and read from the World. The bench gives an endpoint with its spec
  and the model its engine serves, once that engine is in the store (`Endpoint`), whether it is named or is the one a
  variation runs at (`Seen.at`).
- **What things are called**: a digest by the name of a thread they see whose head it is, their own first, else the
  catalog's title (`Seen.title`), so a scorer they forked under a name of their own is called by it.

### Finding things by name

A thread or a family is found by its name, matched whole first, since names may hold a slash, as the facts
`Qwen/Qwen3-8B-AWQ` do; only when nothing has the whole name is it read as `OWNER/NAME`. Among those it names, the
person's own win, else the ones shared with them. Several raise `Ambiguous`, which asks for `OWNER/NAME`; none raises
`NotFound`.

### Finding things by id

By id, a thread, a family or a run is found only among what the person sees, and a thread only among the kinds its word
names; the same method takes a name or an id. A run is also found by the start of its id, among their own, as a person
at a prompt types it; an edge that names things by id can take whole ids only, since a start could name another run
tomorrow.

## What a person is scored against

A person is scored against their own expectation of a case, under the scorer's expectation schema. One shared with them
is there to read and to take, by forking it, and counts once they have. So nothing someone else shares, edits, restores
or hands over changes what a person is scored against, and a correction made upstream reaches them as a proposal (see
"Following an origin") rather than under them.

### Taking

Taking an expectation forks it: a thread of the person's own, from the shared one's head. Forking changes no digest, so
what they are scored against is the shared expectation until either thread moves on, and a correction made to the origin
reaches them as a proposal. A person can take:

- **for many cases at once**, under one schema and in one transaction, an expectation for each case they have none of
  their own for, from any owner or one named. The cases left are named, each with why: theirs is kept, or several are
  shared with them to choose from, or none is.
- **one thread**, an expectation shared with them, which, when they have their own of its case under its schema, is a
  conflict unless they say to replace theirs. Replacing deletes theirs and forks the shared one in one transaction.

Replacing is a delete and a fork rather than an edit of theirs onto the shared head, since their thread would keep the
origin it was forked from, and keep proposing from it. Taking for many cases never replaces: it would reset every case
to the shared heads, the person's own corrections included, and leave every run scored against what it replaced to score
again.

Taking for many cases only adds, so it is safe to offer as one button and to repeat: taking again after more cases were
shared adds the new ones, and nothing a person was scored against changes. A run that holds a newly taken case is left
to score again, since its scoring now holds that case too.

What a person could take for a case are the live expectation threads of it under the schema that are shared with them
and not their own.

### One expectation per case and schema

A person owns at most one live expectation thread per case and expectation schema, and the catalog refuses what would
make two (docs/modules/catalog.md, "Owners"; src/chatddx/catalog/threads.py:_check_expectation). The bench refuses the
same before it writes, worded as the person reads it.

The database doesn't repeat the rule (docs/backlog.md, "Concurrent writers"), so two writers at the same moment can
still leave a person two to choose from. Then nothing picks one, and each place says so:

- scoring refuses the run under that scorer, naming the threads;
- what is left to score keeps the scorer, so the run stays listed until one of the two goes;
- a variation's reach lists the case apart from those that have no expectation;
- the case's expectation under that schema says it has expectations to choose from.

## The variation being tried

Variation is a configuration with recipe parts replaced (docs/modules/catalog.md, "Configurations and variations"): a
configuration's edit's recipe, the name the person called it by, and the parts replaced over it with the name it was set
by. With nothing replaced, it is the configuration itself.

It is a plain value, and nothing of an unsaved one is stored. It runs under its model's handle, so an edge needs a
handle beside it only for a hand-written configuration, which has no model part and runs under the one named.

A variation replaces the recipe's nine chunks and its model, which can't be taken out.

Its label, `NAME+PART=CHUNK`, is a short title for it, where the catalog would give the long one of a variation nobody
saved (docs/modules/catalog.md, "Titles"). Neither is stored.

For a variation, the bench gives:

- **its skeleton**: the stored edit it varies when nothing is replaced, the head unless an earlier edit was named, else
  the varied recipe compiled against the facts about its model as they are stored now, a skeleton nobody has saved;
  compiled into a language, against the facts its compilation pinned when nothing is replaced.
- **the request it would send**, with placeholders for the slots, and for the model when no engine is at hand.
- **where its intents landed**: for a reasoning level and a recommended sampling, the level the recipe's model is asked
  for, and why, when the facts land it on its nearest; read from the facts its compilation was compiled against when
  nothing is replaced.
- **its lints**, `translations.missing` among them (see "Translations").
- **the languages it runs in**, over some families: each language among their cases, with its cases and the skeleton
  they are sent as, or why they are left out (see "Translations").
- **its reach**: for each view of each scorer the person sees, whether the variation's output offers what the view
  reads, and which of the given families have no expectation it picks something from, or several to choose from.

A judge configuration, one whose purpose is `judge`, is looked at as the judge it would make on that engine: its lints
are the judge's, it reads no case, and it has no reach, as no scorer reads what a judge answers. It isn't run on cases:
starting it is refused. Configurations are listed by purpose (`Seen.threads(…, purpose=…)`), since a judge configuration
is no use where a run's is wanted.

Configurations can be listed by what they answer (`Seen.threads(…, answering=…)`): the title of their answer's JSON
Schema, as a page that shows management plans offers only the configurations that answer one. What a skeleton answers is
the title as written (`Seen.answers`): a translated skeleton's is its recipe's, since translating a schema translates
its title too.

### The model

What depends on the model is worked out from the facts about it. A run goes under the handle the model's weights are
under, deleted or not, to the endpoint serving its weights now (`Seen.handle`, `Seen.served`, `Inventory.serving`). A
deleted handle, and one no endpoint here serves, as another World's, are said to the person, to pick another; a look
that can't run says why and has no findings. The engine is the trial's: the handle's latest.

A reasoning level and a recommended sampling are intents rather than settings: compiling resolves them with the facts
about the model as they are stored then (docs/modules/facts.md, "Compiling intents"). So a variation the facts refuse is
refused for its model as it is looked at, before anything runs.

### Translations

Principal author: researchers (translators)

Translations map source texts to their translations, much as gettext does, into languages named by tags such as `sv` or
`pt-BR`. One chunk holds every language a configuration is translated into, so adding a language is a new version of it.
Vignettes aren't translated, so comparing languages is comparing case sets.

A configuration is written in one language and its translations carry it into others. A recipe may name translations,
and compiling it into one of their languages passes every text it holds through that language's entries: the
instructions, the few-shot examples and the prompt, the guidance and the text around where it is placed, the
descriptions of tools and of the answer tool, the titles and descriptions in schemas, and the appendix layout.

`translations.missing`: running the configuration in some language would be refused, and the warning says why, as
compiling it there says: its translations don't go into the language, or leave a text untranslated. It fires for each
language the look's cases are in that can't be sent, saying how many are left out, and for each other language its
translations go into and leave a text untranslated, whatever the cases; never for the configuration's own.

Typical cause: someone edits a source text, for instance the instructions. Translations are keyed by the exact text, so
the old entry stops matching and the new text has none.

## Writes for the person

The bench writes, in the person's name: configurations, chunks, appendices, expectations, scorers, judges, typed cases,
what is said about a thread, runs and scores. Tools, expectation schemas, engines, models, the facts about models and
canary sets are developers' and ops', written through data sets and facts files (docs/chatddx.md, "Requirements";
docs/modules/facts.md), and a scoring is built when a run is scored rather than written by hand.

What every write has in common:

- **One set of writes for every kind.**

- **An edit names the head it was made on**, configurations included, and is refused as `MovedOn` when the thread has
  moved on since (docs/modules/catalog.md, "Threads and edits"). Saving by name names the head it found.
- **Nothing is written that is there already.** An edit that is its thread's head already writes nothing, and says so;
  for a configuration, a head with the same recipe (docs/modules/catalog.md, "Recipes"). Saying what holds of a thread
  writes only what changes.
- **What was written comes back with its lints**, and no write refuses on one: an expectation whose data its schema
  refuses is written, and said so (docs/modules/factors.md, "Lints").
- **Some refusals come before the write**, in the person's words, where the database or the catalog would refuse later
  in theirs: a component of another kind than the thread's, a second expectation of the person's own for a case and
  schema.

### Configurations

- **Forking** keeps a variation as a new configuration of the person's own, forked from the edit it varies.
- **Editing** keeps it as a new version of a configuration the person owns.
- **Saving** by name is one of the two: a new version of the person's own configuration of that name, else a fork.
  Several of their own by that name are refused.
- **Making one from a recipe** a recipe is made with a model's digest picked by its handle, compiled against the facts
  about it.

A configuration is kept with the compilation that makes it: for a variation with parts replaced, or a recipe, the one
the running code compiles; otherwise the configuration's own.

### Components

A person writes the kinds of chunk a recipe's parts take, appendices, expectations, scorers and judges, each from its
JSON as the store gives it:

- **new**, as a thread of the person's own, with a name;
- **a fork** of a thread they see, from its head or from a component given in its place;
- **an edit** of a thread they own.

What a component refers to must be stored already, so a toolset can't bring a tool of its own, and a judge is written
over a judge configuration already kept, which its own rule holds it to (docs/modules/factors.md, "Judge").

### Languages

A text is written with its language when the person gives one, and only a text can have one. A language belongs to the
text, wherever it is held (docs/modules/catalog.md, "Languages"), so a person giving one to a text someone else holds
too would change it for them. So the bench writes one only where the text has none, and refuses one that differs from
what it has; the person writes another text, or leaves it.

### Scorers

A scorer names scoring code the running chatddx ships (docs/modules/factors.md, "Scorer"), and the views the person
writes over it, each picking from an answer and from an expectation. A scorer the running code could never score with is
refused as it is written, and the scoring pass refuses it the same way. A view that can't pick anything from the
scorer's expectation schema is written, and said so.

It is a refusal rather than a lint because what the code ships is also a protection (docs/modules/factors.md, "Scorer").

What a scorer's views and resources are called belongs to the edit they are written with, by its writer
(docs/modules/catalog.md, "Scorer labels"). Labels on the digest would let anyone who forks a scorer unchanged rename
its views for everyone who sees it, the archive's included.

A scorer digest is called what the person's view calls it: the labels of the head that holds it, their own first, else
of the latest edit that held it in a thread they see. Following an origin keeps the labels of whichever side's views the
proposal keeps.

### Appendices and cases

A family stands for one case, the one its current vignette makes alone, else the first that holds it, and lists all of
its cases at its current vignette, that one first. What is run and scored is a case, so a run names cases rather than
families. The bench starts a run on any stored cases; the edges offer only the current ones of the families the person
sees.

A new version of an appendix stores each case that held the old one at that vignette again, with the new one in its
place, so the new cases are there to pick, and says which replaced which. No expectation moves with them, since an
appendix can change the right answer (docs/modules/factors.md, "Case"). Carrying one is an edit of the person's
expectation onto another case of its family, with the same data, as a clinician's word that it still holds there. An
expectation's edit keeps to its family: a case of another is refused.

A case left at an earlier vignette by a repair is offered a replacement (docs/modules/catalog.md, "What has moved on"),
which the bench stores when asked. An appendix's edit replaces only the cases at its own vignette, since one at an
earlier vignette awaits that replacement instead.

### Typed cases

A case can be typed rather than fetched from a directory: the text is kept in the database, in a source of the
`database` kind (agents/wip-portal.md, "Typed cases"), under a new id and never changed, and its case and a family of
the person's own are written with it, all at once, in the language the person says it is written in, and named when they
say so. A typed case always has a language, since a configuration is sent in its case's (see "Translations"). It runs as
any case: a vignette is fetched from its source, a directory's file or a database source's text, wherever the bench, the
runner and the edges read one (src/chatddx/store/texts.py:fetch_vignette).

### What is said about a thread

Only its owner says what holds of a thread, as only they edit it: a collaborator may fork it, but not rename, share or
delete it. One write says what is to hold afterwards, any of: the name, or none so the title takes over; the
description, which is replaced but never taken away; the tags and the collaborators, each as the whole set, the
collaborators by login; and whether it is deleted. Only what changes what holds is written, all at once, so saying the
same again writes nothing. A form shows the whole thread and sends it back; a write per field would ask the edge to tell
what changed, and leave half a change when one of several fails.

### Following an origin

When a fork's origin has moved on, the catalog proposes the origin's head with the fork's changes on top
(docs/modules/catalog.md, "Forks"). The bench shows what following would keep before it is followed: the base and the
origin's head, what the fork varies, the proposal, and the digest it comes to, a recipe compiled by the running code
against the facts as they are stored now, so that an edge can tell a fork it wouldn't change. Nothing is proposed when
the origin hasn't moved on, or when the person no longer sees it, deleted or unshared, since its head is then not theirs
to read.

### Following facts

A configuration is behind what it was compiled for when its facts or its model moved on, as to a new revision of the
weights (docs/modules/catalog.md, "What has moved on"). Whoever sees it sees both (`Bench.moved`,
`GET /api/threads/{thread}/follows` as `moved`, the configuration page); its owner follows them as one edit, the recipe
with the model's head compiled against the current facts (`Bench.follow_moved`, `POST .../follows` with
`"follow": "moved"`). Facts that refuse what it asks are said, not followed.

## Runs and scores

- **Cases** a run is started on are the current cases of the families the person sees, and running again needs every
  case's family still seen; another is "not found", as a family is.
- **Queueing** puts a started run, or a scoring of a finished one under the scorers that apply to it, in the queue for
  the worker (docs/modules/worker.md), as the person's job; a scoring under no scorer, or of an unfinished run, is
  refused.
- **Starting** runs a variation under its model's handle. A run for each language its cases are sent in (see
  "Translations"). As it starts, each is named by the variation's label and says what it varied:
  (docs/modules/catalog.md, "What a run ran").
- **Resuming** a run of the person's own that isn't finished sends what its log lacks (docs/modules/runner.md,
  "Resuming").
- **A person's runs** are their own, newest first, found by the start of their id, or by a component their trial is
  built on.
- **A start's runs** are its first and those started with it, found from the first; a run says the first of its start,
  or nothing when it is the first or was started alone.
- **A run is described** as the repl's `run` and `run tag` say it: the run's name, else the configuration, where it ran,
  its case or how many, the language it was translated into, and the seed.
- **A scorer applies** to a run when the run's output offers what each of its views reads, a view of the whole answer
  only a text answer, and the World lets each of its judges run (docs/modules/runner.md, "What applies to a run").
- **A run's scoring** is built from the expectation each of its cases is scored against.
- **Scoring** scores a finished run under each scorer that applies to it.
- **What is left to score** of a run is each scorer that applies, under which some of its cases have an expectation.
- **Stopping a scoring**, as Ctrl-C does, finishes the score under way with what it has, and the scorers after it aren't
  scored.
- **A run's scores** are the latest under each scorer that scored it, each named by the thread the person sees holding
  that scorer, their own first; or every score of the run, newest first; or one by its id.

## Errors

The bench's errors are told apart by their class, so that an edge can answer each its own way:

| Error        | Is a                   | For                                                                       |
| ------------ | ---------------------- | ------------------------------------------------------------------------- |
| `NotFound`   | `LookupError`          | what the person doesn't see, or the store doesn't hold                    |
| `Ambiguous`  | `LookupError`          | a name, an id's start or a case's expectations that give several          |
| `Conflict`   | `ValueError`           | a write that would undo what the person has                               |
| `MovedOn`    | `ValueError` (catalog) | an edit made on a head that isn't the head any more                       |
| `OverQuota`  | `ValueError`           | more of something than a day takes, or a run of more items than one takes |
| `ValueError` | Any other `ValueError` | what the bench refuses: an unknown part, an unstored digest               |

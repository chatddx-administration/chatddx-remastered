# The portal: plan

The portal is the bench's web edge, beside the repl and the API: HTML rendered on the server from the bench, with Svelte
islands where a page needs a round trip. Its pages are built; its plans were itemized into `docs/backlog.md` and retired
(`git show f8967c3:agents/wip-portal.md` holds the last of them). This plan starts again from the Library. "Decided"
means the user said so. "Take" is the agent's recommendation and still open.

## The configuration space

What clinicians and researchers author, by where it is kept. Principal authors are `docs/glossary.md`'s ("Roles"); what
a person writes is.

### Components kept as threads

A thread is a component's versions; the bench names its kinds by word (`src/chatddx/bench/model.py:KINDS`) and writes
some of them in a person's name (`WRITTEN`).

| Word                                                       | Author                 | What a person writes                                                                                                                                          |
| ---------------------------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| appendix                                                   | clinician              | new, a version, a fork; a new version stores again each case that held the old one                                                                            |
| expectation                                                | clinician              | new, a version, a fork; taken from one shared, carried onto another case of its family; one live per case and schema per owner                                |
| instructions, few_shot, prompt, output, toolset            | researcher             | new, a version, a fork, each with the language of its text                                                                                                    |
| sampling, reasoning, passthrough                           | researcher             | new, a version, a fork; a level or the recommended sampling are intents the facts resolve as a recipe compiles                                                |
| translations                                               | researcher, translator | new, a version, a fork; into languages, with none of its own                                                                                                  |
| configuration                                              | researcher             | a skeleton with the recipe it was compiled from: made from a recipe, or a variation kept as a fork or a version; following its origin, or its model and facts |
| scorer                                                     | researcher             | new, a version, a fork: its views, free parameters, resources and labels, over code and an expectation schema it picks; labels are written with each edit     |
| judge                                                      | researcher             | new, a version, a fork: a judge configuration, a model by its handle, and seeds                                                                               |
| tool, expectation_schema, canary_set, model, engine, facts | developers and ops     | nothing: data sets and facts files write them, and a person forks none of them                                                                                |

### Cases and families

A case has no thread: a vignette and its appendices, named through its family. A clinician types a case, which keeps the
text in the store and writes its case and a family of their own; builds cases of a family's appendices; and stores a
replacement for a case a repair left behind. A family's bindings are its versions, where its vignette is at each repair,
and repairs are curation's. The vignette is sensitive, and has a place of its own at each edge.

### What is said

Entries are said about a thread, a family, a run or a score: a name, a description, tags, an owner, collaborators and
whether it is deleted; a family's language; and what a run ran, which a start writes. Beside them, the labels of a
scorer's edit and the language of a text, which is kept on the component. All of it is append-only, so what was said
before is history the catalog keeps.

### Composed but not kept

- **The variation**: a configuration's edit with parts replaced, a plain value nothing stores until it is kept
- **The trial**: the skeleton, the engine of the handle, the cases, the cleanup and the seeds, built and stored as a run
  starts (`src/chatddx/factors/trial.py:Trial`; `src/chatddx/bench/runs.py:start`). The glossary makes researchers its
  authors, and the catalog lets every kind but cases and compilations have threads, but the bench has no word for it.
- **The execution and the canary set**: the endpoint's, with a concurrency and an order a start may give
  (`src/chatddx/api/schemas.py:NewRun`; `docs/backlog.md`, "Execution settings as a component").
- **The scoring**: built when a run is scored, from the person's own expectations and the scorer, rather than written by
  hand. It is derived, not configured.

### Not theirs

Tools, expectation schemas, canary sets, models, engines and facts are developers' and ops' (see "Components kept as
threads"); the inventory and the World are ops'; people and roles are an admin's (`docs/backlog.md`, "Administering
people"). The archive owns what data sets load and shares it with everyone it loads for, so a person reads the archive's
threads and forks what they want to change.

## Configuration and actions

Take: configuration is what is kept and holds until someone changes it: a component kept by a thread's edit, a case
built, an entry, a label, a language. An action sets the rig going or steers what is going: it writes the ledger, the
queue or a session, and holds nothing for later. The Library is configuration's; actions stay where runs are started and
watched.

| Configuration, in the Library                                                         | Action, elsewhere                                                                                             |
| ------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| a component new, versioned or forked (`Bench.new`, `edit`, `fork`, `save`)            | starting a run: its trial stored, the gate asked, its start record written, its job queued (`start`, `queue`) |
| following an origin or the facts (`follow`, `follow_moved`), each an edit             | running again (`again`) and resuming (`resume`)                                                               |
| taking and carrying expectations (`take`, `take_from`; carrying is an edit)           | scoring, and scoring again (`queue_scoring`, `score`), which build the scoring                                |
| a case typed, a case built, a replacement stored (`type_case`, `case`, `replacement`) | halting a job; pausing, resuming and stopping one's queue                                                     |
| what is said (`say`), a scorer's labels, a text's language                            | signing in and out                                                                                            |

Neither: a look at a variation, a component checked as it is typed, a scorer tried, what a judge is asked. They write
nothing, and sit beside what they preview.

A start writes entries too, the run's name and what it varied: the action's record of itself, not configuration.

The line is unclear in one place, **composing a run**. It is configuration by the data model, a trial a researcher
authors, but it is kept only by starting. Options:

- **(a)** As now: a run is composed where it starts, on a configuration's page and on Review, and the Library shows
  trials only through their runs.
- **(b)** Trials as threads, as the catalog allows: a run is composed in the Library as a trial, whose fields are its
  skeleton, its engine by handle, cases, cleanup and seeds, and starting is queueing that trial's head under an
  execution. A trial is in one language, as it names one skeleton, so a start over several languages stays a start of
  several trials. What has moved on already covers a trial's skeleton, engine and cases.
- **(c)** A draft run held in the page's address, as the variation is, and kept nowhere.

Decided: (b). It is the reflection of the data model, and the one that makes composing a run configuration and queueing
it an action. It comes after the steps that need no new kind.

## The Library today

### What it holds

`/library?kind=WORD` lists every thread of a kind the person sees, their own first, and their deleted threads with
**Restore** (`src/chatddx/portal/threads.py:library`). Each thread has a page, `/threads/{id}`
(`src/chatddx/portal/threads.py:thread_page`; `src/chatddx/portal/templates/thread.html`), with:

- **About it**: its kind, owner, collaborators, language, origin, tags and description, read-only.
- **What it holds**: its versions stepped through with ◀ ▶, each version's fields one level deep, a reference by its
  title, and what it changed from the one before (`frontend/src/islands/Thread.svelte`, `frontend/src/lib/thread/`).
  Without scripts, the head's JSON and a list of versions.
- **What is said of it**, to its owner: one form for its name, description, tags and collaborators, the last two as
  comma-separated words (`src/chatddx/portal/threads.py:saying`), and **Delete it**.
- **Its origin has moved on**, to its owner, with **Follow its origin**.
- **An editor**: a new version of the person's own, or a fork of another's.
- **Fork it as it is**, to everyone.

By kind:

| Word                                                                              | Begun from the Library                                 | Its editor                                                     |
| --------------------------------------------------------------------------------- | ------------------------------------------------------ | -------------------------------------------------------------- |
| configuration                                                                     | no: a recipe on `/configurations`                      | none here: its tab and page lead to `/configurations/{id}`     |
| instructions, few_shot, prompt, output, sampling, reasoning, passthrough, toolset | yes                                                    | `ChunkEditor`                                                  |
| translations                                                                      | no: on `/translate`, beside what it translates         | `TranslationsEditor`                                           |
| appendix                                                                          | no: on a family's page and on Review                   | `AppendixEditor`                                               |
| expectation                                                                       | no: on a family's page and on Review                   | `ExpectationEditor`, drawn from its schema                     |
| scorer                                                                            | yes                                                    | `ScorerEditor`; none for code the running chatddx doesn't ship |
| judge                                                                             | yes                                                    | `JudgeEditor`                                                  |
| tool, expectation_schema, canary_set, model, engine, facts                        | no: "written through data sets, by developers and ops" | none                                                           |

Outside the Library, a configuration's page (`src/chatddx/portal/templates/configuration.html`) shows what is said of it
read-only, its versions stepped through on the server by `head`, its recipe, the variation's island and its runs. A
family's page shows what is said of it read-only, writes appendices, builds cases, and offers each case's expectation to
write, take or carry. A run's page halts, resumes, scores again and runs again.

## Cases

The landscape for step 5, and its options. A family is the catalog's handle on a vignette; to a person it is a case, as
the bench and the repl say it ("no case 12 for alice"), and the Library says so too.

### A case's section, true to the data model

The family is the section's subject, as a thread is a thread's, and the vignette is shown as a case represents it:

- **About it**: its name, owner, collaborators, language, tags and description, with what is said, leaving and deleting
  as a thread's.
- **What it holds**, version N of M by link, a version being a binding: the vignette's source, id and fingerprint, who
  bound it and when, and what changed from the binding before, its id or its content. Its text is never shown: a link
  leads to its own place.
- **Its cases at that vignette**, each a component with its fields one level deep: titled by its name alone first, then
  "NAME with APPENDIX, …"; its digest; its appendices, each by the appendix thread that holds it; and under each schema
  the expectations of it, the person's own and those shared with them, linked. At an earlier binding, each case with its
  replacement, stored or to store.
- **What is begun of it**, at the current binding: a case, its appendices picked one a line; an appendix, with the
  vignette given; an expectation of one of its cases, with the case and the schema given.

### Options

The takes in bold, decided as put and built. What changed since the options were first put, in "Reconsidered".

1. **Where a case lives.** **(a) A Library kind, case: `/library?kind=case` lists the cases a person sees by their
   families, their own first and their deleted ones apart, and `/cases/{id}`, a family's id, is its section.**
   `/families` and `/families/{id}` give way; writing in place, an appendix's text and an expectation's form, is left to
   Review, which the section links.
2. **What is said of a case**: the same interface as a thread's, through the bench, `Bench.say` and `Bench.leave` taking
   a family as they take a thread, and the API. Its language: **(a) among what is said, its owner's to correct, as its
   name is**; (b) as it was typed or loaded, curation's to correct; (c) with a text's language, in step 7. A case's
   language decides which of a configuration's translations it is sent in, so correcting it changes what its next runs
   send.
3. **Its versions**: its bindings, by link and read-only, as above. **Its fingerprint shown whole**, as it is the
   vignette as a case represents it.
4. **Its cases and what is begun of it**, as above. Taking an expectation is forking it as it is, and carrying one is
   editing its case, which its form picks; Review keeps its buttons for both.
5. **Taking for many cases.** **(a) On the case tab, over the cases it lists, filtered by tag: a schema picked, and an
   owner or any**; (b) on an expectation schema's section, over the cases picked there; (c) the API alone.
6. **Where a case comes from.** **Typed on Home, or loaded with a data set: the Library begins none**, as typing one
   writes a vignette, and the case tab says so.
7. **The vignette's own place**, now that `/families/{id}` gives way: **(a) `/cases/{id}/vignette`, a page apart from
   the Library, which the section links**; (b) Review's alone; (c) `/families/{id}/vignette`, as it is.
8. **The API's word.** **(a) `families`, the data model's, as the API is for developers**; (b) `cases`, as the interface
   says.

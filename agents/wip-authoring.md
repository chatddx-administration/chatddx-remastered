# Authoring: work in progress

The writes the bench makes for a person beyond configurations, runs and scores: chunks, recipes, appendices and the
cases that order them, expectations, and what is said about a thread, from its name to whether it is deleted. They are
the bench's, since every edge writes for a person through it (agents/wip-bench.md, "Writes for the person"); the
portal is the first edge to need them (agents/wip-portal.md, "Below the UI", "Phases" 4 and 5).

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **Nothing is decided yet.** The takes below make one plan; "Questions for the user" is what it can't settle alone.
2. **Taking expectations comes first** (phase 1). A person is scored against their own expectations only, so one who
   wasn't given the giftbag has nothing to be scored against until they can take some.
3. **One set of writes for every kind people author** (A1), with builders only where a kind binds to a family's
   vignette: appendices and cases (A2).
4. **No write refuses on a lint** (A6): what was written comes back with its lints. Refusals stay the components' and
   the catalog's.

## What is asked
| What | Principal author | Asked by | Written today |
| --- | --- | --- | --- |
| Chunks: instructions, few-shot, prompt, output, sampling, reasoning, passthrough, translations, toolset | researchers | `docs/chatddx.md`, "Requirements"; `docs/factors.md`, "Requests" | by curation, as the archive; forks of them by the giftbag |
| Recipes, made into configurations | researchers | `docs/chatddx.md`, "Requirements" | only a variation of a configuration the person sees, forked or edited (`Bench.fork`, `Bench.edit`) |
| Appendices, and the cases that order them | clinicians | `docs/factors.md`, "Case" and "Appendix" | nothing: a data set can't hold appendices (`docs/curation.md`, "What a data set can't hold yet") |
| Expectations, and taking one shared | clinicians | `docs/factors.md`, "Expectation"; `agents/wip-bench.md`, "What a person is scored against" | by curation, as the archive; forks of them by the giftbag |
| A text's language, offered the previous version's | — | `docs/catalog.md`, "Languages" | by curation, from a data set's texts |
| Names, descriptions, tags, collaborators; deleting and restoring | — | `docs/catalog.md`, "Entries" and "Deleting"; `docs/chatddx.md`, "Intended evolution of configurations" | a name, when a configuration is forked (`Bench.fork`); the rest by curation |
| Accepting a proposal once a fork's origin moved on | — | `docs/catalog.md`, "Forks" | nothing: `Catalog.proposal` has no caller |
| Typed cases and their families, for swift | clinicians | `agents/wip-portal.md`, "Typed cases" | nothing; needs a `source` schema |
| A scorer's labels, carried to its next edit | — | `docs/catalog.md`, "Scorer labels" | by curation, for each scorer digest, from a data set |

Not here:
- **Trials and batches** are the batch planner's (agents/wip-batch.md).
- **Scorings** are built when a run is scored (`Bench.scoring`), from the scorer and the person's expectations, so
  none is written by hand.
- **Tools, expectation schemas, engines, models and canary sets** are written by developers and ops, through data
  sets (`docs/chatddx.md`, "Requirements").
- **Scorers and judges** wait on a question (see "Questions for the user", 1).

## What it builds on
- **The catalog's writes**, generic over kinds: `create` (with an owner, a name and the edit it was forked from),
  `edit` (with `based_on`), `keep`, `note`, `adopt`, `language`, `label`, and `proposal` and `behind` to read what has
  moved on. Its rules are checked as it writes: a kind that has threads, a `based_on` in the fork's origin, one live
  expectation per owner, case and schema, an entry's shape, a language only on a text, a label only on a position the
  scorer has. The database repeats all but two of them (`docs/catalog.md`, "Concurrent writers"), and refuses an edit
  whose component is of another kind than its thread (`src/chatddx/store/migrations/0010-t0-catalog.sql`).
- **Storing a component** checks its references and the rules that take several components, and errors stop it
  (`docs/factors.md`, "Errors and findings"). A component is built from its JSON by its kind's model
  (`src/chatddx/factors/kinds.py:BY_KIND`).
- **Lints**, which warn and never refuse (`docs/chatddx.md`, "Compromises"), such as an expectation whose data fails
  its schema: "Building an expectation doesn't check its data against its schema. Lints do" (`docs/factors.md`,
  "Expectation").
- **The bench's configuration writes**: a skeleton's edit and its compilation, in one transaction (`Bench.fork`,
  `Bench.edit`, `Bench.save`).

## Takes
### A1. One set of writes for every kind
Three writes, for every kind people author (the chunk kinds, skeletons, appendices and expectations):
- **new**: a component as a new thread of the person's own, with a name;
- **fork**: a thread the person sees as a new thread of their own, with a name, its head or a component given in its
  place;
- **edit**: a new version of a thread the person owns, or nothing when the component is its head already.

A configuration keeps taking a variation where another kind takes a component, as `fork` and `edit` do today, and
`new` takes a recipe for one (A12). A kind people don't author, or a component of another kind than the thread's, is a
`ValueError` before the database refuses it.

Why: the catalog's writes are generic over kinds already, and what differs between kinds is what a component is, which
its model checks. A write per kind would say the same thing nine times.

### A2. Builders where a kind binds to a vignette
- **An appendix** is built by the bench from a family and a text: bound to the family's current vignette, with its line
  endings normalized before it is digested, CRLF and CR to LF. `docs/factors.md` ("Appendix") asks this of the
  portal, since browsers send CRLF; in the bench every edge does it. It is then written as a new thread, or as an edit
  of one.
- **A case** is built from a family and appendices in order: the family's current vignette with those appendices, and
  stored. It writes nothing in the catalog, since a case belongs to its family by its vignette (`docs/catalog.md`,
  "Families and repairs"). An appendix bound to another vignette is refused by the case's own rule.

An expectation needs no builder: an edge has its case, its schema and its data.

### A3. A family's cases
A family stands for one case today: the one its current vignette makes alone, else the first that holds it. Once
appendices are written, a family has several, and what is run and scored is a case. Take: a family lists its cases,
the bare one first, and an edge picks one; the one it stands for today stays its default. Runs, the reach and
expectations take cases already.

### A4. Editing an appendix
A new version of an appendix makes every case that holds the old one behind (`docs/catalog.md`, "What has moved on"),
and expectations are keyed by their case. Take: the edit also stores each such case's replacement, the same appendices
with the new version in its place, so that the new cases are there to pick, but moves no expectation, since an
appendix can change the right answer (`docs/factors.md`, "Case"). Carrying an expectation to a replacement is a write
of its own, an edit of the expectation onto the new case with the same data, made when a clinician confirms that it
still holds, as after a repair that changed a vignette's content (`docs/catalog.md`, "Repairing").

The same builder stores a late case's replacement, which `docs/catalog.md` ("Smaller issues") leaves to the portal.

### A5. Taking expectations
Taking is forking: the person's own thread, starting from the shared one's head and forked from it, so a correction
made to the origin reaches them as a proposal (A8). Forking changes no digest, so the expectation scored against is the
same until either moves on.

For many at once, the bench takes, under one schema and in one transaction, an expectation for each of some cases or
families the person has none of their own for: what the giftbag does for the sample, for any person and from any
owner. Left out, and named in what it returns:
- a case they own one for already, which stays theirs;
- a case with shared ones from several owners, since nothing picks between owners.

Beside it, the giftbag keeps a person's own expectation for a case and schema, as it keeps a fork they already have,
rather than fail `init-data` on the catalog's rule (agents/wip-bench.md, "Outstanding").

### A6. What was written comes back with its lints
Each write returns what it wrote and the lints of it, as findings: an expectation whose data fails its schema or can't
be checked against it, and whatever else the lints say of the component (`docs/factors.md`, "Lints"). Nothing new
refuses: the components' rules, `Store.add` and the catalog's rules still do.

### A7. Languages
A text's language goes with the write that makes the text, and the catalog checks it, as it checks curation's
(`Catalog.language`: text chunks and hand-written skeletons only). The bench doesn't carry the previous version's
language on its own. An edge offers it and the person keeps it or changes it, as `docs/catalog.md` ("Languages")
says. A fork that changes nothing keeps its language, being the same digest.

### A8. Following an origin
Accepting the catalog's proposal for a fork the person owns: compiled when it is a recipe, then an edit with
`based_on` the origin's head (`docs/catalog.md`, "Forks"). Nothing is written without a proposal. It matters first for
taken expectations and the giftbag's forks, which otherwise never see the archive's corrections, and for forked
configurations.

### A9. What is said about a thread
A thread's name, description, tags and collaborators, and deleting or restoring it, are entries the bench writes on
what the person owns (`About.owned_by`), as `edit` already requires: a collaborator may fork a thread, but not edit,
share or delete it. Sharing names a person by login. Restoring is held to the catalog's rules, so restoring a second
expectation of one case and schema is refused. Handing a thread over to another owner isn't offered.

What deleting hides stays the portal's question (`docs/catalog.md`, "Smaller issues"); the bench hides a deleted
thread from everything but its history and the runs that used it.

### A10. An edit names the head it was made on
An edit may name the head the person saw, and the bench refuses it when the thread has moved on since, with an error
of its own that the API maps to 409. It answers "An edit has no precondition" (agents/wip-api.md, "Open") for
configurations too. Optional, so the repl's `save` keeps working as it does.

### A11. Who may write what
Ownership only, as now: a person makes new threads and writes on their own. Roles aren't checked. Z1 will map roles
to the kinds each one sees (agents/wip-identity.md, "Open"); the kinds each one authors can go beside it, clinicians
appendices, expectations and typed cases, researchers chunks and recipes, as a convenience for the portal's forms, not
a refusal (agents/wip-identity.md, "Authorization").

### A12. Recipes into configurations
A recipe the person makes, by the chunks' digests for each part, its purpose and its appendix layout, is compiled and
kept as a new configuration of their own with its compilation, as `fork` keeps one. It has no origin. An edge finds
the chunks by name through `Bench.chunk`.

## The edges
- **API**: the routes `GET /api/threads` already has, made writable for every kind people author:
  `POST /api/threads` (a kind, a component or a recipe, a name, a language), `POST /api/threads/{id}/forks` and
  `POST /api/threads/{id}/edits` (parts for a configuration, else a component; the head seen), and beside them a
  thread's entries, collaborators, deletion and restoration, and following its origin. Families: appendices and
  cases under `/api/families/{id}`. Taking: one request for many cases. A component in a body is its JSON as
  `GET /api/components/{digest}` gives it.
- **Portal**: phase 5's pages (agents/wip-portal.md, "Phases"), and the editors checked against a kind's JSON Schema
  as they are typed ("Islands").
- **Repl**: taking, since its users need expectations to be scored against; the repl is for trying variations, and
  the rest is the portal's.

## Phases
Each with its tests in `src/chatddx/bench/test/` and the API's.
1. **Taking**: taking expectations for cases or families, and the giftbag keeping a person's own; the repl's and the
   API's.
2. **Chunks and expectations**: new, fork and edit for every kind people author, with a language for texts, lints
   returned, kinds checked, and an edit's head.
3. **What is said about a thread**: name, description, tags, collaborators, deleting and restoring.
4. **Following an origin.**
5. **Recipes into configurations.**
6. **Appendices and cases**: the builders, a family's cases, replacement cases, and carrying an expectation over.
7. **Typed cases**, with the portal's swift (agents/wip-portal.md, "Typed cases", and its phase 4).

## Questions for the user
1. **Are scorers and judges written in the portal?** The docs disagree. `docs/chatddx.md` says "Engines, models,
   canary sets, expectation schemas and scorers are authored by ops or developers" ("Requirements"), but names
   researchers as the authors of scorers ("Roles mentioned") and lists judges among the portal's interfaces;
   `docs/factors.md` names researchers as the principal authors of both. If scorers are written in the portal,
   carrying their labels to the next edit is the bench's to do; if only through data sets, curation already writes
   them for each scorer digest.
2. **Taking one they already own.** When a person takes a shared expectation for a case they have their own for,
   should the bench leave theirs (the take, as the giftbag does), or replace it?
3. **Appendix edits and expectations.** Store the replacement cases and carry expectations only when confirmed (the
   take), or carry them along at once?
4. **A precondition on every edit** (A10), configurations included?
5. **Sharing further.** Only the owner shares (the take), or may a collaborator share too? And should a thread ever be
   handed to another owner?

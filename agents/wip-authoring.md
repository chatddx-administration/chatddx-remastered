# Authoring: work in progress

The writes the bench makes for a person beyond configurations, runs and scores: chunks, recipes, appendices and the
cases that order them, expectations, and what is said about a thread, from its name to whether it is deleted. They are
the bench's, since every edge writes for a person through it (agents/wip-bench.md, "Writes for the person"); the
portal is the first edge to need them (agents/wip-portal.md, "Below the UI", "Phases" 4 and 5).

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **Decided: what of a scorer and a judge researchers write** (see "Scorers and judges"). The rest are takes;
   "Questions for the user" is what the plan can't settle alone.
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
| Scorers: their views, free parameters and labels, over shipped code | researchers (decided) | `docs/catalog.md`, "Scorer labels"; "Scorers and judges" below | by curation, as the archive, with the labels of each scorer digest from a data set |
| Judges: a judge configuration, an engine, seeds, a fill rule | researchers (decided) | `docs/factors.md`, "Judge" | nothing; no judged view can be scored yet |

Not here:
- **Trials and batches** are the batch planner's (agents/wip-batch.md).
- **Scorings** are built when a run is scored (`Bench.scoring`), from the scorer and the person's expectations, so
  none is written by hand.
- **Tools, expectation schemas, engines, models and canary sets** are written by developers and ops, through data
  sets (`docs/chatddx.md`, "Requirements").
- **Scoring code and expectation schemas** are developers', shipped with the project and picked (see "Scorers and
  judges").

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
Three writes, for every kind people author (the chunk kinds, skeletons, appendices, expectations, scorers and
judges, each with what of it is written and what picked, as "Scorers and judges" says for the last two):
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

## Scorers and judges
Decided, for what a researcher writes and what they pick:

| Part | Written, picked or shipped |
| --- | --- |
| A scorer's code and entry point | shipped: developers write them and ship them with the project |
| Its expectation schema | picked, among the shipped ones |
| Its views | written by researchers |
| Its free parameters | not decided (see S3) |
| Its resources | picked |
| The labels of its views and resources | written by researchers |
| A judge's skeleton | written, as a configuration whose purpose is `judge` |
| Its engine | picked by researchers |
| Its seeds | written by researchers |
| Its fill rule | picked |

Good pickers need the code to publish what it accepts: its metrics' names and a schema for their parameters, much as
the components' JSON Schemas could name the kinds each reference takes (`docs/factors.md`, "Reference kinds in
components' JSON Schemas").

### What a researcher does with it
- **Starts a scorer** by forking a shipped one, or from shipped code, which needs a list of the code's entry points
  (S1). Today only a data set names an entry point.
- **Writes views**, each picking from what an answer offers and from what an expectation holds: the selectors can be
  checked as they are typed, against the output schema of a configuration they pick and against the scorer's
  expectation schema, as `Bench.reach` and the `view.unreachable` lint do already. The metric and its parameters come
  from what the code publishes (S1, S3); a split and a judge are picked.
- **Labels them** in the same write, so the labels belong to the version they name (S4).
- **Sees its effect** at once: the scorer applies to the runs whose output its views reach (`Bench.scorers_for`), and
  every finished run is left to be scored under the new version (`Bench.outstanding`).
- **Writes a judge** as a configuration of purpose `judge`, with the variation workflow every configuration has, and
  a judge over it with an engine and seeds (S6).

### S1. The code publishes its entry points
The project keeps a list of the scoring entry points it ships. Each one publishes its metrics, each with a name, what
it measures and a JSON Schema for its parameters, and optionally a schema for the parameters every view shares. The
portal's pickers and forms read the list, the bench refuses a scorer that names anything else, and the scoring pass
runs nothing else. Today `chatddx.scorers.scorer.Metrics` publishes names only, and they are checked only when a run
is scored (`chatddx.scorers.scorer.function`).

Why it is a refusal and not a lint: the list is also a protection. `chatddx.core.rig.entry` imports whatever module an
entry point names, of any installed package, and calls it with a view's metric, the picked items and the parameters.
That was safe while only data sets named entry points; a scorer written over the API names its own. Checking that the
code is the running chatddx doesn't check which function in it runs. Tools name entry points the same way, and should
be held to a list of their own.

Packaging entry points would serve as the list (`docs/factors.md`, "Finding code through packaging entry points").

### S2. A scorer's code pin, and deploys
A scorer pins the running chatddx's distribution, version and revision, and only that code is run
(`chatddx.core.rig.entry`). Every deploy changes the revision, so every scorer stops scoring until it is pinned again.
For the archive's scorers, running `init-data` again does that (`src/chatddx/curation/plan.py`); a researcher's own
scorer has nothing that does. And a scorer pinned again is a new scorer, so every finished run is left to be scored
again under it, though nothing in the scoring changed. Tools have the same pin, so each deploy also changes every
skeleton that offers a tool, and every trial over one.

- **C1. Keep the pin**, and give researchers a write that pins their scorers again to the running code, offered after
  a deploy: their scorers and their runs go through it on every deploy.
- **C2. Pin a version of the scoring code** that its developers raise when its behavior changes, as a cleanup step,
  a split or a fill rule is named and versioned (`docs/factors.md`, "Text cleanup"). A deploy that doesn't change how
  anything scores leaves every scorer's digest as it was. Which chatddx scored a run is still kept, in each score's
  `rig` (`src/chatddx/ledger/score.py:ScoreStarted`).

Take: C2, for scorers and tools alike. It is a change to `docs/factors.md` ("Code", "Tool", "Scorer"), so it is the
user's to decide (see "Questions for the user").

### S3. Free parameters
A view's parameters go to its metric, over the scorer's own (`scorer.params | view.params`,
`chatddx.scorers.scorer.score`). None of the shipped metrics reads any (`chatddx.scorers.patterns`), and nothing checks
them. Take: they are written by researchers, as the views are, but only where the code publishes a schema for them
(S1): a view's, from its metric's schema, and the scorer's own only for code that publishes parameters its views share.
Where nothing is published, nothing is offered, so today a researcher sets none. A parameter the schema refuses is
refused by the write, as an unknown metric is, since the scorer could never score with it.

### S4. Labels
A label names a view or a resource of one scorer digest, and the latest label wins, whoever wrote it
(`src/chatddx/store/migrations/0010-t0-catalog.sql`, `catalog.label`). Once researchers write labels, one who forks a
scorer without changing it, and so shares its digest, relabels it for everyone who sees it, the archive's included.
Take: the labels a person sees for a scorer are their own, else those written first for that digest, as a person is
held to their own expectation (`agents/wip-bench.md`, "What a person is scored against"). Every label row records who
wrote it, so it is a change to how labels are read, not stored. A scorer write carries its labels, so they are
carried to the next version by whoever moved the positions, as `docs/catalog.md` ("Scorer labels") expects.

### S5. Resources
A scorer's resources are strings, not references (`src/chatddx/factors/scoring.py:Scorer`), no kind of component
holds one, and the scoring code isn't given them (`chatddx.scorers.scorer.ScoreFunction`). So there is nothing to pick
yet. Take: none are offered until a kind of resource exists, with its own pins, and code that reads it.

### S6. Judges
- **A judge configuration** is a skeleton thread like any other, compiled from a recipe whose prompt has purpose
  `judge`. The bench's lists of configurations hold both purposes today, and a judge configuration can be picked for a
  run, only to be refused when the trial is built. Take: configurations are listed and found by purpose, and the
  variation workflow lints a judge configuration as a judge, a skeleton with an engine (as `chatddx.facts.lints`
  already does for judges), not as a trial.
- **Its engine** is picked among the engines in the store, as a trial's is; the judge's requests are sent where that
  engine is served, cleared for the cases, since a judge prompt can hold case text (`docs/factors.md`, "Judge").
- **Its seeds** are written, and **its fill rule** is picked among those the code names (`FillOp`).
- **Judged views can't be scored yet** (`chatddx.scorers.scorer.score` refuses them). Writing judges is worth doing
  once the scoring pass sends judge requests; until then a researcher could write one and pick it in a view, and see
  "not yet".

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
8. **Scorers**: the published entry points and their schemas (S1), views, parameters and labels (S3, S4), and the
   code pin (S2).
9. **Judges**, once the scoring pass can send judge requests (S6).

## Questions for the user
1. **The code pin** (S2): keep pinning the running chatddx and re-pin after every deploy (C1), or pin a version of
   the scoring and tool code that developers raise when its behavior changes (C2, the take)?
2. **Free parameters** (S3): written where the code publishes a schema for them (the take)?
3. **Labels** (S4): a person's own, else the first written for the digest (the take), or the latest, whoever wrote it,
   as now?
4. **Taking one they already own.** When a person takes a shared expectation for a case they have their own for,
   should the bench leave theirs (the take, as the giftbag does), or replace it?
5. **Appendix edits and expectations.** Store the replacement cases and carry expectations only when confirmed (the
   take), or carry them along at once?
6. **A precondition on every edit** (A10), configurations included?
7. **Sharing further.** Only the owner shares (the take), or may a collaborator share too? And should a thread ever be
   handed to another owner?

Once 1–3 are settled, `docs/chatddx.md` ("Requirements", "Roles mentioned") and `docs/factors.md` ("Scorer", "Judge",
and "Code" for C2) get `AGENT:` suggestions for who writes what, where they disagree today.

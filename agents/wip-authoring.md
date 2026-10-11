# Authoring: work in progress

The writes the bench makes for a person beyond configurations, runs and scores: chunks, recipes, appendices and the
cases that order them, expectations, and what is said about a thread, from its name to whether it is deleted. They are
the bench's, since every edge writes for a person through it (agents/wip-bench.md, "Writes for the person"); the
portal is the first edge to need them (agents/wip-portal.md, "Below the UI", "Phases" 4 and 5).

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **Decided: what of a scorer and a judge researchers write** (see "Scorers and judges"), that scorers and tools pin
   a version of their code rather than the running chatddx (S2), that free parameters are written where the code
   publishes a schema (S3), and that labels belong to the edit they are written with (S4). Also decided: an
   expectation is carried to a replacement case only when confirmed (A4), only the owner shares (A9), and every edit
   names the head it was made on (A10), and a take keeps a person's own expectation, with replacing one a write of
   its own (A5). The rest are takes.
2. **Taking expectations is built** (phase 1): `Bench.take` and `Bench.take_from`, the giftbag keeping a person's own,
   the repl's `take`, and the API's `POST /api/takes` and `POST /api/threads/{thread}/takes` (agents/wip-bench.md,
   "Taking").
3. **Chunks and expectations are built** (phase 2): `Bench.new`, `fork_component` and `edit_component` with lints
   and languages, every edit naming its head (A10, configurations included), and the API's `POST /api/threads` and
   component forks and edits (agents/wip-bench.md, "Components"). The sample has a thread of every chunk kind now,
   and Swedish texts (agents/wip-sample-data.md, "Beyond the old inventory"). Two takes came with it: A7's language
   rule and A10's lock.
4. **What is said about a thread is built** (phase 3): `Bench.say`, the owner's one write of a thread's name,
   description, tags, collaborators and deletion, and the API's `PATCH` and `DELETE /api/threads/{id}`, with the
   person's own deleted threads listed and read by id (agents/wip-bench.md, "What is said about a thread").
5. **Following an origin is built** (phase 4): `Bench.proposal` and `Bench.follow`, and the API's
   `GET /api/threads/{id}/proposal` and `POST /api/threads/{id}/follows` (agents/wip-bench.md, "Following an
   origin").
6. **Recipes into configurations are built** (phase 5): `Bench.new` takes a recipe, and the API's `POST
   /api/threads` takes one in place of a component (agents/wip-bench.md, "Writes for the person").
7. **Appendices and cases are built** (phase 6): the appendix and case builders, a family's cases, replacement cases
   on an appendix's edit and for a late case, carrying an expectation over, and runs that name cases
   (agents/wip-bench.md, "Appendices and cases"). Phase 7, typed cases, comes next, with the portal's swift.
8. **One set of writes for every kind people author** (A1), with builders only where a kind binds to a family's
   vignette: appendices and cases (A2).
9. **No write refuses on a lint** (A6): what was written comes back with its lints. Refusals stay the components' and
   the catalog's.

## What is asked
| What | Principal author | Asked by | Written today |
| --- | --- | --- | --- |
| Chunks: instructions, few-shot, prompt, output, sampling, reasoning, passthrough, translations, toolset | researchers | `docs/chatddx.md`, "Requirements"; `docs/factors.md`, "Requests" | by curation, as the archive; forks of them by the giftbag |
| Recipes, made into configurations | researchers | `docs/chatddx.md`, "Requirements" | only a variation of a configuration the person sees, forked or edited (`Bench.fork`, `Bench.edit`) |
| Appendices, and the cases that order them | clinicians | `docs/factors.md`, "Case" and "Appendix" | nothing: a data set can't hold appendices (`docs/curation.md`, "What a data set can't hold yet") |
| Expectations, and taking one shared | clinicians | `docs/factors.md`, "Expectation"; `agents/wip-bench.md`, "What a person is scored against" | by curation, as the archive; forks of them by the giftbag; taken, by any person (phase 1) |
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

Built for the chunk kinds and expectations (`chatddx.bench.WRITTEN`). A scorer is refused until its phase, and not only
for want of a write: it names code to run, which the published list holds back (S1).

### A2. Builders where a kind binds to a vignette
- **An appendix** is built by the bench from a family and a text: bound to the family's current vignette, with its line
  endings normalized before it is digested, CRLF and CR to LF. `docs/factors.md` ("Appendix") asks this of the
  portal, since browsers send CRLF; in the bench every edge does it. It is then written as a new thread, or as an edit
  of one.
- **A case** is built from a family and appendices in order: the family's current vignette with those appendices, and
  stored. It writes nothing in the catalog, since a case belongs to its family by its vignette (`docs/catalog.md`,
  "Families and repairs"). An appendix bound to another vignette is refused by the case's own rule.

An expectation needs no builder: an edge has its case, its schema and its data.

Takes, built:
- **Appendices go through the shared writes** (`appendix` joins `WRITTEN`), so they are new, forked and edited as any
  kind, and the builder is what the edges call for a family and a text. Every appendix written is checked to be bound
  to the current vignette of a family the person sees, and its line endings made LF, whichever edge sent it.
- **A case is built of appendices the person sees**, held by a thread of theirs or shared with them.

### A3. A family's cases
A family stands for one case today: the one its current vignette makes alone, else the first that holds it. Once
appendices are written, a family has several, and what is run and scored is a case. Take: a family lists its cases,
the bare one first, and an edge picks one; the one it stands for today stays its default. Runs, the reach and
expectations take cases already.

Built: a family lists its cases at its current vignette only, and the API's runs name cases among those, beside
families and tags.

### A4. Editing an appendix
A new version of an appendix makes every case that holds the old one behind (`docs/catalog.md`, "What has moved on"),
and expectations are keyed by their case. Decided: the edit also stores each such case's replacement, the same
appendices with the new version in its place, so that the new cases are there to pick, but moves no expectation, since
an appendix can change the right answer (`docs/factors.md`, "Case"). Carrying an expectation to a replacement is a write
of its own, an edit of the expectation onto the new case with the same data, made only when a clinician confirms that it
still holds, as after a repair that changed a vignette's content (`docs/catalog.md`, "Repairing").

The same builder stores a late case's replacement, which `docs/catalog.md` ("Smaller issues") leaves to the portal.

Built. Takes: an appendix's edit replaces only the cases at its own vignette, since a case at an earlier one awaits a
repair's replacement instead; and carrying keeps to the expectation's family, onto any of its cases.

### A5. Taking expectations
Taking is forking: the person's own thread, starting from the shared one's head and forked from it, so a correction
made to the origin reaches them as a proposal (A8). Forking changes no digest, so the expectation scored against is the
same until either moves on.

For many at once, the bench takes, under one schema and in one transaction, an expectation for each of some cases or
families the person has none of their own for: what the giftbag does for the sample, for any person and from any
owner. Left out, and named in what it returns:
- a case they own one for already (see below);
- a case with shared ones from several owners, since nothing picks between owners.

What a take does with a case the person owns an expectation for already, and what each answer means for someone who
scores runs:
- **K. Keep theirs.** Taking only adds: a bulk take over a tag tops up the cases they have none for, and is safe to
  repeat, so taking the clinicians' expectations again after more cases were shared adds the new ones and changes
  nothing else. Nothing they scored against changes, so no run is left to score again. Corrections reach them through
  following (A8), where each is seen before it is taken. To use someone else's answer for a case they have their own
  for, they delete theirs first, or follow.
- **R. Replace theirs.** Taking switches: the shared expectation becomes theirs, whatever they had. A bulk take over a
  tag resets every case in it to the shared heads, their own corrections included, and every run scored against what
  it replaced is left to score again. It is also two writes in one: deleting their thread and forking the shared one,
  since an edit of theirs onto the shared head would keep the origin they forked first, and proposals would keep
  coming from it.
- **K, with replacing named.** Taking keeps theirs, and what it returns names each case it left; replacing one is a
  write of its own, per case, that deletes theirs and forks the shared one in one transaction.

Decided: K, with replacing named. A bulk write that can't destroy anything is safe to offer as one button, and the
one that can is a choice made case by case.

Beside it, the giftbag keeps a person's own expectation for a case and schema, as it keeps a fork they already have,
rather than fail `init-data` on the catalog's rule (agents/wip-bench.md, "What a person is scored against").

### A6. What was written comes back with its lints
Each write returns what it wrote and the lints of it, as findings: an expectation whose data fails its schema or can't
be checked against it, and whatever else the lints say of the component (`docs/factors.md`, "Lints"). Nothing new
refuses: the components' rules, `Store.add` and the catalog's rules still do.

### A7. Languages
A text's language goes with the write that makes the text, and the catalog checks it, as it checks curation's
(`Catalog.language`: text chunks and hand-written skeletons only). The bench doesn't carry the previous version's
language on its own. An edge offers it and the person keeps it or changes it, as `docs/catalog.md` ("Languages")
says. A fork that changes nothing keeps its language, being the same digest.

Take, built: a language is kept on the digest, and the latest wins, so a person giving one to a text someone else
holds too would change it for them, as labels did before S4. So the bench writes one only where the text has none,
and refuses one that differs from the text's own; the person writes another text, or leaves it. Correcting a wrong
language stays curation's for now, and what a person may correct is open: a text only their own threads hold, say.

### A8. Following an origin
Accepting the catalog's proposal for a fork the person owns: compiled when it is a recipe, then an edit with
`based_on` the origin's head (`docs/catalog.md`, "Forks"). Nothing is written without a proposal. It matters first for
taken expectations and the giftbag's forks, which otherwise never see the archive's corrections, and for forked
configurations.

Takes, built:
- **Only an origin the person sees is followed.** A deleted or unshared origin proposes nothing, since its head is no
  longer theirs to read, as "What has moved on" proposes no deleted thread.
- **Following always writes an edit**, based on the origin's head, even when the proposal is the fork's head already:
  otherwise the fork would keep being compared with its old base and keep proposing.
- **Any kind the person owns a fork of is followed**, the giftbag's tools included, since a proposal holds only the
  origin's head and the fork's own changes, which are stored already; nothing new comes from the person. That is how
  S2's re-pinned scorers and tools reach a person's forks.
- **A proposal is shown before it is followed**, with the digest following would keep, so an edge can tell a fork it
  wouldn't change.

### A9. What is said about a thread
A thread's name, description, tags and collaborators, and deleting or restoring it, are entries the bench writes on what
the person owns (`About.owned_by`), as `edit` already requires: a collaborator may fork a thread, but not edit, share or
delete it. Decided: only the owner shares. Sharing names a person by login. Restoring is held to the catalog's rules, so
restoring a second expectation of one case and schema is refused. Handing a thread over to another owner isn't offered.

What deleting hides stays the portal's question (`docs/catalog.md`, "Smaller issues"); the bench hides a deleted
thread from everything but its history and the runs that used it.

Takes, built:
- **One write says what is to hold**, any of the fields, the tags and collaborators each as the whole set, and only
  what changes is written, at once. A form shows the whole thread and sends it back; a write per field would ask the
  edge to tell what changed, and leave half a change when one of several fails.
- **The owner reads their deleted threads**, listed apart and by id with their history, which is what restoring
  needs; nothing else finds them.
- **Restoring comes first**, and nothing else is said of a thread that stays deleted.
- **Leaving a share isn't offered.** A collaborator can't take a shared thread out of what they see; the owner can.
  Open: whether a collaborator may withdraw themselves, which the catalog would hold as any other collaborator entry.

### A10. Decided: an edit names the head it was made on
Every edit names the head the person saw, configurations included, and the bench refuses it when the thread has moved
on since, with an error of its own that the API maps to 409. It answers "An edit has no precondition"
(agents/wip-api.md, "Open"). The repl's `save NAME`, which edits whichever configuration its name finds, names the head
it found.

Take, built: the catalog checks it (`check_head`, `MovedOn`), while every edit holds its thread's advisory lock, so
it holds with several writers without a rule in the database. The writer may not update the catalog's tables, which
`FOR UPDATE` asks for.

### A11. Who may write what
Ownership only, as now: a person makes new threads and writes on their own. Roles aren't checked. Z1 will map roles
to the kinds each one sees (agents/wip-identity.md, "Open"); the kinds each one authors can go beside it, clinicians
appendices, expectations and typed cases, researchers chunks and recipes, as a convenience for the portal's forms, not
a refusal (agents/wip-identity.md, "Authorization").

### A12. Recipes into configurations
A recipe the person makes, by the chunks' digests for each part, its purpose and its appendix layout, is compiled and
kept as a new configuration of their own with its compilation, as `fork` keeps one. It has no origin. An edge finds
the chunks by name through `Bench.chunk`.

Built, as A1's `new`. A judge-purpose recipe is made as any other, and stays a configuration among the rest until S6
lists configurations by purpose.

## Scorers and judges
Decided, for what a researcher writes and what they pick, with the code pin (S2), free parameters (S3) and labels
(S4):

| Part | Written, picked or shipped |
| --- | --- |
| A scorer's code and entry point | shipped: developers write them and ship them with the project |
| Its expectation schema | picked, among the shipped ones |
| Its views | written by researchers |
| Its free parameters | written by researchers, where the code publishes a schema for them (S3) |
| Its resources | picked |
| The labels of its views and resources | written by researchers, with the scorer version they name (S4) |
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
- **Labels them** in the same write, so the labels belong to the version they name, and renames a view by a new
  version of the same scorer (S4).
- **Sees its effect** at once: the scorer applies to the runs whose output its views reach (`Bench.scorers_for`), and
  every finished run is left to be scored under the new version (`Bench.outstanding`).
- **Writes a judge** as a configuration of purpose `judge`, with the variation workflow every configuration has, and
  a judge over it with an engine and seeds (S6).

### S1. The code publishes its entry points
The project keeps a list of the scoring entry points it ships. Each one publishes its version (S2) and its metrics,
each with a name, what it measures and a JSON Schema for its parameters, and optionally a schema for the parameters
every view shares. The
portal's pickers and forms read the list, the bench refuses a scorer that names anything else, and the scoring pass
runs nothing else. Today `chatddx.scorers.scorer.Metrics` publishes names only, and they are checked only when a run
is scored (`chatddx.scorers.scorer.function`).

Why it is a refusal and not a lint: the list is also a protection. `chatddx.core.rig.entry` imports whatever module an
entry point names, of any installed package, and calls it with a view's metric, the picked items and the parameters.
That was safe while only data sets named entry points; a scorer written over the API names its own. Checking that the
code is the running chatddx doesn't check which function in it runs. Tools name entry points the same way, and should
be held to a list of their own.

Packaging entry points would serve as the list (`docs/factors.md`, "Finding code through packaging entry points").

### S2. Decided: scorers and tools pin a version of their code (C2)
A scorer pins the running chatddx's distribution, version and revision today, and only that code is run
(`chatddx.core.rig.entry`). Every deploy changes the revision, so every scorer stops scoring until it is pinned again.
For the archive's scorers, running `init-data` again does that (`src/chatddx/curation/plan.py`); a researcher's own
scorer has nothing that does. A scorer pinned again is a new scorer, so every finished run is left to be scored again
under it, though nothing in the scoring changed. Tools have the same pin, so each deploy also changes every skeleton
that offers a tool, and every trial over one.

Decided: a scorer and a tool pin their entry point and the version of it the code publishes (S1), and its developers
raise that version when what it does changes, as a cleanup step, a split or a fill rule is named and versioned
(`docs/factors.md`, "Text cleanup"). The rejected option kept the pin and gave researchers a write that pins their
scorers again after each deploy.
- **What runs**: a scorer or a tool whose entry point the running code publishes at that version. Another is refused,
  as other code is refused today. Which chatddx scored or ran is still kept, in each score's and run's `rig`
  (`src/chatddx/ledger/score.py:ScoreStarted`, `src/chatddx/ledger/run.py:RunStarted`).
- **What a deploy changes**: nothing, unless it raises a version. Then the scorers and tools pinned to the earlier one
  are refused until they move on to the new one: the archive's when `init-data` runs again, a person's by following
  its origin (A8), or by an edit.
- **What it costs**: the `Scorer` and `Tool` schemas change, so their schema versions go up, and the store then refuses
  their earlier versions, with every skeleton, trial, scoring and record whose closure holds one (`docs/factors.md`,
  "Versions"). Before production, a store is rebuilt by loading its data sets again.
- **Lints**: "scorer code without a revision" (`docs/factors.md`, "Lints") no longer applies to scorers and tools,
  since they pin no revision. Whether a deploy sets one is seen in its records' `rig`.
- **Docs**: `docs/factors.md` ("Code", "Tool", "Scorer", "Lints") gets suggestions with the build.

### S3. Decided: free parameters, where the code publishes a schema
A view's parameters go to its metric, over the scorer's own (`scorer.params | view.params`,
`chatddx.scorers.scorer.score`). None of the shipped metrics reads any (`chatddx.scorers.patterns`), and nothing checks
them. Decided: they are written by researchers, as the views are, but only where the code publishes a schema for them
(S1): a view's, from its metric's schema, and the scorer's own only for code that publishes parameters its views share.
Where nothing is published, nothing is offered, so today a researcher sets none. A parameter the schema refuses is
refused by the write, as an unknown metric is, since the scorer could never score with it.

### S4. Decided: labels belong to the edit they are written with
A label names a view or a resource of one scorer digest, and the latest label wins, whoever wrote it
(`src/chatddx/store/migrations/0010-t0-catalog.sql`, `catalog.label`). Once researchers write labels, one who forks a
scorer without changing it, and so shares its digest, relabels it for everyone who sees it, the archive's included.

The user's suggestion: labels belong to the scorer version and are written once, with it, by whoever writes it. "The
scorer version" can be read two ways:
- **The component, by its digest.** A component records no writer (`factor.component` has no `by`), so "whoever writes
  it" would be whoever labels that digest first, and everyone who stores the same scorer afterwards, by forking it
  unchanged or by writing the same views, gets those labels. A view could never be renamed: its scorer is the same, so
  its digest is, and the digest's labels are written already. A typo stays. Curation couldn't load a data set that
  renames a view of an unchanged scorer, which it does today by writing a new label (`_Init.record`,
  `src/chatddx/curation/write.py`).
- **The edit, the version of a scorer thread.** An edit has a writer (`catalog.edit.by`), and every thread is its
  owner's. The labels are written in the same write as the edit, by whoever makes it, and never after. A fork is the
  forker's own edit, so it carries their labels, the origin's unless they give others. Renaming is a new edit of the
  same scorer: the thread's history shows it, and since the digest doesn't change, no scoring, score or run left to
  score changes with it. No one's labels change anyone else's, and no rule like the one for expectations is needed.

Decided: the edit. What it changes:
- **Storage**: a label names an edit of a scorer thread instead of a scorer digest, one per edit, part and position,
  written by the edit's writer: a migration at tier 0, and at tier 2 the position's check (as now), that the writer is
  the edit's, and that a label is written once.
- **Writing**: the catalog writes labels only with an edit. `create`, `edit` and `keep` take them for a scorer thread,
  `keep` counts an edit as unchanged only when both the scorer and its labels are the head's, and `Catalog.label` goes.
  Curation writes a data set's labels with the archive's edit, and a renamed view as a new edit of the same scorer.
- **Reading**: a scorer digest's labels are those of the latest edit that holds it among the threads the person sees,
  their own first, as `Bench.holder` picks a thread; for a digest that no thread's head holds any more, the latest edit
  in their history that does; else "view N". The reach and scoring read the head edit they have already.
- **Following an origin** (A8) carries the labels of whichever side's views the proposal keeps.
- **Docs**: `docs/catalog.md` ("Scorer labels") and `docs/catalog-api.md` get suggestions with the build.

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
1. **Taking**, built: taking expectations for cases or families, and the giftbag keeping a person's own; the repl's
   and the API's.
2. **Chunks and expectations**, built: new, fork and edit for the chunk kinds and expectations, with a language for
   texts, lints returned, kinds checked, and an edit's head.
3. **What is said about a thread**, built: name, description, tags, collaborators, deleting and restoring.
4. **Following an origin**, built.
5. **Recipes into configurations**, built.
6. **Appendices and cases**, built: the builders, a family's cases, replacement cases, and carrying an expectation
   over.
7. **Typed cases**, with the portal's swift (agents/wip-portal.md, "Typed cases", and its phase 4).
8. **Scorers**: the published entry points, their versions and their schemas (S1, S2), the code pin moved to them,
   views, parameters (S3), and labels on edits (S4).
9. **Judges**, once the scoring pass can send judge requests (S6).

## Questions for the user
None left open. Handing a thread over to another owner isn't offered (A9), as a take.

`docs/chatddx.md` ("Roles mentioned", "Requirements") and `docs/factors.md` ("Scorer", "Judge") now say who writes
what. The code pin (S2) and labels (S4) get their suggestions with the build, since they describe code that isn't
written yet.

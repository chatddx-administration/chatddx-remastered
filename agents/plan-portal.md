# The portal: plan

The portal is the bench's web edge, beside the repl and the API (`docs/modules/bench.md`): HTML rendered on the server
from the bench, with Svelte islands where a page needs a round trip. Its pages are built; its plans were itemized into
`docs/backlog.md` and retired (`git show f8967c3:agents/wip-portal.md` holds the last of them). This plan starts again
from the Library. "Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this

1. **Decided: the Library is the data model, shown.** People come to it to learn the structure underneath and to have
   total control. Each thread maps to a section whose fields are shown straight up, edited or read-only. Where a natural
   implementation and the user experience pull apart, the natural implementation wins, and an error is reported simply
   and directly when that keeps the implementation simple.
2. **Decided: clinicians and researchers manage their whole configuration space from the Library**, also where another
   page does it more practically. The other pages stay, each shaped by a task: a case typed (Home), a case reviewed
   (Review), a configuration translated (Translate), its lineage compared (Refine).
3. **Decided: one interface for what is said and for versions**, reused by every thread: its name, description, tags and
   collaborators, deleting and restoring, and stepping through its versions.
4. **Decided: in the Library, owners unshare**, and collaborators leave a share. Built for every thread (see "Steps",
   1); a family waits for its step, and a run is said of through its trial.
5. **Take: configuration is what is kept, an action is what is set going** (see "Configuration and actions").
6. **Decided: the Library sets the norms, and the other pages adjust.** Refine and the Library supersede
   `/configurations`, and it and `/translate` move out of the way where they are in the Library's.
7. **Decided: a run is composed as a trial, a thread of its own, and queueing it is an action** (see "Configuration and
   actions", (b)).
8. **Decided: the Library steps through versions by link**; the other pages step through theirs by island.
9. **Decided: fields one level deep, each edited or read-only.** A related component is picked, never edited in place,
   as the data model has it.

## The configuration space

What clinicians and researchers author, by where it is kept. Principal authors are `docs/glossary.md`'s ("Roles"); what
a person writes is `docs/modules/bench.md`'s ("Writes for the person").

### Components kept as threads

A thread is a component's versions (`docs/modules/catalog.md`, "Threads and edits"); the bench names its kinds by word
(`src/chatddx/bench/model.py:KINDS`) and writes some of them in a person's name (`WRITTEN`).

| Word                                                       | Author                 | What a person writes                                                                                                                                                                                                                                   |
| ---------------------------------------------------------- | ---------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| appendix                                                   | clinician              | new, a version, a fork; a new version stores again each case that held the old one (`docs/modules/bench.md`, "Appendices and cases")                                                                                                                   |
| expectation                                                | clinician              | new, a version, a fork; taken from one shared, carried onto another case of its family; one live per case and schema per owner (`docs/modules/catalog.md`, "Owners")                                                                                   |
| instructions, few_shot, prompt, output, toolset            | researcher             | new, a version, a fork, each with the language of its text (`docs/modules/catalog.md`, "Languages")                                                                                                                                                    |
| sampling, reasoning, passthrough                           | researcher             | new, a version, a fork; a level or the recommended sampling are intents the facts resolve as a recipe compiles                                                                                                                                         |
| translations                                               | researcher, translator | new, a version, a fork; into languages, with none of its own                                                                                                                                                                                           |
| configuration                                              | researcher             | a skeleton with the recipe it was compiled from: made from a recipe, or a variation kept as a fork or a version; following its origin, or its model and facts (`docs/modules/bench.md`, "Configurations", "Following an origin" and "Following facts") |
| scorer                                                     | researcher             | new, a version, a fork: its views, free parameters, resources and labels, over code and an expectation schema it picks; labels are written with each edit (`docs/modules/catalog.md`, "Scorer labels")                                                 |
| judge                                                      | researcher             | new, a version, a fork: a judge configuration, a model by its handle, and seeds                                                                                                                                                                        |
| tool, expectation_schema, canary_set, model, engine, facts | developers and ops     | nothing: data sets and facts files write them, and a person forks none of them                                                                                                                                                                         |

### Cases and families

A case has no thread: a vignette and its appendices, named through its family (`docs/modules/catalog.md`, "Families and
repairs"). A clinician types a case, which keeps the text in the store and writes its case and a family of their own
(`docs/modules/bench.md`, "Typed cases"); builds cases of a family's appendices; and stores a replacement for a case a
repair left behind. A family's bindings are its versions, where its vignette is at each repair, and repairs are
curation's (`docs/modules/curation.md`). The vignette is sensitive, and has a place of its own at each edge
(`docs/modules/api.md`, "Sensitive content").

### What is said

Entries are said about a thread, a family, a run or a score (`docs/modules/catalog.md`, "Entries";
`src/chatddx/catalog/model.py:EntryField`): a name, a description, tags, an owner, collaborators and whether it is
deleted; a family's language; and what a run ran, which a start writes. Beside them, the labels of a scorer's edit and
the language of a text, which is kept on the component. All of it is append-only, so what was said before is history the
catalog keeps.

### Composed, not kept

- **The variation**: a configuration's edit with parts replaced, a plain value nothing stores until it is kept
  (`docs/modules/bench.md`, "The variation being tried").
- **The trial**: the skeleton, the engine of the handle, the cases, the cleanup and the seeds, built and stored as a run
  starts (`src/chatddx/factors/trial.py:Trial`; `src/chatddx/bench/runs.py:start`). The glossary makes researchers its
  authors, and the catalog lets every kind but cases and compilations have threads, but the bench has no word for it.
- **The execution and the canary set**: the endpoint's, with a concurrency and an order a start may give
  (`src/chatddx/api/schemas.py:NewRun`; `docs/backlog.md`, "Execution settings as a component").
- **The scoring**: built when a run is scored, from the person's own expectations and the scorer, rather than written by
  hand (`docs/modules/bench.md`, "Writes for the person"). It is derived, not configured.

### Not theirs

Tools, expectation schemas, canary sets, models, engines and facts are developers' and ops' (see "Components kept as
threads"); the inventory and the World are ops'; people and roles are an admin's (`docs/backlog.md`, "Administering
people"). The archive owns what data sets load and shares it with everyone it loads for (`docs/modules/curation.md`,
"The archive"), so a person reads the archive's threads and forks what they want to change.

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

A start writes entries too, the run's name and what it varied (`docs/modules/catalog.md`, "What a run ran"): the
action's record of itself, not configuration.

The line is unclear in one place, **composing a run**. It is configuration by the data model, a trial a researcher
authors, but it is kept only by starting. Options:

- **(a)** As now: a run is composed where it starts, on a configuration's page and on Review, and the Library shows
  trials only through their runs.
- **(b)** Trials as threads, as the catalog allows: a run is composed in the Library as a trial, whose fields are its
  skeleton, its engine by handle, cases, cleanup and seeds, and starting is queueing that trial's head under an
  execution. A trial is in one language, as it names one skeleton, so a start over several languages stays a start of
  several trials. What has moved on already covers a trial's skeleton, engine and cases (`docs/modules/catalog.md`,
  "What has moved on").
- **(c)** A draft run held in the page's address, as the variation is, and kept nowhere.

Decided: (b). It is the reflection of the data model, and the one that makes composing a run configuration and queueing
it an action. It comes after the steps that need no new kind (see "Steps", 6).

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

### Against the plan

Each with what was decided of it.

1. **Configurations are outside the Library.** Their tab and their thread's page lead to `/configurations`, whose page
   has no form for what is said and none to delete. So an owner can't rename, describe, tag, share, unshare or delete a
   configuration in the portal, though `POST /threads/{id}/said` and `/delete` take a configuration as any thread
   (checked by hand). Its name changes only by forking: the variation's island saves a new name as a fork. A deleted
   configuration's link ends in 404, since its page looks at a variation of it, which a deleted thread has none of, so
   it is restored only by the Library's button; and a deleted judge configuration isn't listed there, as the listing
   asks for generation configurations (`src/chatddx/api/threads.py:threads`). Deleting unsuccessful configurations is
   half of the intended workflow (`docs/chatddx.md`, "Intended evolution of configurations").

   Decided: Refine and the Library supersede `/configurations`, which moves out of the way where it is in the way.
   Built: configurations are in the Library (see "Steps", 1); `/configurations` still varies and runs them.

2. **Nothing is said of a family.** `Bench.say` takes a thread only (`src/chatddx/bench/saying.py:say`); a typed case's
   family gets its name and language once, as it is typed (`src/chatddx/bench/cases.py:type_case`), and the API has no
   route for it. So nobody signed in renames, tags, shares, unshares or deletes a family, and the archive's stay with
   everyone they were shared with.

   Decided: a family is a case in the Library, said of, left and deleted as a thread is (see "Cases"). Built (see
   "Steps", 5).

3. **Nothing is said of a run or a score** after a run starts: no tags, though the catalog takes them, and a run is its
   owner's alone, so sharing one would show the collaborator nothing (`docs/modules/bench.md`, "What a person sees").

   Decided: (b) (see "Configuration and actions"). A run is composed as a trial, a thread said of as any other.

4. **A collaborator can't leave a share**, only its owner can take it out of what they see, so what the archive shares
   stays in everyone's lists. It was the backlog's, decided there: a collaborator may withdraw themselves, as an entry
   the catalog holds like any other.

   Decided: built with this. Built (see "Steps", 1).

5. **Versions are stepped through two ways**: by the island on a thread's page, and on the server by `head` on a
   configuration's page, where the variation depends on it. The island keeps no address, so a version can't be linked.
   Nothing makes an earlier version the latest again, though reverting is an edit like any other
   (`docs/modules/catalog.md`, "Threads and edits"): an editor starts from the head. A family's bindings, its versions,
   aren't shown, nor the history of what was said.

   Decided: the Library steps through versions by link, and the other pages by island. Built (see "Steps", 2).

6. **Fields one level deep.** A reference shows its title, and nested values show as JSON.

   Decided: that is the point. A related component is picked, not edited in place, as the data model has it. The editors
   that write one in place, a new judge written in a scorer's view, belong to the other pages. Built (see "Steps", 3).

7. **Read-only kinds offer a fork the bench refuses**: **Fork it as it is** on a tool's page answers 422, "a person
   doesn't write tool components" (checked by hand).

   Decided: a field is edited or read-only, so a read-only kind's section offers no fork. Built (see "Steps", 3).

8. **Begun elsewhere, or nowhere.** Appendices, expectations, translations and configurations aren't begun from the
   Library, and a translations chunk's page edits the languages it has, a new one only on `/translate`. Storing a case's
   replacement and taking expectations for many cases at once, which the bench and the API do (`docs/modules/bench.md`,
   "Appendices and cases" and "Taking"), aren't offered by any page.

   Decided: the Library sets the norms, and `/translate` moves out of the way where it takes the Library's place. Built
   for every kind a person writes (see "Steps", 4), and a case's replacement and taking for many cases on the case tab
   and a case's section (see "Steps", 5).

9. **No write for some of what is said**: handing a thread over, an owner entry, and correcting a text's language
   (`docs/backlog.md`, "Languages", decided for a text only one's own threads hold).

   Open: decided and built when it is reached, with the landscape and options then (see "Steps", 7).

10. **A silent no-op**: an emptied description is sent as none, which the bench takes as "no change", since it never
    takes a description away (`docs/modules/bench.md`, "What is said about a thread"); the form says nothing.

    Decided: true to the data model, an emptied description takes the description away, as an emptied name takes the
    name away: a removal entry, so that "none" is one state, not `None` beside `""`. Built (see "Steps", 1).

What holds already: a refused form answers with a page of its status, code and the bench's sentence
(`src/chatddx/portal/pages.py:paged`), and an editor says a refusal in place.

## Steps

Take, in this order, each a unit of its own. Steps 5 to 7 start with their landscape and options.

1. **What is said of every thread, and leaving a share.** Configurations listed in the Library under their word, of both
   purposes, deleted ones included, and shown at `/threads/{id}` as any thread, following their facts beside following
   their origin, rather than leading to `/configurations`. One form for what is said, as now, for every thread; for a
   collaborator, **Leave**, an entry they write that takes the thread out of what they see; an emptied description taken
   away. `docs/modules/bench.md` is solidified ("What is said about a thread": a collaborator "may fork it, but not
   rename, share or delete it"), so leaving is a suggestion there.

   Built:
   - **The Library lists configurations** under their word, generation and judge alike, with their purpose, and its
     deleted threads of both (`src/chatddx/portal/threads.py:library`); its tab no longer leads to `/configurations`.
   - **A configuration's thread page** is the Library's like any thread's: what is said of it and deleting it, forking
     it as it is, following its origin and its facts, and a link to its page to try variations of it
     (`src/chatddx/portal/templates/thread.html`). A deleted one is read and restored there.
   - **Leaving**: `Bench.leave` writes the collaborator's own entry taking them out of the share, refused as "not found"
     to anyone not collaborating on it (`src/chatddx/bench/saying.py:leave`); the thread's page gives a collaborator
     **Leave it** (`POST /threads/{id}/leave`), which leads back to the kind's list. The API leaves too,
     `POST /api/threads/{id}/leave`, answered 204 as the thread is no longer the collaborator's to read
     (`src/chatddx/api/threads.py:leave`).
   - **A description is taken away** as a name is, by a removal entry, and is never empty
     (`src/chatddx/catalog/model.py:Entry._shape`): `Bench.say` takes `None` for none and refuses `""`, the form sends
     an emptied one as none, and `PATCH /api/threads/{id}` takes `null`, where it refused it. The database repeats it in
     `src/chatddx/store/migrations/0027-t2-catalog-description.sql`, `NOT VALID`, as a store may hold an empty one the
     API wrote before.
   - **Docs**: applied in `docs/modules/bench.md` and `docs/migrations.md`; an `AGENT: amend` suggestion in
     `docs/modules/api.md` ("What is said about a thread") for the API's leaving, and its stamp pending in
     `docs/surfaces/api.md`.
   - **Tests**: `src/chatddx/bench/test/test_said.py`, `src/chatddx/api/test/test_said.py`,
     `src/chatddx/store/test/test_catalog.py` (an old store's empty description migrates),
     `src/chatddx/portal/test/test_library.py` and `src/chatddx/portal/test/test_varying.py`.

   What it leaves:
   - **The repl doesn't leave**, as it doesn't reach every write (`docs/backlog.md`, "The repl's reach").
   - **A configuration isn't begun from the Library** (step 4, built), and a read-only kind still offers a fork (step 3,
     built).
   - **Curation keeps a description a data set drops**, though it drops tags a data set drops
     (`src/chatddx/curation/write.py`); it could take it away now.

2. **Versions by link.** `/threads/{id}` shows the version its address names, rendered on the server, with what it
   changed; its owner makes an earlier version the latest, as an edit. The thread island leaves the Library.

   Built:
   - **A version by its address**, `/threads/{id}?version=N`, counted from 1 as "Version N of M" says, the latest
     without one; one the thread doesn't have is "not found", saying how many it has
     (`src/chatddx/portal/threads.py:thread_page`). The page draws ◀ ▶, the version's fields one level deep, a reference
     by its title and digest, what it changed from the one before, and every version as a link.
   - **What it changed** is worked out on the server, path by path and a text word by word
     (`src/chatddx/portal/changes.py:changes`), as the island's `frontend/src/lib/thread/diff.ts` did, which Review and
     Translate keep.
   - **Made the latest**: on an earlier version, its owner gets **Make it the latest** (`POST /threads/{id}/revert`), an
     edit of the head holding that version: its component, a configuration's variation of that edit, and a scorer's
     labels as that edit wrote them. A head that has moved on since is 409.
   - **The editor** is the only island left on the page, mounted on the latest version alone
     (`frontend/src/lib/thread/Editor.svelte`); `Thread.svelte` and `Holds.svelte` are gone.
   - **Tests**: `src/chatddx/portal/test/test_library.py` (by link, out of range, made the latest for a chunk, a
     configuration and a scorer's labels, someone else's refused), `src/chatddx/portal/test/test_changes.py`.

   What it leaves:
   - **A fork starts from the head**, whichever version is shown.
   - **Configurations keep `head` on `/configurations/{id}`** for the variation, until step 8.

3. **Fields, edited or read-only.** A section's fields one level deep: the owner's edited, everyone else's read-only,
   and a read-only kind's read-only for all, with no fork. A reference is picked from what the person sees of its kind.
   A configuration's fields are its recipe's parts, picked, and its skeleton's fields read-only.

   Decided: one form per kind, drawn from its JSON Schema, a field per property and a picker per reference, in place of
   the editors per kind, which stay on the other pages.

   Built:
   - **Drawn on the server, sent as a plain form**, as the Library steps through versions by link: the latest version's
     fields are its owner's form, `POST /threads/{id}/edit`, and every other version's and everyone else's are read
     (`src/chatddx/portal/fields.py`, `src/chatddx/portal/templates/fields.html`). A refusal is answered on the error
     page, a moved-on head with 409.
   - **A field's shape is its schema's** (`src/chatddx/portal/fields.py:Field`): a reference (`x-kind`) a picker of the
     threads of its kind the person sees, their own first, by head digest, the value held offered beside them; a list of
     references a picker a line, in order, the last adding one; an enum a select; a text a textarea; a text or anything
     else a textarea read as text or as JSON, as its own select says; anything else JSON. Nested values are JSON, as
     fields are one level deep.
   - **What isn't the component's but is kept with it**: a text's language, and a scorer's labels as JSON, by position.
   - **A configuration** is its skeleton's fields, read-only, and its recipe's, the parts picked and saved as a version
     with those parts replaced; the purpose and the appendix layout are read-only, as a variation replaces neither. A
     hand-written one has no recipe and nothing to pick.
   - **Its findings**: what the lints say of the version shown, a written kind's, and why the bench refuses it as it is
     held, as a judge whose model is behind its handle.
   - **A read-only kind** offers no form and no fork.
   - **The thread island is gone**: `Editor.svelte`, and `TranslationsEditor.svelte`, which only the thread page used.
     The editors the begun pages, a family's page and Review mount stay.
   - **Tests**: `src/chatddx/portal/test/test_library.py`, a form sent as it is writes nothing for every written kind
     alice holds, and each kind's edits; `test_clinicians.py` and `test_translating.py`; two browser tests that edited a
     judge and a scorer through their editors are now the library's tests, and one that edited a prompt sends the form
     (`src/chatddx/portal/test/helpers.py:submitted` reads a form as a browser sends it).

   What it leaves:
   - **No check as it is typed**: the findings are the saved version's.
   - **A configuration has no findings here**: its look is its page's, until step 8.
   - **Begun pages keep the editors** (step 4, built: they are gone).

4. **Begun from the Library**: each kind a person writes, configurations from a recipe and translations included.
   `/configurations` and `/translate` give up what the Library takes.

   Built:
   - **Every kind a person writes is begun the same way**, `/library/new?kind=WORD`: the configuration, the nine chunks,
     appendices, expectations, scorers and judges, each the fields of its kind as step 3 draws them, from its schema's
     defaults, a reference picked from nothing ("pick one" where it is required), with a name, a text's language and a
     scorer's labels; `POST /library/new?kind=WORD` writes it (`src/chatddx/portal/threads.py:writing`). A configuration
     is begun as its recipe, the purpose and the appendix layout among its fields. A read-only kind isn't begun.
   - **`/configurations` gives up its recipe's island** for a link to the Library's; `/translate` keeps its own way to a
     translations chunk, beside a configuration, as nothing of it is the Library's place.
   - **What only the begun pages used is gone**: the recipe island, `ChunkEditor` and its forms, `SettingsTable`,
     `ScorerEditor`, `frontend/src/lib/editors/chunks.ts` and `recipe.ts`, and the portal's props for them. The island a
     family's page mounts is `frontend/src/islands/family.ts`, its expectation editor alone.
   - **Tests**: `src/chatddx/portal/test/test_library.py`, every kind offered and read-only ones not, and a sampling, an
     instruction with its language, a judge, a scorer with its labels, an appendix, an expectation refused as a second
     of its case and schema, and a configuration from a recipe, written from nothing; the browser test of a researcher's
     chunks writes its sampling and its configuration in the Library.

   What it leaves:
   - **An appendix's vignette is typed as JSON**, as nothing picks a vignette: a family's section can begin one (step 5,
     built: a case's section begins one with its vignette given).

5. **Families**: what is said of a family, its bindings as its versions, its cases, appendices and expectations, a
   case's replacement and taking for many cases. The landscape and the options are under "Cases".

   Decided: the takes under "Cases", "Options".

   Built:
   - **The bench says of a subject, as the catalog notes one**: `Bench.say` and `Bench.leave` take the catalog's
     `Subject`, a thread or a family, rather than a pair of each, since what is said of either is the same entries
     (`src/chatddx/bench/saying.py`). Only naming it in a refusal, restoring an expectation thread and a family's
     language differ, and the catalog refuses a language for any other subject. A language is replaced, never taken
     away. A person's own deleted families are listed apart and found by id (`src/chatddx/bench/seen.py:Seen.families`,
     `Seen.family`).
   - **The API keeps its word, families**: `PATCH /api/families/{id}` says of one, its language too, and
     `POST /api/families/{id}/leave` leaves it, answered 204; `GET /api/families?deleted=true` lists one's own deleted
     ones, and a family's detail says whether it is deleted (`src/chatddx/api/families.py`). Both PATCH routes say
     through one helper (`src/chatddx/api/threads.py:said`), what is unset left as it is.
   - **The case tab**, `/library?kind=case`, lists the cases a person sees by their families, their own first, by tag,
     and says that none is begun there; it takes the expectations shared with them for the picked ones under a schema,
     from an owner or any, and shows what became of each (`POST /library/takes`). A deleted case is among "Your
     deleted", with **Restore**, on every tab (`src/chatddx/portal/threads.py:library`).
   - **A case's section**, `/cases/{id}` (`src/chatddx/portal/cases.py:case_page`,
     `src/chatddx/portal/templates/case.html`): about it, with links to Review and to its vignette's page; its bindings
     as its versions by link, each its vignette's source, id and fingerprint whole, who bound it and when, and what it
     changed; its cases at that binding, each titled, by digest, with its appendices linked to their threads, and at the
     current binding its expectations under each schema, the person's own, the one picked and those shared with them,
     linked, and **write yours** where it isn't theirs; at an earlier binding, each case's replacement, stored or
     **Store its replacement**. At the current binding it builds a case of the appendices written for its vignette,
     picked one a line, and begins an appendix of its vignette. Its owner says of it, deletes and restores it, and a
     collaborator leaves it. Its vignette's text is on `/cases/{id}/vignette` alone.
   - **A begun page takes fields given in its link**, `f.NAME=VALUE`, read-only, and keeps them through its form
     (`src/chatddx/portal/fields.py:fresh`): an appendix begun with its vignette given, an expectation with its case and
     its schema. A field the kind doesn't have is refused.
   - **`/families` and `/families/{id}` are gone**, with the island that mounted an expectation editor there; the nav
     loses Families, and Review and the variation island link to `/cases/{id}`.
   - **Docs**: `AGENT: amend` suggestions in `docs/modules/bench.md` ("What a person sees", "What is said about a
     thread") and `docs/modules/api.md` ("What is said about a thread"); their stamps pending in
     `docs/surfaces/bench.md` and `docs/surfaces/api.md`.
   - **Tests**: `src/chatddx/bench/test/test_said.py`, `src/chatddx/api/test/test_said.py`,
     `src/chatddx/api/test/test_families.py`, `src/chatddx/portal/test/test_clinicians.py` (begun of a case, built,
     versions and a replacement stored, said of, left, taken for many), `test_reading.py` (the tab, and no vignette in a
     section), `test_reviewing.py`; the browser test of a clinician's appendix, case and expectation goes through the
     Library.

   What it leaves:
   - **An expectation is written as JSON** in the Library; the form drawn from its schema is Review's.
   - **An earlier binding's cases show no expectations**, only their replacements.
   - **Correcting a case's language changes what its next runs send**, and the form says so, nothing more.
   - **The repl doesn't say of a family**, as it doesn't leave a thread (`docs/backlog.md`, "The repl's reach").
   - **The case tab comes last** among the kinds, as it isn't a thread's word.

6. **Trials as threads**: the bench's word for a trial; its fields, a configuration's version, a handle, cases, cleanup
   and seeds, picked; where it is queued and under what execution; and a start over several languages. The landscape and
   the options are under "Trials".

   Decided: every option under "Trials", as it says.

   Built:
   - **The bench writes trials** (`src/chatddx/bench/model.py:KINDS`, `WRITTEN`): new, forked and edited as any
     component, and checked. As one is written, its skeleton is carried into its cases' language: the configuration it
     holds compiled into that language through its translations, against the facts its compilation pinned, the
     compilation kept, as a start carries a variation (`src/chatddx/bench/components.py:_carried`). A trial already in
     its cases' language is held as it is, so a form sent back writes nothing. Cases in several languages are refused,
     as are a language the translations don't go into and cases the person doesn't see.
   - **Trials' versions start as one start** (`Bench.start_trials`, `POST /api/runs/trials`): a run each, in the order
     given, at the endpoint serving its engine, under its execution and canary set, the concurrency and the order given
     over it (`src/chatddx/factors/trial.py:Execution.overlaid`, which the API's start of a variation now uses too),
     named by its trial, the later runs `with` the first, in one transaction. A trial whose engine no endpoint serves is
     refused, its handle to be followed. The sources' cleanup steps for cases are the bench's to say (`Seen.cleanup`).
   - **The trial tab** lists the person's trials, picked to run together on the run page. **The case tab** begins a
     trial of the picked cases: given read-only by their families, its seed drawn and its cases' sources' cleanup steps
     (`src/chatddx/portal/threads.py:beginning`).
   - **A trial's section**: its skeleton picked among generation configurations, and the one held in its cases' language
     shown as its configuration in it, "lines-guided, in sv"; its engine by its model's handle, an earlier one as
     "qwen3-8b-awq, an earlier engine" (`src/chatddx/portal/fields.py:choices`); its cases one a line; its cleanup one
     step a line, a select each (a list of choices drawn as a list of references is); its seeds as JSON. Read-only, a
     list of references shows each by its title. **Its runs**, of each version, and **Run it**.
   - **The run page**, `/runs/new?trial=ID…` (`src/chatddx/portal/runs.py:beginning`): each trial with a version to
     pick, where its engine is served and that endpoint's execution, or why it can't run; the concurrency, the order and
     scoring; it starts and queues them and leads to the first run, whose page links its trial.
   - **Docs**: `AGENT: amend` and `add` suggestions in `docs/modules/bench.md` ("Writes for the person", a new "Trials",
     "Runs and scores"), `docs/modules/api.md` ("Starting one"); stamps pending in `docs/surfaces/bench.md`, `api.md`
     and `factors.md`, and `docs/comments/bench.md`.
   - **Tests**: `src/chatddx/bench/test/test_trials.py`, `src/chatddx/api/test/test_trials.py`,
     `src/chatddx/portal/test/test_trials.py`, and a browser test that begins a trial on the case tab and runs it.

   What it leaves:
   - **What has moved on isn't shown on a trial's section**, nor followed: its engine is followed by picking its handle
     again, and a translated skeleton by picking its configuration again. The catalog's `behind` doesn't follow a
     translated skeleton's compilation to its configuration, as nothing reads it for a trial yet.
   - **A trial's items aren't counted against `settings.ITEMS_PER_RUN` as it is written**, only as it starts.
   - **The run page shows no canary set**: the endpoint's is sent, as a start of a variation sends it.
   - **The places that start a variation** keep no trial, until step 8 (decided).

7. **Handing over, and a text's language corrected.**
8. **`/configurations` retired**, once the Library picks a configuration's parts and keeps them, trials run them, and
   Refine compares them.

## Cases

The landscape for step 5, and its options. A family is the catalog's handle on a vignette; to a person it is a case, as
the bench and the repl say it ("no case 12 for alice"), and the Library says so too.

### What holds

- **A case** is a component: a vignette, as its source, id and fingerprint, and the appendices sent with it, in order
  (`src/chatddx/factors/cases.py:Case`). It has no thread: a change of appendices makes another case.
- **A family** is the handle on one vignette through renames and changes at its source (`docs/modules/catalog.md`,
  "Families and repairs"), and stands for its case, the one its vignette makes alone (`docs/modules/bench.md`, "What a
  person sees"). What is said of it are entries, as of a thread: a name, a description, tags, an owner, collaborators
  and whether it is deleted; and the vignette's language, as the one subject that takes one. Its versions are its
  bindings, where its vignette is, and its cases are the components bound to that vignette, each titled by its name
  alone or "NAME with APPENDIX, …" (:Case title).
- **Who owns which**: the archive owns every family a data set loads and shares it with everyone it loads for
  (`docs/modules/curation.md`, "The archive"); a person owns the family of a case they type
  (`src/chatddx/bench/cases.py:type_case`). Nobody signs in as the archive, so most cases a person sees are shared with
  them, and the ones they own are typed.
- **What is written of a family**: a typed case writes its family's name and language once, and curation writes the
  archive's entries and its repairs (`src/chatddx/curation/write.py`). `Bench.say` and `Bench.leave` take a thread only.
  So nobody signed in renames, describes, tags, shares, unshares, deletes or leaves a case, nor corrects its language.
- **Its bindings** are all kept (`src/chatddx/store/catalog.py:Rows.bindings`), the latest current. A repair adds one,
  builds each stored case anew at the new place and moves the appendix threads whose heads were at the old one, and on a
  rename the expectation threads too (`docs/modules/catalog.md`, "Repairing"); repairs are curation's commands. Nothing
  shows the bindings.
- **Its cases**: the bench lists those at its current vignette only (`src/chatddx/bench/seen.py:Seen.family`). A case
  left at an earlier one is reached through what has moved on, and the bench stores its replacement when asked
  (`src/chatddx/bench/cases.py:replacement`), which no page offers. A person builds a case of the appendices they see at
  the vignette (`src/chatddx/bench/cases.py:case`).
- **Its expectations**: under each expectation schema, a case has the person's own expectation, or several to choose
  from, and those shared with them to take, one at a time or for many cases at once (`Bench.take_from`, `Bench.take`;
  the latter on no page).
- **Its vignette** is sensitive, and has a place of its own at each edge (`docs/modules/api.md`, "Sensitive content"),
  which needs handling of its own. Its fingerprint is in every case's component, which `GET /api/components/{digest}`
  serves already.
- **Its pages**: `/families` lists them by tag. `/families/{id}` shows what is said of one, read-only, writes appendices
  and builds cases of them, and offers each case's expectations to write in place, take or carry. Review,
  `/review/{family}`, does all of that around one case at a time, beside its vignette, its runs and a scorer's composer.

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

The takes in bold, decided as put and built (see "Steps", 5). What changed since the options were first put, in
"Reconsidered".

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

What it asks beneath: the bench saying of, leaving and deleting a family, and listing a person's deleted families apart;
suggestions in `docs/modules/bench.md` ("What a person sees", "What is said about a thread") and `docs/modules/api.md`;
and stamps.

### Reconsidered

The user's: the Library holds what isn't sensitive, so it shows a vignette as a case represents it and never its text,
which pages that show it handle on their own; and a family is a case in the interface.

- **Fell away**: a family page linked from the Library, or kept beside a Library section (1 (b), (c)); a fingerprint
  short or left out (3 (b), (c)), as it is the representation; and a case typed in the Library (6 (a)), as it writes a
  vignette.
- **Added**: the section sketched above; where the vignette's own place goes (7); and the API's word (8).
- **Changed**: the kind, its tab and its address are case's, not family's (1), and taking for many is the case tab's
  (5).

## Trials

The landscape for step 6, and its options. A trial is what a run runs; to a researcher it is what they compose, and the
start record says how it is sent.

### What holds

- **A trial** is a component: a generation skeleton, compiled and so in one language; an engine; one case or more,
  sorted; cleanup steps; and one seed or more, a replicate each (`src/chatddx/factors/trial.py:Trial`). A judge's
  skeleton is refused, and its lints say when its cases are in another language than its skeleton (`language.mixed`),
  when either is unknown, and when its engine serves another model than its skeleton is worked out for
  (`trial.engine_unmatched`).
- **The catalog takes trial threads already**: the kind among `THREAD_KINDS` and the database's check, a title,
  "SKELETON on ENGINE, N cases, N seeds" (`src/chatddx/catalog/titles.py:describe`), its skeleton's language, and what
  has moved on over its skeleton, its engine, its cases and their appendices, and a case a repair left behind
  (`src/chatddx/catalog/threads.py:behind`). Only tests write one: the bench has no word for it
  (`src/chatddx/bench/model.py:KINDS`, `WRITTEN`), so the API refuses the word and `Bench.new` the kind.
- **What a start composes is a level above** (`src/chatddx/bench/runs.py:start`, `POST /api/runs`): a variation, a
  configuration's edit with parts replaced; its model's handle, or one named for a hand-written configuration; cases by
  families, tags or digests; seeds, or replicates drawn; cleanup, the cases' sources' unless given; and the endpoint's
  execution, its concurrency and order given. The bench makes a trial for each language the cases are sent in, compiling
  the configuration into the others and keeping those compilations, names each run by the variation's label, says what
  it varied, and ties the later runs to the first (`with`).
- **Outside the trial**: the execution, the canary set (always the endpoint's), the phases verified and the endpoint are
  the start record's (`src/chatddx/ledger/run.py:RunStarted`). Queueing makes a started run the person's job, holding as
  many of the endpoint's slots as its concurrency (`Bench.queue`; `docs/modules/worker.md`, "A job").
- **Where runs are composed**: the variation island on `/configurations/{id}`, its parts, a handle for a hand-written
  configuration, families by tag or picked, a seed or replicates, and scoring; Review's **Run this case**, a
  configuration, a model and replicates; Home, a typed case under a configuration and a model; a run's page, again and
  resume; the repl's `use`, `set`, `under`, `seed`, `run` and `run tag`; and data sets' scripted runs. None but the API
  sets cleanup, concurrency or order, and none a canary set.
- **Runs are found by their trials**: a person's runs by any component their trial reaches
  (`src/chatddx/bench/seen.py:Seen.runs`), and Refine's columns by the skeletons a configuration compiles to under a
  handle (`src/chatddx/portal/refine.py:_columns`), not by what a start says. A run from a trial alone says nothing of a
  variation (`docs/modules/catalog.md`, "What a run ran").
- **Running again** builds another trial: the old one's skeleton, cases and cleanup, new seeds, and the handle's latest
  engine (`src/chatddx/bench/runs.py:again`). Runs of one trial digest at one endpoint are what drift compares
  (`docs/backlog.md`, "Drift between runs").
- **What waits on it** in `docs/backlog.md`: "Execution settings as a component", named and picked, which waits for the
  portal to offer them; "Loading data sets", where trials and executions have no tables; "Unheeded reasoning",
  variations crossed as several runs; and "A run names the skeleton its look gave".

### A trial's section, true to the data model

- **About it**, what is said and its versions by link, as every thread's.
- **What it holds**: its skeleton, a configuration's version; its engine, by its handle; its cases, one a line, by their
  family's name; its cleanup; its seeds. **Its findings**: its lints.
- **Its runs**: those of each version, as a run's page links its trial.
- **Running it**, an action, on a page apart (see "Options", 6).

### Options

The takes in bold, and what is decided says so: every one, at the user's word. What changed since the options were first
put, in "Reconsidered".

1. **The word, `trial`**: a kind a person writes, as researchers author trials (`docs/glossary.md`, "Roles"), begun from
   the Library as every kind a person writes, with its findings. Decided.
2. **Its skeleton, a configuration's version in its cases' language.** A trial holds a skeleton compiled into one
   language; a configuration's thread holds its skeleton as written, and its compilations into other languages are held
   by no thread. Where the language is taken from the cases: **(a) in the bench, as it writes a trial: a configuration's
   version is picked as written, and the trial holds it carried into its cases' language through its translations, its
   compilation kept, as a start carries one now; the picker shows the configuration a held skeleton was compiled from,
   and beside it what the trial holds, "lines, in sv"; what has moved on follows that compilation's recipe to its
   configuration**; (b) in the trial: it holds the configuration as written, and the runner compiles it into each case's
   language as it sends, so that a trial no longer pins what is sent, a change to the factors and the ledger against the
   cage; (c) in the portal's form alone, so that the API and the repl write a trial as it is held. (a) is a
   configuration's own compromise again: its recipe's parts are picked, and the skeleton they compile to is held.
   Decided: (a).
3. **Its engine, by handle**, as researchers see handles, not engines (`docs/modules/catalog.md`, "Titles"): a handle
   picked, each model the person sees by its name, standing for the engine serving it now, and the one held shown by its
   title, "qwen3-8b, an earlier engine". Decided.
4. **Its cases**, picked one a line by their family's name, as an expectation's case is now; many at once from the case
   tab, given by their families. Decided.
5. **Its cleanup and seeds**, as the trial holds them. Decided. The cleanup is its text-cleanup steps, applied to each
   vignette after it is fingerprinted and before it is sent: line endings made LF, Unicode NFC, both ends trimmed, runs
   of blank lines collapsed (`src/chatddx/factors/cases.py:CleanupOp`), in order; a source names its default ones, and
   no World names any. A new trial is begun with its given cases' sources' steps and one seed drawn; more seeds are more
   replicates. Running a version again runs the same trial, seeds and all, and only its runs differ, which is what drift
   compares (`docs/backlog.md`, "Drift between runs"); new seeds are a new version.
6. **Running it** on a page apart from the Library, `/runs/new?trial=ID`, which a trial's section links: the version
   run, the execution and scoring; it starts that version at the endpoint serving its engine, queues it as the person's
   job and leads to the run; several trials given run together as one start, the later `with` the first. Decided. A
   trial whose engine no endpoint serves any more is refused, its engine to be followed. The execution: **(a) the
   endpoint's, its concurrency and order given, as the API's start, with the endpoint's canary set**; (b) executions as
   a kind picked in the Library (`docs/backlog.md`, "Execution settings as a component"), a new kind and its migration.
   Decided: (a).
7. **Cases in one language**: a trial whose cases are in several languages is refused, written or edited, as there is no
   point in running mixed cases; several languages are several trials, run together (6). Decided, over a form writing a
   trial for each language its cases are in.
8. **What a run of it says**: **(a) its name, the trial's; it is found from its trial, which the thread's version holds,
   and from its skeleton, which its configuration's holds, as Refine finds runs now, and `varied` stays a variation's**;
   (b) an entry naming the trial's version it ran, a field of the catalog and its migration. Decided: (a).
9. **The places that start a variation now**, the variation island, Review, Home, the repl and scripted runs, stay as
   they are, keeping no trial, until step 8. Decided.

### Reconsidered

The user's: even in the Library, nobody chooses a language or works with a translation for a trial: its language is
always its cases'.

- **Fell away**: a skeleton picked in another language (2 (b) and (c) as first put), and every start keeping its trials
  (7 (c) as first put), which 9 rules out.
- **Changed**: where the cases' language is taken (2), and cases in several languages, refused rather than written as
  several trials (7).
- **Where language is in the Library already**:
  - Shown, read-only, in each tab's list and each section's "About it": a text's own, a configuration's worked out from
    its recipe and compilations, a judge's and an expectation's from their skeleton and case, and a case's its family's
    (`docs/modules/catalog.md`, "Languages").
  - Given with a text, as it is begun or edited: the language the text is written in, for instructions, few-shot,
    prompt, output, toolset and hand-written skeletons, kept on the component.
  - Said of a case by its owner (step 5): where the cases' language is chosen, which a trial follows.
  - Worked with as translations: a translations chunk's fields are the languages it goes into and their entries, edited
    in the Library as any chunk and on `/translate`, and a configuration picks one among its parts.

What it asks beneath: the bench's word and writing a trial, carried into its cases' language; starting trials' versions
as one start; the API's routes for them; suggestions in `docs/modules/bench.md` ("Writes for the person", "Runs and
scores") and `docs/modules/api.md`; and stamps.

## Open

- **Runs and scores** apart from their trials: whether anything is said of them, while a run stays its owner's alone
  (`docs/modules/bench.md`, "What a person sees").
- **What was said, shown as history**, as the catalog keeps every entry.
- **Roles**: the Library shows every kind to everyone, as the data model has it; what each role is shown first waits
  (`docs/modules/identity.md`, "Authorization").

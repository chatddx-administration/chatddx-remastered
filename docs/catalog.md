# Catalog

The catalog gives people handles to factors. It names components, families of cases, runs and scores; it keeps the versions
of a component in order; and it remembers who owns what and who it is shared with, what was deleted, which language a
text is written in, and what a scorer's views are called. None of it changes an output or a score: no component refers
to the catalog, so no digest depends on it (docs/factors.md, "Not factors"). This document describes what the catalog
keeps and why. Names, fields, rules and errors are in the API, docs/catalog-api.md.

The catalog builds on the factor components that are referred to by digest, to runs and scores by their start records
(docs/ledger.md), and to people by their identity (docs/identity.md). It holds nothing produced from a vignette, which
is the only sensitive data, so the reader role may read all of it.

## How the catalog works

### Append-only, and the latest wins
Nothing in the catalog is changed or removed. Every change is a new row. For anything that can change (a thread's
current version, a name, a binding, a language), the latest row is what holds now and the earlier rows are its
history. "Latest" means written last, in the order the database numbered the rows; the time a row records is only for
display.

Deleting is a row too, which a later row can undo (see "Deleting"). True deletion is refused by the database
(docs/store.md, "Tiers"); a garbage collector for unreferenced items is on the table (docs/chatddx.md, "On the table").

### Rules
The catalog checks its rules against what is stored when it writes, and a change that takes several rows, such as a
thread with its first version and its owner, a family with its binding, or a repair, is written all at once or not at
all. The rules that two writers at once could break are repeated by the database at tier 2, with one exception (see
"Concurrent writers").

## Threads and edits
A *thread* is a sequence of *edits* and work a handle on a component that people edit.
The latest edit is the thread's *head*, its current version; the others are its history, in order.

Every kind of component has threads except two:
- cases, which are named through families instead (see "Families and repairs");
- compilations, which record how a skeleton was made and which nobody edits. Skeleton edits point at them (see
  "Recipes").

That includes the kinds ops and developers write, such as models, engines, expectation schemas and canary sets. They
are rarely edited, but threads are where names attach for everything except cases.

The same component may appear in several threads, and more than once in one: reverting is an edit that points back at
an earlier version.

A thread is created with its first version and its owner, and its name when one is given. It moves only when someone
saves an edit, and nothing moves along with it. An edit can name the head it was made on, and is then refused when
the thread has moved on since, so that a change made on an older version doesn't undo what came after it unseen.
Edits of one thread are written one at a time, so that holds with several writers too.

The catalog answers what people need to find:
- a thread's versions, and its current one;
- the live threads of a kind, or the deleted ones;
- the threads of a kind with a given name, owned by a given person if asked;
- the forks of a thread;
- the expectation threads of a case;
- where a given component appears, in any thread;
- what a person sees (see "Owners");
- the expectation a person scores a case against, under a given expectation schema: their own. One shared with them
  counts once they fork it. When two writers at once have left them several to choose from, the catalog says so
  rather than choose (see "Concurrent writers").

## Configurations and variations
Researchers refine their configurations by trying variations, keeping what works, and forking new configurations from
it (docs/chatddx.md, "Intended evolution of configurations"). The catalog supports that workflow without having objects
of its own for it.

A *configuration* is a skeleton thread. A *variation* is a fork, of any kind, together with what it changes from the
version it came from. Trying a variation costs nothing in the catalog, since any component can be run without a thread.
A variation worth keeping becomes an edit of its thread, or a fork. Configurations are organised by their lineage, the
recipe parts they use, what is said about them and their runs, not by their names, which are optional.

A *batch* is kept on a thread of its own (docs/factors.md, "Batch"): the variations of a configuration that a person
runs together over the same cases, kept to run again or later. Adding cases to a batch is an edit of its thread, since a
batch's trials pin their cases.

### Recipes
A recipe has no thread of its own; its history is kept on the skeleton thread it compiles to. Each edit of a skeleton
thread can name the compilation that produced its skeleton, and the compilation holds the recipe (docs/factors.md,
"Compilation"). The compilation must be one of that very skeleton, and only skeleton edits name one. A hand-written
skeleton has no compilation, so its edits name none.

### Forks
A *fork* is a new thread started from a version of another thread of the same kind, its *origin*. A fork is compared
with its *base*: the version it was forked from, or the origin version its changes were last re-applied onto. What it
*varies* is what its head changes from the base: the recipe parts it replaced when both are compiled, and otherwise the
component's own fields.

When the origin has moved on, the catalog offers a *proposal*: the origin's head with the fork's changes on top, as a
recipe to compile or as a component. Nothing is stored until someone accepts it. Accepting is an ordinary edit of the
fork that records which origin version the changes were re-applied onto, which can't be earlier than the one the fork
came from. From then on, the fork is compared with that version.

The old chatddx let a configuration extend another and follow it automatically; here a fork follows its origin only
when someone accepts a proposal.

### What has moved on
For any thread, the catalog lists the references of its head that could be updated. It looks at:
- the head's own references, such as a trial's skeleton, engine and cases;
- for a configuration, the parts of its recipe;
- the appendices of each case the head references, since cases have no threads of their own.

A reference is *behind* when a live thread that held it has since moved on to another version. A component can be held
by several threads, so a reference can be behind several of them: for example, when a chunk was forked and both threads
moved on. Deleted threads aren't proposed.

A case is also behind when its family has a newer binding (see "Families and repairs"). The catalog then offers its
*replacement*: the same appendix texts, bound to the family's current vignette. Cases without appendices are flagged
this way too.

Moving on goes one level at a time. A chunk edit makes its skeleton threads behind; saving one of those makes its trial
threads behind. A fork makes nothing behind until it moves on.

## Entries
Names, and everything else people say about something, are *entries*. An entry is about exactly one thread, family, run
or score, its *subject*. A run or a score has to have started before anything can be said about it.

For each field the latest entry wins, and for tags and collaborators, the latest entry about each tag and each
collaborator. A subject nothing has been said about has no name, no owner, and nothing else.

| Field | Holds | Removed by | Used for |
| --- | --- | --- | --- |
| Name | a text, not empty | an entry without a text; the title takes over | titles, and looking threads up |
| Description | a text | nothing: it can only be replaced | people |
| Tag | one tag, not empty; a subject has a set of them | an entry withdrawing that tag | people |
| Owner | a person | nothing: it can only be replaced | what a person sees, and looking threads up |
| Collaborator | a person; a subject has a set of them | an entry withdrawing that person | what a person sees |
| Deleted | a flag | an entry restoring the subject | see "Deleting" |
| Language | a language, only on a family | nothing: it can only be replaced | see "Languages" |

Every field but the language can be said about any subject. The fields the catalog doesn't use itself are for people
and the portal.

### Names
A name is for people. None is required, and names needn't be unique: a thread without one is shown by its title (see
"Titles"). Names can still be used to look threads up by kind, name and owner, which is how `chatddx init-data`
recognises its own records when it runs again (docs/curation.md).

### Owners
Whoever creates a thread or a family is its owner, unless they name someone else, and sharing it with someone makes
them a collaborator. A person sees what they own and what is shared with them, as long as it isn't deleted. Like
authorization, this decides what is relevant to show, not who may read it (docs/identity.md, "Authorization").

Expectations are held to what a person owns, not to what they see. A person is scored against their own expectation of
a case, and one shared with them counts once they fork it, so nothing someone else shares, edits or restores changes
what they are scored against. A person owns at most one live expectation thread per case and expectation schema: a
second one, an edit that moves another onto that case and schema, an owner entry naming them, or a restore that would
make two is refused.

This is the catalog's sense of owning. It is a different thing from the roles' sense, as in "clinicians own the
vignettes" (docs/chatddx.md, "Roles mentioned").

A run's owner is whoever started it, and a score's whoever scored it: the runner and the scoring pass write the
owner entry as they start, and a person's runs are the runs they own.

### Deleting
A deleted thread or family is still there, and so are its components. Deleting takes it out of what people pick from
and of what is proposed to them: the threads of a kind, what a person sees, looking up by name, the expectation a
person scores against, and what has moved on, which proposes no deleted thread and flags no case of a deleted family.
Titles turn to deleted threads only when the live ones give them nothing to show.

What answers questions about the past still includes them: a thread's history, its forks, a case's expectations, where
a component appears, surveys of a source, and repairs, which rebind deleted threads too.

Deleting is undone by another entry. Wiping a person's data deletes what they own and withdraws them from what is shared
with them; loading the sample data again restores a deleted fork rather than forking anew.

What the portal hides is open (see "Open design issues").

## Titles
Anything without a name is shown by a *title*, built when asked and never stored.

A thread's title is its name. Without one, a fork is shown by its origin's title and what it varies from its base
("plan, output: management-plan-shown"), or as "a fork of plan" when it varies nothing; any other thread is shown by
what its head holds.

Any component can be given a title, in a thread or not, so a run of a variation nobody saved can be shown too. The
catalog prefers, in order:
1. a live thread whose head it is: its name, or else its title;
2. a live thread with a name that held it earlier: "plan (earlier)";
3. the same two among deleted threads;
4. what it holds.

A case is shown by its family's name, or without one by the family's current place, followed by the opening words of
its appendices. A case from before a repair says so: "chest pain (earlier) with …". A case without a family is shown by
its own source and id.

What a component holds is described by what tells it apart from others of its kind, and the components it uses are
shown by their titles in turn.

A configuration is described by its recipe's parts, translations and toolset included, when a compilation of it is
stored: "ddx · case · management-plan · recommended · off". A judge's recipe says so first. Without a stored
compilation, as for a hand-written skeleton, it is shown by its purpose and the start of its digest:
"generation skeleton 1a2b3c".

Each kind is described by:

| Component | Described by | Example |
| --- | --- | --- |
| Chunk | Its values or the opening words of its text. | `temperature 1.0, top_p 1.0` or `"{vignette}{appendices}"` |
| Chunk (few-shot) | How many messages it has. | `few-shot, 2 messages` |
| Chunk (output) | Its contract, and its schema's title or properties. | `native output: management_plan_v1` |
| Chunk (toolset) | Its tools. | `with web_search` |
| Chunk (passthrough) | The options it sets. | `passthrough: logprobs, top_logprobs` |
| Translations chunk | Its language and size. | `sv translations, 12 texts` |
| Tool | Its name. | `web_search` |
| Appendix | The opening words of its text. | `"Lab results: CRP 180 mg/L, lactate 2.8…"` |
| Expectation | Its case. | `expectation for Dutchfall11w` |
| Model | Its repository. | `google/gemma-3-12b-it` |
| Local engine | Its model, server and GPU. | `google/gemma-3-12b-it on vllm 0.24.0 (NVIDIA GeForce RTX 5090)` |
| Remote engine | Its model and host. | `gpt-4o at api.openai.com` |
| Trial | Its skeleton, its engine, and how many cases and seeds it has. | `plan on qwen3-8b@pelle, 20 cases, 1 seed` |
| Batch | Variation count, its base, case count, and endpoint. | `4 variations of plan, 20 cases, at qwen3-8b@pelle` |
| Judge | Its skeleton and engine. | `judge grader on qwen3-8b@pelle` |
| Scorer | Its entry point and version. | `scorer chatddx.scorers.patterns:score v1` |
| Scoring | Its scorer and how many expectations it has. | `plan against 20 expectations` |
| Expectation schema | Its title or its properties. | `Targets` |
| Canary set | How many canaries it has. | `2 canaries` |
| Anything with nothing better to go by | Its kind and the start of its digest. | `compilation 1a2b3c` |

Titles aren't unique: two unnamed components can be described alike, and names aren't unique either. Titles change when
the names they're built from change, so an export for publication should freeze the titles it uses.

## Scorer labels
Scorers have labels per edit of a scorer thread, one part (a view or a resource) and one position, and it must name a
view or resource the edit's scorer has. Labels are written with their edit once, so no one's labels change anyone
else's, and the archive's stay as its data sets give them.

Renaming a view is a new edit of the same scorer: the thread's history shows it, and since the scorer's digest doesn't
change, no scoring, score or run left to score changes with it. A fork of a scorer as it is keeps its origin's labels
unless given others; a scorer edited without labels keeps the head's only when it is the head's scorer, since a
position only means something within one scorer, and following an origin keeps the labels of whichever side's views
the proposal keeps. Keeping a scorer whose labels differ from the head's is a new edit, even with the same digest.

A scorer digest is called what the person's view calls it: the labels of the head that holds it, among the threads
they see, their own first; else of the latest edit in their history that held it; else "view N".

## Families and repairs
A case is a component: a vignette plus its appendices (docs/factors.md, "Case"). It has no thread, because changing its
appendices makes another case, not a new version of the same one. The vignette can also change at its source, under
the same file name or another. A *family* is the handle that follows one vignette through all of that. Names, tags and
the rest are said about the family, and every case of the vignette belongs to it.

A family's *bindings* record where its vignette is: the source, the vignette's id there (for a directory, the file
name) and the fingerprint of its content. The latest binding is the current one.

A case belongs to the family with a binding, current or earlier, that matches its vignette exactly. So cases from
before a repair keep their family.

*Adopting* a case gives its family, or creates one bound to its vignette and owned by whoever adopts it, unless they
name someone else. A vignette that would give another family's current place new content, or its content a new name,
isn't adopted: that calls for a repair, not a new family. A source whose texts never move, as a database source's,
adopts by id alone, since the same text typed twice is two vignettes.

### Noticing changes
A *survey* compares what a source lists now, each vignette's id and fingerprint, with the current bindings of that
source's families, and sorts them into:
- unchanged;
- changed: the same id with new content;
- renamed: the same content under a new id, while the old id is gone;
- new, and gone. A vignette whose name and content both changed shows up as gone plus new.

A run notices a changed vignette too (docs/factors.md, "Preparing a case").

### Repairing
A *repair* moves a family to its vignette's new place. It changes exactly one half of the binding, the id or the
content, and keeps the source; the half that stays the same is what identifies the family. A place another family
already holds is refused, as in adopting. A repair, all at once:
1. binds the family to the new place;
2. builds every stored case of the old place anew: the same appendix texts, bound to the new vignette;
3. moves each appendix thread whose head belongs to the old place to its rebound appendix;
4. for a rename only, moves each expectation thread of those cases to an expectation of the new case. A rename can't
   change the right answer, but new content can, so after a content change the expectations stay as they are, and
   what has moved on reports their case with its replacement for a clinician to confirm.

When both the name and the content changed, nothing identifies the family, so there is no repair: the vignette becomes
a new family by adopting it, and its names are carried over by hand. The database holds a family to its source, and
each new binding to the previous one's id or content.

## Languages
The rig never tells a model which language a request is in; what is sent is simply in a language. The catalog records
which one, so that lints can check that a trial doesn't mix languages (docs/factors.md, "Lints").

A language is a tag such as "sv" or "pt-BR". It can be replaced but not removed, and the latest wins. It is kept in one
of two places:
- A vignette's language is said about its family; no other subject takes a language entry.
- A component's language is kept on the component, so it belongs to the text itself: forking a chunk keeps it, and
  changing one component's language touches no other. A new version has no language until someone gives it one; the
  portal can offer the previous version's.

Only components whose language is their own can have one: the chunks that hold text sent to a model (instructions,
few-shot, prompt, output, toolset, and translations, whose language is the one they translate into) and hand-written
skeletons. A compiled skeleton's language comes from its recipe.

The language of any component can be worked out:
- a case's is its family's, and an expectation's is its case's;
- a trial's and a judge's are their skeleton's;
- a compiled skeleton's comes from its recipes, which vote. A recipe with translations votes for the translations'
  language. A recipe without translations votes for the language that all its text-bearing chunks share, toolset
  included and appendix layout not. A recipe whose chunks lack a language or disagree doesn't vote. When the votes
  disagree, the skeleton has no language;
- a chunk's and a hand-written skeleton's are their own.

An unknown or disagreeing language gives none.

Vignettes are never translated: a case runs in the language it was written in. So the request follows the case (a
Swedish case runs under a Swedish-translated configuration), and comparing languages means comparing case sets.

## Storage
The catalog is a schema of its own (docs/store.md; tables in docs/migrations.md, "catalog"), with a table each for
threads, edits, entries, labels, families, bindings and languages. The writer role writes it and the reader role may
read all of it. Rows are never changed or deleted.

The database keeps an edit on its thread's kind and on a stored component of that kind, a fork on a version of the same
kind, a skeleton edit's compilation on one of that very skeleton, a label on an edit of a scorer thread, once per part
and position, written in the edit's transaction by its writer, and a language on a stored component of the kind it
records. At tier 2 it repeats the rules above that two writers at once could break.

## Terms

| Term | Meaning |
| --- | --- |
| Catalog | People's handles on components and records: names, versions, owners, sharing, deletions, languages and labels. |
| Thread | The versions of one component that people edit, in order. |
| Edit | One version on a thread. |
| Head | A thread's latest edit, its current version. |
| Fork | A thread started from a version of another thread of the same kind, its origin. |
| Base | The version a fork is compared with: the one it came from, or the one its changes were last re-applied onto. |
| Configuration | A skeleton thread. |
| Variation | A fork, and what it changes from its base. |
| Proposal | The origin's head with a fork's changes on top. |
| Behind | A reference whose thread has moved on, or a case whose family has a newer binding. |
| Entry | Something said about a thread, a family, a run or a score: a name, description, tag, owner, collaborator, deleted flag or language. |
| Subject | What an entry is about. |
| Owner, collaborator | Who a thread or family belongs to, and who it is shared with. Together they decide what a person sees. |
| Title | How something without a name is shown, built from what it holds. |
| Label | The name of a scorer's view or resource. |
| Family | The handle on one vignette through renames and edits at its source. |
| Binding | Where a family's vignette is: source, id and fingerprint. The latest is current. |
| Survey | Comparing what a source lists with where its families are bound. |
| Repair | Moving a family to its vignette's new id or content, and rebinding what depends on it. |
| Replacement | The case a stale case becomes under its family's current binding. |
| Latest wins | Of the rows about one thing, the one written last is what holds. |

## Open design issues
These are open questions of design. Where the code falls short of this document, the API says so
(docs/catalog-api.md, "Known gaps").

### Concurrent writers
The rules are checked against what is stored when a row is written. That holds with one writer at a time; with two,
only what the database enforces is sure to hold. It repeats every such rule but two: that no two families are bound to
the same vignette, by id or by content, at once, and that a person owns at most one live expectation thread per case
and expectation schema. So two people adopting the same vignette at the same moment can create two families, and two
writes at the same moment can leave a person several expectations to choose from, which scoring then refuses.

### Smaller issues
- **Identical vignettes.** Two vignettes with the same content under different ids in one source look like a rename:
  adopting refuses the second, and a survey reports both ids as renames of the same family.
- **Several matching families.** When bindings of several families match a case, the latest matching binding decides,
  which needn't be the latest family's.
- **Current bindings are compared within a source.** Surveys, adopting and repairing compare a vignette only with the
  families of its own source, which relies on a family never changing source. The database enforces that, and nothing
  in the catalog changes a source.
- **A thread without versions** is possible in the database, and so is a family without bindings; the catalog writes
  each together with its first. A deferred constraint could rule them out at tier 2.
- **A skeleton edit may leave out its compilation** even when one exists, and nothing can require it.
- **A language on a skeleton that is compiled later** is ignored from then on, since the skeleton's language comes from
  its recipe.
- **What deleting hides in the portal**: everywhere, or only in pickers, while the runs that used it stay visible.
- **Who changed an entry or a language isn't shown.** Every row records who wrote it and when, but for these only
  what holds now is shown.
- **Why an edit was made isn't stored.** It can be worked out by comparing consecutive versions' references.
- **Titles take a query for every reference they visit,** are rebuilt from names that change, and aren't unique.
- **An unnamed fork's title can pair two versions.** When the origin has no name and has moved on, the title describes
  the origin's current head, while what the fork varies is measured from the base.
- **Following can drop a fork's renamed view.** Labels follow the views the proposal keeps, so a fork that only
  renamed a view, and follows an origin whose views it keeps, takes the origin's labels.
- **Judges aren't checked for language.** A judge's language could be compared with the cases its scoring grades, the
  way lints check a trial's. An English judge grading Swedish answers may be intended, so it would be a notice rather
  than a warning.
- **A variation nobody saved has a long title.** It is described by its whole recipe:
  "case · diagnoses-tool · recommended (Qwen/Qwen3-8B-AWQ) · off (Qwen/Qwen3-8B-AWQ)", where the repl called it
  "diagnoses-tool (Qwen/Qwen3-8B-AWQ)+reasoning=off": the configuration it came from and the parts set over it.
  Neither is stored. An entry on the run, or a title made from the closest configuration and what the variation
  changes from it, would say it shorter.
- **An edit that names its head holds with several writers without the database repeating the rule**:
  each edit of a thread waits for the one before it to land. The head an edit names is held without the database
  repeating it: every edit takes its thread's advisory lock (src/chatddx/store/catalog.py:Catalog._lock).
  The writer may not update the catalog's tables, so `FOR UPDATE` isn't open to it.

# Catalog

The catalog is how people name, keep and find what the store holds: names for components, families of cases, runs and
scores; versions of a component in order; who owns what and who it is shared with, what was deleted and the language of
texts.

None of it changes an output or a score: no component refers to the catalog, so no digest depends on it.

Fields, classes, functions and errors are in docs/reference/catalog.md.

The catalog refers to

- factor components by digest
- runs and scores by their start records (docs/modules/ledger.md)
- people by their identity (docs/modules/identity.md)

It holds nothing sensitive, so the reader role may read all of catalog.

## How the catalog works

### Append-only, and the latest wins

Nothing in the catalog is changed or removed. Every change is a new row. For anything that can change (a thread's
current version, a name, a binding, a language), the latest row is what holds now and the earlier rows are its history.
"Latest" means written last, in the order the database numbered the rows, not by the time a row records, which is shown,
and counts the runs a person started in the last day.

Deleting is a row too, which a later row can undo (see "Deleting"). True deletion is refused by the database
(docs/modules/store.md, "Tiers"); a garbage collector for unreferenced items waits (docs/backlog.md, "Garbage
collection").

### Rules

The catalog checks its rules against what is stored when it writes, and a change that takes several rows, such as a
thread with its first version and its owner, a family with its binding, or a repair, is written all at once or not at
all. The rules that two writers at once could break are repeated by the database at tier 2, with two exceptions
(docs/backlog.md, "Concurrent writers").

## Threads and edits

A _thread_ is a sequence of _edits_, the versions of a component that people edit. The latest edit is the thread's
_head_, its current version; the others are its history, in order.

Every kind of component has threads except two:

- cases, which are named through families instead (see "Families and repairs");
- compilations, which record how a skeleton was made and which nobody edits. Skeleton edits point at them (see
  "Recipes").

That includes the kinds ops and developers write, such as models, engines, the facts about models, expectation schemas
and canary sets. They are rarely edited, but threads are where names attach for everything except cases. The facts about
a model are a thread of the archive's, named by the model, which `chatddx init-data` writes from the facts files
(docs/modules/facts.md); correcting a fact is a new version of it.

The same component may appear in several threads, and more than once in one: reverting is an edit that points back at an
earlier version.

A thread is created with its first version and its owner, and its name when one is given. It moves only when someone
saves an edit, and nothing moves along with it. An edit can name the head it was made on, and is then refused when the
thread has moved on since, so that a change made on an older version doesn't undo what came after it unseen. Edits of
one thread are written one at a time, so that holds with several writers too.

The catalog answers what people need to find:

- a thread's versions, and its current one;
- the threads of a kind, with what is said of each, deleted or not;
- the threads of a kind with a given name, owned by a given person if asked;
- the forks of a thread;
- the expectation threads of a case, and of several cases under a given expectation schema, with what is said of each;
- where a given component appears, in any thread;
- which of several heads is picked, or that there are several to choose from (docs/backlog.md, "Concurrent writers").

## Configurations and variations

Researchers refine their configurations by trying variations, keeping what works, and forking new configurations from it
(docs/chatddx.md, "Intended evolution of configurations"). The catalog supports that workflow without having objects of
its own for it.

A _configuration_ is a skeleton thread: requests with the recipe it was compiled from (see "Recipes").

A _variation_ is a configuration with recipe parts replaced over a version of a configuration (docs/modules/bench.md,
"The variation being tried"). It is tried until someone keeps it: as a fork, which then varies from its base (see
"Forks"), or as a new version of a configuration of their own.

Trying a variation costs nothing in the catalog, since any component can be run without a thread. A variation worth
keeping becomes an edit of its thread, or a fork. Configurations are organised by their lineage, the recipe parts they
use, what is said about them and their runs, not by their names, which are optional.

### Recipes

A recipe has no thread of its own; its history is kept on the skeleton thread it compiles to. Each edit of a skeleton
thread can name the compilation that produced its skeleton, and the compilation holds the recipe, which names its model,
and the facts about it was worked out from, when it asks them for anything (docs/modules/factors.md, "Compilation"). The
compilation must be one of that very skeleton, and only skeleton edits name one. A hand-written skeleton has no
compilation, so its edits name none.

A skeleton thread's versions hold the recipes people chose: an edit is written when its skeleton or its recipe differs
from the head's, so a recipe that compiles to the head's skeleton is a new version. The head's recipe compiled by other
code, or against other facts, is none, or every configuration init-data loads would get a version at each deploy and at
each correction of a fact, and its forks a proposal that changes nothing.

### Forks

A _fork_ is a new thread started from a version of another thread of the same kind, its _origin_. A fork is compared
with its _base_: the version it was forked from, or the origin version its changes were last re-applied onto. What it
_varies_ is what its head changes from the base: its recipe's fields when both are compiled, the parts a variation
replaced and, in a fork a data set wrote, the purpose and appendix layout too; otherwise the component's own fields.

When the origin has moved on, the catalog offers a _proposal_: the origin's head with the fork's changes on top, as a
recipe to compile or as a component. Nothing is stored until someone accepts it. Accepting is an ordinary edit of the
fork that records which origin version the changes were re-applied onto, which can't be earlier than the one the fork
came from. From then on, the fork is compared with that version.

The old chatddx let a configuration extend another and follow it automatically; here a fork follows its origin only when
someone accepts a proposal.

### What has moved on

For any thread, the catalog lists the references of its head that could be updated. It looks at:

- the head's own references, such as a trial's skeleton, engine and cases;
- for a configuration, the parts of its recipe, its model among them, and the facts it was compiled against;
- the appendices of each case the head references, since cases have no threads of their own.

A model change puts the configuration behind it, and its owner follows it with the facts (docs/modules/bench.md,
"Following facts").

A reference is _behind_ when a live thread that held it has since moved on to another version. A component can be held
by several threads, so a reference can be behind several of them: for example, when a chunk was forked and both threads
moved on. Deleted threads aren't proposed.

Facts are behind only in a configuration that asks them for something: one with a literal sampling and reasoning names
none. Its owner follows them by keeping its recipe compiled against the corrected facts, as a new version
(docs/modules/bench.md, "Following facts"); init-data does so for the archive's.

A configuration's facts are behind only when their thread's head would change what it sends: compiling its recipe
against the newer facts gives another skeleton, or is refused. A correction it doesn't reach, such as a level it doesn't
ask for or the model's context length, leaves it as it is, since a version compiled against it would hold the same
skeleton and recipe, and write nothing (see "Recipes").

A case is also behind when its family has a newer binding (see "Families and repairs"). The catalog then offers its
_replacement_: the same appendix texts, bound to the family's current vignette. Cases without appendices are flagged
this way too.

Moving on goes one level at a time. A chunk edit makes its skeleton threads behind; saving one of those makes its trial
threads behind. A fork makes nothing behind until it moves on.

## Entries

Names, and everything else people say about something, are _entries_. An entry is about exactly one thread, family, run
or score, its _subject_. A run or a score has to have started before anything can be said about it.

For each field the latest entry wins, and for tags and collaborators, the latest entry about each tag and each
collaborator. A subject nothing has been said about has no name, no owner, and nothing else.

| Field        | Holds                                                                        | Removed by                                    | Used for                                   |
| ------------ | ---------------------------------------------------------------------------- | --------------------------------------------- | ------------------------------------------ |
| Name         | a text, not empty                                                            | an entry without a text; the title takes over | titles, and looking threads up             |
| Description  | a text                                                                       | nothing: it can only be replaced              | people                                     |
| Tag          | one tag, not empty; a subject has a set of them                              | an entry withdrawing that tag                 | people                                     |
| Owner        | a person                                                                     | nothing: it can only be replaced              | what a person sees, and looking threads up |
| Collaborator | a person; a subject has a set of them                                        | an entry withdrawing that person              | what a person sees                         |
| Deleted      | a flag                                                                       | an entry restoring the subject                | see "Deleting"                             |
| Language     | a language, only on a family                                                 | nothing: it can only be replaced              | see "Languages"                            |
| Varied       | an edit of a configuration, only on a run                                    | nothing: it can only be replaced              | see "What a run ran"                       |
| Replaced     | a part and the chunk or model it was set to, or none; a run has one per part | nothing: it can only be replaced              | see "What a run ran"                       |
| With         | the first run of the start a run is one of, only on a run                    | nothing: it can only be replaced              | see "What a run ran"                       |

Every field but the language, the varied edit, the replaced parts and the run a run was started with can be said about
any subject. The fields the catalog doesn't use itself are for people and the portal.

### Names

A name is for people. None is required, and names needn't be unique: a thread without one is shown by its title (see
"Titles"). Names can still be used to look threads up by kind, name and owner, which is how `chatddx init-data`
recognises its own stanzas when it runs again (docs/modules/curation.md).

### Owners

Whoever creates a thread or a family is its owner, unless they name someone else, and sharing it with someone makes them
a collaborator. A person sees what they own and what is shared with them, as long as it isn't deleted. Like
authorization, this decides what is relevant to show, not who may read it (docs/modules/identity.md, "Authorization").

Expectations are held to what a person owns, not to what they see. A person is scored against their own expectation of a
case, and one shared with them counts once they fork it, so nothing someone else shares, edits or restores changes what
they are scored against. A person owns at most one live expectation thread per case and expectation schema: a second
one, an edit that moves another onto that case and schema, an owner entry naming them, or a restore that would make two
is refused.

This is the catalog's sense of owning. It is a different thing from the roles' sense, as in "clinicians own the
vignettes" (docs/glossary.md, "Roles").

A run's owner is whoever started it, and a score's whoever scored it: the runner and the scoring pass write the owner
entry as they start, and a person's runs are the runs they own.

### Deleting

A deleted thread or family is still there, and so are its components. Deleting takes it out of what people pick from and
of what is proposed to them: what a person sees, looking up by name, the expectation a person is scored against, and
what has moved on, which proposes no deleted thread and flags no case of a deleted family. The threads of a kind still
include it, marked deleted.

What answers questions about the past still includes them: a thread's history, its forks, a case's expectations, where a
component appears, surveys of a source, and repairs, which rebind deleted threads too.

Deleting is undone by another entry. Wiping a person's data deletes what they own and withdraws them from what is shared
with them; loading the sample data again restores a deleted fork rather than forking anew.

What the portal hides is open (agents/wip-portal.md, "What the docs ask of it").

### What a run ran

The ledger records the trial a run ran (docs/modules/ledger.md); what a person called it and what they varied are said
here. As a run starts, the bench names it by its variation's label and says what it varied: the configuration's edit it
was built on, and each part replaced over it, by the chunk or model it was set to, or none for a part taken out. A start
over cases in several languages is a run per language (docs/modules/bench.md), and each run after the first says the
first, the run it was started _with_, so the runs of one start are found together. A run started from a trial alone, as
the runner starts one, says none of it. Running again says what the run it repeats varied, and starts alone.

So a run of a variation nobody saved links the configuration it came from, while the ledger keeps what was sent. The
database holds a varied edit to a configuration's, a replaced part's chunk to a stored one of that part, a replaced
engine to a stored engine, and the run a run was started with to one that has started.

## Titles

Anything without a name is shown by a _title_, built when asked and never stored.

A thread's title is its name. Without one, a fork is shown by its origin's title and what it varies from its base
("plan, output: management-plan-shown"), or as "a fork of plan" when it varies nothing; any other thread is shown by
what its head holds.

Researchers see handles, not engines, so a run on an earlier engine reads as under its handle, folded with its group
(`qwen3-8b, an earlier engine`); the engine's own title stays ops'.

Any component can be given a title, in a thread or not, so a run of a variation nobody saved can be shown too. The
catalog prefers, in order:

1. a live thread whose head it is: its name, or else its title;
2. a live thread with a name that held it earlier: "plan (earlier)";
3. the same two among deleted threads;
4. what it holds.

A case is shown by its family's name, or without one by the family's current place, followed by the opening words of its
appendices. A case from before a repair says so: "chest pain (earlier) with …". A case without a family is shown by its
own source and id.

What a component holds is described by what tells it apart from others of its kind, and the components it uses are shown
by their titles in turn.

A configuration is described by its recipe's parts, translations, toolset and model included, the model last, when a
compilation of it is stored: "ddx · case · management-plan · recommended · off · qwen3-8b-awq"; one compiled into a
language says so last: "…, in sv". A judge's recipe says so first. Without a stored compilation, as for a hand-written
skeleton, it is shown by its purpose and the start of its digest: "generation configuration 1a2b3c".

Each kind is described by:

| Component                             | Described by                                                            | Example                                                                 |
| ------------------------------------- | ----------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| Chunk                                 | Its values or the opening words of its text.                            | `temperature 1.0, top_p 1.0` or `"{vignette}{appendices}"`              |
| Chunk (recommended sampling)          | That it is recommended, and the values it sets over the recommendation. | `recommended sampling` or `recommended sampling, max_output_tokens 512` |
| Chunk (reasoning level)               | The level it asks for, and its budget.                                  | `reasoning off` or `default reasoning, budget 2048`                     |
| Chunk (few-shot)                      | How many messages it has.                                               | `few-shot, 2 messages`                                                  |
| Chunk (output)                        | Its contract, and its schema's title or properties.                     | `native output: management_plan_v1`                                     |
| Chunk (toolset)                       | Its tools.                                                              | `with web_search`                                                       |
| Chunk (passthrough)                   | The options it sets.                                                    | `passthrough: logprobs, top_logprobs`                                   |
| Translations chunk                    | Languages codes, its size and the texts of the language with the most.  | `translations into de, sv, 12 texts`                                    |
| Tool                                  | Its name.                                                               | `web_search`                                                            |
| Appendix                              | The opening words of its text.                                          | `"Lab results: CRP 180 mg/L, lactate 2.8…"`                             |
| Expectation                           | Its case.                                                               | `expectation for Dutchfall11w`                                          |
| Model                                 | Its repository.                                                         | `google/gemma-3-12b-it`                                                 |
| Local engine                          | Its model, server and GPU.                                              | `google/gemma-3-12b-it on vllm 0.24.0 (NVIDIA GeForce RTX 5090)`        |
| Remote engine                         | Its model and provider.                                                 | `gpt-4o from openai`                                                    |
| Facts                                 | The model they are about.                                               | `facts about Qwen/Qwen3-8B-AWQ`                                         |
| Trial                                 | Its skeleton, its engine, and how many cases and seeds it has.          | `plan on qwen3-8b@pelle, 20 cases, 1 seed`                              |
| Scoring                               | Its scorer and how many expectations it has.                            | `scorer chatddx.scorers.metrics:score v2 against 20 expectations`       |
| Judge                                 | Its skeleton and its model's handle.                                    | `judge grader under qwen3-8b`                                           |
| Scorer                                | Its entry point and version.                                            | `scorer chatddx.scorers.metrics:score v2`                               |
| Expectation schema                    | Its title or its properties.                                            | `Targets`                                                               |
| Canary set                            | How many canaries it has.                                               | `2 canaries`                                                            |
| Anything with nothing better to go by | Its kind and the start of its digest.                                   | `compilation 1a2b3c`                                                    |

Titles aren't unique: two unnamed components can be described alike, and names aren't unique either. Titles change when
the names they're built from change, so an export for publication should freeze the titles it uses.

## Scorer labels

Scorers have labels per edit of a scorer thread, one part (a view or a resource) and one position, and it must name a
view or resource the edit's scorer has. Labels are written with their edit once, so no one's labels change anyone
else's, and the archive's stay as its data sets give them.

Renaming a view is a new edit of the same scorer: the thread's history shows it, and since the scorer's digest doesn't
change, no scoring, score or run left to score changes with it. A fork of a scorer as it is keeps its origin's labels
unless given others; a scorer edited without labels keeps the head's only when it is the head's scorer, since a position
only means something within one scorer, and following an origin keeps the labels of whichever side's views the proposal
keeps. Keeping a scorer whose labels differ from the head's is a new edit, even with the same digest.

A scorer digest is called what the person's view calls it: the labels of the head that holds it, among the threads they
see, their own first; else of the latest edit in their history that held it; else "view N".

## Families and repairs

A case is a component: a vignette plus its appendices (docs/modules/factors.md, "Case"). It has no thread, because
changing its appendices makes another case, not a new version of the same one. The vignette can also change at its
source, under the same file name or another. A _family_ is the handle that follows one vignette through all of that.
Names, tags and the rest are said about the family, and every case of the vignette belongs to it.

A family's _bindings_ record where its vignette is: the source, the vignette's id there (for a directory, the file name)
and the fingerprint of its content. The latest binding is the current one.

A case belongs to the family with a binding, current or earlier, that matches its vignette exactly. So cases from before
a repair keep their family.

_Adopting_ a case gives its family, or creates one bound to its vignette and owned by whoever adopts it, unless they
name someone else. A vignette that would give another family's current place new content, or its content a new name,
isn't adopted: that calls for a repair, not a new family. A source whose texts never move, as a database source's,
adopts by id alone, since the same text typed twice is two vignettes.

### Noticing changes

A _survey_ compares what a source lists now, each vignette's id and fingerprint, with the current bindings of that
source's families, and sorts them into:

- unchanged;
- changed: the same id with new content;
- renamed: the same content under a new id, while the old id is gone;
- new, and gone. A vignette whose name and content both changed shows up as gone plus new.

A run notices a changed vignette too (docs/modules/factors.md, "Preparing a case").

### Repairing

A _repair_ moves a family to its vignette's new place. It changes exactly one half of the binding, the id or the
content, and keeps the source; the half that stays the same is what identifies the family. A place another family
already holds is refused, as in adopting. A repair, all at once:

1. binds the family to the new place;
2. builds every stored case of the old place anew: the same appendix texts, bound to the new vignette;
3. moves each appendix thread whose head belongs to the old place to its rebound appendix;
4. for a rename only, moves each expectation thread of those cases to an expectation of the new case. A rename can't
   change the right answer, but new content can, so after a content change the expectations stay as they are, and what
   has moved on reports their case with its replacement for a clinician to confirm.

When both the name and the content changed, nothing identifies the family, so there is no repair: the vignette becomes a
new family by adopting it, and its names are carried over by hand. The database holds a family to its source, and each
new binding to the previous one's id or content.

## Languages

The rig never tells a model which language a request is in; what is sent is simply in a language. The catalog records
which one, so that each case is sent in its own language (docs/modules/bench.md) and lints can check that a trial
doesn't mix languages (docs/modules/factors.md, "Lints").

A language is a tag such as "sv" or "pt-BR". It can be replaced but not removed, and the latest wins. It is kept in one
of two places:

- A vignette's language is said about its family; no other subject takes a language entry.
- A component's language is kept on the component, so it belongs to the text itself: forking a chunk keeps it, and
  changing one component's language touches no other. A new version has no language until someone gives it one; the
  portal can offer the previous version's.

Only components whose language is their own can have one: the chunks that hold text sent to a model (instructions,
few-shot, prompt, output and toolset) and hand-written skeletons. A translations chunk names the languages it translates
into itself, and has none of its own. A compiled skeleton's language comes from its compilations.

The language of any component can be worked out:

- a case's is its family's, and an expectation's is its case's.
- a trial's and a judge's are their skeleton's.
- a configuration's version's comes from the recipe its edit names, when it names one, so two configurations that hold
  one skeleton can be in two languages.
- a compiled skeleton's comes from its compilations: one compiled into a language is in that language, and one as
  written in the language its recipe votes for, the one all its text-bearing chunks share, toolset included and appendix
  layout not. Translations don't vote. A recipe whose chunks lack a language or disagree doesn't vote. When the
  compilations disagree, the skeleton has no language.
- a chunk's and a hand-written skeleton's are their own.

An unknown or disagreeing language gives none.

Vignettes are never translated: a case runs in the language it was written in. So the request follows the case (a
Swedish case runs under its configuration translated into Swedish; docs/modules/factors.md, "Translations"), and
comparing languages means comparing case sets.

## Storage

The catalog is a schema of its own (docs/modules/store.md; tables in docs/migrations.md, "catalog"), with a table each
for threads, edits, entries, labels, families, bindings and languages. The writer role writes it and the reader role may
read all of it. Rows are never changed or deleted.

The database keeps an edit on its thread's kind and on a stored component of that kind, a fork on a version of the same
kind, a skeleton edit's compilation on one of that very skeleton, a label on an edit of a scorer thread, once per part
and position, written in the edit's transaction by its writer, and a language on a stored component of the kind it
records. At tier 2 it repeats the rules above that two writers at once could break.

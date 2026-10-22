# The portal: work in progress

The portal is the bench's web edge, beside the repl and the API: HTML rendered on the server from the bench, with Svelte
islands where a page needs a round trip. This starts from the Library and the Lab, which are drafted (see "The Library
today" and "The Lab today"), and has what is next in "Next". "Decided" means the user said so. "Take" is the agent's
recommendation and still open.

## Configuration and actions

Decided: the Library is where each component is written, one at a time; the Lab is where researchers combine what exists
already and try to run it, the evolution of configurations (`docs/chatddx.md`, "Intended evolution of configurations").

Decided, built: a run is composed as a trial, a thread of its own whose fields are its skeleton, its engine by handle,
cases, cleanup and seeds, and starting is queueing that trial's head under an execution. A trial is in one language, as
it names one skeleton, so a start over several languages is a start of several trials. A trial is begun of the cases
picked on the case tab; its tab, its page and its configuration's Lab start it on `/lab/run`
(`src/chatddx/portal/test/test_trials.py`).

Composed but not kept:

- **The variation**: a configuration's edit with parts replaced, a plain value nothing stores until it is kept.
- **The execution and the canary set**: the endpoint's, with a concurrency and an order a start may give
  (`src/chatddx/api/schemas.py:NewRun`; `docs/backlog.md`, "Execution settings as a component").
- **The scoring**: built when a run is scored, from the person's own expectations and the scorer, rather than written by
  hand. It is derived, not configured.

## The Library today

Drafted: every page of it is rendered on the server, with no island, and every form but translations' is drawn from its
kind's JSON Schema (`src/chatddx/portal/test/test_library.py`, `src/chatddx/portal/test/test_clinicians.py`).

### What it holds

`/library?kind=WORD` has a tab for each word and one for cases (`src/chatddx/portal/threads.py:library`). A word's tab
lists every thread of it the person sees, their own first, configurations of either purpose with their purpose; on the
trial tab, the picked are run together on `/lab/run`. Every kind's deleted threads, and deleted cases, are listed apart
with **Restore**.

Each kind a person writes is begun at `/library/new?kind=WORD` (`src/chatddx/portal/threads.py:beginning`), a
configuration from a recipe, a trial of the cases picked on the case tab, and translations of a configuration's texts. A
field given in the address as `f.NAME` is shown and not asked (`src/chatddx/portal/fields.py:fresh`), as a case's
section gives an appendix its vignette.

Each thread has a page, `/threads/{id}` (`src/chatddx/portal/threads.py:thread_page`;
`src/chatddx/portal/templates/thread.html`), with:

- **About it**: its kind, owner, collaborators, language, origin, tags and description, read-only; a configuration's
  links to it in the Lab.
- **Its origin has moved on** and **What it was compiled for has moved on**, to its owner, each with its **Follow**.
- **What it holds**: version N of M by link, each field one level deep, a reference by its title, and what the version
  changed from the one before (`src/chatddx/portal/changes.py:changes`). To its owner, at the latest version, the fields
  are a form that saves a new version, with a text's language and a scorer's labels, and a configuration's recipe parts
  picked; at an earlier one, **Make it the latest**. The findings of what a person writes.
- **Its runs**, a trial's, with **Run it**.
- **What is said of it** and **Delete it**, to its owner; **Leave it**, to a collaborator; **Fork it as it is**, to
  everyone, for what a person writes.

A field is drawn by its shape (`src/chatddx/portal/fields.py:Field`): a reference picked from the heads of the threads
of its kinds the person sees, an engine by its model's handle; a list of references or of choices one a line; a choice
from its options; a text in a text box, or as text or as JSON where it may be either; and anything else as JSON in a
text box. The fields still written as JSON:

| Word          | Its fields written as JSON                                                                                                                          |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| configuration | `appendix_layout`                                                                                                                                   |
| few_shot      | `messages`                                                                                                                                          |
| prompt        | `segments`                                                                                                                                          |
| output        | `contract`, `json_schema`, `schema_ops`                                                                                                             |
| sampling      | `temperature`, `top_p`, `top_k`, `min_p`, `presence_penalty`, `frequency_penalty`, `repetition_penalty`, `stop`, `max_output_tokens`, `recommended` |
| reasoning     | `thinking_token_budget`, `chat_template_kwargs`                                                                                                     |
| passthrough   | `body`                                                                                                                                              |
| toolset       | `max_rounds`                                                                                                                                        |
| scorer        | `version`, `views`, `resources`, `params`                                                                                                           |
| judge         | `seeds`                                                                                                                                             |
| expectation   | `data`                                                                                                                                              |
| appendix      | `vignette`, given by a case's section                                                                                                               |
| trial         | `seeds`                                                                                                                                             |

Translations are drawn on the server (`src/chatddx/portal/translations.py`): a language at a time, each text beside its
translation with its edges shown, **Leave it out**, and another language by its tag. Above what it holds, the texts the
configurations holding any of its versions send that it doesn't translate, each started from the translation of a
similar text where one is near enough. A configuration holding an earlier version links to the Lab with this one tried
in its place. Translations are begun of a configuration's texts, into a language.

The case tab lists the cases a person sees by their families, their own first and filtered by tag; over the picked, it
takes the expectations shared with them under a schema, from an owner or any, and begins a trial. The Library begins no
case: a case is typed on Home or loaded with a data set. A case's section is `/cases/{id}`, a family's id
(`src/chatddx/portal/cases.py`; `src/chatddx/portal/test/test_clinicians.py`), with what is said of it as a thread's,
its language among it; its bindings as its versions by link, each with its vignette's source, id and fingerprint whole
and what changed from the one before, the text alone at `/cases/{id}/vignette`; its cases at that vignette, with their
appendices and, under each schema, their expectations, and at an earlier binding each case's replacement; and what is
begun of it: a case of its appendices, an appendix of its vignette, and an expectation of a case under a schema. Writing
an appendix or an expectation in place is Review's, which the section links. The API calls a case a family.

### Beside it

- **Review**, `/review/{id}`: a case's vignette, appendices, expectations, runs and scores, its appendices and
  expectations written in place with `AppendixEditor` and `ExpectationEditor`, and scorers with `Composer`
  (`frontend/src/lib/`).
- **Runs**: a run's page halts, resumes, scores again and runs again.
- **World**, `/world` (`src/chatddx/portal/world.py`): what the portal was started in: the World's directory and the
  files it read, the build serving it, its sources, endpoints and hosts, which handle configurations are made for and
  each judge is bound to, and the models by handle. Decided: the portal shows its World whole.

## The Lab today

Drafted: `/lab/{id}` (`src/chatddx/portal/lab.py`; `src/chatddx/portal/test/test_lab.py`) is where a configuration is
varied, run and compared with its lineage, and `/lab` leads to the person's first configuration. In its address are the
variation's query (`schemas.Varying`, its parts, `head`, `under`, `tag`) and its own: `handle`, `family` and `by`.

- **Lineage**, a drawer: its first origin and every fork below it, each with its mean on the set, the higher first.
- **The configuration**: its name, language, origin and translations; its versions by link; **Follow** its origin or its
  corrected facts; the variation's island (`frontend/src/islands/lab.ts`), which tries parts in place of its own, says
  what it makes, runs it and saves it as a version or a fork; and **Its trials**, run through the runner, whose page for
  trials picked in the Library is `/lab/run`.
- **How they fare**: each configuration of the lineage as a column on a set of cases, under each its own model or one
  handle, by its latest run, sorted by a view.

A judge's configuration is tried and saved there too, without how they fare or trials.

## Next

Take: the Library's forms first.

1. **Scalars written as JSON**: the numbers, booleans and lists of texts or integers in the table above, for which
   `src/chatddx/portal/fields.py:Field` has no shape. Take: shapes of their own, on the server: a number box held to its
   schema's type and minimum, a checkbox, and a list one a line.
2. **What Review writes already.** Take: an expectation's `data` drawn from its schema with `ExpectationEditor`, and a
   scorer's `views`, `resources` and `params` with `Composer`, each an island over its text box that writes its JSON
   into it, so that the form posts as it does without scripts.
3. **The rest of the table.** Open: which of its fields earns a control of its own, and whether a form drawn from the
   JSON Schema (`frontend/src/lib/schema/`) takes the rest.
4. **The Lab.** Open:
   - Its cases are picked twice: the island's tags and the tags how they fare is shown over are one `tag` in its
     address, but each has its control, and the island's changes it without showing how they fare again.
   - What `/translate` did that the Library's translations don't: the request a configuration sends into a language, how
     many texts each configuration lacks by language, and that a case in a regional tag, such as `sv-SE`, wants
     translations of its own.

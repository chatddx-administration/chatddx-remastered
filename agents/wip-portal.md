# The portal: work in progress

The portal is the bench's web edge, beside the repl and the API: HTML rendered on the server from the bench, with Svelte
islands where a page needs a round trip. What each page is for is in "Its pages". This starts from the Library, the Lab
and Scoring, which are drafted (see "The Library today", "The Lab today" and "Scoring today"), and has what is next in
"Next". "Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Its pages

Decided:

- **Review**: where clinicians check their vignettes against appendices, scorers and expectations. Self-contained but for
  judges' configurations, which it picks and doesn't edit.
- **Lab**: the evolution of configurations, and queueing trials and seeing how they fare against each other.
- **Scoring**: managing judges and scorers more deeply than Review does.
- **Runs**: everything run-related: what is under way and what is queued, its order, pausing and halting.
- **Library**: drawn from schemas, instructive of the data model rather than practical; still the best place to manage
  translations.
- **World**: a read-only view of the World the portal runs in.

Take: each page by what it writes, what it weighs and what it only picks, so that a thing is written in one place and
weighed where its consequences show.

| Page    | For                     | Writes                                                          | Weighs                                                     | Picks                  |
| ------- | ----------------------- | --------------------------------------------------------------- | ---------------------------------------------------------- | ---------------------- |
| Review  | clinicians              | appendices, expectations, a scorer's views tried on a case      | a case's answers under each view                           | judges, configurations |
| Lab     | researchers             | configurations of either purpose, as variations; trials         | a lineage on a set of cases                                | parts, models          |
| Scoring | researchers             | judges; a scorer's code, resources, parameters and labels       | what a scorer reads and how it scored; a judge's verdicts  | judges' configurations |
| Runs    | whoever runs and scores | the queue: its order, pausing, halting, stopping; scoring again | what is under way, queued and left to score; runs compared | —                      |
| Library | everyone                | any kind, a field at a time; translations                       | versions, what each changed, findings                      | —                      |
| World   | everyone                | nothing                                                         | the World whole                                            | —                      |

Take, the moves it asks for:

1. **What a judge is asked** is changed on Scoring rather than in Review: `JudgeTexts` left `Composer`
   (`frontend/src/lib/scorer/`) for a judge's page. Review keeps making a judge of a configuration, a model and seeds it
   picks (`JudgeEditor`), and asking another, and links a judge to its page. Built.
2. **A judge's configuration** is still varied in the Lab, beside every other configuration. How its judges fare, which
   the Lab leaves out, is on Scoring, and the Lab links to it.
3. **The code a scorer pins**, its metrics and what each measures and takes, is shipped, so it is the World's to show, as
   models are, and Scoring links to it.
4. **Scoring again** stays on Runs, and Scoring links to what is left to score.
5. **The navigation** reads Review, Lab, Scoring, Runs, Library, World: the three benches by who works at them, then what
   runs, the data model and the World. Built.
6. **The name** Scoring, over Judging or Scorers: a run's scoring is what its scorer and judges make of it. Decided, as
   no namespace collides with it: the kind `scoring` stays derived, is a thread kind of the catalog but no word of the
   bench's (`src/chatddx/bench/model.py:KINDS`), so it has no Library tab, no `kind` of the API's threads and no page,
   and nothing plans one.

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
from its options; a number in a number box held to its schema's type and minimum, empty for none where it may be none; a
boolean as a checkbox; a list of texts or of whole numbers one a line, whole numbers apart by commas too, but a list
holding an empty text or a line break as JSON, which one a line can't write; a text in a text box, or as text or as JSON
where it may be either; and anything else as JSON in a text box. The fields still written as JSON:

| Word          | Its fields written as JSON            |
| ------------- | ------------------------------------- |
| configuration | `appendix_layout`                     |
| few_shot      | `messages`                            |
| prompt        | `segments`                            |
| output        | `contract`, `json_schema`             |
| reasoning     | `chat_template_kwargs`                |
| passthrough   | `body`                                |
| scorer        | `views`, `params`                     |
| expectation   | `data`                                |
| appendix      | `vignette`, given by a case's section |

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
- **Scoring**, `/scoring/{id}`: see "Scoring today".
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

## Scoring today

Drafted: `/scoring/{id}` (`src/chatddx/portal/scoring.py`; `src/chatddx/portal/test/test_scoring.py`) shows a scorer or a
judge the person sees, rendered on the server with no island, and writes nothing yet. `/scoring` leads to the person's
first scorer, and the Library's page of a scorer or a judge and Review's scorer lead to theirs.

- **Scorers and judges**: each the person sees, their own first, the scorers by the expectation schema they grade against
  and the judges by the model they are asked under.
- **A scorer**: its views, each with its metric and what it measures, what it picks of an answer and of an expectation,
  its judge, flagged where it asks an earlier version, and its parameters. The configurations whose answers it reads and
  those it doesn't (`src/chatddx/factors/scoring.py:View.offered_by`). How many of the cases the person sees they expect
  something of under its schema, with those to choose from and those without, each linking to Review. How it scored:
  the person's runs scored by this version, by their mean under each view, compared on `/runs/compare`. Its findings.
- **A judge**: its configuration, linking to the Lab, its model, seeds, fill rule, and the endpoint it is served at now
  or why none. The views of the scorers asking it, by the version of it each asks, or the judge it is forked from, and
  for each scorer asking another, following its latest version: the views asking another are pointed at it, in a new
  version of the person's own scorer or a fork of another's, with its labels. What it is asked, rendered with its
  first seed, a placeholder for the answer, and what a view asking it picks of what a case expects, both picked on the
  page and by default the first such view and the first case it reads something of. What it is asked is changed in
  place with `JudgeTexts` (`frontend/src/islands/scoring.ts`), previewed against the same pick: saving keeps the texts,
  the judge's configuration and the judge as the person's own, and leads to that judge's page. Its verdicts, over the latest score of the person's runs under each scorer
  asking any version of it: the items judged, how many its seeds agree on, how many a seed gave none for, the mean, and
  the items where its seeds disagree. These are the values a view's metric read of each seed's verdict, kept in the
  item's detail, never the verdicts, which are sensitive. Its findings.

## Next

Take: the Library's forms first.

1. **What Review writes already.** Take: an expectation's `data` drawn from its schema with `ExpectationEditor`, and a
   scorer's `views` and `params` with `Composer`, each an island over its text box that writes its JSON
   into it, so that the form posts as it does without scripts.
2. **The rest of the table.** Open: which of its fields earns a control of its own, and whether a form drawn from the
   JSON Schema (`frontend/src/lib/schema/`) takes the rest.
3. **The Lab.** Open:
   - Its cases are picked twice: the island's tags and the tags how they fare is shown over are one `tag` in its
     address, but each has its control, and the island's changes it without showing how they fare again.
   - What `/translate` did that the Library's translations don't: the request a configuration sends into a language, how
     many texts each configuration lacks by language, and that a case in a regional tag, such as `sv-SE`, wants
     translations of its own.
4. **Scoring.** Take, in order:
   - Making and changing a judge on its page with `JudgeEditor`, and its versions by link as the Lab's, each with how it
     scored; how a scorer scored lists its shown version's runs only.
   - A judge against a judge: two judges, or two versions of one, on the same items. It takes scoring the same runs under
     a scorer asking the other, which Runs does a run at a time. Open: judging scored items again without a run.
   - A judge against a clinician: measuring a judge by real answers (`docs/backlog.md`, "The sample's judge") compares
     its verdicts with a clinician's on the same answers, and nothing stores a clinician's verdict on an answer: an
     expectation is written of a case, before any answer. Open, where it is kept: a kind of its own, of an answer and a
     view, or an expectation written of an answer rather than of a case.
   - A scorer's coverage said before a run is scored, as its page says it, which the backlog asks of the scoring
     (`docs/backlog.md`, "Scoring: coverage and judges").
   - Cost: a judge's verdicts read every score of every run any of its versions scored, which is fine for the test World
     and wants a query of its own once measured (`docs/backlog.md`, "Performance, once measured").

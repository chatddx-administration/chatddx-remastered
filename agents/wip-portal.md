# The portal: work in progress

The portal is where clinicians review and researchers research, assume they're tech-illiterate with little time and
cognitive reserves.

## Its pages

- **Review**: where clinicians check their vignettes against appendices, scorers and expectations. Self-contained but
  for judges' configurations, which it picks and doesn't edit.
- **Lab**: the evolution of configurations, and queueing trials and seeing how they fare against each other.
- **Scoring**: managing judges and scorers more deeply than Review does.
- **Runs**: everything run-related: what is under way and what is queued, its order, pausing and halting.
- **Library**: schema driven, instructive of the data model rather than practical. Translations stay in the Library,
  which is the de facto translation page as long as its UX and the Library's philosophy are aligned.
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
3. **The code a scorer pins**, its metrics and what each measures and takes, is shipped, so it is the World's to show,
   as models are, and Scoring links to it.
4. **Scoring again** stays on Runs, and Scoring links to what is left to score.
5. **The navigation** reads Review, Lab, Scoring, Runs, Library, World: the three benches by who works at them, then
   what runs, the data model and the World. Built.
6. **The name** Scoring, over Judging or Scorers: a run's scoring is what its scorer and judges make of it. Decided, as
   no namespace collides with it: the kind `scoring` stays derived, is a thread kind of the catalog but no word of the
   bench's (`src/chatddx/bench/model.py:KINDS`), so it has no Library tab, no `kind` of the API's threads and no page,
   and nothing plans one.

## The look

The pages are HTML documents, and their look follows from what each element does: `frontend/src/portal.css` styles a
button by being a button and a link by what clicking it does, so a template carries a word of what it is rather than
the utilities of how it looks, and no macro draws a button or a link.

Drafted:

- **Contrast**: text at 4.5:1 at least on a pane, inputs' outlines at 3:1, in both colour schemes; panes solid and
  bordered, and lighter than the page in dark mode, darker than it in light.
- **Buttons**: a `<button>` does something. A template's carries only its kind: none for most, `primary` for a form's
  main action, `danger` for what deletes, both for what stops at once, `small` for one in a row. Pressed, it sits a
  pixel lower and darker.
- **Links**: an `<a>` goes somewhere, by what clicking it does:

| Kind       | Clicking it                                                      | Marked by          | Looks                                                   |
| ---------- | ---------------------------------------------------------------- | ------------------ | ------------------------------------------------------- |
| thing      | opens a thing's own page                                         | nothing            | underlined, in the primary colour                       |
| navigation | moves around the portal: the header, sidebars, tabs, breadcrumbs | being in a `<nav>` | not underlined; the current one barred under, or beside |
| jump       | moves down the page                                              | `href="#…"`        | a thing's, with ↓                                       |
| bench      | takes a thing to another bench                                   | `bench`            | a thing's, with →                                       |
| begin      | opens a form that writes something new                           | `begin`            | a thing's, with +                                       |
| view       | changes what the page shows: filters, sorting, paging, versions  | `view`             | grey and dotted; the one in effect bold, with ✓         |

- **Headings**: a section's title in a header ruled off across its pane
  (`src/chatddx/portal/templates/macros.html`), a bare `h2` a pane's title and a bare `h3` a part of one; small
  capitals only over a table's columns.
- **A press**: the script in `src/chatddx/portal/templates/base.html` marks what was pressed and runs a bar along the
  top until the next page comes, and keeps a form from being sent twice meanwhile; Back, and Stop where the browser has
  the Navigation API, clear it.

Open:

- The benches keep their own compact headings, as their `h1` is as large as a section's title.
- Inputs, selects and text boxes are still styled by utilities in each template.
- The islands' buttons and links are shadcn's or utilities, of none of these kinds yet.

## The Library

The Library is for schema driven views, threads fit right in, but cases, runs, configurations and translations do not
and are squeezed in for completeness.

Drafted: every page of it is rendered on the server, with no island, and every form but translations' is drawn from its
kind's JSON Schema (`src/chatddx/portal/test/test_library.py`, `src/chatddx/portal/test/test_clinicians.py`).

Decided, for the internal deploy where clinicians and researchers work on the sample data from the first `init-data`:

- **The sidebar**: the kinds under headings, the headings and the kinds under each sorted alphabetically, always open,
  no deeper tree: what refers to what is a graph, not a hierarchy, and a collapsed branch hides a kind from a person
  with little time.
- **The giftbag stays**: the deploy loads each person with `init-data <login> --giftbag`, so what it forks reads as
  theirs, beside the archive's.
- **A vignette's text stays out of the Library**, deliberately: a case's section links to it on a page of its own.
- **No sample trials for now**: data sets load none, so the trial shelf starts empty, says how a trial is begun, and
  points to the Lab, which runs a configuration on cases straight away.

### What it holds

`/library` is an overview of the shelves (`src/chatddx/portal/shelves.py:SHELVES`): each kind under its heading with
what it is in a line, how many of it are the person's own and how many are shared with them, and whether data sets load
it. The same shelves, with how many of each the person sees, are the sidebar of `/library?kind=WORD`
(`src/chatddx/portal/threads.py:library`), which says what the kind is and lists every thread of it the person sees,
their own first, a fork with what it is forked from, configurations of either purpose with their purpose; on the trial
tab, the picked are run together on `/lab/run`, and with none it says how one is begun. The kind's deleted threads, or
deleted cases, are listed under it with **Restore**.

A shelf is found in by words, `q`, each of which its name, owner, tags or description holds, and says how many of how
many it shows; an expectation's by the schema it is written to as well, picked where the person sees more than one. Each
row says under its name what is said of it, and the columns a phone has no room for are left out there. On the case and
trial shelves, **Pick every one shown** picks them without scripts, and what is done with the picked stays in view below
the list as it scrolls.

What the giftbag forks for a person carries its origin's tags and description, and an unnamed origin's title as its name
(`src/chatddx/curation/write.py:_Init.giftbag`), so that the person's shelves read as the archive's do.

Each kind a person writes is begun at `/library/new?kind=WORD` (`src/chatddx/portal/threads.py:beginning`), a
configuration from a recipe, a trial of the cases picked on the case tab, an appendix of the case picked first, and
translations of a configuration's texts. A field given in the address as `f.NAME` is shown and not asked
(`src/chatddx/portal/fields.py:fresh`), as a case's section gives an appendix its vignette.

A form refused for what was typed in it is shown again, with what was typed and why it was refused, by the field it
concerns where it concerns one (`src/chatddx/portal/fields.py:kept`), and so are an empty pick on the case tab or a
case's section and a language that isn't a tag; what isn't the person's to set right is answered as the API answers it
(`src/chatddx/portal/pages.py:refusable`).

Each thread has a page, `/threads/{id}` (`src/chatddx/portal/threads.py:thread_page`;
`src/chatddx/portal/templates/thread.html`), with:

- **About it**: its kind, owner, collaborators, language, origin by name, tags and description, read-only; a
  configuration's links to it in the Lab.
- **Its origin has moved on** and **What it was compiled for has moved on**, to its owner, each with its **Follow**.
- **What it holds**: version N of M by link, each field one level deep, a reference by its title, linked to the thread
  holding it where the person sees one and a case to its section, and what the version changed from the one before
  (`src/chatddx/portal/changes.py:changes`). A configuration's recipe comes first, what it sends folded under it, and
  what a version changed is what it changed in its recipe, by the parts' titles, where it changed any. To its owner, at
  the latest version, the fields are a form that saves a new version, with a text's language and a scorer's labels, and
  a configuration's recipe parts picked, each linked to the one picked; at an earlier one, **Make it the latest**. The
  findings of what a person writes.
- **Its runs**, a trial's, with **Run it**.
- **What is said of it** and **Delete it**, to its owner; **Leave it**, to a collaborator; **Fork it as it is**, to
  everyone, for what a person writes.

A field is drawn by its shape (`src/chatddx/portal/fields.py:Field`): a reference picked from the heads of the threads
of its kinds the person sees, an engine by its model's handle; a list of references or of choices one a line; a choice
from its options; a number in a number box held to its schema's type and minimum, empty for none where it may be none; a
boolean as a checkbox; a list of texts or of whole numbers one a line, whole numbers apart by commas too, but a list
holding an empty text or a line break as JSON, which one a line can't write; a text in a text box, or as text or as JSON
where it may be either; and anything else as JSON in a text box. The fields still written as JSON:

| Word          | Its fields written as JSON |
| ------------- | -------------------------- |
| configuration | `appendix_layout`          |
| output        | `json_schema`              |
| reasoning     | `chat_template_kwargs`     |
| passthrough   | `body`                     |
| scorer        | `params`                   |

Take: these stay JSON, as what they hold is whatever a request, a template or a schema takes, or mostly whitespace,
which JSON shows; each is checked as it is typed, and its form isn't sent while it doesn't hold JSON of its shape.

With scripts, the Library's island (`frontend/src/islands/library.ts`) draws an editor over the text box of what the
page asks it to (`src/chatddx/portal/editors.py:editors`), and writes into the box only what is changed in it, so that a
form posts as it does without scripts and one sent as it is writes nothing; **Write it as JSON** shows the box again. A
text with inserts or slots, an instructions' `text`, an output's `guidance` and a prompt's `segments`, is written as
text with the inserts and slots it may hold as markers (`TextSegments`); an expectation's `data` by its schema's form
(`SchemaField`), once its schema is picked, and a few-shot's `messages` and an output's `contract` by theirs, a union of
contracts by the kind each fixes; a scorer's `views` and their labels as Review composes them (`ScorerViews`), and its
`params` by the schema its code publishes, where it publishes properties. A new scorer pins the code chatddx ships,
shown and not asked. An expectation's case and schema are shown and not asked on its page, as Review carries it to a
case that replaces its own, and a case is picked by its title.

Translations are drawn on the server (`src/chatddx/portal/translations.py`): a language at a time, each text beside its
translation with its edges shown, **Leave it out**, and another language by its tag. Above what it holds, the texts the
configurations holding any of its versions send that it doesn't translate, each started from the translation of a
similar text where one is near enough. A configuration holding an earlier version links to the Lab with this one tried
in its place. Translations are begun of a configuration's texts, into a language.

The case tab lists the cases a person sees by their families, their own first and narrowed by the tags picked, each of
them; over the picked, it takes the expectations shared with them under a schema, from an owner or any, and begins a
trial. The Library begins no case: a case is typed on Home or loaded with a data set. A case's section is `/cases/{id}`,
a family's id (`src/chatddx/portal/cases.py`; `src/chatddx/portal/test/test_clinicians.py`), with what is said of it as
a thread's, its language among it; its bindings as its versions by link, each with its vignette's source, id and
fingerprint whole and what changed from the one before, the text alone at `/cases/{id}/vignette`; its cases at that
vignette, with their appendices and, under each schema, their expectations, and at an earlier binding each case's
replacement; and what is begun of it: a case of its appendices, an appendix of its vignette, and an expectation of a
case under a schema. Writing an appendix or an expectation in place is Review's, which the section links. The API calls
a case a family.

## The Lab

The Lab is where researchers combine what exists already and try to run it, the evolution of configurations
(`docs/chatddx.md`, "Intended evolution of configurations").

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

A judge's configuration is tried and saved there too, without how they fare, running it, its runs or trials.

## Scoring

Drafted: `/scoring/{id}` (`src/chatddx/portal/scoring.py`; `src/chatddx/portal/test/test_scoring.py`) shows a scorer or
a judge the person sees, rendered on the server with no island, and writes nothing yet. `/scoring` leads to the person's
first scorer, and the Library's page of a scorer or a judge and Review's scorer lead to theirs.

- **Scorers and judges**: each the person sees, their own first, the scorers by the expectation schema they grade
  against and the judges by the model they are asked under.
- **A scorer**: its views, each with its metric and what it measures, what it picks of an answer and of an expectation,
  its judge, flagged where it asks an earlier version, and its parameters. The configurations whose answers it reads and
  those it doesn't (`src/chatddx/factors/scoring.py:View.offered_by`). How many of the cases the person sees they expect
  something of under its schema, with those to choose from and those without, each linking to Review. How it scored: the
  person's runs scored by this version, by their mean under each view, compared on `/runs/compare`. Its findings.
- **A judge**: its configuration, linking to the Lab, its model, seeds, fill rule, and the endpoint it is served at now
  or why none. The views of the scorers asking it, by the version of it each asks, or the judge it is forked from, and
  for each scorer asking another, following its latest version: the views asking another are pointed at it, in a new
  version of the person's own scorer or a fork of another's, with its labels. What it is asked, rendered with its first
  seed, a placeholder for the answer, and what a view asking it picks of what a case expects, both picked on the page
  and by default the first such view and the first case it reads something of. What it is asked is changed in place with
  `JudgeTexts` (`frontend/src/islands/scoring.ts`), previewed against the same pick: saving keeps the texts, the judge's
  configuration and the judge as the person's own, and leads to that judge's page. Its verdicts, over the latest score
  of the person's runs under each scorer asking any version of it: the items judged, how many its seeds agree on, how
  many a seed gave none for, the mean, and the items where its seeds disagree. These are the values a view's metric read
  of each seed's verdict, kept in the item's detail, never the verdicts, which are sensitive. Its findings.

## Next

Take: the Library's forms first.

1. **What Review writes already.** Built: an expectation's `data`, a scorer's `views` and a text's inserts, each an
   editor over its text box.
2. **The rest of the table.** Built: a few-shot's `messages` and an output's `contract` by their schema's form, the
   rest as JSON checked as it is typed.
3. **The Lab.** Open:
   - Its cases are picked twice: the island's tags and the tags how they fare is shown over are one `tag` in its
     address, but each has its control, and the island's changes it without showing how they fare again.
   - What `/translate` did that the Library's translations don't: the request a configuration sends into a language, how
     many texts each configuration lacks by language, and that a case in a regional tag, such as `sv-SE`, wants
     translations of its own.
4. **Scoring.** Take, in order:
   - Making and changing a judge on its page with `JudgeEditor`, and its versions by link as the Lab's, each with how it
     scored; how a scorer scored lists its shown version's runs only.
   - A judge against a judge: two judges, or two versions of one, on the same items. It takes scoring the same runs
     under a scorer asking the other, which Runs does a run at a time. Open: judging scored items again without a run.
   - A judge against a clinician: measuring a judge by real answers (`docs/backlog.md`, "The sample's judge") compares
     its verdicts with a clinician's on the same answers, and nothing stores a clinician's verdict on an answer: an
     expectation is written of a case, before any answer. Open, where it is kept: a kind of its own, of an answer and a
     view, or an expectation written of an answer rather than of a case.
   - A scorer's coverage said before a run is scored, as its page says it, which the backlog asks of the scoring
     (`docs/backlog.md`, "Scoring: coverage and judges").
   - Cost: a judge's verdicts read every score of every run any of its versions scored, which is fine for the test World
     and wants a query of its own once measured (`docs/backlog.md`, "Performance, once measured").

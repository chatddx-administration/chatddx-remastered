# Olof's view: work in progress

A page in the portal where a clinician sees vignettes, writes appendices, edits expectations and composes scorers,
with or without judges, around one case at a time. Olof stands in for that clinician: someone who works best with a
simple, clear interface where everything needed to review a case fully, and everything around it, is a saccade away
rather than a click, a scroll or another page.

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **It can be done.** The bench and the API write everything the page needs: appendices, cases, expectations,
   scorers with their labels, and judges (`docs/api.md`, "Forking and editing"). The portal already has the
   clinicians' half (`agents/wip-portal.md`, 5b). The scorer and judge editors (5d) are missing, as is a way to see
   what a view picks and scores before anything is saved, and a way to read answers to a case that isn't one's own
   run (see "The landscape").
2. **The page gathers what is spread over today's pages.** The vignette is at `/families/{id}/vignette`; appendices,
   cases and expectations are at `/families/{id}`; an expectation's versions are at `/threads/{id}`; scorers have no
   editor; and answers and scores are at `/runs/{id}`, one run at a time.
3. **Decided: the takes on L1 to L7** (see "The landscape"): Olof holds both roles; the island fetches what is
   sensitive from the API's places; he runs the case himself; judges are picked and written before their texts;
   unjudged views are tried as typed, judged ones by scoring; selectors are picked and applied on the server; and the
   page is `/review/{family}`, beside the family's page.
4. **Steps 1 to 6 are built** (see "Built"); what is left is in each step's "What step N leaves" and in "Open".

## What the clinician is here to do
From the request, and from what the sample World waits on (`docs/curation.md`, "Outstanding"):
- **Read the case**: the vignette, with the appendices of the case picked, in order; the family's language and tags;
  whether the vignette has drifted.
- **Write appendices** bound to the vignette, and build cases from them; give an appendix a new version, and move
  their expectation onto the cases that replaced the old ones.
- **Edit expectations**: the targets, and the notes for judges. Revise the targets where the notes disagree, as on
  `Dutchfall11w` (shock, most likely sepsis, where the targets have an aortic aneurysm or a dissection).
- **Compose scorers**: views that pick from the answer and from the expectation, with a metric, and a judge where the
  metric reads one; labels; save.
- **Write the judge**: Olof's prompt replaces the sample's draft judge, as an edit. It settles which of the comment and
  the answer the judge reads, how a Swedish note is read against an English answer, verdict or scale, strictness, and
  the engine and seeds. This is 5c work (a judge's texts), and the sample's judges wait on it.
- **See how answers fare**: the answers to the case, each view's value and the judges' verdicts, so that a target, a
  note, a view or a prompt can be corrected with its effect in view.

## What exists to build on
| To do | Built below the page | In the portal now | Missing |
|---|---|---|---|
| Read the vignette | `GET /api/families/{id}/vignette`, `no-store` | its own page | nothing |
| Appendices, cases | `POST /api/families/{id}/appendices`, `…/cases`, an appendix's edit | the family's page, `AppendixEditor` | nothing |
| Expectations | new, fork, edit, take, carry; `POST /api/components/check` | `ExpectationEditor`, drawn from the schema | nothing |
| Versions of a thread | `GET /api/threads/{id}/edits` | `Thread.svelte`, jsdiff | nothing |
| Scorers | new, fork, edit with `labels`; `GET /api/scorer-code` (metrics, what each measures, its params' schema, whether judged) | the thread's page, read only | the editor (5d) |
| Judges | new, fork, edit over a judge configuration, an engine and seeds | the thread's page, read only | the editor (5d) |
| A judge's texts | chunks new, fork, edit; a configuration from a recipe | the variation page varies a judge configuration | text editors (5c) |
| What a view picks | `chatddx.factors.select:select`, `View.offered_by` | the variation page's reach | a route that gives the picks |
| A view's value before saving | `chatddx.scorers.scorer:score_view`, pure for unjudged views | none | a route |
| Answers to the case | `GET /api/runs?reaching=CASE` (a trial's references followed), `GET /api/runs/{id}/items` | a run's page | only the person's own runs |
| Scores of those answers | `GET /api/runs/{id}/scores`, `…/scores/{score}/items` | a run's page, values only | per-item detail and judge calls in the portal |
| Running the case | `POST /api/runs` | the variation page, the home page | a short form on this page |

The test World has what the page needs to be tested on: `judged` and `appendix` among the scripted runs
(`docs/scripted.md`), notes by placeholder authors (carol, dave), and the `verdict`, `graded` and `remote` judges.

## The page
A sketch, at a wide screen. The page fills the window rather than the 5xl column the other pages keep, and each pane
scrolls on its own. Decided, from the user's first look at step 1: two columns are the main actors, the case and what
is expected of it with what reads it; the list of cases and the record of answers are drawers at the sides, folded to
a rail.

```
┌▲┬ the case ─────────────────────┬ expected ─────────────── under Targets ┬R┐
│C│ Dutchfall11w · en · tags      │ Read by  [diagnoses] [free-text] [notes]│e│
│a│ [vignette alone] [+ ultrasound]│ diagnosis   pattern  aaa | (abdominal… │c│
│s│                               │  │ text · first mention  reads pattern… │o│
│e│ the vignette …                │  │ differential · reciprocal rank  …    │r│
│s│                               │ disposition pattern  surg* | operat* … │d│
│ │ ── appendices, in order ──    │ notes       Olof · sv · comment …      │ │
│2│ ultrasound: …    Change it    │  │ comment · verdict · judge  reads …   │1│
│▼│ ▸ Add to it                   │ [Save] a new version   ▸ versions      │ │
└─┴───────────────────────────────┴────────────────────────────────────────┴─┘
```

- **Cases**, a drawer at the left: the families the person sees, by tag, each marked by what the person holds for it
  under the schema shown. Folded, its rail steps to the case before and after; so do `j` and `k`.
- **The case**: the vignette, then the case's appendices in order, as additions to it, each changed in place; a switch
  between the family's cases; and, folded, writing an appendix and building a case.
- **Expected**: the expectation for the case picked under the schema picked, in the 5b editor, with each view of the
  scorer picked under the field it reads, and what it picks as it is typed; its versions with what each changed;
  those shared to take; moving the person's own onto a replacing case.
- **Record**, a drawer at the right: the answers to the case in the person's runs, each view's value and its mean,
  each answer folded with its detail and the judges' calls. A record to read, not a place to write.

The address keeps what is picked, as the variation's page does: `/review/{family}?case=DIGEST&schema=DIGEST&scorer=ID`.

## The landscape
Questions that change what is built, each with its options. Decided: the take on each.

### L1. Roles
`docs/chatddx.md` ("Roles mentioned") names clinicians as the authors of appendices and expectations, and researchers
as the authors of judges and of "a scorer's views, free parameters and labels"; its requirements say the same. A
person may hold several roles, and nothing checks roles yet (`agents/wip-portal.md`, W10; Z1), so nothing refuses
Olof composing a scorer. But a page built for a clinician that composes scorers and judges either has Olof acting as
a researcher there, or moves scorers into the clinicians' column.
- **(a)** Olof holds both roles; the page is a clinician's that also offers a researcher's composing. Nothing in the
  docs changes. Z1 later shows the scoring pane to whoever holds the researcher role.
- **(b)** Clinicians compose scorers, with judges, as well: a suggestion to `docs/chatddx.md`'s roles, for a human to
  write.
- **(c)** Clinicians compose scorers from views a researcher set up, picking expectation parts and judges only.

Decided: (a). It needs no change to the primary document, and Z1 has to answer which panes a role sees anyway.

### L2. The vignette's place
What is made from a vignette is shown "only in its own places, so that a policy for edges can gate those few"
(`docs/api.md`, "Sensitive content"), and the portal gave the vignette a page of its own (`agents/wip-clearance.md`,
"Open", 5). Here it sits beside everything else.
- **(a)** The page's island fetches the vignette from `GET /api/families/{id}/vignette`, and answers and score details
  from `GET /api/runs/{id}/items` and `…/scores/{score}/items`. The HTML holds nothing sensitive, the places stay the
  API's four, and a refusal from a future gate shows in its own pane. Without scripts the page shows no vignette; the
  vignette's page still does.
- **(b)** The server draws the vignette into the page through the same handler (`api.vignette`), so a gate in the
  handler covers it, and the page becomes a fifth place in `docs/api.md`'s list.

Decided: (a).

### L3. Whose answers
A person sees only their own runs, and being a collaborator on a run shows nothing (`docs/bench.md`, "What a person
sees"). A clinician who doesn't start runs has no answers to review, and a researcher's runs are scored against the
researcher's expectations (`docs/bench.md`, "What a person is scored against").
- **(a)** Olof runs the case himself from the page: a configuration, an endpoint and seeds, scored by his scorers
  against his expectations. This matches how his judge is to be measured: "real answers from pelle and malborg on
  `Dutchfall11w`, `Dutchfall1w` and `casesfromedn1`" (`docs/curation.md`, "Outstanding").
- **(b)** Runs can be shared: a collaborator reads a run's items and scores. That changes `docs/bench.md`, which is
  solidified (a suggestion there), and asks whose expectations a shared run is scored against for the reader.
- **(c)** A reviewer reads across people's runs by role, through Z1.

Decided: (a) now; (b) stays open.

### L4. How deep "with judges" goes
- **(a)** A view picks a judge the person sees.
- **(b)** The person writes a judge over a judge configuration they see: an engine (by the endpoint serving it),
  seeds and the fill rule. This is the judge's 5d form.
- **(c)** The person also writes the judge's texts, its instructions and prompt of purpose `judge`, and a judge
  configuration from a recipe. That needs 5c's text editor (a text that knows its slots and inserts) and a
  configuration made from a recipe. It is what Olof's prompt needs.

Decided: (a) and (b) first, then (c), limited at first to a judge's texts. Beside every judge, what it is asked: the
judge configuration's request with the `expectation` slot filled from the view's picks of this case's expectation,
which isn't sensitive, and the `completion` left as a placeholder.

### L5. Trying a scorer before saving it
- **(a)** Unjudged views are scored as they are typed, against the answers to the case among the person's runs and
  the expectation as typed, with nothing written (`score_view` is pure). This needs a new route, whose answer is
  sensitive, since a detail quotes the answer (`"answer": "3. Septic shock"`). It is `no-store` and joins
  `docs/api.md`'s list of places.
- **(b)** Judged views are tried only by scoring: save, then **Score again** on the case's runs, which the worker
  queues and the ledger records. Judge calls sent while trying, and not recorded, would be exchanges outside the
  ledger, which is there to "record each exchange within the cage" (`docs/chatddx.md`, "Purpose").

Decided: (a) and (b).

### L6. Selectors
A view's selectors are a JSON Pointer or a fixed subset of JSONPath (`docs/factors.md`, "View"), such as
`$.notes[?@.author == 'Olof'].comment`. No clinician should have to type that.
- **Writing them**: (a) typed, with the picks shown live; (b) picked from the expectation schema and from the output
  schemas of the configurations the person sees ("notes by Olof → comment"), which writes the selector, with typed
  as the way out. Decided: (b).
- **What they pick, live**: (a) a route that applies them on the server, one implementation
  (`chatddx.factors.select`, 452 lines); (b) a port to TypeScript, tested against the Python on shared cases.
  Decided: (a). Built in step 1 as `POST /api/picks`: selectors and a document in, what each picks out, or why it
  doesn't read (see "Built").

### L7. Where the page stands among the others
- **Its place**: (a) a new page, `/review/{family}`, with Review in the nav opening the first case of the list;
  (b) the family's page becomes it; (c) a new page now, and the family's page folded into it once it has proved itself.
  Decided: (c). The family's page stays the one without scripts, and keeps 5b's browser test.
- **5c and 5d** (`agents/wip-portal.md`, "Authoring"): the scorer and judge editors are built here as components, and
  the thread's page uses the same ones for a scorer's and a judge's `/threads/{id}`. So this page builds 5d, and 5c's
  text editor arrives with L4 (c). Decided: as said, and `agents/wip-portal.md` points here for them.
- **Its name**: the address and the page's title name no person. Decided: `/review` and "Review"; the tests keep
  to alice, bob and carol (AGENTS.md, "Placeholder username").

## Smaller choices, as takes
- **The expectation's form** as 5b's, with a note's author offered as the person's name, and the language offered as
  the family's. The keys still follow the schema alphabetically (`agents/wip-portal.md`, "What the first half of
  authoring leaves"), although the canonical form keeps JSON data's order (`docs/factors.md`, "Canonical form and
  digest"). Where they get sorted is worth finding first: the order matters more here, where the form is read beside
  the vignette.
- **A scorer's entry point** is picked silently while one is shipped (`chatddx.scorers.metrics:score`, version 2).
  Resources aren't offered (`docs/bench.md`, "Outstanding").
- **A view's reach** is shown beside it: whether the configurations the person sees answer what it reads from the
  answer (`View.offered_by`), so a view that nothing answers says so.
- **Labels** are written with the views and move with them (`docs/catalog.md`, "Scorer labels").
- **Saving** says where a save goes, as W8 does. A scorer of the archive's is forked into the person's own.
- **The archive's expectations** reach Olof as they reach anyone: taken, or given by `chatddx init-data LOGIN
  --giftbag`. His corrections reach a researcher who took from him as proposals. Nothing hands the archive's threads
  over to him (`docs/bench.md`, "What is said about a thread").

## Steps
1. **The page, read only**, built (see "Built"): the list of cases, the case (vignette fetched, appendices, cases),
   the expectation, the scorers that read its schema with what each view picks from it, and the person's answers to the
   case with each view's value and detail. Needs the route that gives picks (L6).
2. **Writing in place**, built (see "Built"): appendices, cases and expectations, with 5b's editors moved into the
   panes; the picks follow the form as it is typed.
3. **Running the case** from the page (L3 a), and **Score again** on its runs, built (see "Built").
4. **Composing a scorer without judges**, built (see "Built"): the views' form, selectors picked (L6), values tried as typed (L5 a),
   saving with labels.
5. **With judges**, built (see "Built"): picking one, writing one (L4 a, b), what it is asked, and judged views scored through the worker
   (L5 b).
6. **The judge's texts** (L4 c), with 5c's text editor, built (see "Built").

Tests, as the portal's: the pages by `TestClient` on `ran`; the new routes in the API's tests, with `no-store` pinned
where they are sensitive; vitest for the panes' logic; and a browser test of a clinician's flow on the test World:
the case `noted` that `judged` ran, its note edited, a view's picks following it, a pattern view's value changing as
the pattern is typed, a scorer saved, and its score.

## Built
### Step 1: the page, read only
- **The API**, suggested to `docs/api.md` and `docs/api-api.md` as `AGENT` blocks: `POST /api/picks`
  (`src/chatddx/api/world.py:picks`), selectors and a document in, and out each selector's picks, by
  `chatddx.factors.select`, or why it doesn't read; and `case` on a run's items and on a score's items, so that the
  island reads one case's alone.
- **`/review`** opens the first family of the list, keeping its tag; **`/review/{family}`** takes `case`, `schema`,
  `scorer` and `tag` (`src/chatddx/portal/review.py`, `templates/review.html`). Review is first in the nav.
  - **Cases**: the families the person sees, by tag, each marked by whether they hold an expectation of their own under
    the schema shown, or several to choose from, and whether their runs answered it. `j` and `k` step through them,
    keeping the schema and the scorer.
  - **The case**: the family's language, tags, owner and page; its cases, the bare one as "the vignette alone"; the
    vignette, fetched by the island from `GET /api/families/{id}/vignette`; and the case's appendices in order, each
    linking its thread.
  - **Expected**: the person's expectation under the schema, drawn from its data (an object's keys as terms, a list's
    items boxed, `false` as "none expected", a pattern in monospace), linking its thread's page to change it; else
    where to write one, and those shared to take.
  - **Scored**: the scorers that read the schema, the person's own first, and by default the first that scored an
    answer to the case. Each view's label, metric (what it measures on hover), judge, and expectation selector, and
    what it picks from the expectation through `picks`, or that it picks nothing.
  - **Answers in your runs**: the runs over the case (`GET /api/runs?reaching=CASE`, 50 at most), an item each, with
    its outcome and the scorer's value under each view. Unfolded, the island fetches the item's answer, and each view's
    detail and judge calls, for the case alone; a management plan is drawn as on a run's page, and the item is linked
    there.
  - **Nothing sensitive in the HTML** (L2): without scripts, the vignette and the answers are links to their pages.
- **The layout**: four panes filling the window from 1280 px wide, each scrolling on its own; two columns from 1024
  px, with the list of cases above and capped; one column below that. Step 2 replaced it (see "The page").
- **The island**: `frontend/src/islands/review.ts`, with `frontend/src/lib/review/`: `Vignette.svelte`,
  `Answer.svelte`, and `review.ts`, the keys and each view's value and detail.
- **Tests**: `src/chatddx/portal/test/test_reviewing.py` on `ran`; the API's `test_world.py` (picks) and
  `test_runs.py` (one case's items); `frontend/src/lib/review/review.test.ts`; and by hand on the sample World in
  Chromium, as a person given the archive's expectations (`chatddx init-data LOGIN --giftbag`) with its scripted runs,
  in light, dark and narrow.

#### What step 1 leaves
- **Its cost**: about 0.75 s a page on the sample World's 99 families, against 0.6 s for a family's page. The marks
  ask `Bench.expectation` once per family, and each answer's run is read whole (`GET /api/runs/{id}`, its check
  included) for its items and scores.
- **A run scored by an earlier version** of the scorer shows "not scored by it": values are matched by the head's
  digest.
- **What a view reads of the answer**, and its reach, aren't shown: step 4.

### Step 2: writing in place, and the layout of "The page"
- **Two columns and two drawers** (`templates/review.html`): the drawers are `details` elements, folded to a rail
  from 1280 px wide and to a bar below that, which the island opens as the person last left them (`localStorage`,
  per viewer, `review.cases` and `review.record`). The record adds each view's mean over the answers listed.
- **The expectation, edited in place** (`frontend/src/lib/review/Expected.svelte`): the 5b editor, open, its own
  versions folded below it with what each changed (`frontend/src/lib/thread/Changed.svelte`), saving back to the
  review; a case without one of the person's starts from the family's case's, as on the family's page. Each view of
  the scorer picked is shown under the top-level field its expectation selector starts in
  (`frontend/src/lib/review/review.ts:fieldOf`), with what it picks of the form as typed, by `POST /api/picks` a
  moment after each change; a view of the whole expectation, or of a field not written, is listed after the form.
- **The schema's form, quiet** (`frontend/src/lib/schema/SchemaField.svelte`, `quiet`): descriptions on hover rather
  than under every field, the outer box gone, and long texts growing with what they hold. `beside` renders a snippet
  under each top-level field; `ExpectationEditor` takes `opened`, `changed`, `beside`, `quiet` and `to`, and
  `AppendixEditor` and `Saving` take `to`, where a save goes instead of the thread's page.
- **An appendix changed in place**: its editor, unfolded under it, saves a new version and returns to the case that
  replaced the one shown (`review.ts:replaced`).
- **Writing an appendix and building a case** without leaving the page: `POST /review/{family}/appendices` and
  `POST /review/{family}/cases` (`src/chatddx/portal/review.py`), which share their checks with the family's page's
  (`src/chatddx/portal/families.py`: `written_for`, `appended`, `built`) and lead back, the second to the case built.
- **Taking and carrying** as on the family's page, plain forms leading back to the review.
- **Tests**: `test_reviewing.py`, the editor's props, writing and building in place, and the record's means;
  vitest for `fieldOf`, `shortly` and `replaced`; and the browser test of the plan's "Tests"
  (`test_browser.py::test_a_clinician_reviews_a_case_and_its_views_read_what_is_typed`): a note and a pattern typed
  and read by their views, saved as a version, an appendix written, a case built of it starting from the family's
  case's expectation, and `j`.

#### What step 2 leaves
- **The fields' order** is still the schema's keys sorted (see "Smaller choices"); in the review it is read beside the
  vignette, so diagnosis, disposition, dont miss, notes, warning reads worse than the data's own order.
- **A view of a long list** is shown under the whole list: the notes' views come after every note, far from the
  comment they read once the notes are long.
- **The record and the marks are the server's**, drawn as the page loads: a save reloads the page, so the views'
  values in the record follow only once the runs are scored again (step 3).
- **Answers only from the person's own runs**, as decided (L3): running the case from the page is step 3.

### Step 3: running the case, and scoring it again
- **Run this case**, folded at the top of the record (open when there is nothing to read): a configuration of purpose
  generation the person sees, their own first; an endpoint, or the one serving its model; replicates; and whether to
  score it once it has finished. `POST /review/{family}/runs` starts the case picked, held to be a current case of the
  family, as `POST /api/runs` starts one (`Bench.variation`, `Bench.start`, `Bench.queue` under `refused`), a run per
  language its translations carry it into, and leads back to the review with the record open (`#record`).
- **Runs under way**: a run of the case with a job queued or under way is listed at the top of the record, and the
  island follows its events (`frontend/src/lib/review/Pending.svelte`, `review.ts:doing`): queued, how many items have
  ended and what the one being sent is doing, then its scoring and the judges' calls. Once every run listed is done,
  the page reloads into what they came to. The rail says how many are under way.
- **Left to score**: a finished run the scorer picked hasn't scored against the expectations as they are now
  (`Bench.unscored`), after an expectation's edit or because it never did. Its values are shown in italics, as what
  it scored before, the rail says how many, and **Score again** queues each of them (`POST /review/{family}/scores`,
  `Bench.queue_scoring` by the scorers it is left to), and leads back to the record, which follows the scorings as it
  follows runs.
- **The record's rows** say when each run started, since runs of one configuration read alike.
- **An endpoint serving another model** runs the configuration with that model in its place, as the variation's page
  does (`diagnoses+model=gpt-oss-20b@malborg`), rather than being refused for serving another model.
- **No jump**: the record is opened by `#record` without an element of that id, so the page doesn't scroll to it, and
  the island drops the hash, so the reload after a run doesn't either.
- **Tests**: `test_running.py`, the case run from its review and followed there, refused from another site and for a
  case of another family, and scored again once its expectation is edited; `test_browser.py`, the case run from the
  record, followed and its answer read once the page reloads; vitest for `doing`. By hand on the sample World with
  its fake engines and a worker (`chatddx fake-engines`, `chatddx run`): Dutchfall11w run on free-text, its diagnosis
  target changed to sepsis, and the two runs scored again, the judged answer rising from 0.50 to 1.00.

#### What step 3 leaves
- **Several runs started together**: one configuration a start; comparing configurations on the case is the portal's
  phase 6 (`agents/wip-portal.md`, "Comparing variations").
- **A run refused** (several endpoints serve the model, a language the translations don't cover, over quota) is
  answered with the error page, not beside the form.
- **The cost of the record grows with the runs**: each run listed is read whole, and what is left to score is worked
  out for each (`Bench.unscored`, about 40 ms a run), 50 runs at most.
- **A scoring that fails** shows as the run no longer under way and still left to score; why is on the run's page.


### Step 4: composing a scorer without judges
- **The API**, suggested to `docs/api.md` and `docs/api-api.md` as `AGENT` blocks: `POST /api/scorers/try`
  (`src/chatddx/api/scores.py:tried`), a scorer as written and an expectation's data tried on a case's items in some of
  the person's runs: each item's answer as the scoring pass reads it, and each view's value and detail by
  `chatddx.scorers.scorer.score_view`, with nothing stored. A judged view isn't tried, since its judge would be sent
  the answer (L5 b): it says so. A scorer the running code can't score with is refused. Sensitive, `no-store`.
- **The composer** (`frontend/src/lib/scorer/Composer.svelte`), opened in the Expected column by **Compose …**: the
  scorer picked, edited when it is the person's own and forked as theirs when it isn't, or a new one from the shipped
  code and the schema shown (**Start a new one**). Each view is a row: its label; what it reads of what is expected
  and of the answer, each a picker (`frontend/src/lib/scorer/SelectorPicker.svelte`) with **typed…** for anything
  else; line by line; the metric, by what it measures; moved up or down with its label, or left out. A judged view
  keeps its metric and judge as they are (step 5). The views as composed are what the fields' annotations show, so
  a view's picks follow both the expectation and the view as each is typed.
- **Selectors picked** (L6 b, `frontend/src/lib/scorer/selectors.ts:choices`): from the expectation schema, the whole
  expectation, each field, what a target holds, each item of a list and its fields, and the items of a list whose
  required text field has a value written, as `notes where author is Olof › comment`
  (`$.notes[?@.author == 'Olof'].comment`); from the output schemas of the configurations the person sees, the
  whole answer and each field, by the schema's title. A dotted path and its JSON Pointer find the same choice
  (`chosen`).
- **Tried as typed** (L5 a): a moment after each change to the scorer or the expectation, every view's value on each
  of the case's answers in the person's runs, its detail on hover; the lints and refusals as a component check gives
  them.
- **Saving** says where the save goes, as every editor does, with the labels (`writing.ts:saved` takes them,
  `Saving` passes them), and comes back to the review with the scorer saved picked (`review.ts:withScorer`). An edit
  that changes only a label is a new edit, as the catalog keeps it (`docs/catalog.md`, "Scorer labels").
- **Tests**: `test_scores.py` (the API's), a scorer tried: the stored score's values, a missed target, judged views
  untried, nothing written, an unknown metric refused, bob not finding the run; `test_reviewing.py`, the composer's
  props; vitest for `choices`, `chosen` and `withScorer`; and `test_browser.py`, a run's answer tried as the
  expectation's pattern is typed, 1.00 then 0.00, and a new scorer composed, tried, saved with its label and picked.

#### What step 4 leaves
- **A metric's params** aren't drawn: the shipped unjudged metrics take none, and the judged ones' are step 5's.
- **A view of a list's fields that filters on anything but a required text field**, or reads deeper than two levels,
  is typed.
- **Resources and the scorer's own params** aren't offered (`docs/bench.md`, "Outstanding").
- **The composer is closed again by reloading**: closing it while keeping what was composed isn't offered.


### Step 5: with judges
- **The API**, suggested to `docs/api.md` and `docs/api-api.md` as `AGENT` blocks: `POST /api/judges/asked`
  (`src/chatddx/api/scores.py:judge_asked`), a stored judge's first request rendered as the scoring pass renders it,
  its `expectation` slot filled by what a view picks of the expectation as typed, the answer and the case's slots as
  placeholders (`chatddx.bench.model.PLACEHOLDERS`). Nothing is sent or stored, and nothing in it is sensitive.
- **A judged view** (`frontend/src/lib/scorer/Composer.svelte`): the metrics that read a judge's verdicts are offered
  beside the others, "by a judge". Picking one picks a judge, the person's own first, each said by its judge
  configuration, where it is asked and its seeds, and starts its params from the judge's output schema
  (`frontend/src/lib/scorer/judging.ts:startingParams`): its verdict at the first field that isn't text, and the
  most points at that field's maximum. The verdict's field is picked from the judge's output schema (`verdictAt`),
  other params are typed.
- **A new judge** (`frontend/src/lib/scorer/JudgeForm.svelte`), from **a new judge…** in a view's judge picker: a
  name, a judge configuration the person sees, the endpoint it is asked at (its engine is the judge's), and its
  seeds (`seedsOf`), checked as typed and saved as a judge of the person's own (`POST /api/threads`), then picked
  for the view. A judge's texts are step 6.
- **What its judge is asked** (`frontend/src/lib/scorer/JudgeAsked.svelte`), folded under a judged view: the judge's
  messages, the expectation filled as the view picks it and following what is typed, the answer as `‹completion›`.
- **Scored through the worker** (L5 b): a judged view isn't tried; saving the scorer leaves the case's runs to score
  by it, and **Score again** in the record queues them, the judges' calls recorded in the ledger as every scoring's
  are.
- **A finished run doesn't reload over work**: the record reloads into what its runs came to only while nothing has
  been typed or picked on the page since it loaded; else each run says **Show it**.
- **Judges and judge configurations are told apart by thread**, since a fork shares its origin's digest.
- **No page to scroll**: the panes and the drawers are each a containing block, so a hidden label of the list
  (`sr-only`) is placed within what scrolls rather than below the page, which it lengthened while a drawer was open.
- **A refusal's page leads back** to the page its request came from, when that is within the site
  (`src/chatddx/portal/pages.py:_back`, by `Referer`), and to nothing else: the link home is gone.
- **Tests**: `test_scores.py` (the API's), what a judge is asked, and what is refused; `test_reviewing.py`, the
  judges, judge configurations and endpoints the composer is given; vitest for `seedsOf` and `startingParams`; and
  `test_browser.py`, a judged view composed of carol's comment, a new judge written for it and picked, its verdict
  at `/meets`, what it is asked, the scorer saved and its runs scored again through the worker.

#### What step 5 leaves
- **A judge is written new**: changing or forking one is on its thread's page, which has no editor yet.
- **The endpoint a new judge is asked at** is the first listed, not one serving its configuration's model; a judge
  whose engine no endpoint serves bars its scorer (`docs/runner.md`, "Judges").
- **A judged view's values come only from scoring**: one judge call per seed per answer, recorded, through the worker.

### Step 6: the judge's texts
- **What a judge comes with** (`src/chatddx/portal/review.py:_texts`): each judge the composer is given carries its
  head, its body and its texts: the judge configuration whose head is its skeleton (the person's own first), the
  recipe that configuration reads, and the recipe's instructions, prompt and output, each with the thread whose head
  it is, whether that thread is the person's, and its language. A judge whose skeleton no configuration in sight
  heads, as a World's judge compiled for its engine, reads the recipe its compilation recorded; it has no
  configuration then, and saving makes one.
- **The text editor** (`frontend/src/lib/scorer/TextSegments.svelte`, `texts.ts`), a start on 5c's: a text and its
  slots and inserts, each slot or insert a chip between text boxes, left out by its ×, and one the part allows and
  doesn't hold put back by its + at the end. What is stored is the canonical form: neighbouring texts merged, empty
  ones dropped, and a plain string where an instruction or guidance holds no insert (`textOf`).
- **Change what it is asked**, under a judged view (`frontend/src/lib/scorer/JudgeTexts.svelte`): its instructions,
  what it is told to answer (the output's guidance) and its prompt, side by side with the messages they would make,
  the guidance placed as `src/chatddx/factors/request.py:compile_request` places it (`texts.ts:asked`), the
  expectation as the view picks it of what is typed and the answer as `‹completion›`. Each changed part is checked
  as typed (`POST /api/components/check`), and a refused one bars saving.
- **Saving** (`frontend/src/lib/scorer/rewriting.ts:rewritten`) writes, in order: each changed text, as a version
  where its thread is the person's, else as a fork of their own (a new thread where none holds it), in its language;
  the judge configuration of those texts, as a version of the person's own, a fork, or, for a judge without one, a
  new configuration from the recipe, named "‹judge›'s request"; and the judge asked through it, a version or a fork
  under its name. The new judge is picked in each of the scorer's views that asked the old one, and the scorer is
  saved as before.
- **Tests**: `test_reviewing.py`, a judge's texts as the composer is given them; vitest for the segments, their
  canonical form, `text@1`, and where guidance lands (`texts.test.ts`); and `test_browser.py`, verdict's guidance
  rewritten under `judged`, the messages following it, saved, what it is asked, and the scorer saved with both its
  verdict views asking alice's own judge through her own judge configuration.

#### What step 6 leaves
- **Saving is several writes, not one**: if one is refused partway, the versions written before it stay, the
  person's own and unused.
- **A version of the person's own text or configuration moves that thread's head**: what holds the earlier version
  keeps it, by digest, and a configuration of theirs holding it is left behind its parts, as the catalog proposes.
- **Only the texts**: the recipe's other parts (sampling, reasoning, few-shot messages, a toolset) and the judge's
  endpoint and seeds aren't changed here, and the messages shown leave out few-shot messages and tool guidance.
- **The text kinds of 5c** stop at a judge's: an appendix's or a generation's instructions and prompts are still
  written on their threads' pages.

## Open
- **Grading answers by hand.** Olof's judge is to be measured against his own grades of real answers, "with a line on
  why" (`docs/curation.md`, "Outstanding"). Nothing stores a person's grade of an item. Such a grade is sensitive,
  since the line can quote the answer, so it belongs with the ledger rather than the catalog, and the ledger records
  what the rig did, not what a person said. This needs a design of its own. Until then the grades live outside the
  rig.
- **Several clinicians' notes in one expectation.** The targets schema holds notes from several authors, while an
  expectation is one person's. A scorer picks a note by its `author`, as the sample's `notes` does. Whether a
  clinician's notes stay in their own expectation, with the author as data, or the selector follows the expectation's
  owner, is open.
- **Small screens.** The two columns and their rails need about 1280 px; below that the panes stack, the drawers as
  bars (see "Built"). A tablet beside a patient isn't planned for.

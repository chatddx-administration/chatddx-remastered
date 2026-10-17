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
4. **Step 1 is built** (see "Built"); step 2 is next (see "Steps").

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
A sketch, at a wide screen. Each pane scrolls on its own, and the page fills the window rather than the 5xl column the
other pages keep.

```
┌ cases ────┬ the case ──────────────────┬ expected ─────────────────┬ scored ───────────────────────┐
│ tag ▾     │ Dutchfall11w · sv · tags   │ under Targets ▾  v2 of 3 ◀▶│ notes (yours) ▾               │
│ ▸ Dutch11 │ [vignette alone][+ ultras.]│ diagnosis  text / pattern │ comment · verdict · judge …   │
│   Dutch1  │                            │ warning    …              │   picks: "Chock, trolig …"    │
│   edn1    │ the vignette …             │ dont miss  …              │ answer  · verdict · …         │
│   …       │                            │ notes                     │ graded  · points / 2 · …      │
│           │ ── appendices, in order ── │   Olof · sv · comment …   │ ── answers to this case ──    │
│ ● expected│ ultrasound: …       [edit] │ [Save] a new version      │ plan × qwen3 · 0.5 · 1 · 2/2  │
│ ○ none    │ + write one                │                           │ ▸ the answer, folded          │
└───────────┴────────────────────────────┴───────────────────────────┴───────────────────────────────┘
```

- **Cases**: the families the person sees, filtered by tag, each marked by what the person holds for it under the
  schema shown: an expectation of their own or none, notes, answers, scored. Keys step through it.
- **The case**: the vignette, then the case's appendices in order, shown as additions to it; a switch between the
  family's cases; writing an appendix, a new version of one, and building a case.
- **Expected**: the expectation for the case picked under the schema picked, in the 5b editor; its versions with what
  each changed; those shared to take; moving the person's own onto a replacing case.
- **Scored**: the scorers reading that schema, the person's own first. Each view is shown with what it picks from the
  expectation as typed, so a note or a target shows what each view will read from it. Below, the answers to the case:
  each run's answer folded, with each view's value, its detail, and the judges' verdicts.

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
1. **The page, read only**, built (see "Built"): the list of cases, the case (vignette fetched, appendices, cases), the expectation, the
   scorers that read its schema with what each view picks from it, and the person's answers to the case with each
   view's value and detail. Needs the route that gives picks (L6).
2. **Writing in place**: appendices, cases and expectations, with 5b's editors moved into the panes; the picks follow
   the form as it is typed.
3. **Running the case** from the page (L3 a), and **Score again** on its runs.
4. **Composing a scorer without judges**: the views' form, selectors picked (L6), values tried as typed (L5 a),
   saving with labels.
5. **With judges**: picking one, writing one (L4 a, b), what it is asked, and judged views scored through the worker
   (L5 b).
6. **The judge's texts** (L4 c), with 5c's text editor.

Tests, as the portal's: the pages by `TestClient` on `ran`; the new routes in the API's tests, with `no-store` pinned
where they are sensitive; vitest for the panes' logic; and a browser test of a clinician's flow on the test World:
the case `noted` that `judged` ran, its note edited, a view's picks following it, a pattern view's value changing as
the pattern is typed, a scorer saved, and its score.

## Built
Step 1, the page read only:
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
  px, with the list of cases above and capped; one column below that.
- **The island**: `frontend/src/islands/review.ts`, with `frontend/src/lib/review/`: `Vignette.svelte`,
  `Answer.svelte`, and `review.ts`, the keys and each view's value and detail.
- **Tests**: `src/chatddx/portal/test/test_reviewing.py` on `ran`; the API's `test_world.py` (picks) and
  `test_runs.py` (one case's items); `frontend/src/lib/review/review.test.ts`; and by hand on the sample World in
  Chromium, as a person given the archive's expectations (`chatddx init-data LOGIN --giftbag`) with its scripted runs,
  in light, dark and narrow.

### What step 1 leaves
- **Its cost**: about 0.75 s a page on the sample World's 99 families, against 0.6 s for a family's page. The marks
  ask `Bench.expectation` once per family, and each answer's run is read whole (`GET /api/runs/{id}`, its check
  included) for its items and scores.
- **A run scored by an earlier version** of the scorer shows "not scored by it": values are matched by the head's
  digest.
- **What a view reads of the answer**, and its reach, aren't shown: step 4.
- **The expectation's versions** and what each changed are on its thread's page: step 2 brings them into the pane.
- **The browser test** of the plan's "Tests" waits for step 2, which gives it something to type.

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
- **Small screens.** The four panes need about 1280 px; below that they stack (see "Built"). A tablet beside a
  patient isn't planned for.

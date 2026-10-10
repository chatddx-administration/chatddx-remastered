# The portal: work in progress

The portal is the web interface "used to configure factors, watch runs and export results" (`docs/chatddx.md`,
glossary). It is the bench's third edge, after the repl and the API (`agents/wip-bench.md`; `agents/wip-api.md`). This
file plans its port from the old project.

"The old portal" is chatddx-administration/chatddx at 504792c: `src/chatddx/django/portal/`, its manual
`docs/portal.md`, and the layers it stood on (`bench/plan.py`, `bench/held.py`, `worker/`). Old permalink base:
https://github.com/chatddx-administration/chatddx/blob/504792cbeb09508f2c52912be29a3d8809d2fa1d/

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **How it is built** (see "Options"): P1, keep the old Django portal; P2, a PWA; P3, HTML with focused islands of
   TS. Take: P3 as P3b, pages rendered on the server from the bench, islands on the API. Not decided.
2. **Most of the work is below the UI**, whichever option is chosen (see "Below the UI"): runs that outlive a request,
   the bench's writes for authoring, the batch planner, the worker, and Z1.
3. **The batch planner and the worker** are planned apart, around one contract settled first (see "The batch planner
   and the worker"). Take, not decided.
4. **Sample runs**, genuine runs answered by a script, are test data for every edge, the portal's among them. They
   are planned with the sample data (`agents/wip-sample-data.md`, "Sample runs").

## The old portal
### What it is
- Django's admin, themed by Unfold (Tailwind), with htmx and a little Alpine for what changes on a page, and three
  small scripts (`static/portal/js/`). Its settings add `unfold` and `corsheaders` to the old project's Django apps
  (`src/chatddx/django/settings/portal.py`).
- About 7,100 lines of Python without tests and migrations, 2,700 of tests, 1,800 of templates and 840 of CSS and
  JS.
- 20 of its 23 modules import the old models from `repo` and `history` or query them (`.objects.`). Its pages are
  `ModelAdmin`s over proxy models (`models.py`: `Case(CaseBranchModel)` and the like), most of them overridden at
  length: `case_admin.py` is 726 lines, `variation_admin.py` 429, `checking.py` 823.
- It had a model of its own, `BatchModel`: a batch's configuration, stack, tags, variations and seed, and its cells,
  held-back cells and cases as JSON. The worker's `JobModel` pointed at it.

### What it offered
From its manual (`docs/portal.md`), which reads as a functional spec:
- **Cases**: a list filtered by tag, language and what targets still want; a case's page steps through its versions
  (◀ and ▶, "version i of n") and shows what each changed, word by word; the latest is a form. A line under the name
  says, as you type, where a save will go: a new version, a new case, or another case of yours. The same vignette
  under another case is pointed out. Under the case, its runs and their scores, with **Score again** for outstanding
  ones.
- **Batches**: planning (a configuration, a stack, case tags, a seed, and the variations of each slice ticked, crossed
  into cells); confirming (the trials, each cell and what it sets, the cells held back and why, the cases, and each
  scorer's reach); keeping it for later or running it now; a batch's page that never changes and follows its state.
- **Status**: the worker at the person's jobs, every second, with pause, resume, stop and stop now.
- **Runs**: a list, and a run's page: the trial, how it came out, why it went wrong, the case at the version run, the
  stack and the LLM as read, tools, tokens, the configuration as it ran, the answer by view, scores, messages part by
  part (folded, linkable as `#message-N`, loaded when opened), and the requests and responses as sent and streamed.
- **Configurations**: a version, with variations set in it, each component by the name of its variation.
- **Stacks**: a version and its parts, and **Test**: a live check of the server and the LLM, written down nowhere.

### What maps onto remastered
| Old portal (504792c) | Remastered | Notes |
|---|---|---|
| a case: a vignette and targets, saved by name, with versions | a family, its case and appendices, and an expectation per schema (`Bench.family_by_id`, `Bench.expectation`); the vignette is a source's, fetched and never stored | the bench writes none of these yet (see "Below the UI") |
| a configuration with slices set | a configuration thread's head and recipe; a variation being tried (`src/chatddx/bench/variation.py:TriedVariation`); `GET /api/threads/{id}/variation` (API phase 3) | "cell" stays the repl's word (`agents/wip-bench.md`, K2) |
| a variation as a stored object (`variation_admin.py`) | a chunk on a thread of its part's kind; a saved variation is a fork (`Bench.fork`) | variations are "a supported portal workflow, not an object in the code" (`docs/chatddx.md`) |
| a stack and its parts | an endpoint and the engine it serves (`Inventory`, `Bench.endpoint`), and the facts (`GET /api/models`) | ops-authored files, read only |
| a stack's **Test** | nothing yet: `confirm` checks an endpoint's binding (`src/chatddx/runner/gate.py:check`), and the `vllm.*` lints check a skeleton | open |
| batches: planning, confirming, kept for later | the batch planner, to plan (see "The batch planner and the worker") | |
| **Status**, the queue, `BatchModel`, `JobModel` | the worker, to plan | |
| a run's page | `Bench.run_by_id`, `Store.run`, `Bench.described`, `Bench.scores_of`, `Bench.rendered_again`, `src/chatddx/bench/outcome.py`; `GET /api/runs/{id}` and `/items` (API phase 4) | requests are kept as fingerprints, and rendered again |
| Django's view, change, add and delete permissions | Z1, roles to kinds, and owners and collaborators (`src/chatddx/identity/identity.py:sees`) | a convenience, not a protection (`agents/wip-identity.md`, "Authorization") |
| Django's users and sessions | `People`, by the API's session (`src/chatddx/api/people.py`) | |

## What the docs already ask of it
- Interfaces for instructions, few-shots, prompts, output, sampling, reasoning, passthrough, recipes, appendices,
  expectations, trials, judges, scorings, and starting and monitoring runs (`docs/chatddx.md`, "Requirements").
- The variation workflow: try, save the successful as configurations, delete the rest, branch (`docs/chatddx.md`,
  "Intended evolution of configurations").
- Appendices written in the portal, with CRLF normalized before they are digested (`docs/factors.md`, "Appendix").
- Copying a scorer's labels to its next edit, "since it knows how the positions moved" (`docs/catalog.md`, "Scorer
  labels" and "Smaller issues").
- Offering a new version the previous version's language (`docs/catalog.md`, "Languages").
- Building a stored replacement for a late case (`docs/catalog.md`, "Smaller issues").
- What deleting hides: everywhere, or only in pickers (`docs/catalog.md`, "Deleting" and "Smaller issues").
- Pickers of the right kind for each reference, if components' JSON Schemas say it (`docs/factors.md`, "Reference
  kinds in components' JSON Schemas"), and execution settings to pick, if they become a component ("Execution
  settings as a component").
- A change made in the portal kept in git through an export (`docs/curation.md`, "Import, export and verification").
- Clearance granted in the database, through the portal and logged, as a long-term option
  (`agents/wip-clearance.md`, "Open", 2).

## Options
### P1. Keep the old portal, Django and all
What would carry over is little:
- Its data layer is the old models. Remastered has none: its store is psycopg, append-only and guarded by the
  database's grants, with its own people, sessions and migrations (`docs/store.md`, `docs/migrations.md`). Django
  would bring a second user table, session table and migration history beside them.
- Its pages are `ModelAdmin`s, which query the models themselves. That is how the old project copied its rules into
  every edge (`agents/wip-bench.md`, "The old bench"). Calling the bench instead leaves the admin little to give.
- Its words are gone: cell, stack, slice, `BatchModel`, variations as objects, the worker's jobs.
- The admin was being worked against already: CRUD over tables, where the data model is append-only threads of
  digests.

What is worth keeping is not the code: the manual, as a spec, and its ways of showing things (the version timeline,
the line that says where a save goes, live checks, the confirmation before a batch, the run's page).

### P2. A PWA
- **Offline buys nothing.** Every action needs the store or an endpoint.
- **What is kept offline is a destination.** A service worker's cache or IndexedDB holding vignettes or completions
  stores sensitive data on an unvetted machine (`docs/chatddx.md`, glossary, "Sensitive"; `agents/wip-clearance.md`,
  "Open", 6; `agents/wip-api.md`, A9).
- **Without the offline part it is a single-page app**, and the API becomes its backend (`agents/wip-api.md`, A1,
  C3). Each page wants an endpoint shaped like it, and the API drifts towards the portal's shape, as the old API
  followed the repl's (`agents/wip-api.md`, "Where it follows the repl").

### P3. HTML, with focused islands of TS where interactive feedback pays
"Static" can be read two ways:
- **P3a. Static pages, built once**, whose content is fetched from the API. What a page shows depends on who is
  asking (B3), so every page needs script and an endpoint: P2 without the service worker.
- **P3b. Pages rendered on the server**, per request, from the bench, with islands that call the API where a page
  needs feedback without a reload.

Take: **P3b.** The portal consumes the bench, as planned (`agents/wip-bench.md`, "Forces"), and is built on the API
where it is interactive (`agents/wip-api.md`, A1, "kept open"). Both, not either.

## The take, concretely
### One app
- `src/chatddx/portal/`, a package beside `src/chatddx/api/`, mounted at `/` in the same FastAPI app as the API at
  `/api/` (`src/chatddx/api/app.py:app`). Its routes return HTML rendered with Jinja2 (Starlette's
  `Jinja2Templates`).
- Its pages build a bench per request, as the API's routes do (`src/chatddx/api/people.py:bench`).
- One session: the API's cookie, `__Host-chatddx-session`, `Path=/`. This answers "whether the portal shares the API's
  cookie" (`agents/wip-identity.md`, "Open"). A sign-in page posts a form to the portal, which calls `People` as
  `POST /api/session` does.
- Forms are plain POSTs, checked by the API's same-origin check (`src/chatddx/api/people.py:same_origin`), so there is
  no CSRF token, as there is none for the API.
- New dependencies: `jinja2`, and `python-multipart` for FastAPI's form fields. Neither is locked today.

### Islands
Only where a page needs feedback that takes a round trip or live state:
- **The variation being tried**: pick a chunk per part and see the skeleton's digest, the findings at an endpoint,
  each scorer view's reach and the request rendered, as you pick. It calls `GET /api/threads/{id}/variation` (API
  phase 3). The old portal did this with htmx, `input changed delay:400ms`.
- **A run as it runs**: its items as they start and end, and the deltas while you watch (API phase 4).
- **A batch's progress** and the worker's state, once they exist.
- Perhaps editors for structured chunks and expectations, checked against their JSON Schema as you type.

Take:
- **Svelte with TypeScript**, built by Vite into static files the app serves. Svelte compiles to small bundles, one
  per island, and the old "swift" client was Svelte (`agents/wip-api.md`, "Where it came from"). React's runtime and
  ecosystem buy nothing for a handful of islands.
- **Types from `/api/openapi.json`** (openapi-typescript), so an island's types follow the API's pydantic schemas. A
  test can check that what is generated is current.
- **Not htmx.** It wants an HTML fragment per interaction: a third surface beside the pages and the API, which
  already answers what the islands ask.
- **The toolchain comes with the first island.** Node and Vite join the flake's dev shell, and the build joins the
  package's. The pages before it need no script.

### Tests
- Pages: `TestClient` on the HTML, in `src/chatddx/portal/test/`, on the seeded sample, as the API's are, and as the
  old portal's were.
- Islands: through the API's tests for what they call. A browser test (Playwright, with the container's Chromium)
  once an island holds logic worth testing on its own.
- Sample runs give the pages genuine runs to show: typical, broken and rich (`agents/wip-sample-data.md`, "Sample
  runs").

## Below the UI
What the portal needs whichever option is chosen:
1. **Runs that outlive the request.** The API runs a trial in the request and halts it when the client goes away
   (`agents/wip-api.md`, A6, W1). For a browser, closing a tab or leaving the page would stop a batch. The portal
   needs W2 at least: `POST /api/runs` answers 202, `GET /api/runs/{id}/events` streams, and a stop calls
   `Running.halt` (`src/chatddx/runner/run.py`).
   - Progress by item can be read from the store, since a run's rows land as they are written. That works from any
     process, and after a reconnect.
   - Deltas aren't stored, so watching a completion as it is written needs the process that runs it.
   - W2's runs end with the process, and two replicas of the app don't see each other's. The worker is the way out
     (see "The batch planner and the worker").
2. **Writes for authoring.** The bench writes configurations (`save`, `fork`, `edit`), runs (`start`) and scores
   (`score`), and nothing else. Chunks of every part, appendices, expectations, cases and families, scorer labels and
   languages have nothing to build on yet. Curation writes them only as the archive, from a data set's files
   (`src/chatddx/curation/write.py`).
3. **The batch planner** and 4. **the worker**, see below.
5. **Z1**, the map from roles to kinds, waits for the portal's views (`agents/wip-bench.md`, "Phase 2", step 12;
   `agents/wip-identity.md`, "Open").
6. **The cookie's `SameSite`.** The session cookie is `SameSite=Strict` (`src/chatddx/api/people.py:sign_in`). A
   link to a run from chat or email is a cross-site navigation, which carries no cookie under `Strict`, so it opens
   signed out. `Lax` is the usual choice for pages; the same-origin check already guards every unsafe request.
7. **Case-derived content in the browser's cache.** A page that shows a vignette or a completion is kept in the
   browser's cache unless it says `Cache-Control: no-store`. The API's A9 (S3) keeps such content in its own places;
   the portal's pages that show it are those places, and want the header. Clearance's open question 6 covers it.

## The batch planner and the worker
### Together or apart
Take: **apart**, as two plans, in this order: the contract between them (below, settled in this file), then the
planner, then the worker.
- **They meet at one narrow seam**: a list of trials to run at an endpoint for an owner. The planner decides which
  trials; the worker decides when and where they run. Neither needs the other's insides.
- **Each is useful without the other.** The planner serves the repl's `batch`, the API and the portal's confirmation
  page, with runs in the request (W1) or beside it (W2). The worker serves single runs from the API and the portal,
  and sample runs.
- **They are different kinds of work.** The planner is pure over the bench and tested without a process; its
  questions are the catalog's: crossing, variants, mixed batches, what a kept plan is. The worker is processes,
  concurrency and failure; its questions are the store's and the deployment's: claims, heartbeats, resuming,
  `max_jobs` across runs, replicas in Kubernetes.
- **The old project fused them, and it cost.** `worker/queue.py:put(owner, batch, trials)` took a batch's id, each
  `JobModel` pointed at a `BatchModel`, and a batch's state ("queued", "running", "unfinished") was its jobs' state.
  In remastered that state can be read from the ledger by trial, so the batch needn't know the worker.

### The contract
Settled before either plan:
1. **The unit of work**: a trial at an endpoint, for an owner, scored afterwards or not. That is `Bench.start`
   followed by `Bench.score` (`src/chatddx/bench/view.py`).
2. **How runs are found from what asked for them**: by trial digest and owner (`Bench.runs`; `GET /api/runs?trial=`),
   or through a kept plan (see "The planner").
3. **The surface an edge calls**, the same whether runs go in the app's process (W2) or to the worker: start, which
   gives a run's id; stop; and the events, by item from the ledger, with deltas where the process has them.

### The planner
What the old `bench/plan.py` did (`crossed`, `Plan.of`) in remastered's terms:
- **In**: a configuration, for each part the chunks to try (its own among them), an endpoint, cases by tag or by id,
  and a seed.
- **Crossing**: the product of the parts' choices, each a `TriedVariation` (`Bench.variation`), with the same skeleton
  digest kept once, as the old `crossed` kept one cell per fingerprint.
- **For each variation at the endpoint**: the findings (`Bench.findings`), warnings and never refusals
  (`docs/chatddx.md`, "Compromises"); what the gate refuses, held back with why (`src/chatddx/runner/gate.py`); and
  each scorer view's reach (`Bench.reach`).
- **Out**: the trials, one per variation, each with the cases and one seed. A trial holds its cases, where the old one
  was a cell, a case and a seed.

Open, for the planner's plan:
- **Is a plan kept?** The old portal kept a batch to run later, and gave it a page that never changes.
  - L1. Not kept: a plan is shown, then its trials start. Nothing groups the runs but their trials.
  - L2. A component of a new kind, `plan`: its trials and endpoint, by digest.
  - L3. L2, kept on a catalog thread when kept for later: named, owned, shared and deleted as configurations are.
  Leaning L3, since it reuses the catalog for what a person keeps. It touches `docs/factors.md` (a new kind) and is
  the user's call.
- **Mixed batches**: English and Swedish cases in one plan, one trial per language under its variant, or refused
  (`agents/wip-variants.md`, "Questions for the user").
- **Several endpoints in one plan**, which the old portal didn't offer.

### The worker
What it adds over W2:
- Runs that survive a closed tab and a restarted app, and are seen from every replica.
- `max_jobs` held across runs on one endpoint (`agents/wip-runner.md`, "Afterwards", "`max_jobs` across runs").
- Pause, resume and stop for an owner's work, as the old **Status** page had.
- Resuming an unfinished run (`agents/wip-runner.md`, "Afterwards", "Resuming").

Open, for the worker's plan: where it keeps what is asked of it. "The append-only store has no place for a queue"
(`agents/wip-api.md`, A6, W3).
- Q1. A table of jobs updated in place, as the old `JobModel`: against "nothing is updated" (`docs/chatddx.md`).
- Q2. An append-only log of what is asked (run this trial at this endpoint for this owner; pause; resume; stop),
  claimed by inserting a unique row, with the rest read from the ledger: asked and unclaimed is queued, claimed and
  unfinished is under way or lost, finished is done.
- Q3. A queue outside the store (Redis, a Kubernetes Job per run): another moving part, and state the store doesn't
  hold.

Leaning Q2, since it fits the store's rules.

## Phases
Assuming the takes.
0. **Before the first page.** `chatddx.portal` mounted beside the API; Jinja2 and python-multipart; the decision on
   `SameSite`; `Cache-Control: no-store` where case-derived content is shown.
1. **Signing in, and pages to read**: runs and a run's page, configurations with their versions and recipe, families
   with their expectations (the vignette in its own place, A9), endpoints and models. No script.
2. **The variation being tried**, and its island, on the API's phase 3.
3. **Starting and watching a run**: W2, and the run's island, on the API's phases 4 and 5.
4. **Authoring**: the bench's writes for chunks, appendices, expectations, labels and languages (see "Below the UI",
   2), and their pages.
5. **Batches**: the planner's plan and its pages; then the worker's plan, a batch's page and the status.
6. **Z1**, and what deleting hides.
7. **Docs**: material for a `docs/portal.md`, kept here as `agents/wip-bench.md` keeps the bench's.

## Open
- **One process or two.** `chatddx api` serving the portal too, or a `chatddx portal` of its own on the same app.
- **Where the islands' build lives**: built by Nix with the package, or committed.
- **A page to test an endpoint**, as the old stack's **Test** did. Canaries and `confirm` cover parts of it.
- **Export.** The portal is to export results (`docs/chatddx.md`, glossary), and the export isn't planned
  (`docs/chatddx.md`, "On the table").
- **Keycloak in front** skips the sign-in page (`agents/wip-identity.md`, "Take, for when Keycloak arrives").

## Surprises
- The session cookie is `SameSite=Strict`, so a link into the portal from another site opens signed out (see "Below
  the UI", 6).
- A run in a request halts when the client goes away (A6, W1): right for the repl and a program, wrong for a browser
  tab.
- The bench can't write a chunk, an appendix or an expectation, and the portal is where they are to be written.
- Neither `jinja2` nor `python-multipart` is a dependency; FastAPI's form fields need the second.

# The portal: work in progress

The portal is the web interface "used to configure factors, watch runs and export results" (`docs/chatddx.md`,
glossary). It is the bench's third edge, after the repl and the API (`agents/wip-bench.md`; `agents/wip-api.md`). This
file plans its port from the old project.

"The old portal" is chatddx-administration/chatddx at 504792c: `src/chatddx/django/portal/`, its manual
`docs/portal.md`, and the layers it stood on (`bench/plan.py`, `bench/held.py`, `worker/`). Old permalink base:
https://github.com/chatddx-administration/chatddx/blob/504792cbeb09508f2c52912be29a3d8809d2fa1d/

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **Decided: P3, HTML with focused Svelte islands** (see "Options"): pages rendered on the server from the bench,
   and islands, in Svelte with TypeScript, that call the API (P3b). How it is built otherwise is still a take (see
   "P3b, concretely").
2. **Decided: the portal integrates swift, and swift is ported to Svelte** (see "Swift"). Swift's free text is the
   open question that blocks it.
3. **Most of the work is below the UI** (see "Below the UI"): the bench's writes for authoring
   (`agents/wip-bench.md`, "Start with this", 6), the worker (`agents/wip-worker.md`), the batch planner
   (`agents/wip-batch.md`), and Z1.
4. **Decided: the batch planner and the worker are planned apart**, in `agents/wip-batch.md` and
   `agents/wip-worker.md`, around one contract (`agents/wip-worker.md`, "The contract").
5. **Sample runs**, genuine runs answered by a script, are test data for every edge, the portal's among them. They
   are planned with the sample data (`agents/wip-sample-data.md`, "Sample runs").
6. **Dependencies**: `jinja2` and `python-multipart` are in `pyproject.toml`.

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
  held-back cells and cases as JSON. The worker's `JobModel` pointed at it (`agents/wip-batch.md`,
  `agents/wip-worker.md`).

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
| batches: planning, confirming, kept for later, `BatchModel` | the batch planner (`agents/wip-batch.md`) | |
| **Status**, the queue, `JobModel` | the worker (`agents/wip-worker.md`) | |
| the old API's `/api/agents`, `/api/auth/` and `/api/diagnose`, for swift | the portal's swift page (see "Swift") | |
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

Decided: **P3**, with Svelte islands: P3b. The portal consumes the bench, as planned (`agents/wip-bench.md`,
"Forces"), and is built on the API where it is interactive (`agents/wip-api.md`, A1, "kept open"). Both, not either.

## P3b, concretely
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
- Dependencies: `jinja2`, and `python-multipart` for FastAPI's form fields, both in `pyproject.toml`, imported only
  under `chatddx.portal` as `rich` is only under `chatddx.repl`.

### Islands
Only where a page needs feedback that takes a round trip or live state:
- **The variation being tried**: pick a chunk per part and see the skeleton's digest, the findings at an endpoint,
  each scorer view's reach and the request rendered, as you pick. It calls `GET /api/threads/{id}/variation` (API
  phase 3). The old portal did this with htmx, `input changed delay:400ms`.
- **A run as it runs**: its items as they start and end, and the deltas while you watch (API phase 4).
- **The batch form**: ticking chunks per part, with the number of trials, what is held back and each scorer's reach
  as you tick (`agents/wip-batch.md`, "Callers").
- **A batch's progress** and the worker's state (`agents/wip-worker.md`).
- **Swift**: its form and its answer (see "Swift").
- Perhaps editors for structured chunks and expectations, checked against their JSON Schema as you type.

Decided: **Svelte with TypeScript**. That settles htmx too, which would have wanted an HTML fragment per interaction:
a third surface beside the pages and the API.

Take:
- **Built by Vite** into static files the app serves, a bundle per island.
- **Types from `/api/openapi.json`** (openapi-typescript), so an island's types follow the API's pydantic schemas. A
  test can check that what is generated is current.
- **Tailwind** for the portal's styling, as swift's and the old portal's Unfold were, and shadcn-svelte where swift's
  components are ported (see "Swift").
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
What the portal needs below its pages:
1. **Runs that outlive the request**: the worker (`agents/wip-worker.md`). A run started over HTTP runs in the
   request and halts when the client goes away (`agents/wip-api.md`, A6, W1); for a browser that is a closed tab.
2. **Writes for authoring**: chunks, appendices and expectations through the bench (`agents/wip-bench.md`, "Start
   with this", 6).
3. **The batch planner** (`agents/wip-batch.md`).
4. **The worker's controls and status** (`agents/wip-worker.md`, "The plan", 4).
5. **Z1**, the map from roles to kinds, waits for the portal's views (`agents/wip-bench.md`, "Phase 2", step 12;
   `agents/wip-identity.md`, "Open").
6. **The cookie's `SameSite`.** The session cookie is `SameSite=Strict` (`src/chatddx/api/people.py:sign_in`). A
   link to a run from chat or email is a cross-site navigation, which carries no cookie under `Strict`, so it opens
   signed out. `Lax` is the usual choice for pages; the same-origin check already guards every unsafe request.
7. **Case-derived content in the browser's cache.** A page that shows a vignette or a completion is kept in the
   browser's cache unless it says `Cache-Control: no-store`. The API's A9 (S3) keeps such content in its own places;
   the portal's pages that show it are those places, and want the header. Clearance's open question 6 covers it.

## The batch planner and the worker
Moved to `agents/wip-batch.md` and `agents/wip-worker.md`, with the contract between them in
`agents/wip-worker.md` ("The contract").

## Swift
Decided: the portal integrates swift, and swift is ported to Svelte.

### What it is
- **LigninDDX/swift-dx-guide** (public): a Lovable project, edited in Lovable and by hand (the latest commit
  2026-09-19), in React 18 with TypeScript, Vite, Tailwind and shadcn/ui (49 components in `src/components/ui/`),
  react-query and sonner, with a flake of its own. Beside the UI components it is about 1,450 lines, most of them in
  `src/pages/Index.tsx` (285), `src/components/DiagnosisResults.tsx` (293), `ManagementSection.tsx` (170) and
  `DiagnosisCard.tsx` (138).
- **One page**, "Emergency Differential Diagnostics": a clinician describes the patient's symptoms and history in free
  text, picks an agent, and gets a differential (each diagnosis with its probability, whether it is critical, a short
  rationale, and optionally red flags and a workup) and a management plan (workups by type and priority, empirical
  treatment, the disposition), with its sources linked and a disclaimer.
- **What it calls**, at `VITE_API_URL`, with the session's cookie: `GET /api/agents?output_type=DDXManagement`, the
  person's agents whose output is the management plan; `GET /api/auth/`, 200 or 401, read as whether one is signed in;
  and `POST /api/diagnose {symptoms, model}`, which answered with the plan as JSON. Signing in, and its "Admin" link,
  go to Django's admin.
- **Where its backend went**: the old project's "ChatDDX Swift API" (`src/chatddx/django/api.py` before 110f9a5) ran
  the agent on the text. It was a submodule of the old project for a day (9647f1d to ac8967e, 2026-06-03 to 06-04);
  the old project had a SvelteKit "swift mvp" client before that (7c7ac74, 8e89253). At 110f9a5 (2026-09-26) the API
  was remade and `/api/agents` and `/api/diagnose` went; at 504792c only `/api/auth/` is left
  (`src/chatddx/django/urls.py`). Swift's latest still calls the other two.

### What remastered has for it
- **The answer it renders** is the sample's management plan (`src/chatddx/data/sample/schemas/management_plan_v1.json`,
  the `plan` recipes): `acute_warning`, `diagnoses` (diagnosis, probability, critical, short rationale), `management`
  (workup, empirical treatment, disposition) and `sources`. Swift also reads a diagnosis's `description`,
  `red_flags` and `workup`, which the schema doesn't have.
- **Its agents** are configurations whose output is that schema: `GET /api/threads?kind=configuration`, filtered by
  their output's schema, which the API doesn't offer yet.
- **The answer** is read as the repl and the API read it (`chatddx.scorers.answer.read`;
  `src/chatddx/bench/outcome.py`), and served from a run's items (`agents/wip-api.md`, A9).
- **One case, one seed, waited for**: through the worker with item events (`agents/wip-worker.md`, K3, E2).
- **Signing in** is the portal's: on one origin the page is rendered signed in, and `/api/auth/` isn't needed.

### Free text
The question that blocks it. A case is a source's vignette, by id, fetched from the World and never stored
(`agents/wip-api.md`, "Left out"), and cases are to "enter the system de-identified from a predefined source"
(`docs/chatddx.md`, "Requirements"). Swift's text is typed by a clinician, may be about a real patient, and comes from
no source.
- **X1. A source that holds the text** for as long as its run, in memory, keyed by its fingerprint. The run is a run
  of a case like any other, recorded with the fingerprint only; its completion is case-derived and lands in the
  ledger. The endpoint must be cleared for that source.
- **X2. Not recorded**: swift's requests go to the endpoint outside the ledger. Against the rig's purpose, to record
  each exchange (`docs/chatddx.md`, "Purpose").
- **X3. No free text**: swift picks a case instead. Loses what swift is for.

Take: X1, with clearance deciding which endpoints a typed text may reach (`agents/wip-clearance.md`, "Open", 5 and
6). The user's call.

### Ported to Svelte
Take:
- **A page of the portal**, rendered on the server, with one island: the form (the text, and the configurations to
  pick from) and the answer (`DiagnosisResults`, `DiagnosisCard`, `ManagementSection`), about 900 lines of React.
- **shadcn-svelte** for the components swift uses (card, button, textarea, select, alert, label, and sonner's
  toasts), on the same Tailwind tokens, so its look carries over.
- **Its repository** stops being where swift is made, and its Lovable project with it. The user's call.

## Phases
Assuming the takes.
0. **Before the first page.** `chatddx.portal` mounted beside the API; the decision on `SameSite`;
   `Cache-Control: no-store` where case-derived content is shown. Jinja2 and python-multipart are in.
1. **Signing in, and pages to read**: runs and a run's page, configurations with their versions and recipe, families
   with their expectations (the vignette in its own place, A9), endpoints and models. No script.
2. **The variation being tried**, and its island, on the API's phase 3.
3. **Starting and watching a run**: the worker (`agents/wip-worker.md`), and the run's island, on the API's phases 4
   and 5.
4. **Swift**, once its free text is decided (see "Swift").
5. **Authoring**: the bench's writes for chunks, appendices, expectations, labels and languages
   (`agents/wip-bench.md`, "Start with this", 6), and their pages.
6. **Batches**: the planner's pages (`agents/wip-batch.md`), then a batch's page and the worker's status
   (`agents/wip-worker.md`).
7. **Z1**, and what deleting hides.
8. **Docs**: material for a `docs/portal.md`, kept here as `agents/wip-bench.md` keeps the bench's.

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
  tab (`agents/wip-worker.md`).
- The bench can't write a chunk, an appendix or an expectation, and the portal is where they are to be written
  (`agents/wip-bench.md`, "Start with this", 6).
- Neither `jinja2` nor `python-multipart` was a dependency; FastAPI's form fields need the second. Both are now.
- Swift is React, not Svelte: the Svelte client the old API served was replaced by swift-dx-guide, a Lovable project.
  Its latest still calls `/api/agents` and `/api/diagnose`, which the old API dropped at 110f9a5.

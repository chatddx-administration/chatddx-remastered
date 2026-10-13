# The portal: work in progress

The portal is the web interface "used to configure factors, watch runs and export results" (`docs/chatddx.md`,
glossary). It is the bench's third edge, after the repl and the API (`docs/bench.md`; `docs/api.md`). This
file plans its port from the old project.

"The old portal" is chatddx-administration/chatddx at 504792c: `src/chatddx/django/portal/`, its manual
`docs/portal.md`, and the layers it stood on (`bench/plan.py`, `bench/held.py`, `worker/`). Old permalink base:
https://github.com/chatddx-administration/chatddx/blob/504792cbeb09508f2c52912be29a3d8809d2fa1d/

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **Decided: HTML with focused Svelte islands** (P3b, see "How it is built"): pages rendered on the server from the
   bench, and islands in Svelte with TypeScript that call the API. How it is built otherwise is a take (see "P3b,
   concretely").
2. **Decided: swift is realized in the portal**, as a page of its own, not ported: swift-dx-guide retires, its look
   isn't kept, and much of what it does will change. The cases typed in it are kept in the database, as a source of
   their own (see "Swift", "Typed cases").
3. **Decided: the session cookie is `SameSite=Lax`**, so a link into the portal from another site opens signed in.
   Built (`src/chatddx/api/people.py:sign_in`).
4. **Most of the work is below the UI** (see "Below the UI"): the bench's writes for authoring
   (`agents/wip-authoring.md`), the worker (`agents/wip-worker.md`), the batch planner (`agents/wip-batch.md`), and Z1.
5. **Decided: the batch planner and the worker are planned apart**, in `agents/wip-batch.md` and
   `agents/wip-worker.md`, around one contract (`agents/wip-worker.md`, "The contract").
6. **Scripted runs**, genuine runs answered by a script, are test data for every edge, the portal's among them
   (`agents/wip-scripted.md`).
7. **Dependencies**: `jinja2` and `python-multipart` are in `pyproject.toml`.

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
| a configuration with slices set | a configuration thread's head and recipe; a variation being tried (`src/chatddx/bench/variation.py:TriedVariation`); `GET /api/threads/{id}/variation` (API phase 3) | "cell" stays the repl's word (`docs/bench.md`, "Cell") |
| a variation as a stored object (`variation_admin.py`) | a chunk on a thread of its part's kind; a saved variation is a fork (`Bench.fork`) | variations are "a supported portal workflow, not an object in the code" (`docs/chatddx.md`) |
| a stack and its parts | an endpoint and the engine it serves (`Inventory`, `Bench.endpoint`), and the facts (`GET /api/models`) | ops-authored files, read only |
| a stack's **Test** | nothing yet: `confirm` checks an endpoint's binding (`src/chatddx/runner/gate.py:check`), and the `vllm.*` lints check a skeleton | open |
| batches: planning, confirming, kept for later, `BatchModel` | the batch planner (`agents/wip-batch.md`) | |
| **Status**, the queue, `JobModel` | the worker (`agents/wip-worker.md`) | |
| the old API's `/api/agents`, `/api/auth/` and `/api/diagnose`, for swift | the portal's swift page, and a source for its typed cases (see "Swift") | |
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
  labels" and "Smaller issues"). Labels now belong to the edit they are written with, so the scorer's editor sends
  each view's label with the views, and moves them with the views it moves (agents/wip-authoring.md, S4).
- Offering a new version the previous version's language (`docs/catalog.md`, "Languages").
- Building a stored replacement for a late case (`docs/catalog.md`, "Smaller issues").
- What deleting hides: everywhere, or only in pickers (`docs/catalog.md`, "Deleting" and "Smaller issues").
- Pickers of the right kind for each reference, if components' JSON Schemas say it (`docs/factors.md`, "Reference
  kinds in components' JSON Schemas"), and execution settings to pick, if they become a component ("Execution
  settings as a component").
- A change made in the portal kept in git through an export (`docs/curation.md`, "Import, export and verification").
- Clearance granted in the database, through the portal and logged, as a long-term option
  (`agents/wip-clearance.md`, "Open", 2).

## How it is built
Decided: **P3b**, HTML pages rendered on the server, per request, from the bench, with Svelte islands that call the
API where a page needs feedback without a reload. The portal consumes the bench, as planned (`docs/bench.md`),
and is built on the API where it is interactive (`agents/wip-api.md` at 100a078, "A1. Who it is for").

Set aside:
- **Keeping the old portal, Django and all.** Its pages are `ModelAdmin`s over the old models, which remastered doesn't
  have; Django would bring a second user table, session table and migration history; and querying models from the pages
  is how the old project copied its rules into every edge (`docs/bench.md` at d5ebf52, "The old bench"). What
  carries over is its manual, as a spec, and its ways of showing things: the version timeline, the line that says where
  a save goes, live checks, the confirmation before a batch, the run's page.
- **A PWA.** Offline buys nothing, and what is kept offline is a destination for sensitive data
  (`agents/wip-clearance.md`, "Open", 6). Without the offline part it is a single-page app, whose pages each want an
  endpoint shaped like them.
- **Static pages, built once (P3a)**: what a page shows depends on who is asking (B3), so every page would need
  script and an endpoint.

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
- **Swift**: the text, and the answer as it comes (see "Swift").
- Perhaps editors for structured chunks and expectations, checked against their JSON Schema as you type.

Decided: **Svelte with TypeScript**. That settles htmx too, which would have wanted an HTML fragment per interaction:
a third surface beside the pages and the API.

Take:
- **Built by Vite** into static files the app serves, a bundle per island.
- **Types from `/api/openapi.json`** (openapi-typescript), so an island's types follow the API's pydantic schemas. A
  test can check that what is generated is current.
- **Tailwind** for the portal's styling, as the old portal's Unfold was.
- **The toolchain comes with the first island.** Node and Vite join the flake's dev shell, and the build joins the
  package's. The pages before it need no script.

### Tests
- Pages: `TestClient` on the HTML, in `src/chatddx/portal/test/`, on the seeded sample, as the API's are, and as the
  old portal's were.
- Islands: through the API's tests for what they call. A browser test (Playwright, with the container's Chromium)
  once an island holds logic worth testing on its own.
- Scripted runs give the pages genuine runs to show: the sample World's ten (`agents/wip-scripted.md`, "The runs").

## Below the UI
What the portal needs below its pages:
1. **Runs that outlive the process**: the worker (`agents/wip-worker.md`). A run started over HTTP is under way in
   the app's process, beside the request, and ends with it (`docs/api.md`, "Where it runs").
2. **Writes for authoring**: chunks, appendices and expectations, and cases and families for swift, through the bench
   (`agents/wip-authoring.md`). Taking an expectation shared with the person is one of them: a person is scored against
   their own only (`docs/bench.md`, "What a person is scored against").
3. **The batch planner** (`agents/wip-batch.md`).
4. **The worker's controls and status** (`agents/wip-worker.md`, "The plan", 4).
5. **Z1**, the map from roles to kinds, waits for the portal's views (`docs/bench.md`, "Outstanding";
   `agents/wip-identity.md`, "Open").
6. **Case-derived content in the browser's cache.** A page that shows a vignette or a completion is kept in the
   browser's cache unless it says `Cache-Control: no-store`. The API's A9 (S3) keeps such content in its own places;
   the portal's pages that show it are those places, and want the header. Clearance's open question 6 covers it.

## The batch planner and the worker
Moved to `agents/wip-batch.md` and `agents/wip-worker.md`, with the contract between them in
`agents/wip-worker.md` ("The contract").

## Swift
Decided:
- **A page of the portal realizes what swift showed**, rather than porting it: a clinician types a case, picks a
  configuration, and reads the answer. Its look isn't kept, and much of what it does will change. It is mainly for
  testing.
- **swift-dx-guide retires** (LigninDDX/swift-dx-guide), and its Lovable project with it.
- **The cases typed in it are kept in the database** (see "Typed cases").

### What the prototype showed
- **One page**: free text about a patient, an agent picked, and back a differential (each diagnosis with its
  probability, whether it is critical, a short rationale) and a management plan (workups by type and priority,
  empirical treatment, the disposition), with its sources and a disclaimer.
- **Its backend is gone.** It calls `GET /api/agents?output_type=DDXManagement`, `GET /api/auth/` and
  `POST /api/diagnose {symptoms, model}`. The old project dropped the first and the last at 110f9a5 (2026-09-26).
- **Remastered has its answer**: the sample's management plan
  (`worlds/sample/_data/schemas/management_plan_v1.json`, the `plan` recipes), read as the repl and the API read
  answers (`chatddx.scorers.answer.read`) and served from a run's items (`docs/api.md`, "Case-derived content").

### Typed cases
Decided: **the texts typed in swift are kept in the database**, as a source of their own. A case is otherwise a
vignette in a source the World names, fetched by id when a run is sent, and never stored in the ledger, which keeps
only its fingerprint (`docs/chatddx.md`, glossary, "Fingerprint"). A typed case becomes one:
- **The source** is a new kind, `database`, which the inventory expects: "Another kind of source, such as a
  database, would be added beside directories as a kind of its own" (`docs/inventory.md`, "Sources"). It is declared
  in the inventory like any other, sensitive, and cleared for the endpoints swift runs on (`docs/inventory.md`,
  "Clearance").
- **Each text is added under a new id**, as typed, and never changed. Text cleanup applies when a run prepares it, as
  for any vignette (`docs/factors.md`, "Preparing a case").
- **The case and its family** are written through the bench for the person who typed it (`agents/wip-authoring.md`): a
  `Case` with the source, the id and the fingerprint of the bytes, and a family. The text, the case and the family are
  written in one transaction.
- **A run like any other**: one case and one seed, through the worker (`agents/wip-worker.md`). Its completion is
  case-derived and lands in the ledger; the vignette doesn't.

Why not a directory the app writes: that is a volume shared by every replica and the worker, backed up apart from the
database, and a second place to vet for sensitive text beside the database that holds the ledger
(`agents/wip-clearance.md`, "Takes"). The database's costs are code, written once.

Built below the page (agents/wip-authoring.md, phase 7), on the takes below and these:
- **A family per typed case**, owned by the person who typed it, named and in a language when they say so. A family
  follows one vignette, so one per person would hold several.
- **Adopted by id alone**: the same text typed twice is two vignettes, where a directory source would take it for a
  rename (`src/chatddx/catalog/families.py:check_adoptable`, `by_content`).
- **A plain fingerprint**, as for the sample: nothing manages keys yet. Open: a keyed one, since a short text's hash
  can be guessed by anyone who reads the factors, the reader included, while the text itself is kept from them.
- **The World's one database source** takes what is typed, unless one is named; the sample World has `typed`,
  cleared for its fake endpoints.
- **Quotas** in `chatddx.core.settings`: 20 000 characters a text, 50 texts a person a day. Over the quota is
  `OverQuota`, which the API answers 429. Runs aren't held to one yet: the worker's (`agents/wip-worker.md`).

Take, for its shape:
- **A schema of its own**, `source`, with a table of texts: the source's name, the id, the text, who typed it and
  when. Migrations at every tier (`docs/store.md`, "Tiers"): the writer may read and insert, the reader nothing, as
  for the ledger's items (`docs/migrations.md`, "ledger", "Tier 1"); insert-only triggers at tier 2, but for a delete
  kept to the admin, to purge spam.
- **Fetched through the store.** The inventory imports no store, so a `database` source is read through the store.
  Vignettes are fetched in five places today: the runner (`src/chatddx/runner/run.py`), `Bench.rendered_again`, the
  repl's `show case` (`src/chatddx/repl/inspecting.py`), the API's vignette (`src/chatddx/api/families.py`) and
  curation (`src/chatddx/curation/write.py`). One function that takes the store and the vignette would serve them
  all; a directory source still fetches itself.
- **One case by id.** `Source.cases` builds every case at once; the writer builds the one it adds.
- **Docs**, once built: suggestions (`AGENTS.md`, "Docs") for `docs/inventory.md` (the source kind), `docs/store.md`
  (the schema) and `docs/migrations.md`.

**Protection.** The demo is on the public web, but the portal has no guest: every request needs a session
(`docs/api.md`, "Signing in"), and people are added by an admin (`chatddx person add`). So:
- a person's typed cases and runs are held to a quota, and a text to a size, with a NUL refused, since the database
  can't keep one (`docs/store.md`, "Known gaps");
- signing in is rate limited, which is open (`agents/wip-identity.md`, "Open");
- a flood's real cost is the inference and the ledger rows each run adds, not the text, so the quota is on runs as
  much as on texts.

Open: a family per typed case, or one per person with tags; the text's language (a family's entry); whether the
demo needs anyone to type without an account, which would bring back a guest (A3 has none); and whether the
configurations offered are those whose output is the management plan, which `GET /api/threads` can't filter for yet.

## Phases
Assuming the takes.
0. **Before the first page.** `chatddx.portal` mounted beside the API; `Cache-Control: no-store` where case-derived
   content is shown. Jinja2 and python-multipart are in, and the cookie is `Lax`.
1. **Signing in, and pages to read**: runs and a run's page, configurations with their versions and recipe, families
   with their expectations (the vignette in its own place, A9), endpoints and models. No script.
2. **The variation being tried**, and its island, on the API's phase 3.
3. **Starting and watching a run**: the worker (`agents/wip-worker.md`), and the run's island, on the API's phases 4
   and 5.
4. **Swift**: the `source` schema and the `database` source kind, the bench's writes for cases and families, quotas,
   and the page (see "Swift"). All but the page is built.
5. **Authoring**: the bench's writes for chunks, appendices, expectations, scorers, labels and languages
   (`agents/wip-authoring.md`), and their pages. The writes are built; a scorer's pickers read
   `GET /api/scorer-code`.
6. **Batches**: the planner's pages (`agents/wip-batch.md`), then a batch's page and the worker's status
   (`agents/wip-worker.md`).
7. **Z1**, and what deleting hides.
8. **Docs**: material for a `docs/portal.md`, kept here as `docs/bench.md` is the bench's.

## Open
- **One process or two.** `chatddx api` serving the portal too, or a `chatddx portal` of its own on the same app.
- **Where the islands' build lives**: built by Nix with the package, or committed.
- **A page to test an endpoint**, as the old stack's **Test** did. Canaries and `confirm` cover parts of it.
- **Export.** The portal is to export results (`docs/chatddx.md`, glossary), and the export isn't planned
  (`docs/chatddx.md`, "On the table").
- **Keycloak in front** skips the sign-in page (`agents/wip-identity.md`, "Take, for when Keycloak arrives").

## Surprises
- The session cookie was `SameSite=Strict`, so a link into the portal from another site opened signed out. It is
  `Lax` now.
- A run in a request halts when the client goes away (A6, W1): right for the repl and a program, wrong for a browser
  tab (`agents/wip-worker.md`).
- The bench can't write a chunk, an appendix or an expectation, and the portal is where they are to be written
  (`agents/wip-authoring.md`).
- Neither `jinja2` nor `python-multipart` was a dependency; FastAPI's form fields need the second. Both are now.
- Swift is React, not Svelte: the old project's SvelteKit client was replaced by swift-dx-guide, a Lovable project.
  Its latest still calls `/api/agents` and `/api/diagnose`, which the old API dropped at 110f9a5.

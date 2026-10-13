# The portal: work in progress

The portal is the web interface "used to configure factors, watch runs and export results" (`docs/chatddx.md`,
glossary). It is the bench's third edge, after the repl and the API (`docs/bench.md`; `docs/api.md`). This file plans
it.

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **Decided: HTML pages rendered on the server from the bench, with Svelte islands in TypeScript that call the API**
   (see "How it is built").
2. **Decided: swift is the portal now.** There is no swift page apart from the portal: what swift showed is the
   portal's home page. A theme skeleton is extracted from swift-dx-guide and its reusable components are salvaged;
   that work sets the structure of the portal's frontend, and shows what Lovable has to teach (see "Swift").
3. **Decided: `chatddx portal`** serves the portal, and starts everything the portal needs with it: the API now, the
   worker once there is one (see "P3b, concretely").
4. **Phases 0 to 4 are built** (see "Built"): `chatddx.portal`, signing in and out, `Cache-Control: no-store`, a
   code beside each error's detail in the API (decided); then the frontend in `frontend/`, swift's theme and
   components, and the home page, the first island; then the pages to read; then the variation being tried, and
   starting and watching a run (decided, see "The variation being tried" and "Starting and watching a run"). The
   choices of phases 1 and 2 are takes (see "Built").
5. **What it stands on is built**: the bench and the API (`docs/bench.md`, `docs/api.md`), the writes for authoring
   (`agents/wip-authoring.md`) and typed cases (`docs/bench.md`, "Typed cases"). What isn't is under "Below the UI":
   the worker, the batch planner, Z1, and a few things the API doesn't give yet.
6. **Next**: phase 5, authoring (see "Phases"), or the worker under the runs (`agents/wip-worker.md`); and what
   phases 2 to 4 left (see "Open").

## What the portal shows
The old portal's manual reads as a functional spec for its pages: `docs/portal.md` in chatddx-administration/chatddx
at 504792c
(https://github.com/chatddx-administration/chatddx/blob/504792cbeb09508f2c52912be29a3d8809d2fa1d/docs/portal.md).
In remastered's terms:

| Page | Shows | Reads |
|---|---|---|
| Sign in | a form, and signing out | `People`, as `POST /api/session` does |
| Home | swift's: a case typed, a configuration and an endpoint picked, the answer as a management plan (see "Swift") | `POST /api/families`, `POST /api/runs`, its events and items |
| Runs | a person's runs, and those left to score with **Score again** | `Bench.runs`, `Bench.outstanding`; `GET /api/runs` |
| A run | the trial, how it came out and why, the case it ran, the endpoint and engine, tools, tokens, the configuration as it ran, the answer by view, scores, the messages part by part (folded, linkable as `#message-N`, loaded when opened), and the requests rendered again | `Bench.run_by_id`, `Bench.described`, `Bench.scores_of`, `Bench.rendered_again`, `src/chatddx/bench/outcome.py`; `GET /api/runs/{id}` and below it |
| Configurations | each with its versions, its recipe part by part, and its runs | `Bench.threads`, `Bench.reaching`, `Bench.scored_by`; `GET /api/threads?kind=configuration` |
| The variation being tried | a chunk picked per part, with the skeleton's digest, the findings at an endpoint, each scorer view's reach and the request rendered, as you pick | `GET /api/threads/{id}/variation` |
| Families | filtered by tag and name; a family's cases, appendices, and the expectation each is scored against under each schema, with those shared to take; the vignette in a place of its own | `Bench.families`, `Bench.family_by_id`, `Bench.expectation`; `GET /api/families` and below it |
| Authoring | a form per kind people write: chunks, recipes, appendices, cases, expectations, scorers and judges; what is said of a thread; following an origin; taking expectations | the bench's writes (`docs/bench.md`, "Writes for the person") |
| Endpoints and models | each endpoint's engine, model, host and clearances; the facts of each model | `GET /api/endpoints`, `GET /api/models` |
| Batches | the form, the confirmation before anything runs, **Run it now** or **Keep it for later**, and a kept batch's page | the batch planner (`agents/wip-batch.md`) |
| Status | the worker at the person's jobs, with pause, resume, stop and stop now | the worker (`agents/wip-worker.md`) |

Ways of showing things the pages keep:
- **A version timeline** on every thread: ◀ and ▶, "version i of n", and what each version changed, word by word.
- **A line that says where a save goes**, as you type: a new version of a thread of yours, a new thread, or a fork.
- **Live checks** where a page needs feedback before anything is written (see "Islands").
- **A confirmation** before a batch runs: the trials, what each variation sets, what is held back and why, the cases,
  and each scorer's reach.

## What the docs ask of it
- Interfaces for instructions, few-shots, prompts, output, sampling, reasoning, passthrough, recipes, appendices,
  expectations, trials, judges, scorings, and starting and monitoring runs (`docs/chatddx.md`, "Requirements").
- The variation workflow: try, save the successful as configurations, delete the rest, branch (`docs/chatddx.md`,
  "Intended evolution of configurations").
- A scorer's labels written with its edit: the editor sends each view's label with the views, and moves them with the
  views it moves (`docs/catalog.md`, "Scorer labels"; `docs/bench.md`, "Scorers").
- A new version offered the previous version's language, which the bench doesn't carry over itself
  (`docs/catalog.md`, "Languages"; `docs/bench.md`, "Languages").
- A case left at an earlier vignette by a repair offered its replacement, which the bench stores when asked
  (`docs/catalog.md`, "What has moved on"; `docs/bench.md`, "Appendices and cases").
- What deleting hides: everywhere, or only in pickers (`docs/catalog.md`, "Deleting" and "Smaller issues").
- Pickers of the right kind for each reference, if components' JSON Schemas say it (`docs/factors.md`, "Reference
  kinds in components' JSON Schemas"), and execution settings to pick, if they become a component ("Execution settings
  as a component").
- A change made in the portal kept in git through an export (`docs/curation.md`, "Import, export and verification").
- Clearance granted in the database, through the portal and logged, as a long-term option
  (`agents/wip-clearance.md`, "Open", 2).

An appendix's line endings need nothing of the portal: the bench makes them LF for every edge (`docs/bench.md`,
"Appendices and cases").

## How it is built
Decided: HTML pages rendered on the server, per request, from the bench, with Svelte islands that call the API where a
page needs feedback without a reload. The portal consumes the bench, as every edge does (`docs/bench.md`), and the API
where it is interactive. Its look and the structure of its frontend come from swift (see "Swift").

### P3b, concretely
Decided:
- **`chatddx portal`** serves the app, the portal at `/` and the API at `/api/`, as `chatddx api` serves the API
  alone, with the same `--world`, `--facts` and `--bind`. It starts everything the portal needs with it: the worker,
  once there is one, in the app's process (`agents/wip-worker.md`, K1), and the frontend's build when it has one.
- **One app.** `src/chatddx/portal/`, a package beside `src/chatddx/api/`, mounted at `/` in the same FastAPI app as
  the API at `/api/` (`src/chatddx/api/app.py:app`). Its routes return HTML rendered with Jinja2 (Starlette's
  `Jinja2Templates`), and build a bench per request, as the API's routes do (`src/chatddx/api/people.py:bench`).
- **One session**: the API's cookie, `__Host-chatddx-session`, `Path=/`, `SameSite=Lax`, so a link into the portal
  from another site opens signed in. A sign-in page posts a form to the portal, which calls `People` as
  `POST /api/session` does.
- **Forms are plain POSTs**, checked by the API's same-origin check (`src/chatddx/api/people.py:same_origin`), so
  there is no CSRF token, as there is none for the API.
- **Errors carry a code** beside their detail, so that a page or an island tells a refusal apart without reading its
  sentence (`docs/api.md`, "Errors", which has an AGENT suggestion).
- **Dependencies**: `jinja2`, and `python-multipart` for FastAPI's form fields, both in `pyproject.toml`, imported
  only under `chatddx.portal` as `rich` is only under `chatddx.repl`.

### Islands
Decided: Svelte with TypeScript, only where a page needs feedback that takes a round trip or live state:
- **The home page**: the text, and the answer as it comes (see "Swift").
- **The variation being tried**: pick a chunk per part and see what it would make, as you pick.
- **A run as it runs**: its items as they start and end, and the deltas while you watch (`docs/api.md`, "Its
  events").
- **The batch form**: ticking chunks per part, with the number of trials, what is held back and each scorer's reach as
  you tick (`agents/wip-batch.md`, "Callers").
- **A batch's progress** and the worker's state (`agents/wip-worker.md`).
- Perhaps editors for structured chunks and expectations, checked against their JSON Schema as you type.

Decided, for how, and built in phase 1:
- **Built by Vite** into static files the app serves, a bundle per island.
- **Types from `/api/openapi.json`** (openapi-typescript), so an island's types follow the API's pydantic schemas. A
  test checks that what they're generated from is current.
- **Tailwind** for the portal's styling, the pages' and the islands' alike.
- **Node and Vite join the flake's dev shell**, and the build joins the flake's packages.

### Tests
Decided:
- **Pages**: `TestClient` on the HTML, in `src/chatddx/portal/test/`, on the test World as `curated` lands it, as the
  API's are; marked `wip` until `docs/portal.md`.
- **Islands**: through the API's tests for what they call; an island's pure logic by vitest
  (`pnpm --dir frontend test`, built in phase 3); and a browser test under pytest (Playwright, with the container's
  Chromium), built in phase 4 (R12).
- **Runs to show**: the test World's six scripted runs (`docs/scripted.md`, "The runs"), run once into `ran`
  (`src/chatddx/conftest.py`), built in phase 2.

## The variation being tried
Decided (phase 3), from the options V1 to V9:
- **V1. Its address is the configuration's page**: `/configurations/{id}?PART=DIGEST…&head=EDIT&endpoint=…&tag=…`,
  parts by digest, as the API takes them. Phase 2's page is the variation with nothing replaced, as the old portal's
  configuration page showed a version "with whatever variations were set in place of its own". Runs and, later, a
  batch's confirmation link to it.
- **V2. An island draws it from the API**: the pickers and what the variation makes, with the address following each
  pick. The server draws the rest of the page; without scripts, the recipe as the address gives it shows read only.
- **V3. A part's picker** offers every chunk of that part the person sees, one entry per digest, their own first and
  others' as `owner/name`, grouped by what the name says it is made for; the lints flag a mismatch. An optional part
  offers none.
- **V4. An endpoint picker**, defaulting to one serving the configuration's model, and the cases by tag; no lints
  without an endpoint. Where another variant of the configuration is made for the endpoint's model, a link says so.
- **V5. Saving in phase 3**: a name, a line saying where the save goes (a new version of this configuration, a new
  configuration, or that it is one already), then a fork or an edit through the API, a conflict shown, and the saved
  configuration's page.
- **V6. The runs of the variation**, by its skeleton (`GET /api/runs?reaching=`), on its page.
- **V7. An edit to vary**: the look takes `head`, and the page steps through the versions with ◀ ▶, keeping what is
  set. A variation of an earlier version is saved as a fork.
- **V8. The API gives** a look's `label` and `held_by` (the configuration whose head the skeleton is, the person's
  own first), and a thread's `language` in listings.
- **V9. Tests**: the pages and the API by `TestClient`, the island's pure logic by vitest, and the island by hand in
  Chromium; a browser test in the suite comes with phase 4's run island.

## Starting and watching a run
Decided (phase 4), from the options R1 to R12:
- **R1. A run is started** from the variation's page, a panel beside what the variation makes, and again from a run's
  page (**Run again**: its variation, cases and endpoint, a new seed); then the run's page follows it.
- **R2. A run is watched on its page**: the server draws what the ledger holds, and an island follows the run's events
  while something is under way for it, then reloads the page into what it finished as.
- **R3. Watching shows** how far it has come (the items ended of all, by outcome), each item's state (waiting,
  thinking or writing with its tokens, ended with its outcome), the text of an item unfolded as it streams, and the
  scoring as each scorer starts and ends, its judges' calls counted.
- **R4. Halt** while something is under way, and **Score again** on a run's page and in the runs left to score; a
  scoring is watched as a run is.
- **R5. A run names the edit it varies** (`head` on `NewRun`), so it runs what was looked at.
- **R6. The cases** are the variation's tags, or families picked, with the number of items said before it starts;
  one seed, the look's, which can be changed.
- **R7. A run is named by its variation's label** as it starts, which `Bench.described` reads first (`docs/api.md`,
  "Outstanding", "Variations").
- **R8. Limits in `settings`**: runs a day per person and items per run, kept by the bench for every edge, refused as
  over quota.
- **R9. Concurrency** stays 1 until the worker shares an endpoint's `max_jobs` between runs.
- **R10. On the jobs in the app's process**; the worker takes their place with the API as it is.
- **R11. A keep-alive** on a run's event stream (`docs/api.md`, "Outstanding", "A quiet stream").
- **R12. A browser test** under pytest with Playwright (Python), on the test World and its fake vLLM: start, watch,
  halt and score again; and the island's logic by vitest.

## Swift
Decided:
- **Swift is the portal now.** What swift showed is the portal's home page, and nothing called swift stands apart
  from the portal.
- **swift-dx-guide is mined, not ported**: a theme skeleton is extracted from it, and its reusable components are
  salvaged. That work sets the structure of the portal's frontend, and shows what Lovable has to teach. The repository
  is chatddx-administration/swift-dx-guide, a Lovable project.
- **The home page**: a person types a case, picks a configuration and an endpoint, and reads the answer as a
  management plan.
- **The texts typed in it are kept in the database**, as a source of their own (see "Typed cases").

### What swift-dx-guide holds
Surveyed at 2e1af7e. React 18 with TypeScript, built by Vite, styled with Tailwind 3 and shadcn/ui (Radix underneath),
with react-query, react-router, lucide icons and sonner toasts; pnpm, and a Nix flake that builds `dist/` with
`fetchPnpmDeps`.
- **The theme**: shadcn's tokens as HSL CSS variables in `src/index.css` (background, foreground, card, popover,
  primary, secondary, muted, accent, destructive, border, input, ring, radius), with `warning`, `success`, two gradient
  stops and two fonts of its own (Plus Jakarta Sans, and Outfit for headings), each in a light and a `.dark` set.
  `tailwind.config.ts` maps them to colors and radii. `glass-card`, `gradient-bg`, `gradient-text`, `glow-primary`
  and a few animations are its own classes. The fonts come from Google Fonts.
- **Primitives**: 49 shadcn/ui components in `src/components/ui/`, of which the page uses 10: alert, badge, button,
  card, label, select, textarea, tooltip, and the two toasters.
- **Its own components** render the answer: `DiagnosisResults` (an acute warning, the differential, the management,
  the sources, copying it all as text, and a disclaimer), `DiagnosisCard` (a diagnosis, its probability, and its
  rationale when unfolded) and `ManagementSection` (the workup by type, lab tests grouped by name; empirical treatment
  with its warnings; the disposition). They read the shape of the sample's management plan
  (`worlds/sample/_data/schemas/management_plan_v1.json`): `acute_warning`, `diagnoses` (`diagnosis`, `probability`,
  `critical`, `short_rationale`), `management` (`workup` with `type`, `investigations` and `priority`;
  `empirical_treatment` with `indication`, `treatment` and `important`; `disposition`) and `sources`. Neither
  `critical` nor a workup's `priority` is shown, and fields of older answers are (`description`, `red_flags`,
  `summary`, `raw`).
- **The page** (`src/pages/Index.tsx`): a header, a disclaimer, the text, a model picked, and the results. It calls
  the old API, which is gone.
- **Lovable's own**: `lovable-tagger`, which tags components for Lovable's editor in development, and its README.

Built, as takes (see "Built", "Phase 1"):
- **The theme skeleton** is the tokens, both sets, and Tailwind's mapping of them, shared by the pages and the islands,
  in `frontend/src/portal.css`. The tokens stay swift's HSL, written as whole colors, which Tailwind 4 mixes itself.
  The dark set follows the system's preference (`prefers-color-scheme`), as swift had no switch. The fonts are served
  by the app (`@fontsource-variable`), so that a page showing case-derived content fetches nothing from a third party.
  `glass-card`, `gradient-bg`, `gradient-text`, `glow-primary` and the animations come along.
- **The primitives come from shadcn-svelte** (v1.7, its "vega" style, the classic shadcn/ui look), and only the ones
  used: alert, badge, button, card, label, native-select and textarea. A native select stands in for Radix's, which
  plain forms on the server's pages can use too.
- **The three answer components are ported to Svelte** as the renderer of a management plan
  (`frontend/src/lib/plan/`), and show what swift didn't: a critical diagnosis, and a workup's priority. The older
  answers' fields are gone. Copying the answer as text isn't ported: it puts case-derived content on the clipboard
  (`agents/wip-clearance.md`, "Open", 6).

### What Lovable teaches
Taken:
- **Tokens as CSS variables**, in a light and a dark set, mapped once to Tailwind's colors and radii.
- **Primitives apart from the app's own components**: `frontend/src/lib/components/ui/` beside `lib/plan/`.
- **`cn()`**, clsx and tailwind-merge, so that a component's classes and a caller's merge.
- **An alias for the source root**: `$lib`, as shadcn-svelte names it, where Lovable has `@`.
- **A Nix build of the bundle** from pinned dependencies (`fetchPnpmDeps`), and pnpm only.

Left:
- **Every primitive generated up front**: 49, of which the page used 10. The portal copies one when a page wants it.
- **A client cache and router** (react-query, react-router) for a page that makes five calls: the server routes, and
  an island fetches what it shows.
- **Toasts for errors**, which go away: an island says what went wrong where it went wrong.
- **An `.env` in the repository**, and the editor's tagger (`lovable-tagger`).

### The home page
- **One page**: a text about a patient, a configuration and an endpoint picked, and back a differential (each
  diagnosis with its probability, whether it is critical, a short rationale), a management plan (workups by type and
  priority, empirical treatment, the disposition), its sources and a disclaimer.
- **Typed, run and read**: the text is typed as a case (`POST /api/families`), run with one seed and not scored
  (`POST /api/runs`), followed (`GET /api/runs/{id}/events`), and its answer read from its item
  (`GET /api/runs/{id}/items`, `answer`).
- **What it offers**: the configurations whose answer's JSON Schema is titled `management_plan_v1`
  (`GET /api/threads?kind=configuration&answers=…`), the person's own before another's of the same name, others' shown
  as `owner/name`; and the endpoints whose engine can be told. Picking an endpoint picks the configuration made for its
  model, when there is one.
- **While it runs**: whether the model is thinking or writing, and its tokens so far. An answer that breaks its schema,
  or was cut short, is shown as far as it goes, and said so.

### Typed cases
Built below the home page: the `database` source kind and the `source` schema, `Bench.type_case`, `POST /api/families`,
and the limits on a text's length and on texts a day (`docs/bench.md` and `docs/api.md`, "Typed cases";
`docs/inventory.md`, "Sources"; `docs/store.md`, "Texts"; `docs/migrations.md`, "source"). A typed case runs as any
case, and its completion lands in the ledger; the vignette doesn't.

### Protection
The demo is on the public web, but the portal has no guest: every request needs a session (`docs/api.md`, "Signing
in"), and people are added by command (`chatddx person add`). So:
- a person's typed texts are held to a quota and a text to a size, with a NUL refused (built);
- a person's runs are held to a quota a day, and a run to its items, by the bench (built in phase 4, R8);
- signing in is rate limited, which is open (`docs/api.md`, "Outstanding", "Signing in");
- a flood's real cost is the inference and the ledger rows each run adds, not the text, so the quota is on runs as
  much as on texts.

### Open
- A family per typed case, as built, or one per person with tags.
- The text's language, a family's entry.
- Whether the demo needs anyone to type without an account, which would bring back a guest (the API has none).
- The configurations offered by the title of their answer's schema, `management_plan_v1`, which the renderer is written
  for. A schema's title is a loose handle: another schema could take the same title.

## Built
Phase 0, `wip` under this file:
- **`src/chatddx/portal/app.py:app`**: the API's app (`src/chatddx/api/app.py:app`), with the portal's pages
  mounted at `/` and left out of the OpenAPI document, and `SignInFirst` answered by a redirect to signing in.
- **`src/chatddx/portal/pages.py`**: `GET /` (the home page, for now who is signed in), `GET` and `POST /sign-in`, and
  `POST /sign-out`. A page wants the session cookie, and without one, or with one that has ended, sends the person to
  `/sign-in?next=` the page. Signing in sets the API's cookie (`src/chatddx/api/people.py:keep_cookie`) and leads to
  `next`, but only within the site: anything not starting with one `/` leads home. A wrong login or password shows the
  form again, with the login kept. Forms pass `same_origin` first. Every page says `Cache-Control: no-store`, since
  pages are per person and most will show case-derived content.
- **`src/chatddx/portal/templates/`**: `base.html`, `sign-in.html` and `home.html`, autoescaped.
- **`chatddx portal`** (`src/chatddx/cli.py:_portal`, sharing `_serve` and `_serving` with `chatddx api`).
- **The API**: `Cache-Control: no-store` on a family's vignette, a run's items, a score's items and a run's events
  (`src/chatddx/api/state.py:no_store`, `NO_STORE`); every refusal as `{"detail", "code"}`
  (`src/chatddx/api/app.py:STATUSES`, `CODES`; `src/chatddx/api/schemas.py:Error`). `docs/api.md` and
  `docs/api-api.md` have AGENT suggestions; the API's tests, which pin the codes and the header, stay `solidified`.
- **Tests**: `src/chatddx/portal/test/test_signing_in.py`.

Found on the way:
- **A route's name is the handler's**, and FastAPI keeps one table for the app: the portal's handlers are named
  `signing_in_page`, `signing_in` and `signing_out`, so that `url_path_for` doesn't find the API's `sign_in` and
  `sign_out` for them.
- **What the portal doesn't route was answered as the API answers**: JSON with a code, as an unknown page's 404 or a
  form from another site's 403. Pages of their own for those are built in phase 2.

Phase 1, `wip` under this file:
- **`frontend/`**, beside `src/`: a Vite project, pnpm only (`packageManager`), Svelte 5 with TypeScript 5.9
  (openapi-typescript and svelte-check don't take 7 yet), Tailwind 4. Its entries are `src/portal.css`, the styles of
  every page, and an island per `src/islands/<name>.ts`. `pnpm build` writes `frontend/dist/` with Vite's manifest;
  `pnpm check` runs svelte-check. Neither `node_modules`, the build nor the generated types are committed.
- **The API's types**: `frontend/openapi.json` is the API's OpenAPI document, written by `chatddx openapi`
  (`src/chatddx/cli.py:_openapi`) and committed, so that the frontend builds without Python; openapi-typescript
  generates `src/lib/api/schema.d.ts` from it, with `--default-non-nullable false`, since a request's defaulted field
  isn't required. `src/lib/api/client.ts`: `api` (openapi-fetch), `why`, the detail of a refusal, and `follow`, a
  run's events through `EventSource`. A test holds the document to the API's
  (`src/chatddx/portal/test/test_frontend.py`).
- **The components**: shadcn-svelte's vega style as its registry holds it (`docs/static/registry/styles/vega/` in
  huntabyte/shadcn-svelte at 63bfef7), with `$UTILS$` and the icon placeholder filled as the CLI fills them, since the
  CLI's registry, shadcn-svelte.com, is denied by this environment's network policy. `components.json` is the CLI's,
  for a later `add`.
- **The home page** (`frontend/src/islands/Home.svelte`; see "Swift", "The home page").
- **Serving it**: `src/chatddx/portal/assets.py:Assets` reads the manifest when a page is rendered, so a rebuild shows
  at once; a page gets the styles, and the home page its island's script and styles. The build is served at `/static/`
  from `settings.portal_assets()`, `CHATDDX_PORTAL_ASSETS` or else `frontend/dist`
  (`src/chatddx/portal/app.py:app` takes another for the tests). The templates are themed, and Tailwind reads them
  (`@source` in `portal.css`, as a glob: the directory alone wasn't read).
- **`chatddx portal --watch`** runs `pnpm install --frozen-lockfile` and then `pnpm run watch` in `frontend/` for as
  long as the portal is served. Without it, and nothing built, it says so and serves unstyled pages.
- **The flake**: Node 22 and pnpm (11) in the dev shell, and `packages.frontend`, the build, from the templates and
  `frontend/`, its dependencies fetched by `fetchPnpmDeps` (`fetcherVersion = 4`) under a hash that changes with
  `pnpm-lock.yaml` (see "Open"). pnpm 11 refuses a release younger than a day (`minimumReleaseAge`), which
  `frontend/pnpm-workspace.yaml` asks of pnpm 10 too; pnpm 10 doesn't hold to it, so two packages it resolved are
  overridden there, and `@lucide/svelte` is pinned a release back. Built and checked here with nixpkgs and the other
  inputs fetched over git (`--override-input`), as this environment reaches GitHub's archives for nothing it hasn't
  attached, and with the dependencies first fetched trusting its proxy's CA (`NODE_EXTRA_CA_CERTS` among the fetch's
  `impureEnvVars`, which the flake doesn't keep).
- **The API**: a run's items carry the answer as read (`answer`: its value, why it couldn't be read or breaks its
  schema, and whether it was salvaged), and configurations are listed by what they answer (`answers`, the title of
  their answer's JSON Schema; `Bench.answering`). `docs/api.md`, `docs/api-api.md`, `docs/bench.md` and
  `docs/bench-api.md` have AGENT suggestions; the tests stay `solidified`.
- **Tests**: `src/chatddx/portal/test/test_frontend.py`, and by hand on the sample World with its fake engines in
  Chromium (Playwright), signed in as alice, light and dark.

Phase 2, `wip` under this file, as takes:
- **The pages call the API's handlers** with a bench made per request (`src/chatddx/portal/pages.py:page_bench`), so a
  page shows what the API answers, and is refused as it is. A module per kind under `src/chatddx/portal/`:
  - `runs.py`: `GET /runs`, a person's runs fifty to a page, and those left to score (`?left=true`), without
    **Score again**, which writes. `GET /runs/{id}`: the run (when, its configuration, linked to the thread whose head
    is its skeleton, the endpoint and engine, the cases, seeds, trial and rig); what was noted as it ran and what is
    checked now; its items; each scoring as a table of case by view, with the means; and a section per item,
    linkable as `#item-N`: how it came out and why, the answer as read, and the last call's message part by part
    (reasoning, content and tool calls, folded but for the content).
  - `configurations.py`: `GET /configurations`, by purpose (generation or judge); `GET /configurations/{id}`, what is
    said of it, its recipe part by part (the chunk picked and what it holds), its versions, and the runs of its latest
    version (`reaching`). A thread of another kind isn't found.
  - `families.py`: `GET /families`, by tags; `GET /families/{id}`, its cases with their appendices, and under each
    expectation schema the expectation each is scored against, or why it is ambiguous, with those shared to take;
    `GET /families/{id}/vignette`, the vignette on a page of its own.
  - `world.py`: `GET /endpoints`, the endpoints and the models' facts.
- **An answer as a management plan**: on a run whose skeleton's output schema is titled `management_plan_v1`, an
  answer is drawn by the home page's renderer, mounted by the `answers` island (`frontend/src/islands/answers.ts`)
  where the page holds the answer as JSON, which shows without scripts. Other answers show as text or JSON.
- **Pages for errors**: a refusal on a page, and a page that isn't there, is answered with a page of the same status,
  titled by its code (`src/chatddx/portal/pages.py:paged`, `templates/error.html`); under `/api/` it is JSON as before.
- **The pieces the pages share** are macros (`templates/macros.html`), and the nav links Runs, Configurations,
  Families and Endpoints. An island's imported chunks are preloaded (`src/chatddx/portal/assets.py:Island`).
- **Tests**: `src/chatddx/portal/test/test_reading.py`, on `ran` (`src/chatddx/conftest.py`), `curated` with alice's
  scripted runs each run once; `docs/scripted.md` has AGENT suggestions. By hand on the sample World in Chromium,
  every page, with the plan drawn.

Phase 3, `wip` under this file, as decided (see "The variation being tried"):
- **The API**: a look takes `head`, the edit to vary, and gives its `label` and `held_by`; a configuration's fork takes
  `head` too; a listed thread has its `language`, looked up for many at once (`Catalog.languages_of`;
  `Bench.variation(…, head)`). `docs/api.md`, `docs/api-api.md`, `docs/bench.md`, `docs/bench-api.md` and
  `docs/catalog-api.md` have AGENT suggestions; the tests stay `solidified`.
- **`GET /configurations/{id}`** takes the API's `Varying` as its query: the parts by digest, `head`, `endpoint`
  and `tag`. Without an endpoint it picks one serving the model the configuration's name is made for. The server
  draws what is said of it and its versions, with ◀ ▶ and every version's link keeping what is set, and a note on an
  earlier one; the variation's recipe and its runs as the address gives them, for a page without scripts; and the
  island's props as JSON (`src/chatddx/portal/configurations.py`).
- **The `variation` island** (`frontend/src/islands/Variation.svelte`): a picker per part (one entry per digest,
  the person's own first, others' as `owner/name`, the names it also goes by, grouped by what the name says it is made
  for, the configuration's own marked); the label, the skeleton, greedy, and the configuration that is the variation
  already; the endpoint, with a link to the configuration made for its model, and the tags; the lints, each scorer
  view's reach with the families it misses, and the request folded; the name and the line saying where a save goes,
  saving by a fork or an edit; and the runs of the skeleton. Each pick asks the API again and keeps the address and
  the versions' links in step (`history.replaceState`). Its pure logic is `frontend/src/lib/variation/logic.ts`.
- **A run's page** links the version it ran: the person's own configuration first, its head or else an earlier edit
  (`src/chatddx/portal/runs.py:_version`).
- **An error page** lists what didn't validate.
- **The frontend**: vitest (`pnpm --dir frontend test`), and shadcn-svelte's input, as the components before. The
  flake's pnpm hash follows the lockfile.
- **Tests**: `src/chatddx/portal/test/test_varying.py`, `frontend/src/lib/variation/logic.test.ts`, and by hand on
  the sample World in Chromium: picking, another endpoint, tags, forking, a new version, stepping back, and the page
  without scripts.

Phase 4, `wip` under this file, as decided (see "Starting and watching a run"):
- **The API**: a run takes `head`, the edit it varies (`NewRun.head`); a run is named by its variation's label as it
  starts, which `Bench.described` reads first; `POST /api/runs/{id}/again` runs a run's trial again with another seed
  (`Bench.again`), so a run of a variation nobody saved can run again without it; runs a day and items a run are
  limited (`settings.RUNS_PER_DAY`, `ITEMS_PER_RUN`; `Catalog.runs_started`), refused as over quota; and a quiet event
  stream sends `: keep-alive` every 15 s (`src/chatddx/api/jobs.py:KEEP_ALIVE`). `docs/api.md`, `docs/api-api.md`,
  `docs/bench.md`, `docs/bench-api.md`, `docs/catalog-api.md` and `docs/repl.md` have AGENT suggestions; the tests stay
  `solidified`.
- **Following a run** (`frontend/src/lib/runs/`): `watch`, a run's events through `EventSource`, and `fold`, which
  folds them into a run's progress: its items as they are sent, stream and end, what is noted, and each scorer's
  scoring with its judges' calls. The home page follows its run with them too.
- **The variation's page** gets **Running it**: the cases tagged, or families picked by name, the seed and whether to
  score, the number of items said, and **Run it**, which leads to the run's page.
- **A run's page**: while something is under way for it in the app's process, the items, scores and answers give way
  to the live view (`frontend/src/islands/RunLive.svelte`), which reloads the page when the run is done. **Halt**,
  **Score again** (by the scorers it is left to) and **Run again** are plain forms (`src/chatddx/portal/runs.py`:
  `halting`, `scoring`, `running_again`), which call the API's handlers and lead back to the run's page; **Score again**
  is also in the runs left to score. The `run` island also draws the answers as management plans, as `answers` did.
- **Tests**: `src/chatddx/portal/test/test_running.py`; `test_browser.py`, the variation run from its page, followed,
  halted, scored again and run again in Chromium (Playwright, a test dependency at 1.56.0, skipped without a build or
  a browser); `frontend/src/lib/runs/progress.test.ts`; and by hand on the sample World with its fake engines.

## Below the UI
What the portal needs below its pages that isn't built:
1. **The worker** (`agents/wip-worker.md`): runs that outlive the app's process and are seen from every replica, and
   a quota on runs. Until then a run is a job in the app's process (`docs/api.md`, "Where it runs"), which the run's
   pages can be built on, since the API stays as it is when the worker takes its place.
2. **The worker's controls and status** (`agents/wip-worker.md`, "The plan", 4).
3. **The batch planner** (`agents/wip-batch.md`).
4. **Z1**, the map from roles to kinds, which waits for the portal's views (`docs/bench.md`, "Outstanding";
   `agents/wip-identity.md`, "Open").
5. **From the API's "Outstanding"** (`docs/api.md`), what the portal meets first: a keep-alive on the event stream,
   which a proxy cuts when it is quiet.

## Phases
0. **Before the first page**, built (see "Built"): `chatddx portal`, `chatddx.portal` mounted beside the API, signing
   in and out, `Cache-Control: no-store` where case-derived content is served, and the API's error codes.
1. **Swift**, built (see "Built"): the frontend's structure, Node, Vite and the build in the flake; Svelte, TypeScript
   and Tailwind; types from `/api/openapi.json`. The theme skeleton and the salvaged components, then the home page,
   the first island.
2. **Pages to read**, built (see "Built"): runs and a run's page, configurations with their versions and recipe,
   families with their expectations (the vignette in its own place), endpoints and models.
3. **The variation being tried**, and its island, built (see "Built").
4. **Starting and watching a run**, built (see "Built"): the run's island, on the API's runs and events; the worker
   under them when it is built (`agents/wip-worker.md`).
5. **Authoring**: the pages for the bench's writes, which are built; a scorer's pickers read `GET /api/scorer-code`.
6. **Batches**: the planner's pages (`agents/wip-batch.md`), then a batch's page and the worker's status
   (`agents/wip-worker.md`).
7. **Z1**, and what deleting hides.
8. **Docs**: material for a `docs/portal.md`.

## Open
- **Where the frontend's build lives.** Take, built: not committed; built by pnpm in development and by Nix
  (`packages.frontend`) for a deployment, which points `CHATDDX_PORTAL_ASSETS` at it. The flake's default package, the
  Python environment, doesn't hold it. A change to `frontend/pnpm-lock.yaml` wants a new hash in `flake.nix`: build
  with `lib.fakeHash`, and take the one Nix reports.
- **Caching the build**: its files are named by their content, so they could be kept for good (`immutable`);
  Starlette's `StaticFiles` sends an ETag and a date only.
- **The home page's flow in the browser test**: it is checked by hand; the browser test drives the variation and the
  run's pages (phase 4).
- **The browser test in the flake's dev shell**: Playwright's Python package brings a driver that a Nix shell may not
  run as it is, and its browser is the container's Chromium (revision 1194, which `playwright==1.56.0` expects). Take:
  nixpkgs' `playwright-driver.browsers` of the same version, pointed at by `PLAYWRIGHT_BROWSERS_PATH`, when a Nix
  shell runs it; until then the test skips where Chromium can't start.
- **The frontend's checks**: `pnpm check` runs by hand; nothing runs it beside `pytest`.
- **A page to test an endpoint**: a live check of the server and the model, written down nowhere. Canaries and
  `confirm` cover parts of it.
- **Export.** The portal is to export results (`docs/chatddx.md`, glossary), and the export isn't planned
  (`docs/chatddx.md`, "On the table").
- **Keycloak in front** skips the sign-in page (`agents/wip-identity.md`, "Take, for when Keycloak arrives").

### What the pages to read leave
From "What the portal shows", not on the pages yet:
- **What each version changed**, word by word: the versions are stepped through (◀ ▶, phase 3), but not compared.
- **The requests rendered again** on a run's page (`GET /api/runs/{id}/rendered-again`), which renders every item's
  requests anew.
- **A score's items**: what a scorer found per item and its judges' calls
  (`GET /api/runs/{id}/scores/{score}/items`), and the runs a scorer scored (`scored_by`). A run's page shows the
  values and their means.
- **The configuration as it ran**: a run links the version of a configuration it ran (phase 3), but a run of an
  unsaved variation links nothing, and its page doesn't show the skeleton's parts, nor a run's tools.
- **A run's calls loaded when opened**: a run's page holds every item's last call. Take: an island that loads an
  item's call when it is opened, once runs are large enough to need it.
- **Families by name**, beside by tag.
- **Runs of a configuration's earlier versions** under its thread: the variation's page lists the runs of the version
  shown.

### What the variation being tried leaves
- **A run of an unsaved variation** isn't linked to the variation it ran: its recipe is stored with its compilation,
  but not what it varied (`docs/api.md`, "Outstanding", "Variations": the label kept as the run's name).
- **The pickers rest on names** for what a chunk is made for (`agents/wip-variants.md`); a chunk older than its
  thread's head is offered only when the variation holds it.
- **The part pickers are native selects**: a long list (26 reasoning chunks in the sample World) wants a searchable
  picker, perhaps bits-ui's combobox.
- **A seed** is drawn for each look and kept while the page is open; it isn't in the address, so a reload draws
  another. A run takes the seed shown, which can be changed.
- **The page's cost**: the server lists every part's chunks, the configurations, the endpoints, the families and the
  look itself, about 0.6 s on the sample World. Listing a configuration's language costs its skeleton's compilations
  (`Catalog.languages_of`), one query per skeleton.
- **The frontend's tests** (`pnpm --dir frontend test`) run by hand, as `pnpm check` does.

### What starting and watching a run leaves
- **Concurrency** is 1 (R9): a run of the sample World's 104 cases sends them one at a time.
- **A run lives in the app's process** (R10): a restart ends it, and another replica tells it from the ledger without
  its live text and can't halt it. The worker takes its place (`agents/wip-worker.md`).
- **The live view holds every item's text** as it streams, in the page; a large run with long answers makes a heavy
  page. Take: drop the text of an item once it has ended, which the run's page shows after it is done.
- **Replicates**: a run takes one seed; several seeds are the batch planner's (`agents/wip-batch.md`).
- **The limits** (`settings.RUNS_PER_DAY`, 100, and `ITEMS_PER_RUN`, 200) are takes, as is counting a day back from
  now. A scoring isn't limited.
- **Running again** re-sends a run's trial; it doesn't follow the configuration if it has moved on since.


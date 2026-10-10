# Healthcheck at 657716a (dirty)

Dirty: reworked in its session instead of left as generated. It was taken at 657716a, then amended as the doc fixes it
prompted landed, last against 950c70a, so it isn't the record of a single pass. Healthchecks from here on are generated
once and left unchanged: re-take one rather than update it.

- **Signed:** Claude Opus 5.5 at effort xhigh, 1M-token context, as the session reports them; Claude Code 2.1.296 in a
  claude.ai cloud session, with a shell, PostgreSQL 16 and GitHub access. The first pass spawned three
  general-purpose subagents of the session, for the plans, the docs and the code.
- **Date:** 2026-10-10.
- **Passes:**
  1. 5976b07: taken at 657716a.
  2. 791f355: the subagents' reviews folded in; checked against a5864d9.
  3. Checked against 950c70a, and what it fixed taken out. `src/`, `worlds/`, README and the project files haven't
     changed since 657716a, so the checks' results and the code findings stand.
- **Prompt:**
  ```
  At 657716a

  Make a healthcheck, check:

  1. The general vibe
  2. What's ahead
  3. How's it going
  ```

Verdict: healthy. A young (12 days, 27 commits), disciplined codebase, green across the board. The risks are process
(no CI, near-zero review latency at thousands of lines a day) and a few privacy edges to close before real patient data.
None of it looks structurally rotten; it reads like a well-shaped draft that needs a hardening pass.

## 1. The general vibe

| Check | Result |
|---|---|
| `pytest` | 501 passed, 63 s (AGENTS.md says ~50 s) |
| `pytest -m 'not slow'` | 447 passed, 25 s; 3 reruns stable |
| basedpyright | 0 errors, 0 warnings (`reportAny` and `reportExplicitAny` are off in pyproject.toml) |
| ruff check / format | clean |
| Suppressions | 0 TODO/FIXME/XXX/HACK, 0 `type: ignore`, no bare `except`; 2 `pyright: ignore` (`factors/base.py:141`, :216) and 1 `noqa: BLE001` on a broad `except Exception` (`runner/rounds.py:65`), all justified |
| README walkthrough | works end to end: migrate → init-data → fake-engines → repl `run DutchFall10w`, scored and recorded |
| `chatddx api` | boots, 14 routes (session + reads), 401 without a session |
| Size | ~14.7k src lines, ~12.5k test lines, 16 docs, 13 wip plans |
| Solidified vs wip tests | 246 / 255 collected (217 / 206 test functions): half the codebase is still draft |

Paths below are relative to `src/chatddx/` unless they start with `docs/`, `agents/`, `worlds/` or `src/`.

### Layering
No import cycles. The layers, bottom up:
1. factors, identity, fake_vllm, tools
2. core, ledger, catalog, inventory, facts
3. scorers, importers, store
4. runner, curation
5. bench
6. api, repl
7. cli

store sits above catalog and ledger (`store/store.py:12`, `store/catalog.py:4`): the catalog's domain code reads
through a `Reader` protocol (`catalog/read.py:23`) that the store implements, so SQL is only the adapter. Against the
grain:
- core → factors (`core/rig.py:5`), so core isn't the bottom layer; `core/settings.py:5` pulls in psycopg.
- catalog → identity (`catalog/model.py:13`) imports only `sees`, but drags argon2 into the domain layer (see
  "Slow import").
- `api/world.py:78` builds `Rows(bench.conn)` itself instead of going through `Bench`.

### Good
- Tests run on real Postgres: each test gets a copy of a migrated (or migrated and curated) template, made ahead on
  threads (`src/chatddx/conftest.py:117`). Fakes are used only for pure-logic packages.
- Every SQL query is parametrized. The only f-strings in SQL insert fixed column-list constants (`store/people.py:18`,
  `store/catalog.py` `_THREAD`/`_EDIT`), and `store/store.py` types its queries as `LiteralString`.
- No hardcoded secrets: the database is peer auth over a Unix socket, and an endpoint's `credential` names an
  environment variable (`runner/gate.py:51`).
- No docstrings in `src`.
- The privacy design is visible in code:
  - a run item stores only the vignette's fingerprint (`ledger/run.py:98`);
  - request options that would echo the prompt back are refused (`factors/request.py:76`);
  - tools are blocked on sensitive sources (`runner/gate.py:39`);
  - nothing logs vignettes.
- API security that holds:
  - every route needs a session, and tests check that each read without one is refused;
  - tokens are 32 random bytes, stored only as SHA-256, expire after 12 h, with the expiry checked in SQL;
  - the cookie is `__Host-`, `Secure`, `HttpOnly`, `SameSite=Lax`;
  - cookie-authenticated unsafe requests are checked with Fetch Metadata, falling back to `Origin`
    (`api/people.py:43`);
  - argon2 verifies unknown logins against a dummy hash, so they take as long as wrong passwords, and rehashes on
    login.
- The draft → solidify → document rhythm shows in the history and works.

### Weaker
- **Overloaded modules.** `factors/request.py` is 1,037 lines and imported by 22 modules in 9 packages. It mixes
  component schemas, translation, compiling (`compile_request`, 127 lines, :826), rendering and response parsing
  (`tool_calls`/`next_request`, :1001); it's the best candidate for splitting.
- **Facades three deep.** Catalog functions are wrapped by `store.Catalog` (36 methods, mostly one-line
  pass-throughs, `store/catalog.py:355-410`), which is wrapped by `Bench` (55 methods, `bench/view.py:124`), which
  api and repl use.
- **`plan_factors`** (`curation/plan.py:236`) is 175 lines of nested closures. It checks user TOML with `assert`
  (:274, :286, :376) and an unchecked `cast` (:206): bad input gives an AssertionError or AttributeError without a
  file location, and the asserts vanish under `python -O`.
- **Slow import.** `identity/identity.py:49` computes an argon2 hash at import (135–214 ms measured), and every
  process that touches the catalog pays it. `cli.py:7-35` eagerly imports FastAPI, uvicorn, fake_vllm and the repl;
  `import chatddx.cli` takes 0.85 s.
- **Small real duplication:**
  - a `_message` helper at `scorers/answer.py:60` and `factors/request.py:993`, and inline at `repl/render.py:137`;
  - the reasoning/reasoning_content handling at `runner/send.py:51` and `repl/render.py:142`;
  - `bench/view.py:680-706` repeats `runner/run.py:276-296` (fetch, prepare, render), so either can drift.
- **Comments that act as docstrings.** 167 of the 254 comment blocks outside tests sit directly above a function or
  class (bench 43, repl 22, factors 17, runner 16), and many restate the code, against AGENTS.md "Docs":
  `inventory/world.py:12`, `bench/view.py:603`, `api/people.py:82`, `curation/plan.py:217`, `store/catalog.py:332-334`.
  Others carry a real why (`fake_vllm/served.py:26`, `runner/wire.py:65`).
- **Comments that reference docs or plans**, against AGENTS.md: `api/app.py:15`, `api/families.py:71`,
  `repl/test/test_vocabulary.py:15`, and `src/chatddx/conftest.py:28` (the marker split, arguably a fair link).

### Duplication that is healthy
- `catalog/` vs `store/catalog.py`: domain vs SQL adapter.
- Scoring is split by job: `factors/scoring` (schemas), `scorers/` (metric functions), `ledger/score` (records and
  checks), `runner/score` (orchestration), `repl/scoring` (UI).
- `api/world.py` (endpoint, model and component routes) vs `inventory/world.py` (the `World` loader): a name clash
  only.
- `catalog/test/memory.py` and `inventory/test/memory.py` are fine fakes, but nothing checks that the in-memory
  `Memory` behaves like the SQL `Rows`, so the fake can drift. Test constants (`QWEN`, `FREE_TEXT`, `PLAN`) are copied
  across the bench, repl, runner and api tests; minor.

### Hotspots
- History is short and mostly docs: `docs/factors.md` changed in 18 commits. The most-changed source files are
  `cli.py` (13) and `store/catalog.py` (9).
- Largest modules: `factors/request.py` (1,037), `bench/view.py` (708), `fake_vllm/chat.py` (609),
  `store/catalog.py` (536).
- Longest functions: `cli.main` (234 lines, all argparse), `plan_factors` (175), `compile_request` (127), `send` (93),
  `check_run` (89).

### Tests
- Test-to-code line ratios: runner 1.42, store 1.33, scorers 1.29, curation 1.03, api 0.83, ledger 0.83, factors 0.64,
  catalog 0.60, facts 0.58. core (68 lines) has no tests of its own but is exercised indirectly.
- identity has 1 test in its own package and 7 more in `store/test/test_identity.py`.
- ledger has only 12 test functions, but all 18 of its finding codes appear in tests; so do all of the facts' lint
  codes.
- `src/chatddx/conftest.py:28` refuses a test that isn't exactly one of `solidified` or `wip`. `slow` marks 54 tests,
  mostly repl (33) and curation (11). A few unmarked calls sit at 0.21 s, on the 0.2 s line.

## 2. How's it going

- Pace: 1–8k lines per commit. 10 of 12 PRs merged within 5 minutes of opening.
- No CI: there is no `.github/`. Tests, types and lint only run when someone runs them.

### Docs drift (at 950c70a)
Most of what the API docs name exists with the documented shape: the signatures quoted in the docs match the code, and
every finding code listed in factors-api, ledger-api and facts-api exists. What's left:
- Code with no doc, covered only by agents/wip-*.md (their tests are all `wip`, which is consistent): runner (1,144
  lines), repl (1,938), bench (837), api (578), scorers (455), tools (56), identity (95). `importers/o11n.py` (335)
  has prose and codes in `docs/inventory.md` but no API doc, though its tests are `solidified`.
- Codes documented nowhere: `case.unreadable` (`runner/run.py:289`), only in wip-runner.
- CLI commands documented nowhere in docs/: `chatddx api`, `chatddx person add` / `person password`.
- README:
  - every command and flag it uses exists (`cli.py`: `migrate`, `init-data --giftbag --world`, `fake-engines`,
    `repl --world`, `import-engine --factors --endpoints`), and the test markers exist;
  - `worlds/sample/inventory.toml` declares both fake endpoints itself (ports 12099/12100 as README says); it has no
    `endpoints.toml`, by design;
  - it leaves out `person`, `repair-data`, `wipe-data`, `api` and `fake-vllm`;
  - its commands without `--world` rely on `CHATDDX_WORLD=worlds/sample`, a relative path, so they work only from the
    repository's root.
- `AGENTS.md:47` opens a quote with `"` and closes it with a backtick (`` "Humans write, agents propose` ``), so a stray
  backtick renders.
- Not a finding: the links to `docs/identity.md` from chatddx.md, factors.md, store.md, store-api.md, catalog.md and
  catalog-api.md are deliberate; they constrain the planned doc, drafted in `agents/wip-identity.md`.
- Checked and fine: inventory-api and ledger-api fully (classes, fields, signatures, codes, schema tables); factors-api
  and catalog-api mostly; every symbol and code `docs/chatddx.md` cites; every `src/…:Symbol` reference in docs/;
  `docs/curation.md`'s "11 of the 24" slow tests.

### Plans drift
- Contradictions:
  - `agents/wip-runner.md:43` says Kompismoln has no `[cleared]` table; it has (`worlds/kompismoln/inventory.toml:15`,
    as `agents/wip-clearance.md:18-20` says).
  - How runs are served: API A6/A7 and phase 4 (`agents/wip-api.md:287-302`, :445) stream in the request or answer
    201 when finished; worker K5 (`agents/wip-worker.md:139-145`) wants `POST /api/runs` to answer 202 and queue.
    `agents/wip-api.md:301` notes it but the plan still says W1, and worker E2 (no deltas) undercuts A6's "events
    stay the same".
  - The docs state the crossed-trials Batch as adopted (`docs/factors.md:516-526`, `docs/catalog.md:75-77`, :212,
    `docs/chatddx.md:44`), the code has no `batch` kind, and `agents/wip-batch.md:101-102` and
    `agents/wip-objects.md:51` still call it proposed. P2 (several endpoints) is still open in
    `agents/wip-batch.md:105-108`, though the docs say "at one endpoint".
  - "batch" means one trial in the repl and crossed trials in the docs.
  - `agents/wip-repl.md:489` says endpoints with a credential are refused; `runner/gate.py:52-61` reads the secret
    from the environment variable the credential names.
- Stale references:
  - Plans point at the docs' and AGENTS.md's "Proposed amendments", which none has since 950c70a:
    `agents/wip-batch.md:139`, `agents/wip-objects.md:83`, `agents/wip-portal.md:224`, `agents/wip-repl.md:29-30`,
    :84, :475-476, :500, `agents/wip-runner.md:230`, :258, `agents/wip-sample-data.md:61`, :252, :281, :522.
  - wip-repl: "at 249548a" (:4); "what it is waits on wip-bench" (:19), though B3 is decided; a section "What the
    bench is now" (:317) that doesn't exist; `conftest.py:seeded` (:365).
  - wip-runner: `Reads` and `store/reads.py` (:235-236), both gone.
  - wip-api: `.env-example` (:189, :577), now `.env-container`; `conftest.py:seeded` (:452), now `curated`.
  - wip-bench: `seeded` (:434); "615 lines" (:198), but `bench/view.py` is 708.
  - wip-sample-data: "What's left, in order" (:16-19) lists only finished items; "After parity" (:101-103) treats the
    runner as unbuilt.
- Out of step: `fake_vllm/test/test_fake_engines.py` is `wip` and belongs to no wip plan, though `docs/vllm.md`
  documents `chatddx fake-engines` since 950c70a.

## 3. What's ahead

Done: factors, ledger, catalog, store, inventory, facts, curation are solidified. Built and awaiting solidify: runner,
repl, identity, bench phase 2, API phases 0–2.

Not started: batch, worker, portal, variants, the real clearance pipeline, and authoring writes. Authoring writes have
no plan at all (`agents/wip-bench.md:22-37`) though portal phases 4–5 and swift depend on them.

The research output itself is barely started: `scorers/aggregate.py` is 27 lines of mean/std; judges, canary drift and
export don't exist yet. Everything so far is rig.

### Each plan
All 13 were last touched 2026-10-09/10.
- **wip-api**: a FastAPI edge over the bench. Phases 0–2 built (sign-in, `/me`, reads of threads, families, the
  vignette, endpoints, models, components: `api/threads.py:43-79`, `api/families.py:42-89`, `api/world.py`); 20 wip
  tests. Next is phase 3 (variation, forks, edits, :23-24); runs and scores (phases 4–5) aren't built. A4–A8 and
  A10–A12 are still takes, though A4, A10 and A12 are built (:22). Open: login rate limiting, proxy buffering,
  `Bench.runs` paging, a connection pool, concurrent saves (:544-550, :563-574). Depends on: bench, the runner's
  `halt` (done), worker K5.
- **wip-batch**: crossing variations × cases into trials (`crossed`, `Bench.plan`, a `batch` kind). Not started: no
  `bench/plan.py`, `factors/batch.py`, or `batch` in `KINDS`/`THREAD_KINDS`; 0 tests. Pending: P2, P3 (a question
  for the user on mixed languages), P4, a trial-count limit, seeds, order, a batch sample (:104-117, :143-147).
  Depends on: objects, worker (step 6), portal, variants (P3).
- **wip-bench**: the person-scoped view (B3). Phase 2 steps 1–11 done; 19 wip tests. Step 12 (Z1) waits for the
  portal (:487-489). Authoring writes (chunks, appendices, expectations, cases/families) are "not planned yet"
  (:22-37). Depends on: identity (Z1), portal.
- **wip-clearance**: the sensitive-source hard block. The interim `[cleared]` table and the gate are built
  (`runner/gate.py`); the real pipeline (a `clearance` schema, grants) isn't. Open 1–6: what a grant keys on, where
  vetting is declared, who grants, sources, edges as destinations (:75-104). Next needed for tools on sensitive
  sources, judges and the first real source (:116-123).
- **wip-identity**: people, roles, sessions, Z1. All built, awaiting solidify; 1 wip test plus the store's. Pending:
  Z1, who may administer people, scheduled `purge_sessions` (only caller `store/test/test_identity.py:60`), rate
  limiting (:89-98).
- **wip-objects**: the factor/object split. `factors/kinds.py:KINDS` is built (:26, `test_factors.py:152`); the split
  itself is deferred until forced. Pending: the name (a question for the user, A/B), `kind` as a class keyword, where
  `refuse_change` lives (:210-215).
- **wip-portal**: server-rendered HTML with Svelte islands, plus swift. Not started: no `portal/`; only `jinja2`,
  `python-multipart` and the `Lax` cookie are in. Pending: one process or two, where the island build lives, an
  endpoint-Test page, export, and swift's questions (a family per typed case, a guest, a configuration filter)
  (:235-237, :257-263). Depends on: API phases 3–5, worker, batch, the bench's authoring writes, Z1, clearance.
- **wip-repl**: the shell. 4a–4c built; 79 wip tests. Outstanding: the cross-check against the old manual and a
  proposed `docs/repl.md`; the D5–D8 takes and the build-time takes await the user (:9-27).
- **wip-repl-manual**: the old `docs/repl.md`, kept verbatim as input to that cross-check, deliberately stale.
- **wip-runner**: sending trials to engines. Phases 0–6, the scoring pass and `halt` done, awaiting solidify; 54 wip
  tests, plus 31 scorers/tools tests. Pending: a round stopped mid-tools is lost from the log (:214-218); tool
  timeouts; an unversioned tool interface; no seeded canary set; a halted call waits for its next chunk (:245-248).
- **wip-sample-data**: parity with the old `init-data`. Parity reached, the real engines imported. Sample runs (fake
  `--script`, `src/chatddx/samples`, a `sampled` fixture) aren't built (:302-355). Pending: a judge prompt that needs
  Olof (:524-532); whether the targets get revised from the notes.
- **wip-variants**: recording variants instead of parsing names. Not started; take B. 3 questions for the user
  (:61-68). Batch P3, the API's "Open" and picking a variant by language depend on it.
- **wip-worker**: runs that outlive a request. Not started, and its step 0 is missing: no `resume`, and `Bench.start`
  passes no execution (`bench/view.py:532-540`, though `runner/run.py:111-118` accepts one). Pending: K1, K3, K4, K5;
  the repl's runs not counting against `max_jobs`; fairness; lost runs; deployment (:175-182).

### Ordering
- Unblocked now: API phase 3, batch steps 1–2 (pure functions), worker step 0, sample runs (the fake stays a leaf),
  portal phases 0–1.
- Blocked: API phase 4 on worker K5; worker steps 1–3 on its K-takes; portal phases 3 and 6 on worker and batch;
  portal phases 4–5 on the bench's unplanned authoring writes; judges on Olof and clearance.

Natural next steps:
1. API phase 3: variation, forks, edits.
2. Decide worker K5 before API phase 4, so the run endpoint isn't built twice.
3. Worker step 0: `resume`, and `Bench.start` passing an execution.
4. Batch: `crossed`, `Bench.plan`, the `batch` kind; the docs already describe it.
5. Sample runs, to feed the API and portal tests.
6. A solidify pass on runner, repl, bench, identity.

### Decisions waiting on humans
The main thing gating progress:
- Worker K5 (`agents/wip-worker.md:139-145`): 202-and-queue vs stream-in-request.
- Variants: 3 questions (`agents/wip-variants.md:61-68`).
- Batch P2/P3: several endpoints, mixed languages (`agents/wip-batch.md:104-117`).
- Objects: the name, A or B (`agents/wip-objects.md:210-215`).
- Clearance Open 1–6 (`agents/wip-clearance.md:75-104`).
- LLM judges: the judge prompt needs Olof (`agents/wip-sample-data.md:524-532`).
- Canary drift (a)/(b)/(c) (`docs/chatddx.md:281`).
- Portal: one process or two, the island build, swift's questions (`agents/wip-portal.md:235-237`, :257-263).
- Takes built but not ratified: API A4/A10/A12 (`agents/wip-api.md:22`), repl D5–D8 (`agents/wip-repl.md:9-27`).

### Risky or under-specified
- Authoring writes have no plan, yet portal phases 4–5 and swift depend on them.
- Swift will store typed real-patient text in the database on the public web, with no rate limiting or quotas built.
- Stopping runs: a halted call can wait on a stalled stream (`runner/wire.py`'s `Stream` can't be shut down), and tool
  calls to third parties can go unlogged after a stop. Both matter for halting on a client's disconnect and for the
  worker's stop.
- The worker's design: a mutable `worker` schema, `NOTIFY`'s 8 KB payload limit, `max_jobs` across runs (the repl's
  included).
- Test databases race; `_settled` waits only 5 s (`agents/wip-api.md:537-542`). Three quick runs here were stable.
- Variants still rest on parsing names, so a person's `draft (sv)` would count as a variant, which blocks picking by
  language for mixed batches.

## 4. Before real patient data

1. Rejected engine bodies are stored verbatim: on a non-2xx, `runner/send.py:128` records `e.body` (parsed in
   `runner/wire.py:91`), and only `prompt_token_ids` is stripped (`ledger/call.py:47`). An engine that echoes input in
   a validation error would put vignette text in the store. Not verified against real vLLM.
2. `GET /api/components/{digest}` skips the `shows()` check every other read has (`api/world.py:76`). Appendices are
   clinical text (`factors/cases.py:28`), and digests can be found by following references. Deliberate (B3), worth
   revisiting.
3. The vignette endpoint (`api/families.py:72`) sends no `Cache-Control: no-store`.
4. Session hardening: a password change doesn't end sessions (`store/people.py:87`); logins aren't rate-limited
   (`agents/wip-api.md:550`); `purge_sessions` (`store/people.py:143`) is never called outside tests; `Role`
   (`identity/identity.py:17`) is stored but nothing checks it.
5. Fingerprints are unkeyed SHA-256: the runner never passes a key (`runner/rounds.py:147`, `runner/run.py:242`), so
   anyone who can read the database and holds a candidate vignette can confirm a match. Known
   (`docs/chatddx.md:167`).
6. Applied migrations aren't checksummed (`store/migrate.py:27`), and history shows migration files modified in place
   18 times and deleted 18 times. A database migrated earlier would silently differ from the files; freeze them before
   any shared database.
7. Smaller: `/api/docs` is public, and each request opens its own database connection with no pool (`api/state.py:27`).

## Surprises

- The full suite took 63 s in the container, against "~50 s" in AGENTS.md; the quick run stays under 30 s.
- 12 leftover `claude/*` branches on origin look like pre-squash snapshots of merged work. Since 676d91c nothing in
  docs/, agents/, AGENTS.md or README cites a commit only they hold, so they can go.
- `CHATDDX_REVISION` is read in `core/rig.py:14`, bypassing `chatddx.core.settings`.
- `worlds/sample/inventory.toml:1` cites `src/chatddx/data/sample/cases.toml`, now `cases-en.toml`/`cases-sv.toml`.

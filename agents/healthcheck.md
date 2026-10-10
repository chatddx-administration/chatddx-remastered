# Healthcheck at 657716a

Taken 2026-10-10. A snapshot, not a plan: re-take it rather than update it.

Verdict: healthy. A young (12 days, 27 commits), disciplined codebase, green across the board. The risks are process
(no CI, near-zero review latency at thousands of lines a day) and a few privacy edges to close before real patient data.

## 1. The general vibe

| Check | Result |
|---|---|
| `pytest` | 501 passed, 63 s (AGENTS.md says ~50 s) |
| `pytest -m 'not slow'` | 447 passed, 25 s; 3 reruns stable |
| basedpyright | 0 errors, 0 warnings |
| ruff check / format | clean |
| Suppressions | 0 TODO/FIXME, 0 `type: ignore`, 2 `pyright: ignore` + 1 `noqa`, all justified |
| README walkthrough | works end to end: migrate → init-data → fake-engines → repl `run DutchFall10w`, scored and recorded |
| `chatddx api` | boots, 14 routes (session + reads), 401 without a session |
| Size | ~14.7k src lines, ~12.5k test lines, 16 docs, 13 wip plans |
| Solidified vs wip tests | 246 / 255: half the codebase is still draft |

Good:
- No import cycles; packages layer cleanly (factors/identity → ledger/catalog/inventory/facts → store/scorers →
  runner/curation → bench → api/repl → cli). Catalog domain sits behind a `Reader` protocol
  (`src/chatddx/catalog/read.py:23`), SQL is the adapter.
- Tests run on real Postgres, each test on a copy of a template database (`src/chatddx/conftest.py:117`).
- Every SQL query is parametrized.
- The privacy design is visible in code: fingerprints instead of text (`src/chatddx/ledger/run.py:98`), the clearance
  gate (`src/chatddx/runner/gate.py`), prompt-echoing request options refused (`src/chatddx/factors/request.py:76`).
- The draft → solidify → document rhythm shows in the history and works.

Weaker:
- Overloaded modules: `src/chatddx/factors/request.py` (1,037 lines, imported by 22 modules); `Bench` (55 methods,
  `src/chatddx/bench/view.py:124`) over `store.Catalog` (36 mostly one-line pass-throughs,
  `src/chatddx/store/catalog.py:355-410`); `api/world.py:78` goes around `Bench` to `Rows`.
- `plan_factors` (`src/chatddx/curation/plan.py:236`) is 175 lines with nested closures and validates user TOML with
  `assert` (:274, :286, :376): bad input gives an AssertionError without a location, and nothing under `python -O`.
- Small real duplication: `src/chatddx/bench/view.py:680-706` repeats `src/chatddx/runner/run.py:276-296`; a
  `_message` helper exists three times (`scorers/answer.py:60`, `factors/request.py:993`, inline in
  `repl/render.py:137`).
- 167 comment blocks sit above functions acting as docstrings, many restating the code, against AGENTS.md "Docs".
- `src/chatddx/identity/identity.py:49` computes an argon2 hash at import (~135 ms); with eager imports in `cli.py`,
  `import chatddx.cli` takes ~0.85 s.

## 2. How's it going

- Pace: 1–8k lines per commit. 10 of 12 PRs merged within 5 minutes of opening.
- No CI: there is no `.github/`. Tests, types and lint only run when someone runs them.
- Docs drift is low and recent:
  - `docs/identity.md` is linked from 10 places (chatddx.md:19, factors.md:16/46, store.md:5/34, catalog.md:14/144,
    catalog-api.md:56, store-api.md:12/119) but doesn't exist; only `agents/wip-identity.md` does.
  - `docs/store-api.md` is behind HEAD: `create_database`/`drop_database` now take `admin` first
    (`src/chatddx/conftest.py:92`, :104); fixtures `copies`, `curated`, `template`, `autocommit` are missing; the
    migration table stops at 0012; the tier-0 list (:170) omits 0013.
  - Dead pointers to proposals since accepted or dropped: `docs/catalog-api.md:740`, `docs/factors-api.md:933`,
    `docs/ledger-api.md:563`, `docs/curation.md:77` and :119.
  - "As of" baselines in catalog-api, factors-api, facts-api, store-api and inventory-api name commits that were
    squashed away; only ledger-api's 401b696 exists.
  - `docs/vllm.md` holds 7 proposals (from :384), all already implemented: they await a human yes.
- Plans drift more than docs:
  - `agents/wip-runner.md:43` says Kompismoln has no `[cleared]` table; it has (`worlds/kompismoln/inventory.toml:15`).
  - The docs state the crossed-trials Batch as adopted (`docs/factors.md:516-526`, `docs/catalog.md:75-77`), the code
    has no `batch` kind, and `agents/wip-batch.md` still calls it proposed.
  - "batch" means one trial in the repl and crossed trials in the docs.
  - Stale references: `.env-example` and `conftest.py:seeded` in wip-api and wip-bench; `Reads`/`store/reads.py` in
    wip-runner; a nonexistent commit d10c96d in wip-identity; "What's left, in order" in wip-sample-data lists only
    finished items.

## 3. What's ahead

Done: factors, ledger, catalog, store, inventory, facts, curation are solidified. Built and awaiting solidify: runner,
repl, identity, bench phase 2, API phases 0–2.

Not started: batch, worker, portal, variants, the real clearance pipeline, and authoring writes. Authoring writes have
no plan at all (`agents/wip-bench.md:22-37`) though portal phases 4–5 depend on them.

Natural next steps:
1. API phase 3: variation, forks, edits.
2. Worker step 0: `resume`, and `Bench.start` passing an execution (`src/chatddx/bench/view.py:532-540`; the runner
   already accepts one, `src/chatddx/runner/run.py:111-118`).
3. Batch: `crossed`, `Bench.plan`, the `batch` kind.
4. Sample runs, to feed API and portal tests.
5. A solidify pass on runner, repl, bench, identity.

Decisions waiting on humans, the main thing gating progress:
- Worker K5 (`agents/wip-worker.md:139-145`): 202-and-queue vs stream-in-request, before API phase 4, or the run
  endpoint gets built twice (`agents/wip-api.md:287-302`).
- Variants: 3 questions (`agents/wip-variants.md:61-68`); batch P3 and choosing by language depend on them.
- Batch P2/P3: several endpoints, mixed languages (`agents/wip-batch.md:104-117`).
- Clearance Open 1–6 (`agents/wip-clearance.md:75-104`): what a grant keys on, who grants, edges as destinations.
- LLM judges: the judge prompt needs Olof (`agents/wip-sample-data.md:524-532`).
- Canary drift (a)/(b)/(c) (`docs/chatddx.md:280`).
- Takes built but not ratified: API A4/A10/A12 (`agents/wip-api.md:22`), repl D5–D8 (`agents/wip-repl.md:9-27`).

The research output itself is barely started: `src/chatddx/scorers/aggregate.py` is 27 lines of mean/std; judges,
canary drift and export don't exist yet. Everything so far is rig.

## Before real patient data

1. Rejected engine bodies are stored verbatim: on a non-2xx, `src/chatddx/runner/send.py:128` records `e.body`, and
   only `prompt_token_ids` is stripped (`src/chatddx/ledger/call.py:47`). An engine that echoes input in a validation
   error would put vignette text in the store. Not verified against real vLLM.
2. `GET /api/components/{digest}` skips the `shows()` check every other read has (`src/chatddx/api/world.py:76`).
   Appendices are clinical text. Deliberate (B3), worth revisiting.
3. The vignette endpoint (`src/chatddx/api/families.py:72`) sends no `Cache-Control: no-store`.
4. Session hardening: a password change doesn't revoke sessions (`src/chatddx/store/people.py:87`); no login rate
   limiting; `purge_sessions` is never scheduled (`src/chatddx/store/people.py:143`); `Role` is stored but unchecked.
5. Fingerprints are unkeyed SHA-256 (`src/chatddx/runner/rounds.py:147`); known (`docs/chatddx.md:167`).
6. Applied migrations aren't checksummed (`src/chatddx/store/migrate.py:27`). Migration files were edited in place
   often in history; fine now, but freeze them before any shared database.
7. A halted call can wait forever on a stalled stream (`agents/wip-runner.md:245-248`).

## Surprises

- The full suite took 63 s in the container, against "~50 s" in AGENTS.md; the quick run stays under 30 s.
- 12 leftover `claude/*` branches on origin look like pre-squash snapshots of merged work; glance before deleting.
- `CHATDDX_REVISION` is read in `src/chatddx/core/rig.py:14`, bypassing `chatddx.core.settings`.
- `docs/chatddx.md:290` has "The agent's take is (c)" inside the human-written body.
- `worlds/sample/inventory.toml:1` cites `src/chatddx/data/sample/cases.toml`, now `cases-en.toml`/`cases-sv.toml`.
- Comments referencing docs or plans, against AGENTS.md: `src/chatddx/api/app.py:15`, `src/chatddx/api/families.py:71`,
  `src/chatddx/repl/test/test_vocabulary.py:15`.

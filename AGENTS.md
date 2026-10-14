# Agent instructions
This document contains project-wide instructions written by humans for agents.

## Environment
* `set -a; . ./.env-container; set +a`.
* `store` uses PostgreSQL 16:
  - pg_ident.conf: chatddx <os-user> chatddx / chatddx <os-user> chatddx_writer
  - pg_hba.conf:   local all all peer map=chatddx
  - Setup database and roles with `src/chatddx/store/setup.sql`
* Base the fake vLLM on 0.24.0, extend/amend continuously as new facts are discovered, questions arise or sample data is needed.
* `chatddx.core.settings` is the project-wide source of truth.

## Typechecking
* Errors and warnings that indicate issues beyond the scope of the current task should remain, never hide them.
* `pnpm --dir frontend check` typechecks the frontend, and `pnpm --dir frontend build` builds it. After a change to
  the API, `chatddx openapi > frontend/openapi.json`.

## Testing
```
AGENT: replace
The baseline leaves out the tests that others verify, `slow` follows a budget instead of a per-call limit, and
pytest-xdist runs any of the runs on several workers.
---
* Baseline is `pytest -m 'not overlap'`, the deduplicated baseline (~115 s); `pytest` runs every test (~120 s), and
  `pytest -m 'not slow'` is the quick run (~22 s). `-n 4` (pytest-xdist) runs the baseline in ~62 s and every test in
  ~70 s; the quick run gains nothing from it. Time a run serially to compare it with another.
* `@pytest.mark.overlap(...)` marks a test whose assertions the tests it names make too; it names them by node id
  under src/chatddx/, or `::name` in its own file. src/chatddx/conftest.py refuses a name that is no test or is an
  overlap itself.
* `@pytest.mark.slow` marks the slowest tests, together ~7/8 of the full run, and the tests that would have the quick
  run make a template only they use (`loaded`, `ran`, `sampled`). `pytest -p chatddx.test.budget`, run serially,
  says which tests to mark or unmark, and which templates a run made.
```
* Baseline is `pytest` which runs every test and takes ~60s; `pytest -m 'not slow'` is the quick run, <30s.
  A test whose call takes 0.2s or more is marked `@pytest.mark.slow` (pyproject.toml, `[tool.pytest]`).
```
AGENT: remove
No mark holds drafts apart any more; a draft's tests are run by their path, e.g. `pytest src/chatddx/portal`.
```
* Drafts are targeted with `pytest -m 'wip'` and excluded with `pytest -m 'not wip'`, see Staging.
* `pnpm --dir frontend test` runs the frontend's unit tests (vitest), each beside the module it tests.

## Staging
```
AGENT: replace
The wip and solidified marks are gone.
---
A module is either wip or solidified.
```
A module is either wip or solidified and are held apart with a pytest mark.
* wip (draft) modules are documented in `agents/wip-<module>.md`
* solidified modules are documented in `docs/<module>*.md`, where the chatddx rule one of documentation applies.

## Docs
All docs except `agents/*` are governed by chatddx rule one of documentation: Humans write, agents suggest.

* A suggestion is inserted as a fenced code-block immediately above the subject to change.
  The backticks are part of the template, use 4 backticks as envelope if the suggestion contains a code-block.
  Prefer whole lines for new content.
```
AGENT: <verb>
<short explanation>
---
<optional suggestion for new content>
```

* Docs refer to the code, the code speaks for itself. ALWAYS remove docstrings/comments that reference docs or explain
  what the code does before committing.

* Important details that can't be learned by reading the code+tests may have a comment if, and only if, it is relevant
  only to the line/section of code that follows and nothing else.

* If a section of code is related to another section of code elsewhere such that reading both make them easier to
  understand, a path in a comment can act as a link for agents and humans alike. A comment linking two or more pieces of
  code this way with a short explanation is allowed.

* Docs in `agents/*` can be created, removed and edited freely.

* Don't reference branch commits, they'll be squashed.

## Misc
* For placeholder usernames in docs and tests, use
  1. alice, bob, carol...
  2. semantic names (archive, guest, nobody, other, collaborator-one, admin).

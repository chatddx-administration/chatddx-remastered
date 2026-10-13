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
* Baseline is `pytest` which runs every test and takes ~60s; `pytest -m 'not slow'` is the quick run, <30s.
  A test whose call takes 0.2s or more is marked `@pytest.mark.slow` (pyproject.toml, `[tool.pytest]`).
* Drafts are targeted with `pytest -m 'wip'` and excluded with `pytest -m 'not wip'`, see Staging.

```
AGENT: add
A line at the end of "Testing", for the frontend's unit tests (agents/wip-portal.md, phase 3).
---
* `pnpm --dir frontend test` runs the frontend's unit tests (vitest), each beside the module it tests.
```
## Staging
A module is either wip or solidified and are held apart with a pytest mark.
* wip (draft) modules are documented in `agents/wip-<module>.md`
* solidified modules are documented in `docs/<module>*.md`, where the chatddx rule one of documentation applies.

## Docs
All docs except `agents/*` are governed by chatddx rule one of documentation: Humans write, agents suggest.

* A suggestion is inserted as a fenced code-block immediately above the subject to change.
  The backticks are part of the template, use 4 backticks as envelope if the suggestion contains a code-block.
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

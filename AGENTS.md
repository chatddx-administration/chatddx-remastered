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

## Testing
* Baseline is `pytest` which runs every test and takes ~50s; `pytest -m 'not slow'` is the quick run, <30s.
  A test whose call takes 0.2 s or more is marked `@pytest.mark.slow` (pyproject.toml, `[tool.pytest]`).

## Docs
All docs except `agents/*` are governed by the rule "Humans write, agents suggest."

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

* `agents/*` are exempt from the "Humans write, agents suggest" rule and agents are free to use it for whatever purpose
  they deem fit.

* Don't reference branch commits, they'll be squashed.

## Misc
* For placeholder usernames in docs and tests, use
  1. alice, bob, carol...
  2. semantic names (archive, guest, nobody, other, collaborator-one, admin).

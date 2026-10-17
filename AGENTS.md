# Agent instructions
This document contains project-wide instructions written by humans for agents.

## Environment
* `set -a; . ./.env-container; set +a`.
* `store` uses PostgreSQL 16:
  - pg_ident.conf: chatddx <os-user> chatddx / chatddx <os-user> chatddx_writer
  - pg_hba.conf:   local all all peer map=chatddx
  - Setup database and roles with `src/chatddx/store/setup.sql`
* Base the fake vLLM on 0.24.0, extend/amend continuously as new facts are discovered, questions arise or sample data is needed.
* `chatddx.settings` is the project-wide source of truth.

## Typechecking
* Errors and warnings that indicate issues beyond the scope of the current task should remain, never hide them.
* `pnpm --dir frontend check` typechecks the frontend, and `pnpm --dir frontend build` builds it. After a change to
  the API, `chatddx openapi > frontend/openapi.json`.

## Testing
* Baseline is `pytest` which runs every test and takes \~110 s; `pytest -m 'not slow'` is the quick run, \~22s.
  `-n 4` (pytest-xdist) runs the baseline in \~70s; the quick run gains nothing from it.
* `@pytest.mark.slow` marks the slowest tests, together \~7/8 of the full run, and the tests that would have the quick
  run make a template only they use (`loaded`, `ran`, `sampled`). `pytest -p chatddx.test.budget`, run serially,
  says which tests to mark or unmark, and which templates a run made.
* Names tests share (models, endpoints, the recipes most tests run, the cases) are spelled once, in
  `src/chatddx/test/world.py`; helpers one package's tests share stay in its `test/helpers.py`.
* A test matches a table's cells, not its padding, so that a longer name doesn't fail it.
* `pnpm --dir frontend test` runs the frontend's unit tests (vitest), each beside the module it tests.

## Staging
A module is either wip or solidified.
* wip (draft) modules are documented in `agents/wip-<module>.md`
* solidified modules are documented in `docs/<module>*.md`, where the chatddx rule one of documentation applies.

## Documentation rules

### 1. Humans write, agents suggest.
In all docs except `agents/*`, agents are only allowed to insert suggestions.

A suggestion is inserted as a fenced code-block immediately above the subject to change.
The backticks are part of the template, use 4 backticks as envelope if the suggestion contains a code-block.
Prefer whole lines for new content.
```
AGENT: <verb>
<short explanation>
---
<optional suggestion for new content>
```

### 2. Docs refer to the code, the code speaks for itself.
Before committing, remove docstrings and comments that:
- reference the docs
- tell what the code does

### 3. How to write comment.
1. Prefix with the comment's nature (e.g. "Patch"/"Compromise"/"Prototype"/"Accomodating for a discovered fact")
2. Tell what's non-evident and only what the code doesn't already tell.

```python
# Optimization: Reusing families' language reduces query-load.
def _languages_of(self, cases: Sequence[str]) -> dict[str, str | None]:
    known = {c: f.about.language for f in self.families() for c in f.cases}
    if rest := [c for c in cases if c not in known]:
        known |= languages_of(self.rows, rest)
    return {c: known[c] for c in cases}
```

3. Optional: Use links. If a section of code is related to another section of code elsewhere such that reading both make
   them easier to understand, insert links between them along with the comment.

```python
# Policy: De facto refusal mechanism for
# src/chatddx/runner/score.py:judge_at and src/chatddx/bench/seen.py:Seen.at
def serving(
    self,
    digest: str,
    serves: Callable[[str], str | None] | None = None,
    called: str | None = None,
) -> str:
    # ...
```

### 4. Don't reference branch commits
They'll be squashed.

### 5. Placeholder username
* For placeholder usernames in docs and tests, use
  1. alice, bob, carol...
  2. semantic names (archive, guest, nobody, other, collaborator-one, admin).

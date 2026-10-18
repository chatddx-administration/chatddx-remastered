# Agent instructions
This document contains project-wide instructions written by humans for agents.

## Environment
* `set -a; . ./.env-container; set +a`.
* `store` uses PostgreSQL 16:
  - pg_ident.conf: chatddx <os-user> chatddx / chatddx <os-user> chatddx_writer
  - pg_hba.conf: local all all peer map=chatddx
  - Setup database and roles with `src/chatddx/store/setup.sql`
* Base the fake vLLM on 0.24.0, extend/amend continuously as new facts are discovered, questions arise or sample data is needed.
* `chatddx.settings` is the project-wide source of truth.

## Typechecking
* Errors and warnings that indicate issues beyond the scope of the current task should remain, never hide them.
* `pnpm --dir frontend check` typechecks the frontend, and `pnpm --dir frontend build` builds it. After a change to
  the API, `chatddx openapi > frontend/openapi.json`.
* Before committing, `chatddx reference` brings `docs/reference/` up to date with the code: it tags what changed for
  a human to apply, and `--check` fails while a reference is behind.

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

## Development stages

1. Felt - Not mentioned anywhere but still present somehow
2. Implied - Shown to be specified indirectly when looking for it
3. Mentioned - Expressed as a concrete need
4. Named - `<thing>` now refers to it and can be grepped
5. Itemized - Referred to as an item in `docs/backlog.md`
6. Planned - Referred to as a plan in `agents/plan-<thing>.md`
7. Drafted - Exists as a moving target in code and `agents/wip-<thing>.md`
8. Solidified - Documented in `docs/<thing>.md` and less volatile as a consequence of doc's rule 1.

Steps 5-8, docs *move*: backlog -> plan -> wip -> doc, and is never explained in more than one doc at the time.

## Documentation rules

### 1. Humans write, agents suggest.
In all docs except `agents/*`, agents are only allowed to insert suggestions.
`docs/reference/*` is written by `chatddx reference` alone: it inserts a tag, `REFERENCE: ADD`, `REPLACE` or `REMOVE`
in the template below, above each change in the code's public names, and a human applies it.

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
The primary document is `docs/chatddx.md`: If a contradiction to it is discovered, stop and prompt a resolution.

Final module-scoped documentation is of shapes:
1. Authoritative spec (`docs/<module>.md`)
2. API Reference (`docs/reference/<module>.md`), written by `chatddx reference`
3. A user manual (`docs/<module>-manual`)

Wip module-scoped documentation is built up as a mirror of final at `agents/wip-<module>[-*].md`.

Other documents that doesn't fit in this scheme may occur but can be considered against the grain.

Before committing, remove all and any docstrings and comments that:
- reference the docs
- tell what the code does

The exception is a docstring on a public name in a package of `settings.REFERENCED`: its reference includes it.

### 3. When and how to write a comment.
- A) Every line of comment imposes a readability tax.
- B) A future reader can be saved work by knowing about non-evident details.
- When B is considerable enough to offset A, a comment is justified.

1. Prefix with the comment's nature (e.g. Patch, Compromise, Prototype, "Accommodating for a discovered fact")
2. Tell what's non-evident and only what the code doesn't already tell, example:

```python
# Optimization: Reusing families' language reduces query-load.
def _languages_of(self, cases: Sequence[str]) -> dict[str, str | None]:
    known = {c: f.about.language for f in self.families() for c in f.cases}
    if rest := [c for c in cases if c not in known]:
        known |= languages_of(self.rows, rest)
    return {c: known[c] for c in cases}
```

3. Optional: Use links. If a section of code is related to another section of code elsewhere such that reading both make
   them easier to understand, insert links between them along with the comment. Example:

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

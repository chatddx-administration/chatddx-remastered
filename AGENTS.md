# Agent instructions
This document contains project-wide instructions written by humans for agents.

## Environment
* `set -a; . ./.env-container; set +a`.
* `store` uses PostgreSQL 16:
  - pg_ident.conf: chatddx <os-user> chatddx / chatddx <os-user> chatddx_writer
  - pg_hba.conf: local all all peer map=chatddx
  - Setup database and roles with `src/chatddx/store/setup.sql`
* Base the fake vLLM on 0.24.0, extend/amend continuously as new facts are discovered, questions arise or sample data is needed.
* `pnpm --dir frontend build` builds frontend.
* `chatddx.settings` is the project-wide source of truth.

## Typechecking
* Errors and warnings that indicate issues beyond the scope of the current task should remain, never hide them.
* `pnpm --dir frontend check` typechecks frontend

## Testing
* Baseline is `pytest` which runs every test and takes ~110s; `pytest -m 'not slow'` is the quick run, ~22s.
  `-n 4` (pytest-xdist) runs the baseline in ~70s; the quick run gains nothing from it.
* Names tests share (models, endpoints, the recipes most tests run, the cases) are spelled once, in
  `src/chatddx/test/world.py`; shared helpers stay in `test/helpers.py`.
* A test matches a table's cells, not its padding, so that a longer name doesn't fail it.
* `pnpm --dir frontend test` tests frontend

## Committing
Before commit:
* Remove all docstrings and comments that don't pass doc rule 2 and 3 respectively.
* run `pytest -p chatddx.test.budget` without `-n 4`, instead of `pytest`, and mark/unmark slow tests accordingly.
* Typecheck and test frontend as normal.
* After a change to the API, run:
  - `chatddx openapi > frontend/openapi.json`
  - `chatddx reference`

## Development stages

A thing under development is in one of the following stages:
1. Felt - Not really anywhere but still present somehow
2. Implied - Seen only when looking for it
3. Mentioned - Expressed as a concrete need
4. Named - Greppable and referred to as `<thing>`
5. Itemized - Has one or more items in `docs/backlog.md`
6. Planned - Has a concept of a plan in `agents/plan-<thing>.md`
7. Drafted - Exists as a moving target in code and `agents/wip-<thing>.md`
8. Solidified - Dependable and documented in `docs/<thing>.md` and `docs/reference/<thing>.md`
9. Cemented - TBD
10. Protected - TBD

Things can bounce around freely across these stages but is only in one stage at once.
Docs are never edited and reworked in the same commit: Move verbatim, commit,
then edit or insert suggestions if permitted.

### Step 5 and above
docs *move*: backlog -> plan -> wip -> doc
A thing is never explained in more than one doc at a time.

### Step 8 and above
Guarded by rule 1 and `chatddx reference`

## Documentation rules

### 1. Humans write, agents suggest.
In all docs except `agents/*`, agents are only allowed to insert suggestions.
`docs/reference/*` is written by `chatddx reference` alone: it inserts a tag, `<settings.REFERENCE_TAG>: ADD`,
`REPLACE` or `REMOVE` in the template below, above each change in the code's public names, and a human applies it.

Verbatim moves as a consequence of a stage change ("Development stages") are allowed, the rules at the destination
applies afterwards.

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
The primary document is `docs/chatddx.md`: If a contradiction to it is discovered, stop,
describe the landscape and provide options.

- The module scoped documentation is in `docs/<module>.md`.
- The doc may refer to code `concepts` or direct file reference `src/chatddx/file.py:Class.prop`.
- References from code to docs are never allowed.

Docstrings in solidified modules' public members are allowed if they follow rule-3, in which case they'll be
reported by `chatddx reference` for sign-off. All other doctrings are forbidden.

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

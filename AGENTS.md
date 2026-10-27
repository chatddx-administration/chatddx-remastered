# Agent instructions

This document contains project-wide instructions for agents.

## Environment

- Hooks should have set you up or told you why they didn't, report friction, poor messaging and surprises.
- Project-wide settings are in `chatddx.settings`.
- Archeology is not allowed unless told otherwise, the environment given has all you need
- That pkill -f pattern might match your own shell

## Session

Hooks run `./dev/agent.sh` with `session-start`, `turn-start` and `turn-end`.

When asked to hand over:

1. In the files this session has touched, remove all comments and docstrings that don't pass "Comments" and
   "Docstrings", pre-existing included.
2. Run `./dev/agent.sh hand-over`. It commits, pushes and runs all checks.

All `./dev/agent.sh` commands are silent on success or print instructions for you to act on. All `./dev/agent.sh` exits
are 0 except `turn-end`, which exits 2 on failure.

## Handling errors and warnings

How to handle a warning or error, in order of preference:

### 0. Let them error

Consider not handling an error or warning if:

- it's out of scope of the current task
- its timing, fallout and message are already about right

### 1. Crash at boot

If it's a runtime error that could have been known at boot:

1. write a check that crashes it at boot
2. attach a "fix boot-check <boot-check>" message, should it occur at runtime

### 2. Raw writes to stderr

If it needs the attention of developers or operations:

- minimize tampering with the message
- maximize simplicity in handling

### 3. Tell the user

If it needs the attention of the user, consider that users should not be able to cause errors, and so the possibility
for error should be addressed rather than the error itself. If it's not a good time for that kind of endeavor, raise
`Whoops(message, pass_on)` and move on. Either way, tell the user, in `message`:

- what's going on
- what they can do now

and, if `Whoops`, put in `pass_on` what they are to pass on to developers and ops, as it is.

## Tests and checks

`./check.sh [stage]...` checks the stages named:

- `openapi`, `stamps` and `locale`, each in step with the code
- `pending`, what is left to stamp or translate
- `format`, `types`, `frontend`, `docs`, `tests` and `browser`.

`./write.sh [commit]` regenerates what follows from the code and the docs.

### Python

- `basedpyright` for typecheck
- `ruff check` for lint

- `pytest` runs every test but the browser tests ~220s.
- `pytest -m 'not slow'`, excludes the slowest tests making up 7/8 of the total test time, ~60s.
- `pytest -n 4` fast given absence of other loads, ~110s.

### TypeScript

- `pnpm --dir frontend check` type checks frontend
- `pnpm --dir frontend test` tests frontend takes less than 2s

### Formatting

- `ruff format` formats the Python.
- `frontend/node_modules/.bin/prettier --write .` formats the frontend and the docs, what `.prettierignore` lets
  through.

### Browser

- run `pnpm --dir frontend build` first if the frontend changed
- `pytest -m browser` runs the browser tests that `pytest` skips, in ~75s

### Nix

Agents aren't expected to run this, just know it exists.

`nix flake check` runs:

- `check.sh`'s openapi, stamps, types, tests, frontend, docs and format stages
- `nix/test.nix` boots the NixOS module in a VM for its test, takes ~7 minutes
- `nix/module-eval.nix`

### Docs

- `chatddx refcheck` checks for broken references including commits not in main.

## Development stages

`settings.STAGES` tracks things under development stages once they exist in `src/chatddx/`, the stages are:

1. Felt - Not really anywhere but still present somehow
2. Implied - Seen only when looking for it
3. Mentioned - Expressed as a concrete need
4. Named - Greppable and referred to as `<name>`
5. Itemized - Has one or more items in `docs/backlog.md`
6. Planned - Has a concept of a plan in `agents/plan-<name>.md`
7. Drafted - Exists as a moving target in `src/chatddx/<name>*` and `agents/wip-<name>.md`
8. Solidified - Its surface stamped, and its docs, if any, in `docs/modules/<name>.md`
9. Cemented: TBD
10. Protected: TBD

Things can move around freely across these stages but are only in one stage at a time, so docs are gathered and moved
rather than copied.

A move entails:

- gathering (project-wide deduplication)
- updating references
- its own commit

## Documentation

Destructive edits are allowed: `turn-end` stamps all changes with git conflict markers for a human to resolve.

The primary document is `docs/chatddx.md`: If a contradiction to it is discovered, stop, describe the landscape and
provide options.

## Comments

- A) Every line of comment imposes a readability tax.
- B) A future reader can be saved work by knowing about non-evident details.
- ⇒ When B is considerable enough to offset A, a comment is justified.

1. Prefix with the comment's nature
2. Tell what's non-evident and only what the code doesn't already tell

## Docstrings

Public names may have a docstring that describes their cost and utility. The cost is the resources it invokes, locks it
holds and complexity of its operations. The utility is derived from its responsibility without any assumptions about the
caller.

Docstrings are stamped along with signature and raises and the docstring should read as a direct continuation of these.

- A) Every line of docstring imposes a readability tax.
- B) Callers can dodge reading the source if the docstring gives them the right idea.
- ⇒ When B outweighs A, a docstring by that amount is justified.

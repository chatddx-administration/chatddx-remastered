# Agent instructions

This document contains project-wide instructions written by humans for agents.

## Environment

- `set -a; . ./.env-container; set +a`.
- `chatddx.settings` is the project-wide source of truth.
- `store` uses PostgreSQL 16:
  - pg_ident.conf: chatddx <os-user> chatddx / chatddx <os-user> chatddx_writer
  - pg_hba.conf: local all all peer map=chatddx
  - Setup database and roles with `src/chatddx/store/setup.sql`

- Base the fake vLLM on 0.24.0, extend/amend continuously as new facts are discovered.

- Archeology is not allowed unless said otherwise, the commit given has all you need.

## Workflow

The workflow is a session's: it starts from a human-reviewed commit and ends with a handover. What the session commits
in between is its own.

### 1. Before work starts

Run `scripts/check.sh baseline`: on non-zero exit, pause work and relay the flags.

### 2. Between units of work

No rules: use your own judgement and the tests and checks at your disposal (see "Tests and checks"). Commit and push as
you see fit, a session's hooks may ask for both at a turn's end, but neither is a handover.

### 3. Handing over

When asked for a handover or pull request:

1. Remove all comments and docstrings that don't pass "Comments" and "Docstrings" respectively (pre-existing included).
2. Run `scripts/check.sh`:
   - relay flags
   - flip what the budget suggests when it feels right
3. Commit, run `chatddx stamp docs` and commit what it writes, then push.

## Handling errors and warnings

How to handle a warning or error, in order of preference:

### 0. Ignore

Consider not handling an error or warning if:

- it's out of scope of the current task
- its timing, fallout and message are already about right

### 1. Crash at boot

If it's a runtime error that could have been known at boot:

1. write a check that crashes it at boot
2. attach a "fix boot-check <boot-check>" message, should it occur at runtime

### 2. Raw writes to stderr and/or edges

These are for developers and ops, so:

- minimize tampering with the message
- maximize simplicity in handling

### 3. Inform UX runtime

Users should not be able to cause errors, and so the possibility for error should be addressed rather than the error
itself. If it's not a good time for that kind of investigation, raise `Whoops(message, pass_on)` and move on. Either
way, tell the user, in `message`:

- what's going on
- what they can do now

and put in `pass_on` what they are to pass on to developers and ops, as it is.

## Tests and checks

Handover check tool is `scripts/check.sh`, capture stdout for budget output and flags to relay. It takes ~350s when diff
against `origin/main` hits all stages, mostly due to browser tests and the budget run.

### Python

- `basedpyright` for typecheck
- `ruff check` for lint

- `pytest` runs every test but the browser tests ~220s.
- `pytest -m 'not slow'`, excludes the slowest tests making up 7/8 of the total test time, ~60s.
- `pytest -n 4` fast given absence of other loads, ~110s.
- Names tests share (models, endpoints, the recipes most tests run, the cases) are spelled once, in
  `src/chatddx/test/world.py`.

### TypeScript

- `pnpm --dir frontend check` type checks frontend
- `pnpm --dir frontend test` tests frontend takes less than 2s

### Browser

- `CHATDDX_CHROMIUM=/opt/pw-browsers/chromium` is in your env and should be good.
- `pnpm --dir frontend install --frozen-lockfile` if `frontend/node_modules` is missing.
- `pnpm --dir frontend build` if not already built.
- `pytest -m browser` runs the browser tests that `pytest` skips, in ~75s

### Nix

Agents aren't expected to run this, just know it exists.

`nix flake check` runs:

- `scripts/check.sh`'s docs, package and frontend stages
- `nix/test.nix` boots the NixOS module in a VM for its test, takes ~7 minutes
- `nix/module-eval.nix`

### Docs

- `chatddx refcheck` checks for broken references and commits off main.

## Development stages

A thing under development is in one of the following stages:

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

Drafts and above are declared in `src/chatddx/settings.py:STAGES`, and `chatddx stamp check` fails on a module in
`src/chatddx/` without one. What `chatddx stamp` writes of a module from which stage on is
`src/chatddx/settings.py:STAMPED_FROM`.

Things can bounce around freely across these stages but are only in one stage at a time, which `chatddx stamp check`
checks of a module: an `agents/wip-<name>.md` past Drafted, or a `docs/modules/<name>.md` before Solidified, is a module
in two. A doc is moved in a commit of its own, and a move entails deduplication and updating references.

## Documentation

The handover's `chatddx stamp docs` inserts git conflict markers between the latest commit a human made and now, a human
needs to stamp these for next baseline to pass.

- The primary document is `docs/chatddx.md`: If a contradiction to it is discovered, stop, describe the landscape and
  provide options.
- Placeholder usernames in docs and tests are alice, bob, carol..., or semantic names (archive, guest, nobody, other,
  collaborator-one, admin).

## Comments

- A) Every line of comment imposes a readability tax.
- B) A future reader can be saved work by knowing about non-evident details.
- ∟ When B is considerable enough to offset A, a comment is justified.

1. Prefix with the comment's nature
2. Tell what's non-evident and only what the code doesn't already tell

## Docstrings

Public solidified entry points may have a docstring that describes their cost and utility. The cost is the resources it
invokes, locks it holds and complexity of its operations. The utility is derived from its responsibility without any
assumptions about the caller.

Docstrings are stamped along with signature, raises and findings and the docstring should read as a direct continuation
of these.

- A) Every line of docstring imposes a readability tax.
- B) Callers can dodge reading the source if the docstring gives them the right idea.
- ∟ When B outweighs A, a docstring by that amount is justified.

# Dev tools

## Check

`./check.sh [stage]...` checks the stages named, or all of them:

- `openapi`, `stamps` and `locale`, each in step with the code
- `pending` and `fuzzy`, what is left to stamp or review
- `format`, `types`, `frontend`, `docs`, `tests` and `browser`.

## Write

`./write.sh [commit]` writes what follows from the code and the docs:

- formatting
- OpenAPI document
- translation files
- surfaces, comments and whoopses with with git conflict markers
- given a commit, git conflict markers in prose since it as stamps pending.

## The database

`dev-db` runs PostgreSQL 16 from `~/.local/state/dev-db/`, on a socket only. The first start creates the cluster, the
roles and the `chatddx` database:

```sh
dev-db start
dev-db status
dev-db enter    # psql as chatddx
dev-db stop     # it keeps running after you leave the shell until you stop it
dev-db reset    # stop and delete everything; the next start begins empty
```

## State

In `dev/`:

- `turn-start`: the commit the turn started at, as in `./write.sh "$(cat dev/turn-start)"`.
- `refused`: there while work is refused this turn.
- `session-start`: what session-start hands the session's first turn.
- `stamped`: the commit `stamp` last found nothing pending in.

## Operator

In the dev shell, pulling and pushing through `as.sh` as `$CHATDDX_DEV`:

```sh
./dev/operator.sh fetch [branch]    # switch to the branch, bring it up to its tip on origin, say what is pending
./dev/operator.sh stamp [message]   # once nothing is pending: commit as "stamp", or the message, push, print the revision
./dev/operator.sh merge [branch]    # once nothing is pending: squash the branch onto main, push it, print its revision
```

`stamp` prints at once when nothing changed since it last stamped, as in `./dev/operator.sh stamp | osc copy`. Start the
next session at the revision it prints, with a first prompt that begins `At <revision>`.

## Agent

All `./dev/agents.sh` exits 0 but `turn-end`, which exits 2 to have the turn go on, and says nothing unless the agent
has something to do.

Claude Code's hooks (`.claude/settings.json`):

- `./dev/agent.sh session-start`, as a session starts: provisions the cloud container, then refuses work on what the
  commit the session starts at holds: anything out of step with the code, stamps or messages pending, and errors of
  format, lint, types or references.
- `./dev/agent.sh turn-start`, as a turn starts: moves a fresh session to the commit its first prompt starts at, or
  fast-forwards to what the operator pushed, and checks what that moved it to, refusing work on the OpenAPI document or
  the catalogs out of step and telling of the rest.
- `./dev/agent.sh turn-end`, as a turn ends: unless work was refused, runs `./write.sh <commit>` against the commit the
  turn started at, commits what that changed as `turn-end` and pushes.

Run at request "hand over":

- `./dev/agent.sh hand-over`: writes as `turn-end` does, commits all as `hand-over` and pushes, then checks the format,
  the types, the references and every test.

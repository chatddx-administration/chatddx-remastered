# Comments in `chatddx.store`

Written by `chatddx stamp write` from the comments in `src/chatddx/store/`, each under its file and the name it is in or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/store/catalog.py:Catalog._bind`

```
# src/chatddx/store/migrations/0012-t2-catalog.sql keeps each
# binding's source, and its id or fingerprint.
```

## `src/chatddx/store/migrations/0002-t1-factor.sql`

```
-- The roles every schema's tier 1 grants to. Roles are cluster-wide, so another database may
-- already have created them, or be creating them at this moment, as the tests' workers do.
```

## `src/chatddx/store/migrations/0003-t2-factor.sql`

```
-- Deferred because a reference may be inserted before the component it points at.
```

```
-- Every schema's insert-only triggers call this.
```

## `src/chatddx/store/migrations/0004-t0-ledger.sql`

```
-- Item rows reference their log's started row; `stage` is a constant so that a
-- foreign key can point at it.
```

## `src/chatddx/store/migrations/0005-t1-ledger.sql`

```
-- chatddx_reader gets nothing: run_item and score_item hold sensitive records
-- (src/chatddx/ledger/record.py: Record.sensitive).
```

## `src/chatddx/store/migrations/0007-t0-identity.sql`

```
-- Only a digest of the token is stored; the token itself lives in the client's cookie.
```

## `src/chatddx/store/migrations/0008-t1-identity.sql`

```
-- No default privileges: tables here may be mutable, so each one is granted explicitly.
```

```
-- chatddx_reader gets neither credential nor session: they hold password hashes and session tokens.
```

## `src/chatddx/store/migrations/0009-t2-identity.sql`

```
-- src/chatddx/identity/identity.py: Role
```

## `src/chatddx/store/migrations/0010-t0-catalog.sql`

```
-- Targets for the composite foreign keys below: a thread's edits point at components of
-- the thread's kind, and an edit's compilation is a compilation of the edit's skeleton.
```

```
-- src/chatddx/catalog/read.py: heads_of takes the edit with the highest id as a thread's head.
```

```
-- src/chatddx/catalog/threads.py: variation takes a fork's latest based_on, else its
-- forked_from, as its base.
```

```
-- src/chatddx/catalog/families.py: family_of matches a case to a binding by source, id and
-- vignette fingerprint; the binding with the highest id is where the family's vignette is now.
```

```
-- src/chatddx/catalog/model.py: About.of folds a subject's entries in id order.
```

```
-- Positions only mean something inside one scorer digest, so labels key on it.
```

```
-- src/chatddx/catalog/language.py: languages_of takes a component's latest row here as its
-- language.
```

## `src/chatddx/store/migrations/0012-t2-catalog.sql`

```
-- src/chatddx/catalog/model.py: THREAD_KINDS
```

```
-- src/chatddx/catalog/model.py: EntryField and Entry._shape, src/chatddx/factors/base.py:
-- LANGUAGE, and check_note in src/chatddx/catalog/threads.py.
-- A check passes when it is NULL, so NULL values are ruled out explicitly.
```

```
-- src/chatddx/catalog/threads.py: check_edit repeats this check.
```

```
-- src/chatddx/catalog/threads.py: check_edit repeats this check.
```

```
-- src/chatddx/catalog/families.py: plan_repair keeps the source and changes exactly one of the
-- id or the fingerprint.
```

```
-- src/chatddx/factors/base.py: LANGUAGE, src/chatddx/catalog/model.py: LANGUAGE_KINDS, and
-- check_language in src/chatddx/catalog/language.py.
```

```
-- A skeleton compiled later still takes its language from its recipe; this only refuses what is
-- already known to be compiled.
```

## `src/chatddx/store/migrations/0013-t0-catalog-binding-content.sql`

```
-- src/chatddx/catalog/families.py: family_of and _holder look a source's bindings up by the
-- vignette's id (binding_source) and by its content.
```

## `src/chatddx/store/migrations/0014-t0-source.sql`

```
-- The vignettes of database sources, as people typed them.
```

```
-- src/chatddx/store/texts.py: Texts.typed_since counts a person's latest texts.
```

## `src/chatddx/store/migrations/0015-t1-source.sql`

```
-- chatddx_reader gets nothing: the texts are vignettes. The writer gets no DELETE, so only
-- the admin deletes a text, to purge spam.
```

## `src/chatddx/store/migrations/0016-t2-source.sql`

```
-- A text is never changed; deleting is left to the admin's grants (0015-t1-source.sql).
```

## `src/chatddx/store/migrations/0017-t0-catalog-label-edit.sql`

```
-- Labels named a scorer digest, and now name the edit of a scorer thread they were written
-- with. The old rows are dropped rather than moved: a store from before holds v1 scorers,
-- which can't be read any more, and is rebuilt by loading its data sets again.
```

## `src/chatddx/store/migrations/0018-t2-catalog-label-edit.sql`

```
-- src/chatddx/catalog/threads.py: check_edit repeats the position's check, and
-- src/chatddx/store/catalog.py:Catalog.edit writes an edit's labels with it.
-- An edit's labels are written in its transaction, by its writer: now() is the
-- transaction's start, so a label written later has another `at` than its edit.
```

```
-- `by` is quoted: unquoted, PL/pgSQL reads it as the BY of FOR ... BY.
```

```
-- Triggers on the table 0017 replaced are gone with it; a store migrated to tier 0 first
-- has them already, from 0012.
```

## `src/chatddx/store/migrations/0019-t0-worker.sql`

```
-- A job takes a started run to its finish, and scores it when asked. What the run did
-- is the ledger's; `stage` is a constant so that a foreign key can point at the run's
-- started row.
```

```
-- A run has one job queued or under way at a time.
```

## `src/chatddx/store/migrations/0020-t1-worker.sql`

```
-- No default privileges: the tables are updated in place, so each one is granted
-- explicitly, and without DELETE, so that what was queued stays. chatddx_reader gets
-- nothing: why a job failed can quote what it was sending.
```

## `src/chatddx/store/migrations/0021-t2-worker.sql`

```
-- src/chatddx/store/queue.py: Status, and the writes that move a job between them.
```

```
-- What a job is asked to do never changes; only how it stands does.
```

## `src/chatddx/store/migrations/0022-t0-ledger-seq.sql`

```
-- One counter across the ledger's tables, so that a run's rows, its scores' included, are
-- read back in the order they were written. Rows from before are numbered in no
-- particular order.
```

## `src/chatddx/store/migrations/0024-t0-worker-scored.sql`

```
-- The scorers a job has finished, so that a job queued again mid-scoring scores what is
-- left.
```

## `src/chatddx/store/migrations/0025-t2-worker-scored.sql`

```
-- What a job is asked to do never changes, and what it has scored only grows; only how
-- it stands changes.
```

## `src/chatddx/store/migrations/0026-t2-catalog-run-variation.sql`

```
-- src/chatddx/catalog/model.py: EntryField, Entry._shape, _VARIED, _REPLACED and _WITH, and
-- check_note in src/chatddx/catalog/threads.py.
-- A check passes when it is NULL, so NULL values are ruled out explicitly.
```

```
-- A constraint trigger fires after the row's checks, so the value has its shape.
```

## `src/chatddx/store/notify.py:LIMIT`

```
# NOTIFY refuses a payload of 8000 bytes or more. Payloads are ASCII, so a character is
# a byte.
```

## `src/chatddx/store/queue.py:Queue.placed`

```
# Policy: a queued job's place is the jobs at its endpoint under way, or queued before
# it and to be claimed; none while its owner has paused.
```

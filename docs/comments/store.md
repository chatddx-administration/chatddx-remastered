# Comments in `store`

Written by `chatddx-dev index` from the comments in `[parts.store]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/store/cache.py:Cache`

```
# Policy: what is held is held per process and database, and only once read outside a
# transaction, so that what a transaction that rolls back wrote isn't held; the least
# recently used go past the size given.
```

## `src/chatddx/store/catalog.py:Catalog._bind`

```
# Dependency: src/chatddx/store/migrations/0012-t2-catalog.sql keeps each binding's
# source, and its id or fingerprint.
```

## `src/chatddx/store/migrations/0002-t1-factor.sql`

```
-- Accommodating for roles, which are cluster-wide: another database may already have
-- created those every schema's tier 1 grants to, or be creating them at this moment, as the
-- tests' workers do.
```

## `src/chatddx/store/migrations/0003-t2-factor.sql`

```
-- Policy: deferred because a reference may be inserted before the component it points at.
```

```
-- Dependency: every schema's insert-only triggers call this.
```

## `src/chatddx/store/migrations/0004-t0-ledger.sql`

```
-- Policy: item rows reference their log's started row; `stage` is a constant so that a
-- foreign key can point at it.
```

## `src/chatddx/store/migrations/0005-t1-ledger.sql`

```
-- Policy: chatddx_reader gets nothing: run_item and score_item hold sensitive records
-- (src/chatddx/ledger/record.py: Record.sensitive).
```

## `src/chatddx/store/migrations/0007-t0-identity.sql`

```
-- Policy: only a digest of the token is stored; the token itself lives in the client's
-- cookie.
```

## `src/chatddx/store/migrations/0008-t1-identity.sql`

```
-- Policy: no default privileges: tables here may be mutable, so each one is granted
-- explicitly.
```

```
-- Policy: chatddx_reader gets neither credential nor session: they hold password hashes and
-- session tokens.
```

## `src/chatddx/store/migrations/0009-t2-identity.sql`

```
-- Duplication: src/chatddx/identity/identity.py: Role
```

## `src/chatddx/store/migrations/0010-t0-catalog.sql`

```
-- Dependency: targets for the composite foreign keys below: a thread's edits point at
-- components of the thread's kind, and an edit's compilation is a compilation of the edit's
-- skeleton.
```

```
-- Dependency: src/chatddx/catalog/read.py: heads_of takes the edit with the highest id as a
-- thread's head.
```

```
-- Dependency: src/chatddx/catalog/threads.py: variation takes a fork's latest based_on,
-- else its forked_from, as its base.
```

```
-- Dependency: src/chatddx/catalog/families.py: family_of matches a case to a binding by
-- source, id and vignette fingerprint; the binding with the highest id is where the
-- family's vignette is now.
```

```
-- Dependency: src/chatddx/catalog/model.py: About.of folds a subject's entries in id order.
```

```
-- Policy: positions only mean something inside one scorer digest, so labels key on it.
```

```
-- Dependency: src/chatddx/catalog/language.py: languages_of takes a component's latest row
-- here as its language.
```

## `src/chatddx/store/migrations/0012-t2-catalog.sql`

```
-- Duplication: src/chatddx/catalog/model.py: THREAD_KINDS
```

```
-- Duplication: src/chatddx/catalog/model.py: EntryField and Entry._shape,
-- src/chatddx/factors/base.py: LANGUAGE, and check_note in src/chatddx/catalog/threads.py.
-- Accommodating for a check, which passes when it is NULL: NULL values are ruled out
-- explicitly.
```

```
-- Duplication: src/chatddx/catalog/threads.py: check_edit repeats this check.
```

```
-- Duplication: src/chatddx/catalog/threads.py: check_edit repeats this check.
```

```
-- Dependency: src/chatddx/catalog/families.py: plan_repair keeps the source and changes
-- exactly one of the id or the fingerprint.
```

```
-- Duplication: src/chatddx/factors/base.py: LANGUAGE, src/chatddx/catalog/model.py:
-- LANGUAGE_KINDS, and check_language in src/chatddx/catalog/language.py.
```

```
-- Scope: a skeleton compiled later still takes its language from its recipe; this only
-- refuses what is already known to be compiled.
```

## `src/chatddx/store/migrations/0013-t0-catalog-binding-content.sql`

```
-- Dependency: src/chatddx/catalog/families.py: family_of and _holder look a source's
-- bindings up by the vignette's id (binding_source) and by its content.
```

## `src/chatddx/store/migrations/0014-t0-source.sql`

```
-- Dependency: src/chatddx/store/texts.py: Texts.typed_since counts a person's latest texts.
```

## `src/chatddx/store/migrations/0015-t1-source.sql`

```
-- Policy: chatddx_reader gets nothing: the texts are vignettes. The writer gets no DELETE,
-- so only the admin deletes a text, to purge spam.
```

## `src/chatddx/store/migrations/0016-t2-source.sql`

```
-- Policy: a text is never changed; deleting is left to the admin's grants
-- (0015-t1-source.sql).
```

## `src/chatddx/store/migrations/0017-t0-catalog-label-edit.sql`

```
-- Compromise: labels named a scorer digest, and now name the edit of a scorer thread they
-- were written with. The old rows are dropped rather than moved: a store from before holds
-- v1 scorers, which can't be read any more, and is rebuilt by loading its data sets again.
```

## `src/chatddx/store/migrations/0018-t2-catalog-label-edit.sql`

```
-- Duplication: src/chatddx/catalog/threads.py: check_edit repeats the position's check.
-- Dependency: src/chatddx/store/catalog.py:Catalog.edit writes an edit's labels with it, in
-- its transaction, by its writer: now() is the transaction's start, so a label written
-- later has another `at` than its edit.
```

```
-- Accommodating for PL/pgSQL, which reads an unquoted `by` as the BY of FOR ... BY.
```

```
-- Accommodating for a store migrated to tier 0 first, which has these triggers already,
-- from 0012; those on the table 0017 replaced are gone with it.
```

## `src/chatddx/store/migrations/0019-t0-worker.sql`

```
-- Policy: what the run did is the ledger's; `stage` is a constant so that a foreign key can
-- point at the run's started row.
```

```
-- Policy: a run has one job queued or under way at a time.
```

## `src/chatddx/store/migrations/0020-t1-worker.sql`

```
-- Policy: no default privileges: the tables are updated in place, so each one is granted
-- explicitly, and without DELETE, so that what was queued stays. chatddx_reader gets
-- nothing: why a job failed can quote what it was sending.
```

## `src/chatddx/store/migrations/0021-t2-worker.sql`

```
-- Duplication: src/chatddx/store/queue.py: Status, and the writes that move a job between
-- them.
```

```
-- Policy: what a job is asked to do never changes; only how it stands does.
```

## `src/chatddx/store/migrations/0022-t0-ledger-seq.sql`

```
-- Policy: one counter across the ledger's tables, so that a run's rows, its scores'
-- included, are read back in the order they were written. Rows from before are numbered in
-- no particular order.
```

## `src/chatddx/store/migrations/0024-t0-worker-scored.sql`

```
-- Policy: the scorers a job has finished, so that a job queued again mid-scoring scores
-- what is left.
```

## `src/chatddx/store/migrations/0025-t2-worker-scored.sql`

```
-- Policy: what a job is asked to do never changes, and what it has scored only grows; only
-- how it stands changes.
```

## `src/chatddx/store/migrations/0026-t2-catalog-run-variation.sql`

```
-- Duplication: src/chatddx/catalog/model.py: EntryField, Entry._shape, _VARIED, _REPLACED
-- and _WITH, and check_note in src/chatddx/catalog/threads.py.
-- Accommodating for a check, which passes when it is NULL: NULL values are ruled out
-- explicitly.
```

```
-- Dependency: a constraint trigger fires after the row's checks, so the value has its
-- shape.
```

## `src/chatddx/store/migrations/0027-t2-catalog-description.sql`

```
-- Duplication: src/chatddx/catalog/model.py: Entry._shape, where a description is taken
-- away as a name is.
-- Accommodating for a check, which passes when it is NULL: NULL values are ruled out
-- explicitly.
-- Accommodating for a store holding an empty description, which the API wrote before a
-- description could be taken away: NOT VALID leaves the rows already written unchecked.
```

## `src/chatddx/store/migrations/0028-t0-catalog-version.sql`

```
-- Policy: one counter for the whole catalog, bumped by each transaction that writes to
-- it as it commits, so that what is held of the catalog is held while the counter
-- stands (src/chatddx/store/cache.py:catalogued). Bumped once per transaction and as
-- late as can be, so that writers wait on each other only as they commit.
```

```
-- Accommodating for the writer, which may not update catalog.version itself: bumped as
-- the admin that made it.
```

## `src/chatddx/store/notify.py:LIMIT`

```
# Accommodating for NOTIFY, which refuses a payload of 8000 bytes or more. Payloads are
# ASCII, so a character is a byte.
```

## `src/chatddx/store/queue.py:Queue.placed`

```
# Policy: a queued job's place is the jobs at its endpoint under way, or queued before
# it and to be claimed; none while its owner has paused.
```

## `src/chatddx/store/store.py:_PARSED`

```
# Policy: so many components held parsed and no more: factor.component is insert-only
# and a digest names what it holds, so one is held without a version.
```

## `src/chatddx/store/store.py:_RUNS`

```
# Policy: so many finished runs and scores held and no more: the ledger is insert-only
# and a finished record seals what was written before it, so one is held without a
# version; one not finished is read anew each time.
```

## `src/chatddx/store/test/test_catalog.py:test_a_store_holding_an_empty_description_still_migrates`

```
# Accommodating for catalog.version's deferred triggers, which a table can't be
# altered with pending: the store's rows are committed before it migrates, as
# `chatddx migrate` finds them.
```

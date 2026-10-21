# Comments in `chatddx.catalog`

Written by `chatddx stamp write` from the comments in `src/chatddx/catalog/`, each under its file and the name it is in or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/catalog/language.py:check_language`

```
# Duplication: src/chatddx/store/migrations/0012-t2-catalog.sql repeats these checks.
```

## `src/chatddx/catalog/model.py:_VARIED`

```
# Duplication: src/chatddx/store/migrations/0026-t2-catalog-run-variation.sql repeats
# these patterns.
```

## `src/chatddx/catalog/model.py:LANGUAGE_KINDS`

```
# Duplication: src/chatddx/store/migrations/0012-t2-catalog.sql repeats these kinds.
```

## `src/chatddx/catalog/model.py:THREAD_KINDS`

```
# Duplication: src/chatddx/store/migrations/0012-t2-catalog.sql repeats these kinds.
```

## `src/chatddx/catalog/threads.py:_check_based_on`

```
# Duplication: src/chatddx/store/migrations/0012-t2-catalog.sql repeats this check.
```

## `src/chatddx/catalog/threads.py:_check_labels`

```
# Duplication: src/chatddx/store/migrations/0018-t2-catalog-label-edit.sql repeats the
# positions.
```

## `src/chatddx/catalog/threads.py:_check_ran`

```
# Duplication: src/chatddx/store/migrations/0026-t2-catalog-run-variation.sql repeats
# this check.
```

```
# Scope: runs are the ledger's, which the catalog doesn't read: the store checks
# this one.
```

## `src/chatddx/catalog/threads.py:_sends_else`

```
# Policy: facts corrected where a configuration doesn't reach leave it as it is:
# following them would write nothing (holds).
```

## `src/chatddx/catalog/threads.py:check_note`

```
# Duplication: src/chatddx/store/migrations/0012-t2-catalog.sql repeats the language
# rule.
```

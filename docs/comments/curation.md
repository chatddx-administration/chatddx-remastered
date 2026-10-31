# Comments in `curation`

Written by `chatddx-dev index` from the comments in `[parts.curation]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/curation/plan.py:_LATE_TABLES`

```
# Dependency: planned after recipes and judges, as a view may name a judge.
```

## `src/chatddx/curation/plan.py:_REFERENCES`

```
# Scope: references outside recipes, by table and field; each names stanzas of another table.
```

## `src/chatddx/curation/plan.py:plan_factors.plan_table`

```
# Policy: a tool's description is a field, what the model reads; it's the
# entry too.
```

## `src/chatddx/curation/plan.py:TABLES`

```
# Dependency: after the stanzas whose texts its entries are grouped by.
```

## `src/chatddx/curation/test/test_init.py:test_sync_archive_and_person_provision_commands`

```
# Scope: what it loads is read in
# test_wipe_data_deletes_and_unshares_and_a_provision_shares_it_back.
```

## `src/chatddx/curation/write.py:_Init.appended`

```
# Dependency: an appendix is bound to the vignette its case was just read at, so
# it's built here rather than planned.
```

## `src/chatddx/curation/write.py:_Init.archived`

```
# Policy: the archive's live threads among those given, or else the latest it
# pruned, restored, so that what comes back to the data comes back as it was,
# its forks' origin with it.
```

## `src/chatddx/curation/write.py:_Init.binds`

```
# Policy: an appendix is named as its case's file names it, so two cases' may share
# a name; each is its vignette's, by the vignette's source and id.
```

## `src/chatddx/curation/write.py:_Init.forked`

```
# Policy: a thread's origin is set when it is created (put), so a re-run only
# reports one that differs from the data's.
```

## `src/chatddx/curation/write.py:_Init.prune`

```
# Policy: what the archive holds and the data doesn't is deleted and unshared, but
# for a case the data names that wasn't reached this time, and what the data names
# that this World can't plan, so that a source or a World amiss prunes nothing of it.
```

## `src/chatddx/curation/write.py:_Writer._unnamed`

```
# Policy: a name an earlier giftbag gave a fork of an expectation, its origin's title,
# is taken back, as an expectation with no name is said by its case.
```

## `src/chatddx/curation/write.py:_Writer.giftbag`

```
# Policy: a fork the person deleted stays deleted, so that a provision
# doesn't bring back what they let go.
```

```
# Policy: an expectation with no name is said by its case where it is shown,
# so its fork takes no title derived of it as a name.
```

## `src/chatddx/curation/write.py:_Writer.said`

```
# Policy: an expectation is said by its case and an appendix by its name and its
# vignette's, as sync-archive says them as it writes them.
```

# Comments in `chatddx.curation`

Written by `chatddx stamp write` from the comments in `src/chatddx/curation/`, each under its file and the name it is in or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/curation/plan.py:LATE_TABLES`

```
# Dependency: planned after recipes and judges, as a view may name a judge.
```

## `src/chatddx/curation/plan.py:plan_factors.plan_table`

```
# Policy: a tool's description is a field, what the model reads; it's the
# entry too.
```

## `src/chatddx/curation/plan.py:REFERENCES`

```
# Scope: references outside recipes, by table and field; each names stanzas of another table.
```

## `src/chatddx/curation/plan.py:TABLES`

```
# Dependency: after the stanzas whose texts its entries are grouped by.
```

## `src/chatddx/curation/test/test_init.py:test_init_data_command`

```
# Scope: what it loads is read in
# test_wipe_data_deletes_and_unshares_and_init_data_gives_it_back.
```

## `src/chatddx/curation/write.py:_Init.appended`

```
# Dependency: an appendix is bound to the vignette its case was just read at, so
# it's built here rather than planned.
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

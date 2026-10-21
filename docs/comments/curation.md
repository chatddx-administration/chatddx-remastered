# Comments in `chatddx.curation`

Written by `chatddx stamp write` from the comments in `src/chatddx/curation/`, each under its file and the name it is in or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/curation/plan.py:LATE_TABLES`

```
# Planned after recipes and judges, as a view may name a judge.
```

## `src/chatddx/curation/plan.py:plan_factors.plan_table`

```
# A tool's description is a field, what the model reads; it's the entry
# too.
```

## `src/chatddx/curation/plan.py:REFERENCES`

```
# Scope: references outside recipes, by table and field; each names stanzas of another table.
```

## `src/chatddx/curation/plan.py:TABLES`

```
# Dependency: after the stanzas whose texts its entries are grouped by.
```

## `src/chatddx/curation/test/cases.py:appended`

```
# What loading the cases lands beside each case and its expectation: the appendices, the
# cases that send them, and those cases' expectations.
```

## `src/chatddx/curation/test/test_init.py:test_init_data_command`

```
# What it loads is read in test_wipe_data_deletes_and_unshares_and_init_data_gives_it_back.
```

## `src/chatddx/curation/test/test_init.py:test_init_data_loads_the_archive`

```
# The rest of the cases, and their expectations, are left over.
```

## `src/chatddx/curation/test/test_init.py:test_wipe_data_deletes_and_unshares_and_init_data_gives_it_back`

```
# Each later run writes an entry per gift and per share, and no thread.
```

## `src/chatddx/curation/test/test_repair.py:test_repair_moves_the_archive_s_families_to_their_vignettes_new_places`

```
# The data follows the rename, and init-data finds the archive whole again: a
# changed case keeps its expectation behind, and a renamed one takes it along.
```

## `src/chatddx/curation/write.py:_Init.appended`

```
# An appendix is bound to the vignette its case was just read at, so it's built here
# rather than planned.
```

## `src/chatddx/curation/write.py:_Init.binds`

```
# An appendix is named as its case's file names it, so two cases' may share a name;
# each is its vignette's, by the vignette's source and id.
```

## `src/chatddx/curation/write.py:_Init.forked`

```
# A thread's origin is set when it is created (put), so a re-run only reports one
# that differs from the data's.
```

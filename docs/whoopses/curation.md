# Whoopses and asserts in `chatddx.curation`

Written by `chatddx stamp write` from the `raise Whoops` and `assert` statements in `src/chatddx/curation/`, its tests left out, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in>`

```
<the statement, as written>
```
````

- A statement in no name is under its file alone, and a `Whoops` is any of its subclasses too.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/curation/plan.py:plan_factors.under`

```
assert inventory is not None
```

## `src/chatddx/curation/write.py:_Init._expecting`

```
assert isinstance(head, Expectation)
```

## `src/chatddx/curation/write.py:_Init.binds`

```
assert isinstance(held, Appendix)
```

## `src/chatddx/curation/write.py:_Init.family_of`

```
assert isinstance(expectation, Expectation)
```

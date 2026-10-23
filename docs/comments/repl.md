# Comments in `chatddx.repl`

Written by `chatddx stamp write` from the comments in `src/chatddx/repl/`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

## `src/chatddx/repl/render.py:_ANSWERED`

```
# Policy: what the scoring pass notes of an answer, which show_answer says already.
```

## `src/chatddx/repl/render.py:_verdict_of`

```
# Dependency: `at` as the verdict metrics read it: src/chatddx/scorers/verdicts.py.
```

## `src/chatddx/repl/running.py:Held._pressed`

```
# Policy: a press goes through once, while scoring: the bench finishes the score
# under way.
```

## `src/chatddx/repl/shell.py:console`

```
# Accommodating for rich, which would read the brackets that names, vignettes and
# answers may hold as markup.
```

## `src/chatddx/repl/test/test_listing.py:listed`

```
# Policy: wide enough that no configuration's name wraps.
```

# Comments in `scorers`

Written by `chatddx-dev index` from the comments in `[parts.scorers]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/scorers/scorer.py:Metric.reads`

```
# Policy: what of the expected items the score depends on, all of them unless given;
# a judged metric's are all its judge is asked.
```

## `src/chatddx/scorers/scorer.py:Metric.refuses`

```
# Policy: why an expected item can't be what it reads, such as an unreadable pattern,
# so that what can't ever be scored isn't written.
```

## `src/chatddx/scorers/scorer.py:Verdicts`

```
# Policy: a verdict that couldn't be read is kept as none, so that a judged view's verdicts
# stay one per seed of its judge.
```

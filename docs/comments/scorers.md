# Comments in `chatddx.scorers`

Written by `chatddx stamp write` from the comments in `src/chatddx/scorers/`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/scorers/scorer.py:Verdicts`

```
# Policy: a verdict that couldn't be read is kept as none, so that a judged view's verdicts
# stay one per seed of its judge.
```

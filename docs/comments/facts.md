# Comments in `chatddx.facts`

Written by `chatddx stamp write` from the comments in `src/chatddx/facts/`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

## `src/chatddx/facts/models.py:_narrowed`

```
# Policy: facts are kept per model, so the engines serving one narrow them only where
# every one of them does, each a vLLM 0.24 whose flags say so.
```

## `src/chatddx/facts/models.py:Facts.load`

```
# Policy: a World's facts about a model take the place of the bundled ones, as its
# engines may serve the model otherwise, as with a shorter context.
```

## `src/chatddx/facts/models.toml`

```
# Provenance: the first two models' facts were the old inventory's llm facts (chatddx 7893656,
# src/chatddx/data/inventory/llms.toml), ported by hand.
```

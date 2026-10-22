# Comments in `chatddx.facts`

Written by `chatddx stamp write` from the comments in `src/chatddx/facts/`, each under its file and the name it is in or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).

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

# Comments in `chatddx.factors`

Written by `chatddx stamp write` from the comments in `src/chatddx/factors/`, each under its file and the name it is in or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/factors/base.py:_walk`

```
# pyright: ignore[reportDeprecated]
```

## `src/chatddx/factors/base.py:Component._storable`

```
# Accommodating for jsonb, which the store keeps each component as and which can't
# hold U+0000 (src/chatddx/store/migrations/0001-t0-factor.sql).
```

## `src/chatddx/factors/base.py:Component.cross_check`

```
# pyright: ignore[reportUnusedParameter]
```

## `src/chatddx/factors/base.py:Component.schema_version`

```
# Policy: bump when an existing field's meaning or default changes; additive fields
# don't.
```

## `src/chatddx/factors/cases.py:CleanupOp`

```
# Policy: each op name pins one behavior; a changed behavior gets a new name.
```

## `src/chatddx/factors/engine.py:_abbreviations`

```
# Accommodating for vLLM's parser, which expands an unambiguous prefix of a flag to the
# whole flag.
```

## `src/chatddx/factors/engine.py:_bare_arguments`

```
# Accommodating for `vllm serve`, which takes the model as its one bare argument, which
# the start-up script gives, so another bare argument stops vLLM from starting. One that
# follows a flag written without "=" may be that flag's value; telling them apart needs
# vLLM's list of flags.
```

## `src/chatddx/factors/engine.py:_READS_DATE`

```
# Accommodating for templates that insert the current date, which make the prompt depend
# on when a run happens.
```

## `src/chatddx/factors/engine.py:flag_names`

```
# Accommodating for vLLM, which reads "_" as "-" in a flag's name, up to its first "."
# (FlexibleArgumentParser).
```

## `src/chatddx/factors/engine.py:LocalModel.name`

```
# Dependency: facts are keyed by it, as by a remote model's.
```

## `src/chatddx/factors/kinds.py:KINDS`

```
# Dependency: the only kinds stored bytes are read as.
# src/chatddx/catalog/model.py:THREAD_KINDS threads all but cases and compilations.
```

## `src/chatddx/factors/request.py:BYPASS_KEYS`

```
# Policy: vLLM request keys that would replace the engine's chat template, constrain the
# answer outside the output contract, or put the prompt's text in the stored response.
```

## `src/chatddx/factors/request.py:compile_request`

```
# Policy: guidance goes where it's inserted, or else after the instructions, in this
# order.
```

## `src/chatddx/factors/request.py:SchemaOp`

```
# Policy: as with CleanupOp (cases.py), each op name pins one behavior; a changed
# behavior gets a new name.
```

## `src/chatddx/factors/response.py:REASONING`

```
# Accommodating for servers: vLLM 0.24 says `reasoning`, as the fake does; other
# OpenAI-compatible servers say `reasoning_content`.
```

## `src/chatddx/factors/scoring.py:FillOp`

```
# Policy: how a judge's slots are written out, one name per behavior as with CleanupOp
# (cases.py).
```

## `src/chatddx/factors/select.py`

```
# Scope: a selector picks the values a view compares: a JSON Pointer (RFC 6901), which
# picks at most one value, or a JSONPath query (RFC 9535) from a small subset: member
# names (`.name`, `['name']`), indexes (`[0]`, `[-1]`), wildcards (`.*`, `[*]`), and
# filters that test a relative path for existence (`[?@.critical]`) or compare it with a
# literal (`[?@.critical == true]`, `!=`). Within the subset, every RFC 9535
# implementation selects the same nodes. RFC 9535 leaves the order of an object's
# members open; this keeps the document's order.
```

## `src/chatddx/factors/select.py:SplitOp`

```
# Policy: splits applied to selected text, one name per behavior as with text-cleanup
# ops.
```

## `src/chatddx/factors/trial.py:suggest_seeds`

```
# Accommodating for some servers, which require seeds within a signed 32-bit int.
```

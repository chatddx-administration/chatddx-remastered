# Comments in `chatddx.fake_vllm`

Written by `chatddx stamp write` from the comments in `src/chatddx/fake_vllm/`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

## `src/chatddx/fake_vllm/chat.py:_placed`

```
# Accommodating for Harmony, whose channel markers are special tokens,
# skipped when detokenized.
```

## `src/chatddx/fake_vllm/chat.py:_tool`

```
# Dependency: the compiler offers the answer tool last
# (src/chatddx/factors/request.py:compile_request).
```

## `src/chatddx/fake_vllm/chat.py:_WORD`

```
# Accommodating for Qwen3's vocabulary, where a thinking tag is a token of its own,
# which vLLM streams alone.
```

## `src/chatddx/fake_vllm/chat.py:instance`

```
# Accommodating for JSON Schema, where a branch holds together with the
# keywords beside it, as `required` beside `type` and `properties` does.
```

## `src/chatddx/fake_vllm/chat.py:respond`

```
# Accommodating for a discovered fact: gpt-oss does so on malborg at times, held
# to a grammar that lets whitespace in before a closing brace: the answer ends,
# the tokens don't.
```

## `src/chatddx/fake_vllm/script.py:Script`

```
# Dependency: a script's file may hold keys of its reader's:
# src/chatddx/scripted/read.py.
```

## `src/chatddx/fake_vllm/served.py:_options`

```
# Accommodating for vLLM, which reads "_" as "-" in a flag's name up to its first ".",
# and where the last of a flag given twice wins. Values run to the next flag, as for
# --served-model-name's nargs="+".
```

## `src/chatddx/fake_vllm/served.py:CLOSURE`

```
# Dependency: the closure a fake engine's runtime names: the command that serves it
# (worlds/sample/engines.toml).
```

## `src/chatddx/fake_vllm/served.py:Served.parses_tools`

```
# Accommodating for vLLM, where a tool parser exists only with both flags, whatever
# the error messages name.
```

## `src/chatddx/fake_vllm/server.py:_Handler._authorized`

```
# Accommodating for vLLM, which with --api-key asks for one of its keys as a bearer
# on /v1 only, so /health and /version answer anyone.
```

## `src/chatddx/fake_vllm/server.py:_Handler._next_token`

```
# Accommodating for vLLM, which hears a hang-up from the socket while it waits for
# the next token, rather than at the next write.
```

## `src/chatddx/fake_vllm/server.py:_Handler.log_message`

```
# Policy: logged, not written to stderr: a request's thread can outlive its client,
# so what it logs goes to whoever listens then; `run` prints it.
```

## `src/chatddx/fake_vllm/test/helpers.py:QWEN_ARGV`

```
# Provenance: as the old chatddx served them (chatddx 7893656,
# src/chatddx/data/inventory/malborg.toml).
```

# `chatddx.fake_vllm`

Written by `chatddx stamp write` from `src/chatddx/fake_vllm/`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it:

```
## `<name>` `@<decorator>` `[<type parameters>]` `(<bases>)`
`<file>:<qualified name>`

* `<parameter or field>: <type> = <default>`
* ∟`<return type>`

Raises:
1. `<exception>`: `<arguments>` (from `<exception caught>`, through `<private helper>`, in a `ValidationError`)

Finds:
1. `<code>`: `<message>` (`<level>`, from `<exception caught>`, through `<private helper>`)
```

- A constant or a type alias is its definition instead of bullets; a class and its `__init__` leave out ∟, and a method its instance; `*`: the parameters after it are keyword-only, `/`: those before it positional-only.
- Raises and Finds are the function's own and its private helpers', in the order the code reaches them, each once, a `Whoops` left out; what a public function it calls raises is in that function's entry.
- Text is quoted, a value in it as `{<expression>}`, and an argument that isn't text is as written; a finding is a warning unless it gives its level.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `accept`
`src/chatddx/fake_vllm/chat.py:accept`

* `served: Sequence[Served]`
* `body: dict[str, Any]`
* ∟`Served`

## `ANSWER`
`src/chatddx/fake_vllm/chat.py:ANSWER`

`ANSWER = "\n".join(DIAGNOSES)`

## `Call` `@dataclass(frozen=True)`
`src/chatddx/fake_vllm/chat.py:Call`

* `name: str`
* `arguments: str`
* `id: str`

## `check`
`src/chatddx/fake_vllm/chat.py:check`

* `served: Served`
* `body: dict[str, Any]`
* ∟`None`

Raises:
1. `Failure`: `""auto" tool choice requires --enable-auto-tool-choice and --tool-call-parser to be set"`
2. `Failure`: `"tool_choice="{choice}" requires --tool-call-parser to be set"`
3. `Failure`: `"Harmony does not support reasoning_effort='none'"`
4. `Failure`: `"reasoning_effort={effort!r} is not supported by Harmony. Supported values are: {', '.join(_HARMONY_EFFORTS)}."`
5. `Failure`: `"thinking_token_budget is set but reasoning_config is not configured. Please set --reasoning-parser and/or --reasoning-config to use thinking_token_budget."`

## `CLOSURE`
`src/chatddx/fake_vllm/served.py:CLOSURE`

`CLOSURE = "chatddx fake-vllm"`

## `completion`
`src/chatddx/fake_vllm/chat.py:completion`

* `served: Served`
* `body: dict[str, Any]`
* `reply: Reply`
* ∟`dict[str, Any]`

## `CONTEXT`
`src/chatddx/fake_vllm/served.py:CONTEXT`

`CONTEXT: dict[str, int] = {…}`

## `DEFAULT_CONTEXT`
`src/chatddx/fake_vllm/served.py:DEFAULT_CONTEXT`

`DEFAULT_CONTEXT = 32768`

## `DIAGNOSES`
`src/chatddx/fake_vllm/chat.py:DIAGNOSES`

`DIAGNOSES = ("Fake diagnosis A", "Fake diagnosis B", "Fake diagnosis C")`

## `Failure` `(Exception)`
`src/chatddx/fake_vllm/chat.py:Failure`

* `message: str`
* `type: str`
* `status: int`
* `param: str | None`

## `Failure.__init__`
`src/chatddx/fake_vllm/chat.py:Failure.__init__`

* `message: str`
* `type: str = "BadRequestError"`
* `status: int = 400`
* `param: str | None = None`

## `Failure.body`
`src/chatddx/fake_vllm/chat.py:Failure.body`

* ∟`dict[str, Any]`

## `got`
`src/chatddx/fake_vllm/server.py:got`

* `served: Sequence[Served]`
* `path: str`
* ∟`tuple[int, Any]`

## `GREEDY_TEMP`
`src/chatddx/fake_vllm/chat.py:GREEDY_TEMP`

`GREEDY_TEMP = 1e-5`

## `instance`
`src/chatddx/fake_vllm/chat.py:instance`

* `schema: Any`
* `root: Any = None`
* `key: str = "value"`
* `n: int | None = None`
* `depth: int = 0`
* `turn: int = 0`
* ∟`Any`

## `log`
`src/chatddx/fake_vllm/chat.py:log`

`log = logging.getLogger(__name__)`

## `models`
`src/chatddx/fake_vllm/server.py:models`

* `served: Sequence[Served]`
* ∟`dict[str, Any]`

## `pick`
`src/chatddx/fake_vllm/chat.py:pick`

* `served: Sequence[Served]`
* `body: dict[str, Any]`
* ∟`Served`

Raises:
1. `Failure`: `` "The model `{model}` does not exist.", "NotFoundError", 404, "model" ``

## `Refused` `(ValueError)`
`src/chatddx/fake_vllm/served.py:Refused`

## `Reply` `@dataclass(frozen=True)`
`src/chatddx/fake_vllm/chat.py:Reply`

* `reasoning: str | None`
* `content: str`
* `calls: tuple[Call, ...]`
* `finish: str`
* `runaway: int = 0`
* `hang_up: int | None = None`
* `hold: int | None = None`

## `respond`
`src/chatddx/fake_vllm/chat.py:respond`

* `served: Served`
* `body: dict[str, Any]`
* `runaway: bool = False`
* ∟`Reply`

## `run`
`src/chatddx/fake_vllm/server.py:run`

* `model: str`
* `argv: Sequence[str]`
* `delay: float`
* `runaway: bool`
* `script: Script | None = None`
* ∟`None`

Raises:
1. `SystemExit`: `"the fake vLLM won't start: {e}"` (from `Refused`)

## `run_all`
`src/chatddx/fake_vllm/server.py:run_all`

* `served: Sequence[Served]`
* `delay: float`
* `runaway: bool`
* `script: Script | None = None`
* ∟`None`

## `Script`
`src/chatddx/fake_vllm/script.py:Script`

* `turns: tuple[Turn, ...]`
* `released: threading.Event`

## `Script.__init__`
`src/chatddx/fake_vllm/script.py:Script.__init__`

* `turns: Iterable[Turn]`

## `Script.load` `@classmethod`
`src/chatddx/fake_vllm/script.py:Script.load`

* `path: Path`
* ∟`"Script"`

## `Script.next`
`src/chatddx/fake_vllm/script.py:Script.next`

* ∟`tuple[int, Turn] | None`

## `Script.of` `@classmethod`
`src/chatddx/fake_vllm/script.py:Script.of`

* `data: dict[str, Any]`
* `where: str = "the script"`
* ∟`"Script"`

Raises:
1. `Refused`: `"{where} has no [[turn]]"`

## `Script.release`
`src/chatddx/fake_vllm/script.py:Script.release`

* ∟`None`

## `scripted`
`src/chatddx/fake_vllm/chat.py:scripted`

* `served: Served`
* `body: dict[str, Any]`
* `turn: Turn`
* ∟`Reply`

## `Served` `@dataclass(frozen=True)`
`src/chatddx/fake_vllm/served.py:Served`

* `model: str`
* `names: tuple[str, ...]`
* `max_model_len: int`
* `reasoning_parser: bool`
* `reasoning_config: bool`
* `auto_tools: bool`
* `tool_parser: str | None`
* `default_chat_template_kwargs: dict[str, Any]`
* `system_fingerprint: str | None`
* `host: str`
* `port: int`
* `api_keys: tuple[str, ...] = ()`

## `Served.family` `@property`
`src/chatddx/fake_vllm/served.py:Served.family`

* ∟`str | None`

## `Served.name` `@property`
`src/chatddx/fake_vllm/served.py:Served.name`

* ∟`str`

## `Served.of` `@classmethod`
`src/chatddx/fake_vllm/served.py:Served.of`

* `model: str`
* `argv: Sequence[str] = ()`
* ∟`"Served"`

Raises:
1. `Refused`: `"the fake vLLM can't read --config FILE; give its arguments instead"` (through `_options`)
2. `Refused`: `"{name} takes one value, not {values}"` (through `_one`)
3. `Refused`: `"invalid tool call parser: None"`
4. `Refused`: `"--api-key takes a key or more"`
5. `Refused`: `"the fake vLLM reads {name} as an integer, not {value!r}"` (through `_int`)
6. `Refused`: `"--default-chat-template-kwargs {value} is no JSON object"` (through `_kwargs`)
7. `Refused`: `"--fingerprint-mode {mode!r} is none of {_FINGERPRINT_MODES}"` (through `_fingerprint`)

## `Served.parses_tools` `@property`
`src/chatddx/fake_vllm/served.py:Served.parses_tools`

* ∟`bool`

## `server`
`src/chatddx/fake_vllm/server.py:server`

* `served: Sequence[Served]`
* `host: str | None = None`
* `port: int | None = None`
* `delay: float = 0.0`
* `runaway: bool = False`
* `script: Script | None = None`
* ∟`ThreadingHTTPServer`

Raises:
1. `ValueError`: `"the fake vLLM needs a model to serve"`

## `serving` `@contextmanager`
`src/chatddx/fake_vllm/server.py:serving`

* `served: Sequence[Served]`
* `host: str | None = None`
* `port: int | None = None`
* `delay: float = 0.0`
* `runaway: bool = False`
* `script: Script | None = None`
* ∟`Generator[tuple[str, int]]`

## `stream`
`src/chatddx/fake_vllm/chat.py:stream`

* `served: Served`
* `body: dict[str, Any]`
* `reply: Reply`
* ∟`Iterator[tuple[str, int]]`

## `temperature`
`src/chatddx/fake_vllm/chat.py:temperature`

* `body: dict[str, Any]`
* ∟`float | None`

## `thinking`
`src/chatddx/fake_vllm/chat.py:thinking`

* `body: dict[str, Any]`
* ∟`str`

## `thinks`
`src/chatddx/fake_vllm/chat.py:thinks`

* `served: Served`
* `body: dict[str, Any]`
* ∟`bool`

## `tool_choice`
`src/chatddx/fake_vllm/chat.py:tool_choice`

* `body: dict[str, Any]`
* ∟`Any`

## `Turn` `@dataclass(frozen=True)`
`src/chatddx/fake_vllm/script.py:Turn`

* `reasoning: str | None = None`
* `content: str = ""`
* `calls: tuple[tuple[str, str], ...] = ()`
* `finish: str | None = None`
* `runaway: int = 0`
* `hang_up: int | None = None`
* `hold: int | None = None`
* `status: int | None = None`

## `turn`
`src/chatddx/fake_vllm/script.py:turn`

* `where: str`
* `value: object`
* ∟`Turn`

Raises:
1. `Refused`: `"{where} is a table"`
2. `Refused`: `"{where} has no {sorted(stray)}"`
3. `Refused`: `"{where} hangs up or holds, not both"`
4. `Refused`: `"{where}.tool_calls is a list"`
5. `Refused`: `"{where} is text, not {value!r}"` (through `_str`)
6. `Refused`: `"{where} is a table of a name and arguments"` (through `_call`)
7. `Refused`: `"{where} is a count, not {value!r}"` (through `_count`)

## `validate`
`src/chatddx/fake_vllm/chat.py:validate`

* `body: dict[str, Any]`
* ∟`None`

Raises:
1. `Failure`: `` "`tools` must not be an empty array. Either provide at least one tool or omit the field entirely." ``
2. `Failure`: `` "When using `tool_choice`, `tools` must be set.", param="tool_choice" ``
3. `Failure`: `` "The tool specified in `tool_choice` does not match any of the specified `tools`", param="tool_choice" ``
4. `Failure`: `` "Invalid value for `tool_choice`: {choice}! Only named tools, "none", "auto" or "required" are supported.", param="tool_choice" ``

## `VERSION`
`src/chatddx/fake_vllm/served.py:VERSION`

`VERSION = "0.24.0+fake"`

## `VOCABULARY`
`src/chatddx/fake_vllm/chat.py:VOCABULARY`

`VOCABULARY = 151936`

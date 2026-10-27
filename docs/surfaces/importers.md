# `chatddx.importers`

Written by `chatddx stamp write` from `src/chatddx/importers/`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it:

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

## `checked`
`src/chatddx/importers/o11n.py:checked`

* `imports: Sequence[Imported]`
* ∟`list[Finding]`

Raises:
1. `ValueError`: `"{i.name} and {other} are both at {e.url}"` (through `_inventory`)
2. `ValueError`: `"{i.name} binds {i.bind}, another server on {i.host} {known.bind}"` (through `_inventory`)
3. `ValueError`: `"; ".join(found)`

## `endpoints_toml`
`src/chatddx/importers/o11n.py:endpoints_toml`

* `imports: Iterable[Imported]`
* ∟`str`

Raises:
1. `ValueError`: `"{i.name} and {other} are both at {e.url}"` (through `_inventory`)
2. `ValueError`: `"{i.name} binds {i.bind}, another server on {i.host} {known.bind}"` (through `_inventory`)
3. `TypeError`: `"no TOML for {value!r}"` (through `_value`)

## `engines_toml`
`src/chatddx/importers/o11n.py:engines_toml`

* `imports: Iterable[Imported]`
* ∟`str`

Raises:
1. `TypeError`: `"no TOML for {value!r}"` (through `_value`)
2. `ValueError`: `"{i.name} serves other weights under handle {i.server!r} than a server of that name on another host"`

## `Imported` `@dataclass(frozen=True)`
`src/chatddx/importers/o11n.py:Imported`

* `name: str`
* `server: str`
* `host: str`
* `model: LocalModel`
* `engine: LocalEngine`
* `bind: str`
* `location: str`
* `template: str`
* `endpoint: EndpointSpec`
* `findings: tuple[Finding, ...]`

## `imported`
`src/chatddx/importers/o11n.py:imported`

* `report: dict[str, Any]`
* `server: str`
* `endpoint_host: str | None = None`
* ∟`Imported`

Raises:
1. `LookupError`: `"the report has no server {server!r}, only {sorted(servers)}"`
2. `ValueError`: `"{name} can't be imported: {e}"` (from `(KeyError, TypeError, ValueError)`)

Finds:
1. `engine.chat_template_unused`: `"vLLM renders this model with Harmony and doesn't read the chat template, so its hash pins nothing"` (`info`, through `_template`)
2. `engine.harmony_date`: `"Harmony writes the current date into every prompt; set VLLM_SYSTEM_START_DATE in the server's environment to fix it"` (through `_template`)
3. `engine.chat_template_unread`: `"the report has no template text, so it wasn't checked"` (`info`, through `_template`)
4. `engine.chat_template_not_the_model_s`: `"the chat template isn't the model's own at this revision ({cast(dict[str, Any], own).get('path')})"` (`info`, through `_template`)
5. `endpoint.process`: `"the server's process wasn't seen: {error}"` (through `_serving`)
6. `endpoint.not_running`: `"the server isn't running"` (through `_serving`)
7. `endpoint.argv`: `"the running server's argv isn't the configured one, so it may predate the configuration"` (through `_serving`)
8. `endpoint.unreachable`: `"the server didn't answer: {error}"` (through `_serving`)
9. `endpoint.version`: `"the server says it is vLLM {served.get('version')}, its package {version}"` (through `_serving`)
10. `endpoint.served_name`: `"the server answers as {', '.join(map(str, names)) or 'nothing'}; put {engine.digest} first in its servedModelNames"` (through `_serving`)

## `read`
`src/chatddx/importers/o11n.py:read`

* `source: str`
* ∟`tuple[dict[str, Any], str | None]`

Raises:
1. `ValueError`: `"{source} is not an {REPORT} report"`

## `REPORT`
`src/chatddx/importers/o11n.py:REPORT`

`REPORT = "o11n.vllm.report/1"`

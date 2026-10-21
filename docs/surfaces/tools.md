# `chatddx.tools`

Written by `chatddx stamp` from `src/chatddx/tools/`; how to read it is in [docs/surfaces.md](../surfaces.md).

## `results`
`src/chatddx/tools/web_search.py:results`

* `page: str`
* `query: str`
* `max_results: int = 5`
* ∟`str`

## `SEARCH_URL`
`src/chatddx/tools/web_search.py:SEARCH_URL`

`SEARCH_URL = "https://html.duckduckgo.com/html/"`

## `ShippedTool` `@dataclass(frozen=True)`
`src/chatddx/tools/shipped.py:ShippedTool`

* `version: int`
* `function: Callable[..., object]`

## `TOOLS`
`src/chatddx/tools/shipped.py:TOOLS`

`TOOLS: dict[str, ShippedTool] = {…}`

## `USER_AGENT`
`src/chatddx/tools/web_search.py:USER_AGENT`

`USER_AGENT = "Mozilla/5.0 (compatible; chatddx-web-search/1.0)"`

## `web_search`
`src/chatddx/tools/web_search.py:web_search`

* `query: str`
* `max_results: int = 5`
* ∟`str`

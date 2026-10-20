# `chatddx.inventory`

Written by `chatddx reference` from `src/chatddx/inventory/`; how to read it is in [docs/reference/README.md](README.md).

## AnySource
`src/chatddx/inventory/inventory.py:AnySource`

* `AnySource`

## broken
`src/chatddx/inventory/check.py:broken`

* `inventory: Inventory`
* `get: Resolver`
* ∟`list[str]`

Finds:
1. `endpoint.engine_unknown`: str(e) (from `StructuralError`, through `_engine`)
2. `endpoint.not_engine`: "{digest} is a {engine.kind_name}, not an engine" (through `_engine`)

## check
`src/chatddx/inventory/check.py:check`

* `inventory: Inventory`
* `get: Resolver`
* ∟`list[Finding]`

Finds:
1. `endpoint.engine_unknown`: str(e) (from `StructuralError`, through `_engine`)
2. `endpoint.not_engine`: "{digest} is a {engine.kind_name}, not an engine" (through `_engine`)
3. `endpoint.unstartable`: str(e) (from `LookupError`, through `_endpoint`)
4. `endpoint.remote_host`: "it serves a remote engine, which no host of ours runs, but names host {host!r}" (through `_endpoint`)
5. `endpoint.shared_url`: "{url} is also the address of endpoint {names[0]!r}"
6. `host.unpinned`: "it says where it keeps {what} {key}, which none of its endpoints' engines pins" (info)
7. `cleared.not_sensitive`: "it is cleared for source {source!r}, which isn't sensitive and needs no clearance" (info)

## DatabaseSource `(Source)`
`src/chatddx/inventory/sources.py:DatabaseSource`

* `kind: Literal["database"] = "database"`

## DirectorySource `(Source)`
`src/chatddx/inventory/sources.py:DirectorySource`

* `kind: Literal["directory"] = "directory"`
* `path: Path`
* `suffix: str = ".txt"`

## DirectorySource.cases
`src/chatddx/inventory/sources.py:DirectorySource.cases`

* ∟`list[Case]`

## DirectorySource.fetch
`src/chatddx/inventory/sources.py:DirectorySource.fetch`

* `id: str`
* ∟`bytes`

Raises:
1. `LookupError`: "case id {id!r} points outside source {self.name!r}"
2. `LookupError`: "no case {id!r} in source {self.name!r}"

## DirectorySource.ids
`src/chatddx/inventory/sources.py:DirectorySource.ids`

* ∟`list[str]`

## EndpointSpec `(Frozen)`
`src/chatddx/inventory/inventory.py:EndpointSpec`

* `engine: Digest`
* `url: HttpUrl`
* `host: str | None = None`
* `max_jobs: int = Field(default=1, ge=1)`
* `credential: str | None = None`
* `canaries: Digest | None = None`
* `execution: Execution = Field(default_factory=Execution)`

Raises:
1. `ValueError`: "the execution sends {self.execution.concurrency} requests at once, and max_jobs takes {self.max_jobs}" (through `EndpointSpec._within_max_jobs`, in a `ValidationError`)

## HostSpec `(Frozen)`
`src/chatddx/inventory/inventory.py:HostSpec`

* `bind: str = "0.0.0.0"`
* `models: dict[Digest, str] = Field(default_factory=dict)`
* `templates: dict[Sha256Hex, str] = Field(default_factory=dict)`

## Inventory `(Frozen)`
`src/chatddx/inventory/inventory.py:Inventory`

* `sources: dict[str, AnySource] = Field(default_factory=dict)`
* `endpoints: dict[str, EndpointSpec] = Field(default_factory=dict)`
* `hosts: dict[str, HostSpec] = Field(default_factory=dict)`
* `cleared: dict[str, tuple[str, ...]] = Field(default_factory=dict)`
* `judges: dict[str, str] = Field(default_factory=dict)`
* `configurations: str | None = None`

Raises:
1. `ValueError`: "source {name!r} is named {source.name!r}" (through `Inventory._sources_named`, in a `ValidationError`)
2. `ValueError`: "endpoint {name!r} names no host {endpoint.host!r}" (through `Inventory._hosts_exist`, in a `ValidationError`)
3. `ValueError`: "cleared names no endpoint {name!r}" (through `Inventory._cleared_exist`, in a `ValidationError`)
4. `ValueError`: "endpoint {name!r} is cleared for no source {', '.join(unknown)}" (through `Inventory._cleared_exist`, in a `ValidationError`)

## Inventory.endpoint
`src/chatddx/inventory/inventory.py:Inventory.endpoint`

* `name: str`
* ∟`EndpointSpec`

Raises:
1. `LookupError`: "no endpoint {name!r} in the inventory"

## Inventory.load `@classmethod`
`src/chatddx/inventory/inventory.py:Inventory.load`

* `path: Path`
* ∟`Self`

Raises:
1. `ValueError`: "{path}: the inventory has only 'include', 'configurations', 'source', 'endpoint', 'host', 'cleared' and 'judge', not {sorted(stray)}"
2. `ValueError`: "{included}: an included inventory has only 'endpoint' and 'host' tables, not {sorted(stray)}"
3. `ValueError`: "{included}: {table} {twice} are in {path} too"

## Inventory.serving
`src/chatddx/inventory/inventory.py:Inventory.serving`

* `digest: str`
* `serves: Callable[[str], str | None] | None = None`
* `called: str | None = None`
* ∟`str`

Raises:
1. `LookupError`: "no endpoint serves {what}, which is ops' to mend"
2. `LookupError`: "{', '.join(named)} serve {what}, which one endpoint should: ops' to mend"

## Inventory.source `[S: Source]`
`src/chatddx/inventory/inventory.py:Inventory.source`

* `name: str | None = None`
* `kind: type[S] = Source`
* ∟`S`

Raises:
1. `LookupError`: f"{len(held)} {word}s ({', '.join(held)}) are in the inventory, " + 'so one must be named' if held else f'no {word} in the inventory'
2. `LookupError`: "no source {name!r} in the inventory"
3. `LookupError`: "source {name!r} isn't a {word}"

## Inventory.takes_typed
`src/chatddx/inventory/inventory.py:Inventory.takes_typed`

* `endpoint: str`
* ∟`bool`

## Source `(Frozen)`
`src/chatddx/inventory/sources.py:Source`

* `name: str`
* `sensitive: bool = True`
* `cleanup: tuple[CleanupOp, ...] = ()`

## start_up
`src/chatddx/inventory/serving.py:start_up`

* `inventory: Inventory`
* `get: Resolver`
* `name: str`
* ∟`StartUp`

Raises:
1. `LookupError`: "endpoint {name!r} serves a {other.kind_name}, not ours to start"
2. `LookupError`: "endpoint {name!r}: {e}" (from `StructuralError`)
3. `LookupError`: "endpoint {name!r} needs a host to start"
4. `LookupError`: "host {endpoint.host!r} doesn't say where it keeps model {engine.model}"
5. `LookupError`: "host {endpoint.host!r} doesn't say where it keeps chat template {engine.chat_template}"

## StartUp `(Frozen)`
`src/chatddx/inventory/serving.py:StartUp`

* `endpoint: str`
* `engine: Digest`
* `closure: str`
* `argv: tuple[str, ...]`
* `env: dict[str, str]`

## World `@dataclass(frozen=True)`
`src/chatddx/inventory/world.py:World`

* `path: Path`
* `inventory: Inventory`
* `engines: tuple[Path, ...] = ()`
* `facts: tuple[Path, ...] = ()`

## World.load `@classmethod`
`src/chatddx/inventory/world.py:World.load`

* `path: Path`
* ∟`Self`

Raises:
1. `LookupError`: "{path} is no World: it holds no inventory.toml"

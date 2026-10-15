# Inventory API

Reference for the `chatddx.inventory` package. It was written from `src/chatddx/inventory/*` and
`docs/inventory.md`. There are no inventory migrations, because the inventory isn't stored. What the inventory is and
why it is shaped this way is in `docs/inventory.md`; this file says what each name accepts, returns and raises.
Factor types it uses (`Digest`, `Sha256Hex`, `Resolver`, `LocalEngine`, `RemoteEngine`, `ModelArtifact`, `Case`,
`Vignette`, `Fingerprint`, …) are in `docs/factors-api.md`. `chatddx import-engine`, which writes inventory files,
is in `docs/inventory.md`, "Importing from a host".

Paths are relative to `src/chatddx/inventory/` unless they start with `src/`, `docs/`, `agents/` or `worlds/`.

## Contents
- [Package](#package)
- [Conventions](#conventions)
- [The file](#the-file)
- [inventory.py](#inventorypy): `EndpointSpec`, `HostSpec`, `Inventory`
- [sources.py](#sourcespy): `Source`, `DatabaseSource`, `ListingSource`, `DirectorySource`
- [serving.py](#servingpy): `StartUp`, `start_up`, `url_of`, `served`, `confirm`
- [world.py](#worldpy): `World`
- [check.py](#checkpy): `check`
- [Worlds](#worlds)
- [Known gaps](#known-gaps)

## Package

`chatddx.inventory` re-exports `LISTEN_FLAGS`, `DatabaseSource`, `DirectorySource`, `EndpointSpec`, `HostSpec`,
`Inventory`, `ListingSource`, `Source`, `StartUp`, `World`, `check`, `confirm`, `served`, `start_up` and `url_of`.
`test/memory.py:MemorySource` is imported by path.

| Module | Builds on |
| --- | --- |
| `sources.py` | `chatddx.factors.{base,cases}` |
| `inventory.py` | `sources.py`, `chatddx.factors.base` |
| `serving.py` | `inventory.py`, `chatddx.factors.{base,engine}` |
| `world.py` | `inventory.py` |
| `check.py` | `inventory.py`, `serving.py`, `chatddx.factors.{base,engine}` |

The package imports no chatddx package but `chatddx.factors`, no third-party package but pydantic, and holds no SQL.
Only `served` and `confirm` connect to anything.

## Conventions

**Models.** Every model derives from `chatddx.factors.base.Frozen`: frozen, `extra="forbid"`. Building one validates
it, so an unknown key in an inventory file is a `ValidationError`.

**Names.** Sources, endpoints and hosts are named by their table keys: `[endpoint."qwen3-8b@pelle"]` is the endpoint
`qwen3-8b@pelle`. Names are free-form.

**Engines.** An endpoint names the engine it serves by digest. The package doesn't hold engines: `serving.py` looks
them up through a `Resolver` (`get`), such as `Registry.get` or `Store.get`.

**Checked late.** Loading checks only what the files show. Whatever needs the engines is checked when `start_up`,
`url_of` or `confirm` is called, or for every entry at once by `check`.

**Errors.**

| Exception | When |
| --- | --- |
| `LookupError` | A source, endpoint or vignette that isn't there; an id that would reach outside a directory source; an endpoint whose engine `get` doesn't know (the resolver's `StructuralError`, turned into `endpoint '<name>': <its message>`), isn't an engine, or can't be started or reached as the inventory says; a server that doesn't list the engine's served name. |
| `ValueError` | `Inventory.load`: a top-level key it doesn't know, a table an included file may not hold, a name defined twice. |
| `pydantic.ValidationError` | An inventory that breaks its own rules: an unknown key, a wrong type, a source named other than its table, an endpoint naming no host, `[cleared]` naming no endpoint or source, `[judge]` binding a judge to no endpoint. Rules written as validators raise `ValueError`, which pydantic wraps. |
| `tomllib.TOMLDecodeError` (a `ValueError`), `OSError` | `Inventory.load` of a file, or an included file, that isn't TOML or can't be read. |
| `OSError` | `served` and `confirm` when the server can't be reached, times out or answers with an HTTP error (`urllib.error.URLError`, `HTTPError`); `DirectorySource` for a directory it can't list or a file it can't read, other than a missing one. |
| `chatddx.factors.base.StructuralError` (a `ValueError`) | `start_up` when the engine's model artifact isn't known to `get` or isn't a model. |

## The file
An inventory file is TOML with the top-level keys `include`, `source`, `endpoint`, `host`, `cleared` and `judge`:

```toml
include = ["endpoints.toml"]          # files whose [endpoint] and [host] tables count too

[source.sample]                       # a DirectorySource named "sample"
path = "vignettes"                    # relative to this file
sensitive = true

[endpoint."qwen3-8b-awq@fake"]        # an EndpointSpec
engine = "sha256:…"
url = "http://127.0.0.1:12099/v1/"
host = "fake"
max_jobs = 4
credential = "QWEN_KEY"

[host.fake]                           # a HostSpec
bind = "127.0.0.1"

[host.fake.models]
"sha256:…" = "Qwen/Qwen3-8B-AWQ"

[host.fake.templates]
"e3b0c442…" = "/dev/null"

[cleared]                             # endpoint -> the sensitive sources it may receive content from
"qwen3-8b-awq@fake" = ["sample"]
```

An included file holds only `endpoint` and `host` tables. Sources, `[cleared]` and `[judge]` are read only from the
inventory's own file.

## inventory.py

### `class EndpointSpec(Frozen)`
Where one engine is served.

| Field | Type | Default |
| --- | --- | --- |
| `engine` | `Digest` | required; the engine served, which is also the name a local engine is served under |
| `url` | `HttpUrl \| None` | `None`; the server's OpenAI-compatible base URL, meant to end in `/v1/` (not checked). A remote engine's endpoint may leave it out. |
| `host` | `str \| None` | `None`; the `[host]` that runs a local engine |
| `max_jobs` | `int`, ≥ 1 | `1`; how many requests it takes at once |
| `credential` | `str \| None` | `None`; the name of the environment variable that holds its secret |
| `canaries` | `Digest \| None` | `None`; a stored canary set every run at the endpoint sends |
| `execution` | `Execution` | `Execution()`; a run's execution unless its request changes the concurrency or the order. Refused when its concurrency is above `max_jobs`: `the execution sends <n> requests at once, and max_jobs takes <m>`. |

### `class HostSpec(Frozen)`
Where a host keeps what its engines pin.

| Field | Type | Default |
| --- | --- | --- |
| `bind` | `str` | `"0.0.0.0"`; the address its servers listen on |
| `models` | `dict[Digest, str]` | `{}`; model artifact digest → location |
| `templates` | `dict[Sha256Hex, str]` | `{}`; chat template SHA-256 → location |

A location is the host's own, a path or a Hugging Face repo ID, and isn't resolved against the inventory file.

### `class Inventory(Frozen)`

| Field | Type | Default |
| --- | --- | --- |
| `sources` | `dict[str, DirectorySource \| DatabaseSource]` | `{}`; by `kind`, `directory` when it has none |
| `endpoints` | `dict[str, EndpointSpec]` | `{}` |
| `hosts` | `dict[str, HostSpec]` | `{}` |
| `cleared` | `dict[str, tuple[str, ...]]` | `{}`; endpoint → sources |
| `judges` | `dict[str, str]` | `{}`; judge → endpoint, from `[judge]` |

A `kind` other than `directory` and `database` is a `ValidationError`.

Building one checks, each a `ValueError` wrapped in `ValidationError`:
- each source's `name` is its key: `source '<key>' is named '<name>'`;
- each endpoint's `host`, when set, is a key of `hosts`: `endpoint '<name>' names no host '<host>'`;
- each key of `cleared` is an endpoint, `cleared names no endpoint '<name>'`, and each of its sources is a source,
- each judge's endpoint is an endpoint: `judge '<name>' is bound to no endpoint '<endpoint>'`.
  `endpoint '<name>' is cleared for no source <names, joined by ", ">`.

| Member | Returns / raises |
| --- | --- |
| `load(path: Path) -> Self` (classmethod) | See below. |
| `source(name: str) -> DirectorySource \| DatabaseSource` | `LookupError("no source '<name>' in the inventory")` when there is none. |
| `listing(name: str \| None = None) -> ListingSource` | The source `name` names, or with no name the only source that lists its vignettes. `LookupError("no source in the inventory lists its vignettes")` or `LookupError("<n> sources list their vignettes (<names>), so one must be named")` without a name; `source`'s `LookupError` for a name it doesn't know; `LookupError("source '<name>' is a database source, whose vignettes are read through the store, not listed")`. |
| `endpoint(name: str) -> EndpointSpec` | `LookupError("no endpoint '<name>' in the inventory")` when there is none. |
| `cleared_for(endpoint: str) -> frozenset[str]` | The sources `[cleared]` lists for the endpoint; empty when it lists none, also for an endpoint that doesn't exist. |

#### `Inventory.load(path: Path) -> Self`
1. Reads `path`. `ValueError("<path>: the inventory has only 'include', 'source', 'endpoint', 'host', 'cleared' and
   'judge', not [<keys>]")` for any other top-level key.
2. For each name in `include`, in order, reads `path.parent / name`. `ValueError("<included>: an included inventory
   has only 'endpoint' and 'host' tables, not [<keys>]")` for any other key, `include` included, so includes don't
   nest. `ValueError("<included>: <table> [<names>] are in <path> too")` for a name already read, from `path` or from
   an earlier include.
3. Names each source after its table, unless the table sets `name` itself, which validation then refuses, and
   resolves its `path` against `path.parent`.
4. Validates the whole. A source table without `path` is a `ValidationError`.

`OSError` or `tomllib.TOMLDecodeError` for a file that can't be read or isn't TOML.

## sources.py

### `class Source(Frozen)`
Where a set of vignettes comes from.

| Member | Description |
| --- | --- |
| `name: str` | Required. The `source` of every case built from it. |
| `sensitive: bool = True` | Whether content from it may only go to endpoints cleared for it (`src/chatddx/runner/gate.py:check`). |
| `cleanup: tuple[CleanupOp, ...] = ()` | The steps its vignettes need, which a run applies unless its request gives its own (`src/chatddx/bench/runs.py:_cleanup_of`). |

### `class DatabaseSource(Source)`
Texts people typed, kept in the store and read through it (`src/chatddx/store/texts.py`). `kind:
Literal["database"] = "database"`. It lists and fetches nothing itself.

### `class ListingSource(Source, ABC)`
A source that lists its vignettes and fetches them by id.

| Member | Description |
| --- | --- |
| `ids() -> list[str]` (abstract) | Its vignettes' ids, sorted. |
| `fetch(id: str) -> bytes` (abstract) | A vignette's raw bytes. `LookupError` when there is none. |
| `cases() -> list[Case]` | One case per id, in `ids()` order: `Case(vignette=Vignette(source=name, id=id, fingerprint=Fingerprint.of(fetch(id))))`, without appendices. Fetches every vignette. |
| `_missing(id) -> LookupError` | `LookupError("no case '<id>' in source '<name>'")`, for subclasses to raise. |

### `class DirectorySource(ListingSource)`

| Field | Type | Default |
| --- | --- | --- |
| `kind` | `Literal["directory"]` | `"directory"` |
| `path` | `Path` | required; resolved by `Inventory.load`, taken as given otherwise |
| `suffix` | `str` | `".txt"` |

| Method | Returns / raises |
| --- | --- |
| `ids()` | The names, without `suffix`, of the entries directly in `path` that are files (`Path.is_file`, which follows symlinks) and end in `suffix`, sorted. |
| `fetch(id)` | The bytes of `path / f"{id}{suffix}"`. `LookupError("case id '<id>' points outside source '<name>'")` for an id holding `/` or `\`, or starting with `.`; `_missing(id)` when the file doesn't exist. Other `OSError`s pass through. |

### `test/memory.py:MemorySource(ListingSource)`
`vignettes: dict[str, bytes]`; `ids()` is its keys, sorted, and `fetch(id)` its value or `_missing(id)`.

## serving.py

### `LISTEN_FLAGS`
`frozenset({"--host", "--port"})`: flags the endpoint decides, which an engine's `argv` may not set for `start_up`.
`src/chatddx/importers/o11n.py` refuses them in a server's extra arguments too.

### `class StartUp(Frozen)`
What the start-up script runs for one endpoint.

| Field | Type | Holds |
| --- | --- | --- |
| `endpoint` | `str` | the endpoint's name |
| `engine` | `Digest` | the engine's digest |
| `closure` | `str` | `engine.runtime.closure`, the runtime to run vLLM from |
| `argv` | `tuple[str, ...]` | vLLM's arguments, below |
| `env` | `dict[str, str]` | `engine.env` |

`argv` is, in order: the model's location on the host, `--revision <model artifact's revision>`,
`--served-model-name <engine digest>`, `--chat-template <template's location on the host>`, `--host <host's bind>`,
`--port <url's port>`, then `engine.argv`. A URL without a port gives its scheme's default, `80` or `443`.

### `start_up(inventory: Inventory, get: Resolver, name: str) -> StartUp`
Raises `LookupError`, checking in this order:
1. `no endpoint '<name>' in the inventory`;
2. `endpoint '<name>': <the resolver's message>` when `get` doesn't know the engine;
3. `endpoint '<name>' serves a <kind>, not ours to start` for anything but a local engine;
4. `endpoint '<name>' needs a url and a host to start`;
5. `host '<host>' doesn't say where it keeps model <digest>`;
6. `host '<host>' doesn't say where it keeps chat template <sha256>`;
7. `engine <digest> sets <flags> in its argv, but endpoint '<name>' decides where it listens` when `flag_names(argv)`
   holds `--host` or `--port`, also as `--port=9000`. An abbreviation such as `--po` isn't caught.

Then it resolves the model artifact for its revision, which raises `StructuralError` when `get` doesn't hold it.
Nothing connects.

### `url_of(inventory: Inventory, get: Resolver, name: str) -> str`
The URL the endpoint's engine is reached at. Raises `LookupError` for a missing endpoint or an engine `get` doesn't
know, as `start_up`, and:

| Engine | Returns | Raises |
| --- | --- | --- |
| remote | `str(url)` | `endpoint '<name>' serves a remote engine but has no url` |
| local | `str(url)` | `endpoint '<name>' serves a local engine but has no url` |
| anything else | | `endpoint '<name>' names a <kind>, not an engine` |

A local engine's host isn't looked at. Nothing connects.

### `served(url: str, timeout: float = 10.0, secret: str | None = None) -> list[str]`
GETs `url` without its trailing `/`, followed by `/models`, and returns `str(entry["id"])` for each entry of the
response's `data` (`[]` when `data` is missing or empty; `"None"` for an entry without `id`). With `secret`, the
request carries `Authorization: Bearer <secret>`, as the runner's calls do.
Raises `OSError` when the server can't be reached, times out or answers with an HTTP error;
`json.JSONDecodeError` for a body that isn't JSON; `AttributeError` for JSON that isn't an object, or an entry that
isn't.

### `confirm(inventory: Inventory, get: Resolver, name: str, timeout: float = 10.0, secret: str | None = None) -> None`
Refuses an endpoint whose server doesn't list the name its engine is served under: a local engine's digest, a remote
engine's `model` (`served_model_name`). In order:
1. `LookupError` for a missing endpoint or an engine `get` doesn't know, as `start_up`;
2. `LookupError("endpoint '<name>' names a <kind>, not an engine")`;
3. `url_of`'s `LookupError`s;
4. `served(url, timeout, secret)` and its errors;
5. `LookupError("endpoint '<name>' at <url> serves <listed names, joined by ", ", or 'nothing'>, not <served
   name>")`.

## `world.py`
`World(path, inventory, engines=(), facts=())`, frozen; `World.load(path)` reads `path / "inventory.toml"` and
takes `engines.toml` and `facts.toml` beside it when they're files;
`LookupError("<path> is no World: it holds no inventory.toml")` without one.

## `check.py`
`check(inventory, get) -> list[Finding]`: the inventory against the engines `get` knows, in the order endpoints,
shared addresses, hosts, clearance. A finding's subject is the endpoint's or the host's name.

| Code | Level | When |
| --- | --- | --- |
| `endpoint.engine_unknown` | warning | `get` doesn't know the endpoint's engine; the resolver's message |
| `endpoint.not_engine` | warning | the endpoint's digest names another kind of component |
| `endpoint.unreachable` | warning | `url_of` refuses it; its message |
| `endpoint.unstartable` | warning | a local engine's endpoint that `start_up` refuses; its message |
| `endpoint.remote_host` | warning | a remote engine's endpoint names a host |
| `endpoint.shared_url` | warning | a local engine's endpoint has the address of an earlier one |
| `host.unpinned` | info | a host says where it keeps a model or a chat template that none of its endpoints' engines pins |
| `cleared.not_sensitive` | info | an endpoint is cleared for a source that isn't sensitive |

## Worlds
A World is a directory with `inventory.toml`, the files it includes, and `engines.toml`, the models and engines its
endpoints serve. `worlds/` holds two:

| World | Sources | Endpoints | Hosts | `[cleared]` |
| --- | --- | --- | --- | --- |
| `worlds/sample/` | `sample`, `path = "vignettes"`, sensitive | `qwen3-8b-awq@fake` (port 12099), `gpt-oss-20b@fake` (port 12100), `max_jobs = 4` | `fake`: `bind = "127.0.0.1"`, models by repo ID, the empty template at `/dev/null` | both endpoints for `sample` |
| `worlds/kompismoln/` | `sample`, `path = "../sample/vignettes"`, sensitive | from `endpoints.toml`: `qwen3-8b@pelle` (`max_jobs = 1`), `gpt-oss-20b@malborg` (`max_jobs = 4`) | from `endpoints.toml`: `pelle`, `malborg`, `bind = "::"` | both endpoints for `sample` |

`endpoints.toml` and `engines.toml` in `worlds/kompismoln/` are what `chatddx import-engine` writes.

`src/chatddx/test/test_worlds.py:test_each_endpoint_serves_the_engine_planned_under_its_name` asserts the check finds
nothing in each World in the repository against its plan.

## Known gaps
From `docs/inventory.md`, "Open design issues":
- The runner and the engine import don't run `check`: they check an entry when they use it.
- Hosts don't start engines from the start-up; only the fake vLLM is started from one.
- Endpoint names are only a convention, and renaming one drops its clearance.
- `max_jobs` holds per run, not per endpoint.

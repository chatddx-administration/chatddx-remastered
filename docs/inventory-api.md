# Inventory API

Reference for the `chatddx.inventory` package. It was written from `src/chatddx/inventory/*` and
`docs/inventory.md`. There are no inventory migrations, because the inventory isn't stored. What the inventory is and
why it is shaped this way is in `docs/inventory.md`; this file says what each name accepts, returns and raises.
Factor types it uses (`Digest`, `Sha256Hex`, `Resolver`, `LocalEngine`, `RemoteEngine`, `LocalModel`, `Case`,
`Vignette`, `Fingerprint`, …) are in `docs/factors-api.md`. `chatddx import-engine`, which writes inventory files,
is in `docs/inventory.md`, "Importing from a host".

Paths are relative to `src/chatddx/inventory/` unless they start with `src/`, `docs/`, `agents/` or `worlds/`.

## Contents
- [Package](#package)
- [Conventions](#conventions)
- [The file](#the-file)
- [inventory.py](#inventorypy): `EndpointSpec`, `HostSpec`, `Inventory`
- [sources.py](#sourcespy): `Source`, `DatabaseSource`, `DirectorySource`
- [serving.py](#servingpy): `StartUp`, `start_up`
- [world.py](#worldpy): `World`
- [check.py](#checkpy): `check`
- [Worlds](#worlds)
- [Known gaps](#known-gaps)

## Package

`chatddx.inventory` re-exports `DatabaseSource`, `DirectorySource`, `EndpointSpec`, `HostSpec`, `Inventory`, `Source`,
`StartUp`, `World`, `check` and `start_up`.

| Module | Builds on |
| --- | --- |
| `sources.py` | `chatddx.factors.{base,cases}` |
| `inventory.py` | `sources.py`, `chatddx.factors.base` |
| `serving.py` | `inventory.py`, `chatddx.factors.{base,engine}` |
| `world.py` | `inventory.py` |
| `check.py` | `inventory.py`, `serving.py`, `chatddx.factors.{base,engine}` |

The package imports no chatddx package but `chatddx.factors`, no third-party package but pydantic, and holds no SQL.
Nothing in it connects: the runner's gate confirms an endpoint (`src/chatddx/runner/gate.py:admit`).

## Conventions

**Models.** Every model derives from `chatddx.factors.base.Frozen`: frozen, `extra="forbid"`. Building one validates
it, so an unknown key in an inventory file is a `ValidationError`.

**Names.** Sources, endpoints and hosts are named by their table keys: `[endpoint."qwen3-8b@pelle"]` is the endpoint
`qwen3-8b@pelle`. Names are free-form.

**Engines.** An endpoint names the engine it serves by digest. The package doesn't hold engines: `serving.py` looks
them up through a `Resolver` (`get`), such as `Registry.get` or `Store.get`.

**Checked late.** Loading checks only what the files show. Whatever needs the engines is checked when `start_up` is
called, or for every entry at once by `check`.

**Errors.**

| Exception | When |
| --- | --- |
| `ValueError` | `Inventory.load`: a top-level key it doesn't know, a table an included file may not hold, a name defined twice. |
| `pydantic.ValidationError` | An inventory that breaks its own rules: an unknown key, a wrong type, a source named other than its table, an endpoint without `url`, an endpoint naming no host, `[cleared]` naming no endpoint or source, `[judge]` binding a judge to no endpoint, `configurations` naming no endpoint. Rules written as validators raise `ValueError`, which pydantic wraps. |
| `tomllib.TOMLDecodeError` (a `ValueError`), `OSError` | `Inventory.load` of a file, or an included file, that isn't TOML or can't be read. |
| `OSError` | `DirectorySource` for a directory it can't list or a file it can't read, other than a missing one. |

## The file
An inventory file is TOML with the top-level keys `include`, `configurations`, `source`, `endpoint`, `host`, `cleared`
and `judge`:

```toml
include = ["endpoints.toml"]          # files whose [endpoint] and [host] tables count too
configurations = "qwen3-8b-awq@fake"  # the endpoint whose engine's model a data set's configurations are made for

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

An included file holds only `endpoint` and `host` tables. Sources, `configurations`, `[cleared]` and `[judge]` are
read only from the inventory's own file.

## inventory.py

### `class EndpointSpec(Frozen)`
Where one engine is served.

| Field | Type | Default |
| --- | --- | --- |
| `engine` | `Digest` | required; the engine served, which is also the name a local engine is served under |
| `url` | `HttpUrl` | required; the server's OpenAI-compatible base URL, meant to end in `/v1/` (not checked) |
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
| `configurations` | `str \| None` | `None`; the endpoint whose engine a data set's configurations are made for (`src/chatddx/curation/plan.py:plan_factors`) |

A `kind` other than `directory` and `database` is a `ValidationError`.

Building one checks, each a `ValueError` wrapped in `ValidationError`:
- each source's `name` is its key: `source '<key>' is named '<name>'`;
- each endpoint's `host`, when set, is a key of `hosts`: `endpoint '<name>' names no host '<host>'`;
- each key of `cleared` is an endpoint, `cleared names no endpoint '<name>'`, and each of its sources is a source,
  `endpoint '<name>' is cleared for no source <names, joined by ", ">`;
- each judge's endpoint is an endpoint: `judge '<name>' is bound to no endpoint '<endpoint>'`;
- `configurations`, when set, is an endpoint: `configurations are made for no endpoint '<name>'`.

| Member | Returns / raises |
| --- | --- |
| `load(path: Path) -> Self` (classmethod) | See below. |
| `source(name: str \| None = None, kind: type[S] = Source) -> S` | The source `name` names, or with no name the only source of `kind`. `LookupError("no source '<name>' in the inventory")`, and `LookupError("source '<name>' isn't a <kind> source")` for one of another kind; with no name, `LookupError("no <kind> source in the inventory")` or `LookupError("<n> <kind> sources (<names>) are in the inventory, so one must be named")`. `<kind> source` is `source` for `Source`. init-data and repair-data ask for a `DirectorySource`, `Bench.type_case` and `Bench.takes_typed` for a `DatabaseSource`. |
| `endpoint(name: str) -> EndpointSpec` | `LookupError("no endpoint '<name>' in the inventory")` when there is none. |
| `serving(digest: str, serves: Callable[[str], str \| None] \| None = None, called: str \| None = None) -> str` | The one endpoint serving `digest`: whose engine is `digest`, or, given `serves`, whose engine `serves` maps to `digest` (`src/chatddx/bench/seen.py:Seen.at` maps an engine to its model). `LookupError("no endpoint serves <what>")` when none does, `LookupError("<names, joined by ", "> serve <what>; name the one to use")` when several do; `<what>` is `called`, or `engine <digest>`. `src/chatddx/runner/score.py:judge_at` turns it into `gate.Refused`, and `Seen.at` into a `ValueError`. |

#### `Inventory.load(path: Path) -> Self`
1. Reads `path`. `ValueError("<path>: the inventory has only 'include', 'configurations', 'source', 'endpoint',
   'host', 'cleared' and 'judge', not [<keys>]")` for any other top-level key.
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

### `class DirectorySource(ListingSource)`

| Field | Type | Default |
| --- | --- | --- |
| `kind` | `Literal["directory"]` | `"directory"` |
| `path` | `Path` | required; resolved by `Inventory.load`, taken as given otherwise |
| `suffix` | `str` | `".txt"` |

| Method | Returns / raises |
| --- | --- |
| `cases() -> list[Case]` | One case per id, in `ids()` order: `Case(vignette=Vignette(source=name, id=id, fingerprint=Fingerprint.of(fetch(id))))`, without appendices. Fetches every vignette. |
| `ids()` | The names, without `suffix`, of the entries directly in `path` that are files (`Path.is_file`, which follows symlinks) and end in `suffix`, sorted. |
| `fetch(id)` | The bytes of `path / f"{id}{suffix}"`. `LookupError("case id '<id>' points outside source '<name>'")` for an id holding `/` or `\`, or starting with `.`; `LookupError("no case '<id>' in source '<name>'")` when the file doesn't exist. Other `OSError`s pass through. |

## serving.py

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
4. `endpoint '<name>': <the resolver's message>` when `get` doesn't hold the engine's model artifact, or it isn't a
   local model;
5. `endpoint '<name>' needs a host to start`;
6. `host '<host>' doesn't say where it keeps model <digest>`;
7. `host '<host>' doesn't say where it keeps chat template <sha256>`.

Nothing connects.

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
| `endpoint.unstartable` | warning | a local engine's endpoint that `start_up` refuses; its message |
| `endpoint.remote_host` | warning | a remote engine's endpoint names a host |
| `endpoint.shared_url` | warning | a local engine's endpoint has the address of an earlier one |
| `host.unpinned` | info | a host says where it keeps a model or a chat template that none of its endpoints' engines pins |
| `cleared.not_sensitive` | info | an endpoint is cleared for a source that isn't sensitive |

## Worlds
A World is a directory with `inventory.toml`, the files it includes, and `engines.toml`, the models and engines its
endpoints serve. `worlds/` holds three:

| World | Sources | Endpoints | Hosts | `[cleared]` |
| --- | --- | --- | --- | --- |
| `worlds/sample/` | `sample`, `path = "vignettes"`, sensitive; `typed`, a database source | `qwen3-8b-awq@fake` (port 12099) and `gpt-oss-20b@fake` (port 12100), `max_jobs = 4`; `mistral-small@remote` (port 12101), `max_jobs = 2`, `credential = "CHATDDX_SAMPLE_KEY"` | `fake`: `bind = "127.0.0.1"`, models by repo ID, the empty template at `/dev/null` | the fakes for `sample` and `typed`, `mistral-small@remote` for `sample` |
| `worlds/kompismoln/` | `sample`, `path = "../sample/vignettes"`, sensitive | from `endpoints.toml`: `qwen3-8b@pelle` (`max_jobs = 1`), `gpt-oss-20b@malborg` (`max_jobs = 4`) | from `endpoints.toml`: `pelle`, `malborg`, `bind = "::"` | both endpoints for `sample` |
| `worlds/test/` | `test`, `path = "vignettes"`, sensitive; `typed`, a database source | `qwen3@fake` (port 12201) and `gpt-oss@fake` (port 12203), `max_jobs = 4`; `qwen3-bare@fake` (port 12202); `mistral@fake` (port 12204), `max_jobs = 2`; `unknown@remote` at `https://remote.invalid/v1/`, `credential = "CHATDDX_TEST_REMOTE"` | `fake`: `bind = "127.0.0.1"`, models by repo ID, `test/mistral-7b` among them, the empty template at `/dev/null` | `qwen3@fake`, `gpt-oss@fake` and `mistral@fake` for `test` and `typed`, `qwen3-bare@fake` for `test`, `unknown@remote` for nothing |

`configurations` is `qwen3-8b-awq@fake` in `worlds/sample/`, `qwen3-8b@pelle` in `worlds/kompismoln/`, and
`qwen3@fake` in `worlds/test/`.

`src/chatddx/test/test_worlds.py:test_each_endpoint_serves_the_engine_planned_under_its_name` asserts the check finds
nothing in each World in the repository against its plan.

## Known gaps
From `docs/inventory.md`, "Open design issues":
- The runner and the engine import don't run `check`: they check an entry when they use it.
- Hosts don't start engines from the start-up; only the fake vLLM is started from one.
- Endpoint names are only a convention, and renaming one drops its clearance.
- `max_jobs` holds per run, not per endpoint.

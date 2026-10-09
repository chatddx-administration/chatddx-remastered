# Inventory API

Reference for the `chatddx.inventory` package, as of e9bdca7. It was written from `src/chatddx/inventory/*` and
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
- [sources.py](#sourcespy): `Source`, `DirectorySource`
- [serving.py](#servingpy): `StartUp`, `start_up`, `url_of`, `served`, `confirm`
- [Worlds](#worlds)
- [Callers](#callers)
- [Known gaps](#known-gaps)
- [Beyond docs/inventory.md](#beyond-docsinventorymd)

## Package

`chatddx.inventory` re-exports `LISTEN_FLAGS`, `DirectorySource`, `EndpointSpec`, `HostSpec`, `Inventory`, `Source`,
`StartUp`, `confirm`, `served`, `start_up` and `url_of`. `test/memory.py:MemorySource` is imported by path.

| Module | Builds on |
| --- | --- |
| `sources.py` | `chatddx.factors.{base,cases}` |
| `inventory.py` | `sources.py`, `chatddx.factors.base` |
| `serving.py` | `inventory.py`, `chatddx.factors.{base,engine}` |

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
`url_of` or `confirm` is called.

**Errors.**

| Exception | When |
| --- | --- |
| `LookupError` | A source, endpoint or vignette that isn't there; an id that would reach outside a directory source; an endpoint whose engine `get` doesn't know (the resolver's `StructuralError`, turned into `endpoint '<name>': <its message>`), isn't an engine, or can't be started or reached as the inventory says; a server that doesn't list the engine's served name. |
| `ValueError` | `Inventory.load`: a top-level key it doesn't know, a table an included file may not hold, a name defined twice. |
| `pydantic.ValidationError` | An inventory that breaks its own rules: an unknown key, a wrong type, a source named other than its table, an endpoint naming no host, `[cleared]` naming no endpoint or source. Rules written as validators raise `ValueError`, which pydantic wraps. |
| `tomllib.TOMLDecodeError` (a `ValueError`), `OSError` | `Inventory.load` of a file, or an included file, that isn't TOML or can't be read. |
| `OSError` | `served` and `confirm` when the server can't be reached, times out or answers with an HTTP error (`urllib.error.URLError`, `HTTPError`); `DirectorySource` for a directory it can't list or a file it can't read, other than a missing one. |
| `chatddx.factors.base.StructuralError` (a `ValueError`) | `start_up` when the engine's model artifact isn't known to `get` or isn't a model. |

## The file
An inventory file is TOML with the top-level keys `include`, `source`, `endpoint`, `host` and `cleared`:

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

An included file holds only `endpoint` and `host` tables. Sources and `[cleared]` are read only from the inventory's
own file.

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
| `sources` | `dict[str, DirectorySource]` | `{}` |
| `endpoints` | `dict[str, EndpointSpec]` | `{}` |
| `hosts` | `dict[str, HostSpec]` | `{}` |
| `cleared` | `dict[str, tuple[str, ...]]` | `{}`; endpoint → sources |

`sources` takes only `DirectorySource`: a `kind` other than `directory` is a `ValidationError`.

Building one checks, each a `ValueError` wrapped in `ValidationError`:
- each source's `name` is its key: `source '<key>' is named '<name>'`;
- each endpoint's `host`, when set, is a key of `hosts`: `endpoint '<name>' names no host '<host>'`;
- each key of `cleared` is an endpoint, `cleared names no endpoint '<name>'`, and each of its sources is a source,
  `endpoint '<name>' is cleared for no source <names, joined by ", ">`.

| Member | Returns / raises |
| --- | --- |
| `load(path: Path) -> Self` (classmethod) | See below. |
| `source(name: str) -> Source` | `LookupError("no source '<name>' in the inventory")` when there is none. |
| `endpoint(name: str) -> EndpointSpec` | `LookupError("no endpoint '<name>' in the inventory")` when there is none. |
| `cleared_for(endpoint: str) -> frozenset[str]` | The sources `[cleared]` lists for the endpoint; empty when it lists none, also for an endpoint that doesn't exist. |

#### `Inventory.load(path: Path) -> Self`
1. Reads `path`. `ValueError("<path>: the inventory has only 'include', 'source', 'endpoint', 'host' and 'cleared',
   not [<keys>]")` for any other top-level key.
2. For each name in `include`, in order, reads `path.parent / name`. `ValueError("<included>: an included inventory
   has only 'endpoint' and 'host' tables, not [<keys>]")` for any other key, `include` included, so includes don't
   nest. `ValueError("<included>: <table> [<names>] are in <path> too")` for a name already read, from `path` or from
   an earlier include.
3. Names each source after its table, unless the table sets `name` itself, which validation then refuses, and
   resolves its `path` against `path.parent`.
4. Validates the whole. A source table without `path` is a `ValidationError`.

`OSError` or `tomllib.TOMLDecodeError` for a file that can't be read or isn't TOML.

## sources.py

### `class Source(Frozen, ABC)`
Where a set of vignettes is fetched from, by id.

| Member | Description |
| --- | --- |
| `name: str` | Required. The `source` of every case built from it. |
| `sensitive: bool = True` | Whether content from it may only go to endpoints cleared for it (`src/chatddx/runner/gate.py:check`). |
| `ids() -> list[str]` (abstract) | Its vignettes' ids, sorted. |
| `fetch(id: str) -> bytes` (abstract) | A vignette's raw bytes. `LookupError` when there is none. |
| `cases() -> list[Case]` | One case per id, in `ids()` order: `Case(vignette=Vignette(source=name, id=id, fingerprint=Fingerprint.of(fetch(id))))`, without appendices. Fetches every vignette. |
| `_missing(id) -> LookupError` | `LookupError("no case '<id>' in source '<name>'")`, for subclasses to raise. |

### `class DirectorySource(Source)`

| Field | Type | Default |
| --- | --- | --- |
| `kind` | `Literal["directory"]` | `"directory"` |
| `path` | `Path` | required; resolved by `Inventory.load`, taken as given otherwise |
| `suffix` | `str` | `".txt"` |

| Method | Returns / raises |
| --- | --- |
| `ids()` | The names, without `suffix`, of the entries directly in `path` that are files (`Path.is_file`, which follows symlinks) and end in `suffix`, sorted. |
| `fetch(id)` | The bytes of `path / f"{id}{suffix}"`. `LookupError("case id '<id>' points outside source '<name>'")` for an id holding `/` or `\`, or starting with `.`; `_missing(id)` when the file doesn't exist. Other `OSError`s pass through. |

### `test/memory.py:MemorySource(Source)`
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
| remote | `str(base_url)` | `endpoint '<name>' has url <url>, but its remote engine's base_url is <base_url>` when the endpoint gives another URL |
| local | `str(url)` | `endpoint '<name>' serves a local engine but has no url` |
| anything else | | `endpoint '<name>' names a <kind>, not an engine` |

A local engine's host isn't looked at. Nothing connects.

### `served(url: str, timeout: float = 10.0) -> list[str]`
GETs `url` without its trailing `/`, followed by `/models`, and returns `str(entry["id"])` for each entry of the
response's `data` (`[]` when `data` is missing or empty; `"None"` for an entry without `id`). It sends no credential.
Raises `OSError` when the server can't be reached, times out or answers with an HTTP error;
`json.JSONDecodeError` for a body that isn't JSON; `AttributeError` for JSON that isn't an object, or an entry that
isn't.

### `confirm(inventory: Inventory, get: Resolver, name: str, timeout: float = 10.0) -> None`
Refuses an endpoint whose server doesn't list the name its engine is served under: a local engine's digest, a remote
engine's `model` (`served_model_name`). In order:
1. `LookupError` for a missing endpoint or an engine `get` doesn't know, as `start_up`;
2. `LookupError("endpoint '<name>' names a <kind>, not an engine")`;
3. `url_of`'s `LookupError`s;
4. `served(url, timeout)` and its errors;
5. `LookupError("endpoint '<name>' at <url> serves <listed names, joined by ", ", or 'nothing'>, not <served
   name>")`.

## Worlds
A World is a directory with `inventory.toml`, the files it includes, and `factors.toml`, the models and engines its
endpoints serve. `worlds/` holds two:

| World | Sources | Endpoints | Hosts | `[cleared]` |
| --- | --- | --- | --- | --- |
| `worlds/sample/` | `sample`, `path = "vignettes"`, sensitive | `qwen3-8b-awq@fake` (port 12099), `gpt-oss-20b@fake` (port 12100), `max_jobs = 4` | `fake`: `bind = "127.0.0.1"`, models by repo ID, the empty template at `/dev/null` | both endpoints for `sample` |
| `worlds/kompismoln/` | `sample`, `path = "../sample/vignettes"`, sensitive | from `endpoints.toml`: `qwen3-8b@pelle` (`max_jobs = 1`), `gpt-oss-20b@malborg` (`max_jobs = 4`) | from `endpoints.toml`: `pelle`, `malborg`, `bind = "::"` | none |

`endpoints.toml` and `factors.toml` in `worlds/kompismoln/` are what `chatddx import-engine` writes.
`test/test_serving.py:test_the_sample_world_binds_each_fake_engine_the_sample_seeds` fails when the sample World's
endpoints don't match the engines the sample seeds.

## Callers
- `src/chatddx/cli.py:_init_data`: `Inventory.load(--world)` and `source(--source)`; without `--world`, a
  `DirectorySource` over `--vignettes`.
- `src/chatddx/seed/world.py:endpoints`: one line per endpoint, after init-data seeds. An endpoint whose engine the
  data doesn't seed is reported as such; otherwise `url_of`, and `start_up` for a local engine, and their
  `LookupError` is the line.
- `src/chatddx/runner/gate.py:check`: refuses a run unless the endpoint exists, the trial's sources exist, the
  endpoint serves the trial's engine, it is `cleared_for` every sensitive source, the skeleton has no tools when a
  source is sensitive, and `confirm` passes; `LookupError` and `OSError` become `Refused`. `gate.py:secret` reads the
  `credential` variable and refuses when it is unset or empty.
- `src/chatddx/runner/run.py`: refuses an execution whose `concurrency` is above `max_jobs` (`ValueError`), records
  the endpoint's name and `url_of` in `RunStarted.endpoint`, and fetches each vignette through `source(...).fetch`;
  `LookupError` there is a `case.unreadable` finding.
- `src/chatddx/importers/o11n.py`: builds `EndpointSpec` and `HostSpec` tables and refuses `LISTEN_FLAGS`.

## Known gaps
From `docs/inventory.md`, "Open design issues":
- Everything that needs the engines is checked only when `start_up`, `url_of` or `confirm` is called, one entry at a
  time; there is no `check(inventory, get)` returning findings.
- Nothing checks two endpoints at one URL, a remote engine's endpoint that names a host, host locations no engine
  pins, or a `[cleared]` entry for a source that isn't sensitive.
- Hosts don't start engines from the start-up; only the fake vLLM is started from one.
- Nothing locates a deployment's World; it is passed in each time.
- Endpoint names are only a convention, and renaming one drops its clearance.
- `max_jobs` holds per run, not per endpoint.

Also, proposed as an amendment to `docs/inventory.md`: a new kind of source has to be added to the type of
`Inventory.sources`.

## Beyond docs/inventory.md
Behavior described here that `docs/inventory.md` doesn't state:
- `Inventory.sources` takes only `DirectorySource`, so a new kind of source is also a change to that field. Proposed
  as an amendment there.
- `served`, and so `confirm` and the runner's gate, send no credential, so a server that wants one for `/v1/models`
  answers with an HTTP error and the endpoint is refused.
- `served` and `confirm` raise `json.JSONDecodeError` or `AttributeError`, not `OSError`, for a server whose answer
  isn't a JSON object; the runner's gate doesn't catch them.
- `start_up` raises `StructuralError` when the engine's model artifact isn't held by `get`.
- `start_up` doesn't catch abbreviated `--host` or `--port` flags.
- A URL without a port starts the server on its scheme's default port.
- `DirectorySource.ids` can list an id starting with `.` that `fetch` refuses, so `cases` raises; and it follows
  symlinks, also to files outside the directory.
- `DirectorySource.fetch` passes through `OSError`s other than a missing file.
- The duplicate-name error names the inventory's own file, also when the clash is between two included files.
- `cleared_for` gives an empty set for an endpoint that doesn't exist.

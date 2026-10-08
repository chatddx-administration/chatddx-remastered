# Inventory

Factors say what something is: an engine, a model, a case. The inventory says where to find it. It is a set of files
that ops write. They say which directory holds a source's vignettes, at which URL an engine is served, and where a
host keeps the model files and chat template an engine pins. Until clearance has a pipeline of its own, the
inventory also says which endpoints may receive content from which sensitive sources.

The inventory is not a factor (`docs/factors.md`, "Not factors"). No component refers to an inventory entry, so
moving a model's files or an engine's server changes no digest. Two things that sound like locations are factors,
though:
- a source's name, which every case built from it carries;
- a remote engine's `base_url`.

The inventory isn't stored in the database, and its history is git's. A run's started row records the endpoint the
run used, by name and URL (`docs/ledger.md`, "RunStarted").

Code paths are relative to `src/chatddx/inventory/` unless they start with `src/` or `docs/`. The package builds on
`chatddx.factors` and nothing else, and `chatddx.inventory` exports the public names. It has three modules:
- `inventory.py`: the file ("The file", "Sources", "Endpoints", "Hosts", "Clearance");
- `sources.py`: reading vignettes ("Sources");
- `serving.py`: joining endpoints and hosts with the engines they serve ("Starting and reaching an engine").

Its callers are `chatddx init-data`, `chatddx import-engine` (`src/chatddx/importers/o11n.py`, "Importing from a
host") and the runner (`src/chatddx/runner/gate.py`).

## The file
An inventory is a TOML file, read by `inventory.py:Inventory.load`. Its top-level keys are `include`, `source`,
`endpoint`, `host` and `cleared`, and it refuses any other key. Names are table keys, so `[endpoint.<name>]` names
an endpoint. Paths in the file are relative to the file's directory (`Inventory.root`). Locations that a host gives
for its own files are not (see "Hosts").

### Includes
`include` lists files whose `[endpoint]` and `[host]` tables count as this inventory's too. Each path is relative
to the including file. An included file may hold only those two tables, so it can't include another file. A name
defined twice, whether in the inventory and an included file or in two included files, is refused.

Includes keep what `chatddx import-engine` writes apart from what people write, so an import can rewrite its file
whole. Sources and `[cleared]` are read only from the inventory's own file, so importing again can't add a source or
clear an endpoint.

### What loading checks
Loading checks only what the files themselves show:
- every endpoint's `host` is a `[host]`;
- `[cleared]` names endpoints and sources that exist.

Whatever needs the engines is checked when an entry is used: whether a digest names an engine, and whether a host
says where the engine's model and template are (see "Starting and reaching an engine" and "Open design issues").

### The Worlds in this repository
- `sample-world/inventory.toml` is the sample World. It has:
  - `[source.sample]`, for the vignettes in `sample-world/vignettes/`;
  - an endpoint for each fake engine, on 127.0.0.1;
  - the fake host;
  - a `[cleared]` table that clears both endpoints for the sample.

  `test/test_serving.py:test_the_sample_world_binds_each_fake_engine_the_sample_seeds` fails when the sample's
  engines change and their endpoints don't.
- `world/inventory.toml` is the World of the hosts pelle and malborg. It is hand-written: the sample's source again,
  and `include = ["endpoints.toml"]`, the file `chatddx import-engine` writes from the hosts' reports. It has no
  `[cleared]` table, so the runner refuses to send the sample to its endpoints.

## Sources
A `[source.<name>]` table locates vignettes (`inventory.py:DirectorySourceSpec`):
- `kind`: `directory`, the only kind and the default;
- `path`: the directory;
- `suffix`: the vignette files' suffix, `.txt` by default;
- `sensitive`: true by default. What it requires is `docs/clearance.md`'s ("Sensitive sources").

`Inventory.source(name)` gives the source as a `sources.py:Source`. A source:
- `ids()` lists its vignettes' ids, sorted. In a directory, an id is a file's name without the suffix, and only
  files directly in the directory that end in the suffix count.
- `fetch(id)` gives a vignette's raw bytes, and raises `LookupError` when there's no such vignette. A directory
  source also refuses an id that could reach outside it: one holding `/` or `\`, or starting with `.`.
- `cases()` builds one case for each vignette, without appendices, with the fingerprint of the raw bytes
  (`docs/factors.md`, "Case").

What happens to the bytes next is `prepare_case`'s (`docs/factors.md`, "Preparing a case").

A source's name is the `source` of every case built from it, so it is part of their digests. Renaming a source
makes new cases; moving its directory changes nothing. `chatddx init-data --world FILE --source NAME` seeds the
cases of the named source.

Each kind of source is two classes: a spec in the file (`inventory.py:DirectorySourceSpec`) and a class that reads
vignettes (`sources.py:DirectorySource`). Tests stand in for a source with `test/memory.py:MemorySource`.

## Endpoints
An `[endpoint.<name>]` table says where an engine is served (`inventory.py:EndpointSpec`):
- `engine`: the engine's digest;
- `url`: the server's OpenAI-compatible base URL, ending in `/v1/`;
- `host`: the `[host]` that runs it, for a local engine;
- `max_jobs`: how many requests it takes at once, 1 by default;
- `credential`: the name of the environment variable that holds the endpoint's secret.

An endpoint serves one engine. A local engine is served under its digest (`docs/factors.md`, "Local engine"), so the
endpoint names the very engine the server answers as. Changing the engine changes its digest, so the endpoint has to
be edited too. A local engine's endpoint needs a `url` to be reached, and a `host` too to be started.

A remote engine's `base_url` is part of its digest, so its endpoint may leave `url` out. If it gives one, it must be
the same URL. The endpoint adds what isn't part of the engine: the secret and the capacity.

Endpoint names are free-form. `chatddx import-engine` names them `<server>@<host>`, such as `qwen3-8b@pelle`, and
the sample World's names follow that pattern (`qwen3-8b-awq@fake`). A run records the name, and `[cleared]` keys on
it.

The runner reads the variable that `credential` names and sends its value as a bearer token. It refuses to run when
the variable isn't set (`src/chatddx/runner/gate.py:secret`). The secret itself never appears in the inventory or
the ledger.

`chatddx import-engine` takes `max_jobs` from the server's `--max-num-seqs`. Nothing reads it yet, because the
runner sends one request at a time.

## Hosts
A `[host.<name>]` table says where a host keeps what its engines pin (`inventory.py:HostSpec`):
- `bind`: the address its servers listen on, `0.0.0.0` by default;
- `models`: maps a model artifact's digest to its location;
- `templates`: maps a chat template's SHA-256 to its location.

A local engine pins its model and chat template by hash (`docs/factors.md`, "Model artifact" and "Local engine"),
and its host says where those files are. Engines on one host share the host's table. A location is the host's own,
written the way its start-up reads it: a path, or a Hugging Face repo ID. It isn't resolved against the inventory
file.

The sample's fake host keeps its models under their repo IDs, which the fake vLLM takes as a model name. Its one
template, the empty one, is at `/dev/null`.

## Clearance
The `[cleared]` table lists, for each endpoint, the sources it may receive case-derived content from:
`"qwen3-8b-awq@fake" = ["sample"]`. `Inventory.cleared_for(endpoint)` reads it. The table stands in until clearance
has a database grant, and what it permits is `docs/clearance.md`'s ("Vetted endpoints"). It is read only from the
inventory's own file (see "Includes"). Clearing an endpoint is a person's statement, so no command writes the table.

## Starting and reaching an engine
`serving.py` joins an endpoint with the engine it serves, which it looks up through a resolver (`get`). For a local
engine it also uses the host that runs it. Each function raises `LookupError` when the inventory or the engine falls
short.

### The start-up
`start_up(inventory, get, name)` gives the `StartUp` for a local engine's endpoint: what the start-up script runs.
It holds:
- `argv`, vLLM's arguments, in this order:
  - the model's location on the host;
  - `--revision`, from the model artifact;
  - `--served-model-name`, the engine's digest;
  - `--chat-template`, the template's location on the host;
  - `--host`, the host's `bind`;
  - `--port`, the URL's port;
  - then the engine's own `argv`.
- `env`, the engine's;
- `closure`, the runtime to run vLLM from (`chatddx fake-vllm` for the fake engines).

It refuses:
- a remote engine, which isn't ours to start;
- an endpoint without `url` or `host`;
- a host that doesn't say where it keeps the model or the template;
- an engine whose `argv` sets `--host` or `--port` (`LISTEN_FLAGS`). The endpoint decides where a server listens,
  just as the start-up owns the flags in `OWNED_FLAGS` (`docs/factors.md`, "Local engine").

The fake vLLM can be started from a start-up: `chatddx fake-vllm` with its `argv` serves the endpoint's engine
(`test/test_serving.py`; `docs/vllm.md`, "The fake vLLM").

### Reaching an engine
- `url_of(inventory, get, name)`: an endpoint's URL; for a remote engine, its `base_url`.
- `served(url)`: the model names that a server's `/v1/models` lists.
- `confirm(inventory, get, name)`: refuses an endpoint whose `/v1/models` doesn't list the name its engine is
  served under, which is a local engine's digest or a remote engine's model. A server that can't be reached raises
  `OSError`. The runner confirms an endpoint before it sends case-derived content (`docs/clearance.md`, "Vetted
  endpoints").

With `--world`, `chatddx init-data` ends with a line per endpoint: its URL and the seeded engine it serves, or why it
can't be started or reached. It finds this out from `start_up` and `url_of`, without connecting.

## Importing from a host
The hosts run vLLM through o11n (`o11n.vllm`, Kompismoln/o11n `nixos/vllm.nix`). Each server runs in a NixOS
container that is configured outside the rig. So an engine's values come from its host, not from people:
`chatddx import-engine` reads each host's report and writes the factors and the inventory entries together
(`src/chatddx/importers/o11n.py`).

`chatddx import-engine REPORT … [--server NAME …] [--endpoint-host HOST] --factors FILE --endpoints FILE`:
- `REPORT` is a host's `o11n.vllm.report/1` (Kompismoln/o11n `nixos/vllm-report.py`), given as its URL (such as
  `http://pelle.km:12008/`), a file, or `-` for stdin.
- For each server, `imported` gives the model artifact, the local engine, the endpoint, and where the host keeps
  the model (the snapshot's directory) and the template. All are named `<server>@<host>`, after the report's
  hostname.
- `--factors` gets the `[model]` and `[local_engine]` tables, for init-data's `--factors`. `--endpoints` gets the
  `[endpoint]` and `[host]` tables, for an inventory's `include`. Both files are rewritten whole, so to change them,
  import again rather than edit.

The import takes:
- the endpoint's URL from the report's URL, or from `--endpoint-host`, with the server's port;
- the host's `bind` from the server's;
- `max_jobs` from `--max-num-seqs`;
- the engine's `env`, minus the variables o11n sets on every server to find the model, the GPU and CUDA (`HOST_ENV`).

It refuses:
- a server on several GPUs, since `Hardware` has no GPU count;
- a model that isn't a Hugging Face repo at a revision;
- a part of the report that couldn't be gathered;
- extra arguments that set `--host` or `--port`;
- whatever `LocalEngine` refuses;
- two servers at one URL, or two servers on one host that bind to different addresses.

It prints findings to stderr: the model's and the engine's lints (`docs/factors.md`, "Lints"), `check_chat_template`
on the template the report gives, and:
- `engine.chat_template_unused` (info): vLLM renders the model with Harmony and doesn't read the template;
- `engine.harmony_date`: such an engine has no `VLLM_SYSTEM_START_DATE` in its env, so every prompt holds the
  current date;
- `engine.chat_template_unread` (info): the report has no template text, so the template wasn't checked;
- `engine.chat_template_not_the_model_s` (info): the template isn't the model's own at its revision;
- `endpoint.process`, `endpoint.not_running`, `endpoint.argv`: the server's process wasn't seen, isn't running, or
  runs other arguments than its configuration;
- `endpoint.unreachable`, `endpoint.version`, `endpoint.served_name`: the server didn't answer, reports a different
  vLLM version than its package, or doesn't answer under the engine's digest.

## Terms

| Term | Meaning |
| --- | --- |
| Inventory | Files written by ops that say where things are: vignette sources, endpoints and hosts. For now, they also say which endpoints are cleared for which sources. |
| Source | Where a set of vignettes is fetched from, by id. Its name is part of every case built from it. |
| Endpoint | Where one engine is served: its URL, capacity and secret, and the host that runs it. |
| Host | A machine that runs local engines, and where it keeps the model files and chat templates they pin. |
| Location | Where a host keeps a file, written the way the host reads it. |
| Start-up | What the start-up script runs for one endpoint: vLLM's arguments, the env and the runtime. |
| Include | A file whose endpoints and hosts an inventory takes as its own. |
| Cleared | An endpoint's permission, for now, to receive content from a sensitive source. |

## Open design issues

### Checks happen when an entry is used
Loading checks only what the files show. Everything that needs the engines is checked only when `start_up`,
`url_of` or `confirm` is called, and fails as a `LookupError`:
- whether an endpoint's digest names an engine;
- whether a local engine's endpoint has a URL and a host;
- whether the host says where the model and template are;
- whether the engine's argv leaves `--host` and `--port` alone.

init-data's endpoint lines are a pass of their own over these checks. A single `check(inventory, get)` returning
findings with `inventory.*` codes would give init-data, the runner and the import the same answer. It would also fit
the split between errors and findings in `docs/chatddx.md` ("Findings and errors"), where problems that need other
components to see raise `StructuralError`.

Nothing checks:
- two endpoints at one URL (the import refuses it only within what it writes);
- a remote engine's endpoint that names a host;
- host locations that no endpoint's engine pins;
- a `[cleared]` entry for a source that isn't sensitive, which clears nothing.

### Hosts don't read the start-up
o11n and the hosts' own configuration (Kompismoln/org, `hosts/*/configuration.nix`) decide what each server runs.
The rig imports what they run, and `start_up` on the imported entries gives back the command line o11n runs. So
the start-up is a check, and only the fake vLLM is started from one.
For a host to start its engines from the rig's start-up, o11n would have to read it, and the import would then
confirm what was started rather than describe it.

### Where a deployment's World is
A World is handed over each time: `chatddx init-data` takes it as `--world`, and the runner takes a loaded `Inventory`.
Nothing in `src/chatddx/core/settings.py` locates one. This repository's `world/` holds the hosts' names and the paths
on them. A deployed orchestrator (`docs/chatddx.md`, "Target stack") needs its World from somewhere. The runner needs
the World the person starting a run meant, since that World decides what is cleared.

### Smaller issues
- **Endpoint names are only a convention.** Nothing enforces `<server>@<host>`. A run records the endpoint's name,
  and `[cleared]` keys on it, so renaming an endpoint drops its clearance without warning, and its runs appear under
  two names.
- **`max_jobs` isn't read** until the runner sends more than one request at a time.
- **A new kind of source takes two classes,** a spec and a reader.

## Proposed amendments

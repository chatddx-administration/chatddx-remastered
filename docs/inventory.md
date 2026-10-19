# Inventory

The inventory says which directory holds a source's vignettes, at which address an engine is served, where a host keeps
the model files and chat template an engine pins.

```
AGENT: REPLACE
Judges and configurations are bound to handles (`src/chatddx/inventory/inventory.py:Inventory`).
---
Until clearance has a pipeline of its own, the inventory also says which endpoints may receive content from which
sensitive sources. It also says under which handle each of a data set's judges judges, and the handle its
configurations are made for.
```
Until clearance has a pipeline of its own, the inventory also says which endpoints may receive content from which
sensitive sources. It also says at which endpoint each of a data set's judges judges, and the endpoint whose engine
its configurations are made for.

Heads-up: The location the vignette sources is a factor! Everything else is not.

The inventory isn't stored in the database, and its history is git's. A run records the endpoint it used, by name and
address (docs/ledger.md, "Run start").

This document describes what the inventory says and why. Classes, fields and errors are in docs/reference/inventory.md.
The `inventory` builds on the `factors` and nothing else.

## The file
An inventory is a file of named entries: sources, endpoints, hosts, and the clearance table. An entry's name is its
table's key. Paths in the file are relative to the file, so a World can be moved whole. Locations a host gives for its
own files are the host's (see "Hosts").

### Includes
```
AGENT: REPLACE
A judge and configurations are bound to handles.
---
endpoints and hosts: it can't include another file, add a source, clear an endpoint, bind a judge or name the handle
configurations are made for, so importing again can't either. A name is defined once, across the inventory and
```
An inventory can include other files, whose endpoints and hosts count as its own. Includes keep what the engine
import writes apart from what people write, so an import can rewrite its file whole. An included file holds only
endpoints and hosts: it can't include another file, add a source, clear an endpoint, bind a judge or name the endpoint
configurations are made for, so importing again can't either. A name is defined once, across the inventory and
everything it includes.

### What loading checks
```
AGENT: REPLACE
Bindings name handles, which the files don't define, so loading no longer checks them; init-data reports one that
doesn't resolve (`src/chatddx/curation/plan.py`).
---
Loading checks what the files themselves show: that each endpoint's host is defined, that the clearance table names
endpoints and sources that exist, and that each source is named by its table. A judge's and the configurations'
handles are resolved as the data set is loaded (docs/curation.md, "Facts and the engine"), and anything else that
needs the engines is checked when an entry is used (src/chatddx/inventory/check.py).
```
Loading checks what the files themselves show: that each endpoint's host is defined, that the clearance table names
endpoints and sources that exist, that each judge is bound to an endpoint that exists, that the endpoint
configurations are made for exists, and that each source is named by its table. Anything that needs the engines is
checked when an entry is used (src/chatddx/inventory/check.py).

### Worlds
In chatddx, a world is technically the only the parameters beyond chatddx's control, but the directories `worlds/*` also
contain the data this repository carries for this world. The non-world data is in directories prefixed with `_`.

Command line tools take `--world DIR` or fall back to `CHATDDX_WORLD`.

The directory must contain an `inventory.toml` and may contain the others, see table.

```
AGENT: REPLACE
The `inventory.toml` row: judges and configurations by handle.
---
| `inventory.toml` | ops, by hand | sources, clearance, which handle judges each judge, and which handle configurations are made for |
```
| File | Author | Holds |
| --- | --- | --- |
| `inventory.toml` | ops, by hand | sources, clearance, which endpoint judges each judge, and which endpoint's engine configurations are made for |
| `endpoints.toml` | the engine import (by hand for fakes), included | endpoints and hosts |
| `engines.toml` | the engine import (by hand for fakes) | models, local engines, remote engines |
| `facts.toml` | whoever adds a model the bundled facts don't know | facts about models |
| `vignettes/` | the source's owner | a directory source's vignettes, when git may hold them |
| `_data/` | researchers and clinicians | the data set (docs/curation.md, "Data sets") |
| `_runs/` | developers | scripted runs (docs/scripted.md) |

```
```
AGENT: REPLACE
The tree's `inventory.toml` line: judges bound to handles.
---
  inventory.toml   sources, clearance, judges bound to handles, configurations, include = ["endpoints.toml"]
```
worlds/<name>/
  inventory.toml   sources, clearance, judges bound to endpoints, configurations, include = ["endpoints.toml"]
  endpoints.toml   endpoints and hosts
  engines.toml     models, local engines, remote engines
  facts.toml       facts about models the bundled facts don't know
  vignettes/       a directory source's vignettes, when git may hold them
  _data/
    factors.toml       chunks without text, tools, the expectation schema, scorers, judges, recipes, canary sets
    texts-<lang>.toml  chunks that hold text, written in that language; translations into it, grouped by record
    cases-<lang>.toml  cases in that language, with tags, targets, appendices and the cases that send them
    schemas/           the JSON files the factors load
  _runs/           scripted runs
```

A World may point into another. An include or a source's path can reach another World's directory, so one World can
take another's vignettes or endpoints without copying them.

This repository has three, in `worlds/`:

```
AGENT: REPLACE
The bare Qwen3 has weights of its own, `qwen3-8b-bare`, as two endpoints serving one model's weights are ops' error
(`worlds/test/engines.toml`).
---
- The test World: what the tests run on, built so that each record exercises something a test reads. Four fake
  endpoints on this machine (one with no reasoning parser and no tool flags, under weights of its own,
  `qwen3-8b-bare`, one serving a made-up model whose facts are the World's own `facts.toml`), a remote endpoint that
  only a fake stands in for, nine vignettes each carrying a quirk of its own, and its data set in `_data/`. Its tools
  are the runner's test tools, so it loads only under pytest.
```
- The test World: what the tests run on, built so that each record exercises something a test reads. Four fake
  endpoints on this machine (one with no reasoning parser and no tool flags, one serving a made-up model whose facts
  are the World's own `facts.toml`), a remote endpoint that only a fake stands in for, nine vignettes each carrying
  a quirk of its own, and its data set in `_data/`. Its tools are the runner's test tools, so it loads only under
  pytest.

- The sample World: the example new Worlds follow, using everything a World can hold. The sample's vignettes and its
  data set (`_data/`), an endpoint for each fake engine on this machine and the fake host, in an included
  `endpoints.toml` as an engine import writes it, a remote engine's endpoint with a credential, which `chatddx
  fake-engines` stands in for, and the facts of the remote engine's model. Every endpoint is cleared for the sample.

- Kompismoln's World: the hosts pelle and malborg. Its inventory is written by hand, takes the sample World's
  vignettes, and binds the sample's judges to pelle and malborg; its endpoints, hosts and engines are what the engine
  import writes from the hosts' reports. Both endpoints are cleared for the sample.

```
AGENT: REPLACE
Each names a handle (`worlds/*/inventory.toml`).
---
Each names the handle its configurations are made for: `qwen3-8b-awq` in the test and the sample World, and
`qwen3-8b` in Kompismoln's.
```
Each names the endpoint its configurations are made for: `qwen3@fake` in the test World, `qwen3-8b-awq@fake` in the
sample World, and `qwen3-8b@pelle` in Kompismoln's.

src/chatddx/test/test_worlds.py fails when a World's engines change and its endpoints don't.

## Sources
A source is where a set of vignettes is fetched from, by id. A source is a directory with one file per vignette,
named by its id, or a database source, `kind = "database"`, whose vignettes are texts people typed, kept in the
database under new ids as written. A source is a directory unless it says otherwise.

Each source name cleanup steps, such as `newlines.lf@1` for a source written with CRLF, and a run applies those of its
cases' sources unless its request gives its own (docs/factors.md, "Preparing a case"). Ops write them, since they are
the source's quirks, so that runs on one source agree unless a researcher varies them.

A directory source lists its vignettes' ids, fetches a vignette's raw bytes, and builds a case for each vignette,
without appendices, with the fingerprint of the raw bytes (docs/factors.md, "Case"). It refuses an id that would reach
outside it. What happens to the bytes next is the case's preparation (docs/factors.md, "Preparing a case"). A
database source lists nothing: its texts are read through the store, by id, so init-data and repair-data, which list
a source, refuse one.

The source's name is part of every case built from it, including their digests. Renaming a source makes new cases;
``
moving its directory changes nothing. init-data loads the cases of a source a World names, or of its only directory
source.

## Endpoints
An endpoint says where one engine is served: the engine, by digest; the server's address; the host that runs it, for a
local engine; how many requests it takes at once; and, when it has a secret, the name of the environment variable that
holds it.

A local engine is served under its digest (docs/factors.md, "Local engine"), so the endpoint names the very engine the
server answers as. Changing the engine changes its digest, so the endpoint has to change with it, and its handle means
the new engine from then on; runs under the handle on its earlier engines stay grouped under it (docs/bench.md).
Every endpoint has an address, and a local engine's needs a host too to be started.

A remote engine's endpoint gives its address, as a local engine's does; the engine itself names its provider and
model. The endpoint adds what isn't part of the engine: the address, the secret and the capacity.

Endpoint names are free-form. The engine import names them after the server and the host, server@host, and the sample
World follows that pattern. A run records the name, and clearance keys on it.

The runner reads the secret from the variable the endpoint names, and sends it as a bearer token with every request to
the endpoint, the one that confirms it included. It refuses to run when the variable isn't set. The secret itself
never appears in the inventory or the ledger.

The capacity matches the server's own limit on requests at once, which the engine import takes from the server's
configuration, as it takes the arguments that only tune the server (docs/backlog.md, "What reaches vLLM: argv and
passthrough"), and the runner refuses an execution that would send more.

An endpoint may name a canary set, by digest, which every run at it sends, so that runs at one endpoint are probed
alike and can be compared; and a default execution, a timeout and retries among it, which a run's request may change
the concurrency and order of. Loading refuses a default concurrency above the capacity.

A run goes to the endpoint its model's handle maps to, and a judge's calls to the one its handle maps to; researchers
name no endpoint. Ops map each handle to exactly one engine and one endpoint, on one hardware class. A handle that
doesn't resolve to one is ops' error: the inventory check reports it at init-data, as a worker starts and at the
engine import, and a researcher's run or scoring is refused saying it is ops'.

## Hosts
A host says the address its servers listen on, and where it keeps what its engines pin. A local engine pins its model
and chat template by hash (docs/factors.md, "Model artifact" and "Local engine"), and its host says where each file is.
Engines on one host share its entries. A location is the host's own, written the way its start-up reads it, as a path
or a Hugging Face repository, and isn't resolved against the inventory file.

The sample's fake host keeps its models under their repository names, which the fake vLLM takes as model names, and
its one chat template, the empty one, is the null device.

## Clearance
The clearance table lists, for each endpoint, the sensitive sources it may receive sensitive content from. It
stands in until clearance has a database grant, and what it permits is clearance's (agents/wip-clearance.md, "Vetted
endpoints"). It is read only from the inventory's own file (see "Includes"). Clearing an endpoint is a person's
statement, so no command writes it.

## Judges
```
AGENT: REPLACE
The table binds handles, as the paragraph below says (`worlds/*/inventory.toml`).
---
The judge table binds each of a data set's judges, by name, to the handle whose latest engine judges it:
`[judge] verdict = "qwen3-8b"`. Which engine judges is the World's choice, as the handle a run goes under is,
```
The judge table binds each of a data set's judges, by name, to the endpoint whose engine judges it:
`[judge] verdict = "qwen3-8b@pelle"`. Which engine judges is the World's choice, as the endpoint a run goes to is,
so a data set's judges are planned with the engines of the World they are loaded into, and a World that binds none of
them leaves them and their scorers out (docs/curation.md, "Factors"). Like clearance, a binding is read only from the
inventory's own file, and no command writes it.

A judge's model is picked by handle, a person's and a data set's alike, and a data set's judge is bound to a
handle rather than an endpoint (`[judge] verdict = "qwen3-8b"`); the scoring pass sends its calls to the handle's
endpoint.

## Configurations
```
AGENT: REPLACE
It names a handle (`worlds/kompismoln/inventory.toml`).
---
`configurations = "qwen3-8b"`, at the top of the inventory, names the handle whose model a data set's configurations
are made for: init-data makes each recipe once, for its model (docs/curation.md).
```
`configurations = "qwen3-8b@pelle"`, at the top of the inventory, names the endpoint whose engine's model a data set's
configurations are made for: init-data makes each recipe once, with that engine (docs/curation.md).

Which model a configuration is made for is the World's choice, and a researcher swaps it by its handle; the engine is
the handle's latest, a trial's and a judge's alike. Ops may put new weights under a handle: configurations pinning the
old ones are then behind their model, and don't run under the handle until followed.

## Starting and reaching an engine
An endpoint is joined with the engine it serves and, for a local engine, with the host that runs it. When the
inventory or the engine falls short of what that needs, starting or reaching the endpoint is refused with the reason.

### The start-up
The start-up is what the start-up script runs for a local engine's endpoint: vLLM's arguments, the engine's
environment, and the runtime to run vLLM from. The arguments are the model's location on the host and its revision,
the engine's digest as the name it is served under, the chat template's location on the host, where to listen, from
the host's address and the endpoint's port, and then the engine's own arguments.

A remote engine isn't ours to start. A start-up is refused for an endpoint without a host, and for a host that
doesn't say where it keeps the model or the template. An engine's own arguments can't say where to listen: the
endpoint decides that, and the engine refuses them as it refuses the arguments that pin the model and the template
(docs/factors.md, "Local engine").

The fake vLLM can be started from a start-up (`chatddx fake-engines`), and then serves the endpoint's engine
(docs/vllm.md, "The fake vLLM").

### Reaching an engine
An endpoint is reached at its address. Before content goes to it, the runner confirms that its server lists the name
its engine is served under (docs/runner.md); the inventory itself connects to nothing.

With a World, init-data ends with the inventory check's findings and a count (src/chatddx/inventory/check.py), and a
worker logs them as it starts, against the engines the store holds. Neither connects to find them.

## Importing from a host
`chatddx import-engine REPORT… [--server NAME]… [--endpoint-host HOST] --engines PATH --endpoints PATH`. A report is
a host's URL, a file, or `-` for stdin. `--server` imports only the servers named, and refuses a name no report has;
`--endpoint-host` puts another host name in the endpoints' URLs, for one report only. `--engines` is the file the
models and engines are written to, and `--endpoints` the file of endpoints and hosts.

The hosts run vLLM through o11n (Kompismoln/o11n). Each server runs in a container configured outside the rig, so an
engine's values come from its host, not from people: the engine import reads each host's report and writes the
factors and the inventory entries together.

For each server, the import puts each server's model under the handle ops give it and its inventory check reports a
handle it leaves without exactly one endpoint. The models and engines go to the World's `engines.toml`, and the
endpoints and hosts to a file an inventory includes. Both files are rewritten whole, so to change them, import again
rather than edit.

The endpoint's address is the report's, or a host name given in its place, with the server's port. The host's
listening address, the capacity and the engine's environment come from the server's configuration, without the
variables o11n sets on every server to find the model, the GPU and CUDA.

The import refuses what it can't describe faithfully: a server on several GPUs, since an engine's hardware has no GPU
count; a model that isn't a Hugging Face repository at a revision; a part of the report that couldn't be gathered;
extra arguments that say where to listen; whatever a local engine refuses; two servers at one address; and two
servers on one host that listen on different addresses.

What it sees without refusing, it reports: the model's and the engine's lints (docs/factors.md, "Lints"); the chat
template, checked against the engine, or that it couldn't be checked, or isn't the model's own; a gpt-oss engine,
whose template vLLM doesn't read and whose prompts hold the current date unless its environment sets one; and a
server that wasn't seen, isn't running, runs other arguments than its configuration, doesn't answer, reports another
vLLM version than its package, or doesn't answer under the engine's digest.

The import's findings have the engine's digest as subject:
- `engine.chat_template_unused` (info): vLLM renders the model with Harmony and doesn't read the chat template, so
  its hash pins nothing (docs/vllm.md).
- `engine.harmony_date` (warning): such an engine's environment doesn't set `VLLM_SYSTEM_START_DATE`, so every prompt
  holds the current date.
- `engine.chat_template_unread` (info): the report has no template text, so the template wasn't checked. When it has,
  the template is checked against the engine (`engine.chat_template`, `engine.chat_template_date`;
  src/chatddx/factors/engine.py).
- `engine.chat_template_not_the_model_s` (info): the template isn't the model's own at its revision.
- `endpoint.process` (warning): the server's process wasn't seen.
- `endpoint.not_running` (warning): the server isn't running.
- `endpoint.argv` (warning): the running server's arguments aren't its configuration's, so it may predate it.
- `endpoint.unreachable` (warning): the server didn't answer.
- `endpoint.version` (warning): the server says it is another vLLM version than its package.
- `endpoint.served_name` (warning): the server doesn't answer under the engine's digest.

Before it writes, the import also checks the endpoints and hosts it writes against the models and engines it writes,
with the inventory check (see "Reaching an engine"), and prints the findings after its own. As it refuses two servers
at one address and says where each engine's model and template are, the check finds nothing in what it writes today.

## Terms

| Term | Meaning |
| --- | --- |
| Inventory | Files written by ops that say where things are: vignette sources, endpoints and hosts. For now, they also say which endpoints are cleared for which sources. |
| World | A directory with an inventory, the files it includes, and the factors of the engines its endpoints serve. |
| Source | Where a set of vignettes is fetched from, by id. Its name is part of every case built from it. |
| Endpoint | Where one engine is served: its address, capacity and secret, and the host that runs it. |
| Host | A machine that runs local engines, and where it keeps the model files and chat templates they pin. |
| Location | Where a host keeps a file, written the way the host reads it. |
| Start-up | What the start-up script runs for one endpoint: vLLM's arguments, the environment and the runtime. |
| Include | A file whose endpoints and hosts an inventory takes as its own. |
| Bound | A data set's judge, given the endpoint whose engine judges it. |
| Configurations | The endpoint whose engine a data set's configurations are made for. |
| Cleared | An endpoint's permission, for now, to receive content from a sensitive source. |

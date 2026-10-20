# Inventory

The inventory says which directory holds a source's vignettes, at which address an engine is served, where a host keeps
the model files and chat template an engine pins.

Heads-up: The location the vignette sources is a factor! Everything else is not.

The inventory isn't stored in the database, and its history is git's. A run records the endpoint it used, by name and
address (docs/modules/ledger.md, "Run start").

```
AGENT: REPLACE
`docs/reference/` is `docs/surfaces/` now.
---
This document describes what the inventory says and why. Classes, fields and errors are in docs/surfaces/inventory.md.
The `inventory` builds on the `factors` and nothing else.
```
This document describes what the inventory says and why. Classes, fields and errors are in docs/reference/inventory.md.
The `inventory` builds on the `factors` and nothing else.

## The file

An inventory is a file of named entries: sources, endpoints, hosts, and the clearance table. An entry's name is its
table's key. Paths in the file are relative to the file, so a World can be moved whole. Locations a host gives for its
own files are the host's (see "Hosts").

### Includes

An inventory can include other files, whose endpoints and hosts count as its own. Includes keep what the engine import
writes apart from what people write. A name is defined once, across the inventory and everything it includes.

### What loading checks

Loading checks what the files themselves show: that each endpoint's host is defined, that the clearance table names
endpoints and sources that exist, and that each source is named by its table. A judge's and the configurations' handles
are resolved as the data set is loaded (docs/modules/curation.md, "Loading"), and anything else that needs
the engines is checked when an entry is used (src/chatddx/inventory/check.py).

### Worlds

In chatddx, a world is technically the only the parameters beyond chatddx's control, but the directories `worlds/*` also
contain the data this repository carries for this world. The non-world data is in directories prefixed with `_`.

Command line tools take `--world DIR` or fall back to `CHATDDX_WORLD`.

The directory must contain an `inventory.toml` and may contain the others, see table.

| File             | Author                                            | Holds                                        |
| ---------------- | ------------------------------------------------- | -------------------------------------------- |
| `inventory.toml` | ops, by hand                                      | sources, clearance, judges                   |
| `endpoints.toml` | the engine import (by hand for fakes), included   | endpoints and hosts                          |
| `engines.toml`   | the engine import (by hand for fakes)             | models, local engines, remote engines        |
| `facts.toml`     | whoever adds a model the bundled facts don't know | facts about models                           |
| `vignettes/`     | the source's owner                                | vignettes' directory, when git may hold them |
| `_data/`         | researchers and clinicians                        | the data set                                 |
| `_runs/`         | developers                                        | scripted runs (docs/modules/scripted.md)     |

```
worlds/<name>/
  inventory.toml
  endpoints.toml
  engines.toml
  facts.toml
  vignettes/
  _data/
    factors.toml       chunks without text, tools, the expectation schema, scorers, judges, recipes, canary sets
    texts-<lang>.toml  chunks that hold text, written in that language; translations into it, grouped by stanza
    cases-<lang>.toml  cases in that language, with tags, targets, appendices and the cases that send them
    schemas/           the JSON files the factors load
  _runs/
```

A World may point into another. An include or a source's path can reach another World's directory, so one World can take
another's vignettes or endpoints without copying them.

This repository has three, in `worlds/`:

- The test World: what the tests run on, built so that each stanza exercises something a test reads. Four fake endpoints
  on this machine (one with no reasoning parser and no tool flags, under weights of its own, `qwen3-8b-bare`, one
  serving a made-up model whose facts are the World's own `facts.toml`), a remote endpoint that only a fake stands in
  for, nine vignettes each carrying a quirk of its own, and its data set in `_data/`. Its tools are the runner's test
  tools, so it loads only under pytest.

- The sample World: the example new Worlds follow, using everything a World can hold. The sample's vignettes and its
  data set (`_data/`), an endpoint for each fake engine on this machine and the fake host, in an included
  `endpoints.toml` as an engine import writes it, a remote engine's endpoint with a credential, which
  `chatddx fake-engines` stands in for, and the facts of the remote engine's model. Every endpoint is cleared for the
  sample.

- Kompismoln's World: the hosts pelle and malborg. Its inventory is written by hand, takes the sample World's vignettes,
  and binds the sample's judges to pelle and malborg; its endpoints, hosts and engines are what the engine import writes
  from the hosts' reports. Both endpoints are cleared for the sample.

Each names the handle its configurations are made for: `qwen3-8b-awq` in the test and the sample World, and `qwen3-8b`
in Kompismoln's.

## Sources

A source is where a set of vignettes is fetched from, by id. A source is a directory with one file per vignette, named
by its id, or a database source, `kind = "database"`, whose vignettes are texts people typed, kept in the database under
new ids as written. A source is a directory unless it says otherwise.

Each source name cleanup steps, such as `newlines.lf@1` for a source written with CRLF, and a run applies those of its
cases' sources unless its request gives its own (docs/modules/factors.md, "Preparing a case"). Ops write them, since
they are the source's quirks, so that runs on one source agree unless a researcher varies them.

## Endpoints

An endpoint says where one engine is served: the engine, by digest; the server's address; the host that runs it, for a
local engine; how many requests it takes at once; and, when it has a secret, the name of the environment variable that
holds it.

Endpoint names are free-form. The engine import names them after the server and the host, server@host, and the sample
World follows that pattern. A run records the name, and clearance keys on it.

An endpoint may name a canary set, by digest, which every run at it sends, so that runs at one endpoint are probed alike
and can be compared; and a default execution, a timeout and retries among it, which a run's request may change the
concurrency and order of. Loading refuses a default concurrency above the capacity.

A run goes to the endpoint its model's handle maps to, and a judge's calls to the one its handle maps to; researchers
name no endpoint. Ops map each handle to exactly one engine and one endpoint, on one hardware class.

Weights served at several endpoints, or held by several model threads, stop `chatddx portal`, `api`, `run`, `worker`,
`repl` and `scripted-runs` from starting, make init-data refuse and write nothing, and make the engine import refuse to
write (src/chatddx/bench/handles.py:broken). A handle no endpoint here serves, and a deleted one, are refused as the
bench says (docs/modules/bench.md, "The model").

## Hosts

A host says the address its servers listen on, and where it keeps what its engines pin. A local engine pins its model
and chat template by hash (docs/modules/factors.md, "Local model" and "Local engine"), and its host says where each file
is. Engines on one host share its entries. A location is the host's own, written the way its start-up reads it, as a
path or a Hugging Face repository, and isn't resolved against the inventory file.

The sample's fake host keeps its models under their repository names, which the fake vLLM takes as model names, and its
one chat template, the empty one, is the null device.

## Clearance

The clearance table lists, for each endpoint, the sensitive sources it may receive sensitive content from. It stands in
until clearance has a database grant, and what it permits is clearance's (agents/wip-clearance.md, "Vetted endpoints").
It is read only from the inventory's own file (see "Includes"). Clearing an endpoint is a person's statement, so no
command writes it.

## Judges

The judge table binds each of a data set's judges, by name, to the handle whose latest engine judges it:
`[judge] verdict = "qwen3-8b"`. Which engine judges is the World's choice, as the handle a run goes under is, so a data
set's judges are planned with the engines of the World they are loaded into, and a World that binds none of them leaves
them and their scorers out (docs/modules/curation.md, "Factors"). Like clearance, a binding is read only from the
inventory's own file, and no command writes it.

## Configurations

`configurations = "qwen3-8b"`, at the top of the inventory, names the handle whose model a data set's configurations are
made for: init-data makes each recipe once, for its model (docs/modules/curation.md).

Which model a configuration is made for is the World's choice, and a researcher swaps it by its handle; the engine is
the handle's latest, a trial's and a judge's alike. Ops may put new weights under a handle, which puts the
configurations pinning the old ones behind their model (docs/modules/bench.md, "The model").

## Starting and reaching an engine

An endpoint is joined with the engine it serves and, for a local engine, with the host that runs it. When the inventory
or the engine falls short of what that needs, starting or reaching the endpoint is refused with the reason.

### The start-up

The start-up is what the start-up script runs for a local engine's endpoint: vLLM's arguments, the engine's environment,
and the runtime to run vLLM from. The arguments are the model's location on the host and its revision, the engine's
digest as the name it is served under, the chat template's location on the host, where to listen, from the host's
address and the endpoint's port, and then the engine's own arguments.

The fake vLLM can be started from a start-up (`chatddx fake-engines`), and then serves the endpoint's engine
(docs/vllm.md, "The fake vLLM").

### Reaching an engine

An endpoint is reached at its address. Before content goes to it, the runner confirms that its server lists the name its
engine is served under (docs/modules/runner.md); the inventory itself connects to nothing.

## Importing from a host

`chatddx import-engine REPORT… [--server NAME]… [--endpoint-host HOST] --engines PATH --endpoints PATH`. A report is a
host's URL, a file, or `-` for stdin. `--server` imports only the servers named, and refuses a name no report has;
`--endpoint-host` puts another host name in the endpoints' URLs, for one report only. `--engines` is the file the models
and engines are written to, and `--endpoints` the file of endpoints and hosts.

What it sees without refusing, it reports: the model's and the engine's lints (docs/modules/factors.md, "Lints"), and
the findings listed below.

The import's findings have the engine's digest as subject:

- `engine.chat_template_unused` (info): vLLM renders the model with Harmony and doesn't read the chat template, so its
  hash pins nothing (docs/vllm.md).
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
with the inventory check (see "Reaching an engine"), and prints the findings after its own. As it refuses two servers at
one address and says where each engine's model and template are, the check finds nothing in what it writes today.

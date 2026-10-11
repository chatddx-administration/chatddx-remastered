# Inventory

Factors say what something is: an engine, a model, a case. The inventory says where to find it. It is a set of files
that ops write. They say which directory holds a source's vignettes, at which address an engine is served, and where a
host keeps the model files and chat template an engine pins. Until clearance has a pipeline of its own, the inventory
also says which endpoints may receive content from which sensitive sources.

The inventory is not a factor (docs/factors.md, "Not factors"). No component refers to an inventory entry, so moving a
model's files or an engine's server changes no digest. Two things that sound like locations are factors, though:
- a source's name, which every case built from it carries;
- a remote engine's address.

The inventory isn't stored in the database, and its history is git's. A run records the endpoint it used, by name and
address (docs/ledger.md, "Run start").

This document describes what the inventory says and why. Names, fields, rules and errors are in the API,
docs/inventory-api.md. The inventory builds on the factors and nothing else. init-data, the engine import and the
runner read it.

## The file
An inventory is a file of named entries: sources, endpoints, hosts, and the clearance table. An entry's name is its
table's key. Paths in the file are relative to the file, so a World can be moved whole. Locations a host gives for its
own files are the host's (see "Hosts").

### Includes
An inventory can include other files, whose endpoints and hosts count as its own. Includes keep what the engine
import writes apart from what people write, so an import can rewrite its file whole. An included file holds only
endpoints and hosts: it can't include another file, add a source or clear an endpoint, so importing again can't either.
A name is defined once, across the inventory and everything it includes.

### What loading checks
Loading checks what the files themselves show: that each endpoint's host is defined, that the clearance table names
endpoints and sources that exist, and that each source is named by its table. Anything that needs the engines is
checked when an entry is used (see "Checks happen when an entry is used").

### Worlds
A World is handed over as its directory, `--world DIR`, and read as its `inventory.toml` and, when present,
`factors.toml` and `facts.toml`, facts about models the bundled ones don't know, loaded beside them by init-data
and the repl (src/chatddx/inventory/world.py, src/chatddx/cli.py). A World may also hold its source's vignettes,
when git may hold them.

`CHATDDX_WORLD` names the deployment's World directory and is the default `--world` of `init-data` and the `repl`
(src/chatddx/core/settings.py:world, `.env`). The runner is handed its inventory by the bench, as before.

A World may point into another. An include or a source's path can reach another World's directory, so one World can
take another's vignettes or endpoints without copying them.

This repository has two, in `worlds/`:
- The sample World: the sample's vignettes, an endpoint for each fake engine on this machine, the fake host, and the
  factors of the fake models and engines. Both endpoints are cleared for the sample. A test fails when its engines
  change and its endpoints don't.
- Kompismoln's World: the hosts pelle and malborg. Its inventory is written by hand and takes the sample World's
  vignettes; its endpoints, hosts and factors are what the engine import writes from the hosts' reports. Both
  endpoints are cleared for the sample.

```
AGENT: CHANGE
The database kind exists now (src/chatddx/inventory/sources.py:DatabaseSource, src/chatddx/store/texts.py), for the
texts people type, as swift's cases (agents/wip-portal.md, "Typed cases").
---
## Sources
A source is where a set of vignettes is fetched from, by id. A source is a directory with one file per vignette,
named by its id, or a database source, `kind = "database"`, whose vignettes are texts people typed, kept in the
database under new ids as written and never changed, and read through the store. A source is a directory unless it
says otherwise.
```
## Sources
A source is where a set of vignettes is fetched from, by id. Today a source is a directory with one file per vignette,
named by its id. Another kind of source, such as a database, would be added beside directories as a kind of its own,
which the inventory then accepts too. A source is sensitive unless it says otherwise; what that requires is
clearance's (agents/wip-clearance.md, "Sensitive sources").

A source lists its vignettes' ids, fetches a vignette's raw bytes, and builds a case for each vignette, without
appendices, with the fingerprint of the raw bytes (docs/factors.md, "Case"). It refuses an id that would reach outside
it. What happens to the bytes next is the case's preparation (docs/factors.md, "Preparing a case").

A source's name is part of every case built from it, and so of their digests. Renaming a source makes new cases;
moving its directory changes nothing. init-data loads the cases of a source a World names.

## Endpoints
An endpoint says where one engine is served: the engine, by digest; the server's address; the host that runs it, for a
local engine; how many requests it takes at once; and, when it has a secret, the name of the environment variable that
holds it.

A local engine is served under its digest (docs/factors.md, "Local engine"), so the endpoint names the very engine the
server answers as. Changing the engine changes its digest, so the endpoint has to change with it. A local engine's
endpoint needs an address to be reached, and a host too to be started.

A remote engine's address is part of its digest, so its endpoint may leave the address out; if it gives one, it must
be the same. The endpoint adds what isn't part of the engine: the secret and the capacity.

Endpoint names are free-form. The engine import names them after the server and the host, server@host, and the sample
World follows that pattern. A run records the name, and clearance keys on it.

The runner reads the secret from the variable the endpoint names, and sends it as a bearer token with every request to
the endpoint, the one that confirms it included. It refuses to run when the variable isn't set. The secret itself
never appears in the inventory or the ledger.

The capacity matches the server's own limit on requests at once, which the engine import takes from the server's
configuration, and the runner refuses an execution that would send more.

## Hosts
A host says the address its servers listen on, and where it keeps what its engines pin. A local engine pins its model
and chat template by hash (docs/factors.md, "Model artifact" and "Local engine"), and its host says where each file is.
Engines on one host share its entries. A location is the host's own, written the way its start-up reads it, as a path
or a Hugging Face repository, and isn't resolved against the inventory file.

The sample's fake host keeps its models under their repository names, which the fake vLLM takes as model names, and
its one chat template, the empty one, is the null device.

## Clearance
The clearance table lists, for each endpoint, the sensitive sources it may receive case-derived content from. It
stands in until clearance has a database grant, and what it permits is clearance's (agents/wip-clearance.md, "Vetted
endpoints"). It is read only from the inventory's own file (see "Includes"). Clearing an endpoint is a person's
statement, so no command writes it.

## Starting and reaching an engine
An endpoint is joined with the engine it serves and, for a local engine, with the host that runs it. When the
inventory or the engine falls short of what that needs, starting or reaching the endpoint is refused with the reason.

### The start-up
The start-up is what the start-up script runs for a local engine's endpoint: vLLM's arguments, the engine's
environment, and the runtime to run vLLM from. The arguments are the model's location on the host and its revision,
the engine's digest as the name it is served under, the chat template's location on the host, where to listen, from
the host's address and the endpoint's port, and then the engine's own arguments.

A remote engine isn't ours to start. A start-up is refused for an endpoint without an address or a host, for a host
that doesn't say where it keeps the model or the template, and for an engine whose own arguments say where to listen:
the endpoint decides that, just as the start-up owns the arguments that pin the model and the template
(docs/factors.md, "Local engine").

The fake vLLM can be started from a start-up (`chatddx fake-engines`), and then serves the endpoint's engine
(docs/vllm.md, "The fake vLLM").

### Reaching an engine
An endpoint is reached at its address, or a remote engine's endpoint at the engine's. Before case-derived content goes
out, the runner confirms the endpoint: its server must list the name the engine is served under, a local engine's
digest or a remote engine's model (agents/wip-clearance.md, "Vetted endpoints"). A server that can't be reached
can't be confirmed.

With a World, init-data ends with the inventory check's findings and a count (see "Checks happen when an entry is
used"). It finds that out without connecting.

## Importing from a host
The hosts run vLLM through o11n (Kompismoln/o11n). Each server runs in a container configured outside the rig, so an
engine's values come from its host, not from people: the engine import reads each host's report and writes the
factors and the inventory entries together.

For each server, the import writes the model artifact, the local engine, the endpoint, and where the host keeps the
model and the template, all named server@host after the report's host name. The factors go to a file `init-data` takes
beside the data's, and the endpoints and hosts to a file an inventory includes. Both files are rewritten whole, so to
change them, import again rather than edit.

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
  docs/factors-api.md, "engine.py").
- `engine.chat_template_not_the_model_s` (info): the template isn't the model's own at its revision.
- `endpoint.process` (warning): the server's process wasn't seen.
- `endpoint.not_running` (warning): the server isn't running.
- `endpoint.argv` (warning): the running server's arguments aren't its configuration's, so it may predate it.
- `endpoint.unreachable` (warning): the server didn't answer. In the inventory's check the same code means the
  endpoint's address can't be worked out, as `url_of` refuses it (docs/inventory-api.md, "check.py").
- `endpoint.version` (warning): the server says it is another vLLM version than its package.
- `endpoint.served_name` (warning): the server doesn't answer under the engine's digest.

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
| Cleared | An endpoint's permission, for now, to receive content from a sensitive source. |
| Confirm | Asking an endpoint's server whether it serves the endpoint's engine, before content goes out. |

## Open design issues
These are open questions of design. Where the code falls short of this document, the API says so
(docs/inventory-api.md, "Known gaps").

### Checks happen when an entry is used
Loading checks only what the files show. Everything that needs the engines is checked when an endpoint is started,
reached or confirmed, one entry at a time:
- whether an endpoint's digest names an engine;
- whether a local engine's endpoint has an address and a host;
- whether the host says where the model and template are;
- whether the engine's own arguments leave where to listen alone.

One pass checks the whole inventory against the engines and returns findings rather than raising. It finds what
starting or reaching each endpoint would refuse, and what nothing refuses but is likely a slip: two local engines'
endpoints at one address, a remote engine's endpoint that names a host, host locations that no endpoint's engine pins,
and a clearance for a source that isn't sensitive, which clears nothing. init-data prints its findings; the runner and
the engine import don't run it yet, and still check one entry at a time.

### Hosts don't read the start-up
o11n and the hosts' own configuration (Kompismoln/org) decide what each server runs. The rig imports what they run,
and the start-up of an imported endpoint gives back the command line o11n runs. So the start-up is a check, and only
the fake vLLM is started from one. For a host to start its engines from the rig's start-up, o11n would have to read
it, and the import would then confirm what was started rather than describe it.

### Smaller issues
- **Endpoint names are only a convention.** Nothing enforces server@host. A run records the endpoint's name, and
  clearance keys on it, so renaming an endpoint drops its clearance without warning, and its runs appear under two
  names.
- **The capacity holds per run.** Two runs on one endpoint can send twice as many requests between them. vLLM queues
  what's over its limit, so nothing fails, but the batching differs from what each run's execution says.

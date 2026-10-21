```
AGENT: write
The module doc of importers, now solidified (AGENTS.md, "Development stages"). Each section is its own suggestion.
docs/modules/inventory.md, "Importing from a host" has one to move the command here, which would take the intro's
pointer to it with it.
---
# Importers

An importer reads what a host reports of the inference servers it runs, and writes them into a World: each server's
model and engine, the endpoint it is reached at, and where its host keeps what they pin. There is one, for the reports
of o11n.vllm, Kompismoln's NixOS module for vLLM, behind `chatddx import-engine`
(docs/modules/inventory.md, "Importing from a host").

This document describes the code `chatddx.importers` (src/chatddx/importers/) and its command in src/chatddx/cli.py. Its
surface is `docs/surfaces/importers.md`.
```

```
AGENT: write
The report an import reads, and what of it is used.
---
## The report

A report, `o11n.vllm.report/1` (`REPORT`), describes the vLLM servers of one host, by name, as o11n's `vllm-report`
gathers them (Kompismoln/o11n, `nixos/vllm-report.py`). It is read from the host's URL, from a file or from stdin
(src/chatddx/importers/o11n.py:read); one read from a URL is reached at the URL's host, unless `--endpoint-host` names
another. A part the report couldn't gather holds only its error.

Of each server, the import takes its GPUs, its model (the Hugging Face repo, its revision, its files' digests and where
it lies), its chat template (its digest, where it lies, its text, whether vLLM reads it, and whether it is the model's
own), vLLM's version and closure, its extra arguments and environment, and the address and port it serves at. What runs
and what answers (`process`, `served`) only feed findings.
```

```
AGENT: write
What a server becomes, and what the import refuses.
---
## What a server becomes

Each server becomes (src/chatddx/importers/o11n.py:imported):

- a local model: its repo, at its revision, with its files' digests;
- a local engine: its one GPU's hardware, vLLM's version and closure, the chat template's digest, its extra arguments,
  and its environment but for what o11n.vllm sets on every server to find the model, the GPU and CUDA (`HOST_ENV`):
  where an engine runs, not what it is;
- an endpoint, `<server>@<host>`, at `http://<host>:<port>/v1/`, whose capacity is vLLM's `--max-num-seqs`, or 1;
- on its host, the address servers bind, and where the model's files and the template lie.

A server's name is its model's handle, so that a model served on several hosts is one handle. The import refuses, naming
the server:

- a model that isn't a repo at a revision, and a server on more than one GPU, since an engine's hardware is one;
- a report without one of the parts it takes, or with one it can't read;
- under one handle, other weights than another host's;
- two servers at one URL, and two addresses servers bind on one host.
```

```
AGENT: write
The two files it writes, and that they are written whole.
---
## What it writes

Two files, each headed by the command that wrote it (src/chatddx/importers/o11n.py:engines_toml and `endpoints_toml`):

- the models and engines, by handle and by endpoint name, which `init-data` loads with the World;
- the endpoints and hosts, which the World's inventory includes (docs/modules/inventory.md, "Includes").

They are written whole, so an engine changes by importing again, not by editing. Before it writes, the import checks
what it writes with the inventory check (`checked`).
```

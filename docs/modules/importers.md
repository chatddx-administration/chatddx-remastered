# Importers

An importer reads what a host reports of the inference servers it runs, and writes them into a World: each server's
model and engine, the endpoint it is reached at, and where its host keeps what they pin. There is one, for the reports
of o11n.vllm, Kompismoln's NixOS module for vLLM, behind `chatddx import-engine`.

This document describes the code `chatddx.importers` (src/chatddx/importers/) and its command in src/chatddx/cli.py. Its
surface is `docs/surfaces/importers.md`.

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
with the inventory check (docs/modules/inventory.md, "Reaching an engine"), and prints the findings after its own. As it
refuses two servers at one address and says where each engine's model and template are, the check finds nothing in what
it writes today.

## The report

A report, `o11n.vllm.report/1` (`REPORT`), describes the vLLM servers of one host, by name, as o11n's `vllm-report`
gathers them (Kompismoln/o11n, `nixos/vllm-report.py`). It is read from the host's URL, from a file or from stdin
(src/chatddx/importers/o11n.py:read); one read from a URL is reached at the URL's host, unless `--endpoint-host` names
another. A part the report couldn't gather holds only its error.

Of each server, the import takes its GPUs, its model (the Hugging Face repo, its revision, its files' digests and where
it lies), its chat template (its digest, where it lies, its text, whether vLLM reads it, and whether it is the model's
own), vLLM's version and closure, its extra arguments and environment, and the address and port it serves at. What runs
and what answers (`process`, `served`) only feed findings.

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

## What it writes

Two files, each headed by the command that wrote it (src/chatddx/importers/o11n.py:engines_toml and `endpoints_toml`):

- the models and engines, by handle and by endpoint name, which `init-data` loads with the World;
- the endpoints and hosts, which the World's inventory includes (docs/modules/inventory.md, "Includes").

They are written whole, so an engine changes by importing again, not by editing. Before it writes, the import checks
what it writes with the inventory check (`checked`).

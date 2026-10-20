# The ChatDDX Rig - requirements and design notes

## Purpose
ChatDDX is a system to measure how accurately LLMs generate differential diagnoses and management plans from emergency-care case vignettes.

The rig provides:
- an environment that can be provably reconstructed (the "cage").
- means to record each exchange within the cage: what was planned, what was sent and what came back.
- first principles for sensitive data so that policies governing this data can be enforced.

It must be possible to deliver the cage together with the results, for scientific rigor.

## Glossary
- **Factor:** Anything that can change an output or its score (`docs/factors.md`, "What a factor is").
- **Fingerprint:** a hash of content that must *not* be stored: vignette, request, prompt token ids. It carries its algorithm: `sha256`, or `hmac-sha256` with a `key_id`
- **Pinned:** a value that can't be altered without changing the digest of one or more factors.
- **Sensitive:** data that may only be stored or sent where it is cleared to go (see "Vignettes and anything made from them are sensitive").
- **Bundle:** a set of root components plus everything they reference (the closure), stored as canonical text keyed by digest, together with the code version that produced it.
- **Cage:** the constrained environment a bundle enforces
- **Digest:** the factor's identity and how it's referenced, an `sha256:<hex>` over the component's canonical bytes.
- **Kind:** the discriminator of a component, e.g. `engine.local`, `chunk.prompt`.

- **Canonical form:** JSON with field names sorted and fields left out when equal to their
  default, plus the type's schema version. JSON data keeps its key order, because a schema's property order is part
  of what a model reads; the keys of settings (`Settings`: bodies, `chat_template_kwargs`, `params`, and `env`) are
  sorted, so equivalent settings share a digest.

- **Chunk:** a factor authored in the portal that fills one part of a recipe (not to be confused with a slot).
- **Recipe:** the chunks and the model a skeleton was compiled from.
- **Skeleton:** the frozen request.
- **Slot:** a placeholder filled at send time.
- **Insert:** a placeholder filled at compile time: `schema` in an output chunk's guidance, filled with that
  output's schema, and `output_guidance` and `tool_guidance` in the instructions or the prompt, filled with the output's
  guidance and the toolset's. An insert's `before` and `after` text appear only when what it inserts isn't empty.
- **Segment:** a literal string, a slot or an insert
- **Purpose:** whether a prompt or skeleton is for `generation` or for a `judge`; it decides which slots are allowed.
- **Contract:** how an output chunk constrains the answer: `native`, `tool` or `text`.
- **Text cleanup:** the named steps a trial applies to vignettes before they are sent.
- **Schema op:** a named, versioned rewrite an output chunk applies to its schema at
  compile time, so the skeleton sends and shows the rewritten schema. Today the only one is `inline_refs@1`.
- **Trial:** The smallest unit of an scientific intent (i.e. Experiment): skeleton + engine + cases + text-cleanup steps + seeds.
- **Replicate:** one seed of a trial, identified by its index.
- **Request:** the body one call sends to an engine: a skeleton rendered with its fills, the served model and the
  seed, or a tool round's next request.
- **Call:** one exchange with an engine: a request sent, in one or more attempts, and what came back.
- **Attempt:** one try at sending a call's request; a call is tried again only when the request didn't get through.
- **Tool round:** the tools a response called, run, and the next request, sent with their results.
- **Item:** one case's replicate in a run: its first request and each tool round's, each sent as a call.
- **Item key:** (case, replicate index), which identifies an item of a run, and with a view an item of a score.
- **Execution:** how a run sends its items, and a score its judge calls: order, concurrency, timeout, retries and the
  runaway cutoff.
- **View:** the part of an output and of an expectation that a scorer scores, and how.
- **Compilation:** A provenance (component) that says which recipe, compiler and facts produced a skeleton, and the
  language it was compiled into, none for the recipe as written
- **Run** and **Score:** a stage log.
- **Worker:** the process that runs the trials queued for it, outside the request that asked for them.
- **Job:** a started run or scoring queued for the worker, at its endpoint, for its owner, scored afterwards or not.
- **Record** / **ledger:** events logged while running or scoring.
- **Seal:** the hash over a log's started row and item rows, kept in its finished row.
- **Finding:** a warning or info produced when something declared doesn't match what was observed, or when a setting is risky.
- **Canary:** a fixed, non-sensitive probe request.
- **Wire-body:** a request as sent: with the streaming options, and the secret in a header. May hold sensitive content.
- **Vetted:** a fact within the planned clearance pipeline.
- **Portal:** the web-interface used to configure factors, watch runs and export results.
- **World:** factor parameters outside of the orchestrator's direct control. (the vignette source, model files, the Nix closure, the chat-template file, the remote engine)
- **Inventory:** files written by ops that say where vignette sources, endpoints and hosts are (`docs/inventory.md`).
- **Facts:** ops- or developer-authored knowledge about models (how each reasoning level is expressed, collapsed,
  refused or landed on its nearest, recommended sampling, output caveats, specs), typed in code, written in TOML and
  stored by init-data as components of kind `facts`, a thread per model, corrected by a new version. Not factors:
  they work out a reasoning level and a recommended sampling for the recipe's model when compiled.
- **Start-up:** what the start-up script runs for one endpoint, joining an engine (what) with inventory entries (where)
  (`docs/inventory.md`, "The start-up").
- **Rig:** the chatddx software that builds cages from factors, runs and scores inside them and records what happened.

### Roles mentioned
These roles are distinct and not overlapping, a person may inhabit more than one role.
- **Clinicians:** Owners of vignettes and authors of Appendices and Expectations
- **Researchers:** Authors of Sampling, Judges and Trials, and of a scorer's views, free parameters and labels
- **Developers:** Authors of schemas, canary sets, scoring and text-cleanup functions
- **Ops**: Owners of engines and authors of the engine's components

## Requirements
- Due to the chaotic nature of both emergency clinicians and inference servers alike, LLM judges will be needed to be carefully orchestrated to score outputs against sloppy notes.
- Conversely, simple and reliable scoring methods are needed to produce clean easily processed outputs, which will require strict and simple pattern matching.
- Due to the sensitive nature of patient data passing through the orchestrator, a separate path is needed where data can be passed along revealing just enough for the orchestrator to fulfill its duty. Cases will enter the system de-identified from a predefined source.
- Nothing can be expected of the vignettes: They may or may not include labs and imaging results, and may even lack basic details such as age or sex. The source exposes no revision identifier.
- Portal interfaces for managing instructions, few-shots, prompts, output, sampling, reasoning, passthrough, translations, toolsets, recipes, appendices, expectations, trials, scorers, judges, scorings and starting and monitoring runs.
- Engines, models, canary sets, expectation schemas and scoring code are authored by ops or developers and shipped. A
  scorer's views, free parameters and labels are written by researchers in the portal, who pick its scoring code,
  expectation schema and resources among those shipped.
- a self-contained bundle that can be verified offline
- scripts that can read the World to import factor parameters.
- import scripts that fingerprint World inputs (model files, closure, chat template, vignettes) into factors.
- a start-up that the start-up script reads (`agents/wip-deploy.md`, "The NixOS module")

### Intended evolution of configurations
The researchers will want to iterate and continuously refine configurations according to the following workflow.
1. Chunks are added by hand-edits
2. Successful variations are saved as configurations proper
3. Unsuccessful variations are deleted
4. A configuration with several successful variations branch out
5. Unsuccessful configurations are deleted

A configuration is a request kept on a skeleton thread, each version with the recipe it was compiled from, and a
variation is one with recipe parts replaced over one of its versions. A variation being tried is just a digest;
saving it makes it a configuration of its own, a fork, or a new version of one of the person's own.

Names are optional: an unnamed configuration is shown by its title, e.g. its base and what it varies.

## Vignettes and anything made from them are sensitive
The vignette and content produced from it: fills, requests, completions, tool arguments and results, judge requests and
responses, an engine's error that echoes a request; are all sensitive. Every part in the system that touches this data
must label it "sensitive".

## The clearance pipeline
Sensitive content may go only where it is cleared to go, so sending it to an engine that isn't cleared, judge engines
included, must be refused, and so must storing it, showing it at an edge, handing it to a tool's third party or
exporting it where it isn't.

## Findings and errors
A finding has a level (`warning` by default, or `info`), a code, a message and optionally the subject it concerns.
It is anything declared that doesn't match what was observed, and anything risky, becomes a finding. The run and
score checks return their findings, and a finished row holds the findings the runner or scorer saw while working,
such as `case.drift`; the run and score checks can be repeated from the stored rows at any time, so their findings
aren't stored.

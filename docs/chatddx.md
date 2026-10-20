# The ChatDDX Rig - requirements and design notes

## Purpose

ChatDDX is a system to measure how accurately LLMs generate differential diagnoses and management plans from
emergency-care case vignettes.

The rig provides:

- an environment that can be provably reconstructed (the "cage").
- means to record each exchange within the cage: what was planned, what was sent and what came back.
- first principles for sensitive data so that policies governing this data can be enforced.

It must be possible to deliver the cage together with the results, for scientific rigor.

## Requirements

- Due to the chaotic nature of both emergency clinicians and inference servers alike, LLM judges will be needed to be
  carefully orchestrated to score outputs against sloppy notes.
- Conversely, simple and reliable scoring methods are needed to produce clean easily processed outputs, which will
  require strict and simple pattern matching.
- Due to the sensitive nature of patient data passing through the orchestrator, a separate path is needed where data can
  be passed along revealing just enough for the orchestrator to fulfill its duty. Cases will enter the system
  de-identified from a predefined source.
- Nothing can be expected of the vignettes: They may or may not include labs and imaging results, and may even lack
  basic details such as age or sex. The source exposes no revision identifier.
- Portal interfaces for managing instructions, few-shots, prompts, output, sampling, reasoning, passthrough,
  translations, toolsets, recipes, appendices, expectations, trials, scorers, judges, scorings and starting and
  monitoring runs.
- Engines, models, canary sets, expectation schemas and scoring code are authored by ops or developers and shipped. A
  scorer is put together by researchers in the portal (`docs/modules/factors.md`, "Scorer"). code and expectation schema
  among those shipped.
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

What a configuration and a variation are, and how a variation is kept, is the catalog's (docs/modules/catalog.md,
"Configurations and variations").

## Vignettes and anything made from them are sensitive

The vignette and content produced from it: fills, requests and responses, tool arguments and results, judge requests and
responses, an engine's error that echoes a request; are all sensitive. Every part in the system that touches this data
must label it "sensitive".

## The clearance pipeline

Sensitive content may go only where it is cleared to go, so sending it to an engine that isn't cleared, judge engines
included, must be refused, and so must storing it, showing it at an edge, handing it to a tool's third party or
exporting it where it isn't.

## Findings

A finding is a non-catastrophic inconsistency discovered at start-up or runtime (docs/backlog.md, "Differentiate
start-up and runtime findings"). They are a separate layer on top of ordinary exceptions to isolate rig-level
irregularities from application-level exceptions, and are listed separately in the generated references at
docs/reference/*. All findings are listed in docs/glossary.md, "Findings".

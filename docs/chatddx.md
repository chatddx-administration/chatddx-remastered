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
  scorer's views, free parameters, labels and resources are written by researchers in the portal, who pick its scoring
  code and expectation schema among those shipped.
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

A configuration is a skeleton thread, each version with the recipe it was compiled from, and a variation is one with
recipe parts replaced over one of its versions. A variation being tried is a plain value, of which nothing is stored;
saving it makes it a configuration of its own, a fork, or a new version of one of the person's own.

Names are optional: an unnamed configuration is shown by its title, e.g. its base and what it varies.

## Vignettes and anything made from them are sensitive

The vignette and content produced from it: fills, requests and responses, tool arguments and results, judge requests and
responses, an engine's error that echoes a request; are all sensitive. Every part in the system that touches this data
must label it "sensitive".

## The clearance pipeline

Sensitive content may go only where it is cleared to go, so sending it to an engine that isn't cleared, judge engines
included, must be refused, and so must storing it, showing it at an edge, handing it to a tool's third party or
exporting it where it isn't.

## Findings and errors

A finding has a level (`warning` by default, or `info`), a code, a message and optionally the subject it concerns. It is
anything declared that doesn't match what was observed, and anything risky, becomes a finding. The run and score checks
return their findings, and a finished row holds the findings the runner or scorer saw while working, such as
`case.drift`; the run and score checks can be repeated from the stored rows at any time, so their findings aren't
stored.

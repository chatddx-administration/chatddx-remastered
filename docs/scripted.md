# Scripted runs

A scripted run is a run made to be looked at: a genuine record of something a run can go through, answered by the fake
vLLM from a script instead of by a model. Everything but the model's words is genuine: the variation, the trial, the
requests, the ledger and the scores. Scripted runs are for every edge that shows runs, the repl's `runs` and `replay`,
the API's runs and items and the portal's pages to come, and for tests that read runs they don't make.

This document describes what a scripted run is and how it runs. The code is `chatddx.scripted` (src/chatddx/scripted/)
and its command in src/chatddx/cli.py. Scripted runs build on the bench, the fake vLLM and the World.

## A scripted run
A scripted run is a file in a World's `_runs/`, named after the run: `<world>/_runs/<name>.toml`. The leading `_` says
the World itself doesn't read it, as with the data set in `_data/` (docs/inventory.md, "Worlds").

| Key | Meaning |
| --- | --- |
| `description` | What the run shows. Required. |
| `configuration` | The configuration, as the bench finds it on the endpoint's model (`Bench.configuration`): `plan` is `plan (en, Qwen/Qwen3-8B-AWQ)` on a Qwen3 endpoint. One made in several languages is named whole, such as `free-text-guided (sv, Qwen/Qwen3-8B-AWQ)`. Required. |
| `set` | Parts to set in the variation, each part to a chunk's name, or to `none` for none. |
| `endpoint` | The World's endpoint the run goes to. Required. |
| `cases` | The cases, by family id, or `<id> with <appendix>[, <appendix>]` for a case that sends appendices, as init-data titles it. At least one. |
| `seed` | The run's seed, 7 by default. |
| `stop_after` | Halt the run once a call has streamed this many tokens. |
| `unfinished` | Leave the run without its finish, as when the process running it dies. |
| `scored` | Score the finished run under every scorer that applies. True by default. |
| `[[turn]]` | The fake's answers, one per call in the order the run sends them (docs/vllm.md, "Scripts"). |

A file with any other key, or a turn the fake can't read, is refused when it is read, naming the file.

## Running one
The variation is the configuration with `set` applied, and the cases are found by their titles (`Bench.case_titled`).
The fake for the endpoint is served at the endpoint's address with the run's turns as its script, and the run is
started, sent and finished through the bench, as the repl runs one (`Bench.start`, `Running.send`, `Running.finish`).
`stop_after` is the run's own halt. A scored run is then scored by `Bench.score`, with a fake without a script at each
judge's endpoint, so a judge answers as the fake does by itself.

The fake for an endpoint is the one `chatddx fake-engines` serves there (`fakes.py:fake_at`, which the command uses
too): for a local engine, from its start-up, which must run the fake vLLM; for a remote engine, a stand-in on this
machine that asks for the key in the variable the endpoint's credential names: in the sample World,
`CHATDDX_SAMPLE_KEY`, which `.env-devshell` and `.env-container` set to `sample-key`. A scripted run serves its own
fakes on the endpoints' ports, so nothing else may listen there.

The fake stays a leaf: it reads a script and knows nothing of the bench. The scripted runs are the edge that joins
them.

## The command
`chatddx scripted-runs LOGIN [--world DIR] [--again] [NAME …]` runs the World's scripted runs, or the ones named, as
LOGIN, after `chatddx init-data LOGIN --giftbag`. One whose trial LOGIN has a run of already isn't run again unless
`--again` is given; it is said as run before, with that run. Each gets a line: its configuration and cases, how its
items ended, its scorers, and the run's id. It serves its own fakes, so `chatddx fake-engines` must not be running.

## The runs
The sample World's ten:

| Run | Configuration on endpoint | Cases | Shows |
| --- | --- | --- | --- |
| `typical` | `plan` on `qwen3-8b-awq@fake` | `DutchFall10w` | A plan thought through once and answered in one go, held to its schema. |
| `invalid` | `plan-prompted` on `gpt-oss-20b@fake` | `Dutchfall12w` | A plan shown its schema with nothing enforcing it, which breaks it. |
| `broken` | `free-text` on `qwen3-8b-awq@fake` | `Dutchfall13w` | A server that goes away halfway through the answer. |
| `runaway` | `diagnoses` on `gpt-oss-20b@fake` | `Dutchfall14w` | A structured answer that runs away in newlines, cut short by the runner. |
| `stopped` | `free-text-guided (sv, …)` on `qwen3-8b-awq@fake` | `casesfromedn2` | A Swedish run halted as it streams. |
| `unfinished` | `diagnoses` on `qwen3-8b-awq@fake` | `Dutchfall15w` | A run never finished, and so never scored. |
| `judged` | `free-text` on `qwen3-8b-awq@fake` | `Dutchfall11w` | An answer to a case Olof wrote notes on, scored by the judges as well as the patterns. |
| `appendix` | `diagnoses` on `qwen3-8b-awq@fake` | `Dutchfall11w with ultrasound` | An appendix that changes the right answer. |
| `several` | `diagnoses` on `qwen3-8b-awq@fake` | four | Answers well, a 503 while the engine loads, and a server that goes away. |
| `remote` | `free-text` on `mistral-small@remote` | `Dutchfall14w` | A run on the remote engine, whose endpoint asks for a key. |

The test World's six are the same shapes on its cases: `valid`, `stopped`, `unfinished`, `several` (not scored),
`judged` and `appendix`.

## Tests
src/chatddx/scripted/test/.

- `test_scripted_runs.py` reads the test World's scripted runs from `ran`, which ran each on `curated`, alice's: how
  each item ended, that a run is finished unless `unfinished` and scored when it is finished and `scored`, that
  judges answer as plain fakes, what a run's file can't say, and, on `curated`, the command running each once and
  finding a run made before.
- `test_sample_world.py` starts from `sampled`, the sample World loaded with alice's giftbag
  (src/chatddx/conftest.py), and runs its ten, each to its outcome, with the judge calls of `judged`.
- The repl's tests of looking back run the test World's scripted runs for runs to look at
  (src/chatddx/repl/test/test_reviewing.py).
- `ran` (src/chatddx/conftest.py) is `curated` with alice's scripted runs each run once, copied for each test, for
  tests that read runs they don't make: the portal's (src/chatddx/portal/test/test_reading.py).

## Terms

| Term | Meaning |
| --- | --- |
| Scripted run | A run made to be looked at, written as a file in a World's `_runs/` and answered by the fake from its script. |
| Script | The turns the fake answers with, one per call. |
| Stand-in | The fake vLLM serving a remote engine's model on this machine, at the remote endpoint's address. |

## Open design issues

### No scripted run has tool rounds
The gate refuses tools on a sensitive source (docs/runner.md, "The gate"), and both Worlds' sources are sensitive, as
a real one is, so no scripted run can send a tool round on their cases. The old chatddx's sample runs `broken` and
`rich` searched the web. A take: a made-up source that isn't sensitive, once calibration wants a tool round to show,
with the web patched in the process that runs the tools (`urllib.request.urlopen`, src/chatddx/tools/web_search.py).

### Smaller issues
```
AGENT: replace
A run sends its endpoint's canary set now, and the Worlds' endpoints name none.
---
- **No scripted run sends a canary set**: the Worlds' endpoints name none (docs/inventory.md, "Endpoints"), and a
  scripted run's turns would have to answer its canaries too.
```
- **No scripted run sends a canary set.** `Bench.start` passes none (docs/bench.md, "Runs and scores"), though both
  data sets hold one.
- **No two scripted runs vary a part over the same cases**, as the page to compare runs wants
  (agents/wip-portal.md, "Comparing variations").
- **`set` and `--again` have no test**, and no scripted run sets a part.

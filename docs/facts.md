# Facts

To ask a model something, the rig needs to know things about it that a request doesn't say: how each reasoning
level is expressed for this model, or that it's refused; which sampling its makers recommend for each level; which
output contracts work with it and with what caveats. Facts are that knowledge, written by ops and developers, one
model at a time.

Facts are not factors (docs/factors.md, "Not factors"). They never reach the wire themselves: they write literal
chunks before compilation, and they check chunks that are already written. No component refers to them, so no digest
depends on them, and correcting a guessed fact changes nothing stored. A skeleton still means exactly what it sends.

This document describes what facts hold, what they are for and why. Names, fields, rules and finding codes are in the
API, docs/facts-api.md. Facts build on the factors and nothing else, and the factors don't depend on them.

## Where facts come from
Facts are files, one entry per model, loaded by whoever needs them. Nothing is stored in the database, and their
history is git's. A model's facts are in one file, so they are never pieced together from several.

Facts are about a model, by its name: the repository a local engine's model comes from, or the model a remote engine
names. An engine's facts are its model's, and an engine whose model has none has none.

`init-data` and the `repl` load the bundled facts, a World's `facts.toml` when it has one, and the files `--facts`
names, beside each other.

## What a model's facts hold
Every part is optional. A missing part means "unknown", not "no". Facts say no with a refusal, which always says why.

### Reasoning
Reasoning is asked for by *level*: off, on, minimal, low, medium, high or xhigh, the old chatddx's intents. For each
level, the facts say one of three things:
- how the model is asked for it: the reasoning effort and the chat template arguments its reasoning chunk sets;
- that it *collapses* into another level: for a model that either thinks or doesn't, asking for low is asking for on;
- that the model refuses it, and why: a model that always reasons can't be asked not to.

A level *lands* where its collapses end: on a way of asking, on a refusal, or on nothing when the level it reaches is
unknown. Facts whose collapses go round, or end on nothing, are refused when they are loaded, so following a level
always gives an answer, a refusal or "unknown".

The model's *default* is the level it uses when a request says nothing about reasoning, and it lands like any other
level. The facts also say whether the model takes a thinking budget, or refuse one.

### Sampling
The facts hold, per level, the sampling the model's makers recommend. A request gets the recommendation for the level
it lands on, so one recommendation serves every level that collapses into it.

They may also say what the server fills in when a chunk leaves a value out. That is descriptive only.

### Output
For each output contract, native, tool and text (docs/factors.md, "Output"), the facts say that it works, with a
caveat if there is one, or that the model refuses it. Which contract the model is usually asked for is descriptive
only.

### Specs
A model's family, size, quantization, context length and licence are descriptive only.

## Writing chunks
Facts apply when a chunk is written. Given a model and a level, or the model's default, they write the literal
reasoning chunk and sampling chunk that level calls for. Values given for the sampling chunk replace the recommended
ones, and a thinking budget can be added to the reasoning chunk.

They refuse, with the fact's reason when there is one, when the level doesn't land on a way of asking (no default is
known, or the level is refused or unknown), when a budget is asked of a model that refuses one or isn't known to take
one, and when nothing is recommended for the level.

Today `chatddx init-data` is the only writer (docs/curation.md). A factors file asks for a chunk from facts and
gets one for each model that an engine it plans serves and the facts know, named after that model, together with
one of each recipe that uses it. A model the facts don't know, a model no planned engine serves, and a chunk the
facts refuse, with the recipes that need it, are skipped and reported.

## Checking pairs
A trial or a judge pairs a skeleton with an engine, whose model may have facts. Checking the pairs warns when the
skeleton was written for another model than the one it is paired with, or asks the model for something its facts
refuse:
- Its reasoning settings match none of the ways the model is known to be asked for a level, so they were written for
  another model: a thinking switch sent to a model that has none, or "no reasoning" sent to one that always reasons.
  A skeleton that leaves reasoning to the model isn't checked.
- Its sampling is what the facts recommend for another model, and for none of this model's levels, so it was written
  for that model: Qwen3's sampling sent to gpt-oss. This is checked even when the paired model has no facts.
  Sampling that is no model's recommendation, such as greedy, is the skeleton's own choice and isn't checked, and
  neither is sampling the paired model's facts recommend too.
- It asks a model that refuses a thinking budget for one.
- Its output contract is one the model refuses.

It also notes, without warning, the facts' caveat on the skeleton's contract, and a pair whose model has no facts, so
that the checks above that need them were skipped.

Facts also feed one of the factors' own lints (docs/factors.md, "Lints"): whether an engine's model reasons when a
request says nothing, which is when its default lands on a level other than off. The lint about a grammar that
constrains the answer before the model can reason uses it for skeletons that leave reasoning to the model: it warns
when the model reasons, says nothing when it doesn't, and only notes it when that is unknown. An engine started with
default chat template arguments of its own changes the model's default, so it stays a note.

Without facts, linting is unchanged.

## Bundled facts
chatddx ships facts about the two models of the sample:
- Qwen/Qwen3-8B-AWQ thinks or doesn't, by a switch in its chat template, so every level from minimal up collapses into
  on. It takes a thinking budget, and its makers recommend different sampling with thinking on and off.
- openai/gpt-oss-20b always reasons, at a low, medium or high effort, so off, minimal and xhigh are refused, and so is
  a thinking budget. On collapses into medium, its default.

## Terms

| Term | Meaning |
| --- | --- |
| Facts | What is known about a model that a request doesn't say, written by people, one model at a time. |
| Level | What a request asks of reasoning: off, on, minimal, low, medium, high or xhigh. |
| Default | The level a model uses when a request says nothing about reasoning. |
| Collapse | A level that is asked for as another. |
| Refusal | A fact that says the model can't do something, and why. |
| Land | Where a level ends after its collapses: on a way of asking, a refusal, or nothing known. |
| Recommended sampling | The sampling a model's makers recommend for a level. |

## Open design issues
These are open questions of design. Where the code falls short of this document, the API says so
(docs/facts-api.md, "Known gaps").

- **xhigh can't be written.** It's a level, but no reasoning effort says it, so a model can only collapse or refuse
  it. Adding the effort is additive, if a model that supports it shows up.
- **Tool choice on harmony.** Named and required tool choices are unverified for gpt-oss. vLLM 0.24's gpt-oss tool
  parser accepts both, so the JSON-array grammar applies; whether harmony's output survives it isn't known.
- **A model or a model on a runtime.** Some facts are really about a model on a runtime, such as harmony ignoring the
  response format. They live on the model for now; facts keyed by runtime can be added when a second runtime
  appears.
- **Defaults from the command line.** An engine's own default chat template arguments and generation config change
  the model's defaults. Facts describe the model's own defaults, and only the grammar-before-reasoning lint accounts
  for the change.

### Smaller issues
- **A budget with reasoning off is written.** Qwen3's off with a budget turns thinking off and sets a thinking budget.
- **Unread recommendations.** A recommendation for a level that collapses never writes a chunk, and nothing reports
  it. Checking pairs still counts it as the model's.
- **An unknown budget passes the check.** A budget sent to a model whose budget is unknown isn't warned about, while
  writing one is refused.
- **Unknown reasoning fails the check.** A skeleton's reasoning settings are compared only with the ways of asking the
  facts know, so a model whose reasoning is unknown, or a skeleton using a level nothing is known about, gets the
  warning, though a missing part otherwise means "unknown".
- **A refused default is accepted.** A default that lands on a refusal loads, and whether the model reasons by default
  is then unknown.

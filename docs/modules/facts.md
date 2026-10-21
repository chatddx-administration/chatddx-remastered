# Facts

Facts about models are used to smooth over implementation details and make the models somewhat easier to compare: How
each reasoning level is expressed for a model, which sampling its makers recommend for each level, which output
contracts work with it and with what caveats.

They never reach the wire themselves. A chunk may ask for an intent, a reasoning level or the recommended sampling, and
compiling a recipe works out what it sends from the facts about the recipe's model; and its compilation names the facts
it was worked out from. Correcting a guessed fact changes nothing stored: a skeleton still means exactly what it sends.

## Where facts come from

Facts are written in files, one entry per model, and their history as written is git's. A model's facts are in one file,
so they are never pieced together from several. `init-data` loads the bundled facts, a World's `facts.toml` when it has
one, and the files `--facts` names, beside each other, and stores the facts about each model an engine of the World
serves as a component of kind `facts`, a thread of the archive's named after the model (docs/modules/curation.md).
Correcting a fact and loading again makes a new version of its thread.

A configuration sent in another language than its own is its recipe compiled into that language, against the facts its
own compilation names rather than the current ones when nothing is replaced, so that the translation differs from it by
its texts alone (docs/modules/bench.md, "Translations"). A correction reaches the translation as it reaches the
configuration, by following its facts.

## What a model's facts hold

Every part is optional. A missing part means "unknown", not "no". Facts say no with a refusal, which always says why.

### Reasoning

Reasoning is asked for by _level_: off, on, minimal, low, medium, high or xhigh, the old chatddx's intents. For each
level, the facts say one of three things:

- how the model is asked for it: the reasoning effort and the chat template arguments the request sends;
- that it _collapses_ into another level: for a model that either thinks or doesn't, asking for low is asking for on;
- that the model refuses it, and why: a model that always reasons can't be asked not to. The refusal may name the
  level's _nearest_, the level it lands on instead: gpt-oss, asked not to reason, reasons at low.

A level _lands_ where its collapses and nearests end: on a way of asking, on a refusal, or on nothing when the level it
reaches is unknown. Facts whose collapses or nearests go round, or end on nothing, are refused when they are loaded, so
following a level always gives an answer, a refusal or "unknown". A collapse says two levels are one request; a nearest
says they aren't, and the landing keeps the refusal's reason, so the repl, the API and the portal can say `off → low`
and why.

The model's _default_ is the level it uses when a request says nothing about reasoning, and it lands like any other
level. The facts also say whether the model takes a thinking budget, or refuse one; a budget has no nearest, so a
refused one stays refused.

### Sampling

The facts hold, per level, the sampling the model's makers recommend. A recommended sampling gets the recommendation for
the level the recipe's reasoning lands on, or for the model's default when the recipe asks for no level, so one
recommendation serves every level that collapses into it or lands on it as its nearest.

They may also say what the server fills in when a chunk leaves a value out. That is descriptive only.

### Output

For each output contract, native, tool and text (docs/modules/factors.md, "Output"), the facts say that it works, with a
caveat if there is one, or that the model refuses it. Which contract the model is usually asked for is descriptive only.

### Specs

A model's family, size, quantization, context length and licence are descriptive only.

## Compiling intents

Facts apply when a recipe is compiled (docs/modules/factors.md, "Recipe and compilation"). A reasoning chunk that asks
for a level, the model's default among them, sends what the level lands on; a sampling chunk that asks for the
recommended sampling sends the recommendation for the level the reasoning lands on, or for the model's default, with the
values the chunk sets itself in place of recommended ones. A thinking budget can stand beside a level.

Compiling refuses, with the fact's reason when there is one, when the level doesn't land on a way of asking (no default
is known, or the level is refused or unknown), when a budget is asked of a model that refuses one or isn't known to take
one, when nothing is recommended for the level, and when the engine's model has no facts. A chunk that sets the effort,
the chat template arguments or the sampling values itself is literal, and compiles as it is on any model.

`chatddx init-data` stores the facts and compiles each recipe against them (docs/modules/curation.md, "Loading"). A
factors file asks for an intent as it writes any chunk, `level = "off"` or `recommended = true`
(docs/modules/curation.md, "Factors", "Intents").

## Checking pairs

A trial pairs a skeleton with an engine, and a judge pairs one with weights, whose model may have facts. Checking the
skeleton was written for another model than the one it is paired with, or asks the model for something its facts refuse:

- Its reasoning settings match none of the ways the model is known to be asked for a level, so they were written for
  another model: a thinking switch sent to a model that has none, or "no reasoning" sent to one that always reasons. A
  skeleton that leaves reasoning to the model isn't checked.
- Its sampling is what the facts recommend for another model, and for none of this model's levels, so it was written for
  that model: Qwen3's sampling sent to gpt-oss. This is checked even when the paired model has no facts. Sampling that
  is no model's recommendation, such as greedy, is the skeleton's own choice and isn't checked, and neither is sampling
  the paired model's facts recommend too.
- It asks a model that refuses a thinking budget for one.
- Its output contract is one the model refuses.

A skeleton compiled from intents for the model it is sent to sends what that model's facts say (see "Compiling
intents"), so the reasoning and sampling checks matter for literal chunks, hand-written skeletons, and a skeleton sent
to another model than its recipe's.

`init-data` checks with the facts it loaded from files, the bench with the stored ones.

It also notes, without warning, the facts' caveat on the skeleton's contract, and a pair whose model has no facts, so
that the checks above that need them were skipped.

Facts also feed one of the factors' own lints (docs/modules/factors.md, "Lints"): whether an engine's model reasons when
a request says nothing, which is when its default lands on a level other than off. The lint about a grammar that
constrains the answer before the model can reason uses it for skeletons that leave reasoning to the model: it warns when
the model reasons, says nothing when it doesn't, and only notes it when that is unknown. An engine started with default
chat template arguments of its own changes the model's default, so it stays a note.

Without facts, linting is unchanged.

## Bundled facts

chatddx ships facts about the two models of the sample:

- Qwen/Qwen3-8B-AWQ thinks or doesn't, by a switch in its chat template, so every level from minimal up collapses into
  on. It takes a thinking budget, and its makers recommend different sampling with thinking on and off.
- openai/gpt-oss-20b always reasons, at a low, medium or high effort, so off and minimal are refused and land on low as
  their nearest, xhigh on high, and a thinking budget is refused. On collapses into medium, its default.

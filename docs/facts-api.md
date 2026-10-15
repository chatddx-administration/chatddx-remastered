# Facts API

```
AGENT: replace
Built (agents/wip-engine-part.md, stage 1): facts are stored, and their classes are the factors'. The paragraph.
---
Reference for the `chatddx.facts` package. It was written from `src/chatddx/facts/*`, `src/chatddx/factors/facts.py`
and `docs/facts.md`. There are no facts migrations: facts are stored as components of kind `facts`
(docs/factors-api.md, "facts.py"), and their threads are the catalog's. What facts are and why they are shaped this
way is in `docs/facts.md`; this file says what each name accepts, returns and raises. Factor types it uses
(`Component`, `Registry`, `Sampling`, `Skeleton`, `Trial`, `Judge`, `Finding`, …) are in `docs/factors-api.md`.
```
Reference for the `chatddx.facts` package. It was written from `src/chatddx/facts/*` and
`docs/facts.md`. There are no facts migrations, because facts aren't stored. What facts are and why they are shaped
this way is in `docs/facts.md`; this file says what each name accepts, returns and raises. Factor types it uses
(`Component`, `Registry`, `Reasoning`, `Sampling`, `Skeleton`, `Trial`, `Judge`, `Finding`, …) are in
`docs/factors-api.md`.

Paths are relative to `src/chatddx/facts/` unless they start with `src/`, `docs/` or `agents/`.

## Contents
- [Package](#package)
- [Conventions](#conventions)
```
AGENT: replace
Built (agents/wip-engine-part.md, stage 1): most of what models.py held is `chatddx.factors.facts`. The line.
---
- [models.py](#modelspy): levels, refusals, landings, writes, reasoning, sampling and output facts, `ModelFacts`
  (from `chatddx.factors.facts`), and `Facts`
```
- [models.py](#modelspy): levels, refusals, writes, reasoning, sampling and output facts, `ModelFacts`, `Facts`
- [The facts file](#the-facts-file)
- [lint.py](#lintpy): `reasons`, `check_pairs`, `lints`
- [Finding codes](#finding-codes)
- [Bundled facts](#bundled-facts)
- [Known gaps](#known-gaps)
- [Beyond docs/facts.md](#beyond-docsfactsmd)

## Package

```
AGENT: replace
Built (agents/wip-engine-part.md, stage 1): the facts' classes are defined in the factors, and facts are stored. The
section's text.
---
`chatddx.facts` re-exports every public name of `src/chatddx/factors/facts.py` and of its own two modules: `BUNDLED`,
`INTENTS`, `ContractFact`, `Effort`, `Facts`, `Intent`, `Landing`, `ModelFacts`, `OutputFacts`, `ReasoningFact`,
`ReasoningFacts`, `Refusal`, `Refused`, `SamplingFacts`, `SamplingValues`, `Writes`, `check_pairs`, `lints`,
`model_name` and `reasons`.

| Module | Builds on |
| --- | --- |
| `src/chatddx/factors/facts.py` | `chatddx.factors.{base,engine}` |
| `models.py` | `chatddx.factors.{base,facts}` |
| `lint.py` | `models.py`, `chatddx.factors.{base,bundle,facts,lint,request,scoring,trial}` |

The package imports no chatddx package but `chatddx.factors`, no third-party package but pydantic, and holds no SQL;
`chatddx.factors` doesn't import it. It reads facts files, for init-data, and checks pairs. init-data stores the facts
(src/chatddx/curation/plan.py:plan_factors), and the bench reads them back (src/chatddx/bench/seen.py:Seen.facts).
```
`chatddx.facts` re-exports every public name of both modules: `BUNDLED`, `INTENTS`, `ContractFact`, `Effort`,
`Facts`, `Intent`, `ModelFacts`, `OutputFacts`, `ReasoningFact`, `ReasoningFacts`, `Refusal`, `Refused`,
`SamplingFacts`, `SamplingValues`, `Writes`, `check_pairs`, `lints`, `model_name` and `reasons`.

| Module | Builds on |
| --- | --- |
| `models.py` | `chatddx.factors.{base,bundle,engine,request}` |
| `lint.py` | `models.py`, `chatddx.factors.{base,bundle,lint,request,scoring,trial}` |

The package imports no chatddx package but `chatddx.factors`, no third-party package but pydantic, and holds no SQL;
`chatddx.factors` doesn't import it. Nothing is stored: whoever needs facts loads them and passes them on.

## Conventions

```
AGENT: replace
Built (agents/wip-engine-part.md, stage 1): a model's facts are a component. The paragraph.
---
**Models.** Every model derives from `chatddx.factors.base.Frozen`: frozen, `extra="forbid"`. Building one validates
it, so an unknown key in a facts file is a `ValidationError` ("Extra inputs are not permitted"). `ModelFacts` is a
component, kind `facts`, with a digest and a canonical form; a compilation refers to the facts it was compiled against
(`/facts`), and no other component refers to them. Its parts aren't components.
```
**Models.** Every model derives from `chatddx.factors.base.Frozen`: frozen, `extra="forbid"`. Building one validates
it, so an unknown key in a facts file is a `ValidationError` ("Extra inputs are not permitted"). Facts aren't
components: they have no `kind`, digest or canonical form, and no component refers to them.

**Unknown.** Every field is optional. `None`, or a missing key in the file, means "unknown", not "no". A refusal says
"no" with a reason.

```
AGENT: replace
Built (agents/wip-engine-part.md, stage 1): no function writes chunks any more. The paragraph.
---
**Levels and efforts.** A level is an `Intent`. An effort is a level or `"default"`, the level the model uses when a
request says nothing about reasoning. `ReasoningFacts.resolve` takes an effort, as `Reasoning.level` holds one.
```
**Levels and efforts.** A level is an `Intent`. An effort is a level or `"default"`, the level the model uses when a
request says nothing about reasoning. Functions that write chunks take an effort.

**Errors.**

```
AGENT: replace
Built (agents/wip-engine-part.md, stage 1): the facts refuse intents rather than chunks, and look engines up through
a resolver. The `Refused`, `pydantic.ValidationError` and `StructuralError` rows.
---
| `Refused` (a `ValueError`) | The facts refuse an intent, or don't know enough to compile one: `ReasoningFacts.resolve`, `ModelFacts.check_budget`, `ModelFacts.recommended`. `reasons_by_default` catches it, and `chatddx.factors.request.landings` turns it into a `StructuralError`. |
| `pydantic.ValidationError` | Facts that break their own rules: an unknown key, a wrong type, collapses or nearests that go round or land on nothing. Rules written as validators raise `ValueError`, which pydantic wraps. |
| `chatddx.factors.base.StructuralError` (a `ValueError`) | `model_name`, `Facts.about`, `reasons` and `check_pairs` when a component they look up isn't known to the resolver or is of the wrong kind (`Registry.get`, `resolve`). |
```
| Exception | When |
| --- | --- |
| `Refused` (a `ValueError`) | A chunk can't be written from the facts: `ReasoningFacts.resolve`, `ModelFacts.reasoning_chunk`, `ModelFacts.sampling_chunk`. `reasons_by_default` catches it. |
| `ValueError` | `Facts.load`: a top-level table other than `model`, or a model with facts in more than one file. `ReasoningFacts.land`: collapses that go round. |
| `pydantic.ValidationError` | Facts that break their own rules: an unknown key, a wrong type, collapses that go round or land on nothing. A chunk that `Reasoning` or `Sampling` refuses: a negative budget, an unknown override. Rules written as validators raise `ValueError`, which pydantic wraps. |
| `tomllib.TOMLDecodeError` (a `ValueError`), `OSError` | `Facts.load` of a file that isn't TOML or can't be read. |
| `chatddx.factors.base.StructuralError` (a `ValueError`) | `model_name`, `Facts.about`, `reasons` and `check_pairs` when a component they look up isn't in the registry or is of the wrong kind (`Registry.get`, `resolve`). |

## models.py

```
AGENT: add
Built (agents/wip-engine-part.md, stage 1): where the names are defined. A paragraph after `## models.py`.
---
`BUNDLED` and `Facts` are defined here; every other name of this section is defined in `src/chatddx/factors/facts.py`
and re-exported.
```
### Names and constants

| Name | Value |
| --- | --- |
| `BUNDLED` | `Path` of `models.toml`, next to `models.py` |
| `Intent` | `Literal["off", "on", "minimal", "low", "medium", "high", "xhigh"]` |
| `Effort` | `Intent \| Literal["default"]` |
| `INTENTS` | `("off", "on", "minimal", "low", "medium", "high", "xhigh")`, in that order |
| `ReasoningFact` | `Intent \| Refusal \| Writes`: a collapse into another level, a refusal, or writes |

### `class Refused(ValueError)`
```
AGENT: replace
Built (agents/wip-engine-part.md, stage 1): facts refuse intents when compiling. The paragraph.
---
Raised when the facts refuse an intent, or don't know enough to compile one. Its message is the refusal's reason, or
one of the messages under `ReasoningFacts.resolve` and `ModelFacts`.
```
Raised when the facts refuse a chunk, or don't know enough to write one. Its message is the refusal's reason, or one
of the messages under `ReasoningFacts.resolve` and `ModelFacts`.

### `class Refusal(Frozen)`
```
AGENT: replace
Built (agents/wip-engine-part.md, "Nearest"): a refusal may name its nearest. The line.
---
`refused: str`, at least one character: why the model can't do it. `nearest: Intent | None = None`: for a level, the
level it lands on instead. Only a level's nearest is followed; a budget's or an output contract's is ignored.
```
`refused: str`, at least one character: why the model can't do it.

### `class Writes(Frozen)`
```
AGENT: replace
Built (agents/wip-engine-part.md, stage 1): writes are sent by compiling, not set in a chunk. The line.
---
What a level sends, as `reasoning_effort` and `chat_template_kwargs`.
```
What a level's `Reasoning` chunk sets.

| Field | Type | Default |
| --- | --- | --- |
| `effort` | `Literal["none", "minimal", "low", "medium", "high"] \| None` | `None` |
| `chat_template_kwargs` | `Settings` (`dict[str, JsonValue]`, keys sorted) | `{}` |

Both may be left out: `{}` is a write that sets nothing.

### `class ReasoningFacts(Frozen)`
How each level is expressed for a model.

| Field | Type | Default |
| --- | --- | --- |
| `default` | `Intent \| None` | `None`; the level the model uses when a request says nothing |
| `off`, `on`, `minimal`, `low`, `medium`, `high`, `xhigh` | `ReasoningFact \| None` | `None` |
| `budget` | `Literal["thinking_token_budget"] \| Refusal \| None` | `None`; whether the model takes a thinking budget |

```
AGENT: replace
Built (agents/wip-engine-part.md, "Nearest"): landing follows nearests too, and gives a `Landing`. This paragraph,
the `land` and `resolve` rows, and the paragraph after the table.
---
A string entry is a collapse into that level; a table with `refused` is a `Refusal`, with `nearest` when it names one;
any other table is `Writes`.

| `land(intent: Intent) -> tuple[Intent, Refusal \| Writes \| None, tuple[str, ...]]` | Follows collapses, and refusals that name a nearest, from `intent`, and returns the level it reaches, that level's entry (writes, a refusal without a nearest, or `None` when it has no entry), and the reasons of the refusals it passed on, in order. `ValueError("<a> -> <b> -> <a>: the collapses go round")` for a cycle, which validation already rules out. |
| `resolve(effort: Effort) -> Landing` | The `Landing` of `effort`: the level it lands on, its writes, and `land`'s reasons as `nearest`. `"default"` reads `default`. `Refused("no default reasoning level is known")` for `"default"` without one; `Refused("nothing is known about reasoning '<level>'")` when it lands on nothing, naming the level it reached; `Refused(<reason>)` when it lands on a refusal. |

Building one checks every collapse and every refusal's nearest, in `INTENTS` order, and then `default` the same way:
each must land on writes or a refusal. One that lands on nothing raises `ValueError("'<level>' collapses into
'<target>', which ends in no fact")` (`'default'` for the default); one that goes round raises `land`'s `ValueError`.
Both are wrapped in `ValidationError`. A `default` that lands on a refusal is accepted.
```
A string entry is a collapse into that level; a table with `refused` is a `Refusal`; any other table is `Writes`.

| Member | Returns / raises |
| --- | --- |
| `fact(intent: Intent) -> ReasoningFact \| None` | The level's own entry. |
| `land(intent: Intent) -> tuple[Intent, Refusal \| Writes \| None]` | Follows collapses from `intent` and returns the level it reaches and that level's entry: writes, a refusal, or `None` when it has no entry. `ValueError("<a> -> <b> -> <a>: the collapses go round")` for a cycle, which validation already rules out. |
| `resolve(effort: Effort) -> tuple[Intent, Writes]` | The level `effort` lands on, with its writes. `"default"` reads `default`. `Refused("no default reasoning level is known")` for `"default"` without one; `Refused("nothing is known about reasoning '<level>'")` when it lands on nothing, naming the level it reached; `Refused(<reason>)` when it lands on a refusal. |
| `realized() -> dict[Intent, Writes]` | The levels whose own entry is writes, in `INTENTS` order. Collapses and refusals are left out. |

Building one checks every collapse, in `INTENTS` order, and then `default` the same way: each must land on writes or
a refusal. A collapse that lands on nothing raises `ValueError("'<level>' collapses into '<target>', which ends in no
fact")` (`'default'` for the default); one that goes round raises `land`'s `ValueError`. Both are wrapped in
`ValidationError`. A `default` that lands on a refusal is accepted.

```
AGENT: add
Built (agents/wip-engine-part.md, "Nearest"): where a level landed. A section before this one.
---
### `class Landing(Frozen)`
Where a level lands, as `ReasoningFacts.resolve` gives it.

| Field | Type | Default |
| --- | --- | --- |
| `level` | `Intent` | required; the level landed on |
| `writes` | `Writes` | required; what it sends |
| `nearest` | `tuple[str, ...]` | `()`; the reasons of the refusals passed on to their nearest, in order: empty unless the level landed on is a nearest |
```
### `class SamplingValues(Frozen)`
The sampling fields of a `Sampling` chunk: `temperature`, `top_p`, `min_p`, `presence_penalty`,
`frequency_penalty` and `repetition_penalty` as `float | None`, and `top_k` as `int | None`, all defaulting to `None`.
`stop`, `max_output_tokens` and `max_tokens_key` aren't among them.

### `class SamplingFacts(Frozen)`

| Field | Type | Default |
| --- | --- | --- |
| `recommended` | `dict[Intent, SamplingValues]` | `{}`; per level, what the model's makers recommend |
| `generation_config` | `SamplingValues \| None` | `None`; what the server fills in when a chunk leaves a field out. Nothing reads it. |

### `class ContractFact(Frozen)`
`note: str | None = None`. The contract works; `note` is a caveat. `{}` in the file is a `ContractFact` without a
note.

### `class OutputFacts(Frozen)`

| Field | Type | Default |
| --- | --- | --- |
| `default` | `Literal["native", "tool", "text"] \| None` | `None`; the contract the model is usually asked for. Nothing reads it. |
| `native`, `tool`, `text` | `ContractFact \| Refusal \| None` | `None` |

`fact(kind: Literal["native", "tool", "text"]) -> ContractFact | Refusal | None` returns the field of that name.

```
AGENT: replace
Built (agents/wip-engine-part.md, stage 1): a model's facts are a component that names its model. The heading, and
two rows at the top of the table.
---
### `class ModelFacts(Component)`, kind `facts`
| `kind` | `Literal["facts"]` | `"facts"` |
| `model` | `str`, at least one character | required; the model's name, `model_name`'s |
```
### `class ModelFacts(Frozen)`
What is known about one model.

| Field | Type | Default |
| --- | --- | --- |
| `family` | `str \| None` | `None` |
| `parameters_b` | `float \| None` | `None` |
| `active_parameters_b` | `float \| None` | `None` |
| `quantization` | `str \| None` | `None` |
| `context_length` | `int \| None` | `None` |
| `licence` | `str \| None` | `None` |
| `reasoning` | `ReasoningFacts` | `ReasoningFacts()` |
| `sampling` | `SamplingFacts` | `SamplingFacts()` |
| `output` | `OutputFacts` | `OutputFacts()` |

The six specs are descriptive: nothing reads them.

```
AGENT: replace
Built (agents/wip-engine-part.md, stage 1): nothing writes chunks from facts; compiling asks the facts instead
(docs/factors-api.md, "landings"). The `reasoning_chunk` and `sampling_chunk` sections.
---
#### `check_budget() -> None`
Whether a thinking budget may stand beside a level: `Refused("nothing is known about a thinking budget")` when
`reasoning.budget` is `None`, `Refused(<reason>)` when it is a refusal, nothing when it is `"thinking_token_budget"`.

#### `recommended(level: Intent) -> SamplingValues`
`sampling.recommended[level]`, for the level a recommended sampling follows, as landed. `Refused("no sampling is
recommended for reasoning '<level>'")` without an entry. An entry for a level that collapses, or lands on its nearest,
is never asked for. `Sampling.over` puts a chunk's own values over it (docs/factors-api.md, "Sampling").
```
#### `reasoning_chunk(effort: Effort = "default", budget: int | None = None) -> Reasoning`
A literal `Reasoning` chunk for this model:
1. `reasoning.resolve(effort)`, which raises `Refused` as described there;
2. when `budget` is given: `Refused("nothing is known about a thinking budget")` when `reasoning.budget` is `None`,
   or `Refused(<reason>)` when it is a refusal;
3. `Reasoning(effort=writes.effort, chat_template_kwargs=writes.chat_template_kwargs,
   thinking_token_budget=budget)`. A negative budget is a `ValidationError`.

The level is resolved before the budget is checked, so a refused level's reason is the one raised. A budget is
written with any level, `off` included.

#### `sampling_chunk(effort: Effort = "default", **overrides: JsonValue) -> Sampling`
A literal `Sampling` chunk with what is recommended for the level `effort` lands on:
1. `reasoning.resolve(effort)`, which raises `Refused` as described there, also when sampling for that level would be
   known;
2. `Refused("no sampling is recommended for reasoning '<level>'")` when `sampling.recommended` has no entry for the
   level it landed on. An entry for a level that collapses is never read;
3. `Sampling.model_validate({**recommended values that are set, **overrides})`.

An override replaces a recommended value, and may set any `Sampling` field, `stop`, `max_output_tokens` and
`max_tokens_key` included; an override of `None` removes a recommended value; an unknown key is a `ValidationError`.
`Sampling`'s greedy rule applies: with `temperature == 0`, `top_p`, `top_k` and `min_p` are dropped.

#### `reasons_by_default() -> bool | None`
Whether the model reasons when a request says nothing: `reasoning.resolve("default")` lands on a level other than
`off`. `None` when that raises `Refused`: no default, or a default that lands on a refusal.

```
AGENT: replace
Built (agents/wip-engine-part.md, stage 1): it takes a digest and a resolver. The section.
---
### `model_name(engine: str, get: Resolver) -> str | None`
The name facts are keyed by, for the component `get` resolves the digest `engine` to:
- a `LocalEngine`: its model artifact's `repo`, through `resolve(get, engine.model, ModelArtifact)`;
- a `RemoteEngine`: its `model`;
- any other component: `None`.
```
### `model_name(engine: Component, registry: Registry) -> str | None`
The name facts are keyed by:
- a `LocalEngine`: its model artifact's `repo`, through `resolve(registry.get, engine.model, ModelArtifact)`;
- a `RemoteEngine`: its `model`;
- any other component: `None`.

### `class Facts(Frozen)`
`models: dict[str, ModelFacts] = {}`, keyed by model name.

#### `load(*paths: Path) -> Self` (classmethod)
```
AGENT: replace
Built (agents/wip-engine-part.md, stage 1): a model's facts name it. The line.
---
Reads the files in order, then validates all their models at once, each with its table's name as `model`. No paths
give `Facts()`. Raises:
```
Reads the files in order, then validates all their models at once. No paths give `Facts()`. Raises:
- `OSError`, or `tomllib.TOMLDecodeError` for a file that isn't TOML;
- `ValueError("<path>: facts have only 'model' tables")` for a file with any other top-level key;
- `ValueError("'<name>' has facts in more than one file")` for a model in a second file, also when the same file is
  given twice;
- `ValidationError` for facts that break their rules.

```
AGENT: replace
Built (agents/wip-engine-part.md, stage 1): facts are also made from stored ones, and engines are looked up by
digest. The section, and one before it.
---
#### `of(found: Iterable[ModelFacts]) -> Self` (classmethod)
The facts given, keyed by their `model`; a later one replaces an earlier one about the same model. The bench makes its
facts so from the stored ones (src/chatddx/bench/seen.py:Seen.facts).

#### `about(engine: str, get: Resolver) -> ModelFacts | None`
`models.get(model_name(engine, get))`, or `None` when the engine has no model name or the facts don't know it.
```
#### `about(engine: Component, registry: Registry) -> ModelFacts | None`
`models.get(model_name(engine, registry))`, or `None` when the engine has no model name or the facts don't know it.

## The facts file
A TOML file of `[model."<name>"]` tables, each a `ModelFacts`, with the parts as sub-tables:

```toml
[model."Qwen/Qwen3-8B-AWQ"]
family = "qwen3"

[model."Qwen/Qwen3-8B-AWQ".reasoning]
default = "on"
off = { chat_template_kwargs = { enable_thinking = false } }   # writes
on = { chat_template_kwargs = { enable_thinking = true } }
low = "on"                                                    # a collapse
budget = "thinking_token_budget"

[model."Qwen/Qwen3-8B-AWQ".sampling.recommended]
on = { temperature = 0.6, top_p = 0.95, top_k = 20, presence_penalty = 1.5 }

[model."Qwen/Qwen3-8B-AWQ".output]
native = {}                                                   # works, no note
text = { refused = "…" }                                      # a refusal
```

```
AGENT: add
Built (agents/wip-engine-part.md, "Nearest"): a refusal may name its nearest, and a table's name is its model. A
paragraph before this one.
---
A refused level may name the level it lands on instead, `off = { refused = "…", nearest = "low" }`. A table's name is
its facts' `model`.
```
Keys are the field names above; anything else is refused.

## lint.py

### `reasons(facts: Facts, registry: Registry) -> Reasons`
A `chatddx.factors.lint.Reasons` (`Callable[[str], bool | None]`) to pass as `reasons=` to
`src/chatddx/factors/lint.py:lint`. Given an engine's digest, it returns `None` when the facts don't know the
engine's model, else that model's `reasons_by_default()`. It looks the engine up with `registry.get`, so an unknown
digest raises `StructuralError` when the lint calls it. `vllm.grammar_before_reasoning` uses it
(`docs/factors-api.md`, "lint.py").

### `check_pairs(registry: Registry, facts: Facts, digests: Iterable[str] | None = None) -> list[Finding]`
Checks each trial and judge among `digests`, or among every component of `registry`, in the registry's insertion
order, when `digests` is `None`. Other kinds are skipped. For each pair it resolves the engine and the skeleton
(`StructuralError` when one isn't there or the skeleton isn't one), and returns findings with the trial's or judge's
digest as subject, in this order:

1. Without facts about the engine's model: `facts.missing` (info). With them:
   1. `facts.reasoning_unmatched` when the skeleton body's `(reasoning_effort, chat_template_kwargs or {})` isn't
      `(None, {})` and equals the `(effort, chat_template_kwargs)` of none of `reasoning.realized()`. The comparison
      is exact: any key in `chat_template_kwargs` counts. A model without writes at any level gets it for every
      skeleton that sets either.
   2. `facts.budget_refused` when the body has `thinking_token_budget` and `reasoning.budget` is a refusal. An
      unknown budget passes.
   3. For `output.fact(skeleton.contract.kind)`: `facts.output_refused` for a refusal, `facts.output_note` (info)
      for a `ContractFact` with a note, nothing otherwise.
2. `facts.sampling_unmatched`, also without facts about the paired model. The skeleton body's `SamplingValues` keys
   are compared with every model's recommendations, each put through `Sampling` (greedy rule, unset values left out)
   and cut to the same keys. Nothing when the body sets none of the keys, or when the paired model's facts recommend
   exactly those values at some level. Otherwise one finding when other models' facts recommend them at some level,
   naming those models in sorted order. Every entry of `sampling.recommended` counts, also one for a level that
   collapses.

```
AGENT: add
Built (agents/wip-engine-part.md, stage 1): which facts the callers pass. A sentence at the end of the section.
---
init-data passes the facts it loaded from files (src/chatddx/curation/write.py), and the bench the stored ones
(src/chatddx/bench/seen.py:Seen.facts).
```
### `lints(registry, facts, digests, languages=None) -> list[Finding]`
The factors' lints of `digests` (`chatddx.factors.lint.lint`, with `reasons(facts, registry)` and `languages`) and
`check_pairs`, in that order.

## Finding codes

| Code | Level | Message |
| --- | --- | --- |
| `facts.missing` | info | `no facts about '<name>', so model-level checks were skipped` (`<name>` is the model name's `repr`) |
| `facts.reasoning_unmatched` | warning | `the configuration's reasoning settings match none of the model's reasoning levels` |
| `facts.budget_refused` | warning | the budget's refusal reason |
| `facts.output_refused` | warning | the contract's refusal reason |
| `facts.output_note` | info | the contract's note |
| `facts.sampling_unmatched` | warning | `the configuration's sampling is what the facts recommend for <models, joined by ", ">, not for <name>` |

The subject is always the trial's or judge's digest.

## Bundled facts
`models.toml` (`BUNDLED`):

```
AGENT: replace
Built (agents/wip-engine-part.md, "Nearest"): gpt-oss's refused levels land on their nearest. The `off`, `minimal`
and `xhigh` rows.
---
| `off` | writes `enable_thinking = false` | refused, nearest `low` |
| `minimal` | → `on` | refused, nearest `low` |
| `xhigh` | → `on` | refused, nearest `high` |
```
| | `Qwen/Qwen3-8B-AWQ` | `openai/gpt-oss-20b` |
| --- | --- | --- |
| Specs | `qwen3`, 8.2 B, `awq`, 32768, `apache-2.0` | `gpt-oss`, 21 B (3.6 B active), `mxfp4`, 131072, `apache-2.0` |
| `default` | `on` | `medium` |
| `off` | writes `enable_thinking = false` | refused |
| `on` | writes `enable_thinking = true` | → `medium` |
| `minimal` | → `on` | refused |
| `low`, `medium`, `high` | → `on` | writes `effort` of the same name |
| `xhigh` | → `on` | refused |
| `budget` | `thinking_token_budget` | refused |
| `recommended` | `on`: temperature 0.6, top_p 0.95, top_k 20, presence_penalty 1.5; `off`: temperature 0.7, top_p 0.8, top_k 20, presence_penalty 1.5 | `low`, `medium`, `high`: temperature 1.0, top_p 1.0 |
| `generation_config` | temperature 0.6, top_p 0.95, top_k 20 | empty |
| `output` | `default = "native"`; `native`, `tool`, `text` without notes | `default = "native"`; a note on `native` (harmony renders no `response_format`); `tool`, `text` without notes |

## Known gaps
From `docs/facts.md`, "Open design issues":
- `xhigh` can't be written: neither `Writes.effort` nor `Reasoning.effort` has the value.
- Named and `required` tool choices are unverified for gpt-oss.
- Some facts are about a model on a runtime, and live on the model.
- An engine's `--default-chat-template-kwargs` and `--generation-config` change the model's defaults; only
  `vllm.grammar_before_reasoning` accounts for the first.
```
AGENT: replace
Built (agents/wip-engine-part.md, stage 1): facts apply when compiling. This item and the two after it.
---
- A budget with reasoning off is compiled.
- A `sampling.recommended` entry for a level that collapses, or lands on its nearest, is never asked for by
  `ModelFacts.recommended`, and nothing reports it.
- An unknown budget passes `facts.budget_refused`, while compiling one beside a level refuses it (`check_budget`).
```
- A budget with reasoning off is written.
- A `sampling.recommended` entry for a level that collapses is never read by `sampling_chunk`, and nothing reports
  it.
- An unknown budget passes `facts.budget_refused`, while `reasoning_chunk` refuses to write it.
- Unknown reasoning fails `facts.reasoning_unmatched`: a model without writes at any level, or a skeleton using a
  level nothing is known about, gets the warning.
- A `default` that lands on a refusal loads, and `reasons_by_default` then says `None`.

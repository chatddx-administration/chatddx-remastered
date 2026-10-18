# Facts API

Reference for the `chatddx.facts` package. It was written from `src/chatddx/facts/*`, `src/chatddx/factors/facts.py`
and `docs/facts.md`. There are no facts migrations: facts are stored as components of kind `facts`
(docs/factors-api.md, "facts.py"), and their threads are the catalog's. What facts are and why they are shaped this
way is in `docs/facts.md`; this file says what each name accepts, returns and raises. Factor types it uses
(`Component`, `Registry`, `Sampling`, `Skeleton`, `Trial`, `Judge`, `Finding`, …) are in `docs/factors-api.md`.

Paths are relative to `src/chatddx/facts/` unless they start with `src/`, `docs/` or `agents/`.

## Contents
- [Package](#package)
- [Conventions](#conventions)
- [models.py](#modelspy): levels, refusals, landings, writes, reasoning, sampling and output facts, `ModelFacts`
  (from `chatddx.factors.facts`), and `Facts`
- [The facts file](#the-facts-file)
- [lint.py](#lintpy): `reasons`, `check_pairs`, `lints`
- [Finding codes](#finding-codes)
- [Bundled facts](#bundled-facts)
- [Beyond docs/facts.md](#beyond-docsfactsmd)

## Package

`chatddx.facts` re-exports every public name of `src/chatddx/factors/facts.py` and of its own two modules: `BUNDLED`,
`INTENTS`, `ContractFact`, `Effort`, `Facts`, `Intent`, `Landing`, `ModelFacts`, `OutputFacts`, `ReasoningFact`,
`ReasoningFacts`, `Refusal`, `Refused`, `SamplingFacts`, `SamplingValues`, `Writes`, `check_pairs`, `lints` and
`reasons`.

| Module | Builds on |
| --- | --- |
| `src/chatddx/factors/facts.py` | `chatddx.factors.{base,engine}` |
| `models.py` | `chatddx.factors.{base,facts}` |
| `lint.py` | `models.py`, `chatddx.factors.{base,bundle,facts,lint,request,scoring,trial}` |

The package imports no chatddx package but `chatddx.factors`, no third-party package but pydantic, and holds no SQL;
`chatddx.factors` doesn't import it. It reads facts files, for init-data, and checks pairs. init-data stores the facts
(src/chatddx/curation/plan.py:plan_factors), and the bench reads them back (src/chatddx/bench/seen.py:Seen.facts).

## Conventions

**Models.** Every model derives from `chatddx.factors.base.Frozen`: frozen, `extra="forbid"`. Building one validates
it, so an unknown key in a facts file is a `ValidationError` ("Extra inputs are not permitted"). `ModelFacts` is a
component, kind `facts`, with a digest and a canonical form; a compilation refers to the facts it was compiled against
(`/facts`), and no other component refers to them. Its parts aren't components.

**Unknown.** Every field is optional. `None`, or a missing key in the file, means "unknown", not "no". A refusal says
"no" with a reason.

**Levels and efforts.** A level is an `Intent`. An effort is a level or `"default"`, the level the model uses when a
request says nothing about reasoning. `ReasoningFacts.landing` takes an effort, as `Reasoning.level` holds one.

## models.py

`BUNDLED` and `Facts` are defined here; every other name of this section is defined in `src/chatddx/factors/facts.py`
and re-exported.

### Names and constants

| Name | Value |
| --- | --- |
| `BUNDLED` | `Path` of `models.toml`, next to `models.py` |
| `Intent` | `Literal["off", "on", "minimal", "low", "medium", "high", "xhigh"]` |
| `Effort` | `Intent \| Literal["default"]` |
| `INTENTS` | `("off", "on", "minimal", "low", "medium", "high", "xhigh")`, in that order |
| `ReasoningFact` | `Intent \| Refusal \| Writes`: a collapse into another level, a refusal, or writes |

### `class Refused(ValueError)`
Raised when the facts refuse an intent, or don't know enough to compile one. Its message is the refusal's reason, or
one of the messages under `ReasoningFacts.landing` and `ModelFacts`.

### `class Refusal(Frozen)`
`refused: str`, at least one character: why the model can't do it. `nearest: Intent | None = None`: for a level, the
level it lands on instead. Only a level's nearest is followed; a budget's or an output contract's is ignored.

### `class Writes(Frozen)`
What a level sends, as `reasoning_effort` and `chat_template_kwargs`.

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

A string entry is a collapse into that level; a table with `refused` is a `Refusal`, with `nearest` when it names one;
any other table is `Writes`.

| `landing(effort: Effort) -> Landing` | The `Landing` of `effort`: following collapses, and refusals that name a nearest, the level it lands on, its writes, and the reasons of the refusals it passed on, in order, as `nearest`. `"default"` reads `default`. `Refused("no default reasoning level is known")` for `"default"` without one; `Refused("nothing is known about reasoning '<level>'")` when it lands on nothing, naming the level it reached; `Refused(<reason>)` when it lands on a refusal. `ValueError("<a> -> <b> -> <a>: the collapses go round")` for a cycle, which validation already rules out. |
| `resolve(effort: Effort) -> Landing` | The `Landing` of `effort`: the level it lands on, its writes, and `land`'s reasons as `nearest`. `"default"` reads `default`. `Refused("no default reasoning level is known")` for `"default"` without one; `Refused("nothing is known about reasoning '<level>'")` when it lands on nothing, naming the level it reached; `Refused(<reason>)` when it lands on a refusal. |

Building one checks every collapse and every refusal's nearest, in `INTENTS` order, and then `default` the same way:
each must land on writes or a refusal. One that lands on nothing raises `ValueError("'<level>' collapses into
'<target>', which ends in no fact")` (`'default'` for the default); one that goes round raises `land`'s `ValueError`.
Both are wrapped in `ValidationError`. A `default` that lands on a refusal is accepted.

### `class Landing(Frozen)`
Where a level lands, as `ReasoningFacts.landing` gives it.

| Field | Type | Default |
| --- | --- | --- |
| `level` | `Intent` | required; the level landed on |
| `writes` | `Writes` | required; what it sends |
| `nearest` | `tuple[str, ...]` | `()`; the reasons of the refusals passed on to their nearest, in order: empty unless the level landed on is a nearest |

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

### `class ModelFacts(Component)`, kind `facts`
What is known about one model.

| Field | Type | Default |
| --- | --- | --- |
| `kind` | `Literal["facts"]` | `"facts"` |
| `model` | `str`, at least one character | required; the model's name, a local model's repository or a remote model's `name` (`chatddx.factors.engine.model_of`) |
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

#### `check_budget() -> None`
Whether a thinking budget may stand beside a level: `Refused("nothing is known about a thinking budget")` when
`reasoning.budget` is `None`, `Refused(<reason>)` when it is a refusal, nothing when it is `"thinking_token_budget"`.

#### `recommended(level: Intent) -> SamplingValues`
`sampling.recommended[level]`, for the level a recommended sampling follows, as landed. `Refused("no sampling is
recommended for reasoning '<level>'")` without an entry. An entry for a level that collapses, or lands on its nearest,
is never asked for. `Sampling.over` puts a chunk's own values over it (docs/factors-api.md, "Sampling").

#### `reasons_by_default() -> bool | None`
Whether the model reasons when a request says nothing: `reasoning.landing("default")` lands on a level other than
`off`. `None` when that raises `Refused`: no default, or a default that lands on a refusal.

### `class Facts(Frozen)`
`models: dict[str, ModelFacts] = {}`, keyed by model name.

#### `load(*paths: Path) -> Self` (classmethod)
Reads the files in order, then validates all their models at once, each with its table's name as `model`. No paths
give `Facts()`. Raises:
- `OSError`, or `tomllib.TOMLDecodeError` for a file that isn't TOML;
- `ValueError("<path>: facts have only 'model' tables")` for a file with any other top-level key;
- `ValueError("'<name>' has facts in more than one file")` for a model in a second file, also when the same file is
  given twice;
- `ValidationError` for facts that break their rules.

#### `of(found: Iterable[ModelFacts]) -> Self` (classmethod)
The facts given, keyed by their `model`; a later one replaces an earlier one about the same model. The bench makes its
facts so from the stored ones (src/chatddx/bench/seen.py:Seen.facts).

#### `about(digest: str, get: Resolver) -> ModelFacts | None`
`models.get(model_of(digest, get).name)`: the facts about the model `digest` names, or the model an engine `digest`
serves; `None` when the facts don't know it.

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

A refused level may name the level it lands on instead, `off = { refused = "…", nearest = "low" }`. A table's name is
its facts' `model`.

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

init-data passes the facts it loaded from files (src/chatddx/curation/write.py), and the bench the stored ones
(src/chatddx/bench/seen.py:Seen.facts).

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

| | `Qwen/Qwen3-8B-AWQ` | `openai/gpt-oss-20b` |
| --- | --- | --- |
| Specs | `qwen3`, 8.2 B, `awq`, 32768, `apache-2.0` | `gpt-oss`, 21 B (3.6 B active), `mxfp4`, 131072, `apache-2.0` |
| `default` | `on` | `medium` |
| `off` | writes `enable_thinking = false` | refused, nearest `low` |
| `on` | writes `enable_thinking = true` | → `medium` |
| `minimal` | → `on` | refused, nearest `low` |
| `low`, `medium`, `high` | → `on` | writes `effort` of the same name |
| `xhigh` | → `on` | refused, nearest `high` |
| `budget` | `thinking_token_budget` | refused |
| `recommended` | `on`: temperature 0.6, top_p 0.95, top_k 20, presence_penalty 1.5; `off`: temperature 0.7, top_p 0.8, top_k 20, presence_penalty 1.5 | `low`, `medium`, `high`: temperature 1.0, top_p 1.0 |
| `generation_config` | temperature 0.6, top_p 0.95, top_k 20 | empty |
| `output` | `default = "native"`; `native`, `tool`, `text` without notes | `default = "native"`; a note on `native` (harmony renders no `response_format`); `tool`, `text` without notes |

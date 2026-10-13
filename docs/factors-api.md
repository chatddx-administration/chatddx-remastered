# Factors API

Reference for the `chatddx.factors` package and the `factor` database schema. It was written from
`src/chatddx/factors/*`, `docs/factors.md` and `src/chatddx/store/migrations/000{1,2,3}-*-factor.sql`. What factors
are and why they are shaped this way is in `docs/factors.md`; this file says what each name accepts, returns and
raises.

Paths are relative to `src/chatddx/factors/` unless they start with `src/` or `docs/`.

## Contents
- [Package](#package)
- [Conventions](#conventions)
- [base.py](#basepy): common types, `Component`, canonical form, `Fingerprint`, `Code`, `Finding`
- [bundle.py](#bundlepy): `Registry`, `Bundle`
- [kinds.py](#kindspy): registry of all kinds
- [Component kinds](#component-kinds): every kind, its class, references and cross-checks
- [cases.py](#casespy): vignettes, appendices, cases, text cleanup, `prepare_case`
- [request.py](#requestpy): chunks, recipes, compilation, skeletons, rendering, tool rounds
- [engine.py](#enginepy): model artifacts, local and remote engines
- [trial.py](#trialpy): trials, seeds, canaries, execution
- [scoring.py](#scoringpy): expectations, judges, views, scorers, scorings
- [select.py](#selectpy): selectors, splits, reachability
- [lint.py](#lintpy): `lint` and its findings
- [Finding codes](#finding-codes)
- [Database: schema `factor`](#database-schema-factor)
- [Known gaps](#known-gaps)

## Package

`chatddx.factors` re-exports `Bundle`, `Code`, `Component`, `Finding`, `Fingerprint`, `Registry`, `StructuralError`
and the modules `cases`, `engine`, `kinds`, `request`, `scoring` and `trial`. Import `chatddx.factors.lint` and
`chatddx.factors.select` by path.

The package imports no other chatddx package. It depends on pydantic, and `lint.py` also depends on `jsonschema` and
`referencing`.

## Conventions

**Models.** Every model is a pydantic model derived from `base.py:Frozen`: frozen, with `extra="forbid"`. Building
one validates it. Sequences are tuples.

**Errors.**

| Exception | When |
| --- | --- |
| `pydantic.ValidationError` | A model breaks its own rules: a wrong type, a duplicate seed, an owned flag in `argv`, U+0000 in a component. Rules written as validators raise `ValueError`, which pydantic wraps. |
| `base.py:StructuralError` (a `ValueError`) | A problem that takes other components, stored bytes or inputs to see: a missing or wrongly typed reference, a failed cross-check, a digest that doesn't match its bytes, an unknown kind or version, a missing translation, a vignette that isn't UTF-8. |
| `KeyError` | `render` with a slot fill missing (a known gap), and `Registry.raw` with an unknown digest. |
| `TypeError` | At class definition: a `Component` subclass whose `kind` has no literal default, or a duplicate kind. |

**Findings.** A `Finding` is a warning or an info about something valid but risky, or observed and not as declared.
Functions return findings; nothing stores them. All codes are listed under "Finding codes".

**Resolvers.** A `Resolver` is `Callable[[str], Component]`, usually `Registry.get`. Cross-checks and compilation
look components up through one.

## base.py

### Common types

| Name | Definition |
| --- | --- |
| `Digest` | `str` matching `^sha256:[0-9a-f]{64}$` |
| `Sha256Hex` | `str` matching `^[0-9a-f]{64}$` |
| `JsonPointer` | `str` matching `^(/([^~/]\|~[01])*)*$`. Defined; no field uses it. |
| `Api` | `Literal["chat.completions"]` |
| `Settings` | `dict[str, JsonValue]` whose top-level keys are sorted on validation; values keep their order |
| `Resolver` | `Callable[[str], Component]` |

### `StructuralError(ValueError)`
Raised for the problems listed under "Conventions".

### `class Component(Frozen)`
The base of every component kind.

| Member | Description |
| --- | --- |
| `schema_version: ClassVar[int] = 1` | The kind's schema version, written as `v`. Bump it when an existing field's meaning or default changes. |
| `kind_name -> str` | The kind, for example `"chunk.prompt"`. |
| `canonical_doc() -> dict[str, JsonValue]` | The canonical JSON document, `v` included (see "Canonical form"). |
| `canonical -> bytes` | Cached. `canonical_bytes(canonical_doc())`, or the stored bytes for a component read by `Registry.add_raw`. |
| `digest -> str` | Cached. `sha256:` + the SHA-256 of `canonical`. |
| `model_copy(*, update=None, deep=False) -> Self` | Without `update`, a plain copy. With `update`, the copy is validated anew and gets its own canonical form and digest. |
| `refs() -> list[RefSite]` | Every reference in the component (see "References"). |
| `cross_check(get: Resolver) -> list[str]` | Rules that need other components; returns problems. `[]` by default. |

Every component refuses U+0000 in any string or object key of its canonical form, because the store's `jsonb` column
can't hold it (`Component._storable`, `ValidationError`).

A subclass declares `kind: Literal["<kind>"] = "<kind>"`. The default is the kind name, and the class is listed in
`kinds.py:KINDS`, the only kinds stored bytes are read as.

### Canonical form

- `canonical_bytes(doc: JsonValue) -> bytes`: `json.dumps(doc, separators=(",", ":"), ensure_ascii=False,
  allow_nan=False)`, encoded as UTF-8.
- In every `Frozen` model, fields are sorted by name, and optional fields equal to their default are left out.
  `kind` (and `stage`) are always kept.
- `canonical_doc()` adds `v`, the class's `schema_version`, at the top level only.
- JSON data keeps its key order: schemas, expectation data, canary messages and values inside settings.
- The top-level keys of settings are sorted: request bodies, `chat_template_kwargs`, `params`, `env` and translation
  entries. A model artifact's files are sorted by path, and a trial's cases by digest.
- pydantic writes NaN and infinity as `null` (see "Known gaps").

### Helpers

| Function | Returns / raises |
| --- | --- |
| `sorted_keys(mapping: dict[str, V]) -> dict[str, V]` | The mapping with its keys sorted. |
| `distinct(values: tuple[T, ...]) -> tuple[T, ...]` | The values unchanged. `ValueError("duplicates are not allowed")` otherwise. |
| `sha256_digest(data: bytes) -> str` | `"sha256:" + hexdigest`. |
| `resolve(get: Resolver, digest: str, cls: type[C]) -> C` | `get(digest)`. `StructuralError` when it isn't a `cls`; whatever `get` raises when it's missing. |

### References

- `RefTo(*kinds: str)`: metadata on a digest field naming the kinds it may point to: `Annotated[Digest,
  RefTo("case")]`.
- `RefSite(path: str, kinds: tuple[str, ...], digest: str)`: one reference found in a component.
- `iter_refs(model: BaseModel, prefix: str = "") -> Iterator[RefSite]`: walks the field types, through nested
  models, optionals, unions, tuples, lists and dicts. `None` values are skipped.

A `path` is a JSON Pointer built from field names and positions, without `~` escaping: `/skeleton`, `/cases/0`,
`/recipe/prompt`, `/views/2/judge`. No field holds references under dict keys today.

### `class Fingerprint(Frozen)`

| Field | Type | Default |
| --- | --- | --- |
| `alg` | `Literal["sha256", "hmac-sha256"]` | `"sha256"` |
| `key_id` | `str \| None` | `None`. Required with `hmac-sha256`, and allowed only with it. |
| `hex` | `Sha256Hex` | required |

`Fingerprint.of(data: bytes, key: tuple[str, bytes] | None = None) -> Fingerprint`: plain SHA-256, or HMAC-SHA-256
with `key = (key_id, secret)`.

### `class Code(Frozen)`
Names code by `distribution: str`, `version: str` and `revision: str | None = None`. Used by `Tool.code`,
`Scorer.code`, `Compilation.compiler` and `Bundle.generator`.

### `class Finding(Frozen)`

| Field | Type | Default |
| --- | --- | --- |
| `level` | `Literal["info", "warning"]` | `"warning"` |
| `code` | `str` | required |
| `message` | `str` | required |
| `subject` | `str \| None` | `None`; the digest the finding concerns |

## bundle.py

### `class Registry`
Components by digest, in memory.

| Method | Description |
| --- | --- |
| `Registry()` | An empty registry. |
| `add(component) -> str` | Adds the component under its digest and returns it. Adding a digest that's already there keeps the first. |
| `add_raw(digest, raw: bytes) -> Component` | Adds stored bytes. `StructuralError("… does not match its bytes")` when `raw` doesn't hash to `digest`. Then parses them (`parse_component`) and pins the component's `canonical` to `raw` and its `digest` to `digest`, so the stored bytes decide the digest even when today's code would write them differently. Replaces any entry under that digest. |
| `get(digest) -> Component` | `StructuralError("… is not in the registry")` when missing. |
| `raw(digest) -> bytes` | The stored bytes. `KeyError` when missing. |
| `digest in registry`, `iter(registry)` | Membership, and the digests in the order they were added. |
| `closure(roots: Iterable[str]) -> list[str]` | The roots and everything they reference, transitively, sorted. `StructuralError` for a missing digest. |
| `check(digests: Iterable[str] \| None = None) -> None` | For each digest (all when `None`): every reference exists and has an allowed kind. When those hold, runs `cross_check`. Raises one `StructuralError` listing every problem, one per line, as `<digest><path>: …` or `<digest>: …`. |
| `bundle(roots, generator: Code) -> Bundle` | Sorts and de-duplicates the roots, checks their closure, and packs the stored text of every component in it. |

`cross_check` implementations assert the kinds of the references they resolve, so run them through `check`, which
checks the kinds first.

### `class Bundle(Frozen)`
A self-contained package that can be verified offline.

| Field | Type | Default |
| --- | --- | --- |
| `format` | `Literal["chatddx.bundle/1"]` | `"chatddx.bundle/1"` |
| `generator` | `Code` | required; the code that wrote the bundle |
| `roots` | `tuple[Digest, ...]` | required |
| `components` | `dict[Digest, str]` | required; digest → canonical text |

`load() -> tuple[Registry, list[Finding]]`:
1. adds every component with `Registry.add_raw` (`StructuralError` on a digest mismatch);
2. reports `bundle.recanonicalized` (warning, subject the digest) for each component that today's code would write
   differently. Its digest stays the stored one;
3. raises `StructuralError("roots missing from bundle: …")` when a root is absent;
4. runs `Registry.check()` over everything.

## kinds.py
`parse_component(data: bytes) -> Component`:
 Parses a JSON object by its `kind`. `StructuralError` when it isn't an object, the kind is unknown, or `v` isn't the
 class's `schema_version`. `ValidationError` for bad fields. Doesn't check any digest. The result has today's canonical
 form, not `data`. It reads only the kinds in `KINDS` lists.

`KINDS: tuple[type[Component], ...]`: every kind of component, in the order of "Component kinds".

`BY_KIND: dict[str, type[Component]]`: kind name → class, `TypeError` at import for a kind listed twice.

## Component kinds

| Kind | Class | References (path: kinds) | `cross_check` |
| --- | --- | --- | --- |
| `model` | `engine.py:ModelArtifact` | | |
| `engine.local` | `engine.py:LocalEngine` | `/model`: `model` | |
| `engine.remote` | `engine.py:RemoteEngine` | | |
| `chunk.instructions` | `request.py:Instructions` | | |
| `chunk.few_shot` | `request.py:FewShot` | | |
| `chunk.prompt` | `request.py:Prompt` | | |
| `chunk.output` | `request.py:Output` | | |
| `chunk.sampling` | `request.py:Sampling` | | |
| `chunk.reasoning` | `request.py:Reasoning` | | |
| `chunk.passthrough` | `request.py:Passthrough` | | |
| `chunk.toolset` | `request.py:Toolset` | `/tools/<i>`: `tool` | tool names are distinct |
| `chunk.translations` | `request.py:Translations` | | |
| `tool` | `request.py:Tool` | | |
| `skeleton` | `request.py:Skeleton` | `/tools/<i>`: `tool` | the body's functions, apart from the answer function, are the referenced tools, by name and in order |
| `compilation` | `request.py:Compilation` | `/recipe/<part>`: `chunk.<part>`; `/skeleton`: `skeleton` | |
| `appendix` | `cases.py:Appendix` | | |
| `case` | `cases.py:Case` | `/appendices/<i>`: `appendix` | every appendix is bound to the case's vignette |
| `trial` | `trial.py:Trial` | `/skeleton`: `skeleton`; `/engine`: `engine.local`, `engine.remote`; `/cases/<i>`: `case` | the skeleton's purpose is `generation` |
| `canary_set` | `trial.py:CanarySet` | | |
| `expectation_schema` | `scoring.py:ExpectationSchema` | | |
| `expectation` | `scoring.py:Expectation` | `/case`: `case`; `/expectation_schema`: `expectation_schema` | |
| `judge` | `scoring.py:Judge` | `/skeleton`: `skeleton`; `/engine`: `engine.local`, `engine.remote` | the skeleton's purpose is `judge`, and it has no tools |
| `scorer` | `scoring.py:Scorer` | `/expectation_schema`: `expectation_schema`; `/views/<i>/judge`: `judge` | |
| `scoring` | `scoring.py:Scoring` | `/scorer`: `scorer`; `/expectations/<i>`: `expectation` | every expectation uses the scorer's expectation schema; at most one expectation per case |

`kinds.py:KINDS` lists them in this order, and a test checks that every component class the package defines is listed
(src/chatddx/factors/test/test_factors.py, `test_every_kind_defined_is_written_down`).

A compilation's `<part>` is one of `instructions`, `few_shot`, `prompt`, `output`, `sampling`, `reasoning`,
`passthrough`, `translations` and `toolset`, pointing to the chunk kind of the same name.

Each kind also has a reference type for fields that point to it: `AppendixRef`, `CaseRef`, `ModelRef`, `EngineRef`
(both engine kinds), `ToolRef`, `SkeletonRef`, `TrialRef`, `CanarySetRef`, `ExpectationSchemaRef`, `ExpectationRef`,
`JudgeRef`, `ScorerRef` and `ScoringRef`.

## cases.py

### `class Vignette(Frozen)`
`source: str`, `id: str`, `fingerprint: Fingerprint` (of the raw bytes as fetched). The vignette's text is never
stored.

### `class Appendix(Component)`, kind `appendix`
| Field | Type | Default |
| --- | --- | --- |
| `vignette` | `Vignette` | required; the vignette it is bound to |
| `text` | `str`, at least 1 character | required; stored and sent as written |

### `class Case(Component)`, kind `case`
| Field | Type | Default |
| --- | --- | --- |
| `vignette` | `Vignette` | required |
| `appendices` | `tuple[AppendixRef, ...]` | `()`; the order is kept and is part of the digest |

`cross_check`: `"appendix … is bound to another vignette"`.

### Text cleanup
`CleanupOp = Literal["newlines.lf@1", "unicode.nfc@1", "strip@1", "blank_lines.collapse@1"]`.

`clean(text: str, ops: Sequence[CleanupOp]) -> str` applies the steps in order:

| Step | Effect |
| --- | --- |
| `newlines.lf@1` | `\r\n` and `\r` become `\n` |
| `unicode.nfc@1` | Unicode NFC normalization |
| `strip@1` | `str.strip()` |
| `blank_lines.collapse@1` | Two or more blank lines in a row become one. A line of only spaces and tabs counts as blank. |

### `class Prepared(Frozen)`
`fills: dict[SlotName, str]`, `fingerprint: Fingerprint` (of the raw bytes, as observed),
`findings: tuple[Finding, ...] = ()`.

### `prepare_case(case, raw, get, layout, cleanup=(), key=None) -> Prepared`

| Parameter | Type |
| --- | --- |
| `case` | `Case` |
| `raw` | `bytes`, the vignette as fetched from its source |
| `get` | `Resolver`, for the appendices |
| `layout` | `AppendixLayout`, usually the skeleton's |
| `cleanup` | `Sequence[CleanupOp]`, usually the trial's |
| `key` | `tuple[str, bytes] \| None`, the HMAC key when the case's fingerprint uses one |

1. Raises `StructuralError` when `key`'s id (or `None`) isn't the fingerprint's `key_id`.
2. Fingerprints `raw` and reports `case.drift` (warning, subject the case's digest) when it differs from the case's.
3. Decodes `raw` as UTF-8, dropping a leading byte-order mark. `StructuralError("vignette <source>/<id> isn't UTF-8:
   …")` otherwise.
4. Returns `fills = {"vignette": clean(text, cleanup), "appendices": layout.join(<appendix texts>)}`.

## request.py

### Names and constants

| Name | Value |
| --- | --- |
| `SlotName` | `Literal["vignette", "appendices", "completion", "expectation"]`: filled at send time |
| `InsertName` | `Literal["schema", "output_guidance", "tool_guidance"]`: filled at compile time |
| `SchemaOp` | `Literal["inline_refs@1"]` |
| `Purpose` | `Literal["generation", "judge"]` |
| `SLOTS_BY_PURPOSE` | `generation`: `vignette`, `appendices`. `judge`: all four slots. |
| `REQUIRED_SLOTS` | `generation`: `vignette`. `judge`: `completion`. |
| `INSERTS_BY_KIND` | `chunk.instructions`, `chunk.prompt`: `output_guidance`, `tool_guidance`. `chunk.output`: `schema`. |
| `RUNTIME_KEYS` | `model`, `messages`, `seed`, `stream`, `n`, `return_token_ids`: no chunk, skeleton or canary may set them |
| `OUTPUT_KEYS` | `response_format`, `tools`, `tool_choice` |
| `MANAGED_KEYS` | `temperature`, `top_p`, `top_k`, `min_p`, `presence_penalty`, `frequency_penalty`, `repetition_penalty`, `stop`, `max_completion_tokens`, `max_tokens`, `reasoning_effort`, `thinking_token_budget`, `chat_template_kwargs` |
| `BYPASS_KEYS` | `chat_template`, `structured_outputs`, `return_prompt_text`, `prompt_logprobs` |
| `GREEDY_DROPS` | `top_p`, `top_k`, `min_p` |
| `ToolName` | `str` matching `^[A-Za-z0-9_-]{1,64}$` |
| `EntryPoint` | `str` matching `^[\w.]+:[\w.]+$`, as `module:attribute` |
| `TRANSLATED` | `output`, `appendix_layout`, `toolset` |
| `RECIPE_PARTS` |  `instructions`, `few_shot`, `prompt`, `output`, `sampling`, `reasoning`, `passthrough`, `translations`, `toolset` |

### Segments and text

- `Slot(slot: SlotName)`.
- `Insert(insert: InsertName, before: str = "", after: str = "")`: `before` and `after` appear only when the
  inserted text isn't empty.
- `Segment = str | Slot`.
- `Text = str | tuple[str | Insert, ...]`: adjacent strings are merged and empty ones dropped on validation. A text
  without inserts becomes one plain string.
- `Message(role: Literal["system", "developer", "user", "assistant"], content: tuple[Segment, ...])`: at least one
  segment.
- `own_texts(chunk, get) -> tuple[str, ...]`: the texts a chunk holds itself, whitespace left out: a toolset's include
  its tools' descriptions and parameter prose, a translations chunk's are its translations, and any other component
  has none.

Slot rules, checked for a prompt and for a skeleton's messages together: only the purpose's slots, every required
slot, and none twice. Insert rules, per chunk: only the kind's inserts, and none twice.

### Chunks

#### `Instructions`, kind `chunk.instructions`
| Field | Type | Default |
| --- | --- | --- |
| `role` | `Literal["system", "developer"]` | `"system"` |
| `text` | `Text`, with the inserts `output_guidance` and `tool_guidance` | required |

#### `FewShot`, kind `chunk.few_shot`
`messages: tuple[Example, ...]`, at least one, where `Example(role: Literal["user", "assistant"], content: str)`.

#### `Prompt`, kind `chunk.prompt`
| Field | Type | Default |
| --- | --- | --- |
| `purpose` | `Purpose` | `"generation"` |
| `segments` | `tuple[str \| Slot \| Insert, ...]`, at least one, with the inserts `output_guidance` and `tool_guidance` | required. Literal segments are not merged, so each is looked up on its own by translations. |

#### Output contracts
`OutputContract` is a union discriminated by `kind`:

| Class | Fields |
| --- | --- |
| `NativeOutput` | `kind: "native"` |
| `ToolOutput` | `kind: "tool"`, `name: str`, `description: str \| None = None` (at least 1 character) |
| `TextOutput` | `kind: "text"`, `json_schema: dict[str, JsonValue] \| None = None`. In an `Output` chunk this must be `None` (the schema goes in `Output.json_schema`). In a skeleton it holds the output's schema. |

#### `Output`, kind `chunk.output`
| Field | Type | Default |
| --- | --- | --- |
| `contract` | `OutputContract` | required |
| `json_schema` | `dict[str, JsonValue] \| None` | `None`; required for `native` and `tool` |
| `guidance` | `Text \| None`, with the insert `schema` | `None`; `schema` needs a schema |
| `schema_ops` | `tuple[SchemaOp, ...]`, distinct | `()`; needs a schema |

- `output_schema -> dict | None`: `json_schema` with `schema_ops` applied in order. The ops run on validation, so a
  schema an op refuses fails validation.
- `guidance_text() -> str`: the guidance with `schema` filled as `json.dumps(output_schema, indent=2,
  ensure_ascii=False)`; `""` without guidance.

`inline_refs@1` replaces every local `$ref` (`#` or `#/…`, a JSON Pointer with `~0`/`~1` and percent-decoding) with
its target, and drops the top-level `$defs` and `definitions`. Nested ones stay, with their refs inlined. Keywords
beside a `$ref` override the target's. It refuses refs outside the schema, refs to nothing and recursive refs.
Refs inside top-level definitions that nothing uses are dropped unchecked.

#### `Sampling`, kind `chunk.sampling`
| Field | Type | Default |
| --- | --- | --- |
| `temperature`, `top_p`, `min_p`, `presence_penalty`, `frequency_penalty`, `repetition_penalty` | `float \| None` | `None` |
| `top_k` | `int \| None` | `None` |
| `stop` | `tuple[str, ...]` | `()` |
| `max_output_tokens` | `int \| None`, at least 1 | `None` |
| `max_tokens_key` | `Literal["max_completion_tokens", "max_tokens"]` | `"max_completion_tokens"` |

With `temperature == 0`, `top_p`, `top_k` and `min_p` are dropped before validation, so equivalent greedy chunks
share a digest.

`body() -> dict[str, JsonValue]`: every field that isn't `None`, `stop` as a list when not empty, and
`max_output_tokens` under `max_tokens_key`.

#### `Reasoning`, kind `chunk.reasoning`
| Field | Type | Default |
| --- | --- | --- |
| `effort` | `Literal["none", "minimal", "low", "medium", "high"] \| None` | `None`; sent as `reasoning_effort` |
| `thinking_token_budget` | `int \| None`, at least 0 | `None` |
| `chat_template_kwargs` | `Settings` | `{}`; sent when not empty |

#### `Passthrough`, kind `chunk.passthrough`
`body: Settings`, required. It may not set `RUNTIME_KEYS`, `OUTPUT_KEYS`, `MANAGED_KEYS` or `BYPASS_KEYS`
(`ValidationError("passthrough may not set […]")`).

#### `Tool`, kind `tool`, v2
| Field | Type | Default |
| --- | --- | --- |
| `name` | `ToolName` | required |
| `description` | `str`, at least 1 character | required |
| `parameters` | `dict[str, JsonValue]` | required; a JSON Schema |
| `entry_point` | `EntryPoint` | required |
| `version` | `int`, from 1 | required; the version of the entry point it pins |

The tool is called with a call's arguments as keyword arguments and returns text. The runner does the calling
(`src/chatddx/core/rig.py:entry` finds what `src/chatddx/tools/shipped.py:TOOLS` ships under the entry point, and
refuses one that isn't shipped, or not at the version pinned).

#### `Toolset`, kind `chunk.toolset`
| Field | Type | Default |
| --- | --- | --- |
| `tools` | `tuple[ToolRef, ...]`, at least one | required; order kept |
| `guidance` | `str \| None`, at least 1 character, plain text | `None` |
| `max_rounds` | `int`, at least 1 | `5` |

#### `Translations`, kind `chunk.translations`
`entries: dict[str, str]`, at least one, sorted by source text. Source texts may not be whitespace only, and every
translation must be non-empty.

### `class AppendixLayout(Frozen)`
`before: str = "\n\n"`, `between: str = "\n\n"`, `after: str = ""`.
`join(appendices: list[str]) -> str`: `before + between.join(appendices) + after`, or `""` when there are none.

### `class Recipe(Frozen)`
Not a component; kept only inside a `Compilation`.

| Field | Type | Default |
| --- | --- | --- |
| `purpose` | `Purpose` | `"generation"` |
| `prompt` | ref `chunk.prompt` | required |
| `output` | ref `chunk.output` | required |
| `sampling` | ref `chunk.sampling` | required |
| `instructions` | ref `chunk.instructions` \| `None` | `None` |
| `few_shot` | ref `chunk.few_shot` \| `None` | `None` |
| `reasoning` | ref `chunk.reasoning` \| `None` | `None` |
| `passthrough` | ref `chunk.passthrough` \| `None` | `None` |
| `translations` | ref `chunk.translations` \| `None` | `None` |
| `toolset` | ref `chunk.toolset` \| `None` | `None` |
| `appendix_layout` | `AppendixLayout` | `AppendixLayout()` |

### `class Skeleton(Component)`, kind `skeleton`
The frozen request that trials and judges reference.

| Field | Type | Default |
| --- | --- | --- |
| `purpose` | `Purpose` | `"generation"` |
| `api` | `Api` | `"chat.completions"` |
| `messages` | `tuple[Message, ...]`, at least one | required |
| `body` | `Settings` | `{}`; every other request key |
| `contract` | `OutputContract` | required |
| `appendix_layout` | `AppendixLayout` | `AppendixLayout()` |
| `tools` | `tuple[ToolRef, ...]` | `()`; the toolset's tools |
| `max_rounds` | `int \| None`, at least 1 | `None`; set exactly when `tools` is |

Before validation, a `body` with `temperature == 0` loses `top_p`, `top_k` and `min_p`. Validation then requires:
- no `RUNTIME_KEYS` in `body`;
- the slot rules over all messages;
- `body["tools"]`, if present, to be a list of `{"function": {"name": …}}` objects with distinct names;
- per contract, with `keys` being the `OUTPUT_KEYS` in `body`:

| Contract | Without `tools` | With `tools` |
| --- | --- | --- |
| `native` | `keys == {response_format}` | `keys == {response_format, tools, tool_choice}`, `tool_choice == "auto"` |
| `tool` | `keys == {tools, tool_choice}`, the answer function is the only function | `keys == {tools, tool_choice}`, the answer function among them, `tool_choice == "required"` |
| `text` | no `keys` | `keys == {tools, tool_choice}`, `tool_choice == "auto"` |

- for `tool`, the answer function's `description` equals the contract's (both may be absent);
- for `native` and `tool`, `output_schema` is an object.

| Member | Description |
| --- | --- |
| `greedy -> bool` | `body["temperature"] == 0` |
| `output_schema -> JsonValue` | `native`: `body["response_format"]["json_schema"]["schema"]`. `tool`: the answer function's `parameters`. `text`: `contract.json_schema`. `None` when absent. |
| `cross_check` | `"the body offers tools […], the skeleton names […]"` when the offered functions, apart from the answer function, differ from `tools` by name or order. Descriptions may differ. |

### `class Compilation(Component)`, kind `compilation`
`recipe: Recipe`, `skeleton: SkeletonRef`, `compiler: Code`. Provenance: no component refers to a compilation, and
nothing checks that the recipe compiles to the skeleton.

### `texts(recipe: Recipe, get: Resolver) -> dict[str, tuple[str, ...]]`
The texts of each part of the recipe, in first-seen order, without duplicates; a translation needs those of the
`TRANSLATED` parts. Whitespace-only texts are left out, and so are parts without texts. Parts and their texts:

| Part | Texts |
| --- | --- |
| `instructions` | the text's strings, and the inserts' `before` and `after` |
| `few_shot` | each message's content |
| `prompt` | each literal segment, and the inserts' `before` and `after` |
| `output` | the guidance's strings and inserts' `before`/`after`, the schema's `title` and `description` strings, and a tool contract's `description` |
| `appendix_layout` | `before`, `between` and `after` |
| `toolset` | the guidance, and each tool's `description` and `title`/`description` strings in its `parameters` |

In schemas, member names under `properties`, `patternProperties`, `$defs`, `definitions` and `dependentSchemas` are
kept, and nothing under `enum`, `const`, `default` or `examples` is translated.

### `compile_request(recipe: Recipe, get: Resolver) -> Skeleton`
1. Resolves every chunk (`StructuralError` for a missing or wrongly typed one).
2. With `recipe.translations`, passes every text listed under `texts` through its entries. Whitespace-only texts
   pass unchanged. `StructuralError("no translation for …")` lists every missing text.
3. `StructuralError` when the prompt's purpose isn't the recipe's.
4. Fills the inserts: `output_guidance` with `Output.guidance_text()`, `tool_guidance` with the toolset's guidance
   (`""` when absent). `StructuralError` when a guidance is inserted in both the instructions and the prompt. A
   non-empty guidance inserted in neither is appended to the instructions' text after `"\n\n"`, output guidance
   first, or becomes the whole first message.
5. Messages: the first message with the instructions' role (`system` without instructions), left out when empty;
   then the few-shot examples; then the prompt as a `user` message, its strings merged.
6. Body: the passthrough's keys, then `Sampling.body()`, `reasoning_effort`, `thinking_token_budget` and
   `chat_template_kwargs` (when set), then:
   - with a toolset, `tools` (its tools as functions with `name`, `description` and `parameters`, in order) and
     `tool_choice: "auto"`;
   - `native`: `response_format = {"type": "json_schema", "json_schema": {"name": "output", "strict": true,
     "schema": <output schema>}}`;
   - `tool`: `StructuralError` when a toolset tool has the answer function's name. The answer function goes last in
     `tools`, and `tool_choice` is `"required"` with a toolset, or else `{"type": "function", "function": {"name":
     …}}`;
   - `text`: no keys. The skeleton's contract becomes `TextOutput(json_schema=<output schema>)`.
7. Returns the skeleton with the recipe's purpose, the translated appendix layout, and the toolset's tools and
   `max_rounds`.

The same recipe and the same compiler always give the same skeleton. Without translations, how a chunk splits its
text doesn't change the skeleton.

### `compiled(recipe, get, compiler) -> tuple[Skeleton, Compilation]`
A recipe compiled by `compiler`, the running code, with the compilation that records what the skeleton was compiled
from.

### `render(skeleton, *, model, seed, fills, return_token_ids=True) -> dict[str, JsonValue]`
| Parameter | Type |
| --- | --- |
| `skeleton` | `Skeleton` |
| `model` | `str`: the engine's `served_model_name` |
| `seed` | `int \| None` |
| `fills` | `Mapping[SlotName, str]` |
| `return_token_ids` | `bool` |

Returns `{"model": model, "messages": [...], **skeleton.body}`. Each message is `{"role", "content"}`, with its
segments joined and every slot replaced by its fill. `seed` is added unless it is `None` or the skeleton is greedy,
and `return_token_ids: true` unless turned off. A slot without a fill raises `KeyError`.

`stream` and `n` are never added. The runner streams on the wire and records `render`'s body.

### Tool rounds
- `ToolCall(id: str, name: str, arguments: str)`.
- `tool_calls(response: Mapping[str, JsonValue]) -> tuple[ToolCall, ...]`: the tool calls in
  `choices[0].message.tool_calls`, in order. Calls without a string `id`, `function.name` and `function.arguments`
  are skipped.
- `next_request(body, response, results: Mapping[str, str]) -> dict[str, JsonValue]`: `body` with its `messages`
  extended by the assistant's message (`content` and `tool_calls` as the response holds them, without its reasoning)
  and one `{"role": "tool", "tool_call_id": id, "content": results[id]}` per call from `tool_calls`. Every other key
  stays, the seed included. `StructuralError("no result for tool calls […]")` when `results` lacks a call.

The runner owns the loop (`docs/factors.md`, "Tool rounds"). It ends when a response calls no tool, calls the answer
tool, or has no whole answer, or after `max_rounds` rounds.

## engine.py

### Flags
- `OWNED_FLAGS`: `--model`, `--served-model-name`, `--chat-template`, `--tokenizer`, `--revision`, which the start-up
  script sets.
- `UNPINNED_FLAGS`: `--config`.
- `flag_names(argv: tuple[str, ...]) -> frozenset[str]`: the names of the `--` arguments, cut at `=`, with `_` read
  as `-` up to the first `.`, as vLLM reads them.

### `class ModelArtifact(Component)`, kind `model`
| Field | Type | Default |
| --- | --- | --- |
| `repo` | `str` | required |
| `revision` | `str` | required |
| `files` | `tuple[FileDigest, ...]`, at least one, distinct paths | required; sorted by path |

`FileDigest(path: str, sha256: Sha256Hex)`.

### `class LocalEngine(Component)`, kind `engine.local`
| Field | Type | Default |
| --- | --- | --- |
| `api` | `Api` | `"chat.completions"` |
| `hardware` | `Hardware(gpu: str, compute_capability: tuple[int, int], vram_mib: int, driver: str)` | required |
| `runtime` | `Runtime(server: Literal["vllm"] = "vllm", version: str, closure: str)` | required |
| `model` | `ModelRef` | required |
| `chat_template` | `Sha256Hex` | required; the SHA-256 of the template file |
| `argv` | `tuple[str, ...]` | `()`; the raw arguments to vLLM |
| `env` | `dict[str, str]`, sorted | `{}` |

`argv` is refused (`ValidationError`) when it:
- sets an owned flag, with dashes or underscores;
- uses `--config`;
- abbreviates an owned flag or `--config` (vLLM expands unambiguous prefixes);
- has a bare argument. An argument after `--` is bare, and an argument right after a flag written without `=` is
  taken to be that flag's value. Negative numbers such as `-1` aren't flags.

`served_model_name -> str`: the engine's digest.

### `class RemoteEngine(Component)`, kind `engine.remote`
`api: Api = "chat.completions"`, `provider: str` (not empty), `model: str`.
`served_model_name -> str`: `model`.

`Engine = LocalEngine | RemoteEngine`. `EngineRef` allows both kinds.

### `check_chat_template(engine: LocalEngine, template: bytes) -> list[Finding]`
- `engine.chat_template` (warning): the template's SHA-256 isn't `engine.chat_template`.
- `engine.chat_template_date` (warning): the template matches `strftime_now`, `date_string` or `now(`.

Both have the engine's digest as subject.

## trial.py

### `class Trial(Component)`, kind `trial`
| Field | Type | Default |
| --- | --- | --- |
| `skeleton` | `SkeletonRef` | required; purpose `generation` (`cross_check`) |
| `engine` | `EngineRef` | required |
| `cases` | `tuple[CaseRef, ...]`, at least one, distinct | required; sorted by digest |
| `cleanup` | `tuple[CleanupOp, ...]` | `()` |
| `seeds` | `tuple[int, ...]`, at least one, distinct | required; order kept, and seed `i` is replicate `i` |

`suggest_seeds(n: int) -> tuple[int, ...]`: `n` distinct random seeds in `[0, 2**31)`.

### `class Canary(Frozen)`
| Field | Type | Default |
| --- | --- | --- |
| `messages` | `tuple[dict[str, JsonValue], ...]`, at least one | required; literal messages |
| `body` | `Settings` without `RUNTIME_KEYS` | `{}` |
| `seed` | `int \| None` | `None` |

`render(*, model: str, return_token_ids: bool = True) -> dict[str, JsonValue]`: `{"model", "messages", **body}`,
plus `seed` when set (whatever the temperature) and `return_token_ids: true` unless turned off.

### `class CanarySet(Component)`, kind `canary_set`
`canaries: tuple[Canary, ...]`, at least one.

### `class Execution(Frozen)`
Not a component. It is recorded in `RunStarted.execution` and `ScoreStarted.execution` (`docs/ledger.md`).

| Field | Type | Default |
| --- | --- | --- |
| `order` | `Order = Literal["case_major@1", "replicate_major@1", "shuffled@1"]` | `"case_major@1"` |
| `shuffle_seed` | `int \| None` | `None`; required with `shuffled@1`, and allowed only with it |
| `concurrency` | `int`, at least 1 | `1` |
| `timeout_s` | `float \| None`, above 0 | `None` |
| `retries` | `int`, at least 0 | `0` |
| `whitespace_limit` | `int \| None`, at least 1 | `100`; a call answering this many whitespace-only tokens in a row is cut short |

`schedule(cases: Sequence[str], replicates: int) -> list[tuple[str, int]]` lists (case, replicate index) pairs in
send order:
- `case_major@1`: every replicate of a case before the next case;
- `replicate_major@1`: every case once per replicate;
- `shuffled@1`: sorted by `sha256(f"{shuffle_seed}:{case}:{replicate}")`.

Cases keep the order given, which is digest order when they come from `Trial.cases`.

## scoring.py

### `class ExpectationSchema(Component)`, kind `expectation_schema`
`json_schema: dict[str, JsonValue]`. Its `$schema` names its draft, 2020-12 when absent (see "lint.py").

### `class Expectation(Component)`, kind `expectation`
`case: CaseRef`, `expectation_schema: ExpectationSchemaRef`, `data: JsonValue`. The data isn't checked against the
schema when the expectation is built; lints check it.

### Fill rules
`FillOp = Literal["text@1"]`.

`fill_text(op: FillOp, items: Sequence[JsonValue]) -> str` writes selected items as text:
- one string: as it is;
- a list of strings, whether picked as one list or as several strings: one per line. Nothing picked gives `""`;
- anything else: `json.dumps(value, indent=2, ensure_ascii=False)`, where `value` is the single item or the list of
  items.

### `class Judge(Component)`, kind `judge`

| Field | Type | Default |
| --- | --- | --- |
| `skeleton` | `SkeletonRef` | required; purpose `judge`, and no tools (`cross_check`) |
| `engine` | `EngineRef` | required |
| `seeds` | `tuple[int, ...]`, at least one, distinct | required |
| `fill` | `FillOp` | `"text@1"` |

`fills(view: View, answer: JsonValue, expectation: JsonValue) -> dict[SlotName, str]` returns
`{"completion": fill_text(fill, view.output_items(answer)), "expectation": fill_text(fill,
view.expectation_items(expectation))}`. `StructuralError` when `view.judge` isn't this judge's digest. The `vignette`
and `appendices` slots come from `prepare_case`.

### `class View(Frozen)`
| Field | Type | Default |
| --- | --- | --- |
| `output` | `Selector` | `""`: the whole answer |
| `expectation` | `Selector` | `""`: the whole expectation data |
| `split` | `SplitOp \| None` | `None`; applied to the output side only |
| `metric` | `str` | required; only the scorer's code interprets it |
| `judge` | `JudgeRef \| None` | `None` |
| `params` | `Settings` | `{}` |

`Selector` is a `str` checked with `select.py:check_selector`.

- `output_items(answer: JsonValue) -> list[JsonValue]`: `select(answer, output)`, then `split` when set.
- `expectation_items(data: JsonValue) -> list[JsonValue]`: `select(data, expectation)`.

### `class Scorer(Component)`, kind `scorer`, v2
| Field | Type | Default |
| --- | --- | --- |
| `entry_point` | `EntryPoint` | required |
| `version` | `int`, from 1 | required; the version of the entry point it pins |
| `expectation_schema` | `ExpectationSchemaRef` | required |
| `views` | `tuple[View, ...]`, at least one | required; referred to by position |
| `resources` | `tuple[str, ...]` | `()`; meant to be digests, referred to by position |
| `params` | `Settings` | `{}` |

`judges -> tuple[str, ...]`: the distinct judges the views name, in view order.

The entry point's interface belongs to `src/chatddx/scorers/scorer.py:ScoreFunction`, and the answer it reads to
`src/chatddx/scorers/answer.py:read`.

`src/chatddx/scorers/shipped.py:SCORERS` ships one `Metrics`, `chatddx.scorers.metrics:score`, with version, metrics,
what each measures, a JSON Schema for a view's params, whether it reads a judge's verdicts, what marks a value that
isn't a score from 0 to 1 (`unit`, `@` for `first_mention`'s offset), and optionally a schema for the scorer's own
params. Its metrics are the pattern metrics (`scorers/patterns.py`) and the judged metrics
(`scorers/verdicts.py`): `verdict`, the share of the judge's seeds whose verdict holds `true` at `at`, a JSON Pointer,
and `points`, their mean of the number at `at` over `max`.

A judged metric is given the verdicts, one per seed in seed order, each none where it couldn't be read; seeds with none
are left out, and the detail lists each seed's value. `shipped.problems` says why a scorer can't be scored by it:
an entry point not shipped, another version, a metric it doesn't publish, params a schema refuses (none where no schema
is published), or a view whose judge and metric disagree, one naming a judge whose metric reads no verdicts or the other
way round.

### `class Scoring(Component)`, kind `scoring`
`scorer: ScorerRef`, `expectations: tuple[ExpectationRef, ...]` (at least one; the order is kept and is part of the
digest).

`cross_check`: `"expectation … is not in the scorer's schema"` and `"case … has more than one expectation"`.

## select.py

### Selectors
A selector is a JSON Pointer (RFC 6901), or a JSONPath query (RFC 9535) from a subset.

- **JSON Pointer**: `""` (the whole document) or `/`-separated tokens with `~0` and `~1`. It picks at most one value.
  On an array, a token picks an element only as an index without leading zeros, so `-` picks nothing.
- **JSONPath**: `$` followed by segments:
  - member names: `.name` (letters, digits, `_` and non-ASCII, not starting with a digit), `['name']`, `["name"]`,
    with JSON escapes;
  - indexes: `[0]`, `[-1]` (no leading zeros, no `-0`);
  - wildcards: `.*`, `[*]`;
  - filters: `[?@<path>]` tests that a relative path of names and indexes exists, and `[?@<path> == <literal>]` or
    `!=` compares it with `true`, `false`, `null`, a string or a number.
  - whitespace is allowed inside brackets and around operators.
  - anything else is refused, including `..`, slices, unions, other operators and functions.

Picks keep the document's order, nulls included. Comparison follows RFC 9535: booleans equal only booleans, numbers
compare by value (`1 == 1.0`), and arrays and objects compare deeply. `!=` holds when the path picks nothing.

| Function | Returns / raises |
| --- | --- |
| `parse_selector(text) -> tuple[Step, ...]` | The parsed steps. `ValueError` naming the position otherwise. |
| `check_selector(text) -> str` | `text`, or `ValueError`. |
| `select(document: JsonValue, selector: str) -> list[JsonValue]` | Every value picked. |

### Splits
`SplitOp = Literal["lines@1"]`.

`split(op: SplitOp, items: Iterable[JsonValue]) -> list[JsonValue]`: each string becomes one item per line
(`str.splitlines`). Each line loses a leading list marker (`-`, `*`, `•`, `<digits>.` or `<digits>)` followed by
whitespace), is trimmed, and is dropped when empty. Items that aren't strings pass unchanged.

### Reachability
`reaches(schema: JsonValue, selector: str) -> bool`: whether `selector` can pick anything from a document that
follows `schema`. It follows local `$ref`s, treats `anyOf`, `oneOf` and `allOf` branches as alternatives, and reads
`type`, `properties`, `patternProperties`, `additionalProperties`, `items` and `prefixItems`. It errs towards `True`:
non-local or cyclic refs, `true`, `{}` and schemas without `type` count as reachable, so `False` is certain. `false`
and a local ref to nothing reach nothing.

## lint.py

### `lint(registry, digests=None, languages=None, reasons=None) -> list[Finding]`
| Parameter | Type |
| --- | --- |
| `registry` | `Registry`, checked: lints resolve references through it |
| `digests` | `Iterable[str] \| None`; every component when `None` |
| `languages` | `Languages = Callable[[str], str \| None] \| None`: a component's language by digest, normally `Catalog.language_of` |
| `reasons` | `Reasons = Callable[[str], bool \| None] \| None`: whether an engine's model reasons when a request doesn't say, by the engine's digest, normally `src/chatddx/facts/lint.py:reasons` |

Lints are plain functions, run on demand. Knowledge that changes between vLLM releases lives here, so it can change
without changing any digest.

#### Model artifacts, local engines, scorers
| Code | Level | Subject | When |
| --- | --- | --- | --- |
| `model.revision` | warning | model | `revision` isn't a 40-character lowercase hex commit |
| `engine.closure` | warning | local engine | `runtime.closure` isn't `/nix/store/<32 chars>-<name>` |
| `view.unreachable` | warning | scorer | a view's `expectation` selector can't reach anything in the expectation schema (`reaches`), one finding per view |

#### Outputs, expectation schemas and expectations
Checked with `jsonschema`. The draft comes from `$schema`, 2020-12 when absent.

| Code | Level | Subject | When |
| --- | --- | --- | --- |
| `output.schema_invalid` | warning | output | the output's `json_schema` has a `$schema` that names no draft the library knows, or breaks its draft's metaschema |
| `expectation_schema.invalid` | warning | schema | `$schema` names no draft the library knows, or the schema breaks its draft's metaschema |
| `expectation.invalid` | warning | expectation | the data fails its schema. The message gives the most relevant error's location (`at /…` or `at the root`) and how many more errors there are. |
| `expectation.unchecked` | warning | expectation | a `$ref` the data reaches can't be resolved. Refs resolve within the schema only, and nothing is fetched. |

An expectation whose schema is invalid isn't checked. `format` isn't enforced.

#### Trials and judges
Each trial and judge is checked as a pair of skeleton and engine. The subject is the trial's or the judge's digest.

On a local engine whose runtime is `vllm` with a version starting `0.24.`, flags are read with `flag_names` (no
abbreviations are expanded):

| Code | Level | When |
| --- | --- | --- |
| `vllm.temperature_clamped` | warning | `0 < body["temperature"] < 0.01`, which vLLM raises to 0.01 |
| `vllm.thinking_budget_refused` | warning | `thinking_token_budget` in the body, with neither `--reasoning-parser` nor `--reasoning-config` |
| `vllm.tools_refused` | warning | `tools` in the body, without both `--enable-auto-tool-choice` and `--tool-call-parser` |
| `vllm.native_tools_uncallable` | warning | a `native` contract with tools: the schema constrains the whole answer, so no tool can be called |
| `vllm.grammar_before_reasoning` | warning or info | a `native` or `tool` contract without `--reasoning-parser`: the answer is constrained from its first token |

`vllm.grammar_before_reasoning` in detail:
1. It isn't reported beside `vllm.tools_refused`: the request is then refused, or, for harmony and Mistral models,
   goes out unconstrained.
2. Whether the skeleton asks for reasoning (`lint.py:_asks_to_reason`): no with `chat_template_kwargs.enable_thinking:
   false` or `reasoning_effort: "none"`, which win. Yes with `enable_thinking: true`, any other `reasoning_effort`, or
   `thinking_token_budget`. Otherwise it's up to the model.
3. When it's up to the model, `reasons(engine digest)` answers, or unknown without `reasons`. When the engine's
   `argv` sets `--default-chat-template-kwargs`, `reasons` isn't asked, and the answer is unknown.
4. Yes gives a warning, unknown gives an info, and no gives nothing.

On any other engine (a remote engine, or another vLLM version):

| Code | Level | When |
| --- | --- | --- |
| `schema.ref_unverified` | warning | a `native` or `tool` skeleton's output schema holds `$ref`. `inline_refs@1` removes it. Also a toolset tool whose parameters hold `$ref`, a finding per tool, which nothing removes. |

#### Judges
| Code | Level | When |
| --- | --- | --- |
| `judge.greedy_seeds` | warning | the judge's skeleton is greedy and it has more than one seed, so every seed sends the same request |

#### Languages, for trials, with `languages`
| Code | Level | When |
| --- | --- | --- |
| `language.unknown` | info | the skeleton's language is unknown (then nothing else is checked), or some cases' languages are; the message counts them |
| `language.mixed` | warning | some cases are in another language than the skeleton |

Checks against the model facts (`facts.*`) are in `src/chatddx/facts/lint.py`.

## Finding codes

| Code | Level | Reported by |
| --- | --- | --- |
| `bundle.recanonicalized` | warning | `Bundle.load` |
| `case.drift` | warning | `prepare_case` |
| `engine.chat_template` | warning | `check_chat_template` |
| `engine.chat_template_date` | warning | `check_chat_template` |
| `engine.closure` | warning | `lint` |
| `view.unreachable` | warning | `lint` |
| `output.schema_invalid` | warning | `lint` |
| `expectation_schema.invalid` | warning | `lint` |
| `expectation.invalid` | warning | `lint` |
| `expectation.unchecked` | warning | `lint` |
| `vllm.temperature_clamped` | warning | `lint` |
| `vllm.thinking_budget_refused` | warning | `lint` |
| `vllm.tools_refused` | warning | `lint` |
| `vllm.native_tools_uncallable` | warning | `lint` |
| `vllm.grammar_before_reasoning` | warning or info | `lint` |
| `schema.ref_unverified` | warning | `lint` |
| `judge.greedy_seeds` | warning | `lint` |
| `language.unknown` | info | `lint` |
| `language.mixed` | warning | `lint` |

## Database: schema `factor`

Created by `0001-t0-factor.sql`, `0002-t1-factor.sql` and `0003-t2-factor.sql` (`docs/migrations.md`, "factor").
`src/chatddx/store/store.py:Store.add` writes it after `Registry.check` on the closure. A digest already stored is
skipped (`ON CONFLICT DO NOTHING`).

### `factor.component`
One row per component, every kind in one table.

| Column | Type | Holds |
| --- | --- | --- |
| `digest` | `text`, primary key | `Component.digest` |
| `kind` | `text NOT NULL`, indexed (`component_kind`) | `Component.kind_name` |
| `v` | `integer NOT NULL` | `schema_version` |
| `canonical` | `text NOT NULL` | the canonical form, the source of truth |
| `doc` | `jsonb NOT NULL` | `canonical` as `jsonb`, for queries |

CHECK (`0003`): `digest = 'sha256:' || encode(sha256(convert_to(canonical, 'UTF8')), 'hex')`,
`doc = canonical::jsonb`, `kind = doc->>'kind'` and `v = (doc->>'v')::integer`. `jsonb` can't hold U+0000, which is
why components refuse it.

### `factor.component_ref`
One row per `RefSite` of a component (`Component.refs()`).

| Column | Type | Holds |
| --- | --- | --- |
| `src` | `text NOT NULL`, FK → `component`, deferrable, initially deferred | the referring component |
| `path` | `text NOT NULL` | `RefSite.path` |
| `dst` | `text NOT NULL`, FK → `component`, deferrable, initially deferred, indexed (`component_ref_dst`) | the referenced digest |
| `kinds` | `text[] NOT NULL` | `RefSite.kinds` |

Primary key `(src, path)`.

`factor.check_ref()`, run by the constraint trigger `component_ref_matches` (AFTER INSERT, deferrable, initially
deferred, per row), raises when:
- `dst`'s kind isn't one of `kinds`: `<src><path>: <kind> is not one of <kinds>`;
- the value at `path` in `src`'s `doc` (split on `/`, without `~` unescaping) isn't `dst`: `<src><path>: component
  holds <value>, not <dst>`.

The checks are deferred because a reference may be inserted before the component it points to.

### Insert-only
`factor.refuse_change()` raises `<schema>.<table> is insert-only`. On both tables, the triggers `insert_only`
(BEFORE UPDATE OR DELETE, per row) and `insert_only_truncate` (BEFORE TRUNCATE, per statement) call it. The ledger's
and the catalog's insert-only triggers call it too (`0006-t2-ledger.sql`, `0012-t2-catalog.sql`).

### Roles (`0002`)
`chatddx_writer` and `chatddx_reader` (NOLOGIN) are created unless they exist. PUBLIC loses all access to the schema
and its tables. Both roles get `USAGE`; the writer gets `SELECT, INSERT` and the reader `SELECT`, on existing tables
and, through default privileges, on tables the admin creates later.

### Other migrations on these tables
- `0004-t0-ledger.sql`: the ledger's `trial`, `case` and `scoring` columns reference `factor.component`.
- `0010-t0-catalog.sql`: adds `UNIQUE (digest, kind)` on `component` and `UNIQUE (src, path, dst)` on
  `component_ref` as targets for the catalog's composite foreign keys.

### What the database checks, and what it doesn't
It checks that each digest matches its bytes, that `doc`, `kind` and `v` agree with them, that references exist,
have an allowed kind and match the document, and that nothing changes. It doesn't validate a component's fields, run
cross-checks, require today's canonical form (bytes that `Bundle.load` would report as recanonicalized are
accepted), or know which schema versions the code reads.

## Known gaps
From `docs/factors.md`, "Open design issues", where they concern this API:
- `render` raises a bare `KeyError` for a missing slot fill, not a `StructuralError` naming the slot.
- `tool_calls` skips a malformed call, but `next_request` copies the response's `tool_calls` as they are, so the
  next request holds a call that no `tool` message answers.
- NaN and infinity pass validation, and the canonical form writes them as `null`. The stored component reads back
  with the field unset, under the same digest, and `Bundle.load` reports `bundle.recanonicalized`. The request still
  carries the NaN.
- `Scorer.resources` are meant to be digests but are typed as plain strings.
- `Scoring.expectations` isn't sorted, so its order changes the digest.
- `render` sends `return_token_ids` to every engine by default; a remote engine that isn't vLLM may refuse it.
- `argv` is checked without vLLM's list of flags: a bare argument after a flag that takes no value passes, and lints
  don't expand abbreviated flags.
- `Hardware` has no GPU count.
- Nothing checks that a compilation's recipe compiles to its skeleton.

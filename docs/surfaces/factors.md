# `chatddx.factors`

Written by `chatddx stamp write` from `src/chatddx/factors/`; how to read it is in [docs/surfaces.md](../surfaces.md).

## `Api`
`src/chatddx/factors/base.py:Api`

`Api = Literal["chat.completions"]`

## `Appendix` `(Component)`
`src/chatddx/factors/cases.py:Appendix`

* `kind: Literal["appendix"] = "appendix"`
* `vignette: Vignette`
* `text: str = Field(min_length=1)`

## `AppendixLayout` `(Frozen)`
`src/chatddx/factors/request.py:AppendixLayout`

* `before: str = "\n\n"`
* `between: str = "\n\n"`
* `after: str = ""`

## `AppendixLayout.join`
`src/chatddx/factors/request.py:AppendixLayout.join`

* `appendices: list[str]`
* ∟`str`

## `AppendixRef`
`src/chatddx/factors/cases.py:AppendixRef`

`AppendixRef = Annotated[Digest, RefTo("appendix")]`

## `ascending`
`src/chatddx/factors/base.py:ascending`

* `values: tuple[str, ...]`
* ∟`tuple[str, ...]`

## `Bundle` `(Frozen)`
`src/chatddx/factors/bundle.py:Bundle`

* `format: Literal["chatddx.bundle/1"] = "chatddx.bundle/1"`
* `generator: Code`
* `roots: tuple[Digest, ...]`
* `components: dict[Digest, str]`

## `Bundle.load`
`src/chatddx/factors/bundle.py:Bundle.load`

* ∟`tuple[Registry, list[Finding]]`

Raises:
1. `StructuralError`: `"roots missing from bundle: {missing}"`

Finds:
1. `bundle.recanonicalized`: `"current code serializes this component differently"`

## `BY_KIND`
`src/chatddx/factors/kinds.py:BY_KIND`

`BY_KIND = _by_kind()`

## `BYPASS_KEYS`
`src/chatddx/factors/request.py:BYPASS_KEYS`

`BYPASS_KEYS = frozenset(…)`

## `Canary` `(Frozen)`
`src/chatddx/factors/trial.py:Canary`

* `messages: tuple[dict[str, JsonValue], ...] = Field(min_length=1)`
* `body: Settings = Field(default_factory=dict)`
* `seed: int | None = None`

Raises:
1. `ValueError`: `"canary body may not set {sorted(owned)}"` (through `Canary._no_runtime_keys`, in a `ValidationError`)

## `Canary.render`
`src/chatddx/factors/trial.py:Canary.render`

* `*`
* `model: str`
* `return_token_ids: bool = True`
* ∟`dict[str, JsonValue]`

## `CanarySet` `(Component)`
`src/chatddx/factors/trial.py:CanarySet`

* `kind: Literal["canary_set"] = "canary_set"`
* `canaries: tuple[Canary, ...] = Field(min_length=1)`

## `CanarySetRef`
`src/chatddx/factors/trial.py:CanarySetRef`

`CanarySetRef = Annotated[Digest, RefTo("canary_set")]`

## `canonical_bytes`
`src/chatddx/factors/base.py:canonical_bytes`

* `doc: JsonValue`
* ∟`bytes`

## `Case` `(Component)`
`src/chatddx/factors/cases.py:Case`

* `kind: Literal["case"] = "case"`
* `vignette: Vignette`
* `appendices: tuple[AppendixRef, ...] = ()`

## `Case.cross_check` `@override`
`src/chatddx/factors/cases.py:Case.cross_check`

* `get: Resolver`
* ∟`list[str]`

## `CaseRef`
`src/chatddx/factors/cases.py:CaseRef`

`CaseRef = Annotated[Digest, RefTo("case")]`

## `check_chat_template`
`src/chatddx/factors/engine.py:check_chat_template`

* `engine: LocalEngine`
* `template: bytes`
* ∟`list[Finding]`

Finds:
1. `engine.chat_template`: `"chat template does not match the declared digest"`
2. `engine.chat_template_date`: `"chat template reads the current date"`

## `check_selector`
`src/chatddx/factors/select.py:check_selector`

* `text: str`
* ∟`str`

## `choice`
`src/chatddx/factors/response.py:choice`

* `response: Mapping[str, JsonValue]`
* ∟`dict[str, JsonValue]`

## `CHUNK_PARTS`
`src/chatddx/factors/request.py:CHUNK_PARTS`

`CHUNK_PARTS = (…)`

## `clean`
`src/chatddx/factors/cases.py:clean`

* `text: str`
* `ops: Sequence[CleanupOp]`
* ∟`str`

## `CleanupOp`
`src/chatddx/factors/cases.py:CleanupOp`

`CleanupOp = Literal[…]`

## `Code` `(Frozen)`
`src/chatddx/factors/base.py:Code`

* `distribution: str`
* `version: str`
* `revision: str | None = None`

## `Compilation` `(Component)`
`src/chatddx/factors/request.py:Compilation`

* `schema_version: ClassVar[int] = 3`
* `kind: Literal["compilation"] = "compilation"`
* `recipe: Recipe`
* `skeleton: SkeletonRef`
* `compiler: Code`
* `facts: FactsRef | None = None`
* `into: Language | None = None`

## `Compilation.cross_check` `@override`
`src/chatddx/factors/request.py:Compilation.cross_check`

* `get: Resolver`
* ∟`list[str]`

## `compile_request`
`src/chatddx/factors/request.py:compile_request`

* `recipe: Recipe`
* `get: Resolver`
* `facts: ModelFacts | None = None`
* `into: str | None = None`
* ∟`Skeleton`

Raises:
1. `StructuralError`: `"no translations into {into}"`
2. `StructuralError`: `"no translation into {into} for {listed}"`
3. `StructuralError`: `"{prompt.purpose} prompt in a {recipe.purpose} recipe"`
4. `StructuralError`: `"{name.replace('_', ' ')} is inserted in both the instructions and the prompt"`
5. `StructuralError`: `"the answer tool {name!r} has the name of a tool in the toolset"`

## `compiled`
`src/chatddx/factors/request.py:compiled`

* `recipe: Recipe`
* `get: Resolver`
* `compiler: Code`
* `facts: ModelFacts | None = None`
* `into: str | None = None`
* ∟`tuple[Skeleton, Compilation]`

## `Component` `(Frozen)`
`src/chatddx/factors/base.py:Component`

* `schema_version: ClassVar[int] = 1`

Raises:
1. `ValueError`: `"a {self.kind_name} may not hold U+0000, which can't be stored"` (through `Component._storable`, in a `ValidationError`)

## `Component.__pydantic_init_subclass__` `@classmethod` `@override`
`src/chatddx/factors/base.py:Component.__pydantic_init_subclass__`

* `**kwargs: Any`
* ∟`None`

Raises:
1. `TypeError`: `"{cls.__name__}.kind needs a literal default"`

## `Component.canonical` `@cached_property`
`src/chatddx/factors/base.py:Component.canonical`

* ∟`bytes`

## `Component.canonical_doc`
`src/chatddx/factors/base.py:Component.canonical_doc`

* ∟`dict[str, JsonValue]`

## `Component.cross_check`
`src/chatddx/factors/base.py:Component.cross_check`

* `get: Resolver`
* ∟`list[str]`

## `Component.digest` `@cached_property`
`src/chatddx/factors/base.py:Component.digest`

* ∟`str`

## `Component.kind_name` `@property`
`src/chatddx/factors/base.py:Component.kind_name`

* ∟`str`

## `Component.model_copy` `@override`
`src/chatddx/factors/base.py:Component.model_copy`

* `*`
* `update: Mapping[str, Any] | None = None`
* `deep: bool = False`
* ∟`Self`

## `Component.refs`
`src/chatddx/factors/base.py:Component.refs`

* ∟`list[RefSite]`

## `ContractFact` `(Frozen)`
`src/chatddx/factors/facts.py:ContractFact`

* `note: str | None = None`

## `Digest`
`src/chatddx/factors/base.py:Digest`

`Digest = Annotated[str, StringConstraints(pattern=r"^sha256:[0-9a-f]{64}$")]`

## `distinct` `[T]`
`src/chatddx/factors/base.py:distinct`

* `values: tuple[T, ...]`
* ∟`tuple[T, ...]`

Raises:
1. `ValueError`: `"duplicates are not allowed"`

## `Effort`
`src/chatddx/factors/facts.py:Effort`

`Effort = Level | Literal["default"]`

## `EngineRef`
`src/chatddx/factors/engine.py:EngineRef`

`EngineRef = Annotated[Digest, RefTo("engine.local", "engine.remote")]`

## `EntryPoint`
`src/chatddx/factors/request.py:EntryPoint`

`EntryPoint = Annotated[str, StringConstraints(pattern=r"^[\w.]+:[\w.]+$")]`

## `Example` `(Frozen)`
`src/chatddx/factors/request.py:Example`

* `role: Literal["user", "assistant"]`
* `content: str`

## `Execution` `(Frozen)`
`src/chatddx/factors/trial.py:Execution`

* `order: Order = "case_major@1"`
* `shuffle_seed: int | None = None`
* `concurrency: int = Field(default=1, ge=1)`
* `timeout_s: float | None = Field(default=None, gt=0)`
* `retries: int = Field(default=0, ge=0)`
* `whitespace_limit: int | None = Field(default=100, ge=1)`

Raises:
1. `ValueError`: `"shuffle_seed goes with shuffled order, and only with it"` (through `Execution._shuffle_seed`, in a `ValidationError`)

## `Execution.overlaid`
`src/chatddx/factors/trial.py:Execution.overlaid`

* `concurrency: int | None = None`
* `order: Order | None = None`
* ∟`"Execution"`

## `Execution.schedule`
`src/chatddx/factors/trial.py:Execution.schedule`

* `cases: Sequence[str]`
* `replicates: int`
* ∟`list[tuple[str, int]]`

## `Expectation` `(Component)`
`src/chatddx/factors/scoring.py:Expectation`

* `kind: Literal["expectation"] = "expectation"`
* `case: CaseRef`
* `expectation_schema: ExpectationSchemaRef`
* `data: JsonValue`

## `ExpectationRef`
`src/chatddx/factors/scoring.py:ExpectationRef`

`ExpectationRef = Annotated[Digest, RefTo("expectation")]`

## `ExpectationSchema` `(Component)`
`src/chatddx/factors/scoring.py:ExpectationSchema`

* `kind: Literal["expectation_schema"] = "expectation_schema"`
* `json_schema: dict[str, JsonValue]`

## `ExpectationSchemaRef`
`src/chatddx/factors/scoring.py:ExpectationSchemaRef`

`ExpectationSchemaRef = Annotated[Digest, RefTo("expectation_schema")]`

## `FactsRef`
`src/chatddx/factors/facts.py:FactsRef`

`FactsRef = Annotated[Digest, RefTo("facts")]`

## `FewShot` `(Component)`
`src/chatddx/factors/request.py:FewShot`

* `kind: Literal["chunk.few_shot"] = "chunk.few_shot"`
* `messages: tuple[Example, ...] = Field(min_length=1)`

## `FileDigest` `(Frozen)`
`src/chatddx/factors/engine.py:FileDigest`

* `path: str`
* `sha256: Sha256Hex`

## `fill_text`
`src/chatddx/factors/scoring.py:fill_text`

* `op: FillOp`
* `items: Sequence[JsonValue]`
* ∟`str`

## `FillOp`
`src/chatddx/factors/scoring.py:FillOp`

`FillOp = Literal["text@1"]`

## `Filter` `@dataclass(frozen=True)`
`src/chatddx/factors/select.py:Filter`

* `path: tuple["Name | Index", ...]`
* `op: Literal["==", "!="] | None = None`
* `value: JsonValue = None`

## `Finding` `(Frozen)`
`src/chatddx/factors/base.py:Finding`

* `level: Literal["info", "warning"] = "warning"`
* `code: str`
* `message: str`
* `subject: str | None = None`

## `Fingerprint` `(Frozen)`
`src/chatddx/factors/base.py:Fingerprint`

* `alg: Literal["sha256", "hmac-sha256"] = "sha256"`
* `key_id: str | None = None`
* `hex: Sha256Hex`

Raises:
1. `ValueError`: `"key_id goes with hmac-sha256, and only with it"` (through `Fingerprint._key_id`, in a `ValidationError`)

## `Fingerprint.of` `@classmethod`
`src/chatddx/factors/base.py:Fingerprint.of`

* `data: bytes`
* `key: tuple[str, bytes] | None = None`
* ∟`"Fingerprint"`

## `flag_names`
`src/chatddx/factors/engine.py:flag_names`

* `argv: tuple[str, ...]`
* ∟`frozenset[str]`

## `flag_value`
`src/chatddx/factors/engine.py:flag_value`

* `argv: tuple[str, ...]`
* `flag: str`
* ∟`str | None`

## `Frozen` `(BaseModel)`
`src/chatddx/factors/base.py:Frozen`

* `model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")`

## `GREEDY_DROPS`
`src/chatddx/factors/request.py:GREEDY_DROPS`

`GREEDY_DROPS = ("top_p", "top_k", "min_p")`

## `Hardware` `(Frozen)`
`src/chatddx/factors/engine.py:Hardware`

* `gpu: str`
* `compute_capability: tuple[int, int]`
* `vram_mib: int`
* `driver: str`

## `Index` `@dataclass(frozen=True)`
`src/chatddx/factors/select.py:Index`

* `index: int`

## `Insert` `(Frozen)`
`src/chatddx/factors/request.py:Insert`

* `insert: InsertName`
* `before: str = ""`
* `after: str = ""`

## `InsertName`
`src/chatddx/factors/request.py:InsertName`

`InsertName = Literal["schema", "output_guidance", "tool_guidance"]`

## `INSERTS_BY_KIND`
`src/chatddx/factors/request.py:INSERTS_BY_KIND`

`INSERTS_BY_KIND: dict[str, frozenset[InsertName]] = {…}`

## `Instructions` `(Component)`
`src/chatddx/factors/request.py:Instructions`

* `kind: Literal["chunk.instructions"] = "chunk.instructions"`
* `role: Literal["system", "developer"] = "system"`
* `text: Text`

Raises:
1. `ValueError`: `"{kind} cannot use inserts {sorted(stray)}"` (through `Instructions._inserts`, in a `ValidationError`)
2. `ValueError`: `"inserts used more than once: {sorted(dupes)}"` (through `Instructions._inserts`, in a `ValidationError`)

## `iter_refs`
`src/chatddx/factors/base.py:iter_refs`

* `model: BaseModel`
* `prefix: str = ""`
* ∟`Iterator[RefSite]`

## `Judge` `(Component)`
`src/chatddx/factors/scoring.py:Judge`

* `kind: Literal["judge"] = "judge"`
* `schema_version: ClassVar[int] = 2`
* `skeleton: SkeletonRef`
* `model: ModelRef`
* `seeds: Annotated[tuple[int, ...], AfterValidator(distinct)] = Field(min_length=1)`
* `fill: FillOp = "text@1"`

## `Judge.cross_check` `@override`
`src/chatddx/factors/scoring.py:Judge.cross_check`

* `get: Resolver`
* ∟`list[str]`

## `Judge.fills`
`src/chatddx/factors/scoring.py:Judge.fills`

* `view: "View"`
* `answer: JsonValue`
* `expectation: JsonValue`
* ∟`dict[SlotName, str]`

Raises:
1. `StructuralError`: `"the view is judged by {view.judge}, not this judge"`

## `JudgeEngine` `(Frozen)`
`src/chatddx/factors/scoring.py:JudgeEngine`

* `judge: JudgeRef`
* `engine: EngineRef`

## `JudgeRef`
`src/chatddx/factors/scoring.py:JudgeRef`

`JudgeRef = Annotated[Digest, RefTo("judge")]`

## `KINDS`
`src/chatddx/factors/kinds.py:KINDS`

`KINDS: tuple[type[Component], ...] = (…)`

## `Landing` `(Frozen)`
`src/chatddx/factors/facts.py:Landing`

* `level: Level`
* `writes: Writes`
* `nearest: tuple[str, ...] = ()`

## `landings`
`src/chatddx/factors/request.py:landings`

* `recipe: Recipe`
* `get: Resolver`
* `facts: ModelFacts | None`
* ∟`tuple[Landing | None, Landing | None]`

Raises:
1. `StructuralError`: `"facts about {facts.model} can't compile for {model}"`
2. `StructuralError`: `"{what} is worked out from the facts about the recipe's model, which has none"`
3. `StructuralError`: `"{facts.model}: {e}"` (from `Refused`)

## `LANGUAGE`
`src/chatddx/factors/base.py:LANGUAGE`

`LANGUAGE = re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{1,8})*$")`

## `Language`
`src/chatddx/factors/base.py:Language`

`type Language = Annotated[str, AfterValidator(language_tag)]`

## `language_tag`
`src/chatddx/factors/base.py:language_tag`

* `value: str`
* ∟`str`

Raises:
1. `ValueError`: `"{value!r} is not a language tag such as 'sv' or 'pt-BR'"`

## `Languages`
`src/chatddx/factors/lint.py:Languages`

`Languages = Callable[[str], str | None]`

## `Level`
`src/chatddx/factors/facts.py:Level`

`Level = Literal["off", "on", "minimal", "low", "medium", "high", "xhigh"]`

## `LEVELS`
`src/chatddx/factors/facts.py:LEVELS`

`LEVELS: tuple[Level, ...] = get_args(Level)`

## `lint`
`src/chatddx/factors/lint.py:lint`

* `registry: Registry`
* `digests: Iterable[str] | None = None`
* `languages: Languages | None = None`
* `reasons: Reasons | None = None`
* `engines: Mapping[str, str] | None = None`
* ∟`list[Finding]`

Finds:
1. `model.revision`: `"revision {c.revision!r} is not a commit and can move"` (through `_model`)
2. `engine.closure`: `"closure {c.runtime.closure!r} is not a Nix store path"` (through `_engine`)
3. `view.unreachable`: `"view {i}'s expectation selector {view.expectation!r} reaches nothing in the expectation schema"` (through `_scorer`)
4. `output.schema_invalid`: `message` (through `_output`)
5. `expectation_schema.invalid`: `message` (through `_expectation_schema`)
6. `expectation.unchecked`: `"a $ref in the schema can't be resolved: {e.ref}"` (from `Unresolvable`, through `_expectation`)
7. `expectation.invalid`: `"{_where(error)}: {error.message}{more}"` (through `_expectation`)
8. `schema.ref_unverified`: `"the schema has $ref, which this engine isn't known to resolve; inline_refs@1 removes them"` (through `_pair`)
9. `schema.ref_unverified`: `"the parameters of tool {name!r} have $ref, which this engine isn't known to resolve"` (through `_pair`)
10. `vllm.temperature_clamped`: `"vLLM 0.24 raises temperature {t} to 0.01"` (through `_pair`)
11. `vllm.thinking_budget_refused`: `"vLLM 0.24 refuses thinking_token_budget without --reasoning-parser or --reasoning-config"` (through `_pair`)
12. `vllm.tools_refused`: `"vLLM 0.24 refuses tool_choice {_choice(skeleton.body.get('tool_choice'))} without --enable-auto-tool-choice and --tool-call-parser; for harmony and Mistral models it goes out unconstrained instead"` (through `_pair`)
13. `vllm.native_tools_uncallable`: `"with tool_choice auto, vLLM 0.24 constrains the whole answer to response_format, so no tool can be called"` (through `_pair`)
14. `vllm.grammar_before_reasoning`: `"without --reasoning-parser, vLLM 0.24 constrains the answer from its first token, so a model can't reason first"` (`{"warning" if reasons else "info"}`, through `_pair`)
15. `trial.engine_unmatched`: `"the skeleton is worked out for {worked}, and the engine serves {serves}"` (through `_made_for`)
16. `judge.model_unmatched`: `"the skeleton is worked out for {worked}, and the judge's model is {serves}"` (through `_made_for`)
17. `language.unknown`: `"the request's language is unknown"` (`info`, through `_languages`)
18. `language.unknown`: `"the language of {unknown} of {len(cases)} cases is unknown"` (`info`, through `_languages`)
19. `language.mixed`: `"the request is {request}, but {len(other)} of {len(cases)} cases {verb} {', '.join(sorted(set(other)))}"` (through `_languages`)
20. `judge.greedy_seeds`: `"the judge is greedy, so its {len(c.seeds)} seeds send the same request"` (through `_judge`)

## `LocalEngine` `(Component)`
`src/chatddx/factors/engine.py:LocalEngine`

* `kind: Literal["engine.local"] = "engine.local"`
* `api: Api = "chat.completions"`
* `hardware: Hardware`
* `runtime: Runtime`
* `model: LocalModelRef`
* `chat_template: Sha256Hex`
* `argv: tuple[str, ...] = ()`
* `env: Annotated[dict[str, str], AfterValidator(sorted_keys)] = Field(…)`

Raises:
1. `ValueError`: `"argv may not set {sorted(owned)}"` (through `LocalEngine._no_owned_flags`, in a `ValidationError`)
2. `ValueError`: `"argv may not use {sorted(unpinned)}: its arguments belong in argv, where the digest pins them"` (through `LocalEngine._no_owned_flags`, in a `ValidationError`)
3. `ValueError`: `"argv may not abbreviate flags it may not use: {listed}"` (through `LocalEngine._no_owned_flags`, in a `ValidationError`)
4. `ValueError`: `"argv may not have bare arguments {bare}: vLLM takes the model as its only bare argument, and the start-up script gives it"` (through `LocalEngine._no_owned_flags`, in a `ValidationError`)

## `LocalModel` `(Component)`
`src/chatddx/factors/engine.py:LocalModel`

* `kind: Literal["model.local"] = "model.local"`
* `repo: str`
* `revision: str`
* `files: tuple[FileDigest, ...] = Field(min_length=1)`

Raises:
1. `ValueError`: `"duplicate file paths"` (through `LocalModel._sorted_unique`, in a `ValidationError`)

## `LocalModel.name` `@property`
`src/chatddx/factors/engine.py:LocalModel.name`

* ∟`str`

## `LocalModelRef`
`src/chatddx/factors/engine.py:LocalModelRef`

`LocalModelRef = Annotated[Digest, RefTo("model.local")]`

## `MANAGED_KEYS`
`src/chatddx/factors/request.py:MANAGED_KEYS`

`MANAGED_KEYS = frozenset(…)`

## `Message` `(Frozen)`
`src/chatddx/factors/request.py:Message`

* `role: Literal["system", "developer", "user", "assistant"]`
* `content: tuple[Segment, ...] = Field(min_length=1)`

## `message`
`src/chatddx/factors/response.py:message`

* `response: Mapping[str, JsonValue]`
* ∟`dict[str, JsonValue]`

## `Model`
`src/chatddx/factors/engine.py:Model`

`Model = LocalModel | RemoteModel`

## `model_of`
`src/chatddx/factors/engine.py:model_of`

* `digest: str`
* `get: Resolver`
* ∟`Model`

Raises:
1. `StructuralError`: `"{digest} is a {other.kind_name}, neither a model nor an engine"`

## `ModelFacts` `(Component)`
`src/chatddx/factors/facts.py:ModelFacts`

* `kind: Literal["facts"] = "facts"`
* `model: str = Field(min_length=1)`
* `family: str | None = None`
* `parameters_b: float | None = None`
* `active_parameters_b: float | None = None`
* `quantization: str | None = None`
* `context_length: int | None = None`
* `licence: str | None = None`
* `reasoning: ReasoningFacts = ReasoningFacts()`
* `sampling: SamplingFacts = SamplingFacts()`
* `output: OutputFacts = OutputFacts()`

## `ModelFacts.check_budget`
`src/chatddx/factors/facts.py:ModelFacts.check_budget`

* ∟`None`

Raises:
1. `Refused`: `"nothing is known about a thinking budget"`
2. `Refused`: `reason`

## `ModelFacts.reasons_by_default`
`src/chatddx/factors/facts.py:ModelFacts.reasons_by_default`

* ∟`bool | None`

## `ModelFacts.recommended`
`src/chatddx/factors/facts.py:ModelFacts.recommended`

* `level: Level`
* ∟`SamplingValues`

Raises:
1. `Refused`: `"no sampling is recommended for reasoning {level!r}"`

## `ModelRef`
`src/chatddx/factors/engine.py:ModelRef`

`ModelRef = Annotated[Digest, RefTo("model.local", "model.remote")]`

## `Name` `@dataclass(frozen=True)`
`src/chatddx/factors/select.py:Name`

* `name: str`

## `NativeOutput` `(Frozen)`
`src/chatddx/factors/request.py:NativeOutput`

* `kind: Literal["native"] = "native"`

## `next_request`
`src/chatddx/factors/request.py:next_request`

* `body: Mapping[str, JsonValue]`
* `response: Mapping[str, JsonValue]`
* `results: Mapping[str, str]`
* ∟`dict[str, JsonValue]`

Raises:
1. `StructuralError`: `"no result for tool calls {missing}"`

## `OPTIONAL_PARTS`
`src/chatddx/factors/request.py:OPTIONAL_PARTS`

`OPTIONAL_PARTS = tuple(…)`

## `Order`
`src/chatddx/factors/trial.py:Order`

`Order = Literal["case_major@1", "replicate_major@1", "shuffled@1"]`

## `Output` `(Component)`
`src/chatddx/factors/request.py:Output`

* `kind: Literal["chunk.output"] = "chunk.output"`
* `contract: OutputContract`
* `json_schema: dict[str, JsonValue] | None = None`
* `guidance: Text | None = None`
* `schema_ops: Annotated[tuple[SchemaOp, ...], AfterValidator(distinct)] = ()`

Raises:
1. `ValueError`: `"an output's schema goes in json_schema, not its contract"` (through `Output._schema_placement`, in a `ValidationError`)
2. `ValueError`: `"{self.contract.kind} contracts need json_schema"` (through `Output._schema_placement`, in a `ValidationError`)
3. `ValueError`: `"{kind} cannot use inserts {sorted(stray)}"` (through `Output._inserts`, in a `ValidationError`)
4. `ValueError`: `"inserts used more than once: {sorted(dupes)}"` (through `Output._inserts`, in a `ValidationError`)
5. `ValueError`: `"only an output with a schema can show it"` (through `Output._inserts`, in a `ValidationError`)
6. `ValueError`: `"schema ops need a schema"` (through `Output._schema_ops`, in a `ValidationError`)

## `Output.guidance_text`
`src/chatddx/factors/request.py:Output.guidance_text`

* ∟`str`

## `Output.output_schema` `@property`
`src/chatddx/factors/request.py:Output.output_schema`

* ∟`dict[str, JsonValue] | None`

## `OUTPUT_KEYS`
`src/chatddx/factors/request.py:OUTPUT_KEYS`

`OUTPUT_KEYS = frozenset({"response_format", "tools", "tool_choice"})`

## `OutputContract`
`src/chatddx/factors/request.py:OutputContract`

`OutputContract = Annotated[…]`

## `OutputFacts` `(Frozen)`
`src/chatddx/factors/facts.py:OutputFacts`

* `default: Literal["native", "tool", "text"] | None = None`
* `native: ContractFact | Refusal | None = None`
* `tool: ContractFact | Refusal | None = None`
* `text: ContractFact | Refusal | None = None`

## `OutputFacts.fact`
`src/chatddx/factors/facts.py:OutputFacts.fact`

* `kind: Literal["native", "tool", "text"]`
* ∟`ContractFact | Refusal | None`

## `own_texts`
`src/chatddx/factors/request.py:own_texts`

* `chunk: Component | AppendixLayout`
* `get: Resolver`
* ∟`tuple[str, ...]`

## `OWNED_FLAGS`
`src/chatddx/factors/engine.py:OWNED_FLAGS`

`OWNED_FLAGS = frozenset(…)`

## `parse_component`
`src/chatddx/factors/kinds.py:parse_component`

* `data: bytes`
* ∟`Component`

Raises:
1. `StructuralError`: `"component is not a JSON object"`
2. `StructuralError`: `"unknown component kind {kind!r}"`
3. `StructuralError`: `"{kind} v{v} is not readable by v{cls.schema_version}"`

## `parse_selector`
`src/chatddx/factors/select.py:parse_selector`

* `text: str`
* ∟`tuple[Step, ...]`

Raises:
1. `ValueError`: `"{text!r}: a JSON Pointer starts with /"` (through `_pointer`)
2. `ValueError`: `"{text!r}: ~ must be followed by 0 or 1"` (through `_pointer`)
3. `ValueError`: `"{text!r}: a selector is a JSON Pointer or a JSONPath query starting with $"`

## `Part` `(NamedTuple)`
`src/chatddx/factors/response.py:Part`

* `kind: Literal["reasoning", "content", "tool_call"]`
* `text: str`
* `name: str | None = None`

## `parts`
`src/chatddx/factors/response.py:parts`

* `response: Mapping[str, JsonValue]`
* ∟`list[Part]`

## `Passthrough` `(Component)`
`src/chatddx/factors/request.py:Passthrough`

* `kind: Literal["chunk.passthrough"] = "chunk.passthrough"`
* `body: Settings`

Raises:
1. `ValueError`: `"passthrough may not set {sorted(owned)}"` (through `Passthrough._no_owned_keys`, in a `ValidationError`)

## `prepare_case`
`src/chatddx/factors/cases.py:prepare_case`

* `case: Case`
* `raw: bytes`
* `get: Resolver`
* `layout: AppendixLayout`
* `cleanup: Sequence[CleanupOp] = ()`
* `key: tuple[str, bytes] | None = None`
* ∟`Prepared`

Raises:
1. `StructuralError`: `"the case's vignette is fingerprinted with key {expected.key_id!r}, not {given!r}"`
2. `StructuralError`: `"vignette {vignette} isn't UTF-8: {e.reason} at byte {e.start}"` (from `UnicodeDecodeError`)

Finds:
1. `case.drift`: `"the vignette at the source differs from the case's"`

## `Prepared` `(Frozen)`
`src/chatddx/factors/cases.py:Prepared`

* `fills: dict[SlotName, str]`
* `fingerprint: Fingerprint`
* `findings: tuple[Finding, ...] = ()`

## `Prompt` `(Component)`
`src/chatddx/factors/request.py:Prompt`

* `kind: Literal["chunk.prompt"] = "chunk.prompt"`
* `purpose: Purpose = "generation"`
* `segments: tuple[Segment | Insert, ...] = Field(min_length=1)`

Raises:
1. `ValueError`: `"{purpose} requests cannot use slots {sorted(stray)}"` (through `Prompt._slots`, in a `ValidationError`)
2. `ValueError`: `"{purpose} requests need slots {sorted(missing)}"` (through `Prompt._slots`, in a `ValidationError`)
3. `ValueError`: `"slots used more than once: {sorted(dupes)}"` (through `Prompt._slots`, in a `ValidationError`)
4. `ValueError`: `"{kind} cannot use inserts {sorted(stray)}"` (through `Prompt._slots`, in a `ValidationError`)
5. `ValueError`: `"inserts used more than once: {sorted(dupes)}"` (through `Prompt._slots`, in a `ValidationError`)

## `Purpose`
`src/chatddx/factors/request.py:Purpose`

`Purpose = Literal["generation", "judge"]`

## `reaches`
`src/chatddx/factors/select.py:reaches`

* `schema: JsonValue`
* `selector: str`
* ∟`bool`

## `REASONING`
`src/chatddx/factors/response.py:REASONING`

`REASONING = ("reasoning", "reasoning_content")`

## `Reasoning` `(Component)`
`src/chatddx/factors/request.py:Reasoning`

* `kind: Literal["chunk.reasoning"] = "chunk.reasoning"`
* `effort: Literal["none", "minimal", "low", "medium", "high"] | None = None`
* `thinking_token_budget: int | None = Field(default=None, ge=0)`
* `chat_template_kwargs: Settings = Field(default_factory=dict)`
* `level: Effort | None = None`

Raises:
1. `ValueError`: `"a reasoning level is worked out from the model's facts, so it comes without an effort or chat template arguments"` (through `Reasoning._level_or_settings`, in a `ValidationError`)

## `reasoning`
`src/chatddx/factors/response.py:reasoning`

* `said: Mapping[str, JsonValue]`
* ∟`str | None`

## `REASONING_FLAGS`
`src/chatddx/factors/engine.py:REASONING_FLAGS`

`REASONING_FLAGS = frozenset({"--reasoning-parser", "--reasoning-config"})`

## `ReasoningFact`
`src/chatddx/factors/facts.py:ReasoningFact`

`ReasoningFact = Level | Refusal | Writes`

## `ReasoningFacts` `(Frozen)`
`src/chatddx/factors/facts.py:ReasoningFacts`

* `default: Level | None = None`
* `off: ReasoningFact | None = None`
* `on: ReasoningFact | None = None`
* `minimal: ReasoningFact | None = None`
* `low: ReasoningFact | None = None`
* `medium: ReasoningFact | None = None`
* `high: ReasoningFact | None = None`
* `xhigh: ReasoningFact | None = None`
* `budget: Literal["thinking_token_budget"] | Refusal | None = None`

Raises:
1. `ValueError`: `"{' -> '.join([*path, level])}: the collapses go round"` (through `ReasoningFacts._collapses_land`, in a `ValidationError`)
2. `ValueError`: `"{name!r} collapses into {target!r}, which ends in no fact"` (through `ReasoningFacts._collapses_land`, in a `ValidationError`)

## `ReasoningFacts.fact`
`src/chatddx/factors/facts.py:ReasoningFacts.fact`

* `level: Level`
* ∟`ReasoningFact | None`

## `ReasoningFacts.landing`
`src/chatddx/factors/facts.py:ReasoningFacts.landing`

* `effort: Effort`
* ∟`Landing`

Raises:
1. `Refused`: `"no default reasoning level is known"`
2. `ValueError`: `"{' -> '.join([*path, level])}: the collapses go round"` (through `ReasoningFacts._land`)
3. `Refused`: `"nothing is known about reasoning {landed!r}"`
4. `Refused`: `reason`

## `ReasoningFacts.realized`
`src/chatddx/factors/facts.py:ReasoningFacts.realized`

* ∟`dict[Level, Writes]`

## `Reasons`
`src/chatddx/factors/lint.py:Reasons`

`Reasons = Callable[[str], bool | None]`

## `Recipe` `(Frozen)`
`src/chatddx/factors/request.py:Recipe`

* `purpose: Purpose = "generation"`
* `instructions: Annotated[Digest, RefTo("chunk.instructions")] | None = None`
* `few_shot: Annotated[Digest, RefTo("chunk.few_shot")] | None = None`
* `prompt: Annotated[Digest, RefTo("chunk.prompt")]`
* `output: Annotated[Digest, RefTo("chunk.output")]`
* `sampling: Annotated[Digest, RefTo("chunk.sampling")]`
* `reasoning: Annotated[Digest, RefTo("chunk.reasoning")] | None = None`
* `passthrough: Annotated[Digest, RefTo("chunk.passthrough")] | None = None`
* `appendix_layout: AppendixLayout = AppendixLayout()`
* `translations: Annotated[Digest, RefTo("chunk.translations")] | None = None`
* `toolset: Annotated[Digest, RefTo("chunk.toolset")] | None = None`
* `model: ModelRef`

## `RECIPE_PARTS`
`src/chatddx/factors/request.py:RECIPE_PARTS`

`RECIPE_PARTS = (*CHUNK_PARTS, "model")`

## `RefSite` `@dataclass(frozen=True)`
`src/chatddx/factors/base.py:RefSite`

* `path: str`
* `kinds: tuple[str, ...]`
* `digest: str`

## `RefTo` `@dataclass(frozen=True, init=False)`
`src/chatddx/factors/base.py:RefTo`

* `kinds: tuple[str, ...]`

## `RefTo.__get_pydantic_json_schema__`
`src/chatddx/factors/base.py:RefTo.__get_pydantic_json_schema__`

* `core: CoreSchema`
* `handler: GetJsonSchemaHandler`
* ∟`JsonSchemaValue`

## `RefTo.__init__`
`src/chatddx/factors/base.py:RefTo.__init__`

* `*kinds: str`

## `Refusal` `(Frozen)`
`src/chatddx/factors/facts.py:Refusal`

* `refused: Annotated[str, StringConstraints(min_length=1)]`
* `nearest: Level | None = None`

## `Refused` `(ValueError)`
`src/chatddx/factors/facts.py:Refused`

## `Registry`
`src/chatddx/factors/bundle.py:Registry`

## `Registry.__contains__`
`src/chatddx/factors/bundle.py:Registry.__contains__`

* `digest: object`
* ∟`bool`

## `Registry.__init__`
`src/chatddx/factors/bundle.py:Registry.__init__`

## `Registry.__iter__`
`src/chatddx/factors/bundle.py:Registry.__iter__`

## `Registry.add`
`src/chatddx/factors/bundle.py:Registry.add`

* `component: Component`
* ∟`str`

## `Registry.add_raw`
`src/chatddx/factors/bundle.py:Registry.add_raw`

* `digest: str`
* `raw: bytes`
* ∟`Component`

Raises:
1. `StructuralError`: `"{digest} does not match its bytes"`

## `Registry.bundle`
`src/chatddx/factors/bundle.py:Registry.bundle`

* `roots: Iterable[str]`
* `generator: Code`
* ∟`"Bundle"`

## `Registry.check`
`src/chatddx/factors/bundle.py:Registry.check`

* `digests: Iterable[str] | None = None`
* ∟`None`

Raises:
1. `StructuralError`: `"\n".join(problems)`

## `Registry.closure`
`src/chatddx/factors/bundle.py:Registry.closure`

* `roots: Iterable[str]`
* ∟`list[str]`

## `Registry.get`
`src/chatddx/factors/bundle.py:Registry.get`

* `digest: str`
* ∟`Component`

Raises:
1. `StructuralError`: `"{digest} is not in the registry"`

## `RemoteEngine` `(Component)`
`src/chatddx/factors/engine.py:RemoteEngine`

* `kind: Literal["engine.remote"] = "engine.remote"`
* `api: Api = "chat.completions"`
* `model: RemoteModelRef`

## `RemoteModel` `(Component)`
`src/chatddx/factors/engine.py:RemoteModel`

* `kind: Literal["model.remote"] = "model.remote"`
* `provider: str = Field(min_length=1)`
* `name: str = Field(min_length=1)`

## `RemoteModelRef`
`src/chatddx/factors/engine.py:RemoteModelRef`

`RemoteModelRef = Annotated[Digest, RefTo("model.remote")]`

## `replicates`
`src/chatddx/factors/trial.py:replicates`

* `skeleton: Skeleton`
* `seeds: Sequence[int]`
* ∟`tuple[int, ...]`

## `REQUIRED_SLOTS`
`src/chatddx/factors/request.py:REQUIRED_SLOTS`

`REQUIRED_SLOTS: dict[Purpose, frozenset[SlotName]] = {…}`

## `resolve` `[C: Component]`
`src/chatddx/factors/base.py:resolve`

* `get: Resolver`
* `digest: str`
* `cls: type[C]`
* ∟`C`

Raises:
1. `StructuralError`: `"{digest} is a {component.kind_name}, not a {cls.__name__}"`

## `Resolver`
`src/chatddx/factors/base.py:Resolver`

`Resolver = Callable[[str], "Component"]`

## `Runtime` `(Frozen)`
`src/chatddx/factors/engine.py:Runtime`

* `server: Literal["vllm"] = "vllm"`
* `version: str`
* `closure: str`

## `RUNTIME_KEYS`
`src/chatddx/factors/request.py:RUNTIME_KEYS`

`RUNTIME_KEYS = frozenset(…)`

## `Sampling` `(Component)`
`src/chatddx/factors/request.py:Sampling`

* `kind: Literal["chunk.sampling"] = "chunk.sampling"`
* `temperature: float | None = None`
* `top_p: float | None = None`
* `top_k: int | None = None`
* `min_p: float | None = None`
* `presence_penalty: float | None = None`
* `frequency_penalty: float | None = None`
* `repetition_penalty: float | None = None`
* `stop: tuple[str, ...] = ()`
* `max_output_tokens: int | None = Field(default=None, ge=1)`
* `max_tokens_key: Literal['max_completion_tokens', 'max_tokens'] = 'max_completion_tokens'`
* `recommended: bool = False`

## `Sampling.body`
`src/chatddx/factors/request.py:Sampling.body`

* ∟`dict[str, JsonValue]`

## `Sampling.over`
`src/chatddx/factors/request.py:Sampling.over`

* `values: SamplingValues`
* ∟`"Sampling"`

## `SamplingFacts` `(Frozen)`
`src/chatddx/factors/facts.py:SamplingFacts`

* `recommended: dict[Level, SamplingValues] = Field(default_factory=dict)`
* `generation_config: SamplingValues | None = None`

## `SamplingValues` `(Frozen)`
`src/chatddx/factors/facts.py:SamplingValues`

* `temperature: float | None = None`
* `top_p: float | None = None`
* `top_k: int | None = None`
* `min_p: float | None = None`
* `presence_penalty: float | None = None`
* `frequency_penalty: float | None = None`
* `repetition_penalty: float | None = None`

## `SchemaOp`
`src/chatddx/factors/request.py:SchemaOp`

`SchemaOp = Literal["inline_refs@1"]`

## `Scorer` `(Component)`
`src/chatddx/factors/scoring.py:Scorer`

* `kind: Literal["scorer"] = "scorer"`
* `schema_version: ClassVar[int] = 2`
* `entry_point: EntryPoint`
* `version: int = Field(ge=1)`
* `expectation_schema: ExpectationSchemaRef`
* `views: tuple[View, ...] = Field(min_length=1)`
* `resources: tuple[str, ...] = ()`
* `params: Settings = Field(default_factory=dict)`

## `Scorer.judges` `@property`
`src/chatddx/factors/scoring.py:Scorer.judges`

* ∟`tuple[str, ...]`

## `ScorerRef`
`src/chatddx/factors/scoring.py:ScorerRef`

`ScorerRef = Annotated[Digest, RefTo("scorer")]`

## `Scoring` `(Component)`
`src/chatddx/factors/scoring.py:Scoring`

* `kind: Literal["scoring"] = "scoring"`
* `schema_version: ClassVar[int] = 2`
* `scorer: ScorerRef`
* `expectations: Annotated[tuple[ExpectationRef, ...], AfterValidator(ascending)] = Field(…)`
* `engines: tuple[JudgeEngine, ...] = ()`

## `Scoring.cross_check` `@override`
`src/chatddx/factors/scoring.py:Scoring.cross_check`

* `get: Resolver`
* ∟`list[str]`

## `Scoring.engine_of`
`src/chatddx/factors/scoring.py:Scoring.engine_of`

* `judge: str`
* ∟`str`

Raises:
1. `StructuralError`: `"the scoring pins no engine for judge {judge}"`

## `ScoringRef`
`src/chatddx/factors/scoring.py:ScoringRef`

`ScoringRef = Annotated[Digest, RefTo("scoring")]`

## `Segment`
`src/chatddx/factors/request.py:Segment`

`Segment = str | Slot`

## `select`
`src/chatddx/factors/select.py:select`

* `document: JsonValue`
* `selector: str`
* ∟`list[JsonValue]`

## `Selector`
`src/chatddx/factors/scoring.py:Selector`

`Selector = Annotated[str, AfterValidator(check_selector)]`

## `served_model_name`
`src/chatddx/factors/engine.py:served_model_name`

* `engine: str`
* `get: Resolver`
* ∟`str`

Raises:
1. `StructuralError`: `"{engine} is a {other.kind_name}, not an engine"`

## `Settings`
`src/chatddx/factors/base.py:Settings`

`Settings = Annotated[dict[str, JsonValue], AfterValidator(sorted_keys)]`

## `sha256_digest`
`src/chatddx/factors/base.py:sha256_digest`

* `data: bytes`
* ∟`str`

## `Sha256Hex`
`src/chatddx/factors/base.py:Sha256Hex`

`Sha256Hex = Annotated[str, StringConstraints(pattern=r"^[0-9a-f]{64}$")]`

## `Skeleton` `(Component)`
`src/chatddx/factors/request.py:Skeleton`

* `kind: Literal["skeleton"] = "skeleton"`
* `purpose: Purpose = "generation"`
* `api: Api = "chat.completions"`
* `messages: tuple[Message, ...] = Field(min_length=1)`
* `body: Settings = Field(default_factory=dict)`
* `contract: OutputContract`
* `appendix_layout: AppendixLayout = AppendixLayout()`
* `tools: tuple[ToolRef, ...] = ()`
* `max_rounds: int | None = Field(default=None, ge=1)`

Raises:
1. `ValueError`: `"body may not set {sorted(owned)}"` (through `Skeleton._structure`, in a `ValidationError`)
2. `ValueError`: `"{purpose} requests cannot use slots {sorted(stray)}"` (through `Skeleton._structure`, in a `ValidationError`)
3. `ValueError`: `"{purpose} requests need slots {sorted(missing)}"` (through `Skeleton._structure`, in a `ValidationError`)
4. `ValueError`: `"slots used more than once: {sorted(dupes)}"` (through `Skeleton._structure`, in a `ValidationError`)
5. `ValueError`: `"a skeleton has max_rounds exactly when it has tools"` (through `Skeleton._structure`, in a `ValidationError`)
6. `ValueError`: `"a tool needs a function with a name, not {tool!r}"` (through `Skeleton._structure`, in a `ValidationError`)
7. `ValueError`: `"tools must be a list"` (through `Skeleton._structure`, in a `ValidationError`)
8. `ValueError`: `"tools named more than once"` (through `Skeleton._structure`, in a `ValidationError`)
9. `ValueError`: `"native contract with tools needs response_format, tools and tool_choice auto"` (through `Skeleton._structure`, in a `ValidationError`)
10. `ValueError`: `"native contract needs response_format and no tools"` (through `Skeleton._structure`, in a `ValidationError`)
11. `ValueError`: `"tool contract needs tools and tool_choice only"` (through `Skeleton._structure`, in a `ValidationError`)
12. `ValueError`: `"tool contract with tools needs a tool named {name!r} and tool_choice required"` (through `Skeleton._structure`, in a `ValidationError`)
13. `ValueError`: `"tool contract needs exactly one tool named {name!r}"` (through `Skeleton._structure`, in a `ValidationError`)
14. `ValueError`: `"tool contract needs its tool described as {description!r}"` (through `Skeleton._structure`, in a `ValidationError`)
15. `ValueError`: `"text contract with tools needs tools and tool_choice auto"` (through `Skeleton._structure`, in a `ValidationError`)
16. `ValueError`: `"text contract may not constrain the output"` (through `Skeleton._structure`, in a `ValidationError`)
17. `ValueError`: `"{self.contract.kind} contract needs its schema as an object"` (through `Skeleton._structure`, in a `ValidationError`)

## `Skeleton.cross_check` `@override`
`src/chatddx/factors/request.py:Skeleton.cross_check`

* `get: Resolver`
* ∟`list[str]`

Raises:
1. `ValueError`: `"a tool needs a function with a name, not {tool!r}"` (through `_tool_names`)
2. `ValueError`: `"tools must be a list"` (through `_tool_names`)

## `Skeleton.greedy` `@property`
`src/chatddx/factors/request.py:Skeleton.greedy`

* ∟`bool`

## `Skeleton.output_schema` `@property`
`src/chatddx/factors/request.py:Skeleton.output_schema`

* ∟`JsonValue`

## `Skeleton.render`
`src/chatddx/factors/request.py:Skeleton.render`

* `*`
* `model: str`
* `seed: int | None`
* `fills: Mapping[SlotName, str]`
* `return_token_ids: bool = True`
* ∟`dict[str, JsonValue]`

Raises:
1. `StructuralError`: `"no fill for slots {sorted(missing)}"`

## `SkeletonRef`
`src/chatddx/factors/request.py:SkeletonRef`

`SkeletonRef = Annotated[Digest, RefTo("skeleton")]`

## `Slot` `(Frozen)`
`src/chatddx/factors/request.py:Slot`

* `slot: SlotName`

## `SlotName`
`src/chatddx/factors/request.py:SlotName`

`SlotName = Literal["vignette", "appendices", "completion", "expectation"]`

## `SLOTS_BY_PURPOSE`
`src/chatddx/factors/request.py:SLOTS_BY_PURPOSE`

`SLOTS_BY_PURPOSE: dict[Purpose, frozenset[SlotName]] = {…}`

## `sorted_keys` `[V]`
`src/chatddx/factors/base.py:sorted_keys`

* `mapping: dict[str, V]`
* ∟`dict[str, V]`

## `split`
`src/chatddx/factors/select.py:split`

* `op: SplitOp`
* `items: Iterable[JsonValue]`
* ∟`list[JsonValue]`

## `SplitOp`
`src/chatddx/factors/select.py:SplitOp`

`SplitOp = Literal["lines@1"]`

## `Step`
`src/chatddx/factors/select.py:Step`

`Step = Name | Index | Wild | Filter | Token`

## `StructuralError` `(ValueError)`
`src/chatddx/factors/base.py:StructuralError`

## `suggest_seeds`
`src/chatddx/factors/trial.py:suggest_seeds`

* `n: int`
* ∟`tuple[int, ...]`

## `Text`
`src/chatddx/factors/request.py:Text`

`Text = Annotated[str | tuple[str | Insert, ...], AfterValidator(_text)]`

## `TextOutput` `(Frozen)`
`src/chatddx/factors/request.py:TextOutput`

* `kind: Literal["text"] = "text"`
* `json_schema: dict[str, JsonValue] | None = None`

## `texts`
`src/chatddx/factors/request.py:texts`

* `recipe: Recipe`
* `get: Resolver`
* ∟`dict[str, tuple[str, ...]]`

## `Token` `@dataclass(frozen=True)`
`src/chatddx/factors/select.py:Token`

* `token: str`

## `Tool` `(Component)`
`src/chatddx/factors/request.py:Tool`

* `kind: Literal["tool"] = "tool"`
* `schema_version: ClassVar[int] = 2`
* `name: ToolName`
* `description: str = Field(min_length=1)`
* `parameters: dict[str, JsonValue]`
* `entry_point: EntryPoint`
* `version: int = Field(ge=1)`

## `tool_calls`
`src/chatddx/factors/response.py:tool_calls`

* `response: Mapping[str, JsonValue]`
* ∟`tuple[ToolCall, ...]`

## `ToolCall` `(Frozen)`
`src/chatddx/factors/response.py:ToolCall`

* `id: str`
* `name: str`
* `arguments: str`

## `ToolName`
`src/chatddx/factors/request.py:ToolName`

`ToolName = Annotated[str, StringConstraints(pattern=r"^[A-Za-z0-9_-]{1,64}$")]`

## `ToolOutput` `(Frozen)`
`src/chatddx/factors/request.py:ToolOutput`

* `kind: Literal["tool"] = "tool"`
* `name: str`
* `description: str | None = Field(default=None, min_length=1)`

## `ToolRef`
`src/chatddx/factors/request.py:ToolRef`

`ToolRef = Annotated[Digest, RefTo("tool")]`

## `Toolset` `(Component)`
`src/chatddx/factors/request.py:Toolset`

* `kind: Literal["chunk.toolset"] = "chunk.toolset"`
* `tools: tuple[ToolRef, ...] = Field(min_length=1)`
* `guidance: str | None = Field(default=None, min_length=1)`
* `max_rounds: int = Field(default=5, ge=1)`

## `Toolset.cross_check` `@override`
`src/chatddx/factors/request.py:Toolset.cross_check`

* `get: Resolver`
* ∟`list[str]`

## `translated`
`src/chatddx/factors/request.py:translated`

* `recipe: Recipe`
* `get: Resolver`
* ∟`dict[str, dict[str, str]]`

## `Translations` `(Component)`
`src/chatddx/factors/request.py:Translations`

* `schema_version: ClassVar[int] = 2`
* `kind: Literal["chunk.translations"] = "chunk.translations"`
* `into: Annotated[dict[Language, dict[str, str]], AfterValidator(sorted_keys)] = Field(…)`

Raises:
1. `ValueError`: `"no translations into {language}"` (through `Translations._into`, in a `ValidationError`)
2. `ValueError`: `"whitespace isn't translated"` (through `Translations._into`, in a `ValidationError`)
3. `ValueError`: `"no translation into {language} given for {empty}"` (through `Translations._into`, in a `ValidationError`)

## `Trial` `(Component)`
`src/chatddx/factors/trial.py:Trial`

* `kind: Literal["trial"] = "trial"`
* `schema_version: ClassVar[int] = 2`
* `skeleton: SkeletonRef`
* `engine: EngineRef`
* `cases: Annotated[tuple[CaseRef, ...], AfterValidator(distinct), AfterValidator(ascending)] = Field(…)`
* `cleanup: tuple[CleanupOp, ...] = ()`
* `seeds: Annotated[tuple[int, ...], AfterValidator(distinct)] = Field(min_length=1)`

## `Trial.cross_check` `@override`
`src/chatddx/factors/trial.py:Trial.cross_check`

* `get: Resolver`
* ∟`list[str]`

## `Trial.item_keys` `@property`
`src/chatddx/factors/trial.py:Trial.item_keys`

* ∟`list[tuple[str, int]]`

## `TrialRef`
`src/chatddx/factors/trial.py:TrialRef`

`TrialRef = Annotated[Digest, RefTo("trial")]`

## `UNPINNED_FLAGS`
`src/chatddx/factors/engine.py:UNPINNED_FLAGS`

`UNPINNED_FLAGS = frozenset({"--config"})`

## `untranslated`
`src/chatddx/factors/request.py:untranslated`

* `recipe: Recipe`
* `get: Resolver`
* `into: str`
* ∟`tuple[str, ...]`

## `Validators`
`src/chatddx/factors/lint.py:Validators`

`Validators = dict[str, Validator | str]`

## `View` `(Frozen)`
`src/chatddx/factors/scoring.py:View`

* `output: Selector = ""`
* `expectation: Selector = ""`
* `split: SplitOp | None = None`
* `metric: str`
* `judge: JudgeRef | None = None`
* `params: Settings = Field(default_factory=dict)`

## `View.expectation_items`
`src/chatddx/factors/scoring.py:View.expectation_items`

* `data: JsonValue`
* ∟`list[JsonValue]`

## `View.offered_by`
`src/chatddx/factors/scoring.py:View.offered_by`

* `schema: JsonValue`
* ∟`bool`

## `View.output_items`
`src/chatddx/factors/scoring.py:View.output_items`

* `answer: JsonValue`
* ∟`list[JsonValue]`

## `Vignette` `(Frozen)`
`src/chatddx/factors/cases.py:Vignette`

* `source: str`
* `id: str`
* `fingerprint: Fingerprint`

## `vllm_024`
`src/chatddx/factors/engine.py:vllm_024`

* `engine: Component`
* ∟`LocalEngine | None`

## `Wild` `@dataclass(frozen=True)`
`src/chatddx/factors/select.py:Wild`

## `Writes` `(Frozen)`
`src/chatddx/factors/facts.py:Writes`

* `effort: Literal["none", "minimal", "low", "medium", "high"] | None = None`
* `chat_template_kwargs: Settings = Field(default_factory=dict)`

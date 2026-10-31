# `scorers`

Written by `chatddx-dev index` from `[parts.scorers]`'s code in `settings.toml`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it, a language's after another's:

Python:

```
## `<name>` `@<decorator>` `[<type parameters>]` `(<bases>)`
`<file>:<qualified name>`

* `<parameter or field>: <type> = <default>`
* ∟`<return type>`

Raises:
1. `<exception>`: `<arguments>` (from `<exception caught>`, through `<private helper>`, in a `ValidationError`)

Finds:
1. `<code>`: `<message>` (`<level>`, from `<exception caught>`, through `<private helper>`)
```

- A constant or a type alias is its definition instead of bullets; a class and its `__init__` leave out ∟, and a method its instance; `*`: the parameters after it are keyword-only, `/`: those before it positional-only.
- Raises and Finds are the function's own and its private helpers', in the order the code reaches them, each once, a `Whoops` left out; what a public function it calls raises is in that function's entry.
- Text is quoted, a value in it as `{<expression>}`, and an argument that isn't text is as written; a finding is a warning unless it gives its level.

- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `AGGREGATES`
`src/chatddx/scorers/aggregate.py:AGGREGATES`

`AGGREGATES: dict[str, Callable[[list[float]], float]] = {…}`

## `Answer` `(NamedTuple)`
`src/chatddx/scorers/answer.py:Answer`

* `value: JsonValue | None`
* `problem: str | None = None`
* `salvaged: bool = False`

## `asked`
`src/chatddx/scorers/verdicts.py:asked`

* `judge: Judge`
* `skeleton: Skeleton`
* `view: View`
* `answer: JsonValue | None`
* `expectation: JsonValue`
* ∟`dict[SlotName, str] | Scored`

## `explain_view`
`src/chatddx/scorers/scorer.py:explain_view`

* `scorer: Scorer`
* `metrics: Metrics`
* `index: int`
* `answer: JsonValue | None`
* `data: JsonValue`
* `verdicts: Verdicts | None = None`
* ∟`Replayed`

## `Explained` `(NamedTuple)`
`src/chatddx/scorers/scorer.py:Explained`

* `scored: Scored`
* `texts: list[str] | None = None`
* `marks: tuple[Mark, ...] = ()`
* `picks: tuple[Pick | None, ...] = ()`

## `ExplainFunction`
`src/chatddx/scorers/scorer.py:ExplainFunction`

`ExplainFunction = Callable[…]`

## `explaining`
`src/chatddx/scorers/scorer.py:explaining`

A metric whose score is its explain's, so that the two never disagree.

* `measures: str`
* `explain: ExplainFunction`
* `*more: Any`
* `**given: Any`
* ∟`Metric`

## `first_mention`
`src/chatddx/scorers/patterns.py:first_mention`

* `items: list[str] | None`
* `target: str`
* ∟`Scored`

## `function`
`src/chatddx/scorers/shipped.py:function`

* `scorer: Scorer`
* ∟`Metrics`

Raises:
1. `LookupError`: `"; ".join(found)`

## `Mark` `(NamedTuple)`
`src/chatddx/scorers/scorer.py:Mark`

* `item: int`
* `start: int`
* `end: int`

## `mean`
`src/chatddx/scorers/aggregate.py:mean`

* `values: list[float]`
* ∟`float`

## `mentions`
`src/chatddx/scorers/patterns.py:mentions`

* `items: list[str] | None`
* `target: str | None`
* ∟`Scored`

## `Metric` `@dataclass(frozen=True)`
`src/chatddx/scorers/scorer.py:Metric`

* `measures: str`
* `score: MetricFunction`
* `params: dict[str, JsonValue] = field(default_factory=_no_params)`
* `judged: bool = False`
* `unit: str | None = None`
* `explain: ExplainFunction | None = None`
* `reads: Callable[[list[JsonValue]], object] | None = None`
* `refuses: Callable[[list[JsonValue]], Exception | None] | None = None`

## `MetricFunction`
`src/chatddx/scorers/scorer.py:MetricFunction`

`MetricFunction = Callable[…]`

## `patterns.METRICS`
`src/chatddx/scorers/patterns.py:METRICS`

`METRICS: dict[str, Metric] = {…}`

## `verdicts.METRICS`
`src/chatddx/scorers/verdicts.py:METRICS`

`METRICS: dict[str, Metric] = {…}`

## `Metrics`
`src/chatddx/scorers/scorer.py:Metrics`

* `version: int`
* `metrics: dict[str, Metric]`
* `params: dict[str, JsonValue] | None`

## `Metrics.__call__`
`src/chatddx/scorers/scorer.py:Metrics.__call__`

* `metric: str`
* `output: list[JsonValue] | None`
* `expected: list[JsonValue]`
* `params: Mapping[str, JsonValue]`
* `verdicts: Verdicts | None = None`
* ∟`Scored`

Raises:
1. `ValueError`: `"no metric {metric!r}, only {sorted(self.metrics)}"`

## `Metrics.__init__`
`src/chatddx/scorers/scorer.py:Metrics.__init__`

* `version: int`
* `metrics: Mapping[str, Metric]`
* `params: dict[str, JsonValue] | None = None`

## `Metrics.explained`
`src/chatddx/scorers/scorer.py:Metrics.explained`

* `metric: str`
* `output: list[JsonValue] | None`
* `expected: list[JsonValue]`
* `params: Mapping[str, JsonValue]`
* `verdicts: Verdicts | None = None`
* ∟`Explained`

Raises:
1. `ValueError`: `"no metric {metric!r}, only {sorted(self.metrics)}"`

## `Metrics.names` `@property`
`src/chatddx/scorers/scorer.py:Metrics.names`

* ∟`frozenset[str]`

## `Metrics.problems`
`src/chatddx/scorers/scorer.py:Metrics.problems`

* `scorer: Scorer`
* ∟`list[str]`

## `Metrics.reads`
`src/chatddx/scorers/scorer.py:Metrics.reads`

* `metric: str`
* `expected: list[JsonValue]`
* ∟`object`

Raises:
1. `ValueError`: `"no metric {metric!r}, only {sorted(self.metrics)}"`

## `Metrics.refusal`
`src/chatddx/scorers/scorer.py:Metrics.refusal`

* `metric: str`
* `expected: list[JsonValue]`
* ∟`Exception | None`

## `NO_ANSWER`
`src/chatddx/scorers/scorer.py:NO_ANSWER`

`NO_ANSWER: JsonValue = {"reason": "no answer"}`

## `NO_PARAMS`
`src/chatddx/scorers/scorer.py:NO_PARAMS`

`NO_PARAMS: dict[str, JsonValue] = {"type": "object", "additionalProperties": False}`

## `NO_TARGET`
`src/chatddx/scorers/scorer.py:NO_TARGET`

`NO_TARGET: JsonValue = {"reason": "no target"}`

## `Pattern`
`src/chatddx/scorers/patterns.py:Pattern`

* `text: str`

## `Pattern.__init__`
`src/chatddx/scorers/patterns.py:Pattern.__init__`

* `text: str`

Raises:
1. `Invalid`: `"a pattern names at least one word"`
2. `Invalid`: `"a '(' in %(text)s is never closed", text=repr(self.text)` (through `Pattern._any`)
3. `Invalid`: `"%(token)s names no word", token=repr(token)` (through `Pattern._any`)
4. `Invalid`: `"a word is missing in %(text)s", text=repr(self.text)` (through `Pattern._any`)
5. `Invalid`: `"unexpected %(token)s in %(text)s", token=repr(self._peek()), text=repr(text)`

## `Pattern.alternatives`
`src/chatddx/scorers/patterns.py:Pattern.alternatives`

Each alternative of the pattern's at its top level, as a pattern of its own:
what finds a text the pattern finds, joined by `|`.

* ∟`list[str]`

## `Pattern.example`
`src/chatddx/scorers/patterns.py:Pattern.example`

A text the pattern finds, with `pick(n)` choosing among n alternatives.

* `pick: Callable[[int], int]`
* ∟`str`

## `Pattern.find`
`src/chatddx/scorers/patterns.py:Pattern.find`

* `text: str`
* ∟`int | None`

## `Pattern.spans`
`src/chatddx/scorers/patterns.py:Pattern.spans`

* `text: str`
* ∟`list[tuple[int, int]] | None`

## `Pick` `(NamedTuple)`
`src/chatddx/scorers/scorer.py:Pick`

* `at: str`
* `value: JsonValue | None`
* `counted: float | None`

## `problems`
`src/chatddx/scorers/shipped.py:problems`

* `scorer: Scorer`
* ∟`list[str]`

## `read`
`src/chatddx/scorers/answer.py:read`

* `skeleton: Skeleton`
* `response: Mapping[str, JsonValue] | None`
* ∟`Answer`

## `read_by`
`src/chatddx/scorers/shipped.py:read_by`

* `scorer: Scorer`
* `data: JsonValue`
* ∟`list[object]`

## `reading`
`src/chatddx/scorers/scorer.py:reading`

What each of the scorer's views reads of the expectation's data: two that read
alike score alike.

* `scorer: Scorer`
* `metrics: Metrics`
* `data: JsonValue`
* ∟`list[object]`

## `reciprocal_rank`
`src/chatddx/scorers/patterns.py:reciprocal_rank`

* `items: list[str] | None`
* `target: str`
* ∟`Scored`

## `refusals`
`src/chatddx/scorers/scorer.py:refusals`

Why each of the scorer's views that can't read the expectation's data can't, by
the view's selector into it.

* `scorer: Scorer`
* `metrics: Metrics`
* `data: JsonValue`
* ∟`list[tuple[str, Exception]]`

## `refused`
`src/chatddx/scorers/shipped.py:refused`

* `scorer: Scorer`
* `data: JsonValue`
* ∟`list[tuple[str, Exception]]`

## `Replayed` `(NamedTuple)`
`src/chatddx/scorers/scorer.py:Replayed`

* `output: list[JsonValue] | None`
* `expected: list[JsonValue]`
* `params: dict[str, JsonValue]`
* `explained: Explained`

## `metrics.score`
`src/chatddx/scorers/metrics.py:score`

`score = Metrics(2, {**patterns.METRICS, **verdicts.METRICS})`

## `scorer.score`
`src/chatddx/scorers/scorer.py:score`

* `scorer: Scorer`
* `run: ScoreFunction`
* `answer: JsonValue | None`
* `data: JsonValue`
* `verdicts: Mapping[int, Verdicts] | None = None`
* ∟`list[Scored]`

Raises:
1. `ValueError`: `"views {unjudged} need their judges' verdicts"`

## `score_view`
`src/chatddx/scorers/scorer.py:score_view`

* `scorer: Scorer`
* `run: ScoreFunction`
* `index: int`
* `answer: JsonValue | None`
* `data: JsonValue`
* `verdicts: Verdicts | None = None`
* ∟`Scored`

## `Scored` `(NamedTuple)`
`src/chatddx/scorers/scorer.py:Scored`

* `value: float | None`
* `detail: JsonValue = None`

## `ScoreFunction` `(Protocol)`
`src/chatddx/scorers/scorer.py:ScoreFunction`

## `ScoreFunction.__call__`
`src/chatddx/scorers/scorer.py:ScoreFunction.__call__`

* `metric: str`
* `output: list[JsonValue] | None`
* `expected: list[JsonValue]`
* `params: Mapping[str, JsonValue]`
* `verdicts: Verdicts | None = None`
* ∟`Scored`

## `SCORERS`
`src/chatddx/scorers/shipped.py:SCORERS`

`SCORERS: dict[str, Metrics] = {"chatddx.scorers.metrics:score": metrics.score}`

## `std`
`src/chatddx/scorers/aggregate.py:std`

* `values: list[float]`
* ∟`float`

## `stderr`
`src/chatddx/scorers/aggregate.py:stderr`

* `values: list[float]`
* ∟`float`

## `unit_of`
`src/chatddx/scorers/shipped.py:unit_of`

* `scorer: Scorer`
* `view: int`
* ∟`str`

## `var`
`src/chatddx/scorers/aggregate.py:var`

* `values: list[float]`
* ∟`float`

## `Verdicts`
`src/chatddx/scorers/scorer.py:Verdicts`

`type Verdicts = list[JsonValue | None]`

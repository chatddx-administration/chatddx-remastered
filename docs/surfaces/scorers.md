# `chatddx.scorers`

Written by `chatddx stamp` from `src/chatddx/scorers/`; how to read it is in [docs/surfaces.md](docs/surfaces.md).

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

## `Metrics.names` `@property`
`src/chatddx/scorers/scorer.py:Metrics.names`

* ∟`frozenset[str]`

## `Metrics.problems`
`src/chatddx/scorers/scorer.py:Metrics.problems`

* `scorer: Scorer`
* ∟`list[str]`

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
1. `ValueError`: `"a pattern names at least one word"`
2. `ValueError`: `"a '(' in {self.text!r} is never closed"` (through `Pattern._any`)
3. `ValueError`: `"{token!r} names no word"` (through `Pattern._any`)
4. `ValueError`: `"a word is missing in {self.text!r}"` (through `Pattern._any`)
5. `ValueError`: `"unexpected {self._peek()!r} in {text!r}"`

## `Pattern.find`
`src/chatddx/scorers/patterns.py:Pattern.find`

* `text: str`
* ∟`int | None`

## `problems`
`src/chatddx/scorers/shipped.py:problems`

* `scorer: Scorer`
* ∟`list[str]`

## `read`
`src/chatddx/scorers/answer.py:read`

* `skeleton: Skeleton`
* `response: Mapping[str, JsonValue] | None`
* ∟`Answer`

## `reciprocal_rank`
`src/chatddx/scorers/patterns.py:reciprocal_rank`

* `items: list[str] | None`
* `target: str`
* ∟`Scored`

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

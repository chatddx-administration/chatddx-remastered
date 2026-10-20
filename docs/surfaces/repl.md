# `chatddx.repl`

Written by `chatddx stamp` from `src/chatddx/repl/`; how to read it is in [docs/surfaces/README.md](README.md).

## `ANSWERED`
`src/chatddx/repl/render.py:ANSWERED`

`ANSWERED = frozenset({"answer.unread", "answer.invalid", "answer.salvaged"})`

## `case_and_seed`
`src/chatddx/repl/running.py:case_and_seed`

* `words: list[str]`
* ∟`list[str]`

## `cases`
`src/chatddx/repl/listing.py:cases`

* `repl: Repl`
* ∟`None`

## `clipped`
`src/chatddx/repl/render.py:clipped`

* `text: str`
* `lines: int = 30`
* ∟`str`

## `clipped_line`
`src/chatddx/repl/render.py:clipped_line`

* `text: str`
* `width: int = 60`
* ∟`str`

## `Command` `@dataclass(frozen=True)`
`src/chatddx/repl/commands.py:Command`

* `params: tuple[str, ...]`
* `text: str`
* `run: Callable[..., None] | None`
* `rest: int | None = None`
* `grouped: Callable[[list[str]], list[str]] | None = None`

## `Command.repeats` `@property`
`src/chatddx/repl/commands.py:Command.repeats`

* ∟`bool`

## `COMMANDS`
`src/chatddx/repl/commands.py:COMMANDS`

`COMMANDS: dict[str, Command] = {…}`

## `complete`
`src/chatddx/repl/commands.py:complete`

* `names: Mapping[str, list[str]]`
* `line: str`
* ∟`list[str]`

## `configurations`
`src/chatddx/repl/listing.py:configurations`

* `repl: Repl`
* `name: str | None = None`
* ∟`None`

## `counted`
`src/chatddx/repl/render.py:counted`

* `findings: Iterable[Finding]`
* ∟`list[tuple[Finding, int]]`

## `drawn_seed`
`src/chatddx/repl/shell.py:drawn_seed`

* ∟`int`

## `endpoints`
`src/chatddx/repl/listing.py:endpoints`

* `repl: Repl`
* ∟`None`

## `finding`
`src/chatddx/repl/render.py:finding`

* `f: Finding`
* `times: int = 1`
* ∟`Text`

## `handle`
`src/chatddx/repl/commands.py:handle`

* `repl: Repl`
* `line: str`
* ∟`bool`

## `Held`
`src/chatddx/repl/running.py:Held`

* `console: Console`
* `message: str`
* `pressed: int`
* `scoring: bool`

## `Held.__enter__`
`src/chatddx/repl/running.py:Held.__enter__`

* ∟`Self`

## `Held.__exit__`
`src/chatddx/repl/running.py:Held.__exit__`

* `*_exc: object`
* ∟`None`

## `Held.__init__`
`src/chatddx/repl/running.py:Held.__init__`

* `console: Console`
* `said: str`

## `Held.said`
`src/chatddx/repl/running.py:Held.said`

* ∟`None`

## `Held.scored`
`src/chatddx/repl/running.py:Held.scored`

* `bench: Bench`
* `run: RunStarted`
* `scorers: list[str] | None = None`
* ∟`list[Graded]`

## `Held.stopped` `@property`
`src/chatddx/repl/running.py:Held.stopped`

* ∟`bool`

## `help_`
`src/chatddx/repl/commands.py:help_`

* `repl: Repl`
* ∟`None`

## `HISTORY`
`src/chatddx/repl/loop.py:HISTORY`

`HISTORY = Path.home() / ".chatddx_history"`

## `JudgeLines`
`src/chatddx/repl/render.py:JudgeLines`

* `console: Console`
* `bench: Bench`
* `asked: JudgeAsked | None`
* `tally: Tally | None`

## `JudgeLines.__init__`
`src/chatddx/repl/render.py:JudgeLines.__init__`

* `console: Console`
* `bench: Bench`

## `JudgeLines.close`
`src/chatddx/repl/render.py:JudgeLines.close`

* ∟`None`

## `JudgeLines.event`
`src/chatddx/repl/render.py:JudgeLines.event`

* `event: ScoringEvent`
* ∟`None`

## `LABEL`
`src/chatddx/repl/render.py:LABEL`

`LABEL = "dim"`

## `LATER`
`src/chatddx/repl/render.py:LATER`

`LATER = "yellow"`

## `loop`
`src/chatddx/repl/loop.py:loop`

* `shell: Repl`
* `history: Path = HISTORY`
* ∟`int`

## `MAX_SEED`
`src/chatddx/repl/shell.py:MAX_SEED`

`MAX_SEED = 2**31 - 1`

## `NAMED`
`src/chatddx/repl/render.py:NAMED`

`NAMED = 10`

## `NONE`
`src/chatddx/repl/shell.py:NONE`

`NONE = "none"`

## `outcome`
`src/chatddx/repl/render.py:outcome`

* `skeleton: Skeleton`
* `item: RunItem`
* ∟`tuple[str, str, str | None]`

## `plural`
`src/chatddx/repl/render.py:plural`

* `n: int`
* `one: str`
* `many: str | None = None`
* ∟`str`

## `reasoning`
`src/chatddx/repl/inspecting.py:reasoning`

* `repl: Repl`
* ∟`None`

## `REFUSED`
`src/chatddx/repl/render.py:REFUSED`

`REFUSED = "red"`

## `Repl`
`src/chatddx/repl/shell.py:Repl`

* `bench: Bench`
* `variation: TriedVariation | None`
* `under: str | None`
* `seed: int`
* `failed: bool`

## `Repl.__init__`
`src/chatddx/repl/shell.py:Repl.__init__`

* `bench: Bench`
* `console: Console`
* `seed: int | None = None`

## `Repl.at` `@property`
`src/chatddx/repl/shell.py:Repl.at`

* ∟`Endpoint | None`

## `Repl.completions`
`src/chatddx/repl/shell.py:Repl.completions`

* ∟`dict[str, list[str]]`

## `Repl.console`
`src/chatddx/repl/shell.py:console`

* `width: int | None = None`
* ∟`Console`

## `Repl.engine` `@property`
`src/chatddx/repl/shell.py:Repl.engine`

* ∟`str | None`

## `Repl.error`
`src/chatddx/repl/shell.py:Repl.error`

* `message: str`
* ∟`None`

## `Repl.forget`
`src/chatddx/repl/shell.py:Repl.forget`

* ∟`None`

## `Repl.handle`
`src/chatddx/repl/shell.py:Repl.handle`

* `at: Endpoint`
* ∟`str`

## `Repl.prompt` `@property`
`src/chatddx/repl/shell.py:Repl.prompt`

* ∟`str`

## `Repl.say_changed`
`src/chatddx/repl/shell.py:Repl.say_changed`

* `variation: TriedVariation`
* ∟`None`

## `Repl.say_findings`
`src/chatddx/repl/shell.py:Repl.say_findings`

* `findings: Iterable[Finding]`
* `tally: bool = False`
* ∟`None`

## `Repl.say_variation`
`src/chatddx/repl/shell.py:Repl.say_variation`

* `variation: TriedVariation`
* ∟`Endpoint | None`

## `replay`
`src/chatddx/repl/reviewing.py:replay`

* `repl: Repl`
* `prefix: str | None = None`
* ∟`None`

## `run`
`src/chatddx/repl/running.py:run`

* `repl: Repl`
* `name: str`
* `seed: str | None = None`
* ∟`None`

## `runs`
`src/chatddx/repl/reviewing.py:runs`

* `repl: Repl`
* `count: str = "20"`
* ∟`None`

## `said`
`src/chatddx/repl/reviewing.py:said`

* `repl: Repl`
* `started: RunStarted`
* ∟`None`

## `save`
`src/chatddx/repl/choosing.py:save`

* `repl: Repl`
* `name: str`
* ∟`None`

## `score`
`src/chatddx/repl/scoring.py:score`

* `repl: Repl`
* `prefix: str | None = None`
* ∟`None`

## `SCORED`
`src/chatddx/repl/inspecting.py:SCORED`

`SCORED = frozenset({"scorer", "judge", "expectation", "expectation_schema"})`

## `scored_findings`
`src/chatddx/repl/render.py:scored_findings`

* `graded: Iterable[Graded]`
* `read: bool = False`
* ∟`list[Finding]`

## `scorers`
`src/chatddx/repl/scoring.py:scorers`

* `repl: Repl`
* ∟`None`

## `SCORING`
`src/chatddx/repl/running.py:SCORING`

`SCORING = "Ctrl-C again stops the scoring"`

## `seed`
`src/chatddx/repl/running.py:seed`

* `repl: Repl`
* `value: str | None = None`
* ∟`None`

## `SEEDS`
`src/chatddx/repl/shell.py:SEEDS`

`SEEDS = 100_000`

## `set_`
`src/chatddx/repl/choosing.py:set_`

* `repl: Repl`
* `part: str`
* `name: str`
* ∟`None`

## `show`
`src/chatddx/repl/inspecting.py:show`

* `repl: Repl`
* `kind: str | None = None`
* `*names: str`
* ∟`None`

## `show_answer`
`src/chatddx/repl/render.py:show_answer`

* `console: Console`
* `skeleton: Skeleton`
* `item: RunItem`
* `graded: list[Graded]`
* ∟`None`

## `show_judged`
`src/chatddx/repl/render.py:show_judged`

* `console: Console`
* `bench: Bench`
* `graded: list[Graded]`
* ∟`None`

## `show_scores`
`src/chatddx/repl/render.py:show_scores`

* `console: Console`
* `graded: list[Graded]`
* ∟`None`

## `show_summary`
`src/chatddx/repl/render.py:show_summary`

* `console: Console`
* `graded: list[Graded]`
* ∟`None`

## `show_table`
`src/chatddx/repl/render.py:show_table`

* `console: Console`
* `names: dict[str, str]`
* `items: list[RunItem]`
* `graded: list[Graded]`
* ∟`None`

## `some`
`src/chatddx/repl/render.py:some`

* `names: Iterable[str]`
* ∟`str`

## `STYLES`
`src/chatddx/repl/render.py:STYLES`

`STYLES: dict[Outcome, str] = {…}`

## `tagged`
`src/chatddx/repl/running.py:tagged`

* `repl: Repl`
* `*tags: str`
* ∟`None`

## `take`
`src/chatddx/repl/scoring.py:take`

* `repl: Repl`
* `*words: str`
* ∟`None`

## `Tally`
`src/chatddx/repl/render.py:Tally`

* `console: Console`
* `width: int`
* `case: str`
* `tokens: int`
* `counted: bool`
* `last: bool`
* `live: Live`

## `Tally.__enter__`
`src/chatddx/repl/render.py:Tally.__enter__`

* ∟`Self`

## `Tally.__exit__`
`src/chatddx/repl/render.py:Tally.__exit__`

* `*_: object`
* ∟`None`

## `Tally.__init__`
`src/chatddx/repl/render.py:Tally.__init__`

* `console: Console`
* `width: int`
* `case: str`

## `Tally.count`
`src/chatddx/repl/render.py:Tally.count`

* `tokens: int`
* ∟`None`

## `Tally.end`
`src/chatddx/repl/render.py:Tally.end`

* `tokens: int`
* `word: str`
* `style: str`
* `said: str | None`
* ∟`None`

## `Tally.stopping`
`src/chatddx/repl/render.py:Tally.stopping`

* ∟`None`

## `THINKING`
`src/chatddx/repl/render.py:THINKING`

`THINKING = "#5f87af"`

## `TOKENS`
`src/chatddx/repl/render.py:TOKENS`

`TOKENS = len("tokens")`

## `Transcript`
`src/chatddx/repl/render.py:Transcript`

* `console: Console`
* `at_start: bool`
* `labelled: bool`
* `held: str`
* `kind: str | None`

## `Transcript.__init__`
`src/chatddx/repl/render.py:Transcript.__init__`

* `console: Console`

## `Transcript.begin`
`src/chatddx/repl/render.py:Transcript.begin`

* `label: str | None`
* ∟`None`

## `Transcript.event`
`src/chatddx/repl/render.py:Transcript.event`

* `event: RunEvent`
* ∟`None`

## `Transcript.item`
`src/chatddx/repl/render.py:Transcript.item`

* `item: RunItem`
* ∟`None`

## `Transcript.write`
`src/chatddx/repl/render.py:Transcript.write`

* `text: str`
* `style: str = ""`
* ∟`None`

## `under`
`src/chatddx/repl/choosing.py:under`

* `repl: Repl`
* `name: str`
* ∟`None`

## `UNTARGETED`
`src/chatddx/repl/render.py:UNTARGETED`

`UNTARGETED: tuple[JsonValue, ...] = (NO_TARGET, NO_EXPECTATION)`

## `use`
`src/chatddx/repl/choosing.py:use`

* `repl: Repl`
* `name: str`
* ∟`None`

## `VALID`
`src/chatddx/repl/render.py:VALID`

`VALID = "green"`

## `value_of`
`src/chatddx/repl/render.py:value_of`

* `value: float | None`
* `unit: str = ""`
* ∟`str`

## `verdict_of`
`src/chatddx/repl/render.py:verdict_of`

* `view: View`
* `verdict: JsonValue | None`
* ∟`tuple[str | None, str | None]`

## `when`
`src/chatddx/repl/reviewing.py:when`

* `started: RunStarted`
* ∟`str`

## `writes`
`src/chatddx/repl/render.py:writes`

* `values: dict[str, JsonValue]`
* `prefix: str = ""`
* ∟`str`

## `WRITING`
`src/chatddx/repl/running.py:WRITING`

`WRITING = "the run is written down and scored first; Ctrl-C again stops the scoring"`

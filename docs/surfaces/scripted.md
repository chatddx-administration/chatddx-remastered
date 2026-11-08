# `scripted`

Written by `chatddx-dev index` from `[parts.scripted]`'s code in `settings.toml`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it, a language's after another's:

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

## `canaried`
`src/chatddx/scripted/fakes.py:canaried`

The messages of each canary of the set, none for none: what a script leaves to the
fake, as a script answers a run's items alone. Reads the set.

* `get: Resolver`
* `canaries: str | None`
* ∟`list[tuple[object, ...]]`

## `clock` `@contextmanager`
`src/chatddx/scripted/answering.py:clock`

* `at: datetime`
* ∟`Generator[None]`

## `Composed` `@dataclass(frozen=True)`
`src/chatddx/scripted/composed.py:Composed`

* `gatherings: dict[str, dict[Sort, int]]`
* `versions: dict[str, int]`
* `broken: int`
* `unfinished: int`
* `skipped: dict[str, str]`

## `composed`
`src/chatddx/scripted/composed.py:composed`

Writes a few weeks of composing for each of the person's configurations that
runs: `versions` versions of it, each its sampling with a temperature drawn, and
`gatherings` gatherings of it spread over the last `days` days, as Run starts
them: a baseline on the World's baseline cases as each version is saved, reviews of
a case, and tries on a handful of cases. Each version is drawn a mean quality its
answers are drawn around, against each case's expectation under the schema, and a
few gatherings are broken by a server that hangs up, or left with a run
unfinished. A configuration without a recipe is gathered at its head alone.

Sends and scores every run in the calling thread, serving each one's fakes the
while, on ports of this machine's for endpoints the fake vLLM doesn't run; lifts
the person's quota of runs for as long.

Heads-up: `LookupError` when no configuration of the person's runs, or the person
sees no case.

* `bench: Bench`
* `schema: str`
* `*`
* `gatherings: int = 36`
* `versions: int = 6`
* `seed: int = 1`
* `days: int = 42`
* ∟`Composed`

Raises:
1. `LookupError`: `"no configuration of {bench.person.login}'s runs: {said}"`
2. `LookupError`: `"{bench.person.login} sees no case to run"`

## `fake_at`
`src/chatddx/scripted/fakes.py:fake_at`

* `inventory: Inventory`
* `get: Resolver`
* `name: str`
* ∟`Served`

Raises:
1. `LookupError`: `str(e)` (from `StructuralError`)
2. `LookupError`: `"endpoint {name!r} isn't on this machine"` (through `_stand_in`)
3. `LookupError`: `"endpoint {name!r} asks for the key in {spec.credential}, which isn't set"` (through `_stand_in`)
4. `LookupError`: `"endpoint {name!r} runs in {startup.closure}, not the fake vLLM"`
5. `LookupError`: `"{name} won't start: {e}"` (from `Refused`)

## `FIELDS`
`src/chatddx/scripted/answering.py:FIELDS`

`FIELDS = ("diagnosis", "warning", "disposition", "dont_miss")`

## `judging` `@contextmanager`
`src/chatddx/scripted/run.py:judging`

* `bench: Bench`
* `run: RunStarted`
* `fakes: Mapping[str, Served] | None = None`
* ∟`Generator[None]`

## `load`
`src/chatddx/scripted/read.py:load`

* `path: Path`
* ∟`ScriptedRun`

Raises:
1. `ValueError`: `"{path}: {e}"` (from `(ValidationError, Refused)`)

## `NONE`
`src/chatddx/scripted/run.py:NONE`

`NONE = "none"`

## `pattern_of`
`src/chatddx/scripted/answering.py:pattern_of`

* `data: JsonValue`
* `field: str`
* ∟`str | None`

## `Placed` `@dataclass(frozen=True)`
`src/chatddx/scripted/answering.py:Placed`

* `variation: TriedVariation`
* `endpoint: str`
* `fake: Served`

## `placing`
`src/chatddx/scripted/answering.py:placing`

* `bench: Bench`
* `fakes: dict[str, Served]`
* `refused: dict[str, str]`
* ∟`tuple[list[Placed], dict[str, str]]`

## `Quality` `@dataclass(frozen=True)`
`src/chatddx/scripted/answering.py:Quality`

* `data: dict[str, JsonValue]`
* `mean: float`

## `ran_before`
`src/chatddx/scripted/run.py:ran_before`

* `bench: Bench`
* `scripted: ScriptedRun`
* ∟`RunStarted | None`

Raises:
1. `ValueError`: `"{scripted.configuration}: a scripted run's cases are sent in one language, not as {said}"` (through `_sent`)

## `review`
`src/chatddx/scripted/review.py:review`

Writes a review's worth of the case for the person: their expectation of it under
the schema in `versions` versions, and `gatherings` evaluations of it, as Run starts
them, spread over the last `days` days, each scored against one of the versions and
answered by the fake vLLM as well as a quality drawn for its version has it. A few
are broken by a server that hangs up, or left with a run unfinished.

Sends and scores every run in the calling thread, serving each one's fakes the while,
on ports of this machine's for endpoints the fake vLLM doesn't run; lifts the
person's quota of runs for as long.

Heads-up: `LookupError` when no configuration of the person's can run the case.

* `bench: Bench`
* `case: str`
* `schema: str`
* `*`
* `gatherings: int = 40`
* `versions: int = 12`
* `seed: int = 1`
* `days: int = 42`
* ∟`Reviewed`

Raises:
1. `LookupError`: `"no configuration of {bench.person.login}'s can run {bench.title(case)}: {said}"`
2. `LookupError`: `"{bench.title(case)} has no expectation under {schema}"` (through `_base`)
3. `LookupError`: `"{bench.title(case)}'s expectation isn't an object"` (through `_base`)

## `Reviewed` `@dataclass(frozen=True)`
`src/chatddx/scripted/review.py:Reviewed`

* `gatherings: int`
* `versions: int`
* `broken: int`
* `unfinished: int`
* `skipped: dict[str, str]`

## `run`
`src/chatddx/scripted/run.py:run`

* `bench: Bench`
* `scripted: ScriptedRun`
* ∟`RunStarted`

Raises:
1. `ValueError`: `"{scripted.configuration}: a scripted run's cases are sent in one language, not as {said}"` (through `_sent`)

## `RUNS`
`src/chatddx/scripted/__init__.py:RUNS`

`RUNS = "_runs"`

## `scripted_runs`
`src/chatddx/scripted/read.py:scripted_runs`

* `directory: Path`
* ∟`list[ScriptedRun]`

## `ScriptedRun` `(BaseModel)`
`src/chatddx/scripted/read.py:ScriptedRun`

* `model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")`
* `name: str`
* `description: str`
* `configuration: str`
* `set: dict[str, str] = Field(default_factory=dict)`
* `endpoint: str`
* `cases: tuple[str, ...] = Field(min_length=1)`
* `seed: int = Field(default=7, ge=0)`
* `stop_after: int | None = Field(default=None, ge=1)`
* `unfinished: bool = False`
* `scored: bool = True`
* `turns: tuple[Turn, ...] = ()`

## `send`
`src/chatddx/scripted/answering.py:send`

* `bench: Bench`
* `fake: Served`
* `fakes: dict[str, Served]`
* `running: Running`
* `turns: list[Turn]`
* `finish: bool`
* ∟`None`

## `Sort`
`src/chatddx/scripted/composed.py:Sort`

`type Sort = Literal["baseline", "review", "try"]`

## `standing_in`
`src/chatddx/scripted/fakes.py:standing_in`

The inventory with each endpoint but those the fake vLLM serves as they are moved
to a free port of this machine, the fakes that serve them all, and why each endpoint
neither can be served is left out. Binds a socket for each port it takes.

* `inventory: Inventory`
* `get: Resolver`
* ∟`tuple[Inventory, dict[str, Served], dict[str, str]]`

## `turn`
`src/chatddx/scripted/answering.py:turn`

* `bench: Bench`
* `running: Running`
* `rng: random.Random`
* `version: Quality`
* `hang_up: bool`
* ∟`Turn`

## `variation`
`src/chatddx/scripted/run.py:variation`

* `bench: Bench`
* `scripted: ScriptedRun`
* ∟`TriedVariation`

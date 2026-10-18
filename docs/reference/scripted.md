# `chatddx.scripted`

Written by `chatddx reference` from `src/chatddx/scripted/`; how to read it is in [docs/reference/README.md](README.md).

## fake_at
`src/chatddx/scripted/fakes.py:fake_at`

* `inventory: Inventory`
* `get: Resolver`
* `name: str`
* ∟`Served`

Raises:

1. `LookupError`: str(e) (from `StructuralError`)
2. `LookupError`: "endpoint {name!r} isn't on this machine" (through `_stand_in`)
3. `LookupError`: "endpoint {name!r} asks for the key in {spec.credential}, which isn't set" (through `_stand_in`)
4. `LookupError`: "endpoint {name!r} runs in {startup.closure}, not the fake vLLM"
5. `LookupError`: "{name} won't start: {e}" (from `Refused`)

## load
`src/chatddx/scripted/read.py:load`

* `path: Path`
* ∟`ScriptedRun`

Raises:

1. `ValueError`: "{path}: {e}" (from `(ValidationError, Refused)`)

## NONE
`src/chatddx/scripted/run.py:NONE`

* `NONE = "none"`

## ran_before
`src/chatddx/scripted/run.py:ran_before`

* `bench: Bench`
* `scripted: ScriptedRun`
* ∟`RunStarted | None`

Raises:

1. `ValueError`: "{scripted.configuration}: a scripted run's cases are sent in one language, not as {said}" (through `_sent`)

## run
`src/chatddx/scripted/run.py:run`

* `bench: Bench`
* `scripted: ScriptedRun`
* ∟`RunStarted`

Raises:

1. `ValueError`: "{scripted.configuration}: a scripted run's cases are sent in one language, not as {said}" (through `_sent`)

## RUNS
`src/chatddx/scripted/__init__.py:RUNS`

* `RUNS = "_runs"`

## scripted_runs
`src/chatddx/scripted/read.py:scripted_runs`

* `directory: Path`
* ∟`list[ScriptedRun]`

## ScriptedRun `(BaseModel)`
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

## variation
`src/chatddx/scripted/run.py:variation`

* `bench: Bench`
* `scripted: ScriptedRun`
* ∟`TriedVariation`

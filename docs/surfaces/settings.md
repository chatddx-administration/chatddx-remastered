# `chatddx.settings`

Written by `chatddx stamp write` from `src/chatddx/settings.py`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it:

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
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

## `chromium`
`src/chatddx/settings.py:chromium`

* ∟`Path | None`

## `database`
`src/chatddx/settings.py:database`

* `admin: bool = False`
* ∟`str`

## `host`
`src/chatddx/settings.py:host`

* ∟`str`

## `ITEMS_PER_RUN`
`src/chatddx/settings.py:ITEMS_PER_RUN`

`ITEMS_PER_RUN = 1000`

## `portal_assets`
`src/chatddx/settings.py:portal_assets`

* ∟`Path`

## `PROJECT_ROOT`
`src/chatddx/settings.py:PROJECT_ROOT`

`PROJECT_ROOT = Path(__file__).resolve().parents[2]`

## `revision`
`src/chatddx/settings.py:revision`

* ∟`str | None`

## `RUNS_PER_DAY`
`src/chatddx/settings.py:RUNS_PER_DAY`

`RUNS_PER_DAY = 100`

## `SESSION_TTL`
`src/chatddx/settings.py:SESSION_TTL`

`SESSION_TTL = timedelta(hours=12)`

## `Stage` `(IntEnum)`
`src/chatddx/settings.py:Stage`

* `FELT = 1`
* `IMPLIED = 2`
* `MENTIONED = 3`
* `NAMED = 4`
* `ITEMIZED = 5`
* `PLANNED = 6`
* `DRAFTED = 7`
* `SOLIDIFIED = 8`
* `CEMENTED = 9`
* `PROTECTED = 10`

## `STAGES`
`src/chatddx/settings.py:STAGES`

`STAGES = {…}`

<<<<<<< signed
=======
## `stamp_base`
`src/chatddx/settings.py:stamp_base`

* ∟`str | None`

>>>>>>> @stamp
## `STAMPED_FROM`
`src/chatddx/settings.py:STAMPED_FROM`

`STAMPED_FROM = {…}`

## `TYPED_PER_DAY`
`src/chatddx/settings.py:TYPED_PER_DAY`

`TYPED_PER_DAY = 50`

## `TYPED_TEXT_LIMIT`
`src/chatddx/settings.py:TYPED_TEXT_LIMIT`

`TYPED_TEXT_LIMIT = 20_000`

## `WORKER_BEAT`
`src/chatddx/settings.py:WORKER_BEAT`

`WORKER_BEAT = timedelta(seconds=1)`

## `WORKER_DEADLINE`
`src/chatddx/settings.py:WORKER_DEADLINE`

`WORKER_DEADLINE = timedelta(seconds=60)`

## `WORKER_JOBS`
`src/chatddx/settings.py:WORKER_JOBS`

`WORKER_JOBS = 8`

## `WORKER_LOST`
`src/chatddx/settings.py:WORKER_LOST`

`WORKER_LOST = timedelta(seconds=10)`

## `world`
`src/chatddx/settings.py:world`

* ∟`Path | None`

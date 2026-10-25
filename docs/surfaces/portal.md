# `chatddx.portal`

Written by `chatddx stamp write` from `src/chatddx/portal/`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it:

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

## `app`
`src/chatddx/portal/app.py:app`

* `world: World`
* `conninfo: str`
* `assets: Path | None = None`
* `worker: bool = False`
* ∟`FastAPI`

## `appended`
`src/chatddx/portal/cases.py:appended`

* `bench: Bench`
* `family: int`
* `name: str`
* `text: str`
* ∟`None`

Raises:
1. `Invalid`: `"an appendix is named"`
2. `Invalid`: `"an appendix holds a text"`

## `appending_in_review` `@router.post("/review/{family}/appendices")`
`src/chatddx/portal/review.py:appending_in_review`

* `bench: BenchDep`
* `family: int`
* `name: Annotated[str, Form()]`
* `text: Annotated[str, Form()]`
* `back: Annotated[str | None, Form()] = None`
* ∟`Response`

## `AskedBy` `@dataclass(frozen=True)`
`src/chatddx/portal/scoring.py:AskedBy`

* `scorer: schemas.Thread`
* `label: str`
* `asks: str`
* `latest: bool`
* `at: int`
* `schema: str`
* `expectation: str`

## `AskedBy.key` `@property`
`src/chatddx/portal/scoring.py:AskedBy.key`

* ∟`str`

## `Assets` `@dataclass(frozen=True)`
`src/chatddx/portal/assets.py:Assets`

* `root: Path`

## `Assets.built` `@property`
`src/chatddx/portal/assets.py:Assets.built`

* ∟`bool`

## `Assets.island`
`src/chatddx/portal/assets.py:Assets.island`

* `name: str`
* ∟`Island`

## `Assets.styles`
`src/chatddx/portal/assets.py:Assets.styles`

* ∟`list[str]`

## `lab.beginning` `@router.get("/lab/run")`
`src/chatddx/portal/lab.py:beginning`

* `request: Request`
* `bench: BenchDep`
* `trial: Annotated[list[int] | None, Query()] = None`
* ∟`Response`

Raises:
1. `NotFound`: `"no trial %(thread)s for %(login)s", thread=thread, login=bench.person.login` (through `_starting`)

## `threads.beginning` `@router.get("/library/new")`
`src/chatddx/portal/threads.py:beginning`

* `request: Request`
* `bench: BenchDep`
* `kind: str`
* `configuration: int | None = None`
* `into: str | None = None`
* ∟`Response`

Raises:
1. `NotFound`: `"no %(kind)s is begun here: what is begun here is %(kinds)s", kind=kind, kinds=", ".join(_BEGUN)` (through `_begun`)
2. `Refusing`: `422, e` (from `NotFound`, through `_beginning_translations`)

## `begun`
`src/chatddx/portal/translations.py:begun`

* `bench: Bench`
* `configuration: int`
* `into: str`
* ∟`list[Entry]`

Raises:
1. `ValueError`: `tr('%(configuration)s has no recipe whose texts to translate', configuration=shown.name or shown.title)`

## `BenchDep`
`src/chatddx/portal/pages.py:BenchDep`

`type BenchDep = Annotated[Bench, Depends(page_bench)]`

## `blank`
`src/chatddx/portal/scoring.py:blank`

* `code: schemas.ScorerCode`
* `schema: str`
* ∟`dict[str, Any]`

## `building` `@router.post("/cases/{family}/cases")`
`src/chatddx/portal/cases.py:building`

* `request: Request`
* `bench: BenchDep`
* `family: int`
* `appendices: Annotated[list[str] | None, Form(alias="f.appendices")] = None`
* `back: Annotated[str | None, Form()] = None`
* ∟`Response`

Raises:
1. `NotFound`: `"no version %(at)s of case %(family)s: it has %(versions)s", at=at, family=family, versions=len(bindings)` (through `_case_page`)

## `built`
`src/chatddx/portal/cases.py:built`

* `bench: Bench`
* `family: int`
* `appendices: list[str] | None`
* ∟`str`

Raises:
1. `Invalid`: `"a case is built of one appendix or more"`

## `carrying` `@router.post("/threads/{thread}/carry")`
`src/chatddx/portal/threads.py:carrying`

* `bench: BenchDep`
* `thread: int`
* `head: Annotated[int, Form()]`
* `case: Annotated[str, Form()]`
* `next: Annotated[str | None, Form()] = None`
* ∟`Response`

## `case_page` `@router.get("/cases/{family}")`
`src/chatddx/portal/cases.py:case_page`

* `request: Request`
* `bench: BenchDep`
* `family: int`
* `version: int | None = None`
* ∟`Response`

Raises:
1. `NotFound`: `"no version %(at)s of case %(family)s: it has %(versions)s", at=at, family=family, versions=len(bindings)` (through `_case_page`)

## `Cased` `(Protocol)`
`src/chatddx/portal/titles.py:Cased`

## `Cased.appendices` `@property`
`src/chatddx/portal/titles.py:Cased.appendices`

* ∟`Sequence[str]`

## `Cased.earlier` `@property`
`src/chatddx/portal/titles.py:Cased.earlier`

* ∟`bool`

## `Cased.name` `@property`
`src/chatddx/portal/titles.py:Cased.name`

* ∟`str`

## `Change` `@dataclass(frozen=True)`
`src/chatddx/portal/changes.py:Change`

* `path: str`
* `was: Literal["added", "removed", "changed"]`
* `before: JsonValue = None`
* `after: JsonValue = None`
* `words: list[tuple[Literal["", "+", "-"], str]] | None = None`

## `changes`
`src/chatddx/portal/changes.py:changes`

* `before: JsonValue`
* `after: JsonValue`
* `path: str = ""`
* ∟`list[Change]`

## `checked`
`src/chatddx/portal/scoring.py:checked`

* `bench: Bench`
* `held: Component`
* ∟`tuple[list[Finding], list[str]]`

## `choices`
`src/chatddx/portal/fields.py:choices`

* `bench: Bench`
* `kinds: tuple[str, ...]`
* `held: JsonValue`
* `purpose: Purpose | None = None`
* ∟`list[tuple[str, str]]`

## `code_of`
`src/chatddx/portal/scoring.py:code_of`

* `bench: Bench`
* `entry_point: str | None = None`
* ∟`schemas.ScorerCode`

## `Column` `@dataclass`
`src/chatddx/portal/lab.py:Column`

* `skeletons: tuple[str, ...]`
* `handle: str | None`
* `why: str | None = None`
* `names: list[schemas.Kin] = field(default_factory=list[schemas.Kin])`
* `run: schemas.Run | None = None`
* `earlier: list[schemas.Run] = field(default_factory=list[schemas.Run])`

## `comparing` `@router.get("/runs/compare")`
`src/chatddx/portal/runs.py:comparing`

* `request: Request`
* `bench: BenchDep`
* `run: Annotated[list[UUID] | None, Query()] = None`
* `by: str | None = None`
* ∟`Response`

Raises:
1. `Invalid`: `"pick the runs to compare on the runs page"`

## `defaults`
`src/chatddx/portal/fields.py:defaults`

* `model: type[BaseModel]`
* ∟`dict[str, JsonValue]`

## `cases.deleting` `@router.post("/cases/{family}/delete")`
`src/chatddx/portal/cases.py:deleting`

* `bench: BenchDep`
* `family: int`
* ∟`Response`

## `threads.deleting` `@router.post("/threads/{thread}/delete")`
`src/chatddx/portal/threads.py:deleting`

* `bench: BenchDep`
* `thread: int`
* ∟`Response`

## `display_case`
`src/chatddx/portal/titles.py:display_case`

* `case: Cased`
* `brief: bool = False`
* ∟`str`

## `display_kind`
`src/chatddx/portal/shelves.py:display_kind`

* `word: str`
* ∟`str`

## `display_thread`
`src/chatddx/portal/titles.py:display_thread`

* `thread: schemas.Thread`
* ∟`str`

## `edges`
`src/chatddx/portal/translations.py:edges`

* `text: str`
* ∟`tuple[str, str]`

## `editing` `@router.post("/threads/{thread}/edit")`
`src/chatddx/portal/threads.py:editing`

* `request: Request`
* `bench: BenchDep`
* `thread: int`
* `form: FormDep`
* ∟`Response`

Raises:
1. `NotFound`: `"no version %(at)s of %(kind)s %(thread)s: it has %(versions)s", at=at, kind=display_kind(word), thread=thread, versions=len(versions)` (through `_thread_page`)
2. `Invalid`: `"configuration %(thread)s is written by hand: it has no recipe to pick parts of", thread=thread`
3. `Invalid`: `"labels: %(refused)s", refused=e.errors()[0]["msg"]` (from `ValidationError`, through `_labels`)

## `editors`
`src/chatddx/portal/editors.py:editors`

* `bench: Bench`
* `model: type[BaseModel]`
* `found: list[Field]`
* ∟`dict[str, Any] | None`

## `Entry` `@dataclass(frozen=True)`
`src/chatddx/portal/translations.py:Entry`

* `text: str`
* `translation: str`
* `sent: bool`
* `held: bool`
* `started: str | None = None`

## `Entry.uneven` `@property`
`src/chatddx/portal/translations.py:Entry.uneven`

* ∟`bool`

## `lab.Fared` `@dataclass(frozen=True)`
`src/chatddx/portal/lab.py:Fared`

* `columns: list[Column]`
* `compared: schemas.Compared | None`
* `rows: list[tuple[str, schemas.ComparedView, list[tuple[float | None, int] | None]]]`
* `by: str | None`
* `mean_of: dict[int, float | None]`
* `cases: int | None`

## `scoring.Fared` `@dataclass(frozen=True)`
`src/chatddx/portal/scoring.py:Fared`

* `run: schemas.Run`
* `means: list[float | None]`

## `Field` `@dataclass(frozen=True)`
`src/chatddx/portal/fields.py:Field`

* `name: str`
* `shape: Shape`
* `value: JsonValue`
* `editable: bool`
* `nullable: bool = False`
* `kinds: tuple[str, ...] = ()`
* `options: tuple[str, ...] = ()`
* `given: bool = True`
* `whole: bool = False`
* `minimum: int | float | None = None`
* `typed: str | None = None`
* `refused: str | None = None`

## `fields`
`src/chatddx/portal/fields.py:fields`

* `model: type[BaseModel]`
* `body: Mapping[str, JsonValue]`
* `editable: Collection[str]`
* ∟`list[Field]`

## `scoring.following` `@router.post("/scoring/{thread}/follow")`
`src/chatddx/portal/scoring.py:following`

* `bench: BenchDep`
* `thread: int`
* `scorer: Annotated[int, Form()]`
* `head: Annotated[int, Form()]`
* ∟`Response`

Raises:
1. `NotFound`: `"no judge %(thread)s for %(login)s", thread=thread, login=bench.person.login`
2. `MovedOn`: `"scorer %(scorer)s has a newer version: look at it again", scorer=scorer`

## `threads.following` `@router.post("/threads/{thread}/follow")`
`src/chatddx/portal/threads.py:following`

* `bench: BenchDep`
* `thread: int`
* `head: Annotated[int, Form()]`
* `next: Annotated[str | None, Form()] = None`
* ∟`Response`

## `following_moved` `@router.post("/threads/{thread}/moved/follow")`
`src/chatddx/portal/threads.py:following_moved`

* `bench: BenchDep`
* `thread: int`
* `head: Annotated[int, Form()]`
* `next: Annotated[str | None, Form()] = None`
* ∟`Response`

## `forking` `@router.post("/threads/{thread}/fork")`
`src/chatddx/portal/threads.py:forking`

* `bench: BenchDep`
* `thread: int`
* `name: Annotated[str, Form()]`
* ∟`Response`

Raises:
1. `Invalid`: `"a fork is named"`

## `FormDep`
`src/chatddx/portal/threads.py:FormDep`

`FormDep = Annotated[FormData, Depends(_form)]`

## `fresh`
`src/chatddx/portal/fields.py:fresh`

* `model: type[BaseModel]`
* `given: Mapping[str, str] | None = None`
* ∟`list[Field]`

Raises:
1. `Invalid`: `"no field %(field)s to give: the fields are %(fields)s", field=repr(unknown[0]), fields=", ".join(properties)`
2. `_Unparsed`: `"%(field)s isn't JSON: %(error)s", field=name, error=str(e)` (from `json.JSONDecodeError`, through `_read`)
3. `_Unparsed`: `"%(field)s isn't a whole number: %(given)s", field=f.name, given=repr(given)` (through `_read`)
4. `_Unparsed`: `"%(field)s isn't a number: %(given)s", field=f.name, given=repr(given)` (through `_read`)

## `halting` `@router.post("/runs/{run}/halt")`
`src/chatddx/portal/runs.py:halting`

* `bench: BenchDep`
* `run: UUID`
* ∟`Response`

## `Held`
`src/chatddx/portal/review.py:Held`

`type Held = tuple[schemas.Thread, Scorer, list[str]]`

## `holding`
`src/chatddx/portal/translations.py:holding`

* `bench: Bench`
* `versions: Collection[str]`
* ∟`list[tuple[schemas.Thread, Recipe]]`

## `home` `@router.get("/")`
`src/chatddx/portal/pages.py:home`

* `request: Request`
* `person: PersonDep`
* ∟`Response`

## `Island` `@dataclass(frozen=True)`
`src/chatddx/portal/assets.py:Island`

* `scripts: list[str]`
* `styles: list[str]`
* `preloads: list[str]`

## `kept`
`src/chatddx/portal/fields.py:kept`

* `found: list[Field]`
* `form: FormData`
* `e: ValueError | None`
* ∟`tuple[list[Field], list[str]]`

## `keyed`
`src/chatddx/portal/lab.py:keyed`

* `view: schemas.ComparedView`
* ∟`str`

## `lab` `@router.get("/lab/{thread}")`
`src/chatddx/portal/lab.py:lab`

* `request: Request`
* `bench: BenchDep`
* `thread: int`
* `handle: str | None = None`
* `family: Annotated[list[int] | None, Query()] = None`
* `by: str | None = None`
* ∟`Response`

Raises:
1. `RequestValidationError`: `errors` (through `_varying`)
2. `NotFound`: `"no configuration %(thread)s for %(login)s", thread=thread, login=bench.person.login`
3. `NotFound`: `"no trial %(thread)s for %(login)s", thread=thread, login=bench.person.login` (through `_trials`)

## `labs` `@router.get("/lab")`
`src/chatddx/portal/lab.py:labs`

* `request: Request`
* `bench: BenchDep`
* ∟`Response`

## `cases.leaving` `@router.post("/cases/{family}/leave")`
`src/chatddx/portal/cases.py:leaving`

* `bench: BenchDep`
* `family: int`
* ∟`Response`

## `threads.leaving` `@router.post("/threads/{thread}/leave")`
`src/chatddx/portal/threads.py:leaving`

* `bench: BenchDep`
* `thread: int`
* ∟`Response`

## `library` `@router.get("/library")`
`src/chatddx/portal/threads.py:library`

* `request: Request`
* `bench: BenchDep`
* `kind: str | None = None`
* `tag: Annotated[list[str] | None, Query()] = None`
* `q: str = ""`
* `pick: Literal["all"] | None = None`
* `schema: str | None = None`
* ∟`Response`

## `library_page`
`src/chatddx/portal/threads.py:library_page`

* `request: Request`
* `bench: Bench`
* `kind: str | None`
* `tag: list[str] | None`
* `typed: Typed | None = None`
* `q: str = ""`
* `pick: Literal["all"] | None = None`
* `schema: str | None = None`
* ∟`Response`

Raises:
1. `NotFound`: `"no kind %(kind)s: the kinds are %(kinds)s", kind=repr(kind), kinds=", ".join(words)`

## `linked`
`src/chatddx/portal/lab.py:linked`

* `query: schemas.Varying`
* `head: int`
* `latest: int`
* ∟`str`

## `listed`
`src/chatddx/portal/fields.py:listed`

* `bench: Bench`
* `word: str`
* `deleted: bool = False`
* ∟`list[tuple[schemas.Thread, Purpose | None]]`

## `MANIFEST`
`src/chatddx/portal/assets.py:MANIFEST`

`MANIFEST = Path(".vite") / "manifest.json"`

## `own_first`
`src/chatddx/portal/pages.py:own_first`

* `bench: Bench`
* `found: list[schemas.Thread]`
* ∟`list[schemas.Thread]`

## `page`
`src/chatddx/portal/pages.py:page`

* `request: Request`
* `name: str`
* `status: int = 200`
* `**context: Any`
* ∟`Response`

## `page_bench`
`src/chatddx/portal/pages.py:page_bench`

* `request: Request`
* `conn: ConnDep`
* `person: PersonDep`
* ∟`Bench`

## `paged`
`src/chatddx/portal/pages.py:paged`

* `answer: Callable[[Request, Any], Response | Awaitable[Response]]`
* ∟`Callable[[Request, Exception], Response]`

## `parsed`
`src/chatddx/portal/fields.py:parsed`

* `found: list[Field]`
* `form: FormData`
* ∟`dict[str, JsonValue]`

Raises:
1. `_Unparsed`: `"%(field)s isn't a whole number: %(given)s", field=f.name, given=repr(given)` (through `_number`)
2. `_Unparsed`: `"%(field)s isn't a number: %(given)s", field=f.name, given=repr(given)` (through `_number`)
3. `_Unparsed`: `"%(field)s isn't JSON: %(error)s", field=name, error=str(e)` (from `json.JSONDecodeError`, through `_json`)

## `pausing` `@router.post("/queue/pause")`
`src/chatddx/portal/runs.py:pausing`

* `bench: BenchDep`
* ∟`Response`

## `PersonDep`
`src/chatddx/portal/pages.py:PersonDep`

`type PersonDep = Annotated[Person, Depends(signed_in)]`

## `PLAN`
`src/chatddx/portal/runs.py:PLAN`

`PLAN = "management_plan_v1"`

## `posted`
`src/chatddx/portal/translations.py:posted`

* `form: FormData`
* ∟`dict[str, str]`

## `pressed` `@contextmanager`
`src/chatddx/portal/runs.py:pressed`

* ∟`Generator[None]`

## `purpose`
`src/chatddx/portal/fields.py:purpose`

* `model: type[BaseModel]`
* ∟`Purpose | None`

## `Read` `@dataclass(frozen=True)`
`src/chatddx/portal/scoring.py:Read`

* `by: AskedBy | None`
* `family: schemas.Family | None`
* `families: list[schemas.Family]`
* `data: JsonValue`
* `picked: list[JsonValue]`

## `refusable`
`src/chatddx/portal/pages.py:refusable`

* `e: ValueError`
* ∟`bool`

## `refusal_of`
`src/chatddx/portal/pages.py:refusal_of`

* `e: Exception`
* ∟`str`

## `replacing` `@router.post("/cases/{family}/replacement")`
`src/chatddx/portal/cases.py:replacing`

* `bench: BenchDep`
* `family: int`
* `case: Annotated[str, Form()]`
* `version: Annotated[int, Form()]`
* ∟`Response`

## `cases.restoring` `@router.post("/cases/{family}/restore")`
`src/chatddx/portal/cases.py:restoring`

* `bench: BenchDep`
* `family: int`
* ∟`Response`

## `threads.restoring` `@router.post("/threads/{thread}/restore")`
`src/chatddx/portal/threads.py:restoring`

* `bench: BenchDep`
* `thread: int`
* ∟`Response`

## `resuming` `@router.post("/runs/{run}/resume")`
`src/chatddx/portal/runs.py:resuming`

* `bench: BenchDep`
* `run: UUID`
* ∟`Response`

## `reverting` `@router.post("/threads/{thread}/revert")`
`src/chatddx/portal/threads.py:reverting`

* `bench: BenchDep`
* `thread: int`
* `head: Annotated[int, Form()]`
* `edit: Annotated[int, Form()]`
* ∟`Response`

Raises:
1. `Invalid`: `"edit %(edit)s isn't a version of thread %(thread)s", edit=edit, thread=thread`

## `review` `@router.get("/review/{family}")`
`src/chatddx/portal/review.py:review`

* `request: Request`
* `bench: BenchDep`
* `family: int`
* `case: str | None = None`
* `schema: str | None = None`
* `scorer: int | None = None`
* `tag: Tags = None`
* ∟`Response`

Raises:
1. `NotFound`: `"no case %(case)s of %(family)s", case=str(case), family=shown.name`
2. `NotFound`: `"no expectation schema %(schema)s for you", schema=schema`
3. `NotFound`: `"no scorer %(scorer)s reading that schema for you", scorer=scorer`

## `reviewing` `@router.get("/review")`
`src/chatddx/portal/review.py:reviewing`

* `request: Request`
* `bench: BenchDep`
* `tag: Tags = None`
* ∟`Response`

## `ROUTE`
`src/chatddx/portal/assets.py:ROUTE`

`ROUTE = "/static"`

## `cases.router`
`src/chatddx/portal/cases.py:router`

`router = APIRouter()`

## `lab.router`
`src/chatddx/portal/lab.py:router`

`router = APIRouter()`

## `pages.router`
`src/chatddx/portal/pages.py:router`

`router = APIRouter()`

## `review.router`
`src/chatddx/portal/review.py:router`

`router = APIRouter()`

## `runs.router`
`src/chatddx/portal/runs.py:router`

`router = APIRouter()`

## `scoring.router`
`src/chatddx/portal/scoring.py:router`

`router = APIRouter()`

## `threads.router`
`src/chatddx/portal/threads.py:router`

`router = APIRouter()`

## `world.router`
`src/chatddx/portal/world.py:router`

`router = APIRouter()`

## `run` `@router.get("/runs/{run}")`
`src/chatddx/portal/runs.py:run`

* `request: Request`
* `bench: BenchDep`
* `run: UUID`
* ∟`Response`

## `running_again` `@router.post("/runs/{run}/again")`
`src/chatddx/portal/runs.py:running_again`

* `bench: BenchDep`
* `run: UUID`
* ∟`Response`

## `running_in_review` `@router.post("/review/{family}/runs")`
`src/chatddx/portal/review.py:running_in_review`

* `bench: BenchDep`
* `family: int`
* `configuration: Annotated[int, Form()]`
* `case: Annotated[str, Form()]`
* `model: Annotated[str, Form()] = ""`
* `replicates: Annotated[int, Form(ge=1, le=settings.ITEMS_PER_RUN)] = 1`
* `score: Annotated[bool, Form()] = False`
* `back: Annotated[str | None, Form()] = None`
* ∟`Response`

Raises:
1. `Invalid`: `"no case %(case)s of family %(family)s", case=case, family=family`

## `runs` `@router.get("/runs")`
`src/chatddx/portal/runs.py:runs`

* `request: Request`
* `bench: BenchDep`
* `number: Annotated[int, Query(alias="page", ge=1)] = 1`
* `left: bool = False`
* ∟`Response`

## `cases.saying` `@router.post("/cases/{family}/said")`
`src/chatddx/portal/cases.py:saying`

* `bench: BenchDep`
* `family: int`
* `name: Annotated[str, Form()] = ""`
* `description: Annotated[str, Form()] = ""`
* `tags: Annotated[str, Form()] = ""`
* `shared: Annotated[str, Form()] = ""`
* `language: Annotated[str, Form()] = ""`
* ∟`Response`

## `threads.saying` `@router.post("/threads/{thread}/said")`
`src/chatddx/portal/threads.py:saying`

* `request: Request`
* `bench: BenchDep`
* `thread: int`
* `name: Annotated[str, Form()] = ""`
* `description: Annotated[str, Form()] = ""`
* `tags: Annotated[str, Form()] = ""`
* `shared: Annotated[str, Form()] = ""`
* ∟`Response`

Raises:
1. `NotFound`: `"no version %(at)s of %(kind)s %(thread)s: it has %(versions)s", at=at, kind=display_kind(word), thread=thread, versions=len(versions)` (through `_thread_page`)

## `scorer_choices`
`src/chatddx/portal/scoring.py:scorer_choices`

* `bench: Bench`
* `code: schemas.ScorerCode`
* `judged: Iterable[str] = ()`
* ∟`dict[str, Any]`

## `runs.scoring` `@router.post("/runs/{run}/scores")`
`src/chatddx/portal/runs.py:scoring`

* `bench: BenchDep`
* `run: UUID`
* ∟`Response`

## `scoring.scoring` `@router.get("/scoring/{thread}")`
`src/chatddx/portal/scoring.py:scoring`

* `request: Request`
* `bench: BenchDep`
* `thread: int`
* `view: str | None = None`
* `family: int | None = None`
* ∟`Response`

Raises:
1. `NotFound`: `"no scorer or judge %(thread)s for %(login)s", thread=thread, login=bench.person.login`
2. `NotFound`: `"no view %(view)s asks this judge", view=view` (through `_judge`)

## `scoring_in_review` `@router.post("/review/{family}/scores")`
`src/chatddx/portal/review.py:scoring_in_review`

* `bench: BenchDep`
* `family: int`
* `run: Annotated[list[UUID], Form()]`
* `scorer: Annotated[str, Form()]`
* `back: Annotated[str | None, Form()] = None`
* ∟`Response`

## `scorings` `@router.get("/scoring")`
`src/chatddx/portal/scoring.py:scorings`

* `request: Request`
* `bench: BenchDep`
* ∟`Response`

## `Served` `@dataclass(frozen=True)`
`src/chatddx/portal/world.py:Served`

* `endpoint: schemas.Endpoint`
* `spec: EndpointSpec`
* `engine: int | None`
* `canaries: str | None`

## `Shape`
`src/chatddx/portal/fields.py:Shape`

`Shape`

## `Shelf` `@dataclass(frozen=True)`
`src/chatddx/portal/shelves.py:Shelf`

* `heading: str`
* `about: str`
* `kinds: dict[str, str]`

## `Shelved` `@dataclass(frozen=True)`
`src/chatddx/portal/shelves.py:Shelved`

* `word: str`
* `about: str`
* `mine: int`
* `seen: int`
* `written: bool`

## `shelved`
`src/chatddx/portal/shelves.py:shelved`

* `bench: Bench`
* `written: list[str]`
* ∟`list[tuple[Shelf, list[Shelved]]]`

## `Shelved.display_kind` `@property`
`src/chatddx/portal/shelves.py:Shelved.display_kind`

* ∟`str`

## `SHELVES`
`src/chatddx/portal/shelves.py:SHELVES`

`SHELVES = (…)`

## `runs.SHOWN`
`src/chatddx/portal/runs.py:SHOWN`

`SHOWN = 50`

## `scoring.SHOWN`
`src/chatddx/portal/scoring.py:SHOWN`

`SHOWN = 50`

## `signed_in`
`src/chatddx/portal/pages.py:signed_in`

* `request: Request`
* `conn: ConnDep`
* ∟`Person`

Raises:
1. `SignInFirst`: `request`

## `SignInFirst` `(Exception)`
`src/chatddx/portal/pages.py:SignInFirst`

* `next: str`

## `SignInFirst.__init__`
`src/chatddx/portal/pages.py:SignInFirst.__init__`

* `request: Request`

## `signing_in` `@router.post("/sign-in")`
`src/chatddx/portal/pages.py:signing_in`

* `request: Request`
* `conn: ConnDep`
* `login: Annotated[str, Form()]`
* `password: Annotated[str, Form()]`
* `next: Annotated[str, Form()] = "/"`
* ∟`Response`

## `signing_in_page` `@router.get("/sign-in")`
`src/chatddx/portal/pages.py:signing_in_page`

* `request: Request`
* `conn: ConnDep`
* `next: str = "/"`
* ∟`Response`

## `signing_out` `@router.post("/sign-out")`
`src/chatddx/portal/pages.py:signing_out`

* `request: Request`
* `conn: ConnDep`
* ∟`Response`

## `starting` `@router.post("/lab/run")`
`src/chatddx/portal/lab.py:starting`

* `bench: BenchDep`
* `version: Annotated[list[str] | None, Form()] = None`
* `concurrency: Annotated[str, Form()] = ""`
* `order: Annotated[str, Form()] = ""`
* `score: Annotated[bool, Form()] = False`
* ∟`Response`

Raises:
1. `Invalid`: `"no order %(order)s: the orders are %(orders)s", order=repr(order), orders=", ".join(get_args(Order))`
2. `Invalid`: `"pick a trial to run"`

## `stopping` `@router.post("/queue/stop")`
`src/chatddx/portal/runs.py:stopping`

* `bench: BenchDep`
* `now: Annotated[bool, Form()] = False`
* ∟`Response`

## `STYLES`
`src/chatddx/portal/assets.py:STYLES`

`STYLES = "src/portal.css"`

## `Tags`
`src/chatddx/portal/review.py:Tags`

`type Tags = Annotated[list[str] | None, Query()]`

## `cases.taking` `@router.post("/library/takes")`
`src/chatddx/portal/cases.py:taking`

* `request: Request`
* `bench: BenchDep`
* `expectation_schema: Annotated[str, Form()]`
* `families: Annotated[list[int] | None, Form(alias="family")] = None`
* `owner: Annotated[str, Form()] = ""`
* `tag: Annotated[list[str] | None, Form()] = None`
* ∟`Response`

Raises:
1. `NotFound`: `"no case %(case)s for %(login)s", case=missing[0], login=bench.person.login`

## `threads.taking` `@router.post("/threads/{thread}/take")`
`src/chatddx/portal/threads.py:taking`

* `bench: BenchDep`
* `thread: int`
* `next: Annotated[str | None, Form()] = None`
* ∟`Response`

## `templates`
`src/chatddx/portal/pages.py:templates`

`templates = Jinja2Templates(directory=Path(__file__).parent / "templates")`

## `thread_page` `@router.get("/threads/{thread}")`
`src/chatddx/portal/threads.py:thread_page`

* `request: Request`
* `bench: BenchDep`
* `thread: int`
* `version: int | None = None`
* `into: str | None = None`
* ∟`Response`

Raises:
1. `NotFound`: `"no version %(at)s of %(kind)s %(thread)s: it has %(versions)s", at=at, kind=display_kind(word), thread=thread, versions=len(versions)` (through `_thread_page`)

## `to_sign_in`
`src/chatddx/portal/pages.py:to_sign_in`

* `_: Request`
* `e: Exception`
* ∟`Response`

## `Translating` `@dataclass(frozen=True)`
`src/chatddx/portal/translations.py:Translating`

* `into: str | None`
* `languages: list[str]`
* `cased: list[str]`
* `entries: list[Entry]`
* `configurations: list[tuple[schemas.Thread, str | None]]`

## `translating`
`src/chatddx/portal/translations.py:translating`

* `bench: Bench`
* `held: Translations`
* `versions: list[str]`
* `into: str | None`
* ∟`Translating`

## `Typed` `@dataclass(frozen=True)`
`src/chatddx/portal/threads.py:Typed`

* `refused: list[str]`
* `name: str | None = None`
* `language: str | None = None`
* `labels: str | None = None`
* `about: dict[str, str] | None = None`
* `kept: bool = True`
* `unnamed: bool = False`

## `unit_in`
`src/chatddx/portal/scoring.py:unit_in`

* `bench: Bench`
* `scorer: str`
* `view: int`
* ∟`str`

## `unpausing` `@router.post("/queue/resume")`
`src/chatddx/portal/runs.py:unpausing`

* `bench: BenchDep`
* ∟`Response`

## `unshipped`
`src/chatddx/portal/scoring.py:unshipped`

* `scorer: Scorer`
* ∟`str | None`

## `updating` `@router.post("/threads/{thread}/update")`
`src/chatddx/portal/threads.py:updating`

* `bench: BenchDep`
* `thread: int`
* `head: Annotated[int, Form()]`
* `next: Annotated[str | None, Form()] = None`
* ∟`Response`

## `updating_all` `@router.post("/library/update")`
`src/chatddx/portal/threads.py:updating_all`

* `request: Request`
* `bench: BenchDep`
* ∟`Response`

## `viewed`
`src/chatddx/portal/lab.py:viewed`

* `views: list[schemas.ComparedView]`
* `by: str | None`
* ∟`str | None`

## `vignette` `@router.get("/cases/{family}/vignette")`
`src/chatddx/portal/cases.py:vignette`

* `request: Request`
* `bench: BenchDep`
* `family: int`
* ∟`Response`

## `visible`
`src/chatddx/portal/translations.py:visible`

* `text: str`
* ∟`str`

## `within`
`src/chatddx/portal/pages.py:within`

* `next: str | None`
* ∟`str`

## `world` `@router.get("/world")`
`src/chatddx/portal/world.py:world`

* `request: Request`
* `bench: BenchDep`
* ∟`Response`

## `writing` `@router.post("/library/new")`
`src/chatddx/portal/threads.py:writing`

* `request: Request`
* `bench: BenchDep`
* `kind: str`
* `form: FormDep`
* `configuration: int | None = None`
* `into: str | None = None`
* ∟`Response`

Raises:
1. `NotFound`: `"no %(kind)s is begun here: what is begun here is %(kinds)s", kind=kind, kinds=", ".join(_BEGUN)` (through `_begun`)
2. `Refusing`: `422, e` (from `NotFound`, through `_beginning_translations`)
3. `Invalid`: `"labels: %(refused)s", refused=e.errors()[0]["msg"]` (from `ValidationError`, through `_labels`)

## `written`
`src/chatddx/portal/translations.py:written`

* `held: Translations | None`
* `into: str`
* `entries: dict[str, str]`
* ∟`Translations`

Raises:
1. `ValueError`: `tr("translations hold a language or more: translate a text, or delete them")`
2. `ValueError`: `e.errors()[0]["msg"].removeprefix("Value error, ")` (from `ValidationError`)

## `written_for`
`src/chatddx/portal/cases.py:written_for`

* `bench: Bench`
* `family: int`
* ∟`list[schemas.Thread]`

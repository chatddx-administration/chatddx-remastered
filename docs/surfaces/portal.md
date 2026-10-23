# `chatddx.portal`

Written by `chatddx stamp write` from `src/chatddx/portal/`; how to read it is in [docs/surfaces.md](../surfaces.md).

## `ANSWERS`
`src/chatddx/portal/review.py:ANSWERS`

`ANSWERS = 50`

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
1. `HTTPException`: `422, "an appendix is named"`
2. `HTTPException`: `422, "an appendix holds a text"`

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

## `Asks` `@dataclass(frozen=True)`
`src/chatddx/portal/scoring.py:Asks`

* `thread: int | None`
* `name: str`
* `latest: bool`

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

## `AUTHORED`
`src/chatddx/portal/threads.py:AUTHORED`

`AUTHORED = WRITTEN | {"skeleton"}`

## `lab.beginning` `@router.get("/lab/run")`
`src/chatddx/portal/lab.py:beginning`

* `request: Request`
* `bench: BenchDep`
* `trial: Annotated[list[int] | None, Query()] = None`
* ∟`Response`

Raises:
1. `HTTPException`: `404, "no trial {thread} for {bench.person.login}"` (through `_starting`)

## `threads.beginning` `@router.get("/library/new")`
`src/chatddx/portal/threads.py:beginning`

* `request: Request`
* `bench: BenchDep`
* `kind: str`
* `configuration: int | None = None`
* `into: str | None = None`
* ∟`Response`

Raises:
1. `HTTPException`: `404, "no {kind} is begun here: what is begun here is {', '.join(BEGUN)}"` (through `_begun`)

## `BEGUN`
`src/chatddx/portal/threads.py:BEGUN`

`BEGUN = [w for w in KINDS if set(KINDS[w]) & AUTHORED]`

## `begun`
`src/chatddx/portal/translations.py:begun`

* `bench: Bench`
* `configuration: int`
* `into: str`
* ∟`list[Entry]`

Raises:
1. `ValueError`: `"{shown.name or shown.title} has no recipe whose texts to translate"`

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

* `bench: BenchDep`
* `family: int`
* `appendices: Annotated[list[str] | None, Form(alias="f.appendices")] = None`
* `back: Annotated[str | None, Form()] = None`
* ∟`Response`

## `built`
`src/chatddx/portal/cases.py:built`

* `bench: Bench`
* `family: int`
* `appendices: list[str] | None`
* ∟`str`

Raises:
1. `HTTPException`: `422, "a case is built of one appendix or more"`

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
1. `HTTPException`: `404, "no version {at} of case {family}: it has {len(bindings)}"`

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

## `closest`
`src/chatddx/portal/translations.py:closest`

* `text: str`
* `unused: Mapping[str, str]`
* ∟`tuple[str, str] | None`

## `code_of`
`src/chatddx/portal/scoring.py:code_of`

* `bench: Bench`
* `entry_point: str | None = None`
* ∟`schemas.ScorerCode`

## `Column` `@dataclass`
`src/chatddx/portal/lab.py:Column`

* `skeletons: tuple[str, ...]`
* `handle: str | None`
* `said: str | None = None`
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
1. `HTTPException`: `422, "pick the runs to compare on the runs page"`

## `Covered` `@dataclass(frozen=True)`
`src/chatddx/portal/scoring.py:Covered`

* `expected: int`
* `choosing: list[schemas.Family]`
* `lacking: list[schemas.Family]`

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

## `Disagreed` `@dataclass(frozen=True)`
`src/chatddx/portal/scoring.py:Disagreed`

* `run: UUID`
* `described: str`
* `case: str`
* `replicate: int`
* `label: str`
* `seeds: list[float | None]`

## `Earlier` `@dataclass(frozen=True)`
`src/chatddx/portal/cases.py:Earlier`

* `case: str`
* `title: str`
* `appendices: list[str]`
* `replacement: str`
* `stored: bool`

## `edges`
`src/chatddx/portal/translations.py:edges`

* `text: str`
* ∟`tuple[str, str]`

## `editing` `@router.post("/threads/{thread}/edit")`
`src/chatddx/portal/threads.py:editing`

* `bench: BenchDep`
* `thread: int`
* `form: FormDep`
* ∟`Response`

Raises:
1. `ValueError`: `"configuration {thread} is written by hand: it has no recipe to pick parts of"`

## `ENGINES`
`src/chatddx/portal/fields.py:ENGINES`

`ENGINES = frozenset({"engine.local", "engine.remote"})`

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

## `FARING`
`src/chatddx/portal/lab.py:FARING`

`FARING = ("handle", "family", "by")`

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
1. `HTTPException`: `404, "no judge {thread} for {bench.person.login}"`
2. `MovedOn`: `"scorer {scorer} has a newer version: look at it again"`

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
1. `HTTPException`: `422, "a fork is named"`

## `FormDep`
`src/chatddx/portal/threads.py:FormDep`

`FormDep = Annotated[FormData, Depends(_form)]`

## `fresh`
`src/chatddx/portal/fields.py:fresh`

* `model: type[BaseModel]`
* `given: Mapping[str, str] | None = None`
* ∟`list[Field]`

Raises:
1. `ValueError`: `"no field {unknown[0]!r} to give: the fields are {', '.join(properties)}"`
2. `ValueError`: `"{name} isn't JSON: {e}"` (from `json.JSONDecodeError`, through `_read`)
3. `ValueError`: `"{f.name} isn't {what}: {given!r}"` (through `_read`)

## `Given`
`src/chatddx/portal/review.py:Given`

`type Given = str | int | list[str] | None`

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

## `judge_choices`
`src/chatddx/portal/scoring.py:judge_choices`

* `bench: Bench`
* ∟`dict[str, list[dict[str, Any]]]`

## `Judged` `@dataclass`
`src/chatddx/portal/scoring.py:Judged`

* `scorer: str`
* `label: str`
* `items: int = 0`
* `agree: int = 0`
* `short: int = 0`
* `values: list[float] = field(default_factory=list[float])`

## `Judged.mean` `@property`
`src/chatddx/portal/scoring.py:Judged.mean`

* ∟`float | None`

## `JudgeShown` `@dataclass(frozen=True)`
`src/chatddx/portal/scoring.py:JudgeShown`

* `configuration: Asks`
* `model: str`
* `seeds: list[int]`
* `fill: str`
* `sent: str | None`
* `unsent: str | None`
* `asked_by: list[AskedBy]`
* `behind: list[tuple[schemas.Thread, list[str]]]`
* `read: Read`
* `asked: dict[str, JsonValue]`
* `judged: list[Judged]`
* `disagreed: list[Disagreed]`
* `editing: dict[str, Any]`

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
2. `HTTPException`: `404, "no configuration {thread} for {bench.person.login}"`
3. `HTTPException`: `404, "no trial {thread} for {bench.person.login}"` (through `_trials`)

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
* `kind: str = "instructions"`
* `tag: Annotated[list[str] | None, Query()] = None`
* ∟`Response`

Raises:
1. `HTTPException`: `404, "no kind {kind!r}: the kinds are {', '.join(words)}"`

## `linked`
`src/chatddx/portal/lab.py:linked`

* `query: schemas.Varying`
* `head: int`
* `latest: int`
* ∟`str`

## `LISTED`
`src/chatddx/portal/fields.py:LISTED`

`LISTED = frozenset({"string", "integer"})`

## `listed`
`src/chatddx/portal/fields.py:listed`

* `bench: Bench`
* `word: str`
* `deleted: bool = False`
* ∟`list[tuple[schemas.Thread, Purpose | None]]`

## `MANIFEST`
`src/chatddx/portal/assets.py:MANIFEST`

`MANIFEST = Path(".vite") / "manifest.json"`

## `NEAR`
`src/chatddx/portal/translations.py:NEAR`

`NEAR = 0.5`

## `OPEN`
`src/chatddx/portal/review.py:OPEN`

`OPEN = ("queued", "under way")`

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
1. `ValueError`: `"{f.name} isn't {what}: {given!r}"` (through `_number`)
2. `ValueError`: `"{name} isn't JSON: {e}"` (from `json.JSONDecodeError`, through `_json`)

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
1. `HTTPException`: `422, "edit {edit} isn't a version of thread {thread}"`

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
1. `HTTPException`: `404, "no case {case} of {shown.name}"`
2. `HTTPException`: `404, "no expectation schema {schema} for you"`
3. `HTTPException`: `404, "no scorer {scorer} reading that schema for you"`

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
1. `HTTPException`: `422, "no case {case} of family {family}"`

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

* `bench: BenchDep`
* `thread: int`
* `name: Annotated[str, Form()] = ""`
* `description: Annotated[str, Form()] = ""`
* `tags: Annotated[str, Form()] = ""`
* `shared: Annotated[str, Form()] = ""`
* ∟`Response`

## `scorer_choices`
`src/chatddx/portal/scoring.py:scorer_choices`

* `bench: Bench`
* `code: schemas.ScorerCode`
* `judged: Iterable[str] = ()`
* ∟`dict[str, Any]`

## `ScorerShown` `@dataclass(frozen=True)`
`src/chatddx/portal/scoring.py:ScorerShown`

* `schema: str`
* `entry_point: str`
* `version: int`
* `unshipped: str | None`
* `views: list[Viewed]`
* `resources: list[str]`
* `params: dict[str, JsonValue]`
* `reads: list[schemas.Thread]`
* `skips: list[schemas.Thread]`
* `covered: Covered`
* `fared: list[Fared]`

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
1. `HTTPException`: `404, "no scorer or judge {thread} for {bench.person.login}"`
2. `HTTPException`: `404, "no view {view} asks this judge"` (through `_judge`)

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

## `Sourced` `@dataclass(frozen=True)`
`src/chatddx/portal/world.py:Sourced`

* `source: Source`
* `vignettes: int | None`
* `unread: str | None`
* `cleared: list[str]`

## `Starting` `@dataclass(frozen=True)`
`src/chatddx/portal/lab.py:Starting`

* `thread: schemas.Thread`
* `versions: list[schemas.Edit]`
* `trial: Trial`
* `endpoint: Endpoint | None`
* `refused: str | None`

## `starting` `@router.post("/lab/run")`
`src/chatddx/portal/lab.py:starting`

* `bench: BenchDep`
* `version: Annotated[list[str] | None, Form()] = None`
* `concurrency: Annotated[str, Form()] = ""`
* `order: Annotated[str, Form()] = ""`
* `score: Annotated[bool, Form()] = False`
* ∟`Response`

Raises:
1. `ValueError`: `"no order {order!r}: the orders are {', '.join(get_args(Order))}"`
2. `ValueError`: `"pick a trial to run"`

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
1. `HTTPException`: `422, "pick one case or more to take for"`
2. `HTTPException`: `404, "no case {missing[0]} for {bench.person.login}"`

## `threads.taking` `@router.post("/threads/{thread}/take")`
`src/chatddx/portal/threads.py:taking`

* `bench: BenchDep`
* `thread: int`
* `next: Annotated[str | None, Form()] = None`
* ∟`Response`

## `TALLIED`
`src/chatddx/portal/runs.py:TALLIED`

`TALLIED: tuple[Outcome, ...] = (…)`

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
1. `HTTPException`: `404, "no version {at} of {word} {thread}: it has {len(versions)}"`

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

## `Viewed` `@dataclass(frozen=True)`
`src/chatddx/portal/scoring.py:Viewed`

* `label: str`
* `metric: str`
* `measures: str | None`
* `unit: str | None`
* `output: str`
* `split: str | None`
* `expectation: str`
* `params: dict[str, JsonValue]`
* `judge: Asks | None`

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
* `into: str | None = None`
* ∟`Response`

Raises:
1. `HTTPException`: `404, "no {kind} is begun here: what is begun here is {', '.join(BEGUN)}"` (through `_begun`)
2. `ValueError`: `"a new {kind.replace('_', ' ')} is named"`

## `written`
`src/chatddx/portal/translations.py:written`

* `held: Translations | None`
* `into: str`
* `entries: dict[str, str]`
* ∟`Translations`

Raises:
1. `ValueError`: `"translations hold a language or more: translate a text, or delete them"`
2. `ValueError`: `e.errors()[0]["msg"].removeprefix("Value error, ")` (from `ValidationError`)

## `written_for`
`src/chatddx/portal/cases.py:written_for`

* `bench: Bench`
* `family: int`
* ∟`list[schemas.Thread]`

# `chatddx.curation`

Written by `chatddx stamp` from `src/chatddx/curation/`; how to read it is in [docs/reference/README.md](README.md).

## `ARCHIVE`
`src/chatddx/curation/write.py:ARCHIVE`

`ARCHIVE = "archive"`

## `DATA_TABLES`
`src/chatddx/curation/plan.py:DATA_TABLES`

`DATA_TABLES = tuple(t for t in PLANNED_TABLES if t not in ENGINE_TABLES)`

## `DataCase` `@dataclass(frozen=True)`
`src/chatddx/curation/plan.py:DataCase`

* `tags: tuple[str, ...]`
* `language: str`
* `targets: JsonValue`
* `appendices: Mapping[str, str] = field(default_factory=dict[str, str])`
* `ordered: tuple[Ordered, ...] = ()`

## `ENGINE_TABLES`
`src/chatddx/curation/plan.py:ENGINE_TABLES`

`ENGINE_TABLES = ("local_model", "remote_model", "local_engine", "remote_engine")`

## `init`
`src/chatddx/curation/write.py:init`

* `conn: Connection`
* `plan: Plan`
* `cases: dict[str, DataCase]`
* `source: DirectorySource`
* `user: Person`
* `giftbag: bool = False`
* ∟`list[str]`

Raises:
1. `ValueError`: `"a data set needs exactly one expectation schema"`

## `LATE_TABLES`
`src/chatddx/curation/plan.py:LATE_TABLES`

`LATE_TABLES = ("scorer",)`

## `load_cases`
`src/chatddx/curation/plan.py:load_cases`

* `data: Path`
* ∟`dict[str, DataCase]`

Raises:
1. `ValueError`: `"{path}: cases are kept in cases-<language>.toml files"`
2. `ValueError`: `"{path}: {e}"` (from `ValueError`)
3. `ValueError`: `"{path}: a cases file has only 'case' tables"`
4. `ValueError`: `"{path}: case.{id} is in {where[id].name} too"`
5. `ValueError`: `"{path}: case.{id}: unknown keys {sorted(stray)}"`
6. `ValueError`: `"{where}: appendices are a table of texts by name"` (through `_appendices`)
7. `ValueError`: `"{where}: appendices {bad} aren't texts"` (through `_appendices`)
8. `ValueError`: `"{where}: a case with appendices is a table"` (through `_ordered`)
9. `ValueError`: `"{where}: unknown keys {sorted(stray)}"` (through `_ordered`)
10. `ValueError`: `"{where}: name its appendices, in order"` (through `_ordered`)
11. `ValueError`: `"{where}: no appendices {unknown}"` (through `_ordered`)
12. `ValueError`: `"{where}: an appendix is named twice"` (through `_ordered`)
13. `ValueError`: `"{path}: case.{id}: a case with appendices is twice"`

## `Ordered` `@dataclass(frozen=True)`
`src/chatddx/curation/plan.py:Ordered`

* `appendices: tuple[str, ...]`
* `targets: JsonValue = None`

## `Plan` `@dataclass`
`src/chatddx/curation/plan.py:Plan`

* `registry: Registry`
* `facts: Facts`
* `stanzas: list[Planned] = field(default_factory=list)`
* `skipped: list[str] = field(default_factory=list)`
* `untranslated: list[str] = field(default_factory=list)`
* `compilations: list[str] = field(default_factory=list)`
* `engines: dict[str, str] = field(default_factory=dict)`

## `Plan.named`
`src/chatddx/curation/plan.py:Plan.named`

* `table: str`
* `name: str`
* ∟`Planned`

Raises:
1. `LookupError`: `"no {table} named {name!r} in the plan"`

## `plan_factors`
`src/chatddx/curation/plan.py:plan_factors`

* `data: Path`
* `facts: Facts`
* `compiler: Code`
* `world: World | None = None`
* ∟`Plan`

Raises:
1. `ValueError`: `"{factors}: {', '.join(held)} tables are the World's, in its engines.toml"`
2. `ValueError`: `"{path}: unknown tables {sorted(stray)}"` (through `_stanzas`)
3. `ValueError`: `"{path}: {table}.{name}: {said}"` (through `_stanzas`)
4. `ValueError`: `"{path}: an engines file holds only {', '.join(ENGINE_TABLES)} tables, not {', '.join(stray)}"`
5. `ValueError`: `"{path}: {table} {twice} are named before it too"`
6. `ValueError`: `"{factors}: translations are written in the texts-<language>.toml of the language they translate into"`
7. `ValueError`: `"{path}: texts are kept in texts-<language>.toml files"` (through `_texts`)
8. `ValueError`: `"{path}: {e}"` (from `ValueError`, through `_texts`)
9. `ValueError`: `"{table}.{name} is in {where} and texts-{language}.toml: a text is written in one language, and translated into others"`
10. `ValueError`: `"tags must be a list of strings, not {value!r}"` (through `_tags`)
11. `ValueError`: `"recipe.{name}: a recipe's model is the World's: its inventory names the handle configurations are made for"`
12. `ValueError`: `"recipe.{name}: no {part} named {body[part]!r}"`
13. `ValueError`: `"judge.{name}: a judge's model is the World's, which binds the judge to a handle in its inventory's [judge] table"`
14. `ValueError`: `"judge.{name}: no recipe named {recipe!r}"`
15. `ValueError`: `"judge.{name}: {e}"` (from `ValidationError`)
16. `ValueError`: `"judge.{name}: {'; '.join(refused)}"`

## `Planned` `@dataclass(frozen=True)`
`src/chatddx/curation/plan.py:Planned`

* `table: str`
* `name: str`
* `kind: str`
* `digest: str`
* `tags: tuple[str, ...] = ()`
* `description: str | None = None`
* `fork_of: str | None = None`
* `compilation: str | None = None`
* `labels: tuple[str | None, ...] = ()`
* `language: str | None = None`

## `PLANNED_TABLES`
`src/chatddx/curation/plan.py:PLANNED_TABLES`

`PLANNED_TABLES = (*TABLES, "recipe", "judge")`

## `REFERENCES`
`src/chatddx/curation/plan.py:REFERENCES`

`REFERENCES: dict[str, dict[str, str]] = {…}`

## `repair`
`src/chatddx/curation/repair.py:repair`

* `conn: Connection`
* `source: DirectorySource`
* `archive: Person`
* `dry: bool = False`
* ∟`list[str]`

## `SHIPPED`
`src/chatddx/curation/plan.py:SHIPPED`

`SHIPPED: dict[str, Mapping[str, Versioned]] = {"tool": TOOLS, "scorer": SCORERS}`

## `short`
`src/chatddx/curation/write.py:short`

* `digest: str`
* ∟`str`

## `TABLES`
`src/chatddx/curation/plan.py:TABLES`

`TABLES: dict[str, type[Component]] = {…}`

## `TEXT_TABLES`
`src/chatddx/curation/plan.py:TEXT_TABLES`

`TEXT_TABLES = frozenset(…)`

## `VERBS`
`src/chatddx/curation/write.py:VERBS`

`VERBS: dict[Kept, str] = {…}`

## `wipe`
`src/chatddx/curation/write.py:wipe`

* `conn: Connection`
* `user: Person`
* ∟`list[str]`

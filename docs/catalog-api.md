# Catalog API

```
AGENT: CHANGE
a3e5050 is on no commit of main, only on the leftover branch claude/fervent-galileo-ckxp3j, and goes when that branch
is deleted. fb6489d, which squashed it into main, has the same src/. Two later changes, 0013 (1dd791a) and threads.py's
import of factors.kinds (657716a), have their own suggestions below.
---
as of fb6489d
```
Reference for the `chatddx.catalog` package and the `catalog` database schema, as of a3e5050. It was written from
`src/chatddx/catalog/*`, `docs/catalog.md` and `src/chatddx/store/migrations/001{0,1,2}-*-catalog.sql`;
`src/chatddx/store/catalog.py` was read only to map the store's `Catalog` onto this package. What the catalog is and
why it is shaped this way is in `docs/catalog.md`; this file says what each name accepts, returns and raises. Factor
types it uses (`Component`, `Fingerprint`, `Vignette`, `Recipe`, `Compilation`, `Registry`, `resolve`, …) are in
`docs/factors-api.md`.

Paths are relative to `src/chatddx/catalog/` unless they start with `src/` or `docs/`.

## Contents
- [Package](#package)
- [Conventions](#conventions)
- [model.py](#modelpy): kinds, language tags, rows, entries, `About`, `latest`, results
- [read.py](#readpy): `Reader` and the helpers that pick the latest
- [threads.py](#threadspy): threads, edits, heads, visibility, forks, variations, proposals, `behind`
- [families.py](#familiespy): bindings, `family_of`, adopting, surveying, repairing, stale cases
- [language.py](#languagepy): a component's language, and the checks on writing one
- [titles.py](#titlespy): descriptions and titles
- [variants.py](#variantspy): the names of what's made for a language or a model
- [The store's Catalog](#the-stores-catalog)
- [Database: schema `catalog`](#database-schema-catalog)
- [Known gaps](#known-gaps)
- [Beyond docs/catalog.md](#beyond-docscatalogmd)

## Package

`chatddx.catalog` re-exports `LANGUAGE`, `LANGUAGE_KINDS`, `THREAD_KINDS`, `About`, `Behind`, `Binding`, `Edit`,
`Entry`, `EntryField`, `Kept`, `Part`, `Reader`, `Repair`, `RepairPlan`, `Subject`, `Survey`, `Thread`, `Variation`,
`check_label`, `language_tag`, `latest`, `made_for`, `variant_name`, `variants_for`, and the modules `families`,
`language`, `read`, `threads`, `titles` and `variants`.
Functions are called through their module (`threads.behind(rows, thread)`); `model.py` is imported by path.

```
AGENT: CHANGE
threads.py imports parse_component from chatddx.factors.kinds since 657716a (src/chatddx/catalog/threads.py:4).
---
| `threads.py` | `families.py`, `model.py`, `read.py`, `chatddx.factors.{base,kinds,request,scoring}` |
```
| Module | Builds on |
| --- | --- |
| `model.py` | `chatddx.factors.{base,cases,scoring}`, `chatddx.identity` |
| `read.py` | `model.py`, `chatddx.factors.{base,cases,request}` |
| `families.py` | `model.py`, `read.py`, `chatddx.factors.{base,bundle,cases,scoring}` |
| `threads.py` | `families.py`, `model.py`, `read.py`, `chatddx.factors.{base,request,scoring}` |
| `language.py` | `families.py`, `model.py`, `read.py`, `chatddx.factors.{base,request,scoring,trial}` |
| `titles.py` | `families.py`, `language.py`, `model.py`, `read.py`, `threads.py`, `chatddx.factors.{base,cases,engine,request,scoring,trial}` |
| `variants.py` | `model.py` |

The package imports no chatddx package but `chatddx.factors` and `chatddx.identity`, no third-party package but
pydantic, and holds no SQL. It reads through a `Reader` and writes nothing; `src/chatddx/store/catalog.py:Catalog`
writes what it decides (see "The store's Catalog").

## Conventions

**Models.** Every model derives from `model.py:_Frozen`, a pydantic model with `frozen=True, extra="forbid"` (not
`chatddx.factors.base.Frozen`). Building one validates it. A model whose fields are all hashable is hashable, so
`Subject` serves as a dict key. `RepairPlan` is a frozen dataclass whose fields are plain dicts and lists.

**Rows and ids.** Threads, edits, families and bindings have `int` ids that the database assigns in insertion order
(`GENERATED ALWAYS AS IDENTITY`). People are `int` ids of `identity.person` (`docs/identity.md`). Runs and scores are
`UUID`s. Components are referred to by digest, typed as plain `str`. `at` is a `datetime` the database sets
(`DEFAULT now()`); nothing in the package reads it.

**Latest wins.** A `Reader` returns rows in the order they were written; nothing in it picks the latest. The
package takes the last row for a key as the one that holds: through `model.py:latest` and `About.of`, and by taking
`[-1]` of a list in `threads.head`, `threads.variation`, `families.family_of`, `families.plan_repair`,
`families.stale_cases` and `titles._case_title`.

**Errors.**

| Exception | When |
| --- | --- |
| `LookupError` | A thread, edit or family that doesn't exist (`no thread with id <id>`, `no edit with id <id>`, `no family with id <id>`); a digest that isn't stored where one is required (`check_adoptable`, `check_language`); `expectation_for` with several expectations to choose from. |
| `ValueError` | A rule refused before writing: `check_threadable`, `check_based_on`, `check_adoptable`, `plan_repair`, `check_language`, `check_entry`, `check_label`, `language_tag`. |
| `pydantic.ValidationError` | A model breaks its own rules: an `Entry` of the wrong shape, a `Subject` that isn't exactly one thing, a `Behind` with both or neither of `head` and `binding`; `proposal` when the merged recipe isn't a valid `Recipe`. Rules written as validators raise `ValueError`, which pydantic wraps. |
| `chatddx.factors.base.StructuralError` (a `ValueError`) | `Reader.get` of a digest that isn't stored (both `Rows` and `test/memory.py:Memory`, through `Store.get` and `Registry.get`); `resolve` of a component of the wrong kind; `proposal` when the merged document isn't a readable component. |

**Deleted subjects.** A subject is deleted when its `About.deleted` is true. What each function does with deleted
threads and families is said in its entry; in short:

| Deleted are | Functions |
| --- | --- |
| skipped, through `About.shows` | `threads.visible`, `families.visible`, `threads.expectation_for` |
| skipped, through `About.deleted` | `threads.heads` (unless `deleted=True`, which returns only them), `threads.find`, `threads.behind` (no deleted thread's head, and no case of a deleted family) |
| ranked last | `titles.title_of` |
| included | `threads.history`, `threads.forks`, `threads.expectations_of`, `families.family_of`, `families.bindings`, `families.survey`, `families.plan_repair`, `language.language_of`, the titles of cases, `Catalog.containing` |

## model.py

### Names and constants

| Name | Value |
| --- | --- |
| `THREAD_KINDS` | `frozenset` of the 22 kinds that have threads: `chunk.instructions`, `chunk.few_shot`, `chunk.prompt`, `chunk.output`, `chunk.sampling`, `chunk.reasoning`, `chunk.passthrough`, `chunk.translations`, `chunk.toolset`, `tool`, `skeleton`, `trial`, `judge`, `scorer`, `scoring`, `appendix`, `expectation`, `model`, `engine.local`, `engine.remote`, `expectation_schema`, `canary_set`. Every component kind but `case` and `compilation`. Repeated in `0012` (`thread_kind_check`). |
| `LANGUAGE_KINDS` | `frozenset` of the 7 kinds that can have a language of their own: `chunk.instructions`, `chunk.few_shot`, `chunk.prompt`, `chunk.output`, `chunk.toolset`, `chunk.translations`, `skeleton`. Repeated in `0012` (`language_kind_check`). |
| `LANGUAGE` | `re.compile(r"^[a-z]{2,3}(-[A-Za-z0-9]{1,8})*$")`. Accepts `sv`, `pt-BR`, `zh-Hant-TW`; refuses `SV`, `en_US`. Repeated in `0012`. |
| `Part` | `Literal["view", "resource"]` |
| `Kept` | `Literal["created", "edited", "unchanged"]`: what `Catalog.keep` did |

### `language_tag(value: str) -> str`
Returns `value` when `LANGUAGE` matches it, else `ValueError("'<value>' is not a language tag such as 'sv' or
'pt-BR'")`.

### `class EntryField(StrEnum)`
`NAME = "name"`, `DESCRIPTION = "description"`, `TAG = "tag"`, `OWNER = "owner"`, `COLLABORATOR = "collaborator"`,
`DELETED = "deleted"`, `LANGUAGE = "language"`. Repeated in `0012` (`entry_field_check`).

### `class Thread(_Frozen)`
A row of `catalog.thread`. Every field is required.

| Field | Type | Description |
| --- | --- | --- |
| `id` | `int` | |
| `kind` | `str` | one of `THREAD_KINDS` (enforced by `Catalog.create` and `0012`, not by the model) |
| `forked_from` | `int \| None` | the edit of the origin it was forked from |
| `by` | `int` | who created it |
| `at` | `datetime` | |

### `class Edit(_Frozen)`
A row of `catalog.edit`, without its `kind` column. Every field is required.

| Field | Type | Description |
| --- | --- | --- |
| `id` | `int` | |
| `thread` | `int` | |
| `digest` | `str` | a component of the thread's kind |
| `compilation` | `str \| None` | for a skeleton edit, the compilation that produced the skeleton |
| `based_on` | `int \| None` | for an edit of a fork, the origin edit it was re-applied onto |
| `by` | `int` | who saved it |
| `at` | `datetime` | |

### `class Binding(_Frozen)`
A row of `catalog.binding`: `id: int`, `family: int`, `vignette: Vignette`, `by: int`, `at: datetime`. The table's
`source`, `source_id` and `fingerprint` columns are `vignette.source`, `vignette.id` and `vignette.fingerprint`.

### `class Subject(_Frozen)`
What an entry is about: `thread: int | None`, `family: int | None`, `run: UUID | None`, `score: UUID | None`, all
defaulting to `None`. Exactly one must be set (`ValueError("a subject is exactly one of a thread, a family, a run or
a score")`, wrapped in `ValidationError`).

### `class Entry(_Frozen)`
One thing said about a subject: `field: EntryField`, `value: str | None = None`, `person: int | None = None`,
`present: bool = True`.

| `field` | `value` | `person` | `present=False` |
| --- | --- | --- | --- |
| `name` | required and not empty when `present`; `None` when not | `None` | removes the name |
| `description` | required; may be empty | `None` | refused |
| `tag` | required and not empty, also when not `present` | `None` | removes that tag |
| `owner` | `None` | required | refused |
| `collaborator` | `None` | required | removes that collaborator |
| `deleted` | `None` | `None` | restores the subject |
| `language` | required; a language tag (`language_tag`) | `None` | refused |

Building one that breaks the table raises `ValidationError` wrapping `ValueError`: `wrong value or person for
<field>`, `<field> can't be removed, only replaced`, `<field> can't be empty`, or the `language_tag` message. The model
doesn't know its subject; `language.py:check_entry` refuses a `language` entry on anything but a family. `0012`
repeats the shapes (`entry_shape_check`) and the family rule (`entry_language_check`).

### `class About(_Frozen)`
What a subject's entries say now.

| Field | Type | Default |
| --- | --- | --- |
| `name` | `str \| None` | `None` |
| `description` | `str \| None` | `None` |
| `tags` | `frozenset[str]` | empty |
| `owner` | `int \| None` | `None` |
| `collaborators` | `frozenset[int]` | empty |
| `deleted` | `bool` | `False` |
| `language` | `str \| None` | `None` |

| Member | Description |
| --- | --- |
| `of(entries: Iterable[Entry]) -> Self` (classmethod) | Folds the entries in the order given. For `name`, `description`, `owner`, `deleted` and `language` the last entry wins; a `name` entry without a value clears the name. For `tag` and `collaborator` the last entry for each member wins: `present` adds it, not `present` removes it. No entries give `About()`. |
| `shows(person: int) -> bool` | `not deleted and (owner == person or person in collaborators)`. |

### `latest[K, V](rows: Iterable[tuple[K, V]]) -> dict[K, V]`
`dict(rows)`: for each key, the value of its last row. A key keeps the position of its first row.

### `check_label(scorer: Scorer, part: Part, position: int) -> None`
`ValueError("<scorer digest> has no <part> at position <position>")` unless `0 <= position < len(scorer.views)` (for
`view`) or `len(scorer.resources)` (for `resource`). `0012` repeats it (`catalog.check_label`).

### Results

#### `class Variation(_Frozen)`
What `threads.variation` returns.

| Member | Description |
| --- | --- |
| `base: Edit` | The origin edit the fork is compared with. |
| `origin_head: Edit` | The origin's head now. |
| `varies: dict[str, tuple[JsonValue, JsonValue]]` | Path → (value at the base, value at the fork's head), for the paths that differ, sorted by path. `None` on a side stands for a missing field as well as a null one. |
| `moved -> bool` (property) | `origin_head.id != base.id`. |

#### `class Behind(_Frozen)`
One reference of a thread's head that could be updated.

| Field | Type | Default |
| --- | --- | --- |
| `path` | `str` | required; where the reference is, from the head (`/skeleton`, `/recipe/output`, `/cases/0/appendices/0`) |
| `digest` | `str` | required; what the head references there |
| `head` | `Edit \| None` | `None`; the head of a thread that held `digest` and has moved on |
| `binding` | `Binding \| None` | `None`; the current binding of the family of a case that is behind it |
| `replacement` | `str \| None` | `None`; the case `digest` becomes under `binding` |

Exactly one of `head` and `binding` is set (`ValueError("behind either a newer head or a newer binding")`), and
`replacement` is set exactly when `binding` is (`ValueError("a replacement case goes with a newer binding, and only
with it")`), both wrapped in `ValidationError`.

#### `class Survey(_Frozen)`
What `families.survey` returns. Every field defaults to `()`.

| Field | Type | Holds |
| --- | --- | --- |
| `unchanged` | `tuple[int, ...]` | families whose id and content are listed as bound |
| `changed` | `tuple[tuple[int, str, Fingerprint], ...]` | (family, id, new fingerprint): the same id with new content |
| `renamed` | `tuple[tuple[int, str, str], ...]` | (family, old id, new id): the same content under a new id |
| `new` | `tuple[str, ...]` | listed ids that match no family |
| `gone` | `tuple[int, ...]` | families none of whose ids or contents are listed |

#### `class Repair(_Frozen)`
What `Catalog.repair` wrote: `binding: Binding` (the new one), `cases: dict[str, str]` and `appendices: dict[str,
str]` (old digest → rebound digest), `edits: tuple[Edit, ...]` (in the order of `RepairPlan.moves`).

## read.py

### `class Reader(Protocol)`
What the rules read. Lists come back in the order the rows were written; for components, by digest. A `Reader` never
picks the latest row. `src/chatddx/store/catalog.py:Rows` implements it over the tables, and
`test/memory.py:Memory` over a `Registry` and lists.

| Method | Returns |
| --- | --- |
| `get(digest: str) -> Component` | The stored component. `StructuralError` when it isn't stored. |
| `kind(digest: str) -> str \| None` | Its kind, or `None` when it isn't stored. |
| `compilations(skeleton: str) -> list[Compilation]` | The stored compilations whose `skeleton` is this one, by compilation digest. |
| `thread(id: int) -> Thread \| None` | |
| `threads(kind: str) -> list[Thread]` | The threads of a kind, by id. |
| `threads_forked_from(edits: Collection[int]) -> list[Thread]` | The threads whose `forked_from` is one of the edits. |
| `edit(id: int) -> Edit \| None` | |
| `edits(threads: Collection[int]) -> list[Edit]` | The edits of these threads, by id. |
| `edits_holding(digests: Collection[str]) -> list[Edit]` | The edits, in any thread, whose digest is one of these, by id. |
| `entries(subjects: Collection[Subject]) -> list[tuple[Subject, Entry, int]]` | The entries about these subjects, by id, each with the person who wrote it. |
| `bindings(family: int) -> list[Binding]` | The family's bindings, by id; `[]` for an unknown family. |
| `families() -> list[int]` | Every family's id. `Rows` reads `catalog.family`; `Memory` lists the families that have bindings. |
| `bindings_in(source: str) -> list[Binding]` | Every binding, of any family, in a source, by id. |
| `bound_to(vignette: Vignette, kind: str) -> list[str]` | The stored components of `kind` (`case` or `appendix`) whose `vignette` equals this one, by digest. |
| `expectations(cases: Collection[str]) -> list[str]` | The stored expectations of these cases, by digest. |
| `languages(digests: Collection[str]) -> list[tuple[str, str]]` | (digest, language) rows for these digests, by id. |
| `labels(scorer: str) -> list[tuple[Part, int, str]]` | (part, position, label) rows for a scorer, by id. |
| `bindings_sharing(vignette: Vignette) -> list[Binding]` | The bindings in the vignette's source to its id or to its fingerprint, by id. |

### Helpers

| Function | Returns |
| --- | --- |
| `heads_of(rows, threads: Collection[int]) -> dict[int, Edit]` | Thread → its latest edit, sorted by thread id. Threads without edits are left out. |
| `holders(rows, digests: Collection[str]) -> dict[int, Edit]` | `heads_of` every thread with an edit, current or earlier, holding one of the digests. |
| `heads_holding(rows, digests: Collection[str]) -> dict[int, Edit]` | The `holders` whose head is one of the digests. |
| `abouts(rows, subjects: Collection[Subject]) -> dict[Subject, About]` | `About.of` each subject's entries; every subject given is a key. |
| `about(rows, subject: Subject) -> About` | `abouts` of one subject. |
| `labels(rows, scorer: str) -> dict[tuple[Part, int], str]` | The latest label for each (part, position). `{}` for a scorer without labels, stored or not. |
| `tags_given(rows, subject: Subject) -> dict[str, int]` | The tags that hold on the subject now, each with the writer of the latest entry about it. |

## threads.py

### Checks

| Function | Raises |
| --- | --- |
| `check_threadable(kind: str) -> None` | `ValueError("<kind> components have no threads")` when `kind` isn't in `THREAD_KINDS`. |
| `check_based_on(rows, thread: int, based_on: int) -> None` | `ValueError("edit <based_on> is not in the origin of thread <thread>")` unless the thread exists, is a fork, and `based_on` is an edit of its origin with an id at or after `forked_from`. `0012` repeats it (`catalog.check_based_on`, same message). |

### Lookups

| Function | Returns / raises |
| --- | --- |
| `thread(rows, id: int) -> Thread` | `LookupError("no thread with id <id>")` when there is none. |
| `edit(rows, id: int) -> Edit` | `LookupError("no edit with id <id>")` when there is none. |
| `history(rows, thread: int) -> list[Edit]` | The thread's edits, by id. `LookupError("no thread with id <thread>")` when it has none, which also covers a thread that doesn't exist. Includes deleted threads. |
| `head(rows, thread: int) -> Edit` | The last of `history`. |
| `recipe(rows, edit: Edit) -> Recipe \| None` | The recipe of the edit's compilation, or `None` when it names none. Takes an edit; `Catalog.recipe(thread)` passes the head. |

### `heads(rows, kind: str, *, deleted: bool = False) -> list[Edit]`
The heads of the threads of `kind` whose `About.deleted` equals `deleted`, in thread id order. Threads without edits
are left out; an unknown kind gives `[]`.

### `find(rows, kind: str, name: str, *, owner: int | None = None) -> list[int]`
The ids of the live threads of `kind` whose current name is exactly `name`, and whose owner is `owner` when given, in
thread id order. Names aren't unique, so it may return several.

### `visible(rows, kind: str, person: int) -> list[tuple[Edit, About]]`
The head and `About` of each thread of `kind` that `About.shows(person)`: live, and owned by `person` or shared with
them as a collaborator. Thread id order; threads without edits are left out.

### `expectation_for(rows, case: str, person: int, schema: str) -> str | None`
The digest of the expectation `person` scores `case` against, among the threads whose head is an expectation of
`case` with `expectation_schema == schema` and which `About.shows(person)`:
1. those `person` owns: one distinct head digest is returned;
2. otherwise all of them, shared ones included: one distinct head digest is returned;
3. nothing: `None`.

Several distinct head digests at the first step that has any raise `LookupError("case <case> has expectations to
choose from, in threads <t1>, <t2>, …")`, naming the threads of that step. Threads with the same head digest count as
one choice. Owning one thread is enough to ignore the shared ones.

### `forks(rows, thread: int) -> list[int]`
The ids of the threads whose `forked_from` is any edit of `thread`, in thread id order. Direct forks only; deleted
forks included. An unknown thread gives `[]`.

### `expectations_of(rows, case: str) -> list[int]`
The ids, sorted, of the threads whose head is an expectation of `case`. Deleted threads included.

### `behind(rows, thread: int) -> list[Behind]`
The references of the thread's head that could be updated. `LookupError` for a thread without edits.

The references looked at:
1. the head's own (`Component.refs()`): `/skeleton`, `/engine`, `/cases/0`, …;
2. when the head names a compilation, its recipe's, under `/recipe` (`/recipe/instructions`, …);
3. for each reference from 1 and 2 that is a case, the case's own references under its path: `/cases/0/appendices/0`,
   or `/case/appendices/0` for an expectation.

For each reference, every thread with an edit, current or earlier, holding its digest is looked at. A live one whose
head now holds another digest gives `Behind(path, digest, head=<that head>)`. A digest held by several threads gives
one entry per thread that moved on.

Each case reference whose family is live and has a current binding other than the case's vignette gives
`Behind(path, digest, binding=<current binding>, replacement=<rebound case>)`, from `families.stale_cases`. The
replacement has the same appendix texts bound to the current vignette; it is computed, and may not be stored.

The result is sorted by path; within a path, `head` entries come in thread id order, then the `binding` entry.
`behind` goes one level: it doesn't follow a reference's own references, except a case's.

### `variation(rows, id: int) -> Variation | None`
`None` when the thread isn't a fork; `LookupError` when it doesn't exist, or is a fork without edits.

The base is the edit named by the fork's latest `based_on`, or else its `forked_from`. The fork is compared by recipe
when both the base and the fork's head name a compilation:
- by recipe: every field of the two recipes (`Recipe.model_dump(mode="json")`), as `/recipe/<field>`; `purpose` and
  `appendix_layout` included;
- otherwise: the top-level fields of the two canonical documents, without `kind` and `v`, as `/<field>`.

`varies` holds the paths whose values differ. `origin_head` is the head of the base's thread.

### `proposal(rows, id: int) -> Recipe | Component | None`
The origin's head with the fork's changes on top, or `None` when `variation` is `None` or hasn't `moved`. Nothing is
stored.
- Compared by recipe: the recipe of the origin's head, with each varied field set to the fork's value, as a
  `Recipe` to compile. `None` when the origin's head names no compilation. `ValidationError` when the result isn't a
  valid recipe.
- Otherwise: the canonical document of the origin's head, with each varied top-level field set to the fork's value,
  or removed where the fork has none, read back with `parse_component`. `StructuralError` or `ValidationError` when
  the result isn't a valid component.

## `variants.py`

### `variant_name(name, language, model)` -> `str`
What's made for a language, a model or both is named after them, so that one name finds
the variant that fits: `NAME (LANGUAGE)`, `NAME (MODEL)` or `NAME (LANGUAGE, MODEL)`.

### `made_for(name, models)` -> `(name, language, model) | None`
What a variant's name says it was made from and for, or None for a name that isn't a
variant's; `models` are the models a variant may be made for.

### `variants_for(name, names, model)`
The variants of `name` among `names` that `model` may use: those made for it, or for
every model.

## families.py

### `bindings(rows, family: int) -> list[Binding]`
The family's bindings, by id; the last is the current one. `LookupError("no family with id <family>")` when it has
none, which also covers a family that doesn't exist.

### `visible(rows, person: int) -> list[tuple[int, About]]`
Each family, in id order, whose `About.shows(person)`, with its `About`.

### `family_of(rows, case: str) -> int | None`
`None` when `case` isn't a stored case. Otherwise, among the bindings in the case's source equal to its vignette
(source, id and fingerprint), the family of the one with the highest id; `None` when none matches. Earlier bindings
count, so a case from before a repair keeps its family. Deleted families included.

### `holder(rows, vignette: Vignette, *, but: int | None = None) -> tuple[int, bool] | None`
Among the current bindings of the families in `vignette.source`, other than `but`, the lowest family id whose binding
has the same id or the same fingerprint as `vignette`, with `True` when the id is the same. `None` when there is none.

### `check_adoptable(rows, case: str) -> Vignette`
Returns the case's vignette. Raises:
- `LookupError("<case> is not a stored case")`;
- `ValueError("<case> gives family <n>'s vignette new content; rebind the family")` when `holder` finds the same id,
  or `… a new name; …` when it finds the same content.

`Catalog.adopt` calls it only after `family_of` found no family, so a case whose vignette is already bound never gets
here.

### `survey(rows, source: str, listing: Mapping[str, Fingerprint]) -> Survey`
Compares `listing` (id → fingerprint) with the current bindings of the families in `source`. For each listed id, in
sorted order:
- a family currently bound to that id: `unchanged` when the fingerprint is the same, else `changed`;
- otherwise, exactly one family currently bound to the same fingerprint under an id that isn't listed: `renamed`;
- otherwise: `new`.

Families none of those took are `gone`, in family id order. A vignette whose id and content both changed is `gone`
plus `new`. Deleted families included.

### Rebinding

| Function | Returns |
| --- | --- |
| `rebind_appendix(appendix: Appendix, vignette: Vignette) -> Appendix` | The same text, bound to `vignette`. |
| `rebind_case(case: Case, vignette: Vignette, get: Resolver) -> tuple[Case, dict[str, Appendix]]` | The case with `vignette` and each appendix rebound, in the same order, and old appendix digest → rebound appendix. |

### `class RepairPlan`
A frozen dataclass: what `plan_repair` decided, for `Catalog.repair` to write.

| Field | Type | Holds |
| --- | --- | --- |
| `vignette` | `Vignette` | the new binding's vignette |
| `registry` | `Registry` | every rebuilt case, appendix and expectation, and the expectation schemas those reference |
| `cases` | `dict[str, str]` | old case digest → rebound case digest |
| `appendices` | `dict[str, str]` | old appendix digest → rebound appendix digest |
| `moves` | `list[tuple[int, str]]` | (thread, digest) edits to write |

### `plan_repair(rows, family: int, *, id: str | None = None, fingerprint: Fingerprint | None = None) -> RepairPlan`
Moves the family's current vignette to a new id or new content, keeping its source. `id` and `fingerprint` default to
the current ones.

Raises:
- `LookupError("no family with id <family>")` when it has no bindings;
- `ValueError("a repair changes exactly one of the id or the fingerprint")` when the new vignette changes neither or
  both;
- `ValueError("family <n> already has the id '<id>'")` or `ValueError("family <n> already has that content")` when
  `holder(…, but=family)` finds another family there.

Plans:
1. every stored case bound to the current vignette, rebound (`rebind_case`), in `cases` and `appendices`;
2. for each thread whose head is an appendix bound to the current vignette, a move to the rebound appendix, in
   thread id order;
3. when the id changes, for each thread whose head is an expectation of one of the old cases, a move to an expectation
   of the rebound case with the same schema and data, in thread id order.

Deleted threads get moves too. Cases and appendices bound to an earlier binding aren't rebuilt. `0012` checks that a
new binding keeps the source, and the id or the fingerprint (`catalog.check_binding`).

### `stale_cases(rows, refs: list[tuple[str, str]]) -> list[Behind]`
For each (path, digest) in `refs` that is a case with a family (`family_of`), live, whose current binding's vignette
isn't the case's: `Behind(path, digest, binding=<current>, replacement=<rebind_case digest>)`, in `refs` order. Other
references are skipped. `threads.behind` calls it.

## language.py

### `own(rows, digest: str) -> str | None`
The latest language recorded for the digest itself (`catalog.language`), or `None`.

### `language_of(rows, digest: str) -> str | None`
By the digest's kind:

| Kind | Language |
| --- | --- |
| `case` | its family's `About.language`; `None` without a family |
| `expectation` | its case's |
| `trial`, `judge` | its skeleton's |
| `skeleton` with compilations | one vote per compilation's recipe; the language when the votes that are cast agree, else `None` |
| anything else, a skeleton without compilations included | `own` |

A recipe votes:
- with translations: for `own(translations)`, when it has one;
- without: for the language that `own` gives every text-bearing part (the keys of
  `chatddx.factors.request.texts(recipe)`, `toolset` included and `appendix_layout` not), when they all have the same
  one. A part without a language, or parts that disagree, cast no vote.

A digest that isn't stored gives `None`.

### `check_language(rows, digest: str, value: str) -> str`
Returns the digest's kind, for the row. Raises, in this order:
- `LookupError("<digest> is not in the store")`;
- `ValueError("<kind> components have no language of their own")` when the kind isn't in `LANGUAGE_KINDS`;
- `ValueError("<digest>: a compiled skeleton's language comes from its recipe")` for a skeleton with a compilation;
- the `language_tag` `ValueError`.

`0012` repeats it (`language_value_check`, `language_kind_check`, `catalog.check_language`).

### `check_entry(subject: Subject, entry: Entry) -> None`
`ValueError("a language entry is for a family's vignette; a component's language is kept on its digest")` for a
`language` entry on anything but a family. `0012` repeats it (`entry_language_check`).

## titles.py

### Names and helpers

| Name | Description |
| --- | --- |
| `Title` | `Callable[[str], str]`: digest → title. Descriptions call it for the digests they mention; `title`, `title_of` and `_derive` pass `partial(title_of, rows)`. |
| `short(digest) -> str` | The first 6 hex digits. |
| `snippet(text, limit=40) -> str` | Whitespace collapsed; when longer than `limit`, cut at the last space within `limit + 1` characters and followed by `…` (a text without a space there keeps `limit + 1` characters); in double quotes. |
| `describe_case(root, appendices, title) -> str` | `<root> with <title of each appendix, joined by ", ">`, or `root` without appendices. |
| `describe_recipe(recipe, title) -> str` | The titles of the recipe's parts that are set, in the order `instructions`, `few_shot`, `prompt`, `output`, `sampling`, `reasoning`, `passthrough`, `translations`, `toolset`, joined by ` · `; prefixed with `judge: ` when `purpose` isn't `generation`. `appendix_layout` isn't shown. |
| `describe_change(path, after, title) -> str` | `path` without `/recipe/` or `/`, then: `no <key>` for `None`; `<key>: <title>` for a digest; `<key>: <snippet>` for other text; `<key>: <JSON>` for anything else. |

### `describe(component: Component, title: Title, language: str | None = None) -> str`
What a component holds. `language` is used only for translations.

| Kind | Description |
| --- | --- |
| `chunk.instructions` | `snippet` of its text; slots and inserts as `{name}` |
| `chunk.few_shot` | `few-shot, <n> message(s)` |
| `chunk.prompt` | `snippet` of its segments |
| `chunk.output` | `native output`, `text output` or `tool <name> output`, followed by `: <schema title>` or `: <property names>` when its schema has one |
| `chunk.sampling` | the sampling values that are set (`temperature 0.2, top_p 0.9`), or `default sampling` |
| `chunk.reasoning` | `effort <e>`, each chat template kwarg as `<key> <JSON>`, and `budget <n>`, joined by `, `; or `default reasoning` |
| `chunk.passthrough` | `passthrough: <keys>` |
| `chunk.translations` | `[<language> ]translations, <n> text(s)` |
| `chunk.toolset` | `with <title of each tool>` |
| `tool` | its name |
| `skeleton` | `<purpose> skeleton <short>` (a compiled skeleton is described by its recipe instead, see `_derive`) |
| `trial` | `<skeleton title> on <engine title>, <n> case(s), <n> seed(s)` |
| `judge` | `judge <skeleton title> on <engine title>` |
| `scorer` | `scorer <distribution> <version>` |
| `scoring` | `<scorer title> against <n> expectation(s)` |
| `appendix` | `snippet` of its text |
| `expectation` | `expectation for <case title>` |
| `case` | `describe_case("<source>/<id>", …)` |
| `model` | its repo |
| `engine.local` | `<model title> on <server> <version> (<gpu>)` |
| `engine.remote` | `<model> at <host>` |
| `expectation_schema` | its schema's title, its property names, or `expectation schema <short>` |
| `canary_set` | `<n> canary` or `<n> canaries` |
| `compilation` | `compilation <short>` |

### `title(rows, thread: int) -> str`
1. The thread's name, when it has one.
2. For a fork, the `title` of its base's thread (the origin), then `describe_change` of each path in
   `variation.varies`, joined by `, `: `plan, output: management-plan-shown`. A fork that varies nothing is
   `a fork of <origin's title>`.
3. Otherwise `_derive` of the head, with the compilation it names.

`LookupError` for an unnamed thread that doesn't exist or has no edits. The origin's title describes the origin's
current head, while `varies` is measured from the base (see "Known gaps").

### `title_of(rows, digest: str) -> str`
For a case, `_case_title`. For anything else, among the threads with an edit holding the digest, live ones first and
then deleted ones, each in thread id order:
1. a thread whose head is the digest and that has a name: the name;
2. a thread whose head is the digest: its `title`;
3. a thread with a name: `<name> (earlier)`.

When no thread gives a title, `_derive(digest)`. `StructuralError` for a digest that isn't stored.

### `_case_title(rows, digest: str) -> str`
Without a family, `describe` of the case. With one, `describe_case` with the family's name, or else its current
binding's `<source>/<id>`, followed by ` (earlier)` when the case's vignette isn't the current one:
`chest pain (earlier) with "Troponin 80 ng/L."`. The family's deletion isn't looked at.

### `_derive(rows, digest: str, compilation: str | None = None) -> str`
A skeleton with a compilation is described by `describe_recipe` of that compilation's recipe: the one given, or else
the first of `Reader.compilations` (by digest). Anything else is `describe`d, with `own(digest)` as its language.

## The store's Catalog

`src/chatddx/store/catalog.py:Catalog` is what callers use. Each method reads through `Rows` and calls this package;
the ones that write insert the rows the package decided on. A rule the database also checks is refused by Postgres
with a psycopg error when the Python lets it through.

| Method | Calls | Writes |
| --- | --- | --- |
| `create(digest, by, *, compilation=None, forked_from=None, name=None, owner=None) -> Edit` | `Reader.kind` (`LookupError("<digest> is not in the store")`), `threads.check_threadable` | in one transaction: the thread, its first edit (`edit`), an `owner` entry for `owner` or else `by`, and a `name` entry when given |
| `edit(thread, digest, by, *, compilation=None, based_on=None) -> Edit` | `threads.check_based_on` when `based_on` is given | the edit, with the thread's kind; `LookupError("no thread with id <thread>")` when there is no thread |
| `thread`, `history`, `head`, `heads`, `find`, `visible`, `expectation_for`, `forks`, `expectations_of`, `behind`, `variation`, `proposal` | the `threads` function of that name | |
| `visible_families(person)` | `families.visible` | |
| `containing(digest) -> list[Edit]` | `Reader.edits_holding([digest])` | |
| `recipe(thread)` | `threads.recipe` of `threads.head` | |
| `title(thread)`, `title_of(digest)` | `titles.title`, `titles.title_of` | |
| `language_of(digest)` | `language.language_of` | |
| `adopt(case, by, *, owner=None) -> int` | `families.family_of`, returning its family when there is one; else `families.check_adoptable` | in one transaction: a family, its binding, an `owner` entry for `owner` or else `by` |
| `family(case)`, `bindings(family)`, `survey(source, listing)` | `families.family_of`, `families.bindings`, `families.survey` | |
| `repair(family, by, *, id=None, fingerprint=None) -> Repair` | `families.plan_repair` | in one transaction: the binding, `Store.add` of the plan's registry, and an edit per move |
| `note(subject, entry, by)` | `language.check_entry` | the entry; a run or score subject also gets its stage column set to `'started'` |
| `language(digest, value, by)` | `language.check_language` | a `catalog.language` row with the kind it returned |
| `about(subject)`, `abouts(subjects)` | `read.about`, `read.abouts` | |
| `involving(person) -> list[Subject]` | the store only | the subjects whose `owner` or `collaborator` entries ever named the person |
| `label(scorer, part, position, value, by)` | `check_label` of the resolved scorer | the label |
| `labels(scorer)` | `read.labels` | |
| `tags_given(subject)` | `read.tags_given` | |
| `keep(digest, by, thread, *, name=None, compilation=None, forked_from=None) -> tuple[Edit, Kept]` | `threads.head`, then `create` without a thread or `edit` | a new thread, a new edit, or nothing when the head is `digest` already |

## Database: schema `catalog`

Created by `0010-t0-catalog.sql`, roles in `0011-t1-catalog.sql`, rules and insert-only triggers in
`0012-t2-catalog.sql` (`docs/migrations.md`, "catalog"). Every table has `id bigint GENERATED ALWAYS AS IDENTITY
PRIMARY KEY`, `by bigint NOT NULL` → `identity.person`, and `at timestamptz NOT NULL DEFAULT now()`; the tables below
list the other columns. "Latest" is the highest id.

`0010` also adds `UNIQUE (digest, kind)` on `factor.component` and `UNIQUE (src, path, dst)` on
`factor.component_ref`, as targets for the composite foreign keys.

### `catalog.thread`
`Thread` rows.

| Column | Type | Holds |
| --- | --- | --- |
| `kind` | `text NOT NULL`; CHECK `thread_kind_check` (0012): one of `THREAD_KINDS` | `kind` |
| `forked_from` | `bigint`; FK `(forked_from, kind)` → `edit (id, kind)` | `forked_from` |

`UNIQUE (id, kind)`, as the target of `edit`'s foreign key.

### `catalog.edit`
`Edit` rows.

| Column | Type | Holds |
| --- | --- | --- |
| `thread` | `bigint NOT NULL`; FK `(thread, kind)` → `thread (id, kind)` | `thread` |
| `kind` | `text NOT NULL` | the thread's kind; `Catalog.edit` copies it from the thread |
| `digest` | `text NOT NULL`; FK `(digest, kind)` → `factor.component (digest, kind)` | `digest` |
| `compilation` | `text`; FK `(compilation, compilation_kind)` → `factor.component (digest, kind)`; FK `(compilation, compilation_path, digest)` → `factor.component_ref (src, path, dst)` | `compilation` |
| `compilation_kind` | `text NOT NULL DEFAULT 'compilation'`, CHECK `= 'compilation'` | constant |
| `compilation_path` | `text NOT NULL DEFAULT '/skeleton'`, CHECK `= '/skeleton'` | constant |
| `based_on` | `bigint`; FK `(based_on, kind)` → `edit (id, kind)` | `based_on` |

`UNIQUE (id, kind)`. CHECK `compilation IS NULL OR kind = 'skeleton'`. Indexes `edit_thread (thread, id)` and
`edit_digest (digest)`. Trigger `edit_based_on` (0012, BEFORE INSERT): `catalog.check_based_on()` raises `edit
<based_on> is not in the origin of thread <thread>`, as `threads.check_based_on` does.

So an edit points at a stored component of its thread's kind, a fork at an edit of its own kind, `based_on` at an edit
of the same kind in the origin at or after the fork, and a compilation only from a skeleton edit, to a compilation
whose `/skeleton` is the edit's digest.

### `catalog.family`
No columns but `id`, `by` and `at`.

### `catalog.binding`
`Binding` rows.

| Column | Type | Holds |
| --- | --- | --- |
| `family` | `bigint NOT NULL`, FK → `family` | `family` |
| `source` | `text NOT NULL` | `vignette.source` |
| `source_id` | `text NOT NULL` | `vignette.id` |
| `fingerprint` | `jsonb NOT NULL` | `vignette.fingerprint`, as its canonical JSON |

```
AGENT: CHANGE
0013-t0-catalog-binding-content.sql (1dd791a) adds a third index, documented in docs/migrations.md, "Tier 0".
---
Indexes `binding_family (family, id)`, `binding_source (source, source_id)` and `binding_content (source,
fingerprint)` (0013).
```
Indexes `binding_family (family, id)` and `binding_source (source, source_id)`. Trigger `binding_anchor` (0012,
BEFORE INSERT): `catalog.check_binding()` raises `family <n>: a new binding must keep the source, and the id or the
fingerprint` unless the new binding has the previous one's source and its `source_id` or its `fingerprint`.

### `catalog.entry`
`(Subject, Entry)` rows.

| Column | Type | Holds |
| --- | --- | --- |
| `thread` | `bigint`, FK → `thread` | `Subject.thread` |
| `family` | `bigint`, FK → `family` | `Subject.family` |
| `run` | `uuid` | `Subject.run` |
| `run_stage` | `text`, CHECK `= 'started'` | `'started'` with a run; FK `(run, run_stage)` → `ledger.run_stage` |
| `score` | `uuid` | `Subject.score` |
| `score_stage` | `text`, CHECK `= 'started'` | `'started'` with a score; FK `(score, score_stage)` → `ledger.score_stage` |
| `field` | `text NOT NULL`; CHECK `entry_field_check` (0012): one of `EntryField` | `field` |
| `value` | `text` | `value` |
| `person` | `bigint`, FK → `identity.person` | `person` |
| `present` | `boolean NOT NULL DEFAULT true` | `present` |

CHECK (0010): `num_nonnulls(thread, family, run, score) = 1`, `(run IS NULL) = (run_stage IS NULL)`, `(score IS NULL)
= (score_stage IS NULL)`. CHECK (0012): `entry_shape_check`, the table under `Entry`, with NULL values ruled out
explicitly, and `entry_language_check`, `field <> 'language' OR family IS NOT NULL`. Partial indexes on `thread`,
`family`, `run` and `score` where not NULL. An entry on a run or a score needs the run's or score's started row.

### `catalog.label`
Scorer labels.

| Column | Type | Holds |
| --- | --- | --- |
| `scorer` | `text NOT NULL`; FK `(scorer, kind)` → `factor.component (digest, kind)` | the scorer's digest |
| `kind` | `text NOT NULL DEFAULT 'scorer'`, CHECK `= 'scorer'` | constant |
| `part` | `text NOT NULL`, CHECK `IN ('view', 'resource')` | `Part` |
| `position` | `integer NOT NULL`, CHECK `>= 0` | the position among the scorer's views or resources |
| `value` | `text NOT NULL` | the label |

Index `label_scorer (scorer)`. Trigger `label_position` (0012, BEFORE INSERT): `catalog.check_label()` raises
`<scorer>: no <part> at position <position>` when the position is past the end of the scorer document's `views` or
`resources` (a missing key counts as empty).

### `catalog.language`
Languages kept on a component's digest.

| Column | Type | Holds |
| --- | --- | --- |
| `digest` | `text NOT NULL`; FK `(digest, kind)` → `factor.component (digest, kind)` | the component |
| `kind` | `text NOT NULL`; CHECK `language_kind_check` (0012): one of `LANGUAGE_KINDS` | its kind, from `check_language` |
| `value` | `text NOT NULL`; CHECK `language_value_check` (0012): matches `LANGUAGE` | the language |

Index `language_digest (digest, id)`. Trigger `language_compiled` (0012, BEFORE INSERT): `catalog.check_language()`
raises `<digest>: a compiled skeleton's language comes from its recipe` when a stored compilation's `/skeleton` points
at the digest.

### Insert-only (`0012`)
On every table, the triggers `insert_only` (BEFORE UPDATE OR DELETE, per row) and `insert_only_truncate` (BEFORE
TRUNCATE, per statement) call `factor.refuse_change()`, which raises `<schema>.<table> is insert-only`.

### Roles (`0011`)
PUBLIC loses all access to the schema and its tables. `chatddx_writer` gets `USAGE` and `SELECT, INSERT`, and
`chatddx_reader` `USAGE` and `SELECT`, on existing tables and, through default privileges, on tables created later.
The catalog holds nothing produced from a vignette, so the reader may read all of it.

### What the database checks, and what it doesn't
It checks thread kinds; that edits point at stored components of their thread's kind; that forks, `based_on` and
compilations point where they may (see `catalog.edit`); that an entry has exactly one subject, an existing run or score
started row, a known field and the right shape, and a language only on a family; that labels name a scorer's
existing view or resource; that a family's bindings keep their source and either the id or the fingerprint; that
languages are tags on components of `LANGUAGE_KINDS` and not on a skeleton already known to be compiled; and that
nothing changes.

It doesn't
- require a thread to have an edit, or a family to have a binding (`Catalog.create` and `Catalog.adopt` write both in
  one transaction);
- keep current bindings unique across families, the check `adopt` and `repair` make through `families.holder`;
- require a new binding to differ from the previous one, which `plan_repair` does;
- require a skeleton edit to name its compilation when one exists;
- notice that a skeleton with a language row is compiled later;
- check names, labels or descriptions beyond what the shapes say, or that a subject has an owner.

## Known gaps
From `docs/catalog.md`, "Open design issues", where they concern this API:
- The rules are checked in Python on rows read inside the writing transaction; with two writers at once only tier 2
  holds. Two `adopt` calls for one vignette at the same moment can create two families.
- Two vignettes with the same content under different ids in one source look like a rename: `adopt` refuses the
  second.
- When bindings of several families match a case, `family_of` takes the family of the latest matching binding.
- Current bindings are read per source, which relies on a family never changing source; tier 2 enforces that.
- A thread without edits is possible in SQL.
- A skeleton edit may leave out its compilation.
- A language on a skeleton that is compiled later is ignored from then on.
- A case stored at a vignette's old place after a repair gets a replacement from `behind` that nothing has stored.
- Who changed an entry, a label or a language isn't returned: `Reader` reads them without `by` and `at`.
- Why an edit was made isn't stored.
- Titles take a query for every reference they visit, are rebuilt from names that change, and aren't unique.
- Scorer labels aren't carried to the next scorer edit.

Also:
- An unnamed fork's title can pair two versions: when its origin has no name and has moved on, `title` describes the
  origin's current head but lists the changes from the base. A fork of `"alpha first version"` whose origin has moved
  on to `"beta second version"` is titled `"beta second version", text: "gamma fork text"`.

## Beyond docs/catalog.md
```
AGENT: CHANGE
docs/catalog.md has no proposals, and main's history never had these six there. The pointer goes; the list stays.
---
Behavior described here that `docs/catalog.md` doesn't state, or states otherwise.
```
Behavior described here that `docs/catalog.md` doesn't state, or states otherwise. The first six are proposed as
amendments there.
- `owner` and `collaborator` entries are read by `About.shows`, so by `visible`, `visible_families` and
  `expectation_for`; `expectation_for` also reads `owner` itself.
- Tools, appendices, judges, scorers, scorings, models, expectation schemas and canary sets have descriptions of their
  own; only a compilation is described by its kind and the start of its digest.
- "Latest wins" is also written as `[-1]` of a `Reader` list, outside `latest` and `About.of`.
- `family_of` takes the family of the latest matching binding, which isn't necessarily the latest family.
- A fork's title starts with its origin's title, which describes the origin's current head, not the base.
- Threads, edits and bindings are returned with `by` and `at`; entries, labels and languages are not.
- `history` and `behind` raise `LookupError` for a thread without edits as well as for one that doesn't exist;
  `forks` gives `[]` for either.
- `expectation_for` counts distinct head digests, so two threads with the same head are one choice, and it raises
  `LookupError`.
- `survey` reports one gone family as renamed to every listed new id with its content.
- `plan_repair` rebuilds only the cases and appendices of the current binding.
- A thread's title falls back to the first compilation by digest when its head names none.
- `title_of` of a case ignores whether its family is deleted.
- The tier-2 binding check accepts a binding identical to the previous one, and the tier-2 label check words its error
  differently from `check_label`.
- `latest` keeps each key at the position of its first row.

## Proposed amendments

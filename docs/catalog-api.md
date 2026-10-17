# Catalog API

Reference for the `chatddx.catalog` package and the `catalog` database schema: each name's signature, what it returns
and what it raises. What the catalog is and why it is shaped this way is in `docs/catalog.md`. Factor types it uses
(`Component`, `Fingerprint`, `Vignette`, `Recipe`, `Compilation`, `Registry`, `resolve`, …) are in
`docs/factors-api.md`.

Paths are relative to `src/chatddx/catalog/` unless they start with `src/` or `docs/`.

## Contents
- [Package](#package)
- [Conventions](#conventions)
- [model.py](#modelpy): kinds, rows, entries, `About`, `latest`, results
- [read.py](#readpy): `Reader` and the helpers that pick the latest
- [threads.py](#threadspy): threads, edits, heads, expectations, forks, divergences, proposals, `behind`
- [families.py](#familiespy): bindings, `family_of`, adopting, surveying, repairing, stale cases
- [language.py](#languagepy): a component's language, and the checks on writing one
- [titles.py](#titlespy): descriptions and titles
- [The store's Catalog](#the-stores-catalog)
- [Database: schema `catalog`](#database-schema-catalog)
- [Known gaps](#known-gaps)

## Package
`chatddx.catalog` re-exports `LANGUAGE_KINDS`, `THREAD_KINDS`, `About`, `Behind`, `Binding`, `Divergence`, `Edit`,
`Entry`, `EntryField`, `Kept`, `Labels`, `MovedOn`, `Part`, `Reader`, `Repair`, `RepairPlan`, `Subject`, `Survey`,
`Thread`, `check_label`, `latest`, and the modules `families`, `language`, `read`, `threads` and `titles`. Functions
are called through their module (`threads.behind(rows, thread)`); `model.py` is imported by path.

The modules, and the ones each builds on:
- `model.py`, on none.
- `read.py`, on `model.py`.
- `families.py`, on `model.py` and `read.py`.
- `threads.py`, on `families.py`, `model.py` and `read.py`.
- `language.py`, on `families.py`, `model.py` and `read.py`.
- `titles.py`, on `families.py`, `model.py`, `read.py` and `threads.py`.

The package imports no chatddx package but `chatddx.factors` and `chatddx.identity` (`threads.py`, for `owns`), and no
third-party package but pydantic. It holds no SQL: it reads through a `Reader` and writes nothing, and
`src/chatddx/store/catalog.py:Catalog` writes what it decides (see "The store's Catalog").

## Conventions
- **Models** derive from `model.py:_Frozen`, a pydantic model with `frozen=True, extra="forbid"`. Building one
  validates it. A model whose fields are all hashable is hashable, so `Subject` serves as a dict key. `RepairPlan` is a
  frozen dataclass of plain dicts and lists.
- **Ids.** Threads, edits, families and bindings have `int` ids the database assigns in insertion order. People are
  `int` ids of `identity.person` (`docs/identity.md`). Runs and scores are `UUID`s. Components are digests, typed as
  `str`. `at` is a `datetime` the database sets; nothing in the package reads it.
- **Latest wins.** A `Reader` returns rows in the order they were written and never picks the latest. The package
  takes the last row for a key as the one that holds, through `model.py:latest` and `About.of`, or by taking `[-1]`.
- **The person asking.** No function takes the person asking. Who sees, owns and collaborates on what are
  `chatddx.identity`'s rules, which the bench applies to what `threads.heads` and `threads.expecting` give
  (`docs/bench-api.md`, `Seen`). An owner is taken only as a key, by `threads.find`, and as the subject of the
  one-expectation rule, in `threads.check_expectation`.
- **Deleted subjects.** A subject is deleted when its `About.deleted` is true.
  - Skipped by `threads.find` (through `chatddx.identity.owns` when given an owner), `threads.check_expectation`,
    `threads.behind` and `families.stale_cases`.
  - Given with their `About`, for the caller to judge, by `threads.heads` and `threads.expecting`.
  - Ranked last by `titles.title_of`.
  - Included by `threads.history`, `threads.forks`, `threads.expectations_of`, `families.family_of`,
    `families.bindings`, `families.survey`, `families.plan_repair`, `language.language_of`, the titles of cases and
    `Catalog.containing`.

**Errors.**
- `LookupError`: a thread, edit or family that doesn't exist (`no thread with id <id>`, `no edit with id <id>`, `no
  family with id <id>`); a digest that isn't stored where one is required (`check_adoptable`, `check_language`);
  `picked` with several expectations to choose from.
- `ValueError`: a rule refused before writing (`check_threadable`, `check_based_on`, `check_expectation`,
  `check_varied`, `check_adoptable`, `plan_repair`, `check_language`, `check_entry`, `check_label`,
  `chatddx.factors.base.language_tag`), and `MovedOn`, from `check_head`.
- `pydantic.ValidationError`: a model that breaks its own rules (an `Entry` of the wrong shape, a `Subject` that isn't
  exactly one thing, a `Behind` with both or neither of `head` and `binding`), and `proposal` when the merged recipe
  isn't a valid `Recipe`. Rules written as validators raise `ValueError`, which pydantic wraps.
- `chatddx.factors.base.StructuralError`, a `ValueError`: `Reader.get` of a digest that isn't stored, `resolve` of a
  component of the wrong kind, and `proposal` when the merged document isn't a readable component.

## model.py

### Constants
- `THREAD_KINDS`: the 23 kinds that have threads, every component kind but `case` and `compilation`, `facts` among
  them. `0012` repeats them (`thread_kind_check`).
- `LANGUAGE_KINDS`: the 6 kinds with a language of their own: `chunk.instructions`, `chunk.few_shot`, `chunk.prompt`,
  `chunk.output`, `chunk.toolset` and `skeleton`. A translations chunk names the languages it translates into itself.
  `0012` repeats them (`language_kind_check`).
- `VARIED`: `^[1-9][0-9]{0,17}$`, an edit's id as a `varied` entry holds it. `0026` repeats it.
- `REPLACED`: `^(<the parts, RECIPE_PARTS, joined by |>)=(sha256:[0-9a-f]{64})?$`, a part and the chunk or engine it
  was set to, or nothing for a part taken out, as a `replaced` entry holds them. `RECIPE_PARTS` is the nine chunk
  parts, `CHUNK_PARTS`, then `model`. `0026` repeats it, and `src/chatddx/store/test/test_catalog.py` holds the
  database's to `RECIPE_PARTS`.
- `WITH`: `^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$`, a run's id as `str(UUID)` writes it, as a
  `with` entry holds it. `0026` repeats it.
- `MODEL_KINDS`: `("model.local", "model.remote")`, the kinds a `replaced` entry's model is stored as. Not
  re-exported.
- `Part`: `Literal["view", "resource"]`.
- `Labels`: `Mapping[tuple[Part, int], str]`, what a scorer edit calls its views and resources, by part and position.
- `Kept`: `Literal["created", "edited", "unchanged"]`, what `Catalog.keep` did.

### `class MovedOn(ValueError)`
An edit named a head that isn't the thread's head any more (`threads.check_head`).

### `class EntryField(StrEnum)`
`NAME`, `DESCRIPTION`, `TAG`, `OWNER`, `COLLABORATOR`, `DELETED`, `LANGUAGE`, `VARIED`, `REPLACED` and `WITH`, valued
as their lowercase names. `0012` repeats the first seven (`entry_field_check`), and `0026` all of them. `RUN_FIELDS`
are `VARIED`, `REPLACED` and `WITH`, the fields only a run takes.

### `class Thread`
A row of `catalog.thread`. Every field is required.
- `id: int`
- `kind: str`: one of `THREAD_KINDS`, held by `Catalog.create` and `0012`, not by the model.
- `forked_from: int | None`: the edit of the origin it was forked from.
- `by: int`: who created it.
- `at: datetime`

### `class Edit`
A row of `catalog.edit`, without its `kind` column. Every field is required.
- `id: int`
- `thread: int`
- `digest: str`: a component of the thread's kind.
- `compilation: str | None`: for a skeleton edit, the compilation that produced the skeleton.
- `based_on: int | None`: for an edit of a fork, the origin edit its changes were re-applied onto.
- `by: int`: who saved it.
- `at: datetime`

### `class Binding`
A row of `catalog.binding`. Every field is required.
- `id: int`
- `family: int`
- `vignette: Vignette`: the table's `source`, `source_id` and `fingerprint`.
- `by: int`
- `at: datetime`

### `class Subject`
What an entry is about. Exactly one field is set.
- `thread: int | None = None`
- `family: int | None = None`
- `run: UUID | None = None`
- `score: UUID | None = None`

Raises `ValueError("a subject is exactly one of a thread, a family, a run or a score")`, wrapped in `ValidationError`.

### `class Entry`
One thing said about a subject.
- `field: EntryField`
- `value: str | None = None`: the text, for the fields that hold one.
- `person: int | None = None`: the person, for `owner` and `collaborator`.
- `present: bool = True`: false to remove what the field holds, for the fields that can be removed.

The shape each field takes:
- `name`: a `value`, not empty; without `present`, no `value`, and the name is removed.
- `description`: a `value`, which may be empty; it can't be removed.
- `tag`: a `value`, not empty, also without `present`, which removes that tag.
- `owner`: a `person`; it can't be removed.
- `collaborator`: a `person`; without `present`, that person is removed.
- `deleted`: neither; without `present`, the subject is restored.
- `language`: a `value` that is a language tag; it can't be removed.
- `varied`: a `value` that `VARIED` matches, an edit's id; it can't be removed.
- `replaced`: a `value` that `REPLACED` matches, `PART=DIGEST`, or `PART=` for a part taken out; it can't be removed,
  only replaced by another about the same part.
- `with`: a `value` that `WITH` matches, a run's id; it can't be removed.

Raises, wrapped in `ValidationError`:
- `ValueError("wrong value or person for <field>")`
- `ValueError("<field> can't be removed, only replaced")`
- `ValueError("<field> can't be empty")`
- `language_tag`'s `ValueError`.
- `ValueError("'<value>' is not an edit's id")`, for `varied`.
- `ValueError("'<value>' is not PART=DIGEST, or PART= for a part taken out")`, for `replaced`.
- `ValueError("'<value>' is not a run's id")`, for `with`.

#### `Entry.varied(edit: int) -> Self`, `Entry.replaced(part: str, digest: str | None) -> Self` and `Entry.started_with(run: UUID) -> Self`
A `varied` entry naming the edit, a `replaced` entry setting the part to the digest, or taking it out for `None`, and
a `with` entry naming the first run of the start a run is one of. The model doesn't know its subject:
`language.check_entry` refuses a `language` entry on anything but a family, and `threads.check_varied` a `varied`,
`replaced` or `with` entry on anything but a run. `0012` repeats the shapes (`entry_shape_check`) and the family rule
(`entry_language_check`); `0026` the shapes again, and the run rule (`entry_run_check`).

### `class About`
What a subject's entries say now. It is a `chatddx.identity.Owned`, by its `owner`, `collaborators` and `deleted`.
- `name: str | None = None`
- `description: str | None = None`
- `tags: frozenset[str] = frozenset()`
- `owner: int | None = None`
- `collaborators: frozenset[int] = frozenset()`
- `deleted: bool = False`
- `language: str | None = None`
- `varied: int | None = None`: for a run, the configuration's edit its variation was built on.
- `replaced: dict[str, str | None] = {}`: for a run, each part replaced over it, the chunk's or the model's digest,
  or `None` for a part taken out, in `RECIPE_PARTS` order.
- `started_with: UUID | None = None`: for a run, the first run of the start it is one of; `None` for the first, and
  for a run started alone.

#### `About.of(entries: Iterable[Entry]) -> Self`
The entries folded in the order given. For `name`, `description`, `owner`, `deleted`, `language`, `varied` and `with`
the last entry wins. For `tag` and `collaborator` the last entry about each member wins, and for `replaced` the last
about each part. No entries give `About()`.

### `latest[K, V](rows: Iterable[tuple[K, V]]) -> dict[K, V]`
For each key, the value of its last row. A key keeps the position of its first row.

### `check_label(scorer: Scorer, part: Part, position: int) -> None`
- Raises `ValueError("<scorer digest> has no <part> at position <position>")` unless the scorer has a view or a
  resource there. `0018` repeats it for the scorer of the label's edit.

### `class Divergence`
What `threads.divergence` returns: a fork compared with its base.
- `base: Edit`: the origin edit the fork is compared with.
- `origin_head: Edit`: the origin's head now.
- `varies: dict[str, tuple[JsonValue, JsonValue]]`: path → (value at the base, value at the fork's head), for the
  paths that differ, sorted by path. `None` stands for a missing field as well as a null one.
- `moved: bool` (property): whether the origin's head is past the base.

### `class Behind`
One reference of a thread's head that could be updated. Exactly one of `head` and `binding` is set.
- `path: str`: where the reference is, from the head, such as `/skeleton`, `/recipe/output` or
  `/cases/0/appendices/0`.
- `digest: str`: what the head references there.
- `head: Edit | None = None`: the head of a thread that held `digest` and has moved on.
- `binding: Binding | None = None`: the current binding of the family of a case that is behind it.
- `replacement: str | None = None`: the case `digest` becomes under `binding`, set exactly when `binding` is.

Raises, wrapped in `ValidationError`:
- `ValueError("behind either a newer head or a newer binding")`
- `ValueError("a replacement case goes with a newer binding, and only with it")`

### `class Survey`
What `families.survey` returns. Every field defaults to `()`.
- `unchanged: tuple[int, ...]`: families whose id and content are listed as bound.
- `changed: tuple[tuple[int, str, Fingerprint], ...]`: (family, id, new fingerprint), the same id with new content.
- `renamed: tuple[tuple[int, str, str], ...]`: (family, old id, new id), the same content under a new id.
- `new: tuple[str, ...]`: listed ids that match no family.
- `gone: tuple[int, ...]`: families none of whose ids or contents are listed.

### `class Repair`
What `Catalog.repair` wrote.
- `binding: Binding`: the new one.
- `cases: dict[str, str]`: old case digest → rebound case digest.
- `appendices: dict[str, str]`: old appendix digest → rebound appendix digest.
- `edits: tuple[Edit, ...]`: in the order of `RepairPlan.moves`.

## read.py

### `class Reader(Protocol)`
What the rules read. Lists come back in the order the rows were written, components by digest.
`src/chatddx/store/catalog.py:Rows` implements it over the tables, and `test/memory.py:Memory` over a `Registry` and
lists.
- `get(digest: str) -> Component`: the stored component. `StructuralError` when it isn't stored.
- `components(digests: Collection[str]) -> list[tuple[str, Component]]`: those of the digests that are stored.
- `kind(digest: str) -> str | None`: its kind, or `None` when it isn't stored.
- `compilations(skeleton: str) -> list[Compilation]`: the stored compilations of this skeleton.
- `thread(id: int) -> Thread | None`
- `threads(kind: str) -> list[Thread]`: the threads of a kind.
- `threads_forked_from(edits: Collection[int]) -> list[Thread]`: the threads forked from one of the edits.
- `edit(id: int) -> Edit | None`
- `edits(threads: Collection[int]) -> list[Edit]`: the edits of these threads.
- `edits_holding(digests: Collection[str]) -> list[Edit]`: the edits, in any thread, of one of these digests.
- `entries(subjects: Collection[Subject]) -> list[tuple[Subject, Entry, int]]`: the entries about these subjects,
  each with the person who wrote it.
- `bindings(families: Collection[int]) -> list[Binding]`: the families' bindings; none for an unknown family.
- `families() -> list[int]`: every family's id.
- `bindings_in(source: str) -> list[Binding]`: every binding in a source.
- `bindings_sharing(vignette: Vignette) -> list[Binding]`: the bindings in the vignette's source to its id or its
  fingerprint.
- `bound_to(vignettes: Collection[Vignette], kind: str) -> list[tuple[str, Vignette]]`: the stored components of
  `kind`, `case` or `appendix`, bound to one of these vignettes, each with it.
- `expectations(cases: Collection[str]) -> list[str]`: the stored expectations of these cases.
- `languages(digests: Collection[str]) -> list[tuple[str, str]]`: (digest, language) rows for these digests.
- `labels(edits: Collection[int]) -> list[tuple[int, Part, int, str]]`: (edit, part, position, label) rows for these
  edits.

### `heads_of(rows: Reader, threads: Collection[int]) -> dict[int, Edit]`
Thread → its latest edit, by thread id. Threads without edits are left out.

### `holders(rows: Reader, digests: Collection[str]) -> dict[int, Edit]`
`heads_of` every thread with an edit, current or earlier, of one of the digests.

### `heads_holding(rows: Reader, digests: Collection[str]) -> dict[int, Edit]`
The `holders` whose head is one of the digests.

### `abouts(rows: Reader, subjects: Collection[Subject]) -> dict[Subject, About]`
`About.of` each subject's entries. Every subject given is a key.

### `about(rows: Reader, subject: Subject) -> About`
`abouts` of one subject.

### `labels(rows: Reader, edit: int) -> Labels`
The edit's labels, by (part, position); `{}` for an edit without any.

### `tags_given(rows: Reader, subject: Subject) -> dict[str, int]`
The tags that hold on the subject, each with the writer of the latest entry about it.

## threads.py

### `check_threadable(kind: str) -> None`
- Raises `ValueError("<kind> components have no threads")` for a kind not in `THREAD_KINDS`.

### `check_based_on(rows: Reader, thread: int, based_on: int) -> None`
- Raises `ValueError("edit <based_on> is not in the origin of thread <thread>")` unless the thread is a fork and
  `based_on` is an edit of its origin at or after `forked_from`. `0012` repeats it (`catalog.check_based_on`).

### `check_head(rows: Reader, thread: int, head: int) -> None`
- Raises `MovedOn("thread <thread> has moved on since edit <head>: its head is edit <current>")` when `head` isn't the
  thread's head, and `history`'s `LookupError`. The database doesn't repeat it; `Catalog.edit` takes the thread's lock
  first.

### `check_labels(rows: Reader, thread_id: int, digest: str, labels: Labels) -> None`
Nothing for no labels.
- Raises `ValueError("a <kind> has no views or resources to label")` for a thread that isn't a scorer's.
- Raises `check_label`'s `ValueError` for a position the scorer at `digest` hasn't.
- Raises `ValueError("the label of <part> <position> is empty")`.

### `check_varied(rows: Reader, subject: Subject, entry: Entry) -> None`
Nothing for an entry of another field than `RUN_FIELDS`. `0026` repeats it (`entry_run_check`,
`catalog.check_varied`).
- Raises `ValueError("a <field> entry is about a run, and what it ran")` for a subject that isn't a run.
- Raises `ValueError("edit <id> is no configuration's")` for a `varied` entry naming an edit that isn't a skeleton
  thread's, or none.
- Raises `ValueError("<digest> isn't a chunk of <part> in the store")` for a `replaced` entry whose chunk isn't stored
  as that part's kind, and `ValueError("<digest> isn't an model in the store")` for a `model` one whose digest isn't
  stored a `model.local` or `model.remote`.
- A `with` entry is checked no further: runs are the ledger's, which the catalog doesn't read, so `0026` alone checks
  that it names a run that has started (`catalog.check_varied()`).

### `thread(rows: Reader, id: int) -> Thread`
- Raises `LookupError("no thread with id <id>")`.

### `edit(rows: Reader, id: int) -> Edit`
- Raises `LookupError("no edit with id <id>")`.

### `history(rows: Reader, thread: int) -> list[Edit]`
The thread's edits, by id, deleted or not.
- Raises `LookupError("no thread with id <thread>")` when it has none, which covers a thread that doesn't exist.

### `head(rows: Reader, thread: int) -> Edit`
The last of `history`.

### `heads(rows: Reader, kind: str) -> list[tuple[Edit, About]]`
The head and `About` of each thread of `kind`, deleted ones included, in thread id order. Threads without edits are
left out; an unknown kind gives `[]`.

### `find(rows: Reader, kind: str, name: str, *, owner: int | None = None) -> list[int]`
The ids of the live threads of `kind` named exactly `name`, in thread id order. Names aren't unique, so it may give
several.
- `owner`: only those this person `chatddx.identity.owns`.

### `recipe(rows: Reader, edit: Edit) -> Recipe | None`
The recipe of the edit's compilation, or `None` when it names none.

### `holds(rows: Reader, edit: Edit, digest: str, compilation: str | None) -> bool`
Whether `edit` holds `digest` with `compilation`'s recipe: it holds `digest`, and `compilation` is `None`, the edit's
own, or a compilation of the recipe the edit's holds, by other code or against other facts.

### `expecting(rows: Reader, cases: Sequence[str], schema: str) -> dict[str, list[tuple[Edit, About]]]`
For each case, the head and `About` of each thread whose head is an expectation of that case under `schema`, whoever
owns it, deleted ones included, in thread id order. Every case given is a key, with `[]` for none.

### `picked(case: str, choices: Mapping[int, str]) -> str | None`
The one head digest among a case's choices, thread → head digest, or `None` for none. Threads with the same head count
as one choice. The bench gives it the threads a person may be scored against (`docs/bench-api.md`,
`Seen.expectation_choices`).
- Raises `LookupError("case <case> has expectations to choose from, in threads <t1>, <t2>, …")`.

### `check_expectation(rows: Reader, thread: int, digest: str | None = None, entry: Entry | None = None) -> None`
Refuses what would leave a person owning two live expectation threads of one case under one expectation schema.
- `digest`: the head the thread would have; its head now when not given.
- `entry`: an entry about to be written about the thread; only `owner` and `deleted` entries are checked.

Only expectation threads are checked, and one without an owner, or deleted, passes.
- Raises `ValueError("person <owner> owns an expectation of case <case> under that schema already, in thread <t>")`,
  naming the first.

### `forks(rows: Reader, thread: int) -> list[int]`
The ids of the threads forked from any edit of `thread`, deleted or not. Direct forks only; an unknown thread gives
`[]`.

### `origin(rows: Reader, id: int) -> int | None`
The id of the thread `id` was forked from, or `None` for one that isn't a fork.
- Raises `thread`'s `LookupError`.

### `expectations_of(rows: Reader, case: str) -> list[int]`
The ids, sorted, of the threads whose head is an expectation of `case`, deleted or not.

### `behind(rows: Reader, thread: int) -> list[Behind]`
The references of the thread's head that could be updated, by path; within a path, the newer heads in thread id order,
then a newer binding. One level only: a reference's own references aren't followed, but a case's are.

The references looked at:
- the head's own (`Component.refs()`), such as `/skeleton`, `/engine` and `/cases/0`;
- the recipe of the compilation the head names, under `/recipe`, its model as `/recipe/model`;
- the facts that compilation names, as `/facts`;
- each case's appendices, under the case's path, such as `/cases/0/appendices/0`.

What is behind:
- A reference held earlier by a live thread whose head is now another digest: a `Behind` with that `head`, one per
  thread that moved on. For `/facts`, only when the head's recipe compiled against that head gives another skeleton
  than the head's, or doesn't compile (`_sends_else`).
- A case of a live family with a newer binding: a `Behind` with that `binding` and the `replacement`
  (`families.stale_cases`). The replacement may not be stored.

Raises `history`'s `LookupError` for a thread without edits.

### `divergence(rows: Reader, id: int) -> Divergence | None`
What a fork varies from its base, or `None` for a thread that isn't a fork. The base is the edit of the fork's latest
`based_on`, else its `forked_from`.
- When the base and the fork's head both name a compilation, their recipes are compared field by field, as
  `/recipe/<field>`.
- Otherwise their canonical documents are compared field by field, without `kind` and `v`, as `/<field>`.

Raises `LookupError` for a thread that doesn't exist, or a fork without edits.

### `proposal(rows: Reader, id: int) -> Recipe | Component | None`
The origin's head with the fork's changes on top, or `None` when `divergence` gives none or one that hasn't `moved`.
Nothing is stored.
- Compared by recipe: a `Recipe` to compile; `None` when the origin's head names no compilation.
- Otherwise: the component, its varied fields set to the fork's values and removed where the fork has none.

Raises `ValidationError` for an invalid recipe or component, and `StructuralError` for a document that isn't a
readable component.

## families.py

### `class RepairPlan`
A frozen dataclass: what `plan_repair` decided, for `Catalog.repair` to write.
- `vignette: Vignette`: the new binding's.
- `registry: Registry`: every rebuilt case, appendix and expectation, and the expectation schemas those reference.
- `cases: dict[str, str]`: old case digest → rebound case digest.
- `appendices: dict[str, str]`: old appendix digest → rebound appendix digest.
- `moves: list[tuple[int, str]]`: (thread, digest), the edits to write.

### `bindings(rows: Reader, family: int) -> list[Binding]`
The family's bindings, by id; the last is the current one.
- Raises `LookupError("no family with id <family>")` when it has none, which covers a family that doesn't exist.

### `family_of(rows: Reader, case: str) -> int | None`
The family of the latest binding equal to the case's vignette, earlier bindings included, so that a case from before a
repair keeps its family. `None` for a case that isn't stored, or one no binding matches. Deleted families included.

### `holder(rows: Reader, vignette: Vignette, *, but: int | None = None) -> tuple[int, bool] | None`
The lowest family, other than `but`, whose current binding in the vignette's source has its id or its fingerprint,
with `True` when it is the id. `None` when there is none.

### `check_adoptable(rows: Reader, case: str, *, by_content: bool = True) -> Vignette`
The case's vignette, when it can be adopted into a new family. `Catalog.adopt` calls it only after `family_of` found
none.
- `by_content`: whether another family's content counts. False for a source whose texts never move, where the same
  text typed twice is two vignettes.

Raises:
- `LookupError("<case> is not a stored case")`
- `ValueError("<case> gives family <n>'s vignette new content; rebind the family")` when `holder` finds its id.
- `ValueError("<case> gives family <n>'s vignette a new name; rebind the family")` when `holder` finds its content.

### `survey(rows: Reader, source: str, listing: Mapping[str, Fingerprint]) -> Survey`
`listing`, id → fingerprint, sorted into a `Survey` against the current bindings of the families in `source`, deleted
or not. Each listed id, in sorted order, is:
- `unchanged` or `changed`, when a family is bound to that id;
- else `renamed`, when exactly one family is bound to that fingerprint under an id that isn't listed;
- else `new`.

The families none of them took are `gone`, by family id. A vignette whose id and content both changed is `gone` plus
`new`.

### `rebind_appendix(appendix: Appendix, vignette: Vignette) -> Appendix`
The same text, bound to `vignette`.

### `rebind_case(case: Case, vignette: Vignette, get: Resolver) -> tuple[Case, dict[str, Appendix]]`
The case with `vignette` and each appendix rebound, in the same order, and old appendix digest → rebound appendix.

### `plan_repair(rows: Reader, family: int, *, id: str | None = None, fingerprint: Fingerprint | None = None) -> RepairPlan`
The family's current vignette moved to a new id or new content in the same source. Deleted threads are moved too.
- `id`, `fingerprint`: the new vignette's; the current one's when not given. Exactly one must change.

It plans:
- every stored case of the current vignette, rebound;
- a move for each thread whose head is an appendix of the current vignette, to the rebound appendix;
- when the id changes, a move for each thread whose head is an expectation of one of those cases, to the same
  expectation of the rebound case.

Cases and appendices of an earlier binding aren't rebuilt. Raises:
- `LookupError("no family with id <family>")`
- `ValueError("a repair changes exactly one of the id or the fingerprint")`
- `ValueError("family <n> already has the id '<id>'")` or `ValueError("family <n> already has that content")`, when
  `holder(…, but=family)` finds another family there.

`0012` checks that a new binding keeps the source, and the id or the fingerprint (`catalog.check_binding`).

### `stale_cases(rows: Reader, refs: list[tuple[str, str]]) -> list[Behind]`
For each (path, digest) in `refs` that is a case of a live family whose current binding isn't the case's vignette, a
`Behind` with that `binding` and the `replacement`, in `refs` order. `threads.behind` calls it.

## language.py

### `own(rows: Reader, digest: str) -> str | None`
The latest language recorded for the digest itself, or `None`.

### `language_of(rows: Reader, digest: str) -> str | None`
The digest's language, by its kind; `None` for a digest that isn't stored.
- `case`: its family's `About.language`, or `None` without a family.
- `expectation`: its case's.
- `trial`, `judge`: its skeleton's.
- `skeleton` with compilations: the language every compilation with one agrees on, its `into`, or for one as written
  the language its recipe votes for; else `None`.
- anything else, a skeleton without compilations included: `own`.

A recipe votes for the `own` language every text-bearing part shares (the keys of `chatddx.factors.request.texts`,
`toolset` included and `appendix_layout` not). A part without a language, or parts that disagree, cast no vote. Its
translations don't vote.

### `languages_of(rows: Reader, digests: Collection[str]) -> dict[str, str | None]`
`language_of` of each digest, reading what they need once for them all.

### `edit_languages(rows: Reader, edits: Collection[Edit]) -> dict[int, str | None]`
Each edit's language, by its id: its compilation's `into`, or for one as written the language its recipe votes for,
when it names one, else `languages_of` its digest, reading what they need once for them all.

### `recipe_language(rows: Reader, recipe: Recipe) -> str | None`
The language `recipe` votes for, or `None` when it casts no vote.

### `check_language(rows: Reader, digest: str, value: str) -> str`
The digest's kind, for the row. Raises, in this order:
- `LookupError("<digest> is not in the store")`
- `ValueError("<kind> components have no language of their own")` for a kind not in `LANGUAGE_KINDS`.
- `ValueError("<digest>: a compiled skeleton's language comes from its recipe")` for a skeleton with a compilation.
- `language_tag`'s `ValueError`.

`0012` repeats it (`language_value_check`, `language_kind_check`, `catalog.check_language`).

### `check_entry(subject: Subject, entry: Entry) -> None`
- Raises `ValueError("a language entry is for a family's vignette; a component's language is kept on its digest")`
  for a `language` entry on anything but a family. `0012` repeats it (`entry_language_check`).

## titles.py

### `type Title = Callable[[str], str]`
Digest → title. Descriptions call it for the digests they mention; `title` and `title_of` pass `partial(title_of,
rows)`.

### `short(digest: str) -> str`
The first 6 hex digits.

### `snippet(text: str, limit: int = 40) -> str`
The text with its whitespace collapsed, in double quotes, cut at the last space within `limit + 1` characters and
followed by `…` when it is longer than `limit`.

### `describe_case(root: str, appendices: Iterable[str], title: Title) -> str`
`<root> with <the appendices' titles, joined by ", ">`, or `root` without appendices.

### `describe_recipe(recipe: Recipe, title: Title) -> str`
The titles of the recipe's parts that are set, in recipe order, so the model last, joined by ` · `, after `judge: `
for a judge's. `appendix_layout` isn't shown.

### `describe_change(path: str, after: JsonValue, title: Title) -> str`
The path's key, without `/recipe/` or `/`, then `no <key>` for `None`, `<key>: <title>` for a digest,
`<key>: <snippet>` for other text, and `<key>: <JSON>` for anything else.

### `describe(component: Component, title: Title) -> str`
What a component holds, by its kind.
- `chunk.instructions`, `chunk.prompt`, `appendix`: a `snippet` of its text, slots and inserts as `{name}`.
- `chunk.few_shot`: `few-shot, <n> message(s)`.
- `chunk.output`: `native output`, `text output` or `tool <name> output`, then `: <schema title>` or
  `: <property names>` when its schema has one.
- `chunk.sampling`: the values that are set, such as `temperature 0.2, top_p 0.9`, or `default sampling`; a
  recommended one is `recommended sampling`, then the values it sets, such as `recommended sampling, max_output_tokens
  512`.
- `chunk.reasoning`: for a level, `reasoning <level>`, or `default reasoning` for `default`, then `, budget <n>` when
  it has a budget; otherwise `effort <e>`, each chat template kwarg as `<key> <JSON>`, and `budget <n>`, joined by
  `, `; or `default reasoning`.
  `default reasoning`.
- `chunk.passthrough`: `passthrough: <keys>`.
- `chunk.translations`: `translations into <its languages, sorted, joined by ", ">, <n> text(s)`, `n` the most texts
  one language has.
- `chunk.toolset`: `with <each tool's title>`.
- `tool`: its name.
- `skeleton`: `<purpose> configuration <short>`.
- `trial`: `<skeleton's title> on <engine's title>, <n> case(s), <n> seed(s)`.
- `judge`: `judge <skeleton's title> on <engine's title>`.
- `scorer`: `scorer <entry point> v<version>`.
- `scoring`: `<scorer's title> against <n> expectation(s)`.
- `expectation`: `expectation for <case's title>`.
- `case`: `describe_case("<source>/<id>", …)`.
- `model`: its repository.
- `engine.local`: `<model's title> on <server> <version> (<gpu>)`.
- `engine.remote`: `<model> from <provider>`.
- `facts`: `facts about <model>`.
- `expectation_schema`: its schema's title or property names, else `expectation schema <short>`.
- `canary_set`: `<n> canary` or `<n> canaries`.
- anything else: `<kind> <short>`.

### `title(rows: Reader, thread: int) -> str`
The first of:
1. the thread's name;
2. for a fork, its origin's `title` and `describe_change` of each path it varies, joined by `, `, such as
   `plan, output: management-plan-shown`; `a fork of <origin's title>` when it varies nothing;
3. what its head holds: for a skeleton, `describe_recipe` of the compilation the head names, else of the first stored
   compilation of it; otherwise, or without one, `describe`.

Raises `LookupError` for an unnamed thread that doesn't exist or has no edits.

### `title_of(rows: Reader, digest: str) -> str`
A case's title is its family's name, else its current binding's `<source>/<id>`, followed by ` (earlier)` when the case
is of an earlier binding, then its appendices (`describe_case`); a case without a family is `describe`d. For anything
else, among the threads that held the digest, live ones first, then deleted ones, each by thread id:
1. the name of a thread whose head it is;
2. the `title` of a thread whose head it is;
3. `<name> (earlier)` of a thread with a name.

Without such a thread, what it holds, as `title`'s step 3. Raises `StructuralError` for a digest that isn't stored.

## The store's Catalog
`src/chatddx/store/catalog.py:Catalog(conn: Connection)` is what callers use. It reads through `Rows` and calls this
package; its writes insert the rows the package decided on. A rule the database also checks is refused by Postgres
with a psycopg error when the Python lets it through.

Reads, each the package function of that name, or the one given, over `Rows`:
- `thread`, `history`, `head`, `heads`, `find`, `expecting`, `forks`, `origin`, `expectations_of`, `behind`,
  `divergence`, `proposal`: `threads`.
- `recipe(thread)`: `threads.recipe` of the thread's head.
- `containing(digest) -> list[Edit]`: `Reader.edits_holding([digest])`.
- `title(thread)`, `title_of(digest)`: `titles`.
- `language_of(digest)`, `languages_of(digests)`, `edit_languages(edits)`, `recipe_language(recipe)`: `language`.
- `family(case)`: `families.family_of`.
- `bindings(family)`, `survey(source, listing)`: `families`.
- `about(subject)`, `abouts(subjects)`, `tags_given(subject)`: `read`.
- `labels(edit) -> dict[tuple[Part, int], str]`: `read.labels`.

### `create(digest: str, by: int, *, compilation: str | None = None, forked_from: int | None = None, name: str | None = None, owner: int | None = None, labels: Labels | None = None) -> Edit`
A new thread with its first edit, an `owner` entry, and a `name` entry when `name` is given, in one transaction.
- `owner`: who owns it; `by` when not given.

Raises:
- `LookupError("<digest> is not in the store")`
- `threads.check_threadable`'s, and `edit`'s and `note`'s.

### `edit(thread: int, digest: str, by: int, *, compilation: str | None = None, based_on: int | None = None, head: int | None = None, labels: Labels | None = None) -> Edit`
A new edit of the thread, with a label row for each label, in one transaction under the thread's lock.
- `head`: the head the edit was made on, which must still be the thread's.
- `based_on`: for a fork following its origin, the origin edit its changes were re-applied onto.

Raises:
- `threads.check_head`'s `MovedOn`, `threads.check_based_on`'s, `threads.check_expectation`'s and
  `threads.check_labels`'s.
- `LookupError("no thread with id <thread>")`

### `keep(digest: str, by: int, thread: int | None, *, name: str | None = None, compilation: str | None = None, forked_from: int | None = None, head: int | None = None, labels: Labels | None = None) -> tuple[Edit, Kept]`
- `thread` `None`: `create`, `created`.

- Else, under the thread's lock: the head, `unchanged`, when `threads.holds(head, digest, compilation)` and
  `labels`, when given, are the head's; else `edit`, `edited`.

Raises `create`'s or `edit`'s.

### `adopt(case: str, by: int, *, owner: int | None = None, by_content: bool = True) -> int`
The case's family: the one `families.family_of` finds, else a new one with its binding and an `owner` entry, in one
transaction.
- `owner`: who owns a new family; `by` when not given.
- `by_content`: as `families.check_adoptable` takes it.

Raises `families.check_adoptable`'s.

### `repair(family: int, by: int, *, id: str | None = None, fingerprint: Fingerprint | None = None) -> Repair`
`families.plan_repair`, written in one transaction: the new binding, the plan's registry, and an edit per move.
- Raises `families.plan_repair`'s.

### `note(subject: Subject, entry: Entry, by: int) -> None`
The entry, about the subject. A run's or a score's has to have started.
- Raises `language.check_entry`'s, `threads.check_varied`'s, and, for a thread, `threads.check_expectation`'s.

### `language(digest: str, value: str, by: int) -> None`
A `catalog.language` row for the digest.
- Raises `language.check_language`'s.

### `involving(person: int) -> list[Subject]`
The subjects whose `owner` or `collaborator` entries ever named the person.

### `runs_started(person: int, since: datetime) -> int`
How many runs' `owner` entries name the person since `since`.

## Database: schema `catalog`
Created by `0010-t0-catalog.sql`, its roles in `0011-t1-catalog.sql`, and its rules and insert-only triggers in
`0012-t2-catalog.sql` (`docs/migrations.md`, "catalog"). Every table has:
- `id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY`; "latest" is the highest id;
- `by bigint NOT NULL`, a foreign key to `identity.person`;
- `at timestamptz NOT NULL DEFAULT now()`.

`0010` also adds `UNIQUE (digest, kind)` on `factor.component` and `UNIQUE (src, path, dst)` on
`factor.component_ref`, as targets of the composite foreign keys.

### `catalog.thread`
`Thread` rows. `UNIQUE (id, kind)`, as the target of `edit`'s foreign key.
- `kind text NOT NULL`: one of `THREAD_KINDS` (`thread_kind_check`, 0012).
- `forked_from bigint`: `(forked_from, kind)` references `edit (id, kind)`.

### `catalog.edit`
`Edit` rows. `UNIQUE (id, kind)`; indexes `edit_thread (thread, id)` and `edit_digest (digest)`.
- `thread bigint NOT NULL`: `(thread, kind)` references `thread (id, kind)`.
- `kind text NOT NULL`: the thread's kind, which `Catalog.edit` copies.
- `digest text NOT NULL`: `(digest, kind)` references `factor.component (digest, kind)`.
- `compilation text`: `(compilation, compilation_kind)` references `factor.component (digest, kind)`, and
  `(compilation, compilation_path, digest)` references `factor.component_ref (src, path, dst)`. Only on a skeleton
  edit (CHECK `compilation IS NULL OR kind = 'skeleton'`).
- `compilation_kind text NOT NULL`: always `'compilation'`.
- `compilation_path text NOT NULL`: always `'/skeleton'`.
- `based_on bigint`: `(based_on, kind)` references `edit (id, kind)`.
- Trigger `edit_based_on` (0012): `catalog.check_based_on()` raises `edit <based_on> is not in the origin of thread
  <thread>`, as `threads.check_based_on` does.

So an edit holds a stored component of its thread's kind, a fork starts from an edit of its own kind, `based_on` is an
edit of the origin at or after the fork, and a compilation is named only by a skeleton edit, and is one whose
`/skeleton` is the edit's digest.

### `catalog.family`
No columns but `id`, `by` and `at`.

### `catalog.binding`
`Binding` rows. Indexes `binding_family (family, id)`, `binding_source (source, source_id)` and `binding_content
(source, fingerprint)` (0013).
- `family bigint NOT NULL`: references `family`.
- `source text NOT NULL`: `vignette.source`.
- `source_id text NOT NULL`: `vignette.id`.
- `fingerprint jsonb NOT NULL`: `vignette.fingerprint`, as canonical JSON.
- Trigger `binding_anchor` (0012): `catalog.check_binding()` raises `family <n>: a new binding must keep the source,
  and the id or the fingerprint` unless the new binding has the previous one's source, and its `source_id` or its
  `fingerprint`.

### `catalog.entry`
`(Subject, Entry)` rows. Partial indexes on `thread`, `family`, `run` and `score`.
- `thread bigint`: references `thread`.
- `family bigint`: references `family`.
- `run uuid`, with `run_stage text`, always `'started'` with a run: `(run, run_stage)` references `ledger.run_stage`.
- `score uuid`, with `score_stage text`, always `'started'` with a score: `(score, score_stage)` references
  `ledger.score_stage`.
- `field text NOT NULL`: one of `EntryField` (`entry_field_check`, 0012, and again with `varied`, `replaced` and
  `with`, 0026).
- `value text`
- `person bigint`: references `identity.person`.
- `present boolean NOT NULL DEFAULT true`

Checks:
- `num_nonnulls(thread, family, run, score) = 1`, and a stage exactly with its run or score (0010).
- `entry_shape_check` (0012): the shapes under `Entry`.
- `entry_shape_check` again (0026), with `varied`, `replaced` and `with`.
- `entry_run_check` (0026): `field NOT IN ('varied', 'replaced', 'with') OR run IS NOT NULL`.
- Constraint trigger `entry_varied` (0026), after the row's checks: `catalog.check_varied()` raises `edit <id> is no
  configuration's` for a `varied` entry naming no skeleton edit, and `<digest> isn't a stored <part>` for a `replaced`
  entry whose chunk isn't stored as that part's kind, or whose engine isn't stored as `engine.local` or
  `engine.remote`, as `threads.check_varied` does; and `run <id> hasn't started` for a `with` entry naming no run with
  a started row in `ledger.run_stage`, which `threads.check_varied` leaves to it.
- `entry_language_check` (0012): `field <> 'language' OR family IS NOT NULL`.

### `catalog.label`
Scorer labels, each written with an edit of a scorer thread (0017). `UNIQUE (edit, part, position)`.
- `edit bigint NOT NULL`: `(edit, kind)` references `catalog.edit (id, kind)`.
- `kind text NOT NULL`: always `'scorer'`.
- `part text NOT NULL`: a `Part`.
- `position integer NOT NULL`: `>= 0`, among the scorer's views or resources.
- `value text NOT NULL`: the label, not empty.
- Trigger `label_position` (0018): `catalog.check_label()` raises `edit <edit>: its labels are written with it, by its
  writer` when `by` or `at` isn't the edit's, and `<digest>: no <part> at position <position>` past the end of the
  edit's scorer's views or resources. `0018` also puts the insert-only triggers back on the table.

### `catalog.language`
Languages kept on a component's digest. Index `language_digest (digest, id)`.
- `digest text NOT NULL`: `(digest, kind)` references `factor.component (digest, kind)`.
- `kind text NOT NULL`: one of `LANGUAGE_KINDS` (`language_kind_check`, 0012), as `check_language` gives it.
- `value text NOT NULL`: matches `chatddx.factors.base.LANGUAGE` (`language_value_check`, 0012).
- Trigger `language_compiled` (0012): `catalog.check_language()` raises `<digest>: a compiled skeleton's language
  comes from its recipe` when a stored compilation's `/skeleton` is the digest.

### Insert-only (0012)
On every table, the triggers `insert_only` (BEFORE UPDATE OR DELETE) and `insert_only_truncate` (BEFORE TRUNCATE) call
`factor.refuse_change()`, which raises `<schema>.<table> is insert-only`.

### Roles (0011)
PUBLIC loses all access. `chatddx_writer` gets `USAGE` and `SELECT, INSERT`, and `chatddx_reader` `USAGE` and
`SELECT`, on the tables there are and, through default privileges, on those made later. The catalog holds nothing made
from a vignette, so the reader may read all of it.

### What the database checks, and what it doesn't
It checks:
- thread kinds;
- that an edit holds a stored component of its thread's kind;
- where forks, `based_on` and compilations point (see `catalog.edit`);
- that an entry has exactly one subject, a run or score that has started, a known field and the right shape, a
  language only on a family, what a run varied only on a run, naming a configuration's edit and stored chunks and
  engines, and the run a run was started with only on a run, naming a run that has started;
- that a label names a view or resource its scorer has;
- that a family's bindings keep their source, and the id or the fingerprint;
- that languages are tags on components of `LANGUAGE_KINDS`, and not on a skeleton known to be compiled;
- that nothing changes.

It doesn't check:
- that a thread has an edit, or a family a binding (`Catalog.create` and `Catalog.adopt` write both in one
  transaction);
- that current bindings are unique across families (`adopt` and `repair` check it through `families.holder`);
- that a new binding differs from the previous one (`plan_repair` checks it);
- that a skeleton edit names its compilation when one exists;
- that a skeleton with a language row is compiled later;
- names, labels or descriptions beyond their shapes, or that a subject has an owner.

## Known gaps
From `docs/catalog.md`, "Open design issues", where they concern this API:
- The rules are checked in Python on rows read inside the writing transaction; with two writers at once only tier 2
  holds. Two `adopt` calls for one vignette at the same moment can create two families.
- Two vignettes with the same content under different ids in one source look like a rename: `adopt` refuses the
  second.
- When bindings of several families match a case, `family_of` takes the family of the latest matching binding.
- Current bindings are read per source, which relies on a family never changing source; tier 2 holds that.
- A thread without edits is possible in SQL.
- A skeleton edit may leave out its compilation.
- A language on a skeleton that is compiled later is ignored from then on.
- A case stored at a vignette's old place after a repair gets a replacement from `behind` that nothing has stored.
- When an entry, a label or a language was written isn't given, nor who wrote a label or a language:
  `Reader.entries` gives an entry's writer only.
- Why an edit was made isn't stored.
- Titles take a query for every reference they visit, are rebuilt from names that change, and aren't unique.
- Scorer labels aren't carried to the next edit of a scorer thread.
- An unnamed fork's title can pair two versions: when its origin has no name and has moved on, `title` describes the
  origin's current head but lists the changes from the base.

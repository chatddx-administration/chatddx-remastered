from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass, field
from types import EllipsisType
from typing import Literal
from uuid import UUID

from pydantic import JsonValue

from chatddx.catalog import (
    LANGUAGE_KINDS,
    About,
    Edit,
    Entry,
    EntryField,
    Kept,
    Subject,
    Variation,
    latest,
    variants_for,
)
from chatddx.catalog.threads import picked
from chatddx.catalog.titles import short
from chatddx.core.rig import rig
from chatddx.factors.base import (
    Component,
    Finding,
    StructuralError,
    iter_refs,
    resolve,
)
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Case, Vignette, prepare_case
from chatddx.factors.engine import LocalEngine, RemoteEngine
from chatddx.factors.kinds import BY_KIND
from chatddx.factors.request import (
    Compilation,
    Recipe,
    Skeleton,
    SlotName,
    compile_request,
    compiled,
    render,
)
from chatddx.factors.scoring import Expectation, Scorer, Scoring
from chatddx.factors.select import reaches
from chatddx.factors.trial import Trial
from chatddx.facts import Facts, lints, model_name
from chatddx.identity import Person, preferred
from chatddx.inventory import Inventory
from chatddx.ledger import ItemKey, Run, RunStarted, Score, fingerprint_request
from chatddx.runner.run import Runner, Running
from chatddx.runner.score import score_run
from chatddx.store import Catalog, People, Store
from chatddx.store.catalog import Rows
from chatddx.store.store import Connection

from .errors import Ambiguous, Conflict, NotFound
from .variation import PARTS, TriedVariation

# The kinds of thread each word names: a configuration is a skeleton thread, a part is a
# chunk of that part, and an engine is local or remote.
KINDS: dict[str, tuple[str, ...]] = {
    "configuration": ("skeleton",),
    **{part: (f"chunk.{part}",) for part in PARTS},
    "tool": ("tool",),
    "scorer": ("scorer",),
    "judge": ("judge",),
    "expectation_schema": ("expectation_schema",),
    "expectation": ("expectation",),
    "canary_set": ("canary_set",),
    "model": ("model",),
    "engine": ("engine.local", "engine.remote"),
}

# The kinds a person writes as components. A configuration is written as a variation.
WRITTEN: frozenset[str] = frozenset(
    {*(f"chunk.{part}" for part in PARTS), "expectation"}
)

COMPILED_LANGUAGE = "a compiled configuration's language comes from its recipe"

# What stands in for each slot in a request rendered to be looked at.
PLACEHOLDERS: dict[SlotName, str] = {
    "vignette": "‹vignette›",
    "appendices": "‹appendices›",
    "completion": "‹completion›",
    "expectation": "‹expectation›",
}


@dataclass(frozen=True)
class Family:
    id: int
    about: About
    case: str

    @property
    def name(self) -> str:
        return self.about.name or f"family {self.id}"


# What one view of a scorer gets from a variation's answers and the cases' expectations.
@dataclass(frozen=True)
class Reach:
    thread: int
    scorer: str
    view: int
    label: str
    offered: bool
    cases: int
    missing: list[Family]
    choosing: list[Family]

    @property
    def have(self) -> int:
        return self.cases - len(self.missing) - len(self.choosing)


# A run's score under one scorer, or why it couldn't be scored.
@dataclass(frozen=True)
class Graded:
    name: str
    scorer: Scorer
    labels: dict[int, str]
    score: Score | None = None
    findings: list[Finding] = field(default_factory=list[Finding])
    refused: str | None = None

    def label(self, view: int) -> str:
        return self.labels.get(view, f"view {view}")


@dataclass(frozen=True)
class Saved:
    name: str
    digest: str
    what: Literal["created", "a new version", "unchanged"]
    variation: TriedVariation


# What following a fork's origin would keep: the origin's head with the fork's changes on
# top, as a recipe or a component, and the digest it comes to, with the compilation that
# makes it for a recipe.
@dataclass(frozen=True)
class Proposed:
    variation: Variation
    proposal: Recipe | Component
    digest: str
    compilation: str | None


# What taking expectations for some cases did with each: by case, the thread the person
# took one into, their own thread left as it was, the shared threads of several owners
# to pick from, and the cases nothing shared has one for.
@dataclass(frozen=True)
class Taken:
    taken: dict[str, int]
    kept: dict[str, int]
    choosing: dict[str, list[int]]
    missing: list[str]


# A component kept in a thread of the person's own, and what the lints say of it.
@dataclass(frozen=True)
class Written:
    edit: Edit
    what: Literal["created", "a new version", "unchanged"]
    findings: list[Finding]


SAVED: dict[Kept, Literal["created", "a new version", "unchanged"]] = {
    "created": "created",
    "edited": "a new version",
    "unchanged": "unchanged",
}


# What one person sees and does: the threads, families and runs they see, the World's
# endpoints, and the variations they try and save. Nothing here is UI.
class Bench:
    def __init__(
        self, conn: Connection, person: Person, inventory: Inventory, facts: Facts
    ) -> None:
        self.conn: Connection = conn
        self.person: Person = person
        self.inventory: Inventory = inventory
        self.facts: Facts = facts
        self.store: Store = Store(conn)
        self.catalog: Catalog = Catalog(conn)
        self._rows: Rows = Rows(conn)
        self._people: People = People(conn)
        self._logins: dict[int, str] = {}
        self._models: dict[str, str | None] = {}

    def login(self, person: int | None) -> str:
        if person is None:
            return "nobody"
        if person not in self._logins:
            self._logins[person] = self._people.get(person).login
        return self._logins[person]

    def owner(self, about: About) -> str:
        return "" if about.owner == self.person.id else self.login(about.owner)

    # The heads of the live threads the person owns or collaborates on, of the kinds
    # `word` names.
    def threads(self, word: str) -> list[tuple[Edit, About]]:
        return [found for kind in KINDS[word] for found in self.visible(kind)]

    # The heads of the live threads of `kind` the person owns or collaborates on.
    def visible(self, kind: str) -> list[tuple[Edit, About]]:
        return self.catalog.visible(kind, self.person.id)

    def names(self, word: str) -> list[str]:
        return sorted({a.name for _, a in self.threads(word) if a.name is not None})

    # A thread by name, as `_named` finds it, or else its one variant `model` may use
    # (`chatddx.catalog.variants_for`). Returns it with the name that found it.
    def thread(
        self, word: str, name: str, model: str | None = None
    ) -> tuple[Edit, str]:
        seen = {kind: self.visible(kind) for kind in KINDS[word]}
        addresses = {
            kind: {
                address
                for _, a in found
                for address in (a.name, self._qualified(a.name, a.owner))
                if address is not None
            }
            for kind, found in seen.items()
        }
        every = set[str]().union(*addresses.values())
        if name not in every:
            match variants_for(name, every, model):
                case [one]:
                    name = one
                case []:
                    pass
                case several:
                    raise Ambiguous(
                        f"{word} {name!r} is made in more than one language: "
                        + f"{', '.join(several)}"
                    )
        kinds = [kind for kind, held in addresses.items() if name in held]
        match kinds:
            case [kind]:
                return self._named(
                    [(e, a.name, a) for e, a in seen[kind]], name, word
                ), name
            case []:
                said = f"no {word} {name!r} for {self.person.login}"
                if per_model := sorted(n for n in every if n.startswith(f"{name} (")):
                    said += f"; per model: {', '.join(per_model)}"
                raise NotFound(said, per_model if model is None else ())
            case _:
                raise Ambiguous(f"{word} {name!r} names a {' and a '.join(kinds)}")

    # A name as `OWNER/NAME`, by which it is found when nothing has the whole name.
    def _qualified(self, name: str | None, owner: int | None) -> str | None:
        if name is None or owner is None:
            return None
        return f"{self.login(owner)}/{name}"

    # The one of `seen` called `name`: the person's own, else the one shared with them.
    # A name is matched whole first, since names may hold a slash, as
    # `plan (Qwen/Qwen3-8B-AWQ)` does; only then as `OWNER/NAME`.
    def _named[T](
        self, seen: list[tuple[T, str | None, About]], name: str, word: str
    ) -> T:
        called = [(found, a.owner) for found, n, a in seen if n == name] or [
            (found, a.owner)
            for found, n, a in seen
            if self._qualified(n, a.owner) == name
        ]
        match preferred(self.person.id, called):
            case [one]:
                return one
            case []:
                raise NotFound(f"no {word} {name!r} for {self.person.login}")
            case several:
                raise Ambiguous(
                    f"{word} {name!r} names {len(several)}; name one as OWNER/NAME"
                )

    # The head of a thread the person sees, by its id, with what the catalog says of it;
    # with `word`, only of the kinds it names.
    # With `deleted`, the person's own deleted threads are found too.
    def thread_by_id(
        self, id: int, word: str | None = None, *, deleted: bool = False
    ) -> tuple[Edit, About]:
        about = self.about(id)
        thread = self._rows.thread(id)
        seen = about.shows(self.person.id) or (
            deleted and about.deleted and about.owner == self.person.id
        )
        if (
            thread is None
            or not seen
            or (word is not None and thread.kind not in KINDS[word])
        ):
            raise NotFound(f"no {word or 'thread'} {id} for {self.person.login}")
        return self.catalog.head(id), about

    # The heads of the person's own deleted threads of `kind`, as `visible` gives the
    # live ones they see.
    def deleted(self, kind: str) -> list[tuple[Edit, About]]:
        heads = self.catalog.heads(kind, deleted=True)
        known = self.catalog.abouts([Subject(thread=e.thread) for e in heads])
        return [
            (e, a)
            for e in heads
            if (a := known[Subject(thread=e.thread)]).owner == self.person.id
        ]

    def about(self, thread: int) -> About:
        return self.catalog.about(Subject(thread=thread))

    # A thread the person sees whose head is `digest`, their own first.
    def holder(self, word: str, digest: str) -> tuple[Edit, About] | None:
        held = [((e, a), a.owner) for e, a in self.threads(word) if e.digest == digest]
        return next(iter(preferred(self.person.id, held)), None)

    def get(self, digest: str) -> Component:
        return self.store.get(digest)

    def title(self, digest: str | None) -> str:
        return "—" if digest is None else self.catalog.title_of(digest)

    def model(self, engine: str) -> str | None:
        if engine not in self._models:
            registry = self.store.load([engine])
            self._models[engine] = model_name(registry.get(engine), registry)
        return self._models[engine]

    def endpoint(self, name: str) -> str:
        engine = self.inventory.endpoint(name).engine
        if self._rows.kind(engine) is None:
            raise NotFound(
                f"endpoint {name!r} serves engine {short(engine)}, which isn't in the "
                + "store: load its World with init-data"
            )
        return engine

    # A configuration by name, with nothing replaced yet; a per-model one is picked by
    # the model `engine` serves.
    def configuration(self, name: str, engine: str | None = None) -> TriedVariation:
        model = None if engine is None else self.model(engine)
        edit, found = self.thread("configuration", name, model)
        called = found.removeprefix(f"{self.person.login}/")
        return TriedVariation(edit, called, self.catalog.recipe(edit.thread))

    def chunk(self, part: str, name: str, engine: str | None = None) -> str:
        model = None if engine is None else self.model(engine)
        return self.thread(part, name, model)[0].digest

    # A configuration by its thread's id, with `parts` replaced: each by the chunk of
    # that digest, or taken out for None.
    def variation(
        self, configuration: int, parts: Mapping[str, str | None] | None = None
    ) -> TriedVariation:
        edit, about = self.thread_by_id(configuration, "configuration")
        name = about.name or self.catalog.title(configuration)
        found = TriedVariation(edit, name, self.catalog.recipe(configuration))
        for part, digest in (parts or {}).items():
            if part not in PARTS:
                raise ValueError(f"no part {part!r}: the parts are {', '.join(PARTS)}")
            if digest is not None and self._rows.kind(digest) not in KINDS[part]:
                raise ValueError(f"{digest} isn't a stored chunk of {part}")
            found = found.set(part, digest, self.title(digest))
        return found

    def skeleton(self, variation: TriedVariation) -> Skeleton:
        recipe = variation.varied
        if not variation.parts or recipe is None:
            return resolve(self.get, variation.configuration.digest, Skeleton)
        registry = self.store.load(s.digest for s in iter_refs(recipe))
        return compile_request(recipe, registry.get)

    # The model name a request to the engine carries.
    def served(self, engine: str) -> str:
        found = self.get(engine)
        if not isinstance(found, LocalEngine | RemoteEngine):
            raise StructuralError(f"{engine} is a {found.kind_name}, not an engine")
        return found.served_model_name

    # The request the variation renders on `engine`, with placeholders for the slots, and
    # for the model when there is no engine.
    def request(
        self, variation: TriedVariation, engine: str | None, seed: int
    ) -> dict[str, JsonValue]:
        model = "‹model›" if engine is None else self.served(engine)
        return render(
            self.skeleton(variation), model=model, seed=seed, fills=PLACEHOLDERS
        )

    def families(self, tags: Iterable[str] = ()) -> list[Family]:
        wanted = set(tags)
        tagged = [(f, a) for f, a in self._families() if not wanted or wanted & a.tags]
        cases = self._cases([f for f, _ in tagged])
        found = [
            Family(family, about, case)
            for family, about in tagged
            if (case := cases[family]) is not None
        ]
        return sorted(found, key=lambda f: f.name)

    def _families(self) -> list[tuple[int, About]]:
        return self.catalog.visible_families(self.person.id)

    # A family's case is the one its vignette makes alone, else the first holding it.
    def _cases(self, families: list[int]) -> dict[int, str | None]:
        current = latest((b.family, b.vignette) for b in self._rows.bindings(families))
        held: dict[Vignette, list[str]] = {}
        for digest, vignette in self._rows.bound_to(current.values(), "case"):
            held.setdefault(vignette, []).append(digest)
        found: dict[int, str | None] = {}
        for family in families:
            vignette = current.get(family)
            cases = [] if vignette is None else held.get(vignette, [])
            bare = None if vignette is None else Case(vignette=vignette).digest
            found[family] = bare if bare in cases else next(iter(cases), None)
        return found

    # A family by its name, as `_named` finds a thread's; one without a name is called
    # `family ID`.
    def family(self, name: str) -> Family:
        return self._named(
            [(f, f.name, f.about) for f in self.families()], name, "case"
        )

    def family_by_id(self, id: int) -> Family:
        about = self.catalog.about(Subject(family=id))
        case = self._cases([id])[id] if about.shows(self.person.id) else None
        if case is None:
            raise NotFound(f"no case {id} for {self.person.login}")
        return Family(id, about, case)

    def tags(self) -> list[str]:
        return sorted({tag for _, about in self._families() for tag in about.tags})

    # The schemas of the expectations the person sees for a case.
    def expectation_schemas(self, case: str) -> list[str]:
        heads = [
            self.catalog.head(t).digest
            for t in self.catalog.expectations_of(case)
            if self.about(t).shows(self.person.id)
        ]
        held = (resolve(self.get, d, Expectation) for d in heads)
        return sorted({e.expectation_schema for e in held})

    # The expectation the case is scored against for the person under `schema`
    # (`Catalog.expectations_for`): Ambiguous when there are several to choose from.
    def expectation(self, case: str, schema: str) -> Expectation | None:
        digest = self._expectations_for([case], schema)[case]
        return None if digest is None else resolve(self.get, digest, Expectation)

    # The expectation threads shared with the person for a case under `schema`, with what
    # is said of each: what they could take.
    def shared(self, case: str, schema: str) -> list[tuple[Edit, About]]:
        return self.catalog.expectations_shared([case], self.person.id, schema)[case]

    # Several to choose from is the one LookupError
    # src/chatddx/catalog/threads.py:expectations_for raises.
    def _expectations_for(self, cases: list[str], schema: str) -> dict[str, str | None]:
        try:
            return self.catalog.expectations_for(cases, self.person.id, schema)
        except LookupError as e:
            raise Ambiguous(str(e)) from None

    def trial(
        self, skeleton: Skeleton, engine: str, cases: list[str], seed: int
    ) -> tuple[Registry, Trial]:
        registry = self.store.load(
            [engine, *cases, *(s.digest for s in skeleton.refs())]
        )
        _ = registry.add(skeleton)
        trial = Trial(
            skeleton=skeleton.digest, engine=engine, cases=tuple(cases), seeds=(seed,)
        )
        _ = registry.add(trial)
        return registry, trial

    # What the lints say of the variation run on `engine` as a trial: the pair's checks,
    # and with `families` the languages of their cases too. Without, any one case makes
    # the trial, since the pair's checks don't read cases.
    def findings(
        self,
        variation: TriedVariation,
        engine: str,
        seed: int,
        families: list[Family] | None = None,
    ) -> list[Finding]:
        if families is None:
            held = self._cases([f for f, _ in self._families()]).values()
            first = next((c for c in held if c is not None), None)
            some = [] if first is None else [first]
        else:
            some = [f.case for f in families]
        if not some:
            return []
        registry, trial = self.trial(self.skeleton(variation), engine, some, seed)
        if families is None:
            return lints(registry, self.facts, [trial.digest])
        # A family's case has the family's language, as Catalog.language_of finds it. The
        # request has its recipe's, which language_of counts only once it is compiled
        # and stored, as a variation being tried isn't.
        known = {f.case: f.about.language for f in families}
        recipe = variation.varied

        def languages(digest: str) -> str | None:
            if digest in known:
                return known[digest]
            if digest == trial.skeleton and recipe is not None:
                return self.catalog.recipe_language(recipe)
            return self.catalog.language_of(digest)

        return lints(registry, self.facts, [trial.digest], languages)

    def scorers(self) -> list[tuple[Edit, About, Scorer]]:
        return [
            (e, a, resolve(self.get, e.digest, Scorer))
            for e, a in self.threads("scorer")
        ]

    # The scorer threads whose every view reaches the run's output schema, the check
    # `check_score` warns with as `view.unreachable`.
    def scorers_for(self, run: RunStarted) -> list[tuple[Edit, About]]:
        return [
            (e, a) for e, a in self.threads("scorer") if self._applies(e.digest, run)
        ]

    def _applies(self, scorer: str, run: RunStarted) -> bool:
        trial = resolve(self.get, run.trial, Trial)
        schema = resolve(self.get, trial.skeleton, Skeleton).output_schema
        views = resolve(self.get, scorer, Scorer).views
        return all(reaches(schema, v.output) for v in views)

    # Each of the run's cases is scored against the expectation the catalog picks for
    # the person (`Catalog.expectations_for`); none when no case has one.
    def scoring(self, run: RunStarted, scorer: str) -> Scoring | None:
        trial = resolve(self.get, run.trial, Trial)
        schema = resolve(self.get, scorer, Scorer).expectation_schema
        held = self._expectations_for(list(trial.cases), schema)
        found = tuple(e for e in held.values() if e is not None)
        return Scoring(scorer=scorer, expectations=found) if found else None

    # The data of the expectation each case is scored against under `schema`, for the
    # cases that have one, and the cases with several to choose from.
    def _expected(
        self, cases: list[str], schema: str
    ) -> tuple[dict[str, JsonValue], set[str]]:
        heads: dict[str, str] = {}
        several: set[str] = set()
        choices = self.catalog.expectation_choices(cases, self.person.id, schema)
        for case, held in choices.items():
            try:
                digest = picked(case, held)
            except LookupError:
                several.add(case)
                continue
            if digest is not None:
                heads[case] = digest
        read = dict(self._rows.components(list(heads.values())))
        data = {
            c: resolve(read.__getitem__, d, Expectation).data for c, d in heads.items()
        }
        return data, several

    def labels(self, scorer: str) -> dict[int, str]:
        return {
            position: label
            for (part, position), label in self.catalog.labels(scorer).items()
            if part == "view"
        }

    # For each view of each scorer: whether the variation's output offers what it reads,
    # and which cases have an expectation it picks something from, or several to choose
    # from.
    def reach(self, variation: TriedVariation, families: list[Family]) -> list[Reach]:
        schema = self.skeleton(variation).output_schema
        cases = [f.case for f in families]
        data: dict[str, tuple[dict[str, JsonValue], set[str]]] = {}
        found: list[Reach] = []
        for edit, about, scorer in self.scorers():
            labels = self.labels(edit.digest)
            name = about.name or self.catalog.title(edit.thread)
            expected = scorer.expectation_schema
            for i, view in enumerate(scorer.views):
                offered = reaches(schema, view.output)
                if offered and expected not in data:
                    data[expected] = self._expected(cases, expected)
                held, several = data.get(expected, ({}, set[str]()))
                choosing = [f for f in families if offered and f.case in several]
                missing = [
                    f
                    for f in families
                    if offered and f.case not in several
                    if (x := held.get(f.case)) is None or not view.expectation_items(x)
                ]
                label = labels.get(i, f"view {i}")
                found.append(
                    Reach(
                        edit.thread,
                        name,
                        i,
                        label,
                        offered,
                        len(families),
                        missing,
                        choosing,
                    )
                )
        return found

    # Keeps the variation as the person's own configuration, under `name`: a new version
    # of their thread of that name, or else a fork of the configuration's thread.
    def save(self, variation: TriedVariation, name: str) -> Saved:
        mine = self.catalog.find("skeleton", name, owner=self.person.id)
        if len(mine) > 1:
            raise Ambiguous(
                f"{self.person.login} has {len(mine)} configurations named {name!r}"
            )
        if not mine:
            return self.fork(variation, name)
        return self.edit(mine[0], variation, self.catalog.head(mine[0]).id)

    # Keeps the variation as a new configuration of the person's own, named `name` and
    # forked from the configuration's edit it varies.
    def fork(self, variation: TriedVariation, name: str) -> Saved:
        return self._kept(variation, None, name)

    # Keeps the variation as a new version of `thread`, a configuration the person owns
    # whose head was `head` when they saw it; nothing is written when it is the head
    # already.
    def edit(self, thread: int, variation: TriedVariation, head: int) -> Saved:
        _, about = self.thread_by_id(thread, "configuration")
        if not about.owned_by(self.person.id):
            raise NotFound(f"no configuration {thread} of yours")
        name = about.name or self.catalog.title(thread)
        return self._kept(variation, thread, name, head)

    def _kept(
        self,
        variation: TriedVariation,
        thread: int | None,
        name: str,
        head: int | None = None,
    ) -> Saved:
        skeleton = self.skeleton(variation)
        with self.conn.transaction():
            compilation = (
                self._compile(variation) or variation.configuration.compilation
            )
            edit, kept = self.catalog.keep(
                skeleton.digest,
                self.person.id,
                thread,
                name=name,
                compilation=compilation,
                forked_from=variation.configuration.id,
                head=head,
            )
        what = SAVED[kept]
        recipe = self.catalog.recipe(edit.thread)
        return Saved(name, skeleton.digest, what, TriedVariation(edit, name, recipe))

    # Stores what an unsaved skeleton was compiled from, by the running code.
    def _compile(self, variation: TriedVariation) -> str | None:
        recipe = variation.varied
        if not variation.parts or recipe is None:
            return None
        registry, compilation = self._compiled(recipe)
        _ = self.store.add(registry, [compilation.digest])
        return compilation.digest

    # A recipe compiled by the running code, in a registry with what it refers to;
    # nothing is stored.
    def _compiled(self, recipe: Recipe) -> tuple[Registry, Compilation]:
        registry = self.store.load(s.digest for s in iter_refs(recipe))
        skeleton, compilation = compiled(recipe, registry.get, rig())
        _ = registry.add(skeleton)
        _ = registry.add(compilation)
        return registry, compilation

    # What following the origin of `thread`, a fork the person sees, would keep; `None`
    # when the origin hasn't moved on since the fork's base, or the person doesn't see
    # it any more.
    def proposal(self, thread: int) -> Proposed | None:
        _, _, word = self._seen(thread)
        found = self._proposed(thread, word)
        return None if found is None else found[0]

    # The proposal for `thread`, a fork the person owns whose head was `head` when they
    # saw it, kept as an edit based on the origin's head. A text takes `language` as
    # `edit_component`'s does.
    def follow(self, thread: int, head: int, language: str | None = None) -> Written:
        _, about, word = self._seen(thread)
        if not about.owned_by(self.person.id):
            raise NotFound(f"no {word} {thread} of yours")
        found = self._proposed(thread, word)
        if found is None:
            raise ValueError(f"{word} {thread} has nothing to follow")
        proposed, registry = found
        kind = self.catalog.thread(thread).kind
        if language is not None and proposed.compilation is not None:
            raise ValueError(COMPILED_LANGUAGE)
        if language is not None and kind not in LANGUAGE_KINDS:
            raise ValueError(f"{kind} components have no language of their own")
        if isinstance(proposed.proposal, Expectation):
            self._check_expecting(proposed.proposal, thread)
        kept = [proposed.compilation or proposed.digest]
        with self.conn.transaction():
            _ = self.store.add(registry, kept)
            if language is not None:
                self._language(proposed.digest, language)
            edit = self.catalog.edit(
                thread,
                proposed.digest,
                self.person.id,
                compilation=proposed.compilation,
                based_on=proposed.variation.origin_head.id,
                head=head,
            )
        return Written(edit, "a new version", self.linted(proposed.digest))

    def _proposed(self, thread: int, word: str) -> tuple[Proposed, Registry] | None:
        varied = self.catalog.variation(thread)
        if varied is None or not varied.moved:
            return None
        if not self.about(varied.origin_head.thread).shows(self.person.id):
            return None
        try:
            proposal = self.catalog.proposal(thread)
            if proposal is None:
                return None
            if isinstance(proposal, Recipe):
                registry, compilation = self._compiled(proposal)
                digest = compilation.skeleton
                proposed = Proposed(varied, proposal, digest, compilation.digest)
            else:
                registry = self.store.load(s.digest for s in proposal.refs())
                digest = registry.add(proposal)
                proposed = Proposed(varied, proposal, digest, None)
        except ValueError as e:
            raise ValueError(
                f"{word} {thread}'s changes don't fit its origin's head: {e}"
            ) from None
        return proposed, registry

    # A component of a kind a person writes, from its JSON as the store gives it, `v`
    # included or not.
    def component(self, doc: Mapping[str, JsonValue]) -> Component:
        kind = doc.get("kind")
        if not isinstance(kind, str) or kind not in WRITTEN:
            raise ValueError(
                f"{kind!r} isn't a kind a person writes: the kinds are "
                + ", ".join(sorted(WRITTEN))
            )
        cls = BY_KIND[kind]
        given = {k: v for k, v in doc.items() if k != "v"}
        if doc.get("v", cls.schema_version) != cls.schema_version:
            raise ValueError(f"{kind} is at v{cls.schema_version}, not v{doc['v']}")
        return cls.model_validate(given)

    # `component` as a new thread of the person's own, named `name`; a recipe is compiled
    # by the running code and kept as a new configuration, with its compilation.
    def new(
        self, component: Component | Recipe, name: str, language: str | None = None
    ) -> Written:
        if not isinstance(component, Recipe):
            return self._written(component, None, name=name, language=language)
        if language is not None:
            raise ValueError(COMPILED_LANGUAGE)
        for part in PARTS:
            digest = getattr(component, part)
            if digest is not None and self._rows.kind(digest) not in KINDS[part]:
                raise ValueError(f"{digest} isn't a stored chunk of {part}")
        registry, compilation = self._compiled(component)
        with self.conn.transaction():
            _ = self.store.add(registry, [compilation.digest])
            edit = self.catalog.create(
                compilation.skeleton,
                self.person.id,
                compilation=compilation.digest,
                name=name,
            )
        return Written(edit, "created", self.linted(compilation.skeleton))

    # A new thread of the person's own, named `name` and forked from the head of
    # `thread`, a thread they see; it starts from `component` when given, else from the
    # head.
    def fork_component(
        self,
        thread: int,
        name: str,
        component: Component | None = None,
        language: str | None = None,
    ) -> Written:
        edit, _, word = self._seen(thread)
        held = self.get(edit.digest) if component is None else component
        self._check_kind(thread, word, held)
        return self._written(
            held, None, name=name, language=language, forked_from=edit.id
        )

    # `component` as a new version of `thread`, a thread the person owns whose head was
    # `head` when they saw it; nothing is written when it is the head already.
    def edit_component(
        self,
        thread: int,
        head: int,
        component: Component,
        language: str | None = None,
    ) -> Written:
        _, about, word = self._seen(thread)
        if not about.owned_by(self.person.id):
            raise NotFound(f"no {word} {thread} of yours")
        self._check_kind(thread, word, component)
        return self._written(component, thread, language=language, head=head)

    # What the lints say of a stored component alone, with the catalog's languages.
    def linted(self, digest: str) -> list[Finding]:
        registry = self.store.load([digest])
        return lints(registry, self.facts, [digest], self.catalog.language_of)

    def _written(
        self,
        component: Component,
        thread: int | None,
        *,
        name: str | None = None,
        language: str | None = None,
        forked_from: int | None = None,
        head: int | None = None,
    ) -> Written:
        kind = component.kind_name
        if kind not in WRITTEN:
            raise ValueError(f"a person doesn't write {kind} components")
        if language is not None and kind not in LANGUAGE_KINDS:
            raise ValueError(f"{kind} components have no language of their own")
        if isinstance(component, Expectation):
            self._check_expecting(component, thread)
        registry = self.store.load(s.digest for s in component.refs())
        _ = registry.add(component)
        with self.conn.transaction():
            _ = self.store.add(registry, [component.digest])
            if language is not None:
                self._language(component.digest, language)
            edit, kept = self.catalog.keep(
                component.digest,
                self.person.id,
                thread,
                name=name,
                forked_from=forked_from,
                head=head,
            )
        return Written(edit, SAVED[kept], self.linted(component.digest))

    # A component's language is its text's, so other threads may hold it too: one it has
    # is kept, and the person's is written only where it has none.
    def _language(self, digest: str, language: str) -> None:
        held = self.catalog.language_of(digest)
        if held is not None and held != language:
            raise ValueError(
                f"{self.title(digest)} is in {held} already: a text's language is the "
                + "same wherever it is held"
            )
        if held is None:
            self.catalog.language(digest, language, self.person.id)

    # A thread the person sees, with the word for its kind to name it by.
    def _seen(self, thread: int) -> tuple[Edit, About, str]:
        found = self._rows.thread(thread)
        kind = None if found is None else found.kind
        word = next((w for w, held in KINDS.items() if kind in held), None)
        edit, about = self.thread_by_id(thread, word)
        return edit, about, word or "thread"

    def _check_kind(self, thread: int, word: str, component: Component) -> None:
        kind = self.catalog.thread(thread).kind
        if kind != component.kind_name:
            raise ValueError(
                f"{word} {thread} holds {kind} components, not {component.kind_name}"
            )

    # The catalog's rule, worded for the person: one expectation of their own per case
    # and schema.
    def _check_expecting(
        self, expectation: Expectation, thread: int | None, then: str = "edit that one"
    ) -> None:
        case, schema = expectation.case, expectation.expectation_schema
        held = self.catalog.expectation_choices([case], self.person.id, schema)[case]
        if others := sorted(t for t in held if t != thread):
            raise ValueError(
                f"{self.person.login} has their own expectation of {self.title(case)} "
                + f"under {self.title(schema)}, in thread {others[0]}: {then}"
            )

    # What is said about `thread`, which the person owns, as it is to hold afterwards: its
    # name, `None` for none and the title takes over; its description; its tags; who it is
    # shared with, by login; and whether it is deleted. `...` and `None` leave a field as
    # it is. Only what changes what holds is written, in one transaction, and what holds
    # afterwards is returned. A deleted thread is restored before anything else is said.
    def say(
        self,
        thread: int,
        *,
        name: str | None | EllipsisType = ...,
        description: str | None = None,
        tags: Collection[str] | None = None,
        collaborators: Collection[str] | None = None,
        deleted: bool | None = None,
    ) -> About:
        found = self._rows.thread(thread)
        kind = None if found is None else found.kind
        word = next((w for w, held in KINDS.items() if kind in held), "thread")
        about = self.about(thread)
        if found is None or about.owner != self.person.id:
            raise NotFound(f"no {word} {thread} of yours")
        changing = (name, description, tags, collaborators) != (..., None, None, None)
        if about.deleted and deleted is not False and changing:
            raise ValueError(
                f"{word} {thread} is deleted: restore it to say more of it"
            )
        if name == "":
            raise ValueError("a name can't be empty: none takes it away")
        if tags is not None and "" in tags:
            raise ValueError("a tag can't be empty")
        sharing: set[int] = (
            set()
            if collaborators is None
            else {self._sharing(c) for c in collaborators}
        )
        if self.person.id in sharing:
            raise ValueError(f"{word} {thread} is yours: it is shared with others")

        said: list[Entry] = []
        if deleted is False and about.deleted:
            head = self.get(self.catalog.head(thread).digest)
            if isinstance(head, Expectation):
                self._check_expecting(head, thread, "delete that one to restore this")
            said.append(Entry(field=EntryField.DELETED, present=False))
        if not isinstance(name, EllipsisType) and name != about.name:
            said.append(
                Entry(field=EntryField.NAME, present=False)
                if name is None
                else Entry(field=EntryField.NAME, value=name)
            )
        if description is not None and description != about.description:
            said.append(Entry(field=EntryField.DESCRIPTION, value=description))
        if tags is not None:
            said += [
                Entry(field=EntryField.TAG, value=t, present=t in tags)
                for t in sorted(about.tags.symmetric_difference(tags))
            ]
        if collaborators is not None:
            said += [
                Entry(field=EntryField.COLLABORATOR, person=c, present=c in sharing)
                for c in sorted(about.collaborators.symmetric_difference(sharing))
            ]
        if deleted and not about.deleted:
            said.append(Entry(field=EntryField.DELETED))
        with self.conn.transaction():
            for entry in said:
                self.catalog.note(Subject(thread=thread), entry, self.person.id)
        return self.about(thread)

    def _sharing(self, login: str) -> int:
        found = self._people.find(login)
        if found is None:
            raise NotFound(f"no person {login!r}")
        return found.id

    # For each case, a fork of the one expectation under `schema` shared with the person,
    # by `owner` when given, unless they have one of their own; in one transaction.
    def take(
        self, cases: Iterable[str], schema: str, owner: str | None = None
    ) -> Taken:
        if self._rows.kind(schema) != "expectation_schema":
            raise ValueError(f"{schema} isn't a stored expectation schema")
        by = None if owner is None else self._people.find(owner)
        if owner is not None and by is None:
            raise NotFound(f"no person {owner!r}")
        wanted = list(dict.fromkeys(cases))
        own = self.catalog.expectation_choices(wanted, self.person.id, schema)
        shared = self.catalog.expectations_shared(wanted, self.person.id, schema)
        found = Taken({}, {}, {}, [])
        with self.conn.transaction():
            for case in wanted:
                offered = [
                    (e, a) for e, a in shared[case] if by is None or a.owner == by.id
                ]
                if mine := sorted(own[case]):
                    found.kept[case] = mine[0]
                elif not offered:
                    found.missing.append(case)
                elif len(offered) > 1:
                    found.choosing[case] = [e.thread for e, _ in offered]
                else:
                    found.taken[case] = self._fork(*offered[0])
        return found

    # A fork of an expectation thread shared with the person. With `replace`, their own
    # of its case under its schema is deleted first, in the same transaction; without,
    # it is a conflict.
    def take_from(self, thread: int, replace: bool = False) -> int:
        edit, about = self.thread_by_id(thread, "expectation")
        if about.owner == self.person.id:
            raise ValueError(f"expectation {thread} is yours already")
        held = resolve(self.get, edit.digest, Expectation)
        case, schema = held.case, held.expectation_schema
        choices = self.catalog.expectation_choices([case], self.person.id, schema)
        mine = sorted(choices[case])
        if mine and not replace:
            raise Conflict(
                f"{self.person.login} has their own expectation of {self.title(case)} "
                + f"under {self.title(schema)}, in thread {mine[0]}: replace it to "
                + "take this one"
            )
        gone = Entry(field=EntryField.DELETED)
        with self.conn.transaction():
            for own in mine:
                self.catalog.note(Subject(thread=own), gone, self.person.id)
            return self._fork(edit, about)

    def _fork(self, head: Edit, about: About) -> int:
        made = self.catalog.create(
            head.digest, self.person.id, forked_from=head.id, name=about.name
        )
        return made.thread

    # The variation run on `cases` with one seed, at `endpoint`; nothing is sent until
    # `Running.send`.
    def start(
        self, variation: TriedVariation, endpoint: str, cases: list[str], seed: int
    ) -> Running:
        skeleton = self.skeleton(variation)
        registry, trial = self.trial(skeleton, self.endpoint(endpoint), cases, seed)
        runner = Runner(self.conn, self.inventory, self.person)
        running = runner.start(trial, registry, endpoint)
        _ = self._compile(variation)
        return running

    # A finished run scored under every scorer that applies to it, or those of
    # `scorers`, as each scoring would be built now.
    def score(
        self, run: RunStarted, scorers: Collection[str] | None = None
    ) -> list[Graded]:
        found: list[Graded] = []
        for edit, about in self.scorers_for(run):
            if scorers is not None and edit.digest not in scorers:
                continue
            name = about.name or self.catalog.title(edit.thread)
            scorer = resolve(self.get, edit.digest, Scorer)
            labels = self.labels(edit.digest)
            try:
                scoring = self.scoring(run, edit.digest)
                if scoring is None:
                    raise LookupError("none of the run's cases has an expectation")
                registry = self.store.load([scoring.scorer, *scoring.expectations])
                score, findings = score_run(
                    self.conn, run.run, scoring, registry, self.person
                )
            except (LookupError, TypeError, NotImplementedError) as e:
                found.append(Graded(name, scorer, labels, refused=str(e)))
                continue
            found.append(Graded(name, scorer, labels, score, findings))
        return found

    # The live runs the person owns, newest first. A collaborator on a run doesn't see it.
    def runs(self) -> list[RunStarted]:
        involved = [s for s in self.catalog.involving(self.person.id) if s.run]
        known = self.catalog.abouts(involved)
        owned = [
            s.run
            for s in involved
            if s.run is not None and known[s].owned_by(self.person.id)
        ]
        return self.store.started(owned)

    # The person's latest run, or the one whose id starts with `prefix`.
    def run(self, prefix: str | None = None) -> RunStarted:
        runs = self.runs()
        if prefix is None:
            if not runs:
                raise NotFound(f"{self.person.login} has no runs")
            return runs[0]
        match [r for r in runs if str(r.run).startswith(prefix)]:
            case [run]:
                return run
            case []:
                raise NotFound(f"no run of yours starts with {prefix!r}")
            case found:
                raise Ambiguous(f"{len(found)} runs of yours start with {prefix!r}")

    # A live run the person owns, by its whole id.
    def run_by_id(self, run: UUID) -> RunStarted:
        about = self.catalog.about(Subject(run=run))
        found = self.store.started([run])
        if not about.owned_by(self.person.id) or not found:
            raise NotFound(f"no run {run} of yours")
        return found[0]

    # The person's runs whose trial is built on `digest`.
    def reaching(self, digest: str) -> list[RunStarted]:
        trials = set(self.store.reaching(digest, "trial"))
        return [r for r in self.runs() if r.trial in trials]

    # What ran, as `run` and `batch` said it: the configuration, where it ran, the case
    # or how many, and the seed.
    def described(self, run: RunStarted) -> str:
        trial = resolve(self.get, run.trial, Trial)
        where = self.title(trial.engine) if run.endpoint is None else run.endpoint.name
        cases = (
            self.title(trial.cases[0])
            if len(trial.cases) == 1
            else f"{len(trial.cases)} cases"
        )
        seeds = ", ".join(str(seed) for seed in trial.seeds)
        return f"{self.title(trial.skeleton)} × {where} × {cases} (seed {seeds})"

    # The latest score under each scorer that scored the run.
    def scores_of(self, run: UUID) -> list[Graded]:
        found: dict[str, Graded] = {}
        for started in self.store.scores_of(run):
            scorer = resolve(self.get, started.scoring, Scoring).scorer
            if scorer in found:
                continue
            held = self.holder("scorer", scorer)
            name = held[1].name if held and held[1].name else self.title(scorer)
            found[scorer] = Graded(
                name,
                resolve(self.get, scorer, Scorer),
                self.labels(scorer),
                self.store.score(started.score),
            )
        return sorted(found.values(), key=lambda g: g.name)

    # The person's runs a scorer gave a score of.
    def scored_by(self, scorer: str) -> list[RunStarted]:
        return [
            run
            for run in self.runs()
            if any(
                resolve(self.get, s.scoring, Scoring).scorer == scorer
                for s in self.store.scores_of(run.run)
            )
        ]

    # The scorers that apply to a run and have no score of it under the scoring each
    # would be built now, so a changed expectation leaves the run to score again. One
    # whose scoring has expectations to choose from is left too, and refuses when scored.
    def unscored(self, run: RunStarted) -> list[str]:
        scored = {s.scoring for s in self.store.scores_of(run.run)}
        found: list[str] = []
        for edit, _ in self.scorers_for(run):
            try:
                scoring = self.scoring(run, edit.digest)
            except Ambiguous:
                found.append(edit.digest)
                continue
            if scoring is not None and scoring.digest not in scored:
                found.append(edit.digest)
        return found

    # The person's finished runs, newest first, with the scorers each is left to score.
    def outstanding(self) -> list[tuple[RunStarted, list[str]]]:
        runs = self.runs()
        finished = self.store.finished([r.run for r in runs])
        return [
            (run, scorers)
            for run in runs
            if run.run in finished and (scorers := self.unscored(run))
        ]

    # Whether each item's first request, rendered again from the trial and the source,
    # is what was sent, since only its fingerprint is kept: None when it is, else why
    # not.
    def rendered_again(self, run: Run) -> dict[ItemKey, str | None]:
        registry = self.store.load([run.started.trial])
        trial = resolve(registry.get, run.started.trial, Trial)
        skeleton = resolve(registry.get, trial.skeleton, Skeleton)
        engine = registry.get(trial.engine)
        assert isinstance(engine, LocalEngine | RemoteEngine)
        found: dict[ItemKey, str | None] = {}
        for item in run.items:
            case = resolve(registry.get, item.key.case, Case)
            try:
                raw = self.inventory.source(case.vignette.source).fetch(
                    case.vignette.id
                )
                prepared = prepare_case(
                    case, raw, registry.get, skeleton.appendix_layout, trial.cleanup
                )
            except (LookupError, StructuralError) as e:
                found[item.key] = str(e)
                continue
            body = render(
                skeleton,
                model=engine.served_model_name,
                seed=trial.seeds[item.key.replicate],
                fills=prepared.fills,
            )
            if prepared.fingerprint != item.vignette:
                found[item.key] = "the vignette at the source isn't the one sent"
            elif fingerprint_request(body) != item.call.request:
                found[item.key] = "the request renders otherwise now"
            else:
                found[item.key] = None
        return found

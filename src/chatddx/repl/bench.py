import secrets
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field, replace
from typing import Literal

from pydantic import JsonValue

from chatddx.catalog import About, Edit, Subject
from chatddx.catalog.titles import short
from chatddx.core.rig import rig
from chatddx.factors.base import Component, Finding, iter_refs, resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Case
from chatddx.factors.lint import lint
from chatddx.factors.request import Compilation, Recipe, Skeleton, compile_request
from chatddx.factors.scoring import Expectation, Scorer
from chatddx.factors.select import reaches
from chatddx.factors.trial import Trial
from chatddx.facts import Facts, check_pairs, model_name, reasons
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.ledger import RunStarted, Score
from chatddx.runner.run import Runner, Running
from chatddx.runner.score import score_run
from chatddx.store import Catalog, People, Reads, Store
from chatddx.store.catalog import Rows
from chatddx.store.store import Connection

PARTS = (
    "instructions",
    "few_shot",
    "prompt",
    "output",
    "sampling",
    "reasoning",
    "passthrough",
    "translations",
    "toolset",
)
OPTIONAL = tuple(p for p in PARTS if not Recipe.model_fields[p].is_required())
NONE = "none"

# What the shell calls each kind of thread; a case and an endpoint aren't threads.
KINDS: dict[str, tuple[str, ...]] = {
    "configuration": ("skeleton",),
    **{part: (f"chunk.{part}",) for part in PARTS},
    "tool": ("tool",),
    "scorer": ("scorer",),
    "judge": ("judge",),
    "expectation_schema": ("expectation_schema",),
    "canary_set": ("canary_set",),
    "model": ("model",),
    "engine": ("engine.local", "engine.remote"),
}

# A drawn seed is short, so the prompt stays readable; any seed a trial takes can be held.
SEEDS = 100_000
MAX_SEED = 2**31 - 1


def drawn_seed() -> int:
    return secrets.randbelow(SEEDS)


@dataclass(frozen=True)
class Cell:
    configuration: Edit | None = None
    name: str = ""
    recipe: Recipe | None = None
    # The parts set over the configuration's recipe: a chunk's digest, or None for an
    # optional part taken out, with the name it was set by.
    parts: Mapping[str, tuple[str | None, str]] = field(
        default_factory=dict[str, tuple[str | None, str]]
    )
    endpoint: str | None = None
    engine: str | None = None

    def using(self, configuration: Edit, name: str, recipe: Recipe | None) -> "Cell":
        return replace(
            self, configuration=configuration, name=name, recipe=recipe, parts={}
        )

    def on(self, endpoint: str, engine: str) -> "Cell":
        return replace(self, endpoint=endpoint, engine=engine)

    @property
    def label(self) -> str:
        if self.configuration is None:
            return ""
        return self.name + "".join(
            f"+{p}={self.parts[p][1]}" for p in PARTS if p in self.parts
        )

    def held(self, part: str) -> str | None:
        if part in self.parts:
            return self.parts[part][0]
        return None if self.recipe is None else getattr(self.recipe, part)

    def set(self, part: str, digest: str | None, name: str) -> "Cell":
        if self.recipe is None:
            raise ValueError(f"{self.name} has no recipe to set its {part} in")
        if digest is None and part not in OPTIONAL:
            raise ValueError(
                f"a configuration always has a {part}: only {', '.join(OPTIONAL)} "
                + f"can be {NONE}"
            )
        parts = {p: held for p, held in self.parts.items() if p != part}
        if getattr(self.recipe, part) != digest:
            parts[part] = (digest, name)
        return replace(self, parts=parts)

    @property
    def varied(self) -> Recipe | None:
        if self.recipe is None:
            return None
        changes = {p: digest for p, (digest, _) in self.parts.items()}
        return Recipe.model_validate(self.recipe.model_dump() | changes)


@dataclass(frozen=True)
class Family:
    id: int
    about: About
    case: str

    @property
    def name(self) -> str:
        return self.about.name or f"family {self.id}"


# What one view of a scorer gets from the cell's answers and the cases' expectations.
@dataclass(frozen=True)
class Reach:
    scorer: str
    view: int
    label: str
    offered: bool
    cases: int
    missing: list[str]

    @property
    def have(self) -> int:
        return self.cases - len(self.missing)


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
    cell: Cell


# What one person works with: the threads and families they see, the World's endpoints,
# and the cell they build up. Nothing here is UI.
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
        self.reads: Reads = Reads(conn, person)
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

    def threads(self, word: str) -> list[tuple[Edit, About]]:
        return [found for kind in KINDS[word] for found in self.reads.threads(kind)]

    def names(self, word: str) -> list[str]:
        return sorted({a.name for _, a in self.threads(word) if a.name is not None})

    # A thread by name, as `Reads.thread` finds it, or else the one made for the model
    # the cell's engine serves, `NAME (MODEL)`. Returns it with the name that found it.
    def thread(
        self, word: str, name: str, model: str | None = None
    ) -> tuple[Edit, str]:
        addresses = {
            kind: {
                address
                for _, a in self.reads.threads(kind)
                if a.name is not None
                for address in (a.name, f"{self.login(a.owner)}/{a.name}")
            }
            for kind in KINDS[word]
        }
        every = set[str]().union(*addresses.values())
        if model is not None and name not in every and f"{name} ({model})" in every:
            name = f"{name} ({model})"
        kinds = [kind for kind, held in addresses.items() if name in held]
        match kinds:
            case [kind]:
                return self.reads.thread(kind, name), name
            case []:
                said = f"no {word} {name!r} for {self.person.login}"
                if per_model := sorted(n for n in every if n.startswith(f"{name} (")):
                    said += f"; per model: {', '.join(per_model)}"
                    if model is None:
                        said += ", picked by the endpoint in the cell"
                raise LookupError(said)
            case _:
                raise LookupError(f"{word} {name!r} names a {' and a '.join(kinds)}")

    def about(self, thread: int) -> About:
        return self.catalog.about(Subject(thread=thread))

    # A thread the person sees whose head is `digest`, their own first.
    def holder(self, word: str, digest: str) -> tuple[Edit, About] | None:
        held = [(e, a) for e, a in self.threads(word) if e.digest == digest]
        held.sort(key=lambda found: found[1].owner != self.person.id)
        return next(iter(held), None)

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
            raise LookupError(
                f"endpoint {name!r} serves engine {short(engine)}, which isn't in the "
                + "store: seed its World's factors with init-data --factors"
            )
        return engine

    def configuration(self, name: str, cell: Cell) -> Cell:
        model = None if cell.engine is None else self.model(cell.engine)
        edit, found = self.thread("configuration", name, model)
        called = found.removeprefix(f"{self.person.login}/")
        return cell.using(edit, called, self.catalog.recipe(edit.thread))

    def chunk(self, part: str, name: str, cell: Cell) -> str | None:
        if name == NONE:
            return None
        model = None if cell.engine is None else self.model(cell.engine)
        return self.thread(part, name, model)[0].digest

    def skeleton(self, cell: Cell) -> Skeleton:
        assert cell.configuration is not None
        recipe = cell.varied
        if not cell.parts or recipe is None:
            return resolve(self.get, cell.configuration.digest, Skeleton)
        registry = self.store.load(s.digest for s in iter_refs(recipe))
        return compile_request(recipe, registry.get)

    def families(self, tags: Iterable[str] = ()) -> list[Family]:
        wanted = set(tags)
        found = [
            Family(family, about, case)
            for family, about in self.reads.families()
            if not wanted or wanted & about.tags
            if (case := self._case(family)) is not None
        ]
        return sorted(found, key=lambda f: f.name)

    # A family's case is the one its vignette makes alone, else the first holding it.
    def _case(self, family: int) -> str | None:
        vignette = self.catalog.bindings(family)[-1].vignette
        cases = self._rows.bound_to(vignette, "case")
        bare = Case(vignette=vignette).digest
        return bare if bare in cases else next(iter(cases), None)

    def family(self, name: str) -> Family:
        found = [
            (family, about)
            for family, about in self.reads.families()
            if (about.name or f"family {family}") == name
        ]
        own = [f for f in found if f[1].owner == self.person.id]
        for choices in (own, found):
            if len(choices) > 1:
                raise LookupError(f"{len(choices)} cases are named {name!r}")
            if choices and (case := self._case(choices[0][0])) is not None:
                return Family(*choices[0], case)
        raise LookupError(f"no case {name!r} for {self.person.login}")

    def tags(self) -> list[str]:
        return sorted({tag for _, about in self.reads.families() for tag in about.tags})

    # The expectation a person reads for a case: the head of their own thread, else of
    # one shared with them.
    def expectation(self, case: str) -> Expectation | None:
        threads = self.catalog.expectations_of(case)
        seen = [(t, a) for t in threads if (a := self.about(t)).shows(self.person.id)]
        own = [t for t, a in seen if a.owner == self.person.id]
        for choices in (own, [t for t, _ in seen]):
            if choices:
                head = self.catalog.head(choices[0])
                return resolve(self.get, head.digest, Expectation)
        return None

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

    # What the lints say of the cell run as a trial: the pair's checks, and with `cases`
    # the languages of those cases too. Without, any one case makes the trial, since the
    # pair's checks don't read cases.
    def findings(
        self, cell: Cell, seed: int, cases: list[str] | None = None
    ) -> list[Finding]:
        assert cell.engine is not None
        some = cases
        if some is None:
            held = (self._case(f) for f, _ in self.reads.families())
            first = next((c for c in held if c is not None), None)
            some = [] if first is None else [first]
        if not some:
            return []
        registry, trial = self.trial(self.skeleton(cell), cell.engine, some, seed)
        languages = None if cases is None else self.catalog.language_of
        found = lint(
            registry,
            [trial.digest],
            languages=languages,
            reasons=reasons(self.facts, registry),
        )
        return found + check_pairs(registry, self.facts, [trial.digest])

    def scorers(self) -> list[tuple[Edit, About, Scorer]]:
        return [
            (e, a, resolve(self.get, e.digest, Scorer))
            for e, a in self.threads("scorer")
        ]

    def labels(self, scorer: str) -> dict[int, str]:
        return {
            position: label
            for (part, position), label in self.catalog.labels(scorer).items()
            if part == "view"
        }

    # For each view of each scorer: whether the cell's output offers what it reads, and
    # which cases have an expectation it picks something from.
    def reach(self, cell: Cell, families: list[Family]) -> list[Reach]:
        schema = self.skeleton(cell).output_schema
        data: dict[tuple[str, str], JsonValue | None] = {}
        found: list[Reach] = []
        for edit, about, scorer in self.scorers():
            labels = self.labels(edit.digest)
            name = about.name or self.catalog.title(edit.thread)
            for i, view in enumerate(scorer.views):
                offered = reaches(schema, view.output)
                missing: list[str] = []
                for f in families if offered else []:
                    key = (f.case, scorer.expectation_schema)
                    if key not in data:
                        digest = self.catalog.expectation_for(
                            f.case, self.person.id, scorer.expectation_schema
                        )
                        data[key] = (
                            None
                            if digest is None
                            else resolve(self.get, digest, Expectation).data
                        )
                    held = data[key]
                    if held is None or not view.expectation_items(held):
                        missing.append(f.name)
                label = labels.get(i, f"view {i}")
                found.append(Reach(name, i, label, offered, len(families), missing))
        return found

    # Keeps the cell's configuration as the person's own, under `name`: a new version of
    # their thread of that name, or else a fork of the configuration's thread.
    def save(self, cell: Cell, name: str) -> Saved:
        assert cell.configuration is not None
        skeleton = self.skeleton(cell)
        mine = self.catalog.find("skeleton", name, owner=self.person.id)
        if len(mine) > 1:
            raise ValueError(
                f"{self.person.login} has {len(mine)} configurations named {name!r}"
            )
        with self.conn.transaction():
            compilation = (
                self._compile(cell, skeleton) or cell.configuration.compilation
            )
            if not mine:
                what = "created"
                edit = self.catalog.create(
                    skeleton.digest,
                    self.person.id,
                    compilation=compilation,
                    forked_from=cell.configuration.id,
                    name=name,
                )
            elif self.catalog.head(mine[0]).digest == skeleton.digest:
                what = "unchanged"
                edit = self.catalog.head(mine[0])
            else:
                what = "a new version"
                edit = self.catalog.edit(
                    mine[0], skeleton.digest, self.person.id, compilation=compilation
                )
        recipe = self.catalog.recipe(edit.thread)
        return Saved(name, skeleton.digest, what, cell.using(edit, name, recipe))

    # Stores what an unsaved skeleton was compiled from, by the running code.
    def _compile(self, cell: Cell, skeleton: Skeleton) -> str | None:
        recipe = cell.varied
        if not cell.parts or recipe is None:
            return None
        registry = self.store.load(s.digest for s in iter_refs(recipe))
        _ = registry.add(skeleton)
        compilation = registry.add(
            Compilation(recipe=recipe, skeleton=skeleton.digest, compiler=rig())
        )
        _ = self.store.add(registry, [compilation])
        return compilation

    # The cell run on `cases` with one seed, at the cell's endpoint; nothing is sent
    # until `Running.send`.
    def start(self, cell: Cell, cases: list[str], seed: int) -> Running:
        assert cell.endpoint is not None and cell.engine is not None
        skeleton = self.skeleton(cell)
        registry, trial = self.trial(skeleton, cell.engine, cases, seed)
        runner = Runner(self.conn, self.inventory, self.person)
        running = runner.start(trial, registry, cell.endpoint)
        _ = self._compile(cell, skeleton)
        return running

    # A finished run scored under every scorer that applies to it, as each scoring would
    # be built now.
    def score(self, run: RunStarted) -> list[Graded]:
        found: list[Graded] = []
        for edit, about in self.reads.scorers(run):
            name = about.name or self.catalog.title(edit.thread)
            scorer = resolve(self.get, edit.digest, Scorer)
            labels = self.labels(edit.digest)
            try:
                scoring = self.reads.scoring(run, edit.digest)
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

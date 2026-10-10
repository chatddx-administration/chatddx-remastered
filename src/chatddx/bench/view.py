from collections.abc import Collection, Iterable, Mapping
from dataclasses import dataclass, field
from typing import Literal
from uuid import UUID

from pydantic import JsonValue

from chatddx.catalog import About, Edit, Kept, Subject, variants_for
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
from chatddx.factors.cases import Case, prepare_case
from chatddx.factors.engine import LocalEngine, RemoteEngine
from chatddx.factors.request import (
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
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.ledger import ItemKey, Run, RunStarted, Score, fingerprint_request
from chatddx.runner.run import Runner, Running
from chatddx.runner.score import score_run
from chatddx.store import Catalog, People, Store
from chatddx.store.catalog import Rows
from chatddx.store.store import Connection

from .errors import Ambiguous, NotFound
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
    "canary_set": ("canary_set",),
    "model": ("model",),
    "engine": ("engine.local", "engine.remote"),
}

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
    variation: TriedVariation


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
                if a.name is not None
                for address in (a.name, f"{self.login(a.owner)}/{a.name}")
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

    # The one of `seen` called `name`: the person's own, else the one shared with them.
    # A name is matched whole first, since names may hold a slash, as
    # `plan (Qwen/Qwen3-8B-AWQ)` does; only then is it read as `OWNER/NAME`.
    def _named[T](
        self, seen: list[tuple[T, str | None, About]], name: str, word: str
    ) -> T:
        called = [(found, a) for found, n, a in seen if n == name]
        own = [found for found, a in called if a.owner == self.person.id]
        shared = [found for found, _ in called]
        if not called and "/" in name:
            login, rest = name.split("/", 1)
            owner = self._people.find(login)
            if owner is not None:
                own = []
                shared = [f for f, n, a in seen if n == rest and a.owner == owner.id]
        for choices in (own, shared):
            if len(choices) == 1:
                return choices[0]
            if choices:
                raise Ambiguous(
                    f"{word} {name!r} names {len(choices)}; name one as OWNER/NAME"
                )
        raise NotFound(f"no {word} {name!r} for {self.person.login}")

    # The head of a thread the person sees, by its id, with what the catalog says of it;
    # with `word`, only of the kinds it names.
    def thread_by_id(self, id: int, word: str | None = None) -> tuple[Edit, About]:
        about = self.about(id)
        thread = self._rows.thread(id)
        if (
            thread is None
            or not about.shows(self.person.id)
            or (word is not None and thread.kind not in KINDS[word])
        ):
            raise NotFound(f"no {word or 'thread'} {id} for {self.person.login}")
        return self.catalog.head(id), about

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
        found = [
            Family(family, about, case)
            for family, about in self._families()
            if not wanted or wanted & about.tags
            if (case := self._case(family)) is not None
        ]
        return sorted(found, key=lambda f: f.name)

    def _families(self) -> list[tuple[int, About]]:
        return self.catalog.visible_families(self.person.id)

    # A family's case is the one its vignette makes alone, else the first holding it.
    def _case(self, family: int) -> str | None:
        vignette = self.catalog.bindings(family)[-1].vignette
        cases = self._rows.bound_to(vignette, "case")
        bare = Case(vignette=vignette).digest
        return bare if bare in cases else next(iter(cases), None)

    # A family by its name, as `_named` finds a thread's; one without a name is called
    # `family ID`.
    def family(self, name: str) -> Family:
        return self._named(
            [(f, f.name, f.about) for f in self.families()], name, "case"
        )

    def family_by_id(self, id: int) -> Family:
        about = self.catalog.about(Subject(family=id))
        case = self._case(id) if about.shows(self.person.id) else None
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
    # (`Catalog.expectation_for`): Ambiguous when there are several to choose from.
    def expectation(self, case: str, schema: str) -> Expectation | None:
        digest = self._expectation_for(case, schema)
        return None if digest is None else resolve(self.get, digest, Expectation)

    # Several to choose from is the one LookupError
    # src/chatddx/catalog/threads.py:expectation_for raises.
    def _expectation_for(self, case: str, schema: str) -> str | None:
        try:
            return self.catalog.expectation_for(case, self.person.id, schema)
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
    # and with `cases` the languages of those cases too. Without, any one case makes the
    # trial, since the pair's checks don't read cases.
    def findings(
        self,
        variation: TriedVariation,
        engine: str,
        seed: int,
        cases: list[str] | None = None,
    ) -> list[Finding]:
        some = cases
        if some is None:
            held = (self._case(f) for f, _ in self._families())
            first = next((c for c in held if c is not None), None)
            some = [] if first is None else [first]
        if not some:
            return []
        registry, trial = self.trial(self.skeleton(variation), engine, some, seed)
        languages = None if cases is None else self.catalog.language_of
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
    # the person (`Catalog.expectation_for`); none when no case has one.
    def scoring(self, run: RunStarted, scorer: str) -> Scoring | None:
        trial = resolve(self.get, run.trial, Trial)
        schema = resolve(self.get, scorer, Scorer).expectation_schema
        found = [
            expectation
            for case in trial.cases
            if (expectation := self._expectation_for(case, schema)) is not None
        ]
        return Scoring(scorer=scorer, expectations=tuple(found)) if found else None

    def labels(self, scorer: str) -> dict[int, str]:
        return {
            position: label
            for (part, position), label in self.catalog.labels(scorer).items()
            if part == "view"
        }

    # For each view of each scorer: whether the variation's output offers what it reads,
    # and which cases have an expectation it picks something from.
    def reach(self, variation: TriedVariation, families: list[Family]) -> list[Reach]:
        schema = self.skeleton(variation).output_schema
        data: dict[tuple[str, str], JsonValue | None] = {}
        found: list[Reach] = []
        for edit, about, scorer in self.scorers():
            labels = self.labels(edit.digest)
            name = about.name or self.catalog.title(edit.thread)
            for i, view in enumerate(scorer.views):
                offered = reaches(schema, view.output)
                missing: list[Family] = []
                for f in families if offered else []:
                    key = (f.case, scorer.expectation_schema)
                    if key not in data:
                        read = self.expectation(f.case, scorer.expectation_schema)
                        data[key] = None if read is None else read.data
                    held = data[key]
                    if held is None or not view.expectation_items(held):
                        missing.append(f)
                label = labels.get(i, f"view {i}")
                found.append(
                    Reach(edit.thread, name, i, label, offered, len(families), missing)
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
        return self.edit(mine[0], variation) if mine else self.fork(variation, name)

    # Keeps the variation as a new configuration of the person's own, named `name` and
    # forked from the configuration's edit it varies.
    def fork(self, variation: TriedVariation, name: str) -> Saved:
        return self._kept(variation, None, name)

    # Keeps the variation as a new version of `thread`, a configuration the person owns;
    # nothing is written when it is the head already.
    def edit(self, thread: int, variation: TriedVariation) -> Saved:
        _, about = self.thread_by_id(thread, "configuration")
        if about.owner != self.person.id:
            raise NotFound(f"no configuration {thread} of yours")
        return self._kept(variation, thread, about.name or self.catalog.title(thread))

    def _kept(self, variation: TriedVariation, thread: int | None, name: str) -> Saved:
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
            )
        what = SAVED[kept]
        recipe = self.catalog.recipe(edit.thread)
        return Saved(name, skeleton.digest, what, TriedVariation(edit, name, recipe))

    # Stores what an unsaved skeleton was compiled from, by the running code.
    def _compile(self, variation: TriedVariation) -> str | None:
        recipe = variation.varied
        if not variation.parts or recipe is None:
            return None
        registry = self.store.load(s.digest for s in iter_refs(recipe))
        skeleton, compilation = compiled(recipe, registry.get, rig())
        _ = registry.add(skeleton)
        _ = self.store.add(registry, [registry.add(compilation)])
        return compilation.digest

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
            if s.run is not None
            and (a := known[s]).owner == self.person.id
            and not a.deleted
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
        if about.owner != self.person.id or about.deleted or not found:
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
    # would be built now, so a changed expectation leaves the run to score again.
    def unscored(self, run: RunStarted) -> list[str]:
        scored = {s.scoring for s in self.store.scores_of(run.run)}
        found: list[str] = []
        for edit, _ in self.scorers_for(run):
            try:
                scoring = self.scoring(run, edit.digest)
            except LookupError:
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

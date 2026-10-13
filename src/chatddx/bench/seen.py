from collections.abc import Iterable, Mapping
from uuid import UUID

from pydantic import JsonValue

from chatddx.catalog import (
    About,
    Edit,
    Subject,
    language_of,
    latest,
    made_for,
    variants_for,
)
from chatddx.catalog.threads import picked, recipe as recipe_of
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
from chatddx.factors.cases import Case, Vignette
from chatddx.factors.engine import LocalEngine, RemoteEngine
from chatddx.factors.request import (
    Compilation,
    Purpose,
    Recipe,
    Skeleton,
    compile_request,
    compiled,
    render,
)
from chatddx.factors.scoring import Expectation, Judge, Scorer, Scoring
from chatddx.factors.trial import Trial
from chatddx.facts import Facts, lints, model_name
from chatddx.identity import Person, preferred
from chatddx.inventory import Inventory
from chatddx.ledger import (
    ItemKey,
    Run,
    RunStarted,
    ScoreStarted,
    fingerprint_request,
)
from chatddx.runner.gate import Refused
from chatddx.runner.prepare import Items
from chatddx.runner.score import judge_at
from chatddx.runner.send import STOPPED
from chatddx.scorers.shipped import problems
from chatddx.store import Catalog, People, Store
from chatddx.store.catalog import Rows
from chatddx.store.store import Connection

from .errors import Ambiguous, NotFound
from .model import KINDS, PLACEHOLDERS, Family, Graded, Reach
from .variation import PARTS, TriedVariation


class Seen:
    def __init__(
        self, conn: Connection, person: Person, inventory: Inventory, facts: Facts
    ) -> None:
        self.conn: Connection = conn
        self.person: Person = person
        self.inventory: Inventory = inventory
        self.facts: Facts = facts
        self.store: Store = Store(conn)
        self.catalog: Catalog = Catalog(conn)
        self.rows: Rows = Rows(conn)
        self.people: People = People(conn)
        self._logins: dict[int, str] = {}
        self._models: dict[str, str | None] = {}

    def login(self, person: int | None) -> str:
        if person is None:
            return "nobody"
        if person not in self._logins:
            self._logins[person] = self.people.get(person).login
        return self._logins[person]

    def owner(self, about: About) -> str:
        return "" if about.owner == self.person.id else self.login(about.owner)

    def threads(self, word: str) -> list[tuple[Edit, About]]:
        return [found for kind in KINDS[word] for found in self.visible(kind)]

    def visible(self, kind: str) -> list[tuple[Edit, About]]:
        return self.catalog.visible(kind, self.person.id)

    def names(self, word: str) -> list[str]:
        return sorted({a.name for _, a in self.threads(word) if a.name is not None})

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
        base, language = name, None
        if name not in every:
            base, language = language_of(name)
            match variants_for(base, every, model, language):
                case [one]:
                    name = one
                case []:
                    pass
                case several:
                    models = [] if model is None else [model]
                    languages = sorted(
                        {m[1] for n in several if (m := made_for(n, models)) and m[1]}
                    )
                    raise Ambiguous(
                        f"{word} {name!r} is made in more than one language: "
                        + f"{', '.join(several)}; name one as "
                        + " or ".join(f"'{base} {lang}'" for lang in languages)
                    )
        kinds = [kind for kind, held in addresses.items() if name in held]
        match kinds:
            case [kind]:
                return self._named(
                    [(e, a.name, a) for e, a in seen[kind]], name, word
                ), name
            case []:
                said = f"no {word} {name!r} for {self.person.login}"
                made = f"{base} ({language}, " if language else f"{base} ("
                if per_model := sorted(n for n in every if n.startswith(made)):
                    said += f"; per model: {', '.join(per_model)}"
                raise NotFound(said, per_model if model is None else ())
            case _:
                raise Ambiguous(f"{word} {name!r} names a {' and a '.join(kinds)}")

    def _qualified(self, name: str | None, owner: int | None) -> str | None:
        if name is None or owner is None:
            return None
        return f"{self.login(owner)}/{name}"

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

    def thread_by_id(
        self, id: int, word: str | None = None, *, deleted: bool = False
    ) -> tuple[Edit, About]:
        about = self.about(id)
        thread = self.rows.thread(id)
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
        if self.rows.kind(engine) is None:
            raise NotFound(
                f"endpoint {name!r} serves engine {short(engine)}, which isn't in the "
                + "store: load its World with init-data"
            )
        return engine

    def configuration(self, name: str, engine: str | None = None) -> TriedVariation:
        model = None if engine is None else self.model(engine)
        edit, found = self.thread("configuration", name, model)
        called = found.removeprefix(f"{self.person.login}/")
        return TriedVariation(edit, called, self.catalog.recipe(edit.thread))

    def chunk(self, part: str, name: str, engine: str | None = None) -> str:
        model = None if engine is None else self.model(engine)
        return self.thread(part, name, model)[0].digest

    def variation(
        self,
        configuration: int,
        parts: Mapping[str, str | None] | None = None,
        head: int | None = None,
    ) -> TriedVariation:
        edit, about = self.thread_by_id(configuration, "configuration")
        if head is not None and head != edit.id:
            edit = self.rows.edit(head)
            if edit is None or edit.thread != configuration:
                raise NotFound(f"no edit {head} of configuration {configuration}")
        name = about.name or self.catalog.title(configuration)
        found = TriedVariation(edit, name, recipe_of(self.rows, edit))
        for part, digest in (parts or {}).items():
            if part not in PARTS:
                raise ValueError(f"no part {part!r}: the parts are {', '.join(PARTS)}")
            if digest is not None and self.rows.kind(digest) not in KINDS[part]:
                raise ValueError(f"{digest} isn't a stored chunk of {part}")
            found = found.set(part, digest, self.title(digest))
        return found

    def skeleton(self, variation: TriedVariation) -> Skeleton:
        recipe = variation.varied
        if not variation.parts or recipe is None:
            return resolve(self.get, variation.configuration.digest, Skeleton)
        registry = self.store.load(s.digest for s in iter_refs(recipe))
        return compile_request(recipe, registry.get)

    def served(self, engine: str) -> str:
        found = self.get(engine)
        if not isinstance(found, LocalEngine | RemoteEngine):
            raise StructuralError(f"{engine} is a {found.kind_name}, not an engine")
        return found.served_model_name

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

    def _cases(self, families: list[int]) -> dict[int, str | None]:
        current = latest((b.family, b.vignette) for b in self.rows.bindings(families))
        held: dict[Vignette, list[str]] = {}
        for digest, vignette in self.rows.bound_to(current.values(), "case"):
            held.setdefault(vignette, []).append(digest)
        found: dict[int, str | None] = {}
        for family in families:
            vignette = current.get(family)
            cases = [] if vignette is None else held.get(vignette, [])
            bare = None if vignette is None else Case(vignette=vignette).digest
            found[family] = bare if bare in cases else next(iter(cases), None)
        return found

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

    def expectation_schemas(self, case: str) -> list[str]:
        heads = [
            self.catalog.head(t).digest
            for t in self.catalog.expectations_of(case)
            if self.about(t).shows(self.person.id)
        ]
        held = (resolve(self.get, d, Expectation) for d in heads)
        return sorted({e.expectation_schema for e in held})

    def expectation(self, case: str, schema: str) -> Expectation | None:
        digest = self._expectations_for([case], schema)[case]
        return None if digest is None else resolve(self.get, digest, Expectation)

    def shared(self, case: str, schema: str) -> list[tuple[Edit, About]]:
        return self.catalog.expectations_shared([case], self.person.id, schema)[case]

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

    def findings(
        self,
        variation: TriedVariation,
        engine: str,
        seed: int,
        families: list[Family] | None = None,
    ) -> list[Finding]:
        skeleton = self.skeleton(variation)
        if skeleton.purpose == "judge":
            return self._judged(skeleton, engine, seed)
        if families is None:
            held = self._cases([f for f, _ in self._families()]).values()
            first = next((c for c in held if c is not None), None)
            some = [] if first is None else [first]
        else:
            some = [f.case for f in families]
        if not some:
            return []
        registry, trial = self.trial(skeleton, engine, some, seed)
        if families is None:
            return lints(registry, self.facts, [trial.digest])
        known = {f.case: f.about.language for f in families}
        recipe = variation.varied

        def languages(digest: str) -> str | None:
            if digest in known:
                return known[digest]
            if digest == trial.skeleton and recipe is not None:
                return self.catalog.recipe_language(recipe)
            return self.catalog.language_of(digest)

        return lints(registry, self.facts, [trial.digest], languages)

    def _judged(self, skeleton: Skeleton, engine: str, seed: int) -> list[Finding]:
        registry = self.store.load([engine, *(s.digest for s in skeleton.refs())])
        _ = registry.add(skeleton)
        judge = Judge(skeleton=skeleton.digest, engine=engine, seeds=(seed,))
        _ = registry.add(judge)
        return lints(registry, self.facts, [judge.digest])

    def purposed(
        self, found: Iterable[tuple[Edit, About]], purpose: Purpose
    ) -> list[tuple[Edit, About]]:
        held = list(found)
        read = dict(self.rows.components([e.digest for e, _ in held]))
        return [
            (e, a)
            for e, a in held
            if resolve(read.__getitem__, e.digest, Skeleton).purpose == purpose
        ]

    def answering(
        self, found: Iterable[tuple[Edit, About]], title: str
    ) -> list[tuple[Edit, About]]:
        held = list(found)
        read = dict(self.rows.components([e.digest for e, _ in held]))
        return [
            (e, a)
            for e, a in held
            if _titled(resolve(read.__getitem__, e.digest, Skeleton).output_schema)
            == title
        ]

    def scorers(self) -> list[tuple[Edit, About, Scorer]]:
        found = [
            (e, a, resolve(self.get, e.digest, Scorer))
            for e, a in self.threads("scorer")
        ]
        return sorted(found, key=lambda s: s[1].name or self.catalog.title(s[0].thread))

    def scorers_for(self, run: RunStarted) -> list[tuple[Edit, About]]:
        return [
            (e, a) for e, a in self.threads("scorer") if self._applies(e.digest, run)
        ]

    def _applies(self, scorer: str, run: RunStarted) -> bool:
        trial = resolve(self.get, run.trial, Trial)
        schema = resolve(self.get, trial.skeleton, Skeleton).output_schema
        found = resolve(self.get, scorer, Scorer)
        if not all(v.offered_by(schema) for v in found.views):
            return False
        try:
            for judge in found.judges:
                _ = judge_at(self.inventory, self.get, judge, trial.cases)
        except (ValueError, Refused):
            return False
        return True

    def scoring(self, run: RunStarted, scorer: str) -> Scoring | None:
        trial = resolve(self.get, run.trial, Trial)
        schema = resolve(self.get, scorer, Scorer).expectation_schema
        held = self._expectations_for(list(trial.cases), schema)
        found = tuple(e for e in held.values() if e is not None)
        return Scoring(scorer=scorer, expectations=found) if found else None

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
        read = dict(self.rows.components(list(heads.values())))
        data = {
            c: resolve(read.__getitem__, d, Expectation).data for c, d in heads.items()
        }
        return data, several

    def labels(self, scorer: str) -> dict[int, str]:
        held = self.holder("scorer", scorer)
        if held is not None:
            return self.labels_of(held[0])
        seen = {e.thread: a.owner for e, a in self.threads("scorer")}
        earlier = [
            (e, seen[e.thread])
            for e in self.rows.edits_holding([scorer])
            if e.thread in seen
        ]
        held_before = sorted(preferred(self.person.id, earlier), key=lambda e: e.id)
        return self.labels_of(held_before[-1]) if held_before else {}

    def labels_of(self, edit: Edit) -> dict[int, str]:
        return {
            position: label
            for (part, position), label in self.catalog.labels(edit.id).items()
            if part == "view"
        }

    def reach(self, variation: TriedVariation, families: list[Family]) -> list[Reach]:
        skeleton = self.skeleton(variation)
        if skeleton.purpose == "judge":
            return []
        schema = skeleton.output_schema
        cases = [f.case for f in families]
        data: dict[str, tuple[dict[str, JsonValue], set[str]]] = {}
        found: list[Reach] = []
        for edit, about, scorer in self.scorers():
            labels = self.labels_of(edit)
            name = about.name or self.catalog.title(edit.thread)
            expected = scorer.expectation_schema
            for i, view in enumerate(scorer.views):
                offered = view.offered_by(schema)
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

    def compiled(self, recipe: Recipe) -> tuple[Registry, Compilation]:
        registry = self.store.load(s.digest for s in iter_refs(recipe))
        skeleton, compilation = compiled(recipe, registry.get, rig())
        _ = registry.add(skeleton)
        _ = registry.add(compilation)
        return registry, compilation

    def linted(self, digest: str) -> list[Finding]:
        registry = self.store.load([digest])
        return lints(registry, self.facts, [digest], self.catalog.language_of)

    def current(self, family: int) -> Vignette:
        return self.rows.bindings([family])[-1].vignette

    def cases(self, family: int) -> list[str]:
        found = self.family_by_id(family)
        vignette = self.current(found.id)
        held = [d for d, _ in self.rows.bound_to([vignette], "case")]
        bare = Case(vignette=vignette).digest
        return sorted(held, key=lambda d: (d != bare, d))

    def worded(self, thread: int) -> tuple[Edit, About, str]:
        found = self.rows.thread(thread)
        kind = None if found is None else found.kind
        word = next((w for w, held in KINDS.items() if kind in held), None)
        edit, about = self.thread_by_id(thread, word)
        return edit, about, word or "thread"

    def check_scorer(self, scorer: Scorer) -> None:
        if found := problems(scorer):
            raise ValueError("; ".join(found))

    def check_kind(self, thread: int, word: str, component: Component) -> None:
        kind = self.catalog.thread(thread).kind
        if kind != component.kind_name:
            raise ValueError(
                f"{word} {thread} holds {kind} components, not {component.kind_name}"
            )

    def check_expecting(
        self, expectation: Expectation, thread: int | None, then: str = "edit that one"
    ) -> None:
        case, schema = expectation.case, expectation.expectation_schema
        held = self.catalog.expectation_choices([case], self.person.id, schema)[case]
        if others := sorted(t for t in held if t != thread):
            raise ValueError(
                f"{self.person.login} has their own expectation of {self.title(case)} "
                + f"under {self.title(schema)}, in thread {others[0]}: {then}"
            )

    def runs(self) -> list[RunStarted]:
        involved = [s for s in self.catalog.involving(self.person.id) if s.run]
        known = self.catalog.abouts(involved)
        owned = [
            s.run
            for s in involved
            if s.run is not None and known[s].owned_by(self.person.id)
        ]
        return self.store.started(owned)

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

    def run_by_id(self, run: UUID) -> RunStarted:
        about = self.catalog.about(Subject(run=run))
        found = self.store.started([run])
        if not about.owned_by(self.person.id) or not found:
            raise NotFound(f"no run {run} of yours")
        return found[0]

    def reaching(self, digest: str) -> list[RunStarted]:
        trials = set(self.store.reaching(digest, "trial"))
        for made in self.store.reaching(digest, "compilation"):
            skeleton = resolve(self.get, made, Compilation).skeleton
            trials.update(self.store.reaching(skeleton, "trial"))
        return [r for r in self.runs() if r.trial in trials]

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

    def scores_of(self, run: UUID, every: bool = False) -> list[Graded]:
        given = self.store.scores_of(run)
        if every:
            return [self._graded(started) for started in given]
        found: dict[str, ScoreStarted] = {}
        for started in given:
            scorer = resolve(self.get, started.scoring, Scoring).scorer
            _ = found.setdefault(scorer, started)
        return sorted((self._graded(s) for s in found.values()), key=lambda g: g.name)

    def score_of(self, run: UUID, score: UUID) -> Graded:
        _ = self.run_by_id(run)
        found = next((s for s in self.store.scores_of(run) if s.score == score), None)
        if found is None:
            raise NotFound(f"no score {score} of run {run}")
        return self._graded(found)

    def _graded(self, started: ScoreStarted) -> Graded:
        scorer = resolve(self.get, started.scoring, Scoring).scorer
        return Graded(
            self.scorer_name(scorer),
            resolve(self.get, scorer, Scorer),
            self.labels(scorer),
            self.store.score(started.score),
        )

    def scorer_name(self, scorer: str) -> str:
        held = self.holder("scorer", scorer)
        return held[1].name if held and held[1].name else self.title(scorer)

    def scored_by(self, digest: str) -> list[RunStarted]:
        scorings = set(self.store.reaching(digest, "scoring"))
        return [
            run
            for run in self.runs()
            if any(s.scoring in scorings for s in self.store.scores_of(run.run))
        ]

    def unscored(self, run: RunStarted) -> list[str]:
        given = self.store.scores_of(run.run)
        keys: set[ItemKey] | None = None
        found: list[str] = []
        for edit, _ in self.scorers_for(run):
            try:
                scoring = self.scoring(run, edit.digest)
            except Ambiguous:
                found.append(edit.digest)
                continue
            if scoring is None:
                continue
            under = [s for s in given if s.scoring == scoring.digest]
            if under and keys is None:
                keys = {i.key for i in self.store.run(run.run).items}
            views = len(resolve(self.get, edit.digest, Scorer).views)
            if not any(self._whole(s, keys or set(), views) for s in under):
                found.append(edit.digest)
        return found

    def _whole(self, started: ScoreStarted, keys: set[ItemKey], views: int) -> bool:
        score = self.store.score(started.score)
        if score.finished is None:
            return False
        calls = (c.call for i in score.items for c in i.judge_calls)
        if any(call.error == STOPPED for call in calls):
            return False
        expected = {(k, v) for k in keys for v in range(views)}
        return expected <= {(i.key, i.view) for i in score.items}

    def outstanding(self) -> list[tuple[RunStarted, list[str]]]:
        runs = self.runs()
        finished = self.store.finished([r.run for r in runs])
        return [
            (run, scorers)
            for run in runs
            if run.run in finished and (scorers := self.unscored(run))
        ]

    def rendered_again(self, run: Run) -> dict[ItemKey, str | None]:
        registry = self.store.load([run.started.trial])
        items = Items(self.conn, self.inventory, registry.get, run.started.trial)
        found: dict[ItemKey, str | None] = {}
        for item in run.items:
            try:
                prepared = items.item(item.key)
            except (LookupError, StructuralError) as e:
                found[item.key] = str(e)
                continue
            if prepared.vignette != item.vignette:
                found[item.key] = "the vignette at the source isn't the one sent"
            elif fingerprint_request(prepared.body) != item.call.request:
                found[item.key] = "the request renders otherwise now"
            else:
                found[item.key] = None
        return found


def _titled(schema: JsonValue) -> str | None:
    match schema:
        case {"title": str() as title}:
            return title
        case _:
            return None

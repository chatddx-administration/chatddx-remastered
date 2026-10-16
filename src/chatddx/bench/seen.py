from collections.abc import Callable, Iterable, Mapping, Sequence
from functools import partial
from typing import Literal
from uuid import UUID

from pydantic import JsonValue

from chatddx.catalog import About, Edit, Subject, latest
from chatddx.catalog.threads import picked, recipe as recipe_of
from chatddx.catalog.titles import short
from chatddx.factors.base import (
    Component,
    Finding,
    StructuralError,
    iter_refs,
    resolve,
)
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Case, CleanupOp, Vignette
from chatddx.factors.engine import LocalEngine, RemoteEngine, served_model_name
from chatddx.factors.facts import Landing, ModelFacts, model_name, model_of
from chatddx.factors.request import (
    Compilation,
    Purpose,
    Recipe,
    Skeleton,
    Translations,
    compile_request,
    compiled,
    landings,
    render,
)
from chatddx.factors.scoring import Expectation, Judge, Scorer, Scoring
from chatddx.factors.trial import Trial
from chatddx.facts import Facts, lints
from chatddx.identity import Person, collaborates, owns, preferred, sees
from chatddx.inventory import Inventory
from chatddx.ledger import (
    ItemKey,
    Run,
    RunStarted,
    ScoreStarted,
    fingerprint_request,
)
from chatddx.rig import rig
from chatddx.runner.gate import Refused
from chatddx.runner.prepare import Items
from chatddx.runner.score import judge_at
from chatddx.runner.send import STOPPED
from chatddx.scorers.shipped import problems
from chatddx.store import Catalog, People, Store
from chatddx.store.catalog import Rows
from chatddx.store.store import Connection

from .errors import Ambiguous, NotFound
from .model import KINDS, PLACEHOLDERS, Carried, Family, Graded, Reach
from .variation import PARTS, TriedVariation


class Seen:
    def __init__(self, conn: Connection, person: Person, inventory: Inventory) -> None:
        self.conn: Connection = conn
        self.person: Person = person
        self.inventory: Inventory = inventory
        self.store: Store = Store(conn)
        self.catalog: Catalog = Catalog(conn)
        self.rows: Rows = Rows(conn)
        self.people: People = People(conn)
        self._logins: dict[int, str] = {}
        self._models: dict[str, str | None] = {}
        self._serves: dict[str, str | None] = {}

    def login(self, person: int | None) -> str:
        if person is None:
            return "nobody"
        if person not in self._logins:
            self._logins[person] = self.people.get(person).login
        return self._logins[person]

    # Read when asked, so that facts corrected while a connection lasts are used.
    @property
    def facts(self) -> Facts:
        live = [(e, a) for e, a in self.catalog.heads("facts") if not a.deleted]
        read = dict(self.rows.components([e.digest for e, _ in live]))
        return Facts.of(
            resolve(read.__getitem__, e.digest, ModelFacts)
            for e, _ in sorted(live, key=lambda found: found[0].id)
        )

    def facts_for(self, model: str) -> ModelFacts | None:
        name = model_name(model, self.get)
        return None if name is None else self.facts.models.get(name)

    def owner(self, about: About) -> str:
        return "" if about.owner == self.person.id else self.login(about.owner)

    def threads(self, word: str) -> list[tuple[Edit, About]]:
        return [found for kind in KINDS[word] for found in self.visible(kind)]

    def visible(self, kind: str) -> list[tuple[Edit, About]]:
        return [(e, a) for e, a in self.catalog.heads(kind) if sees(self.person.id, a)]

    def names(self, word: str) -> list[str]:
        return sorted({a.name for _, a in self.threads(word) if a.name is not None})

    def thread(self, word: str, name: str) -> tuple[Edit, str]:
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
        kinds = [kind for kind, held in addresses.items() if name in held]
        match kinds:
            case [kind]:
                return self._named(
                    [(e, a.name, a) for e, a in seen[kind]], name, word
                ), name
            case []:
                raise NotFound(f"no {word} {name!r} for {self.person.login}")
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
        seen = sees(self.person.id, about) or (
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
        return [
            (e, a)
            for e, a in self.catalog.heads(kind)
            if a.deleted and a.owner == self.person.id
        ]

    def about(self, thread: int) -> About:
        return self.catalog.about(Subject(thread=thread))

    def holder(
        self, word: str, digest: str, recipe: Recipe | None = None
    ) -> tuple[Edit, About] | None:
        held = [
            ((e, a), a.owner)
            for e, a in self.threads(word)
            if e.digest == digest
            and (recipe is None or recipe_of(self.rows, e) == recipe)
        ]
        return next(iter(preferred(self.person.id, held)), None)

    def get(self, digest: str) -> Component:
        return self.store.get(digest)

    def title(self, digest: str | None) -> str:
        return "—" if digest is None else self.catalog.title_of(digest)

    def model(self, engine: str) -> str | None:
        if engine not in self._models:
            registry = self.store.load([engine])
            self._models[engine] = model_name(engine, registry.get)
        return self._models[engine]

    def model_of(self, engine: str) -> str | None:
        if engine not in self._serves:
            stored = self.rows.kind(engine) is not None
            self._serves[engine] = model_of(engine, self.get) if stored else None
        return self._serves[engine]

    def model_at(self, name: str) -> str:
        model = self.model_of(self.endpoint(name))
        if model is None:
            raise ValueError(f"endpoint {name!r} serves no model")
        return model

    def endpoint(self, name: str) -> str:
        engine = self.inventory.endpoint(name).engine
        if self.rows.kind(engine) is None:
            raise NotFound(
                f"endpoint {name!r} serves engine {short(engine)}, which isn't in the "
                + "store: load its World with init-data"
            )
        return engine

    def configuration(self, name: str) -> TriedVariation:
        edit, found = self.thread("configuration", name)
        called = found.removeprefix(f"{self.person.login}/")
        return TriedVariation(edit, called, self.catalog.recipe(edit.thread))

    def chunk(self, part: str, name: str) -> str:
        return self.thread(part, name)[0].digest

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
                what = "model" if part == "model" else f"chunk of {part}"
                raise ValueError(f"{digest} isn't a stored {what}")
            found = found.set(part, digest, self.title(digest))
        return found

    def at(self, variation: TriedVariation, endpoint: str | None) -> tuple[str, str]:
        model = variation.held("model")
        if model is None:
            if endpoint is None:
                raise ValueError(
                    f"{variation.label} names no model: name the endpoint to send it to"
                )
            return endpoint, self.endpoint(endpoint)
        if endpoint is None:
            try:
                endpoint = self.inventory.serving_model(
                    model, self.model_of, self.title(model)
                )
            except LookupError as e:
                raise ValueError(str(e)) from None
        engine = self.endpoint(endpoint)
        if self.model_of(engine) != model:
            raise ValueError(
                f"endpoint {endpoint!r} serves another model than {variation.label}'s, "
                + f"{self.title(model)}"
            )
        return endpoint, engine

    def skeleton(self, variation: TriedVariation, into: str | None = None) -> Skeleton:
        recipe = variation.varied
        if into is None and (not variation.parts or recipe is None):
            return resolve(self.get, variation.configuration.digest, Skeleton)
        if recipe is None:
            raise StructuralError(f"{variation.label} has no translations into {into}")
        registry = self.store.load(s.digest for s in iter_refs(recipe))
        return compile_request(
            recipe, registry.get, self.compiled_with(variation), into
        )

    # The facts the configuration was compiled against, so that a translation of it
    # differs from it by its texts only.
    def compiled_with(self, variation: TriedVariation) -> ModelFacts | None:
        recipe = variation.varied
        if recipe is None:
            return None
        made = variation.configuration.compilation
        if not variation.parts and made is not None:
            pinned = resolve(self.get, made, Compilation).facts
            return None if pinned is None else resolve(self.get, pinned, ModelFacts)
        return self.facts_for(recipe.model)

    def landed(self, variation: TriedVariation) -> dict[str, Landing]:
        recipe = variation.varied
        if recipe is None:
            return {}
        registry = self.store.load(s.digest for s in iter_refs(recipe))
        found = landings(recipe, registry.get, self.compiled_with(variation))
        return {p: at for p, at in zip(("reasoning", "sampling"), found) if at}

    def own_language(self, variation: TriedVariation) -> str | None:
        recipe = variation.varied
        if recipe is None:
            return self.catalog.language_of(variation.configuration.digest)
        return self.catalog.recipe_language(recipe)

    def translated(self, recipe: Recipe | None) -> list[str]:
        if recipe is None or recipe.translations is None:
            return []
        return list(resolve(self.get, recipe.translations, Translations).into)

    def languages(
        self,
        variation: TriedVariation,
        cases: Sequence[str],
        known: Mapping[str, str | None] | None = None,
    ) -> list[Carried]:
        own = self.own_language(variation)
        held = dict(known) if known is not None else self.catalog.languages_of(cases)
        into = self.translated(variation.varied)

        def sent_in(language: str | None) -> str | None:
            if language is None or language == own:
                return None
            if language not in into and own is None:
                return None
            return language

        sent = {case: sent_in(held.get(case)) for case in cases}
        found: list[Carried] = []
        if written := [c for c in cases if sent[c] is None]:
            found.append(Carried(own, written, self.skeleton(variation)))
        for language in sorted({s for s in sent.values() if s is not None}):
            some = [c for c in cases if sent[c] == language]
            if language not in into:
                refused = f"{variation.label} has no translations into {language}"
                found.append(Carried(language, some, refused=refused))
                continue
            try:
                skeleton = self.skeleton(variation, language)
            except StructuralError as e:
                found.append(Carried(language, some, refused=str(e)))
                continue
            found.append(Carried(language, some, skeleton, translated=True))
        return found

    def served(self, engine: str) -> str:
        found = self.get(engine)
        if not isinstance(found, LocalEngine | RemoteEngine):
            raise StructuralError(f"{engine} is a {found.kind_name}, not an engine")
        return served_model_name(found, self.get)

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
        ids = self.rows.families()
        known = self.catalog.abouts([Subject(family=f) for f in ids])
        return [
            (f, a) for f in ids if sees(self.person.id, a := known[Subject(family=f)])
        ]

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
        case = self._cases([id])[id] if sees(self.person.id, about) else None
        if case is None:
            raise NotFound(f"no case {id} for {self.person.login}")
        return Family(id, about, case)

    def tags(self) -> list[str]:
        return sorted({tag for _, about in self._families() for tag in about.tags})

    def expectation_schemas(self, case: str) -> list[str]:
        heads = [
            self.catalog.head(t).digest
            for t in self.catalog.expectations_of(case)
            if sees(self.person.id, self.about(t))
        ]
        held = (resolve(self.get, d, Expectation) for d in heads)
        return sorted({e.expectation_schema for e in held})

    def expectation(self, case: str, schema: str) -> Expectation | None:
        digest = self._expectations_for([case], schema)[case]
        return None if digest is None else resolve(self.get, digest, Expectation)

    def shared(self, case: str, schema: str) -> list[tuple[Edit, About]]:
        held = self.catalog.expecting([case], schema)[case]
        return [(e, a) for e, a in held if collaborates(self.person.id, a)]

    def expectation_choices(
        self, cases: Sequence[str], schema: str
    ) -> dict[str, dict[int, str]]:
        return {
            case: {e.thread: e.digest for e, a in held if owns(self.person.id, a)}
            for case, held in self.catalog.expecting(cases, schema).items()
        }

    def _expectations_for(self, cases: list[str], schema: str) -> dict[str, str | None]:
        choices = self.expectation_choices(cases, schema)
        try:
            return {case: picked(case, held) for case, held in choices.items()}
        except LookupError as e:
            raise Ambiguous(str(e)) from None

    def trial(
        self,
        skeleton: Skeleton,
        engine: str,
        cases: list[str],
        seeds: Sequence[int],
        cleanup: tuple[CleanupOp, ...] = (),
    ) -> tuple[Registry, Trial]:
        registry = self.store.load(
            [engine, *cases, *(s.digest for s in skeleton.refs())]
        )
        _ = registry.add(skeleton)
        trial = Trial(
            skeleton=skeleton.digest,
            engine=engine,
            cases=tuple(cases),
            cleanup=cleanup,
            seeds=tuple(seeds),
        )
        _ = registry.add(trial)
        return registry, trial

    def findings(
        self,
        variation: TriedVariation,
        engine: str,
        seed: int,
        families: list[Family] | None = None,
        carried: list[Carried] | None = None,
    ) -> list[Finding]:
        skeleton = self.skeleton(variation)
        if skeleton.purpose == "judge":
            return self._judged(skeleton, engine, seed, variation.recipe is None)
        if families is None:
            held = self._cases([f for f, _ in self._families()]).values()
            first = next((c for c in held if c is not None), None)
            if first is None:
                return []
            registry, trial = self.trial(skeleton, engine, [first], (seed,))
            if variation.recipe is None:
                self.add_compilations(registry, skeleton.digest)
            return lints(registry, self.facts, [trial.digest])
        known = {f.case: f.about.language for f in families}
        if carried is None:
            carried = self.languages(variation, list(known), known)
        found: list[Finding] = []
        for each in carried:
            if each.skeleton is None:
                found.append(left_out(each, variation.configuration.digest))
                continue
            registry, trial = self.trial(each.skeleton, engine, each.cases, (seed,))
            if variation.recipe is None:
                self.add_compilations(registry, each.skeleton.digest)
            languages = partial(
                _language_in,
                {**known, trial.skeleton: each.language},
                self.catalog.language_of,
            )
            for finding in lints(registry, self.facts, [trial.digest], languages):
                if finding not in found:
                    found.append(finding)
        return found

    def _judged(
        self, skeleton: Skeleton, engine: str, seed: int, by_hand: bool
    ) -> list[Finding]:
        registry = self.store.load([engine, *(s.digest for s in skeleton.refs())])
        _ = registry.add(skeleton)
        if by_hand:
            self.add_compilations(registry, skeleton.digest)
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
        for case, held in self.expectation_choices(cases, schema).items():
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

    def compiled(
        self,
        recipe: Recipe,
        facts: ModelFacts | None | Literal["current"] = "current",
        into: str | None = None,
    ) -> tuple[Registry, Compilation]:
        registry = self.store.load(s.digest for s in iter_refs(recipe))
        if facts == "current":
            facts = self.facts_for(recipe.model)
        if facts is not None:
            _ = registry.add(facts)
        skeleton, compilation = compiled(recipe, registry.get, rig(), facts, into)
        _ = registry.add(skeleton)
        _ = registry.add(compilation)
        return registry, compilation

    def linted(self, digest: str) -> list[Finding]:
        registry = self.store.load([digest])
        if isinstance(paired := registry.get(digest), Trial | Judge):
            self.add_compilations(registry, paired.skeleton)
        return lints(registry, self.facts, [digest], self.catalog.language_of)

    # src/chatddx/factors/lint.py:_made_for reads them from the registry.
    def add_compilations(self, registry: Registry, skeleton: str) -> None:
        for compilation in self.store.compilations(skeleton):
            _ = registry.add(compilation)
            if compilation.facts is not None:
                _ = registry.add(self.get(compilation.facts))
            if compilation.recipe.model not in registry:
                _ = registry.add(self.get(compilation.recipe.model))

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
        held = self.expectation_choices([case], schema)[case]
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
            if s.run is not None and owns(self.person.id, known[s])
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
        if not owns(self.person.id, about) or not found:
            raise NotFound(f"no run {run} of yours")
        return found[0]

    def started_with(self, run: UUID) -> UUID | None:
        return self.catalog.about(Subject(run=run)).started_with

    def together(self, first: UUID) -> list[RunStarted]:
        found = self.runs()
        known = self.catalog.abouts([Subject(run=r.run) for r in found])
        return [
            r for r in found if first in (r.run, known[Subject(run=r.run)].started_with)
        ]

    def ran(self, run: UUID) -> tuple[Edit, dict[str, str | None]] | None:
        about = self.catalog.about(Subject(run=run))
        edit = None if about.varied is None else self.rows.edit(about.varied)
        return None if edit is None else (edit, about.replaced)

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
        name = self.catalog.about(Subject(run=run.run)).name or self.title(
            trial.skeleton
        )
        into = {c.into for c in self.store.compilations(trial.skeleton)}
        sent = (
            f", in {next(iter(into))}, translated"
            if len(into) == 1 and None not in into
            else ""
        )
        return f"{name} × {where} × {cases}{sent} (seed {seeds})"

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


def _language_in(
    known: Mapping[str, str | None], otherwise: Callable[[str], str | None], digest: str
) -> str | None:
    return known[digest] if digest in known else otherwise(digest)


def left_out(carried: Carried, subject: str) -> Finding:
    cases = (
        "1 case is" if len(carried.cases) == 1 else f"{len(carried.cases)} cases are"
    )
    return Finding(
        code="translations.missing",
        message=f"{cases} in {carried.language}, and left out: {carried.refused}",
        subject=subject,
    )


def _titled(schema: JsonValue) -> str | None:
    match schema:
        case {"title": str() as title}:
            return title
        case _:
            return None

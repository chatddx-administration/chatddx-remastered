import re
from collections.abc import Callable, Iterable, Mapping, Sequence
from functools import partial
from typing import Literal
from uuid import UUID

from pydantic import JsonValue

from chatddx.catalog import About, Edit, Subject, read, threads, titles
from chatddx.catalog.language import language_of, languages_of, recipe_language
from chatddx.catalog.titles import short
from chatddx.factors.base import (
    Component,
    Finding,
    StructuralError,
    iter_refs,
    resolve,
)
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Appendix, Case, CleanupOp, Vignette
from chatddx.factors.engine import Model, model_of, served_model_name
from chatddx.factors.facts import Landing, ModelFacts
from chatddx.factors.request import (
    RECIPE_PARTS,
    Compilation,
    Purpose,
    Recipe,
    Skeleton,
    Translations,
    compile_request,
    compiled as compile_recipe,
    landings,
)
from chatddx.factors.scoring import Expectation, Judge, Scorer, Scoring
from chatddx.factors.trial import Trial
from chatddx.facts import Facts, lints
from chatddx.identity import Person, collaborates, owns, preferred, sees
from chatddx.inventory import Inventory
from chatddx.ledger import ItemKey, RunStarted, ScoreStarted
from chatddx.rig import rig
from chatddx.runner.gate import Refused
from chatddx.runner.score import judge_at
from chatddx.runner.send import STOPPED
from chatddx.scorers.shipped import problems
from chatddx.store import Catalog, People, Rows, Store
from chatddx.store.store import Connection

from .errors import Ambiguous, NotFound
from .model import (
    KINDS,
    PLACEHOLDERS,
    Carried,
    Endpoint,
    Family,
    Graded,
    Reach,
    word_of,
)
from .variation import TriedVariation

# A case's title, as src/chatddx/catalog/titles.py:_describe_case writes it.
WITH = re.compile(r"^(?P<family>.+?) with (?P<appendices>.+)$")

NONE = "none"

_ALL_KINDS = tuple(kind for held in KINDS.values() for kind in held)


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
        self._models: dict[str, Model] = {}

    def login(self, person: int | None) -> str:
        if person is None:
            return "nobody"
        if person not in self._logins:
            self._logins[person] = self.people.get(person).login
        return self._logins[person]

    # Read when asked, so that facts corrected while a connection lasts are used.
    @property
    def facts(self) -> Facts:
        live = [(e, a) for e, a in threads.heads(self.rows, "facts") if not a.deleted]
        fetched = dict(self.rows.components([e.digest for e, _ in live]))
        return Facts.of(
            resolve(fetched.__getitem__, e.digest, ModelFacts)
            for e, _ in sorted(live, key=lambda found: found[0].id)
        )

    def threads(
        self,
        word: str,
        *,
        deleted: bool = False,
        purpose: Purpose | None = None,
        answering: str | None = None,
    ) -> list[tuple[Edit, About]]:
        found = [f for kind in KINDS[word] for f in self._visible(kind, deleted)]
        if purpose is None and answering is None:
            return found
        if word != "configuration":
            raise ValueError(
                f"only a configuration has a purpose and an answer: {word}"
            )
        fetched = dict(self.rows.components([e.digest for e, _ in found]))
        held = {
            e.digest: resolve(fetched.__getitem__, e.digest, Skeleton) for e, _ in found
        }
        return [
            (e, a)
            for e, a in found
            if (purpose is None or held[e.digest].purpose == purpose)
            and (
                answering is None or _titled(held[e.digest].output_schema) == answering
            )
        ]

    def _visible(self, kind: str, deleted: bool = False) -> list[tuple[Edit, About]]:
        return [
            (e, a)
            for e, a in threads.heads(self.rows, kind)
            if (
                a.deleted and a.owner == self.person.id
                if deleted
                else sees(self.person.id, a)
            )
        ]

    def thread(
        self, found: int | str, word: str | None = None, *, deleted: bool = False
    ) -> tuple[Edit, About]:
        if isinstance(found, str):
            return self._named_thread(found, word)
        about = read.about(self.rows, Subject(thread=found))
        held = self.rows.thread(found)
        seen = sees(self.person.id, about) or (
            deleted and about.deleted and about.owner == self.person.id
        )
        if (
            held is None
            or not seen
            or (word is not None and held.kind not in KINDS[word])
        ):
            raise NotFound(f"no {word or 'thread'} {found} for {self.person.login}")
        return threads.head(self.rows, found), about

    def _named_thread(self, name: str, word: str | None) -> tuple[Edit, About]:
        kinds = KINDS[word] if word is not None else _ALL_KINDS
        what = word or "thread"
        seen = {kind: self._visible(kind) for kind in kinds}
        addresses = {
            kind: {
                address
                for _, a in found
                for address in (a.name, self._qualified(a.name, a.owner))
                if address is not None
            }
            for kind, found in seen.items()
        }
        match [kind for kind, held in addresses.items() if name in held]:
            case [kind]:
                return self._named(
                    [((e, a), a.name, a) for e, a in seen[kind]], name, what
                )
            case []:
                raise NotFound(f"no {what} {name!r} for {self.person.login}")
            case several:
                raise Ambiguous(f"{what} {name!r} names a {' and a '.join(several)}")

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

    def holder(
        self, digest: str, recipe: Recipe | None = None
    ) -> tuple[Edit, About] | None:
        held = [
            (found, owner)
            for found, owner in self._held(digest)
            if recipe is None or threads.recipe(self.rows, found[0]) == recipe
        ]
        return next(iter(preferred(self.person.id, held)), None)

    def title(self, digest: str) -> str:
        named = [(a.name, o) for (_, a), o in self._held(digest) if a.name is not None]
        found = next(iter(preferred(self.person.id, named)), None)
        return titles.title_of(self.rows, digest) if found is None else found

    def _held(self, digest: str) -> list[tuple[tuple[Edit, About], int | None]]:
        held = read.heads_holding(self.rows, [digest])
        known = read.abouts(self.rows, [Subject(thread=t) for t in held])
        return [
            ((e, a), a.owner)
            for t, e in held.items()
            if sees(self.person.id, a := known[Subject(thread=t)])
        ]

    def endpoint(self, name: str) -> Endpoint:
        try:
            spec = self.inventory.endpoint(name)
        except LookupError as e:
            raise NotFound(str(e)) from None
        model = self._model_of(spec.engine)
        if model is None:
            raise NotFound(
                f"endpoint {name!r} serves engine {short(spec.engine)}, which isn't in "
                + "the store: load its World with init-data"
            )
        return Endpoint(name, spec, model)

    def _model_of(self, engine: str) -> Model | None:
        if engine not in self._models:
            if self.rows.kind(engine) is None:
                return None
            self._models[engine] = model_of(engine, self.store.get)
        return self._models[engine]

    def _served_model(self, engine: str) -> str | None:
        model = self._model_of(engine)
        return None if model is None else model.digest

    def at(self, variation: TriedVariation, endpoint: str | None) -> Endpoint:
        model = variation.held("model")
        if model is None:
            if endpoint is None:
                raise ValueError(
                    f"{variation.label} names no model: name the endpoint to send it to"
                )
            return self.endpoint(endpoint)
        if endpoint is None:
            try:
                endpoint = self.inventory.serving(
                    model, self._served_model, f"model {self.title(model)}"
                )
            except LookupError as e:
                raise ValueError(str(e)) from None
        found = self.endpoint(endpoint)
        if found.model.digest != model:
            raise ValueError(
                f"endpoint {endpoint!r} serves another model than {variation.label}'s, "
                + f"{self.title(model)}"
            )
        return found

    def variation(
        self,
        configuration: int | str,
        parts: Mapping[str, str | None] | None = None,
        head: int | None = None,
    ) -> TriedVariation:
        edit, about = self.thread(configuration, "configuration")
        if isinstance(configuration, str):
            name = configuration.removeprefix(f"{self.person.login}/")
        else:
            name = about.name or titles.title(self.rows, edit.thread)
        if head is not None and head != edit.id:
            earlier = self.rows.edit(head)
            if earlier is None or earlier.thread != edit.thread:
                raise NotFound(f"no edit {head} of configuration {edit.thread}")
            edit = earlier
        found = TriedVariation(edit, name, threads.recipe(self.rows, edit))
        for part, digest in (parts or {}).items():
            if part not in RECIPE_PARTS:
                raise ValueError(
                    f"no part {part!r}: the parts are {', '.join(RECIPE_PARTS)}"
                )
            if digest is not None and self.rows.kind(digest) not in KINDS[part]:
                what = "model" if part == "model" else f"chunk of {part}"
                raise ValueError(f"{digest} isn't a stored {what}")
            found = found.set(
                part, digest, NONE if digest is None else self.title(digest)
            )
        return found

    def skeleton(self, variation: TriedVariation, into: str | None = None) -> Skeleton:
        recipe = variation.varied
        if into is None and (not variation.parts or recipe is None):
            return resolve(self.store.get, variation.configuration.digest, Skeleton)
        if recipe is None:
            raise StructuralError(f"{variation.label} has no translations into {into}")
        registry = self.store.load(s.digest for s in iter_refs(recipe))
        return compile_request(
            recipe, registry.get, compiled_with(self, variation), into
        )

    def landed(self, variation: TriedVariation) -> dict[str, Landing]:
        recipe = variation.varied
        if recipe is None:
            return {}
        registry = self.store.load(s.digest for s in iter_refs(recipe))
        found = landings(recipe, registry.get, compiled_with(self, variation))
        return {p: at for p, at in zip(("reasoning", "sampling"), found) if at}

    def languages(
        self, variation: TriedVariation, cases: Sequence[str]
    ) -> list[Carried]:
        recipe = variation.varied
        own = (
            language_of(self.rows, variation.configuration.digest)
            if recipe is None
            else recipe_language(self.rows, recipe)
        )
        held = self._languages_of(cases)
        into = (
            []
            if recipe is None or recipe.translations is None
            else list(resolve(self.store.get, recipe.translations, Translations).into)
        )

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

    # Optimization: Reusing families' language reduces query-load.
    def _languages_of(self, cases: Sequence[str]) -> dict[str, str | None]:
        known = {c: f.about.language for f in self.families() for c in f.cases}
        if rest := [c for c in cases if c not in known]:
            known |= languages_of(self.rows, rest)
        return {c: known[c] for c in cases}

    def request(
        self, variation: TriedVariation, engine: str | None, seed: int
    ) -> dict[str, JsonValue]:
        model = (
            "‹model›" if engine is None else served_model_name(engine, self.store.get)
        )
        return self.skeleton(variation).render(
            model=model, seed=seed, fills=PLACEHOLDERS
        )

    def findings(
        self,
        variation: TriedVariation,
        engine: str,
        seed: int,
        carried: Sequence[Carried] | None = None,
    ) -> list[Finding]:
        skeleton = self.skeleton(variation)
        by_hand = variation.recipe is None
        if skeleton.purpose == "judge":
            registry = self.store.load([engine, *(s.digest for s in skeleton.refs())])
            _ = registry.add(skeleton)
            if by_hand:
                add_compilations(self, registry, skeleton.digest)
            judge = Judge(skeleton=skeleton.digest, engine=engine, seeds=(seed,))
            _ = registry.add(judge)
            return lints(registry, self.facts, [judge.digest])
        if carried is None:
            first = next(iter(self.families()), None)
            if first is None:
                return []
            registry, made = trial(self, skeleton, engine, [first.case], (seed,))
            if by_hand:
                add_compilations(self, registry, skeleton.digest)
            return lints(registry, self.facts, [made.digest])
        known = self._languages_of([c for each in carried for c in each.cases])
        found: list[Finding] = []
        for each in carried:
            if each.skeleton is None:
                found.append(left_out(each, variation.configuration.digest))
                continue
            registry, made = trial(self, each.skeleton, engine, each.cases, (seed,))
            if by_hand:
                add_compilations(self, registry, each.skeleton.digest)
            languages = partial(
                _language_in,
                {**known, made.skeleton: each.language},
                partial(language_of, self.rows),
            )
            for finding in lints(registry, self.facts, [made.digest], languages):
                if finding not in found:
                    found.append(finding)
        return found

    def reach(self, variation: TriedVariation, families: list[Family]) -> list[Reach]:
        skeleton = self.skeleton(variation)
        if skeleton.purpose == "judge":
            return []
        schema = skeleton.output_schema
        cases = [f.case for f in families]
        data: dict[str, tuple[dict[str, JsonValue], set[str]]] = {}
        found: list[Reach] = []
        named = [
            (e, a.name or titles.title(self.rows, e.thread), s)
            for e, a, s in self.scorers()
        ]
        for edit, name, scorer in sorted(named, key=lambda s: s[1]):
            labels = labels_of(self, edit)
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

    def _expected(
        self, cases: list[str], schema: str
    ) -> tuple[dict[str, JsonValue], set[str]]:
        heads: dict[str, str] = {}
        several: set[str] = set()
        for case, held in choices(self, cases, schema).items():
            try:
                digest = threads.picked(case, held)
            except LookupError:
                several.add(case)
                continue
            if digest is not None:
                heads[case] = digest
        fetched = dict(self.rows.components(list(heads.values())))
        data = {
            c: resolve(fetched.__getitem__, d, Expectation).data
            for c, d in heads.items()
        }
        return data, several

    def families(self, tags: Iterable[str] = ()) -> list[Family]:
        wanted = set(tags)
        tagged = [(f, a) for f, a in self._families() if not wanted or wanted & a.tags]
        held = self._cases([f for f, _ in tagged])
        found = [Family(f, a, *held[f]) for f, a in tagged if f in held]
        return sorted(found, key=lambda f: f.name)

    def _families(self) -> list[tuple[int, About]]:
        ids = self.rows.families()
        known = read.abouts(self.rows, [Subject(family=f) for f in ids])
        return [
            (f, a) for f in ids if sees(self.person.id, a := known[Subject(family=f)])
        ]

    def _cases(
        self, families: list[int]
    ) -> dict[int, tuple[Vignette, tuple[str, ...]]]:
        current = {b.family: b.vignette for b in self.rows.bindings(families)}
        held: dict[Vignette, list[str]] = {}
        for digest, vignette in self.rows.bound_to(current.values(), "case"):
            held.setdefault(vignette, []).append(digest)
        found: dict[int, tuple[Vignette, tuple[str, ...]]] = {}
        for family, vignette in current.items():
            bare = Case(vignette=vignette).digest
            cases = sorted(held.get(vignette, []), key=lambda d: (d != bare, d))
            if cases:
                found[family] = (vignette, tuple(cases))
        return found

    def family(self, found: int | str) -> Family:
        if isinstance(found, str):
            return self._named(
                [(f, f.name, f.about) for f in self.families()], found, "case"
            )
        about = read.about(self.rows, Subject(family=found))
        held = self._cases([found]).get(found) if sees(self.person.id, about) else None
        if held is None:
            raise NotFound(f"no case {found} for {self.person.login}")
        return Family(found, about, *held)

    def case_titled(self, title: str) -> tuple[Family, str]:
        found = WITH.match(title)
        if found is None:
            family = self.family(title)
            return family, family.case
        family = self.family(found["family"])
        names = [name.strip() for name in found["appendices"].split(",")]
        held = {
            about.name: edit.digest
            for edit, about in self._visible("appendix")
            if about.name is not None
            and resolve(self.store.get, edit.digest, Appendix).vignette
            == family.vignette
        }
        if missing := [name for name in names if name not in held]:
            raise NotFound(f"no appendix {', '.join(missing)} of {family.name}")
        appendices = tuple(held[n] for n in names)
        made = Case(vignette=family.vignette, appendices=appendices).digest
        if made not in family.cases:
            raise NotFound(f"no case {title} for {self.person.login}")
        return family, made

    def expectation_schemas(self, case: str) -> list[str]:
        heads = [
            e.digest
            for e, a in threads.expecting(self.rows, [case])[case]
            if sees(self.person.id, a)
        ]
        held = (resolve(self.store.get, d, Expectation) for d in heads)
        return sorted({e.expectation_schema for e in held})

    def expectation(self, case: str, schema: str) -> Expectation | None:
        digest = picked(self, [case], schema)[case]
        return None if digest is None else resolve(self.store.get, digest, Expectation)

    def shared(self, case: str, schema: str) -> list[tuple[Edit, About]]:
        held = threads.expecting(self.rows, [case], schema)[case]
        return [(e, a) for e, a in held if collaborates(self.person.id, a)]

    def scorers(
        self, run: RunStarted | None = None
    ) -> list[tuple[Edit, About, Scorer]]:
        found = [
            (e, a, resolve(self.store.get, e.digest, Scorer))
            for e, a in self.threads("scorer")
        ]
        if run is None:
            return found
        trial = resolve(self.store.get, run.trial, Trial)
        schema = resolve(self.store.get, trial.skeleton, Skeleton).output_schema
        return [s for s in found if self._applies(s[2], trial, schema)]

    def _applies(self, scorer: Scorer, trial: Trial, schema: JsonValue) -> bool:
        if not all(v.offered_by(schema) for v in scorer.views):
            return False
        try:
            for judge in scorer.judges:
                _ = judge_at(self.inventory, self.store.get, judge, trial.cases)
        except (ValueError, Refused):
            return False
        return True

    def labels(self, scorer: str) -> dict[int, str]:
        held = self.holder(scorer)
        if held is not None:
            return labels_of(self, held[0])
        seen = {e.thread: a.owner for e, a in self.threads("scorer")}
        earlier = [
            (e, seen[e.thread])
            for e in self.rows.edits_holding([scorer])
            if e.thread in seen
        ]
        held_before = sorted(preferred(self.person.id, earlier), key=lambda e: e.id)
        return labels_of(self, held_before[-1]) if held_before else {}

    def runs(
        self,
        *,
        reaching: str | None = None,
        scored_by: str | None = None,
        started_with: UUID | None = None,
    ) -> list[RunStarted]:
        involved = [s for s in self.rows.involving(self.person.id) if s.run]
        known = read.abouts(self.rows, involved)
        found = self.store.started(
            [
                s.run
                for s in involved
                if s.run is not None and owns(self.person.id, known[s])
            ]
        )
        if reaching is not None:
            trials = set(self.store.reaching(reaching, "trial"))
            for made in self.store.reaching(reaching, "compilation"):
                skeleton = resolve(self.store.get, made, Compilation).skeleton
                trials.update(self.store.reaching(skeleton, "trial"))
            found = [r for r in found if r.trial in trials]
        if scored_by is not None:
            scorings = set(self.store.reaching(scored_by, "scoring"))
            found = [
                r
                for r in found
                if any(s.scoring in scorings for s in self.store.scores_of(r.run))
            ]
        if started_with is not None:
            found = [
                r
                for r in found
                if started_with in (r.run, known[Subject(run=r.run)].started_with)
            ]
        return found

    def run(self, found: UUID | str | None = None) -> RunStarted:
        if isinstance(found, UUID):
            about = read.about(self.rows, Subject(run=found))
            started = self.store.started([found])
            if not owns(self.person.id, about) or not started:
                raise NotFound(f"no run {found} of yours")
            return started[0]
        runs = self.runs()
        if found is None:
            if not runs:
                raise NotFound(f"{self.person.login} has no runs")
            return runs[0]
        match [r for r in runs if str(r.run).startswith(found)]:
            case [run]:
                return run
            case []:
                raise NotFound(f"no run of yours starts with {found!r}")
            case several:
                raise Ambiguous(f"{len(several)} runs of yours start with {found!r}")

    def described(self, run: RunStarted) -> str:
        trial = resolve(self.store.get, run.trial, Trial)
        where = self.title(trial.engine) if run.endpoint is None else run.endpoint.name
        cases = (
            self.title(trial.cases[0])
            if len(trial.cases) == 1
            else f"{len(trial.cases)} cases"
        )
        seeds = ", ".join(str(seed) for seed in trial.seeds)
        name = read.about(self.rows, Subject(run=run.run)).name or self.title(
            trial.skeleton
        )
        into = {c.into for c in self.store.compilations(trial.skeleton)}
        sent = (
            f", in {next(iter(into))}, translated"
            if len(into) == 1 and None not in into
            else ""
        )
        return f"{name} × {where} × {cases}{sent} (seed {seeds})"

    def unscored(self, run: RunStarted) -> list[str]:
        given = self.store.scores_of(run.run)
        keys: set[ItemKey] | None = None
        found: list[str] = []
        for edit, _, scorer in self.scorers(run):
            try:
                built = scoring(self, run, edit.digest)
            except Ambiguous:
                found.append(edit.digest)
                continue
            if built is None:
                continue
            under = [s for s in given if s.scoring == built.digest]
            if under and keys is None:
                keys = {i.key for i in self.store.run(run.run).items}
            views = len(scorer.views)
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

    def scores_of(self, run: RunStarted, every: bool = False) -> list[Graded]:
        given = self.store.scores_of(run.run)
        if every:
            return [self._graded(started) for started in given]
        found: dict[str, ScoreStarted] = {}
        for started in given:
            scorer = resolve(self.store.get, started.scoring, Scoring).scorer
            _ = found.setdefault(scorer, started)
        return sorted((self._graded(s) for s in found.values()), key=lambda g: g.name)

    def score_of(self, run: RunStarted, score: UUID) -> Graded:
        given = self.store.scores_of(run.run)
        found = next((s for s in given if s.score == score), None)
        if found is None:
            raise NotFound(f"no score {score} of run {run.run}")
        return self._graded(found)

    def _graded(self, started: ScoreStarted) -> Graded:
        scorer = resolve(self.store.get, started.scoring, Scoring).scorer
        return Graded(
            self.title(scorer),
            resolve(self.store.get, scorer, Scorer),
            self.labels(scorer),
            self.store.score(started.score),
        )


def choices(seen: Seen, cases: Sequence[str], schema: str) -> dict[str, dict[int, str]]:
    return {
        case: {e.thread: e.digest for e, a in held if owns(seen.person.id, a)}
        for case, held in threads.expecting(seen.rows, cases, schema).items()
    }


def picked(seen: Seen, cases: Sequence[str], schema: str) -> dict[str, str | None]:
    try:
        return {
            case: threads.picked(case, held)
            for case, held in choices(seen, cases, schema).items()
        }
    except LookupError as e:
        raise Ambiguous(str(e)) from None


def scoring(seen: Seen, run: RunStarted, scorer: str) -> Scoring | None:
    trial = resolve(seen.store.get, run.trial, Trial)
    schema = resolve(seen.store.get, scorer, Scorer).expectation_schema
    held = picked(seen, list(trial.cases), schema)
    found = tuple(e for e in held.values() if e is not None)
    return Scoring(scorer=scorer, expectations=found) if found else None


def labels_of(seen: Seen, edit: Edit) -> dict[int, str]:
    return {
        position: label
        for (part, position), label in read.labels(seen.rows, edit.id).items()
        if part == "view"
    }


def worded(seen: Seen, thread: int) -> tuple[Edit, About, str]:
    found = seen.rows.thread(thread)
    word = word_of(None if found is None else found.kind)
    edit, about = seen.thread(thread, None if word == "thread" else word)
    return edit, about, word


def compiled_with(seen: Seen, variation: TriedVariation) -> ModelFacts | None:
    recipe = variation.varied
    if recipe is None:
        return None
    made = variation.configuration.compilation
    if not variation.parts and made is not None:
        pinned = resolve(seen.store.get, made, Compilation).facts
        return None if pinned is None else resolve(seen.store.get, pinned, ModelFacts)
    return seen.facts.about(recipe.model, seen.store.get)


def compiled(
    seen: Seen,
    recipe: Recipe,
    facts: ModelFacts | None | Literal["current"] = "current",
    into: str | None = None,
) -> tuple[Registry, Compilation]:
    registry = seen.store.load(s.digest for s in iter_refs(recipe))
    if facts == "current":
        facts = seen.facts.about(recipe.model, seen.store.get)
    if facts is not None:
        _ = registry.add(facts)
    skeleton, compilation = compile_recipe(recipe, registry.get, rig(), facts, into)
    _ = registry.add(skeleton)
    _ = registry.add(compilation)
    return registry, compilation


def trial(
    seen: Seen,
    skeleton: Skeleton,
    engine: str,
    cases: list[str],
    seeds: Sequence[int],
    cleanup: tuple[CleanupOp, ...] = (),
) -> tuple[Registry, Trial]:
    registry = seen.store.load([engine, *cases, *(s.digest for s in skeleton.refs())])
    _ = registry.add(skeleton)
    made = Trial(
        skeleton=skeleton.digest,
        engine=engine,
        cases=tuple(cases),
        cleanup=cleanup,
        seeds=tuple(seeds),
    )
    _ = registry.add(made)
    return registry, made


def linted(seen: Seen, digest: str) -> list[Finding]:
    registry = seen.store.load([digest])
    if isinstance(paired := registry.get(digest), Trial | Judge):
        add_compilations(seen, registry, paired.skeleton)
    return lints(registry, seen.facts, [digest], partial(language_of, seen.rows))


# src/chatddx/factors/lint.py:_made_for reads them from the registry.
def add_compilations(seen: Seen, registry: Registry, skeleton: str) -> None:
    for compilation in seen.store.compilations(skeleton):
        _ = registry.add(compilation)
        if compilation.facts is not None:
            _ = registry.add(seen.store.get(compilation.facts))
        if compilation.recipe.model not in registry:
            _ = registry.add(seen.store.get(compilation.recipe.model))


def check_scorer(scorer: Scorer) -> None:
    if found := problems(scorer):
        raise ValueError("; ".join(found))


def check_kind(
    seen: Seen, thread: int, word: str, held: Component | TriedVariation
) -> None:
    kind = threads.thread(seen.rows, thread).kind
    given = "skeleton" if isinstance(held, TriedVariation) else held.kind_name
    if kind != given:
        raise ValueError(f"{word} {thread} holds {kind} components, not {given}")


def check_expecting(
    seen: Seen,
    expectation: Expectation,
    thread: int | None,
    then: str = "edit that one",
) -> None:
    case, schema = expectation.case, expectation.expectation_schema
    held = choices(seen, [case], schema)[case]
    if others := sorted(t for t in held if t != thread):
        raise ValueError(
            f"{seen.person.login} has their own expectation of {seen.title(case)} "
            + f"under {seen.title(schema)}, in thread {others[0]}: {then}"
        )


def left_out(carried: Carried, subject: str) -> Finding:
    cases = (
        "1 case is" if len(carried.cases) == 1 else f"{len(carried.cases)} cases are"
    )
    return Finding(
        code="translations.missing",
        message=f"{cases} in {carried.language}, and left out: {carried.refused}",
        subject=subject,
    )


def _language_in(
    known: Mapping[str, str | None], otherwise: Callable[[str], str | None], digest: str
) -> str | None:
    return known[digest] if digest in known else otherwise(digest)


def _titled(schema: JsonValue) -> str | None:
    match schema:
        case {"title": str() as title}:
            return title
        case _:
            return None

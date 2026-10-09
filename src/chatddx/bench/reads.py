from chatddx.catalog import About, Edit
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.scoring import Scorer, Scoring
from chatddx.factors.select import reaches
from chatddx.factors.trial import Trial
from chatddx.identity import Person
from chatddx.ledger import RunStarted
from chatddx.store import Catalog, People, Store
from chatddx.store.store import Connection

from .errors import Ambiguous, NotFound


# What one person sees: the live threads and families they own or collaborate on, and
# the runs they own.
class Reads:
    def __init__(self, conn: Connection, person: Person) -> None:
        self._store: Store = Store(conn)
        self._catalog: Catalog = Catalog(conn)
        self._people: People = People(conn)
        self._person: Person = person

    def threads(self, kind: str) -> list[tuple[Edit, About]]:
        return self._catalog.visible(kind, self._person.id)

    # A name is matched whole first, since names may hold a slash, as
    # `plan (Qwen/Qwen3-8B-AWQ)` does; only then is it read as `OWNER/NAME`.
    def thread(self, kind: str, name: str) -> Edit:
        seen = [(e, a) for e, a in self.threads(kind) if a.name == name]
        own = [e for e, a in seen if a.owner == self._person.id]
        shared = [e for e, _ in seen]
        if not seen and "/" in name:
            login, rest = name.split("/", 1)
            owner = self._people.find(login)
            if owner is not None:
                own = []
                shared = [
                    e
                    for e, a in self.threads(kind)
                    if a.name == rest and a.owner == owner.id
                ]
        for choices in (own, shared):
            if len(choices) == 1:
                return choices[0]
            if choices:
                threads = ", ".join(str(e.thread) for e in choices)
                raise Ambiguous(
                    f"{kind} {name!r} names threads {threads}; name one as OWNER/NAME"
                )
        raise NotFound(f"no {kind} named {name!r}")

    def families(self) -> list[tuple[int, About]]:
        return self._catalog.visible_families(self._person.id)

    def runs(self) -> list[RunStarted]:
        involved = [s for s in self._catalog.involving(self._person.id) if s.run]
        known = self._catalog.abouts(involved)
        owned = [
            s.run
            for s in involved
            if s.run is not None
            and (a := known[s]).owner == self._person.id
            and not a.deleted
        ]
        return self._store.started(owned)

    def run(self, prefix: str) -> RunStarted:
        found = [r for r in self.runs() if str(r.run).startswith(prefix)]
        match found:
            case [run]:
                return run
            case []:
                raise NotFound(f"no run of yours starts with {prefix!r}")
            case _:
                raise Ambiguous(f"{len(found)} runs of yours start with {prefix!r}")

    def reaching(self, digest: str) -> list[RunStarted]:
        trials = set(self._store.reaching(digest, "trial"))
        return [r for r in self.runs() if r.trial in trials]

    # The scorer threads whose every view reaches the run's output schema, the check
    # `check_score` warns with as `view.unreachable`.
    def scorers(self, run: RunStarted) -> list[tuple[Edit, About]]:
        return [
            (e, a) for e, a in self.threads("scorer") if self._applies(e.digest, run)
        ]

    # Each of the run's cases is scored against the expectation the catalog picks for
    # the person (`Catalog.expectation_for`); none when no case has one.
    def scoring(self, run: RunStarted, scorer: str) -> Scoring | None:
        trial = resolve(self._store.get, run.trial, Trial)
        schema = resolve(self._store.get, scorer, Scorer).expectation_schema
        found = [
            expectation
            for case in trial.cases
            if (
                expectation := self._catalog.expectation_for(
                    case, self._person.id, schema
                )
            )
            is not None
        ]
        return Scoring(scorer=scorer, expectations=tuple(found)) if found else None

    def _applies(self, scorer: str, run: RunStarted) -> bool:
        trial = resolve(self._store.get, run.trial, Trial)
        schema = resolve(self._store.get, trial.skeleton, Skeleton).output_schema
        views = resolve(self._store.get, scorer, Scorer).views
        return all(reaches(schema, v.output) for v in views)

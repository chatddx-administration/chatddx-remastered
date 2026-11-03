from fastapi import APIRouter, Depends

from chatddx.bench import Bench, NotFound
from chatddx.bench.breakdown import Estimate, Point, View
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Scorer
from chatddx.factors.select import field as field_of

from . import schemas
from .people import BenchDep
from .standing import baseline_cases
from .state import no_store
from .threads import edits, thread as threads_detail, threads

router = APIRouter(tags=["threads"])


@router.get("/threads/{thread}/breakdown", dependencies=[Depends(no_store)])
def breakdown(bench: BenchDep, thread: int) -> schemas.Broken:
    """How the configuration fared on the World's baseline cases: its versions, those
    that compile to one skeleton pooled, each view's estimate over every replicate of
    every case and its difference from the version before, case by case; each
    baseline gathering's means, how far its repeats were from it, and its failed
    items, time and tokens; and the person's other configurations' latest baselines
    on the views they share. Costs a read of each of the person's runs and their
    scores, rows read before held."""
    tag = bench.inventory.baseline
    cases = baseline_cases(bench)
    if tag is None or not cases:
        raise NotFound("this World names no baseline cases")
    numbered = {e.id: n for n, e in enumerate(edits(bench, thread), start=1)}
    login = bench.person.login
    owned = {
        t.id: t
        for t in threads(bench, "configuration", purpose="generation", owner=login)
    }
    held = bench.breakdown(thread, cases, list(owned))
    views = list(held.views)

    def point(p: Point) -> schemas.BrokenPoint:
        return schemas.BrokenPoint(
            started=p.started,
            at=p.at,
            version=numbered.get(p.version, 0),
            means=[p.means.get(v) for v in views],
            spread=[p.spread.get(v) for v in views],
            alike=p.alike[0],
            compared=p.alike[1],
            languages=[
                schemas.BrokenLanguage(language=k, cases=n)
                for k, n in sorted(p.languages.items(), key=lambda kv: kv[0] or "")
            ],
            failed=p.failed,
            seconds=p.seconds,
            tokens=p.tokens,
            stale=p.stale,
        )

    shown = owned.get(thread) or threads_detail(bench, thread)
    return schemas.Broken(
        name=shown.name or shown.title,
        tag=tag,
        cases=len(cases),
        views=_views(bench, views),
        versions=[
            schemas.BrokenVersion(
                digest=v.digest,
                versions=sorted({numbered[i] for i in v.versions if i in numbered}),
                estimates=[_estimated(v.estimates.get(view)) for view in views],
                paired=[_estimated(v.paired.get(view)) for view in views],
                points=[point(p) for p in v.points],
            )
            for v in held.timeline
        ],
        peers=[
            schemas.BrokenPeer(
                id=p.configuration,
                name=owned[p.configuration].name or owned[p.configuration].title,
                means=[p.point.means.get(v) if v in p.shared else None for v in views],
                point=point(p.point),
            )
            for p in held.peers
        ],
    )


def _views(bench: Bench, views: list[View]) -> list[schemas.BrokenView]:
    titles = {t.head.digest: t.name or t.title for t in threads(bench, "scorer")}
    found: list[schemas.BrokenView] = []
    for digest, i in views:
        scorer = resolve(bench.store.get, digest, Scorer)
        label = bench.labels(digest).get(i, str(i))
        found.append(
            schemas.BrokenView(
                scorer=digest,
                view=i,
                label=f"{titles.get(digest, bench.title(digest))} › {label}",
                field=field_of(scorer.views[i].expectation),
            )
        )
    return found


def _estimated(e: Estimate | None) -> schemas.Estimated | None:
    return None if e is None else schemas.Estimated(mean=e.mean, half=e.half, n=e.n)

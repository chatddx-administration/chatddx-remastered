from collections.abc import Collection, Hashable
from datetime import datetime
from uuid import UUID

from chatddx.catalog import Subject, read
from chatddx.factors.base import resolve
from chatddx.factors.gatherer import gather
from chatddx.factors.gathering import Center, Gathering, Seeding
from chatddx.factors.trial import Trial
from chatddx.ledger import RunStarted

from .seen import Seen


def gathering(
    seen: Seen,
    center: Center,
    seedings: tuple[Seeding, ...],
    started_with: UUID | None = None,
    among: Collection[UUID] | None = None,
) -> Gathering | None:
    """The person's runs about the center gathered into the seedings, a group for each
    configuration they varied and the latest run first, kept to those started with
    `started_with` and among `among` when given. A component's runs are those whose
    trial or a score reaches it, a seed's those whose trial holds it. Reads the
    person's runs twice for a component and once for a seed, and each run's trial for
    a seed and its configuration's edit."""
    if center.component is None:
        runs = [
            r
            for r in seen.runs(started_with=started_with)
            if center.seed in resolve(seen.store.get, r.trial, Trial).seeds
        ]
    else:
        reaching = seen.runs(reaching=center.component, started_with=started_with)
        scored = seen.runs(scored_by=center.component, started_with=started_with)
        runs = list({r.run: r for r in (*reaching, *scored)}.values())
    if among is not None:
        runs = [r for r in runs if r.run in among]
    abouts = read.abouts(seen.rows, [Subject(run=r.run) for r in runs])
    found: list[tuple[Hashable, UUID, str]] = []
    for r in sorted(runs, key=lambda r: r.at, reverse=True):
        about = abouts[Subject(run=r.run)]
        edit = None if about.varied is None else seen.rows.edit(about.varied)
        key = r.trial if edit is None else edit.thread
        found.append((key, r.run, r.trial))
    return gather(center, seedings, found, seen.store.get)


# Policy: a case's latest gathering under a configuration is the runs started together
# with its latest run reaching it, those of them reaching it, so that whatever started
# it, a review's 3+1 or a trial of many cases, the latest start stands for the case.
def gatherings(
    seen: Seen, cases: Collection[str]
) -> dict[tuple[str, int], list[RunStarted]]:
    """Each case's latest gathering under each configuration the person varied and ran
    it under, by case and the configuration's thread, the latest run first. Reads the
    person's runs, their catalog rows and each one's trial."""
    runs = seen.runs()
    abouts = read.abouts(seen.rows, [Subject(run=r.run) for r in runs])
    latest: dict[tuple[str, int], tuple[datetime, UUID]] = {}
    together: dict[tuple[str, int, UUID], list[RunStarted]] = {}
    for r in runs:
        about = abouts[Subject(run=r.run)]
        varied = None if about.varied is None else seen.rows.edit(about.varied)
        if varied is None:
            continue
        first = about.started_with or r.run
        for case in set(resolve(seen.store.get, r.trial, Trial).cases) & set(cases):
            at = (case, varied.thread)
            together.setdefault((*at, first), []).append(r)
            if at not in latest or latest[at][0] < r.at:
                latest[at] = (r.at, first)
    return {
        at: sorted(together[(*at, first)], key=lambda r: r.at, reverse=True)
        for at, (_, first) in latest.items()
    }

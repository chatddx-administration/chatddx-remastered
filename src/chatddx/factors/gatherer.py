from collections.abc import Hashable, Iterable
from uuid import UUID

from .base import Resolver
from .gathering import Center, Gathered, Gathering, Seeding, fits


def gather(
    center: Center,
    seedings: tuple[Seeding, ...],
    found: Iterable[tuple[Hashable, UUID, str]],
    get: Resolver,
) -> Gathering | None:
    """The gathering of the runs found, each given by its group's key, its id and its
    trial, or None when no run fits a seeding. In each group each seeding in turn takes
    the first run found that fits it, so the order found is the preference; each try
    resolves the run's trial."""
    candidates: dict[Hashable, list[tuple[UUID, str]]] = {}
    for key, run, trial in found:
        candidates.setdefault(key, []).append((run, trial))
    filled: list[dict[str, tuple[UUID, str]]] = []
    for held in candidates.values():
        taken: dict[str, tuple[UUID, str]] = {}
        for s in seedings:
            bound = {name: trial for name, (_, trial) in taken.items()}
            used = {run for run, _ in taken.values()}
            for run, trial in held:
                if run not in used and fits(s, trial, bound, get) is None:
                    taken[s.name] = (run, trial)
                    break
        if taken:
            filled.append(taken)
    if not filled:
        return None
    # Policy: groups go by their trials, so that the same runs gather alike whatever
    # their groups' keys and the order they were found in.
    filled.sort(key=lambda t: [t[s.name][1] if s.name in t else "" for s in seedings])
    gathered = tuple(
        Gathered(group=i, seeding=s.name, run=t[s.name][0], trial=t[s.name][1])
        for i, t in enumerate(filled)
        for s in seedings
        if s.name in t
    )
    return Gathering(center=center, seedings=seedings, gathered=gathered)

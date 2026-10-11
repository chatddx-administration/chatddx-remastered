from collections.abc import Collection

from chatddx.factors.base import resolve
from chatddx.factors.scoring import Scorer
from chatddx.ledger import RunStarted
from chatddx.runner.run import Runner, Running
from chatddx.runner.score import score_run

from .configurations import keep_compilation
from .model import Graded
from .variation import TriedVariation
from .view import Seen


# The variation run on `cases` with one seed, at `endpoint`; nothing is sent until
# `Running.send`.
def start(
    seen: Seen, variation: TriedVariation, endpoint: str, cases: list[str], seed: int
) -> Running:
    skeleton = seen.skeleton(variation)
    registry, trial = seen.trial(skeleton, seen.endpoint(endpoint), cases, seed)
    runner = Runner(seen.conn, seen.inventory, seen.person)
    running = runner.start(trial, registry, endpoint)
    _ = keep_compilation(seen, variation)
    return running


# A finished run scored under every scorer that applies to it, or those of `scorers`, as
# each scoring would be built now.
def score(
    seen: Seen, run: RunStarted, scorers: Collection[str] | None = None
) -> list[Graded]:
    found: list[Graded] = []
    for edit, about in seen.scorers_for(run):
        if scorers is not None and edit.digest not in scorers:
            continue
        name = about.name or seen.catalog.title(edit.thread)
        scorer = resolve(seen.get, edit.digest, Scorer)
        labels = seen.labels_of(edit)
        try:
            scoring = seen.scoring(run, edit.digest)
            if scoring is None:
                raise LookupError("none of the run's cases has an expectation")
            registry = seen.store.load([scoring.scorer, *scoring.expectations])
            score, findings = score_run(
                seen.conn, run.run, scoring, registry, seen.person
            )
        except (LookupError, TypeError, NotImplementedError) as e:
            found.append(Graded(name, scorer, labels, refused=str(e)))
            continue
        found.append(Graded(name, scorer, labels, score, findings))
    return found

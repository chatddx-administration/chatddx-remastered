from collections.abc import Collection

from chatddx.factors.base import resolve
from chatddx.factors.scoring import Scorer
from chatddx.ledger import RunStarted
from chatddx.runner.run import Runner, Running
from chatddx.runner.score import score_run

from .configurations import keep_compilation
from .model import Graded
from .variation import TriedVariation
from .view import View


# The variation run on `cases` with one seed, at `endpoint`; nothing is sent until
# `Running.send`.
def start(
    view: View, variation: TriedVariation, endpoint: str, cases: list[str], seed: int
) -> Running:
    skeleton = view.skeleton(variation)
    registry, trial = view.trial(skeleton, view.endpoint(endpoint), cases, seed)
    runner = Runner(view.conn, view.inventory, view.person)
    running = runner.start(trial, registry, endpoint)
    _ = keep_compilation(view, variation)
    return running


# A finished run scored under every scorer that applies to it, or those of `scorers`, as
# each scoring would be built now.
def score(
    view: View, run: RunStarted, scorers: Collection[str] | None = None
) -> list[Graded]:
    found: list[Graded] = []
    for edit, about in view.scorers_for(run):
        if scorers is not None and edit.digest not in scorers:
            continue
        name = about.name or view.catalog.title(edit.thread)
        scorer = resolve(view.get, edit.digest, Scorer)
        labels = view.labels_of(edit)
        try:
            scoring = view.scoring(run, edit.digest)
            if scoring is None:
                raise LookupError("none of the run's cases has an expectation")
            registry = view.store.load([scoring.scorer, *scoring.expectations])
            score, findings = score_run(
                view.conn, run.run, scoring, registry, view.person
            )
        except (LookupError, TypeError, NotImplementedError) as e:
            found.append(Graded(name, scorer, labels, refused=str(e)))
            continue
        found.append(Graded(name, scorer, labels, score, findings))
    return found

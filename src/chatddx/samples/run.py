from collections.abc import Callable, Generator
from contextlib import ExitStack, contextmanager

from chatddx.bench import Bench, TriedVariation
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Scorer
from chatddx.factors.trial import Trial
from chatddx.fake_vllm.script import Script
from chatddx.fake_vllm.server import serving
from chatddx.ledger import RunStarted
from chatddx.runner.run import Event, Running, Streamed
from chatddx.runner.score import judge_at

from .fakes import fake_at
from .sample import Sample

NONE = "none"


def variation(bench: Bench, sample: Sample) -> TriedVariation:
    engine = bench.endpoint(sample.endpoint)
    tried = bench.configuration(sample.configuration, engine)
    for part, chunk in sample.set.items():
        digest = None if chunk == NONE else bench.chunk(part, chunk, engine)
        tried = tried.set(part, digest, chunk)
    return tried


def ran_before(bench: Bench, sample: Sample) -> RunStarted | None:
    skeleton = bench.skeleton(variation(bench, sample))
    engine = bench.endpoint(sample.endpoint)
    cases = [bench.case_titled(name)[1] for name in sample.cases]
    _, trial = bench.trial(skeleton, engine, cases, sample.seed)
    return next((r for r in bench.runs() if r.trial == trial.digest), None)


def run(bench: Bench, sample: Sample) -> RunStarted:
    tried = variation(bench, sample)
    cases = [bench.case_titled(name)[1] for name in sample.cases]
    fake = fake_at(bench.inventory, bench.get, sample.endpoint)
    script = Script(sample.turns) if sample.turns else None
    with serving([fake], script=script):
        running = bench.start(tried, sample.endpoint, cases, sample.seed)
        running.send(_halting(running, sample.stop_after))
    if sample.unfinished:
        return running.started
    _ = running.finish()
    if sample.scored:
        with _judging(bench, running.started):
            _ = bench.score(running.started)
    return running.started


def _halting(running: Running, after: int | None) -> Callable[[Event], None]:
    def heard(event: Event) -> None:
        streamed = isinstance(event, Streamed) and event.delta.tokens
        if after is not None and streamed and streamed >= after:
            running.halt()

    return heard


@contextmanager
def _judging(bench: Bench, run: RunStarted) -> Generator[None]:
    cases = resolve(bench.get, run.trial, Trial).cases
    at = {
        judge_at(bench.inventory, bench.get, judge, cases)[2]
        for edit, _ in bench.scorers_for(run)
        for judge in resolve(bench.get, edit.digest, Scorer).judges
    }
    with ExitStack() as stack:
        for name in sorted(at):
            fake = fake_at(bench.inventory, bench.get, name)
            _ = stack.enter_context(serving([fake]))
        yield

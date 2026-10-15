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
from .read import ScriptedRun

NONE = "none"


def variation(bench: Bench, scripted: ScriptedRun) -> TriedVariation:
    tried = bench.configuration(scripted.configuration)
    if tried.recipe is not None:
        engine = bench.endpoint(scripted.endpoint)
        tried = tried.set("engine", engine, bench.title(engine))
    for part, chunk in scripted.set.items():
        digest = None if chunk == NONE else bench.chunk(part, chunk)
        tried = tried.set(part, digest, chunk)
    return tried


def ran_before(bench: Bench, scripted: ScriptedRun) -> RunStarted | None:
    skeleton = bench.skeleton(variation(bench, scripted))
    engine = bench.endpoint(scripted.endpoint)
    cases = [bench.case_titled(name)[1] for name in scripted.cases]
    _, trial = bench.trial(skeleton, engine, cases, (scripted.seed,))
    return next((r for r in bench.runs() if r.trial == trial.digest), None)


def run(bench: Bench, scripted: ScriptedRun) -> RunStarted:
    tried = variation(bench, scripted)
    cases = [bench.case_titled(name)[1] for name in scripted.cases]
    fake = fake_at(bench.inventory, bench.get, scripted.endpoint)
    script = Script(scripted.turns) if scripted.turns else None
    with serving([fake], script=script):
        running = bench.start(tried, scripted.endpoint, cases, (scripted.seed,))
        running.send(_halting(running, scripted.stop_after))
    if scripted.unfinished:
        return running.started
    _ = running.finish()
    if scripted.scored:
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

from collections.abc import Callable, Generator, Mapping
from contextlib import ExitStack, contextmanager

from chatddx.bench import Bench, Carried, TriedVariation
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Judge
from chatddx.factors.trial import Trial, replicates
from chatddx.fake_vllm.script import Script
from chatddx.fake_vllm.served import Served
from chatddx.fake_vllm.server import serving
from chatddx.ledger import RunStarted
from chatddx.runner import Halt, RunEvent, Streamed

from .fakes import fake_at
from .read import ScriptedRun

NONE = "none"


def variation(bench: Bench, scripted: ScriptedRun) -> TriedVariation:
    tried = bench.variation(scripted.configuration)
    if tried.recipe is not None:
        model = bench.endpoint(scripted.endpoint).model.digest
        tried = tried.set("model", model, bench.title(model))
    for part, chunk in scripted.set.items():
        digest = None if chunk == NONE else bench.thread(chunk, part)[0].digest
        tried = tried.set(part, digest, chunk)
    return tried


def ran_before(bench: Bench, scripted: ScriptedRun) -> RunStarted | None:
    tried = variation(bench, scripted)
    cases = [bench.case_titled(name)[1] for name in scripted.cases]
    skeleton = _sent(scripted, bench.languages(tried, cases)).skeleton
    assert skeleton is not None
    engine = bench.endpoint(scripted.endpoint).engine
    trial = Trial(
        skeleton=skeleton.digest,
        engine=engine,
        cases=tuple(cases),
        seeds=replicates(skeleton, (scripted.seed,)),
    )
    return next((r for r in bench.runs() if r.trial == trial.digest), None)


def _sent(scripted: ScriptedRun, carried: list[Carried]) -> Carried:
    match carried:
        case [one] if one.skeleton is not None:
            return one
        case _:
            said = "; ".join(f"{c.language}: {c.refused or 'sent'}" for c in carried)
            raise ValueError(
                f"{scripted.configuration}: a scripted run's cases are sent in one "
                + f"language, not as {said}"
            )


def run(bench: Bench, scripted: ScriptedRun) -> RunStarted:
    tried = variation(bench, scripted)
    cases = [bench.case_titled(name)[1] for name in scripted.cases]
    _ = _sent(scripted, bench.languages(tried, cases))
    fake = fake_at(bench.inventory, bench.store.get, scripted.endpoint)
    script = Script(scripted.turns) if scripted.turns else None
    with serving([fake], script=script):
        started = bench.start(tried, scripted.endpoint, cases, (scripted.seed,))
        running = started.first
        halt = Halt()
        running.send(_halting(halt, scripted.stop_after), halt)
    if scripted.unfinished:
        return running.started
    _ = running.finish()
    if scripted.scored:
        with judging(bench, running.started):
            _ = bench.score(running.started)
    return running.started


def _halting(halt: Halt, after: int | None) -> Callable[[RunEvent], None]:
    def heard(event: RunEvent) -> None:
        streamed = isinstance(event, Streamed) and event.delta.tokens
        if after is not None and streamed and streamed >= after:
            halt.set()

    return heard


@contextmanager
def judging(
    bench: Bench, run: RunStarted, fakes: Mapping[str, Served] | None = None
) -> Generator[None]:
    at = {
        bench.judged(resolve(bench.store.get, judge, Judge)).name
        for _, _, scorer in bench.scorers(run)
        for judge in scorer.judges
    }
    with ExitStack() as stack:
        for name in sorted(at):
            held = None if fakes is None else fakes.get(name)
            fake = held or fake_at(bench.inventory, bench.store.get, name)
            _ = stack.enter_context(serving([fake]))
        yield

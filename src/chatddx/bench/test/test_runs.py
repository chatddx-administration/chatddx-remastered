import pytest

from chatddx import settings
from chatddx.bench import Bench, NotFound, OverQuota
from chatddx.catalog import Subject
from chatddx.curation import Plan
from chatddx.factors.base import resolve
from chatddx.factors.trial import Execution, Trial
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.runner.run import Event, ItemEnded
from chatddx.store.store import Connection
from chatddx.test.world import LINES, QWEN, world_facts


@pytest.mark.usefixtures("fake")
def test_a_run_keeps_its_seeds_cleanup_execution_and_canaries_and_again_too(
    conn: Connection, world: Inventory, alice: Person, plan: Plan
):
    bench = Bench(conn, alice, world, world_facts())
    variation = bench.configuration(LINES, bench.endpoint(QWEN))
    probe = plan.named("canary_set", "probe").digest
    cleanup = ("newlines.lf@1", "strip@1")
    running = bench.start(
        variation,
        QWEN,
        [bench.family("crlf").case],
        (3, 5),
        cleanup,
        Execution(concurrency=2),
        probe,
    )
    running.send()
    _ = running.finish()

    started = bench.run_by_id(running.run)
    trial = resolve(bench.get, started.trial, Trial)
    assert (trial.seeds, trial.cleanup) == ((3, 5), cleanup)
    assert (started.execution, started.canaries) == (Execution(concurrency=2), probe)
    assert len(bench.store.run(running.run).items) == 2

    again = bench.again(started, (8,)).started
    repeated = resolve(bench.get, again.trial, Trial)
    assert (repeated.seeds, repeated.cleanup) == ((8,), cleanup)
    assert (again.execution, again.canaries) == (started.execution, probe)


@pytest.mark.usefixtures("fake")
def test_a_run_says_what_it_varied_and_running_again_too(
    conn: Connection, world: Inventory, alice: Person
):
    bench = Bench(conn, alice, world, world_facts())
    engine = bench.endpoint(QWEN)
    named = bench.configuration(LINES, engine)
    off = bench.chunk("reasoning", "off", engine)
    cases = [bench.family("crlf").case]

    plain = bench.start(named, QWEN, cases, (7,)).started
    assert bench.ran(plain.run) == (named.configuration, {})
    varied = named.set("reasoning", off, "off")
    started = bench.start(varied, QWEN, cases, (7,)).started
    ran = (named.configuration, {"reasoning": off})
    assert bench.ran(started.run) == ran
    assert bench.catalog.about(Subject(run=started.run)).name == varied.label
    assert bench.ran(bench.again(started, (8,)).run) == ran


def test_a_run_holds_its_cases_times_its_seeds_in_items(
    bench: Bench, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(settings, "ITEMS_PER_RUN", 3)
    variation = bench.configuration(LINES, bench.endpoint(QWEN))
    cases = [bench.family(name).case for name in ("crlf", "svenska")]
    with pytest.raises(OverQuota, match="at most 3 items, not 4"):
        _ = bench.start(variation, QWEN, cases, (1, 2))


@pytest.mark.usefixtures("fake")
def test_a_person_resumes_their_own_unfinished_run(
    conn: Connection, world: Inventory, alice: Person, bob: Person
):
    bench = Bench(conn, alice, world, world_facts())
    variation = bench.configuration(LINES, bench.endpoint(QWEN))
    cases = [bench.family(name).case for name in ("crlf", "svenska")]
    running = bench.start(variation, QWEN, cases, (7,))

    def stop(event: Event) -> None:
        if isinstance(event, ItemEnded):
            running.stop()

    running.send(stop)
    others = Bench(conn, bob, world, world_facts())
    with pytest.raises(NotFound, match=f"no run {running.run} of yours"):
        _ = others.resume(running.run)

    resumed = bench.resume(running.run)
    resumed.send()
    _ = resumed.finish()
    assert len(bench.store.run(running.run).items) == 2


@pytest.mark.usefixtures("fake")
def test_a_run_takes_its_sources_cleanup_and_its_endpoint_s_canaries_and_execution(
    conn: Connection, world: Inventory, alice: Person, plan: Plan
):
    probe = plan.named("canary_set", "probe").digest
    execution = Execution(timeout_s=60, retries=1)
    sources = dict(world.sources)
    sources["test"] = sources["test"].model_copy(
        update={"cleanup": ("strip@1", "newlines.lf@1")}
    )
    endpoints = dict(world.endpoints)
    endpoints[QWEN] = endpoints[QWEN].model_copy(
        update={"canaries": probe, "execution": execution}
    )
    declared = world.model_copy(update={"sources": sources, "endpoints": endpoints})
    bench = Bench(conn, alice, declared, world_facts())
    variation = bench.configuration(LINES, bench.endpoint(QWEN))
    cases = [bench.family("crlf").case]

    started = bench.start(variation, QWEN, cases, (7,)).started
    trial = resolve(bench.get, started.trial, Trial)
    assert trial.cleanup == ("newlines.lf@1", "strip@1")
    assert (started.execution, started.canaries) == (execution, probe)

    given = bench.start(variation, QWEN, cases, (7,), (), Execution(), probe).started
    assert resolve(bench.get, given.trial, Trial).cleanup == ()
    assert given.execution == Execution()

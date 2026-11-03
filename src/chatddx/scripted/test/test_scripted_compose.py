from datetime import UTC, datetime, timedelta

import pytest

from chatddx.api.standing import baseline_cases, configurations, standing
from chatddx.bench import Bench
from chatddx.catalog import Subject, read
from chatddx.factors.gathering import BASELINE
from chatddx.scripted import composed


@pytest.mark.slow
def test_a_scripted_compose_writes_versions_and_gatherings_of_each_configuration(
    bench: Bench,
) -> None:
    schema = bench.thread("targets", "expectation_schema")[0].digest

    made = composed(bench, schema, gatherings=8, versions=3, seed=3, days=14)

    assert made.gatherings and set(made.gatherings) == set(made.versions)
    assert all(made.versions[name] >= 2 for name in made.gatherings)
    assert any(sorts.get("baseline") for sorts in made.gatherings.values())
    assert sum(n for sorts in made.gatherings.values() for n in sorts.values()) >= 8
    runs = bench.runs()
    abouts = read.abouts(bench.rows, [Subject(run=r.run) for r in runs])
    varied = {abouts[Subject(run=r.run)].varied for r in runs}
    assert len(varied) > len(made.gatherings)
    now = datetime.now(UTC)
    assert min(r.at for r in runs) < now - timedelta(days=7)
    assert max(r.at for r in runs) < now
    finished = bench.store.finished([r.run for r in runs])
    assert all(bench.scores_of(r) for r in runs if r.run in finished)
    cases = baseline_cases(bench)
    stood = standing(bench, configurations(bench), cases, BASELINE, lambda _: [])
    assert any(s.runs for s in stood)

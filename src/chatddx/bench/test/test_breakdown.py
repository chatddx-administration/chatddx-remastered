import pytest

from chatddx.api.standing import baseline_cases, configurations
from chatddx.bench import Bench
from chatddx.scripted import composed


@pytest.mark.slow
def test_a_configuration_s_baselines_are_broken_down_by_what_its_versions_compile_to(
    bench: Bench,
) -> None:
    schema = bench.thread("targets", "expectation_schema")[0].digest
    made = composed(bench, schema, gatherings=8, versions=3, seed=5, days=14)
    cases = baseline_cases(bench)
    owned = configurations(bench)
    by_name = {t.name or t.title: t for t in owned}
    name = max(made.gatherings, key=lambda n: made.gatherings[n].get("baseline", 0))
    thread = by_name[name].id

    held = bench.breakdown(thread, cases, [t.id for t in owned])

    assert held.views and held.timeline
    digests = [p.digest for p in held.timeline]
    assert len(digests) == len(set(digests))
    versions = [v for p in held.timeline for v in p.versions]
    assert versions == sorted(versions)
    for pooled in held.timeline:
        assert pooled.points and set(pooled.estimates) <= set(held.views)
        for point in pooled.points:
            assert point.version in pooled.versions
            assert sum(point.languages.values()) == len(cases)
            alike, of = point.alike
            assert 0 <= alike <= of
            assert 0.0 <= point.failed <= 1.0
    assert held.timeline[0].paired == {}
    assert all(set(p.shared) <= set(held.views) for p in held.peers)
    assert {p.configuration for p in held.peers} <= {t.id for t in owned} - {thread}

    runs = bench.runs()
    first = bench.observed(runs)
    again = bench.observed(runs)
    assert first and all(a.ran is b.ran for a, b in zip(first, again, strict=True))
    assert bench.breakdown(thread, cases, [t.id for t in owned]) == held

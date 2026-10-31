from datetime import UTC, datetime, timedelta

import pytest

from chatddx.bench import Bench
from chatddx.bench.seen import choices
from chatddx.catalog import Subject, read
from chatddx.factors.gathering import REPLICATED, Center
from chatddx.scripted import review
from chatddx.scripted.fared import drawn


@pytest.mark.slow
def test_a_scripted_review_writes_versions_and_evaluations_over_past_weeks(
    bench: Bench,
) -> None:
    case = bench.case_titled("noted")[1]
    schema = bench.thread("targets", "expectation_schema")[0].digest

    made = review(bench, case, schema, gatherings=6, versions=4, seed=3, days=14)

    [thread] = choices(bench, [case], schema)[case]
    written = {e.digest for e in bench.rows.edits([thread])}
    assert (made.gatherings, made.versions) == (6, 4) and len(written) >= 4
    runs = bench.runs(reaching=case)
    abouts = read.abouts(bench.rows, [Subject(run=r.run) for r in runs])
    firsts = {abouts[Subject(run=r.run)].started_with or r.run for r in runs}
    assert len(firsts) == 6
    for first in firsts:
        held = bench.gathering(Center(component=case), REPLICATED, started_with=first)
        assert held is not None
        assert all(len(g) == len(REPLICATED) for g in held.groups())
    now = datetime.now(UTC)
    assert min(r.at for r in runs) < now - timedelta(days=7)
    assert max(r.at for r in runs) < now
    finished = bench.store.finished([r.run for r in runs])
    assert all(bench.scores_of(r) for r in runs if r.run in finished)


def test_what_is_drawn_is_drawn_alike_every_time_and_by_its_inputs() -> None:
    once = drawn(1, "sha256:a", 3, "sha256:s", 0, "reciprocal_rank")
    assert once == drawn(1, "sha256:a", 3, "sha256:s", 0, "reciprocal_rank")
    assert len(once) == 4 and all(v in (0.0, 1.0, 0.5, 1 / 3, 0.25) for v in once)
    every = [drawn(1, f"sha256:{c}", 3, "sha256:s", 0, "mentions") for c in range(200)]
    assert all(v in (0.0, 1.0) for got in every for v in got)
    assert len({sum(got) for got in every}) >= 3
    assert every != [
        drawn(2, f"sha256:{c}", 3, "sha256:s", 0, "mentions") for c in range(200)
    ]

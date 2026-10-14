import pytest

from chatddx.bench import Bench
from chatddx.conftest import Loaded
from chatddx.scripted import RUNS, run, scripted_runs
from chatddx.scripted.test.helpers import UNFINISHED, went
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.test.world import WORLDS, free_world, world_facts

PATH = WORLDS / "sample"
VALID = ("valid", None)
OUTCOMES = {
    "appendix": {"Dutchfall11w with ultrasound": VALID},
    "batch": {
        "Dutchfall12w": ("errored", "HTTP 503: the engine is loading"),
        "Dutchfall13w": VALID,
        "Dutchfall14w": VALID,
        "Dutchfall15w": ("salvaged", UNFINISHED),
    },
    "broken": {"Dutchfall13w": ("completed", UNFINISHED)},
    "invalid": {
        "Dutchfall12w": ("invalid", "at the root: 'sources' is a required property")
    },
    "judged": {"Dutchfall11w": ("completed", None)},
    "remote": {"Dutchfall14w": ("completed", None)},
    "runaway": {
        "Dutchfall14w": ("salvaged", "stopped: nothing but whitespace for 100 tokens")
    },
    "stopped": {"casesfromedn2": ("stopped", None)},
    "typical": {"DutchFall10w": VALID},
    "unfinished": {"Dutchfall15w": VALID},
}


@pytest.fixture
def template(sampled: Loaded) -> str:
    return sampled.name


@pytest.mark.slow
def test_the_sample_world_s_scripted_runs_run_as_they_say(
    conn: Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CHATDDX_SAMPLE_KEY", "sample-key")
    alice = People(conn).find("alice")
    assert alice is not None
    bench = Bench(conn, alice, free_world(PATH), world_facts(PATH))

    ran = {s.name: run(bench, s) for s in scripted_runs(PATH / RUNS)}

    assert {name: went(bench, started) for name, started in ran.items()} == OUTCOMES
    assert not bench.scores_of(ran["unfinished"].run)
    [notes] = [g for g in bench.scores_of(ran["judged"].run) if g.name == "notes"]
    assert notes.score is not None
    assert [len(i.judge_calls) for i in notes.score.items] == [1, 1, 3]

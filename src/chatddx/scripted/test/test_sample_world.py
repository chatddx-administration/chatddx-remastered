import pytest

from chatddx.bench import Bench
from chatddx.scripted import RUNS, run, scripted_runs
from chatddx.scripted.test.helpers import UNFINISHED, went
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.test.helpers import sampled_template
from chatddx.test.world import WORLDS, free_world

__all__ = ["sampled_template"]

PATH = WORLDS / "sample"
VALID = ("valid", None)
OUTCOMES = {
    "appendix": {"dutch-11 with ultrasound": VALID},
    "broken": {"dutch-13": ("completed", UNFINISHED)},
    "invalid": {
        "dutch-12": ("invalid", "at the root: 'sources' is a required property")
    },
    "judged": {"dutch-11": ("completed", None)},
    "remote": {"dutch-14": ("completed", None)},
    "runaway": {
        "dutch-14": ("salvaged", "stopped: nothing but whitespace for 100 tokens")
    },
    "several": {
        "dutch-12": ("errored", "HTTP 503: the engine is loading"),
        "dutch-13": VALID,
        "dutch-14": VALID,
        "dutch-15": ("salvaged", UNFINISHED),
    },
    "stopped": {"akm-02": ("stopped", None)},
    "typical": {"dutch-10": VALID},
    "unfinished": {"dutch-15": VALID},
}


@pytest.mark.slow
def test_the_sample_world_s_scripted_runs_run_as_they_say(
    conn: Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CHATDDX_SAMPLE_KEY", "sample-key")
    alice = People(conn).find("alice")
    assert alice is not None
    bench = Bench(conn, alice, free_world(PATH))

    ran = {s.name: run(bench, s) for s in scripted_runs(PATH / RUNS)}

    assert {name: went(bench, started) for name, started in ran.items()} == OUTCOMES
    assert not bench.scores_of(ran["unfinished"])
    [notes] = [g for g in bench.scores_of(ran["judged"]) if g.name == "notes"]
    assert notes.score is not None
    assert [len(i.judge_calls) for i in notes.score.items] == [1, 1, 3]

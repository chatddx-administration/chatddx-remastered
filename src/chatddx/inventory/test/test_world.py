import shutil
from pathlib import Path

import pytest

from chatddx.inventory import World

WORLDS = Path(__file__).parents[4] / "worlds"


def drawing(tmp_path: Path, world: str, said: str) -> Path:
    _ = shutil.copytree(WORLDS / world, tmp_path / world)
    _ = (tmp_path / world / "synthetic.toml").write_text(said)
    return tmp_path / world


def test_a_world_draws_scores_only_while_its_endpoints_are_on_this_machine(
    tmp_path: Path,
) -> None:
    assert World.load(WORLDS / "test").synthetic is None
    assert World.load(drawing(tmp_path, "sample", "seed = 7\n")).synthetic == 7
    with pytest.raises(LookupError, match="pelle"):
        _ = World.load(drawing(tmp_path, "kompismoln", "seed = 7\n"))
    for said in ("seed = true\n", 'seed = "7"\n', "\n"):
        shutil.rmtree(tmp_path / "sample")
        with pytest.raises(LookupError, match="whole number"):
            _ = World.load(drawing(tmp_path, "sample", said))

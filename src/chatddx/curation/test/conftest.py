import shutil
from pathlib import Path

import pytest

from chatddx.curation import load_cases
from chatddx.curation.plan import SAMPLE
from chatddx.curation.test.sample import FEW, SOME


# The sample data with only FEW's cases, for init-data's --data.
@pytest.fixture
def few(tmp_path: Path) -> Path:
    data = tmp_path / "data"
    _ = shutil.copytree(SAMPLE, data)
    for path in data.glob("cases-*.toml"):
        blocks = path.read_text().split("\n[case.")[1:]
        _ = path.write_text(
            "".join(f"[case.{b}\n" for b in blocks if b.split("]")[0] in FEW)
        )
    assert load_cases(data) == SOME
    return data


# A World whose one source holds FEW's vignettes, each a line of text.
@pytest.fixture
def world(tmp_path: Path) -> Path:
    world = tmp_path / "world"
    (world / "vignettes").mkdir(parents=True)
    for id in SOME:
        _ = (world / "vignettes" / f"{id}.txt").write_text(f"The vignette of {id}.")
    _ = (world / "inventory.toml").write_text('[source.sample]\npath = "vignettes"\n')
    return world

from pathlib import Path

import pytest
from pydantic import ValidationError

from chatddx.factors.base import Fingerprint
from chatddx.factors.cases import Case, Vignette
from chatddx.inventory import DirectorySource, Inventory
from chatddx.inventory.test.memory import MemorySource


def vignettes(root: Path) -> Path:
    directory = root / "vignettes"
    directory.mkdir()
    _ = (directory / "noted.txt").write_bytes(b"A 72-year-old man.\n")
    _ = (directory / "svenska.txt").write_bytes("60-årig kvinna.".encode())
    _ = (directory / "notes.md").write_text("not a vignette")
    return directory


def test_sources_are_declared_in_the_inventory(tmp_path: Path) -> None:
    directory = vignettes(tmp_path)
    path = tmp_path / "inventory.toml"
    _ = path.write_text('[source.test]\npath = "vignettes"\n')
    source = Inventory.load(path).source("test")
    assert isinstance(source, DirectorySource)
    assert (source.name, source.path, source.sensitive) == (
        "test",
        directory.resolve(),
        True,
    )
    with pytest.raises(LookupError, match="no source 'other'"):
        _ = Inventory.load(path).source("other")

    _ = path.write_text('[source.test]\npath = "vignettes"\nsensitive = false\n')
    assert not Inventory.load(path).source("test").sensitive
    _ = path.write_text('[machine.pelle]\naddress = "pelle.km"\n')
    with pytest.raises(
        ValueError,
        match="only 'include', 'source', 'endpoint', 'host', 'cleared' and 'judge'",
    ):
        _ = Inventory.load(path)
    _ = path.write_text('[source.test]\nkind = "s3"\npath = "x"\n')
    with pytest.raises(ValidationError):
        _ = Inventory.load(path)
    _ = path.write_text('[source.test]\nname = "other"\npath = "vignettes"\n')
    with pytest.raises(ValidationError, match="source 'test' is named 'other'"):
        _ = Inventory.load(path)


def test_a_world_takes_sources_and_endpoints_from_another(tmp_path: Path) -> None:
    other = tmp_path / "other"
    other.mkdir()
    directory = vignettes(other)
    _ = (other / "endpoints.toml").write_text(
        '[endpoint.qwen]\nengine = "sha256:' + "c" * 64 + '"\n'
    )
    world = tmp_path / "world"
    world.mkdir()
    _ = (world / "inventory.toml").write_text(
        'include = ["../other/endpoints.toml"]\n\n'
        + '[source.test]\npath = "../other/vignettes"\n'
    )
    inventory = Inventory.load(world / "inventory.toml")
    assert inventory.sources["test"] == DirectorySource(
        name="test", path=directory.resolve()
    )
    assert list(inventory.endpoints) == ["qwen"]


def test_directory_sources_list_fetch_and_make_cases(tmp_path: Path) -> None:
    source = DirectorySource(name="test", path=vignettes(tmp_path))
    assert source.ids() == ["noted", "svenska"]
    assert source.fetch("noted") == b"A 72-year-old man.\n"
    with pytest.raises(LookupError, match="no case 'Missing'"):
        _ = source.fetch("Missing")
    for id in ("../inventory", "sub/case", ".."):
        with pytest.raises(LookupError, match="outside"):
            _ = source.fetch(id)
    assert source.cases() == [
        Case(
            vignette=Vignette(
                source="test",
                id="noted",
                fingerprint=Fingerprint.of(b"A 72-year-old man.\n"),
            ),
        ),
        Case(
            vignette=Vignette(
                source="test",
                id="svenska",
                fingerprint=Fingerprint.of("60-årig kvinna.".encode()),
            ),
        ),
    ]


def test_memory_sources_stand_in_for_tests() -> None:
    source = MemorySource(name="inline", vignettes={"c2": b"two", "c1": b"one"})
    assert source.ids() == ["c1", "c2"]
    assert source.fetch("c1") == b"one"
    assert source.sensitive
    with pytest.raises(LookupError, match="no case 'c3'"):
        _ = source.fetch("c3")

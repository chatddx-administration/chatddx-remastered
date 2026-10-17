from pathlib import Path

import pytest
from pydantic import ValidationError

from chatddx.factors.base import Fingerprint
from chatddx.factors.cases import Case, Vignette
from chatddx.inventory import DirectorySource, Inventory

URL = "http://pelle.km:12009/v1/"


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
        match="only 'include', 'configurations', 'source', 'endpoint', 'host', 'cleared' and 'judge'",
    ):
        _ = Inventory.load(path)
    _ = path.write_text('[source.test]\nkind = "s3"\npath = "x"\n')
    with pytest.raises(ValidationError):
        _ = Inventory.load(path)
    _ = path.write_text('[source.test]\nname = "other"\npath = "vignettes"\n')
    with pytest.raises(ValidationError, match="source 'test' is named 'other'"):
        _ = Inventory.load(path)


def test_a_source_s_cleanup_and_an_endpoint_s_canaries_and_execution_are_declared(
    tmp_path: Path,
) -> None:
    _ = vignettes(tmp_path)
    path = tmp_path / "inventory.toml"
    engine, probe = "sha256:" + "c" * 64, "sha256:" + "d" * 64
    _ = path.write_text(
        '[source.test]\npath = "vignettes"\ncleanup = ["strip@1", "newlines.lf@1"]\n\n'
        + f'[endpoint.qwen]\nengine = "{engine}"\nurl = "{URL}"\nmax_jobs = 2\n'
        + f'canaries = "{probe}"\n\n'
        + "[endpoint.qwen.execution]\nconcurrency = 2\ntimeout_s = 60\n"
    )
    inventory = Inventory.load(path)
    assert inventory.source("test").cleanup == ("strip@1", "newlines.lf@1")
    qwen = inventory.endpoint("qwen")
    assert qwen.canaries == probe
    assert (qwen.execution.concurrency, qwen.execution.timeout_s) == (2, 60)

    _ = path.write_text(
        f'[endpoint.qwen]\nengine = "{engine}"\nurl = "{URL}"\n\n'
        + "[endpoint.qwen.execution]\nconcurrency = 2\n"
    )
    with pytest.raises(ValidationError, match="sends 2 requests at once"):
        _ = Inventory.load(path)
    _ = path.write_text('[source.test]\npath = "vignettes"\ncleanup = ["tidy@1"]\n')
    with pytest.raises(ValidationError):
        _ = Inventory.load(path)


def test_a_world_takes_sources_and_endpoints_from_another(tmp_path: Path) -> None:
    other = tmp_path / "other"
    other.mkdir()
    directory = vignettes(other)
    _ = (other / "endpoints.toml").write_text(
        '[endpoint.qwen]\nengine = "sha256:' + "c" * 64 + f'"\nurl = "{URL}"\n'
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

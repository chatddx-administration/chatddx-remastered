from pathlib import Path

import pytest

from chatddx.inventory import DatabaseSource, DirectorySource, Inventory


def test_an_inventory_declares_a_database_source_by_its_kind(tmp_path: Path) -> None:
    path = tmp_path / "inventory.toml"
    _ = path.write_text('[source.typed]\nkind = "database"\nsensitive = true\n')
    inventory = Inventory.load(path)
    assert inventory.sources["typed"] == DatabaseSource(name="typed")
    with pytest.raises(LookupError, match="source 'typed' isn't a directory source"):
        _ = inventory.source("typed", DirectorySource)

    _ = path.write_text('[source.typed]\nkind = "spreadsheet"\n')
    with pytest.raises(ValueError, match="spreadsheet"):
        _ = Inventory.load(path)


def test_a_source_is_the_one_named_or_the_only_one_of_its_kind(
    tmp_path: Path,
) -> None:
    typed = DatabaseSource(name="typed")
    files = DirectorySource(name="files", path=tmp_path)
    inventory = Inventory(sources={"typed": typed, "files": files})
    assert inventory.source(kind=DirectorySource) == files
    assert inventory.source("files", DirectorySource) == files
    assert inventory.source(kind=DatabaseSource) == inventory.source("typed") == typed
    with pytest.raises(LookupError, match="no source 'other' in the inventory"):
        _ = inventory.source("other", DirectorySource)
    with pytest.raises(
        LookupError,
        match=r"2 sources \(files, typed\) are in the inventory, so one must be named",
    ):
        _ = inventory.source()

    more = DirectorySource(name="more", path=tmp_path)
    inventory = Inventory(sources={"typed": typed, "files": files, "more": more})
    assert inventory.source("more", DirectorySource) == more
    with pytest.raises(
        LookupError,
        match=r"2 directory sources \(files, more\) are in the inventory, so one must",
    ):
        _ = inventory.source(kind=DirectorySource)
    with pytest.raises(LookupError, match="no directory source in the inventory"):
        _ = Inventory(sources={"typed": typed}).source(kind=DirectorySource)

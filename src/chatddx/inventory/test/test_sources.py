from pathlib import Path

import pytest

from chatddx.inventory import DatabaseSource, DirectorySource, Inventory


def test_an_inventory_declares_a_database_source_by_its_kind(tmp_path: Path) -> None:
    path = tmp_path / "inventory.toml"
    _ = path.write_text('[source.typed]\nkind = "database"\nsensitive = true\n')
    inventory = Inventory.load(path)
    assert inventory.sources["typed"] == DatabaseSource(name="typed")
    with pytest.raises(
        LookupError,
        match="source 'typed' is a database source, whose vignettes are read through "
        + "the store, not listed",
    ):
        _ = inventory.listing("typed")

    _ = path.write_text('[source.typed]\nkind = "spreadsheet"\n')
    with pytest.raises(ValueError, match="spreadsheet"):
        _ = Inventory.load(path)


def test_the_source_listed_is_the_one_named_or_the_only_one_that_lists(
    tmp_path: Path,
) -> None:
    typed = DatabaseSource(name="typed")
    files = DirectorySource(name="files", path=tmp_path)
    inventory = Inventory(sources={"typed": typed, "files": files})
    assert inventory.listing() == inventory.listing("files") == files
    with pytest.raises(LookupError, match="no source 'other' in the inventory"):
        _ = inventory.listing("other")

    more = DirectorySource(name="more", path=tmp_path)
    inventory = Inventory(sources={"typed": typed, "files": files, "more": more})
    assert inventory.listing("more") == more
    with pytest.raises(
        LookupError,
        match=r"2 sources list their vignettes \(files, more\), so one must be named",
    ):
        _ = inventory.listing()
    with pytest.raises(
        LookupError, match="no source in the inventory lists its vignettes"
    ):
        _ = Inventory(sources={"typed": typed}).listing()

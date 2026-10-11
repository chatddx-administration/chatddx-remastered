from pathlib import Path

import pytest

from chatddx.inventory import DatabaseSource, Inventory

pytestmark = pytest.mark.wip


def test_an_inventory_declares_a_database_source_by_its_kind(tmp_path: Path) -> None:
    path = tmp_path / "inventory.toml"
    _ = path.write_text('[source.typed]\nkind = "database"\nsensitive = true\n')
    inventory = Inventory.load(path)
    assert inventory.sources["typed"] == DatabaseSource(name="typed")
    with pytest.raises(LookupError, match="source 'typed' is read through the store"):
        _ = inventory.source("typed").ids()

    _ = path.write_text('[source.typed]\nkind = "spreadsheet"\n')
    with pytest.raises(ValueError, match="spreadsheet"):
        _ = Inventory.load(path)

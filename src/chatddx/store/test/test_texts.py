from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from psycopg import errors

from chatddx.factors.base import Fingerprint
from chatddx.factors.cases import Vignette
from chatddx.inventory import DatabaseSource, DirectorySource, Inventory
from chatddx.store import People, Texts, fetch_vignette
from chatddx.store.store import Connection


@pytest.mark.slow
def test_a_database_source_s_texts_are_kept_and_fetched_through_the_store(
    conn: Connection, tmp_path: Path
) -> None:
    alice = People(conn).add("alice", "Alice")
    texts = Texts(conn)
    id = texts.add("typed", "chest pain", alice.id)
    assert texts.get("typed", id) == b"chest pain"
    with pytest.raises(LookupError, match="no case 'nope' in source 'typed'"):
        _ = texts.get("typed", "nope")
    assert texts.typed_since(alice.id, datetime.now(UTC) - timedelta(days=1)) == 1
    assert texts.typed_since(alice.id, datetime.now(UTC) + timedelta(days=1)) == 0

    _ = (tmp_path / "c1.txt").write_bytes(b"cough")
    inventory = Inventory(
        sources={
            "typed": DatabaseSource(name="typed"),
            "files": DirectorySource(name="files", path=tmp_path),
        }
    )
    unknown = Fingerprint.of(b"")
    typed = Vignette(source="typed", id=id, fingerprint=unknown)
    filed = Vignette(source="files", id="c1", fingerprint=unknown)
    assert fetch_vignette(conn, inventory, typed) == b"chest pain"
    assert fetch_vignette(conn, inventory, filed) == b"cough"


@pytest.mark.parametrize("autocommit", [True])
@pytest.mark.slow
def test_a_text_is_never_changed_and_only_the_admin_deletes_one(
    conn: Connection, admin: Connection
) -> None:
    alice = People(conn).add("alice", "Alice")
    id = Texts(conn).add("typed", "chest pain", alice.id)
    for change in ("UPDATE source.text SET text = 'x'", "DELETE FROM source.text"):
        with pytest.raises(errors.InsufficientPrivilege):
            _ = conn.execute(change)
    with pytest.raises(errors.CheckViolation):
        _ = Texts(conn).add("typed", "", alice.id)
    with pytest.raises(errors.RaiseException, match="source.text is insert-only"):
        _ = admin.execute("UPDATE source.text SET text = 'x'")
    admin.rollback()

    _ = admin.execute("DELETE FROM source.text WHERE id = %s", (id,))
    admin.commit()
    with pytest.raises(LookupError):
        _ = Texts(conn).get("typed", id)

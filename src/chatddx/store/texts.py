from datetime import datetime
from uuid import uuid4

from chatddx.factors.cases import Vignette
from chatddx.inventory import DatabaseSource, Inventory

from .store import Connection


class Texts:
    def __init__(self, conn: Connection) -> None:
        self._conn: Connection = conn

    def add(self, source: str, text: str, by: int) -> str:
        id = uuid4().hex
        _ = self._conn.execute(
            "INSERT INTO source.text (source, id, text, by) VALUES (%s, %s, %s, %s)",
            (source, id, text, by),
        )
        return id

    def get(self, source: str, id: str) -> bytes:
        row = self._conn.execute(
            "SELECT text FROM source.text WHERE source = %s AND id = %s", (source, id)
        ).fetchone()
        if row is None:
            raise LookupError(f"no case {id!r} in source {source!r}")
        return str(row[0]).encode()

    def typed_since(self, by: int, since: datetime) -> int:
        row = self._conn.execute(
            "SELECT count(*) FROM source.text WHERE by = %s AND at >= %s", (by, since)
        ).fetchone()
        assert row is not None
        return int(row[0])


def fetch_vignette(conn: Connection, inventory: Inventory, vignette: Vignette) -> bytes:
    source = inventory.source(vignette.source)
    if isinstance(source, DatabaseSource):
        return Texts(conn).get(source.name, vignette.id)
    return source.fetch(vignette.id)

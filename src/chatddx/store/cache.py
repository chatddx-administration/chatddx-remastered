import threading
from collections import OrderedDict
from collections.abc import Hashable

import psycopg
from psycopg.pq import TransactionStatus
from psycopg.rows import TupleRow

type _Connection = psycopg.Connection[TupleRow]


# Policy: what is held is held per process and database, and only once read outside a
# transaction, so that what a transaction that rolls back wrote isn't held; the least
# recently used go past the size given.
class Cache[K: Hashable, V]:
    """What was read from the database, by key, for as long as the process lives: valid
    forever without a version, or while it stands with one, as `catalogued` reads it.
    Holds a lock only while it looks up or puts in; never queries."""

    def __init__(self, size: int) -> None:
        self._size: int = size
        self._held: OrderedDict[tuple[str, K], tuple[int | None, V]] = OrderedDict()
        self._guard: threading.Lock = threading.Lock()

    def get(self, conn: _Connection, key: K, version: int | None = None) -> V | None:
        with self._guard:
            found = self._held.get(at := (_database(conn), key))
            if found is None or found[0] != version:
                return None
            self._held.move_to_end(at)
            return found[1]

    def put(
        self, conn: _Connection, key: K, value: V, version: int | None = None
    ) -> None:
        if conn.info.transaction_status != TransactionStatus.IDLE:
            return
        with self._guard:
            self._held[_database(conn), key] = (version, value)
            self._held.move_to_end((_database(conn), key))
            while len(self._held) > self._size:
                _ = self._held.popitem(last=False)


def catalogued(conn: _Connection) -> int:
    """The catalog's version, which each transaction that writes to it bumps as it
    commits: one query."""
    row = conn.execute("SELECT version FROM catalog.version").fetchone()
    assert row is not None
    return int(row[0])


def _database(conn: _Connection) -> str:
    info = conn.info
    return f"{info.host}:{info.port}/{info.dbname}"

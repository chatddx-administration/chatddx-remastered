import psycopg
import pytest
from psycopg import errors

from chatddx import settings
from chatddx.catalog import MovedOn, threads
from chatddx.factors.bundle import Registry
from chatddx.factors.request import Sampling
from chatddx.store import Catalog, People, Rows, Store
from chatddx.store.store import Connection


def _stored(conn: Connection, *temperatures: float) -> list[str]:
    reg = Registry()
    digests = [reg.add(Sampling(temperature=t)) for t in temperatures]
    _ = Store(conn).add(reg, digests)
    return digests


def test_an_edit_or_a_keep_naming_an_old_head_is_refused(conn: Connection) -> None:
    catalog = Catalog(conn)
    rows = Rows(conn)
    alice = People(conn).add("alice", "Alice")
    cool, warm, hot = _stored(conn, 0.6, 0.7, 0.8)
    first = catalog.create(cool, alice.id)
    second = catalog.edit(first.thread, warm, alice.id, head=first.id)

    with pytest.raises(MovedOn, match=f"its head is edit {second.id}"):
        _ = catalog.edit(first.thread, hot, alice.id, head=first.id)
    with pytest.raises(MovedOn, match=f"since edit {first.id}"):
        _ = catalog.keep(warm, alice.id, first.thread, head=first.id)
    assert catalog.keep(warm, alice.id, first.thread, head=second.id) == (
        second,
        "unchanged",
    )
    third, kept = catalog.keep(hot, alice.id, first.thread, head=second.id)
    assert kept == "edited" and threads.head(rows, first.thread) == third


def test_edits_of_one_thread_land_one_at_a_time(conn: Connection) -> None:
    catalog = Catalog(conn)
    alice = People(conn).add("alice", "Alice")
    cool, warm, hot = _stored(conn, 0.6, 0.7, 0.8)
    first = catalog.create(cool, alice.id)
    conn.commit()

    dbname = conn.info.dbname
    with psycopg.connect(settings.database(), dbname=dbname, autocommit=True) as rival:
        _ = rival.execute("SET lock_timeout = '50ms'")
        with conn.transaction():
            second = catalog.edit(first.thread, warm, alice.id, head=first.id)
            with pytest.raises(errors.LockNotAvailable):
                _ = Catalog(rival).edit(first.thread, hot, alice.id, head=first.id)
        with pytest.raises(MovedOn, match=f"its head is edit {second.id}"):
            _ = Catalog(rival).edit(first.thread, hot, alice.id, head=first.id)

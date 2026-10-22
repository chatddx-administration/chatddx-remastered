from chatddx.factors.bundle import Registry
from chatddx.factors.test.sample import NOW, fp, world
from chatddx.identity import Person
from chatddx.ledger import Call
from chatddx.store import Catalog, People, Store
from chatddx.store.store import Connection
from chatddx.test.helpers import one_attempt


def stored_world(
    conn: Connection,
) -> tuple[Catalog, Store, Registry, dict[str, str], Person]:
    reg = Registry()
    ids = world(reg)
    store = Store(conn)
    _ = store.add(reg, [ids["trial"], ids["scoring"], ids["canaries"]])
    return Catalog(conn), store, reg, ids, People(conn).add("alice", "Alice")


def call(model: str) -> Call:
    return Call(
        request=fp("body"),
        started_at=NOW,
        finished_at=NOW,
        attempts=one_attempt(NOW),
        status=200,
        response={"model": model},
        prompt_tokens=fp("tokens"),
    )

from collections.abc import Iterator
from datetime import UTC, datetime
from uuid import uuid4

import psycopg
import pytest
from psycopg.conninfo import make_conninfo

from chatddx import settings
from chatddx.api import schemas
from chatddx.factors.test.sample import fp
from chatddx.ledger import Call, ItemKey, RunItem
from chatddx.runner.run import ItemEnded
from chatddx.store.notify import Assembler, Events, channel, listen
from chatddx.store.store import Connection
from chatddx.worker import publish
from chatddx.worker.publish import Publisher

NOW = datetime(2026, 1, 1, tzinfo=UTC)
A, B = (f"sha256:{c * 64}" for c in "ab")


@pytest.fixture
def connected(db: str) -> Iterator[tuple[Connection, Connection]]:
    conninfo = make_conninfo(settings.database(), dbname=db)
    with (
        psycopg.connect(conninfo, autocommit=True) as listener,
        psycopg.connect(conninfo, autocommit=True) as told,
    ):
        yield listener, told


def delta(case: str, kind: str, text: str, tokens: int) -> schemas.ItemDeltaData:
    return schemas.ItemDeltaData.model_validate(
        {"case": case, "replicate": 0, "kind": kind, "text": text, "tokens": tokens}
    )


@pytest.mark.slow
def test_deltas_go_out_together_by_item_and_kind_and_an_ended_item_s_go_unsaid(
    connected: tuple[Connection, Connection], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(publish, "EVERY", 60.0)
    listener, told = connected
    run = uuid4()
    listen(listener, channel(run))
    publisher = Publisher(told, run)
    begun = schemas.ItemStartedData(case=A, replicate=0, seed=7)
    publisher.put(("item.started", begun))
    for said in (
        delta(A, "reasoning", "Hm", 1),
        delta(B, "content", "No", 1),
        delta(A, "reasoning", "m.", 2),
        delta(A, "content", "Co", 3),
        delta(A, "content", "lic", 4),
    ):
        publisher.put(("item.delta", said))
    call = Call(request=fp("body"), started_at=NOW, finished_at=NOW)
    key = ItemKey(case=B, replicate=0)
    publisher.run_event(
        ItemEnded(RunItem(run=run, key=key, vignette=fp("v"), call=call))
    )
    publisher.close()

    assembler = Assembler()
    heard = [
        assembler.message(n.channel, n.pid, n.payload)
        for n in listener.notifies(timeout=0.5)
    ]
    assert heard == [
        Events([("item.started", begun.model_dump(mode="json"))]),
        Events(
            [
                ("item.delta", delta(A, "reasoning", "Hmm.", 2).model_dump()),
                ("item.delta", delta(A, "content", "Colic", 4).model_dump()),
            ]
        ),
    ]

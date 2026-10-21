import asyncio
from uuid import uuid4

import psycopg
from psycopg.conninfo import make_conninfo
from pydantic import JsonValue

from chatddx import settings
from chatddx.api.listening import BEHIND, Heard, Lagged, Listener
from chatddx.api.telling import Telling
from chatddx.api.test.helpers import told
from chatddx.bench import Bench
from chatddx.bench.test.helpers import ran, trial
from chatddx.curation import Plan
from chatddx.factors.base import resolve
from chatddx.factors.cases import Case
from chatddx.factors.test.sample import fp
from chatddx.identity import Person
from chatddx.ledger import Call, ItemKey, RunItem, ToolRun, Turn
from chatddx.store import Store
from chatddx.store.notify import Events, JobChanged, Rows, channel, tell
from chatddx.store.store import Connection
from chatddx.test.helpers import NOW
from chatddx.test.world import LINES


def tool(id: str) -> ToolRun:
    return ToolRun(id=id, name="lookup", started_at=NOW, finished_at=NOW, result="r")


def test_a_stream_joined_mid_item_is_told_it_began_and_each_tool_once(
    bench: Bench, conn: Connection, alice: Person, plan: Plan
) -> None:
    made = trial(conn, plan, LINES, "crlf")
    run = ran(conn, alice, made, finished=False)
    [case] = made.cases
    [(started, _)] = Store(conn).rows_of(run)
    telling = Telling(bench, run, started)
    assert telling.rows() == []

    delta: JsonValue = {
        "case": case,
        "replicate": 0,
        "kind": "content",
        "text": "Col",
        "tokens": 1,
    }
    ran_tool: JsonValue = {"case": case, "replicate": 0, "tool": {"id": "first"}}
    said = told("".join(telling.said([("item.delta", delta), ("item.tool", ran_tool)])))
    assert [(i, n) for i, n, _ in said] == [
        (None, "item.started"),
        (None, "item.delta"),
        (None, "item.tool"),
    ]
    assert said[0][2] == {"case": case, "replicate": 0, "seed": 7}
    assert told("".join(telling.said([("item.delta", delta)])))[0][1] == "item.delta"

    call = Call(request=fp("body"), started_at=NOW, finished_at=NOW)
    vignette = resolve(plan.registry.get, case, Case).vignette.fingerprint
    turn = Turn(tools=(tool("first"), tool("second")), call=call)
    item = RunItem(
        run=run,
        key=ItemKey(case=case, replicate=0),
        vignette=vignette,
        call=call,
        turns=(turn,),
    )
    Store(conn).append(item)
    said = told("".join(telling.rows()))
    assert [n for _, n, _ in said] == ["item.tool", "item.ended"]
    assert said[0][2]["tool"]["id"] == "second"
    assert said[1][0] == telling.last > started
    assert telling.said([("item.delta", delta)]) == []


def test_a_listener_fans_a_run_s_messages_out_to_the_streams_following_it(
    db: str,
) -> None:
    conninfo = make_conninfo(settings.database(), dbname=db)
    listener, run = Listener(conninfo), uuid4()
    said: list[tuple[str, JsonValue]] = [("item.delta", {"text": "x" * 9000})]

    async def follow() -> None:
        async with listener.heard(run) as one, listener.heard(run) as two:
            with psycopg.connect(conninfo, autocommit=True) as conn:
                for payload in ["rows", "job finished"]:
                    _ = conn.execute(
                        "SELECT pg_notify(%s, %s)", (channel(run), payload)
                    )
                tell(conn, run, said)
            expected = [Rows(), JobChanged("finished"), Events(said)]
            for hearing in (one, two):
                heard: list[Heard] = []
                while len(heard) < len(expected):
                    heard.extend(await hearing.next(5))
                assert heard == expected
            for _ in range(BEHIND + 1):
                one.put(Rows())
            assert await one.next(1) == [Lagged()]

    try:
        asyncio.run(follow())
        asyncio.run(follow())
    finally:
        listener.stop()

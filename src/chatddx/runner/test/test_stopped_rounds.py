import pytest

from chatddx.curation import Plan
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.runner.run import Event, Runner, ToolRan
from chatddx.runner.send import STOPPED
from chatddx.runner.test.test_run import Heard, elsewhere, insensitive, tooled
from chatddx.runner.test.tools import component
from chatddx.store import Store
from chatddx.store.store import Connection
from chatddx.test.world import LINES, QWEN
from chatddx.tools.shipped import TOOLS, ShippedTool

pytestmark = pytest.mark.wip


def stopped(message: str) -> tuple[str, str]:
    return ("tools.stopped", message)


@pytest.mark.usefixtures("fake")
def test_an_interrupt_after_a_tool_ran_keeps_its_round_without_a_call(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    made = tooled(plan, LINES, component("lookup"), component("broken"))
    running = Runner(conn, insensitive(inventory), alice).start(
        made, plan.registry, QWEN
    )
    ran: list[ToolRan] = []

    def interrupt(event: Event) -> None:
        if isinstance(event, ToolRan):
            ran.append(event)
            if len(ran) == 2:
                raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        running.send(Heard(then=interrupt))
    findings = running.finish()
    [item] = Store(conn).run(running.run).items
    assert [[r.name for r in t.tools] for t in item.turns] == [["lookup"], ["broken"]]
    assert item.turns[-1].call is None
    assert len(item.calls) == 2
    assert stopped("round 2 stopped after 1 of 1 tool calls, before its call") in [
        (f.code, f.message) for f in findings
    ]


@pytest.mark.usefixtures("fake")
def test_an_interrupt_inside_a_tool_records_it_as_stopped(
    conn: Connection,
    inventory: Inventory,
    alice: Person,
    plan: Plan,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def interrupted(**_: object) -> str:
        raise KeyboardInterrupt

    monkeypatch.setitem(
        TOOLS, "chatddx.runner.test.tools:lookup", ShippedTool(1, interrupted)
    )
    made = tooled(plan, LINES, component("lookup"), component("broken"))
    running = Runner(conn, insensitive(inventory), alice).start(
        made, plan.registry, QWEN
    )
    with pytest.raises(KeyboardInterrupt):
        running.send()
    findings = running.finish()
    [item] = Store(conn).run(running.run).items
    [turn] = item.turns
    assert [(r.name, r.result, r.error) for r in turn.tools] == [
        ("lookup", f"error: {STOPPED}", STOPPED)
    ]
    assert turn.call is None
    assert stopped("round 1 stopped after 1 of 1 tool calls, before its call") in [
        (f.code, f.message) for f in findings
    ]


@pytest.mark.usefixtures("fake")
def test_a_halt_while_tools_run_keeps_the_round_and_sends_no_call(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    made = tooled(plan, LINES, component("lookup"), component("broken"))
    running = Runner(conn, insensitive(inventory), alice).start(
        made, plan.registry, QWEN
    )

    def halt(event: Event) -> None:
        if isinstance(event, ToolRan):
            elsewhere(running.halt)

    running.send(Heard(then=halt))
    findings = running.finish()
    [item] = Store(conn).run(running.run).items
    assert [[r.name for r in t.tools] for t in item.turns] == [["lookup"]]
    assert item.calls == (item.call,)
    assert stopped("round 1 stopped after 1 of 1 tool calls, before its call") in [
        (f.code, f.message) for f in findings
    ]

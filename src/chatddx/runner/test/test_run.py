import socket
from collections.abc import Callable, Generator, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import psycopg
import pytest
from psycopg import sql
from pydantic import ValidationError

from chatddx.catalog import Subject
from chatddx.conftest import WORLDS, connect, sample_plan
from chatddx.core import settings
from chatddx.core.rig import rig
from chatddx.curation import Plan
from chatddx.factors.base import Code, Fingerprint, resolve
from chatddx.factors.cases import Case, Vignette, prepare_case
from chatddx.factors.engine import LocalEngine
from chatddx.factors.request import (
    Compilation,
    Skeleton,
    Tool,
    Toolset,
    compile_request,
    next_request,
    render,
    tool_calls,
)
from chatddx.factors.trial import Canary, CanarySet, Execution, Trial
from chatddx.fake_vllm.served import Served
from chatddx.fake_vllm.server import serving
from chatddx.identity import Person
from chatddx.inventory import DirectorySource, Inventory, start_up
from chatddx.ledger import (
    Endpoint,
    ItemKey,
    RunFinished,
    ToolCode,
    check_run,
    fingerprint_request,
)
from chatddx.ledger.call import check_execution
from chatddx.runner import send as sending
from chatddx.runner.gate import Refused
from chatddx.runner.run import (
    CanaryEnded,
    Event,
    ItemEnded,
    ItemStarted,
    Noted,
    Runner,
    Streamed,
    ToolRan,
)
from chatddx.runner.send import STOPPED
from chatddx.runner.test.tools import component
from chatddx.store import Catalog, People, Store
from chatddx.store.store import Connection

WORLD = WORLDS / "sample"
QWEN = "qwen3-8b-awq@fake"
GPT_OSS = "gpt-oss-20b@fake"
CASES = ("DutchFall10w", "casesfromedn1")
# Slow enough that calls sent together overlap: a fake answer is some 40 tokens.
DELAY = 0.005


@pytest.fixture(scope="module")
def plan() -> Plan:
    return sample_plan()


@pytest.fixture
def conn(db: str) -> Iterator[Connection]:
    with psycopg.connect(settings.database(), dbname=db, autocommit=True) as c:
        yield c


@pytest.fixture
def alice(conn: Connection) -> Person:
    return People(conn).add("alice", "Alice")


def world(tmp_path: Path, port: int) -> Inventory:
    text = (WORLD / "inventory.toml").read_text()
    text = text.replace('path = "vignettes"', f'path = "{WORLD / "vignettes"}"')
    path = tmp_path / "inventory.toml"
    _ = path.write_text(
        text.replace("12099", str(port)).replace("12100", str(port + 1))
    )
    return Inventory.load(path)


@pytest.fixture
def inventory(tmp_path: Path) -> Inventory:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = int(s.getsockname()[1])
    return world(tmp_path, port)


@contextmanager
def faked(inventory: Inventory, plan: Plan, delay: float = 0.0) -> Generator[None]:
    startup = start_up(inventory, plan.registry.get, QWEN)
    with serving([Served.of(startup.argv[0], startup.argv[1:])], delay=delay):
        yield


@pytest.fixture
def fake(inventory: Inventory, plan: Plan) -> Iterator[None]:
    with faked(inventory, plan):
        yield


@pytest.fixture
def slow(inventory: Inventory, plan: Plan) -> Iterator[None]:
    with faked(inventory, plan, DELAY):
        yield


def trial(
    plan: Plan,
    skeleton: str = "free-text (Qwen/Qwen3-8B-AWQ)",
    cases: tuple[str, ...] = CASES,
    seeds: tuple[int, ...] = (7, 8),
    engine: str = QWEN,
) -> Trial:
    source = DirectorySource(name="sample", path=WORLD / "vignettes")
    refs = [plan.registry.add(c) for c in source.cases() if c.vignette.id in cases]
    made = Trial(
        skeleton=plan.named("recipe", skeleton).digest,
        engine=plan.named("local_engine", engine).digest,
        cases=tuple(refs),
        seeds=seeds,
    )
    _ = plan.registry.add(made)
    return made


@dataclass
class Heard:
    events: list[Event] = field(default_factory=list[Event])
    then: Callable[[Event], None] | None = None

    def __call__(self, event: Event) -> None:
        self.events.append(event)
        if self.then is not None:
            self.then(event)

    def of[E](self, kind: type[E]) -> list[E]:
        return [e for e in self.events if isinstance(e, kind)]


def reasoning(ended: ItemEnded) -> str:
    response = cast(Any, ended.item.call.response)
    return response["choices"][0]["message"]["reasoning"]


def rows(db: str, table: str) -> int:
    query = sql.SQL("SELECT count(*) FROM ledger.{}").format(sql.Identifier(table))
    with connect(db) as c:
        row = c.execute(query).fetchone()
    assert row is not None
    return int(row[0])


@pytest.mark.usefixtures("fake")
def test_a_run_sends_each_item_and_writes_its_log(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    made = trial(plan)
    running = Runner(conn, inventory, alice).start(made, plan.registry, QWEN)
    heard = Heard()
    running.send(heard)
    assert running.finish() == []

    stored = Store(conn).run(running.run)
    started = stored.started
    assert (started.trial, started.rig, started.execution) == (
        made.digest,
        rig(),
        Execution(),
    )
    assert started.endpoint == Endpoint(
        name=QWEN, url=str(inventory.endpoint(QWEN).url)
    )
    assert isinstance(stored.finished, RunFinished) and stored.finished.findings == ()
    assert [i.key for i in heard.of(ItemStarted)] == [
        ItemKey(case=c, replicate=r) for c in made.cases for r in (0, 1)
    ]
    assert {i.key for i in stored.items} == {e.key for e in heard.of(ItemStarted)}
    assert all(i.call.error is None and i.call.status == 200 for i in stored.items)
    assert [
        f"seed={e.seed} " in reasoning(d)
        for e, d in zip(heard.of(ItemStarted), heard.of(ItemEnded), strict=True)
    ] == [True] * 4
    started = [e.key for e in heard.of(ItemStarted)]
    streamed = [s.key for s in heard.of(Streamed)]
    assert streamed == sorted(streamed, key=started.index)
    assert set(streamed) == set(started) and not heard.of(Noted)
    about = Catalog(conn).about(Subject(run=running.run))
    assert about.owner == alice.id


@pytest.mark.usefixtures("fake")
def test_a_greedy_skeleton_is_sent_without_its_seed(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    named = plan.named("recipe", "free-text (Qwen/Qwen3-8B-AWQ)")
    assert named.compilation is not None
    compiled = resolve(plan.registry.get, named.compilation, Compilation)
    greedy = compiled.recipe.model_copy(
        update={"sampling": plan.named("sampling", "greedy").digest}
    )
    skeleton = compile_request(greedy, plan.registry.get)
    assert skeleton.greedy
    made = trial(plan, cases=CASES[:1], seeds=(7,)).model_copy(
        update={"skeleton": plan.registry.add(skeleton)}
    )
    _ = plan.registry.add(made)
    running = Runner(conn, inventory, alice).start(made, plan.registry, QWEN)
    heard = Heard()
    running.send(heard)
    _ = running.finish()
    [ended] = heard.of(ItemEnded)
    assert "seed=" not in reasoning(ended) and "temperature=0" in reasoning(ended)


@pytest.mark.usefixtures("fake")
def test_each_row_lands_as_it_is_written(
    conn: Connection, db: str, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    running = Runner(conn, inventory, alice).start(trial(plan), plan.registry, QWEN)
    assert rows(db, "run_stage") == 1
    landed: list[int] = []
    running.send(
        Heard(
            then=lambda e: (
                landed.append(rows(db, "run_item"))
                if isinstance(e, ItemEnded)
                else None
            )
        )
    )
    assert landed == [1, 2, 3, 4]
    _ = running.finish()
    assert rows(db, "run_stage") == 2


def test_the_runner_wants_rows_committed_as_they_are_written(
    db: str, inventory: Inventory, alice: Person
) -> None:
    with connect(db) as c, pytest.raises(ValueError, match="autocommit"):
        _ = Runner(c, inventory, alice)


@pytest.mark.usefixtures("fake")
def test_a_case_that_can_t_be_read_or_has_changed_is_noted(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    sample = trial(plan, cases=CASES[:1], seeds=(7,))
    real = resolve(plan.registry.get, sample.cases[0], Case)
    missing = Case(
        vignette=Vignette(
            source="sample", id="nowhere", fingerprint=real.vignette.fingerprint
        )
    )
    changed = Case(
        vignette=real.vignette.model_copy(
            update={"fingerprint": Fingerprint.of(b"before")}
        )
    )
    made = sample.model_copy(
        update={"cases": tuple(plan.registry.add(c) for c in (real, missing, changed))}
    )
    _ = plan.registry.add(made)
    running = Runner(conn, inventory, alice).start(made, plan.registry, QWEN)
    heard = Heard()
    running.send(heard)
    findings = running.finish()
    noted = sorted(n.finding.code for n in heard.of(Noted))
    assert noted == ["case.drift", "case.unreadable"]
    stored = Store(conn).run(running.run)
    assert stored.finished is not None
    assert sorted(f.code for f in stored.finished.findings) == noted
    assert len(stored.items) == 2
    codes = [f.code for f in findings]
    assert "run.incomplete" in codes and "case.drift" in codes


@pytest.mark.usefixtures("fake")
def test_stopping_ends_the_run_after_the_item_under_way(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    running = Runner(conn, inventory, alice).start(trial(plan), plan.registry, QWEN)

    def stop(event: Event) -> None:
        if isinstance(event, Streamed):
            running.stop()

    running.send(Heard(then=stop))
    findings = running.finish()
    assert len(Store(conn).run(running.run).items) == 1
    assert ("run.incomplete", "3 items missing") in [
        (f.code, f.message) for f in findings
    ]


@pytest.mark.usefixtures("fake")
def test_an_interrupt_mid_call_records_the_call_as_stopped(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    running = Runner(conn, inventory, alice).start(trial(plan), plan.registry, QWEN)
    deltas: list[Streamed] = []

    def interrupt(event: Event) -> None:
        if isinstance(event, Streamed):
            deltas.append(event)
            if len(deltas) == 2:
                raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        running.send(Heard(then=interrupt))
    running.send()
    _ = running.finish()
    [item] = Store(conn).run(running.run).items
    assert item.call.error == STOPPED and item.call.prompt_tokens is not None


def test_nothing_is_sent_or_written_where_the_gate_refuses(
    conn: Connection,
    db: str,
    inventory: Inventory,
    alice: Person,
    plan: Plan,
) -> None:
    def refused(made: Trial, endpoint: str, at: Inventory = inventory) -> str:
        with pytest.raises(Refused) as caught:
            _ = Runner(conn, at, alice).start(made, plan.registry, endpoint)
        return str(caught.value)

    uncleared = inventory.model_copy(update={"cleared": {}})
    assert "isn't cleared for source sample, which is sensitive" in refused(
        trial(plan), QWEN, uncleared
    )
    assert "serves engine" in refused(trial(plan), GPT_OSS)
    assert f"endpoint {GPT_OSS!r} can't be confirmed" in refused(
        trial(plan, "free-text (openai/gpt-oss-20b)", engine=GPT_OSS), GPT_OSS
    )
    assert "tools can't be cleared yet" in refused(
        trial(plan, "plan-web (Qwen/Qwen3-8B-AWQ)"), QWEN
    )
    assert rows(db, "run_stage") == 0


@pytest.mark.usefixtures("fake")
def test_a_secret_is_sent_and_never_written(
    conn: Connection,
    db: str,
    inventory: Inventory,
    alice: Person,
    plan: Plan,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    keyed = inventory.model_copy(
        update={
            "endpoints": inventory.endpoints
            | {
                QWEN: inventory.endpoint(QWEN).model_copy(
                    update={"credential": "FAKE_KEY"}
                )
            }
        }
    )
    monkeypatch.delenv("FAKE_KEY", raising=False)
    with pytest.raises(Refused, match=r"needs the secret in \$FAKE_KEY"):
        _ = Runner(conn, keyed, alice).start(trial(plan), plan.registry, QWEN)
    monkeypatch.setenv("FAKE_KEY", "s3cret-value")
    running = Runner(conn, keyed, alice).start(trial(plan), plan.registry, QWEN)
    running.send()
    _ = running.finish()
    with connect(db) as c:
        stored = c.execute(
            "SELECT payload FROM ledger.run_stage UNION ALL SELECT payload FROM ledger.run_item"
        ).fetchall()
    assert stored and not any("s3cret" in str(p) for (p,) in stored)


@pytest.mark.usefixtures("fake")
def test_a_run_is_finished_once_and_sends_nothing_after(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    running = Runner(conn, inventory, alice).start(trial(plan), plan.registry, QWEN)
    _ = running.finish()
    heard = Heard()
    running.send(heard)
    assert heard.events == []
    with pytest.raises(ValueError, match="is finished"):
        _ = running.finish()


ORDERS = [
    Execution(),
    Execution(order="replicate_major@1"),
    Execution(order="shuffled@1", shuffle_seed=3),
]


@pytest.mark.usefixtures("fake")
@pytest.mark.parametrize("concurrency", [1, 3])
@pytest.mark.parametrize("order", ORDERS, ids=lambda e: e.order)
def test_items_are_sent_in_the_execution_s_order(
    conn: Connection,
    inventory: Inventory,
    alice: Person,
    plan: Plan,
    order: Execution,
    concurrency: int,
) -> None:
    made = trial(plan)
    schedules = {tuple(e.schedule(made.cases, 2)) for e in ORDERS}
    assert len(schedules) == len(ORDERS)
    execution = order.model_copy(update={"concurrency": concurrency})
    running = Runner(conn, inventory, alice).start(made, plan.registry, QWEN, execution)
    heard = Heard()
    running.send(heard)
    assert running.finish() == []
    assert [e.key for e in heard.of(ItemStarted)] == [
        ItemKey(case=c, replicate=r) for c, r in execution.schedule(made.cases, 2)
    ]
    assert Store(conn).run(running.run).started.execution == execution


@pytest.mark.usefixtures("slow")
def test_calls_are_in_flight_together_up_to_the_execution_s_concurrency(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    made = trial(plan)
    running = Runner(conn, inventory, alice).start(
        made, plan.registry, QWEN, Execution(concurrency=2)
    )
    heard = Heard()
    running.send(heard)
    assert running.finish() == []
    items = Store(conn).run(running.run).items
    assert all(i.call.error is None and i.call.status == 200 for i in items)
    calls = [i.call for i in items]
    sent = {i.key: i.call.started_at for i in items}
    assert [
        (f.code, f.message) for f in check_execution(Execution(), made, calls, sent)
    ] == [("execution.concurrency", "2 calls were in flight at once, declared 1")]
    assert {e.item.key for e in heard.of(ItemEnded)} == {
        s.key for s in heard.of(Streamed)
    }


@pytest.mark.usefixtures("fake")
def test_a_concurrency_above_the_endpoint_s_max_jobs_is_refused(
    conn: Connection, db: str, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    assert inventory.endpoint(QWEN).max_jobs == 4
    with pytest.raises(
        ValueError, match="takes 4 requests at once, the execution sends 5"
    ):
        _ = Runner(conn, inventory, alice).start(
            trial(plan), plan.registry, QWEN, Execution(concurrency=5)
        )
    assert rows(db, "run_stage") == 0


@pytest.mark.usefixtures("slow")
def test_stopping_a_concurrent_run_ends_it_after_the_calls_in_flight(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    running = Runner(conn, inventory, alice).start(
        trial(plan), plan.registry, QWEN, Execution(concurrency=2)
    )

    def stop(event: Event) -> None:
        if isinstance(event, Streamed):
            running.stop()

    running.send(Heard(then=stop))
    findings = running.finish()
    items = Store(conn).run(running.run).items
    assert [i.call.error for i in items] == [None, None]
    assert ("run.incomplete", "2 items missing") in [
        (f.code, f.message) for f in findings
    ]


@pytest.mark.usefixtures("slow")
def test_an_interrupt_hangs_up_every_call_in_flight_and_records_them_as_stopped(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    running = Runner(conn, inventory, alice).start(
        trial(plan), plan.registry, QWEN, Execution(concurrency=2)
    )
    deltas: list[Streamed] = []

    def interrupt(event: Event) -> None:
        if isinstance(event, Streamed):
            deltas.append(event)
            if len(deltas) == 2:
                raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        running.send(Heard(then=interrupt))
    running.send()
    _ = running.finish()
    items = Store(conn).run(running.run).items
    assert [i.call.error for i in items] == [STOPPED, STOPPED]
    assert all(i.call.prompt_tokens is not None for i in items)


@pytest.mark.usefixtures("slow")
def test_another_interrupt_while_calls_hang_up_leaves_them_out(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    running = Runner(conn, inventory, alice).start(
        trial(plan), plan.registry, QWEN, Execution(concurrency=2)
    )

    def interrupt(event: Event) -> None:
        if isinstance(event, Streamed | ItemEnded):
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        running.send(Heard(then=interrupt))
    _ = running.finish()
    [item] = Store(conn).run(running.run).items
    assert item.call.error == STOPPED


@pytest.mark.usefixtures("fake")
def test_a_call_that_fails_on_its_thread_fails_the_send(
    conn: Connection,
    inventory: Inventory,
    alice: Person,
    plan: Plan,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def broken(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("broken")

    monkeypatch.setattr(sending, "send", broken)
    running = Runner(conn, inventory, alice).start(
        trial(plan), plan.registry, QWEN, Execution(concurrency=2)
    )
    with pytest.raises(RuntimeError, match="broken"):
        running.send()
    _ = running.finish()
    assert Store(conn).run(running.run).items == ()


# The sample's source declared not sensitive, so the gate lets tools see its cases.
def insensitive(inventory: Inventory) -> Inventory:
    sample = inventory.sources["sample"].model_copy(update={"sensitive": False})
    return inventory.model_copy(update={"sources": {"sample": sample}})


def tooled(
    plan: Plan,
    recipe: str,
    *tools: Tool,
    max_rounds: int = 5,
    cases: tuple[str, ...] = CASES[:1],
    seeds: tuple[int, ...] = (7,),
) -> Trial:
    named = plan.named("recipe", recipe)
    assert named.compilation is not None
    compiled = resolve(plan.registry.get, named.compilation, Compilation).recipe
    toolset = Toolset(
        tools=tuple(plan.registry.add(t) for t in tools), max_rounds=max_rounds
    )
    skeleton = compile_request(
        compiled.model_copy(update={"toolset": plan.registry.add(toolset)}),
        plan.registry.get,
    )
    made = trial(plan, cases=cases, seeds=seeds).model_copy(
        update={"skeleton": plan.registry.add(skeleton)}
    )
    _ = plan.registry.add(made)
    return made


FREE_TEXT = "free-text (Qwen/Qwen3-8B-AWQ)"
ASKED = "'fake query'"


@pytest.mark.usefixtures("fake")
def test_a_round_runs_the_tools_a_response_calls_and_sends_back_their_results(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    open_world = insensitive(inventory)
    made = tooled(plan, FREE_TEXT, component("lookup"), component("broken"))
    running = Runner(conn, open_world, alice).start(made, plan.registry, QWEN)
    heard = Heard()
    running.send(heard)
    assert running.finish() == []

    stored = Store(conn).run(running.run)
    skeleton = resolve(plan.registry.get, made.skeleton, Skeleton)
    assert stored.started.tool_code == tuple(
        ToolCode(tool=t, code=rig()) for t in sorted(skeleton.tools)
    )
    [item] = stored.items
    assert [[(r.name, r.result, r.error) for r in t.tools] for t in item.turns] == [
        [("lookup", f"1 results for {ASKED}", None)],
        [
            (
                "broken",
                f"error: OSError: no answer for {ASKED}",
                f"OSError: no answer for {ASKED}",
            )
        ],
    ]
    last = item.turns[-1].call
    assert last.response is not None and tool_calls(last.response) == ()
    assert all(c.status == 200 and c.prompt_tokens is not None for c in item.calls)
    assert [(e.key, e.run.name) for e in heard.of(ToolRan)] == [
        (item.key, "lookup"),
        (item.key, "broken"),
    ]

    case = resolve(plan.registry.get, made.cases[0], Case)
    raw = open_world.source("sample").fetch(case.vignette.id)
    fills = prepare_case(
        case, raw, plan.registry.get, skeleton.appendix_layout, made.cleanup
    ).fills
    engine = resolve(plan.registry.get, made.engine, LocalEngine)
    body = render(skeleton, model=engine.served_model_name, seed=7, fills=fills)
    assert item.call.request == fingerprint_request(body)
    assert item.call.response is not None
    results = {r.id: r.result for r in item.turns[0].tools}
    second = next_request(body, item.call.response, results)
    assert item.turns[0].call.request == fingerprint_request(second)


@pytest.mark.usefixtures("fake")
def test_calling_the_answer_tool_ends_the_item(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    made = tooled(plan, "diagnoses-tool (Qwen/Qwen3-8B-AWQ)", component("lookup"))
    running = Runner(conn, insensitive(inventory), alice).start(
        made, plan.registry, QWEN
    )
    running.send()
    assert running.finish() == []
    [item] = Store(conn).run(running.run).items
    assert [[r.name for r in t.tools] for t in item.turns] == [["lookup"]]
    last = item.turns[-1].call.response
    assert last is not None and [c.name for c in tool_calls(last)] == ["final_result"]


@pytest.mark.usefixtures("fake")
def test_rounds_end_after_max_rounds_and_the_calls_left_are_noted(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    made = tooled(
        plan, FREE_TEXT, component("lookup"), component("broken"), max_rounds=1
    )
    running = Runner(conn, insensitive(inventory), alice).start(
        made, plan.registry, QWEN
    )
    running.send()
    assert [(f.code, f.message) for f in running.finish()] == [
        (
            "tools.unanswered",
            "the last response still calls broken after 1 of 1 rounds",
        )
    ]
    [item] = Store(conn).run(running.run).items
    assert len(item.turns) == 1


@pytest.mark.usefixtures("fake")
def test_a_tool_that_doesn_t_run_the_running_code_is_refused(
    conn: Connection, db: str, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    other = Code(distribution="chatddx", version="0.0.0")
    made = tooled(plan, FREE_TEXT, component("lookup", other))
    with pytest.raises(LookupError, match="pins chatddx 0.0.0"):
        _ = Runner(conn, insensitive(inventory), alice).start(made, plan.registry, QWEN)
    assert rows(db, "run_stage") == 0


@pytest.mark.usefixtures("fake")
def test_an_interrupt_while_tools_run_keeps_the_rounds_that_have_a_call(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    made = tooled(plan, FREE_TEXT, component("lookup"), component("broken"))
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
    assert [[r.name for r in t.tools] for t in item.turns] == [["lookup"]]
    assert (
        "tools.unanswered",
        "the last response still calls broken after 1 of 5 rounds",
    ) in [(f.code, f.message) for f in findings]


@pytest.mark.usefixtures("fake")
def test_rounds_run_on_the_workers_above_concurrency_1(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    made = tooled(
        plan,
        FREE_TEXT,
        component("lookup"),
        component("broken"),
        cases=CASES,
        seeds=(7, 8),
    )
    running = Runner(conn, insensitive(inventory), alice).start(
        made, plan.registry, QWEN, Execution(concurrency=2)
    )
    heard = Heard()
    running.send(heard)
    assert running.finish() == []
    items = Store(conn).run(running.run).items
    assert [len(i.turns) for i in items] == [2, 2, 2, 2]
    assert sorted(str(e.key) for e in heard.of(ToolRan)) == sorted(
        str(i.key) for i in items for _ in range(2)
    )


CANARIES = CanarySet(
    canaries=(
        Canary(
            messages=({"role": "user", "content": "Name three causes of chest pain."},),
            body={"temperature": 0},
        ),
        Canary(messages=({"role": "user", "content": "What is 2+2?"},), seed=7),
    )
)


@pytest.mark.usefixtures("fake")
@pytest.mark.parametrize("concurrency", [1, 2])
def test_canaries_bracket_the_items_and_are_stored_with_the_run(
    conn: Connection,
    inventory: Inventory,
    alice: Person,
    plan: Plan,
    concurrency: int,
) -> None:
    made = trial(plan)
    running = Runner(conn, inventory, alice).start(
        made, plan.registry, QWEN, Execution(concurrency=concurrency), CANARIES
    )
    heard = Heard()
    running.send(heard)
    assert running.finish() == []

    order = [
        "canary" if isinstance(e, CanaryEnded) else "item"
        for e in heard.events
        if isinstance(e, CanaryEnded | ItemStarted | ItemEnded)
    ]
    assert order == ["canary"] * 2 + ["item"] * 8 + ["canary"] * 2
    probes = [(e.call.phase, e.call.canary) for e in heard.of(CanaryEnded)]
    assert probes == [("start", 0), ("start", 1), ("end", 0), ("end", 1)]

    stored = Store(conn).run(running.run)
    assert stored.started.canaries == CANARIES.digest
    served = plan.named("local_engine", QWEN).digest
    for probe in stored.canaries:
        body = CANARIES.canaries[probe.canary].render(model=served)
        assert probe.call.request == fingerprint_request(body)
        assert probe.call.status == 200 and probe.call.prompt_tokens is not None
    registry = Store(conn).load([made.digest, CANARIES.digest])
    assert check_run(stored, registry) == []


@pytest.mark.usefixtures("fake")
def test_canaries_go_only_at_the_phases_planned(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    running = Runner(conn, inventory, alice).start(
        trial(plan), plan.registry, QWEN, canaries=CANARIES, verify_at=("end",)
    )
    running.send()
    assert running.finish() == []
    stored = Store(conn).run(running.run).canaries
    assert sorted((c.phase, c.canary) for c in stored) == [("end", 0), ("end", 1)]


@pytest.mark.usefixtures("fake")
def test_a_stopped_run_sends_no_end_canaries(
    conn: Connection, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    running = Runner(conn, inventory, alice).start(
        trial(plan), plan.registry, QWEN, canaries=CANARIES
    )

    def stop(event: Event) -> None:
        if isinstance(event, Streamed):
            running.stop()

    running.send(Heard(then=stop))
    findings = [(f.code, f.message) for f in running.finish()]
    assert ("run.incomplete", "3 items missing") in findings
    assert ("run.incomplete", "2 canary calls missing") in findings
    stored = Store(conn).run(running.run).canaries
    assert sorted(c.phase for c in stored) == ["start", "start"]


@pytest.mark.usefixtures("fake")
def test_an_interrupt_during_a_canary_records_it_as_stopped(
    conn: Connection,
    inventory: Inventory,
    alice: Person,
    plan: Plan,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real = sending.send

    def interrupted(*args: Any, **kwargs: Any) -> Any:
        heard: list[object] = []

        def on_delta(delta: object) -> None:
            heard.append(delta)
            if len(heard) == 2:
                raise KeyboardInterrupt

        return real(*args, **{**kwargs, "on_delta": on_delta})

    monkeypatch.setattr(sending, "send", interrupted)
    running = Runner(conn, inventory, alice).start(
        trial(plan), plan.registry, QWEN, canaries=CANARIES
    )
    with pytest.raises(KeyboardInterrupt):
        running.send()
    _ = running.finish()
    stored = Store(conn).run(running.run)
    assert [(c.phase, c.canary, c.call.error) for c in stored.canaries] == [
        ("start", 0, STOPPED)
    ]
    assert stored.items == ()


@pytest.mark.usefixtures("fake")
def test_phases_without_a_canary_set_are_refused_before_anything_is_written(
    conn: Connection, db: str, inventory: Inventory, alice: Person, plan: Plan
) -> None:
    with pytest.raises(ValidationError, match="verify_at goes with a canary set"):
        _ = Runner(conn, inventory, alice).start(
            trial(plan), plan.registry, QWEN, verify_at=("end",)
        )
    assert rows(db, "run_stage") == 0

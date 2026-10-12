import codecs
import unicodedata
from collections import Counter

import pytest

from chatddx.curation import init, load_cases
from chatddx.inventory import World, check
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.test.world import DATA, LINTS, TEST, world_plan

pytestmark = pytest.mark.wip

SKIPPED = [
    "from_facts records for test/unknown: the facts don't know it, served by "
    + "engine.remote unknown@remote",
    "from_facts records for test/unserved: no planned engine serves it",
    "reasoning off (openai/gpt-oss-20b): always reasons: vLLM rejects reasoning_effort "
    + "= none for harmony",
    "reasoning on (test/mistral-7b): test/mistral-7b doesn't reason",
    "reasoning high (test/mistral-7b): test/mistral-7b doesn't reason",
    "reasoning on-budget (openai/gpt-oss-20b): no thinking budget is documented for "
    + "harmony",
    "reasoning on-budget (test/mistral-7b): test/mistral-7b doesn't reason",
    "recipe lines-instructed (sv): its output in en needs translations in sv, and "
    + "recipe.lines-instructed names none there",
    "recipe headed (sv): it has no prompt in sv",
    "recipe reasoned (en, test/mistral-7b): the facts refuse its reasoning",
    "recipe budgeted (en, openai/gpt-oss-20b): the facts refuse its reasoning",
    "recipe budgeted (en, test/mistral-7b): the facts refuse its reasoning",
]


@pytest.mark.slow
def test_the_test_world_plans_and_loads_as_designed(conn: Connection) -> None:
    plan = world_plan()
    assert Counter(r.table for r in plan.records) == {
        "model": 3,
        "local_engine": 4,
        "remote_engine": 1,
        "instructions": 2,
        "few_shot": 2,
        "prompt": 3,
        "output": 8,
        "sampling": 5,
        "reasoning": 7,
        "passthrough": 1,
        "translations": 1,
        "tool": 2,
        "toolset": 1,
        "expectation_schema": 1,
        "scorer": 5,
        "recipe": 27,
        "judge": 3,
    }
    assert plan.skipped == SKIPPED
    world = World.load(TEST)

    alice = People(conn).add("alice", "Alice")
    cases = load_cases(DATA)
    source = world.inventory.listing()
    lines = init(conn, plan, cases, source, alice, giftbag=True)
    components = len({r.digest for r in plan.records}) + 2 * len(cases)
    assert [line for line in lines if line.startswith("[lint")] == [
        *LINTS,
        f"[lint] {len(LINTS)} findings in {components} components",
    ]
    adopted = [line for line in lines if line.startswith("[archive case]")]
    assert [line.split(": ")[0] for line in adopted] == [
        f"[archive case] {id}" for id in cases
    ]
    assert all(": created " in line for line in adopted)
    assert check(world.inventory, plan.registry.get) == []

    again = init(conn, plan, cases, source, alice, giftbag=True)
    assert {
        line.split(": ", 1)[1].split(" ")[0]
        for line in again
        if line.startswith(("[archive", "[giftbag"))
    } == {"validated", "kept"}


def test_the_test_world_s_vignettes_hold_what_their_ids_say() -> None:
    source = World.load(TEST).inventory.listing()
    assert source.ids() == sorted(load_cases(DATA))
    raw = {id: source.fetch(id) for id in source.ids()}
    assert raw["crlf"].count(b"\r\n") == 2 and raw["crlf"].endswith(b".\n")
    assert all(b"\r" not in v for id, v in raw.items() if id != "crlf")
    assert raw["bom"].startswith(codecs.BOM_UTF8)
    assert b"  \t\n\n\n" in raw["whitespace"]
    svenska, nfd = raw["svenska"].decode(), raw["nfd"].decode()
    assert (
        set("åäö") <= set(svenska) and unicodedata.normalize("NFC", svenska) == svenska
    )
    assert unicodedata.normalize("NFC", nfd) != nfd

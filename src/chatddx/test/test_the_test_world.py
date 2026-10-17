import codecs
import unicodedata
from collections import Counter

import pytest

from chatddx.curation import init, load_cases
from chatddx.inventory import DirectorySource, World, check
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.test.world import DATA, LINTS, TEST, world_plan

SKIPPED = [
    "facts about test/unknown: none are known, so engine.remote unknown@remote can't "
    + "compile a reasoning level or a recommended sampling",
]


@pytest.mark.slow
def test_the_test_world_plans_and_loads_as_designed(conn: Connection) -> None:
    plan = world_plan()
    assert Counter(r.table for r in plan.records) == {
        "local_model": 3,
        "remote_model": 1,
        "local_engine": 4,
        "remote_engine": 1,
        "facts": 3,
        "instructions": 1,
        "few_shot": 1,
        "prompt": 3,
        "output": 8,
        "sampling": 3,
        "reasoning": 4,
        "passthrough": 1,
        "translations": 1,
        "tool": 2,
        "toolset": 1,
        "expectation_schema": 1,
        "scorer": 6,
        "recipe": 17,
        "judge": 3,
        "canary_set": 1,
    }
    assert plan.skipped == SKIPPED
    assert plan.untranslated == []
    world = World.load(TEST)

    alice = People(conn).add("alice", "Alice")
    cases = load_cases(DATA)
    source = world.inventory.source(kind=DirectorySource)
    lines = init(conn, plan, cases, source, alice, giftbag=True)
    appended = sum(
        len(c.appendices) + sum(1 + (o.targets is not None) for o in c.ordered)
        for c in cases.values()
    )
    components = len({r.digest for r in plan.records}) + 2 * len(cases) + appended
    assert [line for line in lines if line.startswith("[lint")] == [
        *LINTS,
        f"[lint] {len(LINTS)} findings in {components} components",
    ]
    adopted = [line for line in lines if line.startswith("[archive case]")]
    assert [line.split(": ")[0] for line in adopted] == [
        line
        for id, case in cases.items()
        for line in (
            f"[archive case] {id}",
            *(
                f"[archive case] {id} with {', '.join(o.appendices)}"
                for o in case.ordered
            ),
        )
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
    source = World.load(TEST).inventory.source(kind=DirectorySource)
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

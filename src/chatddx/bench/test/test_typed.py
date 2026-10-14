import pytest

from chatddx import settings
from chatddx.bench import Bench, OverQuota
from chatddx.factors.base import Fingerprint, resolve
from chatddx.factors.cases import Case
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.store import Store, fetch_vignette
from chatddx.test.world import LINES, QWEN

TYPED = "A 54-year-old woman with sudden breathlessness after a long flight."


def test_a_typed_case_is_kept_with_its_case_and_family(bench: Bench) -> None:
    family = bench.type_case(TYPED, name="flight", language="en")
    about = family.about
    assert (family.name, about.owner, about.language) == (
        "flight",
        bench.person.id,
        "en",
    )
    vignette = resolve(bench.get, family.case, Case).vignette
    assert vignette.source == "typed"
    assert vignette.fingerprint == Fingerprint.of(TYPED.encode())
    assert fetch_vignette(bench.conn, bench.inventory, vignette) == TYPED.encode()
    assert family.id in [f.id for f in bench.families()]

    unnamed = bench.type_case(TYPED)
    assert unnamed.case != family.case and unnamed.about.name is None


def test_what_can_t_be_typed_is_refused(
    bench: Bench, monkeypatch: pytest.MonkeyPatch
) -> None:
    for text, said in (
        ("  \n", "a typed case holds text"),
        ("a\0b", "U\\+0000"),
    ):
        with pytest.raises(ValueError, match=said):
            _ = bench.type_case(text)
    with pytest.raises(ValueError, match="'test' isn't a database source"):
        _ = bench.type_case(TYPED, source="test")
    with pytest.raises(ValueError, match="is not a language tag"):
        _ = bench.type_case(TYPED, language="Swedish")
    with pytest.raises(ValueError, match="a name can't be empty"):
        _ = bench.type_case(TYPED, name="")

    monkeypatch.setattr(settings, "TYPED_TEXT_LIMIT", 10)
    with pytest.raises(ValueError, match=f"at most 10 characters, not {len(TYPED)}"):
        _ = bench.type_case(TYPED)
    monkeypatch.setattr(settings, "TYPED_TEXT_LIMIT", 1000)
    monkeypatch.setattr(settings, "TYPED_PER_DAY", 1)
    _ = bench.type_case(TYPED)
    with pytest.raises(OverQuota, match="alice has typed 1 cases in the last day"):
        _ = bench.type_case(TYPED)


@pytest.mark.usefixtures("fake")
def test_a_typed_case_runs_as_any_case(
    bench: Bench, world: Inventory, alice: Person
) -> None:
    on_world = Bench(bench.conn, alice, world, bench.facts)
    family = on_world.type_case(TYPED)
    variation = on_world.configuration(LINES, on_world.endpoint(QWEN))
    running = on_world.start(variation, QWEN, [family.case], 7)
    running.send(lambda _: None)
    assert running.finish() == []
    [item] = Store(bench.conn).run(running.run).items
    assert (item.key.case, item.call.status, item.call.error) == (
        family.case,
        200,
        None,
    )

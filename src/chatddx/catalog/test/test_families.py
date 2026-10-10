import pytest

from chatddx.catalog import Entry, EntryField, Subject, Survey, families
from chatddx.catalog.test.memory import Memory
from chatddx.factors.base import resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Case, Vignette
from chatddx.factors.scoring import Expectation, Scoring
from chatddx.factors.test.sample import fp, world

pytestmark = pytest.mark.solidified


def test_cases_find_their_family_through_its_bindings() -> None:
    reg = Registry()
    ids = world(reg)
    rows = Memory(reg)
    vignette = resolve(reg.get, ids["case"], Case).vignette
    assert families.family_of(rows, ids["case"]) is None
    _ = rows.bind(1, vignette)
    assert families.family_of(rows, ids["case"]) == 1
    assert families.family_of(rows, ids["trial"]) is None

    renamed = reg.add(Case(vignette=vignette.model_copy(update={"id": "c1-renamed"})))
    edited = reg.add(
        Case(vignette=vignette.model_copy(update={"fingerprint": fp("edited")}))
    )
    with pytest.raises(ValueError, match="a new name"):
        _ = families.check_adoptable(rows, renamed)
    with pytest.raises(ValueError, match="new content"):
        _ = families.check_adoptable(rows, edited)
    with pytest.raises(LookupError):
        _ = families.check_adoptable(rows, ids["trial"])

    source, fingerprint = vignette.source, vignette.fingerprint
    assert families.survey(rows, source, {"c1": fingerprint}) == Survey(unchanged=(1,))
    assert families.survey(rows, source, {"c1-renamed": fingerprint}).renamed == (
        (1, "c1", "c1-renamed"),
    )
    assert families.survey(rows, source, {"c1": fp("edited")}).changed == (
        (1, "c1", fp("edited")),
    )
    assert families.survey(rows, source, {}).gone == (1,)


def test_only_a_family_s_current_place_holds_a_vignette() -> None:
    reg = Registry()
    ids = world(reg)
    rows = Memory(reg)
    vignette = resolve(reg.get, ids["case"], Case).vignette
    _ = rows.bind(1, vignette)
    _ = rows.bind(1, vignette.model_copy(update={"id": "c1-renamed"}))
    elsewhere = Vignette(source="other", id="c1", fingerprint=vignette.fingerprint)
    _ = rows.bind(2, elsewhere)
    assert [b.family for b in rows.bindings_sharing(vignette)] == [1, 1]

    reused = reg.add(
        Case(vignette=vignette.model_copy(update={"fingerprint": fp("another")}))
    )
    assert families.holder(rows, resolve(reg.get, reused, Case).vignette) is None
    assert families.check_adoptable(rows, reused).id == "c1"
    assert families.family_of(rows, ids["case"]) == 1


def test_repairs_rebind_appendices_cases_and_expectations() -> None:
    reg = Registry()
    ids = world(reg)
    rows = Memory(reg)
    case = resolve(reg.get, ids["case"], Case)
    [appendix] = case.appendices
    expectation = resolve(reg.get, ids["scoring"], Scoring).expectations[0]
    _ = rows.bind(1, case.vignette)
    _ = rows.bind(
        2, Vignette(source=case.vignette.source, id="c2", fingerprint=fp("x"))
    )
    appended, expected = rows.start(appendix), rows.start(expectation)
    with pytest.raises(ValueError, match="exactly one"):
        _ = families.plan_repair(rows, 1)
    with pytest.raises(ValueError, match="family 2 already has the id 'c2'"):
        _ = families.plan_repair(rows, 1, id="c2")
    with pytest.raises(ValueError, match="family 2 already has that content"):
        _ = families.plan_repair(rows, 1, fingerprint=fp("x"))

    plan = families.plan_repair(rows, 1, id="c1-renamed")
    renamed = case.vignette.model_copy(update={"id": "c1-renamed"})
    rebound = resolve(plan.registry.get, plan.cases[ids["case"]], Case)
    assert rebound == Case(vignette=renamed, appendices=(plan.appendices[appendix],))
    e = resolve(reg.get, expectation, Expectation)
    rekeyed = Expectation(
        case=rebound.digest, expectation_schema=e.expectation_schema, data=e.data
    )
    assert plan.moves == [
        (appended.thread, plan.appendices[appendix]),
        (expected.thread, rekeyed.digest),
    ]
    content = families.plan_repair(rows, 1, fingerprint=fp("edited"))
    assert content.moves == [(appended.thread, content.appendices[appendix])]
    same_id = families.plan_repair(
        rows, 1, id=case.vignette.id, fingerprint=fp("edited")
    )
    assert same_id.moves == content.moves

    current = rows.bind(1, renamed)
    [stale] = families.stale_cases(rows, [("/cases/0", ids["case"])])
    assert (stale.binding, stale.replacement) == (current, plan.cases[ids["case"]])
    rows.note(Subject(family=1), Entry(field=EntryField.DELETED))
    assert families.stale_cases(rows, [("/cases/0", ids["case"])]) == []


def test_a_person_sees_the_live_families_they_own_or_share() -> None:
    reg = Registry()
    vignette = resolve(reg.get, world(reg)["case"], Case).vignette
    rows = Memory(reg)
    for family, owner, shared in ((1, 3, 1), (2, 2, None), (3, 1, None), (4, 1, None)):
        _ = rows.bind(family, vignette.model_copy(update={"id": f"c{family}"}))
        rows.note(Subject(family=family), Entry(field=EntryField.OWNER, person=owner))
        if shared is not None:
            rows.note(
                Subject(family=family),
                Entry(field=EntryField.COLLABORATOR, person=shared),
            )
    rows.note(Subject(family=1), Entry(field=EntryField.TAG, value="cardiac"))
    rows.note(Subject(family=4), Entry(field=EntryField.DELETED))
    seen = families.visible(rows, 1)
    assert [(f, a.owner, a.tags) for f, a in seen] == [
        (1, 3, frozenset({"cardiac"})),
        (3, 1, frozenset()),
    ]

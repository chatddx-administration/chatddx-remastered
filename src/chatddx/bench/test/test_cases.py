import pytest

from chatddx.bench import Bench, NotFound
from chatddx.factors.base import Fingerprint, resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Appendix, Case, Vignette
from chatddx.identity import Person
from chatddx.store import Catalog, People, Store

pytestmark = pytest.mark.wip

ZERO = "sha256:" + "0" * 64


def test_an_appendix_makes_a_case_and_its_edit_a_replacement(bench: Bench) -> None:
    family = bench.family("noted")
    labs = bench.appendix(family.id, "Lab:\r\nCRP 120\rHb 98")
    assert labs.text == "Lab:\nCRP 120\nHb 98"
    made = bench.new(labs, "labs")
    assert bench.catalog.thread(made.edit.thread).kind == "appendix"

    case = bench.case(family.id, [labs.digest])
    assert resolve(bench.get, case, Case).appendices == (labs.digest,)
    assert bench.cases(family.id) == [family.case, case]
    assert bench.catalog.family(case) == family.id

    newer = bench.appendix(family.id, "Lab:\nCRP 150")
    edited = bench.edit_component(made.edit.thread, made.edit.id, newer)
    [(old, replacement)] = edited.cases.items()
    assert old == case
    assert resolve(bench.get, replacement, Case).appendices == (newer.digest,)
    assert bench.cases(family.id) == [family.case, *sorted([case, replacement])]
    unchanged = bench.edit_component(made.edit.thread, edited.edit.id, newer)
    assert (unchanged.what, unchanged.cases) == ("unchanged", {})


def test_an_expectation_is_carried_onto_another_case_of_its_family(
    bench: Bench,
) -> None:
    catalog = bench.catalog
    family = bench.family("noted")
    [schema] = bench.expectation_schemas(family.case)
    [mine] = catalog.expectation_choices([family.case], bench.person.id, schema)[
        family.case
    ]
    held = bench.expectation(family.case, schema)
    assert held is not None
    labs = bench.appendix(family.id, "Lab: CRP 120")
    _ = bench.new(labs, "labs")
    case = bench.case(family.id, [labs.digest])

    carried = bench.carry(mine, catalog.head(mine).id, case)
    assert carried.what == "a new version"
    moved = bench.expectation(case, schema)
    assert moved is not None and moved.data == held.data
    assert bench.expectation(family.case, schema) is None

    other = bench.family("crlf").case
    with pytest.raises(ValueError, match=f"{other} isn't a case of the family"):
        _ = bench.carry(mine, carried.edit.id, other)
    appendix = bench.thread("appendix", "labs")[0].thread
    with pytest.raises(ValueError, match=f"appendix {appendix} isn't an expectation"):
        _ = bench.carry(appendix, bench.catalog.head(appendix).id, case)


def test_what_isn_t_the_person_s_to_build_on_is_refused(
    bench: Bench, bob: Person
) -> None:
    family, other = bench.family("noted"), bench.family("crlf")
    elsewhere = Vignette(source="test", id="nowhere", fingerprint=Fingerprint.of(b""))
    with pytest.raises(ValueError, match="bound to the current vignette of a case"):
        _ = bench.new(Appendix(vignette=elsewhere, text="x"), "x")
    with pytest.raises(NotFound, match=f"no appendix {ZERO} for alice"):
        _ = bench.case(family.id, [ZERO])

    theirs = bench.appendix(other.id, "Lab: none")
    _ = bench.new(theirs, "other's")
    with pytest.raises(ValueError, match="bound to another vignette"):
        _ = bench.case(family.id, [theirs.digest])
    with pytest.raises(ValueError, match="at its family's current vignette already"):
        _ = bench.replacement(family.case)

    bobs = Bench(bench.conn, bob, bench.inventory, bench.facts)
    with pytest.raises(NotFound, match=f"no case {family.id} for bob"):
        _ = bobs.appendix(family.id, "x")


def test_a_late_case_is_given_its_replacement(bench: Bench) -> None:
    catalog, store = Catalog(bench.conn), Store(bench.conn)
    archive = People(bench.conn).find("archive")
    assert archive is not None
    family = bench.family("noted")
    old = resolve(bench.get, family.case, Case).vignette
    _ = catalog.repair(family.id, archive.id, fingerprint=Fingerprint.of(b"anew"))
    current = catalog.bindings(family.id)[-1].vignette

    registry = Registry()
    late_labs = registry.add(Appendix(vignette=old, text="Lab: late"))
    late = registry.add(Case(vignette=old, appendices=(late_labs,)))
    _ = store.add(registry, [late])

    replacement = resolve(bench.get, bench.replacement(late), Case)
    assert replacement.vignette == current
    [labs] = replacement.appendices
    assert resolve(bench.get, labs, Appendix).text == "Lab: late"
    assert replacement.digest in bench.cases(family.id)

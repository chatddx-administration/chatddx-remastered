from pathlib import Path

import pytest

from chatddx.catalog import Subject
from chatddx.curation import init, load_cases
from chatddx.curation.test.cases import CASES, vignettes
from chatddx.factors.cases import Appendix, Case
from chatddx.store import Catalog, People, Store
from chatddx.store.store import Connection
from chatddx.test.world import DATA, world_plan

pytestmark = pytest.mark.wip


def test_a_case_names_its_appendices_and_the_cases_that_send_them() -> None:
    whitespace = load_cases(DATA)["whitespace"]

    assert set(whitespace.appendices) == {"labs"}
    [ordered] = whitespace.ordered
    assert ordered.appendices == ("labs",)
    assert ordered.targets == {"diagnosis": {"pattern": "appendicitis & perforat*"}}


@pytest.mark.parametrize(
    ("more", "refusal"),
    [
        ('appendices = "labs"\n', "appendices are a table of texts by name"),
        ("appendices.labs = 1\n", r"appendices \['labs'\] aren't texts"),
        ("[[case.alpha.with]]\n", "name its appendices, in order"),
        ('[[case.alpha.with]]\nappendices = ["xray"]\n', r"no appendices \['xray'\]"),
        ('[[case.alpha.with]]\nappendices = ["labs", "labs"]\n', "named twice"),
        (
            '[[case.alpha.with]]\nappendices = ["labs"]\ntags = ["x"]\n',
            r"unknown keys \['tags'\]",
        ),
        (
            '[[case.alpha.with]]\nappendices = ["labs"]\n' * 2,
            "a case with appendices is twice",
        ),
    ],
)
def test_appendices_are_refused_where_they_say_the_wrong_thing(
    tmp_path: Path, more: str, refusal: str
) -> None:
    case = '[case.alpha]\ntargets.diagnosis.pattern = "x"\n'
    labs = '[case.alpha.appendices]\nlabs = "CRP 180."\n'
    held = case + (more if more.startswith("appendices") else labs + more)
    _ = (tmp_path / "cases-en.toml").write_text(held)

    with pytest.raises(ValueError, match=refusal):
        _ = load_cases(tmp_path)


def test_a_canary_set_is_planned_as_a_record() -> None:
    [probe] = [r for r in world_plan().records if r.table == "canary_set"]

    assert (probe.name, probe.kind) == ("probe", "canary_set")


@pytest.mark.slow
def test_init_data_lands_appendices_the_cases_that_send_them_and_canary_sets(
    conn: Connection,
) -> None:
    alice = People(conn).add("alice", "Alice")
    plan = world_plan()
    lines = init(conn, plan, CASES, vignettes(), alice, giftbag=True)
    catalog, store = Catalog(conn), Store(conn)
    archive = People(conn).find("archive")
    assert archive is not None

    [thread] = catalog.find("appendix", "labs for whitespace", owner=archive.id)
    appendix = store.get(catalog.head(thread).digest)
    assert (
        isinstance(appendix, Appendix)
        and appendix.text == "CRP 180 mg/L, leukocytes 16."
    )
    assert alice.id in catalog.about(Subject(thread=thread)).collaborators

    [bare] = [c for c in vignettes().cases() if c.vignette.id == "whitespace"]
    sent = Case(vignette=bare.vignette, appendices=(appendix.digest,))
    assert store.get(sent.digest) == sent
    assert catalog.family(sent.digest) == catalog.family(bare.digest)
    assert f"[archive case] whitespace with labs: created {sent.digest[7:13]}" in lines

    [schema] = [r.digest for r in plan.records if r.kind == "expectation_schema"]
    [mine] = catalog.expectation_choices([sent.digest], alice.id, schema)[sent.digest]
    assert catalog.about(Subject(thread=mine)).owner == alice.id

    [canaries] = catalog.find("canary_set", "probe", owner=archive.id)
    assert alice.id in catalog.about(Subject(thread=canaries)).collaborators

from dataclasses import replace
from pathlib import Path

import pytest

from chatddx.catalog import Subject, families, read, threads, titles
from chatddx.curation import load_cases, sync
from chatddx.curation.test.cases import CASES, TEXTS, vignettes
from chatddx.factors.cases import Appendix, Case
from chatddx.identity import Person, owns, sees
from chatddx.store import People, Rows, Store
from chatddx.store.store import Connection
from chatddx.test.world import DATA, loaded, world_plan


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


def test_a_canary_set_is_planned_as_a_stanza() -> None:
    [probe] = [r for r in world_plan().stanzas if r.table == "canary_set"]

    assert (probe.name, probe.kind) == ("probe", "canary_set")


@pytest.mark.slow
def test_sync_lands_appendices_the_cases_that_send_them_and_canary_sets(
    conn: Connection,
) -> None:
    alice = People(conn).add("alice", "Alice")
    plan = world_plan()
    lines = loaded(conn, plan, CASES, vignettes(), alice, giftbag=True)
    store = Store(conn)
    rows = Rows(conn)
    archive = People(conn).find("archive")
    assert archive is not None

    [thread] = threads.find(rows, "appendix", "labs", owner=archive.id)
    appendix = store.get(threads.head(rows, thread).digest)
    assert (
        isinstance(appendix, Appendix)
        and appendix.text == "CRP 180 mg/L, leukocytes 16."
    )
    assert alice.id in read.about(rows, Subject(thread=thread)).collaborators

    [bare] = [c for c in vignettes().cases() if c.vignette.id == "whitespace"]
    sent = Case(vignette=bare.vignette, appendices=(appendix.digest,))
    assert store.get(sent.digest) == sent
    assert families.family_of(rows, sent.digest) == families.family_of(
        rows, bare.digest
    )
    assert f"[archive case] whitespace with labs: created {sent.digest[7:13]}" in lines
    assert titles.title_of(rows, sent.digest) == "whitespace with labs"

    [schema] = [r.digest for r in plan.stanzas if r.kind == "expectation_schema"]
    expecting = threads.expecting(rows, [sent.digest], schema)[sent.digest]
    [mine] = [e.thread for e, a in expecting if owns(alice.id, a)]
    assert read.about(rows, Subject(thread=mine)).owner == alice.id

    [canaries] = threads.find(rows, "canary_set", "probe", owner=archive.id)
    assert alice.id in read.about(rows, Subject(thread=canaries)).collaborators


@pytest.mark.parametrize("template", ["loaded"], indirect=True)
@pytest.mark.slow
def test_a_sync_prunes_appendices_the_data_drops_and_restores_those_it_takes_back(
    conn: Connection, alice: Person
) -> None:
    rows = Rows(conn)
    archive = People(conn).find("archive")
    assert archive is not None
    [labs] = threads.find(rows, "appendix", "labs", owner=archive.id)
    assert sees(alice.id, read.about(rows, Subject(thread=labs)))
    [bare] = [c for c in vignettes().cases() if c.vignette.id == "whitespace"]
    family = families.family_of(rows, bare.digest)
    assert family is not None

    gone = vignettes({id: t for id, t in TEXTS.items() if id != "whitespace"})
    lines = sync(conn, world_plan(), CASES, gone)
    assert "[archive case] whitespace: missing at source 'test'" in lines
    assert not [line for line in lines if "pruned" in line]
    assert sees(alice.id, read.about(rows, Subject(thread=labs)))

    plain = replace(CASES["whitespace"], appendices={}, ordered=())
    lines = sync(conn, world_plan(), {**CASES, "whitespace": plain}, vignettes())
    assert sorted(line for line in lines if "pruned" in line) == [
        "[archive appendix] labs for whitespace: pruned, not in the data",
        "[archive expectation] whitespace with labs: pruned, not in the data",
    ]
    about = read.about(rows, Subject(thread=labs))
    assert about.deleted and not sees(alice.id, about)
    assert alice.id not in about.collaborators
    assert sees(alice.id, read.about(rows, Subject(family=family)))

    lines = sync(conn, world_plan(), CASES, vignettes())
    assert any(
        line.startswith("[archive appendix] labs for whitespace: restored ")
        for line in lines
    )
    assert any(
        line.startswith("[archive expectation] whitespace with labs: restored ")
        for line in lines
    )
    assert threads.find(rows, "appendix", "labs", owner=archive.id) == [labs]
    assert sees(alice.id, read.about(rows, Subject(thread=labs)))

from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest

from chatddx.catalog import Entry, EntryField, Subject, families, read, threads, titles
from chatddx.catalog.language import language_of
from chatddx.cli import main
from chatddx.conftest import connect
from chatddx.curation import init
from chatddx.curation.test.cases import CASES, TEXTS, appended, vignettes
from chatddx.identity import Person
from chatddx.store import Catalog, People, Rows
from chatddx.store.store import Connection
from chatddx.test.world import (
    DATA,
    FACT_LINTS,
    FACTOR_LINTS,
    LINES_GUIDED,
    LINTS,
    NATIVE,
    NATIVE_TOOLS,
    TEST,
    copied,
    edit,
    world_plan,
)

LANGUAGES = (", in en", ", in sv")


def tally(lines: list[str]) -> Counter[str]:
    def what(line: str) -> str:
        prefix = line[1 : line.index("]")].split(" ")[0]
        if prefix in ("skipped", "share", "lint"):
            return prefix
        return f"{prefix} {line.split(': ', 1)[1].split(' ')[0]}"

    return Counter(what(line) for line in lines)


def edited(tmp_path: Path, file: str, old: str, new: str) -> Path:
    world = copied(tmp_path)
    edit(world / file, old, new)
    return world


@pytest.mark.slow
def test_init_data_loads_the_archive(conn: Connection) -> None:
    alice = People(conn).add("alice", "Alice")
    plan = world_plan()
    lines = init(conn, plan, CASES, vignettes(), alice)
    appendices, ordered, expected = appended(CASES)
    made = len(plan.records) + len(CASES) + appendices + expected
    assert tally(lines) == Counter(
        {
            "archive created": made + len(CASES) + ordered,
            "skipped": len(plan.skipped),
            "share": 1,
            "lint": len(LINTS) + 1,
        }
    )
    shared = made + len(CASES)
    assert (
        lines[-len(LINTS) - 2]
        == f"[share] {shared} of {shared} archive threads and families with alice"
    )
    components = (
        len({r.digest for r in plan.records}) + 2 * len(CASES) + sum(appended(CASES))
    )
    assert lines[-len(LINTS) - 1 :] == [
        *LINTS,
        f"[lint] {len(LINTS)} findings in {components} components",
    ]

    rows = Rows(conn)
    archive = People(conn).find("archive")
    assert archive is not None
    [native] = threads.find(rows, "skeleton", NATIVE, owner=archive.id)
    [tools] = threads.find(rows, "skeleton", NATIVE_TOOLS)
    diverged = threads.divergence(rows, tools)
    assert diverged is not None and set(diverged.varies) == {"/recipe/toolset"}
    assert diverged.base.thread == native
    about = read.about(rows, Subject(thread=native))
    assert (about.owner, about.tags, alice.id in about.collaborators) == (
        archive.id,
        frozenset({"structured"}),
        True,
    )
    [case] = [c for c in vignettes().cases() if c.vignette.id == "crlf"]
    family = families.family_of(rows, case.digest)
    assert family is not None
    assert read.about(rows, Subject(family=family)).language == "en"
    assert titles.title_of(rows, case.digest) == "crlf"
    [scorer] = threads.find(rows, "scorer", "answer", owner=archive.id)
    assert read.labels(rows, threads.head(rows, scorer).id) == {
        ("view", 0): "differential",
        ("view", 1): "warning",
        ("view", 2): "disposition",
        ("view", 3): "dont-miss",
    }
    [tool] = threads.find(rows, "tool", "lookup", owner=archive.id)
    assert read.about(rows, Subject(thread=tool)).description == "Look the query up."
    assert [line for line in lines if line.endswith(LANGUAGES)] == [
        f"[archive {r.kind}] {r.name}: created {r.digest.removeprefix('sha256:')[:6]}"
        + f", in {r.language}"
        for r in plan.records
        if r.language is not None
    ]
    assert language_of(rows, plan.named("toolset", "lookup").digest) == "en"
    assert language_of(rows, plan.named("prompt", "case").digest) is None
    assert language_of(rows, plan.named("recipe", LINES_GUIDED).digest) == "en"
    assert language_of(rows, plan.named("translations", "guided").digest) is None

    # The rest of the cases, and their expectations, are left over.
    some = {id: CASES[id] for id in ("crlf", "svenska")}
    again = init(conn, world_plan(), some, vignettes(), alice)
    assert {v for v in tally(again) if v.startswith("archive")} == {
        "archive validated",
        "archive not",
    }
    left = {id: case for id, case in CASES.items() if id not in some}
    appendices, _, expected = appended(left)
    assert tally(again)["archive not"] == 2 * len(left) + appendices + expected
    assert "[archive case] matched: not in the data" in again
    assert again[-len(LINTS) - 2].startswith("[share] 0 of ")
    assert not [line for line in again if line.endswith(LANGUAGES)]


@pytest.mark.parametrize("template", ["loaded"], indirect=True)
@pytest.mark.slow
def test_init_data_lints_what_it_lands(conn: Connection, alice: Person) -> None:
    plan = world_plan()
    unlike = replace(CASES["noted"], targets={"warning": {"pattern": "shock"}})
    lines = init(conn, plan, {**CASES, "noted": unlike}, vignettes(), alice)
    components = (
        len({r.digest for r in plan.records}) + 2 * len(CASES) + sum(appended(CASES))
    )
    assert [line for line in lines if line.startswith("[lint")] == [
        *FACTOR_LINTS,
        "[lint warning] expectation noted: expectation.invalid: at the root: "
        + "'diagnosis' is a required property",
        *FACT_LINTS,
        f"[lint] {1 + len(LINTS)} findings in {components} components",
    ]


@pytest.mark.parametrize("template", ["loaded"], indirect=True)
@pytest.mark.slow
def test_init_data_updates_and_gives_forks(
    conn: Connection, alice: Person, tmp_path: Path
) -> None:
    world = edited(
        tmp_path,
        "_data/texts-en.toml",
        'guidance = "List the plausible diagnoses, most likely first."',
        'guidance = "List the diagnoses, most likely first."',
    )
    plan = world_plan(world, world / "_data")
    lines = init(
        conn,
        plan,
        CASES,
        vignettes(crlf=b"Edited at the source."),
        alice,
        giftbag=True,
    )
    assert sorted(line for line in lines if "updated" in line) == [
        line
        for line in sorted(lines)
        if line.startswith(
            (
                "[archive chunk.output] tool-answer:",
                "[archive skeleton] tool-answer:",
                "[archive skeleton] tool-answer-tools:",
            )
        )
    ]
    assert len([line for line in lines if "updated" in line]) == 3
    assert any(line.startswith("[archive case] crlf: needs repair") for line in lines)
    forked = [line for line in lines if line.startswith("[giftbag")]
    assert forked and all(line.split(": ")[1].startswith("forked") for line in forked)
    assert not any(
        line.startswith(("[giftbag expectation_schema", "[giftbag scorer"))
        for line in forked
    )
    assert any(line.startswith("[giftbag tool] lookup: forked") for line in forked)

    rows = Rows(conn)
    archive = People(conn).find("archive")
    assert archive is not None
    output = "tool-answer"
    [archived] = threads.find(rows, "chunk.output", output, owner=archive.id)
    assert len(threads.find(rows, "chunk.output", output, owner=alice.id)) == 1
    owners = [
        read.about(rows, Subject(thread=t)).owner for t in threads.forks(rows, archived)
    ]
    assert owners.count(alice.id) == 1
    again = init(
        conn,
        plan,
        CASES,
        vignettes(crlf=b"Edited at the source."),
        alice,
        giftbag=True,
    )
    assert {line.split(": ")[1] for line in again if line.startswith("[giftbag")} == {
        "kept"
    }

    gone = vignettes({})
    lines = init(conn, plan, {"noted": CASES["noted"]}, gone, alice)
    assert "[archive case] noted: missing at source 'test'" in lines


@pytest.mark.slow
def test_init_data_says_when_a_thread_is_held_as_another_fork_than_the_data_s(
    conn: Connection, tmp_path: Path
) -> None:
    alice = People(conn).add("alice", "Alice")
    factors = "_data/factors.toml"
    guided = 'fork_of = "lines-instructed"\n'
    before = edited(tmp_path / "before", factors, guided, "")
    after = edited(tmp_path / "after", factors, 'fork_of = "native"\n', "")
    _ = init(conn, world_plan(before, before / "_data"), CASES, vignettes(), alice)
    lines = init(conn, world_plan(after, after / "_data"), CASES, vignettes(), alice)
    assert sorted(line for line in lines if "; the data forks it from " in line) == [
        f"[archive skeleton] {LINES_GUIDED}: held as no fork; the data forks it from "
        + "lines-instructed",
        "[archive skeleton] native-tools: held as a fork of native; the data "
        + "forks it from nothing",
    ]


@pytest.mark.parametrize("template", ["loaded"], indirect=True)
@pytest.mark.slow
def test_init_data_withdraws_only_the_tags_the_archive_gave(
    conn: Connection, alice: Person, tmp_path: Path
) -> None:
    catalog = Catalog(conn)
    rows = Rows(conn)
    [native] = threads.find(rows, "skeleton", NATIVE)
    [case] = [c for c in vignettes().cases() if c.vignette.id == "bom"]
    family = families.family_of(rows, case.digest)
    assert family is not None
    for subject in (Subject(thread=native), Subject(family=family)):
        catalog.note(subject, Entry(field=EntryField.TAG, value="alice's"), alice.id)

    described = (
        'description = "A native contract, sampled as the model\'s makers recommend."\n'
    )
    world = edited(
        tmp_path,
        "_data/factors.toml",
        described + 'tags = ["structured"]\n',
        described,
    )
    retagged = {**CASES, "bom": replace(CASES["bom"], tags=("falls",))}
    _ = init(conn, world_plan(world, world / "_data"), retagged, vignettes(), alice)
    assert read.about(rows, Subject(thread=native)).tags == {"alice's"}
    assert read.about(rows, Subject(family=family)).tags == {"alice's", "falls"}


@pytest.mark.parametrize("template", ["loaded"], indirect=True)
@pytest.mark.slow
def test_init_data_says_how_a_vignette_moved_at_its_source(
    conn: Connection, alice: Person
) -> None:
    rows = Rows(conn)
    family_at = {
        c.vignette.id: families.family_of(rows, c.digest) for c in vignettes().cases()
    }
    moved = vignettes(
        {id: text for id, text in TEXTS.items() if id != "noted"},
        noted2=TEXTS["noted"],
        crlf=b"Edited at the source.",
    )
    at = "at source 'test'; repair-data rebinds family"
    lines = init(conn, world_plan(), CASES, moved, alice)
    assert [line for line in lines if "needs repair" in line] == [
        f"[archive case] crlf: needs repair: changed {at} {family_at['crlf']}",
        f"[archive case] noted: needs repair: renamed to noted2 {at} "
        + str(family_at["noted"]),
    ]
    assert not [line for line in lines if "not in the data" in line]

    renamed = {**CASES, "noted2": CASES["noted"]}
    del renamed["noted"]
    lines = init(conn, world_plan(), renamed, moved, alice)
    assert (
        f"[archive case] noted2: needs repair: renamed from noted {at} "
        + str(family_at["noted"])
    ) in lines
    assert not [line for line in lines if "not in the data" in line]


# What it loads is read in test_wipe_data_deletes_and_unshares_and_init_data_gives_it_back.
@pytest.mark.slow
def test_init_data_command(
    db: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DB_NAME", db)
    monkeypatch.setenv("CHATDDX_WORLD", str(TEST))
    data = ["--data", str(DATA)]
    empty = tmp_path / "empty"
    (empty / "vignettes").mkdir(parents=True)
    _ = (empty / "inventory.toml").write_text('[source.test]\npath = "vignettes"\n')
    two = tmp_path / "two"
    (two / "vignettes").mkdir(parents=True)
    _ = (two / "inventory.toml").write_text(
        '[source.test]\npath = "vignettes"\n[source.more]\npath = "vignettes"\n'
        + '[source.typed]\nkind = "database"\n'
    )
    for argv, refusal in [
        (["--world", str(tmp_path)], "is no World: it holds no inventory.toml"),
        (
            ["--world", str(empty)],
            f"none of the data's {len(CASES)} cases is in source 'test' of",
        ),
        (["--world", str(two)], r"2 directory sources \(more, test\) are in the inv"),
        (["--world", str(two), "--source", "typed"], "'typed' isn't a directory"),
        (["--source", "other"], "no source 'other'"),
        (["--facts", str(DATA / "factors.toml")], "facts have only 'model' tables"),
    ]:
        with pytest.raises(SystemExit, match=refusal):
            main(["init-data", "alice", *data, *argv])
    monkeypatch.delenv("CHATDDX_WORLD")
    with pytest.raises(SystemExit, match="give a World with --world DIR"):
        main(["init-data", "alice", *data])


@pytest.mark.slow
def test_a_world_brings_its_engines_and_their_models_facts(
    db: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DB_NAME", db)
    world = copied(tmp_path)
    ghost = "sha256:" + "c" * 64
    with (world / "inventory.toml").open("a") as f:
        _ = f.write(
            f'\n[endpoint.ghost]\nengine = "{ghost}"\nurl = "http://127.0.0.1:1/v1/"\n'
        )
    main(["init-data", "alice", "--world", str(world), "--data", str(world / "_data")])
    out = capsys.readouterr().out.splitlines()
    assert any(
        line.startswith("[archive engine.remote] unknown@remote: created")
        for line in out
    )
    assert out[-2:] == [
        f"[world warning] ghost: endpoint.engine_unknown: {ghost} is not in the registry",
        f"[world] 1 finding in 6 endpoints of {world}",
    ]
    for made in (
        "[archive facts] test/mistral-7b: created",
        "[archive chunk.sampling] recommended: created",
        "[archive skeleton] native: created",
    ):
        assert any(line.startswith(made) for line in out), made


@pytest.mark.slow
def test_wipe_data_deletes_and_unshares_and_init_data_gives_it_back(
    db: str,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DB_NAME", db)

    def run(*argv: str) -> list[str]:
        main(list(argv))
        return capsys.readouterr().out.splitlines()

    def counts() -> tuple[int, int]:
        with connect(db) as conn:
            threads = conn.execute("SELECT count(*) FROM catalog.thread").fetchone()
            entries = conn.execute("SELECT count(*) FROM catalog.entry").fetchone()
        assert threads is not None and entries is not None
        return threads[0], entries[0]

    argv = ["init-data", "alice", "--world", str(TEST), "--giftbag"]
    argv += ["--data", str(DATA)]
    loaded = run(*argv)
    assert loaded[0] == "[person] alice: added"
    assert loaded[1].startswith("[archive model.local] qwen3-8b-awq: created")
    assert any(
        line.startswith("[archive chunk.prompt] case: created") for line in loaded
    )
    assert any(line.startswith("[giftbag skeleton] native:") for line in loaded)
    assert [line for line in loaded if line.startswith("[world")] == [
        f"[world] 0 findings in 5 endpoints of {TEST}"
    ]
    with connect(db) as conn:
        assert conn.execute("SELECT count(*) FROM catalog.family").fetchone() == (
            len(CASES),
        )
    gifts = sum(line.startswith("[giftbag ") for line in loaded)
    shares = int(next(line for line in loaded if line.startswith("[share]")).split()[1])
    threads, entries = counts()

    with monkeypatch.context() as patch:
        patch.setenv("CHATDDX_WORLD", str(TEST))
        again = run("init-data", "alice", "--giftbag", "--data", str(DATA))
    assert not [line for line in again if line.startswith("[person]")]
    with connect(db) as conn:
        alice = People(conn).find("alice")
    assert alice is not None and (alice.name, alice.roles) == ("alice", frozenset())
    assert {
        line.split(": ")[1].split(" ")[0]
        for line in again
        if line.startswith("[archive")
    } == {"validated"}
    assert counts() == (threads, entries)

    wiped = run("wipe-data", "alice")
    assert sum(int(line.split("deleted ")[1].split(",")[0]) for line in wiped) == gifts
    assert sum(int(line.split("unshared ")[1]) for line in wiped) == shares
    assert counts() == (threads, entries + gifts + shares)
    with connect(db) as conn:
        rows = Rows(conn)
        alice = People(conn).find("alice")
        assert alice is not None
        mine = rows.involving(alice.id)
        assert all(
            read.about(rows, s).deleted
            for s in mine
            if read.about(rows, s).owner == alice.id
        )
        assert not [s for s in mine if alice.id in read.about(rows, s).collaborators]
    assert run("wipe-data", "alice") == ["[wipe] alice: nothing to delete or unshare"]
    assert counts() == (threads, entries + gifts + shares)

    # Each later run writes an entry per gift and per share, and no thread.
    cost = gifts + shares
    for cycle in (1, 2):
        again = run(*argv)
        assert sum(line.endswith(": restored") for line in again) == gifts
        assert not [line for line in again if ": created" in line or "forked" in line]
        assert counts() == (threads, entries + 2 * cycle * cost)
        _ = run("wipe-data", "alice")
        assert counts() == (threads, entries + (2 * cycle + 1) * cost)

    with pytest.raises(SystemExit, match="'archive' holds what init-data loads"):
        main(["wipe-data", "archive"])
    with pytest.raises(SystemExit, match="no person with login 'nobody'"):
        main(["wipe-data", "nobody"])

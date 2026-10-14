from pathlib import Path

import pytest

from chatddx.catalog import Subject
from chatddx.cli import main
from chatddx.curation import init, repair
from chatddx.curation.test.cases import CASES, vignettes
from chatddx.factors.bundle import Registry
from chatddx.identity import Person
from chatddx.inventory.test.memory import MemorySource
from chatddx.store import Catalog, People
from chatddx.store.store import Connection, Store
from chatddx.test.world import DATA, copied, world_plan

pytestmark = pytest.mark.solidified


@pytest.mark.slow
@pytest.mark.parametrize("template", ["loaded"], indirect=True)
def test_repair_moves_the_archive_s_families_to_their_vignettes_new_places(
    conn: Connection, alice: Person
) -> None:
    archive = People(conn).find("archive")
    assert archive is not None
    catalog = Catalog(conn)
    families: dict[str, int] = {}
    for c in vignettes().cases():
        if (family := catalog.family(c.digest)) is not None:
            families[c.vignette.id] = family
    texts = vignettes().vignettes
    moved = MemorySource(
        name="test",
        vignettes={
            **{id: text for id, text in texts.items() if id != "noted"},
            "noted2": texts["noted"],
            "crlf": b"Edited at the source.",
        },
    )
    at = "at source 'test'"
    dry = repair(conn, moved, archive, dry=True)
    assert dry == [
        f"[repair case] crlf: changed {at}; family {families['crlf']} would move",
        f"[repair case] noted: renamed to noted2 {at}; family "
        + f"{families['noted']} would move",
    ]
    assert repair(conn, moved, archive, dry=True) == dry

    assert repair(conn, moved, archive) == [
        f"[repair case] crlf: changed {at}; family "
        + f"{families['crlf']} moved, with 1 case, 0 appendices and 0 threads",
        f"[repair case] noted: renamed to noted2 {at}; family "
        + f"{families['noted']} moved, with 1 case, 0 appendices and 1 thread",
    ]
    assert repair(conn, moved, archive) == [f"[repair] nothing to repair {at}"]

    # The data follows the rename, and init-data finds the archive whole again: a
    # changed case keeps its expectation behind, and a renamed one takes it along.
    renamed = {**CASES, "noted2": CASES["noted"]}
    del renamed["noted"]
    lines = init(conn, world_plan(), renamed, moved, alice)
    cases = [
        line
        for line in lines
        if line.startswith(("[archive case]", "[archive expectation]"))
    ]
    assert [line.split(": ")[1].split(" ")[0] for line in cases] == [
        verb
        for id, case in renamed.items()
        for verb in (
            "validated",
            "created" if id == "crlf" else "validated",
            *("validated" for o in case.ordered for _ in range(1 + bool(o.targets))),
        )
    ]
    assert not [line for line in lines if "not in the data" in line]
    assert catalog.about(Subject(family=families["noted"])).name == "noted2"


@pytest.mark.slow
@pytest.mark.parametrize("template", ["loaded"], indirect=True)
def test_repair_leaves_other_people_s_families_alone(
    conn: Connection, alice: Person
) -> None:
    archive = People(conn).find("archive")
    assert archive is not None
    mine = vignettes(Mine=b"Alice's own vignette.")
    [case] = [c for c in mine.cases() if c.vignette.id == "Mine"]
    registry = Registry()
    digest = registry.add(case)
    _ = Store(conn).add(registry, [digest])
    family = Catalog(conn).adopt(digest, alice.id)
    texts = dict(mine.vignettes)
    texts["Mine2"] = texts.pop("Mine")
    assert repair(conn, MemorySource(name="test", vignettes=texts), archive) == [
        f"[repair case] Mine: renamed to Mine2 at source 'test', but family {family} "
        + "isn't the archive's"
    ]


@pytest.mark.slow
def test_repair_data_command(
    db: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DB_NAME", db)
    world = copied(tmp_path)
    with pytest.raises(SystemExit, match="no 'archive' yet; init-data loads it"):
        main(["repair-data", "--world", str(world)])
    main(["init-data", "alice", "--world", str(world), "--data", str(DATA)])
    _ = capsys.readouterr()
    vignettes = world / "vignettes"
    _ = (vignettes / "noted.txt").rename(vignettes / "noted2.txt")

    main(["repair-data", "--world", str(world), "--dry-run"])
    [dry] = capsys.readouterr().out.splitlines()
    assert dry.startswith("[repair case] noted: renamed to noted2 at ")
    assert dry.endswith(" would move")
    monkeypatch.setenv("CHATDDX_WORLD", str(world))
    main(["repair-data"])
    [done] = capsys.readouterr().out.splitlines()
    assert done.endswith(" moved, with 1 case, 0 appendices and 1 thread")
    main(["repair-data"])
    assert capsys.readouterr().out == "[repair] nothing to repair at source 'test'\n"
    with pytest.raises(SystemExit, match="no source 'other'"):
        main(["repair-data", "--source", "other"])

    inventory = world / "inventory.toml"
    _ = inventory.write_text(
        inventory.read_text() + '[source.more]\npath = "vignettes"\n'
    )
    for argv, refusal in [
        ([], r"2 sources list their vignettes \(more, test\), so one must be named"),
        (["--source", "typed"], "source 'typed' is a database source"),
    ]:
        with pytest.raises(SystemExit, match=refusal):
            main(["repair-data", *argv])
    main(["repair-data", "--source", "test"])
    assert capsys.readouterr().out == "[repair] nothing to repair at source 'test'\n"

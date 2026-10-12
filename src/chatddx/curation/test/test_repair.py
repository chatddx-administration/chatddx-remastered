from pathlib import Path

import pytest

from chatddx.catalog import Subject
from chatddx.cli import main
from chatddx.conftest import sample_plan
from chatddx.curation import init, repair
from chatddx.curation.test.sample import SOME, vignettes
from chatddx.factors.bundle import Registry
from chatddx.inventory.test.memory import MemorySource
from chatddx.store import Catalog, People
from chatddx.store.store import Connection, Store

pytestmark = pytest.mark.solidified


@pytest.mark.slow
def test_repair_moves_the_archive_s_families_to_their_vignettes_new_places(
    conn: Connection,
) -> None:
    alice = People(conn).add("alice", "Alice")
    _ = init(conn, sample_plan(), SOME, vignettes(), alice)
    archive = People(conn).find("archive")
    assert archive is not None
    catalog = Catalog(conn)
    families: dict[str, int] = {}
    for c in vignettes().cases():
        if c.vignette.id in SOME and (family := catalog.family(c.digest)) is not None:
            families[c.vignette.id] = family
    texts = vignettes().vignettes
    moved = MemorySource(
        name="sample",
        vignettes={
            **{id: text for id, text in texts.items() if id != "Dutchfall11w"},
            "Dutchfall11W": texts["Dutchfall11w"],
            "DutchFall10w": b"Edited at the source.",
        },
    )
    at = "at source 'sample'"
    dry = repair(conn, moved, archive, dry=True)
    assert dry == [
        f"[repair case] DutchFall10w: changed {at}; family "
        + f"{families['DutchFall10w']} would move",
        f"[repair case] Dutchfall11w: renamed to Dutchfall11W {at}; family "
        + f"{families['Dutchfall11w']} would move",
    ]
    assert repair(conn, moved, archive, dry=True) == dry

    assert repair(conn, moved, archive) == [
        f"[repair case] DutchFall10w: changed {at}; family "
        + f"{families['DutchFall10w']} moved, with 1 case, 0 appendices and 0 threads",
        f"[repair case] Dutchfall11w: renamed to Dutchfall11W {at}; family "
        + f"{families['Dutchfall11w']} moved, with 1 case, 0 appendices and 1 thread",
    ]
    assert repair(conn, moved, archive) == [f"[repair] nothing to repair {at}"]

    # The data follows the rename, and init-data finds the archive whole again.
    renamed = {**SOME, "Dutchfall11W": SOME["Dutchfall11w"]}
    del renamed["Dutchfall11w"]
    lines = init(conn, sample_plan(), renamed, moved, alice)
    cases = [
        line
        for line in lines
        if line.startswith(("[archive case]", "[archive expectation]"))
    ]
    assert [line.split(": ")[1].split(" ")[0] for line in cases] == [
        "validated",
        "created",
        "validated",
        "validated",
        "validated",
        "validated",
    ]
    assert not [line for line in lines if "not in the data" in line]
    assert catalog.about(Subject(family=families["Dutchfall11w"])).name == (
        "Dutchfall11W"
    )


@pytest.mark.slow
def test_repair_leaves_other_people_s_families_alone(conn: Connection) -> None:
    alice = People(conn).add("alice", "Alice")
    _ = init(conn, sample_plan(), SOME, vignettes(), alice)
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
    assert repair(conn, MemorySource(name="sample", vignettes=texts), archive) == [
        f"[repair case] Mine: renamed to Mine2 at source 'sample', but family {family} "
        + "isn't the archive's"
    ]


@pytest.mark.slow
def test_repair_data_command(
    db: str,
    few: Path,
    world: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DB_NAME", db)
    with pytest.raises(SystemExit, match="no 'archive' yet; init-data loads it"):
        main(["repair-data", "--world", str(world)])
    main(["init-data", "alice", "--world", str(world), "--data", str(few)])
    _ = capsys.readouterr()
    vignettes = world / "vignettes"
    _ = (vignettes / "Dutchfall11w.txt").rename(vignettes / "Dutchfall11W.txt")

    main(["repair-data", "--world", str(world), "--dry-run"])
    [dry] = capsys.readouterr().out.splitlines()
    assert dry.startswith("[repair case] Dutchfall11w: renamed to Dutchfall11W at ")
    assert dry.endswith(" would move")
    monkeypatch.setenv("CHATDDX_WORLD", str(world))
    main(["repair-data"])
    [done] = capsys.readouterr().out.splitlines()
    assert done.endswith(" moved, with 1 case, 0 appendices and 1 thread")
    main(["repair-data"])
    assert capsys.readouterr().out == "[repair] nothing to repair at source 'sample'\n"
    with pytest.raises(SystemExit, match="no source 'other'"):
        main(["repair-data", "--source", "other"])

    inventory = world / "inventory.toml"
    _ = inventory.write_text(
        inventory.read_text()
        + '[source.more]\npath = "vignettes"\n[source.typed]\nkind = "database"\n'
    )
    for argv, refusal in [
        ([], r"2 sources list their vignettes \(more, sample\), so one must be named"),
        (["--source", "typed"], "source 'typed' is a database source"),
    ]:
        with pytest.raises(SystemExit, match=refusal):
            main(["repair-data", *argv])
    main(["repair-data", "--source", "sample"])
    assert capsys.readouterr().out == "[repair] nothing to repair at source 'sample'\n"

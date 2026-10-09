import shutil
from collections import Counter
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path

import pytest

from chatddx.catalog import Entry, EntryField, Subject
from chatddx.cli import main
from chatddx.conftest import WORLDS, connect, sample_plan
from chatddx.curation import init
from chatddx.curation.plan import SAMPLE
from chatddx.curation.test.sample import CASES, SOME, vignettes
from chatddx.factors.base import Fingerprint
from chatddx.inventory import Inventory
from chatddx.inventory.test.memory import MemorySource
from chatddx.store import Catalog, People
from chatddx.store.store import Connection

REVISION = "f" * 40
# The fake engines say what they are: no commit, no Nix closure.
FAKES = [
    *(
        f"[lint warning] model {name}: model.revision: revision 'fake' is not a "
        + "commit and can move"
        for name in ("qwen3-8b-awq@fake", "gpt-oss-20b@fake")
    ),
    *(
        f"[lint warning] engine.local {name}: engine.closure: closure 'chatddx "
        + "fake-vllm' is not a Nix store path"
        for name in ("qwen3-8b-awq@fake", "gpt-oss-20b@fake")
    ),
]
SAMPLE_WORLD = WORLDS / "sample"
KOMPISMOLN = WORLDS / "kompismoln"


# A copy of the sample with `old` replaced by `new` in one of its files.
def changed(tmp_path: Path, file: str, old: str, new: str) -> Path:
    data = tmp_path / "data"
    _ = shutil.copytree(SAMPLE, data)
    text = (data / file).read_text()
    assert old in text
    _ = (data / file).write_text(text.replace(old, new))
    return data


def tally(lines: list[str]) -> Counter[str]:
    def what(line: str) -> str:
        prefix = line[1 : line.index("]")].split(" ")[0]
        if prefix in ("skipped", "share", "lint"):
            return prefix
        return f"{prefix} {line.split(': ', 1)[1].split(' ')[0]}"

    return Counter(what(line) for line in lines)


# Its own patch, so it's undone last, after the database fixtures that read DB_NAME.
@pytest.fixture(autouse=True)
def revision() -> Iterator[None]:
    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("CHATDDX_REVISION", REVISION)
        yield


def test_init_data_loads_the_archive(conn: Connection) -> None:
    alice = People(conn).add("alice", "Alice")
    plan = sample_plan()
    lines = init(conn, plan, CASES, vignettes(), alice)
    threads = len(plan.records) + len(CASES)
    assert tally(lines) == Counter(
        {
            "archive created": threads + len(CASES),
            "skipped": 4,
            "share": 1,
            "lint": len(FAKES) + 1,
        }
    )
    shared = threads + len(CASES)
    assert (
        lines[-len(FAKES) - 2]
        == f"[share] {shared} of {shared} archive threads and families with alice"
    )
    components = len({r.digest for r in plan.records}) + 2 * len(CASES)
    assert lines[-len(FAKES) - 1 :] == [
        *FAKES,
        f"[lint] {len(FAKES)} findings in {components} components",
    ]

    catalog = Catalog(conn)
    archive = People(conn).find("archive")
    assert archive is not None
    [plan_thread] = catalog.find(
        "skeleton", "plan (en, Qwen/Qwen3-8B-AWQ)", owner=archive.id
    )
    [shown] = catalog.find("skeleton", "plan-shown (en, Qwen/Qwen3-8B-AWQ)")
    variation = catalog.variation(shown)
    assert variation is not None and set(variation.varies) == {"/recipe/output"}
    assert variation.base.thread == plan_thread
    about = catalog.about(Subject(thread=plan_thread))
    assert (about.owner, about.tags, alice.id in about.collaborators) == (
        archive.id,
        frozenset({"ddx"}),
        True,
    )
    [case] = [c for c in vignettes().cases() if c.vignette.id == "DutchFall10w"]
    family = catalog.family(case.digest)
    assert family is not None
    assert catalog.about(Subject(family=family)).language == "en"
    assert catalog.title_of(case.digest) == "DutchFall10w"
    scorer = plan.named("scorer", "plan")
    assert catalog.labels(scorer.digest) == {
        ("view", 0): "differential",
        ("view", 1): "warning",
        ("view", 2): "disposition",
        ("view", 3): "dont-miss",
    }
    [tool] = catalog.find("tool", "web_search", owner=archive.id)
    assert catalog.about(Subject(thread=tool)).description == (
        "Search the web for up-to-date information"
    )
    assert [line for line in lines if line.endswith(", in en")] == [
        f"[archive {r.kind}] {r.name}: created {r.digest.removeprefix('sha256:')[:6]}"
        + ", in en"
        for r in plan.records
        if r.language is not None
    ]
    assert catalog.language_of(plan.named("toolset", "web (en)").digest) == "en"
    assert catalog.language_of(plan.named("prompt", "case").digest) is None

    # The rest of the sample's cases, and their expectations, are left over.
    again = init(conn, sample_plan(), SOME, vignettes(), alice)
    assert {v for v in tally(again) if v.startswith("archive")} == {
        "archive validated",
        "archive not",
    }
    assert tally(again)["archive not"] == 2 * (len(CASES) - len(SOME))
    assert "[archive case] Dutchfall13w: not in the data" in again
    assert again[-len(FAKES) - 2].startswith("[share] 0 of ")
    assert not [line for line in again if line.endswith(", in en")]


def test_init_data_lints_what_it_lands(
    conn: Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CHATDDX_REVISION")
    alice = People(conn).add("alice", "Alice")
    plan = sample_plan()
    unlike = replace(SOME["Dutchfall11w"], targets={"warning": {"pattern": "shock"}})
    lines = init(conn, plan, {**SOME, "Dutchfall11w": unlike}, vignettes(), alice)
    components = len({r.digest for r in plan.records}) + 2 * len(SOME)
    assert [line for line in lines if line.startswith("[lint")] == [
        *FAKES,
        *(
            f"[lint warning] scorer {name}: scorer.revision: scorer code has no revision"
            for name in ("plan", "diagnoses", "free-text", "raw")
        ),
        "[lint warning] expectation Dutchfall11w: expectation.invalid: at the root: "
        + "'diagnosis' is a required property",
        f"[lint] {5 + len(FAKES)} findings in {components} components",
    ]


def test_init_data_updates_and_gives_forks(conn: Connection, tmp_path: Path) -> None:
    alice = People(conn).add("alice", "Alice")
    _ = init(conn, sample_plan(), SOME, vignettes(), alice)
    edited = changed(
        tmp_path,
        "texts-en.toml",
        'guidance = "Fill in the management plan for the case."',
        'guidance = "Fill in the whole management plan."',
    )
    lines = init(
        conn,
        sample_plan(edited),
        SOME,
        vignettes(DutchFall10w=b"Edited at the source."),
        alice,
        giftbag=True,
    )
    assert sorted(line for line in lines if "updated" in line) == [
        line
        for line in sorted(lines)
        if line.startswith(
            (
                "[archive chunk.output] management-plan (en):",
                "[archive skeleton] plan (en, ",
                "[archive skeleton] plan-web (en, ",
            )
        )
    ]
    assert len([line for line in lines if "updated" in line]) == 5
    assert any(
        line.startswith("[archive case] DutchFall10w: needs repair") for line in lines
    )
    forked = [line for line in lines if line.startswith("[giftbag")]
    assert forked and all(line.split(": ")[1].startswith("forked") for line in forked)
    assert not any(
        line.startswith(("[giftbag expectation_schema", "[giftbag scorer"))
        for line in forked
    )
    assert any(line.startswith("[giftbag tool] web_search: forked") for line in forked)

    catalog = Catalog(conn)
    archive = People(conn).find("archive")
    assert archive is not None
    output = "management-plan (en)"
    [archived] = catalog.find("chunk.output", output, owner=archive.id)
    assert len(catalog.find("chunk.output", output, owner=alice.id)) == 1
    owners = [catalog.about(Subject(thread=t)).owner for t in catalog.forks(archived)]
    assert owners.count(alice.id) == 1
    again = init(
        conn,
        sample_plan(edited),
        SOME,
        vignettes(DutchFall10w=b"Edited at the source."),
        alice,
        giftbag=True,
    )
    assert {line.split(": ")[1] for line in again if line.startswith("[giftbag")} == {
        "kept"
    }

    gone = MemorySource(name="sample", vignettes={})
    lines = init(
        conn, sample_plan(edited), {"Dutchfall11w": SOME["Dutchfall11w"]}, gone, alice
    )
    assert "[archive case] Dutchfall11w: missing at source 'sample'" in lines


def test_init_data_withdraws_only_the_tags_the_archive_gave(
    conn: Connection, tmp_path: Path
) -> None:
    alice = People(conn).add("alice", "Alice")
    _ = init(conn, sample_plan(), SOME, vignettes(), alice)
    catalog = Catalog(conn)
    [plan] = catalog.find("skeleton", "plan (en, Qwen/Qwen3-8B-AWQ)")
    family = catalog.family(vignettes().cases()[0].digest)
    assert family is not None
    for subject in (Subject(thread=plan), Subject(family=family)):
        catalog.note(subject, Entry(field=EntryField.TAG, value="alice's"), alice.id)

    edited = changed(
        tmp_path,
        "factors.toml",
        'tags = ["ddx"]\nprompt = "case"\noutput = "management-plan"\n',
        'prompt = "case"\noutput = "management-plan"\n',
    )
    retagged = {**SOME, "DutchFall10w": replace(SOME["DutchFall10w"], tags=("falls",))}
    _ = init(conn, sample_plan(edited), retagged, vignettes(), alice)
    assert catalog.about(Subject(thread=plan)).tags == {"alice's"}
    assert catalog.about(Subject(family=family)).tags == {"alice's", "falls"}


def test_init_data_says_how_a_vignette_moved_at_its_source(conn: Connection) -> None:
    alice = People(conn).add("alice", "Alice")
    _ = init(conn, sample_plan(), SOME, vignettes(), alice)
    catalog = Catalog(conn)
    families = {
        c.vignette.id: catalog.family(c.digest)
        for c in vignettes().cases()
        if c.vignette.id in SOME
    }
    texts = vignettes().vignettes
    moved = MemorySource(
        name="sample",
        vignettes={
            **{id: text for id, text in texts.items() if id != "Dutchfall11w"},
            "Dutchfall11W": texts["Dutchfall11w"],
            "DutchFall10w": b"Edited at the source.",
        },
    )
    at = "at source 'sample'; repair-data rebinds family"
    lines = init(conn, sample_plan(), SOME, moved, alice)
    assert [line for line in lines if "needs repair" in line] == [
        f"[archive case] DutchFall10w: needs repair: changed {at} "
        + str(families["DutchFall10w"]),
        f"[archive case] Dutchfall11w: needs repair: renamed to Dutchfall11W {at} "
        + str(families["Dutchfall11w"]),
    ]
    assert not [line for line in lines if "not in the data" in line]

    renamed = {**SOME, "Dutchfall11W": SOME["Dutchfall11w"]}
    del renamed["Dutchfall11w"]
    lines = init(conn, sample_plan(), renamed, moved, alice)
    assert (
        f"[archive case] Dutchfall11W: needs repair: renamed from Dutchfall11w {at} "
        + str(families["Dutchfall11w"])
    ) in lines
    assert not [line for line in lines if "not in the data" in line]


def test_init_data_command(
    db: str,
    few: Path,
    world: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DB_NAME", db)
    data = ["--data", str(few), "--factors", str(SAMPLE_WORLD / "factors.toml")]
    main(["init-data", "alice", "--world", str(world), "--giftbag", *data])
    out = capsys.readouterr().out.splitlines()
    assert out[0] == "[person] alice: added"
    assert out[1].startswith("[archive model] qwen3-8b-awq@fake: created")
    assert any(line.startswith("[archive chunk.prompt] case: created") for line in out)
    assert any(line.startswith("[giftbag skeleton] plan (") for line in out)
    with connect(db) as conn:
        assert conn.execute("SELECT count(*) FROM catalog.family").fetchone() == (
            len(SOME),
        )

    monkeypatch.setenv("CHATDDX_WORLD", str(world))
    main(["init-data", "alice", *data])
    out = capsys.readouterr().out.splitlines()
    assert not [line for line in out if line.startswith("[person]")]
    with connect(db) as conn:
        alice = People(conn).find("alice")
    assert alice is not None and (alice.name, alice.roles) == ("alice", frozenset())
    assert {
        line.split(": ")[1].split(" ")[0] for line in out if line.startswith("[archive")
    } == {"validated"}

    empty = tmp_path / "empty"
    (empty / "vignettes").mkdir(parents=True)
    _ = (empty / "inventory.toml").write_text('[source.sample]\npath = "vignettes"\n')
    for argv, refusal in [
        (["--world", str(tmp_path)], "is no World: it holds no inventory.toml"),
        (["--world", str(empty)], "none of the data's 3 cases is in source 'sample'"),
        (["--source", "other"], "no source 'other'"),
        (["--facts", str(SAMPLE / "factors.toml")], "facts have only 'model' tables"),
    ]:
        with pytest.raises(SystemExit, match=refusal):
            main(["init-data", "alice", *data, *argv])
    monkeypatch.delenv("CHATDDX_WORLD")
    with pytest.raises(SystemExit, match="give a World with --world DIR"):
        main(["init-data", "alice", *data])

    main(["init-data", "alice", "--world", str(SAMPLE_WORLD), "--data", str(few)])
    assert [
        line
        for line in capsys.readouterr().out.splitlines()
        if line.startswith("[world")
    ] == [f"[world] 0 findings in 2 endpoints of {SAMPLE_WORLD}"]

    main(["init-data", "alice", "--world", str(KOMPISMOLN), "--data", str(few)])
    real = Inventory.load(KOMPISMOLN / "inventory.toml")
    out = capsys.readouterr().out.splitlines()
    for name in real.endpoints:
        assert any(
            line.startswith(f"[archive engine.local] {name}: created") for line in out
        )
    assert [line for line in out if line.startswith("[world")] == [
        f"[world] 0 findings in 2 endpoints of {KOMPISMOLN}"
    ]
    # The sample World's fake engines aren't Kompismoln's.
    assert sorted(line for line in out if "@fake" in line) == [
        f"[archive {kind}] {name}@fake: not in the data"
        for kind in ("engine.local", "model")
        for name in ("gpt-oss-20b", "qwen3-8b-awq")
    ]


def test_a_world_brings_its_engines_and_their_models_facts(
    db: str,
    few: Path,
    world: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DB_NAME", db)
    _ = (world / "factors.toml").write_text(
        """
[remote_engine."gemma@api"]
base_url = "https://api.example/v1/"
model = "google/gemma-3-27b-it"
"""
    )
    _ = (world / "facts.toml").write_text(
        """
[model."google/gemma-3-27b-it"]
family = "gemma3"

[model."google/gemma-3-27b-it".reasoning]
default = "off"
off = {}

[model."google/gemma-3-27b-it".sampling.recommended]
off = { temperature = 1.0, top_k = 64, top_p = 0.95 }
"""
    )
    ghost = "sha256:" + "c" * 64
    with (world / "inventory.toml").open("a") as f:
        _ = f.write(f'\n[endpoint.ghost]\nengine = "{ghost}"\n')
    main(["init-data", "alice", "--world", str(world), "--data", str(few)])
    out = capsys.readouterr().out.splitlines()
    assert any(
        line.startswith("[archive engine.remote] gemma@api: created") for line in out
    )
    assert out[-2:] == [
        f"[world warning] ghost: endpoint.engine_unknown: {ghost} is not in the registry",
        f"[world] 1 finding in 1 endpoint of {world}",
    ]
    assert any(
        line.startswith(
            "[archive chunk.sampling] recommended (google/gemma-3-27b-it): created"
        )
        for line in out
    )
    assert any(
        line.startswith("[archive skeleton] plan (en, google/gemma-3-27b-it): created")
        for line in out
    )


def test_wipe_data_deletes_and_unshares_and_init_data_gives_it_back(
    db: str,
    few: Path,
    world: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("DB_NAME", db)

    def run(*argv: str) -> list[str]:
        main(list(argv))
        return capsys.readouterr().out.splitlines()

    def rows() -> tuple[int, int]:
        with connect(db) as conn:
            threads = conn.execute("SELECT count(*) FROM catalog.thread").fetchone()
            entries = conn.execute("SELECT count(*) FROM catalog.entry").fetchone()
        assert threads is not None and entries is not None
        return threads[0], entries[0]

    argv = ["init-data", "alice", "--world", str(world), "--giftbag"]
    argv += ["--data", str(few), "--factors", str(SAMPLE_WORLD / "factors.toml")]
    loaded = run(*argv)
    gifts = sum(line.startswith("[giftbag ") for line in loaded)
    shares = int(next(line for line in loaded if line.startswith("[share]")).split()[1])
    threads, entries = rows()
    _ = run(*argv)
    assert rows() == (threads, entries)

    wiped = run("wipe-data", "alice")
    assert sum(int(line.split("deleted ")[1].split(",")[0]) for line in wiped) == gifts
    assert sum(int(line.split("unshared ")[1]) for line in wiped) == shares
    assert rows() == (threads, entries + gifts + shares)
    with connect(db) as conn:
        catalog = Catalog(conn)
        alice = People(conn).find("alice")
        assert alice is not None
        mine = catalog.involving(alice.id)
        assert all(
            catalog.about(s).deleted for s in mine if catalog.about(s).owner == alice.id
        )
        assert not [s for s in mine if alice.id in catalog.about(s).collaborators]
    assert run("wipe-data", "alice") == ["[wipe] alice: nothing to delete or unshare"]
    assert rows() == (threads, entries + gifts + shares)

    # Each later run writes an entry per gift and per share, and no thread.
    cost = gifts + shares
    for cycle in (1, 2):
        again = run(*argv)
        assert sum(line.endswith(": restored") for line in again) == gifts
        assert not [line for line in again if ": created" in line or "forked" in line]
        assert rows() == (threads, entries + 2 * cycle * cost)
        _ = run("wipe-data", "alice")
        assert rows() == (threads, entries + (2 * cycle + 1) * cost)

    with pytest.raises(SystemExit, match="'archive' holds the sample data"):
        main(["wipe-data", "archive"])
    with pytest.raises(SystemExit, match="no person with login 'nobody'"):
        main(["wipe-data", "nobody"])


def test_the_sample_world_holds_the_vignettes_at_7893656() -> None:
    source = Inventory.load(SAMPLE_WORLD / "inventory.toml").source("sample")
    assert source.sensitive
    assert source.ids() == sorted(CASES)
    for id in source.ids():
        _ = source.fetch(id).decode()
    listing = "".join(
        f"{c.vignette.id} {c.vignette.fingerprint.hex}\n" for c in source.cases()
    )
    assert (
        Fingerprint.of(listing.encode()).hex
        == "ce41d6b218347d2b792c86160969f937c6926c8bff255b8644c7159402d7028c"
    )

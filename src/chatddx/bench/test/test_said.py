from collections.abc import Callable

import pytest

from chatddx.bench import Bench, NotFound
from chatddx.catalog import About, Subject
from chatddx.identity import Person
from chatddx.store.catalog import Rows
from chatddx.test.world import LINES

pytestmark = pytest.mark.wip


def _mine(bench: Bench) -> int:
    edit, _ = bench.thread("configuration", LINES)
    return edit.thread


def _entries(bench: Bench, thread: int) -> int:
    return len(Rows(bench.conn).entries([Subject(thread=thread)]))


def test_an_owner_says_what_a_thread_is_called_and_who_it_is_shared_with(
    bench: Bench, bob: Person
) -> None:
    mine = _mine(bench)
    said = bench.say(
        mine,
        name="terse",
        description="Short answers.",
        tags=["ddx", "short"],
        collaborators=["bob"],
    )
    assert (said.name, said.description) == ("terse", "Short answers.")
    assert (said.tags, said.collaborators) == ({"ddx", "short"}, {bob.id})
    assert said.shows(bob.id)

    written = _entries(bench, mine)
    again = bench.say(mine, name="terse", tags=["short", "ddx"], collaborators=["bob"])
    assert (again, _entries(bench, mine)) == (said, written)

    cleared = bench.say(mine, name=None, tags=[], collaborators=[])
    assert (cleared.name, cleared.tags, cleared.collaborators) == (None, set(), set())
    assert cleared.description == "Short answers."
    assert not cleared.shows(bob.id)
    assert _entries(bench, mine) == written + 4


def test_only_what_the_owner_may_say_is_said(bench: Bench) -> None:
    mine = _mine(bench)
    archives = bench.thread("configuration", f"archive/{LINES}")[0].thread
    written = _entries(bench, mine)
    refused: list[tuple[Callable[[], About], type[Exception], str]] = [
        (lambda: bench.say(mine, name=""), ValueError, "a name can't be empty"),
        (
            lambda: bench.say(mine, name="kept", tags=["ddx", ""]),
            ValueError,
            "a tag can't be empty",
        ),
        (
            lambda: bench.say(mine, name="kept", collaborators=["nobody"]),
            NotFound,
            "no person 'nobody'",
        ),
        (
            lambda: bench.say(mine, name="kept", collaborators=["alice"]),
            ValueError,
            f"configuration {mine} is yours",
        ),
    ]
    for said, error, message in refused:
        with pytest.raises(error, match=message):
            _ = said()
    assert _entries(bench, mine) == written

    with pytest.raises(NotFound, match=f"no configuration {archives} of yours"):
        _ = bench.say(archives, name="mine now")
    with pytest.raises(NotFound, match="no thread 999999 of yours"):
        _ = bench.say(999999, deleted=True)


def test_an_owner_deletes_and_restores_a_thread(bench: Bench) -> None:
    mine = _mine(bench)
    assert bench.say(mine, deleted=True).deleted
    assert mine not in [e.thread for e, _ in bench.threads("configuration")]
    assert [e.thread for e, _ in bench.deleted("skeleton")] == [mine]
    with pytest.raises(NotFound, match=f"no configuration {mine} for alice"):
        _ = bench.thread_by_id(mine, "configuration")
    _, about = bench.thread_by_id(mine, "configuration", deleted=True)
    assert about.deleted

    with pytest.raises(ValueError, match="is deleted: restore it to say more of it"):
        _ = bench.say(mine, name="gone")
    back = bench.say(mine, deleted=False, name="back")
    assert (back.deleted, back.name) == (False, "back")
    assert bench.deleted("skeleton") == []


def test_a_restore_is_held_to_one_expectation_per_case_and_schema(
    bench: Bench,
) -> None:
    catalog = bench.catalog
    case = bench.family("noted").case
    [schema] = bench.expectation_schemas(case)
    [mine] = catalog.expectation_choices([case], bench.person.id, schema)[case]
    [(archives, _)] = bench.shared(case, schema)
    _ = bench.say(mine, deleted=True)
    taken = bench.take_from(archives.thread)

    with pytest.raises(ValueError, match=f"in thread {taken}: delete that one"):
        _ = bench.say(mine, deleted=False)
    _ = bench.say(taken, deleted=True)
    assert not bench.say(mine, deleted=False).deleted

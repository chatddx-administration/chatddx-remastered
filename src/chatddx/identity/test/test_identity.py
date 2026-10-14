from dataclasses import dataclass

import pytest

from chatddx.identity import collaborates, owns, preferred, sees

pytestmark = pytest.mark.solidified


@dataclass(frozen=True)
class Said:
    owner: int | None = None
    collaborators: frozenset[int] = frozenset()
    deleted: bool = False


def test_a_person_sees_what_they_own_or_is_shared_with_them() -> None:
    assert sees(1, Said(owner=1))
    assert sees(1, Said(owner=2, collaborators=frozenset({1})))
    assert not sees(1, Said(owner=2, collaborators=frozenset({3})))
    assert not sees(1, Said())


def test_a_person_owns_only_what_names_them_its_owner() -> None:
    assert owns(1, Said(owner=1))
    assert not owns(1, Said(owner=2, collaborators=frozenset({1})))
    assert not owns(1, Said())


def test_a_person_collaborates_on_what_is_shared_with_them_but_not_their_own() -> None:
    assert collaborates(1, Said(owner=2, collaborators=frozenset({1})))
    assert collaborates(1, Said(collaborators=frozenset({1})))
    assert not collaborates(1, Said(owner=1, collaborators=frozenset({1})))
    assert not collaborates(1, Said(owner=1))


def test_nobody_sees_owns_or_collaborates_on_what_is_deleted() -> None:
    gone = Said(owner=1, collaborators=frozenset({2}), deleted=True)
    assert not sees(1, gone) and not owns(1, gone)
    assert not sees(2, gone) and not collaborates(2, gone)


def test_a_person_prefers_their_own_to_what_is_shared_with_them() -> None:
    assert preferred(1, [("a", 2), ("b", 1), ("c", 1)]) == ["b", "c"]
    assert preferred(1, [("a", 2), ("b", None)]) == ["a", "b"]
    assert preferred(1, []) == []

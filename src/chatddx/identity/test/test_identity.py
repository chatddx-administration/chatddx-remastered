import pytest

from chatddx.identity import preferred, sees

pytestmark = pytest.mark.wip


def test_a_person_sees_what_they_own_or_is_shared_with_them() -> None:
    assert sees(1, 1, ())
    assert sees(1, 2, {1})
    assert not sees(1, 2, {3})
    assert not sees(1, None, ())


def test_a_person_prefers_their_own_to_what_is_shared_with_them() -> None:
    assert preferred(1, [("a", 2), ("b", 1), ("c", 1)]) == ["b", "c"]
    assert preferred(1, [("a", 2), ("b", None)]) == ["a", "b"]
    assert preferred(1, []) == []

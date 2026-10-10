import pytest

from chatddx.identity import sees

pytestmark = pytest.mark.wip


def test_a_person_sees_what_they_own_or_is_shared_with_them() -> None:
    assert sees(1, 1, ())
    assert sees(1, 2, {1})
    assert not sees(1, 2, {3})
    assert not sees(1, None, ())

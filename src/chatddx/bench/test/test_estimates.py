import pytest

from chatddx.bench.breakdown import estimate, t975


def test_two_cases_make_an_interval_as_wide_as_student_s_t_says() -> None:
    held = estimate([0.2, 0.8])

    assert held is not None
    assert held.n == 2
    assert held.mean == pytest.approx(0.5)
    assert held.half == pytest.approx(12.706 * 0.4242640687 / 2**0.5)


def test_one_case_has_no_interval_and_none_no_estimate() -> None:
    assert estimate([]) is None
    held = estimate([0.4])
    assert held is not None and held.half is None


@pytest.mark.parametrize(
    ("df", "t"), [(1, 12.706), (30, 2.042), (31, 2.0395), (60, 2.0003), (120, 1.9799)]
)
def test_t_is_student_s_at_0_975(df: int, t: float) -> None:
    assert t975(df) == pytest.approx(t, abs=1e-3)

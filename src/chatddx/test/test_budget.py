import io

import pytest

from chatddx.test.budget import Budget


def test_the_budget_says_so_when_no_test_ran(pytestconfig: pytest.Config) -> None:
    out = io.StringIO()
    Budget().pytest_terminal_summary(pytest.TerminalReporter(pytestconfig, out))
    lines = out.getvalue().splitlines()
    assert "slow budget" in lines[-2]
    assert lines[-1] == "no test ran, so there is nothing to weigh"

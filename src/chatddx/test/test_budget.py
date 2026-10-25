import io
from types import SimpleNamespace
from typing import Literal, cast

import pytest

from chatddx.test.budget import Budget


def summary(budget: Budget, config: pytest.Config) -> list[str]:
    out = io.StringIO()
    budget.pytest_terminal_summary(pytest.TerminalReporter(config, out))
    return out.getvalue().splitlines()


def item(nodeid: str) -> pytest.Item:
    return cast(pytest.Item, cast(object, SimpleNamespace(nodeid=nodeid)))


def made(
    budget: Budget,
    nodeid: str,
    when: Literal["setup", "call", "teardown"],
    duration: float,
) -> pytest.TestReport:
    report = pytest.TestReport(
        nodeid, ("t.py", 0, nodeid), {}, "passed", None, when, duration=duration
    )
    wrapped = budget.pytest_runtest_makereport(item(nodeid))
    next(wrapped)
    with pytest.raises(StopIteration) as stopped:
        _ = wrapped.send(report)
    return cast(pytest.TestReport, stopped.value.value)


def test_the_budget_says_so_when_no_test_ran(pytestconfig: pytest.Config) -> None:
    lines = summary(Budget(), pytestconfig)
    assert "slow budget" in lines[-2]
    assert lines[-1] == "no test ran, so there is nothing to weigh"


def test_a_worker_s_tests_are_weighed_as_they_would_be_alone(
    pytestconfig: pytest.Config,
) -> None:
    worker, controller = Budget(), Budget()
    hook = pytestconfig.hook
    worker.pending.append(("budget: shared", ("copies", 2.4)))
    sent = [made(worker, "t.py::a", "setup", 2.5), made(worker, "t.py::a", "call", 1.0)]
    worker.pytest_runtest_teardown(item("t.py::b"), None)
    worker.pending.append(("budget: waited", ("db", 0.4)))
    sent += [
        made(worker, "t.py::b", "setup", 0.5),
        made(worker, "t.py::b", "call", 1.0),
        made(worker, "t.py::b", "teardown", 4.0),
    ]
    for report in sent:
        data = hook.pytest_report_to_serializable(config=pytestconfig, report=report)
        controller.pytest_runtest_logreport(
            hook.pytest_report_from_serializable(config=pytestconfig, data=data)
        )

    assert dict(controller.took) == pytest.approx({"t.py::a": 1.1, "t.py::b": 1.1})
    assert dict(controller.shared) == pytest.approx({"copies": 2.4})
    assert dict(controller.waited) == pytest.approx({"db": 0.4})


def test_only_a_test_far_off_the_cut_is_marked_or_unmarked(
    pytestconfig: pytest.Config,
) -> None:
    budget = Budget()
    steady = {f"t.py::steady_{n}": 1.0 for n in range(8)}
    budget.took.update(
        {"t.py::big": 6.0, "t.py::twice": 2.0, "t.py::half": 0.5, "t.py::tiny": 0.1}
        | steady
    )
    budget.slow.update({"t.py::half", "t.py::tiny"})

    lines = summary(budget, pytestconfig)
    assert "16.6 s in 12 tests; slow from 1.000 s on" in lines
    assert [line for line in lines if line.startswith(("mark", "unmark"))] == [
        "mark slow: t.py::big (6.000 s)",
        "unmark: t.py::tiny (0.100 s)",
    ]

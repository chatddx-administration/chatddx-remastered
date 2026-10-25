import time
from collections import defaultdict
from collections.abc import Generator
from typing import cast

import pytest

QUICK = 1 / 8
# Policy: a test's time varies from run to run, and more so beside other workers, so only
# one off from the cut by this factor is worth marking or unmarking.
MARGIN = 3.0
# Dependency: src/chatddx/conftest.py:db takes a copy made ahead on Copies' threads, so
# waiting for it weighs the copying, which falls behind beside other workers, not the test.
WAITED = frozenset({"db"})
_SHARED = "budget: shared"
_WAITED = "budget: waited"
_LAST = "budget: last"


class Budget:
    def __init__(self) -> None:
        self.took: defaultdict[str, float] = defaultdict(float)
        self.shared: defaultdict[str, float] = defaultdict(float)
        self.waited: defaultdict[str, float] = defaultdict(float)
        self.slow: set[str] = set()
        self.skipped: set[str] = set()
        self.pending: list[tuple[str, tuple[str, float]]] = []
        self.last: str = ""
        self.depth: int = 0

    # Policy: a fixture wider than a test is set up for every test after it, so the one
    # that happens to set it up isn't charged for it; nor is the last test for the
    # session's teardown.
    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(
        self, fixturedef: pytest.FixtureDef[object]
    ) -> Generator[None, object, object]:
        waited = fixturedef.argname in WAITED
        if fixturedef.scope == "function" and not waited:
            return (yield)
        began = time.perf_counter()
        self.depth += 1
        try:
            return (yield)
        finally:
            self.depth -= 1
            if self.depth == 0:
                spent = time.perf_counter() - began
                kind = _WAITED if waited else _SHARED
                self.pending.append((kind, (fixturedef.argname, spent)))

    def pytest_runtest_teardown(
        self, item: pytest.Item, nextitem: pytest.Item | None
    ) -> None:
        if nextitem is None:
            self.last = item.nodeid

    # Accommodating for pytest-xdist, whose workers run the tests and set up the fixtures
    # while the controller sums the reports: what the budget weighs rides on them.
    @pytest.hookimpl(wrapper=True)
    def pytest_runtest_makereport(
        self, item: pytest.Item
    ) -> Generator[None, pytest.TestReport, pytest.TestReport]:
        report = yield
        report.user_properties.extend(self.pending)
        self.pending = []
        if report.when == "teardown" and item.nodeid == self.last:
            report.user_properties.append((_LAST, True))
        return report

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        said = [(str(name), value) for name, value in report.user_properties]
        for name, value in said:
            if name in (_SHARED, _WAITED):
                argname, spent = cast(tuple[str, float], value)
                (self.shared if name == _SHARED else self.waited)[argname] += spent
                self.took[report.nodeid] -= spent
        if (_LAST, True) in said:
            return
        self.took[report.nodeid] += report.duration
        if "slow" in report.keywords:
            self.slow.add(report.nodeid)
        if report.skipped:
            self.skipped.add(report.nodeid)

    def pytest_terminal_summary(
        self, terminalreporter: pytest.TerminalReporter
    ) -> None:
        took = {
            nodeid: max(t, 0.0)
            for nodeid, t in self.took.items()
            if nodeid not in self.skipped
        }
        total = sum(took.values())
        if not total:
            terminalreporter.section("slow budget")
            terminalreporter.write_line("no test ran, so there is nothing to weigh")
            return
        left, cut = total, 0.0
        for t in sorted(took.values(), reverse=True):
            if left <= total * QUICK:
                break
            left -= t
            cut = t
        quick = sum(t for nodeid, t in took.items() if nodeid not in self.slow)
        mark = [n for n, t in took.items() if t >= cut * MARGIN and n not in self.slow]
        unmark = [n for n, t in took.items() if t < cut / MARGIN and n in self.slow]
        shared = ", ".join(f"{name} {t:.1f} s" for name, t in self.shared.items())
        say = terminalreporter.write_line
        terminalreporter.section("slow budget")
        say(f"{total:.1f} s in {len(took)} tests; slow from {cut:.3f} s on")
        say(f"the quick run takes {quick:.1f} s of it, {quick / total:.0%}")
        say(f"set up once for many tests: {shared}")
        if self.waited:
            waited = ", ".join(f"{name} {t:.1f} s" for name, t in self.waited.items())
            say(f"waited for, made ahead: {waited}")
        for nodeid in sorted(mark):
            say(f"mark slow: {nodeid} ({took[nodeid]:.3f} s)")
        for nodeid in sorted(unmark):
            say(f"unmark: {nodeid} ({took[nodeid]:.3f} s)")


def pytest_configure(config: pytest.Config) -> None:
    _ = config.pluginmanager.register(Budget(), "slow budget")

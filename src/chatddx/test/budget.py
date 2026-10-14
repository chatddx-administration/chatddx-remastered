import time
from collections import defaultdict
from collections.abc import Generator

import pytest

QUICK = 1 / 8
MARGIN = 1.5


class Budget:
    def __init__(self) -> None:
        self.took: defaultdict[str, float] = defaultdict(float)
        self.shared: defaultdict[str, float] = defaultdict(float)
        self.slow: set[str] = set()
        self.skipped: set[str] = set()
        self.running: str = ""
        self.last: str = ""
        self.depth: int = 0

    def pytest_runtest_logstart(self, nodeid: str) -> None:
        self.running = nodeid

    # A fixture wider than a test is set up for every test after it, so the one that
    # happens to set it up isn't charged for it; nor is the last test for the session's
    # teardown.
    @pytest.hookimpl(wrapper=True)
    def pytest_fixture_setup(
        self, fixturedef: pytest.FixtureDef[object]
    ) -> Generator[None, object, object]:
        if fixturedef.scope == "function":
            return (yield)
        began = time.perf_counter()
        self.depth += 1
        try:
            return (yield)
        finally:
            self.depth -= 1
            if self.depth == 0:
                spent = time.perf_counter() - began
                self.shared[fixturedef.argname] += spent
                self.took[self.running] -= spent

    def pytest_runtest_teardown(
        self, item: pytest.Item, nextitem: pytest.Item | None
    ) -> None:
        if nextitem is None:
            self.last = item.nodeid

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        if report.when == "teardown" and report.nodeid == self.last:
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
        for nodeid in sorted(mark):
            say(f"mark slow: {nodeid} ({took[nodeid]:.3f} s)")
        for nodeid in sorted(unmark):
            say(f"unmark: {nodeid} ({took[nodeid]:.3f} s)")


def pytest_configure(config: pytest.Config) -> None:
    _ = config.pluginmanager.register(Budget(), "slow budget")

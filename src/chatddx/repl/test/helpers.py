from collections.abc import Callable

from pydantic import JsonValue

from chatddx.bench import TriedVariation
from chatddx.curation import load_cases
from chatddx.repl.shell import Repl
from chatddx.test.world import DATA

CASES = load_cases(DATA)

type Say = Callable[..., str]


def tagged(*tags: str) -> list[str]:
    return sorted(id for id, case in CASES.items() if set(tags) & set(case.tags))


def targets_of(case: str) -> dict[str, JsonValue]:
    targets = CASES[case].targets
    assert isinstance(targets, dict)
    return targets


def pattern(case: str, target: str = "diagnosis") -> str:
    held = targets_of(case)[target]
    assert isinstance(held, dict)
    found = held["pattern"]
    assert isinstance(found, str)
    return found


def tried(repl: Repl) -> TriedVariation:
    assert repl.cell.variation is not None
    return repl.cell.variation


def line_of(written: str, start: str) -> str:
    return [line for line in written.splitlines() if line.strip().startswith(start)][-1]


def cells(written: str) -> list[list[str]]:
    return [line.split() for line in written.splitlines()]


def row(written: str, *start: str) -> str:
    [found] = [
        line
        for line in written.splitlines()
        if line.split()[: len(start)] == list(start)
    ]
    return found

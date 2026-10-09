import re
from pathlib import Path

import chatddx

SRC = Path(chatddx.__file__).parent
CELL = re.compile(r"(?<!ex)cell", re.IGNORECASE)


# "Cell" is the repl's word for what it runs. The bench and everything under it speak
# of the variation being tried and the endpoint (agents/wip-bench.md, K2). Only code is
# held to it: the cases' data say "basal cell carcinoma".
def test_only_the_repl_speaks_of_a_cell() -> None:
    found = [
        f"{path.relative_to(SRC)}:{n}"
        for path in sorted(SRC.rglob("*"))
        if path.suffix in (".py", ".sql") and not path.is_relative_to(SRC / "repl")
        for n, line in enumerate(path.read_text().splitlines(), 1)
        if CELL.search(line)
    ]
    assert found == []

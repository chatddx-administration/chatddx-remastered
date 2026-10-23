from pathlib import Path
from textwrap import dedent


def catalog(root: Path, po: str) -> Path:
    _ = (root / "sv.po").write_text(dedent(po))
    return root

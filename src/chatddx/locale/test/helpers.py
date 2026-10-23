from pathlib import Path
from textwrap import dedent


def catalog(root: Path, said: str) -> Path:
    _ = (root / "sv.po").write_text(dedent(said))
    return root

from collections.abc import Callable

from chatddx.bench import TriedVariation
from chatddx.repl.shell import Repl

FREE_TEXT = "free-text (Qwen/Qwen3-8B-AWQ)"
PLAN = "plan (Qwen/Qwen3-8B-AWQ)"
QWEN = "qwen3-8b-awq@fake"
GPT_OSS = "gpt-oss-20b@fake"

type Say = Callable[..., str]


def tried(repl: Repl) -> TriedVariation:
    assert repl.cell.variation is not None
    return repl.cell.variation

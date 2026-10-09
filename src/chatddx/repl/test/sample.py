from collections.abc import Callable

from chatddx.conftest import WORLDS

WORLD = WORLDS / "sample" / "inventory.toml"
FREE_TEXT = "free-text (Qwen/Qwen3-8B-AWQ)"
PLAN = "plan (Qwen/Qwen3-8B-AWQ)"
QWEN = "qwen3-8b-awq@fake"
GPT_OSS = "gpt-oss-20b@fake"

type Say = Callable[..., str]

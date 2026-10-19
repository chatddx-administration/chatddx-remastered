from typing import Any

from chatddx.api import threads as api, world as api_world
from chatddx.bench import Bench
from chatddx.factors.base import resolve
from chatddx.factors.request import Compilation, Skeleton

from .pages import own_first


def judge_choices(bench: Bench) -> dict[str, list[dict[str, Any]]]:
    configurations = own_first(
        bench, api.threads(bench, "configuration", purpose="judge")
    )
    return {
        "judging": [
            {
                "digest": t.head.digest,
                "thread": t.id,
                "name": t.name or t.title,
                "owner": t.owner,
                "output_schema": resolve(
                    bench.store.get, t.head.digest, Skeleton
                ).output_schema,
                "weights": None
                if t.head.compilation is None
                else resolve(
                    bench.store.get, t.head.compilation, Compilation
                ).recipe.model,
            }
            for t in configurations
        ],
        "models": [
            {"name": m.name, "weights": m.weights}
            for m in api_world.models(bench)
            if m.engine is not None
        ],
    }

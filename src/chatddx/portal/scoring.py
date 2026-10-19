import json
from collections.abc import Iterable
from typing import Any

from chatddx.api import schemas, threads as api, world as api_world
from chatddx.bench import Bench
from chatddx.catalog import threads as catalog_threads
from chatddx.factors.base import resolve
from chatddx.factors.request import Compilation, Skeleton
from chatddx.factors.scoring import Judge

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


def blank(code: schemas.ScorerCode, schema: str) -> dict[str, Any]:
    unjudged = [m.name for m in code.metrics if not m.judged]
    return {
        "kind": "scorer",
        "entry_point": code.entry_point,
        "version": code.version,
        "expectation_schema": schema,
        "views": [{"metric": unjudged[0] if unjudged else code.metrics[0].name}],
    }


def scorer_choices(
    bench: Bench, code: schemas.ScorerCode, judged: Iterable[str] = ()
) -> dict[str, Any]:
    judges = _judges(bench)
    titles = {j: bench.title(j) for j in judged}
    return {
        "metrics": [m.model_dump(mode="json") for m in code.metrics],
        "outputs": _outputs(bench),
        "judges": judges,
        "titles": titles | {j["digest"]: j["name"] for j in judges},
        "me": bench.person.login,
        **judge_choices(bench),
    }


def _judges(bench: Bench) -> list[dict[str, Any]]:
    login = bench.person.login
    found: list[dict[str, Any]] = []
    for t in sorted(
        api.threads(bench, "judge"), key=lambda t: (t.owner != login, t.name or t.title)
    ):
        judge = resolve(bench.store.get, t.head.digest, Judge)
        try:
            handle = bench.handle(judge.model).name
        except ValueError:
            handle = None
        found.append(
            {
                "digest": t.head.digest,
                "thread": t.id,
                "head": t.head.id,
                "body": judge.model_dump(mode="json"),
                "texts": _texts(bench, judge),
                "name": t.name or t.title,
                "owner": t.owner,
                "configuration": bench.title(judge.skeleton),
                "model": handle,
                "seeds": list(judge.seeds),
                "output_schema": resolve(
                    bench.store.get, judge.skeleton, Skeleton
                ).output_schema,
            }
        )
    return found


def _texts(bench: Bench, judge: Judge) -> dict[str, Any] | None:
    held = bench.holder(judge.skeleton)
    recipe = None if held is None else catalog_threads.recipe(bench.rows, held[0])
    if recipe is None:
        made = bench.store.compilations(judge.skeleton)
        recipe = made[0].recipe if made else None
    if recipe is None:
        return None
    return {
        "configuration": None
        if held is None
        else {
            "thread": held[0].thread,
            "head": held[0].id,
            "mine": held[1].owner == bench.person.id,
            "name": held[1].name or bench.title(held[0].digest),
        },
        "recipe": recipe.model_dump(mode="json"),
        "parts": {
            part: None if digest is None else _chunk(bench, digest)
            for part in ("instructions", "prompt", "output")
            for digest in [getattr(recipe, part)]
        },
    }


def _chunk(bench: Bench, digest: str) -> dict[str, Any]:
    held = bench.holder(digest)
    given: dict[str, Any] = {
        "digest": digest,
        "body": bench.store.get(digest).model_dump(mode="json"),
        "name": bench.title(digest),
    }
    if held is None:
        return {**given, "thread": None}
    edit, about = held
    return {
        **given,
        "thread": edit.thread,
        "head": edit.id,
        "mine": about.owner == bench.person.id,
        "name": about.name or given["name"],
        "language": api.thread(bench, edit.thread).language,
    }


def _outputs(bench: Bench) -> list[dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for t in api.threads(bench, "configuration", purpose="generation"):
        schema = resolve(bench.store.get, t.head.digest, Skeleton).output_schema
        held = found.setdefault(
            json.dumps(schema, sort_keys=True),
            {
                "title": schema.get("title") if isinstance(schema, dict) else None,
                "json_schema": schema,
                "by": [],
            },
        )
        held["by"].append(t.name or t.title)
    return list(found.values())

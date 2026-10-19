from pathlib import Path

import pytest

from chatddx.factors.base import resolve
from chatddx.factors.lint import lint
from chatddx.factors.request import Compilation, Skeleton
from chatddx.factors.scoring import Judge
from chatddx.test.world import (
    GPT_OSS,
    GPT_OSS_ARTIFACT,
    GPT_OSS_MODEL,
    JUDGE,
    QWEN,
    QWEN_ARTIFACT,
    REMOTE,
    UNKNOWN_MODEL,
    copied,
    edit,
    world_plan,
)

SCORER = """
[scorer.noted]
entry_point = "chatddx.scorers.metrics:score"
expectation_schema = "targets"
views = [{ expectation = "/notes", metric = "verdict", judge = "verdict" }]
"""


def edited(tmp_path: Path, old: str, new: str) -> Path:
    world = copied(tmp_path)
    edit(world / "_data" / "factors.toml", old, new)
    return world


def test_a_judge_s_recipe_is_compiled_for_its_handle_s_weights() -> None:
    plan = world_plan()

    def judge(name: str) -> Judge:
        return resolve(plan.registry.get, plan.named("judge", name).digest, Judge)

    graded, verdict, remote = judge("graded"), judge("verdict"), judge("remote")
    skeleton = plan.named("recipe", "judge-graded").digest
    assert (graded.skeleton, graded.model, graded.seeds) == (
        skeleton,
        plan.named("local_model", QWEN_ARTIFACT).digest,
        (1, 2, 3),
    )
    assert verdict.skeleton == remote.skeleton == plan.named("recipe", JUDGE).digest
    assert remote.model == plan.named("remote_model", UNKNOWN_MODEL).digest
    assert plan.engines == {
        graded.digest: plan.named("local_engine", QWEN).digest,
        verdict.digest: plan.named("local_engine", QWEN).digest,
        remote.digest: plan.named("remote_engine", REMOTE).digest,
    }


def test_a_judge_takes_its_weights_from_the_handle_the_world_binds_it_to(
    tmp_path: Path,
) -> None:
    world = copied(tmp_path)
    edit(
        world / "inventory.toml",
        f'graded = "{QWEN_ARTIFACT}"',
        f'graded = "{GPT_OSS_ARTIFACT}"',
    )
    plan = world_plan(world, world / "_data")
    get = plan.registry.get
    graded = resolve(get, plan.named("judge", "graded").digest, Judge)
    assert graded.model == plan.named("local_model", GPT_OSS_ARTIFACT).digest
    assert plan.engines[graded.digest] == plan.named("local_engine", GPT_OSS).digest
    assert graded.skeleton != plan.named("recipe", "judge-graded").digest
    [made] = [
        compilation
        for c in plan.compilations
        if (compilation := resolve(get, c, Compilation)).skeleton == graded.skeleton
    ]
    assert made.recipe.model == plan.named("local_model", GPT_OSS_ARTIFACT).digest
    assert made.facts == plan.named("facts", GPT_OSS_MODEL).digest
    assert resolve(get, graded.skeleton, Skeleton).body["temperature"] == 1.0


def test_a_judge_the_world_doesn_t_bind_is_skipped_and_so_is_its_scorer(
    tmp_path: Path,
) -> None:
    world = edited(
        tmp_path,
        "[expectation_schema.targets]",
        SCORER + "\n[expectation_schema.targets]",
    )
    edit(
        world / "inventory.toml",
        f'verdict = "{QWEN_ARTIFACT}"\n',
        f'nobody = "{QWEN_ARTIFACT}"\n',
    )
    plan = world_plan(world, world / "_data")
    assert "judge verdict: the World binds it to no handle" in plan.skipped
    assert "scorer noted: judge verdict isn't planned" in plan.skipped
    assert (
        f"judge nobody: the World binds it to {QWEN_ARTIFACT}, but the data has none"
        in plan.skipped
    )
    with pytest.raises(LookupError):
        _ = plan.named("judge", "verdict")


@pytest.mark.parametrize("field", ["engine", "model"])
def test_a_judge_names_no_model_or_engine_of_its_own(
    tmp_path: Path, field: str
) -> None:
    world = edited(
        tmp_path, "[judge.verdict]\n", f'[judge.verdict]\n{field} = "{QWEN}"\n'
    )
    with pytest.raises(ValueError, match="judge.verdict: a judge's model is the World"):
        _ = world_plan(world, world / "_data")


def test_a_judge_names_no_language_of_its_own(tmp_path: Path) -> None:
    world = edited(tmp_path, "[judge.verdict]\n", '[judge.verdict]\nlanguage = "sv"\n')
    with pytest.raises(
        ValueError, match="judge.verdict: a judge's request is its recipe's, as written"
    ):
        _ = world_plan(world, world / "_data")


def test_a_view_naming_no_judge_is_refused(tmp_path: Path) -> None:
    world = edited(
        tmp_path,
        "[expectation_schema.targets]",
        SCORER.replace('judge = "verdict"', 'judge = "nobody"')
        + "\n[expectation_schema.targets]",
    )
    with pytest.raises(ValueError, match="scorer.noted: no judge named 'nobody'"):
        _ = world_plan(world, world / "_data")


def test_a_judge_s_skeleton_with_tools_is_refused(tmp_path: Path) -> None:
    world = edited(
        tmp_path,
        'output = "verdict"\nsampling = "greedy"\n',
        'output = "verdict"\nsampling = "greedy"\ntoolset = "lookup"\n',
    )
    with pytest.raises(
        ValueError, match="judge.verdict: .* tools, which a judge can't"
    ):
        _ = world_plan(world, world / "_data")


def test_a_greedy_judge_with_several_seeds_is_linted() -> None:
    plan = world_plan()
    verdict = resolve(plan.registry.get, plan.named("judge", "verdict").digest, Judge)
    twice = plan.registry.add(verdict.model_copy(update={"seeds": (1, 2)}))
    assert [(f.code, f.message) for f in lint(plan.registry, [twice])] == [
        (
            "judge.greedy_seeds",
            "the judge is greedy, so its 2 seeds send the same request",
        )
    ]
    assert lint(plan.registry, [plan.named("judge", "verdict").digest]) == []

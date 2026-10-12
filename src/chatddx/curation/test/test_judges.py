from pathlib import Path

import pytest

from chatddx.factors.base import resolve
from chatddx.factors.lint import lint
from chatddx.factors.scoring import Judge
from chatddx.test.world import QWEN, QWEN_MODEL, REMOTE, copied, edit, world_plan

pytestmark = pytest.mark.solidified

SCORER = """
[scorer.judged]
entry_point = "chatddx.scorers.metrics:score"
expectation_schema = "targets"
views = [{ expectation = "/notes", metric = "verdict", judge = "verdict" }]
"""


def edited(tmp_path: Path, old: str, new: str) -> Path:
    world = copied(tmp_path)
    edit(world / "_data" / "factors.toml", old, new)
    return world


def test_a_judge_takes_its_recipe_s_variant_for_its_engine_s_model() -> None:
    plan = world_plan()

    def judge(name: str) -> Judge:
        return resolve(plan.registry.get, plan.named("judge", name).digest, Judge)

    graded, verdict, remote = judge("graded"), judge("verdict"), judge("remote")
    skeleton = plan.named("recipe", f"judge-graded (en, {QWEN_MODEL})").digest
    assert (graded.skeleton, graded.engine, graded.seeds) == (
        skeleton,
        plan.named("local_engine", QWEN).digest,
        (1, 2, 3),
    )
    assert (
        verdict.skeleton == remote.skeleton == plan.named("recipe", "judge (en)").digest
    )
    assert remote.engine == plan.named("remote_engine", REMOTE).digest


def test_a_judge_on_an_engine_the_world_lacks_is_skipped_and_so_is_its_scorer(
    tmp_path: Path,
) -> None:
    world = edited(
        tmp_path,
        'engine = "qwen3@fake"\nseeds = [1]\n',
        'engine = "nowhere@fake"\nseeds = [1]\n',
    )
    edit(
        world / "_data" / "factors.toml",
        "[expectation_schema.targets]",
        SCORER + "\n[expectation_schema.targets]",
    )
    plan = world_plan(world, world / "_data")
    assert "judge verdict: the World has no engine nowhere@fake" in plan.skipped
    assert "scorer judged: judge verdict isn't planned" in plan.skipped
    with pytest.raises(LookupError):
        _ = plan.named("judge", "verdict")


def test_a_view_naming_no_judge_is_refused(tmp_path: Path) -> None:
    world = edited(
        tmp_path,
        "[expectation_schema.targets]",
        SCORER.replace('judge = "verdict"', 'judge = "nobody"')
        + "\n[expectation_schema.targets]",
    )
    with pytest.raises(ValueError, match="scorer.judged: no judge named 'nobody'"):
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
        ("judge.greedy_seeds", "the judge is greedy, so its 2 seeds send one request")
    ]
    assert lint(plan.registry, [plan.named("judge", "verdict").digest]) == []

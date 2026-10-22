from pathlib import Path

import pytest
from pydantic import JsonValue, ValidationError

from chatddx.factors.bundle import Registry
from chatddx.factors.engine import FileDigest, LocalEngine, LocalModel
from chatddx.factors.lint import lint
from chatddx.factors.request import (
    Message,
    NativeOutput,
    OutputContract,
    Sampling,
    Skeleton,
    Slot,
    TextOutput,
)
from chatddx.factors.test.sample import SHA, local_engine, remote_engine, world
from chatddx.factors.trial import Trial
from chatddx.facts import (
    BUNDLED,
    Facts,
    Landing,
    Level,
    ModelFacts,
    OutputFacts,
    ReasoningFacts,
    Refusal,
    Refused,
    SamplingValues,
    Writes,
    check_pairs,
    lints,
)
from chatddx.test.world import GPT_OSS_MODEL, QWEN_MODEL


@pytest.fixture
def facts() -> Facts:
    return Facts.load(BUNDLED)


def test_reasoning_levels_land_where_the_facts_say(facts: Facts) -> None:
    qwen, gpt_oss = facts.models[QWEN_MODEL], facts.models[GPT_OSS_MODEL]
    thinking = Writes(chat_template_kwargs={"enable_thinking": True})
    assert qwen.reasoning.landing("default") == Landing(level="on", writes=thinking)
    assert qwen.reasoning.landing("xhigh") == Landing(level="on", writes=thinking)
    assert qwen.reasoning.landing("off").writes == Writes(
        chat_template_kwargs={"enable_thinking": False}
    )
    qwen.check_budget()
    assert gpt_oss.reasoning.landing("default") == Landing(
        level="medium", writes=Writes(effort="medium")
    )
    assert gpt_oss.reasoning.landing("on").level == "medium"
    nearest: list[tuple[Level, Level]] = [
        ("off", "low"),
        ("minimal", "low"),
        ("xhigh", "high"),
    ]
    for asked, landed in nearest:
        landing = gpt_oss.reasoning.landing(asked)
        assert (landing.level, landing.writes.effort) == (landed, landed)
        assert len(landing.nearest) == 1
    assert "always reasons" in gpt_oss.reasoning.landing("off").nearest[0]
    with pytest.raises(Refused, match="no thinking budget"):
        gpt_oss.check_budget()
    unknown = ModelFacts(model="m")
    with pytest.raises(Refused, match="nothing is known"):
        _ = unknown.reasoning.landing("high")
    assert qwen.reasons_by_default() is True
    assert unknown.reasons_by_default() is None


def test_a_refusal_lands_on_its_nearest_only_when_it_names_one() -> None:
    def off(refusal: Refusal) -> ReasoningFacts:
        return ReasoningFacts(off=refusal, low=Writes(effort="low"))

    refused = off(Refusal(refused="always reasons"))
    with pytest.raises(Refused, match="always reasons"):
        _ = refused.landing("off")
    nearest = off(Refusal(refused="always reasons", nearest="low"))
    assert nearest.landing("off") == Landing(
        level="low", writes=Writes(effort="low"), nearest=("always reasons",)
    )


def test_recommended_sampling_is_per_reasoning_level(facts: Facts) -> None:
    qwen = facts.models[QWEN_MODEL]
    assert qwen.recommended("off") == SamplingValues(
        temperature=0.7, top_p=0.8, top_k=20, presence_penalty=1.5
    )
    unrecommended = ModelFacts(
        model="m", reasoning=ReasoningFacts(default="on", on=Writes())
    )
    with pytest.raises(Refused, match="no sampling is recommended for reasoning 'on'"):
        _ = unrecommended.recommended("on")


def test_facts_are_checked(tmp_path: Path) -> None:
    def load(text: str) -> Facts:
        path = tmp_path / "facts.toml"
        _ = path.write_text(text)
        return Facts.load(path)

    with pytest.raises(ValidationError, match="go round"):
        _ = load('[model.m.reasoning]\nlow = "high"\nhigh = "low"\n')
    with pytest.raises(ValidationError, match="ends in no fact"):
        _ = load('[model.m.reasoning]\nlow = "high"\n')
    with pytest.raises(ValidationError, match="go round"):
        _ = load('[model.m.reasoning]\noff = { refused = "no", nearest = "off" }\n')
    with pytest.raises(ValidationError, match="ends in no fact"):
        _ = load('[model.m.reasoning]\noff = { refused = "no", nearest = "low" }\n')
    with pytest.raises(ValidationError, match="Extra inputs"):
        _ = load('[model.m.reasoning]\nlow = { reasoning_effort = "low" }\n')
    with pytest.raises(ValueError, match="only 'model' tables"):
        _ = load("[llm.m]\n")
    other = tmp_path / "other.toml"
    _ = other.write_text(f'[model."{QWEN_MODEL}"]\ncontext_length = 8192\n')
    assert Facts.load(BUNDLED, other).models[QWEN_MODEL].context_length == 8192
    again = tmp_path / "again.toml"
    _ = again.write_text(f'[model."{QWEN_MODEL}"]\n')
    with pytest.raises(ValueError, match="more than one file"):
        _ = Facts.load(BUNDLED, other, again)


def test_facts_check_pairs(facts: Facts) -> None:
    reg = Registry()
    ids = world(reg)
    template = local_engine(reg)

    def engine(repo: str, *argv: str) -> str:
        model = reg.add(
            LocalModel(
                repo=repo,
                revision="0" * 40,
                files=(FileDigest(path="model.safetensors", sha256=SHA),),
            )
        )
        return reg.add(
            LocalEngine.model_validate(
                {**template.model_dump(), "model": model, "argv": argv}
            )
        )

    user = Message(role="user", content=(Slot(slot="vignette"),))
    response_format: dict[str, JsonValue] = {
        "type": "json_schema",
        "json_schema": {"name": "output", "schema": {"type": "object"}},
    }

    def skeleton(contract: OutputContract, **body: JsonValue) -> str:
        return reg.add(Skeleton(messages=(user,), body=body, contract=contract))

    def findings(skeleton: str, engine: str) -> dict[str, str]:
        trial = reg.add(
            Trial(skeleton=skeleton, engine=engine, cases=(ids["case"],), seeds=(1,))
        )
        return {f.code: f.level for f in lints(reg, facts, [trial])}

    native = skeleton(NativeOutput(), response_format=response_format)
    qwen = engine(QWEN_MODEL)
    assert findings(native, qwen) == {"vllm.grammar_before_reasoning": "warning"}
    defaults_changed = engine(
        QWEN_MODEL, "--default-chat-template-kwargs", '{"enable_thinking": false}'
    )
    assert findings(native, defaults_changed) == {
        "vllm.grammar_before_reasoning": "info"
    }
    trial = reg.add(
        Trial(skeleton=native, engine=qwen, cases=(ids["case"],), seeds=(1,))
    )
    assert {f.level for f in lint(reg, [trial])} == {"info"}

    effort = skeleton(TextOutput(), reasoning_effort="low")
    assert findings(effort, qwen) == {"facts.reasoning_unmatched": "warning"}
    gpt_oss = engine(GPT_OSS_MODEL, "--reasoning-parser", "openai_gptoss")
    assert findings(effort, gpt_oss) == {}
    assert findings(skeleton(TextOutput(), reasoning_effort="none"), gpt_oss) == {
        "facts.reasoning_unmatched": "warning"
    }
    assert findings(
        skeleton(TextOutput(), reasoning_effort="high", thinking_token_budget=512),
        gpt_oss,
    ) == {"facts.budget_refused": "warning"}
    assert findings(native, gpt_oss) == {"facts.output_note": "info"}

    refusing = Facts(
        models={
            QWEN_MODEL: ModelFacts(
                model=QWEN_MODEL,
                output=OutputFacts(native=Refusal(refused="no grammar")),
            )
        }
    )
    trial = reg.add(
        Trial(skeleton=native, engine=qwen, cases=(ids["case"],), seeds=(1,))
    )
    assert [(f.code, f.message) for f in check_pairs(reg, refusing, [trial])] == [
        ("facts.output_refused", "no grammar")
    ]

    unknown = engine("someone/unknown")
    assert findings(skeleton(TextOutput()), unknown) == {"facts.missing": "info"}
    remote = reg.add(remote_engine(reg, GPT_OSS_MODEL))
    assert findings(effort, remote) == {}


def test_facts_check_that_a_pair_s_sampling_is_for_its_model(facts: Facts) -> None:
    reg = Registry()
    ids = world(reg)
    user = Message(role="user", content=(Slot(slot="vignette"),))

    def findings(engine_model: str, **body: JsonValue) -> dict[str, str]:
        engine = reg.add(remote_engine(reg, engine_model))
        skeleton = reg.add(Skeleton(messages=(user,), body=body, contract=TextOutput()))
        trial = reg.add(
            Trial(skeleton=skeleton, engine=engine, cases=(ids["case"],), seeds=(1,))
        )
        return {f.code: f.message for f in check_pairs(reg, facts, [trial])}

    def recommended(model: str, level: Level) -> dict[str, JsonValue]:
        return Sampling().over(facts.models[model].recommended(level)).body()

    qwen_on, qwen_off = recommended(QWEN_MODEL, "on"), recommended(QWEN_MODEL, "off")
    gpt_oss = recommended(GPT_OSS_MODEL, "medium")
    assert findings(QWEN_MODEL, **qwen_on) == findings(QWEN_MODEL, **qwen_off) == {}
    assert findings(GPT_OSS_MODEL, **gpt_oss) == findings(GPT_OSS_MODEL) == {}
    assert findings(GPT_OSS_MODEL, **qwen_on) == {
        "facts.sampling_unmatched": "the configuration's sampling is what the facts "
        + f"recommend for {QWEN_MODEL}, not for {GPT_OSS_MODEL}"
    }
    assert set(findings(QWEN_MODEL, **gpt_oss)) == {"facts.sampling_unmatched"}
    assert set(findings("google/gemma-3-27b-it", **qwen_on)) == {
        "facts.missing",
        "facts.sampling_unmatched",
    }
    greedy = Sampling(temperature=0).body()
    assert findings(GPT_OSS_MODEL, **greedy) == {}
    assert findings(GPT_OSS_MODEL, **{**qwen_on, "temperature": 0.5}) == {}
    assert findings(GPT_OSS_MODEL, **qwen_on, reasoning_effort="low") == {
        "facts.sampling_unmatched": "the configuration's sampling is what the facts "
        + f"recommend for {QWEN_MODEL}, not for {GPT_OSS_MODEL}"
    }

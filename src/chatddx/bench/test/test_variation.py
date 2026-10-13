from datetime import UTC, datetime

import pytest

from chatddx.bench import TriedVariation
from chatddx.catalog import Edit
from chatddx.factors.request import Recipe

pytestmark = pytest.mark.solidified


def digest(c: str) -> str:
    return "sha256:" + c * 64


RECIPE = Recipe(prompt=digest("1"), output=digest("2"), sampling=digest("3"))
HEAD = Edit(
    id=1,
    thread=1,
    digest=digest("9"),
    compilation=None,
    based_on=None,
    by=1,
    at=datetime(2026, 1, 1, tzinfo=UTC),
)


def test_a_variation_replaces_parts_over_its_configuration() -> None:
    plan = TriedVariation(HEAD, "plan", RECIPE)
    tried = plan.set("reasoning", digest("4"), "off").set(
        "prompt", digest("5"), "terse"
    )

    assert tried.label == "plan+prompt=terse+reasoning=off"
    assert (tried.held("reasoning"), tried.held("sampling")) == (
        digest("4"),
        digest("3"),
    )
    assert tried.varied == RECIPE.model_copy(
        update={"reasoning": digest("4"), "prompt": digest("5")}
    )
    assert tried.configuration == plan.configuration


def test_setting_the_configuration_s_own_chunk_takes_the_part_back() -> None:
    plan = TriedVariation(HEAD, "plan", RECIPE)
    tried = plan.set("prompt", digest("5"), "terse")

    assert tried.set("prompt", digest("1"), "its own").parts == {}
    assert tried.set("prompt", digest("1"), "its own").label == "plan"


def test_only_an_optional_part_can_be_taken_out() -> None:
    plan = TriedVariation(
        HEAD, "plan", RECIPE.model_copy(update={"toolset": digest("6")})
    )

    assert plan.set("toolset", None, "none").held("toolset") is None
    with pytest.raises(ValueError, match="only .* can be taken out"):
        _ = plan.set("prompt", None, "none")
    with pytest.raises(ValueError, match="has no recipe"):
        _ = TriedVariation(HEAD, "by hand").set("prompt", digest("5"), "terse")

from typing import Any

from fastapi.testclient import TestClient

from chatddx.api.test.test_variations import thread
from chatddx.test.world import LINES_GUIDED

INSTRUCTION = (
    "You are assisting a physician in an emergency department. Read the case and give "
    + "your assessment."
)


def translation(signed: TestClient, configuration: int, **body: Any) -> Any:
    return signed.post(f"/api/threads/{configuration}/translation", json=body)


def contents(request: dict[str, Any]) -> list[str]:
    return [m["content"] for m in request["messages"]]


def test_a_configuration_is_given_in_its_language_and_translated(
    signed: TestClient,
) -> None:
    guided = thread(signed, "configuration", LINES_GUIDED)["id"]
    got = translation(signed, guided, into="sv")
    assert got.status_code == 200, got.json()
    shown = got.json()

    assert (shown["label"], shown["language"]) == (LINES_GUIDED, "en")
    assert [t["part"] for t in shown["texts"]] == [
        "instructions",
        "few_shot",
        "few_shot",
        "output",
        "appendix_layout",
    ]
    assert None not in [t["translation"] for t in shown["texts"]]
    assert shown["unused"] == {}
    assert contents(shown["written"])[0].startswith(INSTRUCTION)
    assert contents(shown["request"])[0].startswith("Du bistår en läkare")
    assert shown["request"]["model"] == "‹model›"
    assert "‹vignette›" in contents(shown["request"])[-1]


def test_entries_as_typed_are_translated_and_a_part_can_be_set(
    signed: TestClient,
) -> None:
    guided = thread(signed, "configuration", LINES_GUIDED)["id"]
    shown = translation(signed, guided, into="sv").json()
    typed = {
        t["text"]: t["translation"] for t in shown["texts"] if t["text"] != INSTRUCTION
    }
    typed["Gone since"] = "Borta sedan"

    tried = translation(signed, guided, into="sv", entries=typed).json()
    [instruction] = [t for t in tried["texts"] if t["part"] == "instructions"]
    assert instruction["translation"] is None
    assert tried["unused"] == {"Gone since": "Borta sedan"}
    assert contents(tried["request"])[0].startswith(INSTRUCTION)

    bare = translation(signed, guided, into="sv", translations="").json()
    assert (bare["label"], bare["unused"]) == (f"{LINES_GUIDED}+translations=none", {})
    assert {t["translation"] for t in bare["texts"]} == {None}
    assert bare["request"] == bare["written"]


def test_a_translation_into_its_own_language_or_of_no_configuration_is_refused(
    signed: TestClient,
) -> None:
    guided = thread(signed, "configuration", LINES_GUIDED)["id"]
    own = translation(signed, guided, into="en")
    assert (own.status_code, own.json()["code"]) == (422, "refused")
    assert "written in en" in own.json()["detail"]
    assert translation(signed, guided, into="svenska!").status_code == 422
    assert translation(signed, 999_999, into="sv").status_code == 404

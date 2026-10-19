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


def test_a_configuration_s_request_is_translated_by_its_translations(
    signed: TestClient,
) -> None:
    guided = thread(signed, "configuration", LINES_GUIDED)["id"]
    got = translation(signed, guided, into="sv")
    assert got.status_code == 200, got.json()
    sent = got.json()

    assert contents(sent)[0].startswith("Du bistår en läkare")
    assert sent["model"] == "‹model›"
    assert "‹vignette›" in contents(sent)[-1]


def test_entries_as_typed_are_sent_and_a_text_without_one_as_written(
    signed: TestClient,
) -> None:
    guided = thread(signed, "configuration", LINES_GUIDED)["id"]
    typed = {"Gone since": "Borta sedan"}
    sent = translation(signed, guided, into="sv", entries=typed).json()
    assert contents(sent)[0].startswith(INSTRUCTION)

    bare = translation(signed, guided, into="sv", translations="").json()
    look = signed.get(f"/api/threads/{guided}/variation").json()
    assert contents(bare) == contents(look["request"])


def test_a_translation_into_its_own_language_or_of_no_configuration_is_refused(
    signed: TestClient,
) -> None:
    guided = thread(signed, "configuration", LINES_GUIDED)["id"]
    own = translation(signed, guided, into="en")
    assert (own.status_code, own.json()["code"]) == (422, "refused")
    assert "written in en" in own.json()["detail"]
    assert translation(signed, guided, into="svenska!").status_code == 422
    assert translation(signed, 999_999, into="sv").status_code == 404

import pytest
from fastapi.testclient import TestClient

from chatddx.api.test.test_variations import thread
from chatddx.api.test.test_writes import CLINICIAN, body
from chatddx.bench import KINDS, WRITTEN

GHOST = "sha256:" + "0" * 64


def test_the_kinds_say_their_json_schema_and_what_their_references_take(
    signed: TestClient,
) -> None:
    listed = {k["kind"]: k for k in signed.get("/api/kinds").json()}
    assert set(listed) == {kind for held in KINDS.values() for kind in held}
    assert {k for k, shown in listed.items() if shown["written"]} == WRITTEN
    assert (listed["chunk.reasoning"]["word"], listed["skeleton"]["word"]) == (
        "reasoning",
        "configuration",
    )
    expectation = listed["expectation"]["json_schema"]["properties"]
    assert expectation["case"]["x-kind"] == ["case"]
    assert expectation["expectation_schema"]["x-kind"] == ["expectation_schema"]
    judge = listed["judge"]["json_schema"]["properties"]
    assert (judge["skeleton"]["x-kind"], judge["engine"]["x-kind"]) == (
        ["skeleton"],
        ["engine.local", "engine.remote"],
    )


@pytest.mark.slow
def test_a_component_is_checked_as_a_write_would_store_it_and_nothing_is_written(
    signed: TestClient,
) -> None:
    held = body(signed, thread(signed, "instructions", CLINICIAN, "archive"))
    careful = {**held, "text": "You are a careful physician."}
    got = signed.post("/api/components/check", json=careful)
    assert got.status_code == 200
    checked = got.json()
    assert checked["findings"] == []
    assert signed.get(f"/api/components/{checked['digest']}").status_code == 404

    made = signed.post("/api/threads", json={"component": careful, "name": "careful"})
    assert made.json()["head"]["digest"] == checked["digest"]


@pytest.mark.slow
def test_a_check_says_what_the_lints_say(signed: TestClient) -> None:
    mine = signed.get(
        "/api/threads", params={"kind": "expectation", "owner": "alice"}
    ).json()[0]
    held = body(signed, mine)
    got = signed.post("/api/components/check", json={**held, "data": [1]})
    assert got.status_code == 200
    assert [f["code"] for f in got.json()["findings"]] == ["expectation.invalid"]


@pytest.mark.slow
def test_a_check_refuses_what_a_write_would(signed: TestClient) -> None:
    held = body(signed, thread(signed, "reasoning", "off"))
    expectation = body(
        signed,
        signed.get(
            "/api/threads", params={"kind": "expectation", "owner": "alice"}
        ).json()[0],
    )
    for given, said in (
        ({**held, "effort": "max"}, "effort"),
        ({**expectation, "case": GHOST}, f"not in the store: ['{GHOST}']"),
        ({"kind": "tool"}, "'tool' isn't a kind a person writes"),
    ):
        got = signed.post("/api/components/check", json=given)
        assert got.status_code == 422, given
        assert said in str(got.json()["detail"])

from typing import Any

import pytest
from fastapi.testclient import TestClient

from chatddx.test.world import LINES, QWEN

pytestmark = pytest.mark.solidified

ZERO = "sha256:" + "0" * 64


def _family(signed: TestClient, name: str) -> dict[str, Any]:
    [found] = signed.get("/api/families", params={"name": name}).json()
    return found


@pytest.mark.slow
def test_a_family_s_appendices_make_its_cases_and_carry_its_expectation(
    signed: TestClient, bob: dict[str, str]
) -> None:
    family = _family(signed, "crlf")
    base = f"/api/families/{family['id']}"
    [bare] = signed.get(f"{base}/cases").json()
    assert (bare["case"], bare["default"], bare["appendices"]) == (
        family["case"],
        True,
        [],
    )
    [expected] = bare["expectations"]
    assert signed.get(f"{base}/cases", headers=bob).status_code == 404

    got = signed.post(
        f"{base}/appendices", json={"text": "Lab:\r\nCRP 120", "name": "labs"}
    )
    assert got.status_code == 201
    labs = got.json()
    assert labs["kind"] == "appendix"
    body = signed.get(f"/api/components/{labs['head']['digest']}").json()["body"]
    assert body["text"] == "Lab:\nCRP 120"

    got = signed.post(f"{base}/cases", json={"appendices": [labs["head"]["digest"]]})
    assert got.status_code == 201
    made = got.json()
    assert (made["default"], made["appendices"], made["expectations"]) == (
        False,
        [labs["head"]["digest"]],
        [],
    )
    listed = [c["case"] for c in signed.get(f"{base}/cases").json()]
    assert listed == [family["case"], made["case"]]

    edits = f"/api/threads/{labs['id']}/edits"
    newer = {**body, "text": "Lab:\r\nCRP 150"}
    got = signed.post(edits, json={"head": labs["head"]["id"], "component": newer})
    assert got.status_code == 201
    [(old, replacement)] = got.json()["cases"].items()
    assert old == made["case"]
    assert replacement in [c["case"] for c in signed.get(f"{base}/cases").json()]

    threads = signed.get(
        "/api/threads", params={"kind": "expectation", "owner": "alice"}
    )
    [mine] = [
        t for t in threads.json() if t["head"]["digest"] == expected["expectation"]
    ]
    carries = f"/api/threads/{mine['id']}/carries"
    got = signed.post(carries, json={"head": mine["head"]["id"], "case": replacement})
    assert got.status_code == 201
    [carried] = [
        c for c in signed.get(f"{base}/cases").json() if c["case"] == replacement
    ]
    assert [e["data"] for e in carried["expectations"]] == [expected["data"]]


def test_a_case_built_of_what_isn_t_the_family_s_is_refused(signed: TestClient) -> None:
    family = _family(signed, "crlf")
    other = _family(signed, "bom")
    cases = f"/api/families/{family['id']}/cases"
    refused: list[tuple[dict[str, Any], str]] = [
        ({"appendices": [ZERO]}, f"no appendix {ZERO} for alice"),
        ({"replacing": family["case"]}, "at its family's current vignette already"),
        ({"replacing": other["case"]}, f"isn't a case of family {family['id']}"),
        ({"appendices": [], "replacing": family["case"]}, "not both"),
    ]
    for asked, said in refused:
        got = signed.post(cases, json=asked)
        assert got.status_code == 422, (asked, got.json())
        assert said in str(got.json()["detail"])


def test_a_run_names_its_cases_among_the_current_ones(signed: TestClient) -> None:
    [configuration] = signed.get(
        "/api/threads",
        params={"kind": "configuration", "name": LINES, "owner": "alice"},
    ).json()
    asked = {"configuration": configuration["id"], "endpoint": QWEN, "cases": [ZERO]}
    got = signed.post("/api/runs", json=asked)
    assert (got.status_code, got.json()) == (
        422,
        {"detail": f"no case {ZERO} for alice", "code": "refused"},
    )
    both = {**asked, "tags": ["swedish"]}
    assert signed.post("/api/runs", json=both).status_code == 422

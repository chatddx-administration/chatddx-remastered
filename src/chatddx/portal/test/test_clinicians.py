import json
from typing import Any

import pytest
from fastapi.testclient import TestClient

from chatddx.identity import Person
from chatddx.portal.test.test_library import thread_props
from chatddx.portal.test.test_reading import shown
from chatddx.portal.test.test_signing_in import signing_in


@pytest.fixture
def signed(client: TestClient, alice: Person) -> TestClient:
    assert alice.login == "alice"
    assert signing_in(client).status_code == 303
    return client


def family(signed: TestClient, name: str = "crlf") -> dict[str, Any]:
    [found] = signed.get("/api/families", params={"name": name}).json()
    return found


def editors(page: str) -> list[dict[str, Any]]:
    held = page.split('<div data-editor class="mt-2"><script type="application/json">')
    return [json.loads(part.split("</script>", 1)[0]) for part in held[1:]]


def appendix(signed: TestClient, at: dict[str, Any], text: str) -> dict[str, Any]:
    got = signed.post(
        f"/families/{at['id']}/appendices", data={"name": "ultrasound", "text": text}
    )
    assert (got.status_code, got.headers["location"]) == (
        303,
        f"/families/{at['id']}#appendices",
    )
    query = {"kind": "appendix", "owner": "alice", "name": "ultrasound"}
    [made] = signed.get("/api/threads", params=query).json()
    return made


@pytest.mark.slow
def test_an_appendix_is_written_and_a_case_built_of_it(signed: TestClient) -> None:
    crlf = family(signed)
    made = appendix(signed, crlf, "Gallstones on ultrasound.\r\n")
    page = shown(signed, f"/families/{crlf['id']}")
    assert f'href="/threads/{made["id"]}">ultrasound' in page
    assert f'name="appendix" value="{made["head"]["digest"]}"' in page

    got = signed.post(
        f"/families/{crlf['id']}/cases", data={"appendix": made["head"]["digest"]}
    )
    assert got.status_code == 303
    cases = signed.get(f"/api/families/{crlf['id']}/cases").json()
    [built] = [c for c in cases if c["appendices"] == [made["head"]["digest"]]]
    page = shown(signed, f"/families/{crlf['id']}")
    [editor] = editors(page)
    assert (editor["mode"], editor["case"]) == ("new", built["case"])
    [default] = [c for c in cases if c["default"]]
    assert editor["data"] == default["expectations"][0]["data"]
    assert editor["json_schema"]["title"] == "Targets"

    editing = thread_props(shown(signed, f"/threads/{made['id']}"))["editor"]
    assert (editing["kind"], editing["mode"], editing["text"]) == (
        "appendix",
        "edit",
        "Gallstones on ultrasound.\n",
    )
    assert signed.post(f"/families/{crlf['id']}/cases").status_code == 422


@pytest.mark.slow
def test_an_expectation_is_moved_to_a_case_that_replaces_its_own(
    signed: TestClient,
) -> None:
    crlf = family(signed)
    made = appendix(signed, crlf, "Gallstones.")
    _ = signed.post(
        f"/families/{crlf['id']}/cases", data={"appendix": made["head"]["digest"]}
    )
    cases = signed.get(f"/api/families/{crlf['id']}/cases").json()
    first = next(c for c in cases if not c["default"])
    default = next(c for c in cases if c["default"])
    data = {"diagnosis": {"pattern": "biliary & colic"}}
    body = {
        "component": {
            "kind": "expectation",
            "case": first["case"],
            "expectation_schema": default["expectations"][0]["expectation_schema"],
            "data": data,
        },
        "name": "with ultrasound",
    }
    written = signed.post("/api/threads", json=body).json()

    edits = f"/api/threads/{made['id']}/edits"
    component = signed.get(f"/api/components/{made['head']['digest']}").json()["body"]
    moved = signed.post(
        edits,
        json={
            "head": made["head"]["id"],
            "component": {**component, "text": "Stones."},
        },
    ).json()
    [replacement] = moved["cases"].values()
    page = shown(signed, f"/families/{crlf['id']}")
    assert f'action="/threads/{written["id"]}/carry"' in page
    got = signed.post(
        f"/threads/{written['id']}/carry",
        data={
            "head": written["head"]["id"],
            "case": replacement,
            "next": f"/families/{crlf['id']}",
        },
    )
    assert (got.status_code, got.headers["location"]) == (
        303,
        f"/families/{crlf['id']}",
    )
    carried = signed.get(f"/api/threads/{written['id']}").json()
    held = signed.get(f"/api/components/{carried['head']['digest']}").json()["body"]
    assert (held["case"], held["data"]) == (replacement, data)


@pytest.mark.slow
def test_a_shared_expectation_is_taken_and_one_s_own_changed_on_its_page(
    signed: TestClient,
) -> None:
    crlf = family(signed)
    [expected] = signed.get(f"/api/families/{crlf['id']}").json()["expectations"]
    mine = next(
        t
        for t in signed.get(
            "/api/threads", params={"kind": "expectation", "owner": "alice"}
        ).json()
        if t["head"]["digest"] == expected["expectation"]
    )
    editing = thread_props(shown(signed, f"/threads/{mine['id']}"))["editor"]
    assert (editing["kind"], editing["mode"], editing["data"]) == (
        "expectation",
        "edit",
        expected["data"],
    )
    assert 'id="edit"' not in shown(signed, f"/threads/{mine['id']}")

    assert signed.delete(f"/api/threads/{mine['id']}").status_code == 204
    page = shown(signed, f"/families/{crlf['id']}")
    [shared] = signed.get(f"/api/families/{crlf['id']}").json()["expectations"][0][
        "shared"
    ]
    assert f'action="/threads/{shared["id"]}/take"' in page
    archives = thread_props(shown(signed, f"/threads/{shared['id']}"))["editor"]
    assert archives["mode"] == "fork"

    got = signed.post(
        f"/threads/{shared['id']}/take", data={"next": f"/families/{crlf['id']}"}
    )
    assert (got.status_code, got.headers["location"]) == (
        303,
        f"/families/{crlf['id']}",
    )
    [now] = signed.get(f"/api/families/{crlf['id']}").json()["expectations"]
    assert now["expectation"] == shared["head"]["digest"]

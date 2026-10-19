import json
from typing import Any

import pytest
from fastapi.testclient import TestClient
from markupsafe import escape

from chatddx.identity import Person
from chatddx.portal.test.test_reading import shown
from chatddx.portal.test.test_signing_in import signing_in
from chatddx.test.world import JUDGE, LINES, LINES_GUIDED

INSTRUCTION = (
    "You are assisting a physician in an emergency department. Read the case and give "
    + "your assessment."
)


@pytest.fixture
def signed(client: TestClient, alice: Person) -> TestClient:
    assert alice.login == "alice"
    assert signing_in(client).status_code == 303
    return client


def configuration(
    signed: TestClient, name: str, purpose: str = "generation"
) -> dict[str, Any]:
    query = {"kind": "configuration", "name": name, "owner": "alice"}
    [found] = signed.get("/api/threads", params={**query, "purpose": purpose}).json()
    return found


def props(page: str) -> dict[str, Any]:
    held = page.split('<script type="application/json" id="translate-props">', 1)[1]
    return json.loads(held.split("</script>", 1)[0])


def listed(page: str, thread: int) -> str:
    item = page.split(f'<a href="/translate/{thread}', 1)[1]
    return item.split("</a>", 1)[0]


@pytest.mark.slow
def test_translate_opens_the_person_s_first_configuration(signed: TestClient) -> None:
    found = signed.get(
        "/api/threads", params={"kind": "configuration", "owner": "alice"}
    ).json()
    first = min(found, key=lambda t: t["name"] or t["title"])
    got = signed.get("/translate")
    assert (got.status_code, got.headers["location"]) == (
        303,
        f"/translate/{first['id']}",
    )


@pytest.mark.slow
def test_a_configuration_s_texts_are_shown_beside_their_translations(
    signed: TestClient,
) -> None:
    guided = configuration(signed, LINES_GUIDED)
    page = shown(signed, f"/translate/{guided['id']}")
    held = props(page)
    swedish = {t["text"]: t["translation"] for t in held["texts"]}

    assert (held["into"], held["language"]) == ("sv", "en")
    assert escape(INSTRUCTION) in page and escape(swedish[INSTRUCTION]) in page
    assert "every text translated" in page
    assert "instructions · " in page and "appendix layout · " in page
    assert {b["part"] for b in held["bodies"]} >= {"instructions", "few_shot", "output"}
    assert held["request"]["messages"][0]["content"].startswith("Du bistår")
    assert held["written"]["messages"][0]["content"].startswith(INSTRUCTION)
    assert "sv ✓" in listed(page, guided["id"])


@pytest.mark.slow
def test_a_text_without_a_translation_is_said_missing(signed: TestClient) -> None:
    lines = configuration(signed, LINES)
    page = shown(signed, f"/translate/{lines['id']}")
    [text] = props(page)["texts"]

    assert (text["part"], text["translation"]) == ("output", None)
    assert "· 1 missing" in page and "no translations" in page
    assert "sv 1" in listed(page, lines["id"])
    assert escape(text["text"]) in props(page)["request"]["messages"][0]["content"]


@pytest.mark.slow
def test_an_entry_no_text_holds_is_listed_apart(signed: TestClient) -> None:
    guided = configuration(signed, LINES_GUIDED)
    entries = {
        t["text"]: t["translation"]
        for t in props(shown(signed, f"/translate/{guided['id']}"))["texts"]
    }
    body = {"kind": "chunk.translations", "into": {"sv": {**entries, "Gone": "Borta"}}}
    made = signed.post("/api/threads", json={"name": "more", "component": body})
    assert made.status_code == 201, made.json()
    parts = {"translations": made.json()["head"]["digest"]}
    forked = signed.post(
        f"/api/threads/{guided['id']}/forks", json={"name": "kept", "parts": parts}
    )
    assert forked.status_code == 201, forked.json()

    page = shown(signed, f"/translate/{forked.json()['id']}")
    assert props(page)["unused"] == {"Gone": "Borta"}
    assert "Not used by it: 1" in page and "Borta" in page


@pytest.mark.slow
def test_a_judge_s_configuration_runs_in_no_language(signed: TestClient) -> None:
    judge = configuration(signed, JUDGE, "judge")
    page = shown(signed, f"/translate/{judge['id']}")
    assert "a judge runs in no language" in page
    assert 'id="translate-props"' not in page
    assert f'href="/configurations/{judge["id"]}"' in page


@pytest.mark.slow
def test_a_translation_into_its_own_language_or_no_tag_is_refused(
    signed: TestClient,
) -> None:
    guided = configuration(signed, LINES_GUIDED)
    for into in ("en", "svenska!"):
        got = signed.get(f"/translate/{guided['id']}", params={"into": into})
        assert got.status_code == 422
    assert signed.get("/translate/999999").status_code == 404


@pytest.mark.slow
def test_the_page_is_given_where_a_save_goes(signed: TestClient) -> None:
    guided = configuration(signed, LINES_GUIDED)
    held = props(shown(signed, f"/translate/{guided['id']}"))
    given = held["configuration"]
    assert (given["thread"], given["head"], given["latest"], given["mine"]) == (
        guided["id"],
        guided["head"]["id"],
        True,
        True,
    )
    detail = signed.get(f"/api/threads/{guided['id']}").json()
    translations = held["translations"]
    assert given["translations"] == translations["digest"]
    assert translations["digest"] == detail["recipe"]["translations"]
    assert translations["body"]["kind"] == "chunk.translations"
    assert "sv" in translations["body"]["into"]


@pytest.mark.slow
def test_a_translations_thread_s_page_edits_its_entries(signed: TestClient) -> None:
    query = {"kind": "translations", "owner": "alice"}
    [guided] = signed.get("/api/threads", params=query).json()
    page = shown(signed, f"/threads/{guided['id']}")
    held = page.split('<script type="application/json" id="thread-props">', 1)[1]
    editor = json.loads(held.split("</script>", 1)[0])["editor"]
    body = signed.get(f"/api/components/{guided['head']['digest']}").json()["body"]
    assert (editor["kind"], editor["mode"], editor["into"]) == (
        "translations",
        "edit",
        body["into"],
    )


@pytest.mark.slow
def test_languages_are_offered_its_translations_first_then_its_cases_and_any(
    signed: TestClient,
) -> None:
    lines = configuration(signed, LINES)
    page = shown(signed, f"/translate/{lines['id']}")
    nav = page.split('aria-label="Languages"', 1)[1].split("</nav>", 1)[0]
    assert "cases you see are in it" in nav and 'name="into"' in nav

    guided = configuration(signed, LINES_GUIDED)
    page = shown(signed, f"/translate/{guided['id']}?into=de")
    held = props(page)
    assert held["into"] == "de"
    assert {t["translation"] for t in held["texts"]} == {None}
    assert "a language it isn&#39;t translated into yet" in page


@pytest.mark.slow
def test_a_case_in_a_regional_tag_is_said_to_want_its_own_translations(
    signed: TestClient,
) -> None:
    for language in ("sv-SE", "en-GB"):
        typed = {"text": "Fever and a cough.", "language": language}
        assert signed.post("/api/families", json=typed).status_code == 201
    guided = configuration(signed, LINES_GUIDED)
    page = shown(signed, f"/translate/{guided['id']}")
    assert "Cases you see in sv-SE aren&#39;t sent by its translations into sv" in page
    assert "Cases you see in en-GB aren&#39;t sent as written" in page
    assert "sv-SE ✓" not in listed(page, guided["id"])

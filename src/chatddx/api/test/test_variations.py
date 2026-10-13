from typing import Any

import psycopg
import pytest
from fastapi.testclient import TestClient

from chatddx.api.schemas import Parts
from chatddx.api.test.conftest import sign_in
from chatddx.bench import OPTIONAL, PARTS, Bench
from chatddx.bench.test.helpers import another_expectation
from chatddx.curation import load_cases
from chatddx.factors.request import Translations
from chatddx.store import Store
from chatddx.store.store import Connection
from chatddx.test.world import DATA, LINES, NATIVE, NATIVE_TOOLS, OFF, QWEN

pytestmark = pytest.mark.solidified

DIFFERENTIAL = ("answer", "differential")


def thread(
    signed: TestClient, kind: str, name: str, owner: str = "alice"
) -> dict[str, Any]:
    query = {"kind": kind, "name": name, "owner": owner}
    [found] = signed.get("/api/threads", params=query).json()
    return found


def digest(signed: TestClient, kind: str, name: str) -> str:
    return thread(signed, kind, name)["head"]["digest"]


def variation(
    signed: TestClient, configuration: dict[str, Any], **params: Any
) -> dict[str, Any]:
    got = signed.get(f"/api/threads/{configuration['id']}/variation", params=params)
    assert got.status_code == 200, got.json()
    return got.json()


def parts(shown: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {p["part"]: p for p in shown["parts"]}


def test_a_request_names_the_recipe_s_parts(client: TestClient) -> None:
    assert tuple(Parts.model_fields) == PARTS
    described = client.get("/api/openapi.json").json()
    get = described["paths"]["/api/threads/{thread}/variation"]["get"]
    assert {p["name"] for p in get["parameters"]} == {
        "thread",
        *PARTS,
        "endpoint",
        "tag",
        "seed",
    }


@pytest.mark.slow
def test_a_configuration_with_nothing_replaced_is_itself(signed: TestClient) -> None:
    mine = thread(signed, "configuration", LINES)
    shown = variation(signed, mine, seed=7)
    assert (shown["head"], shown["skeleton"]) == (mine["head"], mine["head"]["digest"])
    assert not shown["greedy"]

    held = parts(shown)
    recipe = signed.get(f"/api/threads/{mine['id']}").json()["recipe"]
    assert {p: held[p]["digest"] for p in PARTS} == {p: recipe[p] for p in PARTS}
    assert not any(p["replaced"] for p in held.values())
    assert (held["output"]["title"], held["output"]["summary"]) == (
        "lines (en)",
        "text output",
    )
    assert held["reasoning"] == {
        "part": "reasoning",
        "digest": None,
        "title": None,
        "summary": None,
        "replaced": False,
    }

    request = shown["request"]
    assert (request["model"], request["seed"]) == ("‹model›", 7)
    assert "‹vignette›‹appendices›" in str(request["messages"])
    assert shown["findings"] is None


@pytest.mark.slow
def test_a_variation_replaces_parts_by_digest_or_takes_them_out(
    signed: TestClient,
) -> None:
    mine = thread(signed, "configuration", LINES)
    off = digest(signed, "reasoning", OFF)
    shown = variation(signed, mine, reasoning=off)
    assert shown["head"] == mine["head"]
    assert shown["skeleton"] != mine["head"]["digest"]
    reasoning = parts(shown)["reasoning"]
    assert (reasoning["digest"], reasoning["title"], reasoning["replaced"]) == (
        off,
        OFF,
        True,
    )
    assert "enable_thinking false" in reasoning["summary"]
    assert shown["request"]["chat_template_kwargs"] == {"enable_thinking": False}

    own = parts(shown)["prompt"]["digest"]
    same = variation(signed, mine, prompt=own)
    assert same["skeleton"] == mine["head"]["digest"]
    assert not parts(same)["prompt"]["replaced"]

    web = thread(signed, "configuration", NATIVE_TOOLS)
    assert "tools" in variation(signed, web)["request"]
    taken = variation(signed, web, toolset="")
    toolset = parts(taken)["toolset"]
    assert (toolset["digest"], toolset["replaced"]) == (None, True)
    assert "tools" not in taken["request"]


@pytest.mark.slow
def test_the_seed_is_drawn_unless_given_and_greedy_sampling_sends_none(
    signed: TestClient,
) -> None:
    mine = thread(signed, "configuration", LINES)
    drawn = variation(signed, mine)
    assert 0 <= drawn["seed"] < 2**31
    assert drawn["request"]["seed"] == drawn["seed"]

    greedy = variation(signed, mine, sampling=digest(signed, "sampling", "greedy"))
    assert greedy["greedy"]
    assert "seed" not in greedy["request"]


@pytest.mark.slow
def test_a_variation_is_rendered_and_linted_for_an_endpoint(
    signed: TestClient,
) -> None:
    web = thread(signed, "configuration", NATIVE_TOOLS)
    engine = signed.get(f"/api/endpoints/{QWEN}").json()["engine"]
    shown = variation(signed, web, endpoint=QWEN)
    assert shown["request"]["model"] == engine
    codes = {f["code"] for f in shown["findings"]}
    assert {"vllm.native_tools_uncallable", "language.mixed"} <= codes

    english = variation(signed, web, endpoint=QWEN, tag="targets")
    assert "language.mixed" not in {f["code"] for f in english["findings"]}
    tagged = signed.get("/api/families", params={"tag": "targets"}).json()
    assert {f["language"] for f in tagged} == {"en"}
    assert {r["cases"] for r in english["reach"]} == {len(tagged)}

    nowhere = variation(signed, web, endpoint=QWEN, tag="nowhere")
    assert {r["cases"] for r in nowhere["reach"]} == {0}
    assert [f["code"] for f in nowhere["findings"]] == ["vllm.native_tools_uncallable"]


@pytest.mark.slow
def test_each_scorer_view_s_reach_names_the_families_it_misses(
    signed: TestClient,
) -> None:
    listed = signed.get("/api/families").json()
    families = sorted(f["id"] for f in listed)
    native = variation(signed, thread(signed, "configuration", NATIVE))
    reach = {(r["name"], r["label"]): r for r in native["reach"]}
    differential = reach[DIFFERENTIAL]
    assert differential["scorer"] == thread(signed, "scorer", "answer", "archive")["id"]
    assert (differential["offered"], differential["cases"]) == (True, len(families))
    assert differential["missing"] == []
    dont_miss = {
        id
        for id, case in load_cases(DATA).items()
        if isinstance(case.targets, dict) and "dont_miss" in case.targets
    }
    assert dont_miss
    assert sorted(reach["answer", "dont-miss"]["missing"]) == sorted(
        f["id"] for f in listed if f["name"] not in dont_miss
    )

    lines = variation(signed, thread(signed, "configuration", LINES))
    reach = {(r["name"], r["label"]): r for r in lines["reach"]}
    assert (
        reach["answer", "warning"]["offered"],
        reach["answer", "warning"]["missing"],
    ) == (
        False,
        [],
    )
    assert reach["lines", "text"]["missing"] == []


@pytest.mark.slow
def test_a_case_with_expectations_to_choose_from_is_shown_apart_in_the_reach(
    signed: TestClient, bench: Bench
) -> None:
    native = thread(signed, "configuration", NATIVE)
    [family] = signed.get("/api/families", params={"name": "crlf"}).json()

    def differential() -> tuple[list[int], list[int]]:
        shown = variation(signed, native)
        [found] = [r for r in shown["reach"] if (r["name"], r["label"]) == DIFFERENTIAL]
        return found["missing"], found["choosing"]

    assert differential() == ([], [])
    _ = another_expectation(bench, family["case"], {"diagnosis": {"pattern": "x"}})
    assert differential() == ([], [family["id"]])


@pytest.mark.slow
def test_an_unsaved_variation_is_linted_in_its_recipe_s_language(
    signed: TestClient,
) -> None:
    web = thread(signed, "configuration", NATIVE_TOOLS)
    off = digest(signed, "reasoning", OFF)

    def codes(**params: Any) -> set[str]:
        shown = variation(signed, web, endpoint=QWEN, reasoning=off, **params)
        assert shown["skeleton"] != web["head"]["digest"]
        return {f["code"] for f in shown["findings"]}

    assert "language.unknown" not in codes(tag="targets")
    assert "language.mixed" in codes()


def test_a_judge_configuration_is_looked_at_as_a_judge(signed: TestClient) -> None:
    query = {"kind": "configuration", "purpose": "judge", "name": "judge (en)"}
    [judging] = signed.get("/api/threads", params={**query, "owner": "alice"}).json()
    shown = variation(signed, judging, endpoint=QWEN)
    assert shown["reach"] == [] and shown["findings"] == []
    assert "‹completion›" in str(shown["request"])


@pytest.mark.slow
def test_a_variation_the_bench_refuses_is_unprocessable(
    signed: TestClient, conn: Connection, bob: dict[str, str]
) -> None:
    mine = thread(signed, "configuration", LINES)
    off = digest(signed, "reasoning", OFF)
    store = Store(conn)
    registry = store.load([])
    untranslated = registry.add(Translations(entries={"Hello": "Hej"}))
    _ = store.add(registry, [untranslated])
    path = f"/api/threads/{mine['id']}/variation"
    for params, said in (
        ({"prompt": off}, f"{off} isn't a stored chunk of prompt"),
        (
            {"prompt": ""},
            "a configuration always has a prompt: only "
            + f"{', '.join(OPTIONAL)} can be taken out",
        ),
        ({"translations": untranslated}, "no translation for "),
        ({"endpoint": "nowhere@fake"}, "no endpoint 'nowhere@fake' in the inventory"),
    ):
        got = signed.get(path, params=params)
        assert got.status_code == 422, params
        assert got.json()["detail"].startswith(said)

    got = signed.get(path, params={"stack": off})
    assert got.status_code == 422
    assert [e["loc"] for e in got.json()["detail"]] == [["query", "stack"]]

    chunk = thread(signed, "reasoning", OFF)["id"]
    got = signed.get(f"/api/threads/{chunk}/variation")
    assert (got.status_code, got.json()) == (
        404,
        {"detail": f"no configuration {chunk} for alice", "code": "not_found"},
    )
    got = signed.get(path, headers=bob)
    assert (got.status_code, got.json()) == (
        404,
        {"detail": f"no configuration {mine['id']} for bob", "code": "not_found"},
    )


@pytest.mark.slow
def test_a_look_s_queries_don_t_grow_with_its_cases(
    signed: TestClient, db: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    web = thread(signed, "configuration", NATIVE_TOOLS)
    counted = [0]
    execute = psycopg.Cursor.execute

    # Only the look's: the fixtures make the next test's database meanwhile.
    def counting(cursor: psycopg.Cursor[Any], *args: Any, **kwargs: Any) -> Any:
        counted[0] += cursor.connection.info.dbname == db
        return execute(cursor, *args, **kwargs)

    monkeypatch.setattr(psycopg.Cursor, "execute", counting)

    def look(**params: Any) -> tuple[int, int]:
        counted[0] = 0
        shown = variation(signed, web, endpoint=QWEN, **params)
        return shown["reach"][0]["cases"], counted[0]

    (few, queries), (every, again) = look(tag="swedish"), look()
    assert few < every
    assert queries == again


@pytest.mark.slow
def test_a_fork_is_a_configuration_of_one_s_own(signed: TestClient) -> None:
    archives = thread(signed, "configuration", LINES, "archive")
    off = digest(signed, "reasoning", OFF)
    path = f"/api/threads/{archives['id']}/forks"
    asked = {"name": "terse", "parts": {"reasoning": off}}

    got = signed.post(path, json=asked)
    assert got.status_code == 201
    made = got.json()
    assert got.headers["location"] == f"/api/threads/{made['id']}"
    assert made.pop("findings") == []
    assert signed.get(got.headers["location"]).json() == made
    assert (made["kind"], made["name"], made["owner"]) == ("skeleton", "terse", "alice")
    assert made["forked_from"] == archives["head"]["id"]
    assert made["recipe"]["reasoning"] == off
    assert (
        made["head"]["digest"] == variation(signed, archives, reasoning=off)["skeleton"]
    )

    again = signed.post(path, json=asked)
    assert again.status_code == 201 and again.json()["id"] != made["id"]
    plain = signed.post(path, json={"name": "mine"}).json()
    assert plain["head"]["digest"] == archives["head"]["digest"]


@pytest.mark.slow
def test_an_edit_is_a_new_version_of_one_s_own_configuration(
    signed: TestClient,
) -> None:
    mine = thread(signed, "configuration", LINES)
    off = digest(signed, "reasoning", OFF)
    path = f"/api/threads/{mine['id']}/edits"
    seen = mine["head"]["id"]

    got = signed.post(path, json={"head": seen, "parts": {"reasoning": off}})
    assert got.status_code == 201
    edited = got.json()
    assert (edited["by"], edited["digest"]) == (
        "alice",
        variation(signed, mine, reasoning=off)["skeleton"],
    )
    assert (edited.pop("findings"), edited.pop("cases")) == ([], {})
    assert signed.get(path).json()[-1] == edited

    now = edited["id"]
    again = signed.post(path, json={"head": now, "parts": {"reasoning": off}})
    assert again.status_code == 200
    assert again.json() == {**edited, "findings": [], "cases": {}}
    assert signed.post(path, json={"head": now}).status_code == 200
    moved = signed.post(path, json={"head": seen, "parts": {"reasoning": None}})
    assert moved.status_code == 409
    assert (
        f"has moved on since edit {seen}: its head is edit {now}"
        in (moved.json()["detail"])
    )

    back = signed.post(path, json={"head": now, "parts": {"reasoning": None}})
    assert back.status_code == 201
    assert [e["digest"] for e in signed.get(path).json()][-3:] == [
        mine["head"]["digest"],
        edited["digest"],
        mine["head"]["digest"],
    ]


def test_only_one_s_own_configuration_is_edited_and_a_seen_one_forked(
    signed: TestClient, bob: dict[str, str]
) -> None:
    archives = thread(signed, "configuration", LINES, "archive")
    got = signed.post(
        f"/api/threads/{archives['id']}/edits", json={"head": archives["head"]["id"]}
    )
    assert (got.status_code, got.json()) == (
        404,
        {"detail": f"no configuration {archives['id']} of yours", "code": "not_found"},
    )

    mine = thread(signed, "configuration", LINES)
    head = mine["head"]["id"]
    for path, body in (
        (f"/api/threads/{mine['id']}/forks", {"name": "bob's"}),
        (f"/api/threads/{mine['id']}/edits", {"head": head}),
    ):
        got = signed.post(path, json=body, headers=bob)
        assert (got.status_code, got.json()) == (
            404,
            {"detail": f"no configuration {mine['id']} for bob", "code": "not_found"},
        )

    off = digest(signed, "reasoning", OFF)
    forks, edits = (f"/api/threads/{mine['id']}/{to}" for to in ("forks", "edits"))
    unvalidated: list[tuple[str, dict[str, Any], list[str]]] = [
        (forks, {"name": ""}, ["body", "name"]),
        (forks, {"parts": {}}, ["body", "name"]),
        (edits, {"head": head, "parts": {"stack": off}}, ["body", "parts", "stack"]),
        (edits, {"parts": {}}, ["body", "head"]),
    ]
    for path, body, where in unvalidated:
        got = signed.post(path, json=body)
        assert got.status_code == 422
        assert [e["loc"] for e in got.json()["detail"]] == [where]
    got = signed.post(edits, json={"head": head, "parts": {"prompt": off}})
    assert (got.status_code, got.json()) == (
        422,
        {"detail": f"{off} isn't a stored chunk of prompt", "code": "refused"},
    )
    assert signed.get(edits).json()[-1] == mine["head"]


def test_trying_forking_and_editing_need_a_session(
    client: TestClient, bench: Bench
) -> None:
    mine = bench.thread("configuration", LINES)[0].thread
    assert client.get(f"/api/threads/{mine}/variation").status_code == 401
    for path in (f"/api/threads/{mine}/forks", f"/api/threads/{mine}/edits"):
        assert client.post(path, json={"name": "x"}).status_code == 401

    _ = sign_in(client, **{"Sec-Fetch-Site": "same-origin"})
    elsewhere = {"Sec-Fetch-Site": "cross-site"}
    got = client.post(
        f"/api/threads/{mine}/forks", json={"name": "x"}, headers=elsewhere
    )
    assert got.status_code == 403

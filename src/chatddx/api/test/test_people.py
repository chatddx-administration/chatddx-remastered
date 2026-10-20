from collections.abc import Callable
from typing import Any

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatddx import cli
from chatddx.api.people import COOKIE
from chatddx.api.schemas import Me
from chatddx.api.test.conftest import PASSWORD, sign_in
from chatddx.bench import Ambiguous, Conflict, MovedOn, NotFound, OverQuota
from chatddx.identity import Person
from chatddx.runner import Refused
from chatddx.test.world import TEST

ELSEWHERE = (
    {"Sec-Fetch-Site": "cross-site"},
    {"Sec-Fetch-Site": "same-site"},
    {"Origin": "https://elsewhere.example"},
    {"Sec-Fetch-Site": "cross-site", "Origin": "https://testserver"},
)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_nothing_is_answered_without_a_session(client: TestClient) -> None:
    got = client.get("/api/me")
    assert got.status_code == 401
    assert got.json() == {"detail": "sign in first", "code": "unauthenticated"}
    assert got.headers["www-authenticate"] == "Bearer"
    assert client.get("/api/me", headers=bearer("made-up")).json() == {
        "detail": "the session has ended: sign in again",
        "code": "unauthenticated",
    }


SIGNING_IN = ("post", "/api/session")
FILLED = {"integer": "1", "string": "x", "uuid": "00000000-0000-0000-0000-000000000000"}


@pytest.mark.slow
def test_every_route_but_signing_in_needs_a_session(
    client: TestClient, described: dict[str, Any]
) -> None:
    for path, operations in described["paths"].items():
        for method, operation in operations.items():
            if (method, path) == SIGNING_IN:
                continue
            filled = path.format(
                **{
                    p["name"]: FILLED[p["schema"].get("format", p["schema"]["type"])]
                    for p in operation.get("parameters", [])
                    if p["in"] == "path"
                }
            )
            body: dict[str, Any] | None = (
                {} if method in ("post", "put", "patch") else None
            )
            got = client.request(method, filled, json=body)
            assert got.status_code == 401, (method, path, got.text)


def test_signing_in_gives_a_token_and_a_cookie_that_each_say_who_you_are(
    client: TestClient, alice: Person
) -> None:
    assert sign_in(client, password="wrong").status_code == 401
    assert sign_in(client, login="nobody").json() == {
        "detail": "wrong login or password",
        "code": "unauthenticated",
    }

    got = sign_in(client)
    assert got.status_code == 201
    me = Me.of(alice).model_dump(mode="json")
    assert got.json()["person"] == me
    cookie = got.headers["set-cookie"].lower()
    assert cookie.startswith(f"{COOKIE.lower()}={got.json()['token'].lower()};")
    for attribute in (
        "httponly",
        "secure",
        "samesite=lax",
        "path=/",
        "max-age=43200",
    ):
        assert attribute in cookie

    assert client.get("/api/me").json() == me
    client.cookies.clear()
    assert client.get("/api/me", headers=bearer(got.json()["token"])).json() == me


@pytest.mark.usefixtures("alice")
@pytest.mark.slow
def test_a_cookie_s_unsafe_requests_must_come_from_this_site(
    client: TestClient,
) -> None:
    for elsewhere in ELSEWHERE:
        assert sign_in(client, **elsewhere).status_code == 403

    token = sign_in(client, **{"Sec-Fetch-Site": "same-origin"}).json()["token"]
    for elsewhere in ELSEWHERE:
        got = client.delete("/api/session", headers=elsewhere)
        assert got.status_code == 403
        assert got.json() == {
            "detail": "a browser's request must come from this site's pages",
            "code": "cross_site",
        }
        assert client.get("/api/me", headers=elsewhere).status_code == 200

    assert (
        client.delete(
            "/api/session", headers={"Origin": "https://testserver"}
        ).status_code
        == 204
    )

    token = sign_in(client).json()["token"]
    client.cookies.clear()
    cross = {**bearer(token), "Sec-Fetch-Site": "cross-site"}
    assert client.delete("/api/session", headers=cross).status_code == 204


@pytest.mark.usefixtures("alice")
def test_signing_out_ends_the_session_and_drops_the_cookie(client: TestClient) -> None:
    token = sign_in(client).json()["token"]
    got = client.delete("/api/session")
    assert got.status_code == 204
    cookie = got.headers["set-cookie"].lower()
    assert cookie.startswith(f"{COOKIE.lower()}=") and "max-age=0" in cookie
    assert client.get("/api/me").json() == {
        "detail": "sign in first",
        "code": "unauthenticated",
    }
    assert client.get("/api/me", headers=bearer(token)).status_code == 401


def test_a_request_that_doesn_t_validate_is_refused_with_where(
    client: TestClient,
) -> None:
    got = client.post("/api/session", json={"login": "alice"})
    assert got.status_code == 422
    assert [e["loc"] for e in got.json()["detail"]] == [["body", "password"]]
    assert got.json()["code"] == "unprocessable"
    extra = {"login": "alice", "password": PASSWORD, "remember": True}
    assert client.post("/api/session", json=extra).status_code == 422


def raising(error: Exception) -> Callable[[], None]:
    def raised() -> None:
        raise error

    return raised


@pytest.mark.slow
def test_the_bench_s_errors_and_the_gate_s_refusals_have_their_status_and_code(
    served: FastAPI, client: TestClient
) -> None:
    for error, status, code in (
        (NotFound("no case 'nope' for alice"), 404, "not_found"),
        (Ambiguous("case 'plan' names 2"), 409, "ambiguous"),
        (
            Conflict("expectation 7 is yours: replace it to take this one"),
            409,
            "conflict",
        ),
        (MovedOn("thread 7 has moved on to edit 9"), 409, "moved_on"),
        (OverQuota("alice has typed 50 cases in the last day"), 429, "over_quota"),
        (Refused("endpoint 'x' isn't cleared for source test"), 422, "refused"),
    ):
        path = f"/api/test/{type(error).__name__}"
        served.add_api_route(path, raising(error))
        got = client.get(path)
        assert (got.status_code, got.json()) == (
            status,
            {"detail": str(error), "code": code},
        )
    got = client.get("/api/nowhere")
    assert (got.status_code, got.json()["code"]) == (404, "not_found")
    got = client.put("/api/me")
    assert (got.status_code, got.json()["code"]) == (405, "not_allowed")


@pytest.mark.slow
def test_the_api_describes_itself(client: TestClient) -> None:
    described = client.get("/api/openapi.json").json()
    assert described["info"]["title"] == "chatddx"
    assert {"/api/session", "/api/me"} <= set(described["paths"])
    schemes = described["components"]["securitySchemes"]
    assert sorted(s["type"] for s in schemes.values()) == ["apiKey", "http"]
    assert client.get("/api/docs").status_code == 200
    assert described["components"]["schemas"]["Error"]["required"] == ["detail", "code"]


@pytest.mark.parametrize(
    ("bind", "where"),
    [("127.0.0.1:9999", ("127.0.0.1", 9999)), ("[::1]:8001", ("::1", 8001))],
)
def test_chatddx_api_serves_where_it_is_told(
    db: str, monkeypatch: pytest.MonkeyPatch, bind: str, where: tuple[str, int]
) -> None:
    monkeypatch.setenv("DB_NAME", db)
    heard: list[tuple[object, str, int]] = []

    def run(served: object, host: str, port: int) -> None:
        heard.append((served, host, port))

    monkeypatch.setattr(uvicorn, "run", run)
    cli.main(["api", "--world", str(TEST), "--bind", bind])
    [(served, host, port)] = heard
    assert isinstance(served, FastAPI) and (host, port) == where

    monkeypatch.setenv("HOST", "0.0.0.0:8123")
    cli.main(["api", "--world", str(TEST)])
    assert heard[-1][1:] == ("0.0.0.0", 8123)
    with pytest.raises(SystemExit, match="bind to HOST:PORT"):
        cli.main(["api", "--world", str(TEST), "--bind", "localhost"])

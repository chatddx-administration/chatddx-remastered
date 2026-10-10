from collections.abc import Callable

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response

from chatddx import cli
from chatddx.api.people import COOKIE
from chatddx.api.schemas import Me
from chatddx.api.test.conftest import PASSWORD
from chatddx.bench import Ambiguous, NotFound
from chatddx.conftest import WORLD
from chatddx.identity import Person
from chatddx.runner.gate import Refused

pytestmark = pytest.mark.wip

ELSEWHERE = (
    {"Sec-Fetch-Site": "cross-site"},
    {"Sec-Fetch-Site": "same-site"},
    {"Origin": "https://elsewhere.example"},
    {"Sec-Fetch-Site": "cross-site", "Origin": "https://testserver"},
)


def sign_in(
    client: TestClient, login: str = "alice", password: str = PASSWORD, **headers: str
) -> Response:
    body = {"login": login, "password": password}
    return client.post("/api/session", json=body, headers=headers)


def bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_nothing_is_answered_without_a_session(client: TestClient) -> None:
    got = client.get("/api/me")
    assert got.status_code == 401
    assert got.json() == {"detail": "sign in first"}
    assert got.headers["www-authenticate"] == "Bearer"
    assert client.get("/api/me", headers=bearer("made-up")).json() == {
        "detail": "the session has ended: sign in again"
    }


def test_signing_in_gives_a_token_and_a_cookie_that_each_say_who_you_are(
    client: TestClient, alice: Person
) -> None:
    assert sign_in(client, password="wrong").status_code == 401
    assert sign_in(client, login="nobody").json() == {
        "detail": "wrong login or password"
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
            "detail": "a browser's request must come from this site's pages"
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
    assert client.get("/api/me").json() == {"detail": "sign in first"}
    assert client.get("/api/me", headers=bearer(token)).status_code == 401


def test_a_request_that_doesn_t_validate_is_refused_with_where(
    client: TestClient,
) -> None:
    got = client.post("/api/session", json={"login": "alice"})
    assert got.status_code == 422
    assert [e["loc"] for e in got.json()["detail"]] == [["body", "password"]]
    extra = {"login": "alice", "password": PASSWORD, "remember": True}
    assert client.post("/api/session", json=extra).status_code == 422


def raising(error: Exception) -> Callable[[], None]:
    def raised() -> None:
        raise error

    return raised


def test_the_bench_s_errors_and_the_gate_s_refusals_have_their_status(
    served: FastAPI, client: TestClient
) -> None:
    for error, status in (
        (NotFound("no case 'nope' for alice"), 404),
        (Ambiguous("case 'plan' names 2"), 409),
        (Refused("endpoint 'x' isn't cleared for source sample"), 422),
    ):
        path = f"/api/test/{type(error).__name__}"
        served.add_api_route(path, raising(error))
        got = client.get(path)
        assert (got.status_code, got.json()) == (status, {"detail": str(error)})


def test_the_api_describes_itself(client: TestClient) -> None:
    described = client.get("/api/openapi.json").json()
    assert described["info"]["title"] == "chatddx"
    assert {"/api/session", "/api/me"} <= set(described["paths"])
    schemes = described["components"]["securitySchemes"]
    assert sorted(s["type"] for s in schemes.values()) == ["apiKey", "http"]
    assert client.get("/api/docs").status_code == 200


@pytest.mark.parametrize(
    ("bind", "where"),
    [("127.0.0.1:9999", ("127.0.0.1", 9999)), ("[::1]:8001", ("::1", 8001))],
)
def test_chatddx_api_serves_where_it_is_told(
    monkeypatch: pytest.MonkeyPatch, bind: str, where: tuple[str, int]
) -> None:
    heard: list[tuple[object, str, int]] = []

    def run(served: object, host: str, port: int) -> None:
        heard.append((served, host, port))

    monkeypatch.setattr(uvicorn, "run", run)
    cli.main(["api", "--world", str(WORLD), "--bind", bind])
    [(served, host, port)] = heard
    assert isinstance(served, FastAPI) and (host, port) == where

    monkeypatch.setenv("HOST", "0.0.0.0:8123")
    cli.main(["api", "--world", str(WORLD)])
    assert heard[-1][1:] == ("0.0.0.0", 8123)
    with pytest.raises(SystemExit, match="bind to HOST:PORT"):
        cli.main(["api", "--world", str(WORLD), "--bind", "localhost"])

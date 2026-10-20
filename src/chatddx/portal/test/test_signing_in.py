import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.testclient import TestClient

from chatddx import cli
from chatddx.api.people import COOKIE
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.portal.app import app
from chatddx.portal.test.helpers import signing_in
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.test.world import TEST

ELSEWHERE = (
    {"Sec-Fetch-Site": "cross-site"},
    {"Origin": "https://elsewhere.example"},
)


def test_a_page_sends_whoever_isn_t_signed_in_to_sign_in_first(
    client: TestClient,
) -> None:
    got = client.get("/", params={"a": "b"})
    assert (got.status_code, got.headers["location"]) == (
        303,
        "/sign-in?next=%2F%3Fa%3Db",
    )
    form = client.get("/sign-in", params={"next": "/?a=b"})
    assert form.status_code == 200
    assert form.headers["content-type"].startswith("text/html")
    assert form.headers["cache-control"] == "no-store"
    assert 'name="next" value="/?a=b"' in form.text


@pytest.mark.slow
def test_signing_in_opens_a_session_the_api_shares(
    client: TestClient, alice: Person
) -> None:
    got = signing_in(client, next="/?a=b")
    assert (got.status_code, got.headers["location"]) == (303, "/?a=b")
    cookie = got.headers["set-cookie"]
    assert cookie.startswith(f"{COOKIE}=")
    assert {"httponly", "path=/", "samesite=lax", "secure"} <= {
        part.strip().lower() for part in cookie.split(";")
    }
    home = client.get("/")
    assert home.status_code == 200 and home.headers["cache-control"] == "no-store"
    assert alice.name in home.text and 'id="home"' in home.text
    assert client.get("/api/me").json()["login"] == "alice"
    assert client.get("/sign-in", params={"next": "/x"}).headers["location"] == "/x"


@pytest.mark.usefixtures("alice")
def test_a_wrong_password_asks_again(client: TestClient) -> None:
    got = signing_in(client, password="wrong")
    assert got.status_code == 200 and "set-cookie" not in got.headers
    assert "Wrong login or password." in got.text
    assert 'name="login" value="alice"' in got.text
    assert client.get("/").status_code == 303


@pytest.mark.usefixtures("alice")
@pytest.mark.slow
def test_signing_in_leads_only_within_the_site(client: TestClient) -> None:
    for away in (
        "//elsewhere.example/x",
        "https://elsewhere.example",
        "/\\elsewhere.example",
    ):
        assert signing_in(client, next=away).headers["location"] == "/"
        assert client.get("/sign-in", params={"next": away}).headers["location"] == "/"


@pytest.mark.usefixtures("alice")
@pytest.mark.slow
def test_a_form_from_another_site_is_refused(client: TestClient) -> None:
    for elsewhere in ELSEWHERE:
        got = signing_in(client, **elsewhere)
        assert got.status_code == 403 and "Refused" in got.text
    assert signing_in(client).status_code == 303
    for elsewhere in ELSEWHERE:
        assert client.post("/sign-out", headers=elsewhere).status_code == 403
    assert client.get("/").status_code == 200


@pytest.mark.usefixtures("alice")
@pytest.mark.slow
def test_signing_out_ends_the_session(client: TestClient) -> None:
    _ = signing_in(client)
    token = client.cookies[COOKIE]
    got = client.post("/sign-out")
    assert (got.status_code, got.headers["location"]) == (303, "/sign-in")
    assert COOKIE not in client.cookies
    assert client.get("/").status_code == 303
    gone = client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
    assert gone.status_code == 401


@pytest.mark.slow
def test_a_page_escapes_what_it_shows(
    client: TestClient, conn: Connection, alice: Person
) -> None:
    _ = People(conn).update(alice.id, name="<b>Alice</b>")
    _ = signing_in(client)
    shown = client.get("/").text
    assert "&lt;b&gt;Alice&lt;/b&gt;" in shown and "<b>Alice</b>" not in shown


@pytest.mark.slow
def test_the_portal_s_pages_aren_t_the_api_s(client: TestClient) -> None:
    described = client.get("/api/openapi.json").json()
    assert all(path.startswith("/api/") for path in described["paths"])


@pytest.mark.parametrize(("command", "worker"), [("portal", False), ("run", True)])
def test_chatddx_portal_and_run_serve_the_portal_and_the_api(
    db: str, monkeypatch: pytest.MonkeyPatch, command: str, worker: bool
) -> None:
    monkeypatch.setenv("DB_NAME", db)
    heard: list[tuple[object, str, int]] = []
    workers: list[bool] = []

    def portal(inventory: Inventory, conninfo: str, worker: bool = False) -> FastAPI:
        workers.append(worker)
        return app(inventory, conninfo, worker=worker)

    def run(served: object, host: str, port: int) -> None:
        heard.append((served, host, port))

    monkeypatch.setattr(cli, "portal", portal)
    monkeypatch.setattr(uvicorn, "run", run)
    cli.main([command, "--world", str(TEST), "--bind", "127.0.0.1:9999"])
    assert workers == [worker]
    [(served, host, port)] = heard
    assert isinstance(served, FastAPI) and (host, port) == ("127.0.0.1", 9999)
    paths = ("home", "signing_in_page", "signing_in", "signing_out", "me")
    assert [served.url_path_for(name) for name in paths] == [
        "/",
        "/sign-in",
        "/sign-in",
        "/sign-out",
        "/api/me",
    ]

import json
import socket
import threading
import time
from collections.abc import Callable, Generator
from contextlib import contextmanager
from typing import Any

import httpx2
import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response
from psycopg.conninfo import make_conninfo

from chatddx import settings
from chatddx.api.app import app
from chatddx.identity import Person
from chatddx.inventory import Inventory
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.test.helpers import PASSWORD
from chatddx.test.world import LINES

type Told = list[tuple[int | None, str, dict[str, Any]]]

# Policy: a fake this slow keeps a run's job under way while a stream asked for at once
# joins it: one asked for after it has ended is told the ledger's rows alone.
UNDER_WAY = 0.02


# Dependency: served as src/chatddx/cli.py:_serve serves the portal.
@contextmanager
def listened(served: FastAPI) -> Generator[tuple[str, uvicorn.Server]]:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        port = int(s.getsockname()[1])
    grace = int(settings.SERVE_GRACE.total_seconds())
    server = uvicorn.Server(
        uvicorn.Config(
            served,
            host="127.0.0.1",
            port=port,
            log_level="warning",
            timeout_graceful_shutdown=grace,
        )
    )
    running = threading.Thread(target=server.run, daemon=True)
    running.start()
    while not server.started:
        time.sleep(0.01)
    try:
        yield f"http://127.0.0.1:{port}", server
    finally:
        server.should_exit = True
        running.join(grace + 30)
        assert not running.is_alive(), "the server didn't stop"


def endpoint(client: TestClient, name: str) -> dict[str, Any]:
    [found] = [e for e in client.get("/api/endpoints").json() if e["name"] == name]
    return found


def thread(
    signed: TestClient, kind: str, name: str, owner: str = "alice"
) -> dict[str, Any]:
    query = {"kind": kind, "name": name, "owner": owner}
    [found] = signed.get("/api/threads", params=query).json()
    return found


def digest(signed: TestClient, kind: str, name: str) -> str:
    return thread(signed, kind, name)["head"]["digest"]


def body(signed: TestClient, found: dict[str, Any]) -> dict[str, Any]:
    return signed.get(f"/api/components/{found['head']['digest']}").json()["body"]


def family(signed: TestClient, name: str = "crlf") -> dict[str, Any]:
    [found] = signed.get("/api/families", params={"name": name}).json()
    return found


def asked(
    signed: TestClient, configuration: str = LINES, **more: Any
) -> dict[str, Any]:
    return {
        "configuration": thread(signed, "configuration", configuration)["id"],
        "families": [family(signed, "crlf")["id"]],
        "seeds": [7],
        **more,
    }


def told(text: str) -> Told:
    said: Told = []
    for block in text.strip().split("\n\n"):
        if block.startswith(":"):
            continue
        fields = dict(line.split(": ", 1) for line in block.splitlines())
        id = int(fields["id"]) if "id" in fields else None
        said.append((id, fields["event"], json.loads(fields["data"])))
    return said


def followed(signed: TestClient, run: str, **headers: str) -> Told:
    got = signed.get(f"/api/runs/{run}/events", headers=headers)
    assert got.status_code == 200, got.text
    assert got.headers["content-type"].startswith("text/event-stream")
    return told(got.text)


# Policy: the owner's queue stays paused until the stream has said its first row: by
# then it listens.
def joined(
    http: httpx2.Client, listening: str, run: str, unpause: Callable[[], None]
) -> Told:
    with http.stream("GET", f"{listening}/api/runs/{run}/events", timeout=30) as got:
        lines = got.iter_lines()
        first = next(lines)
        assert first.startswith("id: ")
        unpause()
        return told("\n".join([first, *lines]))


def sent(signed: TestClient, body: dict[str, Any]) -> tuple[dict[str, Any], Told]:
    got = signed.post("/api/runs", json=body)
    assert got.status_code == 202, got.json()
    said = followed(signed, got.json()["runs"][0]["run"])
    return signed.get(got.headers["location"]).json(), said


def names(said: Told) -> list[str]:
    return [name for _, name, _ in said]


def sign_in(
    client: TestClient, login: str = "alice", password: str = PASSWORD, **headers: str
) -> Response:
    body = {"login": login, "password": password}
    return client.post("/api/session", json=body, headers=headers)


def bearer(conn: Connection, person: Person) -> dict[str, str]:
    return {"Authorization": f"Bearer {People(conn).open_session(person.id)}"}


# Accommodating for pytest, as src/chatddx/test/helpers.py:curated_template does.
@pytest.fixture(name="served")
def world_served(db: str, world: Inventory) -> FastAPI:
    conninfo = make_conninfo(settings.database(), dbname=db)
    return app(world, conninfo, worker=True)

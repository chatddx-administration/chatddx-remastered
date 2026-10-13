import json
import subprocess
from pathlib import Path

import pytest
import uvicorn
from fastapi.testclient import TestClient

from chatddx import cli
from chatddx.api.app import app
from chatddx.core import settings
from chatddx.facts import BUNDLED, Facts
from chatddx.inventory import Inventory
from chatddx.portal.assets import MANIFEST, Assets
from chatddx.portal.test.test_signing_in import signing_in
from chatddx.test.world import TEST

pytestmark = pytest.mark.wip

FRONTEND = settings.PROJECT_ROOT / "frontend"


def build(root: Path) -> None:
    (root / MANIFEST).parent.mkdir(parents=True)
    _ = (root / MANIFEST).write_text(
        json.dumps(
            {
                "src/portal.css": {"file": "assets/portal-1.css", "isEntry": True},
                "src/islands/home.ts": {
                    "file": "assets/home-2.js",
                    "isEntry": True,
                    "css": ["assets/home-3.css"],
                    "imports": ["_shared-4.js"],
                },
                "_shared-4.js": {
                    "file": "assets/shared-4.js",
                    "css": ["assets/shared-5.css"],
                },
            }
        )
    )
    (root / "assets").mkdir()
    _ = (root / "assets" / "portal-1.css").write_text("body {}")


def test_the_built_frontend_is_found_by_its_manifest(tmp_path: Path) -> None:
    assets = Assets(tmp_path)
    assert not assets.built and assets.styles() == []
    assert assets.island("home").scripts == []
    build(tmp_path)
    assert assets.built and assets.styles() == ["/static/assets/portal-1.css"]
    island = assets.island("home")
    assert island.scripts == ["/static/assets/home-2.js"]
    assert island.styles == ["/static/assets/home-3.css", "/static/assets/shared-5.css"]
    assert island.preloads == ["/static/assets/shared-4.js"]
    assert assets.island("nowhere").scripts == []


@pytest.mark.usefixtures("alice")
def test_a_page_takes_the_built_styles_and_its_island(
    client: TestClient, built: Path
) -> None:
    _ = signing_in(client)
    unbuilt = client.get("/").text
    assert "isn't built" in unbuilt and "<script" not in unbuilt
    build(built)
    home = client.get("/").text
    assert '<link rel="stylesheet" href="/static/assets/portal-1.css">' in home
    assert '<script type="module" src="/static/assets/home-2.js"></script>' in home
    assert '<link rel="modulepreload" href="/static/assets/shared-4.js">' in home
    assert "isn't built" not in home
    signed_out = client.post("/sign-out")
    assert signed_out.status_code == 303
    form = client.get("/sign-in").text
    assert "/static/assets/portal-1.css" in form and "<script" not in form
    assert client.get("/static/assets/portal-1.css").text == "body {}"


@pytest.mark.slow
def test_the_frontend_s_openapi_document_is_the_api_s() -> None:
    kept = json.loads((FRONTEND / "openapi.json").read_text())
    assert kept == app(Inventory(), Facts.load(BUNDLED), "").openapi(), (
        "chatddx openapi > frontend/openapi.json"
    )


def test_chatddx_portal_watch_builds_the_frontend_while_it_serves(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ran: list[list[str]] = []

    class Watching:
        def __init__(self, argv: list[str]) -> None:
            ran.append(argv)

        def terminate(self) -> None:
            ran.append(["terminated"])

        def wait(self) -> int:
            return 0

    def run(argv: list[str], check: bool) -> None:
        assert check
        ran.append(argv)

    monkeypatch.setattr(subprocess, "run", run)
    monkeypatch.setattr(subprocess, "Popen", Watching)

    def serve(served: object, host: str, port: int) -> None:
        ran.append([type(served).__name__, host, str(port)])

    monkeypatch.setattr(uvicorn, "run", serve)
    cli.main(["portal", "--world", str(TEST), "--watch", "--bind", "127.0.0.1:9999"])
    frontend = str(FRONTEND)
    assert ran == [
        ["pnpm", "--dir", frontend, "install", "--frozen-lockfile"],
        ["pnpm", "--dir", frontend, "run", "watch"],
        ["FastAPI", "127.0.0.1", "9999"],
        ["terminated"],
    ]

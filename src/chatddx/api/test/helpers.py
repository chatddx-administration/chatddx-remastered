from typing import Any

from fastapi.testclient import TestClient


def endpoint(client: TestClient, name: str) -> dict[str, Any]:
    [found] = [e for e in client.get("/api/endpoints").json() if e["name"] == name]
    return found

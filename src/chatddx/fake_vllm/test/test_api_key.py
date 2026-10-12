import json
import urllib.error
import urllib.request

import pytest

from chatddx.fake_vllm.served import Refused, Served
from chatddx.fake_vllm.server import serving

pytestmark = pytest.mark.wip

QWEN = "Qwen/Qwen3-8B-AWQ"


def status(url: str, key: str | None = None, body: bytes | None = None) -> int:
    request = urllib.request.Request(url, data=body)
    if key is not None:
        request.add_header("Authorization", f"Bearer {key}")
    if body is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(request) as response:
            return int(response.status)
    except urllib.error.HTTPError as e:
        if e.code == 401:
            assert json.loads(e.read()) == {"error": "Unauthorized"}
        return e.code


def test_with_an_api_key_it_asks_for_a_key_as_a_bearer_on_v1_only() -> None:
    served = Served.of(QWEN, ["--api-key", "one", "two"])
    chat = json.dumps(
        {"model": QWEN, "messages": [{"role": "user", "content": "a cough"}]}
    ).encode()

    with serving([served], "127.0.0.1", 0) as (host, port):
        base = f"http://{host}:{port}"
        assert status(f"{base}/v1/models") == 401
        assert status(f"{base}/v1/models", "three") == 401
        assert status(f"{base}/v1/models", "two") == 200
        assert status(f"{base}/v1/chat/completions", None, chat) == 401
        assert status(f"{base}/v1/chat/completions", "one", chat) == 200
        assert status(f"{base}/health") == 200


def test_an_api_key_takes_a_key() -> None:
    with pytest.raises(Refused, match="--api-key takes a key or more"):
        _ = Served.of(QWEN, ["--api-key", "--port", "1"])

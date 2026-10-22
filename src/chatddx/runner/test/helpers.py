import json
import threading
import urllib.request
from collections.abc import Generator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, override

from psycopg import sql

from chatddx.curation import Plan
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.trial import Trial, replicates
from chatddx.fake_vllm.served import Served
from chatddx.inventory import DirectorySource
from chatddx.test.helpers import connect
from chatddx.test.world import (
    LINES,
    QWEN,
    TEST,
)

# Policy: slow enough that calls sent together overlap: a fake answer is some 40 tokens.
DELAY = 0.002
SERVED = Served.of(
    "Qwen/Qwen3-8B-AWQ",
    [
        "--served-model-name",
        "sha256:abc",
        "--reasoning-parser",
        "qwen3",
        "--enable-auto-tool-choice",
        "--tool-call-parser",
        "hermes",
    ],
)
CASES = ("crlf", "svenska")


def trial(
    plan: Plan,
    skeleton: str = LINES,
    cases: tuple[str, ...] = CASES,
    seeds: tuple[int, ...] = (7, 8),
    engine: str = QWEN,
) -> Trial:
    source = DirectorySource(name="test", path=TEST / "vignettes")
    refs = [plan.registry.add(c) for c in source.cases() if c.vignette.id in cases]
    held = resolve(plan.registry.get, plan.named("recipe", skeleton).digest, Skeleton)
    made = Trial(
        skeleton=held.digest,
        engine=plan.named("local_engine", engine).digest,
        cases=tuple(refs),
        seeds=replicates(held, seeds),
    )
    _ = plan.registry.add(made)
    return made


def rows(db: str, table: str) -> int:
    query = sql.SQL("SELECT count(*) FROM ledger.{}").format(sql.Identifier(table))
    with connect(db) as c:
        row = c.execute(query).fetchone()
    assert row is not None
    return int(row[0])


def body(**fields: Any) -> dict[str, Any]:
    return {
        "model": "sha256:abc",
        "messages": [{"role": "user", "content": "a cough"}],
        "temperature": 0.6,
        "seed": 7,
        "return_token_ids": True,
    } | fields


@contextmanager
def going_away(chunked: bool) -> Generator[str]:
    handler = type("Handler", (_GoingAway,), {"chunked": chunked})
    with ThreadingHTTPServer(("127.0.0.1", 0), handler) as server:
        thread = threading.Thread(target=server.serve_forever, args=(0.01,))
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_address[1]}/v1/"
        finally:
            server.shutdown()
            thread.join()


def whole(url: str, request: dict[str, Any]) -> dict[str, Any]:
    sent = urllib.request.Request(
        url + "chat/completions",
        data=json.dumps(request).encode(),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(sent) as response:
        return json.loads(response.read())


# Accommodating for vLLM, which streams over HTTP/1.1 in chunks, and the fake, over
# HTTP/1.0 until it closes: an engine that goes away mid-stream ends the stream either
# way.
class _GoingAway(BaseHTTPRequestHandler):
    protocol_version: str = "HTTP/1.1"
    chunked: bool = False

    def do_POST(self) -> None:
        _ = self.rfile.read(int(self.headers["Content-Length"]))
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        if self.chunked:
            self.send_header("Transfer-Encoding", "chunked")
        self.send_header("Connection", "close")
        self.end_headers()
        data = b'data: {"choices": [{"index": 0, "delta": {"content": "Fake"}}]}\n\n'
        if self.chunked:
            data = b"%x\r\n%s\r\n" % (len(data), data)
        _ = self.wfile.write(data)

    @override
    def log_message(self, format: str, *args: Any) -> None:
        pass

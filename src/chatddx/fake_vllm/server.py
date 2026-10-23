import json
import logging
import select
import socket
import threading
import time
from collections.abc import Generator, Sequence
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, cast, override

from .chat import Failure, Reply, accept, completion, respond, scripted, stream
from .script import Script
from .served import VERSION, Refused, Served

_LOG = logging.getLogger(__name__)


def models(served: Sequence[Served]) -> dict[str, Any]:
    created = int(time.time())
    return {
        "object": "list",
        "data": [
            {
                "id": name,
                "object": "model",
                "created": created,
                "owned_by": "vllm",
                "root": s.model,
                "parent": None,
                "max_model_len": s.max_model_len,
                "permission": [],
            }
            for s in served
            for name in s.names
        ],
    }


def got(served: Sequence[Served], path: str) -> tuple[int, Any]:
    match path.partition("?")[0].rstrip("/"):
        case "/v1/models":
            return 200, models(served)
        case "/version":
            return 200, {"version": VERSION}
        case "/health":
            return 200, None
        case _:
            return 404, {"detail": "Not Found"}


def _request(served: Sequence[Served], raw: bytes) -> tuple[Served, dict[str, Any]]:
    try:
        body: Any = json.loads(raw)
    except ValueError as e:
        raise Failure(f"the request body isn't JSON: {e}") from None
    if not isinstance(body, dict):
        raise Failure("the request body isn't a JSON object")
    request = cast(dict[str, Any], body)
    return accept(served, request), request


class _Handler(BaseHTTPRequestHandler):
    served: tuple[Served, ...] = ()
    delay: float = 0.0
    runaway: bool = False
    script: Script | None = None

    def do_GET(self) -> None:
        if self._authorized():
            self._json(*got(self.served, self.path))

    def do_POST(self) -> None:
        if not self._authorized():
            return
        if self.path.partition("?")[0].rstrip("/") != "/v1/chat/completions":
            self._json(404, {"detail": "Not Found"})
            return
        length = int(self.headers.get("Content-Length", 0))
        try:
            served, body = _request(self.served, self.rfile.read(length))
            reply = self._reply(served, body)
        except Failure as f:
            self._json(f.status, f.body())
            return
        if not body.get("stream"):
            if reply.hang_up is not None:
                self.log_message("went away, as the script says, before answering")
                return
            self._json(200, completion(served, body, reply))
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        sent = 0
        for i, (event, generated) in enumerate(stream(served, body, reply)):
            if i and reply.hang_up is not None and sent >= reply.hang_up:
                self.log_message("went away, as the script says, after %d tokens", sent)
                return
            if (i and not self._next_token()) or not self._sent(event.encode()):
                self.log_message("aborted: the client hung up after %d tokens", sent)
                return
            sent = generated

    def _reply(self, served: Served, body: dict[str, Any]) -> Reply:
        if self.script is None:
            return respond(served, body, self.runaway)
        held = self.script.next()
        if held is None:
            raise Failure(
                "the script has no turn left for this request",
                "InternalServerError",
                500,
            )
        n, turn = held
        self.log_message("turn %d of %d of the script", n, len(self.script.turns))
        if turn.status is not None:
            raise Failure(
                turn.content or f"the script answers {turn.status}",
                "InternalServerError" if turn.status >= 500 else "BadRequestError",
                turn.status,
            )
        return scripted(served, body, turn)

    # Accommodating for vLLM, which with --api-key asks for one of its keys as a bearer
    # on /v1 only, so /health and /version answer anyone.
    def _authorized(self) -> bool:
        keys = {key for s in self.served for key in s.api_keys}
        if not keys or not self.path.startswith("/v1"):
            return True
        scheme, _, key = (self.headers.get("Authorization") or "").partition(" ")
        if scheme.lower() == "bearer" and key in keys:
            return True
        self._json(401, {"error": "Unauthorized"})
        return False

    # Accommodating for vLLM, which hears a hang-up from the socket while it waits for
    # the next token, rather than at the next write.
    def _next_token(self) -> bool:
        ready, _, _ = select.select([self.connection], [], [], self.delay)
        if not ready:
            return True
        try:
            return self.connection.recv(1, socket.MSG_PEEK) != b""
        except OSError:
            return False

    def _sent(self, data: bytes) -> bool:
        try:
            _ = self.wfile.write(data)
            self.wfile.flush()
        except OSError:
            return False
        return True

    # Policy: logged, not written to stderr: a request's thread can outlive its client,
    # so what it logs goes to whoever listens then; `run` prints it.
    @override
    def log_message(self, format: str, *args: Any) -> None:
        _LOG.info(
            "%s - - [%s] %s",
            self.address_string(),
            self.log_date_time_string(),
            format % args,
        )

    def _json(self, status: int, body: Any) -> None:
        content = b"" if body is None else json.dumps(body).encode()
        self.send_response(status)
        if body is not None:
            self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        _ = self.wfile.write(content)


def server(
    served: Sequence[Served],
    host: str | None = None,
    port: int | None = None,
    delay: float = 0.0,
    runaway: bool = False,
    script: Script | None = None,
) -> ThreadingHTTPServer:
    if not served:
        raise ValueError("the fake vLLM needs a model to serve")
    handler = type(
        "Handler",
        (_Handler,),
        {
            "served": tuple(served),
            "delay": delay,
            "runaway": runaway,
            "script": script,
        },
    )
    address = (
        served[0].host if host is None else host,
        served[0].port if port is None else port,
    )
    return ThreadingHTTPServer(address, handler)


@contextmanager
def serving(
    served: Sequence[Served],
    host: str | None = None,
    port: int | None = None,
    delay: float = 0.0,
    runaway: bool = False,
    script: Script | None = None,
) -> Generator[tuple[str, int]]:
    fake = server(served, host, port, delay, runaway, script)
    thread = threading.Thread(
        target=fake.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
    )
    thread.start()
    try:
        yield str(fake.server_address[0]), int(fake.server_address[1])
    finally:
        fake.shutdown()
        fake.server_close()


def run(
    model: str,
    argv: Sequence[str],
    delay: float,
    runaway: bool,
    script: Script | None = None,
) -> None:
    try:
        served = Served.of(model, argv)
    except Refused as e:
        raise SystemExit(f"the fake vLLM won't start: {e}") from None
    run_all([served], delay, runaway, script)


def run_all(
    served: Sequence[Served],
    delay: float,
    runaway: bool,
    script: Script | None = None,
) -> None:
    fakes = [server([s], delay=delay, runaway=runaway, script=script) for s in served]
    printed = logging.StreamHandler()
    _LOG.addHandler(printed)
    _LOG.setLevel(logging.INFO)
    for s, fake in zip(served, fakes, strict=True):
        host, port = fake.server_address[:2]
        names = ", ".join(s.names)
        print(
            f"the fake vLLM {VERSION}, serving {s.model} as {names} "
            + f"at http://{host!s}:{port}/v1"
        )
    first, *others = fakes
    for fake in others:
        threading.Thread(
            target=fake.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
        ).start()
    try:
        first.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        for fake in others:
            fake.shutdown()
        for fake in fakes:
            fake.server_close()
        _LOG.removeHandler(printed)
        _LOG.setLevel(logging.NOTSET)

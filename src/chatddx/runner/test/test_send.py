import json
import logging
import socket
import threading
import time
from collections.abc import Iterator
from datetime import UTC, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, cast, override

import pytest

from chatddx.factors.base import Fingerprint, canonical_bytes
from chatddx.factors.trial import Execution
from chatddx.fake_vllm.chat import ANSWER
from chatddx.fake_vllm.server import serving
from chatddx.ledger import fingerprint_request
from chatddx.runner.send import STOPPED, Delta, Halt, Stopped, send
from chatddx.runner.test.helpers import SERVED, body, going_away, whole


def at(host: str, port: int) -> str:
    return f"http://{host}:{port}/v1/"


@pytest.fixture
def url() -> Iterator[str]:
    with serving([SERVED], "127.0.0.1", 0) as address:
        yield at(*address)


def choice(response: dict[str, Any] | None) -> Any:
    assert response is not None
    return response["choices"][0]


def content(response: dict[str, Any] | None) -> str:
    return choice(response)["message"]["content"]


def test_a_call_records_the_body_s_fingerprint_and_the_answer_without_the_prompt(
    url: str,
) -> None:
    deltas: list[Delta] = []
    call = send(url, body(), on_delta=deltas.append)
    assert call.request == fingerprint_request(body())
    assert (call.status, call.error) == (200, None)
    [attempt] = call.attempts
    assert (attempt.status, attempt.error) == (200, None)
    assert call.started_at <= attempt.started_at <= attempt.finished_at
    assert attempt.finished_at <= call.finished_at
    assert call.response is not None and "prompt_token_ids" not in call.response
    ids = whole(url, body())["prompt_token_ids"]
    assert call.prompt_tokens == Fingerprint.of(canonical_bytes(ids))
    assert call.returned_model == "sha256:abc"
    assert (
        content(call.response) == "Fake diagnosis B\nFake diagnosis C\nFake diagnosis A"
    )
    kinds = [d.kind for d in deltas]
    assert kinds == sorted(kinds, key=["reasoning", "content"].index)
    assert [d.tokens for d in deltas] == list(range(1, len(deltas) + 1))
    assert deltas[-1].tokens == cast(Any, call.response)["usage"]["completion_tokens"]


class _BothReasonings(BaseHTTPRequestHandler):
    protocol_version: str = "HTTP/1.1"

    def do_POST(self) -> None:
        _ = self.rfile.read(int(self.headers["Content-Length"]))
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Connection", "close")
        self.end_headers()
        for delta in (
            {"reasoning": "Hm.", "reasoning_content": "Hm."},
            {"content": "ACS"},
        ):
            chunk = {"choices": [{"index": 0, "delta": delta}]}
            _ = self.wfile.write(b"data: %s\n\n" % json.dumps(chunk).encode())
        _ = self.wfile.write(b"data: [DONE]\n\n")

    @override
    def log_message(self, format: str, *args: Any) -> None:
        pass


def test_reasoning_under_both_names_streams_once() -> None:
    deltas: list[Delta] = []
    with ThreadingHTTPServer(("127.0.0.1", 0), _BothReasonings) as server:
        thread = threading.Thread(target=server.serve_forever, args=(0.01,))
        thread.start()
        try:
            url = f"http://127.0.0.1:{server.server_address[1]}/v1/"
            call = send(url, body(), on_delta=deltas.append)
        finally:
            server.shutdown()
            thread.join()
    assert call.status == 200
    assert [(d.kind, d.text) for d in deltas] == [
        ("reasoning", "Hm."),
        ("content", "ACS"),
    ]


def test_a_runaway_is_cut_short_and_what_came_is_kept(
    caplog: pytest.LogCaptureFixture,
) -> None:
    caplog.set_level(logging.INFO, "chatddx.fake_vllm.server")
    with serving([SERVED], "127.0.0.1", 0, runaway=True) as address:
        call = send(at(*address), body(temperature=0))
        cut = send(
            at(*address), body(temperature=0), execution=Execution(whitespace_limit=5)
        )
        let_run = send(
            at(*address),
            body(temperature=0, max_tokens=150),
            execution=Execution(whitespace_limit=None),
        )
    assert call.error == "stopped: nothing but whitespace for 100 tokens"
    assert content(call.response) == ANSWER + "\n" * 100
    assert choice(call.response)["finish_reason"] is None
    assert cut.error == "stopped: nothing but whitespace for 5 tokens"
    assert let_run.error is None
    assert choice(let_run.response)["finish_reason"] == "length"
    assert "aborted: the client hung up" in caplog.text


def test_an_interrupt_mid_stream_records_what_came_as_stopped(url: str) -> None:
    seen: list[Delta] = []

    def interrupt(delta: Delta) -> None:
        seen.append(delta)
        if len(seen) == 3:
            raise KeyboardInterrupt

    with pytest.raises(Stopped) as caught:
        _ = send(url, body(), on_delta=interrupt)
    call = caught.value.call
    assert (call.error, call.status) == (STOPPED, 200)
    assert call.prompt_tokens is not None
    message = choice(call.response)["message"]
    assert message["reasoning"] == "".join(d.text for d in seen)


def test_a_halt_hangs_up_mid_stream_and_keeps_what_came(url: str) -> None:
    halt = Halt()
    seen: list[Delta] = []

    def halting(delta: Delta) -> None:
        seen.append(delta)
        if len(seen) == 3:
            halt.set()

    with pytest.raises(Stopped) as caught:
        _ = send(url, body(), on_delta=halting, halt=halt)
    call = caught.value.call
    assert (call.error, call.status) == (STOPPED, 200)
    assert call.prompt_tokens is not None
    assert choice(call.response)["message"]["reasoning"] == "".join(
        d.text for d in seen
    )


def test_a_halt_from_another_thread_ends_a_stalled_stream() -> None:
    halt = Halt()
    with serving([SERVED], "127.0.0.1", 0, delay=5.0) as address:
        threading.Timer(0.1, halt.set).start()
        began = time.monotonic()
        with pytest.raises(Stopped) as caught:
            _ = send(at(*address), body(), halt=halt)
        assert time.monotonic() - began < 2
    call = caught.value.call
    assert (call.error, call.status) == (STOPPED, 200)
    assert choice(call.response)["message"]["role"] == "assistant"


@pytest.mark.parametrize("chunked", [False, True], ids=["closed", "chunked"])
def test_a_stream_the_engine_leaves_is_an_error_that_keeps_what_came(
    chunked: bool,
) -> None:
    with going_away(chunked) as url:
        call = send(url, body())
    assert call.error == "Unfinished: the stream ended before [DONE]"
    assert content(call.response) == "Fake"
    assert choice(call.response)["finish_reason"] is None


def test_a_halt_ends_the_wait_between_attempts() -> None:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        closed = at("127.0.0.1", s.getsockname()[1])
    halt = Halt()
    threading.Timer(0.1, halt.set).start()
    began = time.monotonic()
    with pytest.raises(Stopped) as caught:
        _ = send(closed, body(), execution=Execution(retries=3), backoff=30, halt=halt)
    assert time.monotonic() - began < 10
    call = caught.value.call
    assert (call.error, call.status) == (STOPPED, None)
    [attempt] = call.attempts
    assert attempt.error is not None and "Connection refused" in attempt.error


def test_a_call_counts_from_when_the_caller_says_it_was_sent(url: str) -> None:
    sent = datetime.now(UTC) - timedelta(seconds=1)
    assert send(url, body(), started_at=sent).started_at == sent


def test_only_a_call_that_got_no_answer_is_tried_again(url: str) -> None:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        closed = at("127.0.0.1", s.getsockname()[1])
    refused = send(closed, body(), execution=Execution(retries=2), backoff=0)
    assert len(refused.attempts) == 3
    assert all(
        a.error is not None and "Connection refused" in a.error
        for a in refused.attempts
    )
    times = [t for a in refused.attempts for t in (a.started_at, a.finished_at)]
    assert times == sorted(times)
    assert refused.status is None and refused.response is None
    assert refused.error is not None and "Connection refused" in refused.error

    rejected = send(url, body(model="sha256:other"), execution=Execution(retries=2))
    [attempt] = rejected.attempts
    assert (attempt.status, rejected.status) == (404, 404)
    assert rejected.response is not None and "error" in rejected.response
    assert rejected.error is not None and rejected.error.startswith("HTTP 404: ")


def test_a_call_past_its_timeout_is_cut_short() -> None:
    with serving([SERVED], "127.0.0.1", 0, delay=0.02) as address:
        call = send(at(*address), body(), execution=Execution(timeout_s=0.1))
    assert call.error == "stopped: no end after 0.1 s"
    [attempt] = call.attempts
    assert attempt.error == call.error
    assert choice(call.response)["finish_reason"] is None

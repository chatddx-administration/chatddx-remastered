import hashlib
import json
from collections.abc import Generator
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from typing import override
from urllib.error import HTTPError

import pytest
from pydantic import HttpUrl, ValidationError

from chatddx.factors.bundle import Registry
from chatddx.factors.engine import (
    FileDigest,
    Hardware,
    LocalEngine,
    LocalModel,
    Runtime,
)
from chatddx.factors.test.sample import remote_engine
from chatddx.fake_vllm.served import Served
from chatddx.fake_vllm.server import serving
from chatddx.inventory import (
    DirectorySource,
    EndpointSpec,
    HostSpec,
    Inventory,
    check,
    confirm,
    served,
    start_up,
    url_at,
)
from chatddx.test.world import GPT_OSS, QWEN, free_world, world_plan

TEMPLATE = hashlib.sha256(b"{{ messages }}").hexdigest()


def local(reg: Registry, *argv: str) -> tuple[str, str]:
    model = reg.add(
        LocalModel(
            repo="Qwen/Qwen3-8B-AWQ",
            revision="d" * 40,
            files=(FileDigest(path="model.safetensors", sha256="a" * 64),),
        )
    )
    engine = reg.add(
        LocalEngine(
            hardware=Hardware(
                gpu="NVIDIA GeForce RTX 3070",
                compute_capability=(8, 6),
                vram_mib=8192,
                driver="580.95.05",
            ),
            runtime=Runtime(
                version="0.24.0", closure="/nix/store/" + "v" * 32 + "-vllm"
            ),
            model=model,
            chat_template=TEMPLATE,
            argv=argv,
        )
    )
    return model, engine


def world(
    engine: str,
    models: dict[str, str] | None = None,
    templates: dict[str, str] | None = None,
) -> Inventory:
    return Inventory(
        endpoints={
            "qwen@pelle": EndpointSpec.model_validate(
                {"engine": engine, "url": "http://pelle.km:12009/v1/", "host": "pelle"}
            )
        },
        hosts={
            "pelle": HostSpec(bind="::", models=models or {}, templates=templates or {})
        },
    )


def test_endpoints_and_hosts_are_declared_in_the_inventory(tmp_path: Path) -> None:
    path = tmp_path / "inventory.toml"
    _ = path.write_text(
        '[endpoint.qwen]\nengine = "sha256:'
        + "c" * 64
        + '"\n'
        + 'url = "http://pelle.km:12009/v1/"\nhost = "pelle"\n\n[host.pelle]\n'
    )
    inventory = Inventory.load(path)
    endpoint = inventory.endpoint("qwen")
    assert (endpoint.max_jobs, endpoint.credential, str(endpoint.url)) == (
        1,
        None,
        "http://pelle.km:12009/v1/",
    )
    assert inventory.hosts["pelle"] == HostSpec(bind="0.0.0.0")
    with pytest.raises(LookupError, match="no endpoint 'other'"):
        _ = inventory.endpoint("other")
    _ = path.write_text(
        '[endpoint.qwen]\nengine = "sha256:' + "c" * 64 + '"\nhost = "x"\n'
    )
    with pytest.raises(ValidationError, match="names no host 'x'"):
        _ = Inventory.load(path)


def test_an_inventory_includes_the_endpoints_and_hosts_of_other_files(
    tmp_path: Path,
) -> None:
    engine = "sha256:" + "c" * 64
    _ = (tmp_path / "imported.toml").write_text(
        f'[endpoint.qwen]\nengine = "{engine}"\nurl = "http://pelle.km:12009/v1/"\n'
        + 'host = "pelle"\n\n[host.pelle]\nbind = "::"\n'
    )
    path = tmp_path / "inventory.toml"
    _ = path.write_text(
        'include = ["imported.toml"]\n\n[source.sample]\npath = "vignettes"\n'
    )
    inventory = Inventory.load(path)
    assert (inventory.endpoint("qwen").engine, inventory.hosts["pelle"].bind) == (
        engine,
        "::",
    )
    assert inventory.sources["sample"] == DirectorySource(
        name="sample", path=(tmp_path / "vignettes").resolve()
    )
    _ = path.write_text('include = ["imported.toml"]\n\n[host.pelle]\n')
    with pytest.raises(ValueError, match=r"host \['pelle'\] are in .*inventory.toml"):
        _ = Inventory.load(path)
    _ = (tmp_path / "imported.toml").write_text('[source.other]\npath = "x"\n')
    with pytest.raises(ValueError, match="has only 'endpoint' and 'host' tables"):
        _ = Inventory.load(path)


def test_an_inventory_says_which_sources_an_endpoint_is_cleared_for(
    tmp_path: Path,
) -> None:
    engine = "sha256:" + "c" * 64
    imported = tmp_path / "imported.toml"
    _ = imported.write_text(
        f'[endpoint.qwen]\nengine = "{engine}"\nurl = "http://pelle.km:12009/v1/"\n'
    )
    path = tmp_path / "inventory.toml"
    sources = '[source.sample]\npath = "a"\n\n[source.registry]\npath = "b"\n\n'
    _ = path.write_text(
        f'include = ["imported.toml"]\n\n{sources}[cleared]\nqwen = ["sample"]\n'
    )
    inventory = Inventory.load(path)
    assert inventory.cleared_for("qwen") == {"sample"}
    assert inventory.cleared_for("other") == frozenset()
    _ = path.write_text(f'include = ["imported.toml"]\n\n{sources}')
    assert Inventory.load(path).cleared_for("qwen") == frozenset()
    _ = path.write_text(f'{sources}[cleared]\nqwen = ["sample"]\n')
    with pytest.raises(ValidationError, match="cleared names no endpoint 'qwen'"):
        _ = Inventory.load(path)
    _ = path.write_text(
        f'include = ["imported.toml"]\n\n{sources}[cleared]\nqwen = ["other"]\n'
    )
    with pytest.raises(ValidationError, match="'qwen' is cleared for no source other"):
        _ = Inventory.load(path)
    _ = imported.write_text(imported.read_text() + '\n[cleared]\nqwen = ["sample"]\n')
    _ = path.write_text(f'include = ["imported.toml"]\n\n{sources}')
    with pytest.raises(ValueError, match="has only 'endpoint' and 'host' tables"):
        _ = Inventory.load(path)


def test_an_inventory_binds_each_judge_to_an_endpoint(tmp_path: Path) -> None:
    engine = "sha256:" + "c" * 64
    imported = tmp_path / "imported.toml"
    _ = imported.write_text(
        f'[endpoint.qwen]\nengine = "{engine}"\nurl = "http://pelle.km:12009/v1/"\n'
    )
    path = tmp_path / "inventory.toml"
    _ = path.write_text('include = ["imported.toml"]\n\n[judge]\nverdict = "qwen"\n')
    assert Inventory.load(path).judges == {"verdict": "qwen"}
    _ = path.write_text('include = ["imported.toml"]\n\n[judge]\nverdict = "other"\n')
    with pytest.raises(
        ValidationError, match="judge 'verdict' is bound to no endpoint 'other'"
    ):
        _ = Inventory.load(path)
    _ = imported.write_text(imported.read_text() + '\n[judge]\nverdict = "qwen"\n')
    _ = path.write_text('include = ["imported.toml"]\n')
    with pytest.raises(ValueError, match="has only 'endpoint' and 'host' tables"):
        _ = Inventory.load(path)


def test_a_start_up_joins_the_engine_with_where_its_host_keeps_things() -> None:
    reg = Registry()
    model, engine = local(reg, "--max-model-len", "8192")
    inventory = world(engine, {model: "/models/qwen3"}, {TEMPLATE: "/etc/qwen3.jinja"})
    startup = start_up(inventory, reg.get, "qwen@pelle")
    assert startup.argv == (
        "/models/qwen3",
        "--revision",
        "d" * 40,
        "--served-model-name",
        engine,
        "--chat-template",
        "/etc/qwen3.jinja",
        "--host",
        "::",
        "--port",
        "12009",
        "--max-model-len",
        "8192",
    )
    assert startup.closure == "/nix/store/" + "v" * 32 + "-vllm"
    assert url_at(inventory, reg.get, "qwen@pelle") == "http://pelle.km:12009/v1/"


def test_a_start_up_is_refused_where_the_inventory_or_the_engine_falls_short() -> None:
    reg = Registry()
    model, engine = local(reg)
    with pytest.raises(LookupError, match="where it keeps model"):
        _ = start_up(world(engine, templates={TEMPLATE: "/t"}), reg.get, "qwen@pelle")
    with pytest.raises(LookupError, match="where it keeps chat template"):
        _ = start_up(world(engine, models={model: "/m"}), reg.get, "qwen@pelle")
    _, listening = local(reg, "--port=9000")
    complete = world(listening, {model: "/m"}, {TEMPLATE: "/t"})
    with pytest.raises(LookupError, match="sets --port in its argv"):
        _ = start_up(complete, reg.get, "qwen@pelle")
    remote = reg.add(remote_engine(reg, "gemma"))
    with pytest.raises(LookupError, match="engine.remote, not ours to start"):
        _ = start_up(world(remote), reg.get, "qwen@pelle")
    unknown = world("sha256:" + "c" * 64, {model: "/m"}, {TEMPLATE: "/t"})
    for f in (start_up, url_at, confirm):
        with pytest.raises(LookupError, match="'qwen@pelle': sha256:c+ is not in the"):
            _ = f(unknown, reg.get, "qwen@pelle")


def test_a_check_finds_what_starting_or_reaching_each_endpoint_would_refuse() -> None:
    reg = Registry()
    model, engine = local(reg)
    _, listening = local(reg, "--port=9000")
    remote = reg.add(remote_engine(reg, "gemma"))
    url = "http://pelle.km:12009/v1/"
    pelle = HostSpec(models={model: "/m", "sha256:" + "e" * 64: "/old"})
    inventory = Inventory.model_validate(
        {
            "sources": {"sample": {"name": "sample", "path": "/v", "sensitive": False}},
            "endpoints": {
                "qwen@pelle": {"engine": engine, "url": url, "host": "pelle"},
                "again@pelle": {"engine": engine, "url": url, "host": "pelle"},
                "nowhere@pelle": {"engine": engine, "host": "pelle"},
                "listening@pelle": {
                    "engine": listening,
                    "url": "http://pelle.km:12010/v1/",
                    "host": "pelle",
                },
                "gemma": {
                    "engine": remote,
                    "url": "https://api.example.org/v1/",
                    "host": "pelle",
                },
                "ghost": {"engine": "sha256:" + "c" * 64},
                "model": {"engine": model},
            },
            "hosts": {"pelle": pelle},
            "cleared": {"gemma": ["sample"]},
        }
    )
    assert [(f.subject, f.code, f.level) for f in check(inventory, reg.get)] == [
        ("qwen@pelle", "endpoint.unstartable", "warning"),
        ("again@pelle", "endpoint.unstartable", "warning"),
        ("nowhere@pelle", "endpoint.unreachable", "warning"),
        ("listening@pelle", "endpoint.unstartable", "warning"),
        ("gemma", "endpoint.remote_host", "warning"),
        ("ghost", "endpoint.engine_unknown", "warning"),
        ("model", "endpoint.not_engine", "warning"),
        ("again@pelle", "endpoint.shared_url", "warning"),
        ("pelle", "host.unpinned", "info"),
        ("gemma", "cleared.not_sensitive", "info"),
    ]
    messages = {(f.subject, f.code): f.message for f in check(inventory, reg.get)}
    assert messages[("qwen@pelle", "endpoint.unstartable")] == (
        f"host 'pelle' doesn't say where it keeps chat template {TEMPLATE}"
    )
    assert messages[("again@pelle", "endpoint.shared_url")] == (
        f"{url} is also the address of endpoint 'qwen@pelle'"
    )
    assert messages[("pelle", "host.unpinned")] == (
        f"it says where it keeps model sha256:{'e' * 64}, which none of its "
        + "endpoints' engines pins"
    )
    assert messages[("ghost", "endpoint.engine_unknown")] == (
        f"sha256:{'c' * 64} is not in the registry"
    )


def test_a_remote_engine_is_reached_at_its_endpoint_s_url() -> None:
    reg = Registry()
    remote = reg.add(remote_engine(reg, "gemma"))
    at = HttpUrl("https://api.example.org/v1/")
    alone = Inventory(
        endpoints={"gemma": EndpointSpec(engine=remote, url=at, credential="KEY")},
    )
    assert url_at(alone, reg.get, "gemma") == "https://api.example.org/v1/"
    unplaced = Inventory(endpoints={"gemma": EndpointSpec(engine=remote)})
    with pytest.raises(LookupError, match="serves a remote engine but has no url"):
        _ = url_at(unplaced, reg.get, "gemma")


def test_a_fake_started_from_an_endpoint_serves_its_engine() -> None:
    inventory = free_world()
    plan = world_plan()
    at = inventory.endpoint(GPT_OSS).model_copy(
        update={"url": inventory.endpoint(QWEN).url}
    )
    inventory = inventory.model_copy(
        update={"endpoints": {**inventory.endpoints, GPT_OSS: at}}
    )
    startup = start_up(inventory, plan.registry.get, QWEN)
    with serving([Served.of(startup.argv[0], startup.argv[1:])]):
        confirm(inventory, plan.registry.get, QWEN)
        qwen = inventory.endpoint(QWEN).engine
        gpt_oss = inventory.endpoint(GPT_OSS).engine
        with pytest.raises(LookupError, match=f"serves {qwen}, not {gpt_oss}"):
            confirm(inventory, plan.registry.get, GPT_OSS)
    with pytest.raises(OSError):
        confirm(inventory, plan.registry.get, QWEN, timeout=1.0)


@contextmanager
def keyed_models(secret: str, model: str) -> Generator[str]:
    class Models(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.headers.get("Authorization") != f"Bearer {secret}":
                self.send_error(401)
                return
            body = json.dumps({"data": [{"id": model}]}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            _ = self.wfile.write(body)

        @override
        def log_message(self, format: str, *args: object) -> None:
            pass

    with ThreadingHTTPServer(("127.0.0.1", 0), Models) as server:
        thread = Thread(target=server.serve_forever, kwargs={"poll_interval": 0.01})
        thread.start()
        try:
            yield f"http://127.0.0.1:{server.server_port}/v1/"
        finally:
            server.shutdown()
            thread.join()


def test_an_endpoint_s_secret_goes_with_the_request_that_confirms_it() -> None:
    reg = Registry()
    with keyed_models("s3cret", "gemma") as url:
        remote = reg.add(remote_engine(reg, "gemma"))
        inventory = Inventory(
            endpoints={"gemma": EndpointSpec(engine=remote, url=HttpUrl(url))}
        )
        assert served(url, secret="s3cret") == ["gemma"]
        confirm(inventory, reg.get, "gemma", secret="s3cret")
        with pytest.raises(HTTPError, match="401"):
            confirm(inventory, reg.get, "gemma")

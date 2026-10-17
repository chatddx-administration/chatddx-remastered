import hashlib
from pathlib import Path

import pytest
from pydantic import ValidationError

from chatddx.factors.bundle import Registry
from chatddx.factors.engine import (
    FileDigest,
    Hardware,
    LocalEngine,
    LocalModel,
    Runtime,
)
from chatddx.factors.test.sample import remote_engine
from chatddx.inventory import (
    DirectorySource,
    EndpointSpec,
    HostSpec,
    Inventory,
    check,
    start_up,
)

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
        '[endpoint.qwen]\nengine = "sha256:'
        + "c" * 64
        + '"\nurl = "http://pelle.km:12009/v1/"\nhost = "x"\n'
    )
    with pytest.raises(ValidationError, match="names no host 'x'"):
        _ = Inventory.load(path)
    _ = path.write_text('[endpoint.qwen]\nengine = "sha256:' + "c" * 64 + '"\n')
    with pytest.raises(ValidationError, match="url"):
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
    assert Inventory.load(path).cleared == {"qwen": ("sample",)}
    _ = path.write_text(f'include = ["imported.toml"]\n\n{sources}')
    assert Inventory.load(path).cleared == {}
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


def test_a_start_up_is_refused_where_the_inventory_or_the_engine_falls_short() -> None:
    reg = Registry()
    model, engine = local(reg)
    with pytest.raises(LookupError, match="where it keeps model"):
        _ = start_up(world(engine, templates={TEMPLATE: "/t"}), reg.get, "qwen@pelle")
    with pytest.raises(LookupError, match="where it keeps chat template"):
        _ = start_up(world(engine, models={model: "/m"}), reg.get, "qwen@pelle")
    complete = world(engine, {model: "/m"}, {TEMPLATE: "/t"})
    hostless = complete.endpoint("qwen@pelle").model_copy(update={"host": None})
    with pytest.raises(LookupError, match="'qwen@pelle' needs a host to start"):
        _ = start_up(
            complete.model_copy(update={"endpoints": {"qwen@pelle": hostless}}),
            reg.get,
            "qwen@pelle",
        )
    remote = reg.add(remote_engine(reg, "gemma"))
    with pytest.raises(LookupError, match="engine.remote, not ours to start"):
        _ = start_up(world(remote), reg.get, "qwen@pelle")
    unknown = world("sha256:" + "c" * 64, {model: "/m"}, {TEMPLATE: "/t"})
    with pytest.raises(LookupError, match="'qwen@pelle': sha256:c+ is not in the"):
        _ = start_up(unknown, reg.get, "qwen@pelle")
    alone = Registry()
    _ = alone.add(reg.get(engine))
    with pytest.raises(LookupError, match=f"'qwen@pelle': {model} is not in the"):
        _ = start_up(complete, alone.get, "qwen@pelle")


def test_a_check_finds_what_starting_or_reaching_each_endpoint_would_refuse() -> None:
    reg = Registry()
    model, engine = local(reg)
    remote = reg.add(remote_engine(reg, "gemma"))
    url = "http://pelle.km:12009/v1/"
    pelle = HostSpec(models={model: "/m", "sha256:" + "e" * 64: "/old"})
    inventory = Inventory.model_validate(
        {
            "sources": {"sample": {"name": "sample", "path": "/v", "sensitive": False}},
            "endpoints": {
                "qwen@pelle": {"engine": engine, "url": url, "host": "pelle"},
                "again@pelle": {"engine": engine, "url": url, "host": "pelle"},
                "nowhere": {"engine": engine, "url": "http://pelle.km:12010/v1/"},
                "gemma": {
                    "engine": remote,
                    "url": "https://api.example.org/v1/",
                    "host": "pelle",
                },
                "ghost": {"engine": "sha256:" + "c" * 64, "url": url},
                "model": {"engine": model, "url": url},
            },
            "hosts": {"pelle": pelle},
            "cleared": {"gemma": ["sample"]},
        }
    )
    assert [(f.subject, f.code, f.level) for f in check(inventory, reg.get)] == [
        ("qwen@pelle", "endpoint.unstartable", "warning"),
        ("again@pelle", "endpoint.unstartable", "warning"),
        ("nowhere", "endpoint.unstartable", "warning"),
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

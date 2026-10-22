import hashlib
import re
from typing import Annotated, Literal

from pydantic import AfterValidator, Field, field_validator

from .base import (
    Api,
    Component,
    Digest,
    Finding,
    Frozen,
    RefTo,
    Resolver,
    Sha256Hex,
    StructuralError,
    resolve,
    sorted_keys,
)

OWNED_FLAGS = frozenset(
    {
        "--model",
        "--served-model-name",
        "--chat-template",
        "--tokenizer",
        "--revision",
        "--host",
        "--port",
    }
)
UNPINNED_FLAGS = frozenset({"--config"})
REASONING_FLAGS = frozenset({"--reasoning-parser", "--reasoning-config"})


# Accommodating for vLLM, which reads "_" as "-" in a flag's name, up to its first "."
# (FlexibleArgumentParser).
def _flag(arg: str) -> str:
    name, dot, rest = arg.split("=", 1)[0].partition(".")
    return name.replace("_", "-") + dot + rest


def flag_names(argv: tuple[str, ...]) -> frozenset[str]:
    return frozenset(_flag(arg) for arg in argv if arg.startswith("--"))


# Accommodating for vLLM, where the last of a flag given twice wins.
def flag_value(argv: tuple[str, ...], flag: str) -> str | None:
    found = None
    for i, arg in enumerate(argv):
        if not arg.startswith("--") or _flag(arg) != flag:
            continue
        if "=" in arg:
            found = arg.split("=", 1)[1]
        elif i + 1 < len(argv) and not argv[i + 1].startswith("--"):
            found = argv[i + 1]
    return found


# Accommodating for vLLM's parser, which expands an unambiguous prefix of a flag to the
# whole flag.
def _abbreviations(
    argv: tuple[str, ...], flags: frozenset[str]
) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    for name in flag_names(argv) - {"--"}:
        base = name.partition(".")[0]
        if expanded := sorted(f for f in flags if f != base and f.startswith(base)):
            found[name] = expanded
    return found


_NEGATIVE = re.compile(r"-\d")


# Accommodating for `vllm serve`, which takes the model as its one bare argument, which
# the start-up script gives, so another bare argument stops vLLM from starting. One that
# follows a flag written without "=" may be that flag's value; telling them apart needs
# vLLM's list of flags.
def _bare_arguments(argv: tuple[str, ...]) -> list[str]:
    bare: list[str] = []
    value = False
    for i, arg in enumerate(argv):
        if arg == "--":
            return bare + list(argv[i + 1 :])
        if arg.startswith("-") and not _NEGATIVE.match(arg):
            value = "=" not in arg
        elif value:
            value = False
        else:
            bare.append(arg)
    return bare


class FileDigest(Frozen):
    path: str
    sha256: Sha256Hex


class LocalModel(Component):
    kind: Literal["model.local"] = "model.local"
    repo: str
    revision: str
    files: tuple[FileDigest, ...] = Field(min_length=1)

    @field_validator("files")
    @classmethod
    def _sorted_unique(cls, files: tuple[FileDigest, ...]) -> tuple[FileDigest, ...]:
        paths = [f.path for f in files]
        if len(set(paths)) != len(paths):
            raise ValueError("duplicate file paths")
        return tuple(sorted(files, key=lambda f: f.path))

    # Dependency: facts are keyed by it, as by a remote model's.
    @property
    def name(self) -> str:
        return self.repo


class RemoteModel(Component):
    kind: Literal["model.remote"] = "model.remote"
    provider: str = Field(min_length=1)
    name: str = Field(min_length=1)


Model = LocalModel | RemoteModel
LocalModelRef = Annotated[Digest, RefTo("model.local")]
RemoteModelRef = Annotated[Digest, RefTo("model.remote")]
ModelRef = Annotated[Digest, RefTo("model.local", "model.remote")]


class Hardware(Frozen):
    gpu: str
    compute_capability: tuple[int, int]
    vram_mib: int
    driver: str


class Runtime(Frozen):
    server: Literal["vllm"] = "vllm"
    version: str
    closure: str


class LocalEngine(Component):
    kind: Literal["engine.local"] = "engine.local"
    api: Api = "chat.completions"
    hardware: Hardware
    runtime: Runtime
    model: LocalModelRef
    chat_template: Sha256Hex
    argv: tuple[str, ...] = ()
    env: Annotated[dict[str, str], AfterValidator(sorted_keys)] = Field(
        default_factory=dict
    )

    @field_validator("argv")
    @classmethod
    def _no_owned_flags(cls, argv: tuple[str, ...]) -> tuple[str, ...]:
        owned = flag_names(argv) & OWNED_FLAGS
        if owned:
            raise ValueError(f"argv may not set {sorted(owned)}")
        if unpinned := flag_names(argv) & UNPINNED_FLAGS:
            raise ValueError(
                f"argv may not use {sorted(unpinned)}: its arguments belong in argv, "
                + "where the digest pins them"
            )
        if short := _abbreviations(argv, OWNED_FLAGS | UNPINNED_FLAGS):
            listed = ", ".join(
                f"{a} ({' or '.join(f)})" for a, f in sorted(short.items())
            )
            raise ValueError(f"argv may not abbreviate flags it may not use: {listed}")
        if bare := _bare_arguments(argv):
            raise ValueError(
                f"argv may not have bare arguments {bare}: vLLM takes the model as its "
                + "only bare argument, and the start-up script gives it"
            )
        return argv


class RemoteEngine(Component):
    kind: Literal["engine.remote"] = "engine.remote"
    api: Api = "chat.completions"
    model: RemoteModelRef


EngineRef = Annotated[Digest, RefTo("engine.local", "engine.remote")]


def vllm_024(engine: Component) -> LocalEngine | None:
    if (
        isinstance(engine, LocalEngine)
        and engine.runtime.server == "vllm"
        and engine.runtime.version.startswith("0.24.")
    ):
        return engine
    return None


def served_model_name(engine: str, get: Resolver) -> str:
    match get(engine):
        case LocalEngine():
            return engine
        case RemoteEngine(model=model):
            return resolve(get, model, RemoteModel).name
        case other:
            raise StructuralError(f"{engine} is a {other.kind_name}, not an engine")


def model_of(digest: str, get: Resolver) -> Model:
    match get(digest):
        case LocalModel() | RemoteModel() as model:
            return model
        case LocalEngine(model=model):
            return resolve(get, model, LocalModel)
        case RemoteEngine(model=model):
            return resolve(get, model, RemoteModel)
        case other:
            raise StructuralError(
                f"{digest} is a {other.kind_name}, neither a model nor an engine"
            )


# Accommodating for templates that insert the current date, which make the prompt depend
# on when a run happens.
_READS_DATE = re.compile(r"strftime_now|date_string|\bnow\s*\(")


def check_chat_template(engine: LocalEngine, template: bytes) -> list[Finding]:
    findings: list[Finding] = []
    if hashlib.sha256(template).hexdigest() != engine.chat_template:
        findings.append(
            Finding(
                code="engine.chat_template",
                message="chat template does not match the declared digest",
                subject=engine.digest,
            )
        )
    if _READS_DATE.search(template.decode(errors="replace")):
        findings.append(
            Finding(
                code="engine.chat_template_date",
                message="chat template reads the current date",
                subject=engine.digest,
            )
        )
    return findings

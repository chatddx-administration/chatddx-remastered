import tomllib
from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any, Self, cast

from pydantic import Discriminator, Field, HttpUrl, Tag, model_validator

from chatddx.factors.base import Digest, Frozen, Sha256Hex
from chatddx.factors.trial import Execution

from .sources import DatabaseSource, DirectorySource, Source

_TABLES = (
    "include",
    "configurations",
    "source",
    "endpoint",
    "host",
    "cleared",
    "judge",
)


class EndpointSpec(Frozen):
    engine: Digest
    url: HttpUrl
    host: str | None = None
    capacity: int = Field(default=1, ge=1)
    credential: str | None = None
    canaries: Digest | None = None
    execution: Execution = Field(default_factory=Execution)

    @model_validator(mode="after")
    def _within_capacity(self) -> Self:
        if self.execution.concurrency > self.capacity:
            raise ValueError(
                f"the execution sends {self.execution.concurrency} requests at once, "
                + f"and the capacity is {self.capacity}"
            )
        return self


class HostSpec(Frozen):
    bind: str = "0.0.0.0"
    models: dict[Digest, str] = Field(default_factory=dict)
    templates: dict[Sha256Hex, str] = Field(default_factory=dict)


def _source_kind(source: object) -> str:
    if isinstance(source, dict):
        kind = cast(dict[str, object], source).get("kind", "directory")
        return str(kind)
    return str(getattr(source, "kind", "directory"))


type AnySource = Annotated[
    Annotated[DirectorySource, Tag("directory")]
    | Annotated[DatabaseSource, Tag("database")],
    Discriminator(_source_kind),
]


class Inventory(Frozen):
    sources: dict[str, AnySource] = Field(default_factory=dict)
    endpoints: dict[str, EndpointSpec] = Field(default_factory=dict)
    hosts: dict[str, HostSpec] = Field(default_factory=dict)
    cleared: dict[str, tuple[str, ...]] = Field(default_factory=dict)
    judges: dict[str, str] = Field(default_factory=dict)
    configurations: str | None = None

    @model_validator(mode="after")
    def _sources_named(self) -> Self:
        for name, source in self.sources.items():
            if source.name != name:
                raise ValueError(f"source {name!r} is named {source.name!r}")
        return self

    @model_validator(mode="after")
    def _hosts_exist(self) -> Self:
        for name, endpoint in self.endpoints.items():
            if endpoint.host is not None and endpoint.host not in self.hosts:
                raise ValueError(f"endpoint {name!r} names no host {endpoint.host!r}")
        return self

    @model_validator(mode="after")
    def _cleared_exist(self) -> Self:
        for name, sources in self.cleared.items():
            if name not in self.endpoints:
                raise ValueError(f"cleared names no endpoint {name!r}")
            if unknown := sorted(set(sources) - set(self.sources)):
                raise ValueError(
                    f"endpoint {name!r} is cleared for no source {', '.join(unknown)}"
                )
        return self

    @classmethod
    def load(cls, path: Path) -> Self:
        with path.open("rb") as f:
            data = tomllib.load(f)
        if stray := set(data) - set(_TABLES):
            raise ValueError(
                f"{path}: the inventory has only 'include', 'configurations', "
                + "'source', 'endpoint', 'host', 'cleared' and 'judge', not "
                + f"{sorted(stray)}"
            )
        tables = {t: dict(data.get(t, {})) for t in ("source", "endpoint", "host")}
        for name in data.get("include", []):
            included = path.parent / name
            with included.open("rb") as f:
                more = tomllib.load(f)
            if stray := set(more) - {"endpoint", "host"}:
                raise ValueError(
                    f"{included}: an included inventory has only 'endpoint' and "
                    + f"'host' tables, not {sorted(stray)}"
                )
            for table, records in more.items():
                if twice := sorted(set(tables[table]) & set(records)):
                    raise ValueError(f"{included}: {table} {twice} are in {path} too")
                tables[table] |= records
        sources: dict[str, dict[str, Any]] = {}
        for name, record in tables["source"].items():
            sources[name] = {"name": name, **record}
            if "path" in record:
                sources[name]["path"] = (path.parent / record["path"]).resolve()
        return cls.model_validate(
            {
                "sources": sources,
                "endpoints": tables["endpoint"],
                "hosts": tables["host"],
                "cleared": data.get("cleared", {}),
                "judges": data.get("judge", {}),
                "configurations": data.get("configurations"),
            }
        )

    # Policy: De facto refusal mechanism for
    # src/chatddx/runner/score.py:judge_at and src/chatddx/bench/seen.py:Seen.at
    def serving(
        self,
        digest: str,
        serves: Callable[[str], str | None] | None = None,
        called: str | None = None,
    ) -> str:
        named = sorted(
            n
            for n, e in self.endpoints.items()
            if (e.engine if serves is None else serves(e.engine)) == digest
        )
        what = called or f"engine {digest}"
        match named:
            case [one]:
                return one
            case []:
                raise LookupError(f"no endpoint serves {what}, which is ops' to mend")
            case _:
                raise LookupError(
                    f"{', '.join(named)} serve {what}, which one endpoint should: "
                    + "ops' to mend"
                )

    def source[S: Source](self, name: str | None = None, kind: type[S] = Source) -> S:
        word = _word(kind)
        if name is None:
            held = sorted(n for n, s in self.sources.items() if isinstance(s, kind))
            if len(held) != 1:
                raise LookupError(
                    f"{len(held)} {word}s ({', '.join(held)}) are in the inventory, "
                    + "so one must be named"
                    if held
                    else f"no {word} in the inventory"
                )
            name = held[0]
        match self.sources.get(name):
            case None:
                raise LookupError(f"no source {name!r} in the inventory")
            case source if isinstance(source, kind):
                return source
            case _:
                raise LookupError(f"source {name!r} isn't a {word}")

    def endpoint(self, name: str) -> EndpointSpec:
        spec = self.endpoints.get(name)
        if spec is None:
            raise LookupError(f"no endpoint {name!r} in the inventory")
        return spec

    def takes_typed(self, endpoint: str) -> bool:
        try:
            into = self.source(kind=DatabaseSource)
        except LookupError:
            return False
        return not into.sensitive or into.name in self.cleared.get(endpoint, ())


def _word(kind: type[Source]) -> str:
    field = kind.model_fields.get("kind")
    return "source" if field is None else f"{field.default} source"

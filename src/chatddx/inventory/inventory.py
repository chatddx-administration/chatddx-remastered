import tomllib
from pathlib import Path
from typing import Annotated, Any, Self, cast

from pydantic import Discriminator, Field, HttpUrl, Tag, model_validator

from chatddx.factors.base import Digest, Frozen, Sha256Hex

from .sources import DatabaseSource, DirectorySource, Source


class EndpointSpec(Frozen):
    engine: Digest
    url: HttpUrl | None = None
    host: str | None = None
    max_jobs: int = Field(default=1, ge=1)
    credential: str | None = None


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
        if stray := set(data) - {"include", "source", "endpoint", "host", "cleared"}:
            raise ValueError(
                f"{path}: the inventory has only 'include', 'source', 'endpoint', "
                + f"'host' and 'cleared', not {sorted(stray)}"
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
            }
        )

    def source(self, name: str) -> Source:
        source = self.sources.get(name)
        if source is None:
            raise LookupError(f"no source {name!r} in the inventory")
        return source

    def endpoint(self, name: str) -> EndpointSpec:
        spec = self.endpoints.get(name)
        if spec is None:
            raise LookupError(f"no endpoint {name!r} in the inventory")
        return spec

    def cleared_for(self, endpoint: str) -> frozenset[str]:
        return frozenset(self.cleared.get(endpoint, ()))

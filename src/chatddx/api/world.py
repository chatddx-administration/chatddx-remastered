from fastapi import APIRouter

from chatddx.bench import Bench, NotFound
from chatddx.inventory import EndpointSpec, url_of
from chatddx.scorers.scorer import NO_PARAMS
from chatddx.scorers.shipped import SCORERS
from chatddx.store.catalog import Rows

from . import schemas
from .people import BenchDep

router = APIRouter(tags=["world"])


def endpoint_of(bench: Bench, name: str, spec: EndpointSpec) -> schemas.Endpoint:
    title = model = url = problem = None
    try:
        engine = bench.endpoint(name)
        title, model = bench.title(engine), bench.model(engine)
        url = url_of(bench.inventory, bench.get, name)
    except LookupError as e:
        problem = str(e)
    return schemas.Endpoint(
        name=name,
        engine=spec.engine,
        title=title,
        model=model,
        url=url,
        host=spec.host,
        max_jobs=spec.max_jobs,
        credential=spec.credential,
        cleared_for=sorted(bench.inventory.cleared_for(name)),
        problem=problem,
    )


@router.get("/endpoints")
def endpoints(bench: BenchDep) -> list[schemas.Endpoint]:
    return [
        endpoint_of(bench, name, spec)
        for name, spec in sorted(bench.inventory.endpoints.items())
    ]


@router.get("/endpoints/{name}")
def endpoint(bench: BenchDep, name: str) -> schemas.Endpoint:
    try:
        spec = bench.inventory.endpoint(name)
    except LookupError as e:
        raise NotFound(str(e)) from None
    return endpoint_of(bench, name, spec)


@router.get("/models")
def models(bench: BenchDep) -> list[schemas.Model]:
    serving: dict[str, list[str]] = {}
    for name in sorted(bench.inventory.endpoints):
        try:
            model = bench.model(bench.endpoint(name))
        except LookupError:
            continue
        if model is not None:
            serving.setdefault(model, []).append(name)
    known = bench.facts.models
    return [
        schemas.Model(
            name=model,
            facts=known[model].model_dump(mode="json") if model in known else None,
            endpoints=serving.get(model, []),
        )
        for model in sorted(set(known) | set(serving))
    ]


@router.get("/components/{digest}")
def component(bench: BenchDep, digest: str) -> schemas.Component:
    kind = Rows(bench.conn).kind(digest)
    if kind is None:
        raise NotFound(f"no component {digest} in the store")
    return schemas.Component(
        digest=digest,
        kind=kind,
        title=bench.title(digest),
        body=bench.get(digest).model_dump(mode="json"),
    )


@router.get("/scorer-code")
def scorer_code(_: BenchDep) -> list[schemas.ScorerCode]:
    return [
        schemas.ScorerCode(
            entry_point=entry_point,
            version=code.version,
            metrics=[
                schemas.Metric(name=name, measures=m.measures, params=m.params)
                for name, m in sorted(code.metrics.items())
            ],
            params=NO_PARAMS if code.params is None else code.params,
        )
        for entry_point, code in sorted(SCORERS.items())
    ]

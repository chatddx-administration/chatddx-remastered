from fastapi import APIRouter, HTTPException

from chatddx.bench import KINDS, WRITTEN, Bench, NotFound
from chatddx.factors.kinds import BY_KIND
from chatddx.inventory import EndpointSpec, url_of
from chatddx.scorers.scorer import NO_PARAMS
from chatddx.scorers.shipped import SCORERS

from . import schemas
from .people import BenchDep
from .threads import refused

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
        takes_typed=bench.takes_typed(name),
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
    kind = bench.rows.kind(digest)
    if kind is None:
        raise NotFound(f"no component {digest} in the store")
    return schemas.Component(
        digest=digest,
        kind=kind,
        title=bench.title(digest),
        body=bench.get(digest).model_dump(mode="json"),
    )


@router.get("/kinds")
def kinds(_: BenchDep) -> list[schemas.Kind]:
    return [
        schemas.Kind(
            kind=kind,
            word=word,
            written=kind in WRITTEN,
            json_schema=BY_KIND[kind].model_json_schema(),
        )
        for word, held in KINDS.items()
        for kind in held
    ]


@router.post("/components/check")
def check(bench: BenchDep, given: schemas.ComponentBody) -> schemas.Checked:
    with refused():
        try:
            checked = bench.check(bench.component(given))
        except LookupError as e:
            raise HTTPException(422, str(e)) from None
    return schemas.Checked(
        digest=checked.digest,
        findings=[schemas.Finding.of(f) for f in checked.findings],
    )


@router.get("/scorer-code")
def scorer_code(_: BenchDep) -> list[schemas.ScorerCode]:
    return [
        schemas.ScorerCode(
            entry_point=entry_point,
            version=code.version,
            metrics=[
                schemas.Metric(
                    name=name,
                    measures=m.measures,
                    params=m.params,
                    judged=m.judged,
                    unit=m.unit,
                )
                for name, m in sorted(code.metrics.items())
            ],
            params=NO_PARAMS if code.params is None else code.params,
        )
        for entry_point, code in sorted(SCORERS.items())
    ]

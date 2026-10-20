from fastapi import APIRouter
from pydantic import JsonValue

from chatddx.bench import KINDS, WRITTEN, Bench, Checked, Handle, NotFound
from chatddx.factors.engine import model_of
from chatddx.factors.kinds import BY_KIND
from chatddx.factors.request import Recipe
from chatddx.factors.select import select
from chatddx.inventory import EndpointSpec
from chatddx.scorers.scorer import NO_PARAMS
from chatddx.scorers.shipped import SCORERS

from . import schemas
from .people import BenchDep
from .state import refused
from .threads import component_of

router = APIRouter(tags=["world"])


def _endpoint_of(bench: Bench, name: str, spec: EndpointSpec) -> schemas.Endpoint:
    title = model = serves = problem = None
    try:
        found = bench.endpoint(name)
        title, model, serves = (
            bench.title(found.engine),
            found.model.name,
            found.model.digest,
        )
    except LookupError as e:
        problem = str(e)
    return schemas.Endpoint(
        name=name,
        engine=spec.engine,
        title=title,
        model=model,
        serves=serves,
        url=str(spec.url),
        host=spec.host,
        capacity=spec.capacity,
        credential=spec.credential,
        cleared_for=sorted(bench.inventory.cleared.get(name, ())),
        takes_typed=bench.inventory.takes_typed(name),
        problem=problem,
    )


@router.get("/endpoints")
def endpoints(bench: BenchDep) -> list[schemas.Endpoint]:
    return [
        _endpoint_of(bench, name, spec)
        for name, spec in sorted(bench.inventory.endpoints.items())
    ]


@router.get("/models")
def models(bench: BenchDep) -> list[schemas.Model]:
    known = bench.facts.models
    found: list[schemas.Model] = []
    for edit, about in bench.threads("model"):
        handle = Handle(about.name or str(edit.thread), edit.thread, edit.digest)
        weights = model_of(edit.digest, bench.store.get).name
        try:
            at = bench.served(handle)
        except ValueError:
            continue
        found.append(
            schemas.Model(
                name=handle.name,
                weights=edit.digest,
                engine=at.engine,
                facts=known[weights].model_dump(mode="json")
                if weights in known
                else None,
                takes_typed=bench.inventory.takes_typed(at.name),
            )
        )
    return sorted(found, key=lambda m: m.name)


@router.get("/components/{digest}")
def component(bench: BenchDep, digest: str) -> schemas.Component:
    kind = bench.rows.kind(digest)
    if kind is None:
        raise NotFound(f"no component {digest} in the store")
    return schemas.Component(
        digest=digest,
        kind=kind,
        title=bench.title(digest),
        body=bench.store.get(digest).model_dump(mode="json"),
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
    with refused(LookupError):
        return _checked(bench.check(component_of(given)))


@router.post("/recipes/check")
def check_recipe(bench: BenchDep, given: schemas.RecipeBody) -> schemas.Checked:
    with refused(LookupError):
        return _checked(bench.check(Recipe.model_validate(given)))


def _checked(checked: Checked) -> schemas.Checked:
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


@router.post("/picks")
def picks(_: BenchDep, given: schemas.Picking) -> list[schemas.Picked]:
    return [_picked(given.document, s) for s in given.selectors]


def _picked(document: JsonValue, selector: str) -> schemas.Picked:
    try:
        return schemas.Picked(items=select(document, selector), problem=None)
    except ValueError as e:
        return schemas.Picked(items=None, problem=str(e))

import json
from typing import Annotated, Any
from urllib.parse import urlencode
from uuid import UUID

from fastapi import APIRouter, Form, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import JsonValue

from chatddx import settings
from chatddx.api import (
    families as api_families,
    runs as api_runs,
    schemas,
    threads as api,
    world as api_world,
)
from chatddx.api.state import refused
from chatddx.bench import Ambiguous, Bench, NotFound
from chatddx.factors.base import resolve
from chatddx.factors.cases import Appendix
from chatddx.factors.request import Purpose, Skeleton
from chatddx.factors.scoring import Expectation, ExpectationSchema, Judge, Scorer
from chatddx.factors.trial import Trial, suggest_seeds
from chatddx.scorers.shipped import unit_of

from .families import appended, built, written_for
from .pages import BenchDep, page, within
from .runs import PLAN

ANSWERS = 50
OPEN = ("queued", "under way")

router = APIRouter()

type Tags = Annotated[list[str] | None, Query()]


@router.get("/review")
def reviewing(request: Request, bench: BenchDep, tag: Tags = None) -> Response:
    listed = _listed(api_families.families(bench), tag)
    if listed:
        return RedirectResponse(f"/review/{listed[0].id}{_query(tag=tag)}", 303)
    return page(request, "review.html", person=bench.person, family=None, tag=tag)


@router.get("/review/{family}")
def review(
    request: Request,
    bench: BenchDep,
    family: int,
    case: str | None = None,
    schema: str | None = None,
    scorer: int | None = None,
    tag: Tags = None,
) -> Response:
    shown = api_families.family(bench, family)
    picked = next((c for c in shown.cases if case in (None, c.case)), None)
    if picked is None:
        raise HTTPException(404, f"no case {case} of {shown.name}")
    visible = sorted(
        api.threads(bench, "expectation_schema"), key=lambda t: t.name or t.title
    )
    under = next(
        (t.head.digest for t in visible if schema in (None, t.head.digest)), None
    )
    if schema is not None and under is None:
        raise HTTPException(404, f"no expectation schema {schema} for you")
    expected = next(
        (e for e in picked.expectations if e.expectation_schema == under), None
    )
    scorers = _scorers(bench, under)
    ran = _ran(bench, picked.case)
    scored = {
        g.scorer
        for _, d in ran
        for g in d.scores
        if any(i.case == picked.case for i in g.items)
    }
    held = _scorer(scorers, scorer, scored)
    if scorer is not None and held is None:
        raise HTTPException(404, f"no scorer {scorer} reading that schema for you")
    every = api_families.families(bench)
    listed = _listed(every, tag)
    keep = {"tag": tag, "schema": schema, "scorer": scorer}
    at = next((i for i, f in enumerate(listed) if f.id == family), None)
    left = _left(bench, ran, held)
    answers = _answers(bench, ran, picked.case, held, left)
    pending = [
        {"run": str(r.id), "described": r.described}
        for r, _ in ran
        if r.job is not None and r.job.status in OPEN
    ]
    own = _own(bench, expected)
    appendices = _appendices(bench, picked.appendices)
    views = [] if held is None else _views(bench, held, expected)
    query = request.url.query
    back = request.url.path + (f"?{query}" if query else "")
    previous = None if not at else f"/review/{listed[at - 1].id}{_query(**keep)}"
    following = (
        None
        if at is None or at + 1 == len(listed)
        else f"/review/{listed[at + 1].id}{_query(**keep)}"
    )
    props: dict[str, Any] = {
        "family": family,
        "case": picked.case,
        "labels": [] if held is None else held[2],
        "units": []
        if held is None
        else [unit_of(held[1], i) for i, _ in enumerate(held[2])],
        "answers": [
            {k: a[k] for k in ("run", "score", "replicate", "plan", "anchor")}
            for a in answers
        ],
        "expected": {
            "editor": _editing(bench, shown, picked, under, expected, own),
            "digest": None if expected is None else expected.expectation,
            "history": [] if own is None else _history(bench, own),
            "views": [
                {
                    k: v[k]
                    for k in ("label", "metric", "measures", "judge", "expectation")
                }
                for v in views
            ],
            "composing": _composing(bench, held, under, ran, picked.case),
        },
        "appendices": [
            None if a["editor"] is None else {k: a[k] for k in ("editor", "digest")}
            for a in appendices
        ],
        "back": back,
        "pending": pending,
        "previous": previous,
        "next": following,
    }
    return page(
        request,
        "review.html",
        person=bench.person,
        family=shown,
        listed=listed,
        marks=_marks(bench, listed, under),
        tags=sorted({t for f in every for t in f.tags}),
        tag=tag,
        keep=keep,
        case=picked,
        cases=shown.cases,
        appendices=appendices,
        written=written_for(bench, family),
        visible=visible,
        schema=under,
        expected=expected,
        own=own,
        carried=_carried(bench, shown, picked, under, expected),
        scorers=scorers,
        scorer=held,
        views=views,
        answers=answers,
        means=_means(answers, held),
        pending=pending,
        left=left,
        configurations=_configurations(bench),
        endpoints=[e.name for e in api_world.endpoints(bench)],
        most=settings.ITEMS_PER_RUN,
        at=None if at is None else at + 1,
        previous=previous,
        following=following,
        back=back,
        props=props,
        query=_query,
        island="review",
    )


@router.post("/review/{family}/appendices")
def appending_in_review(
    bench: BenchDep,
    family: int,
    name: Annotated[str, Form()],
    text: Annotated[str, Form()],
    back: Annotated[str | None, Form()] = None,
) -> Response:
    appended(bench, family, name, text)
    return RedirectResponse(within(back or f"/review/{family}"), 303)


@router.post("/review/{family}/cases")
def building_in_review(
    bench: BenchDep,
    family: int,
    appendix: Annotated[list[str] | None, Form()] = None,
    tag: Annotated[list[str] | None, Form()] = None,
    under: Annotated[str | None, Form(alias="schema")] = None,
    scorer: Annotated[int | None, Form()] = None,
) -> Response:
    made = built(bench, family, appendix)
    given = _query(case=made, tag=tag, schema=under, scorer=scorer)
    return RedirectResponse(f"/review/{family}{given}", 303)


@router.post("/review/{family}/runs")
def running_in_review(
    bench: BenchDep,
    family: int,
    configuration: Annotated[int, Form()],
    case: Annotated[str, Form()],
    endpoint: Annotated[str, Form()] = "",
    replicates: Annotated[int, Form(ge=1, le=settings.ITEMS_PER_RUN)] = 1,
    score: Annotated[bool, Form()] = False,
    back: Annotated[str | None, Form()] = None,
) -> Response:
    if case not in bench.family(family).cases:
        raise HTTPException(422, f"no case {case} of family {family}")
    with refused(NotFound):
        variation = bench.variation(configuration, {}, None)
        if endpoint and variation.recipe is not None:
            serves = bench.endpoint(endpoint).model.digest
            if variation.held("model") != serves:
                variation = bench.variation(configuration, {"model": serves}, None)
        started = bench.start(
            variation, endpoint or None, [case], suggest_seeds(replicates)
        )
    for _, running in started.runs:
        _ = bench.queue(running, score)
    return RedirectResponse(within(back or f"/review/{family}") + "#record", 303)


@router.post("/review/{family}/scores")
def scoring_in_review(
    bench: BenchDep,
    family: int,
    run: Annotated[list[UUID], Form()],
    back: Annotated[str | None, Form()] = None,
) -> Response:
    _ = bench.family(family)
    for found in run:
        started = bench.run(found)
        with refused():
            _ = bench.queue_scoring(started, bench.unscored(started) or None)
    return RedirectResponse(within(back or f"/review/{family}") + "#record", 303)


type Given = str | int | list[str] | None


def _query(**given: Given) -> str:
    pairs: list[tuple[str, str | int]] = [
        (k, v)
        for k, held in given.items()
        for v in (held if isinstance(held, list) else [held])
        if v is not None
    ]
    return "?" + urlencode(pairs) if pairs else ""


def _listed(every: list[schemas.Family], tag: list[str] | None) -> list[schemas.Family]:
    picked = set(tag or ())
    return [f for f in every if not picked or picked & set(f.tags)]


def _marks(
    bench: Bench, listed: list[schemas.Family], schema: str | None
) -> dict[int, dict[str, bool]]:
    answered = {
        c for r in bench.runs() for c in resolve(bench.store.get, r.trial, Trial).cases
    }
    found: dict[int, dict[str, bool]] = {}
    for f in listed:
        try:
            held = None if schema is None else bench.expectation(f.case, schema)
            choosing = False
        except Ambiguous:
            held, choosing = None, True
        found[f.id] = {
            "expected": held is not None,
            "choosing": choosing,
            "answered": f.case in answered,
        }
    return found


def _appendices(bench: Bench, digests: list[str]) -> list[dict[str, Any]]:
    threads = {t.head.digest: t for t in api.threads(bench, "appendix")}
    found: list[dict[str, Any]] = []
    for d in digests:
        held = resolve(bench.store.get, d, Appendix)
        t = threads.get(d)
        editor = (
            None
            if t is None
            else {
                "kind": "appendix",
                "mode": "edit" if t.owner == bench.person.login else "fork",
                "thread": t.id,
                "head": t.head.id,
                "name": t.name or t.title,
                "vignette": held.vignette.model_dump(mode="json"),
                "text": held.text,
            }
        )
        found.append(
            {
                "title": bench.title(d),
                "text": held.text,
                "thread": None if t is None else t.id,
                "editor": editor,
                "digest": d,
            }
        )
    return found


def _own(bench: Bench, expected: schemas.Expected | None) -> schemas.Thread | None:
    if expected is None or expected.expectation is None:
        return None
    mine = api.threads(bench, "expectation", owner=bench.person.login)
    return next((t for t in mine if t.head.digest == expected.expectation), None)


def _editing(
    bench: Bench,
    shown: schemas.FamilyDetail,
    picked: schemas.FamilyCase,
    schema: str | None,
    expected: schemas.Expected | None,
    own: schemas.Thread | None,
) -> dict[str, Any] | None:
    if schema is None or (expected is not None and expected.ambiguous):
        return None
    given: dict[str, Any] = {
        "kind": "expectation",
        "case": picked.case,
        "schema": schema,
        "json_schema": resolve(bench.store.get, schema, ExpectationSchema).json_schema,
    }
    if own is not None and expected is not None:
        return {
            **given,
            "mode": "edit",
            "thread": own.id,
            "head": own.head.id,
            "name": own.name or own.title,
            "data": expected.data,
        }
    return {
        **given,
        "mode": "new",
        "name": f"expectation for {picked.title}",
        "data": _started(shown, picked, schema),
    }


def _started(
    shown: schemas.FamilyDetail, picked: schemas.FamilyCase, schema: str
) -> JsonValue:
    if picked.default:
        return None
    return next(
        (
            e.data
            for c in shown.cases
            if c.default
            for e in c.expectations
            if e.expectation_schema == schema and e.expectation is not None
        ),
        None,
    )


def _history(bench: Bench, own: schemas.Thread) -> list[dict[str, Any]]:
    return [
        {
            "at": e.at.isoformat(),
            "by": e.by,
            "digest": e.digest,
            "data": resolve(bench.store.get, e.digest, Expectation).data,
        }
        for e in api.edits(bench, own.id)
    ]


def _carried(
    bench: Bench,
    shown: schemas.FamilyDetail,
    picked: schemas.FamilyCase,
    schema: str | None,
    expected: schemas.Expected | None,
) -> list[tuple[str, schemas.Thread]]:
    if schema is None or (
        expected is not None and (expected.expectation or expected.ambiguous)
    ):
        return []
    mine = api.threads(bench, "expectation", owner=bench.person.login)
    own = {t.head.digest: t for t in mine}
    return [
        (c.title, own[e.expectation])
        for c in shown.cases
        if c.case != picked.case and not c.default
        for e in c.expectations
        if e.expectation_schema == schema and e.expectation in own
    ]


type Held = tuple[schemas.Thread, Scorer, list[str]]


def _scorers(bench: Bench, schema: str | None) -> list[Held]:
    login = bench.person.login
    found: list[Held] = []
    for t in api.threads(bench, "scorer"):
        held = resolve(bench.store.get, t.head.digest, Scorer)
        if held.expectation_schema != schema:
            continue
        named = bench.labels(t.head.digest)
        labels = [named.get(i, f"view {i}") for i in range(len(held.views))]
        found.append((t, held, labels))
    return sorted(found, key=lambda s: (s[0].owner != login, s[0].name or s[0].title))


def _views(
    bench: Bench, held: Held, expected: schemas.Expected | None
) -> list[dict[str, Any]]:
    _, scorer, labels = held
    measures = {
        m.name: m.measures
        for code in api_world.scorer_code(bench)
        if code.entry_point == scorer.entry_point
        for m in code.metrics
    }
    picks = (
        []
        if expected is None or expected.data is None
        else api_world.picks(
            bench,
            schemas.Picking(
                document=expected.data, selectors=[v.expectation for v in scorer.views]
            ),
        )
    )
    return [
        {
            "label": labels[i],
            "metric": v.metric,
            "measures": measures.get(v.metric),
            "judge": None if v.judge is None else bench.title(v.judge),
            "output": v.output,
            "split": v.split,
            "expectation": v.expectation,
            "params": v.params,
            "picked": picks[i] if picks else None,
        }
        for i, v in enumerate(scorer.views)
    ]


def _means(answers: list[dict[str, Any]], held: Held | None) -> list[dict[str, Any]]:
    if held is None:
        return []
    found: list[dict[str, Any]] = []
    for i, label in enumerate(held[2]):
        given = [
            value
            for a in answers
            if a["values"] is not None
            for value in [a["values"][i][0]]
            if value is not None
        ]
        found.append(
            {
                "label": label,
                "mean": sum(given) / len(given) if given else None,
                "of": len(given),
                "unit": unit_of(held[1], i),
            }
        )
    return found


def _composing(
    bench: Bench,
    held: Held | None,
    schema: str | None,
    ran: list[tuple[schemas.Run, schemas.RunDetail]],
    case: str,
) -> dict[str, Any] | None:
    shipped = api_world.scorer_code(bench)
    if schema is None or not shipped:
        return None
    [code, *_] = shipped
    unjudged = [m.name for m in code.metrics if not m.judged]
    blank = {
        "kind": "scorer",
        "entry_point": code.entry_point,
        "version": code.version,
        "expectation_schema": schema,
        "views": [{"metric": unjudged[0] if unjudged else code.metrics[0].name}],
    }
    scorer = None
    titles: dict[str, str] = {}
    if held is not None:
        thread, body, labels = held
        scorer = {
            "thread": thread.id,
            "head": thread.head.id,
            "digest": thread.head.digest,
            "name": thread.name or thread.title,
            "mode": "edit" if thread.owner == bench.person.login else "fork",
            "body": body.model_dump(mode="json"),
            "labels": labels,
        }
        titles = {j: bench.title(j) for j in body.judges}
    judges = _judges(bench)
    return {
        "scorer": scorer,
        "blank": blank,
        "metrics": [m.model_dump(mode="json") for m in code.metrics],
        "outputs": _outputs(bench),
        "judges": judges,
        "titles": titles | {j["digest"]: j["name"] for j in judges},
        "me": bench.person.login,
        "judging": [
            {
                "digest": t.head.digest,
                "thread": t.id,
                "name": t.name or t.title,
                "owner": t.owner,
                "output_schema": resolve(
                    bench.store.get, t.head.digest, Skeleton
                ).output_schema,
            }
            for t in _configurations(bench, "judge")
        ],
        "endpoints": [
            {"name": e.name, "engine": e.engine}
            for e in api_world.endpoints(bench)
            if e.problem is None
        ],
        "case": case,
        "runs": [str(r.id) for r, d in ran if any(i.case == case for i in d.items)],
    }


def _judges(bench: Bench) -> list[dict[str, Any]]:
    login = bench.person.login
    found: list[dict[str, Any]] = []
    for t in sorted(
        api.threads(bench, "judge"), key=lambda t: (t.owner != login, t.name or t.title)
    ):
        judge = resolve(bench.store.get, t.head.digest, Judge)
        try:
            at = bench.inventory.serving(judge.engine)
        except LookupError:
            at = None
        found.append(
            {
                "digest": t.head.digest,
                "thread": t.id,
                "name": t.name or t.title,
                "owner": t.owner,
                "configuration": bench.title(judge.skeleton),
                "endpoint": at,
                "seeds": list(judge.seeds),
                "output_schema": resolve(
                    bench.store.get, judge.skeleton, Skeleton
                ).output_schema,
            }
        )
    return found


def _outputs(bench: Bench) -> list[dict[str, Any]]:
    found: dict[str, dict[str, Any]] = {}
    for t in api.threads(bench, "configuration", purpose="generation"):
        schema = resolve(bench.store.get, t.head.digest, Skeleton).output_schema
        held = found.setdefault(
            json.dumps(schema, sort_keys=True),
            {
                "title": schema.get("title") if isinstance(schema, dict) else None,
                "json_schema": schema,
                "by": [],
            },
        )
        held["by"].append(t.name or t.title)
    return list(found.values())


def _scorer(scorers: list[Held], picked: int | None, scored: set[str]) -> Held | None:
    if picked is not None:
        return next((s for s in scorers if s[0].id == picked), None)
    return next(
        (s for s in scorers if s[0].head.digest in scored),
        scorers[0] if scorers else None,
    )


def _ran(bench: Bench, case: str) -> list[tuple[schemas.Run, schemas.RunDetail]]:
    return [
        (r, api_runs.run(bench, r.id))
        for r in api_runs.runs(bench, reaching=case, limit=ANSWERS)
    ]


def _configurations(
    bench: Bench, purpose: Purpose = "generation"
) -> list[schemas.Thread]:
    login = bench.person.login
    found = api.threads(bench, "configuration", purpose=purpose)
    return sorted(found, key=lambda t: (t.owner != login, t.name or t.title))


def _left(
    bench: Bench, ran: list[tuple[schemas.Run, schemas.RunDetail]], held: Held | None
) -> set[str]:
    if held is None:
        return set()
    return {
        str(r.id)
        for r, _ in ran
        if r.finished
        and (r.job is None or r.job.status not in OPEN)
        and held[0].head.digest in bench.unscored(bench.run(r.id))
    }


def _answers(
    bench: Bench,
    ran: list[tuple[schemas.Run, schemas.RunDetail]],
    case: str,
    held: Held | None,
    left: set[str],
) -> list[dict[str, Any]]:
    views = range(0 if held is None else len(held[1].views))
    found: list[dict[str, Any]] = []
    for r, detail in ran:
        skeleton = resolve(bench.store.get, r.skeleton, Skeleton)
        schema = skeleton.output_schema
        graded = (
            None
            if held is None
            else next(
                (g for g in detail.scores if g.scorer == held[0].head.digest), None
            )
        )
        values = (
            {}
            if graded is None
            else {
                (i.replicate, i.view): i.value for i in graded.items if i.case == case
            }
        )
        for at, item in enumerate(detail.items, 1):
            if item.case != case:
                continue
            found.append(
                {
                    "run": str(r.id),
                    "described": r.described,
                    "endpoint": r.endpoint,
                    "at": r.at,
                    "anchor": at,
                    "replicate": item.replicate,
                    "outcome": item.outcome,
                    "plan": isinstance(schema, dict) and schema.get("title") == PLAN,
                    "score": None
                    if graded is None or graded.score is None
                    else str(graded.score),
                    "left": str(r.id) in left,
                    "values": None
                    if graded is None or held is None
                    else [
                        (values.get((item.replicate, v)), unit_of(held[1], v))
                        for v in views
                    ],
                }
            )
    return found

from typing import Annotated, Any
from urllib.parse import urlencode

from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse

from chatddx.api import (
    families as api_families,
    runs as api_runs,
    schemas,
    threads as api,
    world as api_world,
)
from chatddx.bench import Ambiguous, Bench
from chatddx.factors.base import resolve
from chatddx.factors.cases import Appendix
from chatddx.factors.request import Skeleton
from chatddx.factors.scoring import Scorer
from chatddx.factors.trial import Trial
from chatddx.scorers.shipped import unit_of

from .pages import BenchDep, page
from .runs import PLAN

ANSWERS = 50

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
    answers = _answers(bench, ran, picked.case, held)
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
        "previous": None if not at else f"/review/{listed[at - 1].id}{_query(**keep)}",
        "next": None
        if at is None or at + 1 == len(listed)
        else f"/review/{listed[at + 1].id}{_query(**keep)}",
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
        appendices=_appendices(bench, picked.appendices),
        visible=visible,
        schema=under,
        expected=expected,
        own=_own(bench, expected),
        scorers=scorers,
        scorer=held,
        views=[] if held is None else _views(bench, held, expected),
        answers=answers,
        props=props,
        query=_query,
        island="review",
    )


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
    threads = {t.head.digest: t.id for t in api.threads(bench, "appendix")}
    return [
        {
            "title": bench.title(d),
            "text": resolve(bench.store.get, d, Appendix).text,
            "thread": threads.get(d),
        }
        for d in digests
    ]


def _own(bench: Bench, expected: schemas.Expected | None) -> schemas.Thread | None:
    if expected is None or expected.expectation is None:
        return None
    mine = api.threads(bench, "expectation", owner=bench.person.login)
    return next((t for t in mine if t.head.digest == expected.expectation), None)


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


def _answers(
    bench: Bench,
    ran: list[tuple[schemas.Run, schemas.RunDetail]],
    case: str,
    held: Held | None,
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
                    "values": None
                    if graded is None or held is None
                    else [
                        (values.get((item.replicate, v)), unit_of(held[1], v))
                        for v in views
                    ],
                }
            )
    return found

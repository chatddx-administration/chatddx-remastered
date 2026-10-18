from typing import Annotated, Any
from urllib.parse import urlencode

from fastapi import APIRouter, Form, HTTPException, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import JsonValue

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
from chatddx.factors.scoring import Expectation, ExpectationSchema, Scorer
from chatddx.factors.trial import Trial
from chatddx.scorers.shipped import unit_of

from .families import appended, built, written_for
from .pages import BenchDep, page, within
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
        },
        "appendices": [
            None if a["editor"] is None else {k: a[k] for k in ("editor", "digest")}
            for a in appendices
        ],
        "back": back,
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

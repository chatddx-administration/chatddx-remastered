from collections import Counter
from typing import Annotated, Any
from urllib.parse import parse_qsl, urlencode
from uuid import UUID

from fastapi import APIRouter, Form, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import JsonValue

from chatddx import settings
from chatddx.api import (
    families as api_families,
    runs as api_runs,
    schemas,
    threads as api,
)
from chatddx.api.state import refused
from chatddx.bench import Bench, NotFound
from chatddx.factors.base import Fingerprint, Invalid, resolve
from chatddx.factors.cases import Appendix, Case, Vignette
from chatddx.factors.request import Purpose, Skeleton, Translations
from chatddx.factors.scoring import Expectation, ExpectationSchema, Scorer
from chatddx.factors.trial import Trial, suggest_seeds
from chatddx.locale import display_language, tr
from chatddx.scorers.shipped import unit_of
from chatddx.store import fetch_vignette

from .cases import appended, built
from .pages import BenchDep, page, within
from .runs import PLAN, pressed
from .titles import display_case

_ANSWERS = 50
_OPEN = ("queued", "under way")

router = APIRouter()

type Tags = Annotated[list[str] | None, Query()]


@router.get("/review")
def reviewing(
    request: Request, bench: BenchDep, tag: Tags = None, language: Tags = None
) -> Response:
    listed = _listed(api_families.families(bench), tag, language)
    if listed:
        kept = _query(tag=tag, language=language)
        return RedirectResponse(f"/review/{listed[0].id}{kept}", 303)
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
    language: Tags = None,
) -> Response:
    shown = api_families.family(bench, family)
    picked = _picked(shown, case)
    visible = sorted(
        api.threads(bench, "expectation_schema"), key=lambda t: t.name or t.title
    )
    under = next(
        (t.head.digest for t in visible if schema in (None, t.head.digest)), None
    )
    if schema is not None and under is None:
        raise NotFound.of("no expectation schema %(schema)s for you", schema=schema)
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
        raise NotFound.of(
            "no scorer %(scorer)s reading that schema for you", scorer=scorer
        )
    every = api_families.families(bench)
    listed = _listed(every, tag, language)
    keep = {"tag": tag, "language": language, "schema": schema, "scorer": scorer}
    left = _left(bench, ran, held)
    answers = _answers(bench, ran, picked.case, held, left)
    under_way = [r for r, _ in ran if r.job is not None and r.job.status in _OPEN]
    pending = [{"run": str(r.id), "titled": r.titled} for r in under_way]
    own = _own(bench, expected)
    offered = (
        []
        if expected is None or expected.expectation is not None
        else [
            (t, resolve(bench.store.get, t.head.digest, Expectation).data)
            for t in expected.shared
        ]
    )
    appendices = _appendices(bench, picked.appendices)
    query = request.url.query
    back = request.url.path + (f"?{query}" if query else "")
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
        },
        "appendices": [
            None if a["editor"] is None else {k: a[k] for k in ("editor", "digest")}
            for a in appendices
        ],
        "back": back,
        "pending": [
            {"run": str(r.id), "titled": r.titled.model_dump(mode="json")}
            for r in under_way
        ],
        "about": {
            "family": family,
            "tags": shown.tags,
            "language": shown.language,
            "languages": _languages(bench, every, shown.language),
            "editable": bench.person.login in [shown.owner, *shown.collaborators],
        },
    }
    return page(
        request,
        "review.html",
        person=bench.person,
        family=shown,
        every=every,
        listed={f.id for f in listed},
        marks=_marks(bench, every),
        tags=sorted({t for f in every for t in f.tags}),
        languages=sorted({f.language for f in every if f.language}),
        tag=tag,
        keep=keep,
        toggled=_toggled,
        case=picked,
        cases=shown.cases,
        appendices=appendices,
        visible=visible,
        schema=under,
        expected=expected,
        own=own,
        offered=offered,
        carried=_carried(bench, shown, picked, under, expected),
        scorer=held,
        labels=[] if held is None else held[2],
        answers=answers,
        means=_means(answers, held),
        pending=pending,
        left=left,
        configurations=_configurations(bench),
        models=[h.name for h, at in bench.handles() if at is not None],
        most=settings.ITEMS_PER_RUN,
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
    case: Annotated[str | None, Form()] = None,
    back: Annotated[str | None, Form()] = None,
) -> Response:
    picked = _picked(api_families.family(bench, family), case)
    made = built(
        bench, family, [*picked.appendices, appended(bench, family, name, text)]
    )
    return _moved(family, back, made)


@router.post("/review/{family}/appendices/{at}/remove")
def removing_in_review(
    bench: BenchDep,
    family: int,
    at: int,
    case: Annotated[str, Form()],
    back: Annotated[str | None, Form()] = None,
) -> Response:
    picked = _picked(api_families.family(bench, family), case)
    if not 0 <= at < len(picked.appendices):
        raise NotFound.of(
            "no appendix %(at)s in %(case)s", at=at, case=display_case(picked.titled)
        )
    kept = [a for i, a in enumerate(picked.appendices) if i != at]
    with refused():
        made = bench.case(family, kept)
    return _moved(family, back, made)


@router.post("/review/{family}/runs")
def running_in_review(
    bench: BenchDep,
    family: int,
    configuration: Annotated[int, Form()],
    case: Annotated[str, Form()],
    model: Annotated[str, Form()] = "",
    replicates: Annotated[int, Form(ge=1, le=settings.ITEMS_PER_RUN)] = 1,
    score: Annotated[bool, Form()] = False,
    back: Annotated[str | None, Form()] = None,
) -> Response:
    if case not in bench.family(family).cases:
        raise Invalid.of(
            "no case %(case)s of family %(family)s", case=case, family=family
        )
    with refused(NotFound):
        variation = bench.variation(configuration, {}, None)
        if model and variation.recipe is not None:
            weights = bench.handle_named(model).weights
            if variation.held("model") != weights:
                variation = bench.variation(configuration, {"model": weights}, None)
        at = bench.at(
            variation, model=model if model and variation.recipe is None else None
        )
        started = bench.start(variation, at.name, [case], suggest_seeds(replicates))
    for _, running in started.runs:
        _ = bench.queue(running, score)
    return RedirectResponse(within(back or f"/review/{family}") + "#record", 303)


@router.post("/review/{family}/scores")
def scoring_in_review(
    bench: BenchDep,
    family: int,
    run: Annotated[list[UUID], Form()],
    scorer: Annotated[str, Form()],
    back: Annotated[str | None, Form()] = None,
) -> Response:
    _ = bench.family(family)
    for found in run:
        started = bench.run(found)
        if scorer in bench.unscored(started):
            with pressed():
                _ = bench.queue_scoring(started, [scorer])
    return RedirectResponse(within(back or f"/review/{family}") + "#record", 303)


type _Given = str | int | list[str] | None


def _query(**given: _Given) -> str:
    pairs: list[tuple[str, str | int]] = [
        (k, v)
        for k, held in given.items()
        for v in (held if isinstance(held, list) else [held])
        if v is not None
    ]
    return "?" + urlencode(pairs) if pairs else ""


def _picked(shown: schemas.FamilyDetail, case: str | None) -> schemas.FamilyCase:
    picked = next((c for c in shown.cases if case in (None, c.case)), None)
    if picked is None:
        raise NotFound.of(
            "no case %(case)s of %(family)s", case=str(case), family=shown.name
        )
    return picked


def _moved(family: int, back: str | None, case: str) -> RedirectResponse:
    path, _, query = within(back or f"/review/{family}").partition("?")
    kept = [(k, v) for k, v in parse_qsl(query) if k != "case"]
    return RedirectResponse(f"{path}?{urlencode([*kept, ('case', case)])}", 303)


def _listed(
    every: list[schemas.Family], tag: list[str] | None, language: list[str] | None
) -> list[schemas.Family]:
    return [
        f
        for f in every
        if set(tag or ()) <= set(f.tags) and (not language or f.language in language)
    ]


def _toggled(picked: list[str] | None, value: str) -> list[str]:
    held = [p for p in picked or () if p != value]
    return held if value in (picked or ()) else [*held, value]


def _languages(
    bench: Bench, every: list[schemas.Family], current: str | None
) -> list[tuple[str, str]]:
    found = {f.language for f in every if f.language}
    found |= {t.language for t in api.threads(bench, "configuration") if t.language}
    for t in api.threads(bench, "translations"):
        found |= set(resolve(bench.store.get, t.head.digest, Translations).into)
    found |= {current} if current else set()
    return sorted(((t, display_language(t)) for t in found), key=lambda t: t[1])


def _marks(bench: Bench, every: list[schemas.Family]) -> dict[int, dict[str, Any]]:
    held = {f.id: f for f in bench.families()}
    ran: Counter[str] = Counter()
    for r in bench.runs():
        trial = resolve(bench.store.get, r.trial, Trial)
        for c in set(trial.cases):
            ran[c] += len(trial.seeds)
    found: dict[int, dict[str, Any]] = {}
    for f in every:
        family = held[f.id]
        bare = Case(vignette=family.vignette).digest
        found[f.id] = {
            "drifted": _drifted(bench, family.vignette),
            "appended": any(c != bare for c in family.cases),
            "ran": sum(ran[c] for c in family.cases),
        }
    return found


def _drifted(bench: Bench, vignette: Vignette) -> bool | None:
    if vignette.fingerprint.key_id is not None:
        return None
    try:
        raw = fetch_vignette(bench.conn, bench.inventory, vignette)
    except LookupError:
        return True
    return Fingerprint.of(raw) != vignette.fingerprint


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
        "me": bench.person.login,
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
        "name": tr("expectation for %(case)s", case=display_case(picked.titled)),
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
        labels = [named.get(i, tr("view %(n)s", n=i)) for i in range(len(held.views))]
        found.append((t, held, labels))
    return sorted(found, key=lambda s: (s[0].owner != login, s[0].name or s[0].title))


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
        for r in api_runs.runs(bench, reaching=case, limit=_ANSWERS)
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
        and (r.job is None or r.job.status not in _OPEN)
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
        plan = bench.answers(resolve(bench.store.get, r.skeleton, Skeleton)) == PLAN
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
                    "titled": r.titled,
                    "model": r.model,
                    "at": r.at,
                    "anchor": at,
                    "replicate": item.replicate,
                    "outcome": item.outcome,
                    "plan": plan,
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

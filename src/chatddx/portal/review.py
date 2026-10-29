from dataclasses import dataclass
from datetime import datetime
from typing import Annotated, Any
from urllib.parse import parse_qsl, urlencode
from uuid import UUID

from fastapi import APIRouter, Form, Query, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import JsonValue

from chatddx.api import (
    families as api_families,
    schemas,
    threads as api,
)
from chatddx.api.state import refused
from chatddx.bench import Bench, Endpoint, Family, NotFound, TriedVariation
from chatddx.bench.seen import trial
from chatddx.catalog import Subject, read
from chatddx.factors.base import Fingerprint, Invalid, resolve
from chatddx.factors.cases import Appendix, Case, Vignette
from chatddx.factors.gathering import REPLICATED, Center, Gathering
from chatddx.factors.request import Skeleton, Translations
from chatddx.factors.scoring import Expectation, ExpectationSchema, Scorer, Scoring
from chatddx.factors.select import Name, Token, parse_selector
from chatddx.factors.trial import Trial, suggest_seeds
from chatddx.ledger import RunStarted
from chatddx.locale import display_language, tr
from chatddx.runner import Refused, Running
from chatddx.runner.gate import bar
from chatddx.scorers.shipped import unit_of
from chatddx.store import Queue, fetch_vignette

from .pages import BenchDep, page, refusal_of, within
from .titles import display_case

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
    evaluation: UUID | None = None,
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
    every = api_families.families(bench)
    listed = _listed(every, tag, language)
    keep = {"tag": tag, "language": language, "schema": schema}
    own = _own(bench, expected)
    offered = (
        []
        if expected is None or expected.expectation is not None
        else [
            (t, resolve(bench.store.get, t.head.digest, Expectation).data)
            for t in expected.shared
        ]
    )
    seen = _seen(bench)
    appendices = _appendices(bench, picked.appendices, seen)
    branch = _branches(bench, bench.family(family), seen).get(picked.case)
    last = None if branch is None else seen[branch.appendices[-1]]
    live = _configurations(bench)
    named = {t.id: t.name or t.title for t in live}
    evaluations = _evaluations(bench, picked.case)
    busy = _busy(bench, evaluations)
    latest = _latest(bench, picked.case, evaluations)
    at = next((i for i, e in enumerate(evaluations) if e.first == evaluation), None)
    if evaluation is not None and at is None:
        raise NotFound.of(
            "no evaluation %(evaluation)s of %(case)s",
            evaluation=str(evaluation),
            case=display_case(picked.titled),
        )
    held = latest if at is None else evaluations[at]
    stepped = [*evaluations, *([] if latest is None else [latest])]
    step = len(stepped) - 1 if at is None else at
    evaluated = None if held is None else _evaluation(bench, held, under, named)
    behind = (
        []
        if held is None or held is not latest
        else _behind(bench, held, live, picked.case, under, expected, named)
    )
    query = request.url.query
    back = request.url.path + (f"?{query}" if query else "")
    props: dict[str, Any] = {
        "family": family,
        "case": picked.case,
        "expected": {
            "editor": _editing(bench, shown, picked, under, expected, own),
            "history": [] if own is None else _history(bench, own),
        },
        "appendices": appendices,
        "back": back,
        "evaluation": evaluated,
        "busy": None
        if busy is None
        else [str(r) for e in evaluations if e.first == busy for r in e.runs],
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
        marks=_marks(bench, every, seen),
        tags=sorted({t for f in every for t in f.tags}),
        languages=sorted({f.language for f in every if f.language}),
        tag=tag,
        keep=keep,
        toggled=_toggled,
        case=picked,
        appendices=appendices,
        deleting=None
        if last is None or last.owner != bench.person.login
        else last.name or last.title,
        visible=visible,
        schema=under,
        expected=expected,
        own=own,
        offered=offered,
        carried=_carried(bench, shown, picked, under, expected),
        runnable=sum(_placed(bench, t) is not None for t in live),
        busy=busy,
        evaluation=held,
        earlier=stepped[step - 1] if step > 0 else None,
        later=stepped[step + 1] if step + 1 < len(stepped) else None,
        behind=behind,
        left_out=[]
        if evaluated is None
        else [
            (named[t.id], why)
            for t in live
            if t.id not in {c["configuration"] for c in evaluated["configurations"]}
            and ((why := _unrunnable(bench, t, picked.case)) or held is not latest)
        ],
        back=back,
        props=props,
        query=_query,
        island="review",
    )


@router.post("/review/{family}/runs")
def running_in_review(
    bench: BenchDep,
    family: int,
    case: Annotated[str, Form()],
    back: Annotated[str | None, Form()] = None,
) -> Response:
    picked = _picked(api_families.family(bench, family), case)
    # Policy: as on the run page, a press made while an evaluation of the case is under
    # way counts as made: the page it leads back to shows that one.
    first = _busy(bench, _evaluations(bench, picked.case))
    if first is not None:
        return _evaluating(family, back, picked.case, first)
    begun: list[Running] = []
    for t in _configurations(bench):
        if (placed := _placed(bench, t)) is None:
            continue
        variation, at = placed
        drawn: dict[str, tuple[int, ...]] = {}
        for s in REPLICATED:
            each = drawn[s.name] = (
                suggest_seeds(s.seeds)
                if s.repeats is None
                else drawn[s.repeats][-s.seeds :]
            )
            try:
                started = bench.start(
                    variation, at.name, [picked.case], each, joining=first
                )
            except (Invalid, Refused):
                break
            begun += [running for _, running in started.runs]
            first = first or begun[0].started.run
    # Policy: queued once every run is begun, so that the worker sending the first
    # doesn't slow beginning the rest.
    with bench.conn.transaction():
        for running in begun:
            _ = bench.queue(running, True)
    if first is None:
        raise Invalid.of(
            "no configuration can run %(case)s now", case=display_case(picked.titled)
        )
    return _evaluating(family, back, picked.case, first)


def _evaluating(family: int, back: str | None, case: str, first: UUID) -> Response:
    path, _, query = within(back or f"/review/{family}").partition("?")
    kept = [(k, v) for k, v in parse_qsl(query) if k not in ("case", "evaluation")]
    said = urlencode([*kept, ("case", case), ("evaluation", str(first))])
    return RedirectResponse(f"{path}?{said}#evaluating", 303)


@dataclass(frozen=True)
class _Evaluated:
    first: UUID | None
    at: datetime
    gathering: Gathering

    @property
    def runs(self) -> tuple[UUID, ...]:
        return tuple(g.run for g in self.gathering.gathered)


# Policy: an evaluation is a start whose runs all gather about the case, each group
# whole, as running_in_review starts one; no run records where it was started.
def _evaluations(bench: Bench, case: str) -> list[_Evaluated]:
    runs = bench.runs(reaching=case)
    abouts = read.abouts(bench.rows, [Subject(run=r.run) for r in runs])
    started: dict[UUID, list[RunStarted]] = {}
    for r in runs:
        started.setdefault(abouts[Subject(run=r.run)].started_with or r.run, []).append(
            r
        )
    found: list[_Evaluated] = []
    for first, together in started.items():
        head = next((r for r in together if r.run == first), None)
        if head is None:
            continue
        held = bench.gathering(Center(component=case), REPLICATED, started_with=first)
        if (
            held is not None
            and len(held.gathered) == len(together)
            and all(len(g) == len(REPLICATED) for g in held.groups())
        ):
            found.append(_Evaluated(first, head.at, held))
    return sorted(found, key=lambda e: e.at)


# Policy: what the review shows unless asked for an evaluation: the latest of each
# configuration's runs across the case's evaluations, among their runs alone, so that
# no run of other cases mixes its items into the means.
def _latest(
    bench: Bench, case: str, evaluations: list[_Evaluated]
) -> _Evaluated | None:
    if not evaluations:
        return None
    runs = {r for e in evaluations for r in e.runs}
    held = bench.gathering(Center(component=case), REPLICATED, among=runs)
    return None if held is None else _Evaluated(None, evaluations[-1].at, held)


def _behind(
    bench: Bench,
    latest: _Evaluated,
    live: list[schemas.Thread],
    case: str,
    schema: str | None,
    expected: schemas.Expected | None,
    named: dict[int, str],
) -> list[tuple[str, str]]:
    by_id = {t.id: t for t in live}
    runs = latest.runs
    abouts = read.abouts(bench.rows, [Subject(run=r) for r in runs])
    placed = Queue(bench.conn).placed(runs)
    open_runs = {
        r for r in runs if r in placed and placed[r].job.status in _OPEN_STATUSES
    }
    flagged: list[tuple[str, str]] = []
    gathered: set[int] = set()
    for group in latest.gathering.groups():
        head = next(iter(group.values()))
        about = abouts[Subject(run=head.run)]
        varied = None if about.varied is None else bench.rows.edit(about.varied)
        thread = 0 if varied is None else varied.thread
        gathered.add(thread)
        name = named.get(thread, about.name or str(head.run))
        t = by_id.get(thread)
        if t is None:
            flagged.append((name, tr("it is no longer among your configurations")))
            continue
        if why := _unrunnable(bench, t, case):
            flagged.append((name, why))
            continue
        seeds = resolve(bench.store.get, head.trial, Trial).seeds
        if _trial_now(bench, t, case, seeds) != head.trial:
            flagged.append((name, tr("its configuration has changed since it ran")))
        mark = None if expected is None else expected.expectation
        if mark is not None and not all(
            g.run in open_runs or _scored_against(bench, g.run, schema, mark)
            for g in group.values()
        ):
            flagged.append(
                (name, tr("it isn't scored against the expectation as it is"))
            )
    flagged.extend(
        (named[t.id], tr("it has no runs yet"))
        for t in live
        if t.id not in gathered and _unrunnable(bench, t, case) is None
    )
    return flagged


def _trial_now(
    bench: Bench, t: schemas.Thread, case: str, seeds: tuple[int, ...]
) -> str | None:
    variation = bench.variation(t.id, {}, None)
    at = bench.at(variation)
    for each in bench.languages(variation, [case]):
        if each.skeleton is not None:
            cleanup = bench.cleanup(each.cases)
            _, made = trial(bench, each.skeleton, at.engine, each.cases, seeds, cleanup)
            return made.digest
    return None


def _scored_against(
    bench: Bench, run: UUID, schema: str | None, expectation: str
) -> bool:
    for started in bench.store.scores_of(run):
        scoring = resolve(bench.store.get, started.scoring, Scoring)
        scorer = resolve(bench.store.get, scoring.scorer, Scorer)
        if scorer.expectation_schema == schema and expectation in scoring.expectations:
            return True
    return False


_OPEN_STATUSES = ("queued", "under way")


def _busy(bench: Bench, evaluations: list[_Evaluated]) -> UUID | None:
    placed = Queue(bench.conn).placed([r for e in evaluations for r in e.runs])
    return next(
        (
            e.first
            for e in reversed(evaluations)
            if any(
                r in placed and placed[r].job.status in _OPEN_STATUSES for r in e.runs
            )
        ),
        None,
    )


@router.post("/review/{family}/delete")
def deleting_in_review(
    bench: BenchDep,
    family: int,
    case: Annotated[str, Form()],
    back: Annotated[str | None, Form()] = None,
) -> Response:
    shown = bench.family(family)
    seen = _seen(bench)
    branch = _branches(bench, shown, seen).get(case)
    if branch is None:
        raise NotFound.of(
            "no appendix to delete in case %(case)s of %(family)s",
            case=case,
            family=shown.name,
        )
    with refused():
        _ = bench.say(Subject(thread=seen[branch.appendices[-1]].id), deleted=True)
    return _moved(family, back, branch.parent)


type _Given = str | int | list[str] | None


def _query(**given: _Given) -> str:
    pairs: list[tuple[str, str | int]] = [
        (k, v)
        for k, held in given.items()
        for v in (held if isinstance(held, list) else [held])
        if v is not None
    ]
    return "?" + urlencode(pairs) if pairs else ""


def _configurations(bench: Bench) -> list[schemas.Thread]:
    login = bench.person.login
    found = api.threads(bench, "configuration", purpose="generation", owner=login)
    return sorted(found, key=lambda t: t.name or t.title)


def _placed(bench: Bench, t: schemas.Thread) -> tuple[TriedVariation, Endpoint] | None:
    if t.outdated:
        return None
    try:
        variation = bench.variation(t.id, {}, None)
        return variation, bench.at(variation)
    except (Invalid, NotFound):
        return None


def _unrunnable(bench: Bench, t: schemas.Thread, case: str) -> str | None:
    if t.outdated:
        return tr("it is out of date: update it on its page")
    try:
        variation = bench.variation(t.id, {}, None)
        at = bench.at(variation)
    except (Invalid, NotFound) as e:
        return refusal_of(e)
    for each in bench.languages(variation, [case]):
        if each.skeleton is None:
            return each.refused or tr(
                "it has no translation into %(language)s", language=str(each.language)
            )
        registry, made = trial(bench, each.skeleton, at.engine, each.cases, (0,))
        try:
            bar(bench.inventory, registry.get, at.name, made)
        except Refused as e:
            return refusal_of(e)
    return None


def _evaluation(
    bench: Bench,
    evaluated: _Evaluated,
    schema: str | None,
    named: dict[int, str],
) -> dict[str, Any]:
    runs = evaluated.runs
    abouts = read.abouts(bench.rows, [Subject(run=r) for r in runs])
    configurations: list[dict[str, Any]] = []
    for group in evaluated.gathering.groups():
        head = next(iter(group.values())).run
        about = abouts[Subject(run=head)]
        varied = None if about.varied is None else bench.rows.edit(about.varied)
        thread = 0 if varied is None else varied.thread
        held: list[dict[str, Any]] = []
        for g in group.values():
            trial = resolve(bench.store.get, g.trial, Trial)
            greedy = resolve(bench.store.get, trial.skeleton, Skeleton).greedy
            held.append(
                {"run": str(g.run), "seeds": list(trial.seeds), "greedy": greedy}
            )
        configurations.append(
            {
                "configuration": thread,
                "name": named.get(thread, about.name or str(head)),
                "runs": held,
            }
        )
    held_schema = (
        None if schema is None else resolve(bench.store.get, schema, ExpectationSchema)
    )
    properties = (
        {} if held_schema is None else held_schema.json_schema.get("properties")
    )
    return {
        "key": str(evaluated.first or evaluated.gathering.digest),
        "first": None if evaluated.first is None else str(evaluated.first),
        "case": evaluated.gathering.center.component,
        "configurations": sorted(configurations, key=lambda c: c["name"]),
        "fields": list(properties) if isinstance(properties, dict) else [],
        "scorers": _views(bench, schema),
    }


def _views(bench: Bench, schema: str | None) -> dict[str, list[dict[str, Any]]]:
    found: dict[str, list[dict[str, Any]]] = {}
    for t in api.threads(bench, "scorer"):
        held = resolve(bench.store.get, t.head.digest, Scorer)
        if held.expectation_schema != schema:
            continue
        labels = bench.labels(t.head.digest)
        found[t.head.digest] = [
            {
                "label": labels.get(i, tr("view %(n)s", n=i)),
                "field": _field(v.expectation),
                "unit": unit_of(held, i),
            }
            for i, v in enumerate(held.views)
        ]
    return found


def _field(selector: str) -> str | None:
    match parse_selector(selector)[:1]:
        case (Name(name=name),):
            return name
        case (Token(token=token),):
            return token
        case _:
            return None


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


def _seen(bench: Bench) -> dict[str, schemas.Thread]:
    login = bench.person.login
    held = sorted(api.threads(bench, "appendix"), key=lambda t: t.owner == login)
    return {t.head.digest: t for t in held}


@dataclass(frozen=True)
class _Branch:
    appendices: tuple[str, ...]
    parent: str


def _branches(
    bench: Bench, family: Family, seen: dict[str, schemas.Thread]
) -> dict[str, _Branch]:
    built: dict[tuple[str, ...], str] = {}
    for c in family.cases:
        appendices = resolve(bench.store.get, c, Case).appendices
        if c != family.case and appendices and all(a in seen for a in appendices):
            built[appendices] = c
    return {
        c: _Branch(
            appendices,
            next(
                (
                    built[appendices[:n]]
                    for n in range(len(appendices) - 1, 0, -1)
                    if appendices[:n] in built
                ),
                family.case,
            ),
        )
        for appendices, c in built.items()
    }


def _grown(
    branches: dict[str, _Branch], under: str, seen: dict[str, schemas.Thread]
) -> list[dict[str, Any]]:
    start = len(branches[under].appendices) if under in branches else 0
    found = [
        {
            "case": c,
            "names": [seen[a].name or seen[a].title for a in b.appendices[start:]],
            "branches": _grown(branches, c, seen),
        }
        for c, b in branches.items()
        if b.parent == under
    ]
    return sorted(found, key=lambda b: b["names"])


def _marks(
    bench: Bench, every: list[schemas.Family], seen: dict[str, schemas.Thread]
) -> dict[int, dict[str, Any]]:
    held = {f.id: f for f in bench.families()}
    found: dict[int, dict[str, Any]] = {}
    for f in every:
        family = held[f.id]
        branches = _branches(bench, family, seen)
        found[f.id] = {
            "drifted": _drifted(bench, family.vignette),
            "branches": _grown(branches, family.case, seen),
            "cases": {family.case, *branches},
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


def _appendices(
    bench: Bench, digests: list[str], seen: dict[str, schemas.Thread]
) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for d in digests:
        held = resolve(bench.store.get, d, Appendix)
        t = seen.get(d)
        mine = None if t is None or t.owner != bench.person.login else t
        found.append(
            {
                "digest": d,
                "title": bench.title(d),
                "text": held.text,
                "vignette": held.vignette.model_dump(mode="json"),
                "thread": None if mine is None else mine.id,
                "head": None if mine is None else mine.head.id,
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

from collections.abc import Generator, Hashable, Mapping
from contextlib import contextmanager
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
from chatddx.factors.gatherer import gather
from chatddx.factors.gathering import REPLICATED, Center, Gathering
from chatddx.factors.request import Skeleton, Translations
from chatddx.factors.scoring import Expectation, ExpectationSchema, Scorer, Scoring
from chatddx.factors.select import field
from chatddx.factors.trial import Trial, suggest_seeds
from chatddx.ledger import RunStarted
from chatddx.locale import display_language, tr
from chatddx.runner import Refused, Running
from chatddx.runner.gate import bar
from chatddx.scorers.shipped import read_by, unit_of
from chatddx.store import Queue, fetch_vignette

from .pages import BenchDep, page, refusal_of, within
from .runs import pressed
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
    visible = _schemas(bench)
    under = _under(visible, schema)
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
    entries = _entries(bench, picked.case, evaluations)
    at = next((i for i, e in enumerate(entries) if e.first == evaluation), None)
    if evaluation is not None and at is None:
        raise NotFound.of(
            "no evaluation %(evaluation)s of %(case)s",
            evaluation=str(evaluation),
            case=display_case(picked.titled),
        )
    if at is None and entries:
        at = len(entries) - 1
    held = None if at is None else entries[at]
    verdicts = _Verdicts(bench, entries, live, picked.case, under, expected, named)
    told = [verdicts.of(e) for e in entries]
    evaluated = None if held is None else _evaluation(bench, held, under, named)
    behind = [] if at is None else told[at] or []
    # Policy: one that matches is offered before a rework, so that what is there already
    # isn't run again.
    matched = next((e for e, v in zip(entries[::-1], told[::-1]) if v == []), None)
    editor = _editing(bench, shown, picked, under, expected, own)
    used = (
        None
        if held is None or editor is None or not any(b.rescore for b in behind)
        else _scored_with(bench, held, under, picked.case)
    )
    edit_from = (
        None
        if used is None or expected is None or used == expected.expectation
        else resolve(bench.store.get, used, Expectation).data
    )
    query = request.url.query
    back = request.url.path + (f"?{query}" if query else "")
    props: dict[str, Any] = {
        "family": family,
        "case": picked.case,
        "expected": {
            "editor": editor,
            "history": [] if own is None else _history(bench, own),
        },
        "appendices": appendices,
        "back": back,
        "evaluation": evaluated,
        "from": edit_from,
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
        entries=list(zip(entries, told, strict=True)),
        newest=entries[-1] if entries else None,
        behind=behind,
        matched=matched,
        edit_from=edit_from is not None,
        left_out=[]
        if evaluated is None
        else [
            (named[t.id], why)
            for t in live
            if t.id not in {c["configuration"] for c in evaluated["configurations"]}
            and (why := verdicts.unrunnable(t))
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
    chosen = [t for t in _configurations(bench) if _placed(bench, t) is not None]
    bench.check_quota([s.seeds for _ in chosen for s in REPLICATED])
    begun: list[Running] = []
    with _queueing(bench, begun):
        for t in chosen:
            begun += _begin(bench, t, picked.case, first)
            first = first or (begun[0].started.run if begun else None)
    if first is None:
        raise Invalid.of(
            "no configuration can run %(case)s now", case=display_case(picked.titled)
        )
    return _evaluating(family, back, picked.case, first)


@router.post("/review/{family}/rework")
def reworking_in_review(
    bench: BenchDep,
    family: int,
    case: Annotated[str, Form()],
    under: Annotated[str | None, Form()] = None,
    back: Annotated[str | None, Form()] = None,
) -> Response:
    picked = _picked(api_families.family(bench, family), case)
    schema = _under(_schemas(bench), under)
    evaluations = _evaluations(bench, picked.case)
    # Policy: as with Run, a press made while an evaluation of the case is under way
    # counts as made.
    if (busy := _busy(bench, evaluations)) is not None:
        return _evaluating(family, back, picked.case, busy)
    entries = _entries(bench, picked.case, evaluations)
    expected = next(
        (e for e in picked.expectations if e.expectation_schema == schema), None
    )
    live = _configurations(bench)
    named = {t.id: t.name or t.title for t in live}
    verdicts = _Verdicts(bench, entries, live, picked.case, schema, expected, named)
    behind = (verdicts.of(entries[-1]) if entries else None) or []
    rerun = [b for b in behind if b.rerun is not None]
    bench.check_quota([s.seeds for _ in rerun for s in REPLICATED])
    first: UUID | None = None
    begun: list[Running] = []
    with _queueing(bench, begun):
        for b in behind:
            if b.rerun is not None:
                begun += _begin(bench, b.rerun, picked.case, first, b.seeds)
                first = first or (begun[0].started.run if begun else None)
            for run in b.resume:
                with pressed():
                    _ = bench.queue(bench.resume(bench.run(run)))
            for run in b.rescore:
                if left := _stale(bench, run, schema):
                    with pressed():
                        _ = bench.queue_scoring(bench.run(run), left)
    return _moved(family, back, picked.case, "evaluating")


def _schemas(bench: Bench) -> list[schemas.Thread]:
    found = api.threads(bench, "expectation_schema")
    return sorted(found, key=lambda t: t.name or t.title)


def _under(visible: list[schemas.Thread], schema: str | None) -> str | None:
    under = next(
        (t.head.digest for t in visible if schema in (None, t.head.digest)), None
    )
    if schema is not None and under is None:
        raise NotFound.of("no expectation schema %(schema)s for you", schema=schema)
    return under


def _begin(
    bench: Bench,
    t: schemas.Thread,
    case: str,
    first: UUID | None,
    seeds: Mapping[str, tuple[int, ...]] | None = None,
) -> list[Running]:
    if (placed := _placed(bench, t)) is None:
        return []
    variation, at = placed
    drawn: dict[str, tuple[int, ...]] = {}
    begun: list[Running] = []
    for s in REPLICATED:
        each = drawn[s.name] = (
            seeds[s.name]
            if seeds is not None and s.name in seeds
            else suggest_seeds(s.seeds)
            if s.repeats is None
            else drawn[s.repeats][-s.seeds :]
        )
        joining = first or (begun[0].started.run if begun else None)
        try:
            started = bench.start(variation, at.name, [case], each, joining=joining)
        except (Invalid, Refused):
            break
        begun += [running for _, running in started.runs]
    return begun


# Policy: queued once every run is begun, so that the worker sending the first doesn't
# slow beginning the rest, and queued too when beginning one fails, so that none is left
# begun with nothing to send it.
@contextmanager
def _queueing(bench: Bench, begun: list[Running]) -> Generator[None]:
    try:
        yield
    finally:
        with bench.conn.transaction():
            for running in begun:
                _ = bench.queue(running, True)


def _evaluating(family: int, back: str | None, case: str, first: UUID) -> Response:
    path, _, query = within(back or f"/review/{family}").partition("?")
    kept = [(k, v) for k, v in parse_qsl(query) if k not in ("case", "evaluation")]
    said = urlencode([*kept, ("case", case), ("evaluation", str(first))])
    return RedirectResponse(f"{path}?{said}#evaluating", 303)


@dataclass(frozen=True)
class _Evaluated:
    first: UUID
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


# Policy: an entry is the case as it stood once an evaluation was started: the latest of
# each configuration's runs across the evaluations up to it, among their runs alone, so
# that no run of other cases mixes its items into the means, and a rework that starts
# only some configurations' runs still makes a whole one.
def _entries(
    bench: Bench, case: str, evaluations: list[_Evaluated]
) -> list[_Evaluated]:
    if not evaluations:
        return []
    started = {r.run: r for r in bench.runs(reaching=case)}
    ids = [r for e in evaluations for r in e.runs]
    abouts = read.abouts(bench.rows, [Subject(run=r) for r in ids])
    keys: dict[UUID, Hashable] = {}
    for r in ids:
        about = abouts[Subject(run=r)]
        edit = None if about.varied is None else bench.rows.edit(about.varied)
        # Duplication: src/chatddx/bench/gathering.py:gathering keys its groups alike.
        keys[r] = started[r].trial if edit is None else edit.thread
    found: list[UUID] = []
    entries: list[_Evaluated] = []
    for e in evaluations:
        found += e.runs
        ordered = sorted(found, key=lambda r: started[r].at, reverse=True)
        held = gather(
            Center(component=case),
            REPLICATED,
            [(keys[r], r, started[r].trial) for r in ordered],
            bench.store.get,
        )
        if held is not None:
            entries.append(_Evaluated(e.first, e.at, held))
    return entries


@dataclass(frozen=True)
class _Behind:
    name: str
    why: str
    rerun: schemas.Thread | None = None
    seeds: Mapping[str, tuple[int, ...]] | None = None
    rescore: tuple[UUID, ...] = ()
    resume: tuple[UUID, ...] = ()

    @property
    def reworked(self) -> bool:
        return self.rerun is not None or bool(self.rescore or self.resume)


# Policy: what no longer holds of each entry, or None while its runs are under way, with
# what each configuration and run says worked out once, as the same recur in the
# entries after the one they first gather in.
class _Verdicts:
    def __init__(
        self,
        bench: Bench,
        entries: list[_Evaluated],
        live: list[schemas.Thread],
        case: str,
        schema: str | None,
        expected: schemas.Expected | None,
        named: dict[int, str],
    ) -> None:
        self._bench: Bench = bench
        self._live: list[schemas.Thread] = live
        self._case: str = case
        self._schema: str | None = schema
        self._marked: bool = expected is not None and expected.expectation is not None
        self._named: dict[int, str] = named
        runs = list({r for e in entries for r in e.runs})
        self._abouts: dict[Subject, Any] = read.abouts(
            bench.rows, [Subject(run=r) for r in runs]
        )
        self._placed: dict[UUID, Any] = Queue(bench.conn).placed(runs)
        self._finished: set[UUID] = bench.store.finished(runs)
        self._unrunnable: dict[int, str | None] = {}
        self._trials: dict[tuple[int, tuple[int, ...]], str | None] = {}
        self._stale: dict[UUID, bool] = {}

    def status(self, run: UUID) -> str | None:
        held = self._placed.get(run)
        return None if held is None else held.job.status

    def unrunnable(self, t: schemas.Thread) -> str | None:
        if t.id not in self._unrunnable:
            self._unrunnable[t.id] = _unrunnable(self._bench, t, self._case)
        return self._unrunnable[t.id]

    def of(self, entry: _Evaluated) -> list[_Behind] | None:
        if any(self.status(r) in _OPEN_STATUSES for r in entry.runs):
            return None
        by_id = {t.id: t for t in self._live}
        flagged: list[_Behind] = []
        gathered: set[int] = set()
        for group in entry.gathering.groups():
            head = next(iter(group.values()))
            about = self._abouts[Subject(run=head.run)]
            rows = self._bench.rows
            varied = None if about.varied is None else rows.edit(about.varied)
            thread = 0 if varied is None else varied.thread
            gathered.add(thread)
            name = self._named.get(thread, about.name or str(head.run))
            t = by_id.get(thread)
            if t is None:
                flagged.append(
                    _Behind(name, tr("it is no longer among your configurations"))
                )
                continue
            if why := self.unrunnable(t):
                flagged.append(_Behind(name, why))
                continue
            seeds = {
                s: resolve(self._bench.store.get, g.trial, Trial).seeds
                for s, g in group.items()
            }
            changed = self._trial(t, seeds[head.seeding]) != head.trial
            halted = any(self.status(g.run) == "stopped" for g in group.values())
            if changed or halted:
                why = (
                    tr("its configuration has changed since it ran")
                    if changed
                    else tr("it was halted before it finished")
                )
                flagged.append(_Behind(name, why, rerun=t, seeds=seeds))
                continue
            if unsent := tuple(
                g.run for g in group.values() if g.run not in self._finished
            ):
                flagged.append(
                    _Behind(name, tr("it stopped before it finished"), resume=unsent)
                )
            if self._marked and (
                unscored := tuple(
                    g.run for g in group.values() if self._stale_run(g.run)
                )
            ):
                flagged.append(
                    _Behind(
                        name,
                        tr("it isn't scored against the expectation as it is"),
                        rescore=unscored,
                    )
                )
        flagged.extend(
            _Behind(self._named[t.id], tr("it has no runs yet"), rerun=t)
            for t in self._live
            if t.id not in gathered and self.unrunnable(t) is None
        )
        return flagged

    def _trial(self, t: schemas.Thread, seeds: tuple[int, ...]) -> str | None:
        if (t.id, seeds) not in self._trials:
            self._trials[t.id, seeds] = _trial_now(self._bench, t, self._case, seeds)
        return self._trials[t.id, seeds]

    def _stale_run(self, run: UUID) -> bool:
        if run not in self._stale:
            self._stale[run] = bool(_stale(self._bench, run, self._schema))
        return self._stale[run]


# Policy: the expectation the entry's newest scores under the schema were scored against,
# or None when its scores were scored against expectations that read differently.
def _scored_with(
    bench: Bench, entry: _Evaluated, schema: str | None, case: str
) -> str | None:
    used: list[tuple[datetime, str]] = []
    scorers: dict[str, Scorer] = {}
    for run in entry.runs:
        for started in bench.store.scores_of(run):
            scoring = resolve(bench.store.get, started.scoring, Scoring)
            scorer = resolve(bench.store.get, scoring.scorer, Scorer)
            if scorer.expectation_schema != schema:
                continue
            scorers[scoring.scorer] = scorer
            used += [
                (started.at, e)
                for e in scoring.expectations
                if resolve(bench.store.get, e, Expectation).case == case
            ]
    if not used:
        return None
    newest = max(used)[1]
    data = {e: resolve(bench.store.get, e, Expectation).data for _, e in used}
    try:
        alike = all(
            read_by(s, data[e]) == read_by(s, data[newest])
            for s in scorers.values()
            for e in data
        )
    except LookupError:
        return None
    return newest if alike else None


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


def _stale(bench: Bench, run: UUID, schema: str | None) -> list[str]:
    started = bench.run(run)
    if run not in bench.store.finished([run]):
        return []
    return [
        s
        for s in bench.unscored(started)
        if resolve(bench.store.get, s, Scorer).expectation_schema == schema
    ]


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
        "key": str(evaluated.first),
        "first": str(evaluated.first),
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
                "field": field(v.expectation),
                "unit": unit_of(held, i),
            }
            for i, v in enumerate(held.views)
        ]
    return found


def _picked(shown: schemas.FamilyDetail, case: str | None) -> schemas.FamilyCase:
    picked = next((c for c in shown.cases if case in (None, c.case)), None)
    if picked is None:
        raise NotFound.of(
            "no case %(case)s of %(family)s", case=str(case), family=shown.name
        )
    return picked


def _moved(
    family: int, back: str | None, case: str, at: str | None = None
) -> RedirectResponse:
    path, _, query = within(back or f"/review/{family}").partition("?")
    dropped = ("case",) if at is None else ("case", "evaluation")
    kept = [(k, v) for k, v in parse_qsl(query) if k not in dropped]
    said = urlencode([*kept, ("case", case)])
    return RedirectResponse(f"{path}?{said}{'' if at is None else '#' + at}", 303)


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
            "data": expected.data,
        }
    return {
        **given,
        "mode": "new",
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

import hashlib
import json
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from pydantic import JsonValue

from chatddx.catalog import Subject, read
from chatddx.catalog.language import languages_of
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Scoring
from chatddx.factors.trial import Trial
from chatddx.ledger import RunStarted
from chatddx.ledger.call import Call
from chatddx.ledger.run import RunItem
from chatddx.store.cache import Cache, catalogued

from .seen import Seen


@dataclass(frozen=True)
class Sent:
    """An item of a run as a breakdown reads it, `said` None where it answered
    nothing."""

    case: str
    replicate: int
    failed: bool
    seconds: float
    tokens: int | None
    said: str | None


@dataclass(frozen=True)
class Ran:
    """A finished run as a breakdown reads it, `digest` its version's skeleton and
    `started_with` its own id where it began its start."""

    run: UUID
    at: datetime
    trial: str
    skeleton: str
    language: str | None
    cases: tuple[str, ...]
    seeds: tuple[int, ...]
    configuration: int | None
    version: int | None
    digest: str | None
    replaced: bool
    started_with: UUID
    items: tuple[Sent, ...]


@dataclass(frozen=True)
class Valued:
    """A finished score as a breakdown reads it, each value with its case, replicate
    and view."""

    score: UUID
    at: datetime
    scorer: str
    values: tuple[tuple[str, int, int, float | None], ...]


@dataclass(frozen=True)
class Observed:
    """A finished run with the latest finished score of each scorer, and the scorers
    it isn't scored by as things are now."""

    ran: Ran
    scores: tuple[Valued, ...]
    unscored: frozenset[str]


# Policy: so many finished runs and scores held as rows and no more: what a run or a
# score finished with is sealed, so one is held without a version; what isn't scored as
# things are now is held while the catalog stands and the run's scores are the same.
_RAN: Cache[UUID, Ran] = Cache(50_000)
_VALUED: Cache[UUID, Valued] = Cache(200_000)
_UNSCORED: Cache[tuple[UUID, frozenset[UUID]], frozenset[str]] = Cache(50_000)


def observed(seen: Seen, runs: Sequence[RunStarted]) -> list[Observed]:
    """The runs that finished, each with its finished scores and what it isn't scored
    by as things are now, in the order given. Held rows cost nothing to read again;
    each run not held reads its log once with its catalog rows, each score not held
    reads its log, and each run's scores are listed once, and, once the catalog has
    changed, what `seen.unscored` costs."""
    finished = seen.store.finished([r.run for r in runs])
    done = [r for r in runs if r.run in finished]
    version = catalogued(seen.conn)
    ran = _ran(seen, done)
    found: list[Observed] = []
    for r in done:
        given = [s for s in seen.store.scores_of(r.run)]
        latest: dict[str, Valued] = {}
        for started in given:
            valued = _valued(seen, started.score)
            if valued is not None and valued.scorer not in latest:
                latest[valued.scorer] = valued
        key = (r.run, frozenset(s.score for s in given))
        unscored = _UNSCORED.get(seen.conn, key, version)
        if unscored is None:
            unscored = frozenset(seen.unscored(r))
            _UNSCORED.put(seen.conn, key, unscored, version)
        found.append(Observed(ran[r.run], tuple(latest.values()), unscored))
    return found


def _ran(seen: Seen, runs: Sequence[RunStarted]) -> dict[UUID, Ran]:
    held = {r.run: _RAN.get(seen.conn, r.run) for r in runs}
    missing = [r for r in runs if held[r.run] is None]
    if missing:
        abouts = read.abouts(seen.rows, [Subject(run=r.run) for r in missing])
        trials = {r.run: resolve(seen.store.get, r.trial, Trial) for r in missing}
        languages = languages_of(seen.rows, {t.skeleton for t in trials.values()})
        for r in missing:
            about = abouts[Subject(run=r.run)]
            edit = None if about.varied is None else seen.rows.edit(about.varied)
            trial = trials[r.run]
            made = Ran(
                run=r.run,
                at=r.at,
                trial=r.trial,
                skeleton=trial.skeleton,
                language=languages[trial.skeleton],
                cases=trial.cases,
                seeds=trial.seeds,
                configuration=None if edit is None else edit.thread,
                version=None if edit is None else edit.id,
                digest=None if edit is None else edit.digest,
                replaced=bool(about.replaced),
                started_with=about.started_with or r.run,
                items=tuple(_sent(i) for i in seen.store.run(r.run).items),
            )
            _RAN.put(seen.conn, r.run, made)
            held[r.run] = made
    return {k: v for k, v in held.items() if v is not None}


def _valued(seen: Seen, score: UUID) -> Valued | None:
    if (held := _VALUED.get(seen.conn, score)) is not None:
        return held
    made = seen.store.score(score)
    if made.finished is None:
        return None
    scorer = resolve(seen.store.get, made.started.scoring, Scoring).scorer
    valued = Valued(
        score=score,
        at=made.started.at,
        scorer=scorer,
        values=tuple(
            (i.key.case, i.key.replicate, i.view, i.value) for i in made.items
        ),
    )
    _VALUED.put(seen.conn, score, valued)
    return valued


def _sent(item: RunItem) -> Sent:
    calls = [item.call, *(t.call for t in item.turns if t.call is not None)]
    last = calls[-1]
    return Sent(
        case=item.key.case,
        replicate=item.key.replicate,
        failed=any(_failed(c) for c in calls),
        seconds=sum((c.finished_at - c.started_at).total_seconds() for c in calls),
        tokens=_tokens(calls),
        said=_said(last.response),
    )


def _failed(call: Call) -> bool:
    return call.error is not None or call.response is None or call.status != 200


def _tokens(calls: Sequence[Call]) -> int | None:
    found: list[int] = []
    for c in calls:
        match c.response:
            case {"usage": {"completion_tokens": int() as tokens}}:
                found.append(tokens)
            case _:
                pass
    return sum(found) if found else None


# Policy: what an item answered is its last message's text and the names and arguments
# of its tool calls, so that two answers alike to the letter share a digest whatever
# else their responses hold, the calls' ids among it.
def _said(response: dict[str, JsonValue] | None) -> str | None:
    match response:
        case {"choices": [{"message": dict() as message}, *_]}:
            calls = message.get("tool_calls")
            kept = {
                "content": message.get("content"),
                "calls": [
                    c.get("function") if isinstance(c, dict) else c
                    for c in (calls if isinstance(calls, list) else [])
                ],
            }
            raw = json.dumps(kept, sort_keys=True).encode()
            return "sha256:" + hashlib.sha256(raw).hexdigest()
        case _:
            return None

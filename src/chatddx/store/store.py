import json
from collections.abc import Collection, Iterable
from typing import LiteralString
from uuid import UUID

import psycopg
from psycopg.rows import TupleRow

from chatddx.factors.base import Component, StructuralError, resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.request import Compilation
from chatddx.ledger import (
    CanaryCall,
    Record,
    Run,
    RunFinished,
    RunItem,
    RunStarted,
    Score,
    ScoreFinished,
    ScoreItem,
    ScoreStarted,
)

from .cache import Cache
from .notify import ROWS, channel

Connection = psycopg.Connection[TupleRow]

type Written = tuple[int, Record]

_TOLD: dict[str, type[Record]] = {
    "run started": RunStarted,
    "run finished": RunFinished,
    "run item": RunItem,
    "canary call": CanaryCall,
    "score started": ScoreStarted,
    "score finished": ScoreFinished,
    "score item": ScoreItem,
}


# Policy: so many components held parsed and no more: factor.component is insert-only
# and a digest names what it holds, so one is held without a version.
_PARSED: Cache[str, Component] = Cache(20_000)

# Policy: so many finished runs and scores held and no more: the ledger is insert-only
# and a finished record seals what was written before it, so one is held without a
# version; one not finished is read anew each time.
_RUNS: Cache[UUID, Run] = Cache(2_000)
_SCORES: Cache[UUID, Score] = Cache(20_000)


class Store:
    def __init__(self, conn: Connection) -> None:
        self._conn: Connection = conn

    def add(self, registry: Registry, roots: Iterable[str]) -> list[str]:
        digests = registry.closure(roots)
        registry.check(digests)
        with self._conn.transaction(), self._conn.cursor() as cur:
            for d in digests:
                raw = registry.get(d).canonical.decode()
                doc = json.loads(raw)
                _ = cur.execute(
                    """
                    INSERT INTO factor.component (digest, kind, v, canonical, doc)
                    VALUES (%s, %s, %s, %s, %s::jsonb)
                    ON CONFLICT DO NOTHING
                    """,
                    (d, doc["kind"], doc["v"], raw, raw),
                )
                cur.executemany(
                    """
                    INSERT INTO factor.component_ref (src, path, dst, kinds)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                    """,
                    [
                        (d, site.path, site.digest, list(site.kinds))
                        for site in registry.get(d).refs()
                    ],
                )
        return digests

    def get(self, digest: str) -> Component:
        if (held := _PARSED.get(self._conn, digest)) is not None:
            return held
        row = self._conn.execute(
            "SELECT canonical FROM factor.component WHERE digest = %s", (digest,)
        ).fetchone()
        if row is None:
            raise StructuralError(f"{digest} is not in the store")
        component = Registry().add_raw(digest, str(row[0]).encode())
        _PARSED.put(self._conn, digest, component)
        return component

    def load(self, roots: Iterable[str]) -> Registry:
        roots = list(roots)
        rows = self._conn.execute(
            """
            WITH RECURSIVE closure (digest) AS (
                SELECT unnest(%s::text[])
                UNION
                SELECT r.dst FROM factor.component_ref r
                JOIN closure c ON r.src = c.digest
            )
            SELECT c.digest, c.canonical
            FROM closure JOIN factor.component c USING (digest)
            """,
            (roots,),
        ).fetchall()
        registry = Registry()
        for digest, canonical in rows:
            if (held := _PARSED.get(self._conn, str(digest))) is not None:
                _ = registry.add(held)
            else:
                parsed = registry.add_raw(str(digest), str(canonical).encode())
                _PARSED.put(self._conn, parsed.digest, parsed)
        if missing := [r for r in roots if r not in registry]:
            raise StructuralError(f"not in the store: {missing}")
        return registry

    def append(self, *records: Record) -> None:
        with self._conn.transaction(), self._conn.cursor() as cur:
            for record in records:
                payload = record.canonical.decode()
                match record:
                    case RunStarted() | RunFinished():
                        trial = record.trial if isinstance(record, RunStarted) else None
                        _ = cur.execute(
                            """
                            INSERT INTO ledger.run_stage (run, stage, trial, payload, doc)
                            VALUES (%s, %s, %s, %s, %s::jsonb)
                            """,
                            (record.run, record.stage, trial, payload, payload),
                        )
                    case RunItem():
                        _ = cur.execute(
                            """
                            INSERT INTO ledger.run_item (run, "case", replicate, payload, doc)
                            VALUES (%s, %s, %s, %s, %s::jsonb)
                            """,
                            (
                                record.run,
                                record.key.case,
                                record.key.replicate,
                                payload,
                                payload,
                            ),
                        )
                    case CanaryCall():
                        _ = cur.execute(
                            """
                            INSERT INTO ledger.canary_call (run, phase, canary, payload, doc)
                            VALUES (%s, %s, %s, %s, %s::jsonb)
                            """,
                            (record.run, record.phase, record.canary, payload, payload),
                        )
                    case ScoreStarted():
                        _ = cur.execute(
                            """
                            INSERT INTO ledger.score_stage (score, stage, run, run_stage, scoring, payload, doc)
                            VALUES (%s, %s, %s, 'started', %s, %s, %s::jsonb)
                            """,
                            (
                                record.score,
                                record.stage,
                                record.run,
                                record.scoring,
                                payload,
                                payload,
                            ),
                        )
                    case ScoreFinished():
                        _ = cur.execute(
                            """
                            INSERT INTO ledger.score_stage (score, stage, payload, doc)
                            VALUES (%s, %s, %s, %s::jsonb)
                            """,
                            (record.score, record.stage, payload, payload),
                        )
                    case ScoreItem():
                        _ = cur.execute(
                            """
                            INSERT INTO ledger.score_item (score, "case", replicate, view, payload, doc)
                            VALUES (%s, %s, %s, %s, %s, %s::jsonb)
                            """,
                            (
                                record.score,
                                record.key.case,
                                record.key.replicate,
                                record.view,
                                payload,
                                payload,
                            ),
                        )
                    case _:
                        raise TypeError(f"no table for {type(record).__name__}")
            for run in _runs_of(cur, records):
                _ = cur.execute("SELECT pg_notify(%s, %s)", (channel(run), ROWS))

    def run(self, run: UUID) -> Run:
        if (held := _RUNS.get(self._conn, run)) is not None:
            return held
        made = self._run(run)
        if made.finished is not None:
            _RUNS.put(self._conn, run, made)
        return made

    def _run(self, run: UUID) -> Run:
        started, finished = self._stages(
            "SELECT stage, payload FROM ledger.run_stage WHERE run = %s", "run", run
        )
        return Run(
            started=RunStarted.parse(started),
            finished=None if finished is None else RunFinished.parse(finished),
            items=tuple(
                RunItem.parse(p)
                for p in self._payloads(
                    "SELECT payload FROM ledger.run_item WHERE run = %s", run
                )
            ),
            canaries=tuple(
                CanaryCall.parse(p)
                for p in self._payloads(
                    "SELECT payload FROM ledger.canary_call WHERE run = %s", run
                )
            ),
        )

    def score(self, score: UUID) -> Score:
        if (held := _SCORES.get(self._conn, score)) is not None:
            return held
        made = self._score(score)
        if made.finished is not None:
            _SCORES.put(self._conn, score, made)
        return made

    def _score(self, score: UUID) -> Score:
        started, finished = self._stages(
            "SELECT stage, payload FROM ledger.score_stage WHERE score = %s",
            "score",
            score,
        )
        return Score(
            started=ScoreStarted.parse(started),
            finished=None if finished is None else ScoreFinished.parse(finished),
            items=tuple(
                ScoreItem.parse(p)
                for p in self._payloads(
                    "SELECT payload FROM ledger.score_item WHERE score = %s", score
                )
            ),
        )

    def rows_of(self, run: UUID, after: int = 0) -> list[Written]:
        rows = self._conn.execute(
            """
            SELECT seq, 'run ' || stage, payload FROM ledger.run_stage
            WHERE run = %(run)s AND seq > %(after)s
            UNION ALL
            SELECT seq, 'run item', payload FROM ledger.run_item
            WHERE run = %(run)s AND seq > %(after)s
            UNION ALL
            SELECT seq, 'canary call', payload FROM ledger.canary_call
            WHERE run = %(run)s AND seq > %(after)s
            UNION ALL
            SELECT s.seq, 'score ' || s.stage, s.payload FROM ledger.score_stage s
            JOIN ledger.score_stage o ON o.score = s.score AND o.stage = 'started'
            WHERE o.run = %(run)s AND s.seq > %(after)s
            UNION ALL
            SELECT i.seq, 'score item', i.payload FROM ledger.score_item i
            JOIN ledger.score_stage o ON o.score = i.score AND o.stage = 'started'
            WHERE o.run = %(run)s AND i.seq > %(after)s
            ORDER BY 1
            """,
            {"run": run, "after": after},
        ).fetchall()
        return [(int(seq), _TOLD[str(kind)].parse(str(p))) for seq, kind, p in rows]

    def started(self, runs: Collection[UUID]) -> list[RunStarted]:
        return _newest(
            RunStarted.parse(p)
            for p in self._payloads(
                """
                SELECT payload FROM ledger.run_stage
                WHERE stage = 'started' AND run = ANY(%s::uuid[])
                """,
                list(runs),
            )
        )

    def finished(self, runs: Collection[UUID]) -> set[UUID]:
        rows = self._conn.execute(
            """
            SELECT run FROM ledger.run_stage
            WHERE stage = 'finished' AND run = ANY(%s::uuid[])
            """,
            (list(runs),),
        ).fetchall()
        return {UUID(str(run)) for (run,) in rows}

    def scores_of(self, run: UUID) -> list[ScoreStarted]:
        return _newest(
            ScoreStarted.parse(p)
            for p in self._payloads(
                """
                SELECT payload FROM ledger.score_stage
                WHERE stage = 'started' AND run = %s
                """,
                run,
            )
        )

    def reaching(self, digest: str, kind: str) -> list[str]:
        rows = self._conn.execute(
            """
            WITH RECURSIVE up (digest) AS (
                SELECT %s::text
                UNION
                SELECT r.src FROM factor.component_ref r JOIN up ON r.dst = up.digest
            )
            SELECT c.digest FROM factor.component c JOIN up USING (digest)
            WHERE c.kind = %s
            ORDER BY c.digest
            """,
            (digest, kind),
        ).fetchall()
        return [str(d) for (d,) in rows]

    def compilations(self, skeleton: str) -> list[Compilation]:
        rows = self._conn.execute(
            """
            SELECT r.src FROM factor.component_ref r
            JOIN factor.component c ON c.digest = r.src
            WHERE c.kind = 'compilation' AND r.path = '/skeleton' AND r.dst = %s
            ORDER BY r.src
            """,
            (skeleton,),
        ).fetchall()
        return [resolve(self.get, str(src), Compilation) for (src,) in rows]

    def _payloads(self, query: LiteralString, key: object) -> list[str]:
        return [str(p) for (p,) in self._conn.execute(query, (key,))]

    def _stages(
        self, query: LiteralString, log: str, key: UUID
    ) -> tuple[str, str | None]:
        stages = {str(s): str(p) for s, p in self._conn.execute(query, (key,))}
        if not stages:
            raise LookupError(f"{log} {key} is not in the store")
        if "started" not in stages:
            raise StructuralError(f"{log} {key} has no started row")
        return stages["started"], stages.get("finished")


def _runs_of(cur: psycopg.Cursor[TupleRow], records: Iterable[Record]) -> set[UUID]:
    runs: set[UUID] = set()
    scores: list[UUID] = []
    for record in records:
        match record:
            case (
                RunStarted() | RunFinished() | RunItem() | CanaryCall() | ScoreStarted()
            ):
                runs.add(record.run)
            case ScoreFinished() | ScoreItem():
                scores.append(record.score)
            case _:
                pass
    if scores:
        rows = cur.execute(
            """
            SELECT run FROM ledger.score_stage
            WHERE stage = 'started' AND score = ANY(%s::uuid[])
            """,
            (scores,),
        ).fetchall()
        runs.update(UUID(str(run)) for (run,) in rows)
    return runs


def _newest[S: RunStarted | ScoreStarted](started: Iterable[S]) -> list[S]:
    return sorted(started, key=lambda s: s.at, reverse=True)

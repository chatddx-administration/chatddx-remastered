from collections.abc import Collection, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal, cast, get_args
from uuid import UUID

from psycopg import errors

from chatddx.factors.base import Missing, Worded

from .notify import JOB, WORKERS, channel
from .store import Connection

Status = Literal["queued", "under way", "finished", "stopped", "failed"]
_ENDED: tuple[Status, ...] = ("finished", "stopped", "failed")
STATUSES: tuple[Status, ...] = get_args(Status)

TAKEN_OUT = "taken out of the queue"

_COLUMNS = """
    j.id, j.owner, j.run, j.endpoint, j.slots, j.score, j.scorers, j.scored, j.status,
    j.why, j.halt, j.worker, j.queued, j.claimed, j.beat, j.ended
"""

_OPEN = "j.status IN ('queued', 'under way')"

_PAUSED = """
    EXISTS (SELECT 1 FROM worker.control c WHERE c.owner = j.owner AND c.paused)
"""

_LIVE = "j.beat > now() - %(lost)s"


class UnderWay(Worded, ValueError):
    pass


@dataclass(frozen=True)
class Job:
    id: int
    owner: int
    run: UUID
    endpoint: str
    slots: int
    score: bool
    scorers: tuple[str, ...] | None
    scored: tuple[str, ...]
    status: Status
    why: str | None
    halt: bool
    worker: UUID | None
    queued: datetime
    claimed: datetime | None
    beat: datetime | None
    ended: datetime | None


@dataclass(frozen=True)
class Held:
    job: int
    halt: bool
    paused: bool


@dataclass(frozen=True)
class Placed:
    job: Job
    ahead: int | None


@dataclass(frozen=True)
class Standing:
    paused: bool
    queued: int
    under_way: int
    workers: int


@dataclass(frozen=True)
class Stopped:
    taken_out: tuple[UUID, ...]
    halting: tuple[UUID, ...]


def _job(row: tuple[Any, ...]) -> Job:
    (
        id,
        owner,
        run,
        endpoint,
        slots,
        score,
        scorers,
        scored,
        status,
        why,
        halt,
        worker,
        queued,
        claimed,
        beat,
        ended,
    ) = row
    return Job(
        id=id,
        owner=owner,
        run=run,
        endpoint=endpoint,
        slots=slots,
        score=score,
        scorers=None if scorers is None else tuple(scorers),
        scored=tuple(scored),
        status=cast(Status, status),
        why=why,
        halt=halt,
        worker=worker,
        queued=queued,
        claimed=claimed,
        beat=beat,
        ended=ended,
    )


class Queue:
    def __init__(self, conn: Connection) -> None:
        self._conn: Connection = conn

    def put(
        self,
        owner: int,
        run: UUID,
        endpoint: str,
        slots: int,
        score: bool,
        scorers: Collection[str] | None = None,
    ) -> Job:
        try:
            with self._conn.transaction():
                row = self._conn.execute(
                    f"""
                    INSERT INTO worker.job AS j
                        (owner, run, endpoint, slots, score, scorers)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING {_COLUMNS}
                    """,
                    (
                        owner,
                        run,
                        endpoint,
                        slots,
                        score,
                        None if scorers is None else sorted(set(scorers)),
                    ),
                ).fetchone()
                self._tell(run, "queued")
        except errors.UniqueViolation:
            raise UnderWay.of(
                "run %(run)s has something under way", run=str(run)
            ) from None
        assert row is not None
        return _job(row)

    def open(self, run: UUID) -> Job | None:
        row = self._conn.execute(
            f"SELECT {_COLUMNS} FROM worker.job j WHERE j.run = %s AND {_OPEN}", (run,)
        ).fetchone()
        return None if row is None else _job(row)

    # Policy: a queued job's place is the jobs at its endpoint under way, or queued before
    # it and to be claimed; none while its owner has paused.
    def placed(self, runs: Collection[UUID]) -> dict[UUID, Placed]:
        rows = self._conn.execute(
            f"""
            SELECT {_COLUMNS},
                CASE WHEN j.status = 'queued' AND (j.halt OR NOT {_PAUSED}) THEN (
                    SELECT count(*) FROM worker.job a
                    WHERE a.endpoint = j.endpoint
                        AND (a.queued, a.id) < (j.queued, j.id)
                        AND (
                            a.status = 'under way'
                            OR (a.status = 'queued' AND NOT EXISTS (
                                SELECT 1 FROM worker.control c
                                WHERE c.owner = a.owner AND c.paused AND NOT a.halt
                            ))
                        )
                ) END
            FROM (
                SELECT DISTINCT ON (run) * FROM worker.job
                WHERE run = ANY(%s::uuid[]) ORDER BY run, id DESC
            ) j
            """,
            (list(runs),),
        ).fetchall()
        return {
            UUID(str(row[2])): Placed(
                _job(row[:-1]), None if row[-1] is None else int(row[-1])
            )
            for row in rows
        }

    def standing(self, owner: int, lost: timedelta) -> Standing:
        row = self._conn.execute(
            """
            SELECT
                EXISTS (
                    SELECT 1 FROM worker.control WHERE owner = %(owner)s AND paused
                ),
                (
                    SELECT count(*) FROM worker.job
                    WHERE owner = %(owner)s AND status = 'queued'
                ),
                (
                    SELECT count(*) FROM worker.job
                    WHERE owner = %(owner)s AND status = 'under way'
                ),
                (SELECT count(*) FROM worker.worker WHERE seen > now() - %(lost)s)
            """,
            {"owner": owner, "lost": lost},
        ).fetchone()
        assert row is not None
        paused, queued, under_way, workers = row
        return Standing(bool(paused), int(queued), int(under_way), int(workers))

    def stop(self, owner: int, now: bool = False) -> Stopped:
        with self._conn.transaction():
            taken = self._conn.execute(
                """
                UPDATE worker.job SET status = 'stopped', why = %s, ended = now()
                WHERE owner = %s AND status = 'queued'
                RETURNING run
                """,
                (TAKEN_OUT, owner),
            ).fetchall()
            halting = (
                self._conn.execute(
                    """
                    UPDATE worker.job SET halt = true
                    WHERE owner = %s AND status = 'under way' AND NOT halt
                    RETURNING run
                    """,
                    (owner,),
                ).fetchall()
                if now
                else []
            )
            self._tell()
            for (run,) in taken:
                self._tell(run, "stopped")
        return Stopped(
            tuple(UUID(str(r)) for (r,) in taken),
            tuple(UUID(str(r)) for (r,) in halting),
        )

    def halt(self, run: UUID) -> Job:
        with self._conn.transaction():
            row = self._conn.execute(
                f"""
                UPDATE worker.job AS j SET halt = true WHERE j.run = %s AND {_OPEN}
                RETURNING {_COLUMNS}
                """,
                (run,),
            ).fetchone()
            self._tell()
        if row is None:
            raise Missing.of("run %(run)s has nothing under way", run=str(run))
        return _job(row)

    def pause(self, owner: int, paused: bool = True) -> None:
        with self._conn.transaction():
            _ = self._conn.execute(
                """
                INSERT INTO worker.control (owner, paused) VALUES (%s, %s)
                ON CONFLICT (owner) DO UPDATE SET paused = excluded.paused
                """,
                (owner, paused),
            )
            self._tell()

    def enlist(self, worker: UUID) -> None:
        _ = self._conn.execute("INSERT INTO worker.worker (id) VALUES (%s)", (worker,))

    def claim(
        self, worker: UUID, capacity: Mapping[str, int], lost: timedelta
    ) -> Job | None:
        with self._conn.transaction():
            _ = self._conn.execute(
                "SELECT pg_advisory_xact_lock(hashtext('worker.claim'))"
            )
            used = dict(
                self._conn.execute(
                    f"""
                    SELECT j.endpoint, sum(j.slots) FROM worker.job j
                    WHERE j.status = 'under way' AND {_LIVE}
                    GROUP BY j.endpoint
                    """,
                    {"lost": lost},
                ).fetchall()
            )
            endpoints = sorted(capacity)
            free = [capacity[e] - int(used.get(e, 0)) for e in endpoints]
            row = self._conn.execute(
                f"""
                SELECT j.id FROM worker.job j
                LEFT JOIN unnest(%(endpoints)s::text[], %(free)s::int[])
                    AS f (endpoint, free) ON f.endpoint = j.endpoint
                WHERE (j.status = 'queued' OR (j.status = 'under way' AND NOT {_LIVE}))
                    AND (
                        j.halt OR f.endpoint IS NULL OR (
                            j.slots <= f.free AND NOT EXISTS (
                                SELECT 1 FROM worker.control c
                                WHERE c.owner = j.owner AND c.paused
                            )
                        )
                    )
                ORDER BY j.queued, j.id
                LIMIT 1
                FOR UPDATE OF j SKIP LOCKED
                """,
                {"endpoints": endpoints, "free": free, "lost": lost},
            ).fetchone()
            if row is None:
                return None
            claimed = self._conn.execute(
                f"""
                UPDATE worker.job AS j
                SET status = 'under way', worker = %s, claimed = now(), beat = now()
                WHERE j.id = %s
                RETURNING {_COLUMNS}
                """,
                (worker, row[0]),
            ).fetchone()
        assert claimed is not None
        return _job(claimed)

    def beat(self, worker: UUID, jobs: Collection[int]) -> list[Held]:
        with self._conn.transaction():
            _ = self._conn.execute(
                "UPDATE worker.worker SET seen = now() WHERE id = %s", (worker,)
            )
            rows = self._conn.execute(
                """
                UPDATE worker.job AS j SET beat = now()
                WHERE j.id = ANY(%s) AND j.worker = %s AND j.status = 'under way'
                RETURNING j.id, j.halt, EXISTS (
                    SELECT 1 FROM worker.control c WHERE c.owner = j.owner AND c.paused
                )
                """,
                (list(jobs), worker),
            ).fetchall()
        return [Held(job=id, halt=halt, paused=paused) for id, halt, paused in rows]

    def end(
        self, job: int, worker: UUID, status: Status, why: str | None = None
    ) -> bool:
        if status not in _ENDED:
            raise ValueError(f"a job ends {', '.join(_ENDED)}, not {status}")
        with self._conn.transaction():
            row = self._conn.execute(
                """
                UPDATE worker.job SET status = %s, why = %s, ended = now()
                WHERE id = %s AND worker = %s AND status = 'under way'
                RETURNING run
                """,
                (status, why, job, worker),
            ).fetchone()
            if row is not None:
                self._tell(row[0], status)
        return row is not None

    def scored(self, job: int, worker: UUID, scorer: str) -> bool:
        row = self._conn.execute(
            """
            UPDATE worker.job SET scored = array_append(scored, %(scorer)s)
            WHERE id = %(job)s AND worker = %(worker)s AND status = 'under way'
                AND NOT %(scorer)s = ANY(scored)
            RETURNING id
            """,
            {"job": job, "worker": worker, "scorer": scorer},
        ).fetchone()
        return row is not None

    def requeue(self, job: int, worker: UUID, why: str | None = None) -> bool:
        with self._conn.transaction():
            row = self._conn.execute(
                """
                UPDATE worker.job
                SET status = 'queued', why = %s, worker = NULL, claimed = NULL, beat = NULL
                WHERE id = %s AND worker = %s AND status = 'under way'
                RETURNING run
                """,
                (why, job, worker),
            ).fetchone()
            if row is not None:
                self._tell(row[0], "queued")
        return row is not None

    def _tell(self, run: UUID | None = None, status: Status | None = None) -> None:
        _ = self._conn.execute("SELECT pg_notify(%s, '')", (WORKERS,))
        if run is not None and status is not None:
            _ = self._conn.execute(
                "SELECT pg_notify(%s, %s)", (channel(run), JOB + status)
            )

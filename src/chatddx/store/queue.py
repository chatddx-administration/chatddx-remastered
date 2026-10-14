from collections.abc import Collection, Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal, cast, get_args
from uuid import UUID

from psycopg import errors

from .store import Connection

Status = Literal["queued", "under way", "finished", "stopped", "failed"]
ENDED: tuple[Status, ...] = ("finished", "stopped", "failed")
STATUSES: tuple[Status, ...] = get_args(Status)

_COLUMNS = """
    j.id, j.owner, j.run, j.endpoint, j.slots, j.score, j.scorers, j.status, j.why,
    j.halt, j.worker, j.queued, j.claimed, j.beat, j.ended
"""

_OPEN = "j.status IN ('queued', 'under way')"

_LIVE = """
    EXISTS (
        SELECT 1 FROM worker.worker w
        WHERE w.id = j.worker AND w.seen > now() - %(lost)s
    )
"""


class UnderWay(ValueError):
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


def _job(row: tuple[Any, ...]) -> Job:
    (
        id,
        owner,
        run,
        endpoint,
        slots,
        score,
        scorers,
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
        except errors.UniqueViolation:
            raise UnderWay(f"run {run} has something under way") from None
        assert row is not None
        return _job(row)

    def job(self, id: int) -> Job:
        row = self._conn.execute(
            f"SELECT {_COLUMNS} FROM worker.job j WHERE j.id = %s", (id,)
        ).fetchone()
        if row is None:
            raise LookupError(f"no job {id}")
        return _job(row)

    def open(self, run: UUID) -> Job | None:
        row = self._conn.execute(
            f"SELECT {_COLUMNS} FROM worker.job j WHERE j.run = %s AND {_OPEN}", (run,)
        ).fetchone()
        return None if row is None else _job(row)

    def jobs(self, owner: int, limit: int = 100) -> list[Job]:
        rows = self._conn.execute(
            f"""
            SELECT {_COLUMNS} FROM worker.job j WHERE j.owner = %s
            ORDER BY j.queued DESC, j.id DESC LIMIT %s
            """,
            (owner, limit),
        ).fetchall()
        return [_job(r) for r in rows]

    def halt(self, run: UUID) -> Job:
        row = self._conn.execute(
            f"""
            UPDATE worker.job AS j SET halt = true WHERE j.run = %s AND {_OPEN}
            RETURNING {_COLUMNS}
            """,
            (run,),
        ).fetchone()
        if row is None:
            raise LookupError(f"run {run} has nothing under way")
        return _job(row)

    def pause(self, owner: int, paused: bool = True) -> None:
        _ = self._conn.execute(
            """
            INSERT INTO worker.control (owner, paused) VALUES (%s, %s)
            ON CONFLICT (owner) DO UPDATE SET paused = excluded.paused
            """,
            (owner, paused),
        )

    def paused(self, owner: int) -> bool:
        row = self._conn.execute(
            "SELECT paused FROM worker.control WHERE owner = %s", (owner,)
        ).fetchone()
        return row is not None and bool(row[0])

    def enlist(self, worker: UUID) -> None:
        _ = self._conn.execute("INSERT INTO worker.worker (id) VALUES (%s)", (worker,))

    # A job under way whose worker hasn't been seen for `lost` is claimed again. Claims
    # take turns, so that two workers count an endpoint's slots in use alike.
    def claim(
        self, worker: UUID, max_jobs: Mapping[str, int], lost: timedelta
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
            endpoints = sorted(max_jobs)
            free = [max_jobs[e] - int(used.get(e, 0)) for e in endpoints]
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

    # The jobs `worker` still holds of `jobs`, each with whether it is to halt and whether
    # its owner has paused; one another worker took over is left out.
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
        if status not in ENDED:
            raise ValueError(f"a job ends {', '.join(ENDED)}, not {status}")
        row = self._conn.execute(
            """
            UPDATE worker.job SET status = %s, why = %s, ended = now()
            WHERE id = %s AND worker = %s AND status = 'under way'
            RETURNING id
            """,
            (status, why, job, worker),
        ).fetchone()
        return row is not None

    def requeue(self, job: int, worker: UUID, why: str | None = None) -> bool:
        row = self._conn.execute(
            """
            UPDATE worker.job
            SET status = 'queued', why = %s, worker = NULL, claimed = NULL, beat = NULL
            WHERE id = %s AND worker = %s AND status = 'under way'
            RETURNING id
            """,
            (why, job, worker),
        ).fetchone()
        return row is not None

    def waiting(self) -> int:
        row = self._conn.execute(
            f"SELECT count(*) FROM worker.job j WHERE {_OPEN}"
        ).fetchone()
        assert row is not None
        return int(row[0])

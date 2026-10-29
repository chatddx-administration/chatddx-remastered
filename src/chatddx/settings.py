import os
from datetime import timedelta
from enum import IntEnum
from pathlib import Path

from psycopg.conninfo import make_conninfo

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def database(admin: bool = False) -> str:
    return make_conninfo(
        host=os.environ["DB_HOST"],
        user=os.environ["DB_ADMIN" if admin else "DB_USER"],
        dbname=os.environ["DB_NAME"],
    )


SESSION_TTL = timedelta(hours=12)

TYPED_TEXT_LIMIT = 20_000
TYPED_PER_DAY = 50

RUNS_PER_DAY = 100
ITEMS_PER_RUN = 1000

ROWS_PER_PAGE = 100


class Stage(IntEnum):
    FELT = 1
    IMPLIED = 2
    MENTIONED = 3
    NAMED = 4
    ITEMIZED = 5
    PLANNED = 6
    DRAFTED = 7
    SOLIDIFIED = 8
    CEMENTED = 9
    PROTECTED = 10


STAGES = {
    "api": Stage.SOLIDIFIED,
    "bench": Stage.SOLIDIFIED,
    "catalog": Stage.SOLIDIFIED,
    "clearance": Stage.DRAFTED,
    "cli": Stage.SOLIDIFIED,
    "conftest": Stage.SOLIDIFIED,
    "curation": Stage.SOLIDIFIED,
    "factors": Stage.SOLIDIFIED,
    "facts": Stage.SOLIDIFIED,
    "fake_vllm": Stage.SOLIDIFIED,
    "identity": Stage.SOLIDIFIED,
    "importers": Stage.SOLIDIFIED,
    "inventory": Stage.SOLIDIFIED,
    "ledger": Stage.SOLIDIFIED,
    "locale": Stage.SOLIDIFIED,
    "markers": Stage.SOLIDIFIED,
    "portal": Stage.SOLIDIFIED,
    "refcheck": Stage.SOLIDIFIED,
    "repl": Stage.SOLIDIFIED,
    "rig": Stage.SOLIDIFIED,
    "runner": Stage.SOLIDIFIED,
    "scorers": Stage.SOLIDIFIED,
    "scripted": Stage.SOLIDIFIED,
    "settings": Stage.SOLIDIFIED,
    "stamp": Stage.SOLIDIFIED,
    "store": Stage.SOLIDIFIED,
    "test": Stage.SOLIDIFIED,
    "tools": Stage.SOLIDIFIED,
    "whoops": Stage.SOLIDIFIED,
    "worker": Stage.SOLIDIFIED,
}

STAMPED_FROM = {
    "comments": Stage.DRAFTED,
    "surfaces": Stage.SOLIDIFIED,
    "whoopses": Stage.DRAFTED,
}

# Policy: how long a server stopping waits on its open responses, a run's event stream
# among them, which ends only with the run's job, before it cuts them off.
SERVE_GRACE = timedelta(seconds=5)
WORKER_BEAT = timedelta(seconds=1)
WORKER_LOST = timedelta(seconds=10)
# Policy: within the stop timeout of the service that runs the worker, TimeoutStopSec in
# nix/module.nix.
WORKER_DEADLINE = timedelta(seconds=60)
# Policy: bounds a worker's threads, and its connections at 1 + 2 per job
# (src/chatddx/worker/worker.py:Worker._work).
WORKER_JOBS = 8


def host() -> str:
    return os.environ.get("HOST", "localhost:8000")


def revision() -> str | None:
    return os.environ.get("CHATDDX_REVISION") or None


def world() -> Path | None:
    value = os.environ.get("CHATDDX_WORLD")
    return Path(value) if value else None


def portal_assets() -> Path:
    value = os.environ.get("CHATDDX_PORTAL_ASSETS")
    return Path(value) if value else PROJECT_ROOT / "frontend" / "dist"


def chromium() -> Path | None:
    value = os.environ.get("CHATDDX_CHROMIUM")
    return Path(value) if value else None

import os
from datetime import timedelta
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

WORKER_BEAT = timedelta(seconds=1)
WORKER_LOST = timedelta(seconds=10)


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

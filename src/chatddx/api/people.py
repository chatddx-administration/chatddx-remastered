from dataclasses import dataclass
from typing import Annotated
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBearer

from chatddx import settings
from chatddx.bench import Bench
from chatddx.identity import Person
from chatddx.store import People
from chatddx.store.store import Connection

from .schemas import Me, SignedIn, SignIn
from .state import connection, state

COOKIE = "__Host-chatddx-session"
SAFE = frozenset({"GET", "HEAD", "OPTIONS"})

_bearer = HTTPBearer(auto_error=False, description="the token POST /api/session gives")
_cookie = APIKeyCookie(
    name=COOKIE, auto_error=False, description="the cookie POST /api/session sets"
)

router = APIRouter(tags=["people"])

type ConnDep = Annotated[Connection, Depends(connection)]


@dataclass(frozen=True)
class Session:
    person: Person
    token: str


def _unsigned(detail: str = "sign in first") -> HTTPException:
    return HTTPException(401, detail, headers={"WWW-Authenticate": "Bearer"})


def same_origin(request: Request) -> None:
    if request.method in SAFE:
        return
    site = request.headers.get("sec-fetch-site")
    origin = request.headers.get("origin")
    if site is not None:
        own = site in ("same-origin", "none")
    elif origin is not None:
        own = urlsplit(origin).netloc == request.headers.get("host")
    else:
        own = True
    if not own:
        raise HTTPException(403, "a browser's request must come from this site's pages")


def session(
    request: Request,
    conn: ConnDep,
    bearer: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    cookie: Annotated[str | None, Depends(_cookie)],
) -> Session:
    if bearer is not None:
        token = bearer.credentials
    elif cookie is not None:
        same_origin(request)
        token = cookie
    else:
        raise _unsigned()
    person = People(conn).session(token)
    if person is None:
        raise _unsigned("the session has ended: sign in again")
    return Session(person, token)


def keep_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        COOKIE,
        token,
        max_age=int(settings.SESSION_TTL.total_seconds()),
        secure=True,
        httponly=True,
        samesite="lax",
    )


def drop_cookie(response: Response) -> None:
    response.delete_cookie(COOKIE, secure=True, httponly=True, samesite="lax")


def signed_in(held: Annotated[Session, Depends(session)]) -> Person:
    return held.person


def bench(
    request: Request, conn: ConnDep, person: Annotated[Person, Depends(signed_in)]
) -> Bench:
    held = state(request)
    return Bench(conn, person, held.inventory, held.facts)


type BenchDep = Annotated[Bench, Depends(bench)]


@router.post("/session", status_code=201)
def sign_in(
    request: Request, response: Response, given: SignIn, conn: ConnDep
) -> SignedIn:
    same_origin(request)
    people = People(conn)
    person = people.authenticate(given.login, given.password)
    if person is None:
        raise _unsigned("wrong login or password")
    token = people.open_session(person.id)
    keep_cookie(response, token)
    return SignedIn(token=token, person=Me.of(person))


@router.delete("/session", status_code=204)
def sign_out(
    response: Response, held: Annotated[Session, Depends(session)], conn: ConnDep
) -> None:
    People(conn).close_session(held.token)
    drop_cookie(response)


@router.get("/me")
def me(person: Annotated[Person, Depends(signed_in)]) -> Me:
    return Me.of(person)

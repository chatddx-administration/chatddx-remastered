from dataclasses import dataclass
from typing import Annotated
from urllib.parse import urlsplit

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.security import APIKeyCookie, HTTPAuthorizationCredentials, HTTPBearer

from chatddx.core import settings
from chatddx.identity import Person
from chatddx.store import People
from chatddx.store.store import Connection

from .schemas import Me, SignedIn, SignIn
from .state import connection

# `__Host-` has browsers keep the cookie to this host, over HTTPS, for every path.
COOKIE = "__Host-chatddx-session"
SAFE = frozenset({"GET", "HEAD", "OPTIONS"})

_bearer = HTTPBearer(auto_error=False, description="the token POST /api/session gives")
_cookie = APIKeyCookie(
    name=COOKIE, auto_error=False, description="the cookie POST /api/session sets"
)

router = APIRouter(tags=["people"])

type Conn = Annotated[Connection, Depends(connection)]


@dataclass(frozen=True)
class Session:
    person: Person
    token: str


def _unsigned(detail: str = "sign in first") -> HTTPException:
    return HTTPException(401, detail, headers={"WWW-Authenticate": "Bearer"})


# A browser sends the cookie with requests from any page, so an unsafe one must come
# from this site's own: by Fetch Metadata where the browser sends it, else by Origin. A
# request with neither isn't a browser's on another page's behalf.
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


# The session a request acts in: its bearer token, else its cookie.
def session(
    request: Request,
    conn: Conn,
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


def signed_in(held: Annotated[Session, Depends(session)]) -> Person:
    return held.person


@router.post("/session", status_code=201)
def sign_in(
    request: Request, response: Response, given: SignIn, conn: Conn
) -> SignedIn:
    same_origin(request)
    people = People(conn)
    person = people.authenticate(given.login, given.password)
    if person is None:
        raise _unsigned("wrong login or password")
    token = people.open_session(person.id)
    response.set_cookie(
        COOKIE,
        token,
        max_age=int(settings.SESSION_TTL.total_seconds()),
        secure=True,
        httponly=True,
        samesite="strict",
    )
    return SignedIn(token=token, person=Me.of(person))


@router.delete("/session", status_code=204)
def sign_out(
    response: Response, held: Annotated[Session, Depends(session)], conn: Conn
) -> None:
    People(conn).close_session(held.token)
    response.delete_cookie(COOKIE, secure=True, httponly=True, samesite="strict")


@router.get("/me")
def me(person: Annotated[Person, Depends(signed_in)]) -> Me:
    return Me.of(person)

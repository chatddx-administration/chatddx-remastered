import json
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path
from typing import Annotated, Any
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import JsonValue

from chatddx.api.people import COOKIE, ConnDep, drop_cookie, keep_cookie, same_origin
from chatddx.api.state import NO_STORE, state
from chatddx.bench import Bench
from chatddx.identity import Person
from chatddx.store import People

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def _when(at: datetime | None) -> str:
    return "—" if at is None else at.strftime("%Y-%m-%d %H:%M")


def _short(digest: str | None) -> str:
    return "—" if digest is None else digest.removeprefix("sha256:")[:12]


def _pretty(value: JsonValue) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False)


templates.env.filters.update(when=_when, short=_short, pretty=_pretty)

router = APIRouter()


class SignInFirst(Exception):
    def __init__(self, request: Request) -> None:
        super().__init__("sign in first")
        query = request.url.query
        self.next: str = request.url.path + (f"?{query}" if query else "")


def to_sign_in(_: Request, e: Exception) -> Response:
    assert isinstance(e, SignInFirst)
    return RedirectResponse(f"/sign-in?{urlencode({'next': e.next})}", 303)


def page(request: Request, name: str, status: int = 200, **context: Any) -> Response:
    assets = request.app.state.assets
    return templates.TemplateResponse(
        request,
        name,
        {"assets": assets, **context},
        status_code=status,
        headers=NO_STORE,
    )


def within(next: str | None) -> str:
    if next is None or not next.startswith("/") or next.startswith(("//", "/\\")):
        return "/"
    return next


def _person(request: Request, conn: ConnDep) -> Person | None:
    token = request.cookies.get(COOKIE)
    return None if token is None else People(conn).session(token)


def signed_in(request: Request, conn: ConnDep) -> Person:
    person = _person(request, conn)
    if person is None:
        raise SignInFirst(request)
    same_origin(request)
    return person


type PersonDep = Annotated[Person, Depends(signed_in)]


def page_bench(request: Request, conn: ConnDep, person: PersonDep) -> Bench:
    held = state(request)
    return Bench(conn, person, held.inventory)


type BenchDep = Annotated[Bench, Depends(page_bench)]


def paged(
    answer: Callable[[Request, Any], Response | Awaitable[Response]],
) -> Callable[[Request, Exception], Response]:
    def handle(request: Request, e: Exception) -> Response:
        said = answer(request, e)
        assert isinstance(said, Response)
        if request.url.path.startswith("/api/") or not isinstance(said, JSONResponse):
            return said
        with state(request).connect() as conn:
            person = _person(request, conn)
        error = json.loads(bytes(said.body))
        return page(request, "error.html", said.status_code, error=error, person=person)

    return handle


@router.get("/")
def home(request: Request, person: PersonDep) -> Response:
    return page(request, "home.html", person=person, island="home")


@router.get("/sign-in")
def signing_in_page(request: Request, conn: ConnDep, next: str = "/") -> Response:
    if _person(request, conn) is not None:
        return RedirectResponse(within(next), 303)
    return page(request, "sign-in.html", next=within(next))


@router.post("/sign-in")
def signing_in(
    request: Request,
    conn: ConnDep,
    login: Annotated[str, Form()],
    password: Annotated[str, Form()],
    next: Annotated[str, Form()] = "/",
) -> Response:
    same_origin(request)
    people = People(conn)
    person = people.authenticate(login, password)
    if person is None:
        return page(request, "sign-in.html", next=within(next), login=login, wrong=True)
    signed = RedirectResponse(within(next), 303)
    keep_cookie(signed, people.open_session(person.id))
    return signed


@router.post("/sign-out")
def signing_out(request: Request, conn: ConnDep) -> Response:
    same_origin(request)
    token = request.cookies.get(COOKIE)
    if token is not None:
        People(conn).close_session(token)
    out = RedirectResponse("/sign-in", 303)
    drop_cookie(out)
    return out

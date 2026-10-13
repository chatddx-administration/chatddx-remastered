from pathlib import Path
from typing import Annotated, Any
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

from chatddx.api.people import COOKIE, ConnDep, drop_cookie, keep_cookie, same_origin
from chatddx.api.state import NO_STORE
from chatddx.identity import Person
from chatddx.store import People

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

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
    return templates.TemplateResponse(
        request, name, context, status_code=status, headers=NO_STORE
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


@router.get("/")
def home(request: Request, person: PersonDep) -> Response:
    return page(request, "home.html", person=person)


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

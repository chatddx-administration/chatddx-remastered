import json
import re
from dataclasses import replace
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, override

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import Response
from psycopg.conninfo import make_conninfo

from chatddx import settings
from chatddx.inventory import Inventory, World
from chatddx.locale import display_language
from chatddx.portal.app import app
from chatddx.test.helpers import PASSWORD
from chatddx.test.world import TEST


def signing_in(
    client: TestClient, password: str = PASSWORD, next: str = "/", **headers: str
) -> Response:
    form = {"login": "alice", "password": password, "next": next}
    return client.post("/sign-in", data=form, headers=headers)


def shown(client: TestClient, path: str) -> str:
    got = client.get(path)
    assert got.status_code == 200, (path, got.text[:500])
    assert got.headers["content-type"].startswith("text/html")
    assert got.headers["cache-control"] == "no-store"
    return got.text


def said(page: str) -> str:
    main = page.split("<main", 1)[1]
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", main))


def case_title(case: dict[str, Any]) -> str:
    n = len(case["appendices"])
    said = (
        case["name"]
        if not n
        else f"{case['name']} + {n} appendi" + ("x" if n == 1 else "ces")
    )
    return f"{said} (earlier)" if case["earlier"] else said


def run_title(run: dict[str, Any]) -> str:
    titled = run["titled"]
    replaced: list[str] = []
    for r in titled["replaced"]:
        part = r["part"].replace("_", " ")
        replaced.append(f"no {part}" if r["title"] is None else f"{part}: {r['title']}")
    configuration = f"`{titled['name']}`" + (
        f" ({', '.join(replaced)})" if replaced else ""
    )
    language = titled["translated"] and display_language(titled["translated"])
    n = titled["cases"]
    if titled["case"]:
        cases = case_title(titled["case"]) + (f" in {language}" if language else "")
    else:
        cases = " ".join(
            [str(n), *([language] if language else []), "case" if n == 1 else "cases"]
        )
    k = len(titled["seeds"])
    numbers = ", ".join(str(s) for s in titled["seeds"])
    seeds = (
        ("greedy" if k == 1 else f"greedy, {k} replicates")
        if titled["greedy"]
        else (f"seed {numbers}" if k == 1 else f"seeds {numbers}")
    )
    return f"{cases} with {configuration} on {titled['at']} ({seeds})"


def variation_props(page: str) -> dict[str, Any]:
    opened = '<script type="application/json" id="variation-props">'
    return json.loads(page.split(opened, 1)[1].split("</script>", 1)[0])


def submitted(page: str, action: str) -> dict[str, list[str]]:
    found = _Submitted(action)
    found.feed(page)
    assert found.fields, f"no form posting to {action}"
    return found.fields


# Accommodating for what a browser sends of a form: a select's chosen option, else its
# first, a checkbox only when checked, and a textarea's text without the line break that
# follows its opening tag.
class _Submitted(HTMLParser):
    def __init__(self, action: str) -> None:
        super().__init__()
        self.action: str = action
        self.inside: bool = False
        self.fields: dict[str, list[str]] = {}
        self.named: str | None = None
        self.options: list[tuple[str, bool]] = []
        self.text: list[str] | None = None

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        given = dict(attrs)
        if tag == "form" and given.get("action") == self.action:
            self.inside = True
        if not self.inside:
            return
        name = given.get("name")
        unchecked = (
            given.get("type") in ("checkbox", "radio") and "checked" not in given
        )
        if tag == "input" and name is not None and not unchecked:
            self.fields.setdefault(name, []).append(given.get("value") or "")
        elif tag in ("select", "textarea"):
            self.named = name
            self.options, self.text = [], [] if tag == "textarea" else None
        elif tag == "option":
            self.options.append((given.get("value") or "", "selected" in given))

    @override
    def handle_data(self, data: str) -> None:
        if self.inside and self.text is not None:
            self.text.append(data)

    @override
    def handle_endtag(self, tag: str) -> None:
        if not self.inside or self.named is None and tag != "form":
            return
        if tag == "form":
            self.inside = False
        elif tag == "textarea" and self.text is not None:
            value = "".join(self.text).removeprefix("\n")
            self.fields.setdefault(self.named or "", []).append(value)
            self.named, self.text = None, None
        elif tag == "select":
            chosen = [v for v, picked in self.options if picked] or [self.options[0][0]]
            self.fields.setdefault(self.named or "", []).append(chosen[0])
            self.named = None


# Accommodating for pytest, as src/chatddx/test/helpers.py:curated_template does.
@pytest.fixture(name="template")
def ran_template(ran: str) -> str:
    return ran


@pytest.fixture(name="served")
def world_served(db: str, built: Path, world: Inventory) -> FastAPI:
    return app(
        replace(World.load(TEST), inventory=world),
        make_conninfo(settings.database(), dbname=db),
        built,
        worker=True,
    )

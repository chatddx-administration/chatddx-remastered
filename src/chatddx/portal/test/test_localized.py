import re
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from jinja2 import ChoiceLoader, DictLoader

from chatddx.api import schemas
from chatddx.factors import Finding, Invalid
from chatddx.locale import Locales, localizing
from chatddx.locale.test.helpers import catalog
from chatddx.portal.pages import refusal_of, templates
from chatddx.portal.test.helpers import said


def test_a_message_is_said_in_the_locale_where_it_is_translated_and_reviewed(
    tmp_path: Path,
) -> None:
    sv = Locales(
        catalog(
            tmp_path,
            """
            msgid "Library"
            msgstr "Bibliotek"

            msgid "%(n)s run"
            msgid_plural "%(n)s runs"
            msgstr[0] "%(n)s körning"
            msgstr[1] "%(n)s körningar"

            #, fuzzy
            msgid "Fork it"
            msgstr "Forka"
            """,
        )
    ).negotiate("sv")
    shown = templates.env.overlay(
        loader=DictLoader(
            {
                "shelf.html": "{% macro shelf() %}{{ _('Library') }}{% endmacro %}",
                "page.html": "{% from 'shelf.html' import shelf %}{{ shelf() }}, "
                + "{{ ngettext('%(n)s run', '%(n)s runs', 1, n=1) }}, "
                + "{% trans n=2 %}{{ n }} run{% pluralize %}{{ n }} runs{% endtrans %}, "
                + "{{ _('Fork it') }}, {{ _('Delete it') }}",
            }
        )
    )
    page = shown.get_template("page.html")
    with localizing(sv):
        assert page.render() == "Bibliotek, 1 körning, 2 körningar, Fork it, Delete it"
    assert page.render() == "Library, 1 run, 2 runs, Fork it, Delete it"


def test_a_finding_is_said_by_its_code_where_its_message_is_translated(
    tmp_path: Path,
) -> None:
    sv = Locales(
        catalog(
            tmp_path,
            """
            msgctxt "run.incomplete"
            msgid "%(num)s item missing"
            msgid_plural "%(num)s items missing"
            msgstr[0] "%(num)s post saknas"
            msgstr[1] "%(num)s poster saknas"
            """,
        )
    ).negotiate("sv")
    found = [
        schemas.Finding.of(f)
        for f in (
            Finding.of(
                "run.incomplete",
                ("%(num)s item missing", "%(num)s items missing"),
                num=2,
            ),
            Finding(code="call.failed", message="the server didn't answer"),
        )
    ]
    macros = templates.env.loader
    assert macros is not None
    page = templates.env.overlay(
        loader=ChoiceLoader(
            [
                DictLoader(
                    {
                        "page.html": "{% from 'macros.html' import findings %}"
                        + "{{ findings(found) }}"
                    }
                ),
                macros,
            ]
        )
    ).get_template("page.html")
    with localizing(sv):
        shown = page.render(found=found)
    assert "2 poster saknas" in shown and "the server didn&#39;t answer" in shown
    assert "2 items missing" in page.render(found=found)


def test_a_refusal_is_said_by_its_wording_and_what_isn_t_worded_is_passed_on(
    tmp_path: Path,
) -> None:
    sv = Locales(
        catalog(
            tmp_path,
            """
            msgctxt "refusal"
            msgid "a fork is named"
            msgstr "en förgrening har ett namn"

            msgid "That can't be done"
            msgstr "Det går inte"

            msgid "%(title)s. Copy this and send it to drift@chatddx.com: %(pass_on)s"
            msgstr "%(title)s. Kopiera och skicka detta till drift@chatddx.com: %(pass_on)s"
            """,
        )
    ).negotiate("sv")
    with localizing(sv):
        assert refusal_of(Invalid.of("a fork is named")) == "en förgrening har ett namn"
        assert refusal_of(ValueError("slots used twice")) == (
            "Det går inte. Kopiera och skicka detta till drift@chatddx.com: slots used twice"
        )
    assert refusal_of(ValueError("slots used twice")) == (
        "That can't be done. Copy this and send it to drift@chatddx.com: slots used twice"
    )


@pytest.mark.usefixtures("alice")
@pytest.mark.slow
def test_a_page_says_which_language_it_is_in(signed: TestClient) -> None:
    library = signed.get("/library").text
    assert '<html lang="en">' in library and 'id="locale"' not in library
    asked = signed.get("/library", headers={"accept-language": "sv-SE,sv;q=0.9"})
    assert '<html lang="sv">' in asked.text
    home = signed.get("/", headers={"accept-language": "sv"}).text
    assert '<script type="application/json" id="locale">{"tag": "sv", ' in home


@pytest.mark.usefixtures("alice")
def test_a_language_is_said_by_its_name_in_the_locale_asked_for(
    signed: TestClient,
) -> None:
    [family] = [f for f in signed.get("/api/families").json() if f["language"] == "sv"][
        :1
    ]
    path = f"/cases/{family['id']}"
    english = said(signed.get(path).text)
    swedish = said(signed.get(path, headers={"accept-language": "sv"}).text)
    assert " Language Swedish " in english and " sv " not in english
    assert " Språk svenska " in swedish


@pytest.mark.usefixtures("alice")
@pytest.mark.slow
def test_the_library_is_said_in_the_locale_asked_for_its_kinds_by_their_words(
    signed: TestClient, served: FastAPI, tmp_path: Path
) -> None:
    served.state.locales = Locales(
        catalog(
            tmp_path,
            """
            msgid "Library"
            msgstr "Bibliotek"

            msgctxt "kind"
            msgid "configuration"
            msgstr "konfiguration"

            msgid "%(num)s yours"
            msgid_plural "%(num)s yours"
            msgstr[0] "%(num)s din"
            msgstr[1] "%(num)s dina"
            """,
        )
    )
    sv = {"accept-language": "sv"}
    overview = signed.get("/library", headers=sv).text
    assert (
        "1 din · " in overview and "0 dina · " in overview and "yours" not in overview
    )

    page = signed.get("/library?kind=configuration", headers=sv).text
    assert "<title>konfiguration · Bibliotek · ChatDDX</title>" in page
    [shelf, *_] = re.findall(
        r'<ul aria-label="Configurations".*?</ul>', page, re.DOTALL
    )
    words = re.findall(r'href="/library\?kind=(\w+)"', shelf)
    assert words[:4] == ["few_shot", "instructions", "configuration", "output"]
    assert '<span class="min-w-0 flex-1 truncate">konfiguration</span>' in shelf


@pytest.mark.usefixtures("alice")
@pytest.mark.slow
def test_what_the_portal_s_python_says_is_said_in_the_locale_asked_for(
    signed: TestClient, served: FastAPI, tmp_path: Path
) -> None:
    served.state.locales = Locales(
        catalog(
            tmp_path,
            """
            msgid "Trials"
            msgstr "Försök"

            msgid "What is run."
            msgstr "Det som körs."

            msgctxt "refusal"
            msgid "no kind %(kind)s: the kinds are %(kinds)s"
            msgstr "ingen sort %(kind)s: sorterna är %(kinds)s"

            msgctxt "refusal"
            msgid "%(field)s isn't a number: %(given)s"
            msgstr "%(field)s är inget tal: %(given)s"
            """,
        )
    )
    sv = {"accept-language": "sv"}
    overview = signed.get("/library", headers=sv).text
    headings = re.findall(r"<h2[^>]*>([^<]+)</h2>", overview)
    assert headings == ["Cases", "Configurations", "Försök", "Models", "Scoring"]
    assert "Det som körs." in overview

    nowhere = signed.get("/library?kind=nope", headers=sv)
    assert nowhere.status_code == 404 and "ingen sort" in nowhere.text

    action = "/library/new?kind=sampling"
    form = {"name": "warm", "f.temperature": "warm"}
    refused = signed.post(action, data=form, headers=sv)
    assert refused.status_code == 422 and "temperature är inget tal" in refused.text
    assert "isn&#39;t a number" in signed.post(action, data=form).text

import re
from pathlib import Path
from textwrap import dedent

import pytest

from chatddx.locale import Locales, proofs, saying, tr
from chatddx.locale.test.helpers import catalog


def tree(root: Path, files: dict[str, str]) -> Path:
    for name, source in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(dedent(source))
    return root


def test_a_request_is_answered_in_the_language_it_prefers_of_those_there_are(
    tmp_path: Path,
) -> None:
    locales = Locales(catalog(tmp_path, ""))
    for preferred, tag in (
        ("sv-SE,sv;q=0.9,en;q=0.8", "sv"),
        ("en-GB,en;q=0.9,sv;q=0.8", "en"),
        ("de-DE,de;q=0.9", "en"),
        ("de;q=0.9, sv ;q=0.5", "sv"),
        ("sv;q=0, en", "en"),
        ("sv;q=high", "en"),
        ("SV", "sv"),
        ("*", "en"),
        ("", "en"),
        (None, "en"),
    ):
        assert locales.negotiate(preferred).tag == tag, preferred


def test_a_message_is_translated_and_filled_in_one_call(tmp_path: Path) -> None:
    sv = Locales(
        catalog(tmp_path, 'msgid "%(n)s of %(of)s"\nmsgstr "%(n)s av %(of)s"\n')
    ).negotiate("sv")
    with saying(sv):
        assert tr("%(n)s of %(of)s", n=1, of=2) == "1 av 2"
    assert tr("%(n)s of %(of)s", n=1, of=2) == "1 of 2"
    assert tr("%(message)s: %(given)r", message="seed", given="x") == "seed: 'x'"


def test_boot_fails_on_a_catalog_whose_placeholders_are_not_its_message_s(
    tmp_path: Path,
) -> None:
    drafted = '#, fuzzy\nmsgid "%(n)s yours"\nmsgstr "%(antal)s dina"\n'
    assert Locales(catalog(tmp_path, drafted)).negotiate("sv").tag == "sv"
    with pytest.raises(ValueError, match="unknown named placeholder 'antal'"):
        _ = Locales(catalog(tmp_path, 'msgid "%(n)s yours"\nmsgstr "%(antal)s dina"\n'))
    with pytest.raises(ValueError, match="sv.po"):
        _ = Locales(catalog(tmp_path, 'msgid "Library"\nmsgstr "Bibliotek"\nsaid\n'))


def test_an_island_s_messages_are_found_in_its_calls_of_t_tn_tp_tnp_and_th(
    tmp_path: Path,
) -> None:
    root = tree(
        tmp_path,
        {
            "frontend/src/lib/Said.svelte": """
            <p>{t("Hello")}</p>
            <p>{t('it\\'s %(name)s', { name })}</p>
            <p>{tn("%(n)s run", "%(n)s runs", n, { n })}</p>
            <p>{tp("outcome", "valid")} {tnp("outcome", "%(num)s valid", "%(num)s valid", n)}</p>
            <p>{@html th('<a href="/runs/%(run)s">its run</a>', { run })}</p>
            <p>{t(said)} {shift("No")} {words.t("No")} {tn("No plural", n)} {tp("No", said)}</p>
            """,
        },
    )
    [begun] = proofs(["sv"], root, root / "catalogs")
    said = re.findall(
        r"^(?:msgctxt|msgid|msgid_plural) (.*)$", begun.written, re.MULTILINE
    )
    assert said == [
        '""',
        '"Hello"',
        '"it\'s %(name)s"',
        '"%(n)s run"',
        '"%(n)s runs"',
        '"outcome"',
        '"valid"',
        '"outcome"',
        '"%(num)s valid"',
        '"%(num)s valid"',
        '"<a href=\\"/runs/%(run)s\\">its run</a>"',
    ]


def test_a_catalog_is_kept_in_step_with_what_the_code_says(tmp_path: Path) -> None:
    template = "src/chatddx/portal/templates/page.html"
    root = tree(
        tmp_path,
        {
            "src/chatddx/portal/shelves.py": 'SHELF = N_("Cases")\n',
            "src/chatddx/portal/test/test_shelves.py": '_("Not this")\n',
            template: "{{ _('Library') }}\n"
            + "{% trans n=n %}{{ n }} run{% pluralize %}{{ n }} runs{% endtrans %}\n",
            "frontend/src/lib/Said.svelte": "<p>{t('Hello')}</p>\n",
            "frontend/src/lib/said.test.ts": 't("Not this");\n',
        },
    )
    catalogs = root / "locales"
    [begun] = proofs(["sv"], root, catalogs)
    assert begun.current is None and begun.behind
    assert (begun.untranslated, begun.fuzzy) == (4, 0)
    for said in (
        '#: src/chatddx/portal/shelves.py\nmsgid "Cases"',
        f'#: {template}\nmsgid "Library"',
        f'#: {template}\n#, python-format\nmsgid "%(n)s run"\nmsgid_plural "%(n)s runs"',
        '#: frontend/src/lib/Said.svelte\nmsgid "Hello"',
    ):
        assert said in begun.written, said
    assert "Not this" not in begun.written
    catalogs.mkdir()
    _ = begun.path.write_text(
        begun.written.replace(
            'msgid "Library"\nmsgstr ""', 'msgid "Library"\nmsgstr "Bibliotek"'
        )
    )
    [kept] = proofs([], root, catalogs)
    assert not kept.behind and (kept.untranslated, kept.fuzzy) == (3, 0)

    _ = (root / "src/chatddx/portal/templates/other.html").write_text(
        "{{ ngettext('Library', 'Libraries', n) }}\n"
    )
    with pytest.raises(ValueError, match="'Library' is said both counted and not"):
        _ = proofs([], root, catalogs)
    (root / "src/chatddx/portal/templates/other.html").unlink()

    _ = (root / template).write_text("{{ _('The Library') }}\n")
    _ = (root / "src/chatddx/portal/shelves.py").write_text(
        'SHELF = N_("%(n)s runs in all")\n'
    )
    [moved] = proofs([], root, catalogs)
    assert moved.behind and (moved.untranslated, moved.fuzzy) == (2, 1)
    assert '#, fuzzy\nmsgid "The Library"\nmsgstr "Bibliotek"' in moved.written
    assert '"%(n)s run"' not in moved.written


def test_an_island_s_page_holds_what_the_islands_say_and_the_whoopses(
    tmp_path: Path,
) -> None:
    sv = Locales(
        catalog(
            tmp_path,
            """
            #: frontend/src/lib/Said.svelte
            msgid "Hello"
            msgstr "Hej"

            #: frontend/src/lib/runs/progress.ts src/chatddx/portal/templates/run.html
            msgid "%(n)s run"
            msgid_plural "%(n)s runs"
            msgstr[0] "%(n)s körning"
            msgstr[1] "%(n)s körningar"

            #: src/chatddx/bench/seen.py
            msgctxt "whoops"
            msgid "It broke."
            msgstr "Det gick sönder."

            #: src/chatddx/portal/templates/base.html
            msgid "Library"
            msgstr "Bibliotek"

            #: frontend/src/lib/Said.svelte
            msgid "Goodbye"
            msgstr ""

            #, fuzzy
            #: frontend/src/lib/Said.svelte
            msgid "Fork it"
            msgstr "Forka"
            """,
        )
    ).negotiate("sv")
    assert sv.islands == {
        "Hello": "Hej",
        "%(n)s run": ["%(n)s körning", "%(n)s körningar"],
        "whoops\x04It broke.": "Det gick sönder.",
    }

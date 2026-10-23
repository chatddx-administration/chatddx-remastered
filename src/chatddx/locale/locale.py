import ast
import re
import sys
from collections.abc import Collection, Generator, Iterable, Iterator, Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from gettext import GNUTranslations, NullTranslations
from io import BytesIO, StringIO
from pathlib import Path
from typing import IO, Any, cast

from babel.core import Locale as Language, negotiate_locale
from babel.messages.catalog import Catalog, Message
from babel.messages.extract import DEFAULT_KEYWORDS, extract
from babel.messages.mofile import write_mo
from babel.messages.pofile import PoFileError, read_po, write_po
from starlette.datastructures import Headers
from starlette.types import ASGIApp, Receive, Scope, Send

from chatddx import settings

__all__ = [
    "N_",
    "Locale",
    "Locales",
    "Proof",
    "Saying",
    "check",
    "gettext",
    "ngettext",
    "npgettext",
    "pgettext",
    "pgettext_noop",
    "proofs",
    "saying",
    "tr",
    "whoops",
    "write",
]

_CATALOGS = Path(__file__).parent / "catalogs"
_WHOOPS = "whoops"

_KEYWORDS = {**DEFAULT_KEYWORDS, "tr": None, "pgettext_noop": ((1, "c"), 2)}
_ISLANDS = "frontend/src/"
_LEFT_OUT = re.compile(r"/test/|\.test\.ts$|\.d\.ts$|/components/ui/")
_STRING = r"""("(?:[^"\\\n]|\\.)*"|'(?:[^'\\\n]|\\.)*')"""
_CALLED = re.compile(
    rf"(?<![\w$.])(tnp|tn|tp|th|t)\(\s*{_STRING}(?:\s*,\s*{_STRING})?(?:\s*,\s*{_STRING})?"
)


@dataclass(frozen=True)
class Locale:
    tag: str
    translations: NullTranslations
    islands: dict[str, str | list[str]] = field(default_factory=dict)


_ENGLISH = Locale("en", NullTranslations())

# Accommodating for Jinja, whose macros imported without context see nothing of the page
# rendering them: a page is said in the locale set around its rendering.
_SAYING: ContextVar[Locale] = ContextVar("saying", default=_ENGLISH)


class Locales:
    def __init__(self, catalogs: Path = _CATALOGS) -> None:
        self.by_tag: dict[str, Locale] = {_ENGLISH.tag: _ENGLISH}
        for path in sorted(catalogs.glob("*.po")):
            self.by_tag[path.stem] = _locale(path)

    def negotiate(self, accept_language: str | None) -> Locale:
        preferred = _preferred(accept_language or "")
        tag = negotiate_locale(preferred, list(self.by_tag), sep="-")
        return self.by_tag.get(tag or _ENGLISH.tag, _ENGLISH)


class Saying:
    def __init__(self, app: ASGIApp) -> None:
        self.app: ASGIApp = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        locales: Locales = scope["app"].state.locales
        asked = Headers(scope=scope).get("accept-language")
        with saying(locales.negotiate(asked)):
            await self.app(scope, receive, send)


@contextmanager
def saying(locale: Locale) -> Generator[None]:
    token = _SAYING.set(locale)
    try:
        yield
    finally:
        _SAYING.reset(token)


def gettext(message: str) -> str:
    return _SAYING.get().translations.gettext(message)


def tr(message: str, /, **values: object) -> str:
    return gettext(message) % values


def ngettext(singular: str, plural: str, n: int) -> str:
    return _SAYING.get().translations.ngettext(singular, plural, n)


def pgettext(context: str, message: str) -> str:
    return _SAYING.get().translations.pgettext(context, message)


def npgettext(context: str, singular: str, plural: str, n: int) -> str:
    return _SAYING.get().translations.npgettext(context, singular, plural, n)


def N_(message: str) -> str:
    return message


def pgettext_noop(_context: str, message: str) -> str:
    return message


def whoops(message: str) -> str:
    return pgettext(_WHOOPS, message)


def _islands(
    fileobj: IO[bytes],
    _keywords: Collection[str],
    _comment_tags: Collection[str],
    **_options: Mapping[str, Any],
) -> Iterator[tuple[int, str, str | tuple[str, ...], list[str]]]:
    text = fileobj.read().decode()
    for found in _CALLED.finditer(text):
        name, *given = found.groups()
        said = [_literal(s) for s in given if s is not None]
        lineno = text.count("\n", 0, found.start()) + 1
        if name in ("t", "th"):
            yield lineno, "gettext", said[0], []
        elif name in ("tn", "tp") and len(said) >= 2:
            yield (
                lineno,
                "ngettext" if name == "tn" else "pgettext",
                tuple(said[:2]),
                [],
            )
        elif name == "tnp" and len(said) == 3:
            yield lineno, "npgettext", tuple(said), []


_SOURCES = (
    ("src/chatddx/portal/**/*.py", "python", _KEYWORDS, None),
    # Policy: what a whoops tells the person is said in their locale wherever it is raised;
    # what it has them pass on to developers and ops isn't.
    ("src/chatddx/**/*.py", "python", {"Whoops": (1,)}, _WHOOPS),
    (
        "src/chatddx/portal/templates/**/*.html",
        "jinja2.ext:babel_extract",
        _KEYWORDS,
        None,
    ),
    (f"{_ISLANDS}**/*.ts", _islands, _KEYWORDS, None),
    (f"{_ISLANDS}**/*.svelte", _islands, _KEYWORDS, None),
)


def _extracted(root: Path = settings.PROJECT_ROOT) -> Catalog:
    template = Catalog(fuzzy=False)
    for pattern, method, keywords, kind in _SOURCES:
        for path in sorted(root.glob(pattern)):
            where = path.relative_to(root).as_posix()
            if _LEFT_OUT.search(where):
                continue
            with path.open("rb") as held:
                # Accommodating for Babel, whose type for an extraction method's results
                # leaves out the name of the function called, which it reads.
                for lineno, message, _, context in extract(
                    cast(Any, method), held, keywords, options={"trimmed": "true"}
                ):
                    said = message if isinstance(message, str) else message[0]
                    found = template.get(said, kind or context)
                    if found and found.pluralizable != isinstance(message, tuple):
                        raise ValueError(
                            f"{where}:{lineno}: {said!r} is said both counted and not, "
                            + "which gettext holds as one message: give one a context"
                        )
                    _ = template.add(
                        message, "", [(where, lineno)], context=kind or context
                    )
    return template


@dataclass(frozen=True)
class Proof:
    path: Path
    current: str | None
    written: str
    untranslated: int
    fuzzy: int

    @property
    def behind(self) -> bool:
        return self.current != self.written


def proofs(
    tags: Iterable[str] = (),
    root: Path = settings.PROJECT_ROOT,
    catalogs: Path = _CATALOGS,
) -> list[Proof]:
    template = _extracted(root)
    paths = {p.stem: p for p in catalogs.glob("*.po")}
    paths |= {tag: catalogs / f"{tag}.po" for tag in tags}
    found: list[Proof] = []
    for tag, path in sorted(paths.items()):
        current = path.read_text() if path.exists() else None
        catalog = _begun(tag) if current is None else read_po(StringIO(current), tag)
        # Accommodating for Babel, which matches a new message to an untranslated plural one as
        # if it were translated: what holds no translation comes anew from the code.
        for m in [m for m in catalog if m.id and not _translated(m)]:
            catalog.delete(m.id, m.context)
        catalog.update(template, update_creation_date=False)
        written = BytesIO()
        write_po(written, catalog, include_lineno=False, ignore_obsolete=True)
        said = [m for m in catalog if m.id]
        untranslated = sum(not _translated(m) for m in said)
        fuzzy = sum(m.fuzzy for m in said)
        found.append(
            Proof(path, current, written.getvalue().decode(), untranslated, fuzzy)
        )
    return found


def check(baseline: bool) -> None:
    found = proofs()
    behind = [p for p in found if p.behind]
    flags: list[str] = []
    for p in found:
        if baseline and p.behind:
            flags.append(
                f"{_shown(p.path)}: behind the code at the baseline: the code changed "
                + "without chatddx locale write; investigate before work proceeds"
            )
        elif not baseline and (p.untranslated or p.fuzzy):
            flags.append(f"{_shown(p.path)}: {_left(p)}")
    for flag in flags:
        print(f"flag: {flag}", file=sys.stderr)
    if behind and not baseline:
        shown = ", ".join(_shown(p.path) for p in behind)
        raise SystemExit(f"locale: {shown} behind the code: run chatddx locale write")
    if baseline and flags:
        raise SystemExit(1)
    if not flags:
        print("ok")


def write(tags: Iterable[str]) -> None:
    written: list[str] = []
    for p in proofs(tags):
        if not p.behind:
            continue
        p.path.parent.mkdir(parents=True, exist_ok=True)
        _ = p.path.write_text(p.written)
        written.append(
            f"{_shown(p.path)}: {'new, ' if p.current is None else ''}{_left(p)}"
        )
    print("\n".join(written) or "nothing to write")


def _locale(path: Path) -> Locale:
    try:
        with path.open("rb") as held:
            catalog = read_po(held, path.stem, abort_invalid=True)
    except PoFileError as e:
        raise ValueError(f"{path}: {e}") from None
    wrong = [
        f"{m.id!r}: {e}" for m, errors in catalog.check() if not m.fuzzy for e in errors
    ]
    if wrong:
        raise ValueError(f"{path}: {'; '.join(wrong)}")
    compiled = BytesIO()
    write_mo(compiled, catalog)
    _ = compiled.seek(0)
    islands = {
        _keyed(m): _forms(m)
        for m in catalog
        if m.id and not m.fuzzy and _translated(m) and _shared(m)
    }
    return Locale(path.stem, GNUTranslations(compiled), islands)


# Policy: the catalog put in an island's page holds only what the islands say, and the
# whoopses the API may answer them with.
def _shared(message: Message) -> bool:
    return message.context == _WHOOPS or any(
        where.startswith(_ISLANDS) for where, _ in message.locations
    )


def _forms(message: Message) -> str | list[str]:
    string = message.string
    return string if isinstance(string, str) else list(string or ())


def _keyed(message: Message) -> str:
    said = message.id if isinstance(message.id, str) else message.id[0]
    return said if message.context is None else f"{message.context}\x04{said}"


def _preferred(accept_language: str) -> list[str]:
    ranked: list[tuple[float, int, str]] = []
    for at, part in enumerate(accept_language.split(",")):
        tag, _, params = part.partition(";")
        tag = tag.strip()
        weight = 1.0
        for param in params.split(";"):
            key, _, value = param.strip().partition("=")
            if key == "q":
                try:
                    weight = float(value)
                except ValueError:
                    weight = 0.0
        if tag and tag != "*" and weight > 0:
            ranked.append((-weight, at, tag.lower()))
    return [tag for _, _, tag in sorted(ranked)]


def _begun(tag: str) -> Catalog:
    language = Language.parse(tag)
    return Catalog(
        locale=language,
        header_comment=f"# The portal's messages in {language.english_name}.",
        project="chatddx",
        version="portal",
        fuzzy=False,
    )


def _literal(source: str) -> str:
    said = ast.literal_eval(source)
    assert isinstance(said, str)
    return said


def _translated(message: Message) -> bool:
    string = message.string
    return all(string) if isinstance(string, (tuple, list)) else bool(string)


def _left(proof: Proof) -> str:
    return f"{proof.untranslated} untranslated, {proof.fuzzy} fuzzy"


def _shown(path: Path) -> str:
    try:
        return str(path.relative_to(settings.PROJECT_ROOT))
    except ValueError:
        return str(path)

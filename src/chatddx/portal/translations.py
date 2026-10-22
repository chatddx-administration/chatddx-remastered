import difflib
import json
import re
from collections.abc import Collection, Mapping
from dataclasses import dataclass

from pydantic import ValidationError
from starlette.datastructures import FormData

from chatddx.api import families as api_families, schemas, threads as api
from chatddx.bench import Bench
from chatddx.catalog import threads
from chatddx.catalog.language import recipe_language
from chatddx.factors.base import language_tag, resolve
from chatddx.factors.request import Recipe, Translations, texts

# Policy: an entry under half of whose words are the text's is too far off to start from.
NEAR = 0.5

_WORDS = re.compile(r"\w+|\s+|[^\w\s]")


@dataclass(frozen=True)
class Entry:
    text: str
    translation: str
    sent: bool
    held: bool
    started: str | None = None

    @property
    def uneven(self) -> bool:
        return bool(self.translation) and edges(self.text) != edges(self.translation)


@dataclass(frozen=True)
class Translating:
    into: str | None
    languages: list[str]
    cased: list[str]
    entries: list[Entry]
    configurations: list[tuple[schemas.Thread, str | None]]


def edges(text: str) -> tuple[str, str]:
    lead = text[: len(text) - len(text.lstrip())]
    if lead == text:
        return lead, ""
    return lead, text[len(text.rstrip()) :]


def visible(text: str) -> str:
    lead, trail = edges(text)
    core = text[len(lead) : len(text) - len(trail)]
    shown = [e.replace(" ", "·").replace("\t", "⇥") for e in (lead, trail)]
    return (shown[0] + core + shown[1]).replace("\n", "⏎\n")


def closest(text: str, unused: Mapping[str, str]) -> tuple[str, str] | None:
    best: tuple[float, str, str] | None = None
    words = _WORDS.findall(text)
    for was, translation in unused.items():
        held = _WORDS.findall(was)
        matched = difflib.SequenceMatcher(None, held, words, autojunk=False)
        kept = sum(
            len("".join(held[m.a : m.a + m.size]))
            for m in matched.get_matching_blocks()
        )
        score = kept / max(len(was), len(text), 1)
        if score >= NEAR and (best is None or score > best[0]):
            best = (score, was, translation)
    return None if best is None else (best[1], best[2])


def _recipe(bench: Bench, head: int) -> Recipe | None:
    edit = bench.rows.edit(head)
    return None if edit is None else threads.recipe(bench.rows, edit)


def holding(
    bench: Bench, versions: Collection[str]
) -> list[tuple[schemas.Thread, Recipe]]:
    found: list[tuple[schemas.Thread, Recipe]] = []
    for t in api.threads(bench, "configuration", purpose="generation"):
        recipe = _recipe(bench, t.head.id)
        if recipe is not None and recipe.translations in versions:
            found.append((t, recipe))
    return found


def translating(
    bench: Bench, held: Translations, versions: list[str], into: str | None
) -> Translating:
    configurations = holding(bench, versions)
    get = bench.store.get
    sent = {
        t for _, r in configurations for found in texts(r, get).values() for t in found
    }
    own = {recipe_language(bench.rows, r) for _, r in configurations}
    cased = {f.language for f in api_families.families(bench) if f.language}
    languages = sorted(held.into)
    into = next(iter(languages), None) if into is None else language_tag(into)
    entries: list[Entry] = []
    if into is not None:
        given = held.into.get(into, {})
        for text in sorted(sent - given.keys()):
            near = closest(text, given)
            entries.append(
                Entry(text, "", sent=True, held=False)
                if near is None
                else Entry(text, near[1], sent=True, held=False, started=near[0])
            )
        entries += [Entry(t, tr, t in sent, held=True) for t, tr in given.items()]
    return Translating(
        into,
        languages,
        sorted(c for c in cased - set(languages) if c not in own),
        entries,
        [
            (t, None if r.translations == versions[-1] else versions[-1])
            for t, r in configurations
        ],
    )


def begun(bench: Bench, configuration: int, into: str) -> list[Entry]:
    shown = api.thread(bench, configuration)
    recipe = _recipe(bench, shown.head.id) if shown.kind == "skeleton" else None
    if recipe is None:
        raise ValueError(
            f"{shown.name or shown.title} has no recipe whose texts to translate"
        )
    get = bench.store.get
    held = (
        {}
        if recipe.translations is None
        else resolve(get, recipe.translations, Translations).into.get(into, {})
    )
    found = dict.fromkeys(t for part in texts(recipe, get).values() for t in part)
    return [Entry(t, held.get(t, ""), sent=True, held=False) for t in found]


def posted(form: FormData) -> dict[str, str]:
    entries: dict[str, str] = {}
    for key in form:
        if not key.startswith("s."):
            continue
        at = key.removeprefix("s.")
        given = form.get(f"t.{at}", "")
        # Accommodating for browsers, which send a textarea's line breaks as CRLF.
        translation = given.replace("\r\n", "\n") if isinstance(given, str) else ""
        if translation and not form.get(f"out.{at}"):
            entries[str(json.loads(str(form.get(key))))] = translation
    return entries


def written(
    held: Translations | None, into: str, entries: dict[str, str]
) -> Translations:
    languages = {} if held is None else dict(held.into)
    if entries:
        languages[language_tag(into)] = entries
    else:
        _ = languages.pop(into, None)
    if not languages:
        raise ValueError(
            "translations hold a language or more: translate a text, or delete them"
        )
    try:
        return Translations(into=languages)
    except ValidationError as e:
        raise ValueError(e.errors()[0]["msg"].removeprefix("Value error, ")) from None

from collections.abc import Iterable

from .model import LANGUAGE


def variant_name(name: str, language: str | None) -> str:
    return name if language is None else f"{name} ({language})"


def made_in(name: str) -> tuple[str, str | None]:
    base, opened, rest = name.rpartition(" (")
    if opened and rest.endswith(")") and LANGUAGE.match(rest[:-1]):
        return base, rest[:-1]
    return name, None


def variants_for(
    name: str, names: Iterable[str], language: str | None = None
) -> list[str]:
    return sorted(
        n
        for n in names
        if (made := made_in(n))[0] == name
        and made[1] is not None
        and language in (None, made[1])
    )


def language_of(name: str) -> tuple[str, str | None]:
    made = made_in(name)
    if made[1] is not None:
        return made
    base, _, last = name.rpartition(" ")
    return (base, last) if base and LANGUAGE.match(last) else (name, None)

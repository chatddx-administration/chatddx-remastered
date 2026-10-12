from collections.abc import Collection, Iterable

from .model import LANGUAGE


def variant_name(name: str, language: str | None, model: str | None) -> str:
    qualifiers = [q for q in (language, model) if q is not None]
    return f"{name} ({', '.join(qualifiers)})" if qualifiers else name


def made_for(
    name: str, models: Collection[str]
) -> tuple[str, str | None, str | None] | None:
    base, opened, rest = name.rpartition(" (")
    if not opened or not rest.endswith(")"):
        return None
    match rest[:-1].split(", "):
        case [language, model] if LANGUAGE.match(language) and model in models:
            return base, language, model
        case [one] if one in models:
            return base, None, one
        case [one] if LANGUAGE.match(one):
            return base, one, None
        case _:
            return None


def variants_for(
    name: str, names: Iterable[str], model: str | None, language: str | None = None
) -> list[str]:
    models = [] if model is None else [model]
    return sorted(
        n
        for n in names
        if (made := made_for(n, models)) is not None
        and made[0] == name
        and made[2] in (None, model)
        and language in (None, made[1])
    )


def language_of(name: str) -> tuple[str, str | None]:
    made = made_for(name, ())
    if made is not None and made[1] is not None:
        return made[0], made[1]
    base, _, last = name.rpartition(" ")
    return (base, last) if base and LANGUAGE.match(last) else (name, None)

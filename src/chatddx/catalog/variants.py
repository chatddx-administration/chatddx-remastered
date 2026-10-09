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


def variants_for(name: str, names: Iterable[str], model: str | None) -> list[str]:
    models = [] if model is None else [model]
    return sorted(
        n
        for n in names
        if (made := made_for(n, models)) is not None
        and made[0] == name
        and made[2] in (None, model)
    )

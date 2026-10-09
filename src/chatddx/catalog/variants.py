from collections.abc import Collection, Iterable

from .model import LANGUAGE


# What's made for a language, a model or both is named after them, so that one name finds
# the variant that fits: `NAME (LANGUAGE)`, `NAME (MODEL)` or `NAME (LANGUAGE, MODEL)`.
def variant_name(name: str, language: str | None, model: str | None) -> str:
    qualifiers = [q for q in (language, model) if q is not None]
    return f"{name} ({', '.join(qualifiers)})" if qualifiers else name


# What a variant's name says it was made from and for, or None for a name that isn't a
# variant's; `models` are the models a variant may be made for.
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


# The variants of `name` among `names` that `model` may use: those made for it, or for
# every model.
def variants_for(name: str, names: Iterable[str], model: str | None) -> list[str]:
    models = [] if model is None else [model]
    return sorted(
        n
        for n in names
        if (made := made_for(n, models)) is not None
        and made[0] == name
        and made[2] in (None, model)
    )

from chatddx.catalog import threads

from .errors import Ambiguous
from .model import SAVED, Written
from .seen import Seen, compiled, compiled_with, linted
from .variation import TriedVariation


def save(seen: Seen, variation: TriedVariation, name: str) -> Written:
    mine = threads.find(seen.rows, "skeleton", name, owner=seen.person.id)
    if len(mine) > 1:
        raise Ambiguous(
            f"{seen.person.login} has {len(mine)} configurations named {name!r}"
        )
    if not mine:
        return kept(seen, variation, None, name)
    return kept(seen, variation, mine[0], name, threads.head(seen.rows, mine[0]).id)


def kept(
    seen: Seen,
    variation: TriedVariation,
    thread: int | None,
    name: str | None,
    head: int | None = None,
) -> Written:
    skeleton = seen.skeleton(variation)
    with seen.conn.transaction():
        compilation = (
            keep_compilation(seen, variation) or variation.configuration.compilation
        )
        edit, kept = seen.catalog.keep(
            skeleton.digest,
            seen.person.id,
            thread,
            name=name,
            compilation=compilation,
            forked_from=variation.configuration.id,
            head=head,
        )
    return Written(edit, SAVED[kept], linted(seen, skeleton.digest))


def keep_compilation(
    seen: Seen, variation: TriedVariation, into: str | None = None
) -> str | None:
    recipe = variation.varied
    if recipe is None or (into is None and not variation.parts):
        return None
    registry, compilation = compiled(seen, recipe, compiled_with(seen, variation), into)
    _ = seen.store.add(registry, [compilation.digest])
    return compilation.digest

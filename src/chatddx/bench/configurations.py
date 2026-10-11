from .errors import Ambiguous, NotFound
from .model import SAVED, Saved
from .variation import TriedVariation
from .view import Seen


# Keeps the variation as the person's own configuration, under `name`: a new version of
# their thread of that name, or else a fork of the configuration's thread.
def save(seen: Seen, variation: TriedVariation, name: str) -> Saved:
    mine = seen.catalog.find("skeleton", name, owner=seen.person.id)
    if len(mine) > 1:
        raise Ambiguous(
            f"{seen.person.login} has {len(mine)} configurations named {name!r}"
        )
    if not mine:
        return fork(seen, variation, name)
    return edit(seen, mine[0], variation, seen.catalog.head(mine[0]).id)


# Keeps the variation as a new configuration of the person's own, named `name` and forked
# from the configuration's edit it varies.
def fork(seen: Seen, variation: TriedVariation, name: str) -> Saved:
    return _kept(seen, variation, None, name)


# Keeps the variation as a new version of `thread`, a configuration the person owns whose
# head was `head` when they saw it; nothing is written when it is the head already.
def edit(seen: Seen, thread: int, variation: TriedVariation, head: int) -> Saved:
    _, about = seen.thread_by_id(thread, "configuration")
    if not about.owned_by(seen.person.id):
        raise NotFound(f"no configuration {thread} of yours")
    name = about.name or seen.catalog.title(thread)
    return _kept(seen, variation, thread, name, head)


def _kept(
    seen: Seen,
    variation: TriedVariation,
    thread: int | None,
    name: str,
    head: int | None = None,
) -> Saved:
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
    what = SAVED[kept]
    recipe = seen.catalog.recipe(edit.thread)
    return Saved(name, skeleton.digest, what, TriedVariation(edit, name, recipe))


# Stores what an unsaved skeleton was compiled from, by the running code.
def keep_compilation(seen: Seen, variation: TriedVariation) -> str | None:
    recipe = variation.varied
    if not variation.parts or recipe is None:
        return None
    registry, compilation = seen.compiled(recipe)
    _ = seen.store.add(registry, [compilation.digest])
    return compilation.digest

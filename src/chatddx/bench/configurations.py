from .errors import Ambiguous, NotFound
from .model import SAVED, Saved
from .variation import TriedVariation
from .view import View


# Keeps the variation as the person's own configuration, under `name`: a new version of
# their thread of that name, or else a fork of the configuration's thread.
def save(view: View, variation: TriedVariation, name: str) -> Saved:
    mine = view.catalog.find("skeleton", name, owner=view.person.id)
    if len(mine) > 1:
        raise Ambiguous(
            f"{view.person.login} has {len(mine)} configurations named {name!r}"
        )
    if not mine:
        return fork(view, variation, name)
    return edit(view, mine[0], variation, view.catalog.head(mine[0]).id)


# Keeps the variation as a new configuration of the person's own, named `name` and forked
# from the configuration's edit it varies.
def fork(view: View, variation: TriedVariation, name: str) -> Saved:
    return _kept(view, variation, None, name)


# Keeps the variation as a new version of `thread`, a configuration the person owns whose
# head was `head` when they saw it; nothing is written when it is the head already.
def edit(view: View, thread: int, variation: TriedVariation, head: int) -> Saved:
    _, about = view.thread_by_id(thread, "configuration")
    if not about.owned_by(view.person.id):
        raise NotFound(f"no configuration {thread} of yours")
    name = about.name or view.catalog.title(thread)
    return _kept(view, variation, thread, name, head)


def _kept(
    view: View,
    variation: TriedVariation,
    thread: int | None,
    name: str,
    head: int | None = None,
) -> Saved:
    skeleton = view.skeleton(variation)
    with view.conn.transaction():
        compilation = (
            keep_compilation(view, variation) or variation.configuration.compilation
        )
        edit, kept = view.catalog.keep(
            skeleton.digest,
            view.person.id,
            thread,
            name=name,
            compilation=compilation,
            forked_from=variation.configuration.id,
            head=head,
        )
    what = SAVED[kept]
    recipe = view.catalog.recipe(edit.thread)
    return Saved(name, skeleton.digest, what, TriedVariation(edit, name, recipe))


# Stores what an unsaved skeleton was compiled from, by the running code.
def keep_compilation(view: View, variation: TriedVariation) -> str | None:
    recipe = variation.varied
    if not variation.parts or recipe is None:
        return None
    registry, compilation = view.compiled(recipe)
    _ = view.store.add(registry, [compilation.digest])
    return compilation.digest

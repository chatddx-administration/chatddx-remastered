from dataclasses import dataclass

from chatddx.catalog import Edit, Subject, read, threads, titles
from chatddx.factors.base import Component, Invalid, resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.engine import model_of
from chatddx.factors.request import Recipe, Skeleton
from chatddx.factors.scoring import Judge, Scorer
from chatddx.factors.trial import Trial, replicates
from chatddx.identity import owns, preferred, sees

from .components import edit as edit_component
from .errors import NotFound
from .following import follow_moved
from .model import Written
from .seen import Seen, compiled, linted, worded

# Policy: what can't be used until it is updated, in the order it is updated, as a
# scorer's update reads its judges': what holds weights its model's handle no longer
# holds, a scorer asking such a judge, and a trial whose engine no endpoint here serves.
UPDATED = ("skeleton", "judge", "scorer", "trial")


@dataclass(frozen=True)
class Updated:
    thread: int
    written: Written | None
    refused: ValueError | None


def outdated(seen: Seen, edit: Edit, kind: str) -> bool:
    match kind:
        case "skeleton":
            recipe = threads.recipe(seen.rows, edit)
            return recipe is not None and _behind(seen, recipe.model)
        case "judge":
            return _behind(seen, resolve(seen.store.get, edit.digest, Judge).model)
        case "scorer":
            held = resolve(seen.store.get, edit.digest, Scorer)
            return any(_judge_behind(seen, j) for j in held.judges)
        case "trial":
            engine = resolve(seen.store.get, edit.digest, Trial).engine
            try:
                _ = seen.inventory.serving(engine)
            except LookupError:
                return True
            return False
        case _:
            return False


def update(seen: Seen, thread: int, head: int) -> Written | None:
    edit, about, word = worded(seen, thread)
    if not owns(seen.person.id, about):
        raise NotFound(f"no {word} {thread} of yours")
    kind = threads.thread(seen.rows, thread).kind
    if not outdated(seen, edit, kind):
        return None
    name = titles.title(seen.rows, thread)
    match kind:
        case "skeleton":
            return follow_moved(seen, thread, head)
        case "scorer":
            labels = read.labels(seen.rows, edit.id)
            return edit_component(
                seen, thread, head, _scorer(seen, edit, name), labels=labels
            )
        case "judge":
            made, registry, compilations = _judge(seen, edit, name)
        case _:
            made, registry, compilations = _trial(seen, edit, name)
    with seen.conn.transaction():
        _ = seen.store.add(registry, [made.digest, *compilations])
        kept = seen.catalog.edit(thread, made.digest, seen.person.id, head=head)
    return Written(kept, "a new version", linted(seen, made.digest))


def update_all(seen: Seen) -> list[Updated]:
    found: list[Updated] = []
    for kind in UPDATED:
        for edit in _outdated_own(seen, kind):
            try:
                found.append(
                    Updated(edit.thread, update(seen, edit.thread, edit.id), None)
                )
            except ValueError as e:
                found.append(Updated(edit.thread, None, e))
    return found


def outdated_own(seen: Seen) -> list[int]:
    return [e.thread for kind in UPDATED for e in _outdated_own(seen, kind)]


def _outdated_own(seen: Seen, kind: str) -> list[Edit]:
    return [
        edit
        for edit, about in threads.heads(seen.rows, kind)
        if owns(seen.person.id, about) and outdated(seen, edit, kind)
    ]


# Policy: weights no model thread holds, or several do, aren't out of date, as
# src/chatddx/bench/seen.py:Seen.handle says what is wrong where they are tried.
def _behind(seen: Seen, weights: str) -> bool:
    held = {e.thread for e in seen.rows.edits_holding([weights])}
    if len(held) != 1:
        return False
    return threads.head(seen.rows, held.pop()).digest != weights


def _judge_behind(seen: Seen, judge: str) -> bool:
    return _behind(seen, resolve(seen.store.get, judge, Judge).model)


def _judge(seen: Seen, edit: Edit, name: str) -> tuple[Judge, Registry, list[str]]:
    held = resolve(seen.store.get, edit.digest, Judge)
    weights = seen.handle(held.model).weights
    skeleton, registry, compilations = _skeleton(seen, held.skeleton, weights, name)
    made = Judge.model_validate(
        held.model_dump(mode="json") | {"skeleton": skeleton, "model": weights}
    )
    _loaded(seen, registry, made)
    return made, registry, compilations


def _trial(seen: Seen, edit: Edit, name: str) -> tuple[Trial, Registry, list[str]]:
    held = resolve(seen.store.get, edit.digest, Trial)
    weights = model_of(held.engine, seen.store.get).digest
    handle = seen.handle(weights)
    engine = seen.served(handle).engine
    skeleton, registry, compilations = (
        (held.skeleton, Registry(), [])
        if handle.weights == weights
        else _skeleton(seen, held.skeleton, handle.weights, name)
    )
    shape = resolve(
        registry.get if skeleton in registry else seen.store.get, skeleton, Skeleton
    )
    made = Trial(
        skeleton=skeleton,
        engine=engine,
        cases=held.cases,
        cleanup=held.cleanup,
        seeds=replicates(shape, held.seeds),
    )
    _loaded(seen, registry, made)
    return made, registry, compilations


# Policy: a skeleton compiled from a recipe is compiled again for the weights, against
# the current facts and into the language it was; one written by hand is kept as it is.
def _skeleton(
    seen: Seen, skeleton: str, weights: str, name: str
) -> tuple[str, Registry, list[str]]:
    made = seen.rows.compilations(skeleton)
    if not made:
        return skeleton, Registry(), []
    recipe = Recipe.model_validate(made[0].recipe.model_dump() | {"model": weights})
    try:
        registry, compilation = compiled(seen, recipe, into=made[0].into)
    except ValueError as e:
        raise Invalid.of(
            "%(name)s can't be updated: %(refused)s", name=name, refused=str(e)
        ) from None
    return compilation.skeleton, registry, [compilation.digest]


def _scorer(seen: Seen, edit: Edit, name: str) -> Scorer:
    held = resolve(seen.store.get, edit.digest, Scorer)
    latest: dict[str, str] = {}
    for judge in held.judges:
        if not _judge_behind(seen, judge):
            continue
        found = _latest(seen, judge)
        if found is None or _judge_behind(seen, found):
            raise Invalid.of(
                "%(name)s can't be updated until %(judge)s is",
                name=name,
                judge=seen.title(judge),
            )
        latest[judge] = found
    views = [
        v.model_dump(mode="json")
        | ({"judge": latest[v.judge]} if v.judge in latest else {})
        for v in held.views
    ]
    return Scorer.model_validate(held.model_dump(mode="json") | {"views": views})


# Policy: a judge's latest version is its thread's head, the person's own fork of it
# first, as a fork's first version holds the judge it was forked from.
def _latest(seen: Seen, judge: str) -> str | None:
    held = sorted({e.thread for e in seen.rows.edits_holding([judge])})
    known = read.abouts(seen.rows, [Subject(thread=t) for t in held])
    shown = [
        (t, a.owner)
        for t in held
        if sees(seen.person.id, a := known[Subject(thread=t)])
    ]
    found = next(iter(preferred(seen.person.id, shown)), None)
    return None if found is None else threads.head(seen.rows, found).digest


def _loaded(seen: Seen, registry: Registry, component: Component) -> None:
    held = seen.store.load(
        s.digest for s in component.refs() if s.digest not in registry
    )
    for digest in held:
        if digest not in registry:
            _ = registry.add(held.get(digest))
    _ = registry.add(component)

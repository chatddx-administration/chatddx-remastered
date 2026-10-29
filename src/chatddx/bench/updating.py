from dataclasses import dataclass

from chatddx.catalog import (
    LANGUAGE_KINDS,
    THREAD_KINDS,
    Divergence,
    Edit,
    Labels,
    Part,
    Subject,
    read,
    threads,
    titles,
)
from chatddx.factors.base import Component, Invalid, resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.engine import model_of
from chatddx.factors.request import Recipe, Skeleton
from chatddx.factors.scoring import Expectation, Judge, Scorer
from chatddx.factors.trial import Trial, replicates
from chatddx.identity import owns, preferred, sees

from .components import keep_language
from .errors import NotFound
from .model import COMPILED_LANGUAGE, LABELLED, Kin, Proposed, Reason, Written
from .seen import Seen, check_expecting, check_scorer, compiled, linted, worded

# Policy: what is read is updated before what reads it: a scorer's update reads its
# judges', and a fork's its origin's, which a fork's greater id says.
_LATER = ("judge", "scorer", "trial")
_CAUGHT_UP = ("skeleton", *_LATER)
_BLOCKING: tuple[Reason, ...] = ("model", "judge", "engine")


@dataclass(frozen=True)
class Updated:
    thread: int
    written: Written | None
    refused: ValueError | None
    remodelled: tuple[str, str] | None


def outdated(seen: Seen, edit: Edit, kind: str) -> bool:
    return any(r in _BLOCKING for r in _caught_up(seen, edit, kind, facts=False))


def proposal(seen: Seen, thread: int) -> Proposed | None:
    found = _proposed(seen, thread)
    return None if found is None else found[0]


def update(seen: Seen, thread: int, head: int, language: str | None = None) -> Written:
    _, about, word = worded(seen, thread)
    if not owns(seen.person.id, about):
        raise NotFound(f"no {word} {thread} of yours")
    found = _proposed(seen, thread)
    if found is None:
        raise ValueError(f"{word} {thread} has nothing to update")
    return _kept(seen, thread, head, *found, language)


def update_all(seen: Seen) -> list[Updated]:
    found: list[Updated] = []
    for thread in _own(seen):
        try:
            proposed = _proposed(seen, thread)
            if proposed is None:
                continue
            head = threads.head(seen.rows, thread).id
            written = _kept(seen, thread, head, *proposed)
        except ValueError as e:
            found.append(Updated(thread, None, e, None))
            continue
        found.append(Updated(thread, written, None, proposed[0].remodelled))
    return found


def behind_own(seen: Seen) -> list[int]:
    return [t for t in _own(seen) if _behind(seen, t)]


def lineage(seen: Seen, thread: int) -> list[Kin]:
    _ = seen.thread(thread, deleted=True)
    first = thread
    while (up := threads.origin(seen.rows, first)) is not None and _shown(seen, up):
        first = up
    found: list[Kin] = []

    def down(at: int, origin: int | None) -> None:
        edit, about = seen.thread(at, deleted=True)
        diverged = threads.divergence(seen.rows, at)
        found.append(Kin(edit, about, origin, diverged, _behind(seen, at)))
        for fork in sorted(threads.forks(seen.rows, at)):
            if _shown(seen, fork):
                down(fork, at)

    down(first, None)
    return found


def _shown(seen: Seen, thread: int) -> bool:
    try:
        _ = seen.thread(thread, deleted=True)
    except NotFound:
        return False
    return True


def _behind(seen: Seen, thread: int) -> bool:
    edit = threads.head(seen.rows, thread)
    kind = threads.thread(seen.rows, thread).kind
    return _origin_moved(seen, thread) is not None or bool(_caught_up(seen, edit, kind))


def _own(seen: Seen) -> list[int]:
    found = [
        t
        for kind in THREAD_KINDS
        for t in seen.rows.threads(kind)
        if t.forked_from is not None or kind in _CAUGHT_UP
    ]
    known = read.abouts(seen.rows, [Subject(thread=t.id) for t in found])
    mine = [
        t
        for t in found
        if owns(seen.person.id, about := known[Subject(thread=t.id)])
        and not about.deleted
    ]
    ranked = sorted(mine, key=lambda t: (_rank(t.kind), t.id))
    return [t.id for t in ranked]


def _rank(kind: str) -> int:
    return _LATER.index(kind) + 1 if kind in _LATER else 0


def _origin_moved(seen: Seen, thread: int) -> Divergence | None:
    diverged = threads.divergence(seen.rows, thread)
    if diverged is None or not diverged.moved:
        return None
    origin = Subject(thread=diverged.origin_head.thread)
    return diverged if sees(seen.person.id, read.about(seen.rows, origin)) else None


def _caught_up(seen: Seen, edit: Edit, kind: str, facts: bool = True) -> list[Reason]:
    get = seen.store.get
    match kind:
        case "skeleton":
            recipe = threads.recipe(seen.rows, edit)
            if recipe is None:
                return []
            found: list[Reason] = ["model"] if _newer(seen, recipe.model) else []
            if facts and any(
                b.path == "/facts" and b.head is not None
                for b in threads.behind(seen.rows, edit.thread)
            ):
                found.append("facts")
            return found
        case "judge":
            return (
                ["model"]
                if _newer(seen, resolve(get, edit.digest, Judge).model)
                else []
            )
        case "scorer":
            held = resolve(get, edit.digest, Scorer)
            return ["judge"] if any(_judge_behind(seen, j) for j in held.judges) else []
        case "trial":
            try:
                _ = seen.inventory.serving(resolve(get, edit.digest, Trial).engine)
            except LookupError:
                return ["engine"]
            return []
        case _:
            return []


def _proposed(seen: Seen, thread: int) -> tuple[Proposed, Registry, list[str]] | None:
    edit, _, _ = worded(seen, thread)
    kind = threads.thread(seen.rows, thread).kind
    diverged = _origin_moved(seen, thread)
    reasons: list[Reason] = ["origin"] if diverged else []
    reasons += _caught_up(seen, edit, kind)
    if not reasons:
        return None
    name = titles.title(seen.rows, thread)
    registry: Registry = Registry()
    more: list[str] = []
    held: Recipe | Component | None = None
    try:
        held = None if diverged is None else threads.proposal(seen.rows, thread)
        if held is None and diverged is not None:
            diverged = None
            reasons.remove("origin")
            if not reasons:
                return None
        if held is None:
            held = threads.recipe(seen.rows, edit) or seen.store.get(edit.digest)
        if isinstance(held, Recipe):
            if (newer := _newer(seen, held.model)) is not None:
                held = Recipe.model_validate(held.model_dump() | {"model": newer})
            registry, made = compiled(seen, held)
            digest, compilation = made.skeleton, made.digest
        else:
            held, registry, more = _component(seen, held, name)
            digest, compilation = registry.add(held), None
    except ValueError as e:
        if not isinstance(e, Invalid):
            e = Invalid.of(
                "%(name)s can't be updated: %(refused)s", name=name, refused=str(e)
            )
        refused = _proposal(seen, edit, kind, reasons, diverged, held, None, None, e)
        return refused, registry, more
    found = _proposal(seen, edit, kind, reasons, diverged, held, digest, compilation)
    return found, registry, more


def _proposal(
    seen: Seen,
    edit: Edit,
    kind: str,
    reasons: list[Reason],
    diverged: Divergence | None,
    held: Recipe | Component | None,
    digest: str | None,
    compilation: str | None,
    refused: ValueError | None = None,
) -> Proposed:
    return Proposed(
        reasons=tuple(reasons),
        about=_about(seen, edit, kind),
        divergence=diverged,
        remodelled=None if diverged is None else _remodelled(seen, diverged),
        proposal=held,
        digest=digest,
        compilation=compilation,
        refused=refused,
    )


def _component(
    seen: Seen, held: Component, name: str
) -> tuple[Component, Registry, list[str]]:
    registry, more = Registry(), []
    match held:
        case Judge() if _newer(seen, held.model) is not None:
            held, registry, more = _judge(seen, held, name)
        case Scorer() if any(_judge_behind(seen, j) for j in held.judges):
            held = _scorer(seen, held, name)
        case Trial() if _unserved(seen, held):
            held, registry, more = _trial(seen, held, name)
        case _:
            pass
    _loaded(seen, registry, held)
    return held, registry, more


def _kept(
    seen: Seen,
    thread: int,
    head: int,
    proposed: Proposed,
    registry: Registry,
    more: list[str],
    language: str | None = None,
) -> Written:
    if proposed.refused is not None:
        raise proposed.refused
    assert proposed.digest is not None and proposed.proposal is not None
    kind = threads.thread(seen.rows, thread).kind
    if language is not None and proposed.compilation is not None:
        raise ValueError(COMPILED_LANGUAGE)
    if language is not None and kind not in LANGUAGE_KINDS:
        raise ValueError(f"{kind} components have no language of their own")
    if isinstance(proposed.proposal, Expectation):
        check_expecting(seen, proposed.proposal, thread)
    labels = None
    if isinstance(proposed.proposal, Scorer):
        check_scorer(proposed.proposal)
        labels = _labels(seen, thread, proposed.divergence)
    diverged = proposed.divergence
    with seen.conn.transaction():
        _ = seen.store.add(registry, [proposed.compilation or proposed.digest, *more])
        if language is not None:
            keep_language(seen, proposed.digest, language)
        edit = seen.catalog.edit(
            thread,
            proposed.digest,
            seen.person.id,
            compilation=proposed.compilation,
            based_on=None if diverged is None else diverged.origin_head.id,
            head=head,
            labels=labels,
        )
    return Written(edit, "a new version", linted(seen, proposed.digest))


def _about(seen: Seen, edit: Edit, kind: str) -> str | None:
    match kind:
        case "skeleton":
            recipe = threads.recipe(seen.rows, edit)
            model = None if recipe is None else recipe.model
        case "judge":
            model = resolve(seen.store.get, edit.digest, Judge).model
        case _:
            model = None
    return None if model is None else model_of(model, seen.store.get).name


# Policy: a fork's own model is the one updating keeps, so only a model the fork took
# from its origin is said to move.
def _remodelled(seen: Seen, diverged: Divergence) -> tuple[str, str] | None:
    for path in ("/recipe/model", "/model"):
        moved = diverged.moves.get(path)
        if moved is None or path in diverged.varies:
            continue
        was, now = moved
        assert isinstance(was, str) and isinstance(now, str)
        return model_of(was, seen.store.get).name, model_of(now, seen.store.get).name
    return None


def _labels(seen: Seen, thread: int, diverged: Divergence | None) -> Labels:
    fork = read.labels(seen.rows, threads.head(seen.rows, thread).id)
    if diverged is None:
        return fork
    origin = read.labels(seen.rows, diverged.origin_head.id)
    kept: dict[tuple[Part, int], str] = {}
    for part in LABELLED:
        side = fork if f"/{part}s" in diverged.varies else origin
        kept |= {k: v for k, v in side.items() if k[0] == part}
    return kept


# Policy: weights no model thread holds, or several do, aren't out of date, as
# src/chatddx/bench/seen.py:Seen.handle says what is wrong where they are tried.
def _newer(seen: Seen, weights: str) -> str | None:
    held = {e.thread for e in seen.rows.edits_holding([weights])}
    if len(held) != 1:
        return None
    head = threads.head(seen.rows, held.pop()).digest
    return None if head == weights else head


def _judge_behind(seen: Seen, judge: str) -> bool:
    return _newer(seen, resolve(seen.store.get, judge, Judge).model) is not None


def _unserved(seen: Seen, trial: Trial) -> bool:
    try:
        _ = seen.inventory.serving(trial.engine)
    except LookupError:
        return True
    return False


def _judge(seen: Seen, held: Judge, name: str) -> tuple[Judge, Registry, list[str]]:
    weights = seen.handle(held.model).weights
    skeleton, registry, compilations = _skeleton(seen, held.skeleton, weights, name)
    made = Judge.model_validate(
        held.model_dump(mode="json") | {"skeleton": skeleton, "model": weights}
    )
    return made, registry, compilations


def _trial(seen: Seen, held: Trial, name: str) -> tuple[Trial, Registry, list[str]]:
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


def _scorer(seen: Seen, held: Scorer, name: str) -> Scorer:
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

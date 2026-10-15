from chatddx.catalog import LANGUAGE_KINDS, Divergence, Labels, Part
from chatddx.factors.bundle import Registry
from chatddx.factors.request import Recipe
from chatddx.factors.scoring import Expectation, Scorer
from chatddx.identity import owns, sees

from .components import keep_language
from .errors import NotFound
from .model import COMPILED_LANGUAGE, LABELLED, Proposed, Written
from .seen import Seen


def proposal(seen: Seen, thread: int) -> Proposed | None:
    _, _, word = seen.worded(thread)
    found = _proposed(seen, thread, word)
    return None if found is None else found[0]


def follow(seen: Seen, thread: int, head: int, language: str | None = None) -> Written:
    _, about, word = seen.worded(thread)
    if not owns(seen.person.id, about):
        raise NotFound(f"no {word} {thread} of yours")
    found = _proposed(seen, thread, word)
    if found is None:
        raise ValueError(f"{word} {thread} has nothing to follow")
    proposed, registry = found
    kind = seen.catalog.thread(thread).kind
    if language is not None and proposed.compilation is not None:
        raise ValueError(COMPILED_LANGUAGE)
    if language is not None and kind not in LANGUAGE_KINDS:
        raise ValueError(f"{kind} components have no language of their own")
    if isinstance(proposed.proposal, Expectation):
        seen.check_expecting(proposed.proposal, thread)
    labels = None
    if isinstance(proposed.proposal, Scorer):
        seen.check_scorer(proposed.proposal)
        labels = _followed_labels(seen, thread, proposed.divergence)
    kept = [proposed.compilation or proposed.digest]
    with seen.conn.transaction():
        _ = seen.store.add(registry, kept)
        if language is not None:
            keep_language(seen, proposed.digest, language)
        edit = seen.catalog.edit(
            thread,
            proposed.digest,
            seen.person.id,
            compilation=proposed.compilation,
            based_on=proposed.divergence.origin_head.id,
            head=head,
            labels=labels,
        )
    return Written(edit, "a new version", seen.linted(proposed.digest))


def _followed_labels(seen: Seen, thread: int, diverged: Divergence) -> Labels:
    fork = seen.catalog.labels(seen.catalog.head(thread).id)
    origin = seen.catalog.labels(diverged.origin_head.id)
    kept: dict[tuple[Part, int], str] = {}
    for part in LABELLED:
        side = fork if f"/{part}s" in diverged.varies else origin
        kept |= {k: v for k, v in side.items() if k[0] == part}
    return kept


def _proposed(seen: Seen, thread: int, word: str) -> tuple[Proposed, Registry] | None:
    diverged = seen.catalog.divergence(thread)
    if diverged is None or not diverged.moved:
        return None
    if not sees(seen.person.id, seen.about(diverged.origin_head.thread)):
        return None
    try:
        proposal = seen.catalog.proposal(thread)
        if proposal is None:
            return None
        if isinstance(proposal, Recipe):
            registry, compilation = seen.compiled(proposal)
            digest = compilation.skeleton
            proposed = Proposed(diverged, proposal, digest, compilation.digest)
        else:
            registry = seen.store.load(s.digest for s in proposal.refs())
            digest = registry.add(proposal)
            proposed = Proposed(diverged, proposal, digest, None)
    except ValueError as e:
        raise ValueError(
            f"{word} {thread}'s changes don't fit its origin's head: {e}"
        ) from None
    return proposed, registry

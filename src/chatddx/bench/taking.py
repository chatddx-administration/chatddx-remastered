from collections.abc import Iterable

from chatddx.catalog import About, Edit, Entry, EntryField, Subject
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Expectation

from .errors import Conflict, NotFound
from .model import Taken
from .view import Seen


# For each case, a fork of the one expectation under `schema` shared with the person, by
# `owner` when given, unless they have one of their own; in one transaction.
def take(
    seen: Seen, cases: Iterable[str], schema: str, owner: str | None = None
) -> Taken:
    if seen.rows.kind(schema) != "expectation_schema":
        raise ValueError(f"{schema} isn't a stored expectation schema")
    by = None if owner is None else seen.people.find(owner)
    if owner is not None and by is None:
        raise NotFound(f"no person {owner!r}")
    wanted = list(dict.fromkeys(cases))
    own = seen.catalog.expectation_choices(wanted, seen.person.id, schema)
    shared = seen.catalog.expectations_shared(wanted, seen.person.id, schema)
    found = Taken({}, {}, {}, [])
    with seen.conn.transaction():
        for case in wanted:
            offered = [
                (e, a) for e, a in shared[case] if by is None or a.owner == by.id
            ]
            if mine := sorted(own[case]):
                found.kept[case] = mine[0]
            elif not offered:
                found.missing.append(case)
            elif len(offered) > 1:
                found.choosing[case] = [e.thread for e, _ in offered]
            else:
                found.taken[case] = _fork(seen, *offered[0])
    return found


# A fork of an expectation thread shared with the person. With `replace`, their own of
# its case under its schema is deleted first, in the same transaction; without, it is a
# conflict.
def take_from(seen: Seen, thread: int, replace: bool = False) -> int:
    edit, about = seen.thread_by_id(thread, "expectation")
    if about.owner == seen.person.id:
        raise ValueError(f"expectation {thread} is yours already")
    held = resolve(seen.get, edit.digest, Expectation)
    case, schema = held.case, held.expectation_schema
    choices = seen.catalog.expectation_choices([case], seen.person.id, schema)
    mine = sorted(choices[case])
    if mine and not replace:
        raise Conflict(
            f"{seen.person.login} has their own expectation of {seen.title(case)} "
            + f"under {seen.title(schema)}, in thread {mine[0]}: replace it to "
            + "take this one"
        )
    gone = Entry(field=EntryField.DELETED)
    with seen.conn.transaction():
        for own in mine:
            seen.catalog.note(Subject(thread=own), gone, seen.person.id)
        return _fork(seen, edit, about)


def _fork(seen: Seen, head: Edit, about: About) -> int:
    made = seen.catalog.create(
        head.digest, seen.person.id, forked_from=head.id, name=about.name
    )
    return made.thread

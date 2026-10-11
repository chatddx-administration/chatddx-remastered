from collections.abc import Iterable

from chatddx.catalog import About, Edit, Entry, EntryField, Subject
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Expectation

from .errors import Conflict, NotFound
from .model import Taken
from .view import View


# For each case, a fork of the one expectation under `schema` shared with the person, by
# `owner` when given, unless they have one of their own; in one transaction.
def take(
    view: View, cases: Iterable[str], schema: str, owner: str | None = None
) -> Taken:
    if view.rows.kind(schema) != "expectation_schema":
        raise ValueError(f"{schema} isn't a stored expectation schema")
    by = None if owner is None else view.people.find(owner)
    if owner is not None and by is None:
        raise NotFound(f"no person {owner!r}")
    wanted = list(dict.fromkeys(cases))
    own = view.catalog.expectation_choices(wanted, view.person.id, schema)
    shared = view.catalog.expectations_shared(wanted, view.person.id, schema)
    found = Taken({}, {}, {}, [])
    with view.conn.transaction():
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
                found.taken[case] = _fork(view, *offered[0])
    return found


# A fork of an expectation thread shared with the person. With `replace`, their own of
# its case under its schema is deleted first, in the same transaction; without, it is a
# conflict.
def take_from(view: View, thread: int, replace: bool = False) -> int:
    edit, about = view.thread_by_id(thread, "expectation")
    if about.owner == view.person.id:
        raise ValueError(f"expectation {thread} is yours already")
    held = resolve(view.get, edit.digest, Expectation)
    case, schema = held.case, held.expectation_schema
    choices = view.catalog.expectation_choices([case], view.person.id, schema)
    mine = sorted(choices[case])
    if mine and not replace:
        raise Conflict(
            f"{view.person.login} has their own expectation of {view.title(case)} "
            + f"under {view.title(schema)}, in thread {mine[0]}: replace it to "
            + "take this one"
        )
    gone = Entry(field=EntryField.DELETED)
    with view.conn.transaction():
        for own in mine:
            view.catalog.note(Subject(thread=own), gone, view.person.id)
        return _fork(view, edit, about)


def _fork(view: View, head: Edit, about: About) -> int:
    made = view.catalog.create(
        head.digest, view.person.id, forked_from=head.id, name=about.name
    )
    return made.thread

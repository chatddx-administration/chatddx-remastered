from collections.abc import Collection
from types import EllipsisType

from chatddx.catalog import About, Entry, EntryField, Subject, read, threads
from chatddx.factors.scoring import Expectation

from .errors import NotFound
from .model import word_of
from .seen import Seen, check_expecting


def say(
    seen: Seen,
    thread: int,
    *,
    name: str | None | EllipsisType = ...,
    description: str | None = None,
    tags: Collection[str] | None = None,
    collaborators: Collection[str] | None = None,
    deleted: bool | None = None,
) -> About:
    found = seen.rows.thread(thread)
    word = word_of(None if found is None else found.kind)
    about = read.about(seen.rows, Subject(thread=thread))
    if found is None or about.owner != seen.person.id:
        raise NotFound(f"no {word} {thread} of yours")
    changing = (name, description, tags, collaborators) != (..., None, None, None)
    if about.deleted and deleted is not False and changing:
        raise ValueError(f"{word} {thread} is deleted: restore it to say more of it")
    if name == "":
        raise ValueError("a name can't be empty: none takes it away")
    if tags is not None and "" in tags:
        raise ValueError("a tag can't be empty")
    sharing: set[int] = (
        set() if collaborators is None else {_sharing(seen, c) for c in collaborators}
    )
    if seen.person.id in sharing:
        raise ValueError(f"{word} {thread} is yours: it is shared with others")

    said: list[Entry] = []
    if deleted is False and about.deleted:
        head = seen.store.get(threads.head(seen.rows, thread).digest)
        if isinstance(head, Expectation):
            check_expecting(seen, head, thread, "delete that one to restore this")
        said.append(Entry(field=EntryField.DELETED, present=False))
    if not isinstance(name, EllipsisType) and name != about.name:
        said.append(
            Entry(field=EntryField.NAME, present=False)
            if name is None
            else Entry(field=EntryField.NAME, value=name)
        )
    if description is not None and description != about.description:
        said.append(Entry(field=EntryField.DESCRIPTION, value=description))
    if tags is not None:
        said += [
            Entry(field=EntryField.TAG, value=t, present=t in tags)
            for t in sorted(about.tags.symmetric_difference(tags))
        ]
    if collaborators is not None:
        said += [
            Entry(field=EntryField.COLLABORATOR, person=c, present=c in sharing)
            for c in sorted(about.collaborators.symmetric_difference(sharing))
        ]
    if deleted and not about.deleted:
        said.append(Entry(field=EntryField.DELETED))
    with seen.conn.transaction():
        for entry in said:
            seen.catalog.note(Subject(thread=thread), entry, seen.person.id)
    return read.about(seen.rows, Subject(thread=thread))


def _sharing(seen: Seen, login: str) -> int:
    found = seen.people.find(login)
    if found is None:
        raise NotFound(f"no person {login!r}")
    return found.id

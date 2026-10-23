from collections.abc import Collection
from types import EllipsisType

from chatddx.catalog import About, Entry, EntryField, Subject, read, threads
from chatddx.factors.scoring import Expectation
from chatddx.identity import collaborates

from .errors import NotFound
from .model import word_of
from .seen import Seen, check_expecting


def say(
    seen: Seen,
    subject: Subject,
    *,
    name: str | None | EllipsisType = ...,
    description: str | None | EllipsisType = ...,
    tags: Collection[str] | None = None,
    collaborators: Collection[str] | None = None,
    deleted: bool | None = None,
    language: str | None = None,
) -> About:
    """Writes what holds of the thread or family itself in one transaction.
    `...` leaves a name or a description as it is and `None` takes it away.

    Reads the subject's entries before and after, a person per collaborator, and for a
    restored expectation thread the person's expectations of its case and schema.

    Heads-up:
    - Only families take language.
    - An expectation thread is refused while the person owns another of its case and
      schema.
    """
    what = _what(seen, subject)
    about = read.about(seen.rows, subject)
    if about.owner != seen.person.id:
        raise NotFound(f"no {what} of yours")
    changing = (name, description, tags, collaborators, language) != (
        ...,
        ...,
        None,
        None,
        None,
    )
    if about.deleted and deleted is not False and changing:
        raise ValueError(f"{what} is deleted: restore it to say more of it")
    if name == "":
        raise ValueError("a name can't be empty: none takes it away")
    if description == "":
        raise ValueError("a description can't be empty: none takes it away")
    if tags is not None and "" in tags:
        raise ValueError("a tag can't be empty")
    sharing: set[int] = (
        set() if collaborators is None else {_sharing(seen, c) for c in collaborators}
    )
    if seen.person.id in sharing:
        raise ValueError(f"{what} is yours: it is shared with others")

    said: list[Entry] = []
    if deleted is False and about.deleted:
        if subject.thread is not None:
            head = seen.store.get(threads.head(seen.rows, subject.thread).digest)
            if isinstance(head, Expectation):
                check_expecting(seen, head, subject.thread, restoring=True)
        said.append(Entry(field=EntryField.DELETED, present=False))
    if not isinstance(name, EllipsisType) and name != about.name:
        said.append(
            Entry(field=EntryField.NAME, present=False)
            if name is None
            else Entry(field=EntryField.NAME, value=name)
        )
    if not isinstance(description, EllipsisType) and description != about.description:
        said.append(
            Entry(field=EntryField.DESCRIPTION, present=False)
            if description is None
            else Entry(field=EntryField.DESCRIPTION, value=description)
        )
    if language is not None and language != about.language:
        said.append(Entry(field=EntryField.LANGUAGE, value=language))
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
            seen.catalog.note(subject, entry, seen.person.id)
    return read.about(seen.rows, subject)


def leave(seen: Seen, subject: Subject) -> About:
    """Takes the person out of what they see of a thread or a family shared with them,
    by an entry of their own, until its owner shares it with them again.

    Reads the subject's entries before and after, and writes one entry.
    """
    about = read.about(seen.rows, subject)
    if not collaborates(seen.person.id, about):
        raise NotFound(f"no {_what(seen, subject)} shared with {seen.person.login}")
    left = Entry(field=EntryField.COLLABORATOR, person=seen.person.id, present=False)
    with seen.conn.transaction():
        seen.catalog.note(subject, left, seen.person.id)
    return read.about(seen.rows, subject)


def _what(seen: Seen, subject: Subject) -> str:
    if subject.thread is None:
        return f"case {subject.family}"
    found = seen.rows.thread(subject.thread)
    return f"{word_of(None if found is None else found.kind)} {subject.thread}"


def _sharing(seen: Seen, login: str) -> int:
    found = seen.people.find(login)
    if found is None:
        raise NotFound.of("no person %(login)s", login=repr(login))
    return found.id

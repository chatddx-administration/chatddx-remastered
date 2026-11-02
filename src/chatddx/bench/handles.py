from chatddx.catalog import Subject, read
from chatddx.catalog.titles import display_digest
from chatddx.inventory import Inventory, broken as shared
from chatddx.store import Rows

from .model import KINDS


# Policy: What src/chatddx/bench/seen.py:Seen.handle and Seen.served rely on, checked as
# a process starts and before sync-archive commits.
def broken(rows: Rows, inventory: Inventory) -> list[str]:
    threads = [t.id for kind in KINDS["model"] for t in rows.threads(kind)]
    abouts = read.abouts(rows, [Subject(thread=t) for t in threads])
    held: dict[str, set[int]] = {}
    for edit in rows.edits(threads):
        held.setdefault(edit.digest, set()).add(edit.thread)
    found = [
        f"model threads {', '.join(abouts[Subject(thread=t)].name or str(t) for t in sorted(by))} "
        + f"hold weights {display_digest(digest)}, which one model thread should"
        for digest, by in held.items()
        if len(by) > 1
    ]
    return found + shared(inventory, rows.get)

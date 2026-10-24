from collections.abc import Sequence
from typing import Protocol

from chatddx.api import schemas
from chatddx.locale import listed, ngettext, tr


class Cased(Protocol):
    @property
    def name(self) -> str: ...
    @property
    def appendices(self) -> Sequence[str]: ...
    @property
    def earlier(self) -> bool: ...


def said_case(case: Cased, brief: bool = False) -> str:
    n = len(case.appendices)
    if not n:
        said = case.name
    elif brief:
        said = ngettext(
            "%(case)s + %(num)s appendix", "%(case)s + %(num)s appendices", n
        ) % {"case": case.name, "num": n}
    else:
        said = tr(
            "%(case)s with %(appendices)s",
            case=case.name,
            appendices=listed(case.appendices),
        )
    return tr("%(case)s (earlier)", case=said) if case.earlier else said


def said_thread(thread: schemas.Thread) -> str:
    if thread.name is not None:
        return thread.name
    if thread.expecting is not None:
        return tr("expectation for %(case)s", case=said_case(thread.expecting))
    return thread.title

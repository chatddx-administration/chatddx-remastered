import pytest

from chatddx.catalog import MovedOn, threads
from chatddx.catalog.test.memory import Memory
from chatddx.factors.bundle import Registry
from chatddx.factors.request import Sampling


def test_an_edit_made_on_a_head_that_moved_on_is_refused() -> None:
    reg = Registry()
    rows = Memory(reg)
    first = rows.start(reg.add(Sampling(temperature=0.6)))
    later = reg.add(Sampling(temperature=0.7))
    threads.check_edit(rows, first.thread, later, head=first.id)

    second = rows.save(first.thread, later)
    threads.check_edit(rows, first.thread, later, head=second.id)
    with pytest.raises(
        MovedOn,
        match=f"thread {first.thread} has moved on since edit {first.id}: its head "
        + f"is edit {second.id}",
    ):
        threads.check_edit(rows, first.thread, later, head=first.id)
    with pytest.raises(LookupError, match="no thread with id 99"):
        threads.check_edit(rows, 99, later, head=first.id)

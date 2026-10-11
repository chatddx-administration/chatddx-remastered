import pytest

from chatddx.catalog import families
from chatddx.catalog.test.memory import Memory
from chatddx.factors.base import resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Case
from chatddx.factors.test.sample import fp, world

pytestmark = pytest.mark.wip


def test_a_source_whose_texts_never_move_adopts_by_id_alone() -> None:
    reg = Registry()
    ids = world(reg)
    rows = Memory(reg)
    vignette = resolve(reg.get, ids["case"], Case).vignette
    _ = rows.bind(1, vignette)
    again = reg.add(Case(vignette=vignette.model_copy(update={"id": "c1-again"})))
    edited = reg.add(
        Case(vignette=vignette.model_copy(update={"fingerprint": fp("edited")}))
    )

    assert families.check_adoptable(rows, again, by_content=False).id == "c1-again"
    with pytest.raises(ValueError, match="new content"):
        _ = families.check_adoptable(rows, edited, by_content=False)

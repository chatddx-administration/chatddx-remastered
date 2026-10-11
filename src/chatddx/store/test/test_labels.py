import pytest
from psycopg import errors

from chatddx.catalog import Labels
from chatddx.factors.base import resolve
from chatddx.factors.scoring import Scoring
from chatddx.store import People
from chatddx.store.store import Connection
from chatddx.store.test.test_catalog import stored_world

pytestmark = pytest.mark.wip

LABELS: Labels = {
    ("view", 0): "top-1 match",
    ("view", 1): "judge",
    ("resource", 0): "synonyms",
}


def test_a_scorer_s_labels_are_written_with_its_edit(conn: Connection) -> None:
    catalog, _, reg, ids, alice = stored_world(conn)
    scorer = resolve(reg.get, ids["scoring"], Scoring).scorer
    first = catalog.create(scorer, alice.id, labels=LABELS)
    assert catalog.labels(first.id) == LABELS

    renamed: Labels = {**LABELS, ("view", 1): "judge grade"}
    kept, what = catalog.keep(scorer, alice.id, first.thread, labels=renamed)
    assert (what, kept.digest) == ("edited", scorer)
    assert (catalog.labels(first.id), catalog.labels(kept.id)) == (LABELS, renamed)
    assert catalog.keep(scorer, alice.id, first.thread, labels=renamed) == (
        kept,
        "unchanged",
    )
    assert catalog.keep(scorer, alice.id, first.thread) == (kept, "unchanged")
    unlabelled, what = catalog.keep(scorer, alice.id, first.thread, labels={})
    assert (what, catalog.labels(unlabelled.id)) == ("edited", {})


def test_labels_are_refused_where_a_scorer_has_nothing_to_label(
    conn: Connection,
) -> None:
    catalog, _, reg, ids, alice = stored_world(conn)
    scorer = resolve(reg.get, ids["scoring"], Scoring).scorer
    thread = catalog.create(scorer, alice.id).thread
    with pytest.raises(ValueError, match="has no view at position 2"):
        _ = catalog.edit(thread, scorer, alice.id, labels={("view", 2): "x"})
    with pytest.raises(ValueError, match="the label of view 0 is empty"):
        _ = catalog.edit(thread, scorer, alice.id, labels={("view", 0): ""})
    with pytest.raises(ValueError, match="a trial has no views or resources"):
        _ = catalog.create(ids["trial"], alice.id, labels={("view", 0): "x"})
    assert len(catalog.history(thread)) == 1


# The database holds a label to a position its edit's scorer has, written once, in the
# edit's transaction and by its writer.
def test_the_database_holds_labels_to_their_edit(conn: Connection) -> None:
    catalog, _, reg, ids, alice = stored_world(conn)
    bob = People(conn).add("bob", "Bob")
    scorer = resolve(reg.get, ids["scoring"], Scoring).scorer
    labelled = catalog.create(scorer, alice.id, labels=LABELS)
    conn.commit()
    insert = """
        INSERT INTO catalog.label (edit, part, position, value, by)
        VALUES (%s, %s, %s, 'x', %s)
        """
    with (
        pytest.raises(errors.RaiseException, match="no resource at position 1"),
        conn.transaction(),
    ):
        edit = catalog.edit(labelled.thread, scorer, alice.id)
        _ = conn.execute(insert, (edit.id, "resource", 1, alice.id))
    with (
        pytest.raises(errors.RaiseException, match="written with it, by its writer"),
        conn.transaction(),
    ):
        edit = catalog.edit(labelled.thread, scorer, alice.id)
        _ = conn.execute(insert, (edit.id, "view", 0, bob.id))
    with (
        pytest.raises(errors.RaiseException, match="written with it, by its writer"),
        conn.transaction(),
    ):
        _ = conn.execute(insert, (labelled.id, "view", 2, alice.id))
    with pytest.raises(errors.UniqueViolation), conn.transaction():
        edit = catalog.edit(labelled.thread, scorer, alice.id, labels=LABELS)
        _ = conn.execute(insert, (edit.id, "view", 0, alice.id))
    with (
        pytest.raises(errors.RaiseException, match="no view at position 0"),
        conn.transaction(),
    ):
        edit = catalog.create(ids["trial"], alice.id)
        _ = conn.execute(insert, (edit.id, "view", 0, alice.id))

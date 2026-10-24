import pytest
from fastapi.testclient import TestClient

from chatddx.api.test.helpers import thread
from chatddx.bench import Bench
from chatddx.bench.test.helpers import move_model
from chatddx.portal.test.helpers import said, shown, submitted
from chatddx.test.helpers import alices_bench
from chatddx.test.world import LINES, QWEN_ARTIFACT

__all__ = ["alices_bench"]


@pytest.mark.slow
def test_what_is_out_of_date_is_tagged_and_updated_one_by_one_or_all(
    signed: TestClient, bench: Bench
) -> None:
    theirs = thread(signed, "judge", "verdict", "archive")
    mine = bench.fork(theirs["id"], "my-verdict").edit.thread
    bench.conn.commit()
    configuration = thread(signed, "configuration", LINES)
    assert not configuration["outdated"]
    assert "Update all" not in said(shown(signed, "/library"))

    _ = move_model(bench, QWEN_ARTIFACT, revision="moved")
    bench.conn.commit()
    assert thread(signed, "configuration", LINES)["outdated"]
    library = said(shown(signed, "/library?kind=configuration"))
    assert "Out of date" in library and "Update all" in library
    lab = said(shown(signed, f"/lab/{configuration['id']}"))
    assert "Its model has new weights, so it can't run until it is updated." in lab
    scoring = said(shown(signed, f"/scoring/{mine}"))
    assert "Its model has new weights, so it can't judge until it is updated." in scoring
    assert "Only archive can update it: fork it, and update yours." in said(
        shown(signed, f"/threads/{theirs['id']}")
    )

    page = shown(signed, f"/threads/{mine}")
    form = submitted(page, f"/threads/{mine}/update")
    got = signed.post(
        f"/threads/{mine}/update", data={k: v[0] for k, v in form.items()}
    )
    assert (got.status_code, got.headers["location"]) == (303, f"/threads/{mine}")
    assert not thread(signed, "judge", "my-verdict")["outdated"]
    assert "Out of date" not in said(shown(signed, f"/threads/{mine}"))

    done = signed.post("/library/update")
    assert done.status_code == 200, done.text[:500]
    updated = said(done.text)
    assert LINES in updated and "my-verdict" not in updated
    assert "Not updated" not in updated
    assert not thread(signed, "configuration", LINES)["outdated"]
    assert "Update all" not in said(shown(signed, "/library"))

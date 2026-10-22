from pydantic import JsonValue

from chatddx.portal.changes import Change, changes


def test_what_a_version_changed_is_found_by_path() -> None:
    before: JsonValue = {
        "text": "a cold day",
        "settings": {"top_k": 20},
        "seeds": [1, 2],
        "old": 1,
    }
    after: JsonValue = {
        "text": "a warm day",
        "settings": {"top_k": 40},
        "seeds": [1, 2, 3],
        "new": 2,
    }
    assert changes(before, before) == []
    assert changes(before, after) == [
        Change(
            "/text",
            "changed",
            "a cold day",
            "a warm day",
            [("", "a "), ("-", "cold"), ("+", "warm"), ("", " day")],
        ),
        Change("/settings/top_k", "changed", 20, 40),
        Change("/seeds", "changed", [1, 2], [1, 2, 3]),
        Change("/new", "added", after=2),
        Change("/old", "removed", before=1),
    ]
    assert changes(["x", "y"], ["x", "z"]) == [
        Change("/1", "changed", "y", "z", [("-", "y"), ("+", "z")])
    ]

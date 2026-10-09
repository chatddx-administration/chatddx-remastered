from chatddx.repl.test.sample import FREE_TEXT, GPT_OSS, QWEN, Say


def line_of(written: str, start: str) -> str:
    return [line for line in written.splitlines() if line.strip().startswith(start)][-1]


def test_endpoints_are_listed_with_their_engines_and_clearance(say: Say):
    written = say("endpoints")

    assert line_of(written, QWEN).split() == [
        QWEN,
        QWEN,
        "Qwen/Qwen3-8B-AWQ",
        "http://127.0.0.1:12099/v1/",
        "sample",
    ]
    assert line_of(written, GPT_OSS).split()[2] == "openai/gpt-oss-20b"


def test_configurations_are_listed_with_their_parts_and_whose_they_are(say: Say):
    written = say("configurations")
    header = written.splitlines()[0].split()
    rows = [
        line.split()
        for line in written.splitlines()
        if line.strip().startswith(FREE_TEXT)
    ]

    assert header == [
        "configuration",
        "prompt",
        "output",
        "sampling",
        "toolset",
        "owner",
    ]
    assert rows == [
        [
            *FREE_TEXT.split(),
            "case",
            "free-text",
            "recommended",
            "(Qwen/Qwen3-8B-AWQ)",
            "—",
        ],
        [
            *FREE_TEXT.split(),
            "case",
            "free-text",
            "recommended",
            "(Qwen/Qwen3-8B-AWQ)",
            "—",
            "archive",
        ],
    ]
    assert "web" in line_of(written, "plan-web (Qwen")


def test_cases_are_listed_by_name_with_their_tags(say: Say):
    written = say("cases")

    assert "DutchFall10w  Dutchfall11w" in written
    assert "99 cases; tagged dutch-fall 30, edn 20, openxddx 49" in written

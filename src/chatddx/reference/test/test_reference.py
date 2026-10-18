import re
from pathlib import Path
from textwrap import dedent

import pytest

from chatddx import settings
from chatddx.reference import Index, Raises, page, regenerated, tagged, untagged


def written(tmp_path: Path, files: dict[str, str]) -> str:
    root = tmp_path / "src"
    for name, source in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(dedent(source))
    index = Index(root)
    return page(index, Raises(index), "proj.alpha")


def entry(page: str, heading: str) -> list[str]:
    lines = page.splitlines()
    start = lines.index(heading)
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("#")),
        len(lines),
    )
    return [line for line in lines[start + 1 : end] if line]


def applied(text: str) -> str:
    lines = text.splitlines()
    kept: list[str] = []
    i = 0
    while i < len(lines):
        if lines[i].startswith("```") and lines[i + 1].startswith("REFERENCE: "):
            end = lines.index(lines[i], i + 2)
            found = re.search(r"the (\d+) lines below|the line below", lines[i + 2])
            below = 0 if found is None else int(found.group(1) or 1)
            kept += lines[i + 4 : end] if lines[i + 3 : i + 4] == ["---"] else []
            i = end + 1 + below
            continue
        kept.append(lines[i])
        i += 1
    return "\n".join(kept) + "\n"


def test_a_reference_lists_the_public_names_alphabetically_whatever_their_case(
    tmp_path: Path,
) -> None:
    found = written(
        tmp_path,
        {
            "proj/alpha/__init__.py": "",
            "proj/alpha/things.py": """
                from json import dumps

                GAMMA = 1


                def beta() -> None: ...


                def _hidden() -> None: ...


                class Alpha: ...
            """,
        },
    )
    headings = [line for line in found.splitlines() if line.startswith("## ")]
    assert headings == ["## `class Alpha`", "## `beta() -> None`", "## `GAMMA = 1`"]
    assert entry(found, "## `beta() -> None`") == ["`src/proj/alpha/things.py:beta`"]
    assert "dumps" not in found


def test_a_signature_is_written_as_the_code_writes_it(tmp_path: Path) -> None:
    found = written(
        tmp_path,
        {
            "proj/alpha/signed.py": """
                def every[T](
                    a: int, /, b: str = "x", *more: int, c: bool = False, **rest: str
                ) -> list[T]: ...


                def keyed(a, *, b: int) -> None: ...
            """,
        },
    )
    assert (
        '## `every[T](a: int, /, b: str = "x", *more: int, c: bool = False, '
        + "**rest: str) -> list[T]`"
    ) in found
    assert "## `keyed(a, *, b: int) -> None`" in found


def test_a_function_a_class_binds_is_written_once_as_the_class_s_method(
    tmp_path: Path,
) -> None:
    found = written(
        tmp_path,
        {
            "proj/alpha/acting.py": """
                from .seen import Seen


                def act(seen: Seen, times: int) -> int:
                    if times < 0:
                        raise ValueError("a negative number of times")
                    return times
            """,
            "proj/alpha/seen.py": """
                class Seen: ...
            """,
            "proj/alpha/bench.py": """
                from .acting import act
                from .seen import Seen


                class Bench(Seen):
                    act = act
            """,
        },
    )
    assert "## `act(" not in found
    assert entry(found, "### `Bench.act(times: int) -> int`") == [
        "`src/proj/alpha/acting.py:act`",
        '- raises `ValueError("a negative number of times")`',
    ]


def test_a_raise_is_written_with_its_message_and_what_it_interpolates(
    tmp_path: Path,
) -> None:
    found = written(
        tmp_path,
        {
            "proj/alpha/finding.py": """
                NONE = "nothing to find"


                class Missing(LookupError): ...


                def find(name: str) -> None:
                    if not name:
                        raise ValueError(NONE)
                    if name == "all":
                        raise ValueError(name)
                    raise Missing(f"no {name!r} in " + "the store")
            """,
        },
    )
    assert entry(found, "## `find(name: str) -> None`")[1:] == [
        '- raises `ValueError("nothing to find")`',
        "- raises `ValueError(name)`",
        '- raises `Missing("no <name!r> in the store")`',
    ]


def test_what_a_function_catches_isn_t_said_to_be_raised_unless_raised_again(
    tmp_path: Path,
) -> None:
    found = written(
        tmp_path,
        {
            "proj/alpha/caught.py": """
                class Missing(LookupError): ...


                def inner() -> None:
                    raise Missing("gone")


                def held() -> None:
                    try:
                        inner()
                    except LookupError:
                        return None


                def passed() -> None:
                    try:
                        inner()
                    except LookupError:
                        print("passing it on")
                        raise


                def translated() -> None:
                    try:
                        inner()
                    except LookupError as e:
                        raise ValueError(str(e)) from None
            """,
        },
    )
    assert entry(found, "## `held() -> None`")[1:] == []
    assert entry(found, "## `passed() -> None`")[1:] == ["- raises what `inner` raises"]
    assert entry(found, "## `translated() -> None`")[1:] == [
        "- raises `ValueError(str(e))`"
    ]


def test_a_private_helper_s_raises_are_its_caller_s_and_a_public_callee_is_named(
    tmp_path: Path,
) -> None:
    found = written(
        tmp_path,
        {
            "proj/alpha/helped.py": """
                def _checked(times: int) -> None:
                    if times < 0:
                        raise ValueError("a negative number of times")


                def counted(times: int) -> None:
                    raise KeyError("uncounted")


                def done(times: int) -> None:
                    _checked(times)
                    counted(times)
            """,
        },
    )
    assert entry(found, "## `done(times: int) -> None`")[1:] == [
        '- raises `ValueError("a negative number of times")`',
        "- raises what `counted` raises",
    ]


def test_a_method_is_found_through_the_types_the_code_annotates(
    tmp_path: Path,
) -> None:
    found = written(
        tmp_path,
        {
            "proj/beta/__init__.py": """
                from .store import Store
            """,
            "proj/beta/store.py": """
                class Store:
                    def get(self, digest: str) -> str:
                        raise KeyError(digest)
            """,
            "proj/alpha/seen.py": """
                from proj.beta import Store


                class Seen:
                    def __init__(self, store: Store) -> None:
                        self.store: Store = store


                def fetched(seen: Seen) -> str:
                    return seen.store.get("a digest")


                def again(store: Store) -> str:
                    held = store
                    return held.get("a digest")
            """,
        },
    )
    assert entry(found, "## `fetched(seen: Seen) -> str`")[1:] == [
        "- raises what `beta.Store.get` raises"
    ]
    assert entry(found, "## `again(store: Store) -> str`")[1:] == [
        "- raises what `beta.Store.get` raises"
    ]
    assert entry(found, "## `class Seen`")[1:] == ["- `store: Store`"]
    assert "### `Seen(store: Store)`" in found


def test_a_validator_s_raise_reaches_the_caller_in_a_validation_error(
    tmp_path: Path,
) -> None:
    found = written(
        tmp_path,
        {
            "proj/alpha/model.py": """
                from pydantic import BaseModel, field_validator


                class Person(BaseModel):
                    login: str

                    @field_validator("login")
                    @classmethod
                    def _login(cls, login: str) -> str:
                        if not login:
                            raise ValueError("a login can't be empty")
                        return login


                def made(login: str) -> Person:
                    return Person(login=login)


                def tried(login: str) -> Person | None:
                    try:
                        return Person(login=login)
                    except ValueError:
                        return None
            """,
        },
    )
    assert entry(found, "## `class Person(BaseModel)`")[1:] == [
        "- `login: str`",
        '- raises `ValueError("a login can\'t be empty")` in a `ValidationError`',
    ]
    assert entry(found, "## `made(login: str) -> Person`")[1:] == [
        "- raises what `Person` raises"
    ]
    assert entry(found, "## `tried(login: str) -> Person | None`")[1:] == []


def test_a_first_reference_is_written_whole() -> None:
    assert tagged(None, "# a\n\nb\n") == "# a\n\nb\n"


def test_what_changed_is_tagged_above_the_lines_it_changes() -> None:
    assert tagged("a\nb\nc\nd\n", "a\nB\nc\ne\n") == dedent(
        """\
        a
        ```
        REFERENCE: REPLACE
        replace the line below with these
        ---
        B
        ```
        b
        c
        ```
        REFERENCE: REPLACE
        replace the line below with these
        ---
        e
        ```
        d
        """
    )
    assert tagged("a\nb\nc\n", "a\nc\nd\n") == dedent(
        """\
        a
        ```
        REFERENCE: REMOVE
        remove the line below
        ```
        b
        c
        ```
        REFERENCE: ADD
        add these lines here
        ---
        d
        ```
        """
    )


def test_tagging_again_gives_the_same_tags_and_applying_them_none() -> None:
    old, new = "a\nb\nc\nd\ne\n", "a\nx\ny\nc\ne\nf\n"
    once = tagged(old, new)
    assert tagged(once, new) == once
    assert untagged(once) == old.splitlines()
    assert applied(once) == new
    assert tagged(applied(once), new) == new


def test_a_tag_holding_a_fence_is_fenced_with_more_backticks() -> None:
    found = tagged("a\n", "a\n```\nb\n```\n")
    assert found.splitlines()[1] == "````"
    assert applied(found) == "a\n```\nb\n```\n"


def test_an_unclosed_tag_is_refused() -> None:
    with pytest.raises(ValueError, match="line 1: a REFERENCE tag isn't closed"):
        _ = untagged("```\nREFERENCE: ADD\nadd these lines here\n")


def test_each_reference_is_as_chatddx_reference_writes_it() -> None:
    for path, text in regenerated(settings.REFERENCED).items():
        assert path.read_text() == text, "chatddx reference"

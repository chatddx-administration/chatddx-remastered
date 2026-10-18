import re
from pathlib import Path
from textwrap import dedent

import pytest

from chatddx import settings
from chatddx.reference import Code, Raises, page, regenerated, tagged, untagged


def written(tmp_path: Path, files: dict[str, str]) -> str:
    for name, source in files.items():
        path = tmp_path / "src" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(dedent(source))
    code = Code(tmp_path / "src", "proj")
    return page(code, Raises(code), "proj.alpha", tmp_path)


def entry(page: str, heading: str) -> list[str]:
    lines = page.splitlines()
    start = lines.index(heading)
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
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
    assert headings == ["## Alpha", "## beta", "## GAMMA"]
    assert entry(found, "## beta") == [
        "`src/proj/alpha/things.py:beta`",
        "* ∟`None`",
    ]
    assert entry(found, "## GAMMA")[1:] == ["* `GAMMA = 1`"]
    assert "dumps" not in found


def test_a_signature_is_a_list_of_its_parameters_as_the_code_writes_them(
    tmp_path: Path,
) -> None:
    found = written(
        tmp_path,
        {
            "proj/alpha/signed.py": """
                import functools


                @functools.cache
                def every[T](
                    a: int, /, b: str = "x", *more: int, c: bool = False, **rest: str
                ) -> list[T]: ...


                def keyed(a, *, b=1): ...
            """,
        },
    )
    assert entry(found, "## every `@functools.cache` `[T]`")[1:] == [
        "* `a: int`",
        "* `/`",
        '* `b: str = "x"`',
        "* `*more: int`",
        "* `c: bool = False`",
        "* `**rest: str`",
        "* ∟`list[T]`",
    ]
    assert entry(found, "## keyed")[1:] == ["* `a`", "* `*`", "* `b=1`"]


def test_a_class_lists_its_fields_and_each_method_is_an_entry_of_its_own(
    tmp_path: Path,
) -> None:
    found = written(
        tmp_path,
        {
            "proj/alpha/held.py": """
                from dataclasses import dataclass


                class Store:
                    def __init__(self, path: str) -> None:
                        self.path: str = path
                        self._open: bool = False

                    @property
                    def name(self) -> str:
                        return self.path

                    @staticmethod
                    def default() -> "Store":
                        return Store("store")


                @dataclass(frozen=True)
                class Kept(LookupError):
                    digest: str
                    kind: str = "case"
            """,
        },
    )
    headings = [line for line in found.splitlines() if line.startswith("## ")]
    assert headings == [
        "## Kept `@dataclass(frozen=True)` `(LookupError)`",
        "## Store",
        "## Store.__init__",
        "## Store.default `@staticmethod`",
        "## Store.name `@property`",
    ]
    assert entry(found, "## Store")[1:] == ["* `path: str`"]
    assert entry(found, "## Store.__init__")[1:] == ["* `path: str`"]
    assert entry(found, "## Store.name `@property`")[1:] == ["* ∟`str`"]
    assert entry(found, "## Kept `@dataclass(frozen=True)` `(LookupError)`")[1:] == [
        "* `digest: str`",
        '* `kind: str = "case"`',
    ]


def test_a_function_a_class_binds_is_written_once_as_the_class_s_method(
    tmp_path: Path,
) -> None:
    found = written(
        tmp_path,
        {
            "proj/alpha/acting.py": """
                from .seen import Seen


                def act(seen: Seen, times: int) -> int:
                    seen._counted(times)
                    return times
            """,
            "proj/alpha/seen.py": """
                class Seen:
                    def _counted(self, times: int) -> None:
                        if times < 0:
                            raise ValueError("a negative number of times")
            """,
            "proj/alpha/bench.py": """
                from .acting import act
                from .seen import Seen


                class Bench(Seen):
                    act = act
            """,
        },
    )
    assert "## act" not in found
    assert entry(found, "## Bench.act") == [
        "`src/proj/alpha/acting.py:act`",
        "* `times: int`",
        "* ∟`int`",
        "Raises:",
        "1. `ValueError`: a negative number of times (through `Seen._counted`)",
    ]


def test_a_raise_is_said_with_its_message_as_the_code_writes_it(
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
                    if name == "none":
                        raise Missing
                    raise Missing(f"no {name!r} in " + "the store")
            """,
        },
    )
    assert entry(found, "## find")[4:] == [
        "1. `ValueError`: nothing to find",
        "2. `ValueError`: {name}",
        "3. `Missing`",
        "4. `Missing`: no {name!r} in the store",
    ]


def test_raises_are_in_the_order_the_code_reaches_them_helpers_included(
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
                    if times > 9:
                        raise OverflowError("too many times")
                    counted(times)
                    _checked(times - 1)
            """,
        },
    )
    assert entry(found, "## done")[4:] == [
        "1. `ValueError`: a negative number of times (through `_checked`)",
        "2. `OverflowError`: too many times",
    ]


def test_what_a_function_catches_isn_t_said_to_be_raised_unless_raised_again(
    tmp_path: Path,
) -> None:
    found = written(
        tmp_path,
        {
            "proj/alpha/caught.py": """
                REFUSALS = (KeyError, LookupError)


                class Missing(LookupError): ...


                def _inner() -> None:
                    raise Missing("gone")


                def held() -> None:
                    try:
                        _inner()
                    except REFUSALS:
                        return None


                def passed() -> None:
                    try:
                        _inner()
                    except LookupError:
                        print("passing it on")
                        raise


                def translated() -> None:
                    try:
                        _inner()
                    except LookupError as e:
                        raise ValueError(str(e)) from None
            """,
        },
    )
    assert entry(found, "## held")[1:] == ["* ∟`None`"]
    assert entry(found, "## passed")[1:] == [
        "* ∟`None`",
        "Raises:",
        "1. `Missing`: gone (through `_inner`)",
    ]
    assert entry(found, "## translated")[1:] == [
        "* ∟`None`",
        "Raises:",
        "1. `ValueError`: {str(e)}",
    ]


def test_a_validator_s_raise_is_said_of_its_class_in_a_validation_error(
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
            """,
        },
    )
    assert entry(found, "## Person `(BaseModel)`")[1:] == [
        "* `login: str`",
        "Raises:",
        "1. `ValueError`: a login can't be empty "
        + "(through `Person._login`, in a `ValidationError`)",
    ]


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

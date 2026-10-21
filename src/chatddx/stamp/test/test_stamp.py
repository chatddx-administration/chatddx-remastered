from pathlib import Path
from textwrap import dedent

import pytest

from chatddx import settings, stamp
from chatddx.stamp import Surface, surfaces
from chatddx.stamp.code import Code
from chatddx.stamp.index import index
from chatddx.stamp.markers import signed, stamped
from chatddx.stamp.page import page
from chatddx.stamp.trace import Trace


def sourced(tmp_path: Path, files: dict[str, str]) -> Path:
    for name, source in files.items():
        path = tmp_path / "src" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text(dedent(source))
    return tmp_path / "src"


def written(tmp_path: Path, files: dict[str, str]) -> str:
    code = Code(sourced(tmp_path, files), "proj")
    return page(code, Trace(code, "proj.base.Finding"), "proj.alpha", tmp_path)


def indexed(tmp_path: Path, files: dict[str, str]) -> str:
    return index(sourced(tmp_path, files), "proj.alpha", tmp_path)


def entry(page: str, heading: str) -> list[str]:
    lines = page.splitlines()
    start = lines.index(heading)
    end = next(
        (i for i in range(start + 1, len(lines)) if lines[i].startswith("## ")),
        len(lines),
    )
    return [line for line in lines[start + 1 : end] if line]


def applied(text: str) -> str:
    kept: list[str] = []
    dropping = False
    for line in text.splitlines():
        if line in ("<<<<<<< signed", "======="):
            dropping = line == "<<<<<<< signed"
        elif line != ">>>>>>> @stamp" and not dropping:
            kept.append(line)
    return "\n".join(kept) + "\n"


def test_a_surface_lists_the_public_names_alphabetically_whatever_their_case(
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
    assert headings == ["## `Alpha`", "## `beta`", "## `GAMMA`"]
    assert entry(found, "## `beta`") == [
        "`src/proj/alpha/things.py:beta`",
        "* ∟`None`",
    ]
    assert entry(found, "## `GAMMA`")[1:] == ["`GAMMA = 1`"]
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
    assert entry(found, "## `every` `@functools.cache` `[T]`")[1:] == [
        "* `a: int`",
        "* `/`",
        '* `b: str = "x"`',
        "* `*more: int`",
        "* `c: bool = False`",
        "* `**rest: str`",
        "* ∟`list[T]`",
    ]
    assert entry(found, "## `keyed`")[1:] == ["* `a`", "* `*`", "* `b=1`"]


def test_a_class_lists_its_fields_and_each_method_is_an_entry_of_its_own(
    tmp_path: Path,
) -> None:
    found = written(
        tmp_path,
        {
            "proj/alpha/held.py": """
                from dataclasses import dataclass, field


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
                    labels: dict[str, str] = field(
                        default_factory=dict
                    )


                KINDS: dict[str, str] = {
                    "case": "case",
                }
            """,
        },
    )
    headings = [line for line in found.splitlines() if line.startswith("## ")]
    assert headings == [
        "## `Kept` `@dataclass(frozen=True)` `(LookupError)`",
        "## `KINDS`",
        "## `Store`",
        "## `Store.__init__`",
        "## `Store.default` `@staticmethod`",
        "## `Store.name` `@property`",
    ]
    assert entry(found, "## `Store`")[1:] == ["* `path: str`"]
    assert entry(found, "## `Store.__init__`")[1:] == ["* `path: str`"]
    assert entry(found, "## `Store.name` `@property`")[1:] == ["* ∟`str`"]
    assert entry(found, "## `Kept` `@dataclass(frozen=True)` `(LookupError)`")[1:] == [
        "* `digest: str`",
        '* `kind: str = "case"`',
        "* `labels: dict[str, str] = field(…)`",
    ]
    assert entry(found, "## `KINDS`")[1:] == ["`KINDS: dict[str, str] = {…}`"]


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
    assert "## `act`" not in found
    assert entry(found, "## `Bench.act`") == [
        "`src/proj/alpha/acting.py:act`",
        "* `times: int`",
        "* ∟`int`",
        "Raises:",
        '1. `ValueError`: `"a negative number of times"` (through `Seen._counted`)',
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
    assert entry(found, "## `find`")[4:] == [
        '1. `ValueError`: `"nothing to find"`',
        "2. `ValueError`: `name`",
        "3. `Missing`",
        '4. `Missing`: `"no {name!r} in the store"`',
    ]


def test_an_argument_that_isn_t_text_is_said_as_written(tmp_path: Path) -> None:
    found = written(
        tmp_path,
        {
            "proj/alpha/problems.py": """
                class Problem(Exception):
                    def __init__(self, status: int, detail: str = "") -> None:
                        super().__init__(status, detail)


                def _refused(detail: str = "refused") -> Problem:
                    return Problem(403, detail)


                def checked(n: int) -> None:
                    if n < 0:
                        raise Problem(422, f"{n} is negative")
                    if n == 0:
                        raise Problem(status=404, detail="nothing")
                    raise _refused("too many")
            """,
        },
    )
    assert entry(found, "## `checked`")[4:] == [
        '1. `Problem`: `422, "{n} is negative"`',
        '2. `Problem`: `status=404, detail="nothing"`',
        '3. `Problem`: `"too many"` (through `_refused`)',
    ]


def test_code_holding_backticks_is_fenced_with_more_of_them(tmp_path: Path) -> None:
    found = written(
        tmp_path,
        {
            "proj/alpha/quoting.py": """
                def quoted() -> None:
                    raise ValueError("write ``x``, not `x`")
            """,
        },
    )
    assert entry(found, "## `quoted`")[2:] == [
        "Raises:",
        '1. `ValueError`: ``` "write ``x``, not `x`" ```',
    ]


def test_a_name_two_modules_define_is_headed_with_its_module(tmp_path: Path) -> None:
    found = written(
        tmp_path,
        {
            "proj/alpha/one.py": "log = 1\n",
            "proj/alpha/two.py": "log = 2\n",
        },
    )
    headings = [line for line in found.splitlines() if line.startswith("## ")]
    assert headings == ["## `one.log`", "## `two.log`"]


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
    assert "\nRaises:\n1. `ValueError`" in found
    assert entry(found, "## `done`")[4:] == [
        '1. `ValueError`: `"a negative number of times"` (through `_checked`)',
        '2. `OverflowError`: `"too many times"`',
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
    assert entry(found, "## `held`")[1:] == ["* ∟`None`"]
    assert entry(found, "## `passed`")[1:] == [
        "* ∟`None`",
        "Raises:",
        '1. `Missing`: `"gone"` (through `_inner`)',
    ]
    assert entry(found, "## `translated`")[1:] == [
        "* ∟`None`",
        "Raises:",
        "1. `ValueError`: `str(e)` (from `LookupError`)",
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
    assert entry(found, "## `Person` `(BaseModel)`")[1:] == [
        "* `login: str`",
        "Raises:",
        '1. `ValueError`: `"a login can\'t be empty"` '
        + "(through `Person._login`, in a `ValidationError`)",
    ]


def test_a_finding_is_listed_where_the_code_makes_it(tmp_path: Path) -> None:
    found = written(
        tmp_path,
        {
            "proj/base.py": """
                from dataclasses import dataclass


                @dataclass(frozen=True)
                class Finding:
                    code: str
                    message: str
                    level: str = "warning"
            """,
            "proj/alpha/linting.py": """
                from proj.base import Finding


                def _pair(n: int) -> list[Finding]:
                    if n % 2:
                        return [Finding(code="pair.odd", message=f"{n} is odd", level="info")]
                    return []


                def lint(n: int, code: str) -> list[Finding]:
                    found = [Finding(code="lint.started", message="linting")]
                    found += _pair(n)
                    try:
                        _ = int(code)
                    except ValueError as e:
                        found.append(Finding(code=code, message=str(e)))
                    return found
            """,
        },
    )
    assert "\nFinds:\n1. `lint.started`" in found
    assert entry(found, "## `lint`")[4:] == [
        "Finds:",
        '1. `lint.started`: `"linting"`',
        '2. `pair.odd`: `"{n} is odd"` (`info`, through `_pair`)',
        "3. `{code}`: `str(e)` (from `ValueError`)",
    ]


def test_a_comment_is_indexed_under_the_name_it_is_in_or_right_above(
    tmp_path: Path,
) -> None:
    found = indexed(
        tmp_path,
        {
            "proj/alpha/__init__.py": "# Scope: the package.\n",
            "proj/alpha/held.py": """
                import json  # the standard library's

                # Policy: one, ever.
                LIMIT = 1


                class Store:
                    # Policy: the store's own.
                    kind = "store"

                    @property
                    # Compromise: under the decorator.
                    def name(self) -> str:
                        # Policy: a name is its kind,
                        # and stays it.
                        return self.kind  # as it is

                    def opened(self) -> None:
                        def inner() -> None:
                            # Scope: within.
                            pass

                        # Scope: the method's.
                        inner()


                # Scope: a section.

                def after() -> None: ...
            """,
            "proj/alpha/test/test_held.py": """
                # Policy: a test's are indexed too.
                def test_held() -> None:
                    _ = "# not a comment"
            """,
        },
    )
    assert (
        found.splitlines()[3:]
        == dedent(
            """
        ## `src/proj/alpha/__init__.py`

        ```
        # Scope: the package.
        ```

        ## `src/proj/alpha/held.py`

        ```
        # the standard library's
        ```

        ```
        # Scope: a section.
        ```

        ## `src/proj/alpha/held.py:LIMIT`

        ```
        # Policy: one, ever.
        ```

        ## `src/proj/alpha/held.py:Store.kind`

        ```
        # Policy: the store's own.
        ```

        ## `src/proj/alpha/held.py:Store.name`

        ```
        # Compromise: under the decorator.
        ```

        ```
        # Policy: a name is its kind,
        # and stays it.
        ```

        ```
        # as it is
        ```

        ## `src/proj/alpha/held.py:Store.opened`

        ```
        # Scope: the method's.
        ```

        ## `src/proj/alpha/held.py:Store.opened.inner`

        ```
        # Scope: within.
        ```

        ## `src/proj/alpha/test/test_held.py:test_held`

        ```
        # Policy: a test's are indexed too.
        ```
        """
        ).splitlines()
    )


def test_sql_and_toml_comments_are_read_past_their_strings(tmp_path: Path) -> None:
    found = indexed(
        tmp_path,
        {
            "proj/alpha/setup.sql": """
                -- Policy: one row,
                -- ever.
                CREATE TABLE "a--b" (c text DEFAULT 'it''s -- text'); -- trailing
                /* Scope: a block
                   of two lines. */
            """,
            "proj/alpha/models.toml": """
                # Policy: shipped.
                a = "# text"  # trailing
                b = 'C#'
                c = \"\"\"
                # still text
                \"\"\"
            """,
            "proj/alpha/notes.txt": "# not read\n",
        },
    )
    assert entry(found, "## `src/proj/alpha/models.toml`") == [
        "```",
        "# Policy: shipped.",
        "```",
        "```",
        "# trailing",
        "```",
    ]
    assert entry(found, "## `src/proj/alpha/setup.sql`") == [
        "```",
        "-- Policy: one row,",
        "-- ever.",
        "```",
        "```",
        "-- trailing",
        "```",
        "```",
        "/* Scope: a block",
        "   of two lines. */",
        "```",
    ]
    assert "notes.txt" not in found


def test_a_comment_holding_backticks_is_fenced_with_more_of_them(
    tmp_path: Path,
) -> None:
    found = indexed(tmp_path, {"proj/alpha/held.py": "# a ``` fence\n"})
    assert entry(found, "## `src/proj/alpha/held.py`") == [
        "````",
        "# a ``` fence",
        "````",
    ]


def test_a_first_surface_is_written_whole() -> None:
    assert stamped(None, "# a\n\n## b\n") == "# a\n\n## b\n"


def test_what_changed_is_stamped_in_its_place_as_a_git_conflict() -> None:
    assert stamped("## e\na\nb\nc\n", "## e\nA\nb\nd\n") == dedent(
        """\
        ## e
        <<<<<<< signed
        a
        =======
        A
        >>>>>>> @stamp
        b
        <<<<<<< signed
        c
        =======
        d
        >>>>>>> @stamp
        """
    )
    assert stamped("## e\na\nb\n", "## e\nb\nc\n") == dedent(
        """\
        ## e
        <<<<<<< signed
        a
        =======
        >>>>>>> @stamp
        b
        <<<<<<< signed
        =======
        c
        >>>>>>> @stamp
        """
    )


def test_what_comes_before_the_first_entry_is_written_as_it_is_and_not_stamped() -> (
    None
):
    old = "# a\n\nread it so\n\n## e\nb\n"
    assert stamped(old, "# a\n\nread it otherwise\n\n## e\nb\n") == (
        "# a\n\nread it otherwise\n\n## e\nb\n"
    )


def test_stamping_again_gives_the_same_stamps_and_applying_them_none() -> None:
    old, new = "## e\na\nb\nc\nd\ne\n", "## e\na\nx\ny\nc\ne\nf\n"
    once = stamped(old, new)
    assert stamped(once, new) == once
    assert signed(once) == old.splitlines()
    assert applied(once) == new
    assert stamped(applied(once), new) == new


def test_a_line_that_is_a_divider_outside_a_stamp_is_text() -> None:
    assert signed("## e\n=======\n") == ["## e", "======="]


def test_a_conflict_that_isn_t_a_stamp_is_refused() -> None:
    with pytest.raises(ValueError, match="line 2: a conflict marker that isn't"):
        _ = signed("## e\n<<<<<<< HEAD\na\n=======\nb\n>>>>>>> main\n")


def test_an_unclosed_stamp_is_refused() -> None:
    with pytest.raises(ValueError, match="line 1: a stamp isn't closed"):
        _ = signed("<<<<<<< signed\na\n=======\nb\n")


def test_a_surface_counts_the_stamps_it_holds_and_those_a_write_would_add() -> None:
    once = stamped("## e\na\nb\nc\n", "## e\nA\nb\nc\n")
    twice = stamped(once, "## e\nA\nb\nC\n")
    assert Surface(Path("s.md"), once, twice).pending == 1
    assert Surface(Path("s.md"), once, twice).new == 1
    assert Surface(Path("s.md"), twice, twice).new == 0
    assert Surface(Path("s.md"), None, "## e\na\n").new == 0


def faked(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *found: tuple[str, str | None, str]
) -> None:
    docs = tmp_path / "docs" / "surfaces"
    docs.mkdir(parents=True)
    held = [
        Surface(docs / f"{name}.md", current, written)
        for name, current, written in found
    ]
    for s in held:
        if s.current is not None:
            _ = s.path.write_text(s.current)
    monkeypatch.setattr(settings, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(settings, "STAMPED", tuple(name for name, _, _ in found))
    monkeypatch.setattr(stamp, "DOCS", docs)
    monkeypatch.setattr(stamp, "COMMENTS", tmp_path / "docs" / "comments")

    def listed(_: object) -> list[Surface]:
        return held

    monkeypatch.setattr(stamp, "surfaces", listed)


PENDING = stamped("## e\na\n", "## e\nb\n")


def test_check_flags_stamps_pending_and_fails_on_a_surface_behind_the_code(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    faked(monkeypatch, tmp_path, ("a", "## e\n", "## e\n"))
    stamp.check([], baseline=False)
    assert capsys.readouterr() == ("ok\n", "")

    faked(monkeypatch, tmp_path / "pending", ("a", PENDING, PENDING))
    stamp.check([], baseline=False)
    assert capsys.readouterr() == ("", "flag: docs/surfaces/a.md: 1 stamp pending\n")

    faked(monkeypatch, tmp_path / "behind", ("a", PENDING, "## e\nc\n"))
    with pytest.raises(
        SystemExit, match="^stamp: docs/surfaces/a.md behind the code: "
    ):
        stamp.check([], baseline=False)


def test_check_at_the_baseline_fails_on_stamps_pending_and_on_new_ones(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    faked(
        monkeypatch,
        tmp_path,
        ("a", PENDING, PENDING),
        ("b", "## e\na\n", "## e\nb\n"),
        ("c", None, "## e\n"),
        ("d", "## e\n", "## e\n"),
    )
    with pytest.raises(SystemExit) as e:
        stamp.check([], baseline=True)
    assert e.value.code == 1
    assert capsys.readouterr().err.splitlines() == [
        "flag: docs/surfaces/a.md: 1 stamp pending at the baseline: a human stamps "
        + "them before work proceeds",
        "flag: docs/surfaces/b.md: behind the code at the baseline: the code changed "
        + "without chatddx stamp write; investigate before work proceeds",
        "flag: docs/surfaces/c.md: not written at the baseline: the code changed "
        + "without chatddx stamp write; investigate before work proceeds",
    ]


def test_check_flags_a_page_no_package_writes_and_a_broken_stamp(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    faked(monkeypatch, tmp_path, ("a", "## e\n", "## e\n"))
    _ = (tmp_path / "docs" / "surfaces" / "gone.md").write_text("## e\n")
    (tmp_path / "docs" / "comments").mkdir()
    _ = (tmp_path / "docs" / "comments" / "gone.md").write_text("## e\n")
    with pytest.raises(SystemExit) as e:
        stamp.check([], baseline=False)
    assert e.value.code == 1
    assert capsys.readouterr().err.splitlines() == [
        "flag: docs/comments/gone.md: no package of settings.STAMPED writes it",
        "flag: docs/surfaces/gone.md: no package of settings.STAMPED writes it",
    ]

    def broken(_: object) -> list[Surface]:
        raise ValueError("docs/surfaces/a.md: line 2: a stamp isn't closed")

    monkeypatch.setattr(stamp, "surfaces", broken)
    with pytest.raises(SystemExit):
        stamp.check(["a"], baseline=False)
    assert "flag: docs/surfaces/a.md: line 2: a stamp isn't closed" in (
        capsys.readouterr().err
    )


def test_write_says_how_many_stamps_it_wrote_to_each_surface(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    faked(
        monkeypatch,
        tmp_path,
        ("a", "## e\na\n", PENDING),
        ("b", None, "## e\n"),
        ("c", "# old\n\n## e\n", "# new\n\n## e\n"),
        ("d", "## e\n", "## e\n"),
    )
    stamp.write([])
    assert capsys.readouterr().out.splitlines() == [
        "docs/surfaces/a.md: 1 stamp",
        "docs/surfaces/b.md: new",
        "docs/surfaces/c.md: 0 stamps",
    ]
    assert (tmp_path / "docs" / "surfaces" / "b.md").read_text() == "## e\n"

    faked(monkeypatch, tmp_path / "again", ("a", "## e\n", "## e\n"))
    stamp.write([])
    assert capsys.readouterr().out == "nothing to write\n"


@pytest.mark.slow
def test_each_surface_is_as_chatddx_stamp_writes_it() -> None:
    for s in surfaces(settings.STAMPED):
        assert not s.behind, "chatddx stamp write"

import re
import shutil
import subprocess
from pathlib import Path

from chatddx.markers import applied_lines
from chatddx_dev import project
from chatddx_dev.stamp import documents

__all__ = ["check"]

_DOC = re.compile(r"(?<![\w/.-])((?:docs|agents)/[\w./-]+\.md|AGENTS\.md|README\.md)")
_CODE = re.compile(r"(?<![\w/.-])(src/chatddx/[\w./-]+(?::[A-Za-z_][\w.]*)?)")
_SECTIONS = re.compile(r'^`?(?:,\s*|\s*\(\s*)((?:"[^"]+"(?:\s*(?:,|and|or)\s*)?)+)')
_SEE = re.compile(r'\(see ((?:"[^"]+"(?:\s*(?:,|and|or)\s*)?)+)')
_TERM = re.compile(r"(?:(?<=[\s(`])|^):(?=[A-Z])")
_COMMIT = re.compile(
    r"(?<![\w/.:-])(?=[0-9a-f]*[a-f])(?=[0-9a-f]*\d)[0-9a-f]{7,40}(?![\w-])"
)
_MAIN = "origin/main"
# Accommodating for references the docs make on purpose to what isn't here: another
# repository's files, a repository at a commit, an earlier commit's code, and files
# planned or gone.
_ELSEWHERE_BEFORE = re.compile(
    r"(?:o11n's|future|former|was|for a|git show \w+:)\s*`?$"
)
_ELSEWHERE_AFTER = re.compile(r"^`?\s+(?:at [0-9a-f]{7,}|in [\w-]+/[\w-]+)")


def _prose(path: Path) -> list[tuple[int, str]]:
    try:
        now = applied_lines(path.read_text())
    except ValueError as e:
        raise ValueError(f"{path.relative_to(project.PROJECT_ROOT)}: {e}") from None
    lines: list[tuple[int, str]] = []
    fence = False
    for n, line in now:
        if line.lstrip().startswith("```"):
            fence = not fence
        elif not fence:
            lines.append((n, line))
    return lines


class _Doc:
    text: str
    headings: set[str]
    items: set[str]
    entries: set[str]

    def __init__(self, path: Path) -> None:
        text = path.read_text()
        lines = [line for _, line in _prose(path)]
        self.text = " ".join(text.split())
        self.headings = {
            m.group(1) for line in lines if (m := re.match(r"^#+\s+(.*?)\s*$", line))
        }
        self.items = {i.rstrip(".:,;") for i in re.findall(r"\*\*(.+?)\*\*", self.text)}
        self.entries = {
            m.group(1) for line in lines if (m := re.match(r"^:(.+?) — ", line))
        }

    def holds(self, section: str) -> bool:
        if section[0].islower():
            return section in self.text
        return section in self.headings or section.rstrip(".:,;") in self.items


def _code_problem(root: Path, ref: str) -> str | None:
    path, _, name = ref.rstrip(".").partition(":")
    p = root / path
    if not p.exists():
        return "no such path"
    if not name or p.suffix != ".py":
        return None
    src = p.read_text()
    first, _, attr = name.partition(".")
    if not re.search(
        rf"^(?:(?:async )?def|class|type)\s+{re.escape(first)}\b|^{re.escape(first)}\s*[:=]",
        src,
        re.MULTILINE,
    ):
        return f"no {first}"
    if attr and not re.search(
        rf"^\s+(?:(?:async )?def\s+)?{re.escape(attr.split('.')[0])}\b\s*[:=(]",
        src,
        re.MULTILINE,
    ):
        return f"no {first}.{attr}"
    return None


# Accommodating for a checkout without git or main, such as nix's, where commits go
# unchecked, and a shallow one, which holds main only so far back: a commit it doesn't
# hold, or one older than the oldest of main it holds, is taken to be on main.
def _off_main(root: Path, shas: set[str]) -> dict[str, str]:
    if shutil.which("git") is None:
        return {}

    def git(*args: str) -> str | None:
        done = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
        )
        return done.stdout.strip() if done.returncode == 0 else None

    if git("rev-parse", "--verify", "--quiet", _MAIN) is None:
        return {}
    shallow = git("rev-parse", "--is-shallow-repository") == "true"
    held = min(
        map(int, (git("log", "--format=%ct", "--max-parents=0", _MAIN) or "0").split())
    )
    problems: dict[str, str] = {}
    for sha in shas:
        full = git("rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}")
        if full is None:
            if not shallow:
                problems[sha] = "no such commit"
        elif git("merge-base", "--is-ancestor", full, _MAIN) is None and not (
            shallow and int(git("show", "-s", "--format=%ct", full) or 0) < held
        ):
            problems[sha] = f"not on {_MAIN}"
    return problems


def check() -> list[str]:
    root = project.PROJECT_ROOT
    docs: dict[Path, _Doc] = {}

    def doc(path: Path) -> _Doc:
        if path not in docs:
            docs[path] = _Doc(path)
        return docs[path]

    glossary = doc(root / "docs/glossary.md").entries
    found: list[str] = []
    commits: dict[str, list[str]] = {}
    for path in documents():
        rel = path.relative_to(root)
        lines = _prose(path)
        for i, (n, line) in enumerate(lines):
            here = f"{rel}:{n}"
            following = (
                line + " " + (lines[i + 1][1].strip() if i + 1 < len(lines) else "")
            )
            previous = lines[i - 1][1] if i else ""
            for m in _DOC.finditer(line):
                target = m.group(1)
                before, after = previous + " " + line[: m.start()], following[m.end() :]
                if (
                    "<" in target
                    or _ELSEWHERE_BEFORE.search(before)
                    or _ELSEWHERE_AFTER.match(after)
                ):
                    continue
                if not (root / target).is_file():
                    found.append(f"{here}: file: {target}")
                    continue
                if listed := _SECTIONS.match(after):
                    for section in re.findall(r'"([^"]+)"', listed.group(1)):
                        section = " ".join(section.split())
                        if not doc(root / target).holds(section):
                            found.append(f'{here}: section: {target} "{section}"')
            for m in _SEE.finditer(following[: len(line) + 40]):
                for section in re.findall(r'"([^"]+)"', m.group(1)):
                    section = " ".join(section.split())
                    if m.start() < len(line) and not doc(path).holds(section):
                        found.append(f'{here}: section: "{section}"')
            for m in _CODE.finditer(line):
                ref = m.group(1)
                if _ELSEWHERE_BEFORE.search(line[: m.start()]):
                    continue
                if problem := _code_problem(root, ref):
                    found.append(f"{here}: code: {ref}: {problem}")
            for m in _COMMIT.finditer(line):
                commits.setdefault(m.group(), []).append(here)
            if line.startswith(":"):
                continue
            for m in _TERM.finditer(line):
                rest = line[m.end() :]
                if not any(
                    re.match(re.escape(t) + r"(?![\w])", rest) for t in glossary
                ):
                    found.append(f"{here}: term: :{rest.split()[0]}")
    for sha, problem in _off_main(root, set(commits)).items():
        found += [f"{here}: commit: {sha}: {problem}" for here in commits[sha]]
    return found

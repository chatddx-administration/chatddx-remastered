import argparse
import re
import sys
from pathlib import Path

DOC = re.compile(r"(?<![\w/.-])((?:docs|agents)/[\w./-]+\.md|AGENTS\.md|README\.md)")
CODE = re.compile(r"(?<![\w/.-])(src/chatddx/[\w./-]+(?::[A-Za-z_][\w.]*)?)")
SECTIONS = re.compile(r'^`?(?:,\s*|\s*\(\s*)((?:"[^"]+"(?:\s*(?:,|and|or)\s*)?)+)')
SEE = re.compile(r'\(see ((?:"[^"]+"(?:\s*(?:,|and|or)\s*)?)+)')
TERM = re.compile(r"(?:(?<=[\s(`])|^):(?=[A-Z])")
# Accommodating for references the docs make on purpose to what isn't here: another repository's files, a
# repository at a commit, an earlier commit's code, and files planned or gone.
ELSEWHERE_BEFORE = re.compile(r"(?:o11n's|future|former|was|for a|git show \w+:)\s*`?$")
ELSEWHERE_AFTER = re.compile(r"^`?\s+(?:at [0-9a-f]{7,}|in [\w-]+/[\w-]+)")
# Accommodating for AGENTS.md's example of a code reference, and the objects layer that
# docs/purist-object-layer.md imagines.
IGNORED = {
    "src/chatddx/file.py:Class.prop",
    "src/chatddx/objects/",
    "docs/objects.md",
    "docs/objects-api.md",
}


def sources(root: Path) -> list[Path]:
    docs = [
        p
        for p in (root / "docs").rglob("*.md")
        if not {"comments", "surfaces"} & set(p.relative_to(root).parts)
    ]
    return sorted(
        [*docs, *(root / "agents").glob("*.md"), root / "AGENTS.md", root / "README.md"]
    )


def prose(path: Path) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    fence = False
    for n, line in enumerate(path.read_text().splitlines(), 1):
        if line.lstrip().startswith("```"):
            fence = not fence
        elif not fence:
            lines.append((n, line))
    return lines


class Doc:
    text: str
    headings: set[str]
    items: set[str]
    entries: set[str]

    def __init__(self, path: Path) -> None:
        text = path.read_text()
        lines = [line for _, line in prose(path)]
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


def code_problem(root: Path, ref: str) -> str | None:
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


def check(root: Path) -> list[str]:
    docs: dict[Path, Doc] = {}

    def doc(path: Path) -> Doc:
        if path not in docs:
            docs[path] = Doc(path)
        return docs[path]

    glossary = doc(root / "docs/glossary.md").entries
    found: list[str] = []
    for path in sources(root):
        rel = path.relative_to(root)
        lines = prose(path)
        for i, (n, line) in enumerate(lines):
            here = f"{rel}:{n}"
            following = (
                line + " " + (lines[i + 1][1].strip() if i + 1 < len(lines) else "")
            )
            previous = lines[i - 1][1] if i else ""
            for m in DOC.finditer(line):
                target = m.group(1)
                before, after = previous + " " + line[: m.start()], following[m.end() :]
                if (
                    "<" in target
                    or target in IGNORED
                    or ELSEWHERE_BEFORE.search(before)
                    or ELSEWHERE_AFTER.match(after)
                ):
                    continue
                if not (root / target).is_file():
                    found.append(f"{here}: file: {target}")
                    continue
                if listed := SECTIONS.match(after):
                    for section in re.findall(r'"([^"]+)"', listed.group(1)):
                        section = " ".join(section.split())
                        if not doc(root / target).holds(section):
                            found.append(f'{here}: section: {target} "{section}"')
            for m in SEE.finditer(following[: len(line) + 40]):
                for section in re.findall(r'"([^"]+)"', m.group(1)):
                    section = " ".join(section.split())
                    if m.start() < len(line) and not doc(path).holds(section):
                        found.append(f'{here}: section: "{section}"')
            for m in CODE.finditer(line):
                ref = m.group(1)
                if ref in IGNORED or ELSEWHERE_BEFORE.search(line[: m.start()]):
                    continue
                if problem := code_problem(root, ref):
                    found.append(f"{here}: code: {ref}: {problem}")
            if line.startswith(":"):
                continue
            for m in TERM.finditer(line):
                rest = line[m.end() :]
                if not any(
                    re.match(re.escape(t) + r"(?![\w])", rest) for t in glossary
                ):
                    found.append(f"{here}: term: :{rest.split()[0]}")
    return found


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Check what the docs and agents/ refer to: files, their sections, code and the glossary's terms."
    )
    _ = parser.add_argument("root", nargs="?", default=".", type=Path)
    found = check(parser.parse_args().root)
    if found:
        print("\n".join(found))
        sys.exit(1)


if __name__ == "__main__":
    main()

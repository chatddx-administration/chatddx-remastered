from chatddx.catalog import Subject, families, read
from chatddx.factors.base import Fingerprint
from chatddx.identity import Person
from chatddx.inventory import DirectorySource
from chatddx.store.catalog import Catalog, Rows
from chatddx.store.store import Connection


def _count(n: int, one: str, many: str) -> str:
    return f"{n} {one if n == 1 else many}"


def repair(
    conn: Connection, source: DirectorySource, archive: Person, dry: bool = False
) -> list[str]:
    lines: list[str] = []
    at = f"at source {source.name!r}"
    with conn.transaction():
        catalog, rows = Catalog(conn), Rows(conn)
        listing = {c.vignette.id: c.vignette.fingerprint for c in source.cases()}
        survey = families.survey(rows, source.name, listing)
        moves: list[tuple[int, str, str | None, Fingerprint | None, str]] = [
            (family, old, new, None, f"renamed to {new}")
            for family, old, new in survey.renamed
        ]
        moves += [
            (family, id, None, fingerprint, "changed")
            for family, id, fingerprint in survey.changed
        ]
        known = read.abouts(rows, [Subject(family=m[0]) for m in moves])
        for family, id, new, fingerprint, what in sorted(moves, key=lambda m: m[1]):
            if known[Subject(family=family)].owner != archive.id:
                lines.append(
                    f"[repair case] {id}: {what} {at}, but family {family} isn't the "
                    + "archive's"
                )
                continue
            if dry:
                lines.append(
                    f"[repair case] {id}: {what} {at}; family {family} would move"
                )
                continue
            done = catalog.repair(family, archive.id, id=new, fingerprint=fingerprint)
            moved = (
                _count(len(done.cases), "case", "cases"),
                _count(len(done.appendices), "appendix", "appendices"),
                _count(len(done.moves), "thread", "threads"),
            )
            lines.append(
                f"[repair case] {id}: {what} {at}; family {family} moved, with "
                + f"{moved[0]}, {moved[1]} and {moved[2]}"
            )
    return lines or [f"[repair] nothing to repair {at}"]

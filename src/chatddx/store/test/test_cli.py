import psycopg
import pytest

from chatddx import settings
from chatddx.cli import main
from chatddx.identity import Role
from chatddx.store import People


@pytest.mark.slow
def test_migrate_command(
    empty_db: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("DB_NAME", empty_db)
    main(["migrate", "--tier", "1", "--dry-run"])
    main(["migrate", "--tier", "1"])
    main(["migrate", "--tier", "1"])
    main(["migrate"])
    assert capsys.readouterr().out.splitlines() == [
        "would apply 0001-t0-factor",
        "would apply 0002-t1-factor",
        "would apply 0004-t0-ledger",
        "would apply 0005-t1-ledger",
        "would apply 0007-t0-identity",
        "would apply 0008-t1-identity",
        "would apply 0010-t0-catalog",
        "would apply 0011-t1-catalog",
        "would apply 0013-t0-catalog-binding-content",
        "would apply 0014-t0-source",
        "would apply 0015-t1-source",
        "would apply 0017-t0-catalog-label-edit",
        "would apply 0019-t0-worker",
        "would apply 0020-t1-worker",
        "would apply 0022-t0-ledger-seq",
        "would apply 0023-t1-ledger-seq",
        "would apply 0024-t0-worker-scored",
        "applied 0001-t0-factor",
        "applied 0002-t1-factor",
        "applied 0004-t0-ledger",
        "applied 0005-t1-ledger",
        "applied 0007-t0-identity",
        "applied 0008-t1-identity",
        "applied 0010-t0-catalog",
        "applied 0011-t1-catalog",
        "applied 0013-t0-catalog-binding-content",
        "applied 0014-t0-source",
        "applied 0015-t1-source",
        "applied 0017-t0-catalog-label-edit",
        "applied 0019-t0-worker",
        "applied 0020-t1-worker",
        "applied 0022-t0-ledger-seq",
        "applied 0023-t1-ledger-seq",
        "applied 0024-t0-worker-scored",
        "nothing to apply up to tier 1",
        "applied 0003-t2-factor",
        "applied 0006-t2-ledger",
        "applied 0009-t2-identity",
        "applied 0012-t2-catalog",
        "applied 0016-t2-source",
        "applied 0018-t2-catalog-label-edit",
        "applied 0021-t2-worker",
        "applied 0025-t2-worker-scored",
        "applied 0026-t2-catalog-run-variation",
    ]
    with pytest.raises(SystemExit):
        main(["migrate", "--tier", "3"])


def test_person_commands(
    db: str, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("DB_NAME", db)
    main(["person", "add", "alice", "Alice", "--role", "admin", "--role", "ops"])
    answers = iter(["secret", "secret", "secret", "typo", ""])

    def getpass(_prompt: str) -> str:
        return next(answers)

    monkeypatch.setattr("getpass.getpass", getpass)
    main(["person", "password", "alice"])
    with pytest.raises(SystemExit, match="don't match"):
        main(["person", "password", "alice"])
    with pytest.raises(SystemExit, match="can't be empty"):
        main(["person", "password", "alice"])
    assert capsys.readouterr().out.splitlines() == [
        "added alice (id 1)",
        "password set for alice",
    ]
    with psycopg.connect(settings.database(), dbname=db) as conn:
        person = People(conn).authenticate("alice", "secret")
    assert person is not None and person.roles == {Role.ADMIN, Role.OPS}

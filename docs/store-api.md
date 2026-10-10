# Store API

Reference for the `chatddx.store` package, its migrations, `public.migration` and the `identity` database schema, as
of e9bdca7. It was written from `src/chatddx/store/*` (`migrations/` and `setup.sql` included), `docs/store.md` and
`docs/migrations.md`. What the store is and why it is shaped this way is in `docs/store.md`; this file says what each
name accepts, returns and raises.

The other schemas are documented with the packages whose rows they hold: `factor` in `docs/factors-api.md`, `ledger`
in `docs/ledger-api.md` and `catalog` in `docs/catalog-api.md`. `catalog.py:Catalog` is documented in
`docs/catalog-api.md`, "The store's Catalog"; only its `Rows` is described here. Types the store passes through
(`Registry`, `Component`, `Compilation`, records, `Run`, `Score`, `Person`, `Role`, `Edit`, `About`, …) are in those
files and in `docs/identity.md`.

Paths are relative to `src/chatddx/store/` unless they start with `src/`, `docs/` or `agents/`.

## Contents
- [Package](#package)
- [Conventions](#conventions)
- [store.py](#storepy): `Store`, components and ledger records
- [people.py](#peoplepy): `People`, passwords and sessions
- [catalog.py](#catalogpy): `Rows`
- [migrate.py](#migratepy): migrations and tiers
- [Roles and connections](#roles-and-connections)
- [Database: `public.migration`](#database-publicmigration)
- [Database: schema `identity`](#database-schema-identity)
- [Migrations](#migrations)
- [Tests](#tests)
- [Known gaps](#known-gaps)
- [Beyond docs/store.md](#beyond-docsstoremd)

## Package

`chatddx.store` re-exports `TOP_TIER`, `Catalog`, `People`, `Store` and `migrate`. `Connection` (in
`store.py`), `Rows`, `pending`, `migrations`, `Migration` and `MIGRATIONS` are imported by path.

| Module | Builds on |
| --- | --- |
| `store.py` | `chatddx.factors.{base,bundle,request}`, `chatddx.ledger` |
| `migrate.py` | psycopg only |
| `people.py` | `store.py`, `chatddx.core.settings`, `chatddx.identity` |
| `catalog.py` | `store.py`, `chatddx.catalog`, `chatddx.factors.{base,cases,request,scoring}` |

The package holds chatddx's SQL. It uses psycopg 3, synchronously, and no ORM.

## Conventions

**Connections.** `Connection` is `psycopg.Connection[TupleRow]`. Every class takes one and keeps nothing else between
calls. A method that writes several rows does so inside `conn.transaction()`: `Store.add`, `Store.append`,
`People.update`, `Catalog.create`, `Catalog.adopt`, `Catalog.repair`, and each migration. Other methods run single
statements and commit nothing themselves. On an autocommit connection each statement commits as it runs. On one that
isn't, the first statement opens a transaction that only the caller commits, and `conn.transaction()` inside it is a
savepoint.

**Canonical text.** Components are read back from `factor.component.canonical` and records from `payload`, never
from `doc`; `doc`, the `jsonb` copy, is only queried (`Rows.bound_to`, `Rows.expectations`).

**Order.** Listings of runs and scores are newest first, by the started row's `at`. Other listings are in the order
each entry says; a SQL read without `ORDER BY` (the items and canary calls of `Store.run` and `Store.score`) comes
in whatever order Postgres returns.

**Errors.**

| Exception | When |
| --- | --- |
| `LookupError` | A run, score or person that isn't stored; `Catalog`'s lookups (`docs/catalog-api.md`). |
| `chatddx.factors.base.StructuralError` (a `ValueError`) | A digest that isn't stored (`Store.get`, `Store.load`, and `resolve` through them); stored bytes that don't match their digest or can't be read by this version; a log whose started row isn't stored; `Store.add` of a closure that doesn't check (`Registry.closure`, `Registry.check`). |
| `pydantic.ValidationError` | A record that doesn't parse, or a log that breaks its rules (`Run`, `Score`); `People.add` with a login that isn't `chatddx.identity.LOGIN`. |
| `TypeError` | `Store.append` of a record type that has no table. |
| `ValueError` | `People` reading back a role that isn't a `Role`, possible below tier 2. |
| `psycopg.errors.*` | What the database refuses: `UniqueViolation` (a duplicate ledger key, a login that is taken), `ForeignKeyViolation` (a row whose referenced row isn't there), `CheckViolation` (tier 0 and tier 2 CHECKs), `RaiseException` (tier-2 triggers, such as `<schema>.<table> is insert-only`), `InsufficientPrivilege` (tier-1 grants). |

## store.py

### `class Store`
`Store(conn: Connection)`. Writes and reads `factor` and `ledger`.

#### Components

| Method | Returns / raises |
| --- | --- |
| `add(registry: Registry, roots: Iterable[str]) -> list[str]` | `registry.closure(roots)`, after `registry.check` of it (`StructuralError`). In one transaction, inserts each component's `(digest, kind, v, canonical, doc)` and each of its references' `(src, path, dst, kinds)` rows (`Component.refs()`), skipping rows already stored (`ON CONFLICT DO NOTHING`). Returns the closure. |
| `get(digest: str) -> Component` | Reads `canonical` and parses it through `Registry().add_raw`, which checks the digest. `StructuralError("<digest> is not in the store")`; `StructuralError("<digest> does not match its bytes")`; `StructuralError` for another version. A new component each call. |
| `load(roots: Iterable[str]) -> Registry` | The roots and everything they reach through `factor.component_ref`, each through `add_raw`. `StructuralError("not in the store: [<roots>]")` for roots that aren't stored. Doesn't run `Registry.check`. |
| `reaching(digest: str, kind: str) -> list[str]` | The stored components of `kind` whose closure holds `digest`, the digest itself included, sorted. `[]` for a digest that isn't stored. |
| `compilations(skeleton: str) -> list[Compilation]` | The stored compilations whose `/skeleton` reference is the digest, by digest, each read through `get`. |

#### Ledger records

`append(*records: Record) -> None` writes the records in one transaction, each into its table
(`docs/ledger-api.md`, "Database: schema `ledger`"):

| Record | Table | Key columns written |
| --- | --- | --- |
| `RunStarted`, `RunFinished` | `ledger.run_stage` | `run`, `stage`, and `trial` for a started row |
| `RunItem` | `ledger.run_item` | `run`, `"case"`, `replicate` |
| `CanaryCall` | `ledger.canary_call` | `run`, `phase`, `canary` |
| `ScoreStarted` | `ledger.score_stage` | `score`, `stage`, `run`, `run_stage = 'started'`, `scoring` |
| `ScoreFinished` | `ledger.score_stage` | `score`, `stage` |
| `ScoreItem` | `ledger.score_item` | `score`, `"case"`, `replicate`, `view` |

Each row also gets `payload`, the record's `canonical` text, and `doc`, its `jsonb` copy. Nothing is overwritten:
a duplicate key raises `UniqueViolation` and the transaction is rolled back. An item, canary call or score started
row without its log's or run's started row raises `ForeignKeyViolation`; a finished row without its started row is
accepted. `TypeError("no table for <Class>")` for any other record type. It doesn't validate the log; reading it back
does.

| Method | Returns / raises |
| --- | --- |
| `run(run: UUID) -> Run` | The started row, the finished row if any, the items and the canary calls, parsed with `Record.parse` and put together as a `Run`. `LookupError("run <id> is not in the store")` without stage rows; `StructuralError("run <id> has no started row")` for a finished row alone; `Record.parse`'s errors; `ValidationError` from `Run`. |
| `score(score: UUID) -> Score` | As `run`, for a score's stage rows and items: `LookupError("score <id> is not in the store")`, `StructuralError("score <id> has no started row")`. |
| `started(runs: Collection[UUID]) -> list[RunStarted]` | The started rows of those runs, newest first. Unknown ids are skipped. |
| `runs_of(trial: str) -> list[RunStarted]` | The started rows of the runs of a trial, newest first. |
| `finished(runs: Collection[UUID]) -> set[UUID]` | Those of the runs that have a finished row. |
| `scores_of(run: UUID) -> list[ScoreStarted]` | The started rows of the scores of a run, newest first. |

## people.py

### `class People`
`People(conn: Connection)`. Writes and reads `identity` (`docs/identity.md`). A `Person` is
`chatddx.identity.Person`: `id`, `login`, `name`, `roles: frozenset[Role]`, `active`.

| Method | Returns / raises |
| --- | --- |
| `add(login: str, name: str, roles: Iterable[Role] = ()) -> Person` | Inserts the person, roles sorted, and returns them with their new id. `ValidationError` for a login that isn't `LOGIN` (`invalid login '<login>'`); `UniqueViolation` for a login that is taken. |
| `get(id: int) -> Person` | `LookupError("no person with id <id>")`. |
| `find(login: str) -> Person \| None` | |
| `update(id: int, *, name: str \| None = None, roles: Iterable[Role] \| None = None, active: bool \| None = None) -> Person` | In one transaction: sets what is given (roles deduplicated and sorted, `[]` clears them) and leaves what is `None`; with `active=False` also deletes the person's sessions. Returns the person as stored. `LookupError("no person with id <id>")`. |
| `set_password(id: int, password: str) -> None` | Stores `hash_password(password)` (argon2id), replacing any earlier hash. `ForeignKeyViolation` for an unknown person. |
| `authenticate(login: str, password: str) -> Person \| None` | The person when the login exists, has a credential, the password verifies and the person is active; else `None`. An unknown login is verified against a dummy hash, so it takes as long as a wrong password. A hash that `needs_rehash` is replaced with a new one. |
| `open_session(id: int, ttl: timedelta = settings.SESSION_TTL) -> str` | A new token (`new_token`, 32 random bytes, URL-safe). Stores only `token_digest(token)` (SHA-256 hex), expiring `ttl` from now. `ForeignKeyViolation` for an unknown person; `CheckViolation` at tier 2 for a `ttl` that isn't positive. |
| `session(token: str) -> Person \| None` | The person whose session the token is, when it hasn't expired and the person is active. |
| `close_session(token: str) -> None` | Deletes the session; nothing for an unknown token. |
| `purge_sessions() -> int` | Deletes the expired sessions and returns how many. |

`settings.SESSION_TTL` is 12 hours.

## catalog.py

### `class Rows`
`Rows(conn: Connection)` implements `src/chatddx/catalog/read.py:Reader` over the tables, as
`docs/catalog-api.md`, "read.py", lists. In SQL terms:
- `get` is `Store.get`, and `compilations` is `Store.compilations`; `kind` reads `factor.component.kind`.
- Threads, edits, entries, bindings, languages and labels are read `ORDER BY id`; `families` reads `catalog.family`.
- `edit` and `edits` don't read the edit's `kind` column; entries, languages and labels are read without `by` and
  `at`.
- `bound_to(vignette, kind)` matches the `doc` of stored components of `kind` on `vignette.source`, `vignette.id`
  and `vignette.fingerprint` (as canonical `jsonb`), by digest.
- `expectations(cases)` matches stored expectations on `doc ->> 'case'`, by digest.

It also has `subjects_naming(person: int, fields: Collection[EntryField]) -> list[Subject]`: the distinct subjects
of entries with one of `fields` naming the person, ever, as `Catalog.involving` uses it.

### `class Catalog`
`Catalog(conn: Connection)`. Its methods, and what each writes, are in `docs/catalog-api.md`, "The store's Catalog".

## migrate.py

| Name | Value |
| --- | --- |
| `MIGRATIONS` | `Path` of `migrations/` |
| `TOP_TIER` | `2` |
| `class Migration` | A frozen dataclass: `name: str` (the file's stem), `tier: int`, `path: Path`. |

| Function | Returns / raises |
| --- | --- |
| `migrations() -> list[Migration]` | Every `migrations/*.sql`, by file name. The tier is the second `-`-separated part without its `t`: `0012-t2-catalog` is tier 2. A file name with fewer than three parts, or a tier that isn't a number, raises `ValueError`. |
| `pending(conn, tier: int = TOP_TIER) -> list[Migration]` | The migrations at or below `tier` whose names aren't in `public.migration`; all of them when the table doesn't exist. Writes nothing. |
| `migrate(conn, tier: int = TOP_TIER) -> list[str]` | Creates `public.migration` if it doesn't exist and reads `pending`, in one transaction; then applies each pending migration in its own transaction, running the file and recording `(name, tier)`. Returns the names applied, in file-name order. A failing migration raises its psycopg error; the ones before it stay applied. |

File-name order isn't tier order: `migrate(conn, 0)` applies `0001`, `0004`, `0007` and `0010`, and a later
`migrate(conn, 2)` the eight others. Lowering the tier undoes nothing.

### `chatddx migrate [--tier {0,1,2}] [--dry-run]`
`src/chatddx/cli.py:_migrate` connects as `DB_ADMIN` and prints `applied <name>` for each migration `migrate`
applied (default tier `TOP_TIER`), or `would apply <name>` for each one `pending` lists with `--dry-run`; or
`nothing to apply up to tier <n>`.

## Roles and connections

`src/chatddx/core/settings.py:database(admin: bool = False) -> str` makes a libpq connection string from `DB_HOST`,
`DB_NAME`, and `DB_ADMIN` or `DB_USER` (`KeyError` when one isn't set; `.env`).

| Role | Created by | Can |
| --- | --- | --- |
| `chatddx` (`DB_ADMIN`) | `setup.sql`: `LOGIN CREATEDB CREATEROLE`, owner of the database `chatddx` | everything; runs migrations, creates test databases |
| `chatddx_writer` (`DB_USER`) | `setup.sql` as `LOGIN`; `0002` creates it `NOLOGIN` when it doesn't exist | what tier 1 grants: `SELECT, INSERT` on `factor`, `ledger` and `catalog`, and the `identity` grants below |
| `chatddx_reader` | `0002`, `NOLOGIN`, when it doesn't exist | `SELECT` on `factor`, `catalog` and `identity.person`; nothing in `ledger` |

`setup.sql` is run once per cluster by a superuser (`psql -f`). Grants don't bind the admin or a superuser; tier-2
triggers bind the admin too. At tier 0 there are no grants, so only the admin can use the tables. Roles are
cluster-wide.

## Database: `public.migration`
Created by `migrate`, not by a migration file. No grants: only the admin reads it.

| Column | Type |
| --- | --- |
| `name` | `text PRIMARY KEY`; the migration's file stem |
| `tier` | `integer NOT NULL` |
| `applied_at` | `timestamptz NOT NULL DEFAULT now()` |

## Database: schema `identity`
Created by `0007-t0-identity.sql`, roles in `0008-t1-identity.sql`, CHECKs in `0009-t2-identity.sql`. The one
mutable schema: no insert-only triggers. `People` writes it.

### `identity.person`

| Column | Type | Holds |
| --- | --- | --- |
| `id` | `bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY` | `Person.id`; what other schemas reference (`catalog.*.by`, `catalog.entry.person`) |
| `name` | `text NOT NULL` | `Person.name` |
| `login` | `text NOT NULL UNIQUE`; CHECK (0009) `login ~ '^[a-z0-9][a-z0-9._@-]*$'`, as `chatddx.identity.LOGIN` | `Person.login` |
| `roles` | `text[] NOT NULL DEFAULT '{}'`; CHECK (0009) `roles <@ ARRAY['admin', 'clinician', 'developer', 'ops', 'researcher']`, as `chatddx.identity.Role` | `Person.roles`, sorted |
| `active` | `boolean NOT NULL DEFAULT true` | `Person.active` |

`test/test_identity.py:test_roles_match_the_database_check` keeps `Role` and the roles CHECK the same.

### `identity.credential`

| Column | Type | Holds |
| --- | --- | --- |
| `person` | `bigint PRIMARY KEY`, FK → `person` | one credential per person |
| `hash` | `text NOT NULL` | the argon2id hash |

### `identity.session`

| Column | Type | Holds |
| --- | --- | --- |
| `token_digest` | `text PRIMARY KEY` | SHA-256 hex of the token; the token isn't stored |
| `person` | `bigint NOT NULL`, FK → `person` | |
| `created` | `timestamptz NOT NULL DEFAULT now()` | |
| `expires` | `timestamptz NOT NULL`; CHECK (0009) `expires > created` | |

Index `session_person (person)`.

### Roles (`0008`)
PUBLIC loses all access to the schema and its tables. `chatddx_writer` and `chatddx_reader` get `USAGE`. Each table
is granted explicitly, with no default privileges:

| Table | `chatddx_writer` | `chatddx_reader` |
| --- | --- | --- |
| `person` | `SELECT, INSERT, UPDATE` | `SELECT` |
| `credential` | `SELECT, INSERT, UPDATE` | |
| `session` | `SELECT, INSERT, DELETE` | |

So the writer can't delete people or credentials.

### What the database checks, and what it doesn't
It checks unique logins and their pattern, known role names, one credential per person, that credentials and
sessions belong to a person, and that a session expires after it is created. It doesn't check names, that a hash is
argon2id, or that an inactive person has no sessions (`People.update` deletes them, and `People.session` ignores
them).

## Migrations
`migrations/NNNN-tT-<schema>[-<what>].sql`, applied by `migrate`:

| File | Tier | Schema | Documented in |
| --- | --- | --- | --- |
| `0001-t0-factor.sql` | 0 | `factor`: `component`, `component_ref` | `docs/factors-api.md`, "Database: schema `factor`" |
| `0002-t1-factor.sql` | 1 | creates `chatddx_writer` and `chatddx_reader`; `factor` grants | `docs/factors-api.md` |
| `0003-t2-factor.sql` | 2 | `factor` CHECK, `factor.check_ref`, `factor.refuse_change()`, insert-only triggers | `docs/factors-api.md` |
| `0004-t0-ledger.sql` | 0 | `ledger`: run and score logs | `docs/ledger-api.md`, "Database: schema `ledger`" |
| `0005-t1-ledger.sql` | 1 | `ledger` grants, writer only | `docs/ledger-api.md` |
| `0006-t2-ledger.sql` | 2 | `ledger` CHECKs, insert-only triggers | `docs/ledger-api.md` |
| `0007-t0-identity.sql` | 0 | `identity`: `person`, `credential`, `session` | here |
| `0008-t1-identity.sql` | 1 | `identity` grants | here |
| `0009-t2-identity.sql` | 2 | `identity` CHECKs | here |
| `0010-t0-catalog.sql` | 0 | `catalog`, and `UNIQUE` targets on `factor` tables | `docs/catalog-api.md`, "Database: schema `catalog`" |
| `0011-t1-catalog.sql` | 1 | `catalog` grants | `docs/catalog-api.md` |
| `0012-t2-catalog.sql` | 2 | `catalog` CHECKs and triggers, insert-only triggers | `docs/catalog-api.md` |

How to name and list a new migration is in `docs/migrations.md`.

## Tests
`src/chatddx/conftest.py`, shared by every package's tests:

| Name | Description |
| --- | --- |
| `create_database(template: str \| None = None) -> str` | Creates `chatddx_test_<12 hex>` as the admin, from `template` when given, and returns its name. With a template, it first waits for the template's sessions to end (`_settled`), since copying a database that has sessions fails. |
| `drop_database(name: str) -> None` | Waits for the database's sessions to end (`_settled`), then `DROP DATABASE … WITH (FORCE)` as the admin. |
| `_settled(admin: Connection, name: str) -> None` | Polls `pg_stat_activity` until no session is on `name`, every 0.05 s for at most 5 s, then returns either way. A session closed a moment ago may still be ending on the server, and `WITH (FORCE)` as the admin can't end a session of the writer's: it fails with "permission denied to terminate process". |
| `connect(name: str, admin: bool = False) -> Connection` | A connection to that database, as the writer or the admin. |
| `migrated` (session fixture) | A database migrated to `TOP_TIER`, the template for `db`; dropped at the end. |
| `db` | A fresh copy of `migrated` per test, dropped afterwards. |
| `conn`, `admin` | Connections to `db` as the writer and as the admin. |
| `empty_db`, `empty` | An unmigrated database per test, and an admin connection to it. |

Tests fail, rather than skip, when Postgres can't be reached.

## Known gaps
From `docs/store.md`, "Known gaps", where they concern this API:
- The database doesn't check that a component has all its reference rows; `Store.add` writes them together.
- The database allows a thread without edits; `Catalog.create` writes both in one transaction.
- `jsonb` rejects `\u0000`, so a component or record holding NUL can't be stored.
- `doc` reorders object keys; components and records must be read from `canonical` and `payload`.
- No async API, and on a connection that isn't in autocommit mode, writes wait for the caller's commit.
- No per-kind read-only views.
- A log can be written that can't be read back: a finished row is accepted without its started row, and `Store.run`
  and `Store.score` then raise `StructuralError("<log> <id> has no started row")`.
- `RunStarted.canaries` has no foreign key.
- A schema-version bump strands stored rows: `get`, `load`, `run` and `score` refuse another version, and the rows
  can't be rewritten.

## Beyond docs/store.md
Behavior described here that `docs/store.md` doesn't state:
- `Store.finished` returns a set, not a newest-first list.
- `Store.add` returns the whole closure, also the components that were already stored.
- `Store.get` returns a new component on each call; nothing is cached.
- `Store.run` and `Store.score` return items and canary calls in whatever order Postgres returns them.
- `Store.reaching` includes the digest itself when it is of the kind asked for.
- `Store.compilations` isn't listed in `docs/store.md`.
- `People.update` with `roles=[]` clears the roles, and reactivating a person restores no sessions.
- `People` reads roles back as `Role`, so a role the tier-2 CHECK would refuse raises `ValueError` below tier 2.
- `public.migration` is created by `migrate`, not by a migration file, and is readable only by the admin.
- `migrations()` raises `ValueError` for a file name with fewer than three `-`-separated parts.

## Proposed amendments

# Store

The store is chatddx's database: PostgreSQL, reached through psycopg with plain SQL migrations and no ORM. Each module
that keeps data has a schema of its own: the factors (docs/factors.md), the ledger (docs/ledger.md), identity
(docs/identity.md) and the catalog (docs/catalog.md). Everything but identity is append-only, and the database
enforces it at tier 2.

This document describes what the store keeps, how the database guards it, and how it is reached. Names, rules and
errors are in the API, docs/store-api.md. Each schema's tables are described with its module's API, and its
migrations in docs/migrations.md.

## What the store does
The store answers which rows exist; the modules decide what they mean.

### Components
Components are stored a closure at a time: a component with everything it references, transitively, each with a row
for each of its references, all at once and only once the closure checks out. Components already stored are left as
they are. A component is read back from the exact text it was stored as and checked against its digest, so what
comes out is what went in. A closure can be loaded as a registry without checking it, so the registry's own checks
and bundles work on it as on any other.

The store also finds the components of a kind that reach a given one, such as the trials built on a prompt, and the
compilations of a skeleton.

### Records
Ledger records are written as they happen, those that belong together at once, and never overwritten: a record whose
place is taken is refused. A run's or a score's log is read back whole, and validated as it is read. Runs and scores
are listed newest first: those of a trial, those of a run, or those asked for; and the store tells which runs have
finished.

### People
People, their passwords and their sessions are identity's (docs/identity.md). The store adds people and changes them,
but never removes them; it checks passwords and keeps sessions, and disabling a person ends their sessions.

### The catalog
The catalog decides what its rows mean (docs/catalog.md). The store reads the rows it asks for and writes what it
decided, all of one change at once.

### Looking things up for someone
Tools that act for a person, such as the planned shell, look things up the way that person sees them: among the
live threads and families they own or collaborate on, and the runs they own. That lets the person refer to things
loosely. A thread is found by its name, matched whole first and only then read as an owner and a name, since names
may hold a slash, and runs by the start of their id or by a component their trial is built on. For a run, the store
also tells which scorers can grade its answers, which scoring it would be scored under now, from the expectations the
catalog picks for the person, and whether it still has to be scored under that scoring, so a run whose expectations
changed after it was scored is due again. Like authorization, this decides what is relevant to show, not who may read
what (docs/identity.md, "Authorization").

## Tiers
Integrity comes in three tiers, and a deployment applies migrations up to a chosen tier. Each schema has migrations
at every tier:
- Tier 0: schemas, tables, keys, foreign keys, indexes and simple checks on single columns.
- Tier 1: roles and grants.
- Tier 2: checks and triggers that repeat the rules held in Python, and the triggers that keep tables append-only.
  They check the columns the application writes, so the Python code is the same at every tier.

Migrations are applied in file-name order up to the chosen tier, each on its own, and the database records which were
applied. Raising the tier later applies what was skipped; lowering it undoes nothing. File-name order is not tier
order: a later schema's tier 0 runs after an earlier schema's tier 2. The command chatddx migrate applies them as the
admin, up to the top tier unless told otherwise, and can list what it would apply instead.

## Roles and connections
Connections are set up from the environment (.env-example), through the project's settings. Roles belong to the
cluster rather than to a database, so every database in a cluster shares them. Grants don't bind the admin or a
superuser, which is why the app connects as the writer and not as the admin; at tier 0 there are no grants, so a
tier-0 deployment has to connect as the admin. Tier-2 triggers bind the admin too, and only a superuser who disables
triggers gets around them.

| Role | Used by | Created by | May |
| --- | --- | --- | --- |
| Admin | Whoever deploys: it owns the database and its schemas, runs the migrations and creates the tests' databases. | The database setup script, which also creates the database it owns. | Everything. It has to be able to create roles the first time tier 1 runs in a cluster, and databases to run the tests. |
| Writer | The app. | The database setup script, as a role that can log in. Tier 1 creates it, unable to log in, only when it doesn't exist. | Read and add to the factors, the ledger and the catalog; add people and change them and their passwords, but never remove them; open and end sessions. |
| Reader | Nothing yet. | Tier 1, unable to log in, when it doesn't exist. | Read what isn't sensitive: the factors, the catalog and people, but not the ledger, passwords or sessions. |

Agents use the system's cluster (setup in AGENTS.md); the devShell runs one of its own (scripts/dev-db.sh).

## Tests
Every package's tests share one migrated template database per session, and each test gets a fresh copy of it,
dropped afterwards. The admin creates and migrates databases; tests connect as the writer, except where they need the
admin, for tier-0 writes and tier-2 triggers. They fail, rather than skip, when the database can't be reached.

## Terms

| Term | Meaning |
| --- | --- |
| Schema | One module's tables, in a namespace of their own. |
| Tier | How much integrity the database enforces: structure, then grants, then the rules held in Python. |
| Migration | A file of SQL a deployment applies once, at its tier. |
| Admin | The role that owns the database and runs the migrations. |
| Writer | The role the app connects as. |
| Reader | The role that may read what isn't sensitive. |
| Closure | A component and everything it references, transitively. |

## Known gaps
These are known shortcomings of the store's design. The API lists them where they show (docs/store-api.md, "Known
gaps").
- The database doesn't check that a component has all its reference rows, only that the rows it has are right; the
  store writes them together.
- The database allows a thread without versions; the catalog writes a thread together with its first version.
- The database can't keep text holding a NUL character, so a component or record containing one can't be stored.
- The copy of each component and record kept for queries reorders object keys, so a schema's property order survives
  only in the stored text. Components and records are read from the stored text, and a future ORM or view must not
  rebuild them from the copy.
- No async API. The runner is synchronous, and wants each row to land as it is written. On a connection that doesn't
  commit each statement by itself, a write outside a transaction opens one that only the caller commits, and the
  store's own transactions become savepoints inside it.
- Read-only views per kind of component, for a future ORM, aren't written.
- A log can be written that can't be read back. Storing a record checks only what the database can, and a finish
  record isn't tied to its start record, so a finish record alone is accepted; reading the log back then reports that
  it has no start record. Logs are validated only when they are read.
- A run's canary set isn't tied to the run in the database, so a run can name a canary set that isn't stored, and
  then can't be checked.
- A schema-version bump strands stored rows. Reading parses every row, and parsing refuses another version
  (docs/factors.md, "Versions"; docs/ledger.md, "Canonical form and versions"), so after a bump the store can't return
  rows of the old version, nor load a closure that holds one. The rows can't be rewritten either: the tables are
  append-only, and digests and seals depend on the bytes. docs/factors.md, "Splitting expectations", already considers
  a bump of the scorer's schema version.

## Proposed amendments

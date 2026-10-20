# Store

The store is chatddx's database: PostgreSQL, reached through psycopg with plain SQL migrations and no ORM. Each module
that keeps data has a schema of its own: the factors (docs/modules/factors.md), the ledger (docs/modules/ledger.md),
identity (docs/modules/identity.md) and the catalog (docs/modules/catalog.md).

Catalog, factors and ledger are append-only, and the database enforces it at tier 2. Identity and the worker queue allow
updates.

```
AGENT: REPLACE
`docs/reference/` is `docs/surfaces/` now.
---
This document describes what the store keeps, how the database guards it, and how it is reached. Classes, fields and
errors are in docs/surfaces/store.md, and each schema's tables in its migrations (docs/migrations.md).
```
This document describes what the store keeps, how the database guards it, and how it is reached. Classes, fields and
errors are in docs/reference/store.md, and each schema's tables in its migrations (docs/migrations.md).

## What the store does

The store answers which rows exist; the modules decide what they mean.

### Components

Components are stored a closure at a time: a component with everything it references, transitively, each with a row for
each of its references, all at once and only once the closure checks out. Components already stored are left as they
are. A component is read back from the exact text it was stored as and checked against its digest, so what comes out is
what went in. A closure can be loaded as a registry without checking it, so the registry's own checks and bundles work
on it as on any other.

The store also finds the components of a kind that reach a given one, such as the trials built on a prompt, and the
compilations of a skeleton.

### Records

Ledger records are written as they happen with those that belong together in a single transaction.

Heads-up: A record whose place is taken is refused.

### Texts

The texts of database sources (docs/modules/inventory.md, "Sources") are kept as people typed them, each under a new id.
The writer adds and reads them; only the admin deletes one, to purge spam; the reader can't read them, since they are
vignettes.

### People

People, their passwords and their sessions are identity's (docs/modules/identity.md). The store adds people and changes
them. It checks passwords and keeps sessions, removing those expired whenever one opens, and disabling a person ends
their sessions.

### The catalog

The catalog decides what its rows mean (docs/modules/catalog.md). The store reads the rows it asks for and writes what
it decided, all of one change at once. Whoever reads the catalog asks the catalog, over the rows the store reads.

### Notifications

Writing a run's or a score's records tells the run's channel, and the queue tells the workers' and the run's how a job
stands. What a worker says as it happens goes out on the run's channel too, as few notifications as hold it, a long one
in parts that a listener puts together again. The store listens for those who follow, so that neither the worker nor the
app holds SQL of its own.

## Tiers

Integrity comes in three tiers, and a deployment applies migrations up to a chosen tier. Each schema has migrations at
every tier:

- Tier 0: schemas, tables, keys, foreign keys, indexes and simple checks on single columns.
- Tier 1: roles and grants.
- Tier 2: checks and triggers that repeat the rules held in Python, and the triggers that keep tables append-only. They
  check the columns the application writes, so the Python code is the same at every tier.

Migrations are applied in file-name order up to the chosen tier, each on its own, and the database records which were
applied. Raising the tier later applies what was skipped; lowering it undoes nothing. File-name order is not tier order:
a later schema's tier 0 runs after an earlier schema's tier 2. The command chatddx migrate applies them as the admin, up
to the top tier unless told otherwise, and can list what it would apply instead.

## Roles and connections

Connections are set up from the environment (.env), through the project's settings. Roles belong to the cluster rather
than to a database, so every database in a cluster shares them. Grants don't bind the admin or a superuser, which is why
the app connects as the writer and not as the admin.

At tier 0 there are no grants, so a tier-0 deployment has to connect as the admin. Tier-2 triggers bind the admin too,
and only a superuser who disables triggers gets around them.

| Role   | Used by                          | Created by    | May                                                      |
| ------ | -------------------------------- | ------------- | -------------------------------------------------------- |
| Admin  | `chatddx migrate` and the tests. | Setup script. | Own the database and schemas; create databases and roles |
| Writer | The app.                         | Setup script. | Read and add to factors, ledger and catalog.             |
| Reader | Nothing yet.                     | Tier 1.       | Read the factors, the catalog and people.                |

The reader can't read the ledger or sessions.

Agents use the system's cluster (setup in AGENTS.md); the devShell runs one of its own (scripts/dev-db.sh).

## Tests

Every package's tests share one migrated template database per session, and each test gets a fresh copy of it, dropped
afterwards.

Before a database is copied or dropped, the tests wait for the sessions on it to end, since one closed a moment ago may
still be ending on the server, and the admin can't end a writer's session to drop the database by force.

The admin creates and migrates databases; tests connect as the writer, except where they need the admin, for tier-0
writes and tier-2 triggers. They fail, rather than skip, when the database can't be reached.

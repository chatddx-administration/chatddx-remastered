# Identity

Identity is who acts in chatddx: the people, the roles they hold, how they sign in, and what each is shown. Most of what
chatddx does is done as a person, and `identity` is its declarative layer: its rules are data and pure functions with no
store access (src/chatddx/identity/), which the bench, the operational layer, applies to what is in the store and the
World, and the catalog to the owners it records or is asked about.

```
AGENT: REPLACE
`docs/reference/` is `docs/surfaces/` now.
---
This document describes what identity holds and why. Names, signatures and errors are in docs/surfaces/identity.md.
People, their passwords and their sessions are kept by the store (docs/modules/store.md, "People"; `People` in
docs/surfaces/store.md), and the `identity` schema and its migrations are in docs/migrations.md.
```
This document describes what identity holds and why. Names, signatures and errors are in docs/reference/identity.md.
People, their passwords and their sessions are kept by the store (docs/modules/store.md, "People"; `People` in
docs/reference/store.md), and the `identity` schema and its migrations are in docs/migrations.md.

## People

A person has an id, a login, a name, roles, and whether they are active. The id is what the rest of the store refers to:
the catalog's owners, collaborators and writers, and who typed a text. The login is what a person signs in with, unique,
and lowercase as Keycloak keeps usernames, so that people carry over when it comes (see "Keycloak"). The name is for
display.

People are never deleted, since what they wrote refers to them. A person who leaves is made inactive, which ends their
sessions and keeps them from signing in.

## Roles

The roles are admin, clinician, developer, ops and researcher (src/chatddx/identity/identity.py:Role). All but admin are
the principal authors of docs/modules/factors.md (docs/glossary.md, "Roles"); admin is identity's own, for administering
people. A person may hold several. Roles live in code and are stored on the person by name, and the database holds the
names to the code's list.

Nothing checks a role yet: a person writes on what they own, whatever their roles (docs/modules/bench.md, "Writes for
the person"), and nothing asks for admin (docs/backlog.md, "Administering people").

## Authentication

The app signs people in itself, with passwords and sessions in the database; there is no identity provider yet.

- **Passwords** are kept as argon2id hashes, and hashed again when a sign-in finds one made under older parameters. A
  login nobody has is checked against a stand-in hash, so that it takes as long to refuse as a wrong password, and both
  are refused alike.
- **Sessions** are kept on the server. Signing in gives a random token, of which only a sha256 digest is kept, so the
  table holds nothing a client could present. A session lasts `settings.SESSION_TTL`, 12 hours; its expiry is checked
  each time it is used, and signing out or being made inactive ends it.

How a token is carried is the edge's: the API takes it as a bearer token or a cookie (docs/modules/api.md,
"Authentication"). The repl and the commands act as a person by login, over a database connection of their own, without
signing in.

## Authorization

What a person is shown is a convenience, not a protection: it decides what is relevant to show them. Sensitive data is
protected by clearance and the database's grants (agents/wip-clearance.md), not by what a person is shown.

It goes by the catalog's owners and collaborators, and only what is live counts (docs/modules/catalog.md, "Owners"): a
person owns what names them its owner (src/chatddx/identity/identity.py:owns), collaborates on what is shared with them
and isn't theirs (`collaborates`), and sees both (`sees`). Of what they see, their own comes first (`preferred`), which
is how a name finds its thread or family.

The catalog says who owns and shares what, and applies `owns` only to an owner, the one it records, to hold one live
expectation per case and schema, or one it is asked to find threads by. The bench applies the rules to what the catalog
gives, and to what is in the store and the World (docs/modules/bench.md, "What a person sees").

What each role is shown, a map from roles to the kinds each sees, goes beside `sees` once the portal's views give it
meaning (agents/wip-portal.md, "Below the UI").

## Managing people

People are managed by command, connecting as `DB_USER`:

- `chatddx person add LOGIN NAME [--role ROLE …]` adds a person;
- `chatddx person password LOGIN` sets their password, asked for twice, and refuses an empty one;
- `chatddx init-data LOGIN` adds a person by that login, named by it, when there is none (docs/modules/curation.md).

## Keycloak

The deployment is to sit behind Keycloak. Logins follow its lowercase usernames so that people carry over, and signing
in with a password can stay as the development path. How Keycloak hands the app a login isn't decided
(agents/wip-deploy.md, "What holds now", Identity), nor whether roles then come from its realm roles instead of the
person.

## Tests

- src/chatddx/identity/test/test_identity.py: who owns, collaborates on and sees what, nothing deleted, and their own
  first.
- src/chatddx/store/test/test_identity.py: people, passwords and sessions; that tokens aren't stored; what the database
  guards, and that the reader sees people but no secrets.
- src/chatddx/store/test/test_cli.py: the `person` commands.
- Signing in through the API: src/chatddx/api/test/test_people.py (docs/modules/api.md, "Authentication").

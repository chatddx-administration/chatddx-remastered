# Identity

Identity is who acts in chatddx: the people, the roles they hold, how they sign in, and what each is shown. Most of
what chatddx does is done as a person, and `identity` is its declarative layer: its rules are data and pure functions
with no store access (src/chatddx/identity/), which the bench, the operational layer, applies to what is in the store
and the World, and the catalog to the owners it records or is asked about.

This document describes what identity holds and why. Names, signatures and errors are in docs/identity-api.md. People,
their passwords and their sessions are kept by the store (docs/store.md, "People"; `People` and "Database: schema
`identity`" in docs/store-api.md), and their migrations are in docs/migrations.md.

## People
A person has an id, a login, a name, roles, and whether they are active. The id is what the rest of the store refers
to: the catalog's owners, collaborators and writers, and who typed a text. The login is what a person signs in with,
unique, and lowercase as Keycloak keeps usernames, so that people carry over when it comes (see "Keycloak"). The name
is for display.

People are never deleted, since what they wrote refers to them. A person who leaves is made inactive, which ends their
sessions and keeps them from signing in.

Names aren't sensitive (docs/chatddx.md, glossary, "Sensitive"), so the reader may read people. Passwords and sessions
are secrets rather than sensitive data, and it reads neither.

## Roles
The roles are admin, clinician, developer, ops and researcher (src/chatddx/identity/identity.py:Role). All but admin
are the principal authors of docs/chatddx.md ("Roles mentioned") and docs/factors.md; admin is identity's own, for
administering people. A person may hold several. Roles live in code and are stored on the person by name, and the
database holds the names to the code's list.

Nothing checks a role yet: a person writes on what they own, whatever their roles (docs/bench.md, "Writes for the
person"), and nothing asks for admin (see "Open design issues").

## Authentication
The app signs people in itself, with passwords and sessions in the database; there is no identity provider yet.
- **Passwords** are kept as argon2id hashes, and hashed again when a sign-in finds one made under older parameters. A
  login nobody has is checked against a stand-in hash, so that it takes as long to refuse as a wrong password, and both
  are refused alike.
- **Sessions** are kept on the server. Signing in gives a random token, of which only a sha256 digest is kept, so the
  table holds nothing a client could present. A session lasts `settings.SESSION_TTL`, 12 hours; its expiry is checked
  each time it is used, and signing out or being made inactive ends it.

How a token is carried is the edge's: the API takes it as a bearer token or a cookie (docs/api.md, "Signing in"). The
repl and the commands act as a person by login, over a database connection of their own, without signing in.

## Authorization
What a person is shown is a convenience, not a protection: it decides what is relevant to show them. Sensitive data is
protected by clearance and the database's grants (agents/wip-clearance.md), not by what a person is shown.

It goes by the catalog's owners and collaborators, and only what is live counts (docs/catalog.md, "Owners"): a person
owns what names them its owner (src/chatddx/identity/identity.py:owns), collaborates on what is shared with them and
isn't theirs (`collaborates`), and sees both (`sees`). Of what they see, their own comes first (`preferred`), which is
how a name finds its thread or family.

The catalog says who owns and shares what, and applies `owns` only to an owner, the one it records, to hold one live
expectation per case and schema, or one it is asked to find threads by. The bench applies the rules to what the catalog
gives, and to what is in the store and the World (docs/bench.md, "What a person sees").

What each role is shown, a map from roles to the kinds each sees, goes beside `sees` once the portal's views give it
meaning (agents/wip-identity.md, "Open").

## Managing people
People are managed by command, connecting as `DB_USER`:
- `chatddx person add LOGIN NAME [--role ROLE …]` adds a person;
- `chatddx person password LOGIN` sets their password, asked for twice;
- `chatddx init-data LOGIN` adds a person by that login, named by it, when there is none (docs/curation.md).

A person without a password can't sign in to the API, but can be acted as from the repl.

## Keycloak
The deployment is to sit behind Keycloak. Logins follow its lowercase usernames so that people carry over, and signing
in with a password can stay as the development path. How Keycloak hands the app a login isn't decided (docs/api.md,
"Outstanding", "Signing in"), nor whether roles then come from its realm roles instead of the person.

## Tests
- src/chatddx/identity/test/test_identity.py: who owns, collaborates on and sees what, nothing deleted, and their own
  first.
- src/chatddx/store/test/test_identity.py: people, passwords and sessions; that tokens aren't stored; what the
  database guards, and that the reader sees people but no secrets.
- src/chatddx/store/test/test_cli.py: the `person` commands.
- Signing in through the API: src/chatddx/api/test/test_people.py (docs/api.md, "Signing in").

## Terms

| Term | Meaning |
| --- | --- |
| Person | Someone who acts in chatddx, by an id the rest of the store refers to. |
| Login | What a person signs in with: unique and lowercase. |
| Role | Admin, clinician, developer, ops or researcher; a person may hold several. |
| Active | Whether a person may sign in. People are made inactive, never deleted. |
| Session | A person signed in, by a token of which only a digest is kept. |
| Sees | Owns, or collaborates on. |
| Owns | Is the owner of, while it is live. |
| Collaborates on | Has shared with them, while it is live, and isn't the owner of. |

## Open design issues
- **Sign-ins aren't limited.** Each costs an argon2 verification. The API's take is none until Keycloak is in front,
  which limits them itself (docs/api.md, "Outstanding").
- **Nobody administers people through chatddx.** The admin role exists, but nothing asks for it, and the commands
  connect as `DB_USER`, so whoever reaches the database adds people.
- **No command changes a person**: their name, roles, or whether they are active (`People.update`).
- **Expired sessions are kept** until `People.purge_sessions()`, which nothing calls on a schedule. They can't be used,
  since a session's expiry is checked when it is.
- **What each role is shown** isn't written (see "Authorization").

# Identity: what is open

## Open
`docs/identity.md`, "Open design issues", lists these too; here are the takes.

### Z1: what each role is shown
Decided: authorization goes by role first, which kinds a role sees, then by the catalog's owners and collaborators. The
map from roles to kinds isn't written; it needs the portal's views to mean anything.

Take: the map goes beside `sees` in `src/chatddx/identity/identity.py`, as data, and `sees` then takes the person's
roles and the kind as well as the `Owned`. The kinds each role authors can go beside it, clinicians appendices,
expectations and typed cases, researchers chunks and recipes, as a convenience for the portal's forms rather than a
refusal (`agents/wip-authoring.md`, "A11. Who may write what").

### Who may administer people
`Role.ADMIN` exists, but nothing asks for it, and `chatddx person` connects as `DB_USER`, so anyone with database
access adds people. No command changes a person's name, roles or whether they are active (`People.update`).

### Expired sessions and sign-ins
Expired sessions are only removed by `People.purge_sessions()`, which nothing calls on a schedule. Sign-ins aren't
limited; `docs/api.md`, "Outstanding", takes none until Keycloak is in front.

### Take, for when Keycloak arrives
Keycloak, or a proxy in front such as oauth2-proxy, authenticates, and the app maps its username onto `person.login`,
which is why logins are lowercase like Keycloak's. Password login can stay as the development path. Roles could then
come from Keycloak's realm roles instead of the column; not decided.

### What could move to identity
Rules that are pure functions of a person go to `identity`, and the bench applies them (`docs/bench.md`). Moving the
catalog's `About.shows` and `About.owned_by` gave `owns`, `collaborates` and `sees`; making the catalog take no person
moved the filtering of threads, families and expectations to the bench, over those rules.

Moving one-line comparisons one at a time doesn't pay: replacing `about.owner == person` with a call of the same
length adds a name and an import per site (tried on the bench, and reverted). Take: move a rule when it is shared by
several places or grows beyond a comparison. Candidates left where they are:
- **The default owner**, `by if owner is None else owner` in `src/chatddx/store/catalog.py:Catalog.create` and
  `Catalog.adopt`. Take: move it when a second rule about owning on write, such as Z1's kinds a role authors, gives
  identity a reason to hold write rules.
- **The bench's owner comparisons**: a person's own deleted threads (`Seen.thread_by_id`, `Seen.deleted`), only the
  owner says anything of a thread, and nobody shares with themselves (`saying.py:say`), and an expectation that is
  "yours already" (`taking.py:take_from`).
- **The edges' "own first"**: `src/chatddx/repl/listing.py` and `src/chatddx/portal/` list a person's own first, by
  login or id, much as `preferred` picks.
- **`src/chatddx/catalog/threads.py:picked`** is pure, but decides among a case's expectation threads, not who: it
  stays with the catalog.

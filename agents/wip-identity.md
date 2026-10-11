# Identity: work in progress

Material for `docs/identity.md`. Split out of the former `agents/wip-bookkeeping.md`.
`docs/identity.md` was a draft too, and was folded back in here with its proposed amendments applied (see "What holds
now").
"Decided" means the user said so; "Take" is the agent's recommendation and still open.

## Scope
`docs/factors.md` ("Not factors") assigns people, roles, authentication and authorization to identity. Identity is
referenced by the catalog (owners, collaborators, who started a run) and possibly by clearance (who granted it).

## What holds now
### People
People are `identity.person (id, login, name, roles, active)`. `id` is what other schemas reference, `login` is
unique and lowercase, and `name` is for display. People are never deleted: `active = false` disables them and ends
their sessions (`src/chatddx/store/people.py:People.update`).

People are managed with `chatddx person add LOGIN NAME [--role ROLE …]` and `chatddx person password LOGIN`
(`src/chatddx/cli.py`), connecting as `DB_USER`.

Names are not sensitive, so `chatddx_reader` may read `identity.person`, but not credentials or sessions, which are
secrets rather than sensitive data.

### Roles
Roles are defined in code (`src/chatddx/identity/identity.py:Role`: admin, clinician, developer, ops, researcher)
and stored as strings on the person. Tier 2 restricts the column to those names
(`src/chatddx/store/migrations/0009-t2-identity.sql`; `0008-t1-identity.sql` is tier 1's grants).

### Authentication
Authentication is owned by the app: argon2id password hashes in `identity.credential`, and server-side sessions in
`identity.session` holding only a sha256 of the token, with lifetime `settings.SESSION_TTL`
(`src/chatddx/identity/identity.py`, `src/chatddx/store/people.py`). Neither table is readable by `chatddx_reader`.
There is no IdP today. The deployment will eventually sit behind Keycloak, and `login` follows Keycloak's lowercase
usernames so that people carry over; how Keycloak hands the app a login is not decided.

### Authorization
Authorization is a convenience, not a protection: it decides what is relevant to show. Sensitive data is protected by
clearance and database grants, not by authorization. It goes by role first (which kinds a role sees, Z1), then also by
the catalog's owner and collaborators (Z2).
- Who sees what is `src/chatddx/identity/identity.py:sees`: the owner, and the collaborators. The catalog adds that
  what it shows is live (`src/chatddx/catalog/model.py:About.shows`).
- Z1's map from role to kinds goes beside `sees`. `identity` holds both, as data and functions with no store access.
- The bench applies them to what is in the store and the World (`agents/wip-bench.md`, "Decided").

## Done
- Migrations `0007-t0-identity.sql` (person with login, roles and active; credential; session),
  `0008-t1-identity.sql` (grants) and `0009-t2-identity.sql` (login pattern, role names, session expiry), all in
  `src/chatddx/store/migrations/` (`docs/migrations.md`).
- `src/chatddx/identity/identity.py`: `Role`, `Person`, argon2id hashing (`argon2-cffi`), session tokens and `sees`,
  exported by `chatddx.identity`.
- `src/chatddx/store/people.py`: `People`, the store API for people, passwords and sessions.
- `chatddx person add` / `chatddx person password` (`src/chatddx/cli.py`).
- Tests: `src/chatddx/store/test/test_identity.py`, `test_cli.py`, and `src/chatddx/identity/test/test_identity.py`.
- `DB_OWNER` renamed to `DB_ADMIN`, freeing "owner" for the catalog.

## Decisions

### 1. People are a small mutable table of their own
Decided: `(id, name)`, mutable, in its own schema, separate from `factor`, `ledger` and the catalog.

Take:
- schema `identity`, table `identity.person (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY, name text NOT NULL)`;
- the catalog references `identity.person(id)`;
- the writer gets SELECT, INSERT, UPDATE on this table only. It's the one mutable table, so its t2 migration attaches
  no insert-only triggers to it;
- a person who leaves can't be deleted while catalog rows reference them (the foreign key restricts it), which keeps
  the history intact. A later `active` column can hide them in the portal;
- code goes in `src/chatddx/core/identity.py`, since the user's view was that the identity model is what belongs in
  `core`. It has since moved to its own package, `src/chatddx/identity/` (a03f8b5).

### 2. Not sensitive
Decided: only vignettes and data derived from them are sensitive. Names are not, so `chatddx_reader` may read
`identity.person` (not credentials or sessions, which are secrets rather than sensitive data).

### 3. Authentication, roles and authorization
Decided:
- Authentication is owned by the app (option B): passwords and sessions in the database. No IdP today. The deployment
  will eventually sit behind Keycloak; know it, don't implement it.
- Roles live in code and are stored as strings on the person (R1).
- Authorization is a convenience that decides what is relevant to show, not a protection: by role first (Z1), then
  also by catalog owner and collaborators (Z2).
- The rules are `identity`'s, as data and functions with no store access, and the bench applies them
  (`agents/wip-bench.md`, "Decided").

Take, for when Keycloak arrives: Keycloak (or a proxy in front, such as oauth2-proxy) authenticates and the app maps
its username onto `person.login`, which is why logins are lowercase like Keycloak's. Password login can stay as the
development path. Roles could then come from Keycloak's realm roles instead of the column; not decided.

## Open
- **Web framework.** Decided for the API: FastAPI (`agents/wip-api.md`, "Serving"). The API signs people in with
  sessions, by bearer token or by a `__Host-` cookie that is `HttpOnly`, `Secure` and `SameSite=Lax`, and checks that a
  cookie's unsafe requests come from the site's own pages (`src/chatddx/api/people.py`; `agents/wip-api.md`, "Signing
  in"). The portal shares that cookie, as one app with the API (`agents/wip-portal.md`, "P3b, concretely"). Open: login
  rate limiting.
- **Z1's map from role to kinds** isn't written; it needs the portal's views to mean anything.
- **Who may administer people.** `Role.ADMIN` exists, but nothing checks it; the CLI connects as `DB_USER`, so anyone
  with database access can add people.
- **Expired sessions** are only removed by `People.purge_sessions()`; nothing calls it on a schedule.

## What `docs/` expects of `docs/identity.md`
These docs still link to `docs/identity.md`, which is gone until this draft is adopted:
- `docs/chatddx.md` (glossary, "Sensitive"): people's names aren't sensitive;
- `docs/factors.md`: the roles are the principal authors; people, roles, authentication and authorization are
  identity's;
- `docs/store.md` (introduction, "People"): identity's schema, and its people, passwords and sessions;
- `docs/store-api.md` (introduction, `People`): the `identity` schema;
- `docs/catalog.md` (introduction, "Owners"): people by their identity, and "Authorization": what a person sees is
  what is relevant to show, not who may read it;
- `docs/catalog-api.md` ("Conventions"): people are ids of `identity.person`.

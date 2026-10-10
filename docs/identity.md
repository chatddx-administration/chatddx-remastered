```
AGENT: ADD
Ten links in docs/ point here: chatddx.md:19, factors.md:16 and :46, store.md:5 and :34, store-api.md:12 and :119,
catalog.md:14 and :144 (to "Authorization"), catalog-api.md:56. This file was folded into agents/wip-identity.md in
356c96d; identity has since been built and tested (src/chatddx/store/test/test_identity.py). The suggestion is that
plan's "What holds now", checked against the code at 657716a, with its open items as known gaps. If identity should
stay a plan, point the ten links at agents/wip-identity.md instead and drop this file.
---
# Identity

Identity holds people, their roles, how they sign in, and what is relevant to show them. The catalog refers to people
by their identity (owners, collaborators, who started a run), and clearance may too (who granted it). Names, fields,
rules and errors are in the store's API, docs/store-api.md (`people.py`, and the `identity` schema).

Names are not sensitive, so `chatddx_reader` may read `identity.person`, but not credentials or sessions, which are
secrets rather than sensitive data.

## People
People are `identity.person (id, login, name, roles, active)`. `id` is what other schemas reference, `login` is
unique and lowercase, and `name` is for display. People are never deleted: `active = false` disables them and ends
their sessions (`src/chatddx/store/people.py:People.update`).

People are managed with `chatddx person add LOGIN NAME [--role ROLE …]` and `chatddx person password LOGIN`
(`src/chatddx/cli.py`), connecting as `DB_USER`.

## Roles
Roles are defined in code (`src/chatddx/identity/identity.py:Role`: admin, clinician, developer, ops, researcher)
and stored as strings on the person. Tier 2 restricts the column to those names
(`src/chatddx/store/migrations/0009-t2-identity.sql`).

## Authentication
Authentication is owned by the app: argon2id password hashes in `identity.credential`, and server-side sessions in
`identity.session` holding only a SHA-256 of the token, with lifetime `settings.SESSION_TTL`
(`src/chatddx/identity/identity.py`, `src/chatddx/store/people.py`). There is no IdP today. The deployment will
eventually sit behind Keycloak, and `login` follows Keycloak's lowercase usernames so that people carry over; how
Keycloak hands the app a login is not decided.

## Authorization
Authorization is a convenience, not a protection: it decides what is relevant to show. Sensitive data is protected by
clearance and database grants, not by authorization. A person sees what they own and what is shared with them
(`src/chatddx/identity/identity.py:sees`), as long as it isn't deleted (`src/chatddx/catalog/model.py:About.shows`).
Which kinds each role sees is to come first (Z1, agents/wip-identity.md); no code reads roles yet.

## Known gaps
- Nothing checks `Role.ADMIN`: anyone with database access can add people.
- Logins aren't rate-limited.
- Expired sessions are removed only by `People.purge_sessions()`, and nothing calls it on a schedule.
- Setting a password doesn't end the person's sessions.
```

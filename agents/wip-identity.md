# Identity: work in progress

Material for `docs/identity.md`, which holds "What holds now" as AGENT suggestions, one per section, for the user to
adopt (see "What `docs/` expects of `docs/identity.md`").
"Decided" means the user said so; "Take" is the agent's recommendation and still open.

`identity` is the *declarative* layer of the "person-scoped cake". Consult docs/chatddx.md's "The person-scoped cake"
before adding functionality.

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
- Who owns, collaborates on and sees what is `src/chatddx/identity/identity.py:owns`, `collaborates` and `sees`, over
  an `Owned`: anything with an owner, collaborators and a deleted flag, which the catalog's `About` is. Only what is
  live counts. What a person owns is their runs, what they may edit, and the expectations they are scored against
  (`docs/bench.md`, "What a person is scored against"); what they collaborate on, of those, is what they could take;
  and they see both. What they own and deleted they `restores`: it is listed apart, found by id when asked for, and
  theirs to say more of by restoring it. A person `shares` only with others.
- Of what a person sees, their own comes first: `src/chatddx/identity/identity.py:preferred`, which the bench uses to
  find a thread or family by name and to name a digest's thread.
- Z1's map from role to kinds goes beside `sees`. `identity` holds both, as data and functions with no store access.
- The bench applies them to what is in the store and the World (`docs/bench.md`, "What a person sees").

## Done
- Migrations `0007-t0-identity.sql` (person with login, roles and active; credential; session),
  `0008-t1-identity.sql` (grants) and `0009-t2-identity.sql` (login pattern, role names, session expiry), all in
  `src/chatddx/store/migrations/` (`docs/migrations.md`).
- `src/chatddx/identity/identity.py`: `Role`, `Person`, argon2id hashing (`argon2-cffi`), session tokens, `Owned`,
  `owns`, `collaborates`, `sees`, `restores`, `shares` and `preferred`, exported by `chatddx.identity`.
- The person-scoped rules moved down from the catalog and the bench (see "The person-scoped cake").
- `src/chatddx/store/people.py`: `People`, the store API for people, passwords and sessions.
- `chatddx person add` / `chatddx person password` (`src/chatddx/cli.py`).
- Tests: `src/chatddx/store/test/test_identity.py`, `test_cli.py`, and `src/chatddx/identity/test/test_identity.py`.
- `DB_OWNER` renamed to `DB_ADMIN`, freeing "owner" for the catalog.

## The person-scoped cake
`docs/chatddx.md`, "The person-scoped cake": pure rules go to `identity`, procedures over the catalog's rows to
`catalog`, operations across the project to `bench`. A survey of `src/chatddx/catalog/` for person-scoped rules that
need no store found these, and moved them:

| Was, in the catalog | Is, in identity |
| --- | --- |
| `model.py:About.shows(person)`: live, and owned or shared | `sees(person, about)` |
| `model.py:About.owned_by(person)`: live, and owned | `owns(person, about)` |
| `threads.py:expectations_shared`'s `a.shows(person) and a.owner != person` | `collaborates(person, about)` |

`identity.sees(person, owner, collaborators)` ignored deletion; the catalog added it. Now identity's rules include it,
since what a person is shown is the rule and it needs no store. `Owned` is a `Protocol` so that identity imports
nothing of the catalog's: `About`, a run's and a score's included, fits it as it is.

The catalog keeps the procedures that apply them to its rows: `threads.visible`, `threads.find` with an owner,
`threads.expectation_choices` and `expectations_shared` (and so `expectations_for`, `expectation_for` and
`check_expectation`), and `families.visible`.

Looked at and left where they are:
- **`threads.py:picked`** is pure, but it decides among a case's expectation threads, not who: nothing in it is about
  a person. Moving it would bring cases and threads into identity.
- **The default owner**, `by if owner is None else owner` in `src/chatddx/store/catalog.py:Catalog.create` and
  `Catalog.adopt` ("whoever creates it owns it unless they name someone else"), is a pure person rule, but one line in
  the store's writes; a function for it would be ceremony. Take: move it when a second rule about owning on write
  (Z1's kinds a role may write, say) gives identity a reason to hold write rules.
- **Pure but not about people**: `variants.py`, `titles.py:describe*`, `model.py:language_tag`, `check_label`,
  `latest`, `Entry`'s shape and `About.of`'s folding. They belong to the catalog, by subject rather than by
  resources.
- **`threads.py:check_expectation`** (a person owns at most one live expectation per case and schema) reads rows.

The bench, a layer up, held pure person rules inline. They moved too, its messages staying in the bench:

| Was, in the bench | Is, in identity |
| --- | --- |
| `seen.py:Seen.thread_by_id`, `Seen.deleted`: `about.deleted and about.owner == person` | `restores(person, about)` |
| `saying.py:say`: the owner alone says, deleted or not, `about.owner == person` | `owns(person, about) or restores(person, about)` |
| `saying.py:say`: `person in sharing` refused | `not shares(person, sharing)` |
| `taking.py:take_from`: "yours already", `about.owner == person` of a thread it sees | `owns(person, about)` |
| `taking.py:take`: shared by the owner named, `a.owner == by.id` of a live thread | `owns(by.id, a)` |
| `seen.py:Seen.owner`: `""` for the person's own, deleted or not | `owns(person, about) or restores(person, about)` |

From a person's side, `owns`, `collaborates` and `restores` split what is said of a subject: live and theirs, live
and shared with them, and deleted and theirs; `sees` is the first two. Deleted and shared with them is nothing of
theirs.

Still inline, above the bench or beside it, comparing a person with an owner or collaborators:
`src/chatddx/repl/listing.py`, `src/chatddx/portal/threads.py`, `portal/configurations.py` and `portal/runs.py`,
which list the person's own first or apart, by login or id; and `src/chatddx/curation/write.py` and
`curation/repair.py`, for the archive's own, a user's forks, and withdrawing a user from what is shared with them,
deleted or not.

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
  (`docs/bench.md`, "What a person sees").

Take, for when Keycloak arrives: Keycloak (or a proxy in front, such as oauth2-proxy) authenticates and the app maps
its username onto `person.login`, which is why logins are lowercase like Keycloak's. Password login can stay as the
development path. Roles could then come from Keycloak's realm roles instead of the column; not decided.

## Open
- **Web framework.** Decided for the API: FastAPI (`agents/wip-api.md` at 100a078, "A2. The framework"). The API
  signs people in with sessions, by bearer token or by a `__Host-` cookie that is `HttpOnly`, `Secure` and
  `SameSite=Lax`, and checks that a cookie's unsafe requests come from the site's own pages
  (`src/chatddx/api/people.py`; `docs/api.md`, "Signing in"). The portal shares that cookie, as one app with the API (`agents/wip-portal.md`, "P3b, concretely"). Open: login
  rate limiting.
- **Z1's map from role to kinds** isn't written; it needs the portal's views to mean anything.
- **Who may administer people.** `Role.ADMIN` exists, but nothing checks it; the CLI connects as `DB_USER`, so anyone
  with database access can add people.
- **Expired sessions** are only removed by `People.purge_sessions()`; nothing calls it on a schedule.

## What `docs/` expects of `docs/identity.md`
These docs link to `docs/identity.md`, and its suggestions cover what each expects. Once they are adopted,
`src/chatddx/identity/test/test_identity.py` can be marked `solidified`, and this file keeps only what is open:
- `docs/chatddx.md` (glossary, "Sensitive"): people's names aren't sensitive;
- `docs/factors.md`: the roles are the principal authors; people, roles, authentication and authorization are
  identity's;
- `docs/store.md` (introduction, "People"): identity's schema, and its people, passwords and sessions;
- `docs/store-api.md` (introduction, `People`): the `identity` schema;
- `docs/catalog.md` (introduction, "Owners"): people by their identity, and "Authorization": what a person sees is
  what is relevant to show, not who may read it;
- `docs/catalog-api.md` ("Conventions"): people are ids of `identity.person`.

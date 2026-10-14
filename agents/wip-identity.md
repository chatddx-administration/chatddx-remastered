# Identity: what is open

Identity is solidified: what holds is in `docs/identity.md` and `docs/identity-api.md` (drafted as
`agents/identity-api.md`), and its tests are marked `solidified`. This file keeps what is open, with the agent's takes.
"Decided" means the user said so; "Take" is the agent's recommendation and still open.

`identity` is the *declarative* layer of person-scoped functionality, providing rules as pure functions. The `bench`
being the *operational* layer.

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

## What could move to identity
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

# Identity API

Reference for the `chatddx.identity` package: each name's signature, what it returns and what it raises. What
identity is and why it is shaped this way is in `docs/identity.md`. The store's side, `People` and the `identity`
database schema, is in `docs/store-api.md`.

Paths are relative to `src/chatddx/identity/` unless they start with `src/` or `docs/`.

## Contents
- [Package](#package)
- [People and roles](#people-and-roles): `LOGIN`, `Role`, `Person`
- [What a person is shown](#what-a-person-is-shown): `Owned`, `owns`, `collaborates`, `sees`, `preferred`
- [Passwords and sessions](#passwords-and-sessions): `hash_password`, `verify_password`, `needs_rehash`, `new_token`,
  `token_digest`
- [Tests](#tests)

## Package
`chatddx.identity` re-exports everything `identity.py` holds: `LOGIN`, `Owned`, `Person`, `Role`, `collaborates`,
`hash_password`, `needs_rehash`, `new_token`, `owns`, `preferred`, `sees`, `token_digest` and `verify_password`.

The package holds data and pure functions: it reads no store, imports no chatddx package, and no third-party package
but pydantic and `argon2-cffi`. The store keeps people, passwords and sessions (`src/chatddx/store/people.py:People`),
and the bench applies the rules of what a person is shown (`docs/bench-api.md`, `Seen`).

## People and roles

### `LOGIN`
`^[a-z0-9][a-z0-9._@-]*$`: a login is lowercase, as Keycloak keeps usernames, so that people carry over.
`src/chatddx/store/migrations/0009-t2-identity.sql` repeats it.

### `class Role(StrEnum)`
`ADMIN`, `CLINICIAN`, `DEVELOPER`, `OPS` and `RESEARCHER`, valued as their lowercase names.
`src/chatddx/store/migrations/0009-t2-identity.sql` repeats them, and
`src/chatddx/store/test/test_identity.py:test_roles_match_the_database_check` keeps the two the same.

### `class Person`
A frozen pydantic model of a row of `identity.person`.
- `id: int`: what the rest of the store refers to.
- `login: str`: what the person signs in with; matches `LOGIN`.
- `name: str`: for display.
- `roles: frozenset[Role] = frozenset()`
- `active: bool = True`: whether the person may sign in.

Raises `ValueError("invalid login '<login>'")`, wrapped in `ValidationError`.

## What a person is shown
What a person is shown is a convenience, not a protection (`docs/identity.md`, "Authorization"). Each rule takes the
person by id.

### `class Owned(Protocol)`
Anything with an owner, collaborators and a deleted flag, read-only. `src/chatddx/catalog/model.py:About` is one, said
of a thread, a family, a run or a score.
- `owner: int | None`
- `collaborators: Collection[int]`
- `deleted: bool`

### `owns(person: int, owned: Owned) -> bool`
Whether it is live and the person is its owner.

### `collaborates(person: int, owned: Owned) -> bool`
Whether it is live, shared with the person, and not their own.

### `sees(person: int, owned: Owned) -> bool`
Whether the person `owns` it or `collaborates` on it.

### `preferred[T](person: int, seen: Iterable[tuple[T, int | None]]) -> list[T]`
Of `seen`, each thing with its owner, those the person owns, when there are any; else all of them. Order is kept.

## Passwords and sessions
Passwords are hashed with argon2id, `argon2-cffi`'s `PasswordHasher` with its default parameters.

### `hash_password(password: str) -> str`
An argon2id hash of the password.

### `verify_password(hash: str | None, password: str) -> bool`
Whether the password is the one hashed. A malformed hash gives `False`.
- `hash`: `None` for a login nobody has, or one without a password; it is verified against a stand-in hash, so that
  it takes as long to refuse as a wrong password, and gives `False`.

### `needs_rehash(hash: str) -> bool`
Whether the hash was made under other parameters than `hash_password` uses now.

### `new_token() -> str`
A session token: 32 random bytes, URL-safe.

### `token_digest(token: str) -> str`
The token's SHA-256, in hex: what the store keeps of a session, in place of the token.

## Tests
- `src/chatddx/identity/test/test_identity.py`: who owns, collaborates on and sees what, nothing deleted, and their own
  first.
- `src/chatddx/store/test/test_identity.py`: people, passwords and sessions as the store keeps them
  (`docs/store-api.md`, "people.py").

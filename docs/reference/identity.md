# `chatddx.identity`

Written by `chatddx reference` from `src/chatddx/identity/`: each public name's signature and what it raises.

## `collaborates(person: int, owned: Owned) -> bool`
`src/chatddx/identity/identity.py:collaborates`

## `hash_password(password: str) -> str`
`src/chatddx/identity/identity.py:hash_password`

## `LOGIN = re.compile(r"^[a-z0-9][a-z0-9._@-]*$")`
`src/chatddx/identity/identity.py:LOGIN`

## `needs_rehash(hash: str) -> bool`
`src/chatddx/identity/identity.py:needs_rehash`

## `new_token() -> str`
`src/chatddx/identity/identity.py:new_token`

## `class Owned(Protocol)`
`src/chatddx/identity/identity.py:Owned`
- `owner: int | None`, a property
- `collaborators: Collection[int]`, a property
- `deleted: bool`, a property

## `owns(person: int, owned: Owned) -> bool`
`src/chatddx/identity/identity.py:owns`

## `class Person(BaseModel)`
`src/chatddx/identity/identity.py:Person`
- `model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")`
- `id: int`
- `login: str`
- `name: str`
- `roles: frozenset[Role] = frozenset()`
- `active: bool = True`
- raises `ValueError("invalid login <login!r>")` in a `ValidationError`

## `preferred[T](person: int, seen: Iterable[tuple[T, int | None]]) -> list[T]`
`src/chatddx/identity/identity.py:preferred`

## `class Role(StrEnum)`
`src/chatddx/identity/identity.py:Role`
- `ADMIN = "admin"`
- `CLINICIAN = "clinician"`
- `DEVELOPER = "developer"`
- `OPS = "ops"`
- `RESEARCHER = "researcher"`

## `sees(person: int, owned: Owned) -> bool`
`src/chatddx/identity/identity.py:sees`

## `token_digest(token: str) -> str`
`src/chatddx/identity/identity.py:token_digest`

## `verify_password(hash: str | None, password: str) -> bool`
`src/chatddx/identity/identity.py:verify_password`

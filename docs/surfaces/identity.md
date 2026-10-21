# `chatddx.identity`

Written by `chatddx stamp` from `src/chatddx/identity/`; how to read it is in [docs/surfaces.md](../surfaces.md).

## `collaborates`
`src/chatddx/identity/identity.py:collaborates`

* `person: int`
* `owned: Owned`
* ∟`bool`

## `hash_password`
`src/chatddx/identity/identity.py:hash_password`

* `password: str`
* ∟`str`

## `LOGIN`
`src/chatddx/identity/identity.py:LOGIN`

`LOGIN = re.compile(r"^[a-z0-9][a-z0-9._@-]*$")`

## `needs_rehash`
`src/chatddx/identity/identity.py:needs_rehash`

* `hash: str`
* ∟`bool`

## `new_token`
`src/chatddx/identity/identity.py:new_token`

* ∟`str`

## `Owned` `(Protocol)`
`src/chatddx/identity/identity.py:Owned`

## `Owned.collaborators` `@property`
`src/chatddx/identity/identity.py:Owned.collaborators`

* ∟`Collection[int]`

## `Owned.deleted` `@property`
`src/chatddx/identity/identity.py:Owned.deleted`

* ∟`bool`

## `Owned.owner` `@property`
`src/chatddx/identity/identity.py:Owned.owner`

* ∟`int | None`

## `owns`
`src/chatddx/identity/identity.py:owns`

* `person: int`
* `owned: Owned`
* ∟`bool`

## `Person` `(BaseModel)`
`src/chatddx/identity/identity.py:Person`

* `model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")`
* `id: int`
* `login: str`
* `name: str`
* `roles: frozenset[Role] = frozenset()`
* `active: bool = True`

Raises:
1. `ValueError`: `"invalid login {login!r}"` (through `Person._login`, in a `ValidationError`)

## `preferred` `[T]`
`src/chatddx/identity/identity.py:preferred`

* `person: int`
* `seen: Iterable[tuple[T, int | None]]`
* ∟`list[T]`

## `Role` `(StrEnum)`
`src/chatddx/identity/identity.py:Role`

* `ADMIN = "admin"`
* `CLINICIAN = "clinician"`
* `DEVELOPER = "developer"`
* `OPS = "ops"`
* `RESEARCHER = "researcher"`

## `sees`
`src/chatddx/identity/identity.py:sees`

* `person: int`
* `owned: Owned`
* ∟`bool`

## `token_digest`
`src/chatddx/identity/identity.py:token_digest`

* `token: str`
* ∟`str`

## `verify_password`
`src/chatddx/identity/identity.py:verify_password`

* `hash: str | None`
* `password: str`
* ∟`bool`

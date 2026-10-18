# `chatddx.identity`

Written by `chatddx reference` from `src/chatddx/identity/`: each public name, sorted, with its parameters or fields,
```
REFERENCE: REPLACE
replace the line below with these
---
`∟` its return type, what it raises and what it finds.
```
`∟` its return type, and what it raises.

- `*`: the parameters after it are keyword-only; `/`: those before it are positional-only. A function a
  class binds as an attribute is its method: its first parameter, the instance, is left out.
- Raises: the function's own `raise` statements and its private helpers' (through `<helper>`), in the order
  the code reaches them, each once. What the public functions it calls raise is in their own entries.
- A message is quoted, with the values of the code that raises it as `{expr}`; an argument that isn't text is
  as written, and from `<exception>` when it is the exception caught.
```
REFERENCE: ADD
add these lines here
---
- Finds: each `Finding` it makes, as `code`: message, followed as Raises are; a warning unless it says info.
```

## collaborates
`src/chatddx/identity/identity.py:collaborates`

* `person: int`
* `owned: Owned`
* ∟`bool`

## hash_password
`src/chatddx/identity/identity.py:hash_password`

* `password: str`
* ∟`str`

## LOGIN
`src/chatddx/identity/identity.py:LOGIN`

* `LOGIN = re.compile(r"^[a-z0-9][a-z0-9._@-]*$")`

## needs_rehash
`src/chatddx/identity/identity.py:needs_rehash`

* `hash: str`
* ∟`bool`

## new_token
`src/chatddx/identity/identity.py:new_token`

* ∟`str`

## Owned `(Protocol)`
`src/chatddx/identity/identity.py:Owned`

## Owned.collaborators `@property`
`src/chatddx/identity/identity.py:Owned.collaborators`

* ∟`Collection[int]`

## Owned.deleted `@property`
`src/chatddx/identity/identity.py:Owned.deleted`

* ∟`bool`

## Owned.owner `@property`
`src/chatddx/identity/identity.py:Owned.owner`

* ∟`int | None`

## owns
`src/chatddx/identity/identity.py:owns`

* `person: int`
* `owned: Owned`
* ∟`bool`

## Person `(BaseModel)`
`src/chatddx/identity/identity.py:Person`

* `model_config: ClassVar[ConfigDict] = ConfigDict(frozen=True, extra="forbid")`
* `id: int`
* `login: str`
* `name: str`
* `roles: frozenset[Role] = frozenset()`
* `active: bool = True`

Raises:

1. `ValueError`: "invalid login {login!r}" (through `Person._login`, in a `ValidationError`)

## preferred `[T]`
`src/chatddx/identity/identity.py:preferred`

* `person: int`
* `seen: Iterable[tuple[T, int | None]]`
* ∟`list[T]`

## Role `(StrEnum)`
`src/chatddx/identity/identity.py:Role`

* `ADMIN = "admin"`
* `CLINICIAN = "clinician"`
* `DEVELOPER = "developer"`
* `OPS = "ops"`
* `RESEARCHER = "researcher"`

## sees
`src/chatddx/identity/identity.py:sees`

* `person: int`
* `owned: Owned`
* ∟`bool`

## token_digest
`src/chatddx/identity/identity.py:token_digest`

* `token: str`
* ∟`str`

## verify_password
`src/chatddx/identity/identity.py:verify_password`

* `hash: str | None`
* `password: str`
* ∟`bool`

# `identity`

Written by `chatddx-dev index` from `[parts.identity]`'s code in `settings.toml`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it, a language's after another's:

Python:

```
## `<name>` `@<decorator>` `[<type parameters>]` `(<bases>)`
`<file>:<qualified name>`

* `<parameter or field>: <type> = <default>`
* ∟`<return type>`

Raises:
1. `<exception>`: `<arguments>` (from `<exception caught>`, through `<private helper>`, in a `ValidationError`)

Finds:
1. `<code>`: `<message>` (`<level>`, from `<exception caught>`, through `<private helper>`)
```

- A constant or a type alias is its definition instead of bullets; a class and its `__init__` leave out ∟, and a method its instance; `*`: the parameters after it are keyword-only, `/`: those before it positional-only.
- Raises and Finds are the function's own and its private helpers', in the order the code reaches them, each once, a `Whoops` left out; what a public function it calls raises is in that function's entry.
- Text is quoted, a value in it as `{<expression>}`, and an argument that isn't text is as written; a finding is a warning unless it gives its level.

- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

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

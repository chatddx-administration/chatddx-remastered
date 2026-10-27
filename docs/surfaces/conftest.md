# `chatddx.conftest`

Written by `chatddx stamp write` from `src/chatddx/conftest.py`, an entry for each public name, sorted alphabetically whatever its case, so that a class's members follow it:

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

## `admin` `@pytest.fixture`
`src/chatddx/conftest.py:admin`

* `db: str`
* ∟`Iterator[Connection]`

## `autocommit` `@pytest.fixture`
`src/chatddx/conftest.py:autocommit`

* ∟`bool`

## `cheap_hashing` `@pytest.fixture(scope="session", autouse=True)`
`src/chatddx/conftest.py:cheap_hashing`

* ∟`Iterator[None]`

## `conn` `@pytest.fixture`
`src/chatddx/conftest.py:conn`

* `db: str`
* `autocommit: bool`
* ∟`Iterator[Connection]`

## `copies` `@pytest.fixture(scope="session")`
`src/chatddx/conftest.py:copies`

* ∟`Iterator[Copies]`

## `curated` `@pytest.fixture(scope="session")`
`src/chatddx/conftest.py:curated`

* `copies: Copies`
* `migrated: str`
* ∟`Iterator[str]`

## `db` `@pytest.fixture`
`src/chatddx/conftest.py:db`

* `copies: Copies`
* `template: str`
* ∟`Iterator[str]`

## `described` `@pytest.fixture(scope="session")`
`src/chatddx/conftest.py:described`

* ∟`dict[str, Any]`

## `empty` `@pytest.fixture`
`src/chatddx/conftest.py:empty`

* `empty_db: str`
* ∟`Iterator[Connection]`

## `empty_db` `@pytest.fixture`
`src/chatddx/conftest.py:empty_db`

* `copies: Copies`
* ∟`Iterator[str]`

## `fake` `@pytest.fixture`
`src/chatddx/conftest.py:fake`

* `world: Inventory`
* `conn: Connection`
* ∟`Iterator[None]`

## `migrated` `@pytest.fixture(scope="session")`
`src/chatddx/conftest.py:migrated`

* `copies: Copies`
* ∟`Iterator[str]`

## `plan` `@pytest.fixture(scope="module")`
`src/chatddx/conftest.py:plan`

* ∟`Plan`

## `ran` `@pytest.fixture(scope="session")`
`src/chatddx/conftest.py:ran`

* `copies: Copies`
* `curated: str`
* ∟`Iterator[str]`

## `sampled` `@pytest.fixture(scope="session")`
`src/chatddx/conftest.py:sampled`

* `copies: Copies`
* `migrated: str`
* ∟`Iterator[Loaded]`

## `shipped_test_tools` `@pytest.fixture(scope="session", autouse=True)`
`src/chatddx/conftest.py:shipped_test_tools`

* ∟`Iterator[None]`

## `template` `@pytest.fixture`
`src/chatddx/conftest.py:template`

* `request: pytest.FixtureRequest`
* ∟`str`

## `unsynced_commits` `@pytest.fixture(scope="session", autouse=True)`
`src/chatddx/conftest.py:unsynced_commits`

* ∟`Iterator[None]`

## `world` `@pytest.fixture`
`src/chatddx/conftest.py:world`

* ∟`Inventory`

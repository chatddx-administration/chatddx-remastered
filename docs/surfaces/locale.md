# `chatddx.locale`

Written by `chatddx stamp write` from `src/chatddx/locale/`; how to read it is in [docs/surfaces.md](../surfaces.md).

## `check`
`src/chatddx/locale/locale.py:check`

* `baseline: bool`
* ∟`None`

Raises:
1. `SystemExit`: `"locale: {shown} behind the code: run chatddx locale write"`
2. `SystemExit`: `1`

## `gettext`
`src/chatddx/locale/locale.py:gettext`

* `message: str`
* ∟`str`

## `Locale` `@dataclass(frozen=True)`
`src/chatddx/locale/locale.py:Locale`

* `tag: str`
* `translations: NullTranslations`
* `islands: dict[str, str | list[str]] = field(default_factory=dict)`

## `Locales`
`src/chatddx/locale/locale.py:Locales`

* `by_tag: dict[str, Locale]`

## `Locales.__init__`
`src/chatddx/locale/locale.py:Locales.__init__`

* `catalogs: Path = _CATALOGS`

Raises:
1. `ValueError`: `"{path}: {e}"` (from `PoFileError`, through `_locale`)
2. `ValueError`: `"{path}: {'; '.join(wrong)}"` (through `_locale`)

## `Locales.negotiate`
`src/chatddx/locale/locale.py:Locales.negotiate`

* `accept_language: str | None`
* ∟`Locale`

## `N_`
`src/chatddx/locale/locale.py:N_`

* `message: str`
* ∟`str`

## `ngettext`
`src/chatddx/locale/locale.py:ngettext`

* `singular: str`
* `plural: str`
* `n: int`
* ∟`str`

## `npgettext`
`src/chatddx/locale/locale.py:npgettext`

* `context: str`
* `singular: str`
* `plural: str`
* `n: int`
* ∟`str`

## `pgettext`
`src/chatddx/locale/locale.py:pgettext`

* `context: str`
* `message: str`
* ∟`str`

## `pgettext_noop`
`src/chatddx/locale/locale.py:pgettext_noop`

* `_context: str`
* `message: str`
* ∟`str`

## `Proof` `@dataclass(frozen=True)`
`src/chatddx/locale/locale.py:Proof`

* `path: Path`
* `current: str | None`
* `written: str`
* `untranslated: int`
* `fuzzy: int`

## `Proof.behind` `@property`
`src/chatddx/locale/locale.py:Proof.behind`

* ∟`bool`

## `proofs`
`src/chatddx/locale/locale.py:proofs`

* `tags: Iterable[str] = ()`
* `root: Path = settings.PROJECT_ROOT`
* `catalogs: Path = _CATALOGS`
* ∟`list[Proof]`

Raises:
1. `ValueError`: `"{where}:{lineno}: {said!r} is said both counted and not, which gettext holds as one message: give one a context"` (through `_extracted`)

## `Saying`
`src/chatddx/locale/locale.py:Saying`

* `app: ASGIApp`

## `saying` `@contextmanager`
`src/chatddx/locale/locale.py:saying`

* `locale: Locale`
* ∟`Generator[None]`

## `Saying.__call__`
`src/chatddx/locale/locale.py:Saying.__call__`

* `scope: Scope`
* `receive: Receive`
* `send: Send`
* ∟`None`

## `Saying.__init__`
`src/chatddx/locale/locale.py:Saying.__init__`

* `app: ASGIApp`

## `tr`
`src/chatddx/locale/locale.py:tr`

* `message: str`
* `/`
* `**values: object`
* ∟`str`

## `whoops`
`src/chatddx/locale/locale.py:whoops`

* `message: str`
* ∟`str`

## `write`
`src/chatddx/locale/locale.py:write`

* `tags: Iterable[str]`
* ∟`None`

# Comments in `chatddx.locale`

Written by `chatddx stamp write` from the comments in `src/chatddx/locale/`, each under its file and the name it is in or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/locale/locale.py:_extracted`

```
# Accommodating for Babel, whose type for an extraction method's results
# leaves out the name of the function called, which it reads.
```

## `src/chatddx/locale/locale.py:_SAYING`

```
# Accommodating for Jinja, whose macros imported without context see nothing of the page
# rendering them: a page is said in the locale set around its rendering.
```

## `src/chatddx/locale/locale.py:_shared`

```
# Policy: the catalog put in an island's page holds only what the islands say, and the
# whoopses the API may answer them with.
```

## `src/chatddx/locale/locale.py:_SOURCES`

```
# Policy: what a whoops tells the person is said in their locale wherever it is raised;
# what it has them pass on to developers and ops isn't.
```

## `src/chatddx/locale/locale.py:proofs`

```
# Accommodating for Babel, which matches a new message to an untranslated plural one as
# if it were translated: what holds no translation comes anew from the code.
```

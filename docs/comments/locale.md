# Comments in `chatddx.locale`

Written by `chatddx stamp write` from the comments in `src/chatddx/locale/`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

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

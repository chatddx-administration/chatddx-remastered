# Comments in `identity`

Written by `chatddx-dev index` from the comments in `[parts.identity]`'s code in `settings.toml`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/identity/identity.py:_dummy_hash`

```
# Optimization: hashed when first needed rather than at import, which every process that
# imports the catalog would pay for.
```

## `src/chatddx/identity/identity.py:LOGIN`

```
# Accommodating for Keycloak, which stores usernames lowercase, so logins carry over
# unchanged.
# Duplication: src/chatddx/store/migrations/0009-t2-identity.sql repeats this pattern
# and the role names.
```

## `src/chatddx/identity/identity.py:Owned`

```
# Dependency: src/chatddx/catalog/model.py:About is one, said of a thread, family, run
# or score.
```

# Comments in `chatddx.identity`

Written by `chatddx stamp write` from the comments in `src/chatddx/identity/`, each under its file and the name it is in or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/identity/identity.py:_dummy_hash`

```
# Hashed when first needed rather than at import, which every process that imports the
# catalog would pay for.
```

## `src/chatddx/identity/identity.py:LOGIN`

```
# Lowercase, as Keycloak stores usernames, so logins carry over unchanged.
# src/chatddx/store/migrations/0009-t2-identity.sql repeats this pattern and the role names.
```

## `src/chatddx/identity/identity.py:Owned`

```
# src/chatddx/catalog/model.py:About is one, said of a thread, family, run or score.
```

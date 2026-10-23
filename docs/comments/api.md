# Comments in `chatddx.api`

Written by `chatddx stamp write` from the comments in `src/chatddx/api/`, each under its file and the name it is in or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/api/app.py:_raw`

```
# Compromise: Raw, though it may quote sensitive content, until edges hold that back.
```

## `src/chatddx/api/listening.py:_AGAIN`

```
# Policy: how long, in seconds, the listener waits after losing its connection, and at
# most for anything to happen.
```

## `src/chatddx/api/listening.py:BEHIND`

```
# Policy: a stream this many messages behind drops what it holds and reads the ledger
# again.
```

## `src/chatddx/api/state.py:refused`

```
# Policy: what may be missing of what a request's body or query names is a 422, where
# what its path names is a 404.
```

## `src/chatddx/api/telling.py:KEEP_ALIVE`

```
# Accommodating for proxies, which cut a quiet stream: comment lines, which event
# readers skip, keep it going.
```

## `src/chatddx/api/telling.py:told`

```
# Policy: it listens before it reads, so that no row lands unheard in between.
```

## `src/chatddx/api/test/helpers.py:joined`

```
# Policy: the owner's queue stays paused until the stream has said its first row: by
# then it listens.
```

## `src/chatddx/api/test/helpers.py:UNDER_WAY`

```
# Policy: a fake this slow keeps a run's job under way while a stream asked for at once
# joins it: one asked for after it has ended is told the ledger's rows alone.
```

## `src/chatddx/api/test/helpers.py:world_served`

```
# Accommodating for pytest, as src/chatddx/test/helpers.py:curated_template does.
```

## `src/chatddx/api/test/test_variations.py:test_a_look_s_queries_don_t_grow_with_its_cases.counting`

```
# Accommodating for the fixtures, which make the next test's database meanwhile:
# only the look's database's queries count.
```

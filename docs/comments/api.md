# Comments in `chatddx.api`

Written by `chatddx stamp write` from the comments in `src/chatddx/api/`, each under its file and the name it is in or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/api/app.py:_raw`

```
# Compromise: Raw, though it may quote sensitive content, until edges hold that back.
```

## `src/chatddx/api/events.py:said_of`

```
# What a run's events tell that its rows don't, as they happen.
```

## `src/chatddx/api/listening.py:AGAIN`

```
# How long, in seconds, the listener waits after losing its connection, and at most for
# anything to happen.
```

## `src/chatddx/api/listening.py:BEHIND`

```
# A stream this many messages behind drops what it holds and reads the ledger again.
```

## `src/chatddx/api/state.py:refused`

```
# `named`: what may be missing of what a request's body or query names, a 422 where
# what its path names is a 404.
```

## `src/chatddx/api/telling.py:KEEP_ALIVE`

```
# Comment lines, which event readers skip, keep a proxy from cutting a quiet stream.
```

## `src/chatddx/api/telling.py:Telling.rows`

```
# A row's events end with the one that carries its id.
```

## `src/chatddx/api/telling.py:told`

```
# It listens before it reads, so that no row lands unheard in between.
```

## `src/chatddx/api/test/helpers.py:joined`

```
# What a stream is told from before its job is claimed, with the owner's queue paused
# until the stream has said its first row: by then it listens.
```

## `src/chatddx/api/test/helpers.py:UNDER_WAY`

```
# A fake this slow keeps a run's job under way while a stream asked for at once joins
# it: one asked for after it has ended is told the ledger's rows alone.
```

## `src/chatddx/api/test/helpers.py:world_served`

```
# Accommodating for pytest, as src/chatddx/test/helpers.py:curated_template does.
```

## `src/chatddx/api/test/test_variations.py:test_a_look_s_queries_don_t_grow_with_its_cases.counting`

```
# Only the look's: the fixtures make the next test's database meanwhile.
```

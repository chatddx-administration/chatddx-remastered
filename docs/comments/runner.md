# Comments in `chatddx.runner`

Written by `chatddx stamp write` from the comments in `src/chatddx/runner/`, each under its file and the name it is in or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/runner/outcome.py:_streamed`

```
# A stream cut short ends before its usage, but its choice holds the token ids it streamed.
```

## `src/chatddx/runner/rounds.py:converse`

```
# The round under way is always the last of turns, replaced whole as it grows, so an
# interrupt between two statements finds it as far as it got.
```

## `src/chatddx/runner/rounds.py:Toolbox.run`

```
# noqa: BLE001
```

## `src/chatddx/runner/run.py:_resumed`

```
# A run the request started and the worker sends is resumed with nothing written yet.
```

## `src/chatddx/runner/run.py:Running.send`

```
# Its own halt, so that a worker's failure halts this run's calls and not the caller's.
```

## `src/chatddx/runner/test/helpers.py:_GoingAway`

```
# vLLM streams over HTTP/1.1 in chunks, the fake over HTTP/1.0 until it closes. An engine that
# goes away mid-stream ends the stream either way.
```

## `src/chatddx/runner/test/helpers.py:DELAY`

```
# Slow enough that calls sent together overlap: a fake answer is some 40 tokens.
```

## `src/chatddx/runner/test/test_run.py:elsewhere`

```
# Runs `f` on a thread of its own, as a server's request thread would halt a run.
```

## `src/chatddx/runner/test/test_score.py:scoring_of`

```
# Compromise: By weights, so that a judge a test copies finds its original's engine.
```

## `src/chatddx/runner/wire.py:Stream.__init__`

```
# A socket of its own on the connection, so that another thread can shut it down
# without racing the response's close for its descriptor.
```

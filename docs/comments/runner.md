# Comments in `chatddx.runner`

Written by `chatddx stamp write` from the comments in `src/chatddx/runner/`, each under its file and the name it is in or right above; a stamp reads as in [docs/surfaces.md](../surfaces.md).

## `src/chatddx/runner/outcome.py:_streamed`

```
# Accommodating for a stream cut short, which ends before its usage, though its choice
# holds the token ids it streamed.
```

## `src/chatddx/runner/rounds.py:converse`

```
# Policy: the round under way is always the last of turns, replaced whole as it
# grows, so an interrupt between two statements finds it as far as it got.
```

## `src/chatddx/runner/rounds.py:Toolbox.run`

```
# noqa: BLE001
```

## `src/chatddx/runner/run.py:_resumed`

```
# Policy: a run the request started and the worker sends is resumed with nothing written
# yet.
```

## `src/chatddx/runner/run.py:Running.send`

```
# Policy: its own halt, so that a worker's failure halts this run's calls and
# not the caller's.
```

## `src/chatddx/runner/test/helpers.py:_GoingAway`

```
# Accommodating for vLLM, which streams over HTTP/1.1 in chunks, and the fake, over
# HTTP/1.0 until it closes: an engine that goes away mid-stream ends the stream either
# way.
```

## `src/chatddx/runner/test/helpers.py:DELAY`

```
# Policy: slow enough that calls sent together overlap: a fake answer is some 40 tokens.
```

## `src/chatddx/runner/test/test_score.py:scoring_of`

```
# Compromise: By weights, so that a judge a test copies finds its original's engine.
```

## `src/chatddx/runner/wire.py:Stream.__init__`

```
# Policy: a socket of its own on the connection, so that another thread can shut
# it down without racing the response's close for its descriptor.
```

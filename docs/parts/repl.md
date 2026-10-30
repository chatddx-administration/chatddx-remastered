# The repl

`chatddx repl LOGIN` is a shell over a World for one person: it holds a configuration to try, sends it to an endpoint,
scores what comes back and reads back the runs. It is an edge: what it reads and writes goes through the person's bench,
`src/chatddx/bench/bench.py:Bench`, as the API's and the portal's do.

## How it works

- `src/chatddx/cli.py:_repl` finds the person and opens their bench over the World's inventory: `--world`, or
  `CHATDDX_WORLD`.
- `src/chatddx/repl/loop.py:loop` reads a line at a time with readline, which keeps the history in `--history` and
  tab-completes verbs and names.
- `src/chatddx/repl/shell.py:Repl` holds what lasts between lines, and the prompt says it: the variation in use, the
  handle a hand-written configuration runs under, and the seed, as in `alice plan+reasoning=off #7>`. Only `save` keeps
  a variation.
- `run` sends from the repl's own process, not through a worker, and scores the run with each scorer that applies.
  Ctrl-C stops the sending, and what was sent is still written down and scored; Ctrl-C again stops the scoring, and
  `score` scores what is left.
- The repl shows sensitive content at its terminal: `show case` prints the vignette, `run` and `replay` the answers.
  What it sends passes `src/chatddx/runner/gate.py:bar`, which refuses an endpoint that isn't cleared for a case's
  source.
- A command refused says why, and the shell goes on. From a stdin that isn't a terminal, each line is echoed and the
  first refusal ends the shell with status 1, so the examples below run as they are.

## Commands

`help` lists them, from `src/chatddx/repl/commands.py:COMMANDS`. `src/chatddx/repl/commands.py:handle` splits a line as
a shell would, into a verb, or two words as in `run tag`, and its arguments: `[ARG]` may be left out, `ARG...` repeats,
and a name may run over several words unquoted. `exit` and Ctrl-D are `quit`.

Each verb is a function in the module for what it does, in `src/chatddx/repl/`:

| module          | verbs                                |
| --------------- | ------------------------------------ |
| `listing.py`    | `configurations` `endpoints` `cases` |
| `choosing.py`   | `use` `under` `set` `save`           |
| `inspecting.py` | `show` `reasoning`                   |
| `running.py`    | `run` `run tag` `seed`               |
| `scoring.py`    | `score` `scorers` `take`             |
| `reviewing.py`  | `runs` `replay`                      |

## Examples

On the sample World loaded for alice, with `chatddx fake-engines` serving (README.md, "The sample world"). Each picks up
where the one before left off.

### Configuring components

```sh
chatddx repl alice <<'EOF'
use plan
set reasoning off
show
save plan-off
EOF
```

### Running and scoring

```sh
chatddx repl alice <<'EOF'
use plan-off
seed 7
run dutch-10
run tag dutch
EOF
```

### Reading runs

```sh
chatddx repl alice <<'EOF'
runs 5
replay
show configuration plan-off
EOF
```

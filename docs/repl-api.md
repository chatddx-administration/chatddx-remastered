# Repl API

Reference for the `chatddx.repl` package. It was written from `src/chatddx/repl/*` and `docs/repl.md`. What the shell
does and why is in `docs/repl.md`, and how to use it in the manual (docs/repl-manual.md); this file says what
the package holds, what each command calls, and how its tests are set up. The bench it calls on is in
`src/chatddx/bench/` (docs/bench-api.md).

Paths are relative to `src/chatddx/repl/` unless they start with `src/`, `docs/` or `agents/`.

## Contents
- [Package](#package)
- [The entry](#the-entry)
- [loop.py](#looppy): reading lines
- [shell.py](#shellpy): `Repl`, `Cell`, `console`
- [commands.py](#commandspy): the command table, `handle`, `complete`
- [The commands](#the-commands): where each lives and what it calls
- [render.py](#renderpy): what the commands share to show runs and scores
- [running.py](#runningpy): `Held`, `case_and_seed`
- [Tests](#tests)

## Package
`chatddx/repl/__init__.py` is empty. Its one caller is `src/chatddx/cli.py`, which imports `loop.loop`,
`loop.HISTORY`, `shell.Repl` and `shell.console`; nothing else imports from the package. Only `chatddx.repl` imports
`rich`.

| Module | Holds |
| --- | --- |
| `loop.py` | readline, history, lines from a pipe |
| `shell.py` | `Repl`, `Cell`, `console`, the seed's bounds |
| `commands.py` | the command table, `handle`, `complete`, `help` |
| `choosing.py` | `use`, `on`, `cell`, `set`, `save` |
| `listing.py` | `configurations`, `endpoints`, `cases` |
| `inspecting.py` | `show`, `reasoning` |
| `running.py` | `seed`, `run`, `batch`, `Held` |
| `reviewing.py` | `runs`, `replay` |
| `scoring.py` | `score`, `scorers`, `take` |
| `render.py` | styles, the transcript, live lines, answers, scores and findings |

Every command is a function `(repl: Repl, *args: str) -> None` that says what it does on `repl.console`, and errors
through `repl.error`. Only the bench writes (`src/chatddx/bench/`).

## The entry
`cli.py:_repl`, for `chatddx repl LOGIN [--world DIR] [--facts PATH …] [--history PATH]`:
1. the World from `--world`, else `CHATDDX_WORLD`, else `SystemExit("repl: give a World with --world DIR or
   CHATDDX_WORLD")`;
2. `Facts.load` of the bundled facts, the World's and each `--facts`;
3. a psycopg connection to `settings.database()` in autocommit mode;
4. the person by login, else `SystemExit("no person 'LOGIN': chatddx init-data LOGIN adds them")`;
5. `loop(Repl(Bench(conn, person, world.inventory, facts), console()), history)`, and `SystemExit(1)` when it returns
   1.

## loop.py
### `HISTORY`
`Path.home() / ".chatddx_history"`.

### `loop(shell: Repl, history: Path = HISTORY) -> int`
Reads lines with `input(shell.prompt)` until EOF or a command that ends it, and hands each to `handle`. Tab completes
with `complete(shell.completions(), line)`, words split on spaces; the history file is read first and written last,
and an `OSError` either way is ignored. Ctrl-C at the prompt prints a new line and reads again; a `KeyboardInterrupt`
out of a command prints `(interrupted)`. With stdin not a terminal, each line is echoed, and the loop returns 1 as soon
as `shell.failed` is set. Otherwise it returns 0.

## shell.py
### Names
`NONE = "none"`, the chunk that takes an optional part out; `SEEDS = 100_000`, the bound of a drawn seed;
`MAX_SEED = 2**31 - 1`. `drawn_seed() -> int` is `secrets.randbelow(SEEDS)`.

### `console(record: bool = False, width: int | None = None) -> Console`
A rich console with markup off, since names, vignettes and answers hold brackets.

### `class Cell`
Frozen: `variation: TriedVariation | None`, `endpoint: str | None`, `engine: str | None`, `name: str | None`.

| Name | Gives |
| --- | --- |
| `trying(variation, name=None)` | the cell with `variation`, and `name` when given, else the name it held |
| `holding(name)` | the cell with no variation, holding `name` |
| `on(endpoint, engine)` | the cell at `endpoint`, serving `engine` |
| `label` | the variation's label, `NAME+PART=CHUNK…`; the held name with no variation; else `""` |

### `class Repl(bench: Bench, console: Console, seed: int | None = None)`
The shell's state: `bench`, `console`, `cell` (a `Cell()` to begin with), `seed` (`drawn_seed()` unless given) and
`failed` (set by `error`, read by `loop`).

| Name | Does |
| --- | --- |
| `prompt` | `LOGIN #SEED> `, with ` LABEL×ENDPOINT` after the login as the cell fills |
| `completions()` | the names Tab offers, by key (see `complete`): `_names()` plus `replay:run`, the latest 20 runs' id prefixes, and `score:run`, the runs left to score |
| `forget()` | drops the kept names, so the next Tab reads them again; `save` calls it |
| `say_cell()` | prints `cell: LABEL × ENDPOINT`, `?` for what is missing |
| `say_changed()` | `say_cell`, then the cell's lints (`Bench.findings` of the variation, the engine and the seed) when it holds both |
| `say_findings(findings, tally=False)` | a line per finding, `[level] code: message`; with `tally`, each once with `(×N)` |
| `error(message)` | prints `message` in red and sets `failed` |

`_names()` keeps, per kind of `bench/model.py:KINDS`, the names the person sees, a per-model name by what it is made
from, and one made in several languages as `NAME LANG`; `set:PART` adds `none` for an optional part; and `endpoint`,
`case` (family names and `Bench.case_titles()`), `tag`, `part` and `kind`.

## commands.py
### `class Command`
Frozen: `params: tuple[str, ...]`, as `help` shows them, `[…]` optional and a last one ending in `...` repeated;
`text`, `help`'s line; `run: Callable[..., None] | None`, `None` for the command that ends the loop; `rest: int | None`,
the position of the param that takes the words beyond the params; `grouped: Callable[[list[str]], list[str]] | None`,
a function that groups the words into the params in place of `rest`. `repeats` is whether the last param repeats.

### `COMMANDS: dict[str, Command]`
The command table, in `help`'s order; `exit` is read as `quit`. The rows are under "The commands".

### `handle(repl: Repl, line: str) -> bool`
Splits the line as a shell would (`shlex`), groups its words (`grouped`, else `rest`), checks their count against the
params, and calls the command. It returns `False` for `quit` and `exit`, else `True`. What it says, through
`repl.error`:

| When | Message |
| --- | --- |
| a quote left open | `shlex`'s, as `No closing quotation` |
| an unknown verb | `no command 'VERB': try help` |
| too few or too many words | `usage: VERB PARAMS…` |
| the command raises `LookupError` or `ValueError` | its message; for a `NotFound` with per-model variants, `…, picked by the endpoint in the cell` |
| the command raises `psycopg.Error` | `the database failed: FIRST LINE` |

### `complete(names: Mapping[str, list[str]], line: str) -> list[str]`
The words that may come next on `line`: a verb, then names word by word, so a name with spaces is offered a word at a
time. A command's names are under `VERB:PARAM`, else under the param's name lowercased (`endpoint`, `case`, `run`, …);
`show` takes a kind and then that kind's names, `set` a part and then `set:PART`; `batch`, `show tag` and `take` offer
each tag once; `run` and `configurations` complete the whole line as a name. A name a command's `rest` param takes
whole is followed by the next param's names once it is complete.

## The commands

| Command | Function | On the bench |
| --- | --- | --- |
| `configurations [NAME]` | `listing.configurations` | `threads`, `catalog.recipe`, `catalog.origin`, `about`, `title` |
| `endpoints` | `listing.endpoints` | `inventory`, `endpoint`, `model`, `url_of` |
| `cases` | `listing.cases` | `families` |
| `use CONFIGURATION` | `choosing.use` | `configuration` |
| `on ENDPOINT` | `choosing.on` | `endpoint`, then `configuration`, `chunk` and `model` for a held name |
| `cell CONFIGURATION ENDPOINT` | `choosing.cell` | `endpoint`, `configuration` |
| `set PART CHUNK` | `choosing.set_` | `chunk`, `skeleton` |
| `show [KIND] [NAME...]` | `inspecting.show` | `skeleton`, `findings`, `reach`, `thread`, `get`, `reaching`, `scored_by`, `scores_of`, `runs`, `case_titled`, `appendices_of`, `cases`, `expectation_schemas`, `expectation`, `shared`, `store.scores_of` |
| `reasoning` | `inspecting.reasoning` | `facts`, `inventory`, `endpoint`, `model` |
| `run CASE [SEED]` | `running.run` | `case_titled`, `skeleton`, `start`, then `score` through `Held`, `runs` |
| `batch TAG...` | `running.batch` | `families`, `skeleton`, `start`, `score` through `Held`, `runs` |
| `seed [SEED]` | `running.seed` | `skeleton` |
| `save NAME` | `choosing.save` | `save` |
| `runs [COUNT]` | `reviewing.runs` | `runs`, `store.run`, `scores_of`, `described` |
| `replay [RUN]` | `reviewing.replay` | `run`, `store.run`, `rendered_again`, `scores_of` |
| `score [RUN]` | `scoring.score` | `outstanding`, `run`, `store.finished`, `unscored`, `scorers_for`, `score` through `Held`, `scores_of` |
| `scorers` | `scoring.scorers` | `scorers`, `labels_of`, `skeleton` |
| `take [from OWNER] [TAG...]` | `scoring.take` | `families`, `expectation_schemas`, `take` |
| `help` | `commands.help_` | |
| `quit` | | |

`use`, `cell`, `configurations` and `save` take their name with `rest=0`; `set` its chunk with `rest=1`; `run` groups
its words with `running.case_and_seed`.

## render.py
### Styles
`LABEL` (dim), `REFUSED` (red), `VALID` (green), `LATER` (yellow) and `THINKING`. `STYLES` maps each outcome to its
style. `TOKENS` is the width of a token count.

### What a run shows
| Name | Does |
| --- | --- |
| `Transcript(console)` | `event(event)` streams a run's events: thinking, labelled, the answer, `[name] arguments` and `[result]`, and the tokens after; `item(item)` tells a stored item again |
| `Tally(console, width, case)` | a live line: `count(tokens)` as they stream, `stopping()`, `end(tokens, word, style, said)`; a context manager |
| `JudgeLines(console, bench)` | `event(event)` turns the scoring pass's events into a `Tally` per judge call, ended with what the judge said; `close()` |
| `outcome(skeleton, item)` | `(word, style, why)`, from `bench.outcome` |
| `show_answer(console, skeleton, item, graded)` | the call's error, `stopped`, `unread: …`, `salvaged: …`, `valid` or `invalid: …`, then each selection of the views |
| `show_scores(console, graded)` | one item's scores, a row per view with a target, and `no target: …` once |
| `show_judged(console, bench, graded)` | each judge call of one item: view, judge and seed, what it said at the view's `at`, and its reason |
| `show_table(console, names, items, graded)` | a batch's values, by case title, a column per view with a target in some case |
| `show_summary(console, graded)` | per view: scored, mean, stderr, and no answer, no target and no value apart |
| `verdict_of(view, verdict)` | `(what it said at the view's at, the rest of its text)` |
| `value_of(value, unit="")` | `—` for none, else the value, an integer bare, with its metric's mark |

### What the rest share
`finding(f, times=1)`, `counted(findings)`, `scored_findings(graded, read=False)` (with `read`, leaving out the
`answer.*` codes in `ANSWERED`, which `show_answer` says), `writes(values, prefix="")`, `some(names)` (the first
`NAMED` and `and N more`), `clipped(text, lines=30)`, `clipped_line(text, width=60)` and `plural(n, one, many=None)`.
`UNTARGETED` holds the details of a view with no target (`scorers/scorer.py:NO_TARGET`,
`runner/score.py:NO_EXPECTATION`).

## running.py
### `case_and_seed(words: list[str]) -> list[str]`
`run`'s grouping: words holding `with` after the first are a case's title, with a last whole number as its seed; other
words are left as they are, CASE and SEED.

### `class Held(console: Console, said: str)`
A context manager holding Ctrl-C while a run is written down and scored: the first press prints `said`, and a second,
while scoring, raises `KeyboardInterrupt` once. `scored(bench, run, scorers=None) -> list[Graded]` scores the run with
the judges' lines, `[]` once stopped; `stopped` is whether a second press came; `said()` prints `scoring stopped: score
scores what is left` when it did. `WRITING` and `SCORING` are its two messages, for a run just ended and for `score`.

## Tests
`src/chatddx/repl/test/`, on the test World as `src/chatddx/conftest.py:curated` lands it for alice with her giftbag
(docs/inventory.md, "Worlds"), its endpoints on free ports:

| Fixture | Gives |
| --- | --- |
| `template` | `curated`, so each test starts from the test World loaded |
| `autocommit` | `True`, as the runner needs |
| `bench` | alice's `Bench` on the World with freed ports and its facts |
| `repl` | a `Repl` on that bench, a recorded console 200 wide, seed 7 |
| `say(*lines) -> str` | each line handled in turn, then all the console recorded |

`helpers.py` has `tried(repl)` (the cell's variation), `line_of`, `cells` and `row` (lines, words and rows of what was
said), and `tagged`, `targets_of` and `pattern` (the test World's cases). A test that runs uses the root `fake` fixture,
or serves its own fake; runs to look back on come from the test World's scripted runs (`chatddx.scripted`,
`worlds/test/_runs`). Ctrl-C is pressed with `signal.raise_signal` as a call streams (`test_running.py:press_at`).
`test_vocabulary.py` holds the rest of the code to the bench's words: only the repl speaks of a cell.

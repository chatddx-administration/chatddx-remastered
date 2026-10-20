import shlex
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass

import psycopg
from rich.table import Table

from . import choosing, inspecting, listing, reviewing, running, scoring
from .shell import Repl


@dataclass(frozen=True)
class Command:
    params: tuple[str, ...]
    text: str
    run: Callable[..., None] | None
    rest: int | None = None
    grouped: Callable[[list[str]], list[str]] | None = None

    @property
    def repeats(self) -> bool:
        return bool(self.params) and self.params[-1].strip("[]").endswith("...")


def help_(repl: Repl) -> None:
    table = Table(box=None, show_header=False)
    for verb, command in COMMANDS.items():
        table.add_row(" ".join((verb, *command.params)), command.text)
    repl.console.print(table)


COMMANDS: dict[str, Command] = {
    "configurations": Command(
        ("[NAME]",),
        "list the configurations you can use, a row per name with its languages; "
        + "NAME's parts",
        listing.configurations,
        rest=0,
    ),
    "endpoints": Command(
        (), "list the World's endpoints, and the engine each serves", listing.endpoints
    ),
    "cases": Command((), "list the cases you can run", listing.cases),
    "use": Command(
        ("CONFIGURATION",),
        "use a configuration: yours, one shared with you, or OWNER/NAME",
        choosing.use,
        rest=0,
    ),
    "under": Command(
        ("MODEL",),
        "run a hand-written configuration under a model's handle; one with a model "
        + "part runs under its model's",
        choosing.under,
        rest=0,
    ),
    "set": Command(
        ("PART", "CHUNK"),
        "put another chunk, or model, in a part of the configuration in use; none "
        + "takes an optional part out",
        choosing.set_,
        rest=1,
    ),
    "show": Command(
        ("[KIND]", "[NAME...]"),
        "show the configuration in use, its request, what the lints say and the "
        + "cases each scorer can hold it to (tag TAG...: those with any TAG); or a "
        + "KIND, its or NAME, and your runs with it",
        inspecting.show,
    ),
    "reasoning": Command(
        (), "show what each reasoning level does on each model", inspecting.reasoning
    ),
    "run": Command(
        ("CASE", "[SEED]"),
        "run a case on the configuration in use, with SEED or the seed the repl "
        + "holds, and score it; a case that sends appendices is FAMILY with "
        + "APPENDIX, ...",
        running.run,
        grouped=running.case_and_seed,
    ),
    "run tag": Command(
        ("TAG...",),
        "run the configuration in use on each case with any TAG, a run per "
        + "language, then score them (Ctrl-C stops)",
        running.tagged,
    ),
    "seed": Command(
        ("[SEED]",),
        "draw a fresh seed for the runs; SEED holds it",
        running.seed,
    ),
    "save": Command(
        ("NAME",),
        "save the configuration in use as your own, as NAME",
        choosing.save,
        rest=0,
    ),
    "runs": Command(
        ("[COUNT]",),
        "list your latest runs, the last 20 unless COUNT says",
        reviewing.runs,
    ),
    "replay": Command(
        ("[RUN]",),
        "show a run again as it streamed: the latest, or RUN",
        reviewing.replay,
    ),
    "score": Command(
        ("[RUN]",),
        "score your runs that are left to score, or RUN, as the scorings are now",
        scoring.score,
    ),
    "scorers": Command(
        (),
        "list the scorers, what each view reads, and whether the output of the "
        + "configuration in use offers it",
        scoring.scorers,
    ),
    "take": Command(
        ("[from OWNER]", "[TAG...]"),
        "take the expectations shared with you for each case with any TAG, all "
        + "without, keeping your own; OWNER's only, from OWNER",
        scoring.take,
    ),
    "help": Command((), "list the commands", help_),
    "quit": Command((), "leave (or Ctrl-D)", None),
}


def _joined(command: Command, args: list[str]) -> list[str]:
    extra = len(args) - len(command.params)
    if command.rest is None or extra <= 0:
        return args
    at = command.rest
    return [*args[:at], " ".join(args[at : at + extra + 1]), *args[at + extra + 1 :]]


def handle(repl: Repl, line: str) -> bool:
    try:
        words = shlex.split(line)
    except ValueError as e:
        repl.error(str(e))
        return True

    if not words:
        return True

    verb, *args = words

    if args and f"{verb} {args[0]}" in COMMANDS:
        verb, args = f"{verb} {args[0]}", args[1:]

    command = COMMANDS.get("quit" if verb == "exit" else verb)

    if command is None:
        repl.error(f"no command '{verb}': try help")
        return True

    args = command.grouped(args) if command.grouped else _joined(command, args)
    required = [param for param in command.params if not param.startswith("[")]
    most = len(args) if command.repeats else len(command.params)

    if not len(required) <= len(args) <= most:
        repl.error(f"usage: {' '.join((verb, *command.params))}")
        return True

    if command.run is None:
        return False

    try:
        command.run(repl, *args)
    except (LookupError, ValueError) as e:
        repl.error(str(e))
    except psycopg.Error as e:
        said = str(e).strip()
        repl.error(
            f"the database failed: {said.splitlines()[0] if said else type(e).__name__}"
        )

    return True


def _next_words(names: Iterable[str], typed: list[str]) -> list[str]:
    found: dict[str, None] = {}
    for name in names:
        words = name.split(" ")
        if (
            len(words) >= len(typed)
            and words[: len(typed) - 1] == typed[:-1]
            and words[len(typed) - 1].startswith(typed[-1])
        ):
            found[words[len(typed) - 1]] = None
    return list(found)


def complete(names: Mapping[str, list[str]], line: str) -> list[str]:
    verb, *words = line.split(" ")

    if not words:
        return [name for name in COMMANDS if name.startswith(verb) and " " not in name]

    if len(words) > 1 and f"{verb} {words[0]}" in COMMANDS:
        verb, words = f"{verb} {words[0]}", words[1:]

    command = COMMANDS.get(verb)
    params = command.params if command else ()
    position = len(words) - 1

    match verb:
        case "show" if position == 0:
            return _next_words(names.get("kind", []), words)
        case "show" if words[0] == "tag":
            given = words[1:-1]
            return [
                tag
                for tag in names.get("tag", [])
                if tag.startswith(words[-1]) and tag not in given
            ]
        case "show":
            return _next_words(names.get(words[0], []), words[1:])
        case "take" if words[0] == "from" and position == 1:
            return []
        case "take":
            given = words[2:-1] if words[0] == "from" else words[:-1]
            found = [
                tag
                for tag in names.get("tag", [])
                if tag.startswith(words[-1]) and tag not in given
            ]
            return (
                ["from", *found]
                if position == 0 and "from".startswith(words[-1])
                else found
            )
        case "run":
            return _next_words(["tag", *names.get("case", [])], words)
        case "configurations":
            return _next_words(names.get("configuration", []), words)
        case "set" if position >= 1:
            held = names.get(f"set:{words[0]}", names.get(words[0], []))
            return _next_words(held, words[1:])
        case _ if command is not None and command.rest is not None:
            if position < command.rest:
                return _next_words(names.get(params[position].lower(), []), words[-1:])
            name = words[command.rest :]
            found = _next_words(names.get(params[command.rest].lower(), []), name)
            after = command.rest + 1
            if after < len(params) and " ".join(name[:-1]) in names.get(
                params[command.rest].lower(), []
            ):
                found += _next_words(names.get(params[after].lower(), []), name[-1:])
            return found
        case _ if (
            command is not None and command.repeats and position >= len(params) - 1
        ):
            given = words[len(params) - 1 : -1]
            key = command.params[-1].strip("[].").lower()
            return [
                name
                for name in names.get(key, [])
                if name.startswith(words[-1]) and name not in given
            ]
        case _ if position < len(params):
            key = params[position].strip("[].").lower()
            held = names.get(f"{verb}:{key}", names.get(key, []))
            return _next_words(held, words[-1:])
        case _:
            return []

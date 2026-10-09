import readline
import sys
from pathlib import Path

from .commands import complete, handle
from .render import LABEL
from .shell import Repl

HISTORY = Path.home() / ".chatddx_history"


def loop(shell: Repl, history: Path = HISTORY) -> None:
    matches: list[str] = []

    def completer(_word: str, state: int) -> str | None:
        nonlocal matches

        if state == 0:
            line = readline.get_line_buffer()[: readline.get_endidx()]
            matches = complete(shell.completions(), line)

        return f"{matches[state]} " if state < len(matches) else None

    readline.set_completer(completer)
    readline.set_completer_delims(" ")
    readline.parse_and_bind("tab: complete")

    try:
        readline.read_history_file(history)
    except OSError:
        pass

    interactive = sys.stdin.isatty()

    try:
        while True:
            try:
                line = input(shell.prompt)
            except KeyboardInterrupt:
                print()
                continue
            except EOFError:
                print()
                break

            if not interactive:
                print(line)

            try:
                if not handle(shell, line):
                    break
            except KeyboardInterrupt:
                shell.console.print("\n(interrupted)", style=LABEL)
    finally:
        try:
            readline.write_history_file(history)
        except OSError:
            pass

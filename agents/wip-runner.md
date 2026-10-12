# The runner: work in progress

The runner and the scoring pass are solidified. `docs/runner.md` says what a run and a score do and why;
`docs/runner-api.md` says what each name takes, returns and raises. Their tests in `src/chatddx/runner/test/` are
`solidified`, and their open issues are the docs' "Open design issues" and "Known gaps".

This file keeps what the docs don't: work under way, and what belongs to other files. Its phases, decisions and
by-hand checks are in its history; other notes still cite those sections ("Decided", "Phase 5", "The scoring pass",
"Afterwards", "Left"), and `docs/runner.md` describes what they built.

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Under way
### A round stopped while its tools run
Decided: A, a round's call is optional. Built:
- **The ledger.** `Turn.call` is optional (`ledger/call.py`) and left out of the canonical form when missing, so every
  stored round reads and seals as before. `RunItem` refuses a round without its call before the last, and `calls`
  skips it. `check_run` accepts a last round without a call that ran some or all of the calls the response made, and
  notes `tools.stopped` in place of `tools.unanswered` (`ledger/run.py:_rounds`).
- **The runner.** `rounds.py:converse` keeps the round under way as the last of its turns, replaced whole as it grows,
  so an interrupt or a halt mid-round keeps the tools that ran. A halt runs no further tool and sends no request after
  them, where it used to send the round's call and hang it up. An interrupt inside a tool records it as stopped:
  `Toolbox.run` raises `ToolStopped` with the run.
- **Callers.** The bench's `outcome` calls such an item `stopped`; the repl's transcript skips the missing call.
- **Run items keep version 1** (a take). The rule says a changed default needs a new version, but every run item
  written before reads the same, and a reader that requires the call refuses one without it rather than misreading
  it. A bump would make every stored run item unreadable (`docs/store.md`, "Known gaps"). `docs/ledger.md` has an
  AGENT suggestion amending the rule.

The docs have AGENT suggestions: `docs/ledger.md`, `docs/ledger-api.md`, `docs/runner.md`, `docs/runner-api.md` and
`docs/chatddx.md` (`tools.stopped`). The tests are `wip` until those are taken: `ledger/test/test_unsent_rounds.py`
and `runner/test/test_stopped_rounds.py`. Then they join `test_ledger.py` and `test_run.py`.

## Elsewhere
- **`chatddx samples`** back on the runner: `agents/wip-sample-data.md`, "Sample runs".
- **Resuming** and **`max_jobs` across runs**: `agents/wip-worker.md`, "Below the worker".
- **No canary set is seeded** (`docs/runner.md`, "Smaller issues"); `docs/curation.md` points here for it.
- **The gate's cases only the test World reaches aren't read by a test**: `qwen3-bare@fake` not cleared for `typed`,
  and `unknown@remote` cleared for nothing, with its secret unset (`agents/wip-test-world.md`, "Not read yet"). The
  gate's tests edit the inventory instead (`runner/test/test_run.py`).
- **R2 and R10** of the runner's plan were decided "as recommended", but aren't written down anywhere, in this file or
  its history; what they decided needs restating.
- **The real engines are cleared for the sample** (decided: `agents/wip-clearance.md`, "Vetted endpoints").
  `worlds/kompismoln/inventory.toml` clears `qwen3-8b@pelle` and `gpt-oss-20b@malborg` for `sample`.

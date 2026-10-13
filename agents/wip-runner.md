# The runner: work in progress

The runner and the scoring pass are solidified. `docs/runner.md` says what a run and a score do and why;
`docs/runner-api.md` says what each name takes, returns and raises. Their tests in `src/chatddx/runner/test/` are
`solidified`, and their open issues are the docs' "Open design issues" and "Known gaps".

This file keeps only what belongs to other files. Its phases, decisions and by-hand checks are in its history; other
notes still cite those sections ("Decided", "Phase 5", "The scoring pass", "Afterwards", "Left"), and
`docs/runner.md` describes what they built. The last decisions taken there: a round's call is optional, and run items
kept version 1 for it (`docs/ledger.md`, "Tool rounds" and "Canonical form and versions").

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Elsewhere
- **Scripted runs**, `chatddx scripted-runs` on the bench: `docs/scripted.md`.
- **Resuming** and **`max_jobs` across runs**: `agents/wip-worker.md`, "Below the worker".
- **No run sends a canary set** (`docs/runner.md`, "Smaller issues"): data sets hold them now, and `Bench.start`
  passes none.
- **The gate's cases only the test World reaches aren't read by a test**: `qwen3-bare@fake` not cleared for `typed`,
  and `unknown@remote` cleared for nothing, with its secret unset (`agents/wip-test-world.md`, "Not read yet"). The
  gate's tests edit the inventory instead (`runner/test/test_run.py`).
- **The real engines are cleared for the sample** (decided: `agents/wip-clearance.md`, "Vetted endpoints").
  `worlds/kompismoln/inventory.toml` clears `qwen3-8b@pelle` and `gpt-oss-20b@malborg` for `sample`.

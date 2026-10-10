# The batch planner: work in progress

The batch planner crosses the variations of a configuration with a set of cases into the trials a batch runs, and
shows what would run before anything starts: what each variation sets, what is held back and why, and what each
scorer can read. It serves the portal's batch pages first (`agents/wip-portal.md`), and the repl and the API after.
The worker runs what it plans (`agents/wip-worker.md`). This file plans its port from the old project.

"The old planner" is chatddx-administration/chatddx at 504792c: `src/chatddx/bench/plan.py` (129 lines), and the
portal's planning half: `src/chatddx/django/portal/batches.py` (263), `forms.py:BatchForm`, `admin.py:BatchAdmin`,
`models.py:BatchModel`, `templates/portal/batch/`, `static/portal/js/batch_form.js`, 18 tests in
`tests/test_batch.py`, and the manual's "The Batch" (`docs/portal.md`). Old permalink base:
https://github.com/chatddx-administration/chatddx/blob/504792cbeb09508f2c52912be29a3d8809d2fa1d/

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
1. **Decided: planned apart from the worker**, as this file and `agents/wip-worker.md`. What the planner hands the
   worker is the worker's contract (`agents/wip-worker.md`, "The contract").
2. **What it is in remastered** (see "The planner"): pure over the bench, a `Bench.plan` giving a value, with the
   crossing itself a pure function. No queue, no process. Take.
3. **Decisions** (see "Options"): P1, whether a plan is kept; P2, what is crossed; P3, mixed languages; P4, which
   cases, and adding cases later.
4. **Its callers**: the portal's batch form and confirmation, then the repl's `batch` and the API (see "Callers").

## The old planner
### What it was
- **Crossing** (`plan.py:crossed(cell, variations)`): the product over the slices with variations ticked, the
  configuration's own first, each applied with `Cell.set`, one cell kept per fingerprint.
- **Planning** (`Plan.of(bench, cells, tags, seed)`): each cell made ready (`bench.ready`) or held back with why: a
  `NotReady` (not your own, no secret) or the stack's refusals, worded "not yet" or "refused" with the slice
  (`plan.py:reasons`). The cases were the person's with any of the tags. The trials were the ready cells times the
  cases, one case each, and a greedy cell ran unseeded (`Plan.seed_of`).
- **The form** (`BatchForm`): **Use**, a configuration of the person's; **On**, a stack; **Case tags**; **Seed**,
  drawn at random, or none for unseeded; then, once tags were picked, a row per slice of the person's variations, the
  configuration's own ticked (`batch_form.js`).
- **The confirmation** (`batches.py:shown`, `scorers_of`): how many trials (cells times cases); each cell, what it
  set, its seed, and a link to its configuration's page with those set; each cell held back and why; the cases, the
  first twelve named; and for each scorer, how many cells offer the view it reads, and how many cases have the target
  it holds them to, naming those that don't. **Back to the form**, **Run it now** or **Keep it for later**; a plan with
  nothing to run couldn't be kept.
- **What was kept** (`BatchModel`): the configuration, stack, tags, variations and seed, and as JSON the cells (label,
  what each set, fingerprint, seed), those held back, and the cases (name, fingerprint). A batch's page showed it and
  never changed it. Running a kept batch made each cell ready again, and refused one whose fingerprint had changed
  (`batches.py:readies_of`, `Drifted`). More cases could join a kept batch (`batches.py:unheld`,
  `BatchAdmin.cases_view`).
- **Its state** was its jobs' (`agents/wip-worker.md`, "The old worker").

### What changes in remastered
- **The cell is two things**: the variation being tried (`src/chatddx/bench/variation.py:TriedVariation`) and the
  endpoint beside it (`agents/wip-bench.md`, K2 with R1). "Cell" stays the repl's word.
- **Slices are recipe parts** (`PARTS`, `OPTIONAL` in `src/chatddx/bench/variation.py`); the coercion is the output's
  contract (`agents/wip-repl.md`, D6).
- **A trial holds the cases**: one trial per variation, not one per cell and case. A run holds an item per case and
  replicate.
- **Readiness is findings**: warnings, never refusals (`docs/chatddx.md`, "Compromises"; `Bench.findings`). What holds
  a variation back is the gate's refusal (`src/chatddx/runner/gate.py`), or a part that can't be set
  (`TriedVariation.set`'s `ValueError`). "Save it as your own first" is gone: any digest runs (`agents/wip-bench.md`,
  "The old bench").
- **Seeds are explicit**: a trial has at least one, and a greedy trial still hashes its seeds; `render` sends none for
  a greedy skeleton (`agents/wip-repl.md`, D3). "Unseeded" is gone. Several seeds are replicates of one trial, not an
  axis to cross.
- **Names are per model and per language** (`agents/wip-variants.md`): `Bench.configuration(name, engine)` picks a
  configuration's variant by the endpoint's model.
- **A trial is a digest**, stored when it runs and never threaded (`agents/wip-repl.md`, D7). A plan that keeps its
  trials' digests can't drift, so `Drifted` has no counterpart.
- **Batch order** is by case digest, since `Trial` sorts its cases, not by name (moved from `agents/wip-repl.md`,
  "Risks").

## The planner
Take:
- **In**: a configuration (a thread id), for each part the chunks to try (its own among them, by digest, `None` for an
  optional part taken out), an endpoint, the cases (by tag or by family id), and the seeds.
- **Crossing**: `crossed(variation, choices) -> list[TriedVariation]`, the product of the parts' choices over the
  configuration's variation, one kept per skeleton digest. Pure, in `src/chatddx/bench/plan.py`, tested without a
  database as `variation.py` is.
- **Planning**: `Bench.plan(…) -> Plan`, since the bench stays one class and edges call `bench.*` only
  (`agents/wip-bench.md`, "Modules"). For each variation at the endpoint: its skeleton digest, whether it is greedy,
  its findings (`Bench.findings`), and the gate's refusal if any, which holds it back. For the plan: the cases, and
  each scorer view's reach over them (`Bench.reach`).
- **Out**: a `Plan` value: the trials it would run, one per variation not held back, each with the cases and the
  seeds; what is held back and why; the cases; the reach. Nothing is stored.

## Options
### P1. Is a plan kept?
The old portal kept a batch to run later, and its page never changed.
- **L1. Not kept.** A plan is shown, then its trials are asked of the worker. Nothing groups the runs but their
  trials, so a batch has no page of its own.
- **L2. A component of a new kind, `plan`**: its trials and endpoint, by digest. Runs are found from it by their
  trials.
- **L3. L2, kept on a catalog thread** when kept for later: named, owned, shared and deleted as configurations are.
  Adding cases is a new edit of the thread: new trials, since the cases are part of a trial's digest.

Take: L3, since it keeps a plan as the catalog keeps everything a person keeps. D7 keeps ad-hoc trials off threads so
as not to flood the catalog; a kept plan is deliberate, as a configuration is. A new kind changes `docs/factors.md`,
so it is the user's call.

### P2. What is crossed
- The recipe's parts, as before. Take.
- Endpoints too: a plan over several endpoints, which the old form didn't offer. Each endpoint picks its model's
  variant of the configuration, so the variations differ by endpoint.

### P3. Mixed languages
Moved from `agents/wip-variants.md` ("Questions for the user"): with picking by the cases' language, does a batch of
English and Swedish cases run as one trial per language, each under its variant, or is it refused? A question for the
user.

### P4. Which cases
- By tag, as before, and by family id, as the API names things (`agents/wip-api.md`, A4).
- Adding cases to a kept plan, as the old `unheld` did: under L3, an edit.

## What it hands the worker
Per trial, an ask: the trial, the endpoint, the owner, scored or not (`agents/wip-worker.md`, "The contract").
**Run it now** asks at once; **Keep it for later** keeps the plan (P1) and asks when it is run from its page. A kept
plan's state (none run, queued, under way, stopped, unfinished, done) is read from the worker's asks and the ledger
by trial, so the planner keeps none.

## Callers
- **The portal**: the batch form, an island, since ticking chunks wants the number of trials, what is held back and
  each scorer's reach as you tick; the confirmation and a kept plan's page, rendered on the server
  (`agents/wip-portal.md`, "Islands").
- **The repl**: `batch TAG…` runs one variation over the tagged cases with one seed, as one trial and one run
  (`agents/wip-repl.md`, "Built: 4b"). It could take a plan, perhaps as several parts given at once.
- **The API**: a plan read like `GET /api/threads/{id}/variation`, with several chunks per part
  (`agents/wip-api.md`, "The plan"); then asking for it.

## The plan
Assuming the takes.
1. **Crossing**: `crossed` in `src/chatddx/bench/plan.py`, with tests without a database.
2. **Planning**: `Bench.plan` and `Plan`, tested on the curated sample (`src/chatddx/conftest.py:curated`).
3. **The API's read**, beside `variation`.
4. **Kept plans**, once P1 is decided: the kind, its thread kind, and the catalog's entries.
5. **The portal's pages** (`agents/wip-portal.md`, "Phases", 5).
6. **Asking the worker**, once it exists (`agents/wip-worker.md`, "The plan", 3).

## Open
- **How many trials a plan may hold** before the form warns, since crossing multiplies.
- **Seeds**: one drawn per plan, as before, or several for replicates (`src/chatddx/factors/trial.py:suggest_seeds`).
- **The order of the variations**, the configuration's own first, as the old crossing put it.
- **A batch sample run** for the portal's pages (`agents/wip-sample-data.md`, "Sample runs").

## Moved here
- From `agents/wip-portal.md`: the planner's part of "The batch planner and the worker".
- From `agents/wip-repl.md`, "Risks and smaller open points": batch order.
- From `agents/wip-variants.md`, "Questions for the user": mixed batches.

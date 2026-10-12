# Judges: work in progress

A judge is an LLM used as a metric (`docs/factors.md`, "Judge"). Judges are what score free-text expectations, such as
the clinicians' notes in the targets (`agents/wip-sample-data.md`, "Free-text expectations"). This file plans the
judge pipeline: judges in a data set, the scoring pass sending judge requests, and the scorer code turning verdicts
into values. The judge prompt, what a judge is asked and how it answers, is Olof's to shape and comes after.

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
The runner pass before it is done (`agents/wip-runner.md`, "Start with this"), and so is phase 1: one
prepare-and-render, `runner/prepare.py:Items`, whose `case` a judge's fills will use, and the fake's schema examples
picked by seed (`fake_vllm/chat.py:instance`; `docs/vllm.md` has AGENT suggestions). J2, J5 and J9 are decided.
Next: phase 2, then phase 3. Phase 4 needs J1, J6, J7 and J8.

## Decided
- **The pipeline before the prompt.** The judge pipeline is built and tested on the test World (`worlds/test/`,
  `agents/wip-test-world.md`) with made-up material, without waiting on real answers or Olof's prompt. Everything a
  judge pipeline needs goes into the test World first.
- **Free-text expectations** are as `agents/wip-sample-data.md` decided: clinicians' notes are expectation data, kept
  apart as `comment` and `answer`, in the targets schema, as written, with their author and language.
- **J2: the scorer interface's next version, for every scorer.** One shape of metric takes what a view picks and,
  for a judged view, the judge's verdicts, so one scorer can hold pattern views and judged views side by side. There
  is no stored state to keep, so nothing holds the interface back. The pattern metrics compute what they did, and
  where the judged metrics live is phase 3's (see "J2. Judged metrics").
- **J5: a call per view**, as the model has it now. A verdict per aspect is a judge per aspect, each with a prompt
  that asks one thing, which keeps each judge's job simple; cost is the price, and several aspects of one answer may
  not be common. Views that share a judge and pick the same things send the same request, each its own; a lint could
  say so later.
- **J9: judges in the data set** (see "J9. Judges in a data set").
- **J3: a verdict is read as an answer is**, by its skeleton's contract (see "J3. Reading a verdict").
- **J4: a judged view skips what it would read.** A case without notes still has an expectation; what it lacks is
  the optional part a view reads, as pattern views meet already, giving no value with `"no target"`. A judged view
  sends nothing, and gets no value with the reason in the detail, when the answer can't be read, its output selector
  picks nothing, or its expectation selector picks nothing and the judge's prompt has the `expectation` slot. A
  judge that doesn't read the expectation runs on every case.
- **J10: a judge skeleton with tools is refused, and a greedy judge with several seeds is linted** (see "J10. What a
  judge skeleton may be").

## What exists
- **Factors** (`src/chatddx/factors/scoring.py`): `Judge` (a skeleton of purpose `judge`, an engine, seeds, a fill
  rule), `View.judge`, `Scorer.judges`, and `Judge.fills`, which fills the `completion` and `expectation` slots from a
  view's picks with `text@1`.
- **Prompts**: purpose `judge` allows the `vignette`, `appendices`, `completion` and `expectation` slots and requires
  `completion` (`src/chatddx/factors/request.py:SLOTS_BY_PURPOSE`).
- **Ledger** (`src/chatddx/ledger/score.py`): `JudgeCall` (judge, seed index, call) inside `ScoreItem.judge_calls`,
  and `ScoreStarted.execution` for the judge calls. `check_score` raises for a call by another judge than the view's,
  a seed index out of range or used twice, and warns `judge.incomplete` when a value rests on fewer seeds than
  declared. It checks the judge calls' execution against the run's schedule (`ledger/call.py:check_execution`).
- **Lints**: a judge is linted as a skeleton with an engine, as a trial is (`factors/lint.py`, `facts/lint.py`), and
  its language is its skeleton's (`catalog/language.py`).
- **Refused**: `scorers/scorer.py:score` and `runner/score.py:score_run` refuse judged views; the bench reports them
  as refused (`bench/runs.py:score`), and the repl and the API show "not yet".
- **The test World**: the recipe `judge` (purpose `judge`, greedy; its prompt holds the vignette, the completion and
  the expectation), the output `verdict` (`schemas/verdict.json`: `meets`, `why`), and the case `noted`, with carol's
  note (a comment and an answer) and dave's (a comment), in Swedish on an English case.
  `scorers/test/test_scorers.py:test_a_judge_reads_a_case_s_notes_beside_the_targets_the_patterns_read` fills a judge
  from them.
- **Not there**: a data set can't hold a judge (`docs/curation.md`, "What a data set can't hold yet"), no shipped code
  scores a verdict, nothing sends a judge request, and the fake answers a schema the same whatever the seed.

## Takes
### J1. Where judge calls go
A judge names an engine; a call needs an endpoint. Take:
- the scoring pass takes an endpoint per judge, by default the one endpoint in the inventory that serves the judge's
  engine, and refuses when there is none or more than one and the caller named none;
- each endpoint goes through the run's gate (`runner/gate.py:check`), generalized from a trial to an engine, a set of
  cases and whether there are tools: the engine it serves, clearance for the sensitive sources of the run's cases,
  the secret and `confirm`. A judge prompt always holds a completion, which is case-derived, so the clearance check
  always applies, whatever slots the prompt has;
- `ScoreStarted.endpoints`, defaulting to none and left out when empty, records each judge's endpoint by judge,
  name and URL, as `RunStarted.endpoint` does for a run (`agents/wip-clearance.md`, "Takes"). Unjudged scores keep
  their digests.

### J2. Judged metrics
Decided: interface version 2 for every scorer (see "Decided"). The pattern metrics take what a view picks
(`scorers/scorer.py:ScoreFunction`, version 1). The rest is a take:
- `ScoreFunction` also takes the verdicts: none for an unjudged view, else one per seed in seed order, each a value or
  none. `Metrics` publishes which of its metrics are judged, and `Metrics.problems` refuses a judged metric on a view
  without a judge, and the other way round;
- the judged metrics are written in `chatddx/scorers/verdicts.py`, and the shipped entry point publishes them beside
  the pattern metrics, so a scorer can mix them. The pattern metrics compute what they did; whether the entry point's
  version moves is settled when it's built, and moving it re-plans every scorer, which no stored state minds;
- two metrics to start: `verdict`, the share of seeds whose verdict holds `true` at a JSON Pointer in the params
  (`/meets`), and `points`, the mean over seeds of a number at a pointer, divided by a `max` in the params;
- seeds are combined by the mean over the seeds that gave a readable verdict, with each seed's value in the detail.
  No readable verdict gives no value. Majority and agreement are analysis over the detail.

### J3. Reading a verdict
Decided, as this take has it: a judge's answer is read as an answer is, by its skeleton's contract (`scorers/answer.py:read`). A verdict that
breaks the judge's output schema is still read, and noted, as an answer is (`answer.invalid`); one that can't be read
is none for its seed, and noted, with the call's error when it has one. The codes are `verdict.unread` and
`verdict.invalid`.

### J4. Nothing to judge
Decided (see "Decided"). `Judge.fills` today fills an empty pick with an empty string. `check_score` already leaves a
value-less item out of `judge.incomplete`.

### J5. One call, several views
Decided: a call per view (see "Decided"). The options were a call per view, views with the same judge and picks
sharing calls, and a view with several values (a change to `ScoreItem`).

### J6. The scoring pass as a job
`score_run` is synchronous, sends nothing, and has no events or halt. The API scores in the run's thread right after
`finish` (`api/runs.py:_send`). Judges add cases × judged views × seeds calls. Take:
- the scoring pass takes the runner's shape: `start` (gate and refusals before anything is written, then
  `ScoreStarted` and the owner entry), `send(on_event)`, `halt()`, `finish()`, with calls through `runner/send.py`
  under `ScoreStarted.execution` (retries, timeout, whitespace cutoff, halt);
- serial first, in the run's schedule order; concurrency up to the judge endpoint's `max_jobs` later, as the runner's
  phase 4 did it;
- events: one per score item written, and findings as they're noted. No deltas, as canaries have none;
- a halt records the calls under way as stopped. The item is written with the seeds it has, and `judge.incomplete`
  says so;
- unjudged scorers go through the same pass and send nothing, so there is one path;
- where scoring runs, in the request or in a worker, is worker K5's (`agents/wip-worker.md`).

### J7. The vignette in a judge prompt
A judge prompt with the `vignette` or `appendices` slot needs the case fetched again and prepared as the trial
prepared it (`docs/factors.md`, "Smaller issues"). Take:
- one function fetches, prepares and renders an item for the runner and `bench/seen.py:Seen.rendered_again`
  (`runner/prepare.py:Items`, built); a judge's fills come from its `case`;
- the judge's fills use the trial's cleanup and the judge skeleton's appendix layout;
- a vignette whose fingerprint isn't the run item's gets no call and a `case.drift` finding: the judge would read
  another case than the model did.

### J8. Attestation
Judge calls aren't checked the way run items are (`docs/factors.md`, "Smaller issues"). Take: `check_score` checks
each judge call's returned model against the judge engine's served name, with `attestation.model` as `check_run`
does, when the pass is built. The prompt-token check needs the judge request rebuilt from the answer as the scorer
read it; later. Neither changes what is stored.

### J9. Judges in a data set
Decided: in the data set, as this take has it:
- `[judge.NAME]` in a data set's `factors.toml`: `recipe` (the variant made for the engine's model, when the recipe
  is made per model), `engine` (an engine's name in the World), `seeds` and `fill`;
- a scorer's view names a judge by name, as a scorer names its expectation schema;
- a judge whose engine the World doesn't have is skipped with a line, as a recipe is, and so is every scorer that
  names it. A judged scorer's digest pins its judge's engine through the judge, so a judged scorer belongs to the
  Worlds that have that engine. That follows from `View.judge` being a reference (`docs/factors.md`, "Scoring").

### J10. What a judge skeleton may be
Decided, as this take has it: `Judge.cross_check` refuses a skeleton with tools, since a judge has no tool rounds, and a lint warns about a
greedy judge with more than one seed, whose seeds all send the same request (`docs/factors.md`, "Greedy sampling and
seeds").

### J11. Language
A note is in Swedish, an answer may be in English (G18). Take: the pipeline does nothing about it; it is the
prompt's, for Olof. Judges aren't checked for language (`docs/catalog.md`, "Smaller issues") and stay unchecked.

### Hypothetical notes stay out of the sample
Take: the sample's notes carry `author = "Olof"` into every score, and the sample is live data. Made-up notes go in
the test World, under the placeholder authors it has. The sample gets its judge once Olof's prompt exists.

## The test World's additions
Each read by a test, as `agents/wip-test-world.md` asks ("Principles", 1), and pinned in
`src/chatddx/curation/test/test_the_test_world.py`:

| Record | Exercises | Read by |
|---|---|---|
| `verdict.json` with `examples`: one meets, one doesn't | seeds that disagree (J2), with the fake below | the pass's tests |
| output `grade`, `schemas/grade.json`: `points` (0–2), `why` | a verdict on a scale (`points`) | the pass's tests |
| recipe `judge` (exists, greedy) | a judge with one seed | the pass's tests |
| recipe `judge-graded`: the `judge` prompt, output `grade`, sampling `recommended` | a sampled judge made per model | the pass's tests |
| judge `verdict`: recipe `judge`, `qwen3@fake`, seeds `[1]` | the plain case | the pass's tests |
| judge `graded`: recipe `judge-graded`, `qwen3@fake`, seeds `[1, 2, 3]` | seeds combined | the pass's tests |
| judge `remote`: recipe `judge`, `unknown@remote`, seeds `[1]` | the gate's "isn't cleared" and "needs the secret" for a judge (J1); `facts.missing` on a judge | the gate's tests, the lints' |
| scorer `judged`, with the views below | judged and pattern views in one scorer (J2); nothing to judge on every case but `noted` (J4) | the pass's tests, curation's |
| scorer `judged-remote`: one view under `remote` | a judged score refused before anything is written | the gate's tests |

The scorer `judged`, over the schema `targets` and the answer shape `lines`, has four views:
- the differential against the diagnosis, a pattern view as the `lines` scorer has it;
- carol's comment, then carol's answer, each under the judge `verdict`, metric `verdict` at `/meets`;
- carol's comment under the judge `graded`, metric `points` at `/points`, with `max = 2`.

The fake changes with it: a non-greedy request whose schema has `examples` is answered with the example its seed picks
(`docs/vllm.md`, "Schema instances", amended). A greedy one keeps the first.

## Phases
1. **Groundwork** (built). One prepare-and-render for the runner, `rendered_again` and judges (J7). The fake's
   schema examples picked by seed, as its text answer is rotated, the first when greedy
   (`fake_vllm/test/test_seeded_examples.py`).
2. **Curation.** The `judge` table, judged views by name, the refusals and the lint (J9, J10). The test World's
   records above, and the test World's own test.
3. **Judged metrics.** The scorer interface's version 2, `chatddx/scorers/verdicts.py`, verdict reading and
   nothing-to-judge (J2–J4), tested on synthetic responses without a database.
4. **The pass.** Start, send, halt and finish, with the gate on judge endpoints, `ScoreStarted.endpoints`, the
   vignette refetched, and `check_score`'s model check (J1, J6–J8). Tested on the test World's fakes.
5. **The callers.** The bench scores judged scorers and reports a gate refusal as refused; the repl and the API show
   judged values where they say "not yet" now.
6. **After the pipeline.** The sample's judge, on Olof's prompt; a run on pelle or malborg to see real engines write
   valid verdicts; the judge measured against Olof's own grading.

## For Olof, later
What the prompt needs from him:
- his `comment`, his `answer`, or both as two views;
- whether the vignette goes in the judge prompt;
- how a Swedish note is read against an English answer: in the prompt, or translated once into an expectation of its
  own;
- the verdict: pass or fail, a scale, or a verdict per aspect, and how strict about extra or harmful advice;
- the judge's engine and its seeds.

What would measure the judge: real answers on the three cases with notes (`Dutchfall11w`, `Dutchfall1w`,
`casesfromedn1`) from pelle and malborg, graded by Olof with a line on why. Open beside it: notes on more cases, and
whether the targets are revised where his notes disagree with them (`Dutchfall11w`).

# Judge handles: work in progress

A judge names a model handle, as a recipe does, rather than an engine: researchers pick models by handle and see no
engines (`agents/wip-refine.md`, "Start with this", 5). The docs already say so: `docs/factors.md`, "Judge", and
`docs/runner.md`, "Judges". "Decided" means the user said so; "Take" is the agent's recommendation and still open.

## Decided
Decided: judges name a handle, as the take moved here from the backlog has it (see "Taken from the backlog").

## Plan
1. **Factors.** `Judge.model`, the weights picked by handle, replaces `Judge.engine`, a new version of the judge's kind.
   `Scoring.engines` pins the engine each judge the scorer's views name is sent to, the handle's latest when the
   scoring is built, as a trial pins a run's; checked: each judge once, each engine serving its judge's weights. A
   scoring without judges keeps its digest, as defaults are left out of the canonical form.
2. **Runner.** The scoring pass sends each judge's calls to the endpoint serving the engine the scoring pins, and the
   gate bars and admits that engine; checking a score attests the judge calls' model against it.
3. **Bench.** A scoring is built with each judge's handle resolved (`Seen.judged`): a handle that doesn't resolve to
   one endpoint is ops' error, and a judge whose weights its handle no longer holds is behind, "follow it first". What
   applies to a run: a judge whose handle doesn't resolve leaves its scorer out, as an endpoint not serving its engine
   did; a behind judge keeps its scorer applying and left to score, and scoring says why.
4. **Lints.** A judge alone is linted against its weights' facts; the pairing of its skeleton with an engine is linted
   where the engine is known: its handle's latest, for the look of a judge configuration, a judge checked or written,
   and a data set loaded.
5. **Curation.** A data set's judge takes the weights of the handle the World binds it to.
6. **Edges.** What a judge is asked renders the handle's latest engine's name, or `‹model›`; the portal's judge form
   sends the handle's weights; a judge is titled by its skeleton and its handle.

## Built
- **Factors** (`src/chatddx/factors/scoring.py`): `Judge.model`, version 2; `JudgeEngine` and `Scoring.engines`,
  with `Scoring.engine_of`, and the scoring's check that its engines are its scorer's judges', each serving its
  judge's weights. A judge is titled `judge SKELETON under HANDLE` (`src/chatddx/catalog/titles.py`).
- **Runner**: `judge_at` takes the engine; the gate's `bar` and `admit` take the judge with its engine (`judged`);
  the scoring pass sends to the endpoint serving the engine the scoring pins, and `check_score` attests the judge
  calls' model against it (`src/chatddx/ledger/score.py`).
- **Bench** (`src/chatddx/bench/seen.py`): `Seen.judged`, the endpoint a judge's handle resolves to, refused as ops'
  error or as behind; `scoring` pins each judge's engine through it; `_applies` leaves out a scorer whose judge's
  handle doesn't resolve, and keeps one whose judge is behind, which `unscored` then counts left to score and `score`
  refuses saying why. `judging`, the engine a judge's skeleton is linted on, for `check`, `linted` and the look.
- **Lints**: `lint` and `lints` take `engines`, the engine each judge is paired with; a judge alone gets its weights'
  facts, `judge.model_unmatched` (was `judge.engine_unmatched`) and `judge.greedy_seeds`.
- **Curation**: a data set's judge takes its handle's weights, refused as the World's when it names a model or an
  engine; `Plan.engines` keeps the engine each judge is linted on as the data set loads.
- **Edges**: `POST /api/judges/asked` renders the handle's latest engine's name, else `‹model›`; the portal's judge
  form sends the handle's weights (`frontend/src/lib/scorer/JudgeEditor.svelte`); scripted runs start a fake at each
  judge's handle's endpoint.
- **Docs**: the reference's sign-off, and `AGENT` suggestions in `docs/factors.md`, `docs/facts.md`, `docs/api.md`,
  `docs/bench.md`, `docs/runner.md`, `docs/chatddx.md`, `docs/catalog.md` and `docs/inventory.md`.
- **Tests**: `test_factors.py`, a scoring's engines; `test_judges.py`, judges by weights and the plan's engines;
  `test_score.py`, scorings pinning engines; `test_seen.py`, a scoring pinned, left out and behind;
  `test_writes.py` and `test_scores.py`, the API's judge and what it is asked.

### What it leaves
- **Following a judge**, and the scorers whose views pin it: a judge behind its handle is written anew, or edited
  with the handle's weights, and so is each scorer that names it; nothing follows either yet. Related:
  `agents/wip-refine.md`, step 5, "Following a part that moved on".
- **A judge whose handle doesn't resolve leaves its scorer out**, as an endpoint not serving its engine did, rather
  than refusing it saying it is ops'; building the scoring directly says so.
- **Stored judges of version 1 can't be read**, as any bump strands its kind's rows (`docs/backlog.md`, "Old versions
  readable"); no real scores are stored yet.

## Taken from the backlog

### Judges name a model
A judge names a model, as a recipe does, rather than an engine: its calls go to the endpoint serving that model,
picked as a run's endpoint is (see "Picking an endpoint for a model"), and the engine they went to is pinned with the
score, as a trial pins a run's. It changes the judge's kind, so it is cheapest before real scores are stored.

Decided: a judge's model is picked by handle, and its engine is the handle's latest.

Take: judges name model handles, as recipes do. The section becomes "Judges name a handle":

A judge's model is picked by its handle, such as `qwen3-8b`, as a recipe's is: the judge pins the weights, and its
calls go to the endpoint ops map the handle to, at its latest engine, which the scoring pins. A handle that doesn't
resolve to one endpoint refuses the scoring as ops' error, and a judge whose weights the handle no longer holds is
behind, and doesn't judge under it until followed.

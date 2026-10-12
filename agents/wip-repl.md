# The repl: plan

Plan for bringing the old chatddx shell into remastered, and then past it. "The old repl" is
chatddx-administration/chatddx at 504792c: `src/chatddx/repl/` and its manual `docs/repl.md`. The port began on this
repo at 249548a; this file was last checked against the project at 5d4bff1.
Old permalink base: https://github.com/chatddx-administration/chatddx/blob/504792cbeb09508f2c52912be29a3d8809d2fa1d/

"Decided" means the user said so. "Take" is the agent's recommendation and still open.

## Start with this
The port is done: `chatddx repl` chooses and inspects (4a), runs and scores (4b), and looks back and scores again
(4c; see "4. The shell"), and judged scorers score in it since the judges' phase 5 (`agents/wip-judges.md`). What
comes next is "7. Completion".

Decided (the user, after the check at 5d4bff1): **the repl is brought to completion** in four steps:
1. its quirks and misbehaviour fixed;
2. the sample World made a complete example that new Worlds can follow. That is the repl's authoring: authoring
   writes stay the API's and the portal's (`agents/wip-authoring.md`, "The edges"), and what the repl works with comes
   from a World and its data set;
3. the repl calibrated and adjusted with the user, on the sample;
4. a new manual for the result.

The sample data is the main actor, since it gives the repl the pieces it works with.

What's open, in order:
1. **The questions in "7. Completion"**, "Questions for the user", the order of the first two steps among them.
2. **The cross-check with the old manual** is done (see "The old manual, checked"); the new manual,
   `docs/repl.md`, is drafted from it once the completion's commands settle, since they will change `help` and most
   sections.
3. **Takes waiting for the user's word**, listed in "Decisions so far".
4. **Defects found in the check** (see "Where it stands at 5d4bff1" and "The old manual, checked"): step 1 of "7.
   Completion" fixed those that needed no data and no decision; the rest wait for the calibration.
5. **Left from 4b and 4c**, still true: a structured answer cut short is unread, as nothing salvages it; no word on
   reasoning that wasn't heeded; two tool calls in one response run together on one line as they stream (`replay`
   splits them, so the two differ); an unsaved cell's runs are titled by their whole recipe; only an item's first
   request is rendered again.

Where the docs stand on what the shell changed, and what is left to suggest, is in "6. Docs".

## Where it stands at 5d4bff1
Checked by reading the code and plans, and by driving the shell on the sample World with the fake engines. The quick
test run passes (548).

### What this file said that no longer holds
- **Judges** aren't left out: the scoring pass sends judge calls (`runner/score.py:Grader`), the bench scores judged
  scorers like any other (`bench/runs.py:score`), and `scorers` marks a judged view. Phase 2's "judged views stay
  refused" and "Left out"'s "not yet" are history. The same stale line is in `agents/wip-bench.md` ("Runs, in the
  API", "Judges"), `agents/wip-authoring.md` (S6), `agents/wip-judges.md` ("What exists", "Refused" and "Not there")
  and `agents/wip-sample-data.md` ("Then the small parity items", "Parked").
- **Endpoints with a credential** aren't refused: the gate reads the secret from the environment variable the
  credential names and the wire sends it as a bearer (`runner/gate.py:secret`, `runner/wire.py`). The sample World's
  `mistral-small@remote` has one, served here by `fake-engines`' stand-in; the test World's `unknown@remote` is
  unreachable.
- **D8** was rebuilt by the bench: a person is scored against their own expectation only, and a shared one counts
  once taken (`catalog/threads.py:expectation_choices`; `agents/wip-bench.md`, "What a person is scored against").
  "Else the one thread shared with them" is gone.
- **`Reads`** is folded into `Bench`: `Reads.scorers`, `.scoring`, `.runs`, `.run`, `.reaching` are
  `Bench.scorers_for`, `.scoring`, `.runs`, `.run`, `.reaching`.
- **The bench** isn't waiting on anything: it is a module of its own, described by `agents/wip-bench.md` and
  `agents/wip-bench-api.md`.
- **"A configuration on another model's endpoint"** ("Risks") is said straight away since 4a's lints.
- **The runner** is solidified (`docs/runner.md`, `docs/runner-api.md`).

### Defects
Step 1 of "7. Completion" fixed the interrupted scoring, the findings, `show judge`'s runs and the piped session; the
judged view's display, `scorers` naming the judge, the barred judge, the silent scoring and the judge configurations
listed wait for the calibration.
- **An interrupted scoring counts as scored.** A second Ctrl-C while `run`, `batch` or `score` scores raises out of
  `Bench.score` before `Grading.finish`, so the score has no `ScoreFinished`; `Bench.unscored` counts every
  `ScoreStarted` (`store.scores_of`), so the scorer is never offered again, and `runs`, `replay` and `show` read the
  partial score as any other. The run's answer, scores and "recorded as" aren't printed either. The first press is
  held without a word.
- **A score's findings are never shown.** `Graded.findings` (`answer.*`, `verdict.unread`, `verdict.invalid`,
  `judge.incomplete`, `attestation.model`) has no reader in the repl; the API's `graded_of` leaves them out too.
- **A judged view shows as a clipped `{"seeds": [...]}`**: no verdict, no `why`, no judge call, no judge endpoint
  (`ScoreStarted.endpoints`), in `run`, `batch`, `score`, `replay` or `runs`.
- **`show judge NAME` always says there are no runs**: `Bench.reaching` looks through trials, which never reach a
  judge. `show endpoint` counts runs, not judge calls. `scorers` says "judged" without naming the judge, and `show
  scorer` gives it as a bare digest.
- **A judge whose engine two endpoints serve bars its scorer silently**: `_serving` refuses, asking for an endpoint to
  be named, `Seen._applies` reads that as "doesn't apply", and nothing can name one (`Grader.start` takes
  `endpoints`; the bench, the repl and the API pass none).
- **Scoring is silent and can't be halted**: `Bench.score` calls `score_run`, which sends with no events, so a
  batch's judged scorers send cases × judged views × seeds calls with nothing on screen.
- **`configurations` lists judge configurations**, which `run` refuses when the trial is built ("trial uses a judge
  skeleton"); `agents/wip-authoring.md` S6 takes them apart by purpose. No sample configuration is a judge yet, so
  nothing shows it.
- **A piped session goes on after an error** and exits 0, so `printf … | chatddx repl alice` can't be used as a
  routine that must hold.

### What the repl reaches
It reaches 4 of the 19 writes `Bench` binds (`save`, `start`, `score`, `take`) and most of the reads. It never calls
`fork`, `edit`, `new`, `component`, `fork_component`, `edit_component`, `appendix`, `case`, `replacement`,
`type_case`, `carry`, `take_from`, `say`, `proposal`, `follow`, `deleted` or `linted`; the API calls all of them. It
names threads only by name, so a thread with a title and no name can't be reached. `run` takes a family's bare case,
so a case with appendices can't be run; runs take one seed and no execution, canary set or text cleanup; `score`
can't pick a scorer, score again, or name a judge's endpoint. The API has no scoring requests of its own
(`agents/wip-bench.md`, "Outstanding").

The writes stay the API's and the portal's ("Start with this"); of the rest, what the sample gives the repl decides
what it needs.

## Decisions so far
Decided:
- **D1–D4** (`agents/wip-runner.md`'s history): the interim clearance gate, streaming as a transport, seeds without
  `seed none` and a notice on a greedy cell, and the dependencies (`rich` under `chatddx.repl` only, argparse, the
  stdlib for HTTP). D2 is in `docs/factors.md` ("Rendering"), D7's owner and titles in `docs/catalog.md` ("Owners",
  "Titles").
- **The bench as a module of its own**, and the person-scoped view it is (B3, `agents/wip-bench.md`).
- **Judges**: J1–J10, 1B (a scorer the World bars applies to no run) and 2A (every judged scoring confirms its
  judges' endpoints) (`agents/wip-judges.md`). Olof's notes are expectation data, kept as written, beside the targets
  (`agents/wip-sample-data.md`, "Free-text expectations").
- **Authoring**: A4, A5, A9, A10 and S1–S4 (`agents/wip-authoring.md`, "Start with this").
- **The repl's completion** in four steps, its authoring being the sample World (see "Start with this"). An earlier
  reading of it, the repl reaching every write the bench binds, was withdrawn.

Takes, still waiting for a word:
- **D5** (one versioned answer reader, `answer@1`, with salvage as best effort), **D6** (the vocabulary), **D8** as
  the bench rebuilt it.
- **4a**: per-model names tried from a plain name; names that hold spaces, the last name taking the rest of the line;
  the cell's lints said at once; `set` compiling at once and refusing what doesn't; `save` editing the person's own
  thread of that name, else forking; `show`'s placeholders and per-view reach; `show KIND`'s kinds; `reasoning`'s
  table; seeds drawn below 100,000.
- **4b**: scores after the run, in a table, rather than on each batch line; each selection shown once, by its first
  label; an unsaved cell's compilation stored before its run; greedy cells run, with a notice; the transcript's
  trailing whitespace left out.
- **4c**: what is left to score worked out per run; the latest score per scorer is the one read; `runs` shows means.
- **What applies**: every view of a scorer reaches the run's output schema, so the whole-answer scorers (`free-text`,
  `raw`) apply to every run and read a structured answer as its JSON text (see "3. Reads for a person").
- **S6**: judge configurations listed and found apart, by purpose.
- **Hypothetical notes stay out of the sample** (`agents/wip-judges.md`), which the sample's drafted judge keeps: its
  prompt is drafted, the notes are Olof's.

## Background
The old repl is a thin UI (`src/chatddx/repl/`, ~1,600 lines and ~1,500 of tests) on top of four layers that do
the work: `bench/` (identity, the cell, `Ready`, `Trial`, `save`), `runtime/` (resolving a configuration on a stack,
and the run itself on pydantic-ai and httpx2), `history/` (Django models for trials, runs, messages and scores) and
`scoring/`, ~3,200 lines together. Of those four, only `runtime/`'s run has a remastered counterpart so far: the
runner (`src/chatddx/runner/`).

Remastered has every piece a run is built from: `render`, `Trial`, `Execution`, `prepare_case`, the ledger, the
store, the catalog, the scorers, the facts, the World inventory with `url_of`/`confirm`, and the fake vLLM. The
runner strings them together. Phase 1 and D1–D4 moved to `agents/wip-runner.md`, where they are decided and built.

So the plan:
- **Port the UI.** Command table, parsing, completion, prompt, Ctrl-C handling, rendering. These carry over
  nearly as they are.
- **Rebuild what's underneath** on remastered's pieces rather than porting `bench/`, `runtime/`, `history/` and
  `scoring/`.

The order: decisions, runner, scoring pass, reads for a person, the shell, tool rounds.

## Decisions needed before phase 1
### D1. The clearance gate
The sample's vignette source is declared sensitive (`worlds/sample/inventory.toml`, `[source.sample]`). Sending
case-derived content to an endpoint that isn't cleared is the one hard block, and the runner enforces it
(`docs/chatddx.md`, "Findings and errors"). No clearance pipeline exists yet (`agents/wip-clearance.md`, "Open"). A
runner that follows the rule can't send one sample vignette, not even to the fake.

Options:
- (a) An interim declaration in the World inventory: each endpoint lists the sources it's cleared for, such as
  `cleared_for = ["sample"]`, and the runner refuses anything else. This settles wip-clearance Open 2 as "in the
  inventory, for now". A database grant can replace it later.
- (b) Build the clearance schema first, which settles Open 1–3.
- (c) Declare the sample source not sensitive. That contradicts "treated as if they were".

Take: (a). The gate would also:
- include `confirm` (Open 4);
- refuse a toolset on a sensitive source until tools are cleared (`agents/wip-clearance.md`, "Tools").

Also record where calls went, so the gate can be audited from the ledger: add a defaulted `RunStarted.endpoint`
(name and URL). A defaulted field is additive in canonical form (`docs/ledger.md`, "Canonical form and versions").

### D2. Streaming
The old repl streams the thinking and then the answer, and a batch line's token count climbs while it runs.
`docs/factors.md` ("Rendering") says `stream` and `n` are not sent.

Take: the runner may stream as a transport choice.
- After fingerprinting `render`'s body, it adds `stream: true` and `stream_options.include_usage`.
- It reassembles the chunks into the completion-shaped response that `Call.response` holds:
  - `prompt_token_ids` from the first chunk (`docs/vllm.md`, item 1);
  - `system_fingerprint` from the finish or usage chunk (item 15).
- `Call.request` stays the fingerprint of the rendered body.
- A test pins it: on the fake, the reassembled stream equals the completion it gives unstreamed.

`docs/factors.md`, "Rendering", says so.

### D3. Seeds
The old repl:
- drew seeds below 100,000;
- ran unseeded with `seed none`;
- refused a seed on a greedy cell.

In remastered:
- a trial has at least one seed (`docs/factors.md`, "Seeds are explicit");
- `render` sends it unless the skeleton is greedy;
- greedy trials still hash their seeds (`docs/chatddx.md`, "Compromises").

So "unseeded and not greedy" can't be expressed.

Take:
- Drop `seed none`.
- Keep the short draw for a readable prompt, and accept seeds up to 2³¹−1 (`factors/trial.py:suggest_seeds`).
- On a greedy skeleton, give a notice ("greedy: the seed isn't sent") instead of a refusal.

### D4. Dependencies
Remastered keeps its dependencies few: `cli.py` is argparse, and `web_search` was ported to urllib. The old repl leans
on `rich` for tables, colour, the batch's live line and, in tests, `Console(record=True).export_text()`.

Take:
- Add `rich`, imported only under `chatddx.repl`.
- No `typer`: `chatddx repl` is an argparse subcommand like the rest.
- No pydantic-ai or httpx for the runner. pydantic-ai builds requests from its own message model, so the wire body
  wouldn't be `render`'s and `Call.request` would fingerprint something that wasn't sent.
- HTTP is stdlib, as `inventory/serving.py:served` and the fake server already are.

### D5. Turning a response into an answer
Right after a run, the repl shows `valid`/`invalid`, the views and the scores.
`scorers/scorer.py:score` takes an `answer: JsonValue`, but nothing makes one from a response: parsing is open
(`agents/wip-sample-data.md`, "Parked", "Scorers"), and `docs/chatddx.md` puts it in the scorer's code.

Take: one versioned function, `chatddx.scorers.answer` (`answer@1`). It reads the response by the skeleton's
contract:
- native: the content as JSON;
- tool: the answer tool's arguments;
- text: the content, or the JSON in it when the output has a schema.

It returns:
- the value;
- whether it holds to `Skeleton.output_schema`, and why not.

Scorer entry points call it, so the scorer's `Code` pins it. The repl calls the same function to display a run.
The old runaway salvage (`runtime/run.py:Run.salvaged`, which closes a truncated structure) belongs here too, as
best-effort.

### D6. Vocabulary
An old "stack" (`qwen3-8b-awq@pelle`) is an engine plus where it's served. Remastered splits that into:
- an engine, which is a factor;
- a World-inventory endpoint named `<server>@<host>` (`qwen3-8b@pelle`).

Take:
- `endpoints` replaces `stacks`, and `on ENDPOINT` replaces `on STACK`.
- "Configuration" stays: a configuration is a skeleton thread (`docs/catalog.md`).
- Slices become recipe parts (`factors/request.py:Recipe`): `instructions`, `few_shot`, `prompt`, `output`,
  `sampling`, `reasoning`, `passthrough`, `translations`, `toolset`.
- `coercion` is gone, folded into outputs (G4, G5).

### D7. The repl's trials in the catalog
Each `run` and `batch` makes a `Trial`. Trial is a thread kind, but a thread per ad-hoc trial would flood the
catalog.

Take:
- Store the trial (`Store.add`), but don't thread it.
- Give the run an `owner` entry: "a run's owner should be whoever started it", a rule left to the runner
  (`docs/catalog.md`, "Owners").

### D8. Which expectation a case is scored against
A case can have several expectation threads, such as the archive's and the user's giftbag fork. Take:
1. the user's own live thread;
2. otherwise the archive's;
3. otherwise refuse, naming them.

Built, generalized (`src/chatddx/catalog/threads.py:expectation_for`): the person's own thread, else the one thread
shared with them, so the archive's counts through init-data's sharing rather than by name. Several to choose from are
refused, naming the threads; none is no expectation. Only threads whose head is in the scorer's expectation schema
count. Still a take.

Rebuilt since by the bench: only the person's own thread counts, and a shared one counts once they take it
(`catalog/threads.py:expectation_choices`; `agents/wip-bench.md`, "What a person is scored against").

## How the old pieces map
| old (504792c) | remastered | notes |
|---|---|---|
| identity (`core/models.py:IdentityModel`) | `identity.person`, `People.find(login)` | `init-data` adds it |
| configuration, 6 slices (`repo/entities/configuration`) | skeleton thread; parts from `Catalog.recipe` | model-dependent chunks are per model, and texts per language: `plan (en, Qwen/Qwen3-8B-AWQ)` |
| stack (`repo/entities/stack`) | engine plus World endpoint (`url_of`, `confirm`) | D6 |
| resolution and refusals (`runtime/resolution.py`) | the compiled skeleton, plus `factors.lint` and `facts.lint` on a provisional trial | warnings, never refusals (`docs/chatddx.md`, "Compromises") |
| case, tags (`repo/entities/case`) | family (name, tags, language), its case, the vignette from the source | |
| targets | expectation thread per case | D8 |
| run, conversation, messages (`history/`) | `RunStarted`, `RunItem` (`Call`, `Turn`s), `RunFinished` | requests kept only as fingerprints |
| client and build | `RunStarted.rig` (`core/rig.py:rig`) | |
| `Run` on pydantic-ai (`runtime/run.py`) | new `chatddx.runner` | D2, D4 |
| scorer, one view each (`scoring/score.py`) | scorer with views and labels (`Catalog.labels`), one per output shape | batch columns become view labels |
| score (`ScoreModel`) | `ScoreStarted`, `ScoreItem`, `ScoreFinished` under a `Scoring` | built per run (phase 2) |
| mean and stderr (`scoring/metrics.py`) | `scorers/aggregate.py` | display only: analysis, not a score |
| per-identity secrets | endpoint `credential`, the name of an environment variable | read by the gate, sent as a bearer (`runner/gate.py:secret`) |

The old `bench/` (the cell, `save`, `NotOwn`, `Ready`, `Trial`, `Sending`, `Outcome`) maps in `agents/wip-bench.md` at
d5ebf52, "The old bench".

## Commands
| command | backed by | what changes |
|---|---|---|
| `help`, `quit`, `exit` | ported | |
| `configurations` | visible skeleton threads, `Catalog.recipe`, `title_of` for each part | columns are recipe parts |
| `endpoints` (was `stacks`) | World endpoints, `title_of(engine)`, URL | D6 |
| `cases` | visible families and their tags | |
| `use CONFIGURATION` | skeleton thread by name: own, shared or `OWNER/NAME` | warns when its per-model chunks are for another model than the endpoint's |
| `on ENDPOINT` | inventory endpoint, then its engine | |
| `cell CONFIGURATION ENDPOINT` | both | |
| `set PART CHUNK` | swap a recipe part and recompile; `none` empties an optional part | a per-model chunk is picked by the engine's model |
| `show` | parts and their descriptions, the request rendered with placeholder fills, the provisional trial's lints, each scorer's reach and coverage | lints replace refusals |
| `show tag TAG...` | as `show`, with coverage over the tagged cases | |
| `show KIND [NAME]` | the component, `Catalog.about`, and the runs reaching it | remastered's kinds |
| `reasoning` | `Facts`: each model × intent (`ReasoningFacts.realized`, refusals) | read from `facts.toml`, not from stacks |
| `seed [SEED]` | the trial's seeds | D3 |
| `run CASE [SEED]` | runner on a trial of one case and one seed, then the scoring pass | |
| `batch TAG...` | runner on a trial of the tagged cases and one seed | order is the schedule: cases by digest |
| `save NAME` | fork, plus name and owner entries | |
| `runs [COUNT]` | runs the person owns (catalog entries), newest first | |
| `replay [RUN]` | `Store.run`, its responses and the request re-rendered from the trial and source | the request isn't stored |
| `score [RUN]` | scores runs with no score under the scoring as it would be built now | |
| `scorers` | visible scorers, their views and labels, and `reaches` against the cell's output schema | |
| `take [from OWNER] [TAG...]` | `Bench.take` of the tagged cases, or all, under each schema they have expectations in | new: a person is scored against their own expectations only |

## Phases
### 1. Runner: `src/chatddx/runner/`
- **The model name an engine answers to**, one method on the engine. Done: `served_model_name`
  (`agents/wip-runner.md`, R4).
- **`http.py`**: POST `/v1/chat/completions` over the stdlib, returning JSON or an SSE stream, with a timeout.
  `assemble(chunks)` gives the completion-shaped response (D2).
- **`gate.py`**: D1 and `confirm`, before the first case-derived request of a run.
- **`send.py`**: render a request, send it and make a `Call`:
  - it uses `fingerprint_request` and `fingerprint_prompt_tokens`;
  - the runaway guard of `runtime/run.py` (`RUNAWAY = 100` whitespace tokens) goes in `Call.error`;
  - a `KeyboardInterrupt` mid-stream is recorded as `stopped`.
- **`run.py`** runs a trial:
  1. `Store.add` the trial's closure.
  2. Append `RunStarted` (`rig()`, `execution`, `tool_code`), and write the run's owner entry.
  3. For each item of `Execution.schedule`:
     - `Source.fetch`, then `prepare_case`, keeping its findings;
     - `render(skeleton, model=…, seed=trial.seeds[r], fills=…)`;
     - send, then append the `RunItem`.
  4. Append `RunFinished` with the findings, then `check_run`.
- **Events** for a UI: an item starting, reasoning text, content text, a tool call, usage, an item ending (its
  `RunItem`) and a finding. They're synchronous: `Store` has no async API (`docs/store.md`, "Known gaps"). Above
  concurrency 1, calls go out on threads and the events still come on the caller's (`agents/wip-runner.md`, "Phase
  4").
- **Tests** in `src/chatddx/runner/test/`. They:
  - start the fake in a thread on port 0, as `inventory/test/test_serving.py` does;
  - point a temporary World inventory at it;
  - share a seeded template database, like `store/test/conftest.py:migrated` with `seed` run once.

  They cover:
  - streamed matching unstreamed;
  - the seed being sent unless greedy;
  - prompt tokens being fingerprinted, not stored;
  - runaway (the fake's `--runaway`);
  - a stop mid-stream;
  - `case.drift`;
  - the gate's refusal;
  - `confirm` refusing an endpoint that serves another digest;
  - a clean `check_run`.

### 2. Scoring pass
Built but for what needs a person (`agents/wip-runner.md`, "The scoring pass"): the answer reader and
`score_run`, which takes a `Scoring` its caller builds. Which scorers apply, D8 and outstanding runs wait for phase 3.
- **`chatddx.scorers.answer`** (D5).
- **Which scorers apply**: the visible scorer threads whose views reach `Skeleton.output_schema`
  (`factors/select.py:reaches`, the same check as `view.unreachable`).
- **Per run and applicable scorer**:
  1. Build a `Scoring` of the scorer and the expectations of the run's cases (D8), and `Store.add` it.
  2. Append `ScoreStarted`, then a `ScoreItem` per item and view via `scorers/scorer.py:score`, then
     `ScoreFinished`.
  3. Run `check_score`, and write the score's owner entry.
- **Outstanding runs**: runs the person owns with no score under the `Scoring` digest that would be built now. A
  changed expectation makes a new digest, so `score` catches up, as the old one did.
- **Judged views** stay refused (`score` raises `NotImplementedError`) and are shown as "not yet". Since then judges
  score (`agents/wip-judges.md`, phases 4 and 5).
- **Tests**: each sample output shape against its scorer; a changed expectation makes a run outstanding.

### 3. Reads for a person
Built, the `Bench` with the shell in 4a (see "4. The shell"). What was built here:
- `Store.started`, `runs_of`, `finished`, `scores_of` and `reaching` (`src/chatddx/store/store.py`);
- `Catalog.visible`, `visible_families` and `expectation_for`, with the rules in `chatddx.catalog`
  (`model.py:About.shows`: live, and owned or shared);
- `src/chatddx/store/reads.py:Reads(conn, person)`: threads and families, a thread by name (whole, then
  `OWNER/NAME`, since sample names hold slashes), runs (also by id prefix, and those reaching a digest), the scorers
  that apply to a run, the scoring it would be scored under (D8), and the runs still to score;
- tests in `src/chatddx/catalog/test/` and `src/chatddx/store/test/test_reads.py`, on the sample as init-data lands
  it with a giftbag.

`Reads` and its tests have since moved to `src/chatddx/bench/`, without the runs still to score, and `Reads` was
folded into `Bench` (`agents/wip-bench.md` at d5ebf52, "Phase 2").

"Applies" is the plan's rule: every view of the scorer reaches the run's output schema. A view that picks the whole
answer reaches any schema, so the sample's `free-text` and `raw` scorers apply to every run; the pattern scorer then
reads a structured answer as its JSON text. Narrowing that, say to scorers written for the run's output shape, would
be a decision.

The plan, as written:
This closes `docs/store.md`'s known gap "Runs and scores can't be found". The store gets:
- live threads of a kind that the person owns or collaborates on, by name and as `OWNER/NAME`;
- the visible families with their tags and language;
- the runs a person owns, newest first, also by UUID prefix;
- the runs of a trial (for "run N of trial X") and the scores of a run;
- the runs whose trial reaches a digest, through the factor reference rows (for `show KIND NAME`).

A person-scoped layer, the old `Bench`'s role, is planned in `agents/wip-bench.md`.

### 4. The shell: `src/chatddx/repl/`
- **Entry**: `chatddx repl LOGIN [--world DIR] [--history PATH]`, a subcommand in `src/chatddx/cli.py`. `--world`
  (`CHATDDX_WORLD` by default) is a World directory: its inventory locates the vignettes and endpoints, and its
  `facts.toml`, when it has one, is loaded beside the bundled facts, as for `init-data`.
- **Modules**, after the old ones:
  - `commands.py`: the `Command` table, `handle` and `complete`, nearly verbatim;
  - `shell.py`: the prompt and the completion cache;
  - `render.py`: on rich, the streamed transcript, the batch's columns and live line, views, scores and validity;
  - `choosing.py`, `listing.py`, `inspecting.py`, `running.py`, `reviewing.py` and `scoring.py`.
- **Ctrl-C** keeps the old semantics (`running.py:_Stopping`, `_held`), made simpler by a synchronous runner:
  - in a batch, the first press sets a flag that is checked between items;
  - the second raises into the send, which records the item as stopped.
- **In three steps**:
  - 4a, inspecting: `help`, `configurations`, `endpoints`, `cases`, `use`, `on`, `cell`, `set`, `save`, `show`,
    `reasoning`, `scorers` and `seed`. It needs only phase 3, so it can be built alongside phases 1–2.
  - 4b: `run` and `batch`.
  - 4c: `runs`, `replay` and `score`.
- **Tests**: the old tests' scenarios, rewritten for the new names and columns. They use a `say(*lines) -> text`
  fixture over `Console(record=True, width=200)`, as the old conftest's `say_to` did.

#### Built: 4a
`chatddx repl LOGIN [--world DIR] [--facts PATH …] [--history PATH]` (`src/chatddx/cli.py`) connects as `DB_USER` in
autocommit mode, as the runner needs (R6), and refuses a login with no person. `rich` is a dependency now (D4).
- **The bench**, `Cell` and `Bench`, then `bench.py` here, now `src/chatddx/bench/` (`agents/wip-bench-api.md`,
  "Package").
- **`shell.py`** (`Repl`: the cell, the seed, the prompt, the completion cache), **`commands.py`**, **`render.py`**
  (styles and helpers only; the streamed transcript comes with 4b), **`choosing.py`**, **`listing.py`**,
  **`inspecting.py`**, **`scoring.py`** (`scorers`), **`running.py`** (`seed`) and **`loop.py`** (readline, history,
  and lines from a pipe, the old `repl/cli.py`).
- **Tests**: `src/chatddx/repl/test/`, 48 of them, on the sample as init-data lands it from the sample World with a
  giftbag, seeded once per session. The old `test_cli.py` is `test_loop.py` here, after the module it tests. Test
  directories were made packages since, so test files may share a name across packages.

Takes made while building, all still open:
- **Per-model names.** The plan picked a per-model chunk by the engine's model for `set` only. `use`, `cell`, `set`
  and `show KIND NAME` all do it: a name that names nothing alone is tried as its one variant the cell's engine's
  model may use, `NAME (LANGUAGE)`, `NAME (MODEL)` or `NAME (LANGUAGE, MODEL)` (`src/chatddx/catalog/variants.py`),
  so `cell plan qwen3-8b-awq@fake` holds `plan (en, Qwen/Qwen3-8B-AWQ)`. Without an endpoint, `use plan` is refused,
  naming the per-model ones; a name made in more than one language is refused, naming them. Picking the variant in
  the language of the cell's cases is open (`docs/curation.md`, "Picking a variant by the case's language").
- **Names hold spaces.** A command's last name takes the rest of the line (`use plan (en, Qwen/Qwen3-8B-AWQ)`, no
  quotes), and `cell` takes its endpoint from the last word. Completion goes word by word, and offers the name alone
  of each per-model one.
- **The cell's lints straight away** (see "Risks", "A configuration on another model's endpoint"). `use`, `on`,
  `cell` and `set` print what `factors.lint` and `facts.check_pairs` say of the cell's pair, run as a trial of one
  case: `on gpt-oss-20b@fake` under `plan (Qwen/Qwen3-8B-AWQ)` gives `facts.sampling_unmatched`. `show` lints the
  trial of every case it counts, languages included.
- **`set`** compiles at once, so a part that doesn't compile is refused and the cell stays as it was. Setting the
  configuration's own chunk unsets the part; `none` takes an optional part out.
- **`save NAME`** writes the compilation with the running code as compiler when parts are set. The person's live
  thread named NAME gets a new edit, or none when the digest is its head ("unchanged"); without one, a thread named
  NAME is forked from the configuration's edit the cell holds.
- **`show`** lists the parts with the catalog's title and `describe`, renders the request with placeholder fills
  (`‹vignette›`), and leaves the output's schema and the tools' parameters to `show output` and `show tool`. Then the
  lints, and per scorer view the cases it can hold the cell to: a case has it when the expectation the person reads
  under the scorer's schema (`Catalog.expectation_for`) gives the view's expectation selector something to pick. The
  old count also named patterns that don't parse; that reading is the pattern scorer's, and isn't here.
- **`show KIND [NAME]`**: the kinds are `configuration`, the nine parts, `tool`, `scorer`, `judge`, `expectation`
  (since taking, by the thread's name, the person's own first), `expectation_schema`, `canary_set`, `model` and
  `engine`, plus `case` and `endpoint`. A component's fields, its
  catalog entries, and how many of the person's runs reach it (`Reads.reaching`). A case shows its source, the
  vignette fetched from the World, and the expectation the person reads: their own thread's head, else a shared one.
- **`reasoning`**: a column per model the facts know, headed by the endpoints serving it, and a row per level, plus
  the default and the thinking budget; ▸ marks the level the cell holds, by the chunk the facts write for it.
- **`seed`**: drawn below 100,000, held from 0 to 2³¹−1, and "greedy: the seed isn't sent" on a greedy cell, also
  in `show` (D3).

Left from 4a:
- **The bench as a module of its own** (the user's remark): done, `agents/wip-bench.md` at d5ebf52, "Phase 0".
- **An unsaved cell's language is unknown.** `Catalog.language_of` reads the store, so after `set` the request's
  language was `language.unknown` even where the recipe's chunks have one. Done: `Bench.findings` takes the request's
  language from the cell's recipe (`agents/wip-api.md`, "Trying a variation").
- **Runs of a scorer.** Done in 4c: `show scorer NAME` counts the runs it scored.
- **The seeded sample fixture**: done, defined once, now as `src/chatddx/conftest.py:curated` (`agents/wip-bench.md`
  at d5ebf52, "Phase 2", step 5).

#### Built: 4b
`run CASE [SEED]` and `batch TAG...` (`src/chatddx/repl/running.py`), on the runner and the scoring pass through
the bench (`Bench.start`, `Bench.score`).
- **`run`** makes a trial of the cell, the case and the seed, the shell's unless one is given, and starts it at the
  cell's endpoint. The gate's refusals come before anything is written, as `refused: …`: `plan-web` on the sample,
  whose source is sensitive, or an endpoint that doesn't answer. The transcript streams the thinking, labelled, the
  answer, each tool call as `[name] arguments` with its `[result]`, and the tokens used. After `finish`, the run is
  scored under every scorer that applies (`Reads.scorers`, now `Bench.scorers_for`), each as its scoring would be
  built now (`Reads.scoring`, now `Bench.scoring`; D8; `runner/score.py:score_run`). Then: `valid` or `invalid: …` for an output with a schema,
  `unread: …` for an answer that can't be read, the call's error when it has one, what the scorers' views read, the
  scores with their reasons, `check_run`'s findings, and `recorded as run N of trial X`, N counting the person's runs
  of that trial.
- **`batch`** makes one trial of the cases with any of the tags and the shell's seed, so one run. A line per case,
  in the schedule's order (cases by digest), counts its tokens as they stream and says how the call went:
  `completed`, `valid`, `invalid`, `unread`, `errored` or `stopped`, with the call's error. The run is then scored,
  and a table gives each case's value per scorer view, and another, per view, how many were scored, their mean and
  standard error (`scorers/aggregate.py`), and how many have no value.
- **Ctrl-C** as planned (see "Modules"): in `run`, the call hangs up and is recorded as stopped; in a batch, a first
  press is `Running.stop()`, so the case under way finishes and the batch stops, and a second hangs that call up
  too. While a run is finished and scored, a first press waits for it, and a second goes through.
- **Tests**: in `src/chatddx/repl/test/test_running.py`, with the sample World on free ports and the fake vLLM
  serving the Qwen endpoint in a thread; Ctrl-C is pressed with `signal.raise_signal` as a call streams.

Takes made while building, all still open:
- **Scores come after the run.** `score_run` takes a finished run, so a batch's lines say how each call went, and the
  scores follow in a table. The old lines carried each case's scores as it ended.
- **Which views are shown.** After `run`, each selection the applying scorers' views make is listed once, by the
  first label that makes it, and a label used again gets its scorer's name, as `differential (diagnoses)`. A view that
  reads the answer whole isn't listed, since the transcript holds it.
- **An unsaved cell's compilation is stored** before its run, with the running code as compiler, so the run's
  skeleton keeps a recipe and a title.
- **Greedy cells run**, with the notice, rather than being refused a seed (D3). The trial still holds the seed.
- **The transcript leaves out trailing whitespace**, so a runaway's newlines don't fill the screen; the cutoff is
  said after it.

Left from 4b:
- **A structured answer cut short is unread.** A runaway on `plan` stops inside the JSON, which isn't salvaged
  (`agents/wip-runner.md`, "The scoring pass"), so every view scores "no answer". The old repl closed the structure
  where it stopped (D5's salvage); free text keeps what came.
- **No word on reasoning that wasn't heeded**, as the old `bench/outcome.py:unheeded` gave (`agents/wip-runner.md`,
  "Afterwards"), and no `[thinking in content]`: the runner can't tell reasoning a parser missed.
- **Two tool calls in one response run together** on one transcript line: a call's first delta is taken as its
  name, and the deltas don't say where the next call begins.
- **The test databases.** Dropping one `WITH (FORCE)` failed now and then: a test's `DB_USER` session had closed but
  not yet ended on the server, and `DB_ADMIN` may not end it. `src/chatddx/conftest.py:_settled` waits for the
  database's sessions to end before a copy or a drop. The runner's tests had failed the same way.

#### Built: 4c
`runs [COUNT]` and `replay [RUN]` (`src/chatddx/repl/reviewing.py`), and `score [RUN]` (`scoring.py`). What shows an
answer and its scores is shared by all of them, in `render.py`.
- **`runs`** lists the person's runs, newest first (`Reads.runs`), the last 20 or COUNT: the run's and the trial's
  ids, when, what ran (`Bench.described`: the configuration's title, the endpoint, the case or how many, the seeds),
  how it went (an item's outcome and error, or a count of each outcome; `unfinished` without `RunFinished`), and per
  scorer its latest score's view means, as `plan 0/0/0/—`.
- **`replay`** shows the latest run, or the one an id prefix names (`Reads.run`): when, whether it finished, where
  it ran, and on which chatddx. The request isn't stored, so each item's first request is rendered again from the
  trial and the source and held to its fingerprint (`Bench.rendered_again`), saying when the vignette at the source
  isn't the one sent, or the request renders otherwise now. A run of one item is told again as it streamed, from the
  stored responses and tool runs (`Transcript.item`), then its answer and latest scores; a batch gives its lines,
  the score table and the summary.
- **`score`** scores each finished run under the scorers that apply to it and have no score of it under the scoring
  as it would be built now (`Bench.unscored`), so a changed expectation leaves a run to score again; then sums up
  over every score given. With RUN: that run alone, or why not (`unfinished`, `no scorer applies to it`, or
  `scored already, as the scorings are now` with its scores). Scoring holds Ctrl-C as `run` does.
- **`show KIND NAME` and `show case NAME`** sum up the latest scores of the person's runs with it; `show scorer NAME`
  counts and sums up the runs it scored.
- **Completion**: `replay` completes the latest 20 runs' ids, and `score` the runs left to score, both fresh at each
  Tab.
- **Tests**: `src/chatddx/repl/test/test_reviewing.py` and `test_scoring.py`. A changed expectation is a new edit of
  alice's own expectation thread.

Takes made while building, all still open:
- **What is left to score is worked out per run** (`Bench.unscored`); `Reads.outstanding` is gone
  (`agents/wip-bench.md` at d5ebf52, "Phase 2", step 3).
- **The latest score per scorer** is what `runs`, `replay` and `show` read. Older ones stay in the ledger, and
  `scores_of` lists every score of a run, whoever gave it.
- **The runs list shows means** per view, so a batch fits a line per scorer.

Left from 4c:
- **An unsaved cell's runs are titled by their recipe**, as `case · diagnoses-tool · recommended (…) · off (…)`,
  since the cell's label (`diagnoses-tool (…)+reasoning=off`) isn't stored. A catalog entry on the run, or a title
  built as a variation of the closest configuration, would say it shorter.
- **Only an item's first request is rendered again.** A later round's request could be rebuilt with `next_request`
  from the stored responses and tool runs.

### 5. Tool rounds
Built in the runner (`agents/wip-runner.md`, "Phase 5").
- The `next_request` loop, with `max_rounds`, `Turn` and `ToolRun`.
- Tools are found among the code chatddx ships (`core/rig.py:entry`, `tools/shipped.py:TOOLS`), and the version each
  ran at goes in `RunStarted.tool_code`.
- D1 gates tools.

It comes last: `plan-web` can't call its tool on vLLM 0.24 anyway (G8; `docs/vllm.md`, item 10).

### 6. Docs
Agents propose and humans write `docs/*`, with suggestions inline above what they would change (`AGENTS.md`,
"Docs"). The manual's draft stays in `agents/` until it's adopted. Where the shell's changes stand:
- a new `docs/repl.md`, the old manual rewritten. Outstanding: it starts from the cross-check with
  `agents/wip-repl-manual.md` (see "Start with this");
- `docs/factors.md`: streaming (D2) is in "Rendering". Not in the docs: that the shell runs the lints ("Lints"), to
  suggest once the shell is solidified;
- `docs/catalog.md`: the runner writes a run's owner (D7, "Owners"), and a run of a variation nobody saved has a title
  ("Titles"); both in the docs;
- `docs/store.md`: the listings of phase 3, and what is left to score per run, left the store with `Reads`
  (`agents/wip-bench-api.md`, "Runs and scores"). The tests' databases waiting for their sessions to end is
  in `docs/store-api.md`, "Tests";
- `docs/ledger.md`, `RunStarted`, and `agents/wip-clearance.md`: the endpoint and the interim gate (D1, "Run start"),
  and `replay` rebuilding a run's first requests ("Some of what happened isn't checked"); all in the docs;
- the surprises met while building the shell: loading the environment is in `AGENTS.md`, "Environment", and serving
  the sample World's fakes in README and `docs/vllm.md` (`chatddx fake-engines`). Test file names no longer need to be
  unique across packages, since every test directory is a package.

### 7. Completion
Decided: the four steps in "Start with this". Below, everything else is a take until "Questions for the user" are
answered.

#### 1. Quirks and misbehaviour
Decided: first, before the sample. Built:
- **An interrupted scoring is finished.** `Bench.score` runs the scoring pass itself (`Grader.start`, `send`,
  `finish`) rather than `score_run`: a `KeyboardInterrupt` while a scorer sends finishes its score with what it has,
  and the scorers after it are refused as `stopped`; an error while it sends finishes it too. In the repl, `Held`
  (`running.py`) holds the first Ctrl-C while a run is written down and scored, and says so; the second goes through
  once, while scoring, and the repl says "scoring stopped: score scores what is left". `score` stops at that run.
- **Only a whole score counts** against what is left to score (`Bench.unscored`): finished, an item for every run item
  and view, and no judge call stopped. A take, the user's question 4 of the earlier list: a stopped scoring leaves the
  run to score, since nothing else could score it again.
- **A score's findings are said**: those the pass noted (`ScoreFinished.findings`) and those `check_score` gives,
  after `run`, `batch`, `score` and `replay`; after `run` and a one-item `replay` without `answer.*`, which the answer's
  own line says.
- **A batch says each finding once with how often** it came, `(×4)`, as `score` and a batch's `replay` do.
- **Rich markup is off** (`shell.py:console`): the repl never used it, and `help`'s `[from OWNER]`, a vignette's or an
  answer's brackets were read as markup.
- **`show case`** sums the case's own items; `show expectation` its case's.
- **`show` of a part, a tool, a judge, an expectation or an expectation schema** finds its runs: `Bench.reaching`
  reaches through compilations, and `Bench.scored_by` takes anything a scoring holds. The API's run filters share
  both.
- **"no expectation_schema in the cell"**, without the article.
- **`batch`** completes every tag, once each; `show`'s completion offers no `none`, which only `set` takes.
- **`quit now`** is refused as usage.
- **A cut stream's tokens** are counted from the token ids its choice holds (`bench/outcome.py:usage`), so a runaway's
  line and `run` say them.
- **Scorers in one order**, by name: `Bench.scorers`, and so `scorers` and `show`, as score tables have it.
- **A piped session stops at its first error** and exits 1. `replay`'s "the request differs" is said in red without
  being an error.

#### 2. The sample as a complete example
Decided: complete is every table a data set and a World can hold used at least once; the sample's judge prompt is
drafted now, and the sample gets made-up appendices and a canary set. Also decided: the data set moves from the
package into the sample World, `worlds/sample/_data/`, as the test World keeps its own.

Built. The sample is two parts that a new World follows: the data set (`worlds/sample/_data/`) and the World
(`worlds/sample/`), laid out as Kompismoln's is. `src/chatddx/curation/test/test_sample.py:
test_the_sample_uses_every_table_a_data_set_and_a_world_hold` holds it to that. What came:
- **Data sets hold appendices and canary sets** (`curation/plan.py`, `curation/write.py`). A cases file names a case's
  `appendices`, texts by name, each landed as an archive thread of its own name, told apart by its vignette
  (`curation/write.py:binds`), and `[[case.<id>.with]]`, cases of
  the family that send them in the order named, each with `targets` of its own when it has them. `canary_set` is a
  table of `factors.toml`. The test World holds one of each (`whitespace`'s `labs`, `probe`), read by
  `curation/test/test_tables.py`.
- **The data set's default**: init-data takes the World's `_data/` unless `--data` names another (`cli.py`, `DATA`),
  so `init-data alice --giftbag` loads the sample, and Kompismoln names `--data worlds/sample/_data`. A take: it
  revisits `agents/wip-test-world.md`'s "Loading it stays explicit" (see its "Why `_data`").
- **A judge**, drafted by an agent until Olof writes his (`agents/wip-judges.md`, "For Olof, later"): instructions
  and a prompt of purpose `judge` (the answer and the note; no vignette), the outputs `verdict` and `grade` with
  schemas whose `examples` the fake answers by seed, and their Swedish translations; the recipes `judge` (greedy)
  and `judge-graded` (recommended sampling, per model); the judges `verdict` on `qwen3-8b-awq@fake` and `graded` on
  `gpt-oss-20b@fake`; the scorer `notes`, Olof's comment and answer judged as met and his comment graded. The judges
  name the sample World's engines, so Kompismoln skips them and `notes` until it names judges of its own; its
  `factors.toml` is the engine import's to write whole, so where those go is open.
- **Made-up appendices**, labelled so: `labs` and `ultrasound` for `Dutchfall11w`, whose ultrasound changes the right
  answer from the targets' aneurysm to an infected, blocked kidney, held to targets of their own in two cases; and
  `blood-gas` for `casesfromedn1`, in Swedish, which confirms its targets.
- **A canary set**, `basics`: two greedy probes and a seeded one. No run sends it yet: `Bench.start` passes no canary
  set.
- **A remote engine with a credential**: `mistral-small@remote`, Mistral Small 3.2 from provider `fake`, whose
  endpoint reads its key from `CHATDDX_SAMPLE_KEY` (set in `.env-container` and `.env-devshell`), and the facts of its
  model in the World's `facts.toml`, from its makers' model card. `chatddx fake-engines` stands in for a remote engine
  on this machine (`cli.py:_stand_in`), and the fake vLLM takes `--api-key` (`fake_vllm/served.py`, `server.py`). The
  stand-in is cleared for the sample, as it runs here. The model adds a third variant of every per-model recipe.
- **The World's endpoints and host** moved to an included `endpoints.toml`, as an engine import writes them.

- **Sample runs**, so that every repl command has something to show: `chatddx samples alice` runs the sample World's
  ten, answered by the fake from scripts (`agents/wip-sample-data.md`, "Sample runs"). A case that sends appendices
  is titled `Dutchfall11w with ultrasound`.

#### 3. Calibration
With the user, on the sample, once it has its judge. What waits for it, since it depends on what the sample gives:
- **Judged views**: how a verdict, its `why`, the judge's calls and endpoint show in `run`, `batch`, `score` and
  `replay`; `show judge` and `show endpoint` counting judge calls; `scorers` naming the judge.
- **Scoring while it goes**: judge calls streamed as events, halted by Ctrl-C, the scoring pass giving the bench a
  handle as the runner does (`runner/score.py:Grading`; today `score_run` sends with no events).
- **A judge two endpoints serve**, which bars its scorer silently, and naming the endpoint to judge at.
- **What applies to a run**, and the whole-answer scorers' noise on structured runs.
- **An answer that didn't come**, scored 0 or no value.
- **`show`**: what each part becomes on the model, the served name as a whole digest, the prompt's length, `on`
  keeping another model's variant, `configurations`' rows per model and owner.
- **Left from 4b and 4c**, as the user weighs them.

##### Round 1, on the sample runs
Started (the user: "start the calibration on the sample runs"): `chatddx samples alice` on a fresh database, then
`runs`, `replay` of each, `score`, `scorers`, `show` of the judges, endpoints, a scorer and a case, and a live `run`
and `batch` on `fake-engines` with the judges called.

Fixed, as plain defects:
- **`replay` of a stopped run says `stopped`** (`render.py:show_answer`), where it said `unread: no content` or
  nothing.
- **`show judge NAME` counts the runs it judged and its calls**, summing up only its own views, where it counted
  every run its scorer scored and showed the other judge's view (`inspecting.py:_judged`).
- **`show endpoint NAME` counts the judge calls made at it** (`inspecting.py:_judge_calls`), from the scores'
  `JudgeEndpoint`s.
- **`batch` says what it was recorded as**, as `run` does.
- **`scorers` names a judged view's judge** (`verdict, judged by verdict`), and `show` titles digests nested in
  JSON, so `show scorer notes` names its judges.

For the user, each with a take, most telling first:
1. **What applies to a run.** Every replay carries three or four `no target` rows: `notes` applies to every case, and
   no case has a `dont_miss` (item 10). A plan run is scored by `free-text` and `raw` ("unguided free text", whose
   `first_mention` is the diagnosis's offset in the JSON, 210) and by `diagnoses`, whose differential lists the
   plan's diagnosis objects as JSON; a batch's table is nine columns, `notes` `—` in all but one row. Take: a view
   reading the whole answer applies to text outputs only, and a scorer applies when its views are offered
   (`reaches`), so `scorers`' "the cell" and applicability agree; `replay`'s and `run`'s tables leave out `no
   target` rows, saying once which views had none, while the summary still counts them.
2. **A score's meaning on the screen.** `first_mention` is a character offset, 0 when named first, beside 0–1 scores
   where 1 is best, so its best reads as a failure. Take: a value that isn't 0–1 shows with its unit (`@44`).
3. **The detail column** is the detail's JSON: `{"answer": "1. {\"diagnosis\"…`, `{"seeds": [1.0]}`. Take: an
   answer or a reason as plain text; a judged view as its seeds' values and the judge's `why` (item 4).
4. **Judged views.** The judge's `why`, calls and endpoint show nowhere, and scoring is silent while judges are
   called, so with real judges the repl looks hung. Take: `replay` and `run` say each judge call's `why` under the
   scores, and scoring has a live line per judge call, as `batch` has per case.
5. **An answer that didn't come** scores 0 under `reciprocal_rank` and `mentions` but no value under
   `first_mention` and the judged views, so a 503 pulls a batch's mean down. Take: no value, reason `no answer`, for
   every view, and the summary splitting `no answer` from `no target`. A failed call is the engine's, not the
   model's, but the user may weigh it otherwise.
6. **`configurations`** is 64 rows on the sample, every recipe × 3 models × alice's fork and archive's, names
   clipped. Take: a row per name and language, the models as a column, a fork's owner as `yours, from archive`;
   `configurations NAME` for the per-model rows.
7. **`use` before `on`** is refused ("picked by the endpoint in the cell"), and `on` keeps another model's variant,
   with only a sampling warning. Take: the cell holds the name, and `on` picks that name's variant for the model,
   saying so.
8. **A language in a name.** `use free-text-guided` is refused as made in two languages; the whole per-model name
   must be typed. Take: `use free-text-guided sv`, the model from the endpoint.
9. **Cases with appendices** can't be run or shown: `run` takes a family, and `show case Dutchfall11w` lists neither
   its appendices nor the cases that send them, and counts the bare case's runs only. Take: `run` and `show case`
   take a case's title, `Dutchfall11w with ultrasound` (`samples/run.py:case` moves into the bench), and `show case`
   lists the family's appendices and cases, each with its own targets.
10. **No case has a `dont_miss` target**, so the `dont-miss` view of `plan`, `diagnoses` and `free-text` never has a
    value. Take: Olof gives a few, or some are made up and labelled so, as the appendices are.
11. **A structured answer cut short** (left from 4b): the `runaway` sample lacks only its closing brace and is
    unread. Take: salvaged by closing the structure, said so in the outcome.
12. **A batch's lines** come in the trial's case order, by digest (14w, 12w, 13w, 15w). Take: sorted by case title
    on the screen; the sending order stays the trial's.

Not shown by the sample, so not calibrated yet: a judge two endpoints serve (each judge's engine has one), and a
canary set sent with a run (`Bench.start` passes none; `show canary_set basics` shows it).

#### 4. The manual
`docs/repl.md`, drafted in `agents/` from the calibrated shell, with examples on the sample, and proposed for
adoption with the solidify pass on the repl's tests, which are `wip`.

#### Questions for the user
1. **The order of steps 1 and 2.** Decided: step 1 first, and built.
2. **The sample's judge prompt**: decided, drafted now; Olof's replaces it as an edit, which reaches giftbag forks as a
   proposal.
3. **Appendices in the sample**: decided, made up for it, and labelled so.
4. **A canary set in the sample**: decided, yes; and every table, so the remote engine with a credential too.
5. **init-data's default data set**, the World's `_data/`: a take (see step 2).

## Left out
What the port left to others, and where each is planned:
- **The portal** (`agents/wip-portal.md`), and what the old layers held for it:
  - `bench/plan.py`'s crossing is the batch planner (`agents/wip-batch.md`). Until it exists, `batch` runs one
    variation over the tagged cases; it could take a batch then. Batch order moved there too.
  - The worker (`agents/wip-worker.md`), planned apart from the planner around one contract.
  - `bench/held.py`, what holds a configuration, for the portal's pages that delete: the repl's part is
    `Bench.reaching` and `Bench.scored_by`.
- **Sample runs** (`chatddx samples`): not the repl's. They are test data for every edge, the repl's, the API's and
  the portal's, and are built with the sample data (`agents/wip-sample-data.md`, "Sample runs").
- **Endpoints with a credential** were refused here until secrets had a home; the gate reads one now. The sample World's
  remote engine has one; the real World has none.
- **Judges** for the free-text notes were left out; they score now, and showing them is "7. Completion"'s.
- **The injected transport** (`FakeTransport`): tests run the real fake server instead, and sample runs have it
  answer from a script.

## Risks and smaller open points
- **A configuration on another model's endpoint.** The old `show` said what each slice became on the stack.
  Here, model-dependent chunks are fixed at seed time, so such a mismatch shows only through
  `facts.sampling_unmatched` and the `vllm.*` lints. `use`, `on` and `cell` should say so straight away: they do,
  since 4a.
- **The same vignette under two names** can't be in two families: adopting a vignette another family holds, by id or
  by fingerprint, is refused (`src/chatddx/catalog/families.py:check_adoptable`), so a batch runs it once.
- **`return_token_ids` on remote engines** is still undecided (`docs/factors.md`, "Smaller issues"). The fake
  and vLLM accept it.

## The old manual, checked
`agents/wip-repl-manual.md` against the shell at 5d4bff1, section by section, driven on the sample World with
`fake-engines` (and `--runaway`), through a pipe and a terminal. Where the shell does as the manual says, nothing is
listed.

- **Starting**: `fake-engines` serves the sample World's fakes, rather than `fake-vllm` one model; `repl` takes
  `--world`, `--facts` and `--history`.
- **A few words first**: stacks are endpoints, the six slices are nine parts (`instructions`, `few_shot`, `prompt`,
  `output`, `sampling`, `reasoning`, `passthrough`, `translations`, `toolset`; no `coercion`), targets are
  expectations (D6).
- **`help`** lists `endpoints` and `take` too. It prints `take [TAG...]`: rich reads `[from OWNER]` as markup and
  drops it.
- **`configurations`**: a column per part some configuration sets, and every configuration per model, once as
  the archive's and once as alice's giftbag fork: 36 rows for 9 recipes.
- **`endpoints`** (was `stacks`): endpoint, engine, model, URL and what it is cleared for. The engine's title repeats
  the endpoint's name.
- **`cases`** adds a count per tag.
- **Tab** completes word by word, per-model names included. `batch` completes its first tag only.
- **`use`** without an endpoint refuses a name only per-model configurations have, naming them; the old shell held
  `plan × ?`. `use archive/plan` runs without `save`; the old shell asked for `save` first.
- **`on`** to another model's endpoint keeps the variant made for the first model and lints it
  (`facts.sampling_unmatched`); `use` picks again.
- **`set`**: `set reasoning off` keeps the sampling written for "on", and no lint says so (`facts/lint.py:_sampled_for`
  checks the model, not the level). On gpt-oss, `set reasoning off` is refused naming only Qwen's `off`, without why
  gpt-oss has none. The prompt grows with every part set, past a line.
- **`show`** gives a table of parts, the request rendered with placeholders, the body, the lints, and per scorer view
  how many cases it can hold the cell to. It doesn't say what a part becomes on the model (the default reasoning shows
  `—`), refusals are lints, and a pattern that doesn't parse isn't named. The engine's served name is the whole digest.
- **`show tag`** holds.
- **`show KIND NAME`** takes 22 kinds. `show case` shows the source, the vignette, the tags, the language and the
  expectation's fields that exist; the old `missing` and `none expected` lines are gone. Its runs sum every item of
  every run that reached the case, the batch's other cases included. `show` of a part, a tool or an expectation schema
  always says "no runs of yours" (`agents/wip-bench.md`, "Reaching a chunk finds no run"). "a expectation_schema" and
  "a appendix" in the refusals.
- **`reasoning`** holds, with the endpoints heading each model and why a level is refused.
- **`seed`**: no `seed none`, and a greedy cell runs with a notice (D3).
- **`run`** holds, with `valid`, tool calls as `[name] arguments`, and the gate's refusals before anything is
  written. A plan run is scored by the plan's scorer and by `diagnoses`, `free-text` and `raw` too, whose views read
  its JSON text (`free-text`'s `text` gives 19, the characters before the diagnosis in the JSON); "What applies".
  A score's detail may be the raw JSON of what it read. A runaway's free text is kept and scored; a structured one is
  unread and every view scores `0 no answer`, and no token line follows, as a cut stream has no usage. A stopped run
  is scored too, with 0 where the answer didn't come.
- **`batch`** holds, with the scores in a table after the lines. A case with no target and a scorer that found
  nothing both show `—`, where the old lines left the first blank. Stopped and runaway lines count 0 tokens; a
  runaway's structured answer reads `errored`; each failed call's `call.failed` is repeated after the table. Cases go
  one at a time though the endpoint takes four. An English configuration over Swedish cases says nothing at run
  time; `show tag` lints it.
- **`runs`** holds, with means per view; an unsaved variation's run is titled by its recipe ("Left from 4c").
- **`replay`** holds, with where it ran, the build, and whether the request renders as it was sent; a batch gives its
  lines and tables, not each case's transcript.
- **`scorers`** holds; on a plan cell every view "offers it", since a whole-answer view reaches any schema.
- **`score`** catches up after an expectation changes, every run that reached the case included.
- **`save`** holds, with "unchanged" and "a new version"; the old "yours now too" line is gone.
- **Leaving**: `quit`, `exit`, Ctrl-D; `quit now` quits too. A piped session echoes its lines, keeps going after an
  error and exits 0.
- **Judges** can't be driven by hand: the sample has none, and the test World loads only under pytest (its tools
  are the runner's test tools).

New since the old manual: `endpoints` and the clearance gate, `take`, `show KIND` over every kind, `show`'s request
and lints, `reasoning`'s refusals, multi-view scorers with reasons, `score` catching up, `replay` checking the request
and naming the build, and run ids in "recorded as".

Step 1 of "7. Completion" takes the defects: `help`'s markup, `show case`'s sum, the article, `batch`'s completion,
the repeated warnings, and the token count of a cut stream. The rest wait for the calibration:
- **An answer that didn't come scores 0** under `reciprocal_rank` and `mentions` (`scorers/patterns.py`), so a
  stopped run or a server's error pulls a mean down as a wrong answer would; `first_mention` gives none. Take: no
  value, with the reason, so that only what a model answered is scored, and how often it didn't answer is counted
  apart, as `without a value` already is.
- **`use OWNER/NAME` runs another's configuration as it is**; the old shell asked for `save` first. Take: keep it, as
  a run's trial is stored whoever owns the thread.
- **`on` keeps the variant**; take: pick the new model's variant of the same plain name when the cell was chosen by one.
- **The whole-answer scorers on structured runs** ("What applies"): noisy scores like `text 19`.

# Repl

The repl, `chatddx repl LOGIN`, is a shell for one person over a World: choose a configuration and an endpoint, see
what a request would be, run cases, and look back at runs and score them. It works through the bench
(`src/chatddx/bench/`, docs/bench.md), the person-scoped view the API shares, and strings together pieces
documented elsewhere: the runner and the scoring pass (docs/runner.md), what a request is made of (docs/factors.md),
names, owners and titles (docs/catalog.md), endpoints and clearance (docs/inventory.md), and model facts and their
lints (docs/facts.md).

This document describes what the shell does and why. Its modules, the command table and what each command calls on the
bench are in docs/repl-api.md; how to use it, command by command, is the manual (docs/repl-manual.md).

The repl writes only runs and scores, through the runner and the scoring pass, a person's saved configurations
(`save`), and the expectations they take (`take`). Authoring, the chunks, cases, appendices and expectations a person
writes and the edits and proposals between people, is the API's and the portal's. What the repl works with comes from
a World and its data set, and the sample World (`worlds/sample/`) is the example a new World follows.

## Starting
`chatddx repl LOGIN [--world DIR] [--facts PATH …] [--history PATH]`. The World is `--world`, else `CHATDDX_WORLD`: its
inventory locates the sources and the endpoints, and the model facts are the bundled ones, the World's `facts.toml` and
each `--facts`, as for init-data. The shell connects as `DB_USER` in autocommit mode, as the runner needs, and refuses a
login with no person.

Lines are read with readline, which keeps a history (`~/.chatddx_history`, or `--history`) and completes with Tab (see
"Completion"). Lines from a pipe are echoed, and the session stops at the first that fails, exiting with 1, so a piped
routine either holds or says where it broke. Ctrl-C at the prompt clears the line; during a command it ends the
command, but where `run`, `batch` and `score` hold it (see "Stopping").

## What a person sees
The shell acts as one person. It sees the threads they own or collaborate on, live (docs/catalog.md, "Owners"), and
names them as the bench does: a name is the person's own thread first, and another's is named `OWNER/NAME`. Their runs
are the runs they own; the runner writes the owner (docs/catalog.md, "Owners").

A person is scored against their own expectations only. One shared with them counts once they take it (`take`), so
what they're scored against never changes under them when someone else edits theirs.

## The cell
The cell is what the shell runs: a configuration, an endpoint and the engine it serves, and the name the configuration
was given. The configuration is a variation of a configuration thread: the edit the cell holds, its recipe, and the
parts set on it (`TriedVariation`). Every `run` and `batch` runs the cell.

Whenever the cell changes, the shell says what the lints find in it: `factors.lint` and the facts' checks on the pair,
run as a trial of the cell and one case. A configuration made for another model than the endpoint's is said as soon as
the endpoint changes. Lints warn and never refuse (docs/chatddx.md, "Compromises").

### Names
What depends on the model is made per model, and texts per language (docs/curation.md, "Per model"), so a
configuration is a thread per variant: `plan (en, Qwen/Qwen3-8B-AWQ)`. A name is looked for as given, and else as the
one variant of it the cell's model may use, `NAME (LANGUAGE)`, `NAME (MODEL)` or `NAME (LANGUAGE, MODEL)`
(`catalog/variants.py:variants_for`). A name ending in a language, `free-text-guided sv` or `free-text-guided (sv)`,
narrows the variants to it (`language_of`). Variants in several languages are refused, saying how to name one: `name
one as 'free-text-guided en' or 'free-text-guided sv'`.

The cell holds the name as given (`Cell.name`). With no endpoint, a name only per-model variants have is held until
there is one. Each time the endpoint changes, the held name's variant for the new model is picked again, and what was
set on the cell is set again by name; where a part set has no variant for that model, the cell keeps what it held and
says why. A variant named whole, `plan (en, Qwen/Qwen3-8B-AWQ)`, finds itself, so it is held as named, and another
model's endpoint only gets the lints.

Names hold spaces and need no quotes: a command's last name takes the rest of the line, and `cell` takes its endpoint
from the last word. `run` takes a seed only as a whole number after a case's title.

### Parts
```
AGENT: replace
The section is "Recipe and compilation" (docs/factors.md:368). The paragraph:
---
`set PART CHUNK` puts another chunk in one of the recipe's nine parts (docs/factors.md, "Recipe and compilation"), a
chunk made per model named plainly. The variation compiles at once, so a part that doesn't compile is refused and the
cell stays as it was. Setting the configuration's own chunk unsets the part, and `none` takes an optional part out.
```
`set PART CHUNK` puts another chunk in one of the recipe's nine parts (docs/factors.md, "Recipe"), a chunk made per
model named plainly. The variation compiles at once, so a part that doesn't compile is refused and the cell stays as
it was. Setting the configuration's own chunk unsets the part, and `none` takes an optional part out.

### Saving
`save NAME` makes the cell's configuration the person's own. Their live thread named NAME gets a new edit, or none when
its head has the same digest; without one, a thread named NAME is forked from the edit the cell holds. When parts are
set, the compilation is written with the running code as compiler. The cell then holds the saved configuration.

## Looking
Nothing here is sent anywhere.
- **`show`** is the cell: each part with its chunk's title and what it is (`catalog/titles.py:describe`), the
  endpoint and the name its engine is served under, the messages rendered with placeholder fills (`‹vignette›`), and
  the body, with the output's schema and the tools' parameters left to `show output` and `show tool`. A greedy cell
  says its seed isn't sent. Then the lints of a trial of the cell and every case it counts, so a language mismatch
  shows, and per scorer view how many cases it can hold the cell to: a case has it when the expectation the person is
  scored against gives the view's expectation selector something to pick, and the view is offered by the cell's
  output (see "Scoring").
- **`show tag TAG...`** is the same over the cases with any of the tags, those `batch` would run.
- **`show KIND [NAME]`** is a component the person sees, by kind and name, or the cell's own: its fields, digests in
  them titled, its catalog entries, and a summary of the person's runs with it. Runs are found through compilations
  for a configuration and its parts (`Bench.reaching`), through scorings for a scorer, an expectation and a schema
  (`Bench.scored_by`); a judge counts the runs it judged and its calls, and sums up its own views only; an endpoint
  counts the runs at it and the judge calls made at it, from the scores' judge endpoints. The kinds are `case`,
  `endpoint`, `tag`, `configuration`, the nine parts, `tool`, `scorer`, `judge`, `expectation`, `expectation_schema`,
  `appendix`, `canary_set`, `model` and `engine`.
- **A case** is shown with its source, its vignette fetched from the World's source, its tags and language, and the
  expectation the person is scored against, or one shared with them to take. Cases are named by title
  (`Bench.case_titled`): a family's name for its case, or `FAMILY with APPENDIX, …` as the catalog titles a case that
  sends appendices (docs/catalog.md, "Titles"). Such a case shows its appendices' texts and its own expectation; a
  family's case names the family's appendices and the cases that send them.
- **`configurations [NAME]`** lists a row per configuration name and language: its models, each part as its variants
  share it with the model taken off (`recommended`), or `varies`, and its owner; a fork reads `yours, from OWNER`, and
  the origin it forks is left out. With NAME, its variants, a row per model and owner.
- **`endpoints`** lists the World's endpoints: engine, model, URL and the sources each is cleared for.
- **`cases`** lists the person's cases, and how many carry each tag.
- **`reasoning`** is a table of every reasoning level on every model the facts know, headed by the endpoints serving
  it: what is written, the sampling it brings, the level it falls back to, or why the model refuses it; `▸` marks the
  cell's (docs/facts.md, "Reasoning").
- **`scorers`** lists every view of every scorer: its metric, the judge of a judged one, what it reads, what it is held
  to, the scorer's owner, and whether the cell's output offers it.

## Running
### Seeds
A trial has at least one seed (docs/factors.md, "Seeds are explicit"), so there is no unseeded run. The shell holds a
seed: drawn below 100,000 for a readable prompt, and held from 0 to 2³¹−1. On a greedy skeleton the seed isn't sent
(docs/factors.md, "Rendering"); the shell says so and runs, and the trial holds the seed all the same.

### A run
`run CASE [SEED]` makes a trial of the cell's skeleton, the endpoint's engine, one case and one seed, the shell's
unless one is given, and starts it at the cell's endpoint (docs/runner.md, "A run"). The trial is stored and not
threaded: a thread per trial would flood the catalog. An unsaved variation's compilation is stored before its run,
with the running code as compiler, so the run's skeleton keeps a recipe and a title. The gate refuses before anything
is written (docs/runner.md, "The gate"), said as `refused: …`.

The transcript streams the thinking, labelled, then the answer, each tool call as `[name] arguments` with its
`[result]`, and the tokens used. Trailing whitespace is left out, so a runaway's newlines don't fill the screen. The
run is then finished and scored (see "Scoring"), and the shell says how it went: its outcome, the call's error, what
each selection of the applying scorers' views picks from the answer, the scores, what the judges said, the findings,
and `recorded as run N of trial X, run ID`, N counting the person's runs of that trial. Each selection is listed once,
by the first label that makes it, and a label used again gets its scorer's name; a view that reads the answer whole
isn't listed, as the transcript holds it.

### A batch
`batch TAG...` makes one trial of the cases with any of the tags and the shell's seed, so one run. The cases go in the
trial's order, by digest (docs/factors.md, "Execution"), a line each, counting its tokens as it streams and then saying
how it went. The run is then scored, and a table gives each case's value per view, by case title, and a summary per
view. Crossing several variations over cases is the batch planner's (agents/wip-batch.md); until it exists, a batch
is one variation over tagged cases.

### Outcomes
An item's outcome comes from its last call and its answer, read by the skeleton's contract (docs/factors.md,
"Scorer"):
- `stopped`: halted, or a turn left unsent;
- `errored`: no answer, and the call ended in an error;
- `unread`: no answer, and no error;
- `completed`: a text answer;
- `salvaged`: a structured answer cut short, read with its structure closed;
- `invalid`: a structured answer that breaks the output's schema;
- `valid`: one that holds to it.

The call's error goes with the outcome, as `completed: Unfinished: the stream ended before [DONE]`.

### Stopping
In `run`, Ctrl-C hangs the call up, and the item is recorded as stopped. In a batch, a first press lets the case under
way finish and then stops, and a second hangs that call up too (docs/runner.md, "Stopping"). While a run is finished
and scored, a first press waits, saying so; a second stops the scoring: the scorer under way finishes its score with
what it has, those after it are refused as stopped, and the shell says `score` scores what is left.

## Scoring
A finished run is scored under every scorer that applies to it (docs/runner.md, "What applies to a run"), each under
its scoring as it would be built now: the scorer, and the person's own expectations of the run's cases.
- **What is left to score** is worked out per run: a scorer is left when the run has no whole score under the scoring
  as it would be built now, finished, with an item for every run item and view, and no judge call stopped. A changed
  expectation makes a new scoring, so its runs are left to score again, and a stopped scoring leaves its run to score.
- **The latest score per scorer** is the one `runs`, `replay` and `show` read; older ones stay in the ledger.
- **Judge calls are said as they go**, a line per call as a batch has per case, ending with what the judge said at the
  view's `at`, from the scoring pass's events (docs/runner-api.md, "score.py").

### Scores on the screen
- **One item's scores** give, per scorer and view, the value and the detail as text: what was read, as `1. Biliary
  colic`, or why there's no value; a judged view's values by seed, as `by seed: 0.5, 0, 1`. Views with no target
  (`no target`, or the case has no expectation) aren't listed, but named once after: `no target: notes comment,
  answer, graded`.
- **What the judges said** follows one item's scores: each judge call, by view, judge and seed, with what it said at
  the view's `at` and the rest of its answer's text, its reason, or the call's error.
- **A batch's table** has a column per scorer view, but for views with no target in any case, which are named once;
  `—` is no value.
- **The summary** per view counts the values, their mean and standard error (`scorers/aggregate.py`; display only,
  analysis rather than a score), and apart those with no value: where no answer came, where the case has no target,
  and for any other reason.
- **A value that isn't a score from 0 to 1** is written with what marks it, as its metric publishes
  (`scorers/scorer.py:Metric.unit`): `first_mention`'s offset is `@44`. A standard error is written bare.
- **Where no answer came**, every view has no value, so a server's error doesn't count as a wrong answer.
- **Findings** that the run, the scoring pass and the checks note are said after the tables; a batch says each once,
  with how often (`(×4)`). After one item, those about reading its answer aren't said again, as its outcome says them.

## Looking back
- **`runs [COUNT]`** lists the person's runs, newest first, the last 20 or COUNT: the run's and the trial's ids,
  when, what ran (configuration, endpoint, the case or how many, the seeds), how it went (the one item's outcome, or a
  count of each; `unfinished` without a finish record), and per scorer the latest score's view means, as
  `plan 1/1/1/—`.
- **`replay [RUN]`** shows the latest run, or the one an id prefix names: when, whether it finished, the address it
  ran at, and on which chatddx. The request isn't stored (docs/ledger.md, "Some of what happened isn't checked"), so
  each item's first request is rendered again from the trial and the source and held to its fingerprint, saying when
  the vignette at the source isn't the one sent or the request renders otherwise now. A run of one item is told again
  as it streamed, from the stored responses and tool runs, then its outcome, scores and judges; a batch gives its
  lines, by case, the table and the summary.
- **`score [RUN]`** scores each finished run under the scorers left (see "Scoring"), then sums up every score given.
  With RUN: that run, or why not: `unfinished`, `no scorer applies to it`, or `scored already, as the scorings are
  now`, with its scores.
- **`take [from OWNER] [TAG...]`** takes the expectations shared with the person for the cases with any of the tags,
  or all, under each expectation schema they have one in, keeping the person's own. Where several people share one for
  a case, it names them, and `take from OWNER` takes theirs.

## Completion
Tab completes a command, then its names, word by word, from what the person sees: configurations and chunks by their
plain names, a per-model name by what it is made from and one made in several languages as `NAME LANG`, whose bare
name isn't offered; cases by name and the titles of those that send appendices; endpoints, parts, kinds, and tags,
each once. `replay` completes the latest 20 runs' ids, and `score` the runs left to score, both fresh at each Tab.
The rest is read once, and again after a `save`.

## Terms

| Term | Meaning |
| --- | --- |
| Repl, shell | `chatddx repl`, for one person over a World. |
| Cell | What the shell runs: a configuration, an endpoint and the name the configuration was given. |
| Variation | A configuration thread's edit with parts set on it, as the cell holds it. |
| Variant | A configuration or chunk made for one model or language, named after it. |
| Case title | A family's name, or `FAMILY with APPENDIX, …` for a case that sends appendices. |
| Outcome | How an item went, from its last call and its answer. |
| Salvaged | A structured answer cut short, read with its structure closed. |
| Left to score | A scorer that applies to a run with no whole score under its scoring as built now. |
| No target | A view a case's expectation gives nothing to hold an answer to. |

## Open design issues

### What the repl doesn't reach
- It reaches four of the bench's writes (`save`, `start`, `score`, `take`); the API reaches them all.
- A thread with a title and no name can't be named.
- A run takes one seed, and no execution settings, canary set or text cleanup; `score` can't pick a scorer, score a
  run again, or name the endpoint a judge is called at, so a judge whose engine two endpoints serve bars its scorer.

### Smaller issues
- **No word on reasoning that wasn't heeded**, and no `[thinking in content]`: the runner can't tell reasoning a parser
  missed (docs/runner.md, "Smaller issues").
- **Two tool calls in one response run together** on one line as they stream, as a call's first delta is taken as its
  name and the deltas don't say where the next begins; `replay` splits them.
- **Only an item's first request is rendered again**; a later round's could be rebuilt from the stored responses and
  tool runs.

## Outstanding
Suggested, and left for later:
- **The language of a run.** A run is in its configuration's language, and nothing picks it from the cases: a batch
  over Swedish cases under an English configuration runs them in English, and only `language.mixed` warns.
  docs/catalog.md, "Languages", has the request follow the case. The cell could hold a name without a language, as it
  holds one without a model, and run each case under that name's variant in the case's language; a batch over cases in
  several languages would then be a run per language.
- **`diagnoses` applies to a plan**, since a plan's `$.diagnoses[*]` reaches its schema, but the items are objects, so
  its differential lists them as JSON and scores their text. A reach that knew the type of what a view picks would leave
  it out, as `View.offered_by` leaves whole-answer views out of structured runs.
- **The judge lines aren't aligned**, as their labels differ in length; the labels of a scoring's judge calls are known
  when it starts, so their width could be too.

# Repl

The repl, `chatddx repl LOGIN`, is a shell for one person over a World: choose a configuration and an endpoint, see
what a request would be, run cases, and look back at runs and score them. It works through the bench
(`src/chatddx/bench/`, docs/bench.md), the person-scoped view the API shares, and strings together pieces
documented elsewhere: the runner and the scoring pass (docs/runner.md), what a request is made of (docs/factors.md),
names, owners and titles (docs/catalog.md), endpoints and clearance (docs/inventory.md), and model facts and their
lints (docs/facts.md).

```
AGENT: replace
The 2 lines below. docs/repl-api.md is dropped for docs/reference/repl.md, which `chatddx reference` writes from the code.
Its command table is dropped with it: `COMMANDS` holds the commands.
---
This document describes what the shell does and why. Its names and what they raise are in docs/reference/repl.md,
and its commands in `src/chatddx/repl/commands.py:COMMANDS`; how to use it, command by command, is the manual
(docs/repl-manual.md).
```
This document describes what the shell does and why. Its modules, the command table and what each command calls on the
bench are in docs/repl-api.md; how to use it, command by command, is the manual (docs/repl-manual.md).

The repl writes only runs and scores, through the runner and the scoring pass, a person's saved configurations
(`save`), and the expectations they take (`take`). Authoring, the chunks, cases, appendices and expectations a person
writes and the edits and proposals between people, is the API's and the portal's. What the repl works with comes from
a World and its data set, and the sample World (`worlds/sample/`) is the example a new World follows.

## Starting
`chatddx repl LOGIN [--world DIR] [--history PATH]`. The World is `--world`, else `CHATDDX_WORLD`: its inventory
locates the sources and the endpoints. The model facts are the store's, as init-data wrote them (docs/facts.md), read
when they are needed, so facts corrected meanwhile are used. The shell connects as `DB_USER` in autocommit mode, as
the runner needs, and refuses a login with no person.

Lines are read with readline, which keeps a history (`~/.chatddx_history`, or `--history`) and completes with Tab (see
"Completion"). Lines from a pipe are echoed, and the session stops at the first that fails, exiting with 1, so a piped
routine either holds or says where it broke. Ctrl-C at the prompt clears the line; during a command it ends the
command, but where `run` and `score` hold it (see "Stopping").

## What a person sees
The shell acts as one person. It sees the threads they own or collaborate on, live (docs/catalog.md, "Owners"), and
names them as the bench does: a name is the person's own thread first, and another's is named `OWNER/NAME`. Their runs
are the runs they own; the runner writes the owner (docs/catalog.md, "Owners").

A person is scored against their own expectations only. One shared with them counts once they take it (`take`), so
what they're scored against never changes under them when someone else edits theirs.

## The cell
The cell is what the shell runs: a configuration, and the endpoint named for it, if any. The configuration is a
variation of a configuration thread: the edit the cell holds, its recipe, and the parts set on it (`TriedVariation`),
its model among them. The engine the cell is rendered and linted for is the endpoint's, or the one serving the
configuration's model when the cell has no endpoint and one does (`Repl.engine`);

Whenever the cell changes, the shell says what the lints find in it: `factors.lint` and the facts' checks on the pair,
run as a trial of the cell and one case. A reasoning level or a recommended sampling that the facts about a new
engine's model refuse, or that can't be worked out for a model without facts, is said as soon as the engine changes,
as a note rather than a failure, so a piped session goes on; the cell changes all the same, so that `set` can mend it.
Lints warn and never refuse (docs/chatddx.md, "Compromises").

### Names
A configuration is a thread written in one language, which its translations carry into others (docs/curation.md,
"Texts"), so it is one thread whatever the languages its cases are in, `plan`; its model is a part, and its name
carries neither a model nor a language. A name is looked for as given: `plan (en)` and `free-text-guided sv` name
nothing.

The cell holds the configuration a name finds, by the name it is found under (`TriedVariation.name`), and nothing is
picked again by name. `on ENDPOINT` puts the endpoint's model in the configuration, as `set model` would, and keeps
every part set on it, worked out again for the new endpoints's model; `use` and `cell` put the named endpoint's model in.
An endpoint serving the configuration's own model unsets the part (see "Parts").

Names hold spaces and need no quotes: a command's last name takes the rest of the line, and `cell` takes its endpoint
from the last word. `run` takes a seed only as a whole number after a case's title.

### Parts
`set PART CHUNK` puts another chunk in one of the recipe's nine chunk parts, and `set model NAME` another model named as
its thread is (`qwen3-8b-awq`), and keeps an endpoint named that serves it, unsetting one that serves another;
the prompt then shows the endpoint serving the model, when one does.

A chunk is named plainly, as `off`, a reasoning chunk asking for a level that the facts work out for the model.
The variation compiles at once, so a part that doesn't compile is refused and the cell stays as it was.
Setting the configuration's own chunk or model unsets the part, and `none` takes an optional part out.
`set model` keeps an endpoint named that serves the new model, and drops one that serves another,
so the cell runs where the new model is served.

### Saving
`save NAME` makes the cell's configuration the person's own. Their live thread named NAME gets a new edit, or none when
its head has the same digest; without one, a thread named NAME is forked from the edit the cell holds. When parts are
set, the compilation is written with the running code as compiler. The cell then holds the saved configuration.

## Looking
Nothing here is sent anywhere.
- **`show`** is the cell: each part with its chunk's title and what it is (`catalog/titles.py:describe`), the engine
  among them; the level a reasoning level landed on, when the engine's model is asked for another, as `reasoning off
  → low`, with why for a nearest, `its nearest: always reasons: …`; the level a recommended sampling follows, as
  `recommended sampling, for reasoning on`; the endpoint the cell runs at and the name its engine is served under; the messages
  rendered with placeholder fills (`‹vignette›`), and the body, with the output's schema and the tools' parameters
  left to `show output` and `show tool`. A greedy cell says its seed isn't sent. Then the languages the cases it counts
  are in (`Bench.languages`, docs/bench.md), a line each, as a run would send them: `en: 79 cases, as written`, `sv: 20
  cases, translated`, or, in yellow, `sv: 20 cases, left out: plan has no translations into sv`; none for a judge
  configuration. Then the lints of each language's trial of the cell and its cases, the cases left out said as
  `translations.missing`, and per scorer view how many cases it can hold the cell to: a case has it when the
  expectation the person is scored against gives the view's expectation selector something to pick, and the view is
  offered by the cell's output (see "Scoring").
- **`show tag TAG...`** is the same over the cases with any of the tags, those `run tag` would run.
- **`show KIND [NAME]`** is a component the person sees, by kind and name, or the cell's own: its fields, digests in
  them titled, its catalog entries, and a summary of the person's runs with it. Runs are found through compilations
  for a configuration and its parts (`Bench.runs(reaching=…)`), through scorings for a scorer, an expectation and a
  schema (`Bench.runs(scored_by=…)`); a judge counts the runs it judged and its calls, and sums up its own views only;
  an endpoint counts the runs at it and the judge calls made at it, from the scores' judge endpoints. The kinds are
  `case`, `endpoint`, `tag`, `configuration`, the nine chunk parts, `tool`, `scorer`, `judge`, `expectation`,
  `expectation_schema`, `appendix`, `canary_set`, `model`, `engine` and `facts`, a model's stored facts by its name.
- **A case** is shown with its source, its vignette fetched from the World's source, its tags and language, and the
  expectation the person is scored against, or one shared with them to take. Cases are named by title
  (`Bench.case_titled`): a family's name for its case, or `FAMILY with APPENDIX, …` as the catalog titles a case that
  sends appendices (docs/catalog.md, "Titles"). Such a case shows its appendices' texts and its own expectation; a
  family's case names the family's appendices and the cases that send them.
- **`configurations [NAME]`** lists a row per configuration name: the languages it can be sent in, its own first
  (`catalog/language.py:edit_languages`), then those its translations cover, as `en, sv`, or
  `—`; each part as its chunk's title, the model last, or `differs` where configurations of one name differ; and its
  owner; a fork reads `yours, from OWNER`, and the origin it forks is left out. Judge configurations follow, in a
  table of their own. With NAME, the configurations of exactly that name, a row each with its languages, parts and
  owner.
- **`endpoints`** lists the World's endpoints: engine, model, URL and the sources each is cleared for.
- **`cases`** lists the person's cases, and how many carry each tag.
- **`reasoning`** is a table of every reasoning level, `default` first, on every model the stored facts know, headed
  by the endpoints serving it: the level it collapses into or lands on as its nearest, with why, what is sent, and the
  sampling recommended for it, or why the model refuses it; a last row, `budget`, says how a thinking budget is sent,
  or why it is refused. `▸` marks the level the cell's configuration asks for, `default` without a reasoning part, and
  the endpoint the cell runs at (docs/facts.md, "Reasoning").
- **`scorers`** lists every view of every scorer: its metric, the judge of a judged one, what it reads, what it is held
  to, the scorer's owner, and whether the cell's output offers it.

## Running
### Seeds
A trial has at least one seed (docs/factors.md, "Seeds are explicit"), so there is no unseeded run. The shell holds a
seed: drawn below 100,000 for a readable prompt, and held from 0 to 2³¹−1. On a greedy skeleton the seed isn't sent
(docs/factors.md, "Rendering"); the shell says so and runs, and the trial holds the seed all the same.

### A run
`run CASE [SEED]` makes a trial of the cell's skeleton, the endpoint's engine, one case and one seed, the shell's unless one is
given, and starts it at the endpoint the cell runs at (see "The cell"; docs/runner.md, "A run"). The case is sent in
its own language (`Bench.start`, docs/bench.md): as written, in the configuration's own or a case of none, or
translated, and the title says so, `trial: free-text-guided × qwen3-8b-awq@fake × casesfromedn1, in sv, translated
(seed 42)`; a case in a language the translations don't cover isn't sent, `no case can be sent: plan has no
translations into sv`. The trial is stored and not threaded: a thread per trial would flood the catalog. An unsaved
variation's compilation is stored before its run, with the running code as compiler, as a translated skeleton's is,
so the run's skeleton keeps a recipe and a title. The gate refuses before anything is written (docs/runner.md, "The
gate"), said as `refused: …`.

The transcript streams the thinking, labelled, then the answer, each tool call as `[name] arguments` with its
`[result]`, and the tokens used. Trailing whitespace is left out, so a runaway's newlines don't fill the screen. The
run is then finished and scored (see "Scoring"), and the shell says how it went: its outcome, the call's error, what
each selection of the applying scorers' views picks from the answer, the scores, what the judges said, the findings,
and `recorded as run N of trial X, run ID`, N counting the person's runs of that trial. Each selection is listed once,
by the first label that makes it, and a label used again gets its scorer's name; a view that reads the answer whole
isn't listed, as the transcript holds it.

### A run of tagged cases
`run tag TAG...` starts the cases with any of the tags under the shell's seed (`Bench.start`, docs/bench.md): a run
per language they are in, each a trial of its own, the configuration's own language first, as written, then each its
translations cover, translated. The runs go in turn, each titled with its cases and, when there are several or it is
translated, its language: `20 cases tagged edn, in sv, translated`. In each, the cases go in the trial's order, by
digest (docs/factors.md, "Execution"), a line each, counting its tokens as it streams and then saying how it went.
Each run is then scored, and a table gives each case's value per view, by case title, and a summary per view. The
cases left out are said last, in yellow, `left out: 20 cases in sv, as plan has no translations into sv`; with every
case left out, nothing starts: `no case can be sent: plan has no translations into sv`.

### Outcomes
An item's outcome comes from its last call and its answer, read by the skeleton's contract (docs/factors.md,
"Scorer"):
- `stopped`: halted, or its last tool round stopped before its request was sent;
- `errored`: no answer, and the call ended in an error;
- `unread`: no answer, and no error;
- `completed`: a text answer;
- `salvaged`: a structured answer cut short, read with its structure closed;
- `invalid`: a structured answer that breaks the output's schema;
- `valid`: one that holds to it.

The call's error goes with the outcome, as `completed: Unfinished: the stream ended before [DONE]`.

### Stopping
In `run`, Ctrl-C hangs the call up, and the item is recorded as stopped. In `run tag`, a first press lets the case
under way finish and then stops, and a second hangs that call up too (docs/runner.md, "Stopping"); either stops the
runs of the languages after it too, which send nothing and are finished and scored as they are. While a run is
finished and scored, a first press waits, saying so; a second stops the scoring: the scorer under way finishes its
score with what it has, those after it are refused as stopped, and the shell says `score` scores what is left.

## Scoring
A finished run is scored under every scorer that applies to it (docs/runner.md, "What applies to a run"), each under
its scoring as it would be built now: the scorer, and the person's own expectations of the run's cases.
- **What is left to score** is worked out per run: a scorer is left when the run has no whole score under the scoring
  as it would be built now, finished, with an item for every run item and view, and no judge call stopped. A changed
  expectation makes a new scoring, so its runs are left to score again, and a stopped scoring leaves its run to score.
- **The latest score per scorer** is the one `runs`, `replay` and `show` read; older ones stay in the ledger.
- **Judge calls are said as they go**, a line per call as `run tag` has per case, ending with what the judge said at
```
AGENT: replace
docs/runner-api.md is dropped for docs/reference/runner.md, which `chatddx reference` writes from the code.
It has no section for each module: the module is named instead.
---
  the view's `at`, from the scoring pass's events (src/chatddx/runner/score.py).
```
  the view's `at`, from the scoring pass's events (docs/runner-api.md, "score.py").

### Scores on the screen
- **One item's scores** give, per scorer and view, the value and the detail as text: what was read, as `1. Biliary
  colic`, or why there's no value; a judged view's values by seed, as `by seed: 0.5, 0, 1`. Views with no target
  (`no target`, or the case has no expectation) aren't listed, but named once after: `no target: notes comment,
  answer, graded`.
- **What the judges said** follows one item's scores: each judge call, by view, judge and seed, with what it said at
  the view's `at` and the rest of its answer's text, its reason, or the call's error.
- **The table** of a run of several cases has a column per scorer view, but for views with no target in any case,
  which are named once; `—` is no value.
- **The summary** per view counts the values, their mean and standard error (`scorers/aggregate.py`; display only,
  analysis rather than a score), and apart those with no value: where no answer came, where the case has no target,
  and for any other reason.
- **A value that isn't a score from 0 to 1** is written with what marks it, as its metric publishes
  (`scorers/scorer.py:Metric.unit`): `first_mention`'s offset is `@44`. A standard error is written bare.
- **Where no answer came**, every view has no value, so a server's error doesn't count as a wrong answer.
- **Findings** that the run, the scoring pass and the checks note are said after the tables; a run of several cases
  says each once, with how often (`(×4)`). After one item, those about reading its answer aren't said again, as its
  outcome says them.

## Looking back
- **`runs [COUNT]`** lists the person's runs, newest first, the last 20 or COUNT: the run's and the trial's ids,
  when, what ran (configuration, endpoint, the case or how many, the language a translated run was sent in, the
  seeds), how it went (the one item's outcome, or a count of each; `unfinished` without a finish record), and per
  scorer the latest score's view means, as `plan 1/1/1/—`.
- **`replay [RUN]`** shows the latest run, or the one an id prefix names: when, whether it finished, the address it
  ran at, and on which chatddx. The request isn't stored (docs/ledger.md, "Call"), so
  each item's first request is rendered again from the trial and the source and held to its fingerprint, saying when
  the vignette at the source isn't the one sent or the request renders otherwise now. A run of one item is told again
  as it streamed, from the stored responses and tool runs, then its outcome, scores and judges; a run of several
  cases gives its lines, by case, the table and the summary.
- **`score [RUN]`** scores each finished run under the scorers left (see "Scoring"), then sums up every score given.
  With RUN: that run, or why not: `unfinished`, `no scorer applies to it`, or `scored already, as the scorings are
  now`, with its scores.
- **`take [from OWNER] [TAG...]`** takes the expectations shared with the person for the cases with any of the tags,
  or all, under each expectation schema they have one in, keeping the person's own. Where several people share one for
  a case, it names them, and `take from OWNER` takes theirs.

## Completion
Tab completes a command, then its names, word by word, from what the person sees: configurations, chunks and engines
by their names; cases by name and the titles of those that send appendices; endpoints, parts, kinds, and tags, each
once. `replay` completes the latest 20 runs' ids, and `score` the runs left to score, both fresh at each Tab. The rest
is read once, and again after a `save`.

## Terms

| Term | Meaning |
| --- | --- |
| Repl, shell | `chatddx repl`, for one person over a World. |
| Cell | What the shell runs: a configuration, its model one of its parts, and the endpoint named for it, if any. |
| Variation | A configuration thread's edit with parts set on it, as the cell holds it. |
| Translated | A run whose skeleton is the configuration's compiled into its cases' language by its translations. |
| Left out | Cases in a language the configuration's translations don't cover: said, and not sent. |
| Case title | A family's name, or `FAMILY with APPENDIX, …` for a case that sends appendices. |
| Outcome | How an item went, from its last call and its answer. |
| Salvaged | A structured answer cut short, read with its structure closed. |
| Left to score | A scorer that applies to a run with no whole score under its scoring as built now. |
| No target | A view a case's expectation gives nothing to hold an answer to. |

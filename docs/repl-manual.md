# The chatddx shell

The chatddx shell, the repl, is where you run clinical cases through a
language model and see what comes back. You pick what to ask and which
endpoint to ask, run one case or a whole set of them, and every answer is
recorded and scored as it arrives.

This manual goes through the shell command by command. The examples use
the sample World (`worlds/sample`) and its fake engines (`@fake`), which
answer every case the same way, so you can try everything without a GPU.

## Starting

The shell runs as a person: a login that owns your runs and your saved
configurations. Load the World's data set once, which also adds you and
gives you copies of the shared configurations and expectations to call
your own (`--giftbag`):

```
chatddx init-data alice --giftbag
```

To try it without a GPU, serve the World's fake engines in another
terminal first, and leave them running:

```
chatddx fake-engines
```

Then start the shell:

```
chatddx repl alice
```

The World is the one `--world DIR` names, else `CHATDDX_WORLD`; the
development environments set it to the sample. `--facts PATH` adds model
facts to the bundled ones and the World's own `facts.toml`.

The shell greets you with its prompt:

```
alice #2475>
```

`alice` is who you are, and `#2475` is the seed the shell drew for you (see
`seed` below). As you choose what to run, the prompt grows to show it.

For runs to look at before you make any, with what can go wrong among
them, run the sample World's scripted runs once (with `fake-engines`
stopped: they serve their own fakes):

```
chatddx scripted-runs alice
```

## A few words first

- **Configuration:** what to ask and how. The instructions, the prompt the
  case goes into, the kind of answer wanted (free text, a list of
  diagnoses, a management plan), whether the model should think first, and
  how it samples its words. Its parts are called `instructions`,
  `few_shot`, `prompt`, `output`, `sampling`, `reasoning`, `passthrough`,
  `translations` and `toolset`. What depends on the model is made for each
  model, and texts for each language, so one configuration has a variant
  per model and language: `plan (en, Qwen/Qwen3-8B-AWQ)`. You name it
  `plan`, and the endpoint picks the variant.
- **Endpoint:** which model answers, on which machine: `qwen3-8b@pelle` is
  Qwen3-8B as pelle serves it. Each endpoint is cleared for the sources
  whose cases may be sent to it.
- **The cell:** the configuration and the endpoint you have chosen,
  together. Every run uses the cell.
- **Case:** a clinical vignette, from a source the World names. Some cases
  send appendices after the vignette, such as lab results, and are named
  after them: `Dutchfall11w with ultrasound`.
- **Expectation:** what a case is expected to yield: its targets, each a
  few plain words and a pattern the scorers look for in an answer, and
  clinicians' notes, which judges read. You are scored against your own
  expectations.
- **Run:** answers from the cell to one case or several, recorded with
  everything that was received.
- **Trial:** the cell, the cases and a seed together. Running the same
  trial twice gives two runs of one trial.
- **Scorer:** what compares an answer with a case's expectation, view by
  view. A judged view asks a judge, a model of its own, whether the answer
  meets a note.

## Getting around

### `help`

Lists every command, with the words it takes. A word in brackets is
optional; `TAG...` means one tag or several.

### `configurations [NAME]`

Lists the configurations you can use: yours, and those shared with you.
Each row is a configuration in one language, with the models it is made
for and what each part is.

```
alice #2475> configurations
 configuration          models          instructions    few_shot             prompt  output                ...  owner
 diagnoses (en)         gpt-oss-20b     —               —                    case    diagnoses (en)        ...  yours, from archive
                        Mistral-Small…
                        Qwen3-8B-AWQ
 free-text-guided (sv)  gpt-oss-20b     clinician (sv)  worked-example (sv)  case    free-text (en)        ...  yours, from archive
                        Mistral-Small…
                        Qwen3-8B-AWQ
 judge (en)             every model     judge (en)      —                    judge   verdict (en)          ...  yours, from archive
 plan (en)              gpt-oss-20b     —               —                    case    management-plan (en)  ...  yours, from archive
 ...
```

`yours, from archive` is your copy of a configuration the archive (the
shared data set) holds; the archive's own row is left out. A part that
differs between models reads `varies`. With a name, it lists that
configuration's variants, one per model and owner:

```
alice #2475> configurations plan
 configuration                  prompt  output                sampling                          owner
 plan (en, Qwen/Qwen3-8B-AWQ)   case    management-plan (en)  recommended (Qwen/Qwen3-8B-AWQ)
 plan (en, Qwen/Qwen3-8B-AWQ)   case    management-plan (en)  recommended (Qwen/Qwen3-8B-AWQ)   archive
 ...
```

### `endpoints`

Lists the endpoints you can run on: the engine each serves, its model,
where it is reached, and the sources it is cleared for.

```
alice #2475> endpoints
 endpoint              engine                model                                          url                         cleared for
 gpt-oss-20b@fake      gpt-oss-20b@fake      openai/gpt-oss-20b                             http://127.0.0.1:12100/v1/  sample typed
 mistral-small@remote  mistral-small@remote  mistralai/Mistral-Small-3.2-24B-Instruct-2506  http://127.0.0.1:12101/v1/  sample
 qwen3-8b-awq@fake     qwen3-8b-awq@fake     Qwen/Qwen3-8B-AWQ                              http://127.0.0.1:12099/v1/  sample typed
```

### `cases`

Lists the cases you can run, how many there are, and how many carry each
tag.

```
alice #2475> cases
DutchFall10w  Dutchfall11w  ...  casesfromedn1  ...  openxddx-case_9
99 cases; tagged dutch-fall 30, edn 20, openxddx 49
```

Press Tab at any point to complete a command, or a name after it, word by
word: a configuration after `use`, an endpoint after `on`, a case after
`run` (`Dutchfall11w with ultrasound` included), a tag after `batch` or
`show tag`, a run after `replay`. A configuration is offered by its plain
name, and one made in several languages by its name and language:
`free-text-guided sv`.

## Choosing what to run

### `use CONFIGURATION`

Puts a configuration in the cell.

```
alice #2475> use plan
plan is made per model: on ENDPOINT picks its variant
cell: plan × ?
alice plan #2475>
```

The `?` says the cell still needs an endpoint. A configuration someone else
shares with you is named with its owner first: `use bob/bobs-plan`. A
configuration made in several languages is named with the one you want,
`use free-text-guided sv`; its plain name is refused, saying which there
are. Names may hold spaces, and need no quotes: `use plan (en,
Qwen/Qwen3-8B-AWQ)` names one variant, and holds it whatever the endpoint.

### `on ENDPOINT`

Puts an endpoint in the cell, and picks the variant of the cell's
configuration made for its model, saying which:

```
alice plan #2475> on qwen3-8b-awq@fake
plan on Qwen/Qwen3-8B-AWQ: plan (en, Qwen/Qwen3-8B-AWQ)
cell: plan (en, Qwen/Qwen3-8B-AWQ) × qwen3-8b-awq@fake
alice plan (en, Qwen/Qwen3-8B-AWQ)×qwen3-8b-awq@fake #2475>
```

Whenever the cell changes, the shell says what the lints find in it, such
as a sampling made for another model than the endpoint's.

### `cell CONFIGURATION ENDPOINT`

Both at once.

```
alice #2475> cell free-text qwen3-8b-awq@fake
cell: free-text (en, Qwen/Qwen3-8B-AWQ) × qwen3-8b-awq@fake
```

### `set PART CHUNK`

Changes one part of the cell's configuration, leaving the rest as it is.
For example, to have the model answer without thinking first:

```
alice plan (en, Qwen/Qwen3-8B-AWQ)×qwen3-8b-awq@fake #2475> set reasoning off
cell: plan (en, Qwen/Qwen3-8B-AWQ)+reasoning=off × qwen3-8b-awq@fake
```

The prompt shows what you changed (`+reasoning=off`). A chunk made per
model is named plainly, as `off`, and picked for the endpoint's model.
`none` takes an optional part out: `set toolset none` takes the tools away.
Setting the configuration's own chunk again unsets the part, and a chunk
that doesn't fit is refused, leaving the cell as it was. Choosing a
configuration again with `use` or `cell` forgets what you set; `on`
another endpoint keeps it, picked again for the new model. Where the new
model has no such chunk, the cell stays as it was, and says why:

```
alice plan (en, Qwen/Qwen3-8B-AWQ)+reasoning=off×qwen3-8b-awq@fake #2475> on gpt-oss-20b@fake
no reasoning 'off' for alice; per model: off (Qwen/Qwen3-8B-AWQ), off (mistralai/Mistral-Small-3.2-24B-Instruct-2506);
the cell keeps plan (en, Qwen/Qwen3-8B-AWQ)+reasoning=off
cell: plan (en, Qwen/Qwen3-8B-AWQ)+reasoning=off × gpt-oss-20b@fake
[warning] facts.reasoning_unmatched: the skeleton's reasoning settings match none of the model's reasoning levels
[warning] facts.sampling_unmatched: the skeleton's sampling is what the facts recommend for Qwen/Qwen3-8B-AWQ, not for
openai/gpt-oss-20b
```

### `show`

Shows the cell: each part and what it is, the endpoint and the name its
engine is served under, the messages the model will read, with the case's
place marked (`‹vignette›`), and the settings that will be sent. Then what
the lints find, and a table of the scorers: for each view, whether this
kind of answer gives it anything to read, and how many cases have the
target it needs. Nothing is sent.

```
alice plan (en, Qwen/Qwen3-8B-AWQ)×qwen3-8b-awq@fake #4479> show
cell: plan (en, Qwen/Qwen3-8B-AWQ) × qwen3-8b-awq@fake
 part          chunk                            is
 endpoint      qwen3-8b-awq@fake                qwen3-8b-awq@fake, served as sha256:cc0dc8… at http://127.0.0.1:12099/v1/
 instructions  —
 few_shot      —
 prompt        case                             "{vignette}{appendices}"
 output        management-plan (en)             native output: management_plan_v1
 sampling      recommended (Qwen/Qwen3-8B-AWQ)  temperature 0.6, top_p 0.95, top_k 20, presence_penalty 1.5
 reasoning     —
 ...
system
Fill in the management plan for the case.
user
‹vignette›‹appendices›
body
{
  "model": "sha256:cc0dc8…",
  "presence_penalty": 1.5,
  "response_format": {
    "type": "json_schema",
    "json_schema": {
      "name": "output",
      "strict": true,
      "schema": "‹the output's schema›"
    }
  },
  "temperature": 0.6,
  ...
  "seed": 4479,
  "return_token_ids": true
}
lints
[warning] language.mixed: the request is en, but 20 of 99 cases are sv
 scorer     view          of 99 cases
 diagnoses  differential  99 have it
 diagnoses  dont-miss     6 have it; missing: Dutchfall11w Dutchfall13w Dutchfall16w ... and 83 more
 free-text  text          the output offers no such view
 ...
 plan       differential  99 have it
 plan       warning       99 have it
 plan       disposition   99 have it
 ...
```

A view that reads the whole answer is offered by free text only. Cases
with missing targets can still be run; the views that need the missing
target just leave them out. The output's schema and the tools' parameters
are left to `show output` and `show tool`.

### `show tag TAG...`

The same, with the lints and the scorers' table counting only the cases
with any of the tags: the cases `batch` would run.

```
alice plan (en, Qwen/Qwen3-8B-AWQ)×qwen3-8b-awq@fake #4479> show tag edn
...
lints
[warning] language.mixed: the request is en, but 20 of 20 cases are sv
 scorer     view          of 20 cases tagged edn
 diagnoses  differential  20 have it
 ...
```

### `show KIND [NAME]`

Shows anything you can see, by kind and name, and what came of your runs
with it. Without a name, it shows the cell's own. For a case, that is its
source, its vignette, its tags and language, the expectation you are
scored against, and your scores on it; a case that sends appendices shows
them, and a case's family names its appendices and the cases that send
them:

```
alice #4479> show case Dutchfall11w
case Dutchfall11w, archive's  74c4d5
 source                           sample/Dutchfall11w
 vignette                         Main complaint: general weakness and lower abdominal pain
                                  ...
 appendices                       labs, ultrasound
 cases                            Dutchfall11w with ultrasound  its own expectation
                                  Dutchfall11w with labs, ultrasound  its own expectation
 tags                             dutch-fall
 language                         en
 expectation.diagnosis.pattern    aaa | (abdominal | aortic) & aneurysm | dissection
 expectation.warning.pattern      rupture* | dissection | shock | aneurysm*
 expectation.disposition.pattern  surg* | operat* | vascular | icu | intensive & care
 expectation.notes                [ ... ]
no runs of yours with this case
```

`show case Dutchfall11w with ultrasound` shows that case, with the
ultrasound's text and the expectation of its own. An expectation shared
with you that you haven't taken says so (see `take`).

The kinds are `case`, `endpoint`, `configuration`, the nine parts, `tool`,
`scorer`, `judge`, `expectation`, `expectation_schema`, `appendix`,
`canary_set`, `model` and `engine`. A judge counts the runs it judged and
its calls, an endpoint the judge calls made at it too, and a scorer the
runs it scored.

### `reasoning`

Shows, in one table, what every reasoning level becomes on every model,
with the endpoints serving each: the switch or effort that gets sent, the
sampling it brings with it, the level it falls back to (`→ on`), or why a
model refuses it (gpt-oss can't stop thinking, for example). The cell's
current choices are marked with `▸`.

## Running

### `seed [SEED]`

The shell holds a seed, shown in the prompt after `#`. Every run sends it
to the model, which uses it for the random choices it makes while writing.
The same seed on the same cell and case asks for the same answer again, so
a run can be repeated, and it is recorded with its seed.

- `seed` draws a new random seed, below 100,000.
- `seed 42` holds 42; any whole number from 0 to 2147483647 will do.

```
alice free-text (en, Qwen/Qwen3-8B-AWQ)×qwen3-8b-awq@fake #66272> seed
seed: #6035
alice free-text (en, Qwen/Qwen3-8B-AWQ)×qwen3-8b-awq@fake #6035> seed 42
seed: #42
```

Draw a new seed whenever you want fresh answers rather than a repeat of
ones you already have: running a batch twice under the same seed asks the
same questions the same way twice.

A cell whose sampling is greedy (temperature 0) always gives the model's
single most likely answer, and a seed changes nothing. The shell runs it
all the same, saying `greedy: the seed isn't sent`; the run still records
the seed.

### `run CASE [SEED]`

Runs one case on the cell. The answer streams as it is written: the
model's thinking first, labelled, then the answer, and each tool call with
its result. Then come the tokens it used, what each view reads from the
answer, and the scores.

```
alice free-text (en, Qwen/Qwen3-8B-AWQ)×qwen3-8b-awq@fake #42> run DutchFall10w
trial: free-text (en, Qwen/Qwen3-8B-AWQ) × qwen3-8b-awq@fake × DutchFall10w (seed 42)
[thinking] I am the fake vLLM, and nothing here reads the case. ...
Fake diagnosis A
Fake diagnosis B
Fake diagnosis C
(285 in, 43 out)
differential
  1. Fake diagnosis A
  2. Fake diagnosis B
  3. Fake diagnosis C
scores
  free-text   text           —   never named
              differential   0   not listed
              dont-miss      0   not named
  raw         text           —   never named
no target: notes comment, answer, graded
recorded as run 1 of trial 5624e3, run 126f0b9d
```

A seed after the case is used for this run alone, and the shell keeps its
own: `run DutchFall10w 7`. A case that sends appendices is named as
`cases` and `show case` name it: `run Dutchfall11w with ultrasound 7`.

The views a case has no target for aren't scored, and are named once
under the scores. When a view asks a judge, the shell says each call to it
as it goes, with the judge's verdict, and lists what each call said and
why after the scores:

```
alice free-text (en, Qwen/Qwen3-8B-AWQ)×qwen3-8b-awq@fake #42> run Dutchfall11w
...
judging Dutchfall11w: comment by verdict, seed 1 of 1      51  meets true
judging Dutchfall11w: answer by verdict, seed 1 of 1      51  meets true
judging Dutchfall11w: graded by graded, seed 1 of 3      52  points 1
judging Dutchfall11w: graded by graded, seed 2 of 3      45  points 0
judging Dutchfall11w: graded by graded, seed 3 of 3      50  points 2
...
scores
  free-text   text           —     never named
              differential   0     not listed
  notes       comment        1     by seed: 1
              answer         1     by seed: 1
              graded         0.5   by seed: 0.5, 0, 1
  raw         text           —     never named
no target: free-text dont-miss
judged
  comment   verdict, seed 1   meets true   It reads the case as the note does and would lead to the same actions.
  answer    verdict, seed 1   meets true   It reads the case as the note does and would lead to the same actions.
  graded    graded, seed 1    points 1     It gets the reading right but leaves out an action the note calls for.
            graded, seed 2    points 0     It misses what the note leads with.
            graded, seed 3    points 2     It reaches the note's reading of the case and its essential actions.
recorded as run 1 of trial 03cf2d, run 7c620419
```

When the answer should follow a structure (a management plan, a list of
diagnoses), the shell also says whether it did: `valid`, or `invalid` with
what is wrong. A model that fails, a server that errors, or an answer that
can't be read is said in red, and the run is recorded all the same. A case
whose source the endpoint isn't cleared for is refused before anything is
sent, as are tools on a sensitive source:

```
alice plan-web (en, Qwen/Qwen3-8B-AWQ)×qwen3-8b-awq@fake #69535> run DutchFall10w
refused: the skeleton's tools would get content from source sample, which is sensitive, and tools can't be cleared yet
```

A model that runs away, writing nothing but whitespace token after token
as gpt-oss can at the end of its answer, is stopped after 100 tokens of it
and said in red: `stopped: nothing but whitespace for 100 tokens`. What it
wrote before stands as its answer. A structured answer cut short is closed
where it stopped (a string it hadn't finished is closed too), said as
`salvaged`, and is checked, read and scored as any other; the run is
recorded with the stop as its error. [vllm.md](vllm.md) says why gpt-oss
does it, and how to serve it so that it doesn't. `chatddx fake-engines
--runaway` makes the fake engines run away at the end of every answer, to
try it.

Press Ctrl-C to stop a run while it streams. What came so far is recorded,
as stopped. While the run is written down and scored, a first Ctrl-C waits
for it, and a second stops the scoring; `score` scores what is left.

### `batch TAG...`

Runs the cell on every case with any of the tags, as one run under the
shell's seed, a line per case. The token count climbs while the case runs;
then the line fills in with how it went. The run is then scored, and a
table gives each case's score per view, by case, and a summary per view.

```
alice free-text-guided (sv, Qwen/Qwen3-8B-AWQ)×qwen3-8b-awq@fake #42> batch edn
batch: free-text-guided (sv, Qwen/Qwen3-8B-AWQ) × qwen3-8b-awq@fake × 20 cases tagged edn, seed 42
case            tokens  outcome
casesfromedn13      50  completed
casesfromedn9       50  completed
...
judging casesfromedn1: comment by verdict, seed 1 of 1      51  meets true
...
                 free-text  free-text     free-text  notes    notes   notes   raw
 case            text       differential  dont-miss  comment  answer  graded  text
 casesfromedn1   —          0             —          1        1       0.5     —
 casesfromedn10  —          0             —          —        —       —       —
 ...
 scorer     view          scored  mean  stderr  no answer  no target  no value
 free-text  text          0       —     —                             20
            differential  20      0     0
            dont-miss     1       0     0                  19
 notes      comment       1       1     0                  19
 ...
recorded as run 1 of trial 9319f5, run e4a95af3
```

- **Tags** say which set a case belongs to: `dutch-fall`, `edn` and
  `openxddx` in the sample. `batch edn dutch-fall` runs both sets.
- **The lines** come in the order the cases are sent; the table goes by
  case.
- **The outcome** is `completed`, or `valid`, `invalid` or `salvaged` for
  structured answers; `unread`, `errored` or `stopped` when no answer came,
  with the error at the end of the line. A case whose model runs away is
  stopped as `run` stops it, and the batch goes on.
- **In the table**, `—` means no value. **The summary** counts the cases
  scored, their mean and standard error, and apart those with no value:
  where no answer came, where the case has no target, and for any other
  reason. A value such as `@44` is where something was first named, in
  characters, not a score from 0 to 1.
- **What the scorers note**, such as a call that failed, is said once
  after the tables, with how often: `(×4)`.
- **The seed** is the shell's, the same for every case, and shown in the
  first line. A single `run CASE` afterwards, under the same seed, repeats
  what the batch did for that case.
- **Ctrl-C once** lets the case under way finish, and then stops; the line
  says so. **Ctrl-C again** stops that case too, recorded as stopped.
- The same vignette is in one case only, so it is never run twice.

## Looking back

### `runs [COUNT]`

Lists your latest runs, the last 20, or as many as you say: when, what ran
(configuration, endpoint, case and seed), how it went, and per scorer the
mean of each view.

```
alice #42> runs 2
 run       when              trial   what ran                                            outcome       scores
 e4a95af3  2026-10-12 23:24  9319f5  free-text-guided (sv, Qwen/Qwen3-8B-AWQ) ×          20 completed  free-text —/0/0
                                     qwen3-8b-awq@fake × 20 cases (seed 42)                            notes 1/1/0.5
                                                                                                       raw —
 ceb350fd  2026-10-12 23:24  492da1  diagnoses (en, Qwen/Qwen3-8B-AWQ) ×                 valid         diagnoses 0/—
                                     qwen3-8b-awq@fake × Dutchfall11w with ultrasound
                                     (seed 7)
```

A run that never finished, as when the shell is killed mid-run, says
`unfinished`.

### `replay [RUN]`

Shows a run again as it streamed, with when it ran, where, and on which
build of chatddx. Without a run, the latest; otherwise the first letters of
its id from `runs` are enough: `replay 809b`. The request isn't kept, so
the shell renders it again and says whether it is the one that was sent.
A batch is shown by its lines and tables.

```
alice #69535> replay 809be1a5
run 809be1a5 of trial c5cd8e: diagnoses (en, openai/gpt-oss-20b) × gpt-oss-20b@fake × Dutchfall14w (seed 17)
2026-10-12 23:24, finished, at http://127.0.0.1:12100/v1/, on chatddx 0.0.0+dev
the request, rendered again from the trial and the source, is the one that was sent
[thinking] Breathlessness in known COPD with a viral trigger.
{"diagnoses": ["COPD exacerbation", "Pneumonia", "Pulmonary embolism"]
(114 out)
stopped: nothing but whitespace for 100 tokens
salvaged: cut short, and read with its structure closed
valid
differential
  1. COPD exacerbation
  2. Pneumonia
  3. Pulmonary embolism
scores
  diagnoses   differential   1   1. COPD exacerbation
              dont-miss      1   Pulmonary embolism
```

## Scoring

A run is scored as soon as it is recorded, under every scorer that applies
to it. The scorers compare what the answer says with your expectation of
the case.

### `scorers`

Lists the scorers, view by view: the metric, what part of an answer it
reads, which part of the expectation it holds that to, whose it is, and
whether the cell's output offers what it reads.

```
alice plan (en, Qwen/Qwen3-8B-AWQ)×qwen3-8b-awq@fake #4479> scorers
 scorer     view          metric                     reads                      held to                               owner    the cell
 diagnoses  differential  reciprocal_rank            $.diagnoses[*]             /diagnosis                            archive  offers it
            dont-miss     mentions                   $.diagnoses[*]             /dont_miss                                     offers it
 free-text  text          first_mention              the whole answer           /diagnosis                            archive  doesn't offer it
            differential  reciprocal_rank            the whole answer, lines@1  /diagnosis                                     doesn't offer it
 notes      comment       verdict, judged by verdict the whole answer           $.notes[?@.author == 'Olof'].comment  archive  doesn't offer it
            graded        points, judged by graded   the whole answer           $.notes[?@.author == 'Olof'].comment           doesn't offer it
 plan       differential  reciprocal_rank            $.diagnoses[*].diagnosis   /diagnosis                            archive  offers it
 ...
```

- `reciprocal_rank`: 1 if the diagnosis is first in the differential, 1/2
  if second, and so on; 0 if it isn't there.
- `first_mention`: how many characters of the answer come before the
  diagnosis is first named, shown as `@19`; none if it is never named.
- `mentions`: 1 if the warning, the disposition or the diagnosis not to be
  missed names what the case expects, or names nothing where the case
  expects nothing; 0 if not.
- `verdict`, `points`: the share of the judge's seeds that say the answer
  meets the note, and their mean grade out of the most there is.

A scorer applies to a run when the run's output offers every view it
reads; views that read the whole answer are for free text. Where no answer
came, a view has no value rather than 0.

### `score [RUN]`

Scores whatever hasn't been scored as the scorers and expectations are
now. An expectation changed since makes earlier runs of that case waiting
to be scored again; `score` catches them up, and ends with each view's
summary. With a run, it scores that run, or says why not, or shows its
scores when it is scored already.

```
alice #69535> score 809be1a5
run 809be1a5 of trial c5cd8e: diagnoses (en, openai/gpt-oss-20b) × gpt-oss-20b@fake × Dutchfall14w (seed 17)
scored already, as the scorings are now
scores
  diagnoses   differential   1   1. COPD exacerbation
              dont-miss      1   Pulmonary embolism
[info] answer.salvaged: cut short, and read with its structure closed; the call ended with: stopped: nothing but
whitespace for 100 tokens
```

### `take [from OWNER] [TAG...]`

You are scored against your own expectations only. `take` makes the
expectations shared with you your own, for the cases with any of the tags,
or all cases; it keeps those you already have. Where several people share
one for a case, it names them, and `take from OWNER` takes theirs.

```
alice #42> take dutch-fall
take: 30 cases tagged dutch-fall, under targets
 taken          none
 yours already  30: DutchFall10w Dutchfall11w Dutchfall12w ... and 20 more
```

## Keeping and sharing

### `save NAME`

Keeps the cell's configuration, with whatever you changed with `set`, as a
configuration of your own under NAME, and puts it in the cell. Saving
again under a name you have makes a new version of it, or none if nothing
changed.

```
alice free-text-guided (sv, Qwen/Qwen3-8B-AWQ)+reasoning=off×qwen3-8b-awq@fake #42> save my-free-text
saved as my-free-text: created 4bc0cb
cell: my-free-text × qwen3-8b-awq@fake
```

## Leaving

`quit`, `exit` or Ctrl-D. Ctrl-C at the prompt clears the line; during a
command it ends the command, not the shell.

The lines you type are kept in `~/.chatddx_history` (or the file given with
`--history`), so the arrow keys bring them back next time. The shell also
reads lines from a pipe, which is handy for a fixed routine; it echoes each
line, and stops at the first that fails, exiting with 1:

```
printf 'cell plan qwen3-8b@pelle\nseed\nbatch edn\n' | chatddx repl alice
```

```
AGENT: remove
An empty heading left from AGENTS.md's old "Proposed amendments" convention, which no doc keeps since.
```
## Proposed amendments

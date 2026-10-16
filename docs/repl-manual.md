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
development environments set it to the sample. The model facts are those
init-data stored: the bundled ones and the World's own `facts.toml`, and
any `chatddx init-data --facts PATH` adds.

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

## Getting around

### `help`

Lists every command, with the words it takes. A word in brackets is
optional; `TAG...` means one tag or several.

### `configurations [NAME]`
Lists the configurations you can use: yours, and those shared with you.
Each row is a configuration, with the languages it can be sent in, its
own first, then what each part is, its engine last. Judge configurations
follow, in a table of their own.

```
alice #2475> configurations
 configuration     languages  instructions  few_shot        prompt  output                    ...  translations  ...  engine             owner
 diagnoses         en         —             —               case    diagnoses                 ...  —             ...  qwen3-8b-awq@fake  yours, from archive
 diagnoses-tool    en         —             —               case    diagnoses-tool            ...  —             ...  qwen3-8b-awq@fake  yours, from archive
 free-text         en         —             —               case    free-text                 ...  —             ...  qwen3-8b-awq@fake  yours, from archive
 free-text-guided  en, sv     clinician     worked-example  case    free-text                 ...  sample        ...  qwen3-8b-awq@fake  yours, from archive
 plan              en         —             —               case    management-plan           ...  —             ...  qwen3-8b-awq@fake  yours, from archive
 plan-prompted     en         —             —               case    management-plan-prompted  ...  —             ...  qwen3-8b-awq@fake  yours, from archive
 plan-shown        en         —             —               case    management-plan-shown     ...  —             ...  qwen3-8b-awq@fake  yours, from archive
 plan-web          en         —             —               case    management-plan           ...  —             ...  qwen3-8b-awq@fake  yours, from archive

judge configurations
 configuration  languages  instructions  prompt  output   ...  engine             owner
 judge          en         judge         judge   verdict  ...  qwen3-8b-awq@fake  yours, from archive
 judge-graded   en         judge         judge   grade    ...  qwen3-8b-awq@fake  yours, from archive
```

`yours, from archive` is your copy of a configuration the archive (the
shared data set) holds; the archive's own row is left out. With a name,
it lists the configurations of that name, a row each:

```
alice #2475> configurations plan
 configuration  languages  prompt  output           sampling     engine             owner
 plan           en         case    management-plan  recommended  qwen3-8b-awq@fake
 plan           en         case    management-plan  recommended  qwen3-8b-awq@fake  archive
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
word: a configuration after `use`, an endpoint after `on`, an engine
after `set engine`, a case after `run` (`Dutchfall11w with ultrasound`
included), a tag after `run tag` or `show tag`, a run after `replay`.

## Choosing what to run

### `use CONFIGURATION`

Puts a configuration in the cell.

```
alice #2475> use plan
cell: plan × qwen3-8b-awq@fake
alice plan×qwen3-8b-awq@fake #2475>
```

The endpoint is the one serving the configuration's engine, here the
engine the sample's configurations are made for. A configuration someone
else shares with you is named with its owner first: `use bob/bobs-plan`.
A configuration has one name, whatever the languages its cases are in:
`use free-text-guided`. Names may hold spaces, and need no quotes. With
an endpoint you named in the cell (see `on`), `use` puts that endpoint's
engine in the configuration.

### `on ENDPOINT`

Puts an endpoint in the cell, and the engine it serves in the cell's
configuration, keeping everything else you chose. The configuration is
worked out again for the new engine's model:

```
alice plan×qwen3-8b-awq@fake #2475> on gpt-oss-20b@fake
cell: plan+engine=gpt-oss-20b@fake × gpt-oss-20b@fake
[info] facts.output_note: harmony renders no response_format: the model reads the schema only if the guidance shows it
alice plan+engine=gpt-oss-20b@fake×gpt-oss-20b@fake #2475>
```

The prompt shows the engine you swapped in (`+engine=gpt-oss-20b@fake`);
`on qwen3-8b-awq@fake` takes it out again, since that endpoint serves the
configuration's own. Whenever the cell changes, the shell says what the
lints find in it, and what the new engine's model can't do (see `set`).

### `cell CONFIGURATION ENDPOINT`

Both at once: the configuration, with the endpoint's engine in it.

```
alice #2475> cell free-text qwen3-8b-awq@fake
cell: free-text × qwen3-8b-awq@fake
```

### `set PART CHUNK`

Changes one part of the cell's configuration, leaving the rest as it is.
For example, to have the model answer without thinking first:

```
alice plan×qwen3-8b-awq@fake #2475> set reasoning off
cell: plan+reasoning=off × qwen3-8b-awq@fake
```

The prompt shows what you changed (`+reasoning=off`). A reasoning chunk
asks for a level, as `off`, and the engine's model is asked for it as its
facts say. `none` takes an optional part out: `set toolset none` takes
the tools away. Setting the configuration's own chunk again unsets the
part, and a chunk that doesn't fit is refused, leaving the cell as it
was. Choosing a configuration again with `use` or `cell` forgets what you
set, but for the engine of an endpoint you named; `on` another endpoint
keeps it all, worked out again for the new engine's model. A level the
model can't honour lands on the nearest it can, where its facts say so,
and `show` says where (see below):

```
alice plan+reasoning=off×qwen3-8b-awq@fake #2475> on gpt-oss-20b@fake
cell: plan+reasoning=off+engine=gpt-oss-20b@fake × gpt-oss-20b@fake
[info] facts.output_note: harmony renders no response_format: the model reads the schema only if the guidance shows it
```

Where the facts refuse it, as gpt-oss refuses a thinking budget, the
cell changes all the same, and the shell says why in yellow; `set`
another chunk to mend it:

```
alice plan+reasoning=on-budget-2048×qwen3-8b-awq@fake #2475> on gpt-oss-20b@fake
cell: plan+reasoning=on-budget-2048+engine=gpt-oss-20b@fake × gpt-oss-20b@fake
openai/gpt-oss-20b: no thinking budget is documented for harmony: set another in its place
```

`set engine NAME` swaps the engine alone, named as `endpoints` lists it,
and the cell runs at the endpoint serving it; an endpoint you named that
serves another engine is let go.

### `show`

Shows the cell: each part and what it is, the engine among them, where
a reasoning level or a recommended sampling landed on the engine's model,
the endpoint and the name its engine is served under, the messages the
model will read, with the case's place marked (`‹vignette›`), and the
settings that will be sent. Then the languages the cases are in: how
many in each, and whether they are sent as written, translated, or left
out, and why. Then what the lints find, and a table of the scorers: for
each view, whether this kind of answer gives it anything to read, and
how many cases have the target it needs. Nothing is sent.

```
alice plan×qwen3-8b-awq@fake #4479> show
cell: plan × qwen3-8b-awq@fake
 part          chunk              is
 endpoint      qwen3-8b-awq@fake  qwen3-8b-awq@fake, served as sha256:cc0dc8fbbc8dbb3a62d274c6ce62ee4bc9d909b05aef6263015cb46459fdc42f at
                                  http://127.0.0.1:12099/v1/
 instructions  —
 few_shot      —
 prompt        case               "{vignette}{appendices}"
 output        management-plan    native output: management_plan_v1
 sampling      recommended        recommended sampling, for reasoning on
 reasoning     —
 ...
 engine        qwen3-8b-awq@fake  qwen3-8b-awq@fake on vllm 0.24.0+fake (none)
system
Fill in the management plan for the case.
user
‹vignette›‹appendices›
body
{
  "model": "sha256:cc0dc8fbbc8dbb3a62d274c6ce62ee4bc9d909b05aef6263015cb46459fdc42f",
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
languages
en: 79 cases, as written
sv: 20 cases, left out: plan has no translations into sv
lints
[warning] translations.missing: 20 cases are in sv, and left out: plan has no translations into sv
 scorer     view          of 99 cases
 diagnoses  differential  99 have it
 diagnoses  dont-miss     6 have it; missing: Dutchfall11w Dutchfall13w Dutchfall16w Dutchfall17w Dutchfall18w Dutchfall19w Dutchfall1w Dutchfall20w
                          Dutchfall21w Dutchfall22w and 83 more
 free-text  text          the output offers no such view
 ...
 plan       differential  99 have it
 plan       warning       99 have it
 plan       disposition   99 have it
 ...
```

Each case is sent in its own language: as written in the
configuration's, translated where its translations carry it into the
case's, and left out where they don't, said in yellow. `plan` is
written in English, with no translations, so the sample's 20 Swedish
cases are left out of it; `free-text-guided` has translations into
Swedish (`sample`), and sends them translated: `sv: 20 cases,
translated`.

A view that reads the whole answer is offered by free text only. Cases
with missing targets can still be run; the views that need the missing
target just leave them out. The output's schema and the tools' parameters
are left to `show output` and `show tool`.

With `set reasoning off` and `on gpt-oss-20b@fake`, `show` says where
the level landed on gpt-oss, which always reasons, and why, and the
sampling follows the level it landed on:

```
alice plan+reasoning=off+engine=gpt-oss-20b@fake×gpt-oss-20b@fake #4479> show
cell: plan+reasoning=off+engine=gpt-oss-20b@fake × gpt-oss-20b@fake
 part          chunk                                               is
 endpoint      gpt-oss-20b@fake                                    gpt-oss-20b@fake, served as
                                                                   sha256:fc08c407478623b2afdb709752f30ecc3333de3142a0d534bdbbb378a6d8e841 at
                                                                   http://127.0.0.1:12100/v1/
 ...
 sampling      recommended                                         recommended sampling, for reasoning low
 reasoning     off (set; plan has —)                               reasoning off → low, its nearest: always reasons: vLLM rejects reasoning_effort =
                                                                   none for harmony
 ...
 engine        gpt-oss-20b@fake (set; plan has qwen3-8b-awq@fake)  gpt-oss-20b@fake on vllm 0.24.0+fake (none)
...
```

### `show tag TAG...`

The same, with the languages, the lints and the scorers' table counting
only the cases with any of the tags: the cases `run tag` would run.

```
alice plan×qwen3-8b-awq@fake #4479> show tag edn
...
languages
sv: 20 cases, left out: plan has no translations into sv
lints
[warning] translations.missing: 20 cases are in sv, and left out: plan has no translations into sv
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
1 run of yours with it
 scorer     view          scored  mean  stderr  no answer  no target  no value
 free-text  text          1       @44   0
            differential  1       0.5   0
            dont-miss     0       —     —                  1
 notes      comment       1       1     0
            answer        1       1     0
            graded        1       0.5   0
 raw        text          1       @44   0
```

`show case Dutchfall11w with ultrasound` shows that case, with the
ultrasound's text and the expectation of its own. An expectation shared
with you that you haven't taken says so (see `take`).

The kinds are `case`, `endpoint`, `configuration`, the nine chunk parts,
`tool`, `scorer`, `judge`, `expectation`, `expectation_schema`,
`appendix`, `canary_set`, `model`, `engine` and `facts`: `show facts
openai/gpt-oss-20b` is what the facts say of gpt-oss. A judge counts the
runs it judged and its calls, an endpoint the judge calls made at it too,
and a scorer the runs it scored.

### `reasoning`

Shows, in one table, what every reasoning level becomes on every model
the stored facts know, with the endpoints serving each: the switch or
effort that gets sent, the sampling recommended with it, the level it
falls back to (`→ on`), the nearest it lands on and why (`→ low`, `its
nearest: always reasons: …`, since gpt-oss can't stop thinking), or why
a model refuses it. The last row says how a thinking budget is sent, or
why a model refuses one. The level your configuration asks for, and the
endpoint the cell runs at, are marked with `▸`.

## Running

### `seed [SEED]`

The shell holds a seed, shown in the prompt after `#`. Every run sends it
to the model, which uses it for the random choices it makes while writing.
The same seed on the same cell and case asks for the same answer again, so
a run can be repeated, and it is recorded with its seed.

- `seed` draws a new random seed, below 100,000.
- `seed 42` holds 42; any whole number from 0 to 2147483647 will do.

```
alice free-text×qwen3-8b-awq@fake #66272> seed
seed: #59048
alice free-text×qwen3-8b-awq@fake #59048> seed 42
seed: #42
```

Draw a new seed whenever you want fresh answers rather than a repeat of
ones you already have: the same `run tag` twice under the same seed asks
the same questions the same way twice.

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
alice free-text×qwen3-8b-awq@fake #42> run DutchFall10w
trial: free-text × qwen3-8b-awq@fake × DutchFall10w (seed 42)
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
recorded as run 1 of trial 5624e3, run 60758f6d
```

A seed after the case is used for this run alone, and the shell keeps its
own: `run DutchFall10w 7`. A case that sends appendices is named as
`cases` and `show case` name it: `run Dutchfall11w with ultrasound 7`.

A case is sent in its own language. A Swedish case under
`free-text-guided`, written in English with translations into Swedish,
is sent translated, and the first line says so: `trial: free-text-guided
× qwen3-8b-awq@fake × casesfromedn1, in sv, translated (seed 42)`. Under
`plan`, which has no translations, it is refused: `no case can be sent:
plan has no translations into sv`.

The views a case has no target for aren't scored, and are named once
under the scores. When a view asks a judge, the shell says each call to it
as it goes, with the judge's verdict, and lists what each call said and
why after the scores:

```
alice free-text×qwen3-8b-awq@fake #42> run Dutchfall11w
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
recorded as run 1 of trial 03cf2d, run 1afe33cf
```

When the answer should follow a structure (a management plan, a list of
diagnoses), the shell also says whether it did: `valid`, or `invalid` with
what is wrong. A model that fails, a server that errors, or an answer that
can't be read is said in red, and the run is recorded all the same. A case
whose source the endpoint isn't cleared for is refused before anything is
sent, as are tools on a sensitive source:

```
alice plan-web×qwen3-8b-awq@fake #69535> run DutchFall10w
refused: the configuration's tools would get content from source sample, which is sensitive, and tools can't be cleared yet
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

### `run tag TAG...`

Runs the cell on every case with any of the tags, under the shell's
seed, a line per case: a run per language the cases are in, one after
the other, the configuration's own first. The token count climbs while
the case runs; then the line fills in with how it went. Each run is then
scored, and a table gives each case's score per view, by case, and a
summary per view.

```
alice free-text-guided×qwen3-8b-awq@fake #42> run tag edn
trial: free-text-guided × qwen3-8b-awq@fake × 20 cases tagged edn, in sv, translated (seed 42)
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
recorded as run 1 of trial 9319f5, run 2a534bff
```

- **Tags** say which set a case belongs to: `dutch-fall`, `edn` and
  `openxddx` in the sample. `run tag edn dutch-fall` runs both sets.
- **Languages:** cases in several languages make a run per language,
  whose first line says which, and `translated` where the configuration's
  translations carry it there: `run tag dutch-fall edn` under
  `free-text-guided` runs 30 cases `in en`, then 20 `in sv, translated`.
  Cases in a language the configuration has no translations into are
  left out, and the last line says so: under `plan`, `left out: 20 cases
  in sv, as plan has no translations into sv`. With every case left out,
  as for `run tag edn` under `plan`, nothing runs.
- **The lines** come in the order the cases are sent; the table goes by
  case.
- **The outcome** is `completed`, or `valid`, `invalid` or `salvaged` for
  structured answers; `unread`, `errored` or `stopped` when no answer came,
  with the error at the end of the line. A case whose model runs away is
  stopped as `run` stops it, and the run goes on.
- **In the table**, `—` means no value. **The summary** counts the cases
  scored, their mean and standard error, and apart those with no value:
  where no answer came, where the case has no target, and for any other
  reason. A value such as `@44` is where something was first named, in
  characters, not a score from 0 to 1.
- **What the scorers note**, such as a call that failed, is said once
  after the tables, with how often: `(×4)`.
- **The seed** is the shell's, the same for every case, and shown in the
  first line. A single `run CASE` afterwards, under the same seed, repeats
  what `run tag` did for that case.
- **Ctrl-C once** lets the case under way finish, and then stops; the line
  says so. **Ctrl-C again** stops that case too, recorded as stopped.
  Either way, the runs in the languages still to come are stopped before
  their first case.
- The same vignette is in one case only, so it is never run twice.

## Looking back

### `runs [COUNT]`

Lists your latest runs, the last 20, or as many as you say: when, what ran
(configuration, endpoint, case and seed, and the language a translated
run was sent in), how it went, and per scorer the mean of each view.

```
alice #42> runs 2
 run       when              trial   what ran                                                                      outcome       scores
 2a534bff  2026-10-16 08:06  9319f5  free-text-guided × qwen3-8b-awq@fake × 20 cases, in sv, translated (seed 42)  20 completed  free-text —/0/0
                                                                                                                                 notes 1/1/0.5
                                                                                                                                 raw —
 1afe33cf  2026-10-16 08:06  03cf2d  free-text × qwen3-8b-awq@fake × Dutchfall11w (seed 42)                        completed     free-text —/0/—
                                                                                                                                 notes 1/1/0.5
                                                                                                                                 raw —
```

A run that never finished, as when the shell is killed mid-run, says
`unfinished`.

### `replay [RUN]`

Shows a run again as it streamed, with when it ran, where, and on which
build of chatddx. Without a run, the latest; otherwise the first letters of
its id from `runs` are enough: `replay 06b5`. The request isn't kept, so
the shell renders it again and says whether it is the one that was sent.
A run of several cases is shown by its lines and tables.

```
alice #69535> replay 06b5bbd4
run 06b5bbd4 of trial c5cd8e: diagnoses+engine=gpt-oss-20b@fake × gpt-oss-20b@fake × Dutchfall14w (seed 17)
2026-10-16 08:05, finished, at http://127.0.0.1:12100/v1/, on chatddx 0.0.0+dev
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
alice plan×qwen3-8b-awq@fake #4479> scorers
 scorer     view          metric                      reads                                       held to                               owner    the cell
 diagnoses  differential  reciprocal_rank             $.diagnoses[*]                              /diagnosis                            archive  offers it
            dont-miss     mentions                    $.diagnoses[*]                              /dont_miss                                     offers it
 free-text  text          first_mention               the whole answer                            /diagnosis                            archive  doesn't offer it
            differential  reciprocal_rank             the whole answer, lines@1                   /diagnosis                                     doesn't offer it
            dont-miss     mentions                    the whole answer, lines@1                   /dont_miss                                     doesn't offer it
 notes      comment       verdict, judged by verdict  the whole answer                            $.notes[?@.author == 'Olof'].comment  archive  doesn't offer it
            answer        verdict, judged by verdict  the whole answer                            $.notes[?@.author == 'Olof'].answer            doesn't offer it
            graded        points, judged by graded    the whole answer                            $.notes[?@.author == 'Olof'].comment           doesn't offer it
 plan       differential  reciprocal_rank             $.diagnoses[*].diagnosis                    /diagnosis                            archive  offers it
            warning       mentions                    $.acute_warning                             /warning                                       offers it
            disposition   mentions                    $.management.disposition                    /disposition                                   offers it
            dont-miss     mentions                    $.diagnoses[?@.critical == true].diagnosis  /dont_miss                                     offers it
 raw        text          first_mention               the whole answer                            /diagnosis                            archive  doesn't offer it
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
alice #69535> score 06b5bbd4
run 06b5bbd4 of trial c5cd8e: diagnoses+engine=gpt-oss-20b@fake × gpt-oss-20b@fake × Dutchfall14w (seed 17)
scored already, as the scorings are now
scores
  diagnoses   differential   1   1. COPD exacerbation
              dont-miss      1   Pulmonary embolism
[info] answer.salvaged: cut short, and read with its structure closed; the call ended with: stopped: nothing but whitespace for 100 tokens
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
alice free-text-guided+reasoning=off×qwen3-8b-awq@fake #42> save my-free-text
saved as my-free-text: created 00e383
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
printf 'cell plan qwen3-8b@pelle\nseed\nrun tag dutch-fall\n' | chatddx repl alice
```

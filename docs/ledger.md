# Ledger

The ledger says what happened: which requests a run sent and what came back, and how a score graded them. It is
written down as *records*, which are added as things happen and never changed, and the ledger is all of them.
Records refer to components by digest and to each other by id.

It guarantees a run can be shown to have happened under the conditions it claims. This document describes what the
ledger records and why, and what checking it shows. Names, fields, rules and finding codes are in the API,
docs/ledger-api.md.

The ledger builds on the factors and nothing else. The rig writes it: the runner writes runs and the scoring pass
writes scores.

## How records work

### Logs and stages
Every record belongs to a *log*: a run or a score. A log opens with a start record saying what is about to happen,
gains one record for each thing that happens, and closes with a finish record that seals it. The start and finish
records are the log's *stages*. A new kind of stage would be a new record in the same log, not a new log.

### What a record holds
A record holds three kinds of content.

| Content | What it is | Where |
| --- | --- | --- |
| Plan | What the run or the score is set to do, written before it starts: its recorded factors. | Start records |
| Conduct | What the rig itself did: the requests it sent, when, how many attempts they took, what the tools sent back, the values a scorer gave. | Item records |
| Observation | What the world answered: the evidence of the observed factors, such as the responses, the model an engine says it is, the prompt it read, and the vignette as read at its source. | Item records |

A run item holds all three: which item it is comes from the plan, its requests and their times are conduct (the times
also show how fast the engine answered), and its responses are observations. Finish records add conclusions drawn from
the rest: the seal and the findings.

Checking a log sets these side by side, and beside the pinned factors, to show where what happened differs from
what was declared (see "Run" and "Score").

### Canonical form and versions
A record is written out in one fixed way, as a component is (docs/factors.md, "Canonical form and digest"), so the same
record always gives the same bytes, and a seal over records is as stable as a digest over a component.

Each record type has a schema version, under the components' rule (docs/factors.md, "Versions"): adding a field with a
backward-compatible default needs no new version; changing an existing field's meaning or default does. Records written
under another version are refused rather than guessed at, so after a bump the store can't return the old ones
(docs/store.md, "Known gaps").

Every time is kept in UTC, so the same instant is written, and sealed, the same way whatever the writer's time zone.
Nothing finishes before it starts.

### Seal
A log's finish record holds its *seal*: a hash over its start record and every other record of the log. It doesn't
depend on the order storage returns records in, and adding a field with a default keeps old seals valid. Checking a log
recomputes the seal and warns when it differs: records were added, removed or changed after the log was finished. The
finish record itself is outside the seal (see "Open design issues").

### Case-derived records
Content produced from a vignette is *case-derived*. Each record type says whether it may hold any, and a new type is
assumed to unless it says otherwise. Two types do:
- run items: their responses hold the completions and the arguments the model passed to tools, and their tool rounds
  hold what the tools returned;
- score items: their judge responses grade completions and may quote them, and the scorer's detail may hold anything.

Start and finish records hold references, settings, times, seals and findings written by code. Canary calls answer
canaries, which are non-sensitive by definition (docs/factors.md, "Canary sets").

Request bodies and the prompt's token ids would carry the case's text too, so neither is stored, only their
fingerprints (see "Call").

The mark says what a record may hold. Acting on it, by restricting who reads such records or where they go, is up to
whatever stores or exports them (see "Storage").

### Errors and findings
As with components (docs/factors.md, "Errors and findings"), problems come in two strengths.
- An *error* stops the work. A record or log that breaks its own rules can't be built: stages out of order, records of
  another log, a time that finishes before it starts. Checking a run or a score stops when the records don't fit the
  components they refer to: items the trial doesn't contain, canary calls it didn't plan, a score of another run.
- A *finding* is a warning about something observed that doesn't match what was declared. It doesn't stop the work
  (see "Findings").

## Runs
A run is one execution of a trial (docs/factors.md, "Trial"). Its log is written as things happen: the start record,
then an item for each case and replicate and a canary call for each planned canary and phase, in whatever order they
happen, then the finish record.

### Run start
The start record holds the run's recorded factors:
- the trial;
- the execution settings (docs/factors.md, "Execution");
- optionally a canary set, and whether its canaries are sent at the start, at the end, or both;
- the version of the rig, and the code each of the skeleton's tools ran with, as the runner loaded it. Set beside the
  code each tool pins (docs/factors.md, "Tool"), it shows whether what ran is what should have run;
- the endpoint its calls went to, by the inventory's name for it and its address (docs/inventory.md, "Endpoints").

It is not part of the trial's digest. To run a trial again under the same conditions, start a new run with the same
trial, execution settings and canaries. On a batch-invariant engine a rerun may be bitwise identical; on other engines,
reproducing a run is best-effort (docs/factors.md, "Local engine" and "Execution").

### Run items
A run item records one request of the trial and what came back: which case and which replicate, the fingerprint of the
vignette as it was read from its source (to detect drift; docs/factors.md, "Preparing a case"), the first call, and the
tool rounds that followed.

### Tool rounds
When the skeleton offers tools and a response calls some, the runner runs them and sends another request
(docs/factors.md, "Tool rounds"). Each round records the tools run for the previous response's calls and the call that
followed.

A tool run records the call it answers, the tool, when it ran, and the text sent back to the model, as sent, since it
shaped the next request. When the tool failed, including a call that names no tool the skeleton offers, it also records
why; the text is then what the model was told in its place. The arguments aren't repeated: they are in the previous
response.

A round stopped while its tools run has no call, so it isn't recorded, and neither are its tools, even one that
reached a third party.

### Canary calls
A canary call records one canary of the run's set, sent at one phase. Canaries measure the engine before and after the
items, so start calls should be done before the first item is sent, and end calls should start after the last item call
is done.

### Run finish
The finish record closes the run with its time, its seal, and the findings the runner saw while running, such as a
vignette that changed at its source. Checking a run can be repeated at any time from its records, so what it finds isn't
stored.

### Run
Checking a run shows whether it is what its trial produces under the conditions its start record declares.

Records that can't be an account of the plan at all stop the check: work that the trial, the canary plan or the
skeleton couldn't have asked for means the records are wrong, not the world. Everything else is a warning, of four
kinds:
AGENT: change
`check_run` warns `call.failed` for each item and canary call that ended with an error: stopped, cut short,
rejected, unreachable, or left by the engine (agents/wip-runner.md, "Found in a check against the code").
---
- **Complete**: the run did all it planned. Every item and canary call is there and got a whole answer, and no item
  was left waiting on its tools.
- **Complete**: the run did all it planned. Every item and canary call is there, and no item was left waiting on its
  tools.
- **Conducted as declared**: the rig kept to its own plan. It followed the execution settings, kept the canaries clear
  of the items, and ran each tool with the code the tool pins.
- **As pinned**: the world matched the pinned factors. The engine attests to the declared model and to the prompt it
  read, and each vignette is unchanged at its source.
- **Sealed**: nothing changed after the log was finished.

Not everything is checked yet (see "Open design issues").

Two runs whose trials build their prompts alike can also be compared, to show whether the engine read the same prompt
for the same item both times.

## Call
A call records one exchange with an engine: an item's request, a tool round's, a canary's or a judge's. It holds a
fingerprint of the request, when it started and finished, how many attempts it took, the status and the response if
one came, the error if it failed, and a fingerprint of the prompt the engine read. With retries, its times span every
attempt.

The request body isn't stored, since it holds the case's text (docs/factors.md, "Rendering"). Its fingerprint doesn't
depend on how a client spells the JSON or orders the request's settings, but it does depend on the order of a schema's
properties, since that is part of what the model reads.

Rendering asks the engine for the prompt's token ids: the tokens it actually read after applying its chat template.
They encode the case's text too, so the response is stored without them and only their fingerprint is kept. Comparing
fingerprints shows whether the engine read the same prompt, without storing the text.

Fingerprints may be keyed (docs/factors.md, "Fingerprints"), and fingerprints made with different keys never match.

The response also says what the engine claims to be: the model name it answered as, which checks compare with the
declared one, and a system fingerprint, which nothing compares yet.

## Scores
A score grades one run with one scoring (docs/factors.md, "Scoring"). Its log is written the way a run's is: the start
record, an item for each run item and view, then the finish record. A score has no canary calls.

### Score start
The start record holds which run it grades, the scoring, the version of the rig, the scorer code that actually runs,
and the execution settings of its judge calls. The scorer code is a recorded factor: set beside the code the scorer
pins, it shows whether what ran is what should have run.

### Score items
A score item records how one view graded one run item: a value, whatever detail the scorer adds, and the judge calls
made for it. The value is a finite number, or empty when the item couldn't be scored. What the value means and what the
detail holds are up to the scorer (docs/factors.md, "View").

### Judge calls
A view with a judge sends one request for each of the judge's seeds (docs/factors.md, "Judge"). Each judge call records
the judge, the seed and the call. Judge calls live inside score items, so the seal covers them.

### Score finish
The finish record closes the score as a run's does, with the findings the scoring pass saw, such as an answer it
couldn't read from the run item's last response, or one that breaks the output schema and was scored anyway.

### Score
Checking a score shows whether it is what its scoring makes of its run.

Records that can't be an account of that scoring applied to that run stop the check: a score of another run, or views,
items, judges or seeds that don't exist. Everything else is a warning, of four kinds:
- **Fit**: the scoring suits the run. Its views can reach the run's answers, every case has an expectation, and the run
  had finished before the score started.
- **Complete**: every run item is graded by every view, and every judged value rests on all of its judge's seeds.
- **Conducted as declared**: the scorer ran the code it pins, and the judge calls followed the execution settings.
- **Sealed**: nothing changed after the log was finished.

## Findings
A finding (docs/factors.md, "Errors and findings") says what it is about: an item, a tool, a scorer, the run or the
score. All of the ledger's findings are warnings. They come from
- the runner and the scoring pass, while they run, kept in the finish record (see "Run finish" and "Score finish");
- checking a run or a score (see "Run" and "Score"), which can be repeated at any time, so nothing stores them;
- comparing the prompts of two runs (see "Run").

The API lists every finding (docs/ledger-api.md, "Finding codes").

## Storage
The ledger is a schema of its own (docs/store.md; tables in docs/migrations.md, "ledger"): one table per kind of
record, a log's two stages sharing one. Each row holds the record as written, which is the source of truth, and a copy
for queries. Stored records are never changed or deleted.
- Storing a record checks only what the database can: that it is new, and that what it refers to is stored. A log is
  validated when it is read back.
- What a record refers to comes first: a run's trial, a score's scoring and an item's case must already be stored, an
  item needs its log's start record, and a score needs its run's. A run's canary set isn't tied to the run in the
  database. The runner stores it with the trial; another writer must store it too, or the run can't be checked.
- Checking a run or a score takes the components it needs from the store.
- The reader role can't read the ledger at all, which is the store's answer to "Case-derived records".

## Terms

| Term | Meaning |
| --- | --- |
| Record | What the rig writes when something happens; never changed. |
| Plan, conduct, observation | What a record holds: what a run or a score is set to do, what the rig did, and what the world answered. |
| Ledger | All records: the run and score logs. |
| Log | A run or a score: a start record, item records and a finish record, only ever added to. |
| Stage | A log's start or finish record. |
| Item | One request of a run, by case and replicate; or how one view graded one run item. |
| Call | One exchange with an engine. |
| Tool round | Running the tools a response called, and sending the next request. |
| Seal | The hash over a log's records, kept in its finish record. |
| Case-derived | Produced from a vignette: completions, tool arguments and results, judge responses. |
| Attestation | What the engine says about itself: the model it answered as and the prompt it read. |

## Open design issues
These are open questions of design. Where the code falls short of this document, the API says so
(docs/ledger-api.md, "Known gaps").

### Some of what happened isn't checked
Most of the plan is compared with what happened (see "What a record holds"), but not all:
- timeouts: a call's times span all its attempts, so an attempt that ran past the timeout can't be told from them;
- the request a call sent and the request it should have been:
  The repl's replay rebuilds each item's first request from the trial and the vignette and holds it to the call's
  fingerprint. A later round's request, which could be rebuilt from the stored responses and tool runs, and a judge
  request, from the scorer's reading of the answer (docs/factors.md, "Judge"), aren't rebuilt, and checking a run
  rebuilds none.

### Smaller issues
- **Canary drift isn't checked.** Nothing compares canary outputs between phases or between runs.
- **Only run items are attested.** Canary calls and judge calls get no model check and no prompt check.
- **The system fingerprint is kept but never compared** between calls or runs.
- **The finish record is outside the seal.** Its time and findings could change without the seal noticing.
- **Judge calls don't record where they went.** A score's start record has no endpoint, so the ledger can't show which
  one received the case-derived content a judge reads, as a run's does.
- **Records aren't in bundles.** A bundle (docs/factors.md, "Registries and bundles") carries components only; how
  records travel with the factors they reference, for example for publication, isn't specified.
- **Findings have no mechanism of their own.** The runner and the scoring pass keep those they see in the finish record,
  and the checks give the rest when called. They might benefit from a separate mechanism, as lints are for factors, but
  nothing is planned or decided.

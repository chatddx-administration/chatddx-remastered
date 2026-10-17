# Runner

The runner sends a trial's requests to an engine and writes what happened to the ledger. The scoring pass grades a
finished run with a scoring, sending a judge's requests where a view names one. Both string together pieces documented
elsewhere: the factors that render a request and prepare a case (docs/factors.md), the ledger's records and checks
(docs/ledger.md), the store and the catalog (docs/store.md, docs/catalog.md), and the World inventory that says where
an engine is reached and whether it may receive a case (docs/inventory.md).

This document describes what a run and a score do and why. Names, signatures, refusals and messages are in the API,
docs/runner-api.md.

The bench calls the runner for the repl and the API: it starts a run of a variation for each language its cases are
sent in, and scores a finished run under every scorer that applies to it.

## A run
A run is one execution of a trial at one endpoint (docs/ledger.md, "Runs"). It has three steps, and nothing is
written until the first is done.

### Starting
Starting a run refuses, before anything is written:
- an endpoint the gate refuses (see "The gate");
- a tool whose code isn't shipped by the running chatddx, or not at the version the tool pins (docs/factors.md,
  "Tool");
- a concurrency above the endpoint's `max_jobs`;
- phases to send canaries at without a canary set.

Then it stores the trial with everything it refers to, and the canary set, writes the run's start record and the run's
owner entry in the catalog. The start record holds the version of the rig, the execution settings, the canary set and
its phases, the code each tool ran with, and the endpoint by name and address.

### Sending
The items are sent in the execution's order (docs/factors.md, "Execution"). Each is prepared as docs/factors.md,
"Preparing a case", has it: its vignette fetched from its source, checked for drift and cleaned, its appendices
joined, and the request rendered for the model the engine is served under and the replicate's seed. A case that can't
be read is a finding, and the run goes on without it.

A call streams on the wire only (see "Calls"). When the skeleton has tools, the item goes on in rounds (see "Tool
rounds"). Each item is written as soon as its last call is done, so a run that stops leaves every item it finished.

Canaries are sent one at a time, the start phase's before the first item and the end phase's after the last, whatever
the concurrency, so they bracket the items. They are not sensitive and need no clearance.

### Resuming
A run that wasn't finished can resume, the items and canary calls its log holds are kept, and only what it lacks is
sent. Resuming refuses what starting refuses, under the run's own execution, and an endpoint whose address is another
now, since the start record holds the one the run is sent to.

A finished run doesn't resume. The finish notes that the run resumed and how far it had come, and warns when another rig
resumed it than started it, since the start record names the rig that started it. A run with nothing written yet that
the rig which started it resumes, as the worker sends a run the request started, is noted nothing.

### Finishing
Finishing writes the finish record, with the findings the runner saw while it ran, and returns what checking the run
finds (docs/ledger.md, "Run"). A run is finished once.

## The gate
The gate guards the engines so that sensitive content may go only where it is cleared to go
(docs/chatddx.md, "Vignettes and anything made from them are sensitive").

It decides once per run, as it starts and as it resumes, and once per judge as a judged scoring starts, from what they
pin, before anything is prepared or rendered: every request a run sends, each tool round's and attempt's included, goes
to the endpoint the gate admitted. The gate refuses, in order:
- an endpoint that serves another engine than the one asked for;
- a sensitive source of the cases the endpoint isn't cleared for (docs/inventory.md, "Clearance");
- tools on a sensitive source, since a tool can't be cleared yet;
- an endpoint whose credential names a secret that isn't set;
- an endpoint whose server doesn't list the name its engine is served under (docs/runner-api.md, "gate.py").

The first three hold for as long as the World is as it is. The last two may pass later: a secret is set, a server
comes up. The bench uses the difference (see "What applies to a run").

The secret goes only into the request's `Authorization` header. No stored row holds it.

## Calls
A call is one exchange with an engine: one request, sent in one or more attempts, and what came back
(docs/ledger.md, "Call"). Every call streams: the request's fingerprint is taken before the streaming options are added,
and the streamed chunks are added up to the completion an unstreamed request would have had. Streaming is only how a
call travels; what is stored is the same either way. The prompt's token ids leave the response and become its
fingerprint. HTTP is the standard library's.

A call is tried again only when the request didn't get through: a connection that failed, a 429 or a 5xx, after a
pause that doubles each time, up to the execution's retries. Once a stream has started, what comes is the answer, and
it isn't tried again. An engine's refusal keeps its body as the call's response, as a completion would be kept.

A call is cut short, keeping what came, after the execution's run of whitespace tokens in a row (a runaway answer), and
when its timeout has passed since the stream started. The same timeout bounds each wait on the connection, so an
engine that stalls ends the call too. An engine that goes away before the end of the stream leaves an error on the
call, with what came. Each is recorded as the call's error; checking the run notes it (docs/ledger.md, "Run").

`max_output_tokens` (docs/factors.md, "Sampling") bounds every answer, and is the usual way to. The whitespace cutoff
only saves the time a runaway burns until its tokens run out, and an execution can turn it off.

## Tool rounds
When the skeleton offers tools and a response calls some, the runner runs them, in the order the response called them,
sends their results with the next request, and records the round (docs/ledger.md, "Tool rounds"). The rounds end when a
response calls no tool, when it calls the answer tool, when a call ends with an error, or after the skeleton's
`max_rounds`.

A tool is called with the call's arguments and gives back text. When the call names no tool of the skeleton, its
arguments aren't an object that fits the tool's parameters, or the tool fails or gives back anything but text, the
model is told the error in place of a result, the error is recorded, and the run goes on.

Only shipped tool code runs, and a run records the version each tool ran at. A tool on a sensitive source is refused
by the gate.

## Order and concurrency
At concurrency 1 the items are sent one after the other on the caller's thread. Above it, the calls go out on as many
workers as the concurrency allows; everything else stays on the caller's thread: preparing each item, writing it,
the events, and stamping when it was sent. Items are stamped in the execution's order, and an item is sent only once
another call is done, so checking the run finds the order and the concurrency kept.

## Stopping
A run can be stopped three ways:
- **Stop** ends it after the items under way, which finish.
- **An interrupt** (Ctrl-C) hangs up the calls under way at once, records them as stopped, and is raised again once
  they are written. Another interrupt while they hang up leaves them out.
- **A halt** does the same from another thread, as a server's request thread must when its client leaves, and returns
  rather than raises.

A halt ends a stream that waits on a stalled engine at once, by shutting the connection down, and ends the pause
between attempts. A round stopped while its tools run is kept without its call: the tools that ran, one an interrupt
stops while it runs recorded as stopped, and no request after them (docs/ledger.md, "Tool rounds"). A halt runs no
more tools. A stopped run sends no end canaries, so checking it counts them missing.

A worker's unexpected failure is raised on the caller's thread once the other calls under way are halted and
recorded.

## Events
The caller hears a run through a callback, as it happens: an item started, a piece of what it streams, a tool run, an
item ended, a canary ended, a finding. An item starts only once it is prepared, so a case that can't be read starts
none.

A callback rather than an iterator, so an interrupt raised while the caller handles an event lands inside the call the
runner is making, which records it. With an iterator it would land in the caller's frame while the runner waited.

## A score
A score grades one finished run with one scoring (docs/ledger.md, "Scores"). It has a run's three steps.

Starting it refuses, before anything is written: a run that hasn't finished, judge calls at a concurrency above 1,
scorer code the running chatddx can't run, and a judge it can't send (see "Judges").
A scoring with no judge needs no inventory. Then it stores the scoring and
writes the start record, with the endpoint each judge's calls go to, and the score's owner entry.

Sending grades the run's items in the score's execution order. Each item's answer is read from its last call, as its
skeleton's contract has it (docs/factors.md, "Scorer"), and each view grades it, the score items of one run item
written together. A case without an expectation gets every view's item with no value. An answer that can't be read, or
that breaks the output schema, is a finding; the second is still graded.

Finishing writes the finish record with those findings and returns what checking the score finds (docs/ledger.md,
"Score").

### Judges
A judged view's metric reads the verdicts of the view's judge, one per seed (docs/factors.md, "Judge"):
- **Where its calls go.** A judge names an engine; its calls go to the one endpoint serving that engine, unless the
  caller names another, and through the gate as a run's do, for the run's cases, since a judge reads a completion.
  Several serving it and none named is refused rather than picked from, as for a run (docs/bench.md, "Outstanding").
- **What it reads.** The completion and the expectation, as the view picks them. A judge whose skeleton reads the
  vignette or the appendices is refused: no vignette goes to a judge.
- **When it isn't asked.** When the answer can't be read, the view picks nothing from it, or the judge reads the
  expectation and the view picks nothing from that, as when a case has no notes. The item has no value, with the
  reason in its detail.
- **One call per view and seed.** Views that ask the same judge the same thing ask it each time.
- **Its verdict** is read as an answer is, by the judge skeleton's contract. A verdict that can't be read counts as
  none for its seed, and one that breaks the judge's schema is still read; both are findings.

A halt or an interrupt keeps the verdicts of the seeds sent so far. The item's judged views after it, and the items
after it, aren't scored, and checking the score counts them missing.

### What applies to a run
A scorer applies to a run when its views can reach the run's answers (docs/ledger.md, "Score"), a view of the whole
answer reaching only a text answer, and the World lets each of its judges run: no judge reads the case, an endpoint
serves its engine, and that endpoint is cleared for the run's sources. A scorer the World bars is left out, so it isn't
left to score for as long as the World is as it is. What may pass later (a secret not set, an endpoint not answering)
keeps it outstanding, and scoring says why.

## Findings
The runner and the scoring pass note what they see while they work, in the finish record (docs/ledger.md,
"Findings"): a case that can't be read, a run that resumed, an answer or a verdict that can't be read, and one that
breaks its schema. Drift of a vignette is noted as preparing a case notes it (docs/factors.md, "Preparing a case").
The API lists them (docs/runner-api.md, "Finding codes").

## Terms

| Term | Meaning |
| --- | --- |
| Runner | What sends a trial's requests and writes the run. |
| Scoring pass | What grades a finished run with a scoring and writes the score. |
| Gate | What refuses an endpoint before sensitive content goes to it. |
| Endpoint | Where an engine is reached, by the World inventory's name (docs/inventory.md, "Endpoints"). |
| Round | Running the tools a response called and sending the next request. |
| Cutoff | Ending a call early, keeping what came: a runaway, or a timeout. |
| Stop, interrupt, halt | Ending a run after the items under way; at once, raising; at once, from another thread. |
| Verdict | A judge's answer, as its skeleton's contract reads it. |

## Elsewhere
- **Scripted runs**, `chatddx scripted-runs` on the bench: `docs/scripted.md`.
- **`max_jobs` across runs**, and a lost run resumed: `docs/worker.md`, "Claiming".
- **Canary sets are each endpoint's**, in the inventory (docs/inventory.md, "Endpoints"); no World's endpoint names
  one yet, though data sets hold them.
- **The gate's refusal of `qwen3-bare@fake` for `typed` cases isn't read by a test** (docs/curation.md,
  "Outstanding"); the judge `remote`'s tests read `unknown@remote`'s. The gate's tests edit the inventory instead
  (`runner/test/test_run.py`).
- **The real engines are cleared for the sample** (decided: `agents/wip-clearance.md`, "Vetted endpoints").
  `worlds/kompismoln/inventory.toml` clears `qwen3-8b@pelle` and `gpt-oss-20b@malborg` for `sample`.

## Open design issues

### What a stop leaves out
- **A call still waiting for its engine to answer at all**, under an execution with no timeout, waits on after a halt;
  only a stream can be shut down. vLLM answers at once and streams after. The bench sends no execution, so its runs
  have no timeout.

### Smaller issues
- **Tools have no time limit of their own**, and a halt waits for a tool that's running.
- **The tool interface isn't versioned**, unlike the scorer's: keyword arguments in, text out.
- **The answer tool called beside a toolset tool** ends the item, and checking the run notes the other call; no engine
  under test does that. Checking the run doesn't refuse a turn that runs the other call, though the runner never
  writes one.
- **No World's endpoint names a canary set**, though data sets hold them; canary outputs aren't compared
  (docs/chatddx.md, "Possible design issues"), and canary calls stream without events.
- **Fingerprints are unkeyed.** A call can take a key, but neither the runner nor the scoring pass passes one
  (docs/factors.md, "Fingerprints").
- **Judge calls go one at a time**, and every judged scoring confirms its judges' endpoints, even when no item needs a
  judge; an endpoint that hangs holds it up to the confirmation's timeout.
- **Every engine is asked for the prompt's token ids** (docs/factors.md, "Smaller issues").
- **No finding for reasoning that wasn't heeded**, as the old chatddx had.
- **`max_jobs` across runs** belongs to the worker, and so does asking for a lost run to resume.

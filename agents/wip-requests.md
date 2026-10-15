# Requests: work in progress

What a request is, from the chunks it is made of to the calls that send it and what the ledger keeps of it. One
section per piece of work. "Decided" means the user said so; "Take" is the agent's and still open.

## What a request is, its stages, and where clearance falls
Checked against the code at fcef71a: the runner, the ledger, the gate, the factors' rendering and the bench's looks.

### Decided
- **R1.** A request is the body one call sends to an engine (see "Options", R, for the definition).
- **K1.** The item key's wording: an item is a case's replicate in a run, its first request and each tool round's,
  each sent as a call that may take several attempts.
- **B2.** The clearance boundary is every destination of sensitive content, built where `agents/wip-clearance.md`
  builds it, the gate deciding per run.
- **C1.** The hard block guards sensitive content, the vignette included.

### Done
- **The definition, as suggestions**: `docs/chatddx.md` (glossary: fingerprint, sensitive, insert, request, call,
  attempt, tool round, item, item key, execution, sensitive, wire body; the hard block in "Compromises" and
  "Findings and errors"; the dataflow's slots, its tool rounds and its run item), `docs/factors.md` ("Requests",
  "Rendering", "Tool rounds", "Execution", "Terms"), `docs/ledger.md` ("Sensitive records", "Run items", "Call",
  "Terms"), `docs/ledger-api.md` (`ItemKey`, `RunItem`, "Known gaps"), `docs/runner.md` ("The gate", "Calls"),
  `docs/api.md` ("Sensitive content", "Terms") and `docs/scripted.md` (a turn per attempt).
- **`judge.greedy_seeds`** says a greedy judge's seeds send the same request (`src/chatddx/factors/lint.py`), as
  `docs/factors-api.md` has it.
- **`agents/wip-clearance.md`**: B2 and C1 in its scope, and what item 6 of "Before real patient data" keeps is the
  engine's error response.

### Left
- **The suggestions** wait for a human to write them in.
- **B2's other destinations**: the third parties tools send to, the database, the edges and exports, each cleared as
  `agents/wip-clearance.md` builds it.
- **"Turn"** still names a model's response in `docs/factors.md` ("every turn calls a tool") and an unsent round in
  `docs/repl.md`, beside the tool round `Turn` is.
- **K2 and K3**, if an edge comes to show an item's rounds apart, or timeouts are to be checked per attempt.

### The word today
Besides the HTTP requests people send the API and the portal, which are left aside here, "request" names an LLM
request at every stage of its life, and one thing that is several:
- **The layers it is built in**: chunks, a recipe, and the skeleton, "the frozen request" (`docs/factors.md`,
  "Requests"; `docs/chatddx.md`, glossary), and a configuration, "a request kept on a skeleton thread, each version
  with the recipe it was compiled from" (`docs/chatddx.md`, "Intended evolution of configurations").
- **What is sent**: "Rendering produces the request that is sent" (`docs/factors.md`, "Rendering"), and the
  glossary's wire body, "the exact request sent". What is fingerprinted is the request as rendered, without the
  streaming options and the `Authorization` header the wire adds.
- **A tool round's**: "A response that calls tools gets another request" (`docs/factors.md`, "Tool rounds").
- **An attempt's**: "A call is tried again only when the request didn't get through" (`docs/runner.md`, "Calls").
- **The look's**: "the request it would send, with placeholders" (`docs/api.md`, `docs/bench.md`).
- **A canary's and a judge's**: "a fixed, non-sensitive probe request"; "Judge requests are rendered like generation
  requests, once per seed" (`docs/factors.md`).
- **An item**: "Item key: (case, replicate index), which identifies one request of a run" (`docs/chatddx.md`); "Item:
  One request of a run" (`docs/ledger.md`, "Terms"); "One case's request in a run, with its calls" (`docs/api.md`,
  "Terms"). This is the one that doesn't fit: an item is several requests (see "The item key").
- **A run's requests**, all of them, and "the request follows the case", for its language.

The code uses the word for one thing: the body that one call sends (`Call.request`, its fingerprint;
`fingerprint_request`; `next_request`; `Bench.request`, the look's).

### The stages, as built
A generation item, from what people write to what the ledger keeps:

| Stage | What it holds | Made by | Sensitive | Kept |
| --- | --- | --- | --- | --- |
| Chunks | each part's text and settings | people, init-data | no | components |
| Recipe | a chunk per part, a purpose, an appendix layout | people | no | in a compilation |
| Skeleton | messages with slots, body, contract, tools and their round limit; no case, model or seed | `compile_request` | no | a component, pinned by trials and judges |
| Trial | a skeleton, an engine, the cases by their vignettes' fingerprints, text cleanup, seeds | the bench | no | a component |
| Fills | the vignette fetched, checked for drift and cleaned; the appendices joined | `prepare_case` | the vignette; appendices aren't sensitive | memory only |
| Rendered request | slots filled, the served model, the seed unless greedy, `return_token_ids` | `render` | yes | memory; its fingerprint in `Call.request` |
| Wire body | the rendered request with the streaming options, the secret in a header | `send` | yes | sent to the endpoint only |
| Attempts | the wire body again after a failed connection, a 429 or a 5xx, up to the retries + 1 | `send` | yes | their count; the last refusal's body as the response |
| Response | the stream assembled into a completion | `wire.assemble` | yes | the ledger, its prompt token ids replaced by their fingerprint |
| Tool round | the tools run on the response's calls, then the next request: the last one, the assistant's message and the results | `rounds.converse`, `next_request` | yes: the arguments go wherever the tool sends them | the tool runs, and the next call |
| Item | the first call and each round's | `RunItem` | yes | the ledger |

Beside a generation item:
- **The look** renders the skeleton with placeholders (`‹vignette›`, `‹model›`): no case, nothing sent
  (`src/chatddx/bench/seen.py:Seen.request`).
- **Rendered again** renders an item's first request with its real fills, in memory, and compares its fingerprint
  with the call's (`Seen.rendered_again`; the repl's `replay`, `GET /api/runs/{id}/rendered-again`).
- **A canary's** is literal messages and settings, the model and the seed added (`Canary.render`): not sensitive,
  one call, no rounds.
- **A judge's** is a skeleton of purpose `judge`, rendered with the view's picks of the answer and of the expectation
  as `completion` and `expectation`, once per seed, one call each, no rounds. It is sensitive through the
  completion.
- **Live deltas and tool runs** pass through the database's notification queue as they come, keyed by case and
  replicate (`src/chatddx/worker/publish.py`).

### Where clearance falls today
- **What makes a request sensitive**: the vignette's fill in a generation request, and the completion's in a
  judge's. Each later request of an item carries the earlier responses too.
- **The gate decides per run, from what the run pins**, before anything is prepared or rendered: the endpoint serves
  the trial's engine; every sensitive source of the trial's cases is cleared for it (`[cleared]`); the skeleton has no
  tools if a source is sensitive (`gate.bar`); then the secret is set and the server confirmed (`gate.admit`). It runs
  as a run starts and as it resumes, and for each judge as a judged scoring starts (`runner/score.py:judge_at`,
  `Grader.start`). Nothing is gated per item, round, attempt, judge call or canary.
- **That covers every request a run sends**: the trial pins its cases, skeleton and engine, and every call of a run,
  each round's and attempt's included, goes to the endpoint its start record names. Canaries go only there, after the
  gate, and need no clearance.
- **Tools** are refused outright on a sensitive source, by whether the skeleton has any (`bool(skeleton.tools)`),
  since no tool can be cleared yet; on a source that isn't sensitive, a tool sends the model's arguments wherever its
  code does.
- **Beyond the engine**, sensitive content also reaches the ledger (run items, score items, a score's finish), the
  notification queue, the edges (the repl's terminal; the API's no-store places; the portal), a job's `why`, which
  isn't no-store, an engine's error body kept verbatim, and any proxy the environment names. Nothing gates these;
  `agents/wip-clearance.md` tracks each ("Takes", Open 5, "Before real patient data" 4, 6, 10 and 12).
- **The words disagree on what is guarded.** The hard block is worded over sensitive content ("sending
  sensitive content to an engine without clearance", `docs/chatddx.md`), but sensitive is "content produced from
  a vignette" there, so the vignette itself isn't, while `docs/api.md` counts the vignette in. The wire body is
  "sensitive if it contains a vignette", but a judge's holds a completion and no vignette. `prepare_case`'s output is
  "the sensitive fills" in `agents/wip-clearance.md`, appendices included, which aren't sensitive. "Passed to,
  non-approved sources" (`docs/chatddx.md`, "Sensitive") uses "source" for a destination.

### The item key
`ItemKey(case, replicate)` (`src/chatddx/ledger/record.py`) keys a run item and, with a view, a score item. A run item
holds its first call and one per tool round, so up to the skeleton's `max_rounds` + 1 requests, each sent as a call.
A call holds how many attempts it took, up to the execution's retries + 1, and its times span them all. A round is its
place in `turns`; neither a round nor an attempt has an index. A judge call is a score item's, by judge and seed index.

What says otherwise, or loosely:
- **"One request"**: `docs/chatddx.md` (glossary, "Item key"), `docs/ledger.md` ("Run items": "one request of the
  trial and what came back: … the first call, and the tool rounds that followed"; "Terms"), `docs/ledger-api.md`
  (`ItemKey`, `RunItem`) and `docs/api.md` ("Terms").
- **One call**: `docs/chatddx.md`'s dataflow stores "a RunItem row with the key (case, replicate) … and a Call", and
  has no tool rounds.
- **Requests in flight**: `docs/factors.md` ("Execution") says how many "requests" may be in flight; the runner holds
  items in flight, whose rounds go one after another, and the check counts calls, canaries included.
- **The first request only**: the prompt-token comparison and rendered again read an item's first call; outcome and
  answer read its last; usage sums them all.
- **A round's request is "the same request, plus …"** (`docs/factors.md`, "Tool rounds"): the same settings and
  seed, another body and fingerprint.
- **Turn** names a tool round (`Turn`), a model's response ("every turn calls a tool"), an unsent round in the repl,
  and a scripted reply of the fake vLLM, which is consumed per HTTP attempt while `docs/scripted.md` says "one per
  call"; they differ once retries are allowed.

### Other things the check turned up
- `docs/chatddx.md`'s dataflow names the slots `case` and `appendices`, and fills `{"case": …}`; they are `vignette`,
  `appendices`, `completion` and `expectation`. Its glossary fills the `tool_guidance` insert with the output's
  guidance, where it is the toolset's (`src/chatddx/factors/request.py:compile_request`).
- `docs/ledger-api.md` ("Known gaps") says nothing rebuilds a request to compare with `Call.request`. The bench does,
  for first requests (`Seen.rendered_again`), so what is left is a later round's and a judge's, as
  `docs/ledger.md` has it.
- `agents/wip-clearance.md` ("Before real patient data" 6) calls what is kept "a rejected request's body": it is the
  engine's error response, kept as the call's response.
- `judge.greedy_seeds` says a greedy judge's seeds "send one request"; the scoring pass sends that one request once
  per seed.
- The answer tool called beside a toolset tool ends the item while checking the run notes the other call
  (`docs/runner.md`, "Smaller issues"), already tracked.

### Options

#### R. What "request" names
- **R1. One call's body.** A request is the body rendered for one engine call: `render` makes an item's first, a
  judge's and (as `Canary.render`) a canary's, and `next_request` each tool round's. A call sends it, in as many
  attempts as it takes; the wire body is the request with the streaming options; its fingerprint is the request's.
  The earlier stages keep their own names: chunks, a recipe, the skeleton, which stays "the frozen request", a
  request less the case, the model and the seed. An item is no request but the requests of a case's replicate.
- **R2. An item's exchange.** A request is what a run asks of a case's replicate, made of calls, and what a call sends
  is its body. Fits the item key's wording and `docs/api.md`'s Item, but not the code (`Call.request`,
  `next_request`), the factors' "Rendering" or the lints ("the request is en").
- **R3. Every stage.** "Request" stays the word for the whole life, each stage qualified: the compiled request (the
  skeleton), the rendered request, the wire body, an attempt. Most generous, and the word stays loose.

Decided: R1, as the definition:
> A *request* is the body one call sends to an engine: a skeleton rendered with its fills, the served model and the
> seed, or for a tool round, the last request with the assistant's message and the tools' results. Its stages are
> the chunks, the recipe and the skeleton it is built from; its fills, from the case's vignette and appendices or
> from a judged answer; the rendered request, whose fingerprint the call keeps; the wire body, sent in one or more
> attempts; and the response, kept without the prompt's token ids.

#### K. The item key
- **K1. The wording only.** An item key identifies a run item: a case's replicate, its first request and each tool
  round's, each sent as a call that may take several attempts; with a view, it identifies a score item. The
  docs above follow, and "Execution" says items in flight.
- **K2. Rounds addressed.** A call of an item is named by (case, replicate, round), round 0 the first. The live events
  (deltas, tool runs) and the findings about a round say which; the records stay as they are, a round being its
  place in `turns`.
- **K3. Attempts recorded.** Each attempt keeps its times, status and error, so that a timeout can be checked per
  attempt (`docs/ledger.md`, "Some of what happened isn't checked"), and whether an earlier attempt's error body is
  kept is decided rather than incidental. Changes `Call`, so its record's version.

Decided: K1.

#### B. Where the clearance boundary falls
- **B1. At the engine, per run**, as built: a run and a judged scoring are admitted from what they pin, and
  everything they send goes to the admitted endpoint. Complete for engines and judges; silent on every other
  destination.
- **B2. At every destination of sensitive content**: B1, and the tools' third parties (cleared by entry point,
  version and the hosts they reach, as `agents/wip-clearance.md` plans), the database (records, the notification
  queue, a job's reasons, typed texts), the edges and exports, each cleared and refused when not. A run's start record
  could name where its content may go.
- **B3. Per request**: the gate asked at every send, a round's, an attempt's, a judge call's, so that a clearance
  withdrawn during a run stops it.

Decided: B2, with the decision kept per run as in B1.

#### C. What the hard block guards
- **C1. Sensitive content, the vignette included**: the vignette and all that is made from it (fills, rendered
  requests, completions, tool arguments and results, judge requests and responses, error bodies). The wire body is
  sensitive when it holds any; appendices and expectations stay outside it. One word for the block, as
  `docs/api.md` has it.
- **C2. As worded now**: the vignette is sensitive, sensitive is what is made from it, and the block names the
  second.

Decided: C1.

# Backlog, draft

Every open item found outside `agents/` at 2982900, moved here verbatim. Each `From` names the document, the line
at 2982900 and the section it was moved from. Ids are for grouping and triage only.

Swept: docs/ and README.md; docs/chatddx.md's "On the table" and "Work in progress" were found late, during triage. Left
where they are: `healthchecks/`, dated reports whose open findings "address healthcheck 08ae453" carried into docs/ and
agents/; docs/api.md, "Not covered", what the API leaves to others by design; the takes in the body of
docs/purist-object-layer.md, which its "Open" lists; docs/vllm.md, "Not emulated", which the fake's "Extending" works from.

Grouped by whether they'd fit in one PR, as parts of the same larger fix. Each group says the fix in a line; the
items under it are as they were moved. An item that restates another for an API follows it.

## Groups

1. [Canary sets in use](#g1-canary-sets-in-use) (6)
2. [Drift between runs](#g2-drift-between-runs) (8)
3. [Attestation within a run](#g3-attestation-within-a-run) (6)
   - G3b. [Each attempt recorded](#g3b-each-attempt-recorded) (2)
4. [The finish record: seal and findings](#g4-the-finish-record-seal-and-findings) (0, dissolved)
5. [Keyed fingerprints](#g5-keyed-fingerprints) (0, dropped)
6. [Aggregation](#g6-aggregation) (4)
   - G6b. [Export and publication](#g6b-export-and-publication) (6)
   - G6c. [Digests to settle before real data](#g6c-digests-to-settle-before-real-data) (3)
7. [Scoring: coverage and judges](#g7-scoring-coverage-and-judges) (3)
8. [Splits beyond `lines@1`](#g8-splits-beyond-lines1) (2)
   - G8b. [A view's reach knows the type it picks](#g8b-a-views-reach-knows-the-type-it-picks) (1)
9. [Unheeded reasoning](#g9-unheeded-reasoning) (3)
10. [Shipped code: scorers and tools](#g10-shipped-code-scorers-and-tools) (4)
11. [Tool rounds](#g11-tool-rounds) (3)
12. [Engines that aren't vLLM](#g12-engines-that-arent-vllm) (4)
13. [What reaches vLLM: argv and passthrough](#g13-what-reaches-vllm-argv-and-passthrough) (2)
14. [Engine identity: hardware and model files](#g14-engine-identity-hardware-and-model-files) (3)
15. [Hosts read the start-up](#g15-hosts-read-the-start-up) (0, dropped)
16. [Inventory checked everywhere](#g16-inventory-checked-everywhere) (3)
17. [Facts: the checks](#g17-facts-the-checks) (10)
18. [Facts as an engine changes them](#g18-facts-as-an-engine-changes-them) (4)
   - G18b. [Facts waiting on a model or a run](#g18b-facts-waiting-on-a-model-or-a-run) (4)
19. [Stopping: halts, deadlines and time limits](#g19-stopping-halts-deadlines-and-time-limits) (7)
20. [Claims: slots, turns and a lost endpoint](#g20-claims-slots-turns-and-a-lost-endpoint) (5)
21. [Streams that miss nothing](#g21-streams-that-miss-nothing) (3)
22. [Picking an endpoint for a model](#g22-picking-an-endpoint-for-a-model) (3)
23. [Concurrent writers](#g23-concurrent-writers) (6)
24. [The database repeats the rules](#g24-the-database-repeats-the-rules) (8)
25. [Compilations checked](#g25-compilations-checked) (4)
   - G25b. [A run names the skeleton its look gave](#g25b-a-run-names-the-skeleton-its-look-gave) (2)
26. [Vignette identity: renames, repairs and rebinding](#g26-vignette-identity-renames-repairs-and-rebinding) (7)
27. [Titles](#g27-titles) (6)
28. [Edit history: who, when and why](#g28-edit-history-who-when-and-why) (4)
29. [Following keeps a fork's renamed view](#g29-following-keeps-a-forks-renamed-view) (1)
30. [Languages](#g30-languages) (5)
   - G30b. [Translating JSON few-shot answers](#g30b-translating-json-few-shot-answers) (1)
31. [Garbage collection](#g31-garbage-collection) (2)
32. [Values the canonical form can't keep](#g32-values-the-canonical-form-cant-keep) (3)
33. [The store's read API](#g33-the-stores-read-api) (0, dissolved)
34. [Migrations checked by content](#g34-migrations-checked-by-content) (1)
   - G34b. [Old versions readable](#g34b-old-versions-readable) (2)
35. [Deployment](#g35-deployment) (0, dissolved)
36. [Reads that grow with the data](#g36-reads-that-grow-with-the-data) (5)
37. [Administering people](#g37-administering-people) (4)
38. [Signing in: limits, tokens and Keycloak](#g38-signing-in-limits-tokens-and-keycloak) (7)
39. [Z1: what each role is shown](#g39-z1-what-each-role-is-shown) (5)
40. [The repl's reach](#g40-the-repls-reach) (3)
41. [The repl's rendering](#g41-the-repls-rendering) (3)
42. [Unknown query parameters](#g42-unknown-query-parameters) (1)
43. [Curation's round trip](#g43-curations-round-trip) (6)
44. [The sample's data](#g44-the-samples-data) (2)
45. [Missing tests](#g45-missing-tests) (4)
46. [The object layer and new kinds](#g46-the-object-layer-and-new-kinds) (7)
47. [Takes waiting for a word](#g47-takes-waiting-for-a-word) (15)
48. [Text cleanup steps](#g48-text-cleanup-steps) (1)
49. [The archive's configuration under another name](#g49-the-archives-configuration-under-another-name) (1)
50. [The appendix layout as a part](#g50-the-appendix-layout-as-a-part) (1)
51. [A low-level manual for the bench](#g51-a-low-level-manual-for-the-bench) (1)

### G1. Canary sets in use
Worlds' endpoints name a canary set and runs send it: scripted runs answer canaries, canary calls stream events, judge
engines are probed, and a run's canary set is tied to the run in the database.

Triage: kept as is.

**runner.5** · From docs/runner.md:222, "Open design issues", "Smaller issues"

- **No World's endpoint names a canary set**, though data sets hold them; canary outputs aren't compared
  (docs/chatddx.md, "Possible design issues"), and canary calls stream without events.

**scripted.2** · From docs/scripted.md:111, "Open design issues", "Smaller issues"

- **No scripted run sends a canary set**: the Worlds' endpoints name none (docs/inventory.md, "Endpoints"), and a
  scripted run's turns would have to answer its canaries too.

**runner-api.3** · From docs/runner-api.md:331, "Known gaps"

- Canary calls emit no `Streamed`.

**factors.7** · From docs/factors.md:738, "Open design issues", "Smaller issues"

- **Judge engines are never probed.** Canary probes run on the run's engine only. Probing judge engines would put
  canaries in a score's start record, as in a run's; added with defaults, they keep every stored digest.

**store.9** · From docs/store.md:141, "Known gaps"

- A run's canary set isn't tied to the run in the database, so a run can name a canary set that isn't stored, and
  then can't be checked.

**store-api.8** · From docs/store-api.md:407, "Known gaps"

- `RunStarted.canaries` has no foreign key.

### G2. Drift between runs
One check that compares runs: canary outputs (once (a), (b) or (c) is decided), prompt-token fingerprints and system
fingerprints.

Triage: kept as is. Decided: chatddx.1's (c), both, with (b) under a code of its own. Decided: the runs compared are
those of the same trial digest at the same endpoint, and drift is a finding, not a refusal.

**chatddx.1** · From docs/chatddx.md:315, "Possible design issues"

**Canary drift is not implemented:** nothing compares canary outputs between phases or runs. What counts as the
  same canary output is undecided:
  (a) the digest of each choice's message, as the old `compare_canaries` compared
  output digests;
  (b) the prompt-token fingerprint alone, which catches a changed template or tokenizer but not
  changed weights; or
  (c) both, with (b) under a code of its own. None needs a new field, since `CanaryCall.call`
  holds the response and the prompt-token fingerprint.
  A human report that the agent's take is (c)

**factors.6** · From docs/factors.md:737, "Open design issues", "Smaller issues"

- **Canary drift isn't checked.** Nothing compares canary outputs between phases or between runs yet.

**ledger.4** · From docs/ledger.md:257, "Open design issues", "Smaller issues"

- **Canary drift isn't checked.** Nothing compares canary outputs between phases or between runs.

**ledger-api.4** · From docs/ledger-api.md:550, "Known gaps"

- Canary outputs aren't compared between phases or runs.

**ledger.3** · From docs/ledger.md:255, "Open design issues", "Smaller issues"

- **Prompt-token drift isn't checked.** Checking a run notes the items without a prompt-token fingerprint, but
  nothing compares the fingerprints between runs, though that is what they are kept for.

**ledger-api.3** · From docs/ledger-api.md:549, "Known gaps"

- Prompt-token fingerprints aren't compared between runs; `check_run` notes only the items without one.

**ledger.6** · From docs/ledger.md:260, "Open design issues", "Smaller issues"

- **The system fingerprint is kept but never compared** between calls or runs.

**ledger-api.6** · From docs/ledger-api.md:552, "Known gaps"

- A response's `system_fingerprint` is never compared.

### G3. Attestation within a run
Checking a run or a score holds every call to what it should have been: every round's and judge's request rebuilt, in
`runner/prepare.py` since it needs the vignette, and the prompt and model checks for judge and canary calls.

Triage: split, each attempt's record went to G3b.

**ledger.2** · From docs/ledger.md:248, "Open design issues", "Some of what happened isn't checked"

- the request a call sent and the request it should have been:
  The repl's replay rebuilds each item's first request from the trial and the vignette and holds it to the call's
  fingerprint. A later round's request, which could be rebuilt from the stored responses and tool runs, and a judge
  request, from the scorer's reading of the answer (docs/factors.md, "Judge"), aren't rebuilt, and checking a run
  rebuilds none.

**ledger-api.2** · From docs/ledger-api.md:547, "Known gaps"

- Nothing here rebuilds a request to compare with `Call.request`; the bench rebuilds an item's first
  (`chatddx.runner.prepare.rendered_again`), not a later round's or a judge's.

**repl.6** · From docs/repl.md:258, "Open design issues", "Smaller issues"

- **Only an item's first request is rendered again**; a later round's could be rebuilt from the stored responses and
  tool runs.

**ledger.5** · From docs/ledger.md:258, "Open design issues", "Smaller issues"

- **Only run items are fully attested.** Judge calls get the model check but no prompt check, and canary calls get
  neither.

**ledger-api.5** · From docs/ledger-api.md:551, "Known gaps"

- Canary calls get no model check, and neither canary calls nor judge calls a prompt-token check.

**factors.10** · From docs/factors.md:745, "Open design issues", "Smaller issues"

- **Judge calls aren't fully attested.** Their returned model is checked against the judge engine's, but their
  prompt-token fingerprint isn't, as the request would have to be rebuilt from the answer as the scorer read it.

### G3b. Each attempt recorded
A call records each attempt's times, status and error, so that a timeout can be checked; a change to `Call`, cheapest
before real runs are stored.

Triage: split from G3.

**ledger.1** · From docs/ledger.md:245, "Open design issues", "Some of what happened isn't checked"

- timeouts: a call's times span all its attempts, so an attempt that ran past the timeout can't be told from them.
  Recording each attempt's times, status and error would tell them; a call keeps only the last refusal's body, as its
  response;

**ledger-api.1** · From docs/ledger-api.md:546, "Known gaps"

- `Execution.timeout_s` isn't checked: a call's times span all its attempts.

### G4. The finish record: seal and findings
Triage: dissolved. The database refuses changes to a finish row (`0006-t2-ledger.sql`), so the seal matters once records
leave the store: ledger.7 and ledger-api.7 went to G6. ledger.9 and ledger-api.9 were dropped (see "Dropped").

### G5. Keyed fingerprints
Triage: dropped, as tracked in agents/wip-clearance.md ("Typed vignettes", and "Before real patient data", 4); see
"Dropped". From here on, an item a wip plan in agents/ tracks is dropped here.

### G6. Aggregation
What may be pooled and what aggregates scores: runs grouped by their recorded factors, with the evidence of the observed
ones checked, before anything pools them.

Triage: split, export went to G6b and greedy seeds to G6c.

**factors.1** · From docs/factors.md:712, "Open design issues", "Runs of the same trial aren't interchangeable"

A trial's digest covers its pinned factors only. Its outputs also depend on its run's recorded and observed factors:
execution settings on an engine that isn't batch invariant, a remote engine that changed between runs, a tool that
answered differently. Seeds within a run are replicates; runs of the same trial are a second source of variation, and it
has no name yet.

Nothing aggregates scores today, but anything that compares or pools runs by the trial's digest alone would mix
conditions without noticing. It needs to group by the recorded factors as well, and to check the evidence of the
observed ones (prompt-token fingerprints, returned models, canaries) before pooling.

**chatddx.2** · From docs/chatddx.md:288, inline, in "Intended dataflow"

What aggregates them isn't named yet.

**chatddx.3** · From docs/chatddx.md:120, "Requirements", "On the table"

- The result from scorers needs to be aggregated and exported. Since python is well-suited for statistical analysis,
  processing the data into publishable results may become a requirement.

**catalog.17** · From docs/catalog.md:435, "Open design issues", "Smaller issues"

- **Not all a model reads is in the request's language.** Chat templates add English of their own (default system
  prompts, harmony's channel instructions, tool-call scaffolding), and reasoning is often English whatever the
  prompt. The same text also takes another number of tokens in Swedish than in English, so budgets confound a
  comparison between languages.

### G6b. Export and publication
How records leave the store with the factors they reference, under a seal that covers the whole log, and with what an
analysis needs frozen, such as languages.

Triage: split from G6. ledger.7 and ledger-api.7 came from G4, chatddx.5 from docs/chatddx.md, found late.

**ledger.8** · From docs/ledger.md:262, "Open design issues", "Smaller issues"

- **Records aren't in bundles.** A bundle (docs/factors.md, "Registries and bundles") carries components only; how
  records travel with the factors they reference, for example for publication, isn't specified.

**ledger-api.8** · From docs/ledger-api.md:554, "Known gaps"

- Records don't travel in a `Bundle`.

**ledger.7** · From docs/ledger.md:261, "Open design issues", "Smaller issues"

- **The finish record is outside the seal.** Its time and findings could change without the seal noticing.

**ledger-api.7** · From docs/ledger-api.md:553, "Known gaps"

- The finished row is outside the seal: its `at` and `findings` can change without `ledger.seal`.

**catalog.18** · From docs/catalog.md:439, "Open design issues", "Smaller issues"

- **Languages are said, not checked.** Nothing compares a language with the text, and one can be replaced, so an
  analysis split by language should freeze them at export, as titles. A scorer that needs the language, for stemming,
  synonyms or an ontology, takes it from the expectation data or its resources, which are factors, not from the
  catalog at scoring time.

**chatddx.5** · From docs/chatddx.md:125, "Requirements", "Work in progress"

- How scores are aggregated and exported together with the factors and the ledger for publication.

### G6c. Digests to settle before real data
What names a greedy trial's replicates, and a scoring whose digest doesn't depend on the order of its expectations: both
change what is stored, so they go before trials and scorings are stored for real, in one bump.

Triage: split from G6; factors.12 and factors-api.4 came from G7.

**factors.2** · From docs/factors.md:722, "Open design issues", "Greedy sampling and seeds"

No seed is sent with greedy sampling, but a trial's seeds still count toward its digest, so two otherwise identical
greedy trials differ only in digest. Likewise, the seeds of a greedy judge all send the same request.

Keeping the seeds is deliberate. On an engine that isn't batch invariant, greedy replicates still measure
nondeterminism, and the seeds are what name the replicates. The alternative, a replicate count for greedy trials,
changes the shape of a trial, so it is cheapest decided before trials are stored for real.

**factors.12** · From docs/factors.md:750, "Open design issues", "Smaller issues"

- **A scoring's digest depends on the order of its expectations.** Its expectations aren't put in a fixed order as a
  trial's cases are, so the same expectations in another order make another scoring. The person reads build them in the
  trial's case order.

**factors-api.4** · From docs/factors-api.md:1063, "Known gaps"

- `Scoring.expectations` isn't sorted, so its order changes the digest.

### G7. Scoring: coverage and judges
A scoring says what it lacks before it is run, and calls its judges concurrently and only when needed.

Triage: kept, but for the scoring's digest, which went to G6c.

**factors.9** · From docs/factors.md:744, "Open design issues", "Smaller issues"

- **A scoring doesn't say which cases it lacks.** Only checking a score warns, once a run is scored under it.

**runner.7** · From docs/runner.md:226, "Open design issues", "Smaller issues"

- **Judge calls go one at a time**, and every judged scoring confirms its judges' endpoints, even when no item needs a
  judge; an endpoint that hangs holds it up to the confirmation's timeout.

**runner-api.5** · From docs/runner-api.md:333, "Known gaps"

- `Runner.score` refuses judge calls above concurrency 1, and confirms every judge's endpoint, even when no item
  needs a judge.

### G8. Splits beyond `lines@1`
Splits for answers written otherwise than as a list's lines, and for expectations written as free text, once either
turns up.

Triage: split, a view's reach went to G8b.

**factors.3** · From docs/factors.md:730, "Open design issues", "Smaller issues"

- **One split.** A free-text answer is broken into items only as the lines of a list (`lines@1`), so a scorer can't
  read one written otherwise, as prose or with items on one line.

**factors.18** · From docs/factors.md:786, "Potential design improvements", "Splitting expectations"

If expectations written as free text turn up, a view could split them too. Two ways:
- a separate split for the expectation side, next to the output's. It is additive: with none as its default, every
  existing digest stays the same, and each side gets the split it needs.
- one split for both sides. That changes the meaning of an existing field, so the scorer's schema version would have to
  go up, and the two sides rarely need the same split.

### G8b. A view's reach knows the type it picks
A view whose selector reaches objects where it reads text isn't offered: the sample's `diagnoses` scorer reads
`$.diagnoses[*]`, which in `management_plan_v1` are objects, and scores their JSON on every edge.

Triage: split from G8.

**repl.7** · From docs/repl.md:263, "Outstanding"

- **`diagnoses` applies to a plan**, since a plan's `$.diagnoses[*]` reaches its schema, but the items are objects, so
  its differential lists them as JSON and scores their text. A reach that knew the type of what a view picks would leave
  it out, as `View.offered_by` leaves whole-answer views out of structured runs.

### G9. Unheeded reasoning
A finding for reasoning a parser missed, and the repl's word on it.

Triage: kept as is. Only bench.23's unheeded reasoning counts here: its crossing of variations and what holds a
configuration are agents/wip-portal.md's ("Comparing variations", "What holds a configuration"), dropped by G5's rule.

**repl.4** · From docs/repl.md:254, "Open design issues", "Smaller issues"

- **No word on reasoning that wasn't heeded**, and no `[thinking in content]`: the runner can't tell reasoning a parser
  missed (docs/runner.md, "Smaller issues").

**runner.9** · From docs/runner.md:229, "Open design issues", "Smaller issues"

- **No finding for reasoning that wasn't heeded**, as the old chatddx had.

**bench.23** · From docs/bench.md:477, "Outstanding"

- **What the old bench had and this one doesn't**: what a run left unheeded (the old `outcome.py:unheeded`;
  docs/runner.md, "Smaller issues"); the old crossing of variations, which the portal is to start as several runs
  (agents/wip-portal.md, "Comparing variations"); and what holds a configuration, the portal's
  (agents/wip-portal.md), whose part for the repl `Seen.runs(reaching=…)` and `Seen.runs(scored_by=…)` cover.

### G10. Shipped code: scorers and tools
The interface between components and the code they pin: tools versioned as scorers are, resources a scorer can be given,
and how shipped code is found.

Triage: kept as is. It waits for a trigger: a second calling convention for tools, a first kind of resource, or code
from another distribution.

**runner.3** · From docs/runner.md:218, "Open design issues", "Smaller issues"

- **The tool interface isn't versioned**, unlike the scorer's: keyword arguments in, text out.

**factors.5** · From docs/factors.md:734, "Open design issues", "Smaller issues"

- **Resources can't be picked yet.** A scorer's resources are plain strings, no kind of component holds one, and the
  scoring code isn't given them. None are offered until a kind of resource exists, with its pins and code that reads
  it.

**factors-api.3** · From docs/factors-api.md:1062, "Known gaps"

- `Scorer.resources` are meant to be digests but are typed as plain strings.

**factors.19** · From docs/factors.md:793, "Potential design improvements", "Finding code through packaging entry points"

Today chatddx keeps the list of the code it ships in its code: `src/chatddx/scorers/shipped.py` and
`src/chatddx/tools/shipped.py`, by the entry point a component names. Packaging metadata changes only when the package
is installed again, and tests add tools of their own to the list for as long as they run
(src/chatddx/runner/test/tools.py:shipped). Packaging entry points would fit code from other distributions, which
nothing runs today.

### G11. Tool rounds
Tool rounds that can be shown and are consistent: a malformed call, the answer tool beside another, and a source a
scripted run can send tools on.

Triage: kept as is.

**factors-api.1** · From docs/factors-api.md:1057, "Known gaps"

- `tool_calls` skips a malformed call, but `next_request` copies the response's `tool_calls` as they are, so the
  next request holds a call that no `tool` message answers.

**runner.4** · From docs/runner.md:219, "Open design issues", "Smaller issues"

- **The answer tool called beside a toolset tool** ends the item, and checking the run notes the other call; no engine
  under test does that. Checking the run doesn't refuse a turn that runs the other call, though the runner never
  writes one.

**scripted.1** · From docs/scripted.md:105, "Open design issues", "No scripted run has tool rounds"

The gate refuses tools on a sensitive source (docs/runner.md, "The gate"), and both Worlds' sources are sensitive, as
a real one is, so no scripted run can send a tool round on their cases. The old chatddx's sample runs `broken` and
`rich` searched the web. A take: a made-up source that isn't sensitive, once calibration wants a tool round to show,
with the web patched in the process that runs the tools (`urllib.request.urlopen`, src/chatddx/tools/web_search.py).

### G12. Engines that aren't vLLM
Stop assuming vLLM: ask for token ids only where an engine takes them, and lint what OpenAI's API refuses.

Triage: kept as is. It waits for the first real remote endpoint that isn't vLLM; every remote engine in the Worlds is
the fake. Take, for factors.11: the engine says whether it takes token ids, so the choice is a factor a trial shows.

**factors.11** · From docs/factors.md:747, "Open design issues", "Smaller issues"

- **Every engine is asked for the prompt's token ids.** A remote engine that isn't vLLM may refuse the unknown option.
  Either the engine says whether it takes it, which changes the engine's digest, or the runner decides per call, which
  leaves the run without prompt-token fingerprints.

**factors-api.5** · From docs/factors-api.md:1064, "Known gaps"

- `render` sends `return_token_ids` to every engine by default; a remote engine that isn't vLLM may refuse it.

**runner.8** · From docs/runner.md:228, "Open design issues", "Smaller issues"

- **Every engine is asked for the prompt's token ids** (docs/factors.md, "Smaller issues").

**factors.15** · From docs/factors.md:757, "Open design issues", "Smaller issues"

- **Tool parameters whose root isn't an object.** OpenAI's API is reported to refuse function parameters whose root
  isn't `type: object`. Unverified; a candidate lint for tools on a remote engine.

### G13. What reaches vLLM: argv and passthrough
What an engine's command line and a passthrough may hold, checked against what vLLM takes.

Triage: kept as is, built on pinned lists of vLLM 0.24's `serve` flags, each with whether it takes a value, and its
request keys (docs/vllm.md, item 12). The flag list also lets the fake drop the first entry of docs/vllm.md, "Not
emulated". Decided, for factors.20: the refusals stay, and a key vLLM 0.24 doesn't take gets a warning lint, on local
engines only.

**factors-api.6** · From docs/factors-api.md:1065, "Known gaps"

- `argv` is checked without vLLM's list of flags: a bare argument after a flag that takes no value passes, and lints
  don't expand abbreviated flags.

**factors.20** · From docs/factors.md:800, "Potential design improvements", "Passthrough: an allow list, or lints"

A passthrough refuses a fixed list of options and lets everything else through. Two other ways:
- an allow list: a passthrough may set only known engine extras. Nothing unknown gets through, but every new option
  needs a code change, and remote engines accept other options than vLLM, so the list would depend on the engine.
- lints instead of refusals: risky options would give a finding, in the spirit of "warnings, not crashes". But a
  passthrough already refuses what the rig and the output contract set, and options that put case text in the stored
  response are closer to the clearance block than to a warning.

### G14. Engine identity: hardware and model files
An engine described well enough to tell apart, and its files checked against the hub.

Triage: kept as is. The hardware waits for the first server on several GPUs, which the import refuses until then
(`importers/o11n.py`); the hub check likely starts in o11n's report (Kompismoln/o11n, `nixos/vllm-report.py`).

**factors.14** · From docs/factors.md:755, "Open design issues", "Smaller issues"

- **Hardware has no GPU count,** so engines that split a model across GPUs can't be told apart by their hardware. Nor
  does it say the CPU, the RAM, the GPU's uuid, the machine's id or where it is.

**factors-api.7** · From docs/factors-api.md:1067, "Known gaps"

- `Hardware` has no GPU count.

**inventory.5** · From docs/inventory.md:295, "Open design issues", "Smaller issues"

- **Model files aren't checked against the hub.** huggingface_hub keeps the commit's file listing from the download
  (`<repo>/trees/<commit>.json`): the hub's SHA-256 of each LFS file and the git blob hash of the rest. The report
  could compare every file it hashes with it, offline. The import takes the host's hashes as they are.

### G15. Hosts read the start-up
Triage: dropped, as tracked in agents/wip-deploy.md ("The NixOS module", Open: whether the module serves an
inference host's vLLM from an endpoint's start-up); see "Dropped".

### G16. Inventory checked everywhere
The runner, when it starts, and the engine import, before it writes, run the inventory check and pass on its findings,
as init-data does.

Triage: kept, but for endpoint names, dropped as tracked in agents/wip-clearance.md (Open 1, "What a grant keys on").

**inventory.1** · From docs/inventory.md:271, "Open design issues", "Checks happen when an entry is used"

Loading checks only what the files show. Everything that needs the engines is checked when an endpoint is started or
confirmed, one entry at a time:
- whether an endpoint's digest names an engine;
- whether a local engine's endpoint has a host;
- whether the host says where the model and template are.

One pass checks the whole inventory against the engines and returns findings rather than raising. It finds what
starting each endpoint would refuse, and what nothing refuses but is likely a slip: two local engines'
endpoints at one address, a remote engine's endpoint that names a host, host locations that no endpoint's engine pins,
and a clearance for a source that isn't sensitive, which clears nothing. init-data prints its findings; the runner and
the engine import don't run it yet, and still check one entry at a time.

**inventory-api.1** · From docs/inventory-api.md:266, "Known gaps"

- The runner and the engine import don't run `check`: they check an entry when they use it.

**curation.9** · From docs/curation.md:289, "Open design issues", "Smaller issues"

- **The runner and the engine import don't run the inventory check** that loading does.

### G17. Facts: the checks
Checking pairs and loading facts warn where they now stay silent or warn wrongly.

Triage: kept as is.

**facts.5** · From docs/facts.md:157, "Open design issues", "Smaller issues"

- **A budget with reasoning off is compiled.** Qwen3's off with a budget turns thinking off and sets a thinking
  budget.

**facts-api.5** · From docs/facts-api.md:294, "Known gaps"

- A budget with reasoning off is compiled.

**facts.6** · From docs/facts.md:159, "Open design issues", "Smaller issues"

- **Unread recommendations.** A recommendation for a level that collapses, or lands on its nearest, is never
  compiled, and nothing reports it. Checking pairs still counts it as the model's.

**facts-api.6** · From docs/facts-api.md:295, "Known gaps"

- A `sampling.recommended` entry for a level that collapses, or lands on its nearest, is never asked for by
  `ModelFacts.recommended`, and nothing reports it.

**facts.7** · From docs/facts.md:161, "Open design issues", "Smaller issues"

- **An unknown budget passes the check.** A budget sent to a model whose budget is unknown isn't warned about, while
  compiling one beside a level is refused.

**facts-api.7** · From docs/facts-api.md:297, "Known gaps"

- An unknown budget passes `facts.budget_refused`, while compiling one beside a level refuses it (`check_budget`).

**facts.8** · From docs/facts.md:163, "Open design issues", "Smaller issues"

- **Unknown reasoning fails the check.** A skeleton's reasoning settings are compared only with the ways of asking the
  facts know, so a model whose reasoning is unknown, or a skeleton using a level nothing is known about, gets the
  warning, though a missing part otherwise means "unknown".

**facts-api.8** · From docs/facts-api.md:298, "Known gaps"

- Unknown reasoning fails `facts.reasoning_unmatched`: a model without writes at any level, or a skeleton using a
  level nothing is known about, gets the warning.

**facts.9** · From docs/facts.md:166, "Open design issues", "Smaller issues"

- **A refused default is accepted.** A default that lands on a refusal loads, and whether the model reasons by default
  is then unknown.

**facts-api.9** · From docs/facts-api.md:300, "Known gaps"

- A `default` that lands on a refusal loads, and `reasons_by_default` then says `None`.

### G18. Facts as an engine changes them
Facts about a model on a runtime, and the defaults an engine's command line sets over the model's own. facts.4 can be
done now; facts.3 waits for a second runtime.

Triage: split, the facts waiting on a model or a run went to G18b.

**facts.3** · From docs/facts.md:149, "Open design issues"

- **A model or a model on a runtime.** Some facts are really about a model on a runtime, such as harmony ignoring the
  response format. They live on the model for now; facts keyed by runtime can be added when a second runtime
  appears.

**facts-api.3** · From docs/facts-api.md:291, "Known gaps"

- Some facts are about a model on a runtime, and live on the model.

**facts.4** · From docs/facts.md:152, "Open design issues"

- **Defaults from the command line.** An engine's own default chat template arguments and generation config change
  the model's defaults. Facts describe the model's own defaults, and only the grammar-before-reasoning lint accounts
  for the change.

**facts-api.4** · From docs/facts-api.md:292, "Known gaps"

- An engine's `--default-chat-template-kwargs` and `--generation-config` change the model's defaults; only
  `vllm.grammar_before_reasoning` accounts for the first.

### G18b. Facts waiting on a model or a run
Small edits to the facts, each waiting on something outside the code: `xhigh` on a model that supports it, and
harmony's tool choices on a run at `gpt-oss-20b@malborg`.

Triage: split from G18.

**facts.1** · From docs/facts.md:145, "Open design issues"

- **xhigh can't be written.** It's a level, but no reasoning effort says it, so a model can only collapse or refuse
  it. Adding the effort is additive, if a model that supports it shows up.

**facts-api.1** · From docs/facts-api.md:289, "Known gaps"

- `xhigh` can't be written: neither `Writes.effort` nor `Reasoning.effort` has the value.

**facts.2** · From docs/facts.md:147, "Open design issues"

- **Tool choice on harmony.** Named and required tool choices are unverified for gpt-oss. vLLM 0.24's gpt-oss tool
  parser accepts both, so the JSON-array grammar applies; whether harmony's output survives it isn't known.

**facts-api.2** · From docs/facts-api.md:290, "Known gaps"

- Named and `required` tool choices are unverified for gpt-oss.

### G19. Stopping: halts, deadlines and time limits
Everything under way can be ended in time: a call waiting for headers, a running tool, a stopping worker's sending, and
a halted run that could resume.

Triage: kept as is. Decided: at the deadline, and on a second press, the worker halts the calls under way and leaves
the run unfinished; the items under way are recorded stopped, an outcome like any other, and the next claim resumes the
rest.

**runner.1** · From docs/runner.md:212, "Open design issues", "What a stop leaves out"

- **A call still waiting for its engine to answer at all**, under an execution with no timeout, waits on after a halt;
  only a stream can be shut down. vLLM answers at once and streams after. The bench sends no execution, so its runs
  have no timeout.

**runner-api.1** · From docs/runner-api.md:329, "Known gaps"

- A halt can't end a call waiting for its response's headers.

**worker.10** · From docs/worker.md:139, "Open design issues", "Smaller issues"

- **A call still waiting for its engine to answer at all** waits on after a halt (docs/runner.md, "What a stop leaves
  out"), and the job's thread with it.

**runner.2** · From docs/runner.md:217, "Open design issues", "Smaller issues"

- **Tools have no time limit of their own**, and a halt waits for a tool that's running.

**runner-api.2** · From docs/runner-api.md:330, "Known gaps"

- `Toolbox.run` has no time limit.

**worker.8** · From docs/worker.md:134, "Open design issues", "Smaller issues"

- **A stopping worker's sending has no deadline**: its runs stop after the items under way, however long they take,
  and a service's stop timeout kills it before then, leaving the job to be claimed again once it is lost and the items
  to be sent again. Halting them at the deadline would record them stopped, and they wouldn't be sent again.

**worker.9** · From docs/worker.md:137, "Open design issues", "Smaller issues"

- **A halted run is finished**, so a run stopped with the second press can't be resumed; leaving it unfinished would
  record its calls under way as stopped, and its items wouldn't be sent again.

### G20. Claims: slots, turns and a lost endpoint
The repl's runs and the worker's judge calls hold slots at their endpoints, claims take turns per owner at each
endpoint once people wait on each other, "ahead" says what the turns make it, and a job at an endpoint the inventory
lost waits rather than fails. The slots and turns wait for endpoints that are shared and busy.

Triage: kept, but for inventory.4, inventory-api.4 and runner.10, dropped as stale; worker.12 and worker.13 came from
G21.

**worker.1** · From docs/worker.md:109, "Open design issues", "The repl beside the worker"

The repl sends in its own process, and its runs don't count against an endpoint's `max_jobs`. It could queue its runs
and follow their events, or send in its own process but hold slots in the queue, as a worker claiming its own job.
Take: as it is, and holding slots once endpoints are shared and busy.

**worker.4** · From docs/worker.md:124, "Open design issues", "Smaller issues"

- **`max_jobs` beside the worker.** The repl's runs and judge calls don't count. vLLM queues what's over
  `--max-num-seqs` rather than refusing it, so the cost is batching that the runs' executions don't show.

**worker.2** · From docs/worker.md:114, "Open design issues", "Fairness between owners"

Decided: queue order, as built, then turns per owner at each endpoint once people wait on each other. Turns aren't
built.

**worker.12** · From docs/worker.md:144, "Open design issues", "Smaller issues"

- **"Ahead" counts jobs, not items**, and the workers seen are counted for anyone's jobs, not the person's endpoints.

**worker.13** · From docs/worker.md:145, "Open design issues", "Smaller issues"

- **A job at an endpoint the inventory lost** is claimed and fails at the gate, rather than waiting.

### G21. Streams that miss nothing
A stream that can't miss a row or an event, and a notification queue that a slow listener can't hold up.

Triage: kept, but for the queue's items, which went to G20.

**worker.5** · From docs/worker.md:126, "Open design issues", "Smaller issues"

- **The rows' order is their writer's.** A stream reads the rows after the last it told; a row committed after one
  with a higher number would be missed until the stream starts again. One writer per run keeps the two orders alike:
  the queue holds one job open per run, and a log's rows are written one transaction after another. A repl scoring a
  run while the worker writes it doesn't.

**worker.6** · From docs/worker.md:130, "Open design issues", "Smaller issues"

- **What isn't a row is told only to those listening**, so a stream that joins after a scoring started misses
  `run.scoring`. Notes along the way are told with the finish row that holds them, not as they happen.

**worker.11** · From docs/worker.md:141, "Open design issues", "Smaller issues"

- **`NOTIFY`'s queue**: a payload waits in the database's notification queue, kept on disk, until every listener has
  read it, and a listener that stops reading holds the queue up for all. Deltas are sensitive, and pass through the
  database that holds the ledger's completions already.

### G22. Picking an endpoint for a model
A look for a model several endpoints serve is linted, a model that moved on is followed only where served, and a judge
whose engine two endpoints serve doesn't bar its scorer.

Triage: kept as is. bench.15's refusal is decided (agents/wip-engine-part.md, "What building it found": "the decided
refusal stands"); what is open of it is its judge. Decided, for bench.25: a look for no endpoint gives the findings of
the model alone, `facts.*`, and says the engine's wait for an endpoint to be named.

**bench.15** · From docs/bench.md:457, "Outstanding"

- **A model served at several endpoints** isn't picked from them: a run is refused until the endpoint is named, as
  the test World's two Qwen3 endpoints show; the variation page offers the picker, and a look rendered for none of
  them has no findings. A judge pins its engine as a trial does, and a judge whose engine two endpoints serve bars
  its scorer (docs/runner.md, "Judges"), which stays unlikely: it is one engine served twice.

**bench.25** · From docs/bench.md:484, "Outstanding"

- **A look for a model several endpoints serve has no findings** until an endpoint is named, where the engine as the
  part linted it for the recipe's engine; the repl's `show` shows no lints either.

**bench.26** · From docs/bench.md:486, "Outstanding"

- **A model that moved on is followed to its head whether or not an endpoint serves it**; `at` says so afterwards.

### G23. Concurrent writers
The rules hold with two writers at once: adopting a vignette, taking an expectation and saving a name.

Triage: kept as is. Decided: the advisory locks edits take extend to adopting, on the vignette's source and content;
to taking an expectation, on the owner, the case and the schema; and to creating a named thread, on the owner, the
kind and the name. catalog.22 and bench.6 are then confirmed as the mechanism.

**catalog.1** · From docs/catalog.md:399, "Open design issues", "Concurrent writers"

The rules are checked against what is stored when a row is written. That holds with one writer at a time; with two,
only what the database enforces is sure to hold. It repeats every such rule but two: that no two families are bound to
the same vignette, by id or by content, at once, and that a person owns at most one live expectation thread per case
and expectation schema. So two people adopting the same vignette at the same moment can create two families, and two
writes at the same moment can leave a person several expectations to choose from, which scoring then refuses.

**catalog-api.1** · From docs/catalog-api.md:735, "Known gaps"

- The rules are checked in Python on rows read inside the writing transaction; with two writers at once only tier 2
  holds. Two `adopt` calls for one vignette at the same moment can create two families.

**catalog.22** · From docs/catalog.md:454, "Open design issues", "Smaller issues"

- **An edit that names its head holds with several writers without the database repeating the rule**:
  each edit of a thread waits for the one before it to land. The head an edit names is held without the database
  repeating it: every edit takes its thread's advisory lock (src/chatddx/store/catalog.py:Catalog._lock).
  The writer may not update the catalog's tables, so `FOR UPDATE` isn't open to it.

**bench.6** · From docs/bench.md:440, "Outstanding", its takes, built and waiting for a word

- the head an edit names is checked under its thread's advisory lock (docs/catalog.md, "Concurrent writers");

**bench.20** · From docs/bench.md:470, "Outstanding"

- **Two saves of one name at once** can both create a configuration, in the repl's `save` (`docs/catalog.md`,
  "Concurrent writers").

**bench.21** · From docs/bench.md:472, "Outstanding"

- **Taking counts shared threads, not owners**: a case with two threads shared by one owner is to choose from, and
  naming that owner doesn't pick between them. Only two writers at once can leave an owner two (see "One expectation
  per case and schema").

### G24. The database repeats the rules
Deferred constraints and foreign keys for what the code writes together: a component's reference rows, a thread's first
version, a family's first binding, a log's start record.

Triage: kept as is. Decided, for store.2 and store-api.1: left as they are until something other than `Store.add` writes
components, since the triggers would repeat each kind's reference paths in SQL.

**catalog.5** · From docs/catalog.md:414, "Open design issues", "Smaller issues"

- **A thread without versions** is possible in the database, and so is a family without bindings; the catalog writes
  each together with its first. A deferred constraint could rule them out at tier 2.

**catalog-api.5** · From docs/catalog-api.md:741, "Known gaps"

- A thread without edits is possible in SQL.

**store.3** · From docs/store.md:129, "Known gaps"

- The database allows a thread without versions; the catalog writes a thread together with its first version.

**store-api.2** · From docs/store-api.md:400, "Known gaps"

- The database allows a thread without edits; `Catalog.create` writes both in one transaction.

**store.2** · From docs/store.md:127, "Known gaps"

- The database doesn't check that a component has all its reference rows, only that the rows it has are right; the
  store writes them together.

**store-api.1** · From docs/store-api.md:399, "Known gaps"

- The database doesn't check that a component has all its reference rows; `Store.add` writes them together.

**store.8** · From docs/store.md:138, "Known gaps"

- A log can be written that can't be read back. Storing a record checks only what the database can, and a finish
  record isn't tied to its start record, so a finish record alone is accepted; reading the log back then reports that
  it has no start record. Logs are validated only when they are read.

**store-api.7** · From docs/store-api.md:405, "Known gaps"

- A log can be written that can't be read back: a finished row is accepted without its started row, and `Store.run`
  and `Store.score` then raise `StructuralError("<log> <id> has no started row")`.

### G25. Compilations checked
A skeleton's provenance asked for, a compilation checked against its recipe, and an edit that keeps a skeleton's
compilation when one exists.

Triage: split: a run naming its look's skeleton went to G25b, a compiled skeleton's language to G30.

**factors-api.8** · From docs/factors-api.md:1068, "Known gaps"

- Nothing checks that a compilation's recipe compiles to its skeleton.

**factors.8** · From docs/factors.md:740, "Open design issues", "Smaller issues"

- **Skeleton provenance.** Should a skeleton be accepted only with a compilation? Hand-written ones, such as judge
  prompts, are possible today. Decided: keep hand-written skeletons, configurations without a recipe that nothing
  varies, which only the store writes. Provenance is whether a compilation names the skeleton, a question a lint can
  ask once the catalog or ledger is queried for it.

**catalog.6** · From docs/catalog.md:416, "Open design issues", "Smaller issues"

- **A skeleton edit may leave out its compilation** even when one exists, and nothing can require it.

**catalog-api.6** · From docs/catalog-api.md:742, "Known gaps"

- A skeleton edit may leave out its compilation.

### G25b. A run names the skeleton its look gave
A run that sends what was looked at, or is refused.

Triage: split from G25. Decided: a run may name the skeleton's digest, as an edit names its head, and is refused when
the variation compiles to another by then. api.2 is also one of the API's takes waiting for a word (G47).

**catalog.21** · From docs/catalog.md:450, "Open design issues", "Smaller issues"

- **What a fork varies is compared by recipe.** A variation with a part replaced is compiled whole by the running code
  and against the facts as they are stored then (docs/bench.md, "The variation being tried"), so after a change to the
  compiler, or a corrected fact, it can send otherwise than the edit it was built on where nothing was replaced, and
  what its fork varies doesn't say so.

**api.2** · From docs/api.md:405, "Outstanding", "Takes the API is built on"

- **The variation**: stated whole in each request, the configuration by id and its parts by digest, with nothing
  stored by looking. A run may come to name the skeleton its look gave, and be refused when the variation compiles to
  another by then, as an edit names its head.

### G26. Vignette identity: renames, repairs and rebinding
What follows a vignette that exists twice in a source, matches several families, was bound before the current binding,
or was renamed in a data set.

Triage: kept, but for catalog.4 and catalog-api.4, dropped as holding, factors.21, dropped as answered, and bench.2,
which went to G47.

**catalog.2** · From docs/catalog.md:406, "Open design issues", "Smaller issues"

- **Identical vignettes.** Two vignettes with the same content under different ids in one source look like a rename:
  adopting refuses the second, which a survey lists as new. Once the adopted id is gone, a survey reports both ids as
  renames of the same family.

**catalog-api.2** · From docs/catalog-api.md:737, "Known gaps"

- Two vignettes with the same content under different ids in one source look like a rename: `adopt` refuses the
  second.

**catalog.3** · From docs/catalog.md:409, "Open design issues", "Smaller issues"

- **Several matching families.** When bindings of several families match a case, the latest matching binding decides,
  which needn't be the latest family's.

**catalog-api.3** · From docs/catalog-api.md:739, "Known gaps"

- When bindings of several families match a case, `family_of` takes the family of the latest matching binding.

**catalog.16** · From docs/catalog.md:433, "Open design issues", "Smaller issues"

- **A repair moves the current binding only.** Cases and appendices bound to an earlier binding of the family aren't
  rebuilt at the new place (docs/catalog-api.md, "families.py").

**catalog-api.8** · From docs/catalog-api.md:744, "Known gaps"

- A case stored at a vignette's old place after a repair gets a replacement from `behind` that nothing has stored.

**curation.8** · From docs/curation.md:287, "Open design issues", "Smaller issues"

- **A rename isn't followed into the data.** After repair-data, loading says the old id is missing until the data set
  names the new one.

### G27. Titles
Titles that take fewer queries, pair no versions, are short for a variation, and say a translated skeleton's language.

Triage: kept as is. Of catalog.13, the query count is the work; that titles change and aren't unique is by design, and
freezing them is G6b's. Decided, for catalog.20: a skeleton compiled from a variation of a configuration is titled by
the variation's label, as its run is.

**catalog.9** · From docs/catalog.md:422, "Open design issues", "Smaller issues"

- **A translated skeleton's title doesn't say its language.** It has no thread, so it is titled by its compilation's
  recipe, as the configuration's own skeleton is.

**catalog.13** · From docs/catalog.md:428, "Open design issues", "Smaller issues"

- **Titles take a query for every reference they visit,** are rebuilt from names that change, and aren't unique.

**catalog-api.11** · From docs/catalog-api.md:748, "Known gaps"

- Titles take a query for every reference they visit, are rebuilt from names that change, and aren't unique.

**catalog.14** · From docs/catalog.md:429, "Open design issues", "Smaller issues"

- **An unnamed fork's title can pair two versions.** When the origin has no name and has moved on, the title describes
  the origin's current head, while what the fork varies is measured from the base.

**catalog-api.13** · From docs/catalog-api.md:750, "Known gaps"

- An unnamed fork's title can pair two versions: when its origin has no name and has moved on, `title` describes the
  origin's current head but lists the changes from the base.

**catalog.20** · From docs/catalog.md:446, "Open design issues", "Smaller issues"

- **A variation nobody saved has a long title.** It is described by its whole recipe:
  "case · diagnoses-tool · recommended · off · qwen3-8b@pelle", where the repl called it
  "diagnoses-tool+reasoning=off": the configuration it came from and the parts set over it. A run of one is
  named so and says what it varied (see "What a run ran"), but its skeleton is still titled by its recipe.

### G28. Edit history: who, when and why
Show who changed an entry, a label or a language and when, and keep why an edit was made.

Triage: kept as is. Decided, for catalog.12: an edit may carry an optional note, stored with the edit as a commit
message is; what changed stays derived from the references.

**catalog.11** · From docs/catalog.md:425, "Open design issues", "Smaller issues"

- **Who changed an entry or a language isn't shown.** Every row records who wrote it and when, but for these only
  what holds now is shown.

**catalog-api.9** · From docs/catalog-api.md:745, "Known gaps"

- When an entry, a label or a language was written isn't given, nor who wrote a label or a language:
  `Reader.entries` gives an entry's writer only.

**catalog.12** · From docs/catalog.md:427, "Open design issues", "Smaller issues"

- **Why an edit was made isn't stored.** It can be worked out by comparing consecutive versions' references.

**catalog-api.10** · From docs/catalog-api.md:747, "Known gaps"

- Why an edit was made isn't stored.

### G29. Following keeps a fork's renamed view
Following an origin keeps the label of a view the fork renamed, though its scorer is the origin's.

Triage: kept, but for catalog-api.12, dropped as decided, and bench.8, which went to G47.

**catalog.15** · From docs/catalog.md:431, "Open design issues", "Smaller issues"

- **Following can drop a fork's renamed view.** Labels follow the views the proposal keeps, so a fork that only
  renamed a view, and follows an origin whose views it keeps, takes the origin's labels.

### G30. Languages
Where a compiled skeleton's language comes from, said and kept, judges checked for one, and what a person may correct.

Triage: kept, but for bench.3 and bench.10, which went to G47, and factors.4, which went to G30b; catalog.7,
catalog-api.7 and catalog.8 came from G25. Decided, for bench.12: a person may correct the language of a text only
their own threads hold; anything else stays curation's.

**catalog.7** · From docs/catalog.md:417, "Open design issues", "Smaller issues"

- **A language on a skeleton that is compiled later** is ignored from then on, since the skeleton's language comes from
  its compilations.

**catalog-api.7** · From docs/catalog-api.md:743, "Known gaps"

- A language on a skeleton that is compiled later is ignored from then on.

**catalog.8** · From docs/catalog.md:419, "Open design issues", "Smaller issues"

- **A language refused on a compiled skeleton is said to come from its recipe**, by
  `src/chatddx/catalog/language.py:check_language`, `0012`'s `language_compiled` trigger and the bench's
  `COMPILED_LANGUAGE`; a translated skeleton's comes from the language its compilation names.

**catalog.19** · From docs/catalog.md:443, "Open design issues", "Smaller issues"

- **Judges aren't checked for language.** A judge's language could be compared with the cases its scoring grades, the
  way lints check a trial's. An English judge grading Swedish answers may be intended, so it would be a notice rather
  than a warning.

**bench.12** · From docs/bench.md:451, "Outstanding"

- **Correcting a wrong language** stays curation's: the bench refuses a language that differs from the text's own.
  What a person may correct, such as a text only their own threads hold, is open.

### G30b. Translating JSON few-shot answers
A few-shot answer in JSON translated by its texts, rather than whole and by hand.

Triage: split from G30.

**factors.4** · From docs/factors.md:732, "Open design issues", "Smaller issues"

- **Few-shot answers in JSON are translated whole.** An example is one text, so an assistant example that is a JSON
  answer is translated as one entry, by hand, keeping its property names and allowed values as they are.

### G31. Garbage collection
A collection, run as the admin, of what nothing refers to, the ledger and every person's threads, deleted ones too,
counted as references.

Triage: kept, but for catalog.10, dropped as tracked in agents/wip-portal.md ("What the docs ask of it"), and
curation.7, which went to G43. Decided: it waits until storage cost or an erasure calls for it; until then the store
keeps everything, as its tiers mean it to. Erasing a typed text is agents/wip-clearance.md's ("Before real patient
data", 4).

**curation.1** · From docs/curation.md:267, "Open design issues", "Garbage collection"

Nothing is ever removed from the store, and a leftover is only listed. A collection run as the admin could delete what
nothing refers to: components no thread, family, run or other component reaches, and the catalog rows of what it
deletes. The tiers forbid it on purpose (docs/store.md, "Tiers"), and what counts as unreferenced must include the
ledger and every person's threads, deleted ones too, since history answers questions about the past (docs/catalog.md,
"Deleting").

**chatddx.4** · From docs/chatddx.md:122, "Requirements", "On the table"

- Garbage collector for true deletions of non-referenced items.

### G32. Values the canonical form can't keep
NUL and NaN refused where a component, a record or a typed text is built, rather than failing or changing when stored.

Triage: kept as is. Decided: floats refuse NaN and infinity throughout, and strings refuse NUL, typed text included;
nothing stored can hold either, so no stored digest changes.

**store.4** · From docs/store.md:130, "Known gaps"

- The database can't keep text holding a NUL character, so a component or record containing one can't be stored.

**store-api.3** · From docs/store-api.md:401, "Known gaps"

- `jsonb` rejects `\u0000`, so a component or record holding NUL can't be stored.

**factors-api.2** · From docs/factors-api.md:1059, "Known gaps"

- NaN and infinity pass validation, and the canonical form writes them as `null`. The stored component reads back
  with the field unset, under the same digest, and `Bundle.load` reports `bundle.recanonicalized`. The request still
  carries the NaN.

### G33. The store's read API
Triage: dissolved; all three were dropped (see "Dropped").

### G34. Migrations checked by content
An applied migration's file is known by its content too, before a shared database.

Triage: split, old versions went to G34b. Decided: each applied file's sha256 is kept beside its name, and migrating
refuses, naming the file, when an applied file differs; a database migrated before that records its checksums on the
first run after.

**store.1** · From docs/store.md:124, "Known gaps"

- Applied migrations are known by name only, so a migration file edited after a database applied it isn't noticed,
  and that database silently differs from the files. Before a shared database, applied files are frozen, or their
  checksums kept with their names.

### G34b. Old versions readable
Stored rows of an older schema version read after a bump. Due before the first bump once real data is stored, so after
G6c.

Triage: split from G34. Decided: upgrade on read; a kind keeps a reader for each of its older versions, returning the
current shape, and the stored bytes and their digest stay as they are.

**store.10** · From docs/store.md:143, "Known gaps"

- A schema-version bump strands stored rows. Reading parses every row, and parsing refuses another version
  (docs/factors.md, "Versions"; docs/ledger.md, "Canonical form and versions"), so after a bump the store can't return
  rows of the old version, nor load a closure that holds one. The rows can't be rewritten either: the tables are
  append-only, and digests and seals depend on the bytes. docs/factors.md, "Splitting expectations", already considers
  a bump of the scorer's schema version.

**store-api.9** · From docs/store-api.md:408, "Known gaps"

- A schema-version bump strands stored rows: `get`, `load`, `run` and `score` refuse another version, and the rows
  can't be rewritten.

### G35. Deployment
Triage: dissolved; all three were dropped as tracked in agents/ (see "Dropped").

### G36. Reads that grow with the data
Paging in the store, and reads that don't repeat per item, once they are slow.

**api.9** · From docs/api.md:421, "Outstanding", "Serving"

- **A person's runs are all read**, filtered and then paged, and with `unscored`, what is left of each is worked out
  first. Take: as is until slow, then paging by a cursor, the last run's start.

**bench.18** · From docs/bench.md:465, "Outstanding"

- **A person's runs are all read**, and paged afterwards, in the API too (`Bench.runs`), and what is left to score is
  worked out for each of them, about 40 ms a run under five scorers. Page in the store once that is slow.

**bench.16** · From docs/bench.md:461, "Outstanding"

- **A case's language** is its family's, read from the families the person sees, in a few queries however many
  cases (`Seen.languages`, `Seen.findings`); a case of a family they don't see is read one at a time.

**bench.17** · From docs/bench.md:463, "Outstanding"

- **The facts are read from the store each time they are asked for** (`Seen.facts`), several times a look. That is
  cheap with a facts thread per model; cache them per request if it shows.

**bench.24** · From docs/bench.md:481, "Outstanding"

- **A start holds a transaction open while the gate confirms its endpoint**, once per language though every run of a
  start goes to one endpoint; a few seconds at most against an endpoint that answers. Confirming once, before the
  transaction, would remove most of it.

### G37. Administering people
Commands that change a person, an admin role that means something, and a new password that ends sessions.

**identity.1** · From docs/identity.md:96, "Open design issues"

- **A new password doesn't end sessions.** `chatddx person password` replaces the hash, and a session opened with the
  old password stays until it expires; only making the person inactive ends their sessions.

**identity.3** · From docs/identity.md:100, "Open design issues"

- **Nobody administers people through chatddx.** The admin role exists, but nothing asks for it, and the commands
  connect as `DB_USER`, so whoever reaches the database adds people.

**identity.4** · From docs/identity.md:102, "Open design issues"

- **No command changes a person**: their name, roles, or whether they are active (`People.update`).

**identity.7** · From docs/identity.md:120, "Takes on what is open", "Who may administer people"

`Role.ADMIN` exists, but nothing asks for it, and `chatddx person` connects as `DB_USER`, so anyone with database
access adds people. No command changes a person's name, roles or whether they are active (`People.update`).

### G38. Signing in: limits, tokens and Keycloak
How people and scripts sign in once the app is public: Keycloak or a proxy in front, limits, tokens, cookies and
origins.

**api.10** · From docs/api.md:425, "Outstanding", "Signing in"

- **A cookie over plain HTTP** isn't kept: a `Secure`, `__Host-` cookie needs HTTPS, or `localhost`, and a bearer works
  everywhere. Take: as is.

**api.11** · From docs/api.md:427, "Outstanding", "Signing in"

- **`Origin` against `Host`.** A proxy that rewrites `Host` would fail the `Origin` check for a browser that sends no
  `Sec-Fetch-Site`, though today's browsers all send it. Take: as is; the public origin as a setting if it bites.

**api.12** · From docs/api.md:429, "Outstanding", "Signing in"

- **No limit on sign-ins, and no personal tokens.** Each sign-in costs an argon2 verification, a fraction of a second
  of CPU, and a script running longer than a session signs in again. Personal tokens were decided for when a script
  needs one. Take: neither, until Keycloak is in front, which limits sign-ins itself, or a script needs a token.

**api.13** · From docs/api.md:432, "Outstanding", "Signing in"

- **Keycloak.** How it hands the app a login isn't decided. Take: a proxy in front, such as oauth2-proxy, passes the
  login in a header the app believes from it alone, mapped onto `person.login` (docs/identity.md, "Take, for when
  Keycloak arrives"), and Keycloak's own tokens as bearers for scripts when they come.

**identity.2** · From docs/identity.md:98, "Open design issues"

- **Sign-ins aren't limited.** Each costs an argon2 verification. The API's take is none until Keycloak is in front,
  which limits them itself (docs/api.md, "Outstanding").

**identity.8** · From docs/identity.md:124, "Takes on what is open", "Expired sessions and sign-ins"

Expired sessions are removed whenever a session is opened (`People.open_session`). Sign-ins aren't limited;
`docs/api.md`, "Outstanding", takes none until Keycloak is in front.

**identity.9** · From docs/identity.md:128, "Takes on what is open", "Take, for when Keycloak arrives"

Keycloak, or a proxy in front such as oauth2-proxy, authenticates, and the app maps its username onto `person.login`,
which is why logins are lowercase like Keycloak's. Password login can stay as the development path. Roles could then
come from Keycloak's realm roles instead of the column; not decided.

### G39. Z1: what each role is shown
The map from roles to kinds, beside `sees`.

**identity.5** · From docs/identity.md:103, "Open design issues"

- **What each role is shown** isn't written (see "Authorization").

**identity.6** · From docs/identity.md:111, "Takes on what is open", "Z1: what each role is shown"

Decided: authorization goes by role first, which kinds a role sees, then by the catalog's owners and collaborators. The
map from roles to kinds isn't written; it needs the portal's views to mean anything.

Take: the map goes beside `sees` in `src/chatddx/identity/identity.py`, as data, and `sees` then takes the person's
roles and the kind as well as the `Owned`. The kinds each role authors can go beside it, clinicians appendices,
expectations and typed cases, researchers chunks and recipes, as a convenience for the portal's forms rather than a
refusal.

**bench.14** · From docs/bench.md:455, "Outstanding"

- **Z1**: the map from roles to the kinds each role sees goes in `identity` once the portal's views give it meaning
  (docs/identity.md, "Z1: what each role is shown"). `sees` then takes the person's roles and the kind.

**api.14** · From docs/api.md:435, "Outstanding", "Signing in"

- **Roles aren't checked**; Z1 shapes what each role is shown, with the portal (docs/bench.md, "Outstanding").

**bench.7** · From docs/bench.md:441, "Outstanding", its takes, built and waiting for a word

- ownership only, roles unchecked (docs/identity.md);

### G40. The repl's reach
The repl reaches what the bench offers: every write, a titled thread, seeds, settings and scorers.

**repl.1** · From docs/repl.md:248, "Open design issues", "What the repl doesn't reach"

- It reaches four of the bench's writes (`save`, `start`, `score`, `take`); the API reaches them all.

**repl.2** · From docs/repl.md:249, "Open design issues", "What the repl doesn't reach"

- A thread with a title and no name can't be named.

**repl.3** · From docs/repl.md:250, "Open design issues", "What the repl doesn't reach"

- A run takes one seed, and no execution settings, canary set or text cleanup; `score` can't pick a scorer, score a
  run again, or name the endpoint a judge is called at, so a judge whose engine two endpoints serve bars its scorer.

### G41. The repl's rendering
What the repl prints: tool calls apart, a start, and aligned judge lines.

**repl.5** · From docs/repl.md:256, "Open design issues", "Smaller issues"

- **Two tool calls in one response run together** on one line as they stream, as a call's first delta is taken as its
  name and the deltas don't say where the next begins; `replay` splits them.

**repl.8** · From docs/repl.md:266, "Outstanding"

- **`runs` doesn't show a start.** A translated run says the language it was sent in, the run of the configuration's
  own language from the same start says none, and nothing says the two were started together; the API's
  `GET /api/runs?with=` and a run's page in the portal do (`Bench.runs(started_with=…)`).

**repl.9** · From docs/repl.md:269, "Outstanding"

- **The judge lines aren't aligned**, as their labels differ in length; the labels of a scoring's judge calls are known
  when it starts, so their width could be too.

### G42. Unknown query parameters
Routes refuse what they don't declare.

**api.8** · From docs/api.md:418, "Outstanding", "Serving"

- **A query parameter a route doesn't name is ignored**, unless the query is a model (`Varying`), so a misspelt filter
  on `GET /api/runs` or `GET /api/threads` gives everything, and a part given twice in a variation's query counts the
  last. Take: one check for every route that refuses a parameter the route doesn't declare, and a scalar given twice.

### G43. Curation's round trip
Data sets that go both ways: verified, exported, imported as anyone, from several sources, holding what has no table
yet.

**curation.2** · From docs/curation.md:275, "Open design issues", "Import, export and verification"

- verifying that the store holds a data set, without writing anything, which a loading's validated lines only do
  inside a transaction that writes;

**curation.3** · From docs/curation.md:277, "Open design issues", "Import, export and verification"

- exporting what the archive or a person holds back into a data set's files, so a change made in the portal can be
  kept in git;

**curation.4** · From docs/curation.md:279, "Open design issues", "Import, export and verification"

- importing a data set as someone other than the archive.

**curation.5** · From docs/curation.md:282, "Open design issues", "What a data set can't hold yet"

Trials, executions, scorings and hand-written skeletons have no tables, and a data set has one expectation schema.

**curation.6** · From docs/curation.md:285, "Open design issues", "Smaller issues"

- **One source a run.** A data set's cases all come from the source `--source` names.

Added in triage, from G31:

**curation.7** · From docs/curation.md:286, "Open design issues", "Smaller issues"

- **Leftovers are listed every run.** Nothing records that a leftover is known and meant to stay.

### G44. The sample's data
The sample's stage said in code, and Olof's judge.

**curation.10** · From docs/curation.md:292, "Outstanding"

- **Staging data.** The sample is curated for preliminary calibration, and everything in it can be considered
  guessed: its targets, the appendices and `dont_miss` targets made up so that every table is used, its judge,
  drafted before Olof's, and its translations. Its notes are the exception: they are Olof's as written, and carry
  his name into every score, so none is made up; made-up notes go in the test World, under its placeholder authors.
  Data meant to be relied on needs its stage said in code, not in comments: whether it is guessed or vetted, by
  whom, and where it came from, loaded with the data so that a score can say what it rests on.

**curation.11** · From docs/curation.md:298, "Outstanding"

- **The sample's judge** is a draft over Olof's notes until his prompt replaces it, as an edit. His prompt settles
  which of his comment and answer it reads, how a Swedish note is read against an English answer, whether a verdict is
  pass or fail, a scale or one per aspect, how strict it is about extra or harmful advice, and the judge's engine and
  seeds. It is measured by real answers from pelle and malborg on `Dutchfall11w`, `Dutchfall1w` and `casesfromedn1`,
  graded by Olof with a line on why. Open beside it: notes on more cases, and revising the targets where his notes
  disagree, as on `Dutchfall11w` (shock, most likely sepsis, where the targets have an aortic aneurysm or a
  dissection).

### G45. Missing tests
Tests for what only the test World reaches, and for the scripted runs' and the runner's untested paths.

**curation.12** · From docs/curation.md:305, "Outstanding"

- **What only the test World reaches isn't all read.** No test reads the gate refusing `qwen3-bare@fake` for `typed`
  cases, the pair lints its records give (`vllm.*` on `qwen3-bare@fake` and `clamped`, `facts.output_refused`,
  `facts.reasoning_unmatched`, `facts.budget_refused`, `language.unknown`), `headed`'s tool guidance, the texts of
  `lines-guided` translated into sv, the passthrough, or the vignettes' quirks under the cleanup steps. The lints are
  tested on synthetic registries, and two of the judge tests in src/chatddx/scorers/test/test_scorers.py use a
  synthetic judge.

**scripted.3** · From docs/scripted.md:113, "Open design issues", "Smaller issues"

- **No two scripted runs vary a part over the same cases**, as the page to compare runs wants
  (agents/wip-portal.md, "Comparing variations").

**scripted.4** · From docs/scripted.md:115, "Open design issues", "Smaller issues"

- **`set` and `--again` have no test**, and no scripted run sets a part.

**runner-api.6** · From docs/runner-api.md:335, "Known gaps"

- `send` again after a worker's exception isn't tested.

### G46. The object layer and new kinds
Whether execution settings and chat templates become kinds, and with them the object layer's open questions.

**purist-object-layer.1** · From docs/purist-object-layer.md:214, "Open"

- The name, should the split happen (see "Naming").

**purist-object-layer.2** · From docs/purist-object-layer.md:215, "Open"

- `kind` as a class keyword (see "Kinds written down").

**purist-object-layer.3** · From docs/purist-object-layer.md:216, "Open"

- Whether canary sets and compilations ever move.

**purist-object-layer.4** · From docs/purist-object-layer.md:217, "Open"

- Where `refuse_change` lives.

**purist-object-layer.5** · From docs/purist-object-layer.md:218, "Open"

- Whether execution settings become an object, which this take doesn't decide.

**factors.16** · From docs/factors.md:763, "Potential design improvements", "Execution settings as a component"

Today execution settings are a value inside each run's start record: recorded, sealed with the run's log, and compared
by value. They have no digest, so the catalog can't name a set of settings (for example "sequential" or "8-way"), the
portal can't offer them for picking, and finding the runs that used the same settings means comparing values across run
records.

Making them a component of a new kind, which the start record references by digest, would give them a name, a catalog
thread and a foreign key like the pinned factors. They would still stay out of the trial's digest, so this changes how
execution settings are stored, not what a trial means. The cost is a new kind (with the catalog's thread kinds and their
migration) and a change to the run record.

**factors.17** · From docs/factors.md:774, "Potential design improvements", "Chat templates as components"

Today a local engine pins its chat template by the file's hash, like the model files: a world input, fetched from
wherever the inventory says it is. A bundle therefore holds the template's hash but not the template, and only a host
with the file in hand can read it.

Making the template a component of a new kind, holding the template's text, that the engine references by digest, would
put it inside the bundle: it is small and not sensitive, so a bundle could rebuild the engine's prompt formatting
offline. Lints could read it too, so the check for templates that read the current date would run when factors are
linted, not only on a host. Engines sharing a template would share the component. It would move the template from world
input to authored factor, and cost a new kind (with the catalog's thread kinds and their migration) and a change to the
template check.

### G47. Takes waiting for a word
Built takes to confirm or overturn; a decision each, in the docs, rather than code.

**api.1** · From docs/api.md:404, "Outstanding", "Takes the API is built on"

- **Ids**: a path takes a whole id, and a name is a filter on a list, which gives every match.

**api.3** · From docs/api.md:408, "Outstanding", "Takes the API is built on"

- **Scoring**: at once after a run, with an opt-out, and the runs left to score listed.

**api.4** · From docs/api.md:409, "Outstanding", "Takes the API is built on"

- **Errors**: the bench's errors mapped by class, and what else a route means caught where it means it, each answered
  with a code beside its detail (see "Errors").

**api.5** · From docs/api.md:411, "Outstanding", "Takes the API is built on"

- **Keeping a variation**: a fork and an edit, two requests, rather than a save by name.

**api.6** · From docs/api.md:412, "Outstanding", "Takes the API is built on"

- **Paths**: under `/api/`, with no version until there is a second.

**bench.1** · From docs/bench.md:432, "Outstanding", its takes, built and waiting for a word

- one set of writes for every kind people author, with builders only for appendices and cases, a case built only of
  appendices the person sees, and no write refused on a lint ("Writes for the person", "Appendices and cases");

**bench.4** · From docs/bench.md:437, "Outstanding", its takes, built and waiting for a word

- one write says what holds of a thread; a collaborator can't leave a share, and a thread isn't handed over ("What
  is said about a thread");

**bench.13** · From docs/bench.md:453, "Outstanding"

- **Leaving a share**: a collaborator can't take a shared thread out of what they see; only the owner can. Whether
  a collaborator may withdraw themselves, an entry the catalog would hold as any other, is open.

**bench.5** · From docs/bench.md:439, "Outstanding", its takes, built and waiting for a word

- only an origin the person sees is followed, always by an edit, for every kind ("Following an origin");

**bench.9** · From docs/bench.md:445, "Outstanding", its takes, built and waiting for a word

- configurations listed by purpose, in the API.

**identity.10** · From docs/identity.md:133, "Takes on what is open", "What could move to identity"

Rules that are pure functions of a person go to `identity`, and the bench applies them (`docs/bench.md`). Moving the
catalog's `About.shows` and `About.owned_by` gave `owns`, `collaborates` and `sees`; making the catalog take no person
moved the filtering of threads, families and expectations to the bench, over those rules.

Moving one-line comparisons one at a time doesn't pay: replacing `about.owner == person` with a call of the same
length adds a name and an import per site (tried on the bench, and reverted). Take: move a rule when it is shared by
several places or grows beyond a comparison. Candidates left where they are:
- **The default owner**, `by if owner is None else owner` in `src/chatddx/store/catalog.py:Catalog.create` and
  `Catalog.adopt`. Take: move it when a second rule about owning on write, such as Z1's kinds a role authors, gives
  identity a reason to hold write rules.
- **The bench's owner comparisons**: a person's own deleted threads (`Seen.thread` and `Seen.threads`, with
  `deleted`), only the owner says anything of a thread, and nobody shares with themselves (`saying.py:say`), and an
  expectation that is "yours already" (`taking.py:take_from`).
- **The edges' "own first"**: `src/chatddx/repl/listing.py` and `src/chatddx/portal/` list a person's own first, by
  login or id, much as `preferred` picks.
- **`src/chatddx/catalog/threads.py:picked`** is pure, but decides among a case's expectation threads, not who: it
  stays with the catalog.

Added in triage, from G26:

**bench.2** · From docs/bench.md:434, "Outstanding", its takes, built and waiting for a word

- a family's cases are those at its current vignette; an appendix's edit replaces only the cases at its own
  vignette; carrying keeps to the expectation's family ("Appendices and cases");

Added in triage, from G29:

**bench.8** · From docs/bench.md:442, "Outstanding", its takes, built and waiting for a word

- the shipped lists kept in code, versions as integers from 1, an edit keeping the head's labels only when its scorer
  is the head's, and following taking each part's labels from the side whose part it keeps ("Scorers"); no resources
  offered;

Added in triage, from G30:

**bench.3** · From docs/bench.md:436, "Outstanding", its takes, built and waiting for a word

- a language is written only where a text has none ("Languages");

**bench.10** · From docs/bench.md:447, "Outstanding"

- **A case of no language** goes as written, linted `language.unknown`, rather than left out (agents/wip-engine-part.md,
  "A case of no language"); so does a case of a language the translations don't cover when the configuration's own is
  unknown.

### G48. Text cleanup steps
More cleanup steps, if vignettes need them.

**factors.13** · From docs/factors.md:753, "Open design issues", "Smaller issues"

- **Four cleanup steps exist.** Vignettes may also need non-breaking spaces turned into spaces, zero-width characters
  removed, Unicode line breaks turned into newlines, or trailing whitespace stripped.

### G49. The archive's configuration under another name
A finding when a hand-made recipe is a shared configuration's.

**bench.19** · From docs/bench.md:467, "Outstanding"

- **The archive's configuration saved under another name** is saved with no finding: a hand-made recipe that is a
  shared configuration's, compiled to its skeleton, becomes a thread of the person's own, and only a look's `held_by`
  says so (docs/api-api.md, "threads.py"). An expectation the same as one the person holds is refused.

### G50. The appendix layout as a part
A part a variation can replace, when someone wants to vary it.

**bench.22** · From docs/bench.md:475, "Outstanding"

- **The appendix layout as a part** a variation replaces, when someone wants to vary it. It is a value rather than a
  chunk, so a part would hold one where the others hold a digest, at every edge.

### G51. A low-level manual for the bench
The manual, from `agents/wip-authoring.md` at b6f76b8.

**bench.11** · From docs/bench.md:450, "Outstanding"

- **A low-level manual for the bench**, made from `agents/wip-authoring.md` at b6f76b8.

## For the sweep
References to open items found during triage, for step 5:
- agents/wip-portal.md ("Comparing variations", Open; "Export") and docs/catalog.md ("How the catalog works") cite
  docs/chatddx.md, "On the table", which moved here.
- docs/chatddx.md, "Requirements", cites docs/inventory.md, "Hosts don't read the start-up", which G15 dropped for
  agents/wip-deploy.md.
- docs/bench.md's item on what the old bench had (bench.23) hands two of its parts to agents/wip-portal.md.
- agents/wip-portal.md, "What the docs ask of it", cites docs/catalog.md, "Smaller issues", for what deleting hides.
- agents/wip-clearance.md, "Before real patient data", 9, hands migrations to docs/store.md, "Known gaps": store.1 is
  here now.
- agents/wip-clearance.md, "Before real patient data", 2, cites docs/api.md, "Outstanding", "Serving", and
  docs/worker.md, "Smaller issues", for connections; agents/wip-deploy.md cites docs/worker.md, "The deployment".
- agents/wip-engine-part.md, "Outstanding", hands bench.24, bench.25 and bench.26 to docs/bench.md, "Outstanding":
  they are here now.

## Dropped
Dropped in triage, with why.

G4, as naming no failure and no plan; to be raised again if a mechanism for findings is wanted:

**ledger.9** · From docs/ledger.md:264, "Open design issues", "Smaller issues"

- **Findings have no mechanism of their own.** The runner and the scoring pass keep those they see in the finish record,
  and the checks give the rest when called. They might benefit from a separate mechanism, as lints are for factors, but
  nothing is planned or decided.

**ledger-api.9** · From docs/ledger-api.md:555, "Known gaps"

- Findings have no mechanism of their own beyond the finished rows and the check functions.

G5, as tracked in agents/wip-clearance.md. runner-api.4 was stale besides: "drop variants" took `key` off `send`:

**runner.6** · From docs/runner.md:224, "Open design issues", "Smaller issues"

- **Fingerprints are unkeyed.** Neither `send` nor the ledger takes a key for a call's fingerprints
  (docs/factors.md, "Fingerprints").

**runner-api.4** · From docs/runner-api.md:332, "Known gaps"

- `send.send` takes a `key`, but nothing in the package passes one.

chatddx.6, found late, as tracked in agents/wip-clearance.md:

**chatddx.6** · From docs/chatddx.md:126, "Requirements", "Work in progress"

- How sensitivity is enforced: factors and ledgers provide the means but not the enforcment itself.

chatddx.7, found late, as stale: the store is built (docs/store.md), insert-only, and the catalog keeps the version
chains:

**chatddx.7** · From docs/chatddx.md:127, "Requirements", "Work in progress"

- Storage: How components and records map to Postgres, table structures are suggested for clarity but not prescribed. In general:
    - factor and records are insert-only
    - nothing on the rig is updated (people and the worker are outside of the rig)
    - version chains between digests belong to planned catalog pipeline.

G15, as tracked in agents/wip-deploy.md ("The NixOS module", Open):

**inventory.2** · From docs/inventory.md:284, "Open design issues", "Hosts don't read the start-up"

o11n and the hosts' own configuration (Kompismoln/org) decide what each server runs. The rig imports what they run,
and the start-up of an imported endpoint gives back the command line o11n runs. So the start-up is a check, and only
the fake vLLM is started from one. For a host to start its engines from the rig's start-up, o11n would have to read
it, and the import would then confirm what was started rather than describe it.

**inventory-api.2** · From docs/inventory-api.md:267, "Known gaps"

- Hosts don't start engines from the start-up; only the fake vLLM is started from one.

inventory.3 and inventory-api.3, from G16, as tracked in agents/wip-clearance.md (Open 1, "What a grant keys on"):

**inventory.3** · From docs/inventory.md:290, "Open design issues", "Smaller issues"

- **Endpoint names are only a convention.** Nothing enforces server@host. A run records the endpoint's name, and
  clearance keys on it, so renaming an endpoint drops its clearance without warning, and its runs appear under two
  names.

**inventory-api.3** · From docs/inventory-api.md:268, "Known gaps"

- Endpoint names are only a convention, and renaming one drops its clearance.

inventory.4, inventory-api.4 and runner.10, from G20, as stale: the worker's claims hold a job's slots within its
endpoint's `max_jobs` across workers, and resume a lost run (docs/worker.md, "Claiming"):

**inventory.4** · From docs/inventory.md:293, "Open design issues", "Smaller issues"

- **The capacity holds per run.** Two runs on one endpoint can send twice as many requests between them. vLLM queues
  what's over its limit, so nothing fails, but the batching differs from what each run's execution says.

**inventory-api.4** · From docs/inventory-api.md:269, "Known gaps"

- `max_jobs` holds per run, not per endpoint.

**runner.10** · From docs/runner.md:230, "Open design issues", "Smaller issues"

- **`max_jobs` across runs** belongs to the worker, and so does asking for a lost run to resume.

catalog.4 and catalog-api.4, from G26, as holding: the database keeps a family to its source, and nothing changes one:

**catalog.4** · From docs/catalog.md:411, "Open design issues", "Smaller issues"

- **Current bindings are compared within a source.** Surveys, adopting and repairing compare a vignette only with the
  families of its own source, which relies on a family never changing source. The database enforces that, and nothing
  in the catalog changes a source.

**catalog-api.4** · From docs/catalog-api.md:740, "Known gaps"

- Current bindings are read per source, which relies on a family never changing source; tier 2 holds that.

factors.21, from G26, as answered: a repair rebinds (docs/catalog.md, "Repairing"), and a clinician confirms a case's
replacement after a content change, which the bench stores when asked (docs/bench.md, "Appendices and cases"):

**factors.21** · From docs/factors.md:209, inline, in "Cases"

Whether a person or an automatic step rebinds them is open; the catalog has the tools for it (docs/catalog.md).

catalog-api.12, from G29, as decided: a scorer edited without labels keeps the head's only when it is the head's
scorer, since a position only means something within one scorer (docs/catalog.md, "Scorer labels"):

**catalog-api.12** · From docs/catalog-api.md:749, "Known gaps"

- Scorer labels aren't carried to the next edit of a scorer thread.

catalog.10, from G31, as tracked in agents/wip-portal.md ("What the docs ask of it"):

**catalog.10** · From docs/catalog.md:424, "Open design issues", "Smaller issues"

- **What deleting hides in the portal**: everywhere, or only in pickers, while the runs that used it stay visible.

store.5 and store-api.4, from G33, as stated: docs/store-api.md, "Conventions", "Canonical text", reads components
and records from their canonical text, never from `doc`:

**store.5** · From docs/store.md:131, "Known gaps"

- The copy of each component and record kept for queries reorders object keys, so a schema's property order survives
  only in the stored text. Components and records are read from the stored text, and a future ORM or view must not
  rebuild them from the copy.

**store-api.4** · From docs/store-api.md:402, "Known gaps"

- `doc` reorders object keys; components and records must be read from `canonical` and `payload`.

store.7 and store-api.6, from G33, as unplanned: the store is plain SQL with no ORM by design, and views come with
what reads the store from outside, such as G6b's export:

**store.7** · From docs/store.md:137, "Known gaps"

- Read-only views per kind of component, for a future ORM, aren't written.

**store-api.6** · From docs/store-api.md:404, "Known gaps"

- No per-kind read-only views.

store.6 and store-api.5, from G33, as a design choice: the runner wants each row to land as it is written; threads and
connections are G35's and agents/wip-clearance.md's ("Before real patient data", 1 and 2):

**store.6** · From docs/store.md:134, "Known gaps"

- No async API. The runner is synchronous, and wants each row to land as it is written. On a connection that doesn't
  commit each statement by itself, a write outside a transaction opens one that only the caller commits, and the
  store's own transactions become savepoints inside it.

**store-api.5** · From docs/store-api.md:403, "Known gaps"

- No async API, and on a connection that isn't in autocommit mode, writes wait for the caller's commit.

worker.3, from G35, as tracked in agents/wip-deploy.md, which takes the HTTP server to be the proxy in front of the
app; it was stale besides, as `nix/module.nix` is built:

**worker.3** · From docs/worker.md:118, "Open design issues", "The deployment"

Decided: the HTTP server, the API and the worker as separate systemd services on NixOS. The flake has no NixOS module
yet, and its stop timeout is to exceed the worker's deadline. What the HTTP server is stays open: the portal's pages
served apart from the API, or a proxy in front of both; the portal is one app with the API (agents/wip-portal.md, "P3b,
concretely"), and its `__Host-` cookie wants one host for both.

api.7 and worker.7, from G35, as tracked in agents/wip-clearance.md ("Before real patient data", 2, Connections),
which also counts two connections for a run's event stream, not one:

**api.7** · From docs/api.md:415, "Outstanding", "Serving"

- **A connection per request**, about 2.6 ms each over the Unix socket, opened and closed each time; one for each
  stream while it is open, and one per process listening for them all; and two for each job a worker holds. A pool
  (`psycopg_pool`) for requests and streams when a measurement says so.

**worker.7** · From docs/worker.md:132, "Open design issues", "Smaller issues"

- **Connections.** Each stream holds one while it is open, each app process one listening for them all, and the worker
  two for each job it holds.

## Context
What the moved sections said of their items as a whole, moved with them.

From docs/api.md:397, "Outstanding":

> Left for later, each with what holds and the take on it, the agent's recommendation, which waits for a word. The
> bench's are in docs/bench.md, "Outstanding".

From docs/api.md:401, "Outstanding", "Takes the API is built on":

> Built as the takes of the plan at 100a078 had them, and not confirmed since. Decided there: who it is for, kept open;
> FastAPI and uvicorn; signing in; and sensitive content in places of its own. Decided since: where a run runs and
> its events (see "Where it runs" and "Its events").

From docs/bench.md:429, "Outstanding":

> Left for later. The API's are in docs/api.md, "Outstanding". The plan the bench was built from, with the options
> weighed for each decision and the survey of the old project, is `agents/wip-bench.md` at d5ebf52; the writes for
> the person were planned in `agents/wip-authoring.md` at b6f76b8. Its takes were built and still wait for a word:

From docs/catalog.md:395, "Open design issues":

> These are open questions of design. Where the code falls short of this document, the API says so
> (docs/catalog-api.md, "Known gaps").

From docs/catalog-api.md:734, "Known gaps":

> From `docs/catalog.md`, "Open design issues", where they concern this API:

From docs/chatddx.md:315, "Possible design issues":

> **Canary drift is not implemented:** nothing compares canary outputs between phases or runs. What counts as the
>   same canary output is undecided:
>   (a) the digest of each choice's message, as the old `compare_canaries` compared
>   output digests;
>   (b) the prompt-token fingerprint alone, which catches a changed template or tokenizer but not
>   changed weights; or
>   (c) both, with (b) under a code of its own. None needs a new field, since `CanaryCall.call`
>   holds the response and the prompt-token fingerprint.
>   A human report that the agent's take is (c)

From docs/curation.md:274, "Open design issues", "Import, export and verification":

> Curation is the place for the rest of the store's authored content to come and go:

From docs/factors.md:708, "Open design issues":

> These are open questions of design. Where the code falls short of this document, the API says so (docs/factors-api.md,
> "Known gaps").

From docs/factors-api.md:1056, "Known gaps":

> From `docs/factors.md`, "Open design issues", where they concern this API:

From docs/facts.md:142, "Open design issues":

> These are open questions of design. Where the code falls short of this document, the API says so
> (docs/facts-api.md, "Known gaps").

From docs/facts-api.md:288, "Known gaps":

> From `docs/facts.md`, "Open design issues":

From docs/identity.md:106, "Takes on what is open":

> "Open design issues" lists these too; here are the takes.

From docs/identity.md:108, "Takes on what is open":

> `docs/identity.md`, "Open design issues", lists these too; here are the takes.

From docs/inventory.md:267, "Open design issues":

> These are open questions of design. Where the code falls short of this document, the API says so
> (docs/inventory-api.md, "Known gaps").

From docs/inventory-api.md:265, "Known gaps":

> From `docs/inventory.md`, "Open design issues":

From docs/ledger.md:240, "Open design issues":

> These are open questions of design. Where the code falls short of this document, the API says so
> (docs/ledger-api.md, "Known gaps").

From docs/ledger.md:244, "Open design issues", "Some of what happened isn't checked":

> Most of the plan is compared with what happened (see "What a record holds"), but not all:

From docs/ledger-api.md:545, "Known gaps":

> From `docs/ledger.md`, "Open design issues", where they concern this API:

From docs/repl.md:262, "Outstanding":

> Suggested, and left for later:

From docs/runner-api.md:328, "Known gaps":

> From `docs/runner.md`, "Open design issues", where they concern this API:

From docs/store.md:123, "Known gaps":

> These are known shortcomings of the store's design. Some have more details in docs/store-api.md.

From docs/store-api.md:398, "Known gaps":

> From `docs/store.md`, "Known gaps", where they concern this API:

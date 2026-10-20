# Glossary

The terms, the roles, and every finding the code makes, in one place. The terms were gathered from the glossaries
`docs/` used to hold, and reconciled against the code.

- "Terms" holds one definition per term, true to the code. Code names where the code holds it, or none for a
  concept only the research has. A word that names two things has a row for each, told apart in parentheses.
- "Roles" holds the people's roles, what each authors, and the database's roles.
- "Findings" holds every `Finding(…)` made in `src/chatddx/`, by where it is raised.
- "Open" holds what the code can't settle, with options.

## Terms

| Term | Meaning | Code |
| --- | --- | --- |
| Active | Whether a person may sign in; making them inactive ends their sessions. People are made inactive, never deleted. | `src/chatddx/identity/identity.py:Person.active` |
| Admin (database) | The database role that owns the database and its schemas, may create databases and roles, and runs the migrations. | `src/chatddx/store/setup.sql` |
| Appendix | Extra plain text written for one vignette, sent with it by the cases that include it. Text cleanup doesn't touch it. | `src/chatddx/factors/cases.py:Appendix` |
| Archive | The person who owns everything a data set loads, and shares it with each person a loading names. Never wiped. | `src/chatddx/curation/write.py:ARCHIVE` |
| Attempt | One try at sending a call's request. A call is tried again only when the request didn't get through: no connection, a 429 or a 5xx. | `src/chatddx/ledger/call.py:Call.attempts` |
| Attestation | What the engine says about itself in its responses, the model it answered as and the prompt it read, set beside what was declared. | `src/chatddx/ledger/call.py:attest_model` |
| Base | The version a fork is compared with: the one it came from, or the origin's head it last followed. | `src/chatddx/catalog/model.py:Divergence.base` |
| Beat | Marking a worker and its jobs as seen, and hearing whether each is to halt or its owner has paused. | `src/chatddx/store/queue.py:Queue.beat` |
| Behind | A reference of a thread's head that a live thread has since moved on from, or a case whose family has a newer binding. | `src/chatddx/catalog/threads.py:behind` |
| Bench | What one person sees and does, whatever the edge. | `src/chatddx/bench/bench.py:Bench` |
| Binding | Where a family's vignette is: source, id and fingerprint. The latest is current. | `src/chatddx/catalog/model.py:Binding` |
| Bound | Of a data set's judge: given by the World the handle whose model it is made for when loaded, and whose latest engine then judges it. | `src/chatddx/inventory/inventory.py:Inventory.judges` |
| Bundle | A set of root components plus everything they reference, stored as canonical text keyed by digest, together with the code version that produced it, so it can be checked offline. | `src/chatddx/factors/bundle.py:Bundle` |
| Cage | The environment runs and scores happen in, which can be provably rebuilt from what was pinned, and delivered with the results. | none |
| Call | One exchange with an engine: a request sent, in one or more attempts, and what came back or why nothing did. | `src/chatddx/ledger/call.py:Call` |
| Canary | A fixed, non-sensitive probe request, sent at a run's start or end to reveal an engine that changed. | `src/chatddx/factors/trial.py:Canary` |
| Canonical form | The one way a component or a record is written out: JSON with field names sorted, fields equal to their default left out (the kind kept), and the schema version added. JSON data keeps its key order, since a schema's property order is part of what a model reads; settings' keys and other order that means nothing (a model's files, a trial's cases, translations) are put in a fixed order, so equivalent components share a digest. | `src/chatddx/factors/base.py:Component.canonical_doc` |
| Carrying | Editing an expectation onto another case of its family, with the same data. | `src/chatddx/portal/threads.py` |
| Case | A vignette plus the appendices sent with it, in order. | `src/chatddx/factors/cases.py:Case` |
| Case title | How the repl names a case: its family's name, or `FAMILY with APPENDIX, …` for a case that sends appendices, each appendix by its thread's name. | `src/chatddx/bench/seen.py:Seen.case_titled` |
| Catalog | People's handles on components and records: threads and their versions, families and where their vignettes are, and what is said of them. | `src/chatddx/catalog/` |
| Chunk | A component that fills one of a recipe's nine chunk parts: instructions, few-shot, prompt, output, sampling, reasoning, passthrough, translations or toolset. Not to be confused with a slot. | `src/chatddx/factors/request.py:CHUNK_PARTS` |
| Chunk (streamed) | One piece of a response as it streams in. | `src/chatddx/runner/wire.py:Chunk` |
| Claim | Taking the next job that fits its endpoint's free slots, or one that is lost or is to halt, and marking it under way. | `src/chatddx/store/queue.py:Queue.claim` |
| Cleared | An endpoint's permission, for now, to receive content from a sensitive source; without it, the gate refuses runs and judge calls on that source's cases there. | `src/chatddx/inventory/inventory.py:Inventory.cleared` |
| Closure (components) | A set of components and everything they reference, transitively. | `src/chatddx/factors/bundle.py:Registry.closure` |
| Closure (Nix) | The Nix store path a local engine's runtime runs from. | `src/chatddx/factors/engine.py:Runtime.closure` |
| Collaborates on | Has it shared with them, while it is live, and isn't its owner. | `src/chatddx/identity/identity.py:collaborates` |
| Collapse | A level the model is asked for exactly as another, so the two are one request. | `src/chatddx/factors/facts.py:ReasoningFacts` |
| Compilation | A provenance component that says which recipe, compiler and facts produced a skeleton, and the language it was compiled into, none for the recipe as written. | `src/chatddx/factors/request.py:Compilation` |
| Component | An immutable set of parameters of one kind, identified by its digest and referring to other components by theirs. Pinned factors are held in components; canary sets, facts and compilations are components but not factors. | `src/chatddx/factors/base.py:Component` |
| Configuration | A skeleton thread: each version a request, with the recipe it was compiled from unless written by hand. | `src/chatddx/bench/model.py:KINDS` |
| Configurations (inventory) | The handle whose model a data set's configurations are made for when it is loaded. | `src/chatddx/inventory/inventory.py:Inventory.configurations` |
| Contract | How an output, and the skeleton compiled from it, constrains the answer: native (the engine enforces the schema), tool (the answer is a forced function call) or text (nothing is constrained). | `src/chatddx/factors/request.py:OutputContract` |
| Curation | Loading a data set into the store as the archive's and sharing it, keeping it in step with its files and its vignettes' sources, and taking back all a person owns. | `src/chatddx/curation/` |
| Cutoff | Ending a call early and keeping what came, with why as its error: a runaway of whitespace, or a timeout. | `src/chatddx/runner/send.py:send` |
| Data set | A directory of authored files: factors, texts and cases by language, and the files they load. Its engines are the World's. | `src/chatddx/curation/plan.py:plan_factors` |
| Deadline | How long a stopping worker's scorings go on before they are cut short and queued again. | `src/chatddx/settings.py:WORKER_DEADLINE` |
| Default | The reasoning level a model uses when a request says nothing about reasoning. A reasoning chunk may ask for it, and it lands like any other level. | `src/chatddx/factors/facts.py:ReasoningFacts.default` |
| Digest | The hash of a component's canonical form as stored, `sha256:<hex>`. Components are told apart and referred to by it. | `src/chatddx/factors/base.py:Component.digest` |
| Edge | What a person reaches the bench through: the repl, the API, the portal, or a command acting as them. | none |
| Edit | One version on a thread. Editing writes a new one on a thread of one's own, naming the head it was made on. | `src/chatddx/catalog/model.py:Edit` |
| Endpoint | Where one engine is served, under the inventory's name for it: its address, the host that runs a local engine, how many requests it takes at once, the variable holding its secret, and the canary set and execution its runs default to. | `src/chatddx/inventory/inventory.py:EndpointSpec` |
| Engine | What answers requests: a vLLM server we run, pinned by its hardware, runtime, weights, chat template and arguments, or a remote API's model. Where it is reached is its endpoint. | `src/chatddx/factors/engine.py:LocalEngine` |
| Entry | Something said about a thread, a family, a run or a score: a name, description, tag, owner, collaborator, deleted flag, a family's language, or what a run varied, replaced and was started with. | `src/chatddx/catalog/model.py:Entry` |
| Event | One message of a run's event stream: a record of its log as written, or what its worker says as it happens. | `src/chatddx/api/telling.py:Telling` |
| Execution | How a run sends its items, and a score its judge calls: order, concurrency, timeout, retries and the runaway cutoff. Recorded at the start, not pinned; the endpoint gives the default. | `src/chatddx/factors/trial.py:Execution` |
| Expectation | The reference data for one case, written to an expectation schema, that a scorer's views grade answers against. | `src/chatddx/factors/scoring.py:Expectation` |
| Factor | Anything that can change an output or its score: what the research varies, holds fixed, or has to account for. The package and the schema named for factors hold every component, factors or not. | none |
| Facts | What is known about one model that a request doesn't say: its reasoning levels, recommended sampling, output caveats and specs. Written by people in TOML, stored as a component on a thread per model, and read by compiling and by lints; not a factor. | `src/chatddx/factors/facts.py:ModelFacts` |
| Family | The handle on one vignette through renames and changes at its source; every case of the vignette belongs to it. | `src/chatddx/catalog/families.py:family_of` |
| Finding | A warning or an info with a code, a message and what it is about: something declared that doesn't match what was observed, something that failed or is missing, or a risky setting. | `src/chatddx/factors/base.py:Finding` |
| Fingerprint | A hash of content that is not stored with the factors or the ledger: a vignette, a request, a prompt's token ids. It names its algorithm: `sha256`, or `hmac-sha256` with the key's id. | `src/chatddx/factors/base.py:Fingerprint` |
| Following | Keeping the proposal as an edit of the person's own fork, based on its origin's head. | `src/chatddx/bench/following.py:follow` |
| Following its facts | Keeping a configuration's recipe, with its model's head, compiled against the facts as they are now, as a new version of the person's own. | `src/chatddx/bench/following.py:follow_moved` |
| Fork | A thread started from a version of another thread of the same kind, its origin. Forking makes one of one's own from any thread one sees. | `src/chatddx/catalog/model.py:Thread.forked_from` |
| Gate | What refuses an endpoint or a judge before a run or a scoring uses it: another engine than the trial's, a sensitive source not cleared, tools on a sensitive source, a judge that reads the case, an unset secret, or a server not serving the model. | `src/chatddx/runner/gate.py:bar` |
| Giftbag | A person's own forks of the chunks, tools, skeletons and expectations a loading gives the archive. | `src/chatddx/curation/write.py:_Init.giftbag` |
| Guidance | Text that tells the model how to answer, an output's, which may show the schema, or how to use its tools, a toolset's. | `src/chatddx/factors/request.py:Output.guidance` |
| Halt (job) | Asking a run's queued or running job to end at once: its calls are hung up and the run is finished unscored, or its scoring stops. | `src/chatddx/store/queue.py:Queue.halt` |
| Head | A thread's latest edit, its current version. A variation is built on it unless an earlier edit is named. | `src/chatddx/catalog/threads.py:head` |
| Host (inventory) | A machine that runs local engines: the address its servers listen on, and where it keeps the model files and chat templates they pin. | `src/chatddx/inventory/inventory.py:HostSpec` |
| Include | A file of endpoints and hosts, as the engine import writes them, that an inventory takes as its own. | `src/chatddx/inventory/inventory.py:Inventory.load` |
| Insert | A placeholder filled at compile time: the output's schema in its guidance, or the output's or the toolset's guidance in the instructions or the prompt. Its text before and after appears only when what it inserts isn't empty. | `src/chatddx/factors/request.py:Insert` |
| Instrument | A component that measures without being a factor: canary sets. | `src/chatddx/factors/trial.py:CanarySet` |
| Intent | What a reasoning or sampling chunk asks of the model instead of setting it: a reasoning level, or the recommended sampling, worked out from the facts about the recipe's model when the recipe is compiled. | `src/chatddx/factors/request.py:Reasoning.level` |
| Inventory | The files that say where vignette sources, endpoints and hosts are, and for now which endpoints are cleared for which sources, which handle each of a data set's judges is bound to, and which handle configurations are made for. Ops write them; the engine import writes the endpoints and hosts. | `src/chatddx/inventory/inventory.py:Inventory` |
| Item (run) | One case's replicate in a run: the fingerprint of the vignette as read, its first call and each tool round's. | `src/chatddx/ledger/run.py:RunItem` |
| Item (score) | How one view graded one run item, with the judge calls it took. | `src/chatddx/ledger/score.py:ScoreItem` |
| Item key | A case and a replicate's index, which identify an item of a run, and with a view an item of a score. | `src/chatddx/ledger/record.py:ItemKey` |
| Job | A run queued for the worker, for its owner at its endpoint: to send and finish, then score when asked, or, finished, to score again. | `src/chatddx/store/queue.py:Job` |
| Judge | An LLM used as a metric by a scorer's views: a judge skeleton, the model's weights, its own seeds, and a rule for filling in what a view picks. The scoring pins the engine it is sent to. | `src/chatddx/factors/scoring.py:Judge` |
| Kind | What a component is, written into it and read first: `engine.local`, `chunk.prompt` and the rest. | `src/chatddx/factors/kinds.py:KINDS` |
| Label (scorer) | What an edit of a scorer thread calls one of its views or resources. | `src/chatddx/catalog/read.py:labels` |
| Label (variation) | A variation's short title, `NAME+PART=CHUNK`, which names its runs. | `src/chatddx/bench/variation.py:TriedVariation.label` |
| Land | Where a level ends after its collapses and nearests: on a way of asking, a refusal, or nothing known. Only a way of asking compiles. | `src/chatddx/factors/facts.py:Landing` |
| Latest wins | Of the rows about one thing, the one written last holds; for tags and collaborators, the last about each. | `src/chatddx/catalog/model.py:About.of` |
| Ledger | All records: the logs of every run and every score. | `src/chatddx/ledger/` |
| Left out | The cases of a language a configuration's translations can't carry it into, because they don't go into it or leave a text untranslated. Said with why, and not sent. | `src/chatddx/bench/model.py:Started.left_out` |
| Left to score | A scorer that applies to a finished run, with an expectation for some of its cases, and no whole score of the run under the scoring built now. | `src/chatddx/bench/seen.py:Seen.unscored` |
| Leftover | An archive thread or family a loading didn't come to, as when the data set no longer names it. Listed, never deleted. | `src/chatddx/curation/write.py:_Init.leftovers` |
| Level (finding) | How much a finding weighs: a warning, or an info. | `src/chatddx/factors/base.py:Finding.level` |
| Level (reasoning) | What a reasoning chunk asks of reasoning: off, on, minimal, low, medium, high or xhigh, or the model's default. The facts say how each is asked for; a request carries only what it lands on. | `src/chatddx/factors/facts.py:Intent` |
| Location | Where a host keeps a model or a chat template, written the way vLLM on the host reads it. | `src/chatddx/inventory/inventory.py:HostSpec` |
| Log | A run or a score as written: a start record, a record per item (and, for a run, per canary call), and once it is done a finish record. Only ever added to. | `src/chatddx/ledger/record.py:Log` |
| Login | What a person signs in with, and is named by when shared with or acted as. Unique and lowercase. | `src/chatddx/identity/identity.py:Person.login` |
| Look | Asking for a configuration's variation with nothing stored: its parts, the request it would send, the handle it runs under or why it can't run, its lints, the languages its cases are sent in and its reach. | `src/chatddx/api/threads.py` |
| Lost | A job under way whose worker hasn't been seen for a while, so a claim takes it. | `src/chatddx/store/queue.py:Queue.claim` |
| Migration | A file of SQL, at a tier, that a deployment applies once when it migrates to that tier or above. | `src/chatddx/store/migrate.py:Migration` |
| Nearest | The level a refused level is asked for instead, when its refusal names one. Landing goes on from it. | `src/chatddx/factors/facts.py:Refusal.nearest` |
| No target | Why a view gives a case no value: its expectation gives the view nothing to hold an answer to, or there is none. | `src/chatddx/scorers/scorer.py:NO_TARGET` |
| Outcome | How an item ended, from its last call and the answer read from it: stopped, errored, unread, salvaged, completed, invalid or valid. | `src/chatddx/runner/outcome.py:Outcome` |
| Own language | A configuration's language: the one its recipe's texts are all written in, or a hand-written skeleton's. Cases in it, or in none, are sent as written. | `src/chatddx/catalog/language.py:recipe_language` |
| Owner, collaborator | Who a thread, family, run or score belongs to, and who it is shared with. Together they decide what a person sees. | `src/chatddx/catalog/model.py:About` |
| Owns | Is the owner of, while it is live. | `src/chatddx/identity/identity.py:owns` |
| Parts | The chunks and the model a variation replaces over a configuration, each by its digest. An empty chunk takes an optional part out; the model can't be taken out. | `src/chatddx/api/schemas.py:Parts` |
| Person | Someone who acts in chatddx, by an id the rest of the store refers to, with a login, a name, roles, and whether they are active. | `src/chatddx/identity/identity.py:Person` |
| Pinned | Fixed in advance inside a component, so that changing it changes that component's digest and the digest of every component that refers to it. | none |
| Pinned, recorded, observed | The three ways a factor is held: fixed in advance by digest, written into a run's or a score's start record, or only detected afterwards. | `src/chatddx/ledger/run.py:RunStarted` |
| Plan, conduct, observation | What a start or an item record holds: what the run or score was set to do, what the rig did, and what the world answered. A finish record holds its seal and findings. | `src/chatddx/ledger/run.py:RunStarted` |
| Portal | The web interface where people write and version their components, review cases, and start, watch, score and compare runs; the bench's third edge. It is to export results, which isn't built. | `src/chatddx/portal/app.py:app` |
| Proposal | When the origin has moved on, its head with a fork's changes on top. | `src/chatddx/catalog/threads.py:proposal` |
| Provenance | A component that says how another was made, without being a factor: compilations. | `src/chatddx/factors/request.py:Compilation` |
| Purpose | Whether a prompt, a recipe or a skeleton writes an answer (generation) or grades one (judge). It decides which slots are allowed and which are required. | `src/chatddx/factors/request.py:Purpose` |
| Reach | Of a scorer's view: whether a variation's output offers what it reads, and which cases have an expectation of the person's own it picks from, none, or several to choose from. | `src/chatddx/bench/model.py:Reach` |
| Reader | The database role that may read the factors, the catalog and people, and nothing else; nothing connects as it yet. | `src/chatddx/store/migrations/0002-t1-factor.sql` |
| Recipe | The chunks, purpose, appendix layout and model a skeleton is compiled from. Not a component: it is kept in its compilations. | `src/chatddx/factors/request.py:Recipe` |
| Recommended sampling | The sampling a model's makers recommend for a reasoning level, as the facts hold it; a sampling chunk may ask for it. | `src/chatddx/factors/facts.py:SamplingFacts.recommended` |
| Record (data set) | A named entry of a data set's factors or texts files, or of a World's engines files, loaded as a thread. | `src/chatddx/curation/plan.py:Planned` |
| Record (ledger) | What the rig writes as a run or a score goes, its start, each item or canary call, and its finish; never changed. | `src/chatddx/ledger/record.py:Record` |
| Refusal | A fact that says the model can't be asked for a level, a thinking budget or an output contract, and why. | `src/chatddx/factors/facts.py:Refusal` |
| Repair | Moving a family to its vignette's new id or content: its cases rebuilt, its appendix threads moved, and on a rename its expectation threads. | `src/chatddx/catalog/families.py:plan_repair` |
| Repl, shell | `chatddx repl`, a shell for one person over a World. | `src/chatddx/repl/shell.py:Repl` |
| Replacement | The case a stale case becomes under its family's current binding: the same appendices on the current vignette. | `src/chatddx/catalog/families.py:replacement` |
| Replicate | One seed of a trial, identified by that seed's position in the trial. | `src/chatddx/ledger/record.py:ItemKey.replicate` |
| Request | The body one call sends to an engine: a skeleton rendered with its fills, the model and the seed, a tool round's next request, or a canary. | `src/chatddx/factors/request.py:Skeleton.render` |
| Rig | The chatddx software that builds cages from factors, runs and scores inside them and records what happened, which build of it included. | `src/chatddx/rig.py:rig` |
| Role (person) | Admin, clinician, developer, ops or researcher; a person may hold several, and nothing checks one yet. | `src/chatddx/identity/identity.py:Role` |
| Run | One execution of a trial at one endpoint, written as a log: what it was set to do, each item's calls, and its finish. | `src/chatddx/ledger/run.py:Run` |
| Runner | What starts or resumes a run at an endpoint, sends its items and canaries, runs its tools, and writes the run. | `src/chatddx/runner/run.py:Runner` |
| Salvaged | A structured answer cut short, read with its structure closed. | `src/chatddx/scorers/answer.py:Answer.salvaged` |
| Saying | The owner writing what holds of a thread: its name, description, tags, collaborators and whether it is deleted. | `src/chatddx/bench/saying.py:say` |
| Schema (database) | One namespace of the database's tables: factor, ledger, identity, catalog, source (typed vignettes) or worker (the queue). | `src/chatddx/store/migrations/` |
| Schema op | A named, versioned rewrite an output chunk applies to its schema at compile time, so the skeleton sends and shows the rewritten schema. Today the only one is `inline_refs@1`. | `src/chatddx/factors/request.py:SchemaOp` |
| Score | One scoring of a finished run, written as a log: what it was set to do, how each view graded each run item, and its finish. | `src/chatddx/ledger/score.py:Score` |
| Scoring pass | What grades a finished run with a scoring, asking a view's judge where it names one, and writes the score. | `src/chatddx/runner/score.py:grade` |
| Script | The turns the fake answers with, one per request it accepts, so one per attempt. | `src/chatddx/fake_vllm/script.py:Script` |
| Scripted run | A run made to be looked at, described by a file in a World's `_runs/` and answered by the fake from its script. | `src/chatddx/scripted/read.py:ScriptedRun` |
| Seal | The hash over a log's records but its finish record, kept in the finish record. | `src/chatddx/ledger/record.py:seal_rows` |
| Seed | A number that fixes the sampler's randomness, not sent when sampling is greedy. Each seed of a trial is one replicate; a judge's seeds and an execution's shuffle seed are not. | `src/chatddx/factors/trial.py:Trial.seeds` |
| Sees | Owns or collaborates on; a run only when one owns it. | `src/chatddx/identity/identity.py:sees` |
| Segment | One piece of a message: a literal string or a slot. A prompt's pieces may also be inserts, which compiling fills. | `src/chatddx/factors/request.py:Segment` |
| Sensitive | Content that may go only where it is cleared to go: a source's vignettes, unless the source says otherwise, and everything made from them. Today only sending to an endpoint is checked. | `src/chatddx/runner/gate.py:bar` |
| Session | A person signed in: a token, carried as a bearer or a cookie, of which only a digest is kept. It lasts 12 hours, or until they sign out or are made inactive. | `src/chatddx/store/people.py:People.open_session` |
| Skeleton | The frozen request trials and judges reference: everything sent but the slots' fills, the model and the seed. Compiled from a recipe, or written by hand. | `src/chatddx/factors/request.py:Skeleton` |
| Slot | A placeholder filled at send time: the vignette, the appendices, the completion or the expectation. | `src/chatddx/factors/request.py:Slot` |
| Slots | What a job holds of its endpoint's `max_jobs` while under way: its run's concurrency. A scoring alone holds none. | `src/chatddx/store/queue.py:Job.slots` |
| Source | Where a set of vignettes is fetched from, by id: a directory, or texts people typed, kept in the database. Its name is part of every case built from it, and it is sensitive unless it says otherwise. | `src/chatddx/inventory/sources.py:Source` |
| Stage | A log's start or finish record. | `src/chatddx/ledger/record.py:Stage` |
| Stand-in | The fake vLLM serving a remote engine's model on this machine, at the remote endpoint's address. | `src/chatddx/scripted/fakes.py:fake_at` |
| Start | The runs one start of a variation makes: a run per language its cases are sent in, the later ones `with` the first. | `src/chatddx/bench/runs.py:start` |
| Start-up | What starting a local engine's endpoint takes: vLLM's arguments, the engine's environment and the runtime, joining the engine with where its host keeps what it pins. | `src/chatddx/inventory/serving.py:StartUp` |
| Stop, interrupt, halt (runner) | Ending a run: after the items under way; at once, recording the calls under way as stopped and raising; or at once from another thread, returning. | `src/chatddx/runner/run.py:Running.stop` |
| Subject | The thread, family, run or score an entry is about. | `src/chatddx/catalog/model.py:Subject` |
| Survey | Comparing what a source lists with where its families are bound: unchanged, changed, renamed, new or gone. | `src/chatddx/catalog/families.py:survey` |
| Taking | Forking an expectation shared with the person into a thread of their own, so that it counts. | `src/chatddx/bench/taking.py:take` |
| Text | A chunk that holds what the model reads: instructions, few-shot examples, a prompt, an output or a toolset, written in one language; in a data set, the one its texts file is named for. | `src/chatddx/curation/plan.py:TEXT_TABLES` |
| Text (translated) | One string the model reads, as a translations chunk maps it. | `src/chatddx/factors/request.py:texts` |
| Text cleanup | The named, versioned steps a trial applies to its vignettes after fingerprinting and before sending; a source names the default ones. | `src/chatddx/factors/cases.py:CleanupOp` |
| Thread | A handle on a sequence of components of one kind, its versions in the order they were saved. | `src/chatddx/catalog/model.py:Thread` |
| Tier | How much integrity the database enforces: structure, then grants, then checks and triggers that repeat the rules held in Python and keep tables append-only. | `src/chatddx/store/migrate.py:TOP_TIER` |
| Title | How something without a name is shown, built when asked and never stored: for a fork, its origin's title and what it varies; else a name it had earlier; else what it holds. | `src/chatddx/catalog/titles.py:title` |
| To choose from | A case with several expectations under one schema where one is needed: several of the person's own that differ, or several shared with them to take. | `src/chatddx/bench/seen.py:choices` |
| Tool round | Running the tools a response called, and sending their results in the next request. A round stopped while its tools run has no request. | `src/chatddx/ledger/call.py:Turn` |
| Translated | A run whose skeleton is its configuration's recipe compiled into its cases' language through the recipe's translations. | `src/chatddx/bench/model.py:Carried.translated` |
| Translations | A chunk that maps each text a recipe's other chunks and appendix layout hold to its translation, for each language it goes into; cases and appendices aren't translated. In a data set it is written in the texts file of each such language. | `src/chatddx/factors/request.py:Translations` |
| Trial | One experimental condition, the smallest unit of a scientific intent: a generation skeleton, an engine, cases, text-cleanup steps and seeds. | `src/chatddx/factors/trial.py:Trial` |
| Typed case | A case whose vignette is a text the person typed, kept in a database source, with a family of their own in the language they say. | `src/chatddx/bench/cases.py:type_case` |
| Variation | A version of a configuration with recipe parts replaced over it, or none, as it is tried before anyone keeps it as a fork or a new version. | `src/chatddx/bench/variation.py:TriedVariation` |
| Varies | Of a fork: what its head changes from its base. | `src/chatddx/catalog/model.py:Divergence.varies` |
| Verdict | A judge's answer for one seed, as its skeleton's contract reads it, or none when it can't be read. | `src/chatddx/runner/score.py:Grading` |
| Vetted | Cleared by a person to receive sensitive content: today an endpoint in the inventory's clearance table, later what the planned clearance pipeline grants. | none |
| View | One comparison a scorer makes: what it picks from an output and from an expectation, how the output's pick is split, and the metric, with its parameters and its judge if any, that grades them. | `src/chatddx/factors/scoring.py:View` |
| Vignette | The clinical text a source holds under one id, named by the source, the id and a fingerprint of its bytes. Sensitive unless its source says otherwise. | `src/chatddx/factors/cases.py:Vignette` |
| Wire-body | A request as it goes over the wire: the rendered request plus the streaming options, sent with the endpoint's secret in a header. May hold sensitive content. | `src/chatddx/runner/send.py` |
| Word | What a kind of thread is asked for by: configuration, each chunk part, model, engine and the rest. | `src/chatddx/bench/model.py:KINDS` |
| Worker | What claims queued jobs and works them, each on a thread, in a process of its own or the app's. | `src/chatddx/worker/worker.py:Worker` |
| world | What lies outside chatddx's control: vignette sources, model files, the Nix closure, the chat-template file, a remote engine. Its factors are observed, or imported by fingerprint. | none |
| World | The directory that describes one deployment's world: an inventory, the engines and model facts it adds, and the data carried with it. | `src/chatddx/inventory/world.py:World` |
| Writer | The database role the app connects as: it reads and adds, updates only people, their passwords and the worker's queue, and deletes only sessions. | `src/chatddx/store/setup.sql` |

## Roles

### People
The roles live in code (`src/chatddx/identity/identity.py:Role`) and are stored on the person by name; a person may
hold several, and nothing checks a role yet (`docs/identity.md`, "Roles"). The second column is what
`docs/chatddx.md` said under "Roles mentioned", verbatim, which lives only here now; the third gathers each
"Principal author" line of `docs/factors.md` and `docs/bench.md`.

| Role | Roles mentioned | Principal author of |
| --- | --- | --- |
| admin | (not mentioned; identity's own, for administering people) | nothing |
| clinician | Owners of vignettes and authors of Appendices and Expectations | case, appendix, expectation |
| developer | Authors of schemas, canary sets, scoring and text-cleanup functions | tool, model facts (the bundled ones), expectation schema, scorer (its scoring code), canary sets |
| ops | Owners of engines and authors of the engine's components | local model, local engine, remote engine |
| researcher | Authors of Sampling, Judges and Trials, and of a scorer's views, free parameters and labels | instructions, few-shot, prompt, output, sampling, reasoning, passthrough, toolset, recipe, trial, scorer (its views, free parameters and labels; picks its code, expectation schema and resources), judge (its skeleton and seeds; picks its model by handle and its fill rule), scoring, translations (as translators) |

- `docs/chatddx.md` said: "These roles are distinct and not overlapping, a person may inhabit more than one role."
- Nobody authors compilations, and skeletons are compiled but for a hand-written configuration's. A World's model
  facts are written by whoever adds a model they don't know.
- Ops write the inventory, but for the endpoints and hosts the engine import writes ("Terms": Inventory).
- Translators are researchers (`agents/wip-translators-view.md`, T1); `docs/chatddx.md` named none.
- A person also stands to a thread, a family, a run or a score as its owner or a collaborator, and one person, the
  archive, owns what data sets load ("Terms": Owner, collaborator; Archive).
- Placeholder people in docs and tests are alice, bob, carol…, or semantic names (`AGENTS.md`, rule 6).

### The database
PostgreSQL's roles, not people's: "admin" names both (`docs/store.md`, "Roles and connections"; the grants are in the
tier-1 migrations, `src/chatddx/store/migrations/`).

| Role | In PostgreSQL | Used by | Created by | May |
| --- | --- | --- | --- | --- |
| Admin | `chatddx` | `chatddx migrate` and the tests | the setup script | own the database and schemas; create databases and roles |
| Writer | `chatddx_writer` | every other command | the setup script, or tier 1 when it is missing | read and add to the factors, the ledger, the catalog and typed vignettes; read, add and update people, their passwords and the worker's queue; end sessions |
| Reader | `chatddx_reader` | nothing yet | tier 1 | read the factors, the catalog and people; not passwords, sessions, the ledger, typed vignettes or the queue |

## Findings
A finding (`src/chatddx/factors/base.py:Finding`) has a level, `warning` unless said, a code, a message and optionally
a subject. What findings are is in `docs/chatddx.md` ("Findings and errors"), `docs/factors.md` and `docs/ledger.md`
("Errors and findings"), `docs/ledger.md` and `docs/runner.md` ("Findings"); the o11n import's are in
`docs/inventory.md`. This is every code made in `src/chatddx/`, by where it is raised. A code raised in more than one
place has a row in each.

### Lints
A component's checks against the components it references, made by `src/chatddx/factors/lint.py` and, with the
facts, `src/chatddx/facts/lint.py`. Raised by a look (`src/chatddx/bench/seen.py:Seen.findings`), a written edit
(`src/chatddx/bench/seen.py:linted`), checking a component (`src/chatddx/bench/components.py:check`), a loading
(`src/chatddx/curation/write.py:_Init.lint`) and, `src/chatddx/factors/lint.py` only, an o11n import
(`src/chatddx/importers/o11n.py:imported`). A judge is linted on its handle's latest engine, and on none where it
can't judge.

| Code | Level | Subject | When |
| --- | --- | --- | --- |
| `model.revision` | warning | local model | Its revision isn't a commit, so it can move. |
| `engine.closure` | warning | local engine | Its runtime's closure isn't a Nix store path. |
| `view.unreachable` | warning | scorer | A view's expectation selector reaches nothing in the expectation schema. |
| `expectation_schema.invalid` | warning | expectation schema | Its `$schema` names no draft that can be checked, or it breaks its draft. |
| `output.schema_invalid` | warning | output | Its JSON schema names no draft that can be checked, or breaks its draft. |
| `expectation.unchecked` | warning | expectation | A `$ref` in its schema can't be resolved. |
| `expectation.invalid` | warning | expectation | Its data breaks its schema. |
| `schema.ref_unverified` | warning | trial, judge | The constrained answer's schema, or a tool's parameters, hold `$ref`, on an engine other than vLLM 0.24. |
| `vllm.temperature_clamped` | warning | trial, judge | A temperature above 0 and below 0.01, which vLLM 0.24 raises to 0.01. |
| `vllm.thinking_budget_refused` | warning | trial, judge | `thinking_token_budget` on a vLLM 0.24 without `--reasoning-parser` or `--reasoning-config`. |
| `vllm.tools_refused` | warning | trial, judge | Tools on a vLLM 0.24 without `--enable-auto-tool-choice` and `--tool-call-parser`. |
| `vllm.native_tools_uncallable` | warning | trial, judge | A native contract with tools: vLLM 0.24 constrains the whole answer, so no tool can be called. |
| `vllm.grammar_before_reasoning` | warning, or info when the request isn't known to reason | trial, judge | A constrained answer on a vLLM 0.24 without `--reasoning-parser`, so the model can't reason first. |
| `language.unknown` | info | trial | The request's language, or some cases', is unknown. |
| `language.mixed` | warning | trial | Cases in another language than the request's. |
| `trial.engine_unmatched` | warning | trial | The skeleton was worked out from the facts about another model than the engine serves. |
| `judge.model_unmatched` | warning | judge | The skeleton was worked out from the facts about another model than the judge's. |
| `judge.greedy_seeds` | warning | judge | A greedy judge with several seeds, which send the same request. |
| `facts.missing` | info | trial, judge | No facts about the model, so the model's checks are skipped. |
| `facts.reasoning_unmatched` | warning | trial, judge | The reasoning settings match none of the model's reasoning levels. |
| `facts.budget_refused` | warning | trial, judge | `thinking_token_budget` on a model whose facts refuse a budget. |
| `facts.output_refused` | warning | trial, judge | The model's facts refuse the skeleton's contract. |
| `facts.output_note` | info | trial, judge | The model's facts note a caveat on the skeleton's contract. |
| `facts.sampling_unmatched` | warning | trial, judge | The sampling is what the facts recommend for other models, not this one. |

### Looking at translations
Raised by a look (`src/chatddx/bench/seen.py:missing`).

| Code | Level | Subject | When |
| --- | --- | --- | --- |
| `translations.missing` | warning | configuration | Cases in a language its translations can't carry it into, left out; or a language its translations go into that doesn't compile. |

### The inventory
Raised at the end of `chatddx init-data` (`src/chatddx/cli.py`) and of an o11n import
(`src/chatddx/importers/o11n.py:checked`), by `src/chatddx/inventory/check.py:check`.

| Code | Level | Subject | When |
| --- | --- | --- | --- |
| `endpoint.engine_unknown` | warning | endpoint | Its engine isn't known. |
| `endpoint.not_engine` | warning | endpoint | Its engine's digest is another kind of component. |
| `endpoint.unstartable` | warning | endpoint | Its start-up can't be made from the inventory. |
| `endpoint.remote_host` | warning | endpoint | It serves a remote engine and names a host. |
| `endpoint.shared_url` | warning | endpoint | Another local endpoint has its address. |
| `host.unpinned` | info | host | It says where it keeps a model or chat template that none of its endpoints' engines pins. |
| `cleared.not_sensitive` | info | endpoint | It is cleared for a source that isn't sensitive. |

### An o11n import
Raised for each server imported (`src/chatddx/importers/o11n.py:imported`), the chat template checked by
`src/chatddx/factors/engine.py:check_chat_template`. Every subject is the local engine.

| Code | Level | When |
| --- | --- | --- |
| `engine.chat_template` | warning | The chat template doesn't match the declared digest. |
| `engine.chat_template_date` | warning | The chat template reads the current date. |
| `engine.chat_template_unused` | info | vLLM renders the model with Harmony and doesn't read the chat template. |
| `engine.harmony_date` | warning | Harmony writes the date into every prompt, and `VLLM_SYSTEM_START_DATE` isn't set. |
| `engine.chat_template_unread` | info | The report has no template text. |
| `engine.chat_template_not_the_model_s` | info | The chat template isn't the model's own at this revision. |
| `endpoint.process` | warning | The server's process wasn't seen. |
| `endpoint.not_running` | warning | The server isn't running. |
| `endpoint.argv` | warning | The running server's argv isn't the configured one. |
| `endpoint.unreachable` | warning | The server didn't answer. |
| `endpoint.version` | warning | The server's vLLM version isn't its package's. |
| `endpoint.served_name` | warning | The server doesn't answer as the engine's digest. |

### Loading a bundle
Raised by `src/chatddx/factors/bundle.py:Bundle.load`.

| Code | Level | Subject | When |
| --- | --- | --- | --- |
| `bundle.recanonicalized` | warning | component | The running code serializes the component differently from its stored text. |

### Running
Noted by the runner as it works, and kept in the run's finish record (`src/chatddx/runner/run.py`,
`src/chatddx/factors/cases.py:prepare_case`).

| Code | Level | Subject | When |
| --- | --- | --- | --- |
| `run.resumed` | warning when another build of the rig resumes it than started it, else info | none | The run was resumed. |
| `case.unreadable` | warning | item | The item's case can't be prepared. |
| `case.drift` | warning | case | The vignette at the source differs from the case's. |

### Scoring
Noted by the scoring pass as it works, and kept in the score's finish record (`src/chatddx/runner/score.py`).

| Code | Level | Subject | When |
| --- | --- | --- | --- |
| `answer.salvaged` | info | item | The answer was cut short, and read with its structure closed. |
| `answer.unread` | warning | item | The answer can't be read. |
| `answer.invalid` | warning | item | The answer was read and breaks its schema. |
| `verdict.unread` | warning | item | A judge's verdict can't be read. |
| `verdict.invalid` | warning | item | A judge's verdict was read and breaks its schema. |

### Checking a run
Raised by `src/chatddx/ledger/run.py:check_run`, with `src/chatddx/ledger/call.py` and
`src/chatddx/ledger/record.py:check_seal`, when a run finishes and when the API shows a run or tells that it
finished; repeatable, so never stored.

| Code | Level | Subject | When |
| --- | --- | --- | --- |
| `ledger.seal` | warning | run | Rows changed after the log was sealed. |
| `run.incomplete` | warning | none | A finished run lacks items or canary calls. |
| `case.drift` | warning | item | The vignette read differs from the case's. |
| `call.failed` | warning | item, canary call | Its last call ended with an error. |
| `tools.stopped` | warning | item | A round stopped before its tool calls had all run. |
| `tools.unanswered` | warning | item | The last response still calls tools after the last round. |
| `tools.code` | warning | tool | The tool's code ran at another version than it pins, or isn't recorded. |
| `attestation.model` | warning | item | The engine answered as another model than declared, or as none. |
| `attestation.prompt_tokens` | warning | none | Items without a prompt token fingerprint. |
| `execution.retries` | warning | none | Calls took more attempts than allowed. |
| `execution.order` | warning | none | Items were sent before items scheduled ahead of them. |
| `execution.concurrency` | warning | none | More calls were in flight at once than declared. |
| `canary.phase` | warning | none | Start canary calls hadn't finished when the first item was sent, or end canary calls started before the last item call finished. |

### Checking a score
Raised by `src/chatddx/ledger/score.py:check_score`, with `src/chatddx/ledger/call.py` and
`src/chatddx/ledger/record.py:check_seal`, when a scoring pass finishes; repeatable, so never stored.

| Code | Level | Subject | When |
| --- | --- | --- | --- |
| `view.unreachable` | warning | scorer | A view's output selector reaches nothing in the run's output schema. |
| `judge.incomplete` | warning | item | A view's value rests on fewer of its judge's seeds than declared. |
| `attestation.model` | warning | item | The judge engine answered as another model than declared, or as none. |
| `score.scorer_code` | warning | score | The scorer's code ran at another version than it pins. |
| `score.run_unfinished` | warning | score | The run hasn't finished, or the score started before it did. |
| `ledger.seal` | warning | score | Rows changed after the log was sealed. |
| `score.no_expectation` | warning | score | Some of the run's cases have no expectation in the scoring. |
| `score.incomplete` | warning | none | A finished score lacks items. |
| `execution.retries` | warning | none | Judge calls took more attempts than allowed. |
| `execution.order` | warning | none | Items' judge calls were sent before those of items scheduled ahead of them. |
| `execution.concurrency` | warning | none | More judge calls were in flight at once than declared. |

## Open
What reconciling the terms left for a human: words the code uses for two things, or that the docs and the code use
differently. Nothing here is decided.

1. **Record.** A ledger record and a data set's record are two things under one word ("Terms": Record (ledger),
   Record (data set)).
   - (a) Both stay, told apart by their qualifier.
   - (b) A data set's record gets a word of its own; "entry" is the catalog's.
2. **Intent and level.** The docs' intent is what a reasoning or sampling chunk asks for; the code's `Intent`
   (`src/chatddx/factors/facts.py:Intent`) is the type of the reasoning levels, which `docs/facts.md` calls levels and
   "the old chatddx's intents".
   - (a) The docs' words stand, and the code's type is named for levels.
   - (b) Both stand, the type's name read as "the intents a level can be".
3. **`max_jobs`.** An endpoint's `max_jobs` counts requests at once, not jobs
   (`src/chatddx/inventory/inventory.py:EndpointSpec`), and a job's slots are its run's requests at once
   ("Terms": Endpoint, Slots).
   - (a) The field is renamed for what it counts, as `docs/inventory.md` calls it: capacity.
   - (b) It stays, and the docs say what it counts.
4. **A variation "is just a digest".** `docs/chatddx.md` ("Intended evolution of configurations") and `docs/bench.md`
   ("The variation being tried") say so of one being tried, where the code holds it as a value
   (`src/chatddx/bench/variation.py:TriedVariation`): an edit, its recipe and the parts set on it. Only the skeleton it
   compiles to has a digest.
   - (a) Read as "nothing is stored of it", and left as it is.
   - (b) A suggestion to both docs: a plain value, of which nothing is stored.
5. **A case's title.** The catalog titles a case of an unnamed family by its vignette's `SOURCE/ID`
   (`src/chatddx/catalog/titles.py:_case_title`), and the bench finds the family as `family N`
   (`src/chatddx/bench/model.py:Family.name`), so a title as shown may not find its case
   (`src/chatddx/bench/seen.py:Seen.case_titled`). Read from the code, not run.
   - (a) The bench finds an unnamed family by `SOURCE/ID` too.
   - (b) The title says `family N` too.
6. **Request.** "Terms": Request is the body a call sends, but `docs/chatddx.md` calls a skeleton "the frozen request"
   and a configuration "a request kept on a skeleton thread", and the API's requests are HTTP requests.
   - (a) Request stays the body a call sends, and the other two are said as skeleton and configuration.
   - (b) "Request" is the frozen request, and the body a call sends is "the request as sent".

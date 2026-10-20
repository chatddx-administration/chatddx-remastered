# Glossary

Every term table and glossary in `docs/`, the roles, and every finding the code makes, in one place.

- "Terms" holds the rows of `docs/chatddx.md` ("Glossary") and of each `docs/<doc>.md` ("Terms"), copied verbatim and
  sorted by term. Doc names the doc a row comes from. A term several docs define keeps a row for each.
- "Roles" holds the people's roles, what each authors, and the database's roles.
- "Findings" holds every `Finding(…)` made in `src/chatddx/`, by where it is raised.
- "Where the docs part" holds the definitions that disagree with each other or with the code, with options.

## Terms

| Term | Meaning | Doc |
| --- | --- | --- |
| Active | Whether a person may sign in. People are made inactive, never deleted. | identity |
| Admin | The role that owns the database and runs the migrations. | store |
| Appendix | Extra plain text written for one vignette. | factors |
| Archive | The person who owns what a data set loads, and shares it with everyone else. | curation |
| Attempt | one try at sending a call's request; a call is tried again only when the request didn't get through. | chatddx |
| Attempt | One try at sending a call's request. | ledger |
| Attestation | What the engine says about itself: the model it answered as and the prompt it read. | ledger |
| Base | The version a fork is compared with: the one it came from, or the one its changes were last re-applied onto. | catalog |
| Beat | Marking a worker and its jobs as seen, and hearing whether each is to halt or its owner has paused. | worker |
| Behind | A reference whose thread has moved on, or a case whose family has a newer binding. | catalog |
| Bench | What one person sees and does, whatever the edge. | bench |
| Binding | Where a family's vignette is: source, id and fingerprint. The latest is current. | catalog |
| Bound | A data set's judge, given the handle whose latest engine judges it. | inventory |
| Bundle | a set of root components plus everything they reference (the closure), stored as canonical text keyed by digest, together with the code version that produced it. | chatddx |
| Cage | the constrained environment a bundle enforces | chatddx |
| Call | one exchange with an engine: a request sent, in one or more attempts, and what came back. | chatddx |
| Call | One exchange with an engine. | ledger |
| Canary | a fixed, non-sensitive probe request. | chatddx |
| Canary | A fixed, non-sensitive probe request. | factors |
| Canonical form | JSON with field names sorted and fields left out when equal to their default, plus the type's schema version. JSON data keeps its key order, because a schema's property order is part of what a model reads; the keys of settings (`Settings`: bodies, `chat_template_kwargs`, `params`, and `env`) are sorted, so equivalent settings share a digest. | chatddx |
| Carrying | Editing an expectation onto another case of its family, with the same data. | bench |
| Case | A vignette plus the appendices sent with it. | factors |
| Case title | A family's name, or `FAMILY with APPENDIX, …` for a case that sends appendices. | repl |
| Catalog | People's handles on components and records: names, versions, owners, sharing, deletions, languages and labels. | catalog |
| Cell | What the shell runs: a configuration, its model one of its parts, and the endpoint named for it, if any. | repl |
| Chunk | a factor authored in the portal that fills one part of a recipe (not to be confused with a slot). | chatddx |
| Chunk | A component that fills one part of a request. | factors |
| Claim | Taking the next job that fits, and marking it under way. | worker |
| Cleared | An endpoint's permission, for now, to receive content from a sensitive source. | inventory |
| Closure | A component and everything it references, transitively. | store |
| Collaborates on | Has shared with them, while it is live, and isn't the owner of. | identity |
| Collapse | A level that is asked for as another. | facts |
| Compilation | A provenance (component) that says which recipe, compiler and facts produced a skeleton, and the language it was compiled into, none for the recipe as written | chatddx |
| Component | An immutable set of parameters identified by its digest. Pinned factors are held in components. | factors |
| Configuration | A skeleton thread: requests, each version with the recipe it was compiled from. | catalog |
| Configurations | The handle whose model a data set's configurations are made for. | inventory |
| Contract | how an output chunk constrains the answer: `native`, `tool` or `text`. | chatddx |
| Contract | How the answer is constrained: native, tool or text. | factors |
| Curation | Getting authored content into the store as the archive's, keeping it in step with its files, and taking it out of people's way. | curation |
| Cutoff | Ending a call early, keeping what came: a runaway, or a timeout. | runner |
| Data set | A directory of authored files: factors, cases by language, and what they load. | curation |
| Deadline | How long a stopping worker's scorings go on. | worker |
| Default | The level a model uses when a request says nothing about reasoning. | facts |
| Digest | the factor's identity and how it's referenced, an `sha256:<hex>` over the component's canonical bytes. | chatddx |
| Digest | The hash of a component's canonical form. Components are told apart and referred to by it. | factors |
| Edge | What a person reaches the bench through: the repl, the API, the portal. | bench |
| Edit | One version on a thread. | catalog |
| Edit | A new version of a configuration of one's own. | api |
| Endpoint | Where one engine is served: its address, capacity and secret, and the host that runs it. | inventory |
| Endpoint | Where an engine is reached, by the World inventory's name (docs/inventory.md, "Endpoints"). | runner |
| Engine | Where requests go: a vLLM server we run, or a remote API. | factors |
| Entry | Something said about a thread, a family, a run or a score: a name, description, tag, owner, collaborator, deleted flag or language. | catalog |
| Event | One step of what is under way for a run, as its events tell it. | api |
| Execution | how a run sends its items, and a score its judge calls: order, concurrency, timeout, retries and the runaway cutoff. | chatddx |
| Expectation | The reference answer for one case. | factors |
| Factor | Anything that can change an output or its score (`docs/factors.md`, "What a factor is"). | chatddx |
| Factor | Anything that can change an output or its score. | factors |
| Facts | ops- or developer-authored knowledge about models (how each reasoning level is expressed, collapsed, refused or landed on its nearest, recommended sampling, output caveats, specs), typed in code, written in TOML and stored by init-data as components of kind `facts`, a thread per model, corrected by a new version. Not factors: they work out a reasoning level and a recommended sampling for the recipe's model when compiled. | chatddx |
| Facts | What is known about a model that a request doesn't say. A component, but not a factor. | factors |
| Facts | What is known about a model that a request doesn't say, written by people, one model at a time, and stored as a component, a thread per model. | facts |
| Family | The handle on one vignette through renames and edits at its source. | catalog |
| Finding | a warning or info produced when something declared doesn't match what was observed, or when a setting is risky. | chatddx |
| Fingerprint | a hash of content that must *not* be stored: vignette, request, prompt token ids. It carries its algorithm: `sha256`, or `hmac-sha256` with a `key_id` | chatddx |
| Following | Keeping the catalog's proposal as an edit of the person's fork, based on its origin's head. | bench |
| Following its facts | Keeping a configuration's recipe, compiled against the facts corrected since, as an edit of the person's own. | bench |
| Fork | A thread started from a version of another thread of the same kind, its origin. | catalog |
| Fork | A new configuration of one's own, made from one the person sees. | api |
| Gate | What refuses an endpoint before sensitive content goes to it. | runner |
| Giftbag | A person's own forks of the archive's chunks, tools, skeletons and expectations. | curation |
| Guidance | Text that tells the model how to answer, or how to use its tools. | factors |
| Halt | Ending what is under way for a run early: its sending, hanging up the calls under way, or its scoring. | api |
| Head | A thread's latest edit, its current version. | catalog |
| Head | A configuration's latest version, which a request's variation is built on. | api |
| Host | A machine that runs local engines, and where it keeps the model files and chat templates they pin. | inventory |
| Include | A file whose endpoints and hosts an inventory takes as its own. | inventory |
| Insert | a placeholder filled at compile time: `schema` in an output chunk's guidance, filled with that output's schema, and `output_guidance` and `tool_guidance` in the instructions or the prompt, filled with the output's guidance and the toolset's. An insert's `before` and `after` text appear only when what it inserts isn't empty. | chatddx |
| Insert | A placeholder filled at compile time: the output's schema, the output guidance or the tool guidance. | factors |
| Instrument | A component that measures without being a factor: canary sets. | factors |
| Intent | What a reasoning or sampling chunk asks of the model, a reasoning level or the recommended sampling, worked out from the facts about the recipe's model when the recipe is compiled. | factors |
| Intent | A reasoning level or the recommended sampling, asked for in a chunk and worked out from the facts when a recipe is compiled. | facts |
| Inventory | files written by ops that say where vignette sources, endpoints and hosts are (`docs/inventory.md`). | chatddx |
| Inventory | Files written by ops that say where things are: vignette sources, endpoints and hosts. For now, they also say which endpoints are cleared for which sources. | inventory |
| Item | one case's replicate in a run: its first request and each tool round's, each sent as a call. | chatddx |
| Item | One case's replicate in a run: its first request and each tool round's. | factors |
| Item | One case's replicate in a run: its first request and each tool round's; or how one view graded one run item. | ledger |
| Item | One case's replicate in a run: its first request and each tool round's, each a call. | api |
| Item key | (case, replicate index), which identifies an item of a run, and with a view an item of a score. | chatddx |
| Job | a started run or scoring queued for the worker, at its endpoint, for its owner, scored afterwards or not. | chatddx |
| Job | A started run to finish and score when asked, or a finished run to score again, for its owner. | worker |
| Job | What the app has under way for a run: the run, or a scoring of it, with its events. | api |
| Judge | An LLM used to grade outputs. | factors |
| Kind | the discriminator of a component, e.g. `engine.local`, `chunk.prompt`. | chatddx |
| Label | The name of a scorer's view or resource. | catalog |
| Label | Of a variation: its short title, `NAME+PART=CHUNK`, not stored. Of a scorer: what an edit calls one of its views or resources. | bench |
| Land | Where a level ends after its collapses and nearests: on a way of asking, a refusal, or nothing known. | facts |
| Latest wins | Of the rows about one thing, the one written last is what holds. | catalog |
| Ledger | All records: the run and score logs. | ledger |
| Left out | The cases of a language a configuration's translations can't carry it into, said and not sent. | bench |
| Left out | Cases in a language the configuration's translations don't cover: said, and not sent. | repl |
| Left to score | Scorers that applies in finished run that has no whole score of it under the scoring built now. | bench |
| Left to score | A scorer that applies to a run with no whole score under its scoring as built now. | repl |
| Leftover | An archive thread or family the data set no longer names. | curation |
| Level | What a request asks of reasoning: off, on, minimal, low, medium, high or xhigh. | facts |
| Location | Where a host keeps a file, written the way the host reads it. | inventory |
| Log | A run or a score: a start record, item records and a finish record, only ever added to. | ledger |
| Login | What a person signs in with: unique and lowercase. | identity |
| Look | Asking for a configuration's variation: what it would send, its lints, the languages its cases are sent in and its reach, with nothing stored. | api |
| Lost | A job under way whose worker hasn't been seen for a while, claimed again. | worker |
| Migration | A file of SQL a deployment applies once, at its tier. | store |
| Nearest | The level a refused level lands on instead, when its refusal names one. | facts |
| No target | A view a case's expectation gives nothing to hold an answer to. | repl |
| Outcome | How an item ended: stopped, errored, unread, salvaged, completed, invalid or valid. | api |
| Outcome | How an item went, from its last call and its answer. | repl |
| Own | Owned by the person, while it is live. | bench |
| Own language | A configuration's: its recipe's texts', or a hand-written skeleton's. It is sent in it as written. | bench |
| Owner, collaborator | Who a thread or family belongs to, and who it is shared with. Together they decide what a person sees. | catalog |
| Owns | Is the owner of, while it is live. | identity |
| Parts | The chunks and the engine a variation replaces over a configuration, each by its digest, or nothing to take an optional chunk out. | api |
| Person | Someone who acts in chatddx, by an id the rest of the store refers to. | identity |
| Pinned | a value that can't be altered without changing the digest of one or more factors. | chatddx |
| Pinned, recorded, observed | The three ways a factor is held: fixed in advance by digest, written into a run's or a score's start record, or only detected afterwards. | factors |
| Plan, conduct, observation | What a record holds: what a run or a score is set to do, what the rig did, and what the world answered. | ledger |
| Portal | the web-interface used to configure factors, watch runs and export results. | chatddx |
| Portal | The web interface where components are written and runs are watched. | factors |
| Proposal | The origin's head with a fork's changes on top. | catalog |
| Provenance | A component that says how another was made, without being a factor: compilations. | factors |
| Purpose | whether a prompt or skeleton is for `generation` or for a `judge`; it decides which slots are allowed. | chatddx |
| Purpose | Whether a request writes an answer (generation) or grades one (judge). It decides which slots are allowed. | factors |
| Reach | Of a scorer's view: whether a variation's output offers what it reads, and which cases have an expectation it picks from. | bench |
| Reach | Of a scorer's view: whether a variation's output offers what it reads, and which cases have an expectation it picks from. | api |
| Reader | The role that may read what isn't sensitive. | store |
| Recipe | the chunks and the model a skeleton was compiled from. | chatddx |
| Recipe | The choice of chunks, and the engine, a request is compiled from. Not a component. | factors |
| Recommended sampling | The sampling a model's makers recommend for a level. | facts |
| Record | A named entry of a data set's factors file, loaded as a thread. | curation |
| Record | What the rig writes when something happens; never changed. | ledger |
| Record / ledger | events logged while running or scoring. | chatddx |
| Refusal | A fact that says the model can't do something, and why. | facts |
| Repair | Moving a family to its vignette's new id or content, and rebinding what depends on it. | catalog |
| Repl, shell | `chatddx repl`, for one person over a World. | repl |
| Replacement | The case a stale case becomes under its family's current binding. | catalog |
| Replicate | one seed of a trial, identified by its index. | chatddx |
| Request | the body one call sends to an engine: a skeleton rendered with its fills, the served model and the seed, or a tool round's next request. | chatddx |
| Request | The body one call sends to an engine: a skeleton rendered, or a tool round's next request. | factors |
| Request | The body one call sends to an engine. | ledger |
| Rig | the chatddx software that builds cages from factors, runs and scores inside them and records what happened. | chatddx |
| Role | Admin, clinician, developer, ops or researcher; a person may hold several. | identity |
| Round | Running the tools a response called and sending the next request. | runner |
| Run | One execution of a trial: its requests, responses and records. | factors |
| Run | A variation sent at an endpoint on some cases with some seeds, recorded as it goes. | api |
| Run and Score | a stage log. | chatddx |
| Runner | What sends a trial's requests and writes the run. | runner |
| Salvaged | A structured answer cut short, read with its structure closed. | repl |
| Saying | Writing what holds of a thread: its name, description, tags, collaborators, and whether it is deleted. | bench |
| Saying | Writing what holds of a thread: its name, description, tags, collaborators, and whether it is deleted. | api |
| Schema | One module's tables, in a namespace of their own. | store |
| Schema op | a named, versioned rewrite an output chunk applies to its schema at compile time, so the skeleton sends and shows the rewritten schema. Today the only one is `inline_refs@1`. | chatddx |
| Scoring pass | What grades a finished run with a scoring and writes the score. | runner |
| Script | The turns the fake answers with, one per attempt. | scripted |
| Scripted run | A run made to be looked at, written as a file in a World's `_runs/` and answered by the fake from its script. | scripted |
| Seal | the hash over a log's started row and item rows, kept in its finished row. | chatddx |
| Seal | The hash over a log's records, kept in its finish record. | ledger |
| Seed, replicate | A seed fixes the sampler's randomness. Each seed of a trial is one replicate, identified by its position. | factors |
| Sees | Owns, or collaborates on. | identity |
| Sees | Owns or collaborates on, while it is live. | bench |
| Segment | a literal string, a slot or an insert | chatddx |
| Segment | One piece of a text: a literal string, a slot or an insert. | factors |
| Sensitive | data that may only be stored or sent where it is cleared to go (see "Vignettes and anything made from them are sensitive"). | chatddx |
| Session | A person signed in, by a token of which only a digest is kept. | identity |
| Session | A person signed in: a token, carried as a bearer or as a cookie, for 12 hours. | api |
| Skeleton | the frozen request. | chatddx |
| Skeleton | The compiled, frozen request. | factors |
| Slot | a placeholder filled at send time. | chatddx |
| Slot | A placeholder filled at send time: the vignette, the appendices, the completion or the expectation. | factors |
| Slots | What a job holds of its endpoint's `max_jobs`: its run's concurrency. | worker |
| Source | Where a set of vignettes is fetched from, by id. Its name is part of every case built from it. | inventory |
| Stage | A log's start or finish record. | ledger |
| Stand-in | The fake vLLM serving a remote engine's model on this machine, at the remote endpoint's address. | scripted |
| Start | The runs one start makes: a run per language its cases are sent in, the later ones `with` the first. | bench |
| Start | The runs one request starts: a run per language its cases are sent in, the later ones started with the first. | api |
| Start-up | what the start-up script runs for one endpoint, joining an engine (what) with inventory entries (where) (`docs/inventory.md`, "The start-up"). | chatddx |
| Start-up | What the start-up script runs for one endpoint: vLLM's arguments, the environment and the runtime. | inventory |
| Stop, interrupt, halt | Ending a run after the items under way; at once, raising; at once, from another thread. | runner |
| Subject | What an entry is about. | catalog |
| Survey | Comparing what a source lists with where its families are bound. | catalog |
| Take | A fork of an expectation shared with the person, so that it counts. | api |
| Taking | Forking a thread shared with the person to make it their own, as an expectation must be to count. | bench |
| Text | A chunk that holds text the model reads, written in a texts file whose name gives its language. | curation |
| Text cleanup | the named steps a trial applies to vignettes before they are sent. | chatddx |
| Text cleanup | Named steps that tidy a vignette before it is sent. | factors |
| Thread | The versions of one component that people edit, in order. | catalog |
| Tier | How much integrity the database enforces: structure, then grants, then the rules held in Python. | store |
| Title | How something without a name is shown, built from what it holds. | catalog |
| To choose from | A case with several expectations of the person's own under one schema or several shared with them. | bench |
| Tool round | the tools a response called, run, and the next request, sent with their results. | chatddx |
| Tool round | Running the tools a response called, and sending the next request. | ledger |
| Translated | A run whose skeleton is the configuration's compiled into its cases' language by its translations. | repl |
| Translations | A chunk that translates a data set's texts into other languages, written in the texts file of each language it translates into. | curation |
| Trial | The smallest unit of an scientific intent (i.e. Experiment): skeleton + engine + cases + text-cleanup steps + seeds. | chatddx |
| Trial | The pinned factors of one experiment: a skeleton, an engine, cases, text cleanup and seeds. | factors |
| Typed case | A case whose vignette is a text the person typed, kept in a database source. | bench |
| Variation | A configuration with recipe parts replaced over a version of a configuration: tried, or kept as a fork or a new version. | catalog |
| Variation | A configuration thread's edit with parts set on it: what the shell holds and runs, under its model's handle. | repl |
| Variation being tried | A configuration with recipe parts replaced over it, or none, that nobody has saved. | bench |
| Varies | Of a fork: what its head changes from its base. | catalog |
| Verdict | A judge's answer, as its skeleton's contract reads it. | runner |
| Vetted | a fact within the planned clearance pipeline. | chatddx |
| View | the part of an output and of an expectation that a scorer scores, and how. | chatddx |
| View | One comparison a scorer makes between part of an output and part of an expectation. | factors |
| Vignette | The clinical text of one case at its source. Sensitive. | factors |
| Wire-body | a request as sent: with the streaming options, and the secret in a header. May hold sensitive content. | chatddx |
| Word | What a kind of thread is asked for by: configuration, a recipe part, engine and the rest. | bench |
| Worker | the process that runs the trials queued for it, outside the request that asked for them. | chatddx |
| Worker | What claims queued jobs and works them, in a process of its own or the app's. | worker |
| World | factor parameters outside of the orchestrator's direct control. (the vignette source, model files, the Nix closure, the chat-template file, the remote engine) | chatddx |
| World | A directory with an inventory, the files it includes, and the factors of the engines its endpoints serve. | inventory |
| Writer | The role the app connects as. | store |

## Roles

### People
The roles live in code (`src/chatddx/identity/identity.py:Role`) and are stored on the person by name; a person may
hold several, and nothing checks a role yet (`docs/identity.md`, "Roles"). The second column is `docs/chatddx.md`
("Roles mentioned") verbatim; the third gathers each "Principal author" line of `docs/factors.md` and
`docs/bench.md`.

| Role | Roles mentioned | Principal author of |
| --- | --- | --- |
| admin | (not mentioned; identity's own, for administering people) | nothing |
| clinician | Owners of vignettes and authors of Appendices and Expectations | case, appendix, expectation |
| developer | Authors of schemas, canary sets, scoring and text-cleanup functions | tool, model facts (the bundled ones), expectation schema, scorer (its scoring code), canary sets |
| ops | Owners of engines and authors of the engine's components | local model, local engine, remote engine |
| researcher | Authors of Sampling, Judges and Trials, and of a scorer's views, free parameters and labels | instructions, few-shot, prompt, output, sampling, reasoning, passthrough, toolset, recipe, trial, scorer (its views, free parameters and labels; picks its code, expectation schema and resources), judge (its skeleton and seeds; picks its model by handle and its fill rule), scoring, translations (as translators) |

- `docs/chatddx.md`: "These roles are distinct and not overlapping, a person may inhabit more than one role."
- Nobody authors compilations and skeletons; the compiler writes them. A World's model facts are written by whoever
  adds a model they don't know.
- Ops also write the inventory (`docs/inventory.md`, "Terms").
- Translators are researchers (`agents/wip-translators-view.md`, T1); `docs/chatddx.md` names none.
- A person also stands to a thread or a family as its owner or a collaborator, and one person, the archive, owns what
  data sets load ("Terms": Owner, collaborator; Archive).
- Placeholder people in docs and tests are alice, bob, carol…, or semantic names (`AGENTS.md`, rule 6).

### The database
From `docs/store.md` ("Roles and connections"), verbatim. These are PostgreSQL roles, not people's: `admin` names both.

| Role | Used by | Created by | May |
| --- | --- | --- | --- |
| Admin | `chatddx migrate` and the tests. | Setup script. | Own the database and schemas; create databases and roles. |
| Writer | The app. | Setup script. | Read and add to factors, ledger and catalog; create, read and update people and the worker queue. |
| Reader | Nothing yet. | Tier 1. | Read the factors, the catalog and people, but not passwords. |

The reader can't read the ledger or sessions.

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

## Where the docs part
Gathering the glossaries puts these side by side. Nothing here is decided.

1. **Recipe.** `docs/chatddx.md`'s row, `docs/factors.md` ("Recipe and compilation") and the code
   (`src/chatddx/factors/request.py:Recipe.model`) say a recipe holds a model. `docs/factors.md`'s row says "the
   engine", and so does `docs/api.md`'s Parts, where `src/chatddx/api/schemas.py:Parts` has a model and no engine.
   - (a) The two rows go with their tables, and `docs/chatddx.md`'s stands.
   - (b) If the tables stay, a suggestion to each row: model for engine.
2. **Cell.** `docs/repl.md` defines the cell, and its "Saving" says what the cell holds, but `src/chatddx/repl/` has
   no cell any more; the shell holds a variation (`TriedVariation`).
   - (a) The row goes with its table, and a suggestion to "Saving": the variation for the cell.
   - (b) "Cell" stays the doc's word for what the shell holds, said as such.
3. **World.** `docs/chatddx.md`'s row: what is outside the orchestrator's control. `docs/inventory.md`'s row: a
   directory with an inventory. `docs/inventory.md` ("Worlds") reconciles them: a world is technically only what is
   beyond chatddx's control, and `worlds/*` also hold the data this repository carries for it, in `_` directories.
   - (a) Both rows stand, and `docs/inventory.md`'s says it is the directory, as "Worlds" does.
   - (b) `docs/chatddx.md`'s row only; the directory is described where it is, in `docs/inventory.md`.
4. **A finding's level.** `docs/ledger.md` ("Findings") says all of the ledger's findings are warnings, counting the
   runner's and the scoring pass's in the finish record among them, but `run.resumed` and `answer.salvaged` can be
   info ("Findings": Running, Scoring).
   - (a) A suggestion to `docs/ledger.md`: the checks' findings are warnings, and the finish record's either.
   - (b) The runner's and the scoring pass's become warnings.
5. **One word, two things.** In the gathered table only the Doc column tells them apart.
   - Admin: a person's role (identity) and the database's owner (store).
   - Closure: a component and what it references (store, and `docs/chatddx.md`'s Bundle), and a Nix closure
     (`docs/chatddx.md`'s World, `engine.closure`).
   - Configuration: a skeleton thread (catalog), and `configurations`, the handle a data set's configurations are made
     for (inventory).
   - Label: a scorer's view's or resource's name (catalog, bench), and a variation's short title (bench).
   - Record: what the rig writes (ledger, and `docs/chatddx.md`'s "Record / ledger"), and an entry of a data set's
     factors file (curation).
   - Stage: what a run and a score are logs of (`docs/chatddx.md`'s "Run and Score"), and a log's start or finish
     record (ledger).

   Options: (a) the gathered rows say which, by a qualifier in the term ("Record (ledger)"); (b) one of each pair is
   renamed, which is a human's choice of word.

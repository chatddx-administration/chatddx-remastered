# Glossary

The terms, the roles, and every finding the code makes, in one place. The terms were gathered from the glossaries
`docs/` used to hold, and reconciled against the code.

Every entry is one line that starts with a colon: `grep '^:Edge' docs/glossary.md` finds what an edge is, and
`grep ':Edge'` where it is used too, since an entry refers to another as `:Edge`. A word that names two things has an
entry for each, told apart in parentheses, so `grep '^:Item'` finds both. An entry ends with where the code holds it, if
anywhere.

- "Terms" holds one definition per term, true to the code.
- "Roles" holds the people's roles and what each authors.
- "Findings" holds every `Finding(…)` made in `src/chatddx/`, by where it is raised.

## Terms

:Active — Whether a person may sign in; making them inactive ends their sessions. People are made inactive, never
deleted. `src/chatddx/identity/identity.py:Person.active`

:Admin (database) — The database role that owns the database and its schemas, may create databases and roles, and runs
the migrations: `chatddx` in PostgreSQL, made by the setup script, used by `chatddx migrate` and the tests.
`src/chatddx/store/setup.sql`

:Answer — What an item's last response is read as, by its skeleton's contract: the answer tool's arguments, JSON
content, or text, or the JSON in it when the output has a schema. One cut short is salvaged, one that can't be read is
none, and one that breaks the output's schema is still an answer. A verdict is read the same way.
`src/chatddx/scorers/answer.py:Answer`

:Answer tool — A tool contract's function, offered last, whose call is the answer; no tool component, and never run.
`src/chatddx/factors/request.py:ToolOutput`

:Appendix — Extra plain text written for one vignette, sent with it by the cases that include it. Text cleanup doesn't
touch it. `src/chatddx/factors/cases.py:Appendix`

:Appendix layout — What goes before, between and after a case's appendices when they are joined into the one text that
fills the appendices slot; nothing when it has none. A recipe holds one and its skeleton keeps it, translated with the
other texts; a variation doesn't replace it. `src/chatddx/factors/request.py:AppendixLayout`

:Archive — The person who owns everything a data set loads, and shares it with each person a loading names. Never wiped.
`src/chatddx/curation/write.py:ARCHIVE`

:Attempt — One try at sending a call's request, kept with its times, status and error. A call is tried again only when
the request didn't get through: no connection, a 429 or a 5xx. `src/chatddx/ledger/call.py:Attempt`

:Attestation — What the engine says about itself in its responses, the model it answered as and the prompt it read, set
beside what was declared. `src/chatddx/ledger/call.py:attest_model`

:Base — The version a fork is compared with: the one it came from, or the origin's head it last followed.
`src/chatddx/catalog/model.py:Divergence.base`

:Beat — Marking a worker and its jobs as seen, and hearing whether each is to halt or its owner has paused.
`src/chatddx/store/queue.py:Queue.beat`

:Behind — A reference of a thread's head that a live thread has since moved on from, or a case whose family has a newer
binding. `src/chatddx/catalog/threads.py:behind`

:Bench — What one person sees and does, whatever the edge. `src/chatddx/bench/bench.py:Bench`

:Binding — Where a family's vignette is: source, id and fingerprint. The latest is current.
`src/chatddx/catalog/model.py:Binding`

:Bound — Of a data set's judge: given by the World the handle whose model it is made for when loaded, and whose latest
engine then judges it. `src/chatddx/inventory/inventory.py:Inventory.judges`

:Bundle — A set of root components plus everything they reference, stored as canonical text keyed by digest, together
with the code version that produced it, so it can be checked offline. `src/chatddx/factors/bundle.py:Bundle`

:Cage — The environment runs and scores happen in, which can be provably rebuilt from what was pinned, and delivered
with the results.

:Call — One exchange with an engine: a request sent, in one or more attempts, and what came back or why nothing did.
`src/chatddx/ledger/call.py:Call`

:Canary — A fixed, non-sensitive probe request, sent at a run's start or end to reveal an engine that changed.
`src/chatddx/factors/trial.py:Canary`

:Canary set — A fixed list of non-sensitive probe requests, each with its messages, options and optional seed, that a
run sends at its start, its end or both to show whether the engine changed. An instrument; a run takes its endpoint's.
`src/chatddx/factors/trial.py:CanarySet`

:Canonical form — The one way a component or a record is written out: JSON with field names sorted, fields equal to
their default left out (the kind kept), and the schema version added. JSON data keeps its key order, since a schema's
property order is part of what a model reads; settings' keys and other order that means nothing (a model's files, a
trial's cases, translations) are put in a fixed order, so equivalent components share a digest.
`src/chatddx/factors/base.py:Component.canonical_doc`

:Capacity — How many requests an endpoint takes at once: a run's concurrency may not go above it, and the worker's jobs
at the endpoint share it. `src/chatddx/inventory/inventory.py:EndpointSpec.capacity`

:Carrying — Editing an expectation onto another case of its family, with the same data. `src/chatddx/portal/threads.py`

:Case — A vignette plus the appendices sent with it, in order. `src/chatddx/factors/cases.py:Case`

:Chunk — A component that fills one of a recipe's nine chunk parts: instructions, few-shot, prompt, output, sampling,
reasoning, passthrough, translations or toolset. Not to be confused with a slot.
`src/chatddx/factors/request.py:CHUNK_PARTS`

:Chunk (streamed) — One piece of a response as it streams in. `src/chatddx/runner/wire.py:Chunk`

:Claim — Taking the next job that fits its endpoint's free slots, or one that is lost or is to halt, and marking it
under way. `src/chatddx/store/queue.py:Queue.claim`

:Cleared — An endpoint's permission, for now, to receive content from a sensitive source; without it, the gate refuses
runs and judge calls on that source's cases there. `src/chatddx/inventory/inventory.py:Inventory.cleared`

:Closure (components) — A set of components and everything they reference, transitively.
`src/chatddx/factors/bundle.py:Registry.closure`

:Closure (Nix) — The Nix store path a local engine's runtime runs from. `src/chatddx/factors/engine.py:Runtime.closure`

:Collaborates on — Has it shared with them, while it is live, and isn't its owner.
`src/chatddx/identity/identity.py:collaborates`

:Collapse — A level the model is asked for exactly as another, so the two are one request.
`src/chatddx/factors/facts.py:ReasoningFacts`

:Compilation — A provenance component that says which recipe, compiler and facts produced a skeleton, and the language
it was compiled into, none for the recipe as written. `src/chatddx/factors/request.py:Compilation`

:Compiling — Turning a recipe into a skeleton: working out what its intents send from the facts about its model,
carrying its texts into a language when asked, placing the guidance, and building the messages and the request's
options. The compiler is the chatddx code that did it, named in each compilation.
`src/chatddx/factors/request.py:compile_request`

:Completion — The slot a judge's skeleton must have, filled at send time with what a view picks from the answer it
grades. `src/chatddx/factors/request.py:SlotName`

:Component — An immutable set of parameters of one kind, identified by its digest and referring to other components by
theirs. Pinned factors are held in components; canary sets, facts and compilations are components but not factors.
`src/chatddx/factors/base.py:Component`

:Configuration — A skeleton thread: each version a skeleton, with the recipe it was compiled from unless written by
hand. `src/chatddx/bench/model.py:KINDS`

:Configurations (inventory) — The handle whose model a data set's configurations are made for when it is loaded.
`src/chatddx/inventory/inventory.py:Inventory.configurations`

:Contract — How an output, and the skeleton compiled from it, constrains the answer: native (the engine enforces the
schema), tool (the answer is a forced function call) or text (nothing is constrained).
`src/chatddx/factors/request.py:OutputContract`

:Curation — Loading a data set into the store as the archive's and sharing it, keeping it in step with its files and its
vignettes' sources, and taking back all a person owns. `src/chatddx/curation/`

:Cutoff — Ending a call early and keeping what came, with why as its error: a runaway of whitespace, or a timeout.
`src/chatddx/runner/send.py:send`

:Data set — A directory of authored files: factors, texts and cases by language, and the files they load. Its engines
are the World's. `src/chatddx/curation/plan.py:plan_factors`

:Deadline — How long a stopping worker's scorings go on before they are cut short and queued again.
`src/chatddx/settings.py:WORKER_DEADLINE`

:Default — The reasoning level a model uses when a request says nothing about reasoning. A reasoning chunk may ask for
it, and it lands like any other level. `src/chatddx/factors/facts.py:ReasoningFacts.default`

:Digest — The hash of a component's canonical form as stored, `sha256:<hex>`. Components are told apart and referred to
by it. `src/chatddx/factors/base.py:Component.digest`

:Edge — What a person reaches the bench through: the repl, the API, the portal, or a command acting as them.

:Edit — One version on a thread. Editing writes a new one on a thread of one's own, naming the head it was made on.
`src/chatddx/catalog/model.py:Edit`

:Endpoint — Where one engine is served, under the inventory's name for it: its address, the host that runs a local
engine, its capacity, the variable holding its secret, and the canary set and execution its runs default to.
`src/chatddx/inventory/inventory.py:EndpointSpec`

:Engine — What answers requests: a vLLM server we run, pinned by its hardware, runtime, weights, chat template and
arguments, or a remote API's model. Where it is reached is its endpoint. `src/chatddx/factors/engine.py:LocalEngine`

:Engine import — `chatddx import-engine`: reading o11n's reports of a host's vLLM servers, and writing each server's
model, engine, endpoint and host into a World, its model under the server's name as its handle. Its files are rewritten
whole, so they are changed by importing again. `src/chatddx/importers/o11n.py:imported`

:Entry — Something said about a thread, a family, a run or a score: a name, description, tag, owner, collaborator,
deleted flag, a family's language, or what a run varied, replaced and was started with.
`src/chatddx/catalog/model.py:Entry`

:Event — One message of a run's event stream: a record of its log as written, or what its worker says as it happens.
`src/chatddx/api/telling.py:Telling`

:Execution — How a run sends its items, and a score its judge calls: order, concurrency, timeout, retries and the
runaway cutoff. Recorded at the start, not pinned; the endpoint gives the default.
`src/chatddx/factors/trial.py:Execution`

:Expectation — The reference data for one case, written to an expectation schema, that a scorer's views grade answers
against. `src/chatddx/factors/scoring.py:Expectation`

:Expectation schema — A JSON Schema, in the draft it names (2020-12 if none), for the reference data a scorer grades
against. Expectations are written to it, and a scorer and its scoring's expectations name the same one.
`src/chatddx/factors/scoring.py:ExpectationSchema`

:Factor — Anything that can change an output or its score: what the research varies, holds fixed, or has to account for.
The package and the schema named for factors hold every component, factors or not.

:Facts — What is known about one model that a request doesn't say: its reasoning levels, recommended sampling, output
caveats and specs. Written by people in TOML, stored as a component on a thread per model, and read by compiling and by
lints; not a factor. `src/chatddx/factors/facts.py:ModelFacts`

:Family — What keeps one vignette together through renames and changes at its source; every case of the vignette belongs
to it. Shown and found by its name, or its vignette's `SOURCE/ID`. `src/chatddx/bench/model.py:Family`

:Few-shot — A chunk of example messages, each the user's or the assistant's, in plain text, sent after the instructions
and before the prompt. `src/chatddx/factors/request.py:FewShot`

:Fill rule — How a judge writes a view's picks into its completion and expectation slots. Fill rules are named and
versioned; the only one, `text@1`, writes a string as it is, strings one per line, and anything else as JSON.
`src/chatddx/factors/scoring.py:Judge.fill`

:Finding — non-catastrophic inconsistency discovered at start-up or runtime, see "Findings" below.

:Fingerprint — A hash of content that is not stored with the factors or the ledger: a vignette, a request, a prompt's
token ids. It names its algorithm: `sha256`, or `hmac-sha256` with the key's id.
`src/chatddx/factors/base.py:Fingerprint`

:Following — Keeping the proposal as an edit of the person's own fork, based on its origin's head.
`src/chatddx/bench/following.py:follow`

:Following its facts — Keeping a configuration's recipe, with its model's head, compiled against the facts as they are
now, as a new version of the person's own. `src/chatddx/bench/following.py:follow_moved`

:Fork — A thread started from a version of another thread of the same kind, its origin. Forking makes one of one's own
from any thread one sees. `src/chatddx/catalog/model.py:Thread.forked_from`

:Free parameters — Parameters a scorer gives the metrics of all its views, taken only where its code publishes a schema
for them; a view's own parameters override them. The shipped code takes none.
`src/chatddx/factors/scoring.py:Scorer.params`

:Gate — What refuses an endpoint or a judge before a run or a scoring uses it: another engine than the trial's, a
sensitive source not cleared, tools on a sensitive source, a judge that reads the case, an unset secret, or a server not
serving the model. `src/chatddx/runner/gate.py:bar`

:Giftbag — A person's own forks of the chunks, tools, skeletons and expectations a loading gives the archive.
`src/chatddx/curation/write.py:_Init.giftbag`

:Greedy — Sampling at a temperature of exactly 0. The settings that matter only when sampling are dropped, so equivalent
greedy chunks share a digest, and no seed is sent. `src/chatddx/factors/request.py:Skeleton.greedy`

:Guidance — Text that tells the model how to answer, an output's, which may show the schema, or how to use its tools, a
toolset's. `src/chatddx/factors/request.py:Output.guidance`

:Halt (job) — Asking a run's queued or running job to end at once: its calls are hung up and the run is finished
unscored, or its scoring stops. `src/chatddx/store/queue.py:Queue.halt`

:Handle — A model thread, by its name, by which researchers pick a model. Its head is the weights it holds now, and its
latest engine is the engine of the one endpoint that serves them; ops may put new weights under it.
`src/chatddx/bench/model.py:Handle`

:Hardware — The one GPU a local engine runs on, written into the engine: its name, compute capability, VRAM and driver
version. Another GPU makes another engine. `src/chatddx/factors/engine.py:Hardware`

:Head — A thread's latest edit, its current version. A variation is built on it unless an earlier edit is named.
`src/chatddx/catalog/threads.py:head`

:Host (inventory) — A machine that runs local engines: the address its servers listen on, and where it keeps the model
files and chat templates they pin. `src/chatddx/inventory/inventory.py:HostSpec`

:Include — A file of endpoints and hosts, as the engine import writes them, that an inventory takes as its own.
`src/chatddx/inventory/inventory.py:Inventory.load`

:Insert — A placeholder filled at compile time: the output's schema in its guidance, or the output's or the toolset's
guidance in the instructions or the prompt. Its text before and after appears only when what it inserts isn't empty.
`src/chatddx/factors/request.py:Insert`

:Instructions — A chunk that becomes the request's first message, as a system or a developer message, and may place the
output's and the toolset's guidance. Guidance nothing places is added after it.
`src/chatddx/factors/request.py:Instructions`

:Instrument — A component that measures without being a factor: canary sets. `src/chatddx/factors/trial.py:CanarySet`

:Intent — What a reasoning or sampling chunk asks of the model instead of setting it: a reasoning level, or the
recommended sampling, worked out from the facts about the recipe's model when the recipe is compiled.
`src/chatddx/factors/request.py:Reasoning.level`

:Inventory — The files that say where vignette sources, endpoints and hosts are, and for now which endpoints are cleared
for which sources, which handle each of a data set's judges is bound to, and which handle configurations are made for.
Ops write them; the engine import writes the endpoints and hosts. `src/chatddx/inventory/inventory.py:Inventory`

:Item (run) — One case's replicate in a run: the fingerprint of the vignette as read, its first call and each tool
round's. `src/chatddx/ledger/run.py:RunItem`

:Item (score) — How one view graded one run item, with the judge calls it took. `src/chatddx/ledger/score.py:ScoreItem`

:Item key — A case and a replicate's index, which identify an item of a run, and with a view an item of a score.
`src/chatddx/ledger/record.py:ItemKey`

:Job — A run queued for the worker, for its owner at its endpoint: to send and finish, then score when asked, or,
finished, to score again. `src/chatddx/store/queue.py:Job`

:Judge — An LLM a view asks to grade, whose verdicts a judged metric turns into a value: a judge skeleton, a model, its
own seeds and a fill rule. The scoring pins the engine it is sent to. `src/chatddx/factors/scoring.py:Judge`

:Kind — What a component is, written into it and read first: `engine.local`, `chunk.prompt` and the rest.
`src/chatddx/factors/kinds.py:KINDS`

:Label (scorer) — What an edit of a scorer thread calls one of its views or resources.
`src/chatddx/catalog/read.py:labels`

:Label (variation) — A variation's short title, `NAME+PART=CHUNK`, which names its runs.
`src/chatddx/bench/variation.py:TriedVariation.label`

:Land — Where a level ends after its collapses and nearests: on a way of asking, a refusal, or nothing known. Only a way
of asking compiles. `src/chatddx/factors/facts.py:Landing`

:Language — The tag, such as `sv` or `pt-BR`, of what is sent to a model; the model is never told it. A text or a
hand-written skeleton holds its own, and a case's is said of its family; a compiled skeleton, and so a run, is in the
language it was compiled into, else the one its recipe's texts share. `src/chatddx/factors/base.py:Language`

:Latest wins — Of the rows about one thing, the one written last holds; for tags and collaborators, the last about each.
`src/chatddx/catalog/model.py:About.of`

:Ledger — All records: the logs of every run and every score. `src/chatddx/ledger/`

:Left out — The cases of a language a configuration's translations can't carry it into, because they don't go into it or
leave a text untranslated. Said with why, and not sent. `src/chatddx/bench/model.py:Started.left_out`

:Left to score — A scorer that applies to a finished run, with an expectation for some of its cases, and no whole score
of the run under the scoring built now. `src/chatddx/bench/seen.py:Seen.unscored`

:Leftover — An archive thread or family a loading didn't come to, as when the data set no longer names it. Listed, never
deleted. `src/chatddx/curation/write.py:_Init.leftovers`

:Level (finding) — How much a finding weighs: a warning, or an info. `src/chatddx/factors/base.py:Finding.level`

:Level (reasoning) — What a reasoning chunk asks of reasoning: off, on, minimal, low, medium, high or xhigh, or the
model's default. The facts say how each is asked for; a request carries only what it lands on.
`src/chatddx/factors/facts.py:Level`

:Lint — A check, made when asked, of a component against the components it references and the facts about its model. It
gives warnings or infos that nothing stores, and no write refuses on one. `src/chatddx/factors/lint.py:lint`

:Live — Not deleted. A deleted thread, family, run or score is still stored, but nobody owns it, collaborates on it or
finds it by name until an entry restores it. `src/chatddx/identity/identity.py:owns`

:Loading — One run of `chatddx init-data`: planning a data set with its World's engines and facts, writing it into the
store as the archive's, sharing it with the person it names, then linting it and checking the World. Running it again
loads the changes. `src/chatddx/curation/write.py:init`

:Location — Where a host keeps a model or a chat template, written the way vLLM on the host reads it.
`src/chatddx/inventory/inventory.py:HostSpec`

:Log — A run or a score as written: a start record, a record per item (and, for a run, per canary call), and once it is
done a finish record. Only ever added to. `src/chatddx/ledger/record.py:Log`

:Login — What a person signs in with, and is named by when shared with or acted as. Unique and lowercase.
`src/chatddx/identity/identity.py:Person.login`

:Look — Asking for a configuration's variation with nothing stored: its parts, the request it would send, the handle it
runs under or why it can't run, its lints, the languages its cases are sent in and its reach.
`src/chatddx/api/threads.py`

:Lost — A job under way that its worker hasn't beaten for a while, so a claim takes it.
`src/chatddx/store/queue.py:Queue.claim`

:Metric — A measure the scorer's code publishes and a view names: what it measures, the parameters a view may give it,
whether it reads a judge's verdicts, and its unit. Given a view's picks, it gives a value, or none, and a detail.
`src/chatddx/scorers/scorer.py:Metric`

:Migration — A file of SQL, at a tier, that a deployment applies once when it migrates to that tier or above.
`src/chatddx/store/migrate.py:Migration`

:Model — What an engine serves and a recipe or a judge picks, by digest: a local model, weights pinned by repository,
revision and the hash of every file, or a remote model, a provider's model by name. Its name keys its facts.
`src/chatddx/factors/engine.py:LocalModel`

:Nearest — The level a refused level is asked for instead, when its refusal names one. Landing goes on from it.
`src/chatddx/factors/facts.py:Refusal.nearest`

:No target — Why a view gives a case no value: its expectation gives the view nothing to hold an answer to, or there is
none. `src/chatddx/scorers/scorer.py:NO_TARGET`

:Origin — The thread a fork was started from, of the same kind. The fork's base is one of its versions, and following
brings the fork onto its head. `src/chatddx/catalog/threads.py:origin`

:Output (answer) — What a model wrote for an item, which a view picks from. `src/chatddx/ledger/run.py:RunItem`

:Output (chunk) — A chunk that says what shape the answer has and how it is enforced: a contract, a schema (needed
unless the contract is text), guidance that may show the schema, and schema ops. `src/chatddx/factors/request.py:Output`

:Own language — A configuration's language: the one its recipe's texts are all written in, or a hand-written skeleton's.
Cases in it, or in none, are sent as written. `src/chatddx/catalog/language.py:recipe_language`

:Owner, collaborator — Who a thread, family, run or score belongs to, and who it is shared with. Together they decide
what a person sees. `src/chatddx/catalog/model.py:About`

:Owns — Is the owner of, while it is live. `src/chatddx/identity/identity.py:owns`

:Parts — The chunks and the model a variation replaces over a configuration, each by its digest. An empty chunk takes an
optional part out; the model can't be taken out. `src/chatddx/api/schemas.py:Parts`

:Passthrough — A chunk of request options no other chunk covers, sent as written. It may not set what is set at send
time, by the output's contract or the tools, by sampling or reasoning, or what goes around other factors.
`src/chatddx/factors/request.py:Passthrough`

:Person — Someone who acts in chatddx, by an id the rest of the store refers to, with a login, a name, roles, and
whether they are active. `src/chatddx/identity/identity.py:Person`

:Phase — When a run sends its canaries: at its start, before the first item, or at its end, after the last; both unless
its start record names one. `src/chatddx/ledger/run.py:Phase`

:Pinned — Fixed in advance inside a component, so that changing it changes that component's digest and the digest of
every component that refers to it.

:Pinned, recorded, observed — The three ways a factor is held: fixed in advance by digest, written into a run's or a
score's start record, or only detected afterwards. `src/chatddx/ledger/run.py:RunStarted`

:Plan, conduct, observation — What a start or an item record holds: what the run or score was set to do, what the rig
did, and what the world answered. A finish record holds its seal and findings. `src/chatddx/ledger/run.py:RunStarted`

:Portal — The web interface where people write and version their components, review cases, and start, watch, score and
compare runs; the bench's third edge. It is to export results, which isn't built. `src/chatddx/portal/app.py:app`

:Prompt (chunk) — A chunk that becomes the request's last message, the user's: literal text, slots, and the guidance
where it places it. Its purpose decides which slots it may and must hold, and matches the recipe's.
`src/chatddx/factors/request.py:Prompt`

:Prompt (read) — Everything the engine reads for a request, as its chat template renders it; a call keeps its token ids'
fingerprint. `src/chatddx/ledger/call.py:Call.prompt_tokens`

:Proposal — When the origin has moved on, its head with a fork's changes on top.
`src/chatddx/catalog/threads.py:proposal`

:Provenance — A component that says how another was made, without being a factor: compilations.
`src/chatddx/factors/request.py:Compilation`

:Purpose — Whether a prompt, a recipe or a skeleton writes an answer (generation) or grades one (judge). It decides
which slots are allowed and which are required. `src/chatddx/factors/request.py:Purpose`

:Reach — Of a scorer's view: whether a variation's output offers what it reads, and which cases have an expectation of
the person's own it picks from, none, or several to choose from. `src/chatddx/bench/model.py:Reach`

:Reader — The database role that may read the factors, the catalog and people, and not passwords, sessions, the ledger,
typed vignettes or the queue; nothing connects as it yet. `chatddx_reader` in PostgreSQL, made at tier 1.
`src/chatddx/store/migrations/0002-t1-factor.sql`

:Reasoning — A chunk that sets how the model reasons: an effort, a thinking-token budget and chat-template arguments, or
a reasoning level, worked out from the facts, with at most a budget beside it. A recipe without one leaves reasoning to
the model. `src/chatddx/factors/request.py:Reasoning`

:Recipe — The chunks, purpose, appendix layout and model a skeleton is compiled from. Not a component: it is kept in its
compilations. `src/chatddx/factors/request.py:Recipe`

:Recommended sampling — The sampling a model's makers recommend for a reasoning level, as the facts hold it; a sampling
chunk may ask for it. `src/chatddx/factors/facts.py:SamplingFacts.recommended`

:Record — What the rig writes as a run or a score goes, its start, each item or canary call, and its finish; never
changed. `src/chatddx/ledger/record.py:Record`

:Refusal — A fact that says the model can't be asked for a level, a thinking budget or an output contract, and why.
`src/chatddx/factors/facts.py:Refusal`

:Repair — Moving a family to its vignette's new id or content: its cases rebuilt, its appendix threads moved, and on a
rename its expectation threads. `src/chatddx/catalog/families.py:plan_repair`

:Repl, shell — `chatddx repl`, a shell for one person over a World. `src/chatddx/repl/shell.py:Repl`

:Replacement — The case a stale case becomes under its family's current binding: the same appendices on the current
vignette. `src/chatddx/catalog/families.py:replacement`

:Replicate — One seed of a trial, identified by that seed's position in the trial.
`src/chatddx/ledger/record.py:ItemKey.replicate`

:Request — The body one call sends to an engine: a skeleton rendered with its fills, the model and the seed, a tool
round's next request, or a canary. `src/chatddx/factors/request.py:Skeleton.render`

:Resource — A string a scorer holds, in order and labelled by position, such as the name of a synonym table or an
ontology release. No kind of component holds one, and the scoring code isn't given them (`docs/backlog.md`, "Shipped
code: scorers and tools"). `src/chatddx/factors/scoring.py:Scorer.resources`

:Rig — The chatddx software that builds cages from factors, runs and scores inside them and records what happened, which
build of it included. `src/chatddx/rig.py:rig`

:Role (person) — Admin, clinician, developer, ops or researcher; a person may hold several, and nothing checks one yet.
`src/chatddx/identity/identity.py:Role`

:Runner — What starts or resumes a run at an endpoint, sends its items and canaries, runs its tools, and writes the run.
`src/chatddx/runner/run.py:Runner`

:Runtime — What a local engine's vLLM runs from, written into the engine: the server, its version, and the Nix closure
it is started from. `src/chatddx/factors/engine.py:Runtime`

:Salvaged — A structured answer cut short, read with its structure closed.
`src/chatddx/scorers/answer.py:Answer.salvaged`

:Sampling — A chunk that sets how the engine samples and how long the answer may be: temperature and the other sampler
settings, penalties, stop strings and a cap on output tokens; or it asks for the recommended sampling, with any value
set beside it winning. Every recipe has one. `src/chatddx/factors/request.py:Sampling`

:Saying — The owner writing what holds of a thread or a family: its name, description, tags, collaborators and whether
it is deleted, and a family's language; a family's tags and language are said by those it is shared with too.
`src/chatddx/bench/saying.py:say`

:Schema (database) — One namespace of the database's tables: factor, ledger, identity, catalog, source (typed vignettes)
or worker (the queue). `src/chatddx/store/migrations/`

:Schema op — A named, versioned rewrite an output chunk applies to its schema at compile time, so the skeleton sends and
shows the rewritten schema. Today the only one is `inline_refs@1`. `src/chatddx/factors/request.py:SchemaOp`

:Score — One scoring of a finished run, written as a log: what it was set to do, how each view graded each run item, and
its finish. `src/chatddx/ledger/score.py:Score`

:Scorer — A component that names the scoring code chatddx ships and the version of it it pins, the expectation schema it
grades against, its views, its resources and its free parameters. `src/chatddx/factors/scoring.py:Scorer`

:Scoring — What a score applies: a scorer, the expectations it grades against, at most one per case, and the engine each
of its judges is sent to. Built when a run is scored, not written by hand. `src/chatddx/factors/scoring.py:Scoring`

:Scoring pass — What grades a finished run with a scoring, asking a view's judge where it names one, and writes the
score. `src/chatddx/runner/score.py:grade`

:Script — The turns the fake answers with, one per request it accepts, so one per attempt.
`src/chatddx/fake_vllm/script.py:Script`

:Scripted run — A run made to be looked at, described by a file in a World's `_runs/` and answered by the fake from its
script. `src/chatddx/scripted/read.py:ScriptedRun`

:Seal — The hash over a log's records but its finish record, kept in the finish record.
`src/chatddx/ledger/record.py:seal_rows`

:Secret — The key an endpoint asks for, sent as a bearer token with every request to it. The inventory names only the
variable holding it, the endpoint's credential; the gate refuses an endpoint whose variable isn't set, and nothing
stored holds it. `src/chatddx/inventory/inventory.py:EndpointSpec.credential`

:Seed — A number that fixes the sampler's randomness, not sent when sampling is greedy. Each seed of a trial is one
replicate, and a greedy trial's seeds are its replicates' positions, from 0, since none is sent; a judge's seeds and an
execution's shuffle seed are not. `src/chatddx/factors/trial.py:Trial.seeds`

:Sees — Owns or collaborates on; a run only when one owns it. `src/chatddx/identity/identity.py:sees`

:Segment — One piece of a message: a literal string or a slot. A prompt's pieces may also be inserts, which compiling
fills. `src/chatddx/factors/request.py:Segment`

:Selector — What picks the values a view compares from an answer or an expectation: a JSON Pointer, or a JSONPath query
from a fixed subset, in the document's order. The empty one picks the whole document.
`src/chatddx/factors/scoring.py:Selector`

:Sensitive — Content that may go only where it is cleared to go: a source's vignettes, unless the source says otherwise,
and everything made from them. Today only sending to an endpoint is checked. `src/chatddx/runner/gate.py:bar`

:Served model name — The name a request asks an engine for and the engine answers as: for a local engine its own digest,
so each response names the exact engine; for a remote engine its model's name.
`src/chatddx/factors/engine.py:served_model_name`

:Session — A person signed in: a token, carried as a bearer or a cookie, of which only a digest is kept. It lasts 12
hours, or until they sign out or are made inactive. `src/chatddx/store/people.py:People.open_session`

:Skeleton — What trials and judges reference: everything a request sends but the slots' fills, the model and the seed.
Compiled from a recipe, or written by hand. `src/chatddx/factors/request.py:Skeleton`

:Slot — A placeholder filled at send time: the vignette, the appendices, the completion or the expectation.
`src/chatddx/factors/request.py:Slot`

:Slots — What a job holds of its endpoint's capacity while under way: its run's concurrency. A scoring alone holds none.
`src/chatddx/store/queue.py:Job.slots`

:Source — Where a set of vignettes is fetched from, by id: a directory, or texts people typed, kept in the database. Its
name is part of every case built from it, and it is sensitive unless it says otherwise.
`src/chatddx/inventory/sources.py:Source`

:Split — How a view breaks what it picks from an output into items before they are compared. Splits are named and
versioned; the only one, `lines@1`, takes the lines of a list without their markers. An expectation's pick is never
split. `src/chatddx/factors/select.py:SplitOp`

:Stage — A log's start or finish record. `src/chatddx/ledger/record.py:Stage`

:Stand-in — The fake vLLM serving a remote engine's model on this machine, at the remote endpoint's address.
`src/chatddx/scripted/fakes.py:fake_at`

:Stanza — A named table of a data set's factors or texts files, or of a World's engines files, such as `[prompt.plan]`,
loaded as a thread. `src/chatddx/curation/plan.py:Planned`

:Start-up — What starting a local engine's endpoint takes: vLLM's arguments, the engine's environment and the runtime,
joining the engine with where its host keeps what it pins. `src/chatddx/inventory/serving.py:StartUp`

:Stop, interrupt, halt (runner) — Ending a run: after the items under way; at once, recording the calls under way as
stopped and raising; or at once from another thread, returning. `src/chatddx/runner/run.py:Running.stop`

:Subject — The thread, family, run or score an entry is about. `src/chatddx/catalog/model.py:Subject`

:Survey — Comparing what a source lists with where its families are bound: unchanged, changed, renamed, new or gone.
`src/chatddx/catalog/families.py:survey`

:Taking — Forking an expectation shared with the person into a thread of their own, so that it counts.
`src/chatddx/bench/taking.py:take`

:Text — A chunk that holds what the model reads: instructions, few-shot examples, a prompt, an output or a toolset,
written in one language; in a data set, the one its texts file is named for. `src/chatddx/curation/plan.py:TEXT_TABLES`

:Text (translated) — One string the model reads, as a translations chunk maps it. `src/chatddx/factors/request.py:texts`

:Text cleanup — The named, versioned steps a trial applies to its vignettes after fingerprinting and before sending; a
source names the default ones. `src/chatddx/factors/cases.py:CleanupOp`

:Thread — A sequence of components of one kind that people edit, its versions in the order they were saved.
`src/chatddx/catalog/model.py:Thread`

:Tier — How much integrity the database enforces: structure, then grants, then checks and triggers that repeat the rules
held in Python and keep tables append-only. `src/chatddx/store/migrate.py:TOP_TIER`

:Title — How something without a name is shown, built when asked and never stored: for a fork, its origin's title and
what it varies; else a name it had earlier; else what it holds. `src/chatddx/catalog/titles.py:title`

:To choose from — A case with several expectations under one schema where one is needed: several of the person's own
that differ, or several shared with them to take. `src/chatddx/bench/seen.py:choices`

:Tool — A function the model may call between rounds: a name, a description, a JSON Schema for its parameters, and the
shipped code that runs it, pinned by entry point and version. Not a chunk; a toolset offers it.
`src/chatddx/factors/request.py:Tool`

:Tool round — Running the tools a response called, and sending their results in the next request. A round stopped while
its tools run has no request. `src/chatddx/ledger/call.py:Turn`

:Toolset — A chunk that offers tools: one or more, with distinct names, plain-text guidance on using them, and the most
tool rounds an item may take, five unless set. `src/chatddx/factors/request.py:Toolset`

:Translated — A run whose skeleton is its configuration's recipe compiled into its cases' language through the recipe's
translations. `src/chatddx/bench/model.py:Carried.translated`

:Translations — A chunk that maps each text a recipe's other chunks and appendix layout hold to its translation, for
each language it goes into; cases and appendices aren't translated. In a data set it is written in the texts file of
each such language. `src/chatddx/factors/request.py:Translations`

:Trial — One experimental condition, the smallest unit of a scientific intent: a generation skeleton, an engine, cases,
text-cleanup steps and seeds. `src/chatddx/factors/trial.py:Trial`

:Typed case — A case whose vignette is a text the person typed, kept in a database source, with a family of their own in
the language they say. `src/chatddx/bench/cases.py:type_case`

:Variation — A version of a configuration with recipe parts replaced over it, or none, as it is tried before anyone
keeps it as a fork or a new version. `src/chatddx/bench/variation.py:TriedVariation`

:Varies — Of a fork: what its head changes from its base. `src/chatddx/catalog/model.py:Divergence.varies`

:Verdict — A judge's answer for one seed, as its skeleton's contract reads it, or none when it can't be read.
`src/chatddx/runner/score.py:Grading`

:Vetted — Cleared by a person to receive sensitive content: today an endpoint in the inventory's clearance table, later
what the planned clearance pipeline grants.

:View — One comparison a scorer makes: what it picks from an output and from an expectation, how the output's pick is
split, and the metric, with its parameters and its judge if any, that grades them. `src/chatddx/factors/scoring.py:View`

:Vignette — The clinical text a source holds under one id, named by the source, the id and a fingerprint of its bytes.
Sensitive unless its source says otherwise. `src/chatddx/factors/cases.py:Vignette`

:Whole score — A score of a run that finished, with an item for every run item under every view, and no judge call
stopped. `src/chatddx/bench/seen.py:Seen._whole`

:Wire-body — A request as it goes over the wire: the rendered request plus the streaming options, sent with the
endpoint's secret in a header. May hold sensitive content. `src/chatddx/runner/send.py`

:Word — What a kind of thread is asked for by: configuration, each chunk part, model, engine and the rest.
`src/chatddx/bench/model.py:KINDS`

:Worker — What claims queued jobs and works them, each on a thread, in a process of its own or the app's.
`src/chatddx/worker/worker.py:Worker`

:world — What lies outside chatddx's control: vignette sources, model files, the Nix closure, the chat-template file, a
remote engine. Its factors are observed, or imported by fingerprint.

:World — The directory that describes one deployment's world: an inventory, the engines and model facts it adds, and the
data carried with it. `src/chatddx/inventory/world.py:World`

:Writer — The database role the app connects as: it reads and adds, updates only people, their passwords and the
worker's queue, and deletes only sessions. `chatddx_writer` in PostgreSQL, made by the setup script, or at tier 1 when
missing. `src/chatddx/store/setup.sql`

## Roles

### People

The roles live in code (`src/chatddx/identity/identity.py:Role`) and are stored on the person by name; a person may hold
several, and nothing checks a role yet.

:Admin (person) — Not mentioned; identity's own, for administering people. Principal author of nothing.

:Clinician — "Owners of vignettes and authors of Appendices and Expectations". Principal author of case, appendix,
expectation.

:Developer — "Authors of schemas, canary sets, scoring and text-cleanup functions". Principal author of tool, model
facts (the bundled ones), expectation schema, scorer (its scoring code), canary sets.

:Ops — "Owners of engines and authors of the engine's components". Principal author of local model, local engine, remote
engine.

:Researcher — "Authors of Sampling, Judges and Trials, and of a scorer's views, free parameters and labels". Principal
author of instructions, few-shot, prompt, output, sampling, reasoning, passthrough, toolset, recipe, trial, scorer (its
views, free parameters, labels and resources; picks its code and expectation schema), judge (its skeleton and seeds;
picks its model by handle and its fill rule), scoring, translations (as translators).

- Nobody authors compilations, and skeletons are compiled but for a hand-written configuration's. A World's model facts
  are written by whoever adds a model they don't know.
- Ops write the inventory, but for the endpoints and hosts the engine import writes (:Inventory).
- Translators are researchers.
- A person also stands to a thread, a family, a run or a score as its owner or a collaborator, and one person, the
  archive, owns what data sets load (:Owner, collaborator; :Archive).

- Placeholder people in docs and tests are alice, bob, carol…, or semantic names (`AGENTS.md`, "Documentation").

### The database

PostgreSQL's roles, not people's: :Admin (database), :Writer and :Reader. "Admin" names a person's role too.

## Findings

A finding (`src/chatddx/factors/base.py:Finding`) has a level, `warning` unless said, a code, a message and optionally a
subject; one made with `Finding.of` keeps its message as written and what fills it too, which the portal says in the
reader's language by its code.

### Lints

A component's checks against the components it references, made by `src/chatddx/factors/lint.py` and, with the facts,
`src/chatddx/facts/lint.py`. Raised by a look (`src/chatddx/bench/seen.py:Seen.findings`), a written edit
(`src/chatddx/bench/seen.py:linted`), checking a component (`src/chatddx/bench/components.py:check`), a loading
(`src/chatddx/curation/write.py:_Init.lint`) and, `src/chatddx/factors/lint.py` only, an o11n import
(`src/chatddx/importers/o11n.py:imported`). A judge is linted on its handle's latest engine, and on none where it can't
judge.

:model.revision — Its revision isn't a commit, so it can move. (warning; local model)

:engine.closure — Its runtime's closure isn't a Nix store path. (warning; local engine)

:view.unreachable — A view picks from the expectation what its schema doesn't have. (warning; scorer)

:expectation_schema.invalid — Its `$schema` names no draft that can be checked, or it breaks its draft. (warning;
expectation schema)

:output.schema_invalid — Its JSON schema names no draft that can be checked, or breaks its draft. (warning; output)

:expectation.unchecked — A `$ref` in its schema can't be resolved. (warning; expectation)

:expectation.invalid — Its data breaks its schema. (warning; expectation)

:schema.ref_unverified — The constrained answer's schema, or a tool's parameters, hold `$ref`, on an engine other than
vLLM 0.24. (warning; trial, judge)

:vllm.temperature_clamped — A temperature above 0 and below 0.01, which vLLM 0.24 raises to 0.01. (warning; trial,
judge)

:vllm.thinking_budget_refused — `thinking_token_budget` on a vLLM 0.24 without `--reasoning-parser` or
`--reasoning-config`. (warning; trial, judge)

:vllm.tools_refused — Tools on a vLLM 0.24 without `--enable-auto-tool-choice` and `--tool-call-parser`. (warning;
trial, judge)

:vllm.native_tools_uncallable — A native contract with tools: vLLM 0.24 constrains the whole answer, so no tool can be
called. (warning; trial, judge)

:vllm.grammar_before_reasoning — A constrained answer on a vLLM 0.24 without `--reasoning-parser`, so the model can't
reason first. (warning, or info when the request isn't known to reason; trial, judge)

:language.unknown — The request's language, or some cases', is unknown. (info; trial)

:language.mixed — Cases in another language than the request's. (warning; trial)

:trial.engine_unmatched — The skeleton was worked out from the facts about another model than the engine serves.
(warning; trial)

:judge.model_unmatched — The skeleton was worked out from the facts about another model than the judge's. (warning;
judge)

:judge.greedy_seeds — A greedy judge with several seeds, which send the same request. (warning; judge)

:facts.missing — No facts about the model, so the model's checks are skipped. (info; trial, judge)

:facts.reasoning_unmatched — The reasoning settings match none of the model's reasoning levels. (warning; trial, judge)

:facts.budget_refused — `thinking_token_budget` on a model whose facts refuse a budget. (warning; trial, judge)

:facts.output_refused — The model's facts refuse the skeleton's contract. (warning; trial, judge)

:facts.output_note — The model's facts note a caveat on the skeleton's contract. (info; trial, judge)

:facts.sampling_unmatched — The sampling is what the facts recommend for other models, not this one. (warning; trial,
judge)

### Looking at translations

Raised by a look (`src/chatddx/bench/seen.py:missing`).

:translations.missing — A language its translations go into that doesn't compile, though no case it is tried on is in
it. (warning; configuration)

### The inventory

Raised at the end of `chatddx init-data` (`src/chatddx/cli.py`) and of an o11n import
(`src/chatddx/importers/o11n.py:checked`), by `src/chatddx/inventory/check.py:check`.

:endpoint.engine_unknown — Its engine isn't known. (warning; endpoint)

:endpoint.not_engine — Its engine's digest is another kind of component. (warning; endpoint)

:endpoint.unstartable — Its start-up can't be made from the inventory. (warning; endpoint)

:endpoint.remote_host — It serves a remote engine and names a host. (warning; endpoint)

:endpoint.shared_url — Another local endpoint has its address. (warning; endpoint)

:host.unpinned — It says where it keeps a model or chat template that none of its endpoints' engines pins. (info; host)

:cleared.not_sensitive — It is cleared for a source that isn't sensitive. (info; endpoint)

### An o11n import

Raised for each server imported (`src/chatddx/importers/o11n.py:imported`), the chat template checked by
`src/chatddx/factors/engine.py:check_chat_template`. Every subject is the local engine.

:engine.chat_template — The chat template doesn't match the declared digest. (warning; local engine)

:engine.chat_template_date — The chat template reads the current date. (warning; local engine)

:engine.chat_template_unused — vLLM renders the model with Harmony and doesn't read the chat template. (info; local
engine)

:engine.harmony_date — Harmony writes the date into every prompt, and `VLLM_SYSTEM_START_DATE` isn't set. (warning;
local engine)

:engine.chat_template_unread — The report has no template text. (info; local engine)

:engine.chat_template_not_the_model_s — The chat template isn't the model's own at this revision. (info; local engine)

:endpoint.process — The server's process wasn't seen. (warning; local engine)

:endpoint.not_running — The server isn't running. (warning; local engine)

:endpoint.argv — The running server's argv isn't the configured one. (warning; local engine)

:endpoint.unreachable — The server didn't answer. (warning; local engine)

:endpoint.version — The server's vLLM version isn't its package's. (warning; local engine)

:endpoint.served_name — The server doesn't answer as the engine's digest. (warning; local engine)

### Loading a bundle

Raised by `src/chatddx/factors/bundle.py:Bundle.load`.

:bundle.recanonicalized — The running code serializes the component differently from its stored text. (warning;
component)

### Running

Noted by the runner as it works, and kept in the run's finish record (`src/chatddx/runner/run.py`,
`src/chatddx/factors/cases.py:prepare_case`).

:run.resumed — The run was resumed. (warning when another build of the rig resumes it than started it, else info)

:case.unreadable — The item's case can't be prepared. (warning; item)

:case.drift — The vignette at the source differs from the case's. (warning; case)

### Scoring

Noted by the scoring pass as it works, and kept in the score's finish record (`src/chatddx/runner/score.py`).

:answer.salvaged — The answer was cut short, and read with its structure closed. (info; item)

:answer.unread — The answer can't be read. (warning; item)

:answer.invalid — The answer was read and breaks its schema. (warning; item)

:verdict.unread — A judge's verdict can't be read. (warning; item)

:verdict.invalid — A judge's verdict was read and breaks its schema. (warning; item)

### Checking a run

Raised by `src/chatddx/ledger/run.py:check_run`, with `src/chatddx/ledger/call.py` and
`src/chatddx/ledger/record.py:check_seal`, when a run finishes and when the API shows a run or tells that it finished;
repeatable, so never stored.

:ledger.seal — Rows changed after the log was sealed. (warning; run)

:run.incomplete — A finished run lacks items or canary calls. (warning)

:case.drift — The vignette read differs from the case's. (warning; item)

:call.failed — Its last call ended with an error. (warning; item, canary call)

:tools.stopped — A round stopped before its tool calls had all run. (warning; item)

:tools.unanswered — The last response still calls tools after the last round. (warning; item)

:tools.code — The tool's code ran at another version than it pins, or isn't recorded. (warning; tool)

:attestation.model — The engine answered as another model than declared, or as none. (warning; item)

:attestation.prompt_tokens — Items without a prompt token fingerprint. (warning)

:execution.timeout — Attempts took longer than the execution's timeout. (warning)

:execution.retries — Calls took more attempts than allowed. (warning)

:execution.order — Items were sent before items scheduled ahead of them. (warning)

:execution.concurrency — More calls were in flight at once than declared. (warning)

:canary.phase — Start canary calls hadn't finished when the first item was sent, or end canary calls started before the
last item call finished. (warning)

### Checking a score

Raised by `src/chatddx/ledger/score.py:check_score`, with `src/chatddx/ledger/call.py` and
`src/chatddx/ledger/record.py:check_seal`, when a scoring pass finishes; repeatable, so never stored.

:view.unreachable — A view picks from the output what the run's output schema doesn't have. (warning; scorer)

:judge.incomplete — A view's value rests on fewer of its judge's seeds than declared. (warning; item)

:attestation.model — The judge engine answered as another model than declared, or as none. (warning; item)

:score.scorer_code — The scorer's code ran at another version than it pins. (warning; score)

:score.run_unfinished — The run hasn't finished, or the score started before it did. (warning; score)

:ledger.seal — Rows changed after the log was sealed. (warning; score)

:score.no_expectation — Some of the run's cases have no expectation in the scoring. (warning; score)

:score.incomplete — A finished score lacks items. (warning)

:execution.timeout — Judge calls' attempts took longer than the execution's timeout. (warning)

:execution.retries — Judge calls took more attempts than allowed. (warning)

:execution.order — Items' judge calls were sent before those of items scheduled ahead of them. (warning)

:execution.concurrency — More judge calls were in flight at once than declared. (warning)

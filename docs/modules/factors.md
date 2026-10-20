# Factors

An LLM can be given a case vignette in countless ways. The instructions, the sampling settings, the GPU, the model
weights and many other choices all affect what comes out. Varying each choice on its own is impractical, so we group
them into a manageable number of categories. We call these categories factors.

There is a catch-22: grouping well requires knowing _how_ each choice affects the output, and that is exactly what the
research is trying to find out. So we start from a flexible set of factors based on reasonable guesses and refine it as
we learn.

Factors are the building blocks of the chatddx rig: an environment that can be rebuilt exactly, and shown to be the
same, for scientific rigor. This document describes what each factor is for and how factors combine. Names, fields, and
errors are in docs/reference/factors.md.

Factors depend on nothing else in chatddx; the model facts, the catalog, the ledger and the store build on them.
Principal authors are the roles in docs/modules/identity.md.

## What a factor is

A _factor_ is anything that can change an output or its score: what the research varies, holds fixed, or has to account
for.

A _component_ is how most factors are stored: an immutable set of parameters identified by a hash of its content, its
_digest_. Changing a parameter gives a new component with a new digest; nothing is edited in place. Components refer to
each other by digest, so a trial's digest pins every component the trial depends on.

Being a factor and being a component are separate questions. A factor is held in one of three ways.

1. **Pinned**: chosen in advance and fixed by digest: a trial or a scoring, and every component it references. Prompts,
   sampling, engines, model weights, cases, seeds, expectations and scorers are pinned.
2. **Recorded**: set or known when a run or a score starts, and written into its start record, which is sealed with the
   rest of its log (docs/modules/ledger.md): the execution settings (see "Execution"), the version of the rig that sent
   the requests, and the scorer code that actually ran. Set beside the code the scorer pins, the last shows whether what
   ran is what should have run, and checking a score warns when they differ.
3. **Observed**: set by nobody, and only detected afterwards. These are the parts of the world outside our control: a
   remote engine that changes without notice, a tool such as a web search that answers differently from day to day, a
   vignette edited at its source, GPU arithmetic that isn't deterministic. Fingerprints, returned model names, drift
   findings and canaries reveal them (docs/modules/ledger.md, "Findings").

A trial's outputs therefore depend on the trial's pinned factors and on its run's recorded and observed factors. Two
runs of the same trial are interchangeable only when those agree too (docs/backlog.md, "Aggregation").

### Not factors

- Records of what happened (runs, scores, calls): [docs/modules/ledger.md]. They hold the recorded factors and the
  evidence of the observed ones, but they aren't factors themselves.
- People, roles, authentication and authorization: [docs/modules/identity.md].
- Names, labels, languages, tags, descriptions, owners, collaborators and version history: [docs/modules/catalog.md].
- Sensitivity and vetting: [agents/wip-clearance.md].
- Facts from model cards: [docs/modules/facts.md].
- Inventory: [docs/modules/inventory.md].
- Knowledge about models (reasoning levels, recommended sampling, output caveats, specs): the model facts
  (docs/modules/facts.md). Facts work out what a recipe's intents send when it is compiled, and check skeletons against
  engines; the skeleton holds what they did, so no factor's digest depends on them (see "Components but not factors").

#### Components but not factors

Most components are factors, these are the exceptions:

- Canary sets are _instruments_: fixed probe requests that measure observed factors without changing any output (see
  "Canary sets").

- Compilations are _provenance_: each says how a skeleton was made, and no component refers to one, so they change no
  digest and no output (see "Compilation").

- Model facts are _knowledge_: what is known about a model, which compiling a recipe's intents reads (see "Model
  facts"). Only a compilation refers to them, so they change no factor's digest.

## How components work

Some things live inside components or records without being components themselves: recipes (in compilations), views (in
scorers), canaries (in canary sets) and execution settings (in run records).

### Canonical form and digest

A component is written out in one fixed way, its _canonical form_, so that equal components always give the same bytes.
Its digest is the hash of those bytes, and components are told apart, and referred to, by it.

The canonical form keeps what means something and drops what doesn't:

- Order that means nothing doesn't change a digest. The keys of settings (request options, chat-template arguments,
  parameters, environment variables), a translations chunk's languages and each language's entries, a model's files and
  a trial's cases are put in a fixed order, so equivalent components share a digest.
- Order that means something is kept. A schema's property order is part of what a model reads, so JSON data keeps its
  order, and so do lists whose order carries meaning, such as a case's appendices, a trial's seeds and a scorer's views.
- Adding a field whose default keeps the old behavior changes no existing digest, since values equal to their defaults
  are left out.

What is stored is the truth. A component read back keeps the digest it was stored under, even where today's code would
write it differently; the difference is reported, never quietly corrected. A component changed in any way is built anew,
follows its kind's rules, and gets its own digest.

### Versions

Each component type has a schema version. Adding a field with a backward-compatible default needs no new version;
changing an existing field's meaning or default does. Bytes written under another version are refused rather than
guessed at, so after a bump the store can't return components of the old version, nor load a closure that holds one
(docs/backlog.md, "Old versions readable").

### Kinds

Every component has a kind that says what it is. Together, the kinds pin everything a run sends and everything a score
applies, and they fall into a few groups:

- **Clinical input**: cases and their appendices, what the model is asked about.
- **Requests**: chunks, each filling one part of a request, the tools a request may offer, and the skeletons compiled
  from them: how the model is asked.
- **Engines**: where requests go, a server we run or an API we don't, and the model weights a server runs.
- **Grading**: expectations and the schemas they follow, scorers, and judges: how answers are scored.
- **Roots**: trials and scorings. A trial ties a request, an engine and cases into one experimental condition; a scoring
  ties a scorer to the expectations it grades against. Pinning a root pins everything it references.
- **Instruments, knowledge and provenance**: canary sets, model facts and compilations, components that aren't factors.

The sections below take each kind in turn.

### References and checks

A reference names the kinds it may point to, and every reference is checked: it must exist and point to an allowed kind.
Rules that need several components, such as "a trial must use a generation skeleton", are checked alongside, for each
component whose own references hold.

### Errors and findings

Problems come in two strengths.

An _error_ stops the work. A component that breaks its own rules can't be built, such as one with duplicate seeds, or an
engine that sets a flag the start-up script owns. A problem that takes other components to see stops the work too: a
missing or wrongly typed reference, a failed cross-component rule, stored bytes that don't match their digest, an
unknown kind or version.

A _finding_ is a warning, or an info, about something valid but risky, or about something observed that doesn't match
what was declared. It says what it concerns.

### Registries and bundles

A registry holds components by digest, in memory, accepts stored bytes only when they match their digest, and can list a
set of components together with everything they reference.

A bundle is a self-contained package that can be verified offline: some root digests, the stored form of everything they
reference, and the version of the code that wrote it. Loading a bundle verifies every digest and every reference, and
reports each component that today's code would write differently; the stored form still decides its digest.

### Fingerprints

A fingerprint is a hash of content that must not be stored, such as a vignette. It is a plain hash by default, or a
keyed hash that names its key.

### Code

Code is named by its distribution, its version and, optionally, its revision. Compilations name their compiler this way,
bundles the code that wrote them, and runs and scores the code that ran them. Scorers and tools pin code chatddx ships
instead: an entry point, and the version of it the code publishes, which its developers raise when what it does changes,
as a cleanup step's name is (see "Text cleanup"). Only the code chatddx ships runs, at the version pinned, so a deploy
changes no scorer or tool unless it raises a version.

Scorers and tools pinned the running chatddx first. Each deploy then stopped every scorer until it was pinned again, and
a scorer pinned again is a new one, so every finished run was left to score again; every skeleton that offers a tool
changed too, and every trial over one.

### Storage

Components are stored in one table for all kinds, plus one row per reference so that every reference gets a foreign key
(docs/modules/store.md; tables in docs/migrations.md, "factor"). Stored components are never changed or deleted.
Anything a component can hold can be stored: a component the store couldn't hold can't be built.

Storing a component checks it and stores everything it references; storing it again changes nothing. Reading verifies
every digest. A bundle is exported from the store, and imported by loading it and storing what it holds.

## Cases

### Case

Principal author: clinicians.

A case is a vignette plus the appendices to send with it, in order. The vignette is named by the source it comes from,
its id there, and the fingerprint of its raw bytes as fetched. Sources are declared in the inventory
(docs/modules/inventory.md, "Sources") and hand over vignettes as UTF-8 text.

The vignette itself is sensitive by default, unstructured, and never edited. The factors and the ledger never store it,
only its fingerprint; a typed vignette is kept as its database source's text, apart from them (docs/modules/store.md,
"Texts"). A case covers the vignette and its appendices, so the same vignette with different appendices is a different
case. Expectations are keyed by the case, which lets appendices change the correct answer.

When a vignette changes at its source, or is renamed there, it needs a new case, new appendices bound to the new
vignette, and new expectations; the catalog tells a renamed vignette from a changed one.

Text cleanup is not part of the case. The trial chooses it (see "Trial").

### Appendix

Principal author: clinicians.

An appendix is a block of plain text, written in the portal and bound to one vignette. It is the only way to add
information to a vignette; edits anchored inside the vignette were considered and ruled out as too complex. Appendices
are not sensitive. They are stored and sent exactly as written, and text cleanup doesn't touch them.

An appendix can't be reused across vignettes, but it can appear in several cases of the same vignette: for example a
case with a lab appendix and one without. A case's appendices go in a fixed order, which is part of the case. At send
time they are joined into one text by the skeleton's appendix layout (see "Skeleton").

Browsers submit CRLF line endings, so line endings are normalized to LF before an appendix is digested, whichever edge
writes it; nothing cleans it afterwards.

### Text cleanup

Text cleanup is an ordered list of steps from a closed set. Each step's name pins one behavior; a changed behavior gets
a new name. Today the steps normalize line endings, apply Unicode NFC normalization, trim whitespace at both ends, and
collapse runs of blank lines into one.

Cleanup applies to the vignette only, after it has been fingerprinted.

### Preparing a case

Preparing a case turns a case and its raw vignette into what a request is filled with: the vignette, decoded and
cleaned, and the appendices, joined by the layout.

UTF-8 is the contract with sources: bytes that aren't UTF-8 are an error naming the vignette. Preparing also
fingerprints the raw bytes again, with the same key when the case's fingerprint is keyed, and reports drift when they no
longer match the case.

## Requests

### Overview

A _request_ is the body one call sends to an engine: a skeleton rendered with its fills, the served model and the seed
(see "Rendering"), or a tool round's next request (see "Tool rounds"). It is built in three layers:

1. Chunks are written in the portal, one component per part of the request.
2. A recipe picks one chunk per part, and the model the request is for.
3. The compiler turns the recipe into a skeleton, which trials and judges reference, working out what its intents send
   from the facts about the model.

Nothing in a request is a template: text is plain text. There are two kinds of placeholder, and nothing else is
interpreted:

- inserts, filled at compile time;
- slots, filled at send time by plain concatenation, so clinical text is never interpreted.

There are no validation retries: a run stores the raw response, and parsing it belongs to scoring. Transport retries are
a separate matter, declared per run (see "Execution") and counted per call.

### How chunks affect each other

Chunks affect each other only in a few fixed ways, all decided in code:

- The output's guidance goes where the instructions or the prompt place it. Otherwise it is appended to the
  instructions, and it becomes the whole first message when there are no instructions.
- The toolset's guidance does the same, after the output's.
- A toolset adds tools to the request, which changes how the output contract is expressed (see "Recipe and
  compilation").
- Compiled into a language, translations replace every text the other chunks and the appendix layout bring (see
  "Translations").
- Greedy sampling drops the settings that only matter when sampling, and no seed is sent.
- A reasoning level and a recommended sampling send what the facts about the recipe's model say.
- A recommended sampling follows the reasoning level the recipe asks for, where it lands, or the model's default level
  when the reasoning chunk asks for none or the recipe has none.

Compiled as written, how a chunk splits its text never changes the skeleton. Compiled into a language it can, since each
text is looked up exactly as the chunk holds it.

### Instructions

Principal author: researchers.

Instructions are the first message, as a system or a developer message. They may place the output's guidance and the
toolset's guidance, each at most once, with text around each that appears only when there is guidance to place. A first
message that ends up empty is left out.

### Few-shot

Principal author: researchers.

A few-shot chunk is a list of example messages, each from the user or the assistant, in plain text. They go after the
instructions and before the prompt.

### Prompt

Principal author: researchers.

A prompt is the user message: literal text, slots, and the guidances when the instructions don't place them. Its
purpose, generation or judge, decides which slots it may use, and must match the recipe's.

- A generation prompt contains the vignette, and may contain the appendices.
- A judge prompt contains the completion it grades, and may contain the vignette, the appendices and the expectation.

No slot appears twice. Each guidance is placed in the instructions or in the prompt, not both.

### Output

Principal author: researchers.

An output chunk says what shape the answer has and how that shape is enforced. Its contract is one of:

- _native_: the engine constrains the answer to the schema.
- _tool_: the answer is a call to a function whose parameters are the schema, and the model is made to call it.
- _text_: nothing is constrained. A schema is optional; it serves scoring and can be shown to the model.

Optional guidance tells the model how to answer, and may show it the schema.

An output may list schema operations, named and versioned like cleanup steps, that turn the schema as written into the
one schema the skeleton both sends and shows. There is one today: it inlines a schema's references for engines that
don't resolve them themselves; vLLM 0.24 does (docs/vllm.md).

### Sampling

Principal author: researchers.

A sampling chunk may instead ask for the sampling the model's makers recommend, an intent: compiling fills it in from
the facts about the recipe's model, for the level the reasoning chunk asks for, where it lands, or the model's default
when the reasoning chunk asks for no level or the recipe has none. A value the chunk sets beside it replaces the
recommended one, and the recipe doesn't compile when nothing is recommended for that level.

Temperature zero is greedy: top-p, top-k and min-p are dropped, so equivalent greedy chunks share a digest, and no seed
is sent.

### Reasoning

Principal author: researchers.

A reasoning chunk holds the reasoning effort, a thinking-token budget and arguments for the chat template, or asks for a
reasoning level (off, on, minimal, low, medium, high, xhigh, or the model's default), an intent, with at most a
thinking-token budget beside it. Compiling works out what a level sends from the facts about the recipe's model: the
effort and chat template arguments of the level it lands on, which may be another, its nearest, when the model can't be
asked for the first (docs/modules/facts.md, "Reasoning"). A level the model refuses, or a budget it refuses or isn't
known to take, doesn't compile. A recipe without a reasoning chunk leaves reasoning to the model.

### Passthrough

Principal author: researchers.

A passthrough chunk holds engine-specific request options that no other chunk covers. It may not set:

- what the rig sets at send time (see "Rendering");
- what the output contract sets;
- anything the sampling or reasoning chunks manage, whether the recipe uses them or not. So a passthrough can't make a
  request greedy behind the sampling chunk's back;
- options that go around other factors: replacing the engine's pinned chat template, constraining the answer outside the
  output contract, or putting the prompt's text, and so the case's, in the stored response.

Since no other chunk can produce what a passthrough sets, a passthrough never clashes with the rest of the recipe.

### Tool

Principal author: developers.

A tool is a function the model may call between turns: a name, a description, a JSON Schema for its parameters, and the
code that runs it, an entry point chatddx ships at the version it pins. Its code is pinned like a scorer's, because what
it returns is what the model reads next: a new version is a new tool, so a new skeleton and a new trial. What a tool
returned is still recorded per run, with the version it ran at, since a tool such as a web search can answer differently
from day to day: an observed factor.

Only code the running chatddx ships can be run, at the version pinned: a tool or a scorer that pins an entry point it
doesn't ship, or another version, is refused. Naming an entry point picks among the shipped ones, so a scorer written by
anyone runs only code developers shipped.

### Toolset

Principal author: researchers.

A toolset offers tools to the model. It holds the tools, with distinct names; optional guidance, in plain text; and the
most tool rounds one item may take. Its guidance goes where the instructions or the prompt place it, or else after the
instructions, following the output's guidance.

### Translations

A recipe's translations are a chunk of its own, `chunk.translations`, which docs/modules/bench.md, "Translations",
describes. Here they are what compiling into a language reads: `translated` gives what a recipe's translations hold, by
language, and `untranslated` the texts of the recipe they leave without an entry in one, every text in a language they
don't go into. Compiling into a language refuses one they don't go into, and one they leave a text untranslated in,
listing every such text.

### Recipe and compilation

Principal author: researchers.

A recipe is not a component. It holds a purpose and an appendix layout, a prompt, an output, a sampling chunk and a
model, and optionally instructions, few-shot examples, reasoning, a passthrough, translations and a toolset.

Compiling a recipe gives a skeleton, of the recipe as written or translated into one of its translations' languages. It
reads the facts about the recipe's model for the chunks that ask for an intent, and fails on a missing or wrongly typed
chunk or model, a prompt whose purpose differs from the recipe's, translations that don't go into the language asked for
or a text they leave untranslated, a guidance placed in both the instructions and the prompt, an answer function named
like one of the toolset's tools, an intent the facts refuse or know nothing of, an intent on a model with no facts, and
facts about another model than the recipe's.

With a toolset, the request offers the toolset's tools, in order. Under a native or a text contract, the model answers
when it stops calling tools. Under a tool contract, the answer tool is offered last, every response calls a tool, and
calling the answer tool ends the item.

The recipe is kept only in the compilation, next to the compiler's version, the facts compiled against and the language
compiled into (see "Compilation"). Trials reference the skeleton, not the recipe, so neither the compiler's code nor the
facts are a separate factor: whatever they did is frozen in the skeleton. A skeleton holds no model: the model changes
it only through its facts, so a recipe compiles to one skeleton per language for every engine of its model, and, without
intents, for every model. What a run of it was sent to is its trial's engine.

### Compilation

Principal author: none; written by the compiler.

A compilation says that a recipe compiled to a skeleton. It holds the recipe, the skeleton, the version of the compiler,
the language it was compiled into, none for the recipe as written, and the facts it was worked out from: none when the
recipe asks them for nothing, a literal sampling and reasoning, since such a skeleton is the same on every model. It is
the only place a recipe is kept, and so the lineage from the chunks written in the portal to the skeleton.

A compilation is provenance, not a factor: no component refers to it, so it changes no digest and no output. Trials and
judges reference the skeleton, which holds whatever the compiler did. The same recipe compiled by the same compiler
against the same facts into the same language always gives the same compilation. Different recipes can give the same
skeleton (see "How chunks affect each other"), two recipes that differ only in a model they ask no intent of among them,
so a skeleton may have several compilations, and a hand-written one has none.

A bundle carries a compilation when it is one of the roots, and the chunks, the model and the facts then come with it,
so the bundle shows how its skeleton was made. Nothing checks that the recipe compiles to the skeleton, only that the
compilation's facts are about the recipe's model, and that the recipe's translations go into the language it names.

### Skeleton

Principal author: none; normally produced by the compiler.

A skeleton is what trials and judges reference. It is the only component normally produced by code rather than people,
though nothing prevents writing one by hand (docs/backlog.md, "Compilations checked").

It is fully pre-rendered: the whole request except what is filled in at send time. It holds a purpose, the messages with
their slots (few-shot examples already baked in), every other request option, the output contract and the appendix
layout. With a toolset, it also references the tools it offers and holds the round limit.

Its own rules repeat the chunks', so a hand-written skeleton meets them too. The tools it offers are the tools it
references, though their descriptions may be translated.

The appendix layout says what goes before, between and after the appendices.

### Rendering

Rendering produces the request that is sent:

1. Every slot is replaced by its fill. A slot without a fill is an error.
2. The model is added: the engine's digest for a local engine, or its model's name for a remote one.
3. The seed is added, unless sampling is greedy.
4. The response is asked to carry the prompt's token ids, so a run can fingerprint what the model was actually given.

What the rig adds at send time can't be set by any chunk, skeleton or canary. The runner streams every request and
reassembles the response it records; the request it fingerprints is the request as rendered, without the streaming
options.

### Tool rounds

A response that calls tools gets another request: the last one, plus the assistant's message (its content and tool
calls, without its reasoning) and one answer per call, in the calls' order. Its settings stay, the seed included; its
body, and so its fingerprint, is its own.

The loop belongs to the runner. It ends when a response calls no tool, calls the answer tool, or has no whole answer (an
error or a cutoff), or after the round limit. A tool is called with the call's arguments and returns text. A call that
names no offered tool, arguments that don't fit the tool's parameters, and a tool that fails are each answered with an
error for the model to read.

## Engines

An engine is where requests are sent, written by ops (docs/glossary.md, "Roles"), who map each model handle, such as
`qwen3-8b`, to one engine and one endpoint; a handle always means its latest engine (docs/modules/inventory.md).
Researchers pick a recipe's model and a judge's by handle, and see no engines, endpoints or proper model names. Every
engine speaks the same API: OpenAI-compatible chat completions.

### Local model

Principal author: ops.

A local model pins a model's weights: the repository, a revision, and the hash of every file, collected by an import
script. It is a component of its own, so several engines can share it. Its name, what facts are keyed by, is its
repository.

### Local engine

Principal author: ops.

A local engine is a vLLM server we run. It declares:

- its hardware: GPU, compute capability, VRAM and driver.
- its runtime: vLLM, its version and its Nix closure.
- the local model it serves.
- the content of its chat template, by hash; where the file lives is the inventory's business, so moving it doesn't
  change the engine.
- the exact arguments vLLM is started with, and its environment, minus what the host sets to find the model, the GPU and
  CUDA.

The start-up script owns the model's identity: the weights, the served name, the chat template, the tokenizer and the
revision, and where the server listens, which is the endpoint's. Every other argument that changes what is computed
belongs in the engine, where its digest pins it, and nothing may get around that: not an argument that sets what the
script owns, however it is spelled or shortened; not one that reads arguments from a file; and not one that would stop
vLLM from starting. The arguments that only tune the server are the endpoint's, recorded with each run.

The served model name is the engine's digest, so every response names the exact engine it came from. Batch invariance is
declared through the environment. Knowledge that changes between vLLM versions lives in lints, not in the engine.

With the template file in hand, a host can check it against the declared hash, and flag a template that reads the
current date, since that makes the prompt depend on when a run happens.

Hardware and runtime are part of the engine rather than components of their own. So they can't be listed, picked or
reused on their own, for example in the portal or as database foreign keys: the same GPU or closure is repeated in every
engine that uses it, and finding the engines that share a closure means scanning them all.

### Remote engine

Principal author: ops.

A remote engine is an API we don't control. It declares only the API and its model, a remote model, which names its
provider and its name there; where it is served is the inventory's (docs/modules/inventory.md, "Endpoints"), and its
chat template is not pinned.

Canary probes at the start and end of a run apply to any engine and are planned per run, so they are not part of the
engine.

### Model facts

Principal author: developers, for the bundled facts; whoever adds a model they don't know, for a World's
(docs/modules/inventory.md, "Worlds").

Model facts are what is known about one model that a request doesn't say (docs/modules/facts.md), by the model's name: a
`model.local` component's repository or a `model.remote` component's `name`.

They are knowledge, not a factor: no component but a compilation refers to them, and a skeleton holds what they did.
init-data writes them from facts files, a thread per model (docs/modules/curation.md); correcting a fact is a new
version of its thread, and a configuration compiled against the old one is then behind where the new one changes what it
sends (docs/modules/catalog.md, "What has moved on"), until its owner follows them (docs/modules/api.md, "Following").

## Trials

### Trial

Principal author: researchers.

A trial is one experimental condition (the smallest unit of a scientific intent) and holds:

- a generation skeleton;
- an engine;
- the cases;
- the text-cleanup steps;
- the seeds.

A trial pins the factors chosen in advance; each of its runs adds recorded and observed ones.

#### Send order and de-duplication

A trial lists each case and each seed once. The order of its cases is no part of the trial; the run declares the send
order (see "Execution"). Seeds keep their order, as each seed's position names a replicate.

#### Seeds are explicit

Seeds are chosen in advance, not drawn when a run starts. A helper can propose distinct random seeds, which users are
free to change. Each seed defines one replicate, identified by its position. With greedy sampling no seed is sent, but
the seeds still count toward the trial's digest (docs/backlog.md, "Digests to settle before real data").

### Execution

When a run issues its requests, or a score its judge requests, its execution settings say:

- the order in which items are sent: every replicate of a case before the next case (the default), every case once per
  replicate, or shuffled by a declared seed;
- how many items may be in flight at once, each sending its requests one after another (one by default);
- an optional timeout;
- how many transport retries a call may take (none by default);
- a runaway cutoff, on by default: a call that answers a long run of nothing but whitespace is cut short and keeps what
  came, since a model that runs away would write it until its tokens or its context run out. Like a timeout, it decides
  what answer gets recorded. The sampling chunk's token limit bounds every answer; the cutoff bounds only a runaway.

These settings are a recorded factor, not a component: they are written into the start record of each run or score,
without affecting the trial's or the scoring's digest, so running a trial or a scoring again with other settings is a
rerun of the same one.

This suits batch-invariant engines, but the settings change outputs on engines that aren't batch invariant, where they
affect how requests are batched and so the arithmetic (docs/backlog.md, "Aggregation"). Timeout and retries also decide
whether a request gets an answer at all.

A run's calls, and a score's judge calls, show whether the settings were followed: checks warn when a call took more
attempts than its retries allow, when items were sent out of order, or when more calls were in flight than allowed
(docs/modules/ledger.md, "Run" and "Score"). Timeouts aren't checked.

## Scoring

### Expectation schema

Principal author: developers.

An expectation schema is a JSON Schema for the reference data a scorer consumes, written in the draft it names (2020-12
by default).

### Expectation

Principal author: clinicians.

An expectation is the reference answer for one case, written in the portal against an expectation schema. Because it is
keyed by the case, appendices included, the same vignette can have different expectations under different appendices.
Expectations are not sensitive.

Building an expectation doesn't check its data against its schema. Lints do (see "Lints"), and the scorer decides what
to do with data that fails.

### Scorer

Principal authors: developers, who write the scoring code and ship it with the project, and researchers, who write the
views, the free parameters where the code publishes a schema for them, the labels and the resources, and pick the code
and the expectation schema.

- the entry point of the scoring code chatddx ships, and the version of it it pins;
- the expectation schema it consumes;
- an ordered list of views;
- ordered resources: strings, such as the name of a synonym table or an ontology release;
- free parameters.

Views and resources are referred to by position; their labels live in the catalog, with the edit of the scorer's thread
they were written with.

The scoring code publishes its version and its metrics, each with what it measures and a JSON Schema for the parameters
a view gives it, and optionally a schema for the parameters every view shares. A scorer is refused when its code isn't
shipped at the version it pins, when a view names a metric the code doesn't publish, or when parameters don't fit the
schema published for them; where nothing is published, no parameters are taken.

The scoring function sees one view at a time: what the view picks from the answer (nothing when the run has no answer),
what it picks from the expectation, and the parameters. It returns a value, or none, and a detail. Its interface is
versioned.

The answer is read from the item's last response by the skeleton's contract: a native answer is the content as JSON, a
tool answer the answer tool's arguments, and a text answer the content, or, when the output has a schema, the JSON in
it. A native or tool answer cut short is salvaged: read with what it holds up to its last complete value, a string it
stopped in closed, and its structure closed; JSON that breaks before its end isn't salvaged. An answer that can't be
read is no answer.

The shipped pattern metrics hold what a view picks from the answer to one target, what its expectation selector picks: a
pattern, an object with a `pattern`, or `false`, nothing expected. A pattern is words, matched whole and regardless of
case: words side by side are a phrase, found in that order, a word ending in `*` matches any word it begins, `&` needs
every part somewhere and `|` any part, `&` binding first, and parentheses group. Unlike the old chatddx's matcher, it
never matches part of a word. No target, several, an object without a pattern, such as words for a judge, or a pattern
that doesn't read, give no value, with the reason in the detail.

Only shipped code runs.

### View

A view scores one part of an output against one part of an expectation. It holds:

- a selector into the output and one into the expectation
- optionally, how to split what the output selector picks
- a metric that only the scorer's code interprets, with optional parameters
- optionally, the judge it uses. The view's selections are then what the judge sees (see "Judge").

Selectors are written in standard notations: a JSON Pointer, which picks at most one value, or a JSONPath query from a
fixed subset within which every implementation picks the same values. Anything outside the subset is refused. Where the
standard leaves the order open, selection keeps the document's order, and it keeps nulls.

Only the output side is split. A model answering under a text contract writes one block of free text, which has to be
broken into items before it can be compared; splits are named and versioned like cleanup steps, and there is one today,
into the lines of a list. An expectation is written against its schema, so a list in it is already a list, and free-text
notes in expectations are for judges to read.

Every scorer selects the same way, through its views.

### Judge

Principal author: researchers, who write the judge skeleton, as a configuration of purpose `judge`, and the seeds, and
pick the model, by its handle, and the fill rule.

A judge is an LLM used as a metric: a judge skeleton, the weights picked by handle, its own seeds, and a fill rule. Its
calls go to the handle's endpoint, at its latest engine, which the scoring pins.

Vignettes will probably never go to a judge: the scoring pass refuses a judge whose skeleton reads them, before anything
is written.

A judge is given a view's picks: its fill rule fills the `completion` and `expectation` slots. Purpose `judge` still
allows the `vignette` and `appendices` slots, but a judge whose skeleton has either is refused.

Judge requests are rendered like generation requests, once per seed, and recorded per score item. Their scores are
reproducible on a best-effort basis. Given the scorer's reading of an answer, a judge request can be rebuilt from stored
data and checked against what its call recorded; the reading belongs to the scorer's code, so the rig can't do that
check on its own. Because a judge prompt can contain case text, judge engines fall under the same clearance rule as
generation engines (agents/wip-clearance.md).

### Scoring

Principal author: researchers.

A scoring is what a score applies: a scorer plus the expectations it scores against, and the engine each of its judges
is sent to. Every expectation follows the scorer's expectation schema, and each case has at most one. The judges a
scoring uses are the ones its scorer's views name, each pinned to one engine serving its weights.

## Canary sets

Principal author: developers.

Canary probes detect observed factors, such as an engine that changed between runs. A canary set is a list of fixed,
non-sensitive probe requests. Each canary holds literal messages, request options, none of them the rig's, and an
optional seed. A run names the canary set it uses. Canaries are rendered as skeletons are, without slots. They are
components so that the same set can be compared across runs.

## Lints

Lints warn about settings that are valid but risky. They run on demand, and no component stores their findings. Keeping
them out of the components means knowledge that changes between vLLM releases can change without changing any digest.

They look at:

- Pins that can move: a model revision that isn't a commit, a runtime that isn't a Nix store path.
- Views whose expectation selector can't pick anything from documents that follow the scorer's expectation schema. The
  check leans towards "reachable", so a finding is certain.
- Expectation schemas and outputs' schemas that can't be checked or break their draft, and expectations whose data fails
  its schema or can't be checked against it.
- Each trial, and each judge on the engine it is sent to, as a pair of skeleton and engine. A temperature it raises, a
  thinking budget or tools without the server options they need, tools that a native contract leaves uncallable, and a
  constrained answer that the model can't reason before giving. On any other engine, a schema reference the engine isn't
  known to resolve, in the output's schema or a toolset tool's parameters.
- Each trial whose skeleton its compilations say was worked out for another model than its engine serves, and each judge
  whose weights are another model: a level or a recommended sampling meant for one model, sent to another. Two engines
  of one model, and a skeleton worked out from no facts, pair with any; a skeleton with no compilation at hand isn't
  checked.
- With languages known, trials whose cases are in another language than the request, or in an unknown one.

Checks against the model facts belong to the facts (docs/modules/facts.md). Other findings come from the steps that
observe them: drift when preparing a case, a chat template that doesn't match its hash or reads the date, and a
component that a bundle holds in a form today's code wouldn't write. Each finding is made where it is found, as
`Finding(…)`.

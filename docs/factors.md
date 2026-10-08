# Factors

An LLM can be given a case vignette in countless ways. The instructions, the sampling settings, the GPU, the model
weights and many other choices all affect what comes out. Varying each choice on its own is impractical, so we group
them into a manageable number of categories. We call these categories factors.

There is a catch-22: grouping well requires knowing *how* each choice affects the output, and that is exactly what the
research is trying to find out. So we start from a flexible set of factors based on reasonable guesses and refine it as
we learn.

Factors are the building blocks of the chatddx rig: an environment that can be rebuilt exactly, and shown to be the
same, for scientific rigor. This document describes what each factor is for and how factors combine. Names, fields,
rules and errors are in the API, docs/factors-api.md.

Factors depend on nothing else in chatddx; the model facts, the catalog, the ledger and the store build on them.
Principal authors are the roles in docs/identity.md.

## What a factor is

A *factor* is anything that can change an output or its score: what the research varies, holds fixed, or has to account
for.

A *component* is how most factors are stored: an immutable set of parameters identified by a hash of its content, its
*digest*. Changing a parameter gives a new component with a new digest; nothing is edited in place. Components refer to
each other by digest, so a trial's digest pins every component the trial depends on.

Being a factor and being a component are separate questions. A factor is held in one of three ways.

1. **Pinned**: chosen in advance and fixed by digest: a trial or a scoring, and every component it references. Prompts,
   sampling, engines, model weights, cases, seeds, expectations and scorers are pinned.
2. **Recorded**: set or known when a run or a score starts, and written into its start record, which is sealed with the
   rest of its log (docs/ledger.md): the execution settings (see "Execution"), the version of the rig that sent the
   requests, and the scorer code that actually ran. Set beside the code the scorer pins, the last shows whether what ran
   is what should have run, and checking a score warns when they differ.
3. **Observed**: set by nobody, and only detected afterwards. These are the parts of the world outside our control: a
   remote engine that changes without notice, a tool such as a web search that answers differently from day to day, a
   vignette edited at its source, GPU arithmetic that isn't deterministic. Fingerprints, returned model names, drift
   findings and canaries reveal them (docs/ledger.md, "Findings").

Canary sets are components but not factors. They are *instruments*: fixed probe requests that measure observed factors
without changing any output (see "Canary sets").

Compilations are components but not factors either. They are *provenance*: each says how a skeleton was made, and no
component refers to one, so they change no digest and no output (see "Compilation").

A trial's outputs therefore depend on the trial's pinned factors and on its run's recorded and observed factors. Two
runs of the same trial are interchangeable only when those agree too (see "Open design issues").

### Not factors
- Records of what happened (runs, scores, calls): [docs/ledger.md]. They hold the recorded factors and the evidence of the
  observed ones, but they aren't factors themselves.
- People, roles, authentication and authorization: [docs/identity.md].
- Names, labels, languages, tags, descriptions, owners, collaborators and version history: [docs/catalog.md].
- Sensitivity and vetting: [agents/wip-clearance.md].
- Facts from model cards: [docs/facts.md].
- Inventory: [docs/inventory.md].
- Knowledge about models (reasoning levels, recommended sampling, output caveats, specs): the model facts
  (docs/facts.md). Facts help write chunks and check them, but no digest depends on them.
- Instruments and provenance: canary sets and compilations are components, but not factors.

## How components work

Some things live inside components or records without being components themselves: recipes (in compilations), views (in
scorers), canaries (in canary sets) and execution settings (in run records).

### Canonical form and digest
A component is written out in one fixed way, its *canonical form*, so that equal components always give the same bytes.
Its digest is the hash of those bytes, and components are told apart, and referred to, by it.

The canonical form keeps what means something and drops what doesn't:
- Order that means nothing doesn't change a digest. The keys of settings (request options, chat-template arguments,
  parameters, environment variables, translation entries), a model's files and a trial's cases are put in a fixed order,
  so equivalent components share a digest.
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
(docs/store.md, "Known gaps").

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
- **Instruments and provenance**: canary sets and compilations, components that aren't factors.

The sections below take each kind in turn.

### References and checks
A reference names the kinds it may point to, and every reference is checked: it must exist and point to an allowed kind.
Rules that need several components, such as "a trial must use a generation skeleton", are checked alongside, for each
component whose own references hold.

### Errors and findings
Problems come in two strengths.

An *error* stops the work. A component that breaks its own rules can't be built, such as one with duplicate seeds, or an
engine that sets a flag the start-up script owns. A problem that takes other components to see stops the work too: a
missing or wrongly typed reference, a failed cross-component rule, stored bytes that don't match their digest, an
unknown kind or version.

A *finding* is a warning, or an info, about something valid but risky, or about something observed that doesn't match
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
Code is named by its distribution, its version and, optionally, its revision. Scorers and tools pin their code this way,
compilations name their compiler, and bundles name the code that wrote them.

### Storage
Components are stored in one table for all kinds, plus one row per reference so that every reference gets a foreign key
(docs/store.md; tables in docs/migrations.md, "factor"). Stored components are never changed or deleted. Anything a
component can hold can be stored: a component the store couldn't hold can't be built.

Storing a component checks it and stores everything it references; storing it again changes nothing. Reading verifies
every digest. A bundle is exported from the store, and imported by loading it and storing what it holds.

## Terms

| Term | Meaning |
| --- | --- |
| Factor | Anything that can change an output or its score. |
| Pinned, recorded, observed | The three ways a factor is held: fixed in advance by digest, written into a run's or a score's start record, or only detected afterwards. |
| Component | An immutable set of parameters identified by its digest. Pinned factors are held in components. |
| Digest | The hash of a component's canonical form. Components are told apart and referred to by it. |
| Instrument | A component that measures without being a factor: canary sets. |
| Provenance | A component that says how another was made, without being a factor: compilations. |
| Run | One execution of a trial: its requests, responses and records. |
| Vignette | The clinical text of one case at its source. Sensitive. |
| Case | A vignette plus the appendices sent with it. |
| Appendix | Extra plain text written for one vignette. |
| Chunk | A component that fills one part of a request. |
| Recipe | The choice of chunks a request is compiled from. Not a component. |
| Skeleton | The compiled, frozen request. |
| Slot | A placeholder filled at send time: the vignette, the appendices, the completion or the expectation. |
| Insert | A placeholder filled at compile time: the output's schema, the output guidance or the tool guidance. |
| Segment | One piece of a text: a literal string, a slot or an insert. |
| Purpose | Whether a request writes an answer (generation) or grades one (judge). It decides which slots are allowed. |
| Contract | How the answer is constrained: native, tool or text. |
| Guidance | Text that tells the model how to answer, or how to use its tools. |
| Text cleanup | Named steps that tidy a vignette before it is sent. |
| Seed, replicate | A seed fixes the sampler's randomness. Each seed of a trial is one replicate, identified by its position. |
| Engine | Where requests go: a vLLM server we run, or a remote API. |
| Trial | The pinned factors of one experiment: a skeleton, an engine, cases, text cleanup and seeds. |
| Expectation | The reference answer for one case. |
| View | One comparison a scorer makes between part of an output and part of an expectation. |
| Judge | An LLM used to grade outputs. |
| Canary | A fixed, non-sensitive probe request. |
| Portal | The web interface where components are written and runs are watched. |

## Cases

### Case
Principal author: clinicians.

A case is a vignette plus the appendices to send with it, in order. The vignette is named by the source it comes from,
its id there, and the fingerprint of its raw bytes as fetched. Sources are declared in the inventory (docs/inventory.md,
"Sources") and hand over vignettes as UTF-8 text.

The vignette itself is sensitive by default, unstructured, and never edited or stored: only its fingerprint is. A case
covers the vignette and its appendices, so the same vignette with different appendices is a different case. Expectations
are keyed by the case, which lets appendices change the correct answer.

When a vignette changes at its source, or is renamed there, it needs a new case, new appendices bound to the new
vignette, and new expectations; the catalog tells a renamed vignette from a changed one. Whether a person or an
automatic step rebinds them is open; the catalog has the tools for it (docs/catalog.md).

Text cleanup is not part of the case. The trial chooses it (see "Trial").

### Appendix
Principal author: clinicians.

An appendix is a block of plain text, written in the portal and bound to one vignette. It is the only way to add
information to a vignette; edits anchored inside the vignette were considered and ruled out as too complex. Appendices
are not sensitive. They are stored and sent exactly as written, and text cleanup doesn't touch them.

An appendix can't be reused across vignettes, but it can appear in several cases of the same vignette: for example a
case with a lab appendix and one without. A case's appendices go in a fixed order, which is part of the case. At send
time they are joined into one text by the skeleton's appendix layout (see "Skeleton").

Browsers submit CRLF line endings, so the portal normalizes line endings before an appendix is digested; nothing cleans
it afterwards.

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
A request is built in three layers:
1. Chunks are written in the portal, one component per part of the request.
2. A recipe picks one chunk per part.
3. The compiler turns the recipe into a skeleton: the frozen request that trials and judges reference.

Nothing in a request is a template: text is plain text. There are two kinds of placeholder, and nothing else is
interpreted:
- inserts, filled at compile time;
- slots, filled at send time by plain concatenation, so clinical text is never interpreted.

There are no validation retries: a run stores the raw completion, and parsing it belongs to scoring. Transport retries
are a separate matter, declared per run (see "Execution") and counted per call.

### How chunks affect each other
Chunks affect each other only in a few fixed ways, all decided in code:
- The output's guidance goes where the instructions or the prompt place it. Otherwise it is appended to the
  instructions, and it becomes the whole first message when there are no instructions.
- The toolset's guidance does the same, after the output's.
- A toolset adds tools to the request, which changes how the output contract is expressed (see "Recipe and
  compilation").
- Translations replace every text the other chunks bring (see "Translations").
- Greedy sampling drops the settings that only matter when sampling, and no seed is sent.

Without translations, how a chunk splits its text never changes the skeleton. With translations it can, since each text
is looked up exactly as the chunk holds it.

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
- *native*: the engine constrains the answer to the schema.
- *tool*: the answer is a call to a function whose parameters are the schema, and the model is made to call it.
- *text*: nothing is constrained. A schema is optional; it serves scoring and can be shown to the model.

Optional guidance tells the model how to answer, and may show it the schema.

An output may list schema operations, named and versioned like cleanup steps, that turn the schema as written into the
one schema the skeleton both sends and shows. There is one today: it inlines a schema's references for engines that
don't resolve them themselves; vLLM 0.24 does (docs/vllm.md).

### Sampling
Principal author: researchers.

A sampling chunk holds the temperature, top-p, top-k and min-p, the presence, frequency and repetition penalties, stop
sequences, and the most tokens an answer may take, sent under the name the engine expects. Whatever a chunk leaves out
is left to the server.

Temperature zero is greedy: top-p, top-k and min-p are dropped, so equivalent greedy chunks share a digest, and no seed
is sent.

### Reasoning
Principal author: researchers.

A reasoning chunk holds the reasoning effort, a thinking-token budget and arguments for the chat template. A recipe
without one leaves reasoning to the model.

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
code that runs it. Its code is pinned like a scorer's, because what it returns is what the model reads next: a new
implementation is a new tool, so a new skeleton and a new trial. What a tool returned is still recorded per run, since a
tool such as a web search can answer differently from day to day: an observed factor.

Only the running chatddx can be run: a tool or a scorer pinned to other code is refused.

### Toolset
Principal author: researchers.

A toolset offers tools to the model. It holds the tools, with distinct names; optional guidance, in plain text; and the
most tool rounds one item may take. Its guidance goes where the instructions or the prompt place it, or else after the
instructions, following the output's guidance.

### Translations
Principal author: researchers (translators).

Translations map source texts to their translations, the way gettext does. Each entry is a text exactly as a chunk holds
it, whitespace included, and its translation.

A recipe may name translations, and compilation then passes every text the recipe brings through them: the instructions,
the examples and the prompt; the guidance and the text around where it is placed; the appendix layout; the descriptions
of tools and of the answer function; and the titles and descriptions in schemas. What defines the answer's structure,
such as property names and allowed values, is not translated, so the answer's structure and its scoring don't change. A
text without a translation fails the compilation, which lists every missing text: nothing is guessed, and languages
never mix.

Translations carry no language. A request's language is implicit in its text, and no language tag reaches the model;
languages are recorded in the catalog (docs/catalog.md). The skeleton holds the translated text, and its compilation
keeps the recipe, which names the translations.

### Recipe and compilation
Principal author: researchers.

A recipe is not a component. It holds a purpose and an appendix layout, a prompt, an output and a sampling chunk, and
optionally instructions, few-shot examples, reasoning, a passthrough, translations and a toolset.

Compiling a recipe gives a skeleton. It fails on a missing or wrongly typed chunk, a prompt whose purpose differs from
the recipe's, a missing translation, a guidance placed in both the instructions and the prompt, or an answer function
named like one of the toolset's tools.

With a toolset, the request offers the toolset's tools, in order. Under a native or a text contract, the model answers
when it stops calling tools. Under a tool contract, the answer function is offered last, every turn calls a tool, and
calling the answer function ends the item.

The recipe is kept only in the compilation, next to the compiler's version (see "Compilation"). Trials reference the
skeleton, not the recipe, so the compiler's code is not a separate factor: whatever it did is frozen in the skeleton.

### Compilation
Principal author: none; written by the compiler.

A compilation says that a recipe compiled to a skeleton. It holds the recipe, the skeleton and the version of the
compiler. It is the only place a recipe is kept, and so the lineage from the chunks written in the portal to the frozen
request.

A compilation is provenance, not a factor: no component refers to it, so it changes no digest and no output. Trials and
judges reference the skeleton, which holds whatever the compiler did. The same recipe compiled by the same compiler
always gives the same compilation. Different recipes can give the same skeleton (see "How chunks affect each other"), so
a skeleton may have several compilations, and a hand-written one has none.

A bundle carries a compilation when it is one of the roots, and the chunks then come with it, so the bundle shows how
its skeleton was made. Nothing checks that the recipe compiles to the skeleton.

### Skeleton
Principal author: none; normally produced by the compiler.

A skeleton is the frozen request that trials and judges reference. It is the only component normally produced by code
rather than people, though nothing prevents writing one by hand (see "Open design issues").

It is fully pre-rendered: the whole request except what is filled in at send time. It holds a purpose, the messages with
their slots (few-shot examples already baked in), every other request option, the output contract and the appendix
layout. With a toolset, it also references the tools it offers and holds the round limit.

Its own rules repeat the chunks', so a hand-written skeleton meets them too. The tools it offers are the tools it
references, though their descriptions may be translated.

The appendix layout says what goes before, between and after the appendices.

### Rendering
Rendering produces the request that is sent:
1. Every slot is replaced by its fill. A slot without a fill is an error.
2. The model is added: the engine's digest for a local engine, or the configured model for a remote one.
3. The seed is added, unless sampling is greedy.
4. The response is asked to carry the prompt's token ids, so a run can fingerprint what the model was actually given.

What the rig adds at send time can't be set by any chunk, skeleton or canary. The runner streams every request and
reassembles the completion it records; what it records as the request is the request as rendered.

### Tool rounds
A response that calls tools gets another request: the same request, plus the assistant's message (its content and tool
calls, without its reasoning) and one answer per call, in the calls' order. Everything else stays, the seed included.

The loop belongs to the runner. It ends when a response calls no tool, calls the answer function, or has no whole answer
(an error or a cutoff), or after the round limit. A tool is called with the call's arguments and returns text. A call
that names no offered tool, arguments that don't fit the tool's parameters, and a tool that fails are each answered with
an error for the model to read.

## Engines
An engine is where requests are sent. Researchers pick engines for trials and judges. Every engine speaks the same API:
OpenAI-compatible chat completions.

### Model artifact
Principal author: ops.

A model artifact pins a model's weights: the repository, a revision, and the hash of every file, collected by an import
script. It is a component of its own, so several engines can share it.

### Local engine
Principal author: ops.

A local engine is a vLLM server we run. It declares:
- its hardware: GPU, compute capability, VRAM and driver;
- its runtime: vLLM, its version and its Nix closure;
- the model artifact it serves;
- the content of its chat template, by hash; where the file lives is the inventory's business, so moving it doesn't
  change the engine;
- the exact arguments vLLM is started with, and its environment, minus what the host sets to find the model, the GPU and
  CUDA.

The start-up script owns the model's identity: the weights, the served name, the chat template, the tokenizer and the
revision. Every other argument belongs in the engine, where its digest pins it, and nothing may get around that: not an
argument that sets what the script owns, however it is spelled or shortened; not one that reads arguments from a file;
and not one that would stop vLLM from starting.

The served model name is the engine's digest, so every response names the exact engine it came from. Batch invariance is
declared through the environment. Knowledge that changes between vLLM versions lives in lints, not in the engine.

With the template file in hand, a host can check it against the declared hash, and flag a template that reads the
current date, since that makes the prompt depend on when a run happens.

Hardware and runtime are part of the engine rather than components of their own. So they can't be listed, picked or
reused on their own, for example in the portal or as database foreign keys: the same GPU or closure is repeated in every
engine that uses it, and finding the engines that share a closure means scanning them all.

### Remote engine
Principal author: ops.

A remote engine is an API we don't control. It declares only the API, its address and the requested model; its chat
template is not pinned. What the API does on a given day is an observed factor. Of what it returns, only the model name
is checked today (docs/ledger.md).

Canary probes at the start and end of a run apply to any engine and are planned per run, so they are not part of the
engine.

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
the seeds still count toward the trial's digest (see "Greedy sampling and seeds").

### Execution
When a run issues its requests, or a score its judge requests, its execution settings say:
- the order in which items are sent: every replicate of a case before the next case (the default), every case once per
  replicate, or shuffled by a declared seed;
- how many requests may be in flight at once (one by default);
- an optional timeout;
- how many transport retries a call may take (none by default);
- a runaway cutoff, on by default: a call that answers a long run of nothing but whitespace is cut short and keeps what
  came, since a model that runs away would write it until its tokens or its context run out. Like a timeout, it decides
  what answer gets recorded. The sampling chunk's token limit bounds every answer; the cutoff bounds only a runaway.

These settings are a recorded factor, not a component: they are written into the start record of each run or score,
without affecting the trial's or the scoring's digest, so running a trial or a scoring again with other settings is a
rerun of the same one.

This suits batch-invariant engines, but the settings change outputs on engines that aren't batch invariant, where they
affect how requests are batched and so the arithmetic (see "Runs of the same trial aren't interchangeable"). Timeout and
retries also decide whether a request gets an answer at all.

A run's calls, and a score's judge calls, show whether the settings were followed: checks warn when a call took more
attempts than its retries allow, when items were sent out of order, or when more calls were in flight than allowed
(docs/ledger.md, "Run" and "Score"). Timeouts aren't checked.

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
Principal author: researchers.

A scorer pins scoring code written by developers. It declares:
- the code, and the function in it that does the scoring;
- the expectation schema it consumes;
- an ordered list of views;
- ordered resources, such as synonym tables or ontology releases, pinned by digest;
- free parameters.

Views and resources are referred to by position; their labels live in the catalog.

The scoring function sees one view at a time: what the view picks from the answer (nothing when the run has no answer),
what it picks from the expectation, and the parameters. It returns a value, or none, and a detail. Its interface is
versioned.

The answer is read from the item's last response by the skeleton's contract: a native answer is the content as JSON, a
tool answer the answer function's arguments, and a text answer the content, or, when the output has a schema, the JSON
in it. An answer that can't be read is no answer.

Only the running chatddx can be run (see "Tool").

### View
A view scores one part of an output against one part of an expectation. It holds:
- a selector into the output and one into the expectation (the whole document by default);
- optionally, how to split what the output selector picks;
- a metric that only the scorer's code interprets, with optional parameters;
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
Principal author: researchers.

A judge is an LLM used as a metric: a judge skeleton, an engine, its own seeds, and a fill rule.

The view decides what the judge sees, and the judge decides how it is written out. The completion slot gets what the
view's output selector picks from the answer, as the scorer read it, and the expectation slot what its expectation
selector picks from the expectation. The fill rule, named and versioned like cleanup steps, turns those picks into text.
The vignette and the appendices are filled as for the trial (see "Preparing a case").

Judge requests are rendered like generation requests, once per seed, and recorded per score item. Their scores are
reproducible on a best-effort basis. Given the scorer's reading of an answer, a judge request can be rebuilt from stored
data and checked against what its call recorded; the reading belongs to the scorer's code, so the rig can't do that
check on its own. Because a judge prompt can contain case text, judge engines fall under the same clearance rule as
generation engines (agents/wip-clearance.md).

### Scoring
Principal author: researchers.

A scoring is what a score applies: a scorer plus the expectations it scores against. Every expectation follows the
scorer's expectation schema, and each case has at most one. The judges a scoring uses are the ones its scorer's views
name.

## Canary sets
Principal author: developers.

A canary set is a list of fixed, non-sensitive probe requests. Each canary holds literal messages, request options, none
of them the rig's, and an optional seed. A run names the canary set it uses. Canaries are rendered as skeletons are,
without slots.

A canary set is an instrument, not a factor: it changes no output and no score, and it is there to detect observed
factors, such as an engine that changed between runs. It is a component so that the same set can be compared across
runs.

## Lints
Lints warn about settings that are valid but risky. They run on demand, and no component stores their findings. The
seeder runs them over every component it seeds and prints what they find, without storing it either.

Keeping them out of the components means knowledge that changes between vLLM releases can change without changing any
digest.

They look at:
- pins that can move: a model revision that isn't a commit, a runtime that isn't a Nix store path, scorer code without a
  revision;
- views whose expectation selector can't pick anything from documents that follow the scorer's expectation schema. The
  check leans towards "reachable", so a finding is certain;
- expectation schemas that can't be checked or break their draft, and expectations whose data fails its schema or can't
  be checked against it;
- each trial and judge as a pair of skeleton and engine. On a vLLM 0.24 engine, that is what vLLM would change, refuse
  or quietly defeat: a temperature it raises, a thinking budget or tools without the server options they need, tools
  that a native contract leaves uncallable, and a constrained answer that the model can't reason before giving. On any
  other engine, a schema reference the engine isn't known to resolve;
- with languages known, trials whose cases are in another language than the request, or in an unknown one.

Checks against the model facts belong to the facts (docs/facts.md). Other findings come from the steps that observe
them: drift when preparing a case, a chat template that doesn't match its hash or reads the date, and a component that a
bundle holds in a form today's code wouldn't write. The API lists every finding (docs/factors-api.md, "Finding
codes").

## Open design issues
These are open questions of design. Where the code falls short of this document, the API says so (docs/factors-api.md,
"Known gaps").

### Runs of the same trial aren't interchangeable
A trial's digest covers its pinned factors only. Its outputs also depend on its run's recorded and observed factors:
execution settings on an engine that isn't batch invariant, a remote engine that changed between runs, a tool that
answered differently. Seeds within a run are replicates; runs of the same trial are a second source of variation, and it
has no name yet.

Nothing aggregates scores today, but anything that compares or pools runs by the trial's digest alone would mix
conditions without noticing. It needs to group by the recorded factors as well, and to check the evidence of the
observed ones (prompt-token fingerprints, returned models, canaries) before pooling.

### Greedy sampling and seeds
No seed is sent with greedy sampling, but a trial's seeds still count toward its digest, so two otherwise identical
greedy trials differ only in digest. Likewise, the seeds of a greedy judge all send the same request.

Keeping the seeds is deliberate. On an engine that isn't batch invariant, greedy replicates still measure
nondeterminism, and the seeds are what name the replicates. The alternative, a replicate count for greedy trials,
changes the shape of a trial, so it is cheapest decided before trials are stored for real.

### Smaller issues
- **Canary drift isn't checked.** Nothing compares canary outputs between phases or between runs yet.
- **Judge engines are never probed.** Canary probes run on the run's engine only. Probing judge engines would put
  canaries in a score's start record, as in a run's; added with defaults, they keep every stored digest.
- **Skeleton provenance.** Should a skeleton be accepted only with a compilation? Hand-written ones, such as judge
  prompts, are possible today. A take: keep hand-written skeletons. Provenance is whether a compilation names the
  skeleton, a question a lint can ask once the catalog or ledger is queried for it.
- **A scoring doesn't say which cases it lacks.** Only checking a score warns, once a run is scored under it.
- **Judge calls aren't attested.** Their returned model and prompt-token fingerprint aren't checked the way run items
  are.
- **Judges that read the vignette must fetch it again.** A judge skeleton with the vignette slot makes the scorer fetch
  the sensitive vignette again and redo the trial's cleanup. Preparing a case covers the cleanup; nothing fetches the
  vignette.
- **Every engine is asked for the prompt's token ids.** A remote engine that isn't vLLM may refuse the unknown option.
  Either the engine says whether it takes it, which changes the engine's digest, or the runner decides per call, which
  leaves the run without prompt-token fingerprints.
- **A scoring's digest depends on the order of its expectations.** Its expectations aren't put in a fixed order as a
  trial's cases are, so the same expectations in another order make another scoring. The person reads build them in the
  trial's case order.
- **Four cleanup steps exist.** Vignettes may also need non-breaking spaces turned into spaces, zero-width characters
  removed, Unicode line breaks turned into newlines, or trailing whitespace stripped.
- **Hardware has no GPU count,** so engines that split a model across GPUs can't be told apart by their hardware.

## Potential design improvements

### Execution settings as a component
Today execution settings are a value inside each run's start record: recorded, sealed with the run's log, and compared
by value. They have no digest, so the catalog can't name a set of settings (for example "sequential" or "8-way"), the
portal can't offer them for picking, and finding the runs that used the same settings means comparing values across run
records.

Making them a component of a new kind, which the start record references by digest, would give them a name, a catalog
thread and a foreign key like the pinned factors. They would still stay out of the trial's digest, so this changes how
execution settings are stored, not what a trial means. The cost is a new kind (with the catalog's thread kinds and their
migration) and a change to the run record.

### Chat templates as components
Today a local engine pins its chat template by the file's hash, like the model files: a world input, fetched from
wherever the inventory says it is. A bundle therefore holds the template's hash but not the template, and only a host
with the file in hand can read it.

Making the template a component of a new kind, holding the template's text, that the engine references by digest, would
put it inside the bundle: it is small and not sensitive, so a bundle could rebuild the engine's prompt formatting
offline. Lints could read it too, so the check for templates that read the current date would run when factors are
linted, not only on a host. Engines sharing a template would share the component. It would move the template from world
input to authored factor, and cost a new kind (with the catalog's thread kinds and their migration) and a change to the
template check.

### Splitting expectations
If expectations written as free text turn up, a view could split them too. Two ways:
- a separate split for the expectation side, next to the output's. It is additive: with none as its default, every
  existing digest stays the same, and each side gets the split it needs.
- one split for both sides. That changes the meaning of an existing field, so the scorer's schema version would have to
  go up, and the two sides rarely need the same split.

### Finding code through packaging entry points
Tools and scorers name their function in the component. Python packaging offers another way: the distribution declares
its function in its own metadata, under a group for chatddx scorers or tools, and the runner looks it up there. The
pinned distribution and version would then decide which function runs, with no field in the component. It would keep the
choice with the code's authors, at the cost of being less visible in the factors, and tools and scorers should switch
together.

### Passthrough: an allow list, or lints
A passthrough refuses a fixed list of options and lets everything else through. Two other ways:
- an allow list: a passthrough may set only known engine extras. Nothing unknown gets through, but every new option
  needs a code change, and remote engines accept other options than vLLM, so the list would depend on the engine.
- lints instead of refusals: risky options would give a finding, in the spirit of "warnings, not crashes". But a
  passthrough already refuses what the rig and the output contract set, and options that put case text in the stored
  response are closer to the clearance block than to a warning.

### Reference kinds in components' JSON Schemas
The JSON Schema of each component kind could say which kinds each reference may point to. A portal form could then offer
a picker of the right kind for every reference, straight from the schema. References used to say this, and stopped
because nothing read it. The JSON Schema plays no part in any digest, so adding it back changes no digest.

## Proposed amendments

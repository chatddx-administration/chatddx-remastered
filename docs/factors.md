# Factors

An LLM can be given a case vignette in countless ways. The instructions, the sampling settings, the GPU, the model
weights and many other choices all affect what comes out. Varying each choice on its own is impractical, so we group
them into a manageable number of categories. We call these categories factors.

There is a catch-22: grouping well requires knowing *how* each choice affects the output, and that is exactly what the
research is trying to find out. So we start from a flexible set of factors based on reasonable guesses and refine it as
we learn.

Factors are the building blocks of the chatddx rig: an environment that can be rebuilt exactly, and shown to be the
same, for scientific rigor. This document describes what each factor is for and how factors combine. Names, fields,
and errors are in docs/reference/factors.md.

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

A trial's outputs therefore depend on the trial's pinned factors and on its run's recorded and observed factors. Two
runs of the same trial are interchangeable only when those agree too (docs/backlog.md, "Aggregation").

### Not factors
- Records of what happened (runs, scores, calls): [docs/ledger.md]. They hold the recorded factors and the evidence of the
  observed ones, but they aren't factors themselves.
- People, roles, authentication and authorization: [docs/identity.md].
- Names, labels, languages, tags, descriptions, owners, collaborators and version history: [docs/catalog.md].
- Sensitivity and vetting: [agents/wip-clearance.md].
- Facts from model cards: [docs/facts.md].
- Inventory: [docs/inventory.md].
- Knowledge about models (reasoning levels, recommended sampling, output caveats, specs): the model facts
  (docs/facts.md). Facts work out what a recipe's intents send when it is compiled, and check skeletons against
  engines; the skeleton holds what they did, so no factor's digest depends on them (see "Components but not
  factors").

#### Components but not factors
Most components are factors, these are the exceptions:
- Canary sets are *instruments*: fixed probe requests that measure observed factors without changing any output
  (see "Canary sets").

- Compilations are *provenance*: each says how a skeleton was made, and no component refers to one, so they change
  no digest and no output (see "Compilation").

- Model facts are *knowledge*: what is known about a model, which compiling a recipe's intents reads (see "Model
  facts"). Only a compilation refers to them, so they change no factor's digest.

## How components work

Some things live inside components or records without being components themselves: recipes (in compilations), views (in
scorers), canaries (in canary sets) and execution settings (in run records).

### Canonical form and digest
A component is written out in one fixed way, its *canonical form*, so that equal components always give the same bytes.
Its digest is the hash of those bytes, and components are told apart, and referred to, by it.

The canonical form keeps what means something and drops what doesn't:
- Order that means nothing doesn't change a digest. The keys of settings (request options, chat-template arguments,
  parameters, environment variables), a translations chunk's languages and each language's entries, a model's files
  and a trial's cases are put in a fixed order, so equivalent components share a digest.
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
- **Instruments, knowledge and provenance**: canary sets, model facts and compilations, components that aren't
  factors.

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
Code is named by its distribution, its version and, optionally, its revision. Compilations name their compiler this
way, bundles the code that wrote them, and runs and scores the code that ran them. Scorers and tools pin code chatddx
ships instead: an entry point, and the version of it the code publishes, which its developers raise when what it does
changes, as a cleanup step's name is (see "Text cleanup"). Only the code chatddx ships runs, at the version pinned, so
a deploy changes no scorer or tool unless it raises a version.

Scorers and tools pinned the running chatddx first. Each deploy then stopped every scorer until it was pinned again,
and a scorer pinned again is a new one, so every finished run was left to score again; every skeleton that offers a
tool changed too, and every trial over one.

### Storage
Components are stored in one table for all kinds, plus one row per reference so that every reference gets a foreign key
(docs/store.md; tables in docs/migrations.md, "factor"). Stored components are never changed or deleted. Anything a
component can hold can be stored: a component the store couldn't hold can't be built.

Storing a component checks it and stores everything it references; storing it again changes nothing. Reading verifies
every digest. A bundle is exported from the store, and imported by loading it and storing what it holds.

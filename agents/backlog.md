# Backlog, draft

Every open item found outside `agents/` at 2982900, moved here verbatim. Each `From` names the document, the line
at 2982900 and the section it was moved from. Ids are for grouping and triage only.

Swept: docs/ and README.md. Left where they are: `healthchecks/`, dated reports whose open findings
"address healthcheck 08ae453" carried into docs/ and agents/; docs/api.md, "Not covered", what the API leaves
to others by design; the takes in the body of docs/purist-object-layer.md, which its "Open" lists.

## Items

### docs/api.md, "Outstanding"

*Context, docs/api.md:397:*

> Left for later, each with what holds and the take on it, the agent's recommendation, which waits for a word. The
> bench's are in docs/bench.md, "Outstanding".

*Context, docs/api.md:401, "Takes the API is built on":*

> Built as the takes of the plan at 100a078 had them, and not confirmed since. Decided there: who it is for, kept open;
> FastAPI and uvicorn; signing in; and sensitive content in places of its own. Decided since: where a run runs and
> its events (see "Where it runs" and "Its events").

**api.1** · From docs/api.md:404, "Takes the API is built on"

- **Ids**: a path takes a whole id, and a name is a filter on a list, which gives every match.

**api.2** · From docs/api.md:405, "Takes the API is built on"

- **The variation**: stated whole in each request, the configuration by id and its parts by digest, with nothing
  stored by looking. A run may come to name the skeleton its look gave, and be refused when the variation compiles to
  another by then, as an edit names its head.

**api.3** · From docs/api.md:408, "Takes the API is built on"

- **Scoring**: at once after a run, with an opt-out, and the runs left to score listed.

**api.4** · From docs/api.md:409, "Takes the API is built on"

- **Errors**: the bench's errors mapped by class, and what else a route means caught where it means it, each answered
  with a code beside its detail (see "Errors").

**api.5** · From docs/api.md:411, "Takes the API is built on"

- **Keeping a variation**: a fork and an edit, two requests, rather than a save by name.

**api.6** · From docs/api.md:412, "Takes the API is built on"

- **Paths**: under `/api/`, with no version until there is a second.

**api.7** · From docs/api.md:415, "Serving"

- **A connection per request**, about 2.6 ms each over the Unix socket, opened and closed each time; one for each
  stream while it is open, and one per process listening for them all; and two for each job a worker holds. A pool
  (`psycopg_pool`) for requests and streams when a measurement says so.

**api.8** · From docs/api.md:418, "Serving"

- **A query parameter a route doesn't name is ignored**, unless the query is a model (`Varying`), so a misspelt filter
  on `GET /api/runs` or `GET /api/threads` gives everything, and a part given twice in a variation's query counts the
  last. Take: one check for every route that refuses a parameter the route doesn't declare, and a scalar given twice.

**api.9** · From docs/api.md:421, "Serving"

- **A person's runs are all read**, filtered and then paged, and with `unscored`, what is left of each is worked out
  first. Take: as is until slow, then paging by a cursor, the last run's start.

**api.10** · From docs/api.md:425, "Signing in"

- **A cookie over plain HTTP** isn't kept: a `Secure`, `__Host-` cookie needs HTTPS, or `localhost`, and a bearer works
  everywhere. Take: as is.

**api.11** · From docs/api.md:427, "Signing in"

- **`Origin` against `Host`.** A proxy that rewrites `Host` would fail the `Origin` check for a browser that sends no
  `Sec-Fetch-Site`, though today's browsers all send it. Take: as is; the public origin as a setting if it bites.

**api.12** · From docs/api.md:429, "Signing in"

- **No limit on sign-ins, and no personal tokens.** Each sign-in costs an argon2 verification, a fraction of a second
  of CPU, and a script running longer than a session signs in again. Personal tokens were decided for when a script
  needs one. Take: neither, until Keycloak is in front, which limits sign-ins itself, or a script needs a token.

**api.13** · From docs/api.md:432, "Signing in"

- **Keycloak.** How it hands the app a login isn't decided. Take: a proxy in front, such as oauth2-proxy, passes the
  login in a header the app believes from it alone, mapped onto `person.login` (docs/identity.md, "Take, for when
  Keycloak arrives"), and Keycloak's own tokens as bearers for scripts when they come.

**api.14** · From docs/api.md:435, "Signing in"

- **Roles aren't checked**; Z1 shapes what each role is shown, with the portal (docs/bench.md, "Outstanding").

### docs/bench.md, "Outstanding"

*Context, docs/bench.md:429:*

> Left for later. The API's are in docs/api.md, "Outstanding". The plan the bench was built from, with the options
> weighed for each decision and the survey of the old project, is `agents/wip-bench.md` at d5ebf52; the writes for
> the person were planned in `agents/wip-authoring.md` at b6f76b8. Its takes were built and still wait for a word:

**bench.1** · From docs/bench.md:432, its takes, built and waiting for a word

- one set of writes for every kind people author, with builders only for appendices and cases, a case built only of
  appendices the person sees, and no write refused on a lint ("Writes for the person", "Appendices and cases");

**bench.2** · From docs/bench.md:434, its takes, built and waiting for a word

- a family's cases are those at its current vignette; an appendix's edit replaces only the cases at its own
  vignette; carrying keeps to the expectation's family ("Appendices and cases");

**bench.3** · From docs/bench.md:436, its takes, built and waiting for a word

- a language is written only where a text has none ("Languages");

**bench.4** · From docs/bench.md:437, its takes, built and waiting for a word

- one write says what holds of a thread; a collaborator can't leave a share, and a thread isn't handed over ("What
  is said about a thread");

**bench.5** · From docs/bench.md:439, its takes, built and waiting for a word

- only an origin the person sees is followed, always by an edit, for every kind ("Following an origin");

**bench.6** · From docs/bench.md:440, its takes, built and waiting for a word

- the head an edit names is checked under its thread's advisory lock (docs/catalog.md, "Concurrent writers");

**bench.7** · From docs/bench.md:441, its takes, built and waiting for a word

- ownership only, roles unchecked (docs/identity.md);

**bench.8** · From docs/bench.md:442, its takes, built and waiting for a word

- the shipped lists kept in code, versions as integers from 1, an edit keeping the head's labels only when its scorer
  is the head's, and following taking each part's labels from the side whose part it keeps ("Scorers"); no resources
  offered;

**bench.9** · From docs/bench.md:445, its takes, built and waiting for a word

- configurations listed by purpose, in the API.

**bench.10** · From docs/bench.md:447

- **A case of no language** goes as written, linted `language.unknown`, rather than left out (agents/wip-engine-part.md,
  "A case of no language"); so does a case of a language the translations don't cover when the configuration's own is
  unknown.

**bench.11** · From docs/bench.md:450

- **A low-level manual for the bench**, made from `agents/wip-authoring.md` at b6f76b8.

**bench.12** · From docs/bench.md:451

- **Correcting a wrong language** stays curation's: the bench refuses a language that differs from the text's own.
  What a person may correct, such as a text only their own threads hold, is open.

**bench.13** · From docs/bench.md:453

- **Leaving a share**: a collaborator can't take a shared thread out of what they see; only the owner can. Whether
  a collaborator may withdraw themselves, an entry the catalog would hold as any other, is open.

**bench.14** · From docs/bench.md:455

- **Z1**: the map from roles to the kinds each role sees goes in `identity` once the portal's views give it meaning
  (docs/identity.md, "Z1: what each role is shown"). `sees` then takes the person's roles and the kind.

**bench.15** · From docs/bench.md:457

- **A model served at several endpoints** isn't picked from them: a run is refused until the endpoint is named, as
  the test World's two Qwen3 endpoints show; the variation page offers the picker, and a look rendered for none of
  them has no findings. A judge pins its engine as a trial does, and a judge whose engine two endpoints serve bars
  its scorer (docs/runner.md, "Judges"), which stays unlikely: it is one engine served twice.

**bench.16** · From docs/bench.md:461

- **A case's language** is its family's, read from the families the person sees, in a few queries however many
  cases (`Seen.languages`, `Seen.findings`); a case of a family they don't see is read one at a time.

**bench.17** · From docs/bench.md:463

- **The facts are read from the store each time they are asked for** (`Seen.facts`), several times a look. That is
  cheap with a facts thread per model; cache them per request if it shows.

**bench.18** · From docs/bench.md:465

- **A person's runs are all read**, and paged afterwards, in the API too (`Bench.runs`), and what is left to score is
  worked out for each of them, about 40 ms a run under five scorers. Page in the store once that is slow.

**bench.19** · From docs/bench.md:467

- **The archive's configuration saved under another name** is saved with no finding: a hand-made recipe that is a
  shared configuration's, compiled to its skeleton, becomes a thread of the person's own, and only a look's `held_by`
  says so (docs/api-api.md, "threads.py"). An expectation the same as one the person holds is refused.

**bench.20** · From docs/bench.md:470

- **Two saves of one name at once** can both create a configuration, in the repl's `save` (`docs/catalog.md`,
  "Concurrent writers").

**bench.21** · From docs/bench.md:472

- **Taking counts shared threads, not owners**: a case with two threads shared by one owner is to choose from, and
  naming that owner doesn't pick between them. Only two writers at once can leave an owner two (see "One expectation
  per case and schema").

**bench.22** · From docs/bench.md:475

- **The appendix layout as a part** a variation replaces, when someone wants to vary it. It is a value rather than a
  chunk, so a part would hold one where the others hold a digest, at every edge.

**bench.23** · From docs/bench.md:477

- **What the old bench had and this one doesn't**: what a run left unheeded (the old `outcome.py:unheeded`;
  docs/runner.md, "Smaller issues"); the old crossing of variations, which the portal is to start as several runs
  (agents/wip-portal.md, "Comparing variations"); and what holds a configuration, the portal's
  (agents/wip-portal.md), whose part for the repl `Seen.runs(reaching=…)` and `Seen.runs(scored_by=…)` cover.

**bench.24** · From docs/bench.md:481

- **A start holds a transaction open while the gate confirms its endpoint**, once per language though every run of a
  start goes to one endpoint; a few seconds at most against an endpoint that answers. Confirming once, before the
  transaction, would remove most of it.

**bench.25** · From docs/bench.md:484

- **A look for a model several endpoints serve has no findings** until an endpoint is named, where the engine as the
  part linted it for the recipe's engine; the repl's `show` shows no lints either.

**bench.26** · From docs/bench.md:486

- **A model that moved on is followed to its head whether or not an endpoint serves it**; `at` says so afterwards.

### docs/catalog.md, "Open design issues"

*Context, docs/catalog.md:395:*

> These are open questions of design. Where the code falls short of this document, the API says so
> (docs/catalog-api.md, "Known gaps").

**catalog.1** · From docs/catalog.md:399, "Concurrent writers"

The rules are checked against what is stored when a row is written. That holds with one writer at a time; with two,
only what the database enforces is sure to hold. It repeats every such rule but two: that no two families are bound to
the same vignette, by id or by content, at once, and that a person owns at most one live expectation thread per case
and expectation schema. So two people adopting the same vignette at the same moment can create two families, and two
writes at the same moment can leave a person several expectations to choose from, which scoring then refuses.

**catalog.2** · From docs/catalog.md:406, "Smaller issues"

- **Identical vignettes.** Two vignettes with the same content under different ids in one source look like a rename:
  adopting refuses the second, which a survey lists as new. Once the adopted id is gone, a survey reports both ids as
  renames of the same family.

**catalog.3** · From docs/catalog.md:409, "Smaller issues"

- **Several matching families.** When bindings of several families match a case, the latest matching binding decides,
  which needn't be the latest family's.

**catalog.4** · From docs/catalog.md:411, "Smaller issues"

- **Current bindings are compared within a source.** Surveys, adopting and repairing compare a vignette only with the
  families of its own source, which relies on a family never changing source. The database enforces that, and nothing
  in the catalog changes a source.

**catalog.5** · From docs/catalog.md:414, "Smaller issues"

- **A thread without versions** is possible in the database, and so is a family without bindings; the catalog writes
  each together with its first. A deferred constraint could rule them out at tier 2.

**catalog.6** · From docs/catalog.md:416, "Smaller issues"

- **A skeleton edit may leave out its compilation** even when one exists, and nothing can require it.

**catalog.7** · From docs/catalog.md:417, "Smaller issues"

- **A language on a skeleton that is compiled later** is ignored from then on, since the skeleton's language comes from
  its compilations.

**catalog.8** · From docs/catalog.md:419, "Smaller issues"

- **A language refused on a compiled skeleton is said to come from its recipe**, by
  `src/chatddx/catalog/language.py:check_language`, `0012`'s `language_compiled` trigger and the bench's
  `COMPILED_LANGUAGE`; a translated skeleton's comes from the language its compilation names.

**catalog.9** · From docs/catalog.md:422, "Smaller issues"

- **A translated skeleton's title doesn't say its language.** It has no thread, so it is titled by its compilation's
  recipe, as the configuration's own skeleton is.

**catalog.10** · From docs/catalog.md:424, "Smaller issues"

- **What deleting hides in the portal**: everywhere, or only in pickers, while the runs that used it stay visible.

**catalog.11** · From docs/catalog.md:425, "Smaller issues"

- **Who changed an entry or a language isn't shown.** Every row records who wrote it and when, but for these only
  what holds now is shown.

**catalog.12** · From docs/catalog.md:427, "Smaller issues"

- **Why an edit was made isn't stored.** It can be worked out by comparing consecutive versions' references.

**catalog.13** · From docs/catalog.md:428, "Smaller issues"

- **Titles take a query for every reference they visit,** are rebuilt from names that change, and aren't unique.

**catalog.14** · From docs/catalog.md:429, "Smaller issues"

- **An unnamed fork's title can pair two versions.** When the origin has no name and has moved on, the title describes
  the origin's current head, while what the fork varies is measured from the base.

**catalog.15** · From docs/catalog.md:431, "Smaller issues"

- **Following can drop a fork's renamed view.** Labels follow the views the proposal keeps, so a fork that only
  renamed a view, and follows an origin whose views it keeps, takes the origin's labels.

**catalog.16** · From docs/catalog.md:433, "Smaller issues"

- **A repair moves the current binding only.** Cases and appendices bound to an earlier binding of the family aren't
  rebuilt at the new place (docs/catalog-api.md, "families.py").

**catalog.17** · From docs/catalog.md:435, "Smaller issues"

- **Not all a model reads is in the request's language.** Chat templates add English of their own (default system
  prompts, harmony's channel instructions, tool-call scaffolding), and reasoning is often English whatever the
  prompt. The same text also takes another number of tokens in Swedish than in English, so budgets confound a
  comparison between languages.

**catalog.18** · From docs/catalog.md:439, "Smaller issues"

- **Languages are said, not checked.** Nothing compares a language with the text, and one can be replaced, so an
  analysis split by language should freeze them at export, as titles. A scorer that needs the language, for stemming,
  synonyms or an ontology, takes it from the expectation data or its resources, which are factors, not from the
  catalog at scoring time.

**catalog.19** · From docs/catalog.md:443, "Smaller issues"

- **Judges aren't checked for language.** A judge's language could be compared with the cases its scoring grades, the
  way lints check a trial's. An English judge grading Swedish answers may be intended, so it would be a notice rather
  than a warning.

**catalog.20** · From docs/catalog.md:446, "Smaller issues"

- **A variation nobody saved has a long title.** It is described by its whole recipe:
  "case · diagnoses-tool · recommended · off · qwen3-8b@pelle", where the repl called it
  "diagnoses-tool+reasoning=off": the configuration it came from and the parts set over it. A run of one is
  named so and says what it varied (see "What a run ran"), but its skeleton is still titled by its recipe.

**catalog.21** · From docs/catalog.md:450, "Smaller issues"

- **What a fork varies is compared by recipe.** A variation with a part replaced is compiled whole by the running code
  and against the facts as they are stored then (docs/bench.md, "The variation being tried"), so after a change to the
  compiler, or a corrected fact, it can send otherwise than the edit it was built on where nothing was replaced, and
  what its fork varies doesn't say so.

**catalog.22** · From docs/catalog.md:454, "Smaller issues"

- **An edit that names its head holds with several writers without the database repeating the rule**:
  each edit of a thread waits for the one before it to land. The head an edit names is held without the database
  repeating it: every edit takes its thread's advisory lock (src/chatddx/store/catalog.py:Catalog._lock).
  The writer may not update the catalog's tables, so `FOR UPDATE` isn't open to it.

### docs/catalog-api.md, "Known gaps"

*Context, docs/catalog-api.md:734:*

> From `docs/catalog.md`, "Open design issues", where they concern this API:

**catalog-api.1** · From docs/catalog-api.md:735

- The rules are checked in Python on rows read inside the writing transaction; with two writers at once only tier 2
  holds. Two `adopt` calls for one vignette at the same moment can create two families.

**catalog-api.2** · From docs/catalog-api.md:737

- Two vignettes with the same content under different ids in one source look like a rename: `adopt` refuses the
  second.

**catalog-api.3** · From docs/catalog-api.md:739

- When bindings of several families match a case, `family_of` takes the family of the latest matching binding.

**catalog-api.4** · From docs/catalog-api.md:740

- Current bindings are read per source, which relies on a family never changing source; tier 2 holds that.

**catalog-api.5** · From docs/catalog-api.md:741

- A thread without edits is possible in SQL.

**catalog-api.6** · From docs/catalog-api.md:742

- A skeleton edit may leave out its compilation.

**catalog-api.7** · From docs/catalog-api.md:743

- A language on a skeleton that is compiled later is ignored from then on.

**catalog-api.8** · From docs/catalog-api.md:744

- A case stored at a vignette's old place after a repair gets a replacement from `behind` that nothing has stored.

**catalog-api.9** · From docs/catalog-api.md:745

- When an entry, a label or a language was written isn't given, nor who wrote a label or a language:
  `Reader.entries` gives an entry's writer only.

**catalog-api.10** · From docs/catalog-api.md:747

- Why an edit was made isn't stored.

**catalog-api.11** · From docs/catalog-api.md:748

- Titles take a query for every reference they visit, are rebuilt from names that change, and aren't unique.

**catalog-api.12** · From docs/catalog-api.md:749

- Scorer labels aren't carried to the next edit of a scorer thread.

**catalog-api.13** · From docs/catalog-api.md:750

- An unnamed fork's title can pair two versions: when its origin has no name and has moved on, `title` describes the
  origin's current head but lists the changes from the base.

### docs/chatddx.md, "Possible design issues"

**chatddx.1** · From docs/chatddx.md:315

**Canary drift is not implemented:** nothing compares canary outputs between phases or runs. What counts as the
  same canary output is undecided:
  (a) the digest of each choice's message, as the old `compare_canaries` compared
  output digests;
  (b) the prompt-token fingerprint alone, which catches a changed template or tokenizer but not
  changed weights; or
  (c) both, with (b) under a code of its own. None needs a new field, since `CanaryCall.call`
  holds the response and the prompt-token fingerprint.
  A human report that the agent's take is (c)

### docs/curation.md, "Open design issues"

**curation.1** · From docs/curation.md:267, "Garbage collection"

Nothing is ever removed from the store, and a leftover is only listed. A collection run as the admin could delete what
nothing refers to: components no thread, family, run or other component reaches, and the catalog rows of what it
deletes. The tiers forbid it on purpose (docs/store.md, "Tiers"), and what counts as unreferenced must include the
ledger and every person's threads, deleted ones too, since history answers questions about the past (docs/catalog.md,
"Deleting").

*Context, docs/curation.md:274, "Import, export and verification":*

> Curation is the place for the rest of the store's authored content to come and go:

**curation.2** · From docs/curation.md:275, "Import, export and verification"

- verifying that the store holds a data set, without writing anything, which a loading's validated lines only do
  inside a transaction that writes;

**curation.3** · From docs/curation.md:277, "Import, export and verification"

- exporting what the archive or a person holds back into a data set's files, so a change made in the portal can be
  kept in git;

**curation.4** · From docs/curation.md:279, "Import, export and verification"

- importing a data set as someone other than the archive.

**curation.5** · From docs/curation.md:282, "What a data set can't hold yet"

Trials, executions, scorings and hand-written skeletons have no tables, and a data set has one expectation schema.

**curation.6** · From docs/curation.md:285, "Smaller issues"

- **One source a run.** A data set's cases all come from the source `--source` names.

**curation.7** · From docs/curation.md:286, "Smaller issues"

- **Leftovers are listed every run.** Nothing records that a leftover is known and meant to stay.

**curation.8** · From docs/curation.md:287, "Smaller issues"

- **A rename isn't followed into the data.** After repair-data, loading says the old id is missing until the data set
  names the new one.

**curation.9** · From docs/curation.md:289, "Smaller issues"

- **The runner and the engine import don't run the inventory check** that loading does.

### docs/curation.md, "Outstanding"

**curation.10** · From docs/curation.md:292

- **Staging data.** The sample is curated for preliminary calibration, and everything in it can be considered
  guessed: its targets, the appendices and `dont_miss` targets made up so that every table is used, its judge,
  drafted before Olof's, and its translations. Its notes are the exception: they are Olof's as written, and carry
  his name into every score, so none is made up; made-up notes go in the test World, under its placeholder authors.
  Data meant to be relied on needs its stage said in code, not in comments: whether it is guessed or vetted, by
  whom, and where it came from, loaded with the data so that a score can say what it rests on.

**curation.11** · From docs/curation.md:298

- **The sample's judge** is a draft over Olof's notes until his prompt replaces it, as an edit. His prompt settles
  which of his comment and answer it reads, how a Swedish note is read against an English answer, whether a verdict is
  pass or fail, a scale or one per aspect, how strict it is about extra or harmful advice, and the judge's engine and
  seeds. It is measured by real answers from pelle and malborg on `Dutchfall11w`, `Dutchfall1w` and `casesfromedn1`,
  graded by Olof with a line on why. Open beside it: notes on more cases, and revising the targets where his notes
  disagree, as on `Dutchfall11w` (shock, most likely sepsis, where the targets have an aortic aneurysm or a
  dissection).

**curation.12** · From docs/curation.md:305

- **What only the test World reaches isn't all read.** No test reads the gate refusing `qwen3-bare@fake` for `typed`
  cases, the pair lints its records give (`vllm.*` on `qwen3-bare@fake` and `clamped`, `facts.output_refused`,
  `facts.reasoning_unmatched`, `facts.budget_refused`, `language.unknown`), `headed`'s tool guidance, the texts of
  `lines-guided` translated into sv, the passthrough, or the vignettes' quirks under the cleanup steps. The lints are
  tested on synthetic registries, and two of the judge tests in src/chatddx/scorers/test/test_scorers.py use a
  synthetic judge.

### docs/factors.md, "Open design issues"

*Context, docs/factors.md:708:*

> These are open questions of design. Where the code falls short of this document, the API says so (docs/factors-api.md,
> "Known gaps").

**factors.1** · From docs/factors.md:712, "Runs of the same trial aren't interchangeable"

A trial's digest covers its pinned factors only. Its outputs also depend on its run's recorded and observed factors:
execution settings on an engine that isn't batch invariant, a remote engine that changed between runs, a tool that
answered differently. Seeds within a run are replicates; runs of the same trial are a second source of variation, and it
has no name yet.

Nothing aggregates scores today, but anything that compares or pools runs by the trial's digest alone would mix
conditions without noticing. It needs to group by the recorded factors as well, and to check the evidence of the
observed ones (prompt-token fingerprints, returned models, canaries) before pooling.

**factors.2** · From docs/factors.md:722, "Greedy sampling and seeds"

No seed is sent with greedy sampling, but a trial's seeds still count toward its digest, so two otherwise identical
greedy trials differ only in digest. Likewise, the seeds of a greedy judge all send the same request.

Keeping the seeds is deliberate. On an engine that isn't batch invariant, greedy replicates still measure
nondeterminism, and the seeds are what name the replicates. The alternative, a replicate count for greedy trials,
changes the shape of a trial, so it is cheapest decided before trials are stored for real.

**factors.3** · From docs/factors.md:730, "Smaller issues"

- **One split.** A free-text answer is broken into items only as the lines of a list (`lines@1`), so a scorer can't
  read one written otherwise, as prose or with items on one line.

**factors.4** · From docs/factors.md:732, "Smaller issues"

- **Few-shot answers in JSON are translated whole.** An example is one text, so an assistant example that is a JSON
  answer is translated as one entry, by hand, keeping its property names and allowed values as they are.

**factors.5** · From docs/factors.md:734, "Smaller issues"

- **Resources can't be picked yet.** A scorer's resources are plain strings, no kind of component holds one, and the
  scoring code isn't given them. None are offered until a kind of resource exists, with its pins and code that reads
  it.

**factors.6** · From docs/factors.md:737, "Smaller issues"

- **Canary drift isn't checked.** Nothing compares canary outputs between phases or between runs yet.

**factors.7** · From docs/factors.md:738, "Smaller issues"

- **Judge engines are never probed.** Canary probes run on the run's engine only. Probing judge engines would put
  canaries in a score's start record, as in a run's; added with defaults, they keep every stored digest.

**factors.8** · From docs/factors.md:740, "Smaller issues"

- **Skeleton provenance.** Should a skeleton be accepted only with a compilation? Hand-written ones, such as judge
  prompts, are possible today. Decided: keep hand-written skeletons, configurations without a recipe that nothing
  varies, which only the store writes. Provenance is whether a compilation names the skeleton, a question a lint can
  ask once the catalog or ledger is queried for it.

**factors.9** · From docs/factors.md:744, "Smaller issues"

- **A scoring doesn't say which cases it lacks.** Only checking a score warns, once a run is scored under it.

**factors.10** · From docs/factors.md:745, "Smaller issues"

- **Judge calls aren't fully attested.** Their returned model is checked against the judge engine's, but their
  prompt-token fingerprint isn't, as the request would have to be rebuilt from the answer as the scorer read it.

**factors.11** · From docs/factors.md:747, "Smaller issues"

- **Every engine is asked for the prompt's token ids.** A remote engine that isn't vLLM may refuse the unknown option.
  Either the engine says whether it takes it, which changes the engine's digest, or the runner decides per call, which
  leaves the run without prompt-token fingerprints.

**factors.12** · From docs/factors.md:750, "Smaller issues"

- **A scoring's digest depends on the order of its expectations.** Its expectations aren't put in a fixed order as a
  trial's cases are, so the same expectations in another order make another scoring. The person reads build them in the
  trial's case order.

**factors.13** · From docs/factors.md:753, "Smaller issues"

- **Four cleanup steps exist.** Vignettes may also need non-breaking spaces turned into spaces, zero-width characters
  removed, Unicode line breaks turned into newlines, or trailing whitespace stripped.

**factors.14** · From docs/factors.md:755, "Smaller issues"

- **Hardware has no GPU count,** so engines that split a model across GPUs can't be told apart by their hardware. Nor
  does it say the CPU, the RAM, the GPU's uuid, the machine's id or where it is.

**factors.15** · From docs/factors.md:757, "Smaller issues"

- **Tool parameters whose root isn't an object.** OpenAI's API is reported to refuse function parameters whose root
  isn't `type: object`. Unverified; a candidate lint for tools on a remote engine.

### docs/factors.md, "Potential design improvements"

**factors.16** · From docs/factors.md:763, "Execution settings as a component"

Today execution settings are a value inside each run's start record: recorded, sealed with the run's log, and compared
by value. They have no digest, so the catalog can't name a set of settings (for example "sequential" or "8-way"), the
portal can't offer them for picking, and finding the runs that used the same settings means comparing values across run
records.

Making them a component of a new kind, which the start record references by digest, would give them a name, a catalog
thread and a foreign key like the pinned factors. They would still stay out of the trial's digest, so this changes how
execution settings are stored, not what a trial means. The cost is a new kind (with the catalog's thread kinds and their
migration) and a change to the run record.

**factors.17** · From docs/factors.md:774, "Chat templates as components"

Today a local engine pins its chat template by the file's hash, like the model files: a world input, fetched from
wherever the inventory says it is. A bundle therefore holds the template's hash but not the template, and only a host
with the file in hand can read it.

Making the template a component of a new kind, holding the template's text, that the engine references by digest, would
put it inside the bundle: it is small and not sensitive, so a bundle could rebuild the engine's prompt formatting
offline. Lints could read it too, so the check for templates that read the current date would run when factors are
linted, not only on a host. Engines sharing a template would share the component. It would move the template from world
input to authored factor, and cost a new kind (with the catalog's thread kinds and their migration) and a change to the
template check.

**factors.18** · From docs/factors.md:786, "Splitting expectations"

If expectations written as free text turn up, a view could split them too. Two ways:
- a separate split for the expectation side, next to the output's. It is additive: with none as its default, every
  existing digest stays the same, and each side gets the split it needs.
- one split for both sides. That changes the meaning of an existing field, so the scorer's schema version would have to
  go up, and the two sides rarely need the same split.

**factors.19** · From docs/factors.md:793, "Finding code through packaging entry points"

Today chatddx keeps the list of the code it ships in its code: `src/chatddx/scorers/shipped.py` and
`src/chatddx/tools/shipped.py`, by the entry point a component names. Packaging metadata changes only when the package
is installed again, and tests add tools of their own to the list for as long as they run
(src/chatddx/runner/test/tools.py:shipped). Packaging entry points would fit code from other distributions, which
nothing runs today.

**factors.20** · From docs/factors.md:800, "Passthrough: an allow list, or lints"

A passthrough refuses a fixed list of options and lets everything else through. Two other ways:
- an allow list: a passthrough may set only known engine extras. Nothing unknown gets through, but every new option
  needs a code change, and remote engines accept other options than vLLM, so the list would depend on the engine.
- lints instead of refusals: risky options would give a finding, in the spirit of "warnings, not crashes". But a
  passthrough already refuses what the rig and the output contract set, and options that put case text in the stored
  response are closer to the clearance block than to a warning.

### docs/factors-api.md, "Known gaps"

*Context, docs/factors-api.md:1056:*

> From `docs/factors.md`, "Open design issues", where they concern this API:

**factors-api.1** · From docs/factors-api.md:1057

- `tool_calls` skips a malformed call, but `next_request` copies the response's `tool_calls` as they are, so the
  next request holds a call that no `tool` message answers.

**factors-api.2** · From docs/factors-api.md:1059

- NaN and infinity pass validation, and the canonical form writes them as `null`. The stored component reads back
  with the field unset, under the same digest, and `Bundle.load` reports `bundle.recanonicalized`. The request still
  carries the NaN.

**factors-api.3** · From docs/factors-api.md:1062

- `Scorer.resources` are meant to be digests but are typed as plain strings.

**factors-api.4** · From docs/factors-api.md:1063

- `Scoring.expectations` isn't sorted, so its order changes the digest.

**factors-api.5** · From docs/factors-api.md:1064

- `render` sends `return_token_ids` to every engine by default; a remote engine that isn't vLLM may refuse it.

**factors-api.6** · From docs/factors-api.md:1065

- `argv` is checked without vLLM's list of flags: a bare argument after a flag that takes no value passes, and lints
  don't expand abbreviated flags.

**factors-api.7** · From docs/factors-api.md:1067

- `Hardware` has no GPU count.

**factors-api.8** · From docs/factors-api.md:1068

- Nothing checks that a compilation's recipe compiles to its skeleton.

### docs/facts.md, "Open design issues"

*Context, docs/facts.md:142:*

> These are open questions of design. Where the code falls short of this document, the API says so
> (docs/facts-api.md, "Known gaps").

**facts.1** · From docs/facts.md:145

- **xhigh can't be written.** It's a level, but no reasoning effort says it, so a model can only collapse or refuse
  it. Adding the effort is additive, if a model that supports it shows up.

**facts.2** · From docs/facts.md:147

- **Tool choice on harmony.** Named and required tool choices are unverified for gpt-oss. vLLM 0.24's gpt-oss tool
  parser accepts both, so the JSON-array grammar applies; whether harmony's output survives it isn't known.

**facts.3** · From docs/facts.md:149

- **A model or a model on a runtime.** Some facts are really about a model on a runtime, such as harmony ignoring the
  response format. They live on the model for now; facts keyed by runtime can be added when a second runtime
  appears.

**facts.4** · From docs/facts.md:152

- **Defaults from the command line.** An engine's own default chat template arguments and generation config change
  the model's defaults. Facts describe the model's own defaults, and only the grammar-before-reasoning lint accounts
  for the change.

**facts.5** · From docs/facts.md:157, "Smaller issues"

- **A budget with reasoning off is compiled.** Qwen3's off with a budget turns thinking off and sets a thinking
  budget.

**facts.6** · From docs/facts.md:159, "Smaller issues"

- **Unread recommendations.** A recommendation for a level that collapses, or lands on its nearest, is never
  compiled, and nothing reports it. Checking pairs still counts it as the model's.

**facts.7** · From docs/facts.md:161, "Smaller issues"

- **An unknown budget passes the check.** A budget sent to a model whose budget is unknown isn't warned about, while
  compiling one beside a level is refused.

**facts.8** · From docs/facts.md:163, "Smaller issues"

- **Unknown reasoning fails the check.** A skeleton's reasoning settings are compared only with the ways of asking the
  facts know, so a model whose reasoning is unknown, or a skeleton using a level nothing is known about, gets the
  warning, though a missing part otherwise means "unknown".

**facts.9** · From docs/facts.md:166, "Smaller issues"

- **A refused default is accepted.** A default that lands on a refusal loads, and whether the model reasons by default
  is then unknown.

### docs/facts-api.md, "Known gaps"

*Context, docs/facts-api.md:288:*

> From `docs/facts.md`, "Open design issues":

**facts-api.1** · From docs/facts-api.md:289

- `xhigh` can't be written: neither `Writes.effort` nor `Reasoning.effort` has the value.

**facts-api.2** · From docs/facts-api.md:290

- Named and `required` tool choices are unverified for gpt-oss.

**facts-api.3** · From docs/facts-api.md:291

- Some facts are about a model on a runtime, and live on the model.

**facts-api.4** · From docs/facts-api.md:292

- An engine's `--default-chat-template-kwargs` and `--generation-config` change the model's defaults; only
  `vllm.grammar_before_reasoning` accounts for the first.

**facts-api.5** · From docs/facts-api.md:294

- A budget with reasoning off is compiled.

**facts-api.6** · From docs/facts-api.md:295

- A `sampling.recommended` entry for a level that collapses, or lands on its nearest, is never asked for by
  `ModelFacts.recommended`, and nothing reports it.

**facts-api.7** · From docs/facts-api.md:297

- An unknown budget passes `facts.budget_refused`, while compiling one beside a level refuses it (`check_budget`).

**facts-api.8** · From docs/facts-api.md:298

- Unknown reasoning fails `facts.reasoning_unmatched`: a model without writes at any level, or a skeleton using a
  level nothing is known about, gets the warning.

**facts-api.9** · From docs/facts-api.md:300

- A `default` that lands on a refusal loads, and `reasons_by_default` then says `None`.

### docs/identity.md, "Open design issues"

**identity.1** · From docs/identity.md:96

- **A new password doesn't end sessions.** `chatddx person password` replaces the hash, and a session opened with the
  old password stays until it expires; only making the person inactive ends their sessions.

**identity.2** · From docs/identity.md:98

- **Sign-ins aren't limited.** Each costs an argon2 verification. The API's take is none until Keycloak is in front,
  which limits them itself (docs/api.md, "Outstanding").

**identity.3** · From docs/identity.md:100

- **Nobody administers people through chatddx.** The admin role exists, but nothing asks for it, and the commands
  connect as `DB_USER`, so whoever reaches the database adds people.

**identity.4** · From docs/identity.md:102

- **No command changes a person**: their name, roles, or whether they are active (`People.update`).

**identity.5** · From docs/identity.md:103

- **What each role is shown** isn't written (see "Authorization").

### docs/identity.md, "Takes on what is open"

*Context, docs/identity.md:106:*

> "Open design issues" lists these too; here are the takes.

*Context, docs/identity.md:108:*

> `docs/identity.md`, "Open design issues", lists these too; here are the takes.

**identity.6** · From docs/identity.md:111, "Z1: what each role is shown"

Decided: authorization goes by role first, which kinds a role sees, then by the catalog's owners and collaborators. The
map from roles to kinds isn't written; it needs the portal's views to mean anything.

Take: the map goes beside `sees` in `src/chatddx/identity/identity.py`, as data, and `sees` then takes the person's
roles and the kind as well as the `Owned`. The kinds each role authors can go beside it, clinicians appendices,
expectations and typed cases, researchers chunks and recipes, as a convenience for the portal's forms rather than a
refusal.

**identity.7** · From docs/identity.md:120, "Who may administer people"

`Role.ADMIN` exists, but nothing asks for it, and `chatddx person` connects as `DB_USER`, so anyone with database
access adds people. No command changes a person's name, roles or whether they are active (`People.update`).

**identity.8** · From docs/identity.md:124, "Expired sessions and sign-ins"

Expired sessions are removed whenever a session is opened (`People.open_session`). Sign-ins aren't limited;
`docs/api.md`, "Outstanding", takes none until Keycloak is in front.

**identity.9** · From docs/identity.md:128, "Take, for when Keycloak arrives"

Keycloak, or a proxy in front such as oauth2-proxy, authenticates, and the app maps its username onto `person.login`,
which is why logins are lowercase like Keycloak's. Password login can stay as the development path. Roles could then
come from Keycloak's realm roles instead of the column; not decided.

**identity.10** · From docs/identity.md:133, "What could move to identity"

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

### docs/inventory.md, "Open design issues"

*Context, docs/inventory.md:267:*

> These are open questions of design. Where the code falls short of this document, the API says so
> (docs/inventory-api.md, "Known gaps").

**inventory.1** · From docs/inventory.md:271, "Checks happen when an entry is used"

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

**inventory.2** · From docs/inventory.md:284, "Hosts don't read the start-up"

o11n and the hosts' own configuration (Kompismoln/org) decide what each server runs. The rig imports what they run,
and the start-up of an imported endpoint gives back the command line o11n runs. So the start-up is a check, and only
the fake vLLM is started from one. For a host to start its engines from the rig's start-up, o11n would have to read
it, and the import would then confirm what was started rather than describe it.

**inventory.3** · From docs/inventory.md:290, "Smaller issues"

- **Endpoint names are only a convention.** Nothing enforces server@host. A run records the endpoint's name, and
  clearance keys on it, so renaming an endpoint drops its clearance without warning, and its runs appear under two
  names.

**inventory.4** · From docs/inventory.md:293, "Smaller issues"

- **The capacity holds per run.** Two runs on one endpoint can send twice as many requests between them. vLLM queues
  what's over its limit, so nothing fails, but the batching differs from what each run's execution says.

**inventory.5** · From docs/inventory.md:295, "Smaller issues"

- **Model files aren't checked against the hub.** huggingface_hub keeps the commit's file listing from the download
  (`<repo>/trees/<commit>.json`): the hub's SHA-256 of each LFS file and the git blob hash of the rest. The report
  could compare every file it hashes with it, offline. The import takes the host's hashes as they are.

### docs/inventory-api.md, "Known gaps"

*Context, docs/inventory-api.md:265:*

> From `docs/inventory.md`, "Open design issues":

**inventory-api.1** · From docs/inventory-api.md:266

- The runner and the engine import don't run `check`: they check an entry when they use it.

**inventory-api.2** · From docs/inventory-api.md:267

- Hosts don't start engines from the start-up; only the fake vLLM is started from one.

**inventory-api.3** · From docs/inventory-api.md:268

- Endpoint names are only a convention, and renaming one drops its clearance.

**inventory-api.4** · From docs/inventory-api.md:269

- `max_jobs` holds per run, not per endpoint.

### docs/ledger.md, "Open design issues"

*Context, docs/ledger.md:240:*

> These are open questions of design. Where the code falls short of this document, the API says so
> (docs/ledger-api.md, "Known gaps").

*Context, docs/ledger.md:244, "Some of what happened isn't checked":*

> Most of the plan is compared with what happened (see "What a record holds"), but not all:

**ledger.1** · From docs/ledger.md:245, "Some of what happened isn't checked"

- timeouts: a call's times span all its attempts, so an attempt that ran past the timeout can't be told from them.
  Recording each attempt's times, status and error would tell them; a call keeps only the last refusal's body, as its
  response;

**ledger.2** · From docs/ledger.md:248, "Some of what happened isn't checked"

- the request a call sent and the request it should have been:
  The repl's replay rebuilds each item's first request from the trial and the vignette and holds it to the call's
  fingerprint. A later round's request, which could be rebuilt from the stored responses and tool runs, and a judge
  request, from the scorer's reading of the answer (docs/factors.md, "Judge"), aren't rebuilt, and checking a run
  rebuilds none.

**ledger.3** · From docs/ledger.md:255, "Smaller issues"

- **Prompt-token drift isn't checked.** Checking a run notes the items without a prompt-token fingerprint, but
  nothing compares the fingerprints between runs, though that is what they are kept for.

**ledger.4** · From docs/ledger.md:257, "Smaller issues"

- **Canary drift isn't checked.** Nothing compares canary outputs between phases or between runs.

**ledger.5** · From docs/ledger.md:258, "Smaller issues"

- **Only run items are fully attested.** Judge calls get the model check but no prompt check, and canary calls get
  neither.

**ledger.6** · From docs/ledger.md:260, "Smaller issues"

- **The system fingerprint is kept but never compared** between calls or runs.

**ledger.7** · From docs/ledger.md:261, "Smaller issues"

- **The finish record is outside the seal.** Its time and findings could change without the seal noticing.

**ledger.8** · From docs/ledger.md:262, "Smaller issues"

- **Records aren't in bundles.** A bundle (docs/factors.md, "Registries and bundles") carries components only; how
  records travel with the factors they reference, for example for publication, isn't specified.

**ledger.9** · From docs/ledger.md:264, "Smaller issues"

- **Findings have no mechanism of their own.** The runner and the scoring pass keep those they see in the finish record,
  and the checks give the rest when called. They might benefit from a separate mechanism, as lints are for factors, but
  nothing is planned or decided.

### docs/ledger-api.md, "Known gaps"

*Context, docs/ledger-api.md:545:*

> From `docs/ledger.md`, "Open design issues", where they concern this API:

**ledger-api.1** · From docs/ledger-api.md:546

- `Execution.timeout_s` isn't checked: a call's times span all its attempts.

**ledger-api.2** · From docs/ledger-api.md:547

- Nothing here rebuilds a request to compare with `Call.request`; the bench rebuilds an item's first
  (`chatddx.runner.prepare.rendered_again`), not a later round's or a judge's.

**ledger-api.3** · From docs/ledger-api.md:549

- Prompt-token fingerprints aren't compared between runs; `check_run` notes only the items without one.

**ledger-api.4** · From docs/ledger-api.md:550

- Canary outputs aren't compared between phases or runs.

**ledger-api.5** · From docs/ledger-api.md:551

- Canary calls get no model check, and neither canary calls nor judge calls a prompt-token check.

**ledger-api.6** · From docs/ledger-api.md:552

- A response's `system_fingerprint` is never compared.

**ledger-api.7** · From docs/ledger-api.md:553

- The finished row is outside the seal: its `at` and `findings` can change without `ledger.seal`.

**ledger-api.8** · From docs/ledger-api.md:554

- Records don't travel in a `Bundle`.

**ledger-api.9** · From docs/ledger-api.md:555

- Findings have no mechanism of their own beyond the finished rows and the check functions.

### docs/purist-object-layer.md, "Open"

**purist-object-layer.1** · From docs/purist-object-layer.md:214

- The name, should the split happen (see "Naming").

**purist-object-layer.2** · From docs/purist-object-layer.md:215

- `kind` as a class keyword (see "Kinds written down").

**purist-object-layer.3** · From docs/purist-object-layer.md:216

- Whether canary sets and compilations ever move.

**purist-object-layer.4** · From docs/purist-object-layer.md:217

- Where `refuse_change` lives.

**purist-object-layer.5** · From docs/purist-object-layer.md:218

- Whether execution settings become an object, which this take doesn't decide.

### docs/repl.md, "Open design issues"

**repl.1** · From docs/repl.md:248, "What the repl doesn't reach"

- It reaches four of the bench's writes (`save`, `start`, `score`, `take`); the API reaches them all.

**repl.2** · From docs/repl.md:249, "What the repl doesn't reach"

- A thread with a title and no name can't be named.

**repl.3** · From docs/repl.md:250, "What the repl doesn't reach"

- A run takes one seed, and no execution settings, canary set or text cleanup; `score` can't pick a scorer, score a
  run again, or name the endpoint a judge is called at, so a judge whose engine two endpoints serve bars its scorer.

**repl.4** · From docs/repl.md:254, "Smaller issues"

- **No word on reasoning that wasn't heeded**, and no `[thinking in content]`: the runner can't tell reasoning a parser
  missed (docs/runner.md, "Smaller issues").

**repl.5** · From docs/repl.md:256, "Smaller issues"

- **Two tool calls in one response run together** on one line as they stream, as a call's first delta is taken as its
  name and the deltas don't say where the next begins; `replay` splits them.

**repl.6** · From docs/repl.md:258, "Smaller issues"

- **Only an item's first request is rendered again**; a later round's could be rebuilt from the stored responses and
  tool runs.

### docs/repl.md, "Outstanding"

*Context, docs/repl.md:262:*

> Suggested, and left for later:

**repl.7** · From docs/repl.md:263

- **`diagnoses` applies to a plan**, since a plan's `$.diagnoses[*]` reaches its schema, but the items are objects, so
  its differential lists them as JSON and scores their text. A reach that knew the type of what a view picks would leave
  it out, as `View.offered_by` leaves whole-answer views out of structured runs.

**repl.8** · From docs/repl.md:266

- **`runs` doesn't show a start.** A translated run says the language it was sent in, the run of the configuration's
  own language from the same start says none, and nothing says the two were started together; the API's
  `GET /api/runs?with=` and a run's page in the portal do (`Bench.runs(started_with=…)`).

**repl.9** · From docs/repl.md:269

- **The judge lines aren't aligned**, as their labels differ in length; the labels of a scoring's judge calls are known
  when it starts, so their width could be too.

### docs/runner.md, "Open design issues"

**runner.1** · From docs/runner.md:212, "What a stop leaves out"

- **A call still waiting for its engine to answer at all**, under an execution with no timeout, waits on after a halt;
  only a stream can be shut down. vLLM answers at once and streams after. The bench sends no execution, so its runs
  have no timeout.

**runner.2** · From docs/runner.md:217, "Smaller issues"

- **Tools have no time limit of their own**, and a halt waits for a tool that's running.

**runner.3** · From docs/runner.md:218, "Smaller issues"

- **The tool interface isn't versioned**, unlike the scorer's: keyword arguments in, text out.

**runner.4** · From docs/runner.md:219, "Smaller issues"

- **The answer tool called beside a toolset tool** ends the item, and checking the run notes the other call; no engine
  under test does that. Checking the run doesn't refuse a turn that runs the other call, though the runner never
  writes one.

**runner.5** · From docs/runner.md:222, "Smaller issues"

- **No World's endpoint names a canary set**, though data sets hold them; canary outputs aren't compared
  (docs/chatddx.md, "Possible design issues"), and canary calls stream without events.

**runner.6** · From docs/runner.md:224, "Smaller issues"

- **Fingerprints are unkeyed.** Neither `send` nor the ledger takes a key for a call's fingerprints
  (docs/factors.md, "Fingerprints").

**runner.7** · From docs/runner.md:226, "Smaller issues"

- **Judge calls go one at a time**, and every judged scoring confirms its judges' endpoints, even when no item needs a
  judge; an endpoint that hangs holds it up to the confirmation's timeout.

**runner.8** · From docs/runner.md:228, "Smaller issues"

- **Every engine is asked for the prompt's token ids** (docs/factors.md, "Smaller issues").

**runner.9** · From docs/runner.md:229, "Smaller issues"

- **No finding for reasoning that wasn't heeded**, as the old chatddx had.

**runner.10** · From docs/runner.md:230, "Smaller issues"

- **`max_jobs` across runs** belongs to the worker, and so does asking for a lost run to resume.

### docs/runner-api.md, "Known gaps"

*Context, docs/runner-api.md:328:*

> From `docs/runner.md`, "Open design issues", where they concern this API:

**runner-api.1** · From docs/runner-api.md:329

- A halt can't end a call waiting for its response's headers.

**runner-api.2** · From docs/runner-api.md:330

- `Toolbox.run` has no time limit.

**runner-api.3** · From docs/runner-api.md:331

- Canary calls emit no `Streamed`.

**runner-api.4** · From docs/runner-api.md:332

- `send.send` takes a `key`, but nothing in the package passes one.

**runner-api.5** · From docs/runner-api.md:333

- `Runner.score` refuses judge calls above concurrency 1, and confirms every judge's endpoint, even when no item
  needs a judge.

**runner-api.6** · From docs/runner-api.md:335

- `send` again after a worker's exception isn't tested.

### docs/scripted.md, "Open design issues"

**scripted.1** · From docs/scripted.md:105, "No scripted run has tool rounds"

The gate refuses tools on a sensitive source (docs/runner.md, "The gate"), and both Worlds' sources are sensitive, as
a real one is, so no scripted run can send a tool round on their cases. The old chatddx's sample runs `broken` and
`rich` searched the web. A take: a made-up source that isn't sensitive, once calibration wants a tool round to show,
with the web patched in the process that runs the tools (`urllib.request.urlopen`, src/chatddx/tools/web_search.py).

**scripted.2** · From docs/scripted.md:111, "Smaller issues"

- **No scripted run sends a canary set**: the Worlds' endpoints name none (docs/inventory.md, "Endpoints"), and a
  scripted run's turns would have to answer its canaries too.

**scripted.3** · From docs/scripted.md:113, "Smaller issues"

- **No two scripted runs vary a part over the same cases**, as the page to compare runs wants
  (agents/wip-portal.md, "Comparing variations").

**scripted.4** · From docs/scripted.md:115, "Smaller issues"

- **`set` and `--again` have no test**, and no scripted run sets a part.

### docs/store.md, "Known gaps"

*Context, docs/store.md:123:*

> These are known shortcomings of the store's design. Some have more details in docs/store-api.md.

**store.1** · From docs/store.md:124

- Applied migrations are known by name only, so a migration file edited after a database applied it isn't noticed,
  and that database silently differs from the files. Before a shared database, applied files are frozen, or their
  checksums kept with their names.

**store.2** · From docs/store.md:127

- The database doesn't check that a component has all its reference rows, only that the rows it has are right; the
  store writes them together.

**store.3** · From docs/store.md:129

- The database allows a thread without versions; the catalog writes a thread together with its first version.

**store.4** · From docs/store.md:130

- The database can't keep text holding a NUL character, so a component or record containing one can't be stored.

**store.5** · From docs/store.md:131

- The copy of each component and record kept for queries reorders object keys, so a schema's property order survives
  only in the stored text. Components and records are read from the stored text, and a future ORM or view must not
  rebuild them from the copy.

**store.6** · From docs/store.md:134

- No async API. The runner is synchronous, and wants each row to land as it is written. On a connection that doesn't
  commit each statement by itself, a write outside a transaction opens one that only the caller commits, and the
  store's own transactions become savepoints inside it.

**store.7** · From docs/store.md:137

- Read-only views per kind of component, for a future ORM, aren't written.

**store.8** · From docs/store.md:138

- A log can be written that can't be read back. Storing a record checks only what the database can, and a finish
  record isn't tied to its start record, so a finish record alone is accepted; reading the log back then reports that
  it has no start record. Logs are validated only when they are read.

**store.9** · From docs/store.md:141

- A run's canary set isn't tied to the run in the database, so a run can name a canary set that isn't stored, and
  then can't be checked.

**store.10** · From docs/store.md:143

- A schema-version bump strands stored rows. Reading parses every row, and parsing refuses another version
  (docs/factors.md, "Versions"; docs/ledger.md, "Canonical form and versions"), so after a bump the store can't return
  rows of the old version, nor load a closure that holds one. The rows can't be rewritten either: the tables are
  append-only, and digests and seals depend on the bytes. docs/factors.md, "Splitting expectations", already considers
  a bump of the scorer's schema version.

### docs/store-api.md, "Known gaps"

*Context, docs/store-api.md:398:*

> From `docs/store.md`, "Known gaps", where they concern this API:

**store-api.1** · From docs/store-api.md:399

- The database doesn't check that a component has all its reference rows; `Store.add` writes them together.

**store-api.2** · From docs/store-api.md:400

- The database allows a thread without edits; `Catalog.create` writes both in one transaction.

**store-api.3** · From docs/store-api.md:401

- `jsonb` rejects `\u0000`, so a component or record holding NUL can't be stored.

**store-api.4** · From docs/store-api.md:402

- `doc` reorders object keys; components and records must be read from `canonical` and `payload`.

**store-api.5** · From docs/store-api.md:403

- No async API, and on a connection that isn't in autocommit mode, writes wait for the caller's commit.

**store-api.6** · From docs/store-api.md:404

- No per-kind read-only views.

**store-api.7** · From docs/store-api.md:405

- A log can be written that can't be read back: a finished row is accepted without its started row, and `Store.run`
  and `Store.score` then raise `StructuralError("<log> <id> has no started row")`.

**store-api.8** · From docs/store-api.md:407

- `RunStarted.canaries` has no foreign key.

**store-api.9** · From docs/store-api.md:408

- A schema-version bump strands stored rows: `get`, `load`, `run` and `score` refuse another version, and the rows
  can't be rewritten.

### docs/worker.md, "Open design issues"

**worker.1** · From docs/worker.md:109, "The repl beside the worker"

The repl sends in its own process, and its runs don't count against an endpoint's `max_jobs`. It could queue its runs
and follow their events, or send in its own process but hold slots in the queue, as a worker claiming its own job.
Take: as it is, and holding slots once endpoints are shared and busy.

**worker.2** · From docs/worker.md:114, "Fairness between owners"

Decided: queue order, as built, then turns per owner at each endpoint once people wait on each other. Turns aren't
built.

**worker.3** · From docs/worker.md:118, "The deployment"

Decided: the HTTP server, the API and the worker as separate systemd services on NixOS. The flake has no NixOS module
yet, and its stop timeout is to exceed the worker's deadline. What the HTTP server is stays open: the portal's pages
served apart from the API, or a proxy in front of both; the portal is one app with the API (agents/wip-portal.md, "P3b,
concretely"), and its `__Host-` cookie wants one host for both.

**worker.4** · From docs/worker.md:124, "Smaller issues"

- **`max_jobs` beside the worker.** The repl's runs and judge calls don't count. vLLM queues what's over
  `--max-num-seqs` rather than refusing it, so the cost is batching that the runs' executions don't show.

**worker.5** · From docs/worker.md:126, "Smaller issues"

- **The rows' order is their writer's.** A stream reads the rows after the last it told; a row committed after one
  with a higher number would be missed until the stream starts again. One writer per run keeps the two orders alike:
  the queue holds one job open per run, and a log's rows are written one transaction after another. A repl scoring a
  run while the worker writes it doesn't.

**worker.6** · From docs/worker.md:130, "Smaller issues"

- **What isn't a row is told only to those listening**, so a stream that joins after a scoring started misses
  `run.scoring`. Notes along the way are told with the finish row that holds them, not as they happen.

**worker.7** · From docs/worker.md:132, "Smaller issues"

- **Connections.** Each stream holds one while it is open, each app process one listening for them all, and the worker
  two for each job it holds.

**worker.8** · From docs/worker.md:134, "Smaller issues"

- **A stopping worker's sending has no deadline**: its runs stop after the items under way, however long they take,
  and a service's stop timeout kills it before then, leaving the job to be claimed again once it is lost and the items
  to be sent again. Halting them at the deadline would record them stopped, and they wouldn't be sent again.

**worker.9** · From docs/worker.md:137, "Smaller issues"

- **A halted run is finished**, so a run stopped with the second press can't be resumed; leaving it unfinished would
  record its calls under way as stopped, and its items wouldn't be sent again.

**worker.10** · From docs/worker.md:139, "Smaller issues"

- **A call still waiting for its engine to answer at all** waits on after a halt (docs/runner.md, "What a stop leaves
  out"), and the job's thread with it.

**worker.11** · From docs/worker.md:141, "Smaller issues"

- **`NOTIFY`'s queue**: a payload waits in the database's notification queue, kept on disk, until every listener has
  read it, and a listener that stops reading holds the queue up for all. Deltas are sensitive, and pass through the
  database that holds the ledger's completions already.

**worker.12** · From docs/worker.md:144, "Smaller issues"

- **"Ahead" counts jobs, not items**, and the workers seen are counted for anyone's jobs, not the person's endpoints.

**worker.13** · From docs/worker.md:145, "Smaller issues"

- **A job at an endpoint the inventory lost** is claimed and fails at the gate, rather than waiting.

### docs/chatddx.md, inline

**chatddx.2** · From docs/chatddx.md:288, in "Intended dataflow"

What aggregates them isn't named yet.

### docs/factors.md, inline

**factors.21** · From docs/factors.md:209, in "Cases"

Whether a person or an automatic step rebinds them is open; the catalog has the tools for it (docs/catalog.md).

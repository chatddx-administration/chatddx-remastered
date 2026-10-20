# Backlog, triage record

Every open item found outside `agents/` at 2982900, moved here verbatim. Each `From` names the document, the line
at 2982900 and the section it was moved from. Ids are for grouping and triage only.

Swept: docs/ and README.md; docs/chatddx.md's "On the table" and "Work in progress" were found late, during triage. Left
where they are: `healthchecks/`, dated reports whose open findings "address healthcheck 08ae453" carried into docs/ and
agents/; docs/api.md, "Not covered", what the API leaves to others by design; the takes in the body of
docs/purist-object-layer.md, which its "Open" lists; docs/vllm.md, "Not emulated", which the fake's "Extending" works
from.

Grouped by whether they'd fit in one PR, triaged group by group, and moved to docs/backlog.md, by readiness; the
references to them were swept. What is left here is the triage's record: the takes it confirmed, what it dropped and
why, and the moved sections' context.

## Confirmed
Takes confirmed in triage, now decisions; bench.4's "a collaborator can't leave a share" is overturned by
docs/backlog.md, "A collaborator leaves a share":

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

**bench.2** · From docs/bench.md:434, "Outstanding", its takes, built and waiting for a word

- a family's cases are those at its current vignette; an appendix's edit replaces only the cases at its own
  vignette; carrying keeps to the expectation's family ("Appendices and cases");

**bench.3** · From docs/bench.md:436, "Outstanding", its takes, built and waiting for a word

- a language is written only where a text has none ("Languages");

**bench.4** · From docs/bench.md:437, "Outstanding", its takes, built and waiting for a word

- one write says what holds of a thread; a collaborator can't leave a share, and a thread isn't handed over ("What
  is said about a thread");

**bench.5** · From docs/bench.md:439, "Outstanding", its takes, built and waiting for a word

- only an origin the person sees is followed, always by an edit, for every kind ("Following an origin");

**bench.8** · From docs/bench.md:442, "Outstanding", its takes, built and waiting for a word

- the shipped lists kept in code, versions as integers from 1, an edit keeping the head's labels only when its scorer
  is the head's, and following taking each part's labels from the side whose part it keeps ("Scorers"); no resources
  offered;

**bench.9** · From docs/bench.md:445, "Outstanding", its takes, built and waiting for a word

- configurations listed by purpose, in the API.

**bench.10** · From docs/bench.md:447, "Outstanding"

- **A case of no language** goes as written, linted `language.unknown`, rather than left out (agents/wip-engine-part.md,
  "A case of no language"); so does a case of a language the translations don't cover when the configuration's own is
  unknown.

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
endpoint's capacity across workers, and resume a lost run (docs/worker.md, "Claiming"):

**inventory.4** · From docs/inventory.md:293, "Open design issues", "Smaller issues"

- **The capacity holds per run.** Two runs on one endpoint can send twice as many requests between them. vLLM queues
  what's over its limit, so nothing fails, but the batching differs from what each run's execution says.

**inventory-api.4** · From docs/inventory-api.md:269, "Known gaps"

- Capacity holds per run, not per endpoint.

**runner.10** · From docs/runner.md:230, "Open design issues", "Smaller issues"

- **Capacity across runs** belongs to the worker, and so does asking for a lost run to resume.

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

api.10 and api.11, from G38, as holding: the NixOS module's nginx forces HTTPS and passes `Host` on
(`nix/module.nix`, `forceSSL`, `recommendedProxySettings`):

**api.10** · From docs/api.md:425, "Outstanding", "Signing in"

- **A cookie over plain HTTP** isn't kept: a `Secure`, `__Host-` cookie needs HTTPS, or `localhost`, and a bearer works
  everywhere. Take: as is.

**api.11** · From docs/api.md:427, "Outstanding", "Signing in"

- **`Origin` against `Host`.** A proxy that rewrites `Host` would fail the `Origin` check for a browser that sends no
  `Sec-Fetch-Site`, though today's browsers all send it. Take: as is; the public origin as a setting if it bites.

api.12, identity.2 and identity.8, from G38, as tracked in agents/wip-clearance.md ("Before real patient data", 1);
the NixOS module's nginx limits sign-ins per address:

**api.12** · From docs/api.md:429, "Outstanding", "Signing in"

- **No limit on sign-ins, and no personal tokens.** Each sign-in costs an argon2 verification, a fraction of a second
  of CPU, and a script running longer than a session signs in again. Personal tokens were decided for when a script
  needs one. Take: neither, until Keycloak is in front, which limits sign-ins itself, or a script needs a token.

**identity.2** · From docs/identity.md:98, "Open design issues"

- **Sign-ins aren't limited.** Each costs an argon2 verification. The API's take is none until Keycloak is in front,
  which limits them itself (docs/api.md, "Outstanding").

**identity.8** · From docs/identity.md:124, "Takes on what is open", "Expired sessions and sign-ins"

Expired sessions are removed whenever a session is opened (`People.open_session`). Sign-ins aren't limited;
`docs/api.md`, "Outstanding", takes none until Keycloak is in front.

api.13 and identity.9, from G38, as tracked in agents/wip-deploy.md ("Identity"; "Keycloak in front"), which takes
their takes in the sweep:

**api.13** · From docs/api.md:432, "Outstanding", "Signing in"

- **Keycloak.** How it hands the app a login isn't decided. Take: a proxy in front, such as oauth2-proxy, passes the
  login in a header the app believes from it alone, mapped onto `person.login` (docs/identity.md, "Take, for when
  Keycloak arrives"), and Keycloak's own tokens as bearers for scripts when they come.

**identity.9** · From docs/identity.md:128, "Takes on what is open", "Take, for when Keycloak arrives"

Keycloak, or a proxy in front such as oauth2-proxy, authenticates, and the app maps its username onto `person.login`,
which is why logins are lowercase like Keycloak's. Password login can stay as the development path. Roles could then
come from Keycloak's realm roles instead of the column; not decided.

G39, as tracked in agents/wip-portal.md (phase 7; "Below the UI", 3); identity.6's decision and take go there in the
sweep:

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

scripted.3, from G45, as tracked in agents/wip-portal.md ("Comparing variations", Open: runs to compare in the tests):

**scripted.3** · From docs/scripted.md:113, "Open design issues", "Smaller issues"

- **No two scripted runs vary a part over the same cases**, as the page to compare runs wants
  (agents/wip-portal.md, "Comparing variations").

G51, as having no reader the docs don't serve: the edges have their own, and a script on the bench reads
docs/reference/bench.md; it can come back when someone writes against the bench directly:

**bench.11** · From docs/bench.md:450, "Outstanding"

- **A low-level manual for the bench**, made from `agents/wip-authoring.md` at b6f76b8.

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

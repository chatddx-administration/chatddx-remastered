# Clearance: work in progress

Material for a future `docs/clearance.md`. Split out of the former `agents/wip-bookkeeping.md`. The stub that was
`docs/clearance.md` is folded into "What holds now", since clearance is still in progress. The interim table and the
gate are built; the clearance pipeline (a `clearance` schema and its grants) isn't.
"Decided" means the user said so; "Take" is the agent's recommendation and still open.

## Scope
Decided: clearance tracks sensitive sources, sensitive derived content and vetted endpoints, both engines and
databases. It is enforcement, not curation: sending case-derived content to an engine that isn't cleared, judge
engines included, is the system's one hard block (`docs/chatddx.md`, "Findings and errors"). The factors and the
ledger provide the means; the runner enforces.

## What holds now
### Vetted endpoints
Until clearance has a database grant, a World inventory's `[cleared]` table (`docs/inventory.md`, "Clearance") says
which sensitive sources each endpoint may receive case-derived content from.

Decided: Kompismoln's endpoints, `qwen3-8b@pelle` and `gpt-oss-20b@malborg`, are cleared for the sample World's
vignettes, in `worlds/kompismoln/inventory.toml`. Kompismoln will need to be cleared for the sample World in the
clearance pipeline when it is up, as the table goes.

Before a run or a judged scoring writes anything, the gate refuses (`docs/runner.md`, "The gate";
`src/chatddx/runner/gate.py`):
- an endpoint serving another engine than the one asked for;
- a sensitive source of the cases the endpoint isn't cleared for;
- tools on a sensitive source;
- an endpoint whose credential names a secret that isn't set;
- an endpoint the inventory can't confirm serves its engine.

The first three hold for as long as the World is as it is (`gate.bar`); the last two may pass later (`gate.admit`
adds them). The bench leaves a judged scorer that `bar` refuses out of what applies to a run (`docs/runner.md`, "What
applies to a run").

### Sensitive sources
Every source, a directory or a database, is sensitive unless declared otherwise (`docs/inventory-api.md`, `Source`).
The gate enforces it against the inventory's `[cleared]` table until the clearance pipeline replaces the table. A
`[cleared]` entry for a source that isn't sensitive clears nothing and is said so (`cleared.not_sensitive`,
`docs/inventory.md`, "Checks happen when an entry is used").

### Completions derived from vignettes
- Case-derived records are run items, score items and a score's finish (`docs/ledger.md`, "Case-derived records";
  `src/chatddx/ledger/record.py:Record.case_derived`): completions, the arguments the model passed to tools and what
  the tools returned, judge responses, the scorer's `detail`, and findings that quote the answer. Start records, a
  run's finish and canary calls are not. Compilations are components (`src/chatddx/factors/request.py:Compilation`),
  not records, and hold no case text.
- No policy has settled. Options: a database-level read restriction on case-derived tables; a destination check
  when records are exported.
- Part of it exists: the case-derived tables are in schema `ledger`, and at tier 1 `chatddx_reader` can read
  `factor` but not `ledger` (`src/chatddx/store/migrations/0005-t1-ledger.sql`), nor the typed texts in `source`
  (`0015-t1-source.sql`). Nothing uses the reader yet (`docs/store.md`, "Roles and connections"), and who gets it is
  open.

### Typed vignettes
- A clinician may type about a real patient on the portal's home page (`agents/wip-portal.md`, "Swift"). The text is a
  vignette, kept in the store as a database source's (`docs/store.md`, "Texts"; `docs/bench.md`, "Typed cases"), so
  the database holds vignettes now, not only what is derived from them.
- Each World clears its endpoints for `typed` as it does for its directory source: the test and sample Worlds clear
  their fakes, not the sample's remote engine nor the test World's `qwen3-bare@fake`. Kompismoln has no database
  source, so nothing can be typed there.
- Their fingerprints are plain, as the sample's, since nothing manages keys yet: a short text's hash can be guessed by
  anyone who reads the factors, the reader included, while the text itself is kept from them. Open: a keyed one.

### Tools
- A tool's arguments are written by the model from the case. A tool that sends them off the host (a web search;
  the sample's `chatddx.tools.web_search` goes to DuckDuckGo) sends case-derived content to a third party, so the
  hard block covers tools as it covers engines and judges.
- Tools are pinned by their entry point and the version of it chatddx ships (`Tool.entry_point`, `Tool.version`;
  `src/chatddx/tools/shipped.py:TOOLS`), and a run records the version that ran (`RunStarted.tool_code`). So the
  clearance pipeline can clear a tool by its entry point and version, with the endpoints it reaches. Nothing declares
  those yet; that belongs to clearance, not to the factor.
- Tool results come back from the third party and are stored in the ledger (`ToolRun.result`), next to the
  responses.
- The runner runs tools (`docs/runner.md`, "Tool rounds"), and the gate refuses them on a sensitive source until a
  tool can be cleared. What ships a tool is in `docs/factors-api.md` ("Tool").

### Judges
- A judge's engine falls under the hard block: a judge prompt always holds a completion, which is case-derived. The
  scoring pass gates each judge's endpoint as a run's (`gate.bar` in `runner/score.py:judge_at`, `gate.admit` in
  `Grader.start`), and refuses a judge reading the vignette or appendices.
- Judge calls record their endpoints, by judge, name and URL (`ScoreStarted.endpoints`,
  `src/chatddx/ledger/score.py:JudgeEndpoint`), as a run records its own (`RunStarted.endpoint`), so whether a judged
  scoring was cleared can be audited from the ledger as a run's can.

## What the code offers
- `Vignette.source` (`src/chatddx/factors/cases.py:Vignette`) names a vignette's source, and is part of the case's
  digest.
- `prepare_case` produces the case-derived fills the hard block guards (`docs/factors.md`, "Preparing a case").
- No factor holds an endpoint: every engine is located by the inventory (`docs/inventory.md`, "Endpoints"). A remote
  engine names its provider and model (`src/chatddx/factors/engine.py:RemoteEngine`); its address is its endpoint's.
- `RunStarted.endpoint` and `ScoreStarted.endpoints` (`src/chatddx/ledger/run.py:Endpoint`) record where a run's and
  a scoring's calls went, by the endpoint's name and URL.
- The old module had `EndpointBinding(engine, base_url, clearances)` and `CaseSourcePolicy(source,
  required_clearances)`, with a check that every endpoint reached by case-derived content held the clearances its
  sources require (`git show de843eb:src/chatddx/core/manifest.py`, around L1913 and L2258). That shape still fits:
  sources require clearances, endpoints hold them, and the gate refuses when one is missing.

## Takes
- Databases count as endpoints, because the ledger *is* case-derived storage, and the `source` schema holds typed
  vignettes themselves. The Postgres instance holding them has to be vetted like an engine, and an export target
  (records leaving for publication) is another endpoint.
- Storage: schema `clearance`, append-only like the catalog (SELECT, INSERT for the writer; t2 insert-only triggers).
  Granting clearance is the action the hard block depends on, so possibly only a separate role
  (`chatddx_clearance`) may write it. That is the one place a new database role seems justified.

## Open
1. **What a grant keys on.** This blocks the schema. Endpoints live in the inventory (`docs/inventory.md`):
   ops-authored TOML, mutable, no ids. Candidates:
   - the URL (simple, but a local host serves different engines over time, and one engine may have several hosts);
   - an inventory entry name (stable for humans, but the inventory isn't in the database, so no foreign key);
   - the engine digest plus URL (what the old `EndpointBinding` did).

   An endpoint has a name and binds one engine digest to a URL (`src/chatddx/inventory/inventory.py:EndpointSpec`),
   a remote engine's URL too. So a grant can key on the endpoint's name with the digest and URL it holds, as the old
   `EndpointBinding` did. Today `[cleared]` keys on the name alone, so renaming an endpoint drops its clearance
   (`docs/inventory.md`, "Smaller issues").
2. **Where vetting is declared.** Decided for now (`docs/inventory.md`, "Clearance"): in the inventory, as
   `[cleared]`. For the long term: the inventory keeps all location facts in one place, while a database grant
   (through the portal, logged) gives an audit trail and fits the append-only store.
3. **Who may grant clearance**, and whether that needs its own role.
4. **Binding check before sending.** Built: the gate refuses an endpoint that `confirm` can't confirm, for runs,
   canaries and judges alike.
5. **Sources.** Sources say only whether they are sensitive. Still unspecified: what clearance each requires beyond
   that.
6. **Edges as destinations.** The repl shows case-derived content at its terminal: `show case` prints the vignette and
   `run` streams the completion. The API sends it over the network to whoever signed in, but only from its own places,
   each with `Cache-Control: no-store` (`docs/api.md`, "Case-derived content": the vignette, a run's items, a score's
   items and findings, and a run's events). The portal is an edge too: every page is `no-store`, the vignette has a
   page of its own, its fonts are served by the app so that a page fetches nothing from a third party, and copying an
   answer as text wasn't ported, since it puts case-derived content on the clipboard (`agents/wip-portal.md`,
   "Swift"). The takes count a database and an export target as endpoints to vet, but nothing says whether an edge's
   client is one, nor who may read the vignette or a run's items through it. Open: whether edges are vetted like
   endpoints, by what (the edge, the person, or the client's address), and whether the repl falls under the same
   rule.

## When to build it
Nothing built so far waits on it:
- The gate reads `Inventory.cleared_for` once per endpoint it admits (`gate.bar`), for runs and judges. A database
  grant changes that one call. The repl, the API and the portal also read `cleared_for` to show an endpoint's
  clearances (`src/chatddx/repl/listing.py`, `src/chatddx/repl/inspecting.py`, `src/chatddx/api/world.py`).
- A run and a scoring already record what a grant would key on (Open 1): the endpoint's name and URL
  (`RunStarted.endpoint`, `ScoreStarted.endpoints`) and, through the trial or the judge, the engine's digest. If grants
  are append-only and dated, whether a run was cleared at `RunStarted.at` is a query, so the pipeline adds no field to
  stored runs.

It becomes the next blocker at:
- tool rounds on a sensitive source: the gate refuses tools on a sensitive source until a tool can be cleared
  ("Tools"). The runner's tests declare the test World's source not sensitive for them, and `plan-web` can't call its
  tool on vLLM 0.24 anyway (`docs/vllm.md`, item 10);
- the first real sensitive source, typed cases from clinicians included, or the first runs on `pelle` and `malborg`
  whose clearance should be auditable from the database rather than from the inventory's git history.

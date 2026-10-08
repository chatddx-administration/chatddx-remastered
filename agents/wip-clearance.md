# Clearance: work in progress

Material for a future `docs/clearance.md`. Split out of the former `agents/wip-bookkeeping.md`. The stub that was
`docs/clearance.md` is folded into "What holds now", since clearance is still in progress.
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

Before a run writes anything, the runner refuses (`src/chatddx/runner/gate.py:check`):
- an endpoint serving another engine than the trial's;
- a sensitive source the endpoint isn't cleared for;
- tools on a sensitive source;
- an endpoint whose `/v1/models` doesn't list its engine.

### Sensitive sources
Vignette sources are sensitive unless declared otherwise (`docs/inventory.md`, "Sources"). The runner enforces it
against the inventory's `[cleared]` table until the clearance pipeline replaces the table.

### Completions derived from vignettes
- Case-derived records are run items and score items (`src/chatddx/ledger/record.py:Record.case_derived`):
  completions, the arguments the model passed to tools and what the tools returned, judge responses, and the
  scorer's `detail`. Started and finished rows are not case-derived. Compilations are components
  (`src/chatddx/factors/request.py:Compilation`), not records, and hold no case text.
- No policy has settled. Options: a database-level read restriction on case-derived tables; a destination check
  when records are exported.
- Part of it exists: the case-derived tables are in schema `ledger`, and at tier 1 `chatddx_reader` can read
  `factor` but not `ledger` (`src/chatddx/store/migrations/0005-t1-ledger.sql`). Who gets that role is open.

### Tools
- A tool's arguments are written by the model from the case. A tool that sends them off the host (a web search;
  the sample's `chatddx.tools.web_search` goes to DuckDuckGo) sends case-derived content to a third party, so the
  hard block covers tools as it covers engines and judges.
- Tools are pinned by code (`Tool.code`, `entry_point`), so the clearance pipeline can clear a tool by its code, with
  the endpoints it reaches. Nothing declares those yet; that belongs to clearance, not to the factor.
- Tool results come back from the third party and are stored in the ledger (`ToolRun.result`), next to the
  responses.

## What the code offers
- `Vignette.source` (`src/chatddx/factors/cases.py:Vignette`) names a vignette's source, and is part of the case's
  digest.
- `prepare_case` produces the case-derived fills the hard block guards (`docs/factors.md`, "Preparing a case").
- `RemoteEngine.base_url` (`src/chatddx/factors/engine.py:RemoteEngine`) is the only endpoint in a factor, and it is
  part of the engine's digest. A local engine is located by the inventory (`docs/inventory.md`, "Endpoints").
- `RunStarted.endpoint` (`src/chatddx/ledger/run.py:Endpoint`) records where a run's calls went, by the endpoint's
  name and URL. Judge calls record no endpoint (`src/chatddx/ledger/score.py:ScoreStarted`).
- The old module had `EndpointBinding(engine, base_url, clearances)` and `CaseSourcePolicy(source,
  required_clearances)`, with a check that every endpoint reached by case-derived content held the clearances its
  sources require (`git show de843eb:src/chatddx/core/manifest.py`, around L1913 and L2258). That shape still fits:
  sources require clearances, endpoints hold them, and the runner refuses when one is missing.

## Takes
- Databases count as endpoints, because the ledger *is* case-derived storage. The Postgres instance holding `ledger`
  has to be vetted like an engine, and an export target (records leaving for publication) is another endpoint.
- Storage: schema `clearance`, append-only like the catalog (SELECT, INSERT for the writer; t2 insert-only triggers).
  Granting clearance is the action the hard block depends on, so possibly only a separate role
  (`chatddx_clearance`) may write it. That is the one place a new database role seems justified.
- Judges record their endpoint as runs do: a defaulted `ScoreStarted.endpoint`, so the clearance check on judge
  calls can be audited from the ledger.

## Open
1. **What a grant keys on.** This blocks the schema. Endpoints live in the inventory (`docs/inventory.md`):
   ops-authored TOML, mutable, no ids. Candidates:
   - the URL (simple, but a local host serves different engines over time, and one engine may have several hosts);
   - an inventory entry name (stable for humans, but the inventory isn't in the database, so no foreign key);
   - the engine digest plus URL (what the old `EndpointBinding` did).

   Since decision 2A (`agents/wip-sample-data.md`, "Decided"), an endpoint has a name and binds one engine digest to
   a URL (`src/chatddx/inventory/inventory.py:EndpointSpec`), and `base_url` stays in the remote engine's digest. So
   a grant can key on the endpoint's name with the digest and URL it holds, as the old `EndpointBinding` did. Today
   `[cleared]` keys on the name alone, so renaming an endpoint drops its clearance (`docs/inventory.md`, "Smaller
   issues").
2. **Where vetting is declared.** Decided for now (`agents/wip-repl.md`, D1; `agents/wip-runner.md`, "Decided"): in
   the inventory, as `[cleared]`. For the long term: the inventory keeps all location facts in one place, while a
   database grant (through the portal, logged) gives an audit trail and fits the append-only store.
3. **Who may grant clearance**, and whether that needs its own role.
4. **Binding check before sending.** Built: the gate refuses an endpoint that `confirm` can't confirm
   (`src/chatddx/runner/gate.py:check`), so it is part of the hard block for runs. Judges and canaries don't run yet.
5. **Sources.** Sources say only whether they are sensitive. Still unspecified: what clearance each requires beyond
   that. A `[cleared]` entry for a source that isn't sensitive is accepted and clears nothing
   (`docs/inventory.md`, "Open design issues").

## When to build it
Checked against the runner's phases 4–6 (`agents/wip-runner.md`, "Left"), before phase 4 was built. Nothing in the
runner waits on it:
- The gate runs once, in `Runner.start`, and reads `Inventory.cleared_for` (`src/chatddx/runner/gate.py:check`). A
  database grant changes that one call.
- A run already records what a grant would key on (Open 1): the endpoint's name and URL (`RunStarted.endpoint`) and,
  through its trial, the engine's digest. If grants are append-only and dated, whether a run was cleared at
  `RunStarted.at` is a query, so the pipeline adds no field to stored runs.
- Phase 4 (order, concurrency) doesn't touch clearance, and phase 6's canaries aren't case-derived.

It becomes the next blocker at:
- tool rounds on a sensitive source (phase 5): the gate refuses them until a tool can be cleared ("Tools"). Until
  then, the runner's tests can use a source that isn't sensitive, and `plan-web` can't call its tool on vLLM 0.24
  anyway (`docs/vllm.md`, item 10);
- judges (the scoring pass), whose engines fall under the hard block, and whose endpoint isn't recorded yet (see
  "Takes");
- the first real sensitive source, or the first runs on `pelle` and `malborg` whose clearance should be auditable
  from the database rather than from the inventory's git history.

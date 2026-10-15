# Deploy: work in progress

How chatddx is to run outside a development shell: a NixOS module whose systemd services run it on a host, and
containers for a Kubernetes cluster. Nothing of either is built.
"Decided" means the user said so; "Take" is the agent's recommendation and still open.

## Start with this
1. **Decided: deploy is the last wip.** It can be solidified only once every other wip is resolved, and
   `agents/wip-clearance.md` above all: a deployment is where real patient data first arrives, and what has to hold
   before then is listed there ("Before real patient data").
2. **Decided: `chatddx portal` is renamed `chatddx run`**, so that the NixOS module's systemd services each run a
   command of their own (see "Renaming `chatddx portal`").
3. **Decided: two targets**, a NixOS module (see "The NixOS module") and containers for a Kubernetes cluster (see
   "Containers for Kubernetes"). Which of them serves real patient data first is open.

## What holds now
- **The flake** (`flake.nix`) has `packages.default`, the Python environment with `chatddx` on its PATH, and
  `packages.frontend`, the portal's build, which a deployment points `CHATDDX_PORTAL_ASSETS` at
  (`agents/wip-portal.md`, "Open"). It has no `nixosModules`, no image and no `checks`, and nothing builds it but a
  person: there is no CI.
- **What serves**, by command (`src/chatddx/cli.py`):

  | Command | Serves |
  |---|---|
  | `chatddx api` | the API at `/api/`, with no worker; `chatddx worker` runs beside it |
  | `chatddx portal` | the portal at `/` and the API at `/api/`, with a worker on a thread of its process; `--watch` builds the frontend with pnpm as it changes |
  | `chatddx worker` | the queue for a World, until SIGTERM or SIGINT; what it holds then is queued again |
  | `chatddx migrate` | the migrations, as the admin, up to a tier (`docs/store.md`, "Tiers") |
  | `chatddx fake-engines` | the World's fake engines, for development |

- **Stopping a worker**: its scorings go on for `settings.WORKER_DEADLINE` (60 s), which is to be "within the stop
  timeout of the service that runs the worker" (`src/chatddx/settings.py`). systemd's default stop timeout is 90 s;
  Kubernetes' default grace period is 30 s.
- **Several processes may serve one database**: workers take turns to claim (`docs/worker.md`, "Where it runs"), and a
  run's events reach every app through `LISTEN`/`NOTIFY` (`src/chatddx/api/listening.py`). Sessions are in the
  database.
- **What a process reads from its environment**: `DB_HOST`, `DB_NAME`, `DB_USER` and `DB_ADMIN`
  (`settings.database`); `HOST`, where to listen; `CHATDDX_WORLD`, `CHATDDX_PORTAL_ASSETS` and `CHATDDX_REVISION`;
  and each endpoint's secret, under the variable its `credential` names (`docs/inventory.md`, "Endpoints"), read in
  `src/chatddx/runner/gate.py` and `src/chatddx/scripted/fakes.py`, not through `chatddx.settings`.
- **The database**: `src/chatddx/store/setup.sql` makes the admin `chatddx`, the writer `chatddx_writer` and the
  database. Development connects on a socket with peer authentication, OS users mapped to roles (AGENTS.md,
  "Environment"). `settings.database` names a host, a user and a database only, so a password or TLS can come only
  from libpq's own `PG*` variables.
- **A World is a directory**: its inventory, its facts, and a directory source's vignettes (`worlds/sample/vignettes`),
  which are sensitive unless declared otherwise (`docs/inventory-api.md`, `Source`). Every process but `migrate`
  reads one.
- **Where it is to run**, in two places that don't agree yet:
  - `docs/chatddx.md` ("Target stack"): the orchestrator "Runs in Kubernetes, writes the start-ups and hosts the
    portal", and each inference server serves vLLM in a NixOS container;
  - `docs/worker.md` ("Where it runs") and `agents/wip-portal.md` (item 3 of "Start with this"): a deployment runs
    the HTTP server, the API and the worker as separate services, systemd services on NixOS.
- **Identity**: "The deployment is to sit behind Keycloak" (`docs/identity.md`, "Keycloak"), which isn't decided
  further.

## Renaming `chatddx portal`
Decided: `chatddx portal` becomes `chatddx run`.
- `chatddx run` is what `chatddx portal` is now: the portal, the API and a worker in one process, and `--watch`. It is
  the convenience for development, and the README's command.
- Take: `chatddx portal` then serves the portal and the API without a worker (`chatddx.portal.app.app` with
  `worker=False`), the web service of a deployment. Each service runs one command, with no flag that changes what it
  serves:

  | Service | Command |
  |---|---|
  | the portal, with the API | `chatddx portal` |
  | the API alone, where nothing serves the portal | `chatddx api` |
  | each worker | `chatddx worker` |
  | the migrations, before the others start | `chatddx migrate` |

- What it touches:
  - `src/chatddx/cli.py`: `_portal`, its parser, and the messages that say `portal:`; the tests that call it
    (`src/chatddx/portal/test/test_frontend.py:108`, `src/chatddx/portal/test/test_signing_in.py:132`);
  - as suggestions, the docs that name it: README ("The portal"), `docs/worker.md` ("Where it runs"),
    `docs/worker-api.md` ("The command"), `docs/api-api.md` ("The command") and `docs/api.md` ("Tests");
  - `agents/wip-portal.md`: item 3 of "Start with this", "P3b, concretely", "Built" and "Phases".
- Open: what "the HTTP server" is beside "the API" in `docs/worker.md` ("Where it runs"). Take: a reverse proxy in
  front of `chatddx portal` (see "The NixOS module"), since the portal's islands call the API on the portal's own
  origin.

## The NixOS module
A `nixosModules.default` in the flake, as `services.chatddx`:
- **Options**: the package (`packages.default`) and the frontend (`packages.frontend`, as `CHATDDX_PORTAL_ASSETS`);
  the World; more facts; where to listen; the database's host and name; the tier to migrate to; how many workers; and
  a file of endpoint secrets.
- **Services**:
  - `chatddx-migrate`, a oneshot as the admin, that the others start after;
  - `chatddx-portal`, `chatddx portal` as the writer;
  - `chatddx-worker@`, `chatddx worker` as the writer, one instance per worker, with `TimeoutStopSec` above
    `WORKER_DEADLINE`;
  - and once there is a command for it, a timer that purges expired sessions (`agents/wip-clearance.md`, "Before real
    patient data", Sessions).
- **The database**: Take: `services.postgresql` 16 on the same host, its roles and database made as `setup.sql` makes
  them, with peer authentication mapped as AGENTS.md maps it. Two system users, one for the admin and one for the
  writer, so that the web process can't act as the admin.
- **Secrets**: endpoint credentials from a file outside the Nix store (`EnvironmentFile`, or systemd credentials),
  under the names the inventory gives.
- **The World**: the Nix store is readable by every user of the host, so a World with a sensitive directory source
  isn't a store path. Take: the option is a path on the host as a string, readable by the writer alone, and only a
  World with no sensitive directory source may come from the store.
- **In front**: Take: nginx (`services.nginx`) with TLS from ACME, `/static/` served from the frontend's build, and a
  run's event stream passed through unbuffered (the API sends a keep-alive every 15 s,
  `src/chatddx/api/telling.py:KEEP_ALIVE`). The headers, the body limit and the sign-in limit that
  `agents/wip-clearance.md` lists could be set here, though the Kubernetes target would need them too.
- **Hardening**: the services sandboxed (`ProtectSystem=strict`, `PrivateTmp`, `NoNewPrivileges` and the like), and no
  `HTTP_PROXY` or `HTTPS_PROXY` in their environment, since the engine client follows them
  (`agents/wip-clearance.md`, "Before real patient data").
- **A test**: Take: a NixOS VM test (`pkgs.testers.runNixOSTest`) in the flake's `checks` that boots the module with
  the test World and its fake engines, signs in and runs a case.
- Open: whether the module also serves an inference host's vLLM from an endpoint's start-up, as `fake-engines` serves
  a fake from it, or that stays with the hosts' own NixOS containers (`docs/chatddx.md`, "Target stack").

## Containers for Kubernetes
- **The image**: Take: built by Nix (`dockerTools.streamLayeredImage`) from `packages.default` and
  `packages.frontend`, so that it holds the flake's closure and nothing else, with `CHATDDX_REVISION` set from the
  flake's revision. One image; each workload names its command.
- **Workloads**:
  - a Deployment for `chatddx portal`, with a Service and an Ingress, the event stream unbuffered there too;
  - a Deployment for `chatddx worker`, with `terminationGracePeriodSeconds` above `WORKER_DEADLINE`, since the
    default is shorter;
  - a Job for `chatddx migrate` before each release, as the admin.
- **The database**: peer authentication doesn't reach across pods, so the roles sign in with a password or a
  certificate over TCP. `settings.database` passes neither (see "What holds now"). Take: `chatddx.settings` names what
  libpq takes (`PGPASSFILE`, `PGSSLMODE` and the like), as the project's source of truth, rather than leaving it to
  libpq's environment. In the cluster (an operator such as CloudNativePG) or outside it is open.
- **Connections**: replicas multiply what each process holds, with no pool (`agents/wip-clearance.md`, "Before real
  patient data", Connections), against Postgres' `max_connections`.
- **The World**: not in the image, which a registry holds. Take: the inventory and facts as a ConfigMap; a directory
  source's vignettes on a volume only the workloads mount; endpoint secrets as a Secret, under the names the
  inventory gives.
- **Egress**: Take: a NetworkPolicy that lets the pods reach Postgres and the inventory's endpoints only, so that the
  network holds what the gate holds (`agents/wip-clearance.md`, "Vetted endpoints").
- **Probes**: the app has no health route, and the worker no HTTP at all. Open: a route for readiness, and whether the
  worker's beats (`settings.WORKER_BEAT`) can serve as its liveness.
- **Reaching the inference hosts**: pelle and malborg are on Kompismoln's VPN (README, "Kompismoln's hosts"). Open:
  how the cluster's pods reach them.
- Open: where the manifests live and what writes them (plain YAML in the repository, Helm, or Nix).

## Open
- Which target serves real patient data first, and whether the other stays (`docs/chatddx.md` puts the orchestrator
  in Kubernetes; `docs/worker.md` and `agents/wip-portal.md` name systemd on NixOS).
- Keycloak in front (`docs/identity.md`, "Keycloak"; `agents/wip-portal.md`, "Open"): which target runs it, and how it
  hands the app a login.
- CI: what builds the image and the module's test, and runs `pytest` and the frontend's checks, before a deployment
  takes a revision.

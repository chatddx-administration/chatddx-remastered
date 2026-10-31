# Testing the NixOS module from a cloud session

How the NixOS module (`nix/module.nix`) is tested when a claude.ai cloud session changes it, so that the next session
can do it again. `docs/parts/deploy.md` ("The NixOS module") says what the module and its tests are; this file says who
runs what, how, and what got in the way.

Decided: a cloud session has no KVM, and its VM test by emulation is too slow and too fragile to rely on (see "Runs").
The session runs everything that needs no VM; the person runs the VM test on a host with KVM. CI with KVM, which would
close the loop without the person, is an option in o11n's `agents/wip-self-hosted-kvm.md`.

## Who runs what

| Check                                                 | What it covers                                                                                                                                                                                                                                                     | Who, where                              |
| ----------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------- |
| `checks.<system>.module-eval` (`nix/module-eval.nix`) | The module's wiring, evaluated: services, users, environment, ordering, the sandbox's settings, PostgreSQL's versions, assertions, paths in the store refused                                                                                                      | The session, seconds                    |
| Building `checks.<system>.module.driver`              | The VM test's script typed (mypy) and linted (pyflakes), without booting                                                                                                                                                                                           | The session, a minute                   |
| `pytest` against PostgreSQL 17 (and 16)               | The app and its migrations on either version                                                                                                                                                                                                                       | The session, two minutes                |
| The host flow                                         | The services' commands as the module runs them, under an org's identities: migrations as a hyphenated admin, the World read through the admin's group, the operator's commands, a run through the portal sent and scored by a worker                               | The session, minutes                    |
| `checks.<system>.module` (`nix/test.nix`)             | What only a VM shows: systemd's ordering and failures at boot, NixOS' activation (users merged, homes, tmpfiles), `ensureUsers` against a real cluster, the sandbox not breaking the services, nginx in front (TLS, headers, the sign-in limit), the proxies unset | The person, on a host with KVM, minutes |

## What the session has, and doesn't

- Nix 2.34 with flakes, run as root, sandboxed builds (`build-users-group = nixbld`), and cache.nixos.org as its
  substituter. Check with `nix --version` and `nix config show | grep -E '^(sandbox|substituters)'`.
- **No `/dev/kvm`.** QEMU would run the VM by emulation (TCG); see "Runs" for what that came to.
- **No IPv6.** The container's kernel has none (`/proc/net/if_inet6` is missing; `AF_INET6` sockets fail), so nothing
  can listen on `[::1]` here.
- **No GitHub archives.** The flake's inputs are locked as `github:` URLs, which Nix fetches as tarballs, and the agent
  proxy answers those with 403 ("GitHub access to this repository is not enabled for this session"). Git over HTTPS
  works for the same repositories, so the inputs are overridden with shallow git fetches of the locked revisions (step
  1).
- **An agent proxy that re-signs TLS**, and only HTTPS through it: no SSH, so no remote builder. Tools trust its CA
  through `SSL_CERT_FILE`, `NIX_SSL_CERT_FILE` and the like, but a Nix sandbox sees none of them. Python wheels from
  PyPI and the NixOS closure from cache.nixos.org fetch fine; pnpm's fetch of the frontend's dependencies doesn't (step
  3).
- **PostgreSQL 16** from Debian, stopped and without AGENTS.md's mapping; PostgreSQL 17 comes from Nix (step 5).

## Steps in a session

All commands run from the repository's root.

### 0. Track what the flake should see

A flake in a git repository sees only tracked files. New files under `nix/` need at least `git add -N nix/` before any
`nix` command can read them; edits to tracked files are seen as they are (the tree is reported dirty).

### 1. Override the inputs with git fetches

This sets `OVERRIDES` from `flake.lock`, so that it follows the lock as it changes:

```sh
mapfile -t OVERRIDES < <(python3 - <<'PY'
import json

nodes = json.load(open("flake.lock"))["nodes"]
for name, key in nodes["root"]["inputs"].items():
    locked, original = nodes[key]["locked"], nodes[key]["original"]
    assert locked["type"] == "github", (name, locked["type"])
    url = f"git+https://github.com/{locked['owner']}/{locked['repo']}?rev={locked['rev']}&shallow=1"
    if "ref" in original:
        url += f"&ref={original['ref']}"
    print("--override-input")
    print(name)
    print(url)
PY
)
printf '%s\n' "${OVERRIDES[@]}"
```

Every `nix eval` and `nix build` of the flake below takes `"${OVERRIDES[@]}"`. Each prints "not writing modified lock
file" with the inputs it overrode: expected. `flake.lock` is left as it is, and never committed with git URLs.

The first evaluation fetches nixpkgs over git, which takes several minutes; later ones reuse the fetch:

```sh
nix eval "${OVERRIDES[@]}" --raw .#packages.x86_64-linux.default.name   # chatddx-env
for ((i = 0; i < ${#OVERRIDES[@]}; i += 3)); do
  [ "${OVERRIDES[i+1]}" = nixpkgs ] && NIXPKGS_URL=${OVERRIDES[i+2]}
done
NIXPKGS=$(nix flake prefetch --json "$NIXPKGS_URL" \
  | python3 -c 'import json, sys; print(json.load(sys.stdin)["storePath"])')
```

`$NIXPKGS`, the fetched nixpkgs, gives tools to run from it (`nix build "path:$NIXPKGS#nixfmt"`).

### 2. The module's evaluation

```sh
nix build "${OVERRIDES[@]}" --no-link -L .#checks.x86_64-linux.module-eval
nix eval "${OVERRIDES[@]}" --json .#checks.x86_64-linux.module-eval.failures   # [] when it passes
```

A failure lists each case with what was expected and what came out (`lib.runTests`); `.cases` evaluates them all. To try
options beyond these, add a case and its expectation to `nix/module-eval.nix`. A check that has never failed proves
little: break the module on purpose (a `UMask` changed was caught) and put it back. A made-up store path such as
`/nix/store/x-world` passes `types.externalPath`, as it has no hash: test with a real one (`"${pkgs.hello}"`).

### 3. Build the packages, and fetch the frontend's dependencies once by hand

```sh
nix build "${OVERRIDES[@]}" --no-link --print-out-paths -L \
  .#packages.x86_64-linux.default .#packages.x86_64-linux.frontend
```

The Python environment builds: its wheels come from PyPI, which the sandbox reaches. The frontend fails in
`chatddx-frontend-pnpm-deps` with `SELF_SIGNED_CERT_IN_CHAIN` and then `ERR_PNPM_META_FETCH_FAIL`, since Node in the
sandbox doesn't trust the proxy's CA. That derivation is fixed-output: its output path depends only on its name and the
hash in `flake.nix`, not on how it was built. So it is built once from a copy of its derivation that trusts the CA, and
the flake's own build then finds the output in the store:

```sh
SCRATCH=$(mktemp -d)
install -m 0644 /root/.ccr/ca-bundle.crt /tmp/proxy-ca.crt
DRV=$(nix eval "${OVERRIDES[@]}" --raw .#packages.x86_64-linux.frontend.pnpmDeps.drvPath)
nix derivation show "$DRV" | python3 -c '
import json, sys
shown = json.load(sys.stdin)
[(path, drv)] = shown.get("derivations", shown).items()
drv["env"]["NODE_EXTRA_CA_CERTS"] = "/tmp/proxy-ca.crt"
print(json.dumps(drv))' > "$SCRATCH/pnpm-deps.json"
NEW=$(nix derivation add < "$SCRATCH/pnpm-deps.json")
nix build --no-link --print-out-paths "$NEW^out" --option extra-sandbox-paths /tmp/proxy-ca.crt
```

The path it prints must be the one the flake expects,
`nix eval "${OVERRIDES[@]}" --raw .#packages.x86_64-linux.frontend.pnpmDeps.outPath`; Nix checks the hash, so a
different set of dependencies fails rather than lands. The CA is copied out of `/root` because the build users can't
read there. This is needed again only when `frontend/pnpm-lock.yaml`, and with it the hash in `flake.nix`, changes. Then
run the `nix build` of the packages again; the frontend builds.

### 4. The VM test's script, typechecked without a VM

```sh
nix build "${OVERRIDES[@]}" --no-link -L .#checks.x86_64-linux.module.driver
```

The driver's build types the script with mypy and lints it with pyflakes, so an unused import or a misspelt name fails
here, before the person boots anything.

### 5. `pytest` against PostgreSQL 17

A cluster of 17 beside Debian's 16, on port 5433, its socket in `/var/run/postgresql`, with AGENTS.md's mapping, and an
identity mapping for the host flow's users (step 6):

```sh
PG=$(nix build --no-link --print-out-paths "path:$NIXPKGS#postgresql_17")
D=/var/lib/postgresql/chatddx-17
id chatddx-test >/dev/null 2>&1 || useradd --system --user-group --no-create-home chatddx-test
id chatddx_writer >/dev/null 2>&1 || useradd --system --user-group --no-create-home chatddx_writer
install -d -o postgres -g postgres /var/run/postgresql
runuser -u postgres -- "$PG/bin/initdb" -D "$D" -U postgres --auth-local=peer --auth-host=reject \
  -E UTF8 --locale=C.UTF-8
printf '%s\n' 'local all postgres peer' 'local all all peer map=chatddx' > "$D/pg_hba.conf"
printf '%s\n' 'chatddx root chatddx' 'chatddx root chatddx_writer' \
  'chatddx chatddx-test chatddx-test' 'chatddx chatddx_writer chatddx_writer' > "$D/pg_ident.conf"
chown postgres:postgres "$D/pg_hba.conf" "$D/pg_ident.conf"
runuser -u postgres -- "$PG/bin/pg_ctl" -D "$D" -l "$D/log" -w \
  -o "-p 5433 -k /var/run/postgresql -c listen_addresses=''" start
runuser -u postgres -- "$PG/bin/psql" -h /var/run/postgresql -p 5433 -f src/chatddx/store/setup.sql
uv sync --all-groups
set -a; . ./.env-container; set +a
PGPORT=5433 .venv/bin/pytest -n 4 -q
```

`-E UTF8` matters: initdb in the container's locale makes `SQL_ASCII`, in which psycopg returns text as bytes
(`b'model.local' components have no threads`) and hundreds of tests fail. NixOS initialises in UTF-8.

### 6. The host flow

The services' commands, run as the module runs them but without systemd or nginx, against the cluster of step 5, under
an org's identities: the admin `chatddx-test` (a hyphenated role, as Kompismoln's `chatddx-dev`) owning the database of
its name, and the writer reading the World through the admin's group.

```sh
psql17() { runuser -u postgres -- "$PG/bin/psql" -h /var/run/postgresql -p 5433 -qtA "$@"; }
psql17 -c 'CREATE ROLE "chatddx-test" LOGIN CREATEROLE'          # once
psql17 -c 'DROP DATABASE IF EXISTS "chatddx-test" WITH (FORCE)'
psql17 -c 'CREATE DATABASE "chatddx-test" OWNER "chatddx-test"'
usermod -aG chatddx-test chatddx_writer
install -d -m 0750 -o chatddx-test -g chatddx-test /var/lib/chatddx-test
cp -rT worlds/sample /var/lib/chatddx-test/sample
chown -R chatddx-test:chatddx-test /var/lib/chatddx-test/sample
chmod -R u=rwX,g=rX,o= /var/lib/chatddx-test/sample
runuser -u chatddx_writer -- test -r /var/lib/chatddx-test/sample/inventory.toml   # the writer reads it
! runuser -u nobody -- test -r /var/lib/chatddx-test/sample/inventory.toml        # nobody doesn't

CHATDDX=$(nix build "${OVERRIDES[@]}" --no-link --print-out-paths .#packages.x86_64-linux.default)/bin/chatddx
ASSETS=$(nix build "${OVERRIDES[@]}" --no-link --print-out-paths .#packages.x86_64-linux.frontend)
ENV=(env -u http_proxy -u HTTP_PROXY -u https_proxy -u HTTPS_PROXY -u all_proxy -u ALL_PROXY
  DB_HOST=/var/run/postgresql PGPORT=5433 DB_NAME=chatddx-test DB_ADMIN=chatddx-test DB_USER=chatddx_writer
  HOST=127.0.0.1:8766 CHATDDX_WORLD=/var/lib/chatddx-test/sample CHATDDX_PORTAL_ASSETS="$ASSETS"
  CHATDDX_SAMPLE_KEY=sample-key PYTHONUNBUFFERED=1)
runuser -u chatddx-test -- "${ENV[@]}" "$CHATDDX" migrate --tier 2
<<<<<<< signed
runuser -u chatddx_writer -- "${ENV[@]}" "$CHATDDX" init-data alice --giftbag
=======
runuser -u chatddx_writer -- "${ENV[@]}" "$CHATDDX" sync-archive
runuser -u chatddx_writer -- "${ENV[@]}" "$CHATDDX" person provision alice
>>>>>>> @stamp
printf '%s\n%s\n' 'correct horse' 'correct horse' \
  | runuser -u chatddx_writer -- setsid -w "${ENV[@]}" "$CHATDDX" person password alice
for command in fake-engines portal worker; do
  runuser -u chatddx_writer -- "${ENV[@]}" "$CHATDDX" "$command" > "$SCRATCH/$command.log" 2>&1 &
done
```

Then the calls of the VM test's subtest 2 against `http://127.0.0.1:8766`, from a script with no proxy (Python's
`urllib` with `ProxyHandler({})`): wait for the portal and the fake engines' ports 12099 to 12101; `POST /api/session`
with alice's password; `GET /api/threads?kind=configuration&owner=alice&name=plan`; `POST /api/families` with
`{"text": …, "language": "en"}`; `POST /api/runs` with the configuration, `qwen3-8b-awq@fake`, the family and
`"score": true`; `GET /api/runs/<run>` until its job is neither queued nor under way, and it must be finished. Last,
`pkill -u chatddx_writer`: killing `runuser` doesn't reach the process under it.

`127.0.0.1` and not `[::1]`, since the container has no IPv6; the VM test listens on `[::1]`.

### 7. Check the formatting

```sh
nix run "path:$NIXPKGS#nixfmt" -- --check flake.nix nix/module.nix nix/module-eval.nix nix/test.nix
```

## For the person: the VM test on a host with KVM

From the repository, at the revision to test, on a host with KVM (stationary, pelle, or a build host over
`--store ssh-ng://` once o11n's `agents/wip-nixservice.md` is done):

```sh
nix build -L .#checks.x86_64-linux.module
```

A passing run ends with the test's output path. A failing one prints `!!!` lines with the subtest, the command and a
traceback, then "Cannot build '…-vm-test-run-chatddx.drv'"; those lines, or `nix log` of that derivation, are what the
session needs back. A passed test is cached until something it depends on changes; `--rebuild` runs it again. Noise in
the log, not failures: `dhcpcd[…]: timed out` (the test network has no DHCP) and
`cfg80211: failed to load regulatory.db`.

## What the test does

`nix/test.nix` boots one machine with the module, PostgreSQL 17, two workers, the portal on `[::1]:8000` and nginx for
`chatddx.test`, with a certificate it makes for itself, which the machine trusts. The admin is `chatddx-test`, a user
the test declares as an org would, with a home in `/var/lib/chatddx-test` (0750), whose group the writer is in. The
sample World is copied out of the store into `/var/lib/chatddx-test/sample` by tmpfiles, inside that home, and its
remote endpoint's secret is in `/var/lib/chatddx-test/secrets`, mode 0400. Then: 0. **The admin and the World**:
<<<<<<< signed
`chatddx-migrate` runs as `chatddx-test`; the writer reads the World, `nobody` doesn't.
=======
`chatddx-migrate` runs as `chatddx-test`; the writer reads the World, `nobody` doesn't; `chatddx-sync-archive` has
written the sample's data into the archive.
>>>>>>> @stamp

<<<<<<< signed
1. **The operator's command**: `chatddx init-data alice --giftbag` and `chatddx person password alice`, as root, through
=======
1. **The operator's command**: `chatddx person provision alice` and `chatddx person password alice`, as root, through
>>>>>>> @stamp
   the wrapper, which runs them as `chatddx_writer`; then `chatddx-fake-engines`, a service of the test's that runs
   `chatddx fake-engines` the same way, and its three ports.
2. **A run through the portal**: over HTTPS through nginx, sign in at `/api/session`, find the configuration `plan` of
   alice's, store a typed case in English, start a scored run at `qwen3-8b-awq@fake`, and wait until its job is no
   longer queued or under way; it must be finished. `chatddx portal` runs no worker, so this shows a worker service took
   it.
3. **nginx**: the headers of a GET of `/sign-in`, HSTS among them, and a 429 among twelve failed sign-ins sent at once,
   with `signInRate` at `1r/m` for the test.
4. **No proxy**: with `HTTPS_PROXY` set in the service manager's environment, a restarted worker's environment holds
   none.

## Timings

By emulation in a session, the run that passed, after the packages were built and the NixOS closure was mostly
substituted:

| Step                                                  | Seconds |
| ----------------------------------------------------- | ------- |
| booting the VM                                        | 208     |
| until `chatddx-portal.service` is active (after boot) | 473     |
| until port 8000 answers                               | 180     |
<<<<<<< signed
| `chatddx init-data alice --giftbag`                   | 120     |
=======
| `chatddx init-data alice --giftbag`, before the split | 120     |
>>>>>>> @stamp
| until the fake engines' first port answers            | 51      |
| subtest 2, the run, sent and scored                   | 39      |

About 20 minutes up to the end of subtest 2. With KVM it is a few minutes.

## Debugging

- **The interactive driver**: `nix build .#checks.x86_64-linux.module.driverInteractive`, then
  `./result/bin/nixos-test-driver`, and in its Python prompt `start_all()`, `machine.succeed("…")` or
  `machine.shell_interact()`.
- **The driver outside the Nix sandbox**: `./result/bin/nixos-test-driver --test-script <file>` (of
  `.#checks.x86_64-linux.module.driver`) runs another script with the same machines. Its sockets live under `$TMPDIR`,
  which must be short: a socket's path is limited to 108 bytes ("AF_UNIX path too long").

## What went wrong on the way

- **`curl -I` against the app** fails: FastAPI adds no HEAD to a GET route, so HEAD is 405. The test reads headers from
  a GET (`curl -sf -o /dev/null -D -`).
- **A limit that emulation doesn't reach**: at 10 a minute with a burst of 5, nginx takes a sign-in every 6 s beyond the
  burst. By emulation each `curl`, and the argon2 behind it, takes several seconds, so eight in a row all got 200. The
  test sends its sign-ins at once (`curl … &` in a loop, then `wait`), at `1r/m`.
- **`getpass` with no terminal**: `chatddx person password` reads `/dev/tty` when there is one. `setsid -w` runs it
  without a controlling terminal, so that it reads the password from stdin.
- **`retry`** in the test driver takes `timeout` as a `datetime.timedelta`; a number of seconds is deprecated.
- **tmpfiles' `C`** copies the World into a directory the test makes first (`d`). Its copy is root's, and a `Z` that
  would give it to the admin is refused: "unsafe path transition" from the admin's home to a file of root's. The home's
  mode keeps other users out, as on Kompismoln, where the app's own user copies the World.
- **PostgreSQL's start by emulation**: initdb took longer than `postgresql.service`'s 120 s on a slower host, and the
  chatddx services, failed on the dependency, weren't started again when it was. The test raises its `TimeoutSec`.
- **The guest's shell by emulation**: the driver waits 300 s for it (ten times 30 s, not configurable); boots took
  longer twice.
- **PostgreSQL's version**: the VM's default for its `stateVersion` is neither 16 nor 17, which the module warns about,
  so the test pins `postgresql_17`, the version Kompismoln's hosts serve (`docs/parts/deploy.md`, "On Kompismoln").
- **A typed case's language**: `POST /api/families` requires `language`; the test sent none and got 422. The host flow
  found it in minutes.
- **`pkill -f chatddx`** from the Bash tool matches the tool's own shell, whose command line holds the pattern, and
  kills it. Kill by PID, or by user (`pkill -u chatddx_writer`).

## Runs

- **By emulation, before the admin option**: the first run failed on `curl -sfI`, the second on the sign-in limit (see
  "What went wrong on the way"); the third passed, all four subtests, the script in 1,146 s (subtests 1 to 4: 248, 45,
  70 and 5 s).
- **By emulation, with the admin option**: five tries, on another day. Two boots outlasted the driver's 300 s for the
  guest's shell; one booted, and the services failed after PostgreSQL's start limit (and showed tmpfiles' refused `Z`);
  one run of the driver outside the sandbox failed on its socket's path. None reached the subtests, hence the split
  above.
- **The host flow, with the admin option, on PostgreSQL 17**: failed on the typed case's missing `language` (422); with
  it, passed: migrations as `chatddx-test`, the World read through its group, the operator's commands, a run queued by
  the portal, sent and scored by a worker, finished.
- **`pytest` on PostgreSQL 17.11**: 883 passed, 8 skipped (the browser tests: no build in `frontend/dist`, no browser
  for Playwright).
- **The VM test with the admin option, on KVM**: not yet run.

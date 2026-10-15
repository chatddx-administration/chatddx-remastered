# Running the NixOS VM test in a cloud session

How `checks.<system>.module` (`nix/test.nix`), the VM test of the NixOS module (`nix/module.nix`), was built and run
in a claude.ai cloud session, so that the next session can do it again. `agents/wip-deploy.md` ("The NixOS module")
says what the module and the test are; this file says how to run them here, and what got in the way.

## What the session has, and doesn't
- Nix 2.34 with flakes, run as root, sandboxed builds (`build-users-group = nixbld`), and cache.nixos.org as its
  substituter. Check with `nix --version` and `nix config show | grep -E '^(sandbox|substituters)'`.
- **No `/dev/kvm`.** QEMU runs the VM by emulation (TCG), roughly ten times slower than with KVM (see "Timings").
- **No GitHub archives.** The flake's inputs are locked as `github:` URLs, which Nix fetches as tarballs, and the
  agent proxy answers those with 403 ("GitHub access to this repository is not enabled for this session"). Git over
  HTTPS works for the same repositories, so the inputs are overridden with shallow git fetches of the locked revisions
  (step 1).
- **An agent proxy that re-signs TLS.** Tools trust its CA through `SSL_CERT_FILE`, `NIX_SSL_CERT_FILE` and the like,
  but a Nix sandbox sees none of them. Python wheels from PyPI and the NixOS closure from cache.nixos.org fetch
  fine; pnpm's fetch of the frontend's dependencies doesn't (step 3).
- The host's PostgreSQL isn't needed for the VM test: the VM runs its own. It is needed only for the tests in
  AGENTS.md and the host flow in "Debugging".

## Steps
All commands run from the repository's root.

### 0. Track what the flake should see
A flake in a git repository sees only tracked files. New files under `nix/` need at least `git add -N nix/` before
any `nix` command can read them; edits to tracked files are seen as they are (the tree is reported dirty).

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
```

### 2. Check the module by evaluation (optional, fast)
Evaluating a NixOS system with the module and a stub for `inputs.chatddx` checks options, assertions and types
without building anything. Write the stub's expression to a scratch directory:

```sh
SCRATCH=$(mktemp -d)
cat > "$SCRATCH/eval.nix" <<'EOF'
{ nixpkgs, repo, extra ? { } }:
let
  pinned = builtins.getFlake "path:${toString nixpkgs}";
  pkgs = pinned.legacyPackages.x86_64-linux;
  stub = {
    packages.x86_64-linux = { default = pkgs.hello; frontend = pkgs.hello; };
    rev = "abc";
  };
  system = pinned.lib.nixosSystem {
    system = "x86_64-linux";
    specialArgs.inputs.chatddx = stub;
    modules = [
      (repo + "/nix/module.nix")
      {
        boot.loader.grub.enable = false;
        fileSystems."/" = { device = "/dev/null"; fsType = "ext4"; };
        system.stateVersion = "26.11";
        services.postgresql.package = pkgs.postgresql_16;
        services.chatddx = { enable = true; world = "/var/lib/chatddx/world"; };
      }
      extra
    ];
  };
in
{
  inherit (system.config.services.chatddx) revision;
  units = builtins.attrNames (
    pinned.lib.filterAttrs (n: _: pinned.lib.hasPrefix "chatddx" n) system.config.systemd.services
  );
  nginx = system.config.services.nginx.enable;
  inherit (system.config) warnings;
  portal = system.config.systemd.services.chatddx-portal.serviceConfig.ExecStart;
  toplevel = system.config.system.build.toplevel.drvPath;
}
EOF
```

It takes the fetched nixpkgs as a store path:

```sh
for ((i = 0; i < ${#OVERRIDES[@]}; i += 3)); do
  [ "${OVERRIDES[i+1]}" = nixpkgs ] && NIXPKGS_URL=${OVERRIDES[i+2]}
done
NIXPKGS=$(nix flake prefetch --json "$NIXPKGS_URL" \
  | python3 -c 'import json, sys; print(json.load(sys.stdin)["storePath"])')
```

Then evaluate it as it is, or with `extra` set to a module of options to try:

```sh
nix eval --impure --json --expr "import $SCRATCH/eval.nix { nixpkgs = $NIXPKGS; repo = $PWD; }"
nix eval --impure --json --expr "import $SCRATCH/eval.nix { nixpkgs = $NIXPKGS; repo = $PWD;
  extra = { services.chatddx.workers = 3; services.chatddx.facts = [ \"/etc/facts.toml\" ]; }; }"
```

The attributes leave `toplevel` unforced unless asked for; assertions and the types of `world` and
`environmentFile` are checked only when it is, so ask for `.toplevel` (`--raw --expr "(import … ).toplevel"`) to see
them refuse. What was checked this way:

| `extra` | Expected |
|---|---|
| none | units `chatddx-migrate`, `chatddx-portal`, `chatddx-worker-1`; nginx off; no warnings |
| `workers = 3; facts = [ "/etc/facts.toml" ]` | three workers; `--facts /etc/facts.toml` in `ExecStart` |
| `database.createLocally = false; workers = 0` | no worker units |
| `nginx.enable = true` with no `hostName` | "The option `services.chatddx.nginx.hostName` was accessed but has no value defined" |
| `database.name = "other"` (toplevel) | the assertion: the name must be `chatddx` when `createLocally` |
| `world = lib.mkForce "/nix/store/<a real store path>"` (toplevel) | "not of type `absolute path not in the Nix store`" |
| `environmentFile = ./flake.nix` (toplevel) | refused the same way |

A made-up store path such as `/nix/store/x-world` passes the type, as it has no hash: test with a real one.

### 3. Build the packages, and fetch the frontend's dependencies once by hand
```sh
nix build "${OVERRIDES[@]}" --no-link --print-out-paths -L \
  .#packages.x86_64-linux.default .#packages.x86_64-linux.frontend
```

The Python environment builds: its wheels come from PyPI, which the sandbox reaches. The frontend fails in
`chatddx-frontend-pnpm-deps` with `SELF_SIGNED_CERT_IN_CHAIN` and then `ERR_PNPM_META_FETCH_FAIL`, since Node in the
sandbox doesn't trust the proxy's CA. That derivation is fixed-output: its output path depends only on its name and
the hash in `flake.nix`, not on how it was built. So it is built once from a copy of its derivation that trusts the
CA, and the flake's own build then finds the output in the store:

```sh
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
different set of dependencies fails rather than lands. The CA is copied out of
`/root` because the build users can't read there. This is needed again only when `frontend/pnpm-lock.yaml`, and with
it the hash in `flake.nix`, changes. Then run the `nix build` of the packages again; the frontend builds.

### 4. Run the VM test
```sh
nix build "${OVERRIDES[@]}" --no-link --print-out-paths -L \
  --option system-features "nixos-test benchmark big-parallel kvm" \
  .#checks.x86_64-linux.module > "$SCRATCH/vmtest.log" 2>&1
echo "exit $?" >> "$SCRATCH/vmtest.log"
```

- `system-features`: the test asks for `nixos-test` and `kvm`, which this Nix doesn't list. Declaring them lets it
  run; with no `/dev/kvm`, QEMU falls back to TCG.
- Run it in the background (the Bash tool's `run_in_background`, with a timeout of an hour or two), and follow the log
  with a filter, since every poll the test makes is a line:

  ```sh
  tail -n 0 -F "$SCRATCH/vmtest.log" | grep -E --line-buffered \
    "subtest:|!!!|Traceback|error:|Test .* failed|^exit "
  ```

- A passing run prints the test's output path and `exit 0`. A failing one prints `!!!` lines with the subtest, the
  command and a traceback, then "Cannot build '…-vm-test-run-chatddx.drv'" and `exit 1`. The whole log is in
  `nix log` of that derivation too.
- A passed test is cached: building it again does nothing until something it depends on changes. `--rebuild` runs it
  again.
- Noise in the log, not failures: `dhcpcd[…]: timed out` (the test network has no DHCP) and `cfg80211: failed to load
  regulatory.db`.

### 5. Check the formatting
```sh
nix run "path:$NIXPKGS#nixfmt" -- --check flake.nix nix/module.nix nix/test.nix
```

## What the test does
`nix/test.nix` boots one machine with the module, PostgreSQL 16, two workers and nginx for `chatddx.test`, with a
certificate it makes for itself, which the machine trusts. The sample World is copied out of the store into
`/var/lib/chatddx-test/sample` by tmpfiles, and its remote endpoint's secret is in `/var/lib/chatddx-test/secrets`,
mode 0400. Then:
1. **The operator's command**: `chatddx init-data alice --giftbag` and `chatddx person password alice`, as root,
   through the wrapper, which runs them as `chatddx_writer`; then `chatddx-fake-engines`, a service of the test's
   that runs `chatddx fake-engines` the same way, and its three ports.
2. **A run through the portal**: over HTTPS through nginx, sign in at `/api/session`, find
   `plan (en, Qwen/Qwen3-8B-AWQ)` of alice's, store a typed case, start a scored run at `qwen3-8b-awq@fake`, and wait
   until its job is no longer queued or under way; it must be finished. `chatddx portal` runs no worker, so this
   shows a worker service took it.
3. **nginx**: the headers of a GET of `/sign-in`, HSTS among them, and a 429 among twelve failed sign-ins sent at
   once, with `signInRate` at `1r/m` for the test.
4. **No proxy**: with `HTTPS_PROXY` set in the service manager's environment, a restarted worker's environment holds
   none.

## Timings
The first run, by emulation, after the packages were built and the NixOS closure was mostly substituted:

| Step | Seconds |
|---|---|
| booting the VM | 208 |
| until `chatddx-portal.service` is active (after boot) | 473 |
| until port 8000 answers | 180 |
| `chatddx init-data alice --giftbag` | 120 |
| until the fake engines' first port answers | 51 |
| subtest 2, the run, sent and scored | 39 |

About 20 minutes up to the end of subtest 2. With KVM it would be a few minutes.

## Debugging
- **The interactive driver**: `nix build "${OVERRIDES[@]}" .#checks.x86_64-linux.module.driverInteractive`, then
  `./result/bin/nixos-test-driver`, and in its Python prompt `start_all()`, `machine.succeed("…")` or
  `machine.shell_interact()`. It builds without the `system-features`, which only the test's run asks for, and runs
  by emulation here too.
- **The test script is checked** before it runs: typed with mypy and linted with pyflakes, so an unused import fails
  the build before the VM starts.
- **The flow on the host, before the VM**: the API calls of subtest 2 can be tried against the host's database in
  seconds. With PostgreSQL set up as AGENTS.md says, the environment from `.env-container`, the venv from `uv sync`,
  and the sample loaded (`chatddx init-data alice --giftbag`, then a password as below), run `chatddx fake-engines`,
  `chatddx portal --bind 127.0.0.1:8766` and `chatddx worker` in the background, and make the same calls with curl or
  a script. A container that restarted leaves PostgreSQL stopped: `pg_ctlcluster 16 main start`.

## What went wrong on the way
- **`curl -I` against the app** fails: FastAPI adds no HEAD to a GET route, so HEAD is 405. The test reads headers
  from a GET (`curl -sf -o /dev/null -D -`).
- **A limit that emulation doesn't reach**: at 10 a minute with a burst of 5, nginx takes a sign-in every 6 s beyond
  the burst. By emulation each `curl`, and the argon2 behind it, takes several seconds, so eight in a row all got 200.
  The test sends its sign-ins at once (`curl … &` in a loop, then `wait`), at `1r/m`.
- **`getpass` with no terminal**: `chatddx person password` reads `/dev/tty` when there is one. Under the test driver,
  `setsid -w` runs it without a controlling terminal, so that it reads the password from stdin.
- **`retry`** in the test driver takes `timeout` as a `datetime.timedelta`; a number of seconds is deprecated.
- **tmpfiles' `C`** copies the World into a directory the test makes first (`d`).
- **PostgreSQL's version**: the VM's default for its `stateVersion` isn't 16, which the module warns about, so the
  test pins `postgresql_16`.
- **`pkill -f chatddx`** from the Bash tool matches the tool's own shell, whose command line holds the pattern, and
  kills it. Match something narrower, such as `chatddx (portal|worker|fake-engines)`.

## Runs
- **First run**: subtests 1 and 2 passed; subtest 3 failed on `curl -sfI` (see "What went wrong on the way").
- **Second run**: subtests 1 and 2 passed, and the headers; the limit didn't answer 429 to sign-ins in a row (see
  "What went wrong on the way"). Its timings were within 10% of the first's.

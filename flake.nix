{
  description = "A reproducible and composable rig for accuracy assessment of LLMs in emergency care";

  inputs = {

    nixpkgs.url = "github:kompismoln/nixpkgs/nixos-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs = {
        nixpkgs.follows = "nixpkgs";
        pyproject-nix.follows = "pyproject-nix";
        uv2nix.follows = "uv2nix";
      };
    };

  };

  outputs =
    {
      self,
      nixpkgs,
      uv2nix,
      pyproject-nix,
      pyproject-build-systems,
    }:
    let
      name = "chatddx";
      version = toString (self.shortRev or self.dirtyShortRev or self.lastModified or "unknown");

      inherit (nixpkgs) lib;
      forAllSystems = lib.genAttrs lib.systems.flakeExposed;

      workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };

      overlay = workspace.mkPyprojectOverlay {
        sourcePreference = "wheel";
      };

      editableOverlay = workspace.mkEditablePyprojectOverlay {
        root = "$REPO_ROOT";
      };

      pythonSets = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          python = pkgs.python313;
        in
        (pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        }).overrideScope
          (
            lib.composeManyExtensions [
              pyproject-build-systems.overlays.wheel
              overlay
            ]
          )
      );

      frontend =
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        pkgs.stdenv.mkDerivation (finalAttrs: {
          pname = "${name}-frontend";
          inherit version;
          src = lib.fileset.toSource {
            root = ./.;
            fileset = lib.fileset.unions [
              ./frontend
              # Accommodating for Tailwind, which reads the portal's templates beside the frontend
              # (frontend/src/portal.css).
              ./src/chatddx/portal/templates
            ];
          };
          pnpmRoot = "frontend";
          nativeBuildInputs = [
            pkgs.nodejs_22
            pkgs.pnpm
            pkgs.pnpmConfigHook
          ];
          pnpmDeps = pkgs.fetchPnpmDeps {
            inherit (finalAttrs) pname version;
            src = ./frontend;
            fetcherVersion = 4;
            hash = "sha256-/i0p8mORqPJPC2A9QDfjLP9/p2yLcuKTojfPLcQpUpI=";
          };
          buildPhase = ''
            runHook preBuild
            pnpm --dir frontend build
            runHook postBuild
          '';
          installPhase = ''
            runHook preInstall
            cp -r frontend/dist $out
            runHook postInstall
          '';
        });

      devEnv =
        system:
        (pythonSets.${system}.overrideScope editableOverlay).mkVirtualEnv "${name}-dev-env"
          workspace.deps.all;

      dev-db =
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        pkgs.writeShellApplication {
          name = "dev-db";
          runtimeInputs = [
            pkgs.postgresql_16
            pkgs.coreutils
          ];
          text = builtins.readFile ./scripts/dev-db.sh;
        };

      # Optimization: a stage of scripts/check.sh sees only the files it reads, so that nix runs
      # it again only when one of them changes.
      check =
        system: stage: fileset: attrs:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        pkgs.stdenvNoCC.mkDerivation (
          {
            name = "${name}-check-${stage}";
            src = lib.fileset.toSource {
              root = ./.;
              fileset = lib.fileset.unions [
                fileset
                ./scripts/check.sh
              ];
            };
            buildPhase = ''
              runHook preBuild
              bash scripts/check.sh ${stage}
              runHook postBuild
            '';
            installPhase = "touch $out";
          }
          // attrs
        );

    in
    {

      packages = forAllSystems (system: {
        default = pythonSets.${system}.mkVirtualEnv "chatddx-env" workspace.deps.default;
        frontend = frontend system;
      });

      nixosModules.default = lib.modules.importApply ./nix/module.nix { inherit self; };

      checks = lib.genAttrs [ "x86_64-linux" "aarch64-linux" ] (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          module = import ./nix/test.nix {
            inherit pkgs self;
          };
          module-eval = import ./nix/module-eval.nix {
            inherit pkgs self;
            inherit (lib) nixosSystem;
          };

          docs =
            check system "docs"
              (lib.fileset.unions [
                ./docs
                ./agents
                ./AGENTS.md
                ./README.md
                ./scripts/refcheck.py
                ./src
              ])
              {
                nativeBuildInputs = [ pkgs.python313 ];
              };

          # Compromise: scripts/check.sh's browser stage isn't checked here, for the browser
          # it starts.
          package =
            check system "package"
              (lib.fileset.unions [
                ./src
                ./worlds
                ./docs/surfaces
                ./frontend/openapi.json
                ./pyproject.toml
                ./uv.lock
                ./scripts/dev-db.sh
                ./.env-devshell
              ])
              {
                nativeBuildInputs = [
                  (devEnv system)
                  (dev-db system)
                ];
                # Accommodating for stdenv's SSL_CERT_FILE, a file that isn't there, which httpx2
                # loads for plain HTTP too.
                preBuild = ''
                  unset PYTHONPATH
                  export HOME="$TMPDIR" REPO_ROOT="$PWD" CHATDDX_STATE_HOME="$PWD"
                  export SSL_CERT_FILE="${pkgs.cacert}/etc/ssl/certs/ca-bundle.crt"
                  set -a && source .env-devshell && set +a
                  dev-db start
                '';
                postBuild = "dev-db stop";
              };

          frontend =
            check system "frontend"
              (lib.fileset.unions [
                ./frontend
                ./src/chatddx/portal/templates
                ./worlds/test/_data/schemas
                ./worlds/sample/_data/schemas
              ])
              {
                pnpmRoot = "frontend";
                inherit (frontend system) pnpmDeps;
                nativeBuildInputs = [
                  pkgs.nodejs_22
                  pkgs.pnpm
                  pkgs.pnpmConfigHook
                ];
              };
        }
      );

      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
          pythonSet = pythonSets.${system}.overrideScope editableOverlay;

          # Accommodating for playwright, which launches only the browsers of its own minor
          # release, and the browser tests, which launch only the headless shell.
          browsers =
            let
              pinned = pythonSet.playwright.version;
              packaged = pkgs.playwright-driver.version;
            in
            lib.warnIf (lib.versions.majorMinor pinned != lib.versions.majorMinor packaged)
              "pyproject.toml pins playwright ${pinned}, nixpkgs' playwright-driver is ${packaged}: the browser tests find no browser of their minor release, and skip"
              (
                pkgs.playwright-driver.browsers.override {
                  withChromium = false;
                  withFirefox = false;
                  withWebkit = false;
                }
              );
        in
        {
          default = pkgs.mkShell {
            inherit name;

            packages = [
              (devEnv system)
              (dev-db system)
              pkgs.uv
              pkgs.nodejs_22
              pkgs.pnpm
            ];

            env = {
              UV_NO_SYNC = "1";
              UV_PYTHON = pythonSet.python.interpreter;
              UV_PYTHON_DOWNLOADS = "never";
              UV_VENV = "/dev/null";
              PLAYWRIGHT_BROWSERS_PATH = "${browsers}";
              PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS = "true";
            };

            shellHook = ''
              unset PYTHONPATH
              export REPO_ROOT=$(git rev-parse --show-toplevel)
              export CHATDDX_STATE_HOME="$HOME/.local/state"
              set -a && source "$REPO_ROOT/.env" && set +a
              echo "• Flake version: ${version}"
              echo "• Nixpkgs:       ${nixpkgs.shortRev}"
              echo "• Python path:   $UV_PYTHON"
            '';
          };
        }
      );
    };
}

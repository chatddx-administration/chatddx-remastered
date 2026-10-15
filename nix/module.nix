{
  config,
  lib,
  pkgs,
  inputs,
  ...
}:
let
  cfg = config.services.chatddx;
  flake = inputs.chatddx;
  system = pkgs.stdenv.hostPlatform.system;
  inherit (lib) mkOption types;

  # Peer authentication on the socket maps each system user to the role of its name.
  admin = "chatddx";
  writer = "chatddx_writer";

  environment = {
    DB_HOST = cfg.database.host;
    DB_NAME = cfg.database.name;
    DB_USER = writer;
    DB_ADMIN = admin;
    HOST = cfg.listen;
    CHATDDX_WORLD = cfg.world;
    CHATDDX_PORTAL_ASSETS = "${cfg.frontend}";
    PYTHONUNBUFFERED = "1";
  }
  // lib.optionalAttrs (cfg.revision != null) { CHATDDX_REVISION = cfg.revision; };

  facts = lib.concatMap (f: [
    "--facts"
    "${f}"
  ]) cfg.facts;

  # The engine client follows a proxy named in its environment (src/chatddx/runner/wire.py).
  proxies = [
    "http_proxy"
    "HTTP_PROXY"
    "https_proxy"
    "HTTPS_PROXY"
    "all_proxy"
    "ALL_PROXY"
  ];

  hardened = {
    UnsetEnvironment = proxies;
    UMask = "0077";
    NoNewPrivileges = true;
    CapabilityBoundingSet = "";
    PrivateTmp = true;
    PrivateDevices = true;
    ProtectSystem = "strict";
    ProtectHome = true;
    ProtectProc = "invisible";
    ProtectClock = true;
    ProtectHostname = true;
    ProtectKernelTunables = true;
    ProtectKernelModules = true;
    ProtectKernelLogs = true;
    ProtectControlGroups = true;
    RestrictAddressFamilies = [
      "AF_UNIX"
      "AF_INET"
      "AF_INET6"
    ];
    RestrictNamespaces = true;
    RestrictRealtime = true;
    RestrictSUIDSGID = true;
    LockPersonality = true;
    RemoveIPC = true;
    SystemCallArchitectures = "native";
    SystemCallFilter = [
      "@system-service"
      "~@privileged"
    ];
  };

  migrated = {
    after = [ "chatddx-migrate.service" ];
    requires = [ "chatddx-migrate.service" ];
    wantedBy = [ "chatddx.target" ];
    partOf = [ "chatddx.target" ];
    inherit environment;
  };

  served =
    command:
    hardened
    // {
      User = writer;
      Group = writer;
      ExecStart = lib.escapeShellArgs (
        [
          "${cfg.package}/bin/chatddx"
          command
        ]
        ++ facts
      );
      EnvironmentFile = lib.optional (cfg.environmentFile != null) cfg.environmentFile;
      Restart = "on-failure";
    };

  operator = pkgs.writeShellApplication {
    name = "chatddx";
    runtimeInputs = [ pkgs.util-linux ];
    text = ''
      user=${writer}
      if [ "''${1-}" = migrate ]; then
        user=${admin}
      fi
      ${lib.concatStrings (
        lib.mapAttrsToList (k: v: "export ${k}=${lib.escapeShellArg v}\n") environment
      )}
      ${lib.optionalString (cfg.environmentFile != null) ''
        if [ -r ${lib.escapeShellArg cfg.environmentFile} ]; then
          set -a
          # shellcheck disable=SC1091
          . ${lib.escapeShellArg cfg.environmentFile}
          set +a
        fi
      ''}
      if [ "$(id -u)" = 0 ]; then
        exec runuser -u "$user" -- ${cfg.package}/bin/chatddx "$@"
      fi
      exec ${cfg.package}/bin/chatddx "$@"
    '';
  };
in
{
  options.services.chatddx = {
    enable = lib.mkEnableOption "chatddx: the portal with the API, its workers and its database";

    package = mkOption {
      type = types.package;
      default = flake.packages.${system}.default;
      defaultText = lib.literalExpression "inputs.chatddx.packages.\${system}.default";
      description = "The Python environment with `chatddx` on its PATH.";
    };

    frontend = mkOption {
      type = types.package;
      default = flake.packages.${system}.frontend;
      defaultText = lib.literalExpression "inputs.chatddx.packages.\${system}.frontend";
      description = "The portal's build, served at `/static/` (`CHATDDX_PORTAL_ASSETS`).";
    };

    revision = mkOption {
      type = types.nullOr types.str;
      default = flake.rev or flake.dirtyRev or null;
      defaultText = lib.literalExpression "inputs.chatddx.rev or inputs.chatddx.dirtyRev or null";
      description = "The code's revision, recorded with every run (`CHATDDX_REVISION`).";
    };

    world = mkOption {
      type = types.externalPath;
      example = "/var/lib/chatddx/world";
      description = ''
        The World directory (`CHATDDX_WORLD`): its inventory, its facts and its directory sources' vignettes, which
        are sensitive unless declared otherwise. It is kept out of the Nix store, which every user of the host can
        read, and should be readable by `${writer}` alone. It can't be under /home, which the services can't see.
      '';
    };

    facts = mkOption {
      type = types.listOf types.path;
      default = [ ];
      description = "More model facts, beside the bundled ones and the World's (`--facts`).";
    };

    listen = mkOption {
      type = types.str;
      default = "127.0.0.1:8000";
      description = "Where `chatddx portal` listens, as HOST:PORT (`HOST`).";
    };

    workers = mkOption {
      type = types.ints.unsigned;
      default = 1;
      description = "How many `chatddx worker` services run, as `chatddx-worker-1` and on.";
    };

    environmentFile = mkOption {
      type = types.nullOr types.externalPath;
      default = null;
      example = "/run/secrets/chatddx";
      description = ''
        The endpoints' secrets, as `NAME=value` lines under the variables the inventory's endpoints name in
        `credential`. systemd reads it for the portal and the workers, so it can be readable by root alone; the
        `chatddx` command reads it too when run as root.
      '';
    };

    database = {
      createLocally = mkOption {
        type = types.bool;
        default = true;
        description = ''
          Whether to set up PostgreSQL on this host with the database, the admin `${admin}` and the writer
          `${writer}`, reached on its socket by peer authentication. Otherwise they are made as
          `src/chatddx/store/setup.sql` makes them, wherever `host` points.
        '';
      };

      host = mkOption {
        type = types.str;
        default = "/run/postgresql";
        description = "The database server's host, or the directory of its socket (`DB_HOST`).";
      };

      name = mkOption {
        type = types.str;
        default = "chatddx";
        description = "The database (`DB_NAME`).";
      };

      tier = mkOption {
        type = types.enum [
          1
          2
        ];
        default = 2;
        description = ''
          The tier `chatddx migrate` applies migrations up to. Tier 0 has no grants, and the services connect as the
          writer.
        '';
      };
    };

    nginx = {
      enable = lib.mkEnableOption "nginx in front of the portal, on HTTPS, with a limit on sign-ins";

      hostName = mkOption {
        type = types.str;
        example = "chatddx.example.org";
        description = "The portal's public host name, its virtual host in `services.nginx`.";
      };

      signInRate = mkOption {
        type = types.str;
        default = "10r/m";
        description = "How often one address may try to sign in, as nginx's `limit_req_zone` takes it.";
      };
    };
  };

  config = lib.mkIf cfg.enable (
    lib.mkMerge [
      {
        assertions = [
          {
            assertion = cfg.database.createLocally -> cfg.database.name == admin;
            message = "services.chatddx.database.name must be ${admin} when createLocally, the admin owning it";
          }
        ];

        warnings =
          lib.optional
            (
              cfg.database.createLocally && lib.versions.major config.services.postgresql.package.version != "16"
            )
            "services.chatddx: chatddx is developed and tested on PostgreSQL 16, and this host serves another";

        users.users.${admin} = {
          isSystemUser = true;
          group = admin;
        };
        users.groups.${admin} = { };
        users.users.${writer} = {
          isSystemUser = true;
          group = writer;
        };
        users.groups.${writer} = { };

        environment.systemPackages = [ operator ];

        systemd.targets.chatddx = {
          description = "chatddx";
          wantedBy = [ "multi-user.target" ];
        };

        systemd.services = {
          chatddx-migrate = {
            description = "chatddx: the database's migrations";
            after = if cfg.database.createLocally then [ "postgresql.target" ] else [ "network-online.target" ];
            requires = lib.optional cfg.database.createLocally "postgresql.target";
            wants = lib.optional (!cfg.database.createLocally) "network-online.target";
            wantedBy = [ "chatddx.target" ];
            partOf = [ "chatddx.target" ];
            inherit environment;
            serviceConfig = hardened // {
              Type = "oneshot";
              RemainAfterExit = true;
              User = admin;
              Group = admin;
              ExecStart = "${cfg.package}/bin/chatddx migrate --tier ${toString cfg.database.tier}";
            };
          };

          chatddx-portal = migrated // {
            description = "chatddx: the portal and the API";
            serviceConfig = served "portal";
          };
        }
        // lib.listToAttrs (
          map (
            i:
            lib.nameValuePair "chatddx-worker-${toString i}" (
              migrated
              // {
                description = "chatddx: worker ${toString i}";
                serviceConfig = served "worker" // {
                  # Above the worker's deadline for its scorings (src/chatddx/settings.py:WORKER_DEADLINE).
                  TimeoutStopSec = "90s";
                };
              }
            )
          ) (lib.range 1 cfg.workers)
        );
      }

      (lib.mkIf cfg.database.createLocally {
        services.postgresql = {
          enable = true;
          ensureDatabases = [ cfg.database.name ];
          ensureUsers = [
            {
              name = admin;
              ensureDBOwnership = true;
              ensureClauses = {
                login = true;
                createrole = true;
              };
            }
            {
              name = writer;
              ensureClauses.login = true;
            }
          ];
        };
      })

      (lib.mkIf cfg.nginx.enable {
        services.nginx = {
          enable = true;
          recommendedProxySettings = true;
          recommendedTlsSettings = true;
          commonHttpConfig = ''
            map $request_method $chatddx_signing_in {
              POST $binary_remote_addr;
              default "";
            }
            limit_req_zone $chatddx_signing_in zone=chatddx_signing_in:1m rate=${cfg.nginx.signInRate};
          '';
          virtualHosts.${cfg.nginx.hostName} =
            let
              proxied = {
                proxyPass = "http://${cfg.listen}";
              };
              signingIn = proxied // {
                extraConfig = ''
                  limit_req zone=chatddx_signing_in burst=5 nodelay;
                  limit_req_status 429;
                '';
              };
            in
            {
              forceSSL = true;
              enableACME = lib.mkDefault true;
              extraConfig = ''
                add_header Strict-Transport-Security "max-age=31536000" always;
                add_header X-Content-Type-Options nosniff always;
                add_header Referrer-Policy same-origin always;
                add_header Content-Security-Policy "frame-ancestors 'none'" always;
              '';
              locations = {
                "/" = proxied;
                "= /sign-in" = signingIn;
                "= /api/session" = signingIn;
              };
            };
        };
      })
    ]
  );
}

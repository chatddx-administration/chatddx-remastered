{
  pkgs,
  self,
  nixosSystem,
}:
let
  inherit (pkgs) lib;
  inherit (pkgs.stdenv.hostPlatform) system;

  evaluated =
    extra:
    (nixosSystem {
      inherit system;
      modules = [
        self.nixosModules.default
        {
          boot.loader.grub.enable = false;
          fileSystems."/" = {
            device = "/dev/null";
            fsType = "ext4";
          };
          system.stateVersion = lib.trivial.release;
          services.postgresql.package = lib.mkOverride 900 pkgs.postgresql_17;
          services.chatddx = {
            enable = true;
            world = lib.mkOverride 900 "/var/lib/chatddx/world";
          };
        }
        extra
      ];
    }).config;

  ofAnOrg = {
    users.users.chatddx-test = {
      isSystemUser = true;
      group = "chatddx-test";
      uid = 3017;
      home = "/var/lib/chatddx-test";
      createHome = true;
    };
    users.groups.chatddx-test = {
      gid = 3017;
      members = [ "chatddx_writer" ];
    };
    services.chatddx = {
      admin = "chatddx-test";
      listen = "[fd00::3017:11]:8000";
      world = "/var/lib/chatddx-test/sample";
      nginx = {
        enable = true;
        hostName = "chatddx.test";
      };
    };
  };

  services =
    config: lib.attrNames (lib.filterAttrs (n: _: lib.hasPrefix "chatddx" n) config.systemd.services);

  environment = config: {
    inherit (config.systemd.services.chatddx-portal.environment)
      DB_ADMIN
      DB_USER
      DB_NAME
      HOST
      CHATDDX_WORLD
      ;
  };

  refused = value: !(builtins.tryEval (builtins.deepSeq value value)).success;

  cases = {
    defaults =
      let
        config = evaluated { };
      in
      {
        services = services config;
        environment = environment config;
        migrate = config.systemd.services.chatddx-migrate.serviceConfig.User;
        portal = config.systemd.services.chatddx-portal.serviceConfig.User;
        roles = map (u: u.name) config.services.postgresql.ensureUsers;
        databases = config.services.postgresql.ensureDatabases;
        inherit (config) warnings;
      };

    the_flakes_packages =
      let
        config = evaluated { };
        packages = self.packages.${system};
      in
      {
        package = config.services.chatddx.package.drvPath == packages.default.drvPath;
        frontend = config.services.chatddx.frontend.drvPath == packages.frontend.drvPath;
        assets =
          config.systemd.services.chatddx-portal.environment.CHATDDX_PORTAL_ASSETS == "${packages.frontend}";
      };

    an_orgs_admin =
      let
        config = evaluated ofAnOrg;
      in
      {
        environment = environment config;
        migrate = config.systemd.services.chatddx-migrate.serviceConfig.User;
        admin = {
          inherit (config.users.users.chatddx-test)
            isSystemUser
            group
            uid
            home
            ;
        };
        chatddx = config.users.users ? chatddx;
        roles = map (u: u.name) config.services.postgresql.ensureUsers;
        databases = config.services.postgresql.ensureDatabases;
        proxied = config.services.nginx.virtualHosts."chatddx.test".locations."/".proxyPass;
        inherit (config) warnings;
      };

    workers =
      let
        config = evaluated {
          services.chatddx.workers = 3;
        };
      in
      {
        services = services config;
        stop = config.systemd.services.chatddx-worker-3.serviceConfig.TimeoutStopSec;
        command = lib.removePrefix "${config.services.chatddx.package}/bin/" config.systemd.services.chatddx-worker-3.serviceConfig.ExecStart;
      };

    no_workers_nor_local_database =
      let
        config = evaluated {
          services.chatddx = {
            workers = 0;
            database = {
              createLocally = false;
              host = "db.example.org";
            };
          };
        };
      in
      {
        services = services config;
        postgresql = config.services.postgresql.enable;
        after = config.systemd.services.chatddx-migrate.after;
        host = config.systemd.services.chatddx-portal.environment.DB_HOST;
      };

    ordering =
      let
        config = evaluated { };
      in
      {
        migrate = {
          inherit (config.systemd.services.chatddx-migrate) after requires;
        };
        portal = {
          inherit (config.systemd.services.chatddx-portal) after requires;
        };
      };

    sandbox = {
      inherit ((evaluated { }).systemd.services.chatddx-portal.serviceConfig)
        ProtectSystem
        ProtectHome
        UMask
        UnsetEnvironment
        ;
    };

    postgresql_versions = lib.genAttrs [ "16" "17" "18" ] (
      major: (evaluated { services.postgresql.package = pkgs."postgresql_${major}"; }).warnings
    );

    database_of_another_name =
      let
        config = evaluated { services.chatddx.database.name = "other"; };
      in
      lib.filter (lib.hasPrefix "services.chatddx") (
        map (a: a.message) (lib.filter (a: !a.assertion) config.assertions)
      );

    store_paths = {
      world = refused (evaluated { services.chatddx.world = "${pkgs.hello}"; }).services.chatddx.world;
      environmentFile =
        refused
          (evaluated { services.chatddx.environmentFile = "${pkgs.hello}"; })
          .services.chatddx.environmentFile;
      outside = refused (evaluated { }).services.chatddx.world;
    };
  };

  expected = {
    defaults = {
      services = [
        "chatddx-migrate"
        "chatddx-portal"
        "chatddx-worker-1"
      ];
      environment = {
        DB_ADMIN = "chatddx";
        DB_USER = "chatddx_writer";
        DB_NAME = "chatddx";
        HOST = "127.0.0.1:8000";
        CHATDDX_WORLD = "/var/lib/chatddx/world";
      };
      migrate = "chatddx";
      portal = "chatddx_writer";
      roles = [
        "chatddx"
        "chatddx_writer"
      ];
      databases = [ "chatddx" ];
      warnings = [ ];
    };

    the_flakes_packages = {
      package = true;
      frontend = true;
      assets = true;
    };

    an_orgs_admin = {
      environment = {
        DB_ADMIN = "chatddx-test";
        DB_USER = "chatddx_writer";
        DB_NAME = "chatddx-test";
        HOST = "[fd00::3017:11]:8000";
        CHATDDX_WORLD = "/var/lib/chatddx-test/sample";
      };
      migrate = "chatddx-test";
      admin = {
        isSystemUser = true;
        group = "chatddx-test";
        uid = 3017;
        home = "/var/lib/chatddx-test";
      };
      chatddx = false;
      roles = [
        "chatddx-test"
        "chatddx_writer"
      ];
      databases = [ "chatddx-test" ];
      proxied = "http://[fd00::3017:11]:8000";
      warnings = [ ];
    };

    workers = {
      services = [
        "chatddx-migrate"
        "chatddx-portal"
        "chatddx-worker-1"
        "chatddx-worker-2"
        "chatddx-worker-3"
      ];
      stop = "90s";
      command = "chatddx worker";
    };

    no_workers_nor_local_database = {
      services = [
        "chatddx-migrate"
        "chatddx-portal"
      ];
      postgresql = false;
      after = [ "network-online.target" ];
      host = "db.example.org";
    };

    ordering = {
      migrate = {
        after = [ "postgresql.target" ];
        requires = [ "postgresql.target" ];
      };
      portal = {
        after = [ "chatddx-migrate.service" ];
        requires = [ "chatddx-migrate.service" ];
      };
    };

    sandbox = {
      ProtectSystem = "strict";
      ProtectHome = true;
      UMask = "0077";
      UnsetEnvironment = [
        "http_proxy"
        "HTTP_PROXY"
        "https_proxy"
        "HTTPS_PROXY"
        "all_proxy"
        "ALL_PROXY"
      ];
    };

    postgresql_versions = {
      "16" = [ ];
      "17" = [ ];
      "18" = [
        "services.chatddx: chatddx is developed and tested on PostgreSQL 16 and 17, and this host serves another"
      ];
    };

    database_of_another_name = [
      "services.chatddx.database.name must be the admin's, chatddx, when createLocally, the admin owning it"
    ];

    store_paths = {
      world = true;
      environmentFile = true;
      outside = false;
    };
  };

  failures = lib.runTests (
    lib.mapAttrs' (
      name: expr:
      lib.nameValuePair "test_${name}" {
        inherit expr;
        expected = expected.${name};
      }
    ) cases
  );
in
pkgs.runCommand "chatddx-module-eval"
  {
    passthru = { inherit cases failures; };
    failures = builtins.toJSON failures;
    nativeBuildInputs = [ pkgs.jq ];
  }
  ''
    if [ "$failures" != "[]" ]; then
      echo "$failures" | jq .
      exit 1
    fi
    touch $out
  ''

{ pkgs, self }:
let
  host = "chatddx.test";
  password = "correct horse";
  cert = pkgs.runCommand "chatddx-test-cert" { nativeBuildInputs = [ pkgs.openssl ]; } ''
    mkdir $out
    openssl req -x509 -newkey rsa:2048 -nodes -days 36500 -subj /CN=${host} \
      -addext subjectAltName=DNS:${host} -keyout $out/key.pem -out $out/cert.pem
  '';
in
pkgs.testers.runNixOSTest {
  name = "chatddx";

  nodes.machine = {
    imports = [ self.nixosModules.default ];
    virtualisation.memorySize = 2048;
    services.postgresql.package = pkgs.postgresql_17;
    # Accommodating for emulation: initdb alone can take longer than the unit's 120 s by TCG, and then the
    # chatddx services, failed on the dependency, aren't started again.
    systemd.services.postgresql.serviceConfig.TimeoutSec = pkgs.lib.mkForce 600;
    networking.hosts."127.0.0.1" = [ host ];
    security.pki.certificateFiles = [ "${cert}/cert.pem" ];

    # The admin as an org declares it: a user of its own, with a home, that the World is in.
    users.users.chatddx-test = {
      isSystemUser = true;
      group = "chatddx-test";
      home = "/var/lib/chatddx-test";
      homeMode = "0750";
      createHome = true;
    };
    users.groups.chatddx-test.members = [ "chatddx_writer" ];

    services.chatddx = {
      enable = true;
      admin = "chatddx-test";
      listen = "[::1]:8000";
      world = "/var/lib/chatddx-test/sample";
      environmentFile = "/var/lib/chatddx-test/secrets";
      workers = 2;
      nginx = {
        enable = true;
        hostName = host;
        signInRate = "1r/m";
      };
    };
    services.nginx.virtualHosts.${host} = {
      enableACME = false;
      sslCertificate = "${cert}/cert.pem";
      sslCertificateKey = "${cert}/key.pem";
    };

    systemd.tmpfiles.settings.chatddx-test = {
      "/var/lib/chatddx-test".d = {
        mode = "0750";
        user = "chatddx-test";
        group = "chatddx-test";
      };
      "/var/lib/chatddx-test/sample".C.argument = "${self}/worlds/sample";
      "/var/lib/chatddx-test/secrets".f = {
        mode = "0400";
        argument = "CHATDDX_SAMPLE_KEY=sample-key";
      };
    };

    systemd.services.chatddx-fake-engines = {
      path = [ "/run/current-system/sw" ];
      script = "exec chatddx fake-engines";
    };
  };

  testScript = ''
    import datetime
    import json
    import shlex

    def call(method, path, body=None, token=None):
        asked = ["curl", "-sf", "-X", method, "https://${host}" + path]
        asked += ["-H", "content-type: application/json"]
        if token:
            asked += ["-H", f"authorization: Bearer {token}"]
        if body is not None:
            asked += ["-d", json.dumps(body)]
        return json.loads(machine.succeed(shlex.join(asked)))

    machine.wait_for_unit("chatddx-portal.service")
    machine.wait_for_unit("chatddx-worker-2.service")
    machine.wait_for_unit("nginx.service")
    machine.wait_for_open_port(8000, "::1")

    with subtest("the admin is the host's own user, and the World is reached through its group"):
        assert machine.succeed("systemctl show -P User chatddx-migrate").strip() == "chatddx-test"
        machine.succeed("runuser -u chatddx_writer -- cat /var/lib/chatddx-test/sample/inventory.toml")
        machine.fail("runuser -u nobody -- cat /var/lib/chatddx-test/sample/inventory.toml")

    with subtest("the operator's command runs as the writer, with the services' World"):
        machine.succeed("chatddx init-data alice --giftbag")
        machine.succeed("printf '%s\n%s\n' '${password}' '${password}' | setsid -w chatddx person password alice")
        machine.succeed("systemctl start chatddx-fake-engines")
        for port in (12099, 12100, 12101):
            machine.wait_for_open_port(port)

    with subtest("the portal queues a typed case's run, and a worker sends and scores it"):
        token = call("POST", "/api/session", {"login": "alice", "password": "${password}"})["token"]
        name = "plan"
        [configuration] = call("GET", "/api/threads?kind=configuration&owner=alice&name=" + name.replace(" ", "%20"), token=token)
        family = call("POST", "/api/families", {"text": "A woman of 79 fell at home.", "language": "en"}, token)
        body = {"configuration": configuration["id"], "endpoint": "qwen3-8b-awq@fake", "families": [family["id"]], "score": True}
        run = call("POST", "/api/runs", body, token)["runs"][0]["run"]

        def ended(_):
            job = call("GET", f"/api/runs/{run}", token=token)["job"]
            return job["status"] not in ("queued", "under way")

        retry(ended, timeout=datetime.timedelta(minutes=10))
        job = call("GET", f"/api/runs/{run}", token=token)["job"]
        assert job["status"] == "finished", job

    with subtest("nginx sends the headers and limits sign-ins"):
        headers = machine.succeed("curl -sf -o /dev/null -D - https://${host}/sign-in").lower()
        assert "strict-transport-security" in headers, headers
        codes = machine.succeed(
            "for _ in $(seq 12); do curl -s -o /dev/null -w '%{http_code}\\n' -X POST"
            + " -d login=nobody -d password=wrong https://${host}/sign-in & done; wait"
        ).split()
        assert "429" in codes, codes

    with subtest("the services see no proxy"):
        machine.succeed("systemctl set-environment HTTPS_PROXY=http://127.0.0.1:9")
        machine.succeed("systemctl restart chatddx-worker-1")
        pid = machine.succeed("systemctl show -P MainPID chatddx-worker-1").strip()
        machine.fail(f"grep -qz HTTPS_PROXY /proc/{pid}/environ")
  '';
}

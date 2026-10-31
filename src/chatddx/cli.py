import argparse
import getpass
import json
import logging
import signal
import subprocess
import sys
import threading
from collections import Counter
from collections.abc import Callable, Sequence
from pathlib import Path
from types import FrameType

import psycopg
import uvicorn
from fastapi import FastAPI

from chatddx import locale, settings
from chatddx.api.app import app
from chatddx.bench import Bench
from chatddx.bench.handles import broken
from chatddx.curation import load_cases, plan_factors, provision, repair, sync, wipe
from chatddx.curation.write import ARCHIVE
from chatddx.factors.base import resolve
from chatddx.factors.request import Skeleton
from chatddx.factors.trial import Trial
from chatddx.facts import BUNDLED, Facts
from chatddx.fake_vllm.script import Script
from chatddx.fake_vllm.server import run, run_all
from chatddx.identity import Role
from chatddx.importers.o11n import (
    Imported,
    checked,
    endpoints_toml,
    engines_toml,
    imported,
    read,
)
from chatddx.inventory import DirectorySource, Inventory, World, check
from chatddx.ledger import RunStarted
from chatddx.portal.app import app as portal
from chatddx.portal.assets import Assets
from chatddx.repl.loop import HISTORY, loop
from chatddx.repl.shell import Repl, console
from chatddx.rig import rig
from chatddx.runner import Refused, outcome
from chatddx.scripted import (
    RUNS,
    fake_at,
    ran_before,
    review as review_scripted,
    run as run_scripted,
    scripted_runs,
)
from chatddx.store import Rows
from chatddx.store.migrate import TOP_TIER, migrate, pending
from chatddx.store.people import People
from chatddx.store.store import Connection, Store
from chatddx.worker import Worker


def _migrate(args: argparse.Namespace) -> None:
    tier = int(args.tier)
    with psycopg.connect(settings.database(admin=True)) as conn:
        if args.dry_run:
            names = [m.name for m in pending(conn, tier)]
        else:
            names = migrate(conn, tier)
    verb = "would apply" if args.dry_run else "applied"
    for name in names:
        print(f"{verb} {name}")
    if not names:
        print(f"nothing to apply up to tier {tier}")


def _person_add(args: argparse.Namespace) -> None:
    with psycopg.connect(settings.database()) as conn:
        person = People(conn).add(args.login, args.name, map(Role, args.role))
    print(f"added {person.login} (id {person.id})")


def _person_password(args: argparse.Namespace) -> None:
    password = getpass.getpass(f"new password for {args.login}: ")
    if not password:
        raise SystemExit("a password can't be empty")
    if getpass.getpass("again: ") != password:
        raise SystemExit("passwords don't match")
    with psycopg.connect(settings.database()) as conn:
        people = People(conn)
        person = people.find(args.login)
        if person is None:
            raise SystemExit(f"no person with login {args.login!r}")
        people.set_password(person.id, password)
    print(f"password set for {args.login}")


# Policy: a World's data set is where the World itself doesn't read it; sync-archive's by
# default.
DATA = "_data"


def _world(command: str, path: Path | None) -> World:
    path = path or settings.world()
    if path is None:
        raise SystemExit(f"{command}: give a World with --world DIR or CHATDDX_WORLD")
    try:
        return World.load(path)
    except LookupError as e:
        raise SystemExit(f"{command}: {e}") from None


def _held(command: str, world: World, conn: Connection) -> None:
    if found := broken(Rows(conn), world.inventory):
        raise SystemExit(
            f"{command}: {world.path}, as loaded:\n"
            + "\n".join(f"  {f}" for f in found)
        )


def _sync_archive(args: argparse.Namespace) -> None:
    world = _world("sync-archive", args.world)
    data: Path = args.data or world.path / DATA
    if not data.is_dir():
        raise SystemExit(
            f"sync-archive: {world.path} has no {DATA}/: give a data set with --data DIR"
        )
    try:
        facts = Facts.load(BUNDLED, *world.facts, *(args.facts or ()))
        plan = plan_factors(data, facts, rig(), world)
        cases = load_cases(data)
    except ValueError as e:
        raise SystemExit(f"sync-archive: {e}") from None
    try:
        source = world.inventory.source(args.source, DirectorySource)
    except LookupError as e:
        raise SystemExit(f"sync-archive: {world.path}: {e}") from None
    if not set(cases) & set(source.ids()):
        raise SystemExit(
            f"sync-archive: none of the data's {len(cases)} cases is in source "
            + f"{source.name!r} of {world.path}"
        )
    with psycopg.connect(settings.database()) as conn, conn.transaction():
        lines = sync(conn, plan, cases, source)
        _held("sync-archive, refused and nothing written", world, conn)
    findings = check(world.inventory, plan.registry.get)
    lines += [f"[world {f.level}] {f.subject}: {f.code}: {f.message}" for f in findings]
    n, m = len(findings), len(world.inventory.endpoints)
    lines.append(
        f"[world] {n} finding{'' if n == 1 else 's'} in {m} endpoint"
        + f"{'' if m == 1 else 's'} of {world.path}"
    )
    for line in lines:
        print(line)


def _person_provision(args: argparse.Namespace) -> None:
    if args.login == ARCHIVE:
        raise SystemExit(
            f"person provision: {ARCHIVE!r} holds what is provisioned; it isn't "
            + "provisioned"
        )
    lines: list[str] = []
    with psycopg.connect(settings.database()) as conn, conn.transaction():
        people = People(conn)
        if people.find(ARCHIVE) is None:
            raise SystemExit(
                f"person provision: no {ARCHIVE!r} yet; sync-archive loads it"
            )
        user = people.find(args.login)
        if user is None:
            user = people.add(args.login, args.name or args.login)
            lines.append(f"[person] {args.login}: added")
        lines += provision(conn, user)
    for line in lines:
        print(line)


def _repair_data(args: argparse.Namespace) -> None:
    world = _world("repair-data", args.world)
    try:
        source = world.inventory.source(args.source, DirectorySource)
    except LookupError as e:
        raise SystemExit(f"repair-data: {world.path}: {e}") from None
    with psycopg.connect(settings.database()) as conn:
        archive = People(conn).find(ARCHIVE)
        if archive is None:
            raise SystemExit(f"repair-data: no {ARCHIVE!r} yet; sync-archive loads it")
        lines = repair(conn, source, archive, dry=args.dry_run)
    for line in lines:
        print(line)


def _wipe_data(args: argparse.Namespace) -> None:
    if args.user == ARCHIVE:
        raise SystemExit(
            f"wipe-data: {ARCHIVE!r} holds what sync-archive loads; it isn't wiped"
        )
    with psycopg.connect(settings.database()) as conn:
        user = People(conn).find(args.user)
        if user is None:
            raise SystemExit(f"wipe-data: no person with login {args.user!r}")
        lines = wipe(conn, user)
    for line in lines:
        print(line)


def _import_engine(args: argparse.Namespace) -> None:
    if args.endpoint_host and len(args.reports) > 1:
        raise SystemExit("import-engine: --endpoint-host takes one report")
    try:
        imports: list[Imported] = []
        for source in args.reports:
            report, url_host = read(source)
            imports += [
                imported(report, server, args.endpoint_host or url_host)
                for server in report["servers"]
                if not args.server or server in args.server
            ]
        if missing := sorted(set(args.server or ()) - {i.server for i in imports}):
            raise LookupError(f"no report has a server {', '.join(missing)}")
        engines, endpoints = engines_toml(imports), endpoints_toml(imports)
        found = checked(imports)
    except (OSError, LookupError, ValueError) as e:
        raise SystemExit(f"import-engine: {e}") from None
    for i in imports:
        for f in i.findings:
            print(
                f"[import {f.level}] {i.name}: {f.code}: {f.message}", file=sys.stderr
            )
    for f in found:
        print(
            f"[inventory {f.level}] {f.subject}: {f.code}: {f.message}",
            file=sys.stderr,
        )
    written = f"# Written by `{' '.join(['chatddx import-engine', *args.reports])}`.\n"
    _ = args.engines.write_text(
        written
        + "# The models and engines its hosts serve; import again rather than edit.\n"
        + f"# Where they're served: {args.endpoints.name}.\n\n"
        + engines
    )
    _ = args.endpoints.write_text(
        written
        + f"# Where the engines in {args.engines.name} are served, and where their hosts\n"
        + "# keep what they pin; import again rather than edit. A World inventory\n"
        + "# includes it.\n\n"
        + endpoints
    )
    for i in imports:
        print(f"[import] {i.name}: engine {i.engine.digest} at {i.endpoint.url}")


def _repl(args: argparse.Namespace) -> None:
    world = _world("repl", args.world)
    with psycopg.connect(settings.database(), autocommit=True) as conn:
        _held("repl", world, conn)
        person = People(conn).find(args.login)
        if person is None:
            raise SystemExit(
                f"no person {args.login!r}: chatddx person provision {args.login} adds them"
            )
        bench = Bench(conn, person, world.inventory)
        if loop(Repl(bench, console()), args.history):
            raise SystemExit(1)


def _scripted_runs(args: argparse.Namespace) -> None:
    world = _world("scripted-runs", args.world)
    try:
        held = scripted_runs(world.path / RUNS)
    except ValueError as e:
        raise SystemExit(f"scripted-runs: {e}") from None
    if unknown := sorted(set(args.name) - {s.name for s in held}):
        raise SystemExit(
            f"scripted-runs: no scripted run {', '.join(unknown)} in {world.path}"
        )
    chosen = [s for s in held if not args.name or s.name in args.name]
    if not chosen:
        raise SystemExit(f"scripted-runs: {world.path} has no {RUNS}/*.toml")
    with psycopg.connect(settings.database(), autocommit=True) as conn:
        _held("scripted-runs", world, conn)
        person = People(conn).find(args.login)
        if person is None:
            raise SystemExit(
                f"no person {args.login!r}: chatddx person provision {args.login} adds them"
            )
        bench = Bench(conn, person, world.inventory)
        for scripted in chosen:
            try:
                before = None if args.again else ran_before(bench, scripted)
                started = before or run_scripted(bench, scripted)
            except OSError as e:
                raise SystemExit(
                    f"scripted-runs: {scripted.name}: {e}; scripted runs serve their "
                    + "own fakes, so chatddx fake-engines must not be running"
                ) from None
            except (LookupError, ValueError, Refused) as e:
                raise SystemExit(f"scripted-runs: {scripted.name}: {e}") from None
            said = "ran before as" if before else "ran as"
            print(
                f"[scripted run {scripted.name}] {_ran(bench, started)}, {said} run "
                + str(started.run)[:8]
            )


def _scripted_review(args: argparse.Namespace) -> None:
    world = _world("scripted-review", args.world)
    with psycopg.connect(settings.database(), autocommit=True) as conn:
        _held("scripted-review", world, conn)
        person = People(conn).find(args.login)
        if person is None:
            raise SystemExit(
                f"no person {args.login!r}: chatddx person provision {args.login} adds them"
            )
        bench = Bench(conn, person, world.inventory)
        try:
            case = bench.case_titled(args.case)[1]
            schema = bench.thread(args.schema, "expectation_schema")[0].digest
            made = review_scripted(
                bench,
                case,
                schema,
                gatherings=args.gatherings,
                versions=args.versions,
                seed=args.seed,
                days=args.days,
            )
        except OSError as e:
            raise SystemExit(
                f"scripted-review: {e}; scripted runs serve their own fakes, so "
                + "chatddx fake-engines must not be running"
            ) from None
        except (LookupError, ValueError, Refused) as e:
            raise SystemExit(f"scripted-review: {e}") from None
        print(
            f"[scripted review {args.case}] {made.gatherings} gatherings against "
            + f"{made.versions} versions of {args.login}'s expectation, "
            + f"{made.broken} broken and {made.unfinished} left unfinished"
        )
        for name, why in made.skipped.items():
            print(f"[scripted review {args.case}] left out {name}: {why}")


def _ran(bench: Bench, started: RunStarted) -> str:
    run = bench.store.run(started.run)
    trial = resolve(bench.store.get, started.trial, Trial)
    skeleton = resolve(bench.store.get, trial.skeleton, Skeleton)
    counted = Counter(outcome(skeleton, item)[0] for item in run.items)
    went = ", ".join(f"{n} {word}" for word, n in counted.items()) or "no items"
    if run.finished is None:
        went += ", unfinished"
    scored = len(bench.scores_of(started))
    return f"{bench.described(started)}: {went}, scored by {scored}"


def _serve(
    command: str,
    args: argparse.Namespace,
    made: Callable[[World, str], FastAPI],
) -> None:
    world = _world(command, args.world)
    bind: str = args.bind or settings.host()
    host, _, port = bind.rpartition(":")
    if not host or not port.isdigit():
        raise SystemExit(f"{command}: bind to HOST:PORT, not {bind!r}")
    with psycopg.connect(settings.database()) as conn:
        _held(command, world, conn)
    served = made(world, settings.database())
    uvicorn.run(
        served,
        host=host.strip("[]"),
        port=int(port),
        timeout_graceful_shutdown=int(settings.SERVE_GRACE.total_seconds()),
    )


def _api(args: argparse.Namespace) -> None:
    _serve("api", args, lambda w, c: app(w.inventory, c))


def _portal(args: argparse.Namespace) -> None:
    _unbuilt("portal", "or CHATDDX_PORTAL_ASSETS")
    _serve("portal", args, portal)


def _run(args: argparse.Namespace) -> None:
    if not args.watch:
        _unbuilt("run", "or --watch")
    watching = _watching() if args.watch else None
    try:
        _serve("run", args, lambda w, c: portal(w, c, worker=True))
    finally:
        if watching is not None:
            watching.terminate()
            _ = watching.wait()


def _unbuilt(command: str, otherwise: str) -> None:
    built = settings.portal_assets()
    if not Assets(built).built:
        print(
            f"{command}: nothing built in {built}: pnpm --dir frontend build, {otherwise}",
            file=sys.stderr,
        )


def _watching() -> subprocess.Popen[bytes]:
    frontend = str(settings.PROJECT_ROOT / "frontend")
    try:
        _ = subprocess.run(
            ["pnpm", "--dir", frontend, "install", "--frozen-lockfile"], check=True
        )
        return subprocess.Popen(["pnpm", "--dir", frontend, "run", "watch"])
    except FileNotFoundError:
        raise SystemExit("run: --watch builds with pnpm, which isn't on PATH") from None
    except subprocess.CalledProcessError as e:
        raise SystemExit(f"run: pnpm install ended with {e.returncode}") from None


def _worker(args: argparse.Namespace) -> None:
    world = _world("worker", args.world)
    with psycopg.connect(settings.database()) as conn:
        _held("worker", world, conn)
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    worker = Worker(settings.database(), world.inventory)
    stopping = threading.Event()

    # Policy: as the repl's Ctrl-C, the first press ends the runs after the items under
    # way, the second hangs those up at once and the third kills.
    def stop(asked: int, _frame: FrameType | None) -> None:
        if not stopping.is_set():
            print(
                f"worker {worker.id}: stopping after the items under way "
                + "(Ctrl-C again hangs them up)"
            )
            stopping.set()
            worker.wake()
            return
        print(
            f"worker {worker.id}: hanging up the items under way (Ctrl-C again kills)"
        )
        worker.cut()
        _ = signal.signal(asked, signal.SIG_DFL)

    for asked in (signal.SIGTERM, signal.SIGINT):
        _ = signal.signal(asked, stop)
    print(f"worker {worker.id}: serving the queue for {world.path}")
    worker.serve(stopping)
    print(f"worker {worker.id}: stopped, and what it held is queued again")


def _openapi(_: argparse.Namespace) -> None:
    document = app(Inventory(), "").openapi()
    print(json.dumps(document, indent=2, ensure_ascii=False))


def _locale(args: argparse.Namespace) -> None:
    if args.localing == "check":
        locale.check()
    elif args.localing == "pending":
        locale.pending()
    else:
        locale.write(args.tag)


def _fake_vllm(args: argparse.Namespace) -> None:
    try:
        script = None if args.script is None else Script.load(args.script)
    except (OSError, ValueError) as e:
        raise SystemExit(f"fake-vllm: {e}") from None
    run(args.model, args.argv, delay=args.delay, runaway=args.runaway, script=script)


def _fake_engines(args: argparse.Namespace) -> None:
    world = _world("fake-engines", args.world)
    with psycopg.connect(settings.database()) as conn:
        get = Store(conn).get
        try:
            served = [
                fake_at(world.inventory, get, name)
                for name in args.endpoint or world.inventory.endpoints
            ]
        except LookupError as e:
            raise SystemExit(f"fake-engines: {e}") from None
    run_all(served, delay=args.delay, runaway=args.runaway)


def _serving(parser: argparse.ArgumentParser, what: str) -> None:
    _ = parser.add_argument(
        "--world",
        type=Path,
        help=f"the World directory whose endpoints and vignettes {what} uses "
        + "(CHATDDX_WORLD)",
    )
    _ = parser.add_argument(
        "--bind", help=f"where to listen, as HOST:PORT ($HOST, else {settings.host()})"
    )


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="chatddx")
    commands = parser.add_subparsers(required=True)

    m = commands.add_parser("migrate", help="apply database migrations as DB_ADMIN")
    _ = m.add_argument(
        "--tier",
        type=int,
        choices=range(TOP_TIER + 1),
        default=TOP_TIER,
        help=f"apply migrations up to this tier (default {TOP_TIER})",
    )
    _ = m.add_argument(
        "--dry-run", action="store_true", help="list what would be applied"
    )
    m.set_defaults(run=_migrate)

    person = commands.add_parser("person", help="manage people as DB_USER")
    person_commands = person.add_subparsers(required=True)
    add = person_commands.add_parser("add", help="add a person")
    _ = add.add_argument("login")
    _ = add.add_argument("name")
    _ = add.add_argument(
        "--role", action="append", default=[], choices=[r.value for r in Role]
    )
    add.set_defaults(run=_person_add)
    password = person_commands.add_parser("password", help="set a person's password")
    _ = password.add_argument("login")
    password.set_defaults(run=_person_password)
    provisioning = person_commands.add_parser(
        "provision",
        help="share what the archive holds with a person and give them forks of what "
        + "they have none of, live or deleted",
    )
    _ = provisioning.add_argument("login", help="the person's, added when missing")
    _ = provisioning.add_argument(
        "--name", help="the name a person added is given (their login)"
    )
    provisioning.set_defaults(run=_person_provision)

    syncing = commands.add_parser(
        "sync-archive",
        help="write a data set into the archive, prune what it no longer holds, and "
        + "share what it holds with each person it is shared with",
    )
    _ = syncing.add_argument(
        "--world",
        type=Path,
        help="the World directory: its inventory.toml locates the vignettes and "
        + "endpoints, and its engines.toml and facts.toml are loaded with the data's "
        + "(CHATDDX_WORLD)",
    )
    _ = syncing.add_argument(
        "--source",
        help="the name of the World's directory source that holds the cases' "
        + "vignettes, needed when it has more than one",
    )
    _ = syncing.add_argument(
        "--data",
        type=Path,
        help="what to load: a directory with factors.toml and cases-<language>.toml "
        + f"(the World's {DATA}/)",
    )
    _ = syncing.add_argument(
        "--facts",
        type=Path,
        action="append",
        help="more model facts to load, beside the bundled ones and the World's",
    )
    syncing.set_defaults(run=_sync_archive)

    repair_parser = commands.add_parser(
        "repair-data",
        help="move the archive's families whose vignettes were renamed or changed at "
        + "their source",
    )
    _ = repair_parser.add_argument(
        "--world",
        type=Path,
        help="the World directory whose source holds the vignettes (CHATDDX_WORLD)",
    )
    _ = repair_parser.add_argument(
        "--source",
        help="the name of the World's directory source to survey, needed when it "
        + "has more than one",
    )
    _ = repair_parser.add_argument(
        "--dry-run", action="store_true", help="list the repairs without making them"
    )
    repair_parser.set_defaults(run=_repair_data)

    wipe_parser = commands.add_parser(
        "wipe-data",
        help="delete what a person owns and unshare what they collaborate on; "
        + "person provision shares it back, and leaves the forks it deleted deleted",
    )
    _ = wipe_parser.add_argument("user", help="the person's login")
    wipe_parser.set_defaults(run=_wipe_data)

    imp = commands.add_parser(
        "import-engine",
        help="write the models, engines, endpoints and hosts of the vLLM servers "
        + "o11n.vllm reports describe",
    )
    _ = imp.add_argument(
        "reports",
        nargs="+",
        help="each host's report: its URL, such as http://pelle.km:12008/, a file, or "
        + "- for stdin",
    )
    _ = imp.add_argument(
        "--server",
        action="append",
        help="a server to import, by name (default: every server of every report)",
    )
    _ = imp.add_argument(
        "--endpoint-host",
        help="the host in the endpoints' URLs, for one report (default: the report "
        + "URL's, or else the host's name)",
    )
    _ = imp.add_argument(
        "--engines",
        type=Path,
        required=True,
        help="the engines file to write the models and engines to, such as "
        + "worlds/kompismoln/engines.toml, which sync-archive loads with its World",
    )
    _ = imp.add_argument(
        "--endpoints",
        type=Path,
        required=True,
        help="the inventory file to write the endpoints and hosts to, such as "
        + "worlds/kompismoln/endpoints.toml, for a World inventory's include",
    )
    imp.set_defaults(run=_import_engine)

    shell = commands.add_parser(
        "repl",
        help="the chatddx shell: choose a configuration, see what would be sent, and "
        + "run it under its model's handle and score it",
    )
    _ = shell.add_argument("login", help="who you are in the shell")
    _ = shell.add_argument(
        "--world",
        type=Path,
        help="the World directory whose endpoints and vignettes the shell uses "
        + "(CHATDDX_WORLD)",
    )
    _ = shell.add_argument(
        "--history",
        type=Path,
        default=HISTORY,
        help=f"where the lines you type are kept ({HISTORY})",
    )
    shell.set_defaults(run=_repl)

    scripted = commands.add_parser(
        "scripted-runs",
        help="run the World's scripted runs (_runs/*.toml) for a person, each answered "
        + "by the fake vLLM from its script, and score them",
    )
    _ = scripted.add_argument("login", help="whose runs they are")
    _ = scripted.add_argument(
        "--world",
        type=Path,
        help="the World whose scripted runs to run (CHATDDX_WORLD)",
    )
    _ = scripted.add_argument(
        "--again",
        action="store_true",
        help="run a scripted run whose trial the person has a run of already",
    )
    _ = scripted.add_argument(
        "name", nargs="*", help="the scripted runs to run, by name (every one)"
    )
    scripted.set_defaults(run=_scripted_runs)

    reviewed = commands.add_parser(
        "scripted-review",
        help="write a review's worth of a case for a person: their expectation of it in "
        + "many versions and dozens of evaluations of it over the last weeks, each "
        + "answered by the fake vLLM as well as a quality drawn for its version has it",
    )
    _ = reviewed.add_argument("login", help="whose review it is")
    _ = reviewed.add_argument("case", help="the case, by its title")
    _ = reviewed.add_argument(
        "--world", type=Path, help="the World it is written in (CHATDDX_WORLD)"
    )
    _ = reviewed.add_argument(
        "--schema", default="targets", help="the expectation schema (targets)"
    )
    _ = reviewed.add_argument(
        "--gatherings", type=int, default=40, help="how many evaluations (40)"
    )
    _ = reviewed.add_argument(
        "--versions", type=int, default=12, help="how many expectations (12)"
    )
    _ = reviewed.add_argument(
        "--days", type=int, default=42, help="over how many days past (42)"
    )
    _ = reviewed.add_argument("--seed", type=int, default=1, help="the draw's seed (1)")
    reviewed.set_defaults(run=_scripted_review)

    api = commands.add_parser(
        "api",
        help="serve the chatddx API over HTTP, with its documentation at /api/docs",
    )
    _serving(api, "the API")
    api.set_defaults(run=_api)

    portal_parser = commands.add_parser(
        "portal",
        help="serve the portal over HTTP, and the API with it at /api/, with no "
        + "worker: chatddx worker runs beside it",
    )
    _serving(portal_parser, "the portal")
    portal_parser.set_defaults(run=_portal)

    run_parser = commands.add_parser(
        "run",
        help="serve the portal over HTTP, the API with it at /api/, and a worker in "
        + "the same process, for development",
    )
    _serving(run_parser, "the portal")
    _ = run_parser.add_argument(
        "--watch",
        action="store_true",
        help="build the frontend in frontend/ as it changes, while the portal is served",
    )
    run_parser.set_defaults(run=_run)

    worker = commands.add_parser(
        "worker",
        help="send and score the runs queued for the worker, until stopped; what it "
        + "holds then is queued again",
    )
    _ = worker.add_argument(
        "--world",
        type=Path,
        help="the World directory whose endpoints and vignettes the worker uses "
        + "(CHATDDX_WORLD)",
    )
    worker.set_defaults(run=_worker)

    openapi = commands.add_parser(
        "openapi",
        help="print the API's OpenAPI document, as frontend/openapi.json keeps it",
    )
    openapi.set_defaults(run=_openapi)

    localing = commands.add_parser(
        "locale",
        help="the catalogs in src/chatddx/locale/catalogs/, kept in step with the "
        + "messages the portal and its islands say, with English as the source",
    )
    locale_commands = localing.add_subparsers(required=True)
    locale_check = locale_commands.add_parser(
        "check",
        help="write nothing; fail while a catalog is behind the code",
    )
    locale_check.set_defaults(run=_locale, localing="check")
    locale_pending = locale_commands.add_parser(
        "pending",
        help="write nothing; flag the messages untranslated, and fail while one is",
    )
    locale_pending.set_defaults(run=_locale, localing="pending")
    locale_write = locale_commands.add_parser(
        "write",
        help="write the catalogs behind the code, and say what is left to translate",
    )
    _ = locale_write.add_argument(
        "tag",
        nargs="*",
        help="a locale to begin a catalog of as well, such as sv",
    )
    locale_write.set_defaults(run=_locale, localing="write")

    fake = commands.add_parser(
        "fake-vllm",
        help="serve a fake vLLM 0.24 for a model, set up by vllm serve's own flags",
    )
    _ = fake.add_argument(
        "--delay", type=float, default=0.03, help="seconds between streamed tokens"
    )
    _ = fake.add_argument(
        "--runaway",
        action="store_true",
        help="go on with newlines till max_tokens or the context runs out, after a "
        + "text answer or before a document's closing brace, as gpt-oss does at times",
    )
    _ = fake.add_argument(
        "--script",
        type=Path,
        help="answer each request with the next [[turn]] of this TOML file instead",
    )
    _ = fake.add_argument("model", help="the model, as vllm serve takes it")
    _ = fake.add_argument(
        "argv",
        nargs=argparse.REMAINDER,
        help="vllm serve's flags, such as --served-model-name, --reasoning-parser, "
        + "--enable-auto-tool-choice, --tool-call-parser, --host and --port",
    )
    fake.set_defaults(run=_fake_vllm)

    fakes = commands.add_parser(
        "fake-engines",
        help="serve the World's fake engines, each where its endpoint's start-up says, "
        + "and stand in for its remote engines on this machine, till Ctrl-C",
    )
    _ = fakes.add_argument(
        "--world",
        type=Path,
        help="the World directory whose endpoints to serve (CHATDDX_WORLD)",
    )
    _ = fakes.add_argument(
        "--delay", type=float, default=0.03, help="seconds between streamed tokens"
    )
    _ = fakes.add_argument(
        "--runaway", action="store_true", help="as fake-vllm's --runaway"
    )
    _ = fakes.add_argument(
        "endpoint",
        nargs="*",
        help="the endpoints to serve, each a fake's (every endpoint of the World)",
    )
    fakes.set_defaults(run=_fake_engines)

    args = parser.parse_args(argv)
    args.run(args)

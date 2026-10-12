import argparse
import getpass
import sys
from collections import Counter
from collections.abc import Sequence
from pathlib import Path

import psycopg
import uvicorn

from chatddx.api.app import app
from chatddx.bench import Bench, outcome
from chatddx.core import settings
from chatddx.core.rig import rig
from chatddx.curation import init, load_cases, plan_factors, repair, wipe
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
    endpoints_toml,
    factors_toml,
    imported,
    read,
)
from chatddx.inventory import World, check
from chatddx.ledger import RunStarted
from chatddx.repl.loop import HISTORY, loop
from chatddx.repl.shell import Repl, console
from chatddx.runner.gate import Refused
from chatddx.samples import RUNS, fake_at, ran_before, run as run_sample, samples
from chatddx.store.migrate import TOP_TIER, migrate, pending
from chatddx.store.people import People
from chatddx.store.store import Store


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
    if getpass.getpass("again: ") != password:
        raise SystemExit("passwords don't match")
    with psycopg.connect(settings.database()) as conn:
        people = People(conn)
        person = people.find(args.login)
        if person is None:
            raise SystemExit(f"no person with login {args.login!r}")
        people.set_password(person.id, password)
    print(f"password set for {args.login}")


# A World's data set, which the World itself doesn't read: init-data's by default.
DATA = "_data"


def _world(command: str, path: Path | None) -> World:
    path = path or settings.world()
    if path is None:
        raise SystemExit(f"{command}: give a World with --world DIR or CHATDDX_WORLD")
    try:
        return World.load(path)
    except LookupError as e:
        raise SystemExit(f"{command}: {e}") from None


def _init_data(args: argparse.Namespace) -> None:
    world = _world("init-data", args.world)
    data: Path = args.data or world.path / DATA
    if not data.is_dir():
        raise SystemExit(
            f"init-data: {world.path} has no {DATA}/: give a data set with --data DIR"
        )
    more = [*world.factors, *(args.factors or ())]
    try:
        facts = Facts.load(BUNDLED, *world.facts, *(args.facts or ()))
        plan = plan_factors(data, facts, rig(), more=more)
        cases = load_cases(data)
    except ValueError as e:
        raise SystemExit(f"init-data: {e}") from None
    try:
        source = world.inventory.listing(args.source)
    except LookupError as e:
        raise SystemExit(f"init-data: {world.path}: {e}") from None
    if not set(cases) & set(source.ids()):
        raise SystemExit(
            f"init-data: none of the data's {len(cases)} cases is in source "
            + f"{source.name!r} of {world.path}"
        )
    lines: list[str] = []
    with psycopg.connect(settings.database()) as conn:
        people = People(conn)
        user = people.find(args.user)
        if user is None:
            user = people.add(args.user, args.user)
            lines.append(f"[person] {args.user}: added")
        lines += init(conn, plan, cases, source, user, giftbag=args.giftbag)
    findings = check(world.inventory, plan.registry.get)
    lines += [f"[world {f.level}] {f.subject}: {f.code}: {f.message}" for f in findings]
    n, m = len(findings), len(world.inventory.endpoints)
    lines.append(
        f"[world] {n} finding{'' if n == 1 else 's'} in {m} endpoint"
        + f"{'' if m == 1 else 's'} of {world.path}"
    )
    for line in lines:
        print(line)


def _repair_data(args: argparse.Namespace) -> None:
    world = _world("repair-data", args.world)
    try:
        source = world.inventory.listing(args.source)
    except LookupError as e:
        raise SystemExit(f"repair-data: {world.path}: {e}") from None
    with psycopg.connect(settings.database()) as conn:
        archive = People(conn).find(ARCHIVE)
        if archive is None:
            raise SystemExit(f"repair-data: no {ARCHIVE!r} yet; init-data loads it")
        lines = repair(conn, source, archive, dry=args.dry_run)
    for line in lines:
        print(line)


def _wipe_data(args: argparse.Namespace) -> None:
    if args.user == ARCHIVE:
        raise SystemExit(
            f"wipe-data: {ARCHIVE!r} holds what init-data loads; it isn't wiped"
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
        factors, endpoints = factors_toml(imports), endpoints_toml(imports)
    except (OSError, LookupError, ValueError) as e:
        raise SystemExit(f"import-engine: {e}") from None
    for i in imports:
        for f in i.findings:
            print(
                f"[import {f.level}] {i.name}: {f.code}: {f.message}", file=sys.stderr
            )
    written = f"# Written by `{' '.join(['chatddx import-engine', *args.reports])}`.\n"
    _ = args.factors.write_text(
        written
        + "# The models and engines its hosts serve; import again rather than edit.\n"
        + f"# Where they're served: {args.endpoints.name}.\n\n"
        + factors
    )
    _ = args.endpoints.write_text(
        written
        + f"# Where the engines in {args.factors.name} are served, and where their hosts\n"
        + "# keep what they pin; import again rather than edit. A World inventory\n"
        + "# includes it.\n\n"
        + endpoints
    )
    for i in imports:
        print(f"[import] {i.name}: engine {i.engine.digest} at {i.endpoint.url}")


def _repl(args: argparse.Namespace) -> None:
    world = _world("repl", args.world)
    facts = Facts.load(BUNDLED, *world.facts, *(args.facts or ()))
    with psycopg.connect(settings.database(), autocommit=True) as conn:
        person = People(conn).find(args.login)
        if person is None:
            raise SystemExit(
                f"no person {args.login!r}: chatddx init-data {args.login} adds them"
            )
        bench = Bench(conn, person, world.inventory, facts)
        if loop(Repl(bench, console()), args.history):
            raise SystemExit(1)


def _samples(args: argparse.Namespace) -> None:
    world = _world("samples", args.world)
    try:
        held = samples(world.path / RUNS)
        facts = Facts.load(BUNDLED, *world.facts)
    except ValueError as e:
        raise SystemExit(f"samples: {e}") from None
    if unknown := sorted(set(args.sample) - {s.name for s in held}):
        raise SystemExit(f"samples: no sample {', '.join(unknown)} in {world.path}")
    chosen = [s for s in held if not args.sample or s.name in args.sample]
    if not chosen:
        raise SystemExit(f"samples: {world.path} has no {RUNS}/*.toml")
    with psycopg.connect(settings.database(), autocommit=True) as conn:
        person = People(conn).find(args.login)
        if person is None:
            raise SystemExit(
                f"no person {args.login!r}: chatddx init-data {args.login} adds them"
            )
        bench = Bench(conn, person, world.inventory, facts)
        for sample in chosen:
            try:
                before = None if args.again else ran_before(bench, sample)
                started = before or run_sample(bench, sample)
            except OSError as e:
                raise SystemExit(
                    f"samples: {sample.name}: {e}; the samples serve their own fakes, "
                    + "so chatddx fake-engines must not be running"
                ) from None
            except (LookupError, ValueError, Refused) as e:
                raise SystemExit(f"samples: {sample.name}: {e}") from None
            said = "ran before as" if before else "ran as"
            print(
                f"[sample {sample.name}] {_ran(bench, started)}, {said} run "
                + str(started.run)[:8]
            )


def _ran(bench: Bench, started: RunStarted) -> str:
    run = bench.store.run(started.run)
    trial = resolve(bench.get, started.trial, Trial)
    skeleton = resolve(bench.get, trial.skeleton, Skeleton)
    counted = Counter(outcome(skeleton, item)[0] for item in run.items)
    went = ", ".join(f"{n} {word}" for word, n in counted.items()) or "no items"
    if run.finished is None:
        went += ", unfinished"
    scored = len(bench.scores_of(started.run))
    return f"{bench.described(started)}: {went}, scored by {scored}"


def _api(args: argparse.Namespace) -> None:
    world = _world("api", args.world)
    facts = Facts.load(BUNDLED, *world.facts, *(args.facts or ()))
    bind: str = args.bind or settings.host()
    host, _, port = bind.rpartition(":")
    if not host or not port.isdigit():
        raise SystemExit(f"api: bind to HOST:PORT, not {bind!r}")
    served = app(world.inventory, facts, settings.database())
    uvicorn.run(served, host=host.strip("[]"), port=int(port))


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

    init = commands.add_parser(
        "init-data",
        help="load the sample data into the archive and share it with a person",
    )
    _ = init.add_argument(
        "user", help="the login to share the archive with, added when missing"
    )
    _ = init.add_argument(
        "--world",
        type=Path,
        help="the World directory: its inventory.toml locates the vignettes and "
        + "endpoints, and its factors.toml and facts.toml are loaded with the data's "
        + "(CHATDDX_WORLD)",
    )
    _ = init.add_argument(
        "--source",
        help="the name of the World's source that holds the cases' vignettes, needed "
        + "when more than one source lists its vignettes",
    )
    _ = init.add_argument(
        "--giftbag", action="store_true", help="also give the user forks of their own"
    )
    _ = init.add_argument(
        "--data",
        type=Path,
        help="what to load: a directory with factors.toml and cases-<language>.toml "
        + f"(the World's {DATA}/)",
    )
    _ = init.add_argument(
        "--factors",
        type=Path,
        action="append",
        help="more factors to load with the data's and the World's",
    )
    _ = init.add_argument(
        "--facts",
        type=Path,
        action="append",
        help="more model facts to write per-model chunks from, beside the bundled "
        + "ones and the World's",
    )
    init.set_defaults(run=_init_data)

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
        help="the name of the World's source to survey, needed when more than one "
        + "source lists its vignettes",
    )
    _ = repair_parser.add_argument(
        "--dry-run", action="store_true", help="list the repairs without making them"
    )
    repair_parser.set_defaults(run=_repair_data)

    wipe_parser = commands.add_parser(
        "wipe-data",
        help="delete what a person owns and unshare what they collaborate on; "
        + "init-data shares and gives it back",
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
        "--factors",
        type=Path,
        required=True,
        help="the factors file to write the models and engines to, such as "
        + "worlds/kompismoln/factors.toml, which init-data loads with its World",
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
        help="the chatddx shell: choose a configuration and an endpoint, see what would "
        + "be sent, and run and score it",
    )
    _ = shell.add_argument("login", help="who you are in the shell")
    _ = shell.add_argument(
        "--world",
        type=Path,
        help="the World directory whose endpoints, vignettes and facts the shell uses "
        + "(CHATDDX_WORLD)",
    )
    _ = shell.add_argument(
        "--facts",
        type=Path,
        action="append",
        help="more model facts, beside the bundled ones and the World's, as init-data "
        + "was given",
    )
    _ = shell.add_argument(
        "--history",
        type=Path,
        default=HISTORY,
        help=f"where the lines you type are kept ({HISTORY})",
    )
    shell.set_defaults(run=_repl)

    sampled = commands.add_parser(
        "samples",
        help="run the World's sample runs (_runs/*.toml) for a person, each answered by "
        + "the fake vLLM from its script, and score them",
    )
    _ = sampled.add_argument("login", help="whose runs they are")
    _ = sampled.add_argument(
        "--world", type=Path, help="the World whose samples to run (CHATDDX_WORLD)"
    )
    _ = sampled.add_argument(
        "--again",
        action="store_true",
        help="run a sample whose trial the person has a run of already",
    )
    _ = sampled.add_argument(
        "sample", nargs="*", help="the samples to run, by name (every one)"
    )
    sampled.set_defaults(run=_samples)

    api = commands.add_parser(
        "api",
        help="serve the chatddx API over HTTP, with its documentation at /api/docs",
    )
    _ = api.add_argument(
        "--world",
        type=Path,
        help="the World directory whose endpoints, vignettes and facts the API uses "
        + "(CHATDDX_WORLD)",
    )
    _ = api.add_argument(
        "--facts",
        type=Path,
        action="append",
        help="more model facts, beside the bundled ones and the World's, as init-data "
        + "was given",
    )
    _ = api.add_argument(
        "--bind", help=f"where to listen, as HOST:PORT ($HOST, else {settings.host()})"
    )
    api.set_defaults(run=_api)

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

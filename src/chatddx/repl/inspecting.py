import copy
import json
import re
from dataclasses import replace

from pydantic import JsonValue
from rich.table import Table
from rich.text import Text

from chatddx.bench import KINDS, PARTS, Carried, Family, Graded, TriedVariation
from chatddx.catalog import About
from chatddx.catalog.titles import describe, short
from chatddx.factors.base import Component, resolve
from chatddx.factors.cases import Appendix, Case
from chatddx.factors.engine import LocalEngine
from chatddx.factors.request import Reasoning, Sampling, Skeleton
from chatddx.factors.scoring import Expectation, Scoring
from chatddx.facts import (
    INTENTS,
    Effort,
    Landing,
    ModelFacts,
    Refusal,
    Refused,
    Writes,
)
from chatddx.inventory import url_of
from chatddx.ledger import RunStarted
from chatddx.store import fetch_vignette

from .render import (
    LABEL,
    LATER,
    REFUSED,
    clipped,
    plural,
    show_summary,
    some,
    writes,
)
from .shell import Repl

_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")

SCORED = frozenset({"scorer", "judge", "expectation", "expectation_schema"})


def show(repl: Repl, kind: str | None = None, *names: str) -> None:
    name = " ".join(names) or None

    if kind is None:
        _show_cell(repl)
    elif kind == "tag":
        if names:
            _show_cell(repl, names)
        else:
            repl.error("usage: show tag TAG...")
    elif kind == "case":
        _show_case(repl, name)
    elif kind == "endpoint":
        _show_endpoint(repl, name)
    elif kind in KINDS:
        _show_thread(repl, kind, name)
    else:
        repl.error(f"no kind '{kind}': tag, case, endpoint, {', '.join(KINDS)}")


def _show_cell(repl: Repl, tags: tuple[str, ...] = ()) -> None:
    bench, cell = repl.bench, repl.cell
    variation = cell.variation

    if not (variation or cell.endpoint):
        repl.error("the cell is empty: use CONFIGURATION, on ENDPOINT")
        return

    families = bench.families(tags)

    if tags and not families:
        repl.error(f"no case tagged {' or '.join(tags)} for {bench.person.login}")
        return

    repl.say_cell()
    table = Table(box=None, header_style="bold")

    for column in ("part", "chunk", "is"):
        table.add_column(column)

    endpoint = repl.where()
    if endpoint and cell.engine:
        served = bench.served(cell.engine)
        url = url_of(bench.inventory, bench.get, endpoint)
        where = f"{bench.title(cell.engine)}, served as {served} at {url}"
        table.add_row("endpoint", endpoint, where)

    if variation:
        landed = bench.landed(variation)
        for part in PARTS:
            held = variation.held(part)
            component = None if held is None else bench.get(held)
            said = "" if component is None else describe(component, bench.title)
            table.add_row(
                part, _chunk(repl, variation, part), _landed(component, said, landed)
            )

    repl.console.print(table)

    if not variation:
        return

    skeleton = bench.skeleton(variation)
    request = bench.request(variation, cell.engine, repl.seed)

    messages = request.pop("messages")
    assert isinstance(messages, list)

    for message in messages:
        assert isinstance(message, dict)
        repl.console.print(str(message["role"]), style="bold")
        repl.console.print(Text(clipped(str(message["content"]))))

    repl.console.print("body", style="bold")
    repl.console.print(
        Text(clipped(json.dumps(_abridged(request), indent=2, ensure_ascii=False)))
    )

    if skeleton.greedy:
        repl.console.print("greedy: the seed isn't sent", style=LABEL)

    carried = None
    if families and skeleton.purpose != "judge":
        known = {f.case: f.about.language for f in families}
        carried = bench.languages(variation, list(known), known)
        repl.console.print("languages", style="bold")
        for each in carried:
            repl.console.print(_carried(each))

    if cell.engine is not None:
        findings = bench.findings(variation, cell.engine, repl.seed, families, carried)
        repl.console.print("lints", style="bold")
        repl.say_findings(findings)
        if not findings:
            repl.console.print("no findings", style=LABEL)

    _show_scorers(repl, variation, families, tags)


def _carried(carried: Carried) -> Text:
    cases = plural(len(carried.cases), "case")
    if carried.refused is not None:
        said = f"{carried.language}: {cases}, left out: {carried.refused}"
        return Text(said, style=LATER)
    how = "translated" if carried.translated else "as written"
    return Text(f"{carried.language or 'unknown'}: {cases}, {how}")


def _landed(component: Component | None, said: str, landed: dict[str, Landing]) -> Text:
    text = Text(said)
    match component:
        case Reasoning(level=asked) if "reasoning" in landed:
            at = landed["reasoning"]
            if at.level != asked:
                _ = text.append(f" → {at.level}", style="bold")
            for reason in at.nearest:
                _ = text.append(f", its nearest: {reason}", style=LATER)
        case Sampling() if "sampling" in landed:
            _ = text.append(f", for reasoning {landed['sampling'].level}")
        case _:
            pass
    return text


def _chunk(repl: Repl, variation: TriedVariation, part: str) -> Text:
    bench = repl.bench
    own = None if variation.recipe is None else getattr(variation.recipe, part)

    if part not in variation.parts:
        return Text(bench.title(own))

    text = Text(variation.parts[part][1], style="bold")
    _ = text.append(f" (set; {variation.name} has {bench.title(own)})", style=LABEL)
    return text


def _show_scorers(
    repl: Repl,
    variation: TriedVariation,
    families: list[Family],
    tags: tuple[str, ...],
) -> None:
    where = f" tagged {' or '.join(tags)}" if tags else ""
    table = Table(box=None, header_style="bold")

    for column in ("scorer", "view", f"of {plural(len(families), 'case')}{where}"):
        table.add_column(column)

    for reach in repl.bench.reach(variation, families):
        if not reach.offered:
            said = Text("the output offers no such view", style=REFUSED)
        else:
            said = Text(f"{reach.have} have it")
            if reach.missing:
                _ = said.append(
                    f"; missing: {some(f.name for f in reach.missing)}", style=LATER
                )
            if reach.choosing:
                _ = said.append(
                    f"; to choose from: {some(f.name for f in reach.choosing)}",
                    style=REFUSED,
                )
        table.add_row(reach.scorer, reach.label, said)

    repl.console.print(table)


def _show_thread(repl: Repl, word: str, name: str | None) -> None:
    bench, cell = repl.bench, repl.cell

    if name is not None:
        edit, found = bench.thread(word, name)
        _show_component(repl, word, found, edit.digest, bench.about(edit.thread))
        return

    variation = cell.variation

    if word == "configuration" and variation and variation.parts:
        skeleton = bench.skeleton(variation)
        header = Text(f"configuration {cell.label}", style="bold")
        _ = header.append(", unsaved")
        _ = header.append(f"  {short(skeleton.digest)}", style=LABEL)
        repl.console.print(header)
        repl.console.print(_fields(repl, skeleton))
        return

    digest = _in_cell(repl, word)

    if digest is None:
        return

    held = bench.holder(word, digest)
    about = None if held is None else held[1]
    _show_component(repl, word, bench.title(digest), digest, about)


def _in_cell(repl: Repl, word: str) -> str | None:
    bench, cell = repl.bench, repl.cell
    variation = cell.variation
    digest: str | None = None

    if word == "configuration" and variation:
        digest = variation.configuration.digest
    elif word in ("engine", "model") and cell.engine:
        digest = cell.engine
        engine = bench.get(cell.engine)
        if word == "model":
            if not isinstance(engine, LocalEngine):
                repl.error(f"the cell's engine is a {engine.kind_name}, with no model")
                return None
            digest = engine.model
    elif word in PARTS and variation:
        digest = variation.held(word)
        if digest is None:
            repl.error(f"the cell has no {word}")
            return None
    elif word in ("engine", "model"):
        repl.error(f"the cell has no configuration or endpoint: show {word} NAME")
    elif word in PARTS or word == "configuration":
        repl.error(f"the cell has no configuration: show {word} NAME")
    else:
        repl.error(f"no {word} in the cell: show {word} NAME")

    return digest


def _show_component(
    repl: Repl, word: str, name: str, digest: str, about: About | None
) -> None:
    bench = repl.bench
    header = Text(f"{word} {name}", style="bold")

    if about is not None and (owner := bench.owner(about)):
        _ = header.append(f", {owner}'s")

    _ = header.append(f"  {short(digest)}", style=LABEL)
    repl.console.print(header)
    table = _fields(repl, bench.get(digest))

    if about is not None:
        _about(table, about)

    repl.console.print(table)
    _runs(repl, word, digest)


def _fields(repl: Repl, component: Component) -> Table:
    table = Table(box=None, show_header=False)
    table.add_column(style=LABEL)
    table.add_column()

    doc = component.canonical_doc()

    if isinstance(component, Skeleton):
        doc["body"] = _abridged(component.body)

    for field, value in doc.items():
        if field not in ("kind", "v"):
            _add_rows(repl, table, field, value)

    return table


def _abridged(body: dict[str, JsonValue]) -> dict[str, JsonValue]:
    shown = copy.deepcopy(body)
    held = shown.get("response_format")
    if isinstance(held, dict) and isinstance(held.get("json_schema"), dict):
        schema = held["json_schema"]
        assert isinstance(schema, dict)
        schema["schema"] = "‹the output's schema›"
    tools = shown.get("tools")
    for tool in tools if isinstance(tools, list) else []:
        function = tool.get("function") if isinstance(tool, dict) else None
        if isinstance(function, dict) and "parameters" in function:
            function["parameters"] = "‹the tool's parameters›"
    return shown


def _about(table: Table, about: About) -> None:
    if about.description:
        table.add_row("description", about.description)
    if about.tags:
        table.add_row("tags", " ".join(sorted(about.tags)))
    if about.language:
        table.add_row("language", about.language)


def _runs(repl: Repl, word: str, digest: str) -> None:
    if word == "judge":
        _judged(repl, digest)
        return

    bench = repl.bench
    scored = word in SCORED
    runs = bench.scored_by(digest) if scored else bench.reaching(digest)

    if not runs:
        said = "it scored" if word == "scorer" else f"with this {word}"
        repl.console.print(f"no runs of yours {said}", style=LABEL)
        return

    said = "it scored" if word == "scorer" else "with it"
    repl.console.print(f"{plural(len(runs), 'run')} of yours {said}", style=LABEL)
    graded = [
        g for run in runs for g in bench.scores_of(run.run) if g.score is not None
    ]

    if scored:
        graded = [g for g in graded if _scored_with(repl, g, digest)]

    if word == "expectation":
        case = resolve(bench.get, digest, Expectation).case
        graded = [_of_case(g, case) for g in graded]
    elif word == "case":
        graded = [_of_case(g, digest) for g in graded]

    show_summary(repl.console, graded)


def _judged(repl: Repl, judge: str) -> None:
    bench = repl.bench
    judged: list[Graded] = []
    runs = 0

    for run in bench.scored_by(judge):
        graded = [_by_judge(g, judge) for g in bench.scores_of(run.run) if g.score]
        graded = [g for g in graded if g.score and g.score.items]
        runs += bool(graded)
        judged += graded

    if not runs:
        repl.console.print("no runs of yours it judged", style=LABEL)
        return

    calls = sum(
        c.judge == judge
        for g in judged
        if g.score
        for i in g.score.items
        for c in i.judge_calls
    )
    repl.console.print(
        f"{plural(runs, 'run')} of yours it judged, in {plural(calls, 'call')}",
        style=LABEL,
    )
    show_summary(repl.console, judged)


def _by_judge(graded: Graded, judge: str) -> Graded:
    assert graded.score is not None
    items = tuple(
        i for i in graded.score.items if any(c.judge == judge for c in i.judge_calls)
    )
    return replace(graded, score=graded.score.model_copy(update={"items": items}))


def _scored_with(repl: Repl, graded: Graded, digest: str) -> bool:
    assert graded.score is not None
    scoring = resolve(repl.bench.get, graded.score.started.scoring, Scoring)
    return digest in (
        scoring.scorer,
        *scoring.expectations,
        graded.scorer.expectation_schema,
    )


def _of_case(graded: Graded, case: str) -> Graded:
    assert graded.score is not None
    items = tuple(i for i in graded.score.items if i.key.case == case)
    return replace(graded, score=graded.score.model_copy(update={"items": items}))


def _add_rows(
    repl: Repl, table: Table, field: str, value: JsonValue, depth: int = 1
) -> None:
    if isinstance(value, dict) and value and depth > 0:
        plain = all(not isinstance(v, (dict, list)) for v in value.values())
        if plain or depth > 1:
            for key, item in value.items():
                _add_rows(repl, table, f"{field}.{key}", item, depth - 1)
            return

    table.add_row(field, _text(repl, value))


def _text(repl: Repl, value: JsonValue) -> Text:
    if value is None or (isinstance(value, (str, list, dict)) and not value):
        return Text("—", style=LABEL)

    match value:
        case str() if _DIGEST.match(value):
            return Text(repl.bench.title(value))
        case [*items] if all(isinstance(i, str) and _DIGEST.match(i) for i in items):
            return Text(", ".join(repl.bench.title(str(i)) for i in items))
        case str():
            return Text(clipped(value))
        case list() if all(isinstance(i, (str, int, float)) for i in value):
            return Text(" ".join(str(i) for i in value))
        case dict() | list():
            titled = _titled(repl, value)
            return Text(clipped(json.dumps(titled, indent=2, ensure_ascii=False)))
        case _:
            return Text(json.dumps(value))


def _show_case(repl: Repl, name: str | None) -> None:
    bench = repl.bench

    if name is None:
        repl.error("no case in the cell: show case NAME")
        return

    family, digest = bench.case_titled(name)
    case = resolve(bench.get, digest, Case)
    shown = family.name if digest == family.case else bench.title(digest)
    header = Text(f"case {shown}", style="bold")

    if owner := bench.owner(family.about):
        _ = header.append(f", {owner}'s")

    _ = header.append(f"  {short(digest)}", style=LABEL)
    repl.console.print(header)

    table = Table(box=None, show_header=False)
    table.add_column(style=LABEL)
    table.add_column()
    vignette = case.vignette
    table.add_row("source", f"{vignette.source}/{vignette.id}")

    try:
        raw = fetch_vignette(bench.conn, bench.inventory, vignette)
        table.add_row("vignette", clipped(raw.decode(errors="replace")))
    except LookupError as e:
        table.add_row("vignette", Text(str(e), style=REFUSED))

    for appendix in case.appendices:
        text = resolve(bench.get, appendix, Appendix).text
        table.add_row(f"appendix {bench.title(appendix)}", clipped(text))

    if digest == family.case:
        _sending(repl, table, family)

    _about(table, family.about)
    schemas = bench.expectation_schemas(digest)

    if not schemas:
        table.add_row("expectation", Text("none for you", style=LATER))

    for schema in schemas:
        label = "expectation"

        if len(schemas) > 1:
            label += f" ({bench.title(schema)})"

        try:
            expectation = bench.expectation(digest, schema)
        except LookupError as e:
            table.add_row(label, Text(str(e), style=REFUSED))
            continue

        if expectation is None:
            said = Text("none of yours", style=LATER)
            owners = {bench.login(a.owner) for _, a in bench.shared(digest, schema)}
            if owners:
                _ = said.append(
                    f"; shared by {some(sorted(owners))}: take", style=LABEL
                )
            table.add_row(label, said)
        else:
            _add_rows(repl, table, label, expectation.data, depth=3)

    repl.console.print(table)
    _runs(repl, "case", digest)


def _sending(repl: Repl, table: Table, family: Family) -> None:
    bench = repl.bench

    if appendices := bench.appendices_of(family.id):
        table.add_row("appendices", ", ".join(appendices))

    cases = Text()

    for case in bench.cases(family.id):
        if case == family.case:
            continue
        _ = cases.append(("\n" if cases else "") + bench.title(case))
        if bench.expectation_schemas(case):
            _ = cases.append("  its own expectation", style=LABEL)

    if cases:
        table.add_row("cases", cases)


def _titled(repl: Repl, value: JsonValue) -> JsonValue:
    match value:
        case str() if _DIGEST.match(value):
            return repl.bench.title(value)
        case dict():
            return {k: _titled(repl, v) for k, v in value.items()}
        case list():
            return [_titled(repl, v) for v in value]
        case _:
            return value


def _show_endpoint(repl: Repl, name: str | None) -> None:
    bench = repl.bench
    name = name or repl.where()

    if name is None:
        repl.error("the cell has no endpoint: show endpoint NAME")
        return

    spec = bench.inventory.endpoint(name)
    repl.console.print(Text(f"endpoint {name}", style="bold"))
    table = Table(box=None, show_header=False)
    table.add_column(style=LABEL)
    table.add_column()

    try:
        engine = bench.endpoint(name)
        table.add_row("engine", bench.title(engine))
        table.add_row("model", bench.model(engine) or "—")
        table.add_row("url", url_of(bench.inventory, bench.get, name))
    except LookupError as e:
        table.add_row("engine", Text(str(e), style=REFUSED))

    table.add_row("host", spec.host or "—")
    table.add_row("max jobs", str(spec.max_jobs))
    table.add_row("credential", spec.credential or "—")
    table.add_row("cleared for", " ".join(sorted(bench.inventory.cleared_for(name))))
    repl.console.print(table)

    ran = bench.runs()
    runs = [r for r in ran if r.endpoint and r.endpoint.name == name]
    if not runs:
        repl.console.print("no runs of yours at this endpoint", style=LABEL)
    else:
        repl.console.print(f"{plural(len(runs), 'run')} of yours at it", style=LABEL)

    judged = [n for n in (_judge_calls(repl, r, name) for r in ran) if n]
    if judged:
        repl.console.print(
            f"judged {plural(len(judged), 'run')} of yours at it, in "
            + plural(sum(judged), "call"),
            style=LABEL,
        )


def _judge_calls(repl: Repl, run: RunStarted, endpoint: str) -> int:
    store = repl.bench.store
    calls = 0
    for started in store.scores_of(run.run):
        at = {j.judge for j in started.endpoints if j.endpoint.name == endpoint}
        if at:
            items = store.score(started.score).items
            calls += sum(c.judge in at for i in items for c in i.judge_calls)
    return calls


def reasoning(repl: Repl) -> None:
    bench, cell = repl.bench, repl.cell
    models = bench.facts.models
    serving: dict[str, list[str]] = {}
    where = repl.where()

    for endpoint in sorted(bench.inventory.endpoints):
        try:
            model = bench.model(bench.endpoint(endpoint))
        except LookupError:
            continue
        if model is not None:
            marked = f"▸ {endpoint}" if endpoint == where else endpoint
            serving.setdefault(model, []).append(marked)

    current = None if cell.engine is None else bench.model(cell.engine)
    asked = _asked(repl, cell.variation)
    caption = (
        "▸ the level the cell's configuration asks for, as its model's facts say"
        if asked is not None and current in models
        else "the cell has no configuration asking for a level on a model the facts know"
    )
    table = Table(header_style="bold", show_lines=True, caption=caption)
    table.add_column("reasoning")

    for model in models:
        table.add_column("\n".join([model, *serving.get(model, [])]), overflow="fold")

    for effort in ("default", *INTENTS):
        cells = [_level(facts, effort) for facts in models.values()]
        table.add_row(f"▸ {effort}" if effort == asked else effort, *cells)

    table.add_row("budget", *(_budget(facts) for facts in models.values()))
    repl.console.print(table)


def _asked(repl: Repl, variation: TriedVariation | None) -> Effort | None:
    if variation is None or variation.recipe is None:
        return None
    held = variation.held("reasoning")
    if held is None:
        return "default"
    return resolve(repl.bench.get, held, Reasoning).level


def _level(facts: ModelFacts, effort: Effort) -> Text:
    try:
        landed = facts.reasoning.resolve(effort)
    except Refused as e:
        return Text(f"refused: {e}", style=REFUSED)

    text = Text(f"→ {landed.level}\n" if landed.level != effort else "")
    for reason in landed.nearest:
        _ = text.append(f"its nearest: {reason}\n", style=LATER)
    _ = text.append(_writes(landed.writes) or "nothing")

    try:
        sampling = Sampling().over(facts.recommended(landed.level))
        _ = text.append(f"\n{writes(sampling.body()) or 'no sampling'}", style=LABEL)
    except Refused as e:
        _ = text.append(f"\n{e}", style=LABEL)

    return text


def _budget(facts: ModelFacts) -> Text:
    match facts.reasoning.budget:
        case None:
            return Text("nothing is known", style=LABEL)
        case Refusal(refused=reason):
            return Text(f"refused: {reason}", style=REFUSED)
        case key:
            return Text(f"{key}=N")


def _writes(written: Writes) -> str:
    sent: dict[str, JsonValue] = {}
    if written.effort is not None:
        sent["reasoning_effort"] = written.effort
    if written.chat_template_kwargs:
        sent["chat_template_kwargs"] = written.chat_template_kwargs
    return writes(sent)

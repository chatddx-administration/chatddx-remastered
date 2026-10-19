import json
import re
import tomllib
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from pydantic import JsonValue, ValidationError

from chatddx.factors.base import Code, Component, StructuralError, language_tag
from chatddx.factors.bundle import Registry
from chatddx.factors.engine import (
    LocalEngine,
    LocalModel,
    RemoteEngine,
    RemoteModel,
    model_of,
)
from chatddx.factors.facts import ModelFacts
from chatddx.factors.request import (
    CHUNK_PARTS,
    AppendixLayout,
    FewShot,
    Instructions,
    Output,
    Passthrough,
    Prompt,
    Reasoning,
    Recipe,
    Sampling,
    Tool,
    Toolset,
    Translations,
    compile_request,
    compiled,
    landings,
    own_texts,
    translated,
)
from chatddx.factors.scoring import ExpectationSchema, Judge, Scorer
from chatddx.factors.trial import CanarySet
from chatddx.facts import Facts
from chatddx.inventory import World
from chatddx.rig import Versioned, entry
from chatddx.scorers.shipped import SCORERS, problems
from chatddx.tools.shipped import TOOLS

TABLES: dict[str, type[Component]] = {
    "local_model": LocalModel,
    "remote_model": RemoteModel,
    "local_engine": LocalEngine,
    "remote_engine": RemoteEngine,
    "instructions": Instructions,
    "few_shot": FewShot,
    "prompt": Prompt,
    "output": Output,
    "sampling": Sampling,
    "reasoning": Reasoning,
    "passthrough": Passthrough,
    "tool": Tool,
    "toolset": Toolset,
    # After the records whose texts its entries are grouped by.
    "translations": Translations,
    "expectation_schema": ExpectationSchema,
    "scorer": Scorer,
    "canary_set": CanarySet,
}
ENGINE_TABLES = ("local_model", "remote_model", "local_engine", "remote_engine")
# Planned after recipes and judges, as a view may name a judge.
LATE_TABLES = ("scorer",)
PLANNED_TABLES = (*TABLES, "recipe", "judge")
DATA_TABLES = tuple(t for t in PLANNED_TABLES if t not in ENGINE_TABLES)
# The tables whose records pin shipped code, with what the running code ships.
SHIPPED: dict[str, Mapping[str, Versioned]] = {"tool": TOOLS, "scorer": SCORERS}
# References outside recipes, by table and field: each names records of another table.
REFERENCES: dict[str, dict[str, str]] = {
    "toolset": {"tools": "tool"},
    "scorer": {"expectation_schema": "expectation_schema"},
    "local_engine": {"model": "local_model"},
    "remote_engine": {"model": "remote_model"},
}


@dataclass(frozen=True)
class Planned:
    table: str
    name: str
    kind: str
    digest: str
    tags: tuple[str, ...] = ()
    description: str | None = None
    fork_of: str | None = None
    compilation: str | None = None
    labels: tuple[str | None, ...] = ()
    language: str | None = None


@dataclass
class Plan:
    registry: Registry
    facts: Facts
    records: list[Planned] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    untranslated: list[str] = field(default_factory=list)
    compilations: list[str] = field(default_factory=list)

    def named(self, table: str, name: str) -> Planned:
        for r in self.records:
            if (r.table, r.name) == (table, name):
                return r
        raise LookupError(f"no {table} named {name!r} in the plan")


TEXT_TABLES = frozenset(
    {"instructions", "few_shot", "prompt", "output", "toolset", "translations"}
)
_TEXTS = re.compile(r"^texts-(.+)\.toml$")


def _short(text: str) -> str:
    return repr(text if len(text) <= 60 else text[:57] + "…")


def _with_files(node: JsonValue, root: Path) -> JsonValue:
    match node:
        case dict():
            out: dict[str, JsonValue] = {}
            for k, v in node.items():
                if k == "json_schema_path":
                    assert isinstance(v, str)
                    with (root / v).open() as f:
                        out["json_schema"] = json.load(f)
                else:
                    out[k] = _with_files(v, root)
            return out
        case list():
            return [_with_files(v, root) for v in node]
        case _:
            return node


def _component(table: str, body: dict[str, JsonValue]) -> Component:
    if "from_facts" in body:
        raise ValueError(
            f"{table}: from_facts is gone; the facts are applied when a recipe is "
            + "compiled, so ask for a reasoning `level` or a `recommended` sampling"
        )
    return TABLES[table].model_validate(body)


def _labels(table: str, body: dict[str, JsonValue]) -> tuple[str | None, ...]:
    views = body.get("views")
    if table != "scorer" or not isinstance(views, list):
        return ()
    labels: list[str | None] = []
    for view in views:
        label = view.pop("label", None) if isinstance(view, dict) else None
        if label is not None and not isinstance(label, str):
            raise ValueError(f"a view's label must be a string, not {label!r}")
        labels.append(label)
    return tuple(labels)


def _check_runs(component: Component) -> None:
    match component:
        case Tool():
            _ = entry(TOOLS, component.entry_point, component.version)
        case Scorer():
            if found := problems(component):
                raise LookupError("; ".join(found))
        case _:
            pass


def _tags(value: JsonValue) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(isinstance(t, str) for t in value):
        raise ValueError(f"tags must be a list of strings, not {value!r}")
    return tuple(str(t) for t in value)


def _read(path: Path) -> dict[str, Any]:
    with path.open("rb") as f:
        return tomllib.load(f)


def _records(
    path: Path, data: dict[str, Any], tables: Collection[str]
) -> dict[str, dict[str, JsonValue]]:
    if stray := set(data) - set(tables):
        raise ValueError(f"{path}: unknown tables {sorted(stray)}")
    found: dict[str, dict[str, JsonValue]] = {}
    for table, records in cast(dict[str, dict[str, JsonValue]], data).items():
        found[table] = {}
        for name, raw in records.items():
            if isinstance(raw, dict) and "language" in raw:
                said = (
                    "a judge's request is its recipe's, as written"
                    if table == "judge"
                    else "a text's language is the texts file it's written in"
                )
                raise ValueError(f"{path}: {table}.{name}: {said}")
            found[table][name] = _with_files(raw, path.parent)
    return found


def _texts(data: Path) -> dict[str, dict[str, dict[str, JsonValue]]]:
    texts: dict[str, dict[str, dict[str, JsonValue]]] = {}
    for path in sorted(data.glob("texts*.toml")):
        named = _TEXTS.match(path.name)
        if named is None:
            raise ValueError(f"{path}: texts are kept in texts-<language>.toml files")
        try:
            language = language_tag(named[1])
        except ValueError as e:
            raise ValueError(f"{path}: {e}") from None
        texts[language] = _records(path, _read(path), TEXT_TABLES)
    return texts


def plan_factors(
    data: Path, facts: Facts, compiler: Code, world: World | None = None
) -> Plan:
    factors = data / "factors.toml"
    written = _read(factors)
    if held := sorted(set(written) & set(ENGINE_TABLES)):
        raise ValueError(
            f"{factors}: {', '.join(held)} tables are the World's, in its engines.toml"
        )
    found = _records(factors, written, DATA_TABLES)
    for path in () if world is None else world.engines:
        written = _read(path)
        if stray := sorted(set(written) - set(ENGINE_TABLES)):
            raise ValueError(
                f"{path}: an engines file holds only {', '.join(ENGINE_TABLES)} "
                + f"tables, not {', '.join(stray)}"
            )
        for table, records in _records(path, written, ENGINE_TABLES).items():
            known = found.setdefault(table, {})
            if twice := sorted(set(known) & set(records)):
                raise ValueError(f"{path}: {table} {twice} are named before it too")
            known.update(records)
    bodies: dict[str, dict[str, tuple[str | None, JsonValue]]] = {
        table: {name: (None, body) for name, body in records.items()}
        for table, records in found.items()
    }
    if "translations" in bodies:
        raise ValueError(
            f"{factors}: translations are written in the texts-<language>.toml of the "
            + "language they translate into"
        )
    translating: dict[str, dict[str, JsonValue]] = {}
    for language, tables in _texts(data).items():
        for table, records in tables.items():
            for name, body in records.items():
                if table == "translations":
                    translating.setdefault(name, {})[language] = body
                    continue
                held = bodies.setdefault(table, {})
                if name in held:
                    was = held[name][0]
                    where = "factors.toml" if was is None else f"texts-{was}.toml"
                    raise ValueError(
                        f"{table}.{name} is in {where} and texts-{language}.toml: a "
                        + "text is written in one language, and translated into others"
                    )
                held[name] = (language, body)
    plan = Plan(Registry(), facts)
    planned: dict[tuple[str, str], Planned | None] = {}

    def add(table: str, name: str, record: Planned | None) -> None:
        planned[(table, name)] = record
        if record is not None:
            plan.records.append(record)

    def base(table: str, name: str, fork_of: object) -> str | None:
        if fork_of is None:
            return None
        assert isinstance(fork_of, str)
        if (table, fork_of) not in planned:
            raise ValueError(f"{table}.{fork_of} must come before its forks")
        if (origin := planned[(table, fork_of)]) is None:
            plan.skipped.append(
                f"{table} {name}: no fork of {table}.{fork_of}, which isn't planned"
            )
            return None
        return origin.name

    def texts_of(record: str, language: str) -> set[str]:
        table, _, name = record.partition(".")
        if table == "recipe" and name in found.get("recipe", {}):
            raw = found["recipe"][name]
            assert isinstance(raw, dict)
            try:
                layout = AppendixLayout.model_validate(raw.get("appendix_layout", {}))
            except ValidationError as e:
                raise ValueError(f"recipe.{name}: {e}") from None
            return set(own_texts(layout, plan.registry.get))
        if table not in TEXT_TABLES - {"translations"} and table != "recipe":
            raise ValueError(f"{record!r} names no record of texts")
        if (r := planned.get((table, name))) is None:
            raise ValueError(f"{record!r}: no {table} named {name!r}")
        if r.language == language:
            raise ValueError(f"{record} is written in {language}")
        get = plan.registry.get
        return set(own_texts(get(r.digest), get))

    def grouped(name: str, language: str, of: object) -> dict[str, JsonValue]:
        where = f"texts-{language}.toml: translations.{name}"
        match of:
            case dict():
                groups = cast(dict[str, object], of)
            case _:
                raise ValueError(f"{where}: `of` is a table of records and their texts")
        entries: dict[str, JsonValue] = {}
        for record, pairs in groups.items():
            try:
                texts = texts_of(record, language)
            except ValueError as e:
                raise ValueError(f"{where}: {e}") from None
            listed = cast(list[object], pairs) if isinstance(pairs, list) else [pairs]
            for pair in listed:
                match pair:
                    case {
                        "text": str() as text,
                        "translation": str() as translation,
                    } if len(cast(dict[str, object], pair)) == 2:
                        pass
                    case _:
                        raise ValueError(
                            f"{where}: {record}: each entry is a text and its translation"
                        )
                if text not in texts:
                    raise ValueError(f"{where}: {record} holds no text {_short(text)}")
                if entries.setdefault(text, translation) != translation:
                    raise ValueError(f"{where}: {_short(text)} is translated two ways")
        return entries

    def plan_table(table: str) -> None:
        kind = TABLES[table]
        for name, (language, raw) in bodies.get(table, {}).items():
            assert isinstance(raw, dict)
            where = "factors.toml" if language is None else f"texts-{language}.toml"
            body = dict(raw)
            tags = _tags(body.pop("tags", []))
            # A tool's description is a field, what the model reads; it's the entry
            # too.
            if "description" in kind.model_fields:
                description = body.get("description")
            else:
                description = body.pop("description", None)
            fork_of = body.pop("fork_of", None)
            for field_name, target in REFERENCES.get(table, {}).items():
                match body.get(field_name):
                    case str() as one:
                        body[field_name] = plan.named(target, one).digest
                    case list() as names:
                        body[field_name] = [
                            plan.named(target, str(n)).digest for n in names
                        ]
                    case _:
                        pass
            if table in SHIPPED and "version" not in body:
                shipped = SHIPPED[table].get(str(body.get("entry_point")))
                if shipped is not None:
                    body["version"] = shipped.version
            if table == "scorer" and (
                unplanned := _judged(name, body, planned, found.get("judge", {}))
            ):
                plan.skipped.append(f"scorer {name}: judge {unplanned} isn't planned")
                add(table, name, None)
                continue
            labels = _labels(table, body)
            try:
                component = _component(table, body)
            except ValidationError as e:
                raise ValueError(f"{where}: {table}.{name}: {e}") from None
            try:
                _check_runs(component)
            except LookupError as e:
                raise ValueError(f"{table}.{name}: {e}") from None
            holds = bool(own_texts(component, plan.registry.get))
            if language is None and holds and table in TEXT_TABLES:
                raise ValueError(
                    f"{table}.{name} holds text, so it's written in a "
                    + "texts-<language>.toml"
                )
            if language is not None and not holds:
                raise ValueError(
                    f"{where}: {table}.{name} holds no text, so it belongs in "
                    + "factors.toml"
                )
            add(
                table,
                name,
                Planned(
                    table=table,
                    name=name,
                    kind=component.kind_name,
                    digest=plan.registry.add(component),
                    tags=tags,
                    description=None if description is None else str(description),
                    fork_of=base(table, name, fork_of),
                    labels=labels,
                    language=language,
                ),
            )

    def plan_translations() -> None:
        for name, written in translating.items():
            tags: set[str] = set()
            said: dict[str, object] = {}
            into: dict[str, JsonValue] = {}
            for language, raw in written.items():
                assert isinstance(raw, dict)
                where = f"texts-{language}.toml: translations.{name}"
                body = dict(raw)
                tags.update(_tags(body.pop("tags", [])))
                for key in ("description", "fork_of"):
                    if (value := body.pop(key, None)) is None:
                        continue
                    if said.setdefault(key, value) != value:
                        raise ValueError(
                            f"{where}: its {key} isn't the one another texts file gives"
                        )
                match body:
                    case {"of": of, **rest} if not rest:
                        into[language] = grouped(name, language, of)
                    case {"entries": entries, **rest} if not rest:
                        into[language] = entries
                    case _:
                        raise ValueError(
                            f"{where}: give its entries or its `of`, and nothing else"
                        )
            try:
                component = Translations.model_validate({"into": into})
            except ValidationError as e:
                raise ValueError(f"translations.{name}: {e}") from None
            description = said.get("description")
            add(
                "translations",
                name,
                Planned(
                    table="translations",
                    name=name,
                    kind=component.kind_name,
                    digest=plan.registry.add(component),
                    tags=tuple(sorted(tags)),
                    description=None if description is None else str(description),
                    fork_of=base("translations", name, said.get("fork_of")),
                ),
            )

    for table in ENGINE_TABLES:
        plan_table(table)
    inventory = None if world is None else world.inventory
    engines = {
        r.digest: r
        for r in plan.records
        if r.table in ("local_engine", "remote_engine")
    }
    models = {
        r.digest: r for r in plan.records if r.table in ("local_model", "remote_model")
    }

    def under(handle: str) -> tuple[Planned, Planned] | str:
        assert inventory is not None
        model = next((r for r in models.values() if r.name == handle), None)
        if model is None:
            return f"the World has no model under handle {handle}"

        def serves(engine: str) -> str | None:
            if engine not in engines:
                return None
            return model_of(engine, plan.registry.get).digest

        try:
            endpoint = inventory.serving(model.digest, serves, f"model {handle}")
        except LookupError as e:
            return str(e)
        return model, engines[inventory.endpoint(endpoint).engine]

    served: dict[str, list[str]] = {}
    for r in engines.values():
        model = model_of(r.digest, plan.registry.get).name
        served.setdefault(model, []).append(f"{r.kind} {r.name}")
    facts_of: dict[str, ModelFacts] = {}
    for model in sorted(served):
        if (about := facts.models.get(model)) is None:
            plan.skipped.append(
                f"facts about {model}: none are known, so {', '.join(served[model])} "
                + "can't compile a reasoning level or a recommended sampling"
            )
            continue
        facts_of[model] = about
        add("facts", model, Planned("facts", model, "facts", plan.registry.add(about)))

    def compiled_for(
        what: str, body: dict[str, JsonValue], model: Planned
    ) -> tuple[str, str] | None:
        try:
            recipe = Recipe.model_validate({**body, "model": model.digest})
        except ValidationError as e:
            raise ValueError(f"{what}: {e}") from None
        get = plan.registry.get
        about = facts_of.get(model_of(model.digest, get).name)
        try:
            _ = landings(recipe, get, about)
        except ValueError as e:
            plan.skipped.append(f"{what}: {e}, for {model.kind} {model.name}")
            return None
        skeleton, compilation = compiled(recipe, get, compiler, about)
        if what.startswith("recipe "):
            for language in translated(recipe, get):
                try:
                    _ = compile_request(recipe, get, about, language)
                except StructuralError as e:
                    plan.untranslated.append(f"{what}: {e}")
        return plan.registry.add(skeleton), plan.registry.add(compilation)

    for table in TABLES:
        if table == "translations":
            plan_translations()
        elif table not in (*ENGINE_TABLES, *LATE_TABLES):
            plan_table(table)

    configured = None if inventory is None else inventory.configurations
    target = None if configured is None else under(configured)
    made: dict[str, dict[str, JsonValue]] = {}
    for name, raw in found.get("recipe", {}).items():
        assert isinstance(raw, dict)
        body = dict(raw)
        tags = _tags(body.pop("tags", []))
        description = body.pop("description", None)
        fork_of = body.pop("fork_of", None)
        if "model" in body:
            raise ValueError(
                f"recipe.{name}: a recipe's model is the World's: its inventory names "
                + "the handle configurations are made for"
            )
        for part in CHUNK_PARTS:
            if part not in body:
                continue
            if (chunk := planned.get((part, str(body[part])))) is None:
                raise ValueError(f"recipe.{name}: no {part} named {body[part]!r}")
            body[part] = chunk.digest
        made[name] = body
        if not isinstance(target, tuple):
            plan.skipped.append(
                f"recipe {name}: "
                + (target or "the World names no handle configurations are made for")
            )
            add("recipe", name, None)
            continue
        held = compiled_for(f"recipe {name}", body, target[0])
        if held is None:
            add("recipe", name, None)
            continue
        skeleton, compilation = held
        add(
            "recipe",
            name,
            Planned(
                table="recipe",
                name=name,
                kind="skeleton",
                digest=skeleton,
                tags=tags,
                description=None if description is None else str(description),
                fork_of=base("recipe", name, fork_of),
                compilation=compilation,
            ),
        )

    bound = {} if inventory is None else inventory.judges
    judges = found.get("judge", {})
    for name, raw in judges.items():
        assert isinstance(raw, dict)
        body = dict(raw)
        if "engine" in body:
            raise ValueError(
                f"judge.{name}: a judge's engine is the World's, which binds the judge "
                + "to a handle in its inventory's [judge] table"
            )
        tags = _tags(body.pop("tags", []))
        description = body.pop("description", None)
        recipe = str(body.pop("recipe", ""))
        if (asked := made.get(recipe)) is None:
            raise ValueError(f"judge.{name}: no recipe named {recipe!r}")
        if inventory is None or (handle := bound.get(name)) is None:
            plan.skipped.append(f"judge {name}: the World binds it to no handle")
            add("judge", name, None)
            continue
        if isinstance(resolved := under(handle), str):
            plan.skipped.append(f"judge {name}: {resolved}")
            add("judge", name, None)
            continue
        of, at = resolved
        held = compiled_for(f"judge {name}", asked, of)
        if held is None:
            add("judge", name, None)
            continue
        skeleton, compilation = held
        plan.compilations.append(compilation)
        try:
            judge = Judge.model_validate(
                {**body, "skeleton": skeleton, "engine": at.digest}
            )
        except ValidationError as e:
            raise ValueError(f"judge.{name}: {e}") from None
        if refused := judge.cross_check(plan.registry.get):
            raise ValueError(f"judge.{name}: {'; '.join(refused)}")
        add(
            "judge",
            name,
            Planned(
                table="judge",
                name=name,
                kind="judge",
                digest=plan.registry.add(judge),
                tags=tags,
                description=None if description is None else str(description),
            ),
        )
    for name in sorted(set(bound) - set(judges)):
        plan.skipped.append(
            f"judge {name}: the World binds it to {bound[name]}, but the data has none"
        )

    for table in LATE_TABLES:
        plan_table(table)
    return plan


def _judged(
    scorer: str,
    body: dict[str, JsonValue],
    planned: Mapping[tuple[str, str], Planned | None],
    judges: Collection[str],
) -> str | None:
    views = body.get("views")
    if not isinstance(views, list):
        return None
    copied = [dict(v) if isinstance(v, dict) else v for v in views]
    for view in copied:
        if not isinstance(view, dict) or (named := view.get("judge")) is None:
            continue
        if not isinstance(named, str) or named not in judges:
            raise ValueError(f"scorer.{scorer}: no judge named {named!r}")
        if (judge := planned.get(("judge", named))) is None:
            return named
        view["judge"] = judge.digest
    body["views"] = cast(list[JsonValue], copied)
    return None


@dataclass(frozen=True)
class Ordered:
    appendices: tuple[str, ...]
    targets: JsonValue = None


@dataclass(frozen=True)
class DataCase:
    tags: tuple[str, ...]
    language: str
    targets: JsonValue
    appendices: Mapping[str, str] = field(default_factory=dict[str, str])
    ordered: tuple[Ordered, ...] = ()


_CASES = re.compile(r"^cases-(.+)\.toml$")


def _appendices(where: str, value: object) -> dict[str, str]:
    match value:
        case dict():
            held = cast(dict[str, object], value)
        case _:
            raise ValueError(f"{where}: appendices are a table of texts by name")
    if bad := sorted(n for n, t in held.items() if not (isinstance(t, str) and t)):
        raise ValueError(f"{where}: appendices {bad} aren't texts")
    return cast(dict[str, str], held)


def _ordered(where: str, value: object, appendices: Mapping[str, str]) -> Ordered:
    match value:
        case dict():
            held = cast(dict[str, object], value)
        case _:
            raise ValueError(f"{where}: a case with appendices is a table")
    if stray := set(held) - {"appendices", "targets"}:
        raise ValueError(f"{where}: unknown keys {sorted(stray)}")
    names = held.get("appendices")
    if not isinstance(names, list) or not names:
        raise ValueError(f"{where}: name its appendices, in order")
    listed = [str(n) for n in cast(list[object], names)]
    if unknown := sorted(set(listed) - set(appendices)):
        raise ValueError(f"{where}: no appendices {unknown}")
    if len(set(listed)) != len(listed):
        raise ValueError(f"{where}: an appendix is named twice")
    return Ordered(tuple(listed), cast(JsonValue, held.get("targets")))


def load_cases(data: Path) -> dict[str, DataCase]:
    cases: dict[str, DataCase] = {}
    where: dict[str, Path] = {}
    for path in sorted(data.glob("cases*.toml")):
        named = _CASES.match(path.name)
        if named is None:
            raise ValueError(f"{path}: cases are kept in cases-<language>.toml files")
        try:
            language = language_tag(named[1])
        except ValueError as e:
            raise ValueError(f"{path}: {e}") from None
        with path.open("rb") as f:
            tables = tomllib.load(f)
        if set(tables) - {"case"}:
            raise ValueError(f"{path}: a cases file has only 'case' tables")
        for id, case in tables.get("case", {}).items():
            if id in where:
                raise ValueError(f"{path}: case.{id} is in {where[id].name} too")
            if stray := set(case) - {"tags", "targets", "appendices", "with"}:
                raise ValueError(f"{path}: case.{id}: unknown keys {sorted(stray)}")
            where[id] = path
            appendices = _appendices(
                f"{path}: case.{id}.appendices", case.get("appendices", {})
            )
            ordered = tuple(
                _ordered(f"{path}: case.{id}.with[{n}]", entry, appendices)
                for n, entry in enumerate(case.get("with", []))
            )
            if len({o.appendices for o in ordered}) != len(ordered):
                raise ValueError(f"{path}: case.{id}: a case with appendices is twice")
            cases[id] = DataCase(
                tags=tuple(case.get("tags", ())),
                language=language,
                targets=case.get("targets"),
                appendices=appendices,
                ordered=ordered,
            )
    return cases

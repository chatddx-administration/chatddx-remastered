import json
import re
import tomllib
from collections.abc import Collection, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from pydantic import JsonValue, ValidationError

from chatddx.catalog import language_tag, variant_name
from chatddx.factors.base import Code, Component
from chatddx.factors.bundle import Registry
from chatddx.factors.engine import LocalEngine, ModelArtifact, RemoteEngine
from chatddx.factors.facts import ModelFacts, model_name
from chatddx.factors.request import (
    CHUNK_PARTS,
    TRANSLATED,
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
    compiled,
    landings,
    own_texts,
)
from chatddx.factors.scoring import ExpectationSchema, Judge, Scorer
from chatddx.factors.trial import CanarySet
from chatddx.facts import Facts
from chatddx.inventory import World
from chatddx.rig import Versioned, entry
from chatddx.scorers.shipped import SCORERS, problems
from chatddx.tools.shipped import TOOLS

TABLES: dict[str, type[Component]] = {
    "model": ModelArtifact,
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
ENGINE_TABLES = ("model", "local_engine", "remote_engine")
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
    "local_engine": {"model": "model"},
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
    compilations: list[str] = field(default_factory=list)

    def named(self, table: str, name: str) -> Planned:
        for r in self.records:
            if (r.table, r.name) == (table, name):
                return r
        raise LookupError(f"no {table} named {name!r} in the plan")


# A record's language: None for one that serves every language.
Key = str | None
Variants = dict[Key, Planned]
ALL: Key = None
TEXT_TABLES = frozenset(
    {"instructions", "few_shot", "prompt", "output", "toolset", "translations"}
)
_TEXTS = re.compile(r"^texts-(.+)\.toml$")


def _short(text: str) -> str:
    return repr(text if len(text) <= 60 else text[:57] + "…")


def _named(name: str, key: Key) -> str:
    return variant_name(name, key)


def _pick[T](variants: Mapping[Key, T], key: Key) -> T | None:
    return variants.get(key, variants.get(ALL))


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
                raise ValueError(
                    f"{path}: {table}.{name}: a text's language is the texts file it's "
                    + "written in"
                )
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
    # Each table's records by name, then by language: None for factors.toml's.
    bodies: dict[str, dict[str, dict[str | None, JsonValue]]] = {
        table: {name: {None: body} for name, body in records.items()}
        for table, records in found.items()
    }
    for language, tables in _texts(data).items():
        for table, records in tables.items():
            for name, body in records.items():
                if None in (
                    written := bodies.setdefault(table, {}).setdefault(name, {})
                ):
                    raise ValueError(
                        f"{table}.{name} is in factors.toml and texts-{language}.toml"
                    )
                written[language] = body
    plan = Plan(Registry(), facts)
    planned: dict[tuple[str, str], Variants] = {}

    def add(table: str, name: str, variants: Variants) -> None:
        planned[(table, name)] = variants
        plan.records.extend(variants.values())

    # Crosses into the origin's one language as _recipe does for a part.
    def base(table: str, name: str, fork_of: object, key: Key) -> str | None:
        if fork_of is None:
            return None
        assert isinstance(fork_of, str)
        variants = planned.get((table, fork_of))
        if variants is None:
            raise ValueError(f"{table}.{fork_of} must come before its forks")
        found = _pick(variants, key)
        written = sorted(k for k in variants if k is not None)
        if found is None and key is not None and key not in written:
            if len(written) > 1:
                raise ValueError(
                    f"{table}.{name}: {table}.{fork_of} has no variant in {key} "
                    + f"to fork, and is written in {', '.join(written)}"
                )
            if written:
                found = variants[written[0]]
        if found is None:
            plan.skipped.append(
                f"{table} {_named(name, key)}: no fork of {table}.{fork_of}, which "
                + "isn't planned"
            )
        return None if found is None else found.name

    # The texts a translations record in `language` may translate, of the record named.
    def texts_of(record: str, language: str | None) -> set[str]:
        table, _, name = record.partition(".")
        if table == "recipe" and name in bodies.get("recipe", {}):
            raw = bodies["recipe"][name][None]
            assert isinstance(raw, dict)
            try:
                layout = AppendixLayout.model_validate(raw.get("appendix_layout", {}))
            except ValidationError as e:
                raise ValueError(f"recipe.{name}: {e}") from None
            return {
                t for t in (layout.before, layout.between, layout.after) if t.strip()
            }
        if table not in ("output", "toolset", "recipe"):
            raise ValueError(f"{record!r} names no output, toolset or recipe")
        if (variants := planned.get((table, name))) is None:
            raise ValueError(f"{record!r}: no {table} named {name!r}")
        get = plan.registry.get
        return {
            text
            for written, r in variants.items()
            if written != language
            for text in own_texts(get(r.digest), get)
        }

    def grouped(name: str, language: str | None, of: object) -> dict[str, JsonValue]:
        where = f"translations.{name}"
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
        for name, written in bodies.get(table, {}).items():
            variants: Variants = {}
            for language, raw in written.items():
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
                if table == "translations" and "of" in body:
                    if "entries" in body:
                        raise ValueError(
                            f"{where}: translations.{name}: give its entries or its "
                            + "`of`, not both"
                        )
                    body["entries"] = grouped(name, language, body.pop("of"))
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
                    plan.skipped.append(
                        f"scorer {name}: judge {unplanned} isn't planned"
                    )
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
                variants[language] = Planned(
                    table=table,
                    name=_named(name, language),
                    kind=component.kind_name,
                    digest=plan.registry.add(component),
                    tags=tags,
                    description=None if description is None else str(description),
                    fork_of=base(table, name, fork_of, language),
                    labels=labels,
                    language=language,
                )
            add(table, name, variants)

    for table in ENGINE_TABLES:
        plan_table(table)
    engines = {
        r.digest: r
        for r in plan.records
        if r.table in ("local_engine", "remote_engine")
    }
    served: dict[str, list[str]] = {}
    for r in engines.values():
        if (model := model_name(r.digest, plan.registry.get)) is not None:
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
        add(
            "facts",
            model,
            {ALL: Planned("facts", model, "facts", plan.registry.add(about))},
        )

    def compiled_for(
        what: str, body: dict[str, JsonValue], engine: Planned
    ) -> tuple[str, str] | None:
        try:
            recipe = Recipe.model_validate({**body, "engine": engine.digest})
        except ValidationError as e:
            raise ValueError(f"{what}: {e}") from None
        get = plan.registry.get
        about = facts_of.get(model_name(engine.digest, get) or "")
        try:
            _ = landings(recipe, get, about)
        except ValueError as e:
            plan.skipped.append(f"{what}: {e}, on {engine.kind} {engine.name}")
            return None
        skeleton, compilation = compiled(recipe, get, compiler, about)
        return plan.registry.add(skeleton), plan.registry.add(compilation)

    for table in TABLES:
        if table not in (*ENGINE_TABLES, *LATE_TABLES):
            plan_table(table)

    inventory = None if world is None else world.inventory
    configured = None if inventory is None else inventory.configurations
    target = (
        None
        if inventory is None or configured is None
        else engines.get(inventory.endpoint(configured).engine)
    )
    made: dict[str, dict[Key, dict[str, JsonValue]]] = {}
    for name, raw in found.get("recipe", {}).items():
        assert isinstance(raw, dict)
        body = dict(raw)
        tags = _tags(body.pop("tags", []))
        description = body.pop("description", None)
        fork_of = body.pop("fork_of", None)
        if "engine" in body:
            raise ValueError(
                f"recipe.{name}: a recipe's engine is the World's: its inventory names "
                + "the endpoint configurations are made for"
            )
        parts = {p: planned[(p, str(body.pop(p)))] for p in CHUNK_PARTS if p in body}
        languages = sorted({k for v in parts.values() for k in v if k is not None})
        variants: Variants = {}
        made[name] = {}
        for language in languages or [ALL]:
            chosen = _recipe(name, language, parts)
            if isinstance(chosen, str):
                plan.skipped.append(f"recipe {_named(name, language)}: {chosen}")
                continue
            made[name][language] = {**body, **chosen}
            if target is None:
                plan.skipped.append(
                    f"recipe {_named(name, language)}: the World names no endpoint "
                    + "configurations are made for"
                )
                continue
            held = compiled_for(
                f"recipe {_named(name, language)}", made[name][language], target
            )
            if held is None:
                continue
            skeleton, compilation = held
            variants[language] = Planned(
                table="recipe",
                name=_named(name, language),
                kind="skeleton",
                digest=skeleton,
                tags=tags,
                description=None if description is None else str(description),
                fork_of=base("recipe", name, fork_of, language),
                compilation=compilation,
            )
        add("recipe", name, variants)

    bound = {} if inventory is None else inventory.judges
    judges = found.get("judge", {})
    for name, raw in judges.items():
        assert isinstance(raw, dict)
        body = dict(raw)
        if "engine" in body:
            raise ValueError(
                f"judge.{name}: a judge's engine is the World's, which binds the judge "
                + "to an endpoint in its inventory's [judge] table"
            )
        tags = _tags(body.pop("tags", []))
        description = body.pop("description", None)
        recipe = str(body.pop("recipe", ""))
        language = body.pop("language", None)
        if (recipes := made.get(recipe)) is None:
            raise ValueError(f"judge.{name}: no recipe named {recipe!r}")
        if inventory is None or (endpoint := bound.get(name)) is None:
            plan.skipped.append(f"judge {name}: the World binds it to no endpoint")
            add("judge", name, {})
            continue
        if (at := engines.get(inventory.endpoint(endpoint).engine)) is None:
            plan.skipped.append(
                f"judge {name}: endpoint {endpoint} serves no engine the World has"
            )
            add("judge", name, {})
            continue
        written = sorted(k for k in recipes if k is not None)
        if language is None and len(written) > 1:
            raise ValueError(
                f"judge.{name}: recipe.{recipe} is written in {', '.join(written)}, "
                + "so the judge names its language"
            )
        key = str(language) if language else (written or [ALL])[0]
        if (asked := _pick(recipes, key)) is None:
            plan.skipped.append(f"judge {name}: recipe.{recipe} has none in {key}")
            add("judge", name, {})
            continue
        held = compiled_for(f"judge {name}", asked, at)
        if held is None:
            add("judge", name, {})
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
        judged = Planned(
            table="judge",
            name=name,
            kind="judge",
            digest=plan.registry.add(judge),
            tags=tags,
            description=None if description is None else str(description),
        )
        add("judge", name, {ALL: judged})
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
    planned: Mapping[tuple[str, str], Variants],
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
        if (judge := planned[("judge", named)].get(ALL)) is None:
            return named
        view["judge"] = judge.digest
    body["views"] = cast(list[JsonValue], copied)
    return None


def _recipe(name: str, key: Key, parts: dict[str, Variants]) -> dict[str, str] | str:
    chosen: dict[str, str] = {}
    missing: list[str] = []
    translated: list[str] = []
    for part, variants in parts.items():
        if part == "translations":
            continue
        found = _pick(variants, key)
        if found is None and part in TRANSLATED and key is not None:
            written = sorted(k for k in variants if k is not None)
            if len(written) == 1:
                found = variants[written[0]]
                translated.append(f"{part} in {written[0]}")
        if found is not None:
            chosen[part] = found.digest
        else:
            missing.append(part)
    if missing:
        return f"it has no {', '.join(missing)} in {key}"
    if translated:
        named = parts.get("translations")
        found = None if named is None else _pick(named, key)
        if found is None:
            return (
                f"its {', '.join(translated)} needs translations in {key}, and "
                + f"recipe.{name} names none there"
            )
        chosen["translations"] = found.digest
    return chosen


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

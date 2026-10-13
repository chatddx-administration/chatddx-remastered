import json
import re
import tomllib
from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from pydantic import JsonValue, ValidationError

from chatddx.catalog import language_tag, variant_name
from chatddx.core.rig import Versioned, entry
from chatddx.factors.base import Code, Component
from chatddx.factors.bundle import Registry
from chatddx.factors.engine import LocalEngine, ModelArtifact, RemoteEngine
from chatddx.factors.request import (
    RECIPE_PARTS,
    TRANSLATED,
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
    own_texts,
)
from chatddx.factors.scoring import ExpectationSchema, Judge, Scorer
from chatddx.factors.trial import CanarySet
from chatddx.facts import INTENTS, Effort, Facts, Refused, model_name
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
    "translations": Translations,
    "tool": Tool,
    "toolset": Toolset,
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

    def named(self, table: str, name: str) -> Planned:
        for r in self.records:
            if (r.table, r.name) == (table, name):
                return r
        raise LookupError(f"no {table} named {name!r} in the plan")


Key = tuple[str | None, str | None]
Variants = dict[Key, Planned]
ALL: Key = (None, None)
TEXT_TABLES = frozenset(
    {"instructions", "few_shot", "prompt", "output", "toolset", "translations"}
)
_TEXTS = re.compile(r"^texts-(.+)\.toml$")


def _named(name: str, key: Key) -> str:
    return variant_name(name, *key)


def _pick(variants: Variants, key: Key) -> Planned | None:
    language, model = key
    for k in (key, (language, None), (None, model), ALL):
        if k in variants:
            return variants[k]
    return None


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


def _component(
    table: str, body: dict[str, JsonValue], model: str | None, facts: Facts
) -> Component:
    from_facts = body.pop("from_facts", None)
    if from_facts is None:
        return TABLES[table].model_validate(body)
    assert model is not None and isinstance(from_facts, dict)
    model_facts = facts.models[model]
    options = dict(from_facts)
    effort = options.pop("effort", "default")
    if effort not in (*INTENTS, "default"):
        raise ValueError(f"{table}: {effort!r} is no reasoning level")
    level: Effort = effort
    match table:
        case "sampling":
            return model_facts.sampling_chunk(level, **options, **body)
        case "reasoning":
            budget = options.pop("budget", None)
            if options or body or not (budget is None or isinstance(budget, int)):
                raise ValueError(
                    f"{table}: from_facts takes an effort and a budget only"
                )
            return model_facts.reasoning_chunk(level, budget=budget)
        case _:
            raise ValueError(f"{table} records can't come from facts")


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
    data: Path, facts: Facts, compiler: Code, engines: Sequence[Path] = ()
) -> Plan:
    factors = data / "factors.toml"
    written = _read(factors)
    if held := sorted(set(written) & set(ENGINE_TABLES)):
        raise ValueError(
            f"{factors}: {', '.join(held)} tables are the World's, in its engines.toml"
        )
    found = _records(factors, written, DATA_TABLES)
    for path in engines:
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
        language, model = key
        found = _pick(variants, key)
        written = sorted({k[0] for k in variants if k[0] is not None})
        if found is None and language is not None and language not in written:
            if len(written) > 1:
                raise ValueError(
                    f"{table}.{name}: {table}.{fork_of} has no variant in {language} "
                    + f"to fork, and is written in {', '.join(written)}"
                )
            if written:
                found = _pick(variants, (written[0], model))
        if found is None:
            plan.skipped.append(
                f"{table} {_named(name, key)}: no fork of {table}.{fork_of}, which "
                + (
                    f"has no variant for {model}"
                    if model is not None
                    else "is made per model, and it isn't"
                )
            )
        return None if found is None else found.name

    def plan_table(table: str, models: list[str]) -> None:
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
                for model in models if "from_facts" in body else [None]:
                    key = (language, model)
                    try:
                        component = _component(table, dict(body), model, facts)
                    except Refused as e:
                        plan.skipped.append(f"{table} {_named(name, key)}: {e}")
                        continue
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
                    variants[key] = Planned(
                        table=table,
                        name=_named(name, key),
                        kind=component.kind_name,
                        digest=plan.registry.add(component),
                        tags=tags,
                        description=None if description is None else str(description),
                        fork_of=base(table, name, fork_of, key),
                        labels=labels,
                        language=language,
                    )
            add(table, name, variants)

    for table in ENGINE_TABLES:
        plan_table(table, [])
    served: dict[str, list[str]] = {}
    for r in plan.records:
        if r.kind in ("engine.local", "engine.remote"):
            model = model_name(plan.registry.get(r.digest), plan.registry)
            if model is not None:
                served.setdefault(model, []).append(f"{r.kind} {r.name}")
    models = sorted(set(served) & set(facts.models))
    for model in sorted(set(served) - set(facts.models)):
        plan.skipped.append(
            f"from_facts records for {model}: the facts don't know it, served by "
            + ", ".join(served[model])
        )
    for model in sorted(set(facts.models) - set(served)):
        plan.skipped.append(
            f"from_facts records for {model}: no planned engine serves it"
        )
    for table in TABLES:
        if table not in (*ENGINE_TABLES, *LATE_TABLES):
            plan_table(table, models)

    for name, raw in found.get("recipe", {}).items():
        assert isinstance(raw, dict)
        body = dict(raw)
        tags = _tags(body.pop("tags", []))
        description = body.pop("description", None)
        fork_of = body.pop("fork_of", None)
        parts = {p: planned[(p, str(body.pop(p)))] for p in RECIPE_PARTS if p in body}
        languages = sorted(
            {k[0] for v in parts.values() for k in v if k[0] is not None}
        )
        per_model = any(k[1] is not None for v in parts.values() for k in v)
        variants: Variants = {}
        for language in languages or [None]:
            for model in models if per_model else [None]:
                key = (language, model)
                made = _recipe(name, key, parts)
                if isinstance(made, str):
                    plan.skipped.append(f"recipe {_named(name, key)}: {made}")
                    continue
                try:
                    recipe = Recipe.model_validate({**body, **made})
                except ValidationError as e:
                    raise ValueError(f"recipe.{name}: {e}") from None
                skeleton, compilation = compiled(recipe, plan.registry.get, compiler)
                variants[key] = Planned(
                    table="recipe",
                    name=_named(name, key),
                    kind="skeleton",
                    digest=plan.registry.add(skeleton),
                    tags=tags,
                    description=None if description is None else str(description),
                    fork_of=base("recipe", name, fork_of, key),
                    compilation=plan.registry.add(compilation),
                )
        add("recipe", name, variants)

    planned_engines = {
        r.name: r for r in plan.records if r.table in ("local_engine", "remote_engine")
    }
    for name, raw in found.get("judge", {}).items():
        assert isinstance(raw, dict)
        body = dict(raw)
        tags = _tags(body.pop("tags", []))
        description = body.pop("description", None)
        recipe, engine = str(body.pop("recipe", "")), str(body.pop("engine", ""))
        language = body.pop("language", None)
        if (recipes := planned.get(("recipe", recipe))) is None:
            raise ValueError(f"judge.{name}: no recipe named {recipe!r}")
        if (at := planned_engines.get(engine)) is None:
            plan.skipped.append(f"judge {name}: the World has no engine {engine}")
            add("judge", name, {})
            continue
        written = sorted({k[0] for k in recipes if k[0] is not None})
        if language is None and len(written) > 1:
            raise ValueError(
                f"judge.{name}: recipe.{recipe} is written in {', '.join(written)}, "
                + "so the judge names its language"
            )
        model = model_name(plan.registry.get(at.digest), plan.registry)
        key = (str(language) if language else (written or [None])[0], model)
        if (skeleton := _pick(recipes, key)) is None:
            plan.skipped.append(
                f"judge {name}: recipe.{recipe} has no variant for {model} on {engine}"
            )
            add("judge", name, {})
            continue
        try:
            judge = Judge.model_validate(
                {**body, "skeleton": skeleton.digest, "engine": at.digest}
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

    for table in LATE_TABLES:
        plan_table(table, models)
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
    language, model = key
    chosen: dict[str, str] = {}
    refused: list[str] = []
    missing: list[str] = []
    translated: list[str] = []
    for part, variants in parts.items():
        if part == "translations":
            continue
        found = _pick(variants, key)
        if found is None and part in TRANSLATED and language is not None:
            written = sorted({k[0] for k in variants if k[0] is not None})
            if len(written) == 1:
                found = _pick(variants, (written[0], model))
                translated.append(f"{part} in {written[0]}")
        if found is not None:
            chosen[part] = found.digest
        elif any(k[1] is not None for k in variants):
            refused.append(part)
        else:
            missing.append(part)
    if refused:
        return f"the facts refuse its {', '.join(refused)}"
    if missing:
        return f"it has no {', '.join(missing)} in {language}"
    if translated:
        named = parts.get("translations")
        found = None if named is None else _pick(named, key)
        if found is None:
            return (
                f"its {', '.join(translated)} needs translations in {language}, and "
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

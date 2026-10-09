import json
import re
import tomllib
from collections.abc import Collection, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from pydantic import JsonValue, ValidationError

from chatddx.catalog import language_tag, variant_name
from chatddx.core.rig import entry
from chatddx.factors.base import Code, Component
from chatddx.factors.bundle import Registry
from chatddx.factors.engine import LocalEngine, ModelArtifact, RemoteEngine
from chatddx.factors.request import (
    RECIPE_PARTS,
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
from chatddx.factors.scoring import ExpectationSchema, Scorer
from chatddx.facts import INTENTS, Effort, Facts, Refused, model_name
from chatddx.scorers.scorer import function

# The sample's tables, in the order they're planned: a table may reference only those before it.
# Models and engines come first, so `from_facts` records are written for the models they serve.
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
}
ENGINE_TABLES = ("model", "local_engine", "remote_engine")
# References outside recipes, by table and field: each names records of another table.
REFERENCES: dict[str, dict[str, str]] = {
    "toolset": {"tools": "tool"},
    "scorer": {"expectation_schema": "expectation_schema"},
    "local_engine": {"model": "model"},
}
SAMPLE = Path(__file__).parent.parent / "data" / "sample"


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
    # a scorer's view labels, by position
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


# What a record is made for: a language, when it's written in one, and a model, when it's
# written from the model's facts. None for either is all of them.
Key = tuple[str | None, str | None]
Variants = dict[Key, Planned]
ALL: Key = (None, None)
# The tables of chunks that hold text the model reads, kept by language in texts files.
TEXT_TABLES = (
    "instructions",
    "few_shot",
    "prompt",
    "output",
    "toolset",
    "translations",
)
# Text a recipe's translations stand in for when the language it's made in lacks it.
TRANSLATED = ("output", "toolset")
_TEXTS = re.compile(r"^texts-(.+)\.toml$")


def _named(name: str, key: Key) -> str:
    return variant_name(name, *key)


# The variant of `variants` for `key`, else the one for all languages or all models.
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
            if not callable(entry(component.code, component.entry_point)):
                raise TypeError(f"{component.entry_point} isn't a function")
        case Scorer():
            _ = function(component)
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


# A data set's texts, by language, from its texts-<language>.toml files.
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


# A data set's factors.toml, and its texts-<language>.toml files, planned with `more`
# factors files, such as a World's imported engines; each file resolves its files against
# its own directory.
def plan_factors(
    data: Path, facts: Facts, compiler: Code, more: Sequence[Path] = ()
) -> Plan:
    factors = data / "factors.toml"
    found = _records(factors, _read(factors), [*TABLES, "recipe"])
    for extra in more:
        for table, records in _records(
            extra, _read(extra), [*TABLES, "recipe"]
        ).items():
            known = found.setdefault(table, {})
            if twice := sorted(set(known) & set(records)):
                raise ValueError(f"{extra}: {table} {twice} are named before it too")
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

    def base(table: str, fork_of: object, key: Key) -> str | None:
        if fork_of is None:
            return None
        assert isinstance(fork_of, str)
        variants = planned.get((table, fork_of))
        if variants is None:
            raise ValueError(f"{table}.{fork_of} must come before its forks")
        found = _pick(variants, key)
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
                # Tools and scorers pin the code that runs them: the running chatddx,
                # which compilations record as their compiler, unless they name other
                # code.
                if table in ("tool", "scorer") and "code" not in body:
                    body["code"] = compiler.model_dump(mode="json")
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
                    if getattr(component, "code", None) == compiler:
                        try:
                            _check_runs(component)
                        except (LookupError, TypeError) as e:
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
                        fork_of=base(table, fork_of, key),
                        labels=labels,
                        language=language,
                    )
            add(table, name, variants)

    for table in ENGINE_TABLES:
        plan_table(table, [])
    # A `from_facts` record is written for each model a planned engine serves and the facts
    # know; the others are reported.
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
        if table not in ENGINE_TABLES:
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
                    fork_of=base("recipe", fork_of, key),
                    compilation=plan.registry.add(compilation),
                )
        add("recipe", name, variants)
    return plan


# A recipe's parts for `key`, by digest, or why it can't be made there. A part written in
# another language than the recipe's is the output's or toolset's, which the recipe's
# translations in its language stand in for; in its own language, it needs none.
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
class SampleCase:
    tags: tuple[str, ...]
    language: str
    targets: JsonValue


_CASES = re.compile(r"^cases-(.+)\.toml$")


# A data set's cases are in its cases-<language>.toml files, each case in its file's
# language.
def load_cases(data: Path) -> dict[str, SampleCase]:
    cases: dict[str, SampleCase] = {}
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
            if stray := set(case) - {"tags", "targets"}:
                raise ValueError(f"{path}: case.{id}: unknown keys {sorted(stray)}")
            where[id] = path
            cases[id] = SampleCase(
                tags=tuple(case.get("tags", ())),
                language=language,
                targets=case.get("targets"),
            )
    return cases

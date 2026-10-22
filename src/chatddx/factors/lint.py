import re
from collections.abc import Callable, Iterable, Mapping, Sequence

from jsonschema import ValidationError, validators
from jsonschema.exceptions import SchemaError, relevance
from jsonschema.protocols import Validator
from pydantic import JsonValue
from referencing.exceptions import Unresolvable
from referencing.jsonschema import UnknownDialect, specification_with

from .base import Component, Finding, resolve
from .bundle import Registry
from .engine import (
    REASONING_FLAGS,
    LocalEngine,
    LocalModel,
    flag_names,
    model_of,
    vllm_024,
)
from .facts import ModelFacts
from .request import Compilation, NativeOutput, Output, Skeleton, ToolOutput
from .scoring import Expectation, ExpectationSchema, Judge, Scorer
from .select import reaches
from .trial import Trial

_COMMIT = re.compile(r"^[0-9a-f]{40}$")
_NIX_STORE = re.compile(r"^/nix/store/[0-9a-z]{32}-.+$")

Languages = Callable[[str], str | None]
Reasons = Callable[[str], bool | None]
Validators = dict[str, Validator | str]


def _model(c: LocalModel, _: Registry) -> Iterable[Finding]:
    if not _COMMIT.match(c.revision):
        yield Finding(
            code="model.revision",
            message=f"revision {c.revision!r} is not a commit and can move",
            subject=c.digest,
        )


def _engine(c: LocalEngine, _: Registry) -> Iterable[Finding]:
    if not _NIX_STORE.match(c.runtime.closure):
        yield Finding(
            code="engine.closure",
            message=f"closure {c.runtime.closure!r} is not a Nix store path",
            subject=c.digest,
        )


def _scorer(c: Scorer, registry: Registry) -> Iterable[Finding]:
    schema = resolve(registry.get, c.expectation_schema, ExpectationSchema).json_schema
    for i, view in enumerate(c.views):
        if not reaches(schema, view.expectation):
            yield Finding(
                code="view.unreachable",
                message=f"view {i}'s expectation selector {view.expectation!r} "
                + "reaches nothing in the expectation schema",
                subject=c.digest,
            )


def _where(error: ValidationError | SchemaError) -> str:
    path: Sequence[str | int] = error.absolute_path
    if not path:
        return "at the root"
    tokens = (str(p).replace("~", "~0").replace("/", "~1") for p in path)
    return "at /" + "/".join(tokens)


def _known_draft(draft: JsonValue) -> bool:
    if not isinstance(draft, str):
        return False
    try:
        _ = specification_with(draft)
    except UnknownDialect:
        return False
    return True


def _validator(schema: dict[str, JsonValue]) -> Validator | str:
    draft = schema.get("$schema", "https://json-schema.org/draft/2020-12/schema")
    if not _known_draft(draft):
        return f"$schema {draft!r} names no draft that can be checked"
    cls = validators.validator_for(schema)
    try:
        cls.check_schema(schema)
    except SchemaError as e:
        return f"{_where(e)}: {e.message}"
    return cls(schema)


def _validator_of(
    digest: str, registry: Registry, known: Validators
) -> Validator | str:
    if digest not in known:
        schema = resolve(registry.get, digest, ExpectationSchema).json_schema
        known[digest] = _validator(schema)
    return known[digest]


def _expectation_schema(
    c: ExpectationSchema, registry: Registry, known: Validators
) -> Iterable[Finding]:
    match _validator_of(c.digest, registry, known):
        case str() as message:
            yield Finding(
                code="expectation_schema.invalid", message=message, subject=c.digest
            )
        case _:
            pass


def _output(c: Output, _: Registry) -> Iterable[Finding]:
    if c.json_schema is None:
        return
    match _validator(c.json_schema):
        case str() as message:
            yield Finding(
                code="output.schema_invalid", message=message, subject=c.digest
            )
        case _:
            pass


def _expectation(
    c: Expectation, registry: Registry, known: Validators
) -> Iterable[Finding]:
    validator = _validator_of(c.expectation_schema, registry, known)
    if isinstance(validator, str):
        return
    try:
        errors = list(validator.iter_errors(c.data))
    except Unresolvable as e:
        yield Finding(
            code="expectation.unchecked",
            message=f"a $ref in the schema can't be resolved: {e.ref}",
            subject=c.digest,
        )
        return
    error = max(errors, key=relevance, default=None)
    if error is not None:
        more = f" (and {len(errors) - 1} more)" if len(errors) > 1 else ""
        yield Finding(
            code="expectation.invalid",
            message=f"{_where(error)}: {error.message}{more}",
            subject=c.digest,
        )


def _has_ref(node: JsonValue) -> bool:
    match node:
        case {"$ref": str()}:
            return True
        case dict():
            return any(_has_ref(v) for v in node.values())
        case list():
            return any(_has_ref(v) for v in node)
        case _:
            return False


def _tools_with_refs(skeleton: Skeleton) -> list[str]:
    answer = (
        skeleton.contract.name if isinstance(skeleton.contract, ToolOutput) else None
    )
    tools = skeleton.body.get("tools")
    named: list[str] = []
    for t in tools if isinstance(tools, list) else []:
        match t:
            case {"function": {"name": str() as name, "parameters": parameters}} if (
                name != answer and _has_ref(parameters)
            ):
                named.append(name)
            case _:
                pass
    return named


def _choice(choice: JsonValue) -> str:
    match choice:
        case {"function": {"name": str() as name}}:
            return repr(name)
        case str():
            return choice
        case _:
            return "auto"


def _asks_to_reason(body: dict[str, JsonValue]) -> bool | None:
    kwargs = body.get("chat_template_kwargs")
    thinking = kwargs.get("enable_thinking") if isinstance(kwargs, dict) else None
    effort = body.get("reasoning_effort")
    if thinking is False or effort == "none":
        return False
    if thinking is True or effort is not None or "thinking_token_budget" in body:
        return True
    return None


def _runtime(
    subject: str, skeleton: Skeleton, engine: Component, by_default: bool | None
) -> Iterable[Finding]:
    constrained = isinstance(skeleton.contract, NativeOutput | ToolOutput)
    local = vllm_024(engine)
    if local is None:
        if constrained and _has_ref(skeleton.output_schema):
            yield Finding(
                code="schema.ref_unverified",
                message="the schema has $ref, which this engine isn't known to "
                + "resolve; inline_refs@1 removes them",
                subject=subject,
            )
        for name in _tools_with_refs(skeleton):
            yield Finding(
                code="schema.ref_unverified",
                message=f"the parameters of tool {name!r} have $ref, which this "
                + "engine isn't known to resolve",
                subject=subject,
            )
        return

    flags = flag_names(local.argv)
    t = skeleton.body.get("temperature")
    if isinstance(t, int | float) and 0 < t < 0.01:
        yield Finding(
            code="vllm.temperature_clamped",
            message=f"vLLM 0.24 raises temperature {t} to 0.01",
            subject=subject,
        )
    if "thinking_token_budget" in skeleton.body and not flags & REASONING_FLAGS:
        yield Finding(
            code="vllm.thinking_budget_refused",
            message="vLLM 0.24 refuses thinking_token_budget without "
            + "--reasoning-parser or --reasoning-config",
            subject=subject,
        )
    if "tools" in skeleton.body and not (
        {"--enable-auto-tool-choice", "--tool-call-parser"} <= flags
    ):
        constrained = False
        yield Finding(
            code="vllm.tools_refused",
            message="vLLM 0.24 refuses tool_choice "
            + f"{_choice(skeleton.body.get('tool_choice'))} without "
            + "--enable-auto-tool-choice and --tool-call-parser; for harmony and "
            + "Mistral models it goes out unconstrained instead",
            subject=subject,
        )
    if isinstance(skeleton.contract, NativeOutput) and skeleton.tools:
        yield Finding(
            code="vllm.native_tools_uncallable",
            message="with tool_choice auto, vLLM 0.24 constrains the whole answer to "
            + "response_format, so no tool can be called",
            subject=subject,
        )
    if constrained and "--reasoning-parser" not in flags:
        reasons = _asks_to_reason(skeleton.body)
        if reasons is None and "--default-chat-template-kwargs" not in flags:
            reasons = by_default
        if reasons is not False:
            yield Finding(
                level="warning" if reasons else "info",
                code="vllm.grammar_before_reasoning",
                message="without --reasoning-parser, vLLM 0.24 constrains the "
                + "answer from its first token, so a model can't reason first",
                subject=subject,
            )


def _languages(c: Trial, languages: Languages) -> Iterable[Finding]:
    request = languages(c.skeleton)
    if request is None:
        yield Finding(
            level="info",
            code="language.unknown",
            message="the request's language is unknown",
            subject=c.digest,
        )
        return
    cases = [languages(case) for case in c.cases]
    if unknown := cases.count(None):
        yield Finding(
            level="info",
            code="language.unknown",
            message=f"the language of {unknown} of {len(cases)} cases is unknown",
            subject=c.digest,
        )
    other = [lang for lang in cases if lang is not None and lang != request]
    if other:
        verb = "is" if len(other) == 1 else "are"
        yield Finding(
            code="language.mixed",
            message=f"the request is {request}, but {len(other)} of {len(cases)} "
            + f"cases {verb} {', '.join(sorted(set(other)))}",
            subject=c.digest,
        )


def _pair(
    subject: str,
    skeleton: str,
    engine: str,
    registry: Registry,
    reasons: Reasons | None,
) -> Iterable[Finding]:
    found = resolve(registry.get, skeleton, Skeleton)
    by_default = None if reasons is None else reasons(engine)
    yield from _runtime(subject, found, registry.get(engine), by_default)


def _made_for(c: Trial | Judge, registry: Registry) -> Iterable[Finding]:
    made = [
        found.facts
        for d in registry
        if isinstance(found := registry.get(d), Compilation)
        and found.skeleton == c.skeleton
    ]
    if not made or None in made:
        return
    models = {resolve(registry.get, f, ModelFacts).model for f in made if f}
    serves = model_of(c.engine if isinstance(c, Trial) else c.model, registry.get).name
    if serves in models:
        return
    worked = ", ".join(sorted(models))
    if isinstance(c, Trial):
        yield Finding(
            code="trial.engine_unmatched",
            message=f"the skeleton is worked out for {worked}, and the engine serves "
            + serves,
            subject=c.digest,
        )
    else:
        yield Finding(
            code="judge.model_unmatched",
            message=f"the skeleton is worked out for {worked}, and the judge's model "
            + f"is {serves}",
            subject=c.digest,
        )


def _judge(c: Judge, registry: Registry) -> Iterable[Finding]:
    if resolve(registry.get, c.skeleton, Skeleton).greedy and len(c.seeds) > 1:
        yield Finding(
            code="judge.greedy_seeds",
            message=f"the judge is greedy, so its {len(c.seeds)} seeds send the same request",
            subject=c.digest,
        )


def lint(
    registry: Registry,
    digests: Iterable[str] | None = None,
    languages: Languages | None = None,
    reasons: Reasons | None = None,
    engines: Mapping[str, str] | None = None,
) -> list[Finding]:
    findings: list[Finding] = []
    known: Validators = {}
    for d in registry if digests is None else digests:
        match registry.get(d):
            case LocalModel() as c:
                findings.extend(_model(c, registry))
            case LocalEngine() as c:
                findings.extend(_engine(c, registry))
            case Scorer() as c:
                findings.extend(_scorer(c, registry))
            case Output() as c:
                findings.extend(_output(c, registry))
            case ExpectationSchema() as c:
                findings.extend(_expectation_schema(c, registry, known))
            case Expectation() as c:
                findings.extend(_expectation(c, registry, known))
            case Trial() as c:
                findings.extend(_pair(d, c.skeleton, c.engine, registry, reasons))
                findings.extend(_made_for(c, registry))
                if languages is not None:
                    findings.extend(_languages(c, languages))
            case Judge() as c:
                if engines is not None and d in engines:
                    engine = engines[d]
                    findings.extend(_pair(d, c.skeleton, engine, registry, reasons))
                findings.extend(_made_for(c, registry))
                findings.extend(_judge(c, registry))
            case _:
                pass
    return findings

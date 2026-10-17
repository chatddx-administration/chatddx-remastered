import json
import math
from datetime import datetime, timedelta, timezone
from typing import Literal
from uuid import uuid4

import pytest
from pydantic import JsonValue, ValidationError

from chatddx.factors.base import Fingerprint, StructuralError, resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.cases import Case
from chatddx.factors.engine import LocalEngine
from chatddx.factors.scoring import Scorer, Scoring, View
from chatddx.factors.test.sample import NOW, RIG, fp, world
from chatddx.factors.trial import Execution
from chatddx.ledger import (
    Call,
    CanaryCall,
    Endpoint,
    ItemKey,
    JudgeCall,
    Run,
    RunFinished,
    RunItem,
    RunStarted,
    Score,
    ScoreFinished,
    ScoreItem,
    ScoreStarted,
    ToolCode,
    ToolRun,
    Turn,
    check_run,
    check_score,
    fingerprint_request,
)
from chatddx.ledger.test.rounds import ran, rounds


@pytest.fixture
def reg() -> Registry:
    return Registry()


def test_run_and_score_checks(reg: Registry) -> None:
    ids = world(reg)
    engine = reg.get(ids["engine"])
    assert isinstance(engine, LocalEngine)
    run_id = uuid4()

    def call(model: str, tokens: list[JsonValue] | None = None) -> Call:
        return Call(
            request=fp("body"),
            started_at=NOW,
            finished_at=NOW,
            status=200,
            response={"model": model, "prompt_token_ids": tokens or [2, 106, 1645]},
        )

    vignette = resolve(reg.get, ids["case"], Case).vignette.fingerprint

    def item(replicate: int, c: Call, observed: Fingerprint = vignette) -> RunItem:
        return RunItem(
            run=run_id,
            key=ItemKey(case=ids["case"], replicate=replicate),
            vignette=observed,
            call=c,
        )

    started = RunStarted(
        run=run_id, at=NOW, rig=RIG, trial=ids["trial"], canaries=ids["canaries"]
    )
    items = (item(0, call(engine.digest)), item(1, call("other")))
    canaries = tuple(
        CanaryCall(run=run_id, phase=p, canary=0, call=call("c"))
        for p in ("start", "end")
    )
    open_run = Run(started=started, items=items, canaries=canaries)
    run = Run(
        started=started, finished=open_run.finish(NOW), items=items, canaries=canaries
    )
    assert [f.code for f in check_run(run, reg)] == ["attestation.model"]
    unprobed = Run(started=started, items=items, canaries=canaries[:1])
    assert [
        f.message
        for f in check_run(
            unprobed.model_copy(update={"finished": unprobed.finish(NOW)}),
            reg,
        )
        if f.code == "run.incomplete"
    ] == ["1 canary calls missing"]
    assert run.items[0].call.response == {"model": engine.digest}
    unnamed = items[0].call.model_copy(update={"response": {"choices": []}})
    silent = Run(
        started=started, items=(items[0].model_copy(update={"call": unnamed}),)
    )
    assert [(f.code, f.message) for f in check_run(silent, reg)] == [
        (
            "attestation.model",
            f"engine returned no model name, declared {engine.digest!r}",
        )
    ]
    drifted = Run(
        started=started,
        items=(item(0, call(engine.digest), fp("edited at the source")),),
    )
    assert [(f.code, f.subject) for f in check_run(drifted, reg)] == [
        ("case.drift", str(drifted.items[0].key))
    ]

    tampered = run.model_copy(update={"items": items[:1]})
    assert "ledger.seal" in [f.code for f in check_run(tampered, reg)]

    rerun = Run(
        started=started,
        items=(
            item(0, call(engine.digest, [2, 106, 9])),
            item(1, items[1].call.model_copy(update={"prompt_tokens": None})),
        ),
    )
    assert "attestation.prompt_tokens" in [f.code for f in check_run(rerun, reg)]

    with pytest.raises(StructuralError, match="outside the trial"):
        _ = check_run(Run(started=started, items=(*items, item(2, call("m")))), reg)
    with pytest.raises(StructuralError, match="not planned"):
        bad_canary = CanaryCall(run=run_id, phase="start", canary=1, call=call("c"))
        _ = check_run(Run(started=started, canaries=(bad_canary,)), reg)
    with pytest.raises(StructuralError, match="duplicate canary calls"):
        _ = check_run(Run(started=started, canaries=canaries[:1] * 2), reg)
    with pytest.raises(ValidationError, match="different logs"):
        _ = Run(started=started, items=(items[0].model_copy(update={"run": uuid4()}),))
    with pytest.raises(ValidationError, match="instance of RunFinished"):
        _ = Run.model_validate({"started": started, "finished": started})

    score_id = uuid4()

    def score(*score_items: ScoreItem) -> Score:
        return Score(
            started=ScoreStarted(
                score=score_id,
                run=run_id,
                at=NOW,
                rig=RIG,
                scorer_version=1,
                scoring=ids["scoring"],
            ),
            items=score_items,
        )

    ok = ScoreItem(
        score=score_id,
        key=ItemKey(case=ids["case"], replicate=0),
        view=1,
        value=1.0,
        judge_calls=(
            JudgeCall(judge=ids["judge"], seed_index=0, call=call(engine.digest)),
        ),
    )
    assert check_score(score(ok), run, reg) == []
    assert [(f.code, f.message) for f in check_score(score(ok), open_run, reg)] == [
        ("score.run_unfinished", "the run hasn't finished")
    ]
    late = Run(
        started=started,
        finished=open_run.finish(NOW + timedelta(seconds=1)),
        items=items,
        canaries=canaries,
    )
    assert [(f.code, f.message) for f in check_score(score(ok), late, reg)] == [
        ("score.run_unfinished", "the score started before the run finished")
    ]
    with pytest.raises(StructuralError, match="seed index 1 out of range"):
        _ = check_score(
            score(
                ok.model_copy(
                    update={
                        "judge_calls": (
                            JudgeCall(
                                judge=ids["judge"],
                                seed_index=1,
                                call=call(engine.digest),
                            ),
                        )
                    }
                )
            ),
            run,
            reg,
        )
    elsewhere = score(ok).started.model_copy(update={"scorer_version": 2})
    assert [
        (f.code, f.message)
        for f in check_score(Score(started=elsewhere, items=(ok,)), run, reg)
    ] == [
        (
            "score.scorer_code",
            "the scorer code ran at version 2 of chatddx_scoring.match:score, not the "
            + "version the scorer pins (1)",
        )
    ]
    with pytest.raises(StructuralError, match="view 2 is out of range"):
        _ = check_score(score(ok.model_copy(update={"view": 2})), run, reg)
    with pytest.raises(StructuralError, match="duplicate score items"):
        _ = check_score(score(ok, ok), run, reg)
    with pytest.raises(StructuralError, match="is not view 0's judge"):
        _ = check_score(score(ok.model_copy(update={"view": 0})), run, reg)
    with pytest.raises(StructuralError, match="duplicate judge calls"):
        _ = check_score(
            score(ok.model_copy(update={"judge_calls": ok.judge_calls * 2})), run, reg
        )

    unjudged = ok.model_copy(update={"judge_calls": ()})
    assert [(f.code, f.message) for f in check_score(score(unjudged), run, reg)] == [
        ("judge.incomplete", "view 1's value rests on 0 of 1 judge seeds")
    ]
    unscored = unjudged.model_copy(update={"value": None})
    assert check_score(score(unscored), run, reg) == []

    partial = score(ok)
    finished = partial.model_copy(update={"finished": partial.finish(NOW)})
    assert [(f.code, f.message) for f in check_score(finished, run, reg)] == [
        ("score.incomplete", "3 items missing")
    ]


def test_seal_survives_a_storage_roundtrip() -> None:
    run_id = uuid4()
    local = datetime(2026, 9, 29, 2, tzinfo=timezone(timedelta(hours=2)))
    c = Call(request=fp("body"), started_at=local, finished_at=local)
    started = RunStarted(run=run_id, at=local, rig=RIG, trial="sha256:" + "0" * 64)
    items = tuple(
        RunItem(
            run=run_id,
            key=ItemKey(case="sha256:" + d * 64, replicate=r),
            vignette=fp("v"),
            call=c,
        )
        for d in "12"
        for r in range(2)
    )
    canaries = tuple(
        CanaryCall(run=run_id, phase=p, canary=0, call=c) for p in ("start", "end")
    )
    run = Run(started=started, items=items, canaries=canaries)
    assert started.at == NOW and started.at.utcoffset() == timedelta(0)

    stored = Run(
        started=RunStarted.parse(started.canonical),
        items=tuple(RunItem.parse(i.canonical) for i in reversed(items)),
        canaries=tuple(CanaryCall.parse(c.canonical) for c in reversed(canaries)),
    )
    assert stored.seal() == run.seal()
    assert "attempts" not in json.loads(items[0].canonical)["call"]


def test_where_a_run_went_and_its_cutoff_are_added_without_moving_old_seals() -> None:
    trial = "sha256:" + "0" * 64
    started = RunStarted(run=uuid4(), at=NOW, rig=RIG, trial=trial)
    doc = json.loads(started.canonical)
    assert "endpoint" not in doc and "execution" not in doc
    assert Execution().whitespace_limit == 100
    reached = RunStarted(
        run=started.run,
        at=NOW,
        rig=RIG,
        trial=trial,
        endpoint=Endpoint(name="qwen@pelle", url="http://pelle.km:12009/v1/"),
        execution=Execution(whitespace_limit=None),
    )
    parsed = RunStarted.parse(reached.canonical)
    assert parsed.endpoint == Endpoint(
        name="qwen@pelle", url="http://pelle.km:12009/v1/"
    )
    assert parsed.execution.whitespace_limit is None


def test_records_carry_their_schema_version() -> None:
    started = RunStarted(run=uuid4(), at=NOW, rig=RIG, trial="sha256:" + "0" * 64)
    doc = json.loads(started.canonical)
    assert doc["v"] == 2 and doc["stage"] == "started"
    doc["v"] = 1
    with pytest.raises(StructuralError, match="RunStarted v1 is not readable by v2"):
        _ = RunStarted.parse(json.dumps(doc))
    with pytest.raises(StructuralError, match="not a JSON object"):
        _ = RunStarted.parse("[]")


def test_execution_is_checked_against_the_calls(reg: Registry) -> None:
    ids = world(reg)
    run_id = uuid4()
    vignette = resolve(reg.get, ids["case"], Case).vignette.fingerprint

    def at(seconds: int) -> datetime:
        return NOW + timedelta(seconds=seconds)

    def item(replicate: int, start: int, end: int, attempts: int = 1) -> RunItem:
        call = Call(
            request=fp("body"),
            started_at=at(start),
            finished_at=at(end),
            attempts=attempts,
            prompt_tokens=fp("tokens"),
        )
        return RunItem(
            run=run_id,
            key=ItemKey(case=ids["case"], replicate=replicate),
            vignette=vignette,
            call=call,
        )

    def check(execution: Execution, *items: RunItem) -> list[tuple[str, str]]:
        started = RunStarted(
            run=run_id, at=NOW, rig=RIG, trial=ids["trial"], execution=execution
        )
        run = Run(started=started, items=items)
        return [(f.code, f.message) for f in check_run(run, reg)]

    sequential = Execution()
    assert check(sequential, item(0, 0, 5), item(1, 5, 9)) == []
    assert check(sequential, item(0, 0, 5, attempts=2), item(1, 5, 9)) == [
        ("execution.retries", "1 calls took more than the 1 attempts allowed")
    ]
    assert check(Execution(retries=1), item(0, 0, 5, attempts=2)) == []
    assert check(sequential, item(0, 5, 9), item(1, 0, 5)) == [
        ("execution.order", "1 items were sent before items scheduled ahead of them")
    ]
    shuffled = Execution(order="shuffled@1", shuffle_seed=7)
    first, second = (r for _, r in shuffled.schedule((ids["case"],), 2))
    assert check(shuffled, item(first, 0, 5), item(second, 5, 9)) == []
    assert [c for c, _ in check(shuffled, item(second, 0, 5), item(first, 5, 9))] == [
        "execution.order"
    ]
    assert check(sequential, item(0, 0, 6), item(1, 5, 9)) == [
        ("execution.concurrency", "2 calls were in flight at once, declared 1")
    ]
    assert check(Execution(concurrency=2), item(0, 0, 6), item(1, 5, 9)) == []


def test_canaries_bracket_the_items(reg: Registry) -> None:
    ids = world(reg)
    run_id = uuid4()
    vignette = resolve(reg.get, ids["case"], Case).vignette.fingerprint

    def call(start: int, end: int) -> Call:
        return Call(
            request=fp("body"),
            started_at=NOW + timedelta(seconds=start),
            finished_at=NOW + timedelta(seconds=end),
        )

    item = RunItem(
        run=run_id,
        key=ItemKey(case=ids["case"], replicate=0),
        vignette=vignette,
        call=call(10, 20),
    )

    def check(start: tuple[int, int], end: tuple[int, int]) -> list[str]:
        started = RunStarted(
            run=run_id, at=NOW, rig=RIG, trial=ids["trial"], canaries=ids["canaries"]
        )
        canaries = (
            CanaryCall(run=run_id, phase="start", canary=0, call=call(*start)),
            CanaryCall(run=run_id, phase="end", canary=0, call=call(*end)),
        )
        run = Run(started=started, items=(item,), canaries=canaries)
        return [f.message for f in check_run(run, reg) if f.code == "canary.phase"]

    assert check((0, 10), (20, 30)) == []
    assert check((0, 15), (25, 30)) == [
        "1 start canary calls hadn't finished when the first item was sent"
    ]
    assert check((0, 5), (15, 30)) == [
        "1 end canary calls started before the last item call finished"
    ]


def test_judge_calls_are_checked_against_the_score_execution(reg: Registry) -> None:
    ids = world(reg)
    run_id, score_id = uuid4(), uuid4()
    vignette = resolve(reg.get, ids["case"], Case).vignette.fingerprint
    keys = [ItemKey(case=ids["case"], replicate=r) for r in range(2)]
    run = Run(
        started=RunStarted(run=run_id, at=NOW, rig=RIG, trial=ids["trial"]),
        items=tuple(
            RunItem(
                run=run_id,
                key=k,
                vignette=vignette,
                call=Call(request=fp("body"), started_at=NOW, finished_at=NOW),
            )
            for k in keys
        ),
    )

    run = run.model_copy(update={"finished": run.finish(NOW)})

    def judged(replicate: int, start: int, end: int, attempts: int = 1) -> ScoreItem:
        call = Call(
            request=fp("judge"),
            started_at=NOW + timedelta(seconds=start),
            finished_at=NOW + timedelta(seconds=end),
            attempts=attempts,
        )
        return ScoreItem(
            score=score_id,
            key=keys[replicate],
            view=1,
            value=1.0,
            judge_calls=(JudgeCall(judge=ids["judge"], seed_index=0, call=call),),
        )

    def check(execution: Execution, *items: ScoreItem) -> list[str]:
        started = ScoreStarted(
            score=score_id,
            run=run_id,
            at=NOW,
            rig=RIG,
            scorer_version=1,
            scoring=ids["scoring"],
            execution=execution,
        )
        score = Score(started=started, items=items)
        return [f.code for f in check_score(score, run, reg)]

    sequential = Execution()
    assert check(sequential, judged(0, 0, 5), judged(1, 5, 9)) == []
    assert check(sequential, judged(0, 0, 5, attempts=2)) == ["execution.retries"]
    assert check(sequential, judged(0, 5, 9), judged(1, 0, 5)) == ["execution.order"]
    assert check(sequential, judged(0, 0, 6), judged(1, 5, 9)) == [
        "execution.concurrency"
    ]
    assert check(Execution(concurrency=2), judged(0, 0, 6), judged(1, 5, 9)) == []


def test_records_refuse_what_cannot_have_happened() -> None:
    later = NOW + timedelta(seconds=1)
    with pytest.raises(ValidationError, match="finished before it started"):
        _ = Call(request=fp("body"), started_at=later, finished_at=NOW)
    with pytest.raises(ValidationError, match="result"):
        _ = ToolRun.model_validate(
            {"id": "c0", "name": "t", "started_at": NOW, "finished_at": NOW}
        )
    failed = ToolRun(
        id="c0", name="t", started_at=NOW, finished_at=NOW, result="r", error="e"
    )
    assert json.loads(failed.model_dump_json())["result"] == "r"
    with pytest.raises(ValidationError, match="finite number"):
        _ = ScoreItem(
            score=uuid4(),
            key=ItemKey(case="sha256:" + "1" * 64, replicate=0),
            view=0,
            value=math.nan,
        )

    run_id, trial, canaries = uuid4(), "sha256:" + "0" * 64, "sha256:" + "1" * 64
    started = RunStarted(run=run_id, at=later, rig=RIG, trial=trial)
    with pytest.raises(ValidationError, match="finished before it started"):
        _ = Run(started=started, finished=RunFinished(run=run_id, at=NOW, seal=trial))

    def probed(*phases: Literal["start", "end"]) -> RunStarted:
        return RunStarted(
            run=run_id,
            at=NOW,
            rig=RIG,
            trial=trial,
            canaries=canaries,
            verify_at=phases,
        )

    assert probed("end", "start").canonical == probed("start", "end").canonical
    with pytest.raises(ValidationError, match="duplicates"):
        _ = probed("end", "end")
    with pytest.raises(ValidationError, match="at least 1"):
        _ = probed()
    with pytest.raises(ValidationError, match="goes with a canary set"):
        _ = RunStarted(run=run_id, at=NOW, rig=RIG, trial=trial, verify_at=("end",))


def test_items_and_a_score_s_finish_are_sensitive() -> None:
    records = (
        RunStarted,
        RunItem,
        CanaryCall,
        RunFinished,
        ScoreStarted,
        ScoreItem,
        ScoreFinished,
    )
    assert [r for r in records if r.sensitive] == [RunItem, ScoreItem, ScoreFinished]


def test_a_call_keeps_only_a_fingerprint_of_the_prompt_token_ids() -> None:
    def call(response: dict[str, JsonValue], tokens: Fingerprint | None = None) -> Call:
        return Call(
            request=fp("body"),
            started_at=NOW,
            finished_at=NOW,
            response=response,
            prompt_tokens=tokens,
        )

    read = call({"model": "m", "prompt_token_ids": [2, 106]})
    assert read.response == {"model": "m"}
    assert read.prompt_tokens == Fingerprint.of(b"[2,106]")
    unread = call({"model": "m", "prompt_token_ids": None})
    assert (unread.response, unread.prompt_tokens) == ({"model": "m"}, None)
    with pytest.raises(ValidationError, match="both given"):
        _ = call({"prompt_token_ids": [1]}, fp("tokens"))


def test_request_fingerprint_is_over_canonical_bytes() -> None:
    a = fingerprint_request({"model": "m", "messages": [], "temperature": 0})
    b = fingerprint_request({"temperature": 0, "messages": [], "model": "m"})
    assert a == b == Fingerprint.of(b'{"messages":[],"model":"m","temperature":0}')
    authored = fingerprint_request(
        {"response_format": {"properties": {"a": 1, "b": 2}}}
    )
    flipped = fingerprint_request({"response_format": {"properties": {"b": 2, "a": 1}}})
    assert authored != flipped


def test_tool_rounds_are_checked(reg: Registry) -> None:
    made = rounds(reg)
    ids, web, answer, trial = made.ids, made.web, made.answer, made.trial
    started, run_id, vignette = made.started, made.started.run, made.vignette
    call, check = made.call, made.check

    assert check(call("answer")) == []

    def code_findings(*entries: ToolCode) -> list[tuple[str, str]]:
        recorded = started.model_copy(update={"tool_code": entries})
        return [
            (f.code, f.message)
            for f in check_run(Run(started=recorded), reg)
            if f.code == "tools.code"
        ]

    assert code_findings() == [
        ("tools.code", "the code tool 'web_search' ran with isn't recorded")
    ]
    assert code_findings(ToolCode(tool=web, version=2)) == [
        (
            "tools.code",
            "tool 'web_search' ran at version 2 of chatddx_tools.web:search, not the "
            + "version it pins (1)",
        )
    ]
    with pytest.raises(StructuralError, match="the skeleton lacks"):
        _ = code_findings(
            ToolCode(tool=web, version=1), ToolCode(tool=answer, version=1)
        )
    with pytest.raises(ValidationError, match="duplicates"):
        _ = RunStarted(
            run=run_id,
            at=NOW,
            rig=RIG,
            trial=trial,
            tool_code=(ToolCode(tool=web, version=1),) * 2,
        )
    zero = "sha256:" + "0" * 64
    either = (ToolCode(tool=web, version=1), ToolCode(tool=zero, version=1))
    reordered = started.model_validate(
        {**started.model_dump(), "tool_code": either[::-1]}
    )
    assert [e.tool for e in reordered.tool_code] == sorted([web, zero])
    assert check(call("web_search"), Turn(tools=ran("c0"), call=call("answer"))) == []
    searched = Turn(tools=ran("c0"), call=call("web_search"))
    assert check(call("web_search"), searched, searched) == ["tools.unanswered"]
    assert check(call("web_search"), searched) == ["tools.unanswered"]
    drifted = Turn(tools=ran("c0"), call=call("answer", model="other"))
    assert check(call("web_search"), drifted) == ["attestation.model"]
    with pytest.raises(StructuralError, match="more than 2 rounds"):
        _ = check(call("web_search"), searched, searched, searched)
    with pytest.raises(StructuralError, match="no tool named 'fetch'"):
        _ = check(call("web_search"), Turn(tools=ran("c0", name="fetch"), call=call()))
    refused = ToolRun(
        id="c0",
        name="fetch",
        started_at=NOW,
        finished_at=NOW,
        result="There is no tool named fetch.",
        error="unknown tool",
    )
    assert check(call("fetch"), Turn(tools=(refused,), call=call("answer"))) == []
    with pytest.raises(StructuralError, match="didn't make"):
        _ = check(call("web_search"), Turn(tools=ran("c9"), call=call("answer")))

    plain = RunItem(
        run=run_id,
        key=ItemKey(case=ids["case"], replicate=0),
        vignette=vignette,
        call=call(),
        turns=(Turn(tools=ran("c0"), call=call()),),
    )
    plain_run = Run(
        started=RunStarted(run=run_id, at=NOW, rig=RIG, trial=ids["trial"]),
        items=(plain,),
    )
    with pytest.raises(StructuralError, match="no tools"):
        _ = check_run(plain_run, reg)
    assert (
        "turns"
        not in RunItem.model_validate(
            {**plain.model_dump(), "turns": ()}
        ).canonical_doc()
    )


def test_a_round_stopped_before_its_call_is_kept_and_noted(reg: Registry) -> None:
    made = rounds(reg)
    two = made.call("web_search", "web_search")
    for tools, message in (
        (ran("c0"), "round 1 stopped after 1 of 2 tool calls, before its call"),
        (ran("c0", "c1"), "round 1 stopped after 2 of 2 tool calls, before its call"),
    ):
        unsent = Turn(tools=tools)
        assert made.item(two, unsent).calls == (two,)
        assert [(f.code, f.message) for f in made.findings(two, unsent)] == [
            ("tools.stopped", message)
        ]
    later = (
        Turn(tools=ran("c0", "c1"), call=two),
        Turn(tools=ran("c0", error="stopped")),
    )
    assert [f.message for f in made.findings(two, *later)] == [
        "round 2 stopped after 1 of 2 tool calls, before its call"
    ]


def test_a_round_without_its_call_leaves_no_call_in_the_record(reg: Registry) -> None:
    made = rounds(reg)
    sent = made.item(made.call("web_search"), Turn(tools=ran("c0"), call=made.call()))
    unsent = made.item(made.call("web_search"), Turn(tools=ran("c0")))
    assert set(json.loads(sent.canonical)["turns"][0]) == {"tools", "call"}
    assert set(json.loads(unsent.canonical)["turns"][0]) == {"tools"}


def test_only_the_last_round_may_lack_its_call(reg: Registry) -> None:
    made = rounds(reg)
    two = made.call("web_search", "web_search")
    with pytest.raises(ValidationError, match="only the last round may lack its call"):
        _ = made.item(two, Turn(tools=ran("c0")), Turn(tools=ran("c0"), call=two))


def test_a_round_without_its_call_runs_only_tools_the_response_called(
    reg: Registry,
) -> None:
    made = rounds(reg)
    with pytest.raises(StructuralError, match="didn't make"):
        _ = made.check(made.call("web_search"), Turn(tools=ran("c0", "c1")))


def test_score_views_are_checked_against_the_output_schema(reg: Registry) -> None:
    ids = world(reg)
    scoring = resolve(reg.get, ids["scoring"], Scoring)
    expectation_schema = resolve(reg.get, scoring.scorer, Scorer).expectation_schema
    scorer = reg.add(
        Scorer(
            entry_point="chatddx_scoring.match:score",
            version=1,
            expectation_schema=expectation_schema,
            views=(
                View(output="$.ddx[*]", metric="m"),
                View(output="$.ddx.first", metric="m"),
            ),
        )
    )
    unreachable = reg.add(Scoring(scorer=scorer, expectations=scoring.expectations))
    run_id, score_id = uuid4(), uuid4()
    opened = Run(started=RunStarted(run=run_id, at=NOW, rig=RIG, trial=ids["trial"]))
    run = Run(started=opened.started, finished=opened.finish(NOW))
    score = Score(
        started=ScoreStarted(
            score=score_id,
            run=run_id,
            at=NOW,
            rig=RIG,
            scorer_version=1,
            scoring=unreachable,
        )
    )
    assert [(f.code, f.message) for f in check_score(score, run, reg)] == [
        (
            "view.unreachable",
            "view 1's output selector '$.ddx.first' reaches nothing in the run's "
            + "output schema",
        )
    ]

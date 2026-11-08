from uuid import uuid4

from pydantic import JsonValue

from chatddx.factors.base import Fingerprint
from chatddx.factors.test.sample import NOW, RIG, fp
from chatddx.ledger import (
    Call,
    CanaryCall,
    Endpoint,
    Run,
    RunStarted,
    check_drift,
)
from chatddx.test.helpers import one_attempt

TRIAL = "sha256:" + "0" * 64
CANARIES = "sha256:" + "1" * 64
PELLE = Endpoint(name="qwen@pelle", url="http://pelle.km:12009/v1/")


def said(
    content: str, tokens: Fingerprint | None = None, system: str | None = None
) -> Call:
    response: dict[str, JsonValue] = {
        "choices": [{"message": {"role": "assistant", "content": content}}]
    }
    if system is not None:
        response["system_fingerprint"] = system
    return Call(
        request=fp("body"),
        started_at=NOW,
        finished_at=NOW,
        attempts=one_attempt(NOW),
        status=200,
        response=response,
        prompt_tokens=tokens or fp("tokens"),
    )


def ran(*calls: Call, endpoint: Endpoint = PELLE) -> Run:
    run = uuid4()
    started = RunStarted(
        run=run, at=NOW, rig=RIG, trial=TRIAL, endpoint=endpoint, canaries=CANARIES
    )
    return Run(
        started=started,
        canaries=tuple(
            CanaryCall(run=run, phase=phase, canary=0, call=c)
            for phase, c in zip(("start", "end"), calls, strict=False)
        ),
    )


def test_a_canary_answered_alike_has_drifted_nowhere() -> None:
    assert check_drift([ran(said("ready"), said("ready")), ran(said("ready"))]) == []


def test_a_canary_answered_otherwise_drifts_within_a_run_and_between_runs() -> None:
    within = check_drift([ran(said("ready"), said("Ready."))])
    between = check_drift([ran(said("ready")), ran(said("Ready."))])

    for found in (within, between):
        assert [(f.code, f.subject, f.params["ways"]) for f in found] == [
            ("canary.drift", "canary 0", 2)
        ]


def test_tokens_and_system_fingerprints_drift_under_codes_of_their_own() -> None:
    found = check_drift(
        [
            ran(said("ready", system="fp-a")),
            ran(said("ready", tokens=fp("other"), system="fp-b")),
        ]
    )

    assert [f.code for f in found] == ["canary.prompt_drift", "engine.system_drift"]


def test_runs_are_compared_only_at_the_same_endpoint() -> None:
    malborg = Endpoint(name="gpt@malborg", url="http://malborg.km:12009/v1/")

    assert (
        check_drift([ran(said("ready")), ran(said("Ready."), endpoint=malborg)]) == []
    )

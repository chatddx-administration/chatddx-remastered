import importlib
import json
from functools import cache
from typing import Any, cast

import pytest
from pydantic import JsonValue

from chatddx.curation import Plan, load_cases
from chatddx.factors.base import resolve
from chatddx.factors.bundle import Registry
from chatddx.factors.request import Skeleton, SlotName
from chatddx.factors.scoring import Judge, Scorer, View
from chatddx.factors.select import reaches
from chatddx.factors.test.sample import world
from chatddx.fake_vllm.chat import ANSWER as ANSWER_TEXT, instance
from chatddx.scorers.aggregate import AGGREGATES
from chatddx.scorers.metrics import score as shipped
from chatddx.scorers.patterns import (
    Pattern,
    first_mention,
    mentions,
    reciprocal_rank,
)
from chatddx.scorers.scorer import (
    Explained,
    Mark,
    Metric,
    Metrics,
    Pick,
    Scored,
    explain_view,
    score,
)
from chatddx.scorers.shipped import SCORERS, function, problems, read_by, refused
from chatddx.scorers.verdicts import asked
from chatddx.test.helpers import SHIPPED
from chatddx.test.world import DATA, world_plan


@cache
def read_only_plan() -> Plan:
    return world_plan()


SCHEMA = "sha256:" + "0" * 64


@pytest.mark.parametrize(
    "pattern, text, at",
    [
        ("pneumonia", "Likely pneumonia", 7),
        ("PNEUMONIA", "pneumonia", 0),
        ("mi", "Iron deficiency anemia", None),
        ("mi", "Acute MI", 6),
        ("hus", "Thus far unexplained fever", None),
        ("stone", "Kidney stones", None),
        ("stone*", "Kidney stones", 7),
        ("meningit*", "Viral meningitis", 6),
        ("tumör", "Hjärntumör", None),
        ("hjärntumör", "Misstänkt hjärntumör", 10),
        ("acute coronary syndrome", "Acute coronary syndrome (ACS)", 0),
        ("coronary acute", "Acute coronary syndrome", None),
        ("parkinson's disease", "Parkinson's disease", 0),
        ("gastro & intestinal", "Gastro-intestinal bleed", 0),
        ("gastro & intestinal", "Gastrointestinal bleed", None),
        ("copd | exacerbation & pulmonary", "Pulmonary exacerbation", 0),
        ("copd | exacerbation & pulmonary", "An exacerbation", None),
        ("copd | exacerbation & pulmonary", "Known COPD", 6),
        ("(renal | kidney) & (colic | stone*)", "Renal colic", 0),
        ("(renal | kidney) & (colic | stone*)", "Kidney stones", 0),
        ("(renal | kidney) & (colic | stone*)", "Renal failure", None),
        ("liver & failure", "Failure of the liver", 0),
    ],
)
def test_a_pattern_finds_whole_words(pattern: str, text: str, at: int | None) -> None:
    assert Pattern(pattern).find(text) == at


@pytest.mark.parametrize(
    "pattern, problem",
    [
        ("", "at least one word"),
        ("(pneumonia | copd", "never closed"),
        ("pneumonia &", "a word is missing"),
        ("pneumonia ) copd", r"unexpected '\)'"),
        ("* | copd", "names no word"),
    ],
)
def test_a_pattern_that_doesn_t_read_is_refused(pattern: str, problem: str) -> None:
    with pytest.raises(ValueError, match=problem):
        _ = Pattern(pattern)


@pytest.mark.parametrize(
    "pattern, alternatives",
    [
        ("pneumonia", ["pneumonia"]),
        ("copd | exacerbation & pulmonary", ["copd", "exacerbation & pulmonary"]),
        ("(renal | kidney) & colic | stone*", ["(renal | kidney) & colic", "stone*"]),
        ("((a | b)) | c", ["((a | b))", "c"]),
    ],
)
def test_a_pattern_s_alternatives_are_those_at_its_top_level(
    pattern: str, alternatives: list[str]
) -> None:
    assert Pattern(pattern).alternatives() == alternatives
    for alternative in alternatives:
        _ = Pattern(alternative)


def test_the_reciprocal_rank_is_that_of_the_first_diagnosis_found() -> None:
    differential = ["Pulmonary embolism", "Pneumonia", "Pneumonia, atypical"]
    assert reciprocal_rank(differential, "pneumonia") == Scored(
        0.5, {"answer": "2. Pneumonia"}
    )
    assert reciprocal_rank(differential, "sepsis") == Scored(
        0.0, {"reason": "not listed"}
    )
    assert reciprocal_rank(None, "pneumonia") == Scored(None, {"reason": "no answer"})


@pytest.mark.parametrize(
    "target, differential",
    [
        (
            "myocardial & infarction | mi | acs | acute & coronary & syndrome",
            ["Iron deficiency anemia"],
        ),
        ("uti | urinary & infection* | cystitis | urosepsis", ["Acute cholecystitis"]),
        ("hemolytic & uremic & syndrome | hus", ["Thus far unexplained fever"]),
        ("liver & failure | cirrosis | cirrhosis", ["Heart failure", "Liver abscess"]),
        ("overdose | drug & use | intoxication", ["Pain because of a fall"]),
        ("(gastro & intestinal | gi) & inflammation", ["Allergic inflammation"]),
    ],
)
def test_what_the_old_scorer_found_in_parts_of_words_is_not_found(
    target: str, differential: list[str]
) -> None:
    assert reciprocal_rank(differential, target).value == 0


def test_the_first_mention_is_counted_in_characters_to_its_first_word() -> None:
    text = "Cough and fever. Pneumonia is likely.\nPE is less likely."
    assert first_mention([text], "pneumonia") == Scored(
        17.0, {"answer": "Pneumonia is likely."}
    )
    assert first_mention([text], "pe | embolism") == Scored(
        38.0, {"answer": "PE is less likely."}
    )
    assert first_mention([text], "sepsis") == Scored(None, {"reason": "never named"})
    assert first_mention(None, "sepsis") == Scored(None, {"reason": "no answer"})


def test_a_first_mention_holds_the_target_to_one_sentence_at_a_time() -> None:
    text = "Heart failure is likely. A liver abscess is not."
    assert first_mention([text], "liver & failure").value is None
    assert first_mention([text], "liver & abscess").value == 27


def test_mentions_says_whether_the_target_is_named_at_all() -> None:
    assert mentions(["Admit to the surgical ward."], "admit*") == Scored(
        1.0, {"answer": "Admit to the surgical ward."}
    )
    assert mentions(["Discharge home."], "admit*") == Scored(
        0.0, {"reason": "not named"}
    )
    assert mentions([], "admit*") == Scored(0.0, {"reason": "not named"})
    assert mentions(None, "admit*") == Scored(None, {"reason": "no answer"})


def test_mentions_with_no_target_expects_nothing_named() -> None:
    assert mentions([], None) == Scored(1.0, {"reason": "none named, as expected"})
    assert mentions(["Signs of sepsis."], None) == Scored(
        0.0, {"answer": "Signs of sepsis.", "reason": "none expected"}
    )
    assert mentions(None, None) == Scored(None, {"reason": "no answer"})


@pytest.mark.parametrize(
    "aggregate, values, expected",
    [
        ("mean", [1.0, 0.5, 0.0], 0.5),
        ("mean", [], 0.0),
        ("std", [1.0, 0.0], 0.7071),
        ("var", [1.0, 0.0], 0.5),
        ("stderr", [1.0, 0.0], 0.5),
        ("stderr", [1.0], 0.0),
        ("std", [], 0.0),
    ],
)
def test_each_aggregate_is_inspect_s(
    aggregate: str, values: list[float], expected: float
) -> None:
    assert AGGREGATES[aggregate](values) == pytest.approx(expected, abs=1e-4)


def plan_scorer(**changes: Any) -> Scorer:
    fields: dict[str, Any] = {
        "entry_point": SHIPPED,
        "version": shipped.version,
        "expectation_schema": SCHEMA,
        "views": (
            View(
                output="$.diagnoses[*].diagnosis",
                expectation="/diagnosis",
                metric="reciprocal_rank",
            ),
            View(output="$.acute_warning", expectation="/warning", metric="mentions"),
            View(
                output="$.management.disposition",
                expectation="/disposition",
                metric="mentions",
            ),
        ),
    }
    return Scorer.model_validate(fields | changes)


ANSWER: JsonValue = {
    "diagnoses": [{"diagnosis": "Pulmonary embolism"}, {"diagnosis": "Pneumonia"}],
    "acute_warning": None,
    "management": {"disposition": "Admit to the medical ward"},
}
TARGETS: JsonValue = {
    "diagnosis": {"pattern": "pneumonia"},
    "warning": {"pattern": "sepsis"},
    "disposition": {"pattern": "admit*"},
}


def test_a_scorer_scores_each_of_its_views_through_its_entry_point() -> None:
    scorer = plan_scorer()
    run = function(scorer)
    assert run is shipped
    assert score(scorer, run, ANSWER, TARGETS) == [
        Scored(0.5, {"answer": "2. Pneumonia"}),
        Scored(0.0, {"reason": "not named"}),
        Scored(1.0, {"answer": "Admit to the medical ward"}),
    ]
    assert [s.value for s in score(scorer, run, None, TARGETS)] == [None, None, None]


def test_a_pattern_view_refuses_a_target_whose_pattern_doesn_t_read() -> None:
    scorer = plan_scorer()
    broken: JsonValue = {"diagnosis": {"pattern": "copd | (asthma"}}
    worded: JsonValue = {"diagnosis": {"text": "Asthma, or COPD."}}
    assert [(at, str(e)) for at, e in refused(scorer, broken)] == [
        ("/diagnosis", "a '(' in 'copd | (asthma' is never closed")
    ]
    assert refused(scorer, worded) == []
    assert refused(scorer, TARGETS) == []


def test_a_pattern_view_reads_its_target_s_pattern_and_a_judged_one_all_of_it() -> None:
    scorer = plan_scorer()
    targets: dict[str, JsonValue] = {"diagnosis": {"pattern": "pneumonia"}}
    worded: JsonValue = {"diagnosis": {"pattern": "pneumonia", "text": "Pneumonia."}}
    moved: JsonValue = {"diagnosis": {"pattern": "pneumonia*"}}
    assert read_by(scorer, worded) == read_by(scorer, targets)
    assert read_by(scorer, moved) != read_by(scorer, targets)
    judged = plan_scorer(
        views=(
            View(
                output="$.diagnoses[*].diagnosis",
                expectation="/diagnosis",
                metric="verdict",
                judge=JUDGE,
                params={"at": "/meets"},
            ),
        )
    )
    assert read_by(judged, worded) != read_by(judged, targets)


@pytest.mark.parametrize(
    "pattern, text, spans",
    [
        ("pneumonia", "Likely pneumonia", [(7, 16)]),
        ("acute coronary syndrome", "Acute coronary syndrome (ACS)", [(0, 23)]),
        ("liver & failure", "Failure of the liver", [(0, 7), (15, 20)]),
        ("copd | exacerbation", "COPD exacerbation", [(0, 4), (5, 17)]),
        ("stone*", "Kidney stones", [(7, 13)]),
        ("liver & failure", "Heart failure", None),
    ],
)
def test_a_pattern_tells_the_spans_it_matched(
    pattern: str, text: str, spans: list[tuple[int, int]] | None
) -> None:
    assert Pattern(pattern).spans(text) == spans


def test_an_explained_view_marks_what_its_metric_matched() -> None:
    scorer = plan_scorer()
    first, warning, disposition = (
        explain_view(scorer, function(scorer), i, ANSWER, TARGETS) for i in range(3)
    )
    assert first.output == ["Pulmonary embolism", "Pneumonia"]
    assert first.expected == [{"pattern": "pneumonia"}]
    assert first.explained == Explained(
        Scored(0.5, {"answer": "2. Pneumonia"}),
        ["Pulmonary embolism", "Pneumonia"],
        (Mark(1, 0, 9),),
    )
    assert warning.explained == Explained(Scored(0.0, {"reason": "not named"}), [])
    assert disposition.explained.marks == (Mark(0, 0, 5),)


def test_a_first_mention_marks_within_its_item_not_its_sentence() -> None:
    scorer = plan_scorer(
        views=(View(expectation="/diagnosis", metric="first_mention"),)
    )
    text = "Cough and fever. Pneumonia is likely."
    replayed = explain_view(scorer, function(scorer), 0, text, TARGETS)
    assert replayed.explained.marks == (Mark(0, 17, 26),)
    assert replayed.explained.scored.value == 17.0


def test_a_metric_without_an_explain_explains_by_its_score() -> None:
    def scored(*_: Any) -> Scored:
        return Scored(1.0, {"said": "so"})

    metrics = Metrics(1, {"plain": Metric("anything", scored)})
    assert metrics.explained("plain", [], [], {}) == Explained(
        Scored(1.0, {"said": "so"})
    )


def test_a_view_without_a_target_or_a_readable_one_isn_t_scored() -> None:
    scorer = plan_scorer()
    targets: JsonValue = {"diagnosis": {"pattern": "pneumonia &"}, "warning": False}
    first, warning, disposition = score(scorer, function(scorer), ANSWER, targets)
    assert first.value is None
    assert first.detail == {
        "reason": "the pattern doesn't read: a word is missing in 'pneumonia &'"
    }
    assert warning == Scored(1.0, {"reason": "none named, as expected"})
    assert disposition == Scored(None, {"reason": "no target"})


def test_free_text_is_split_by_the_view_before_it_is_scored() -> None:
    scorer = plan_scorer(
        views=(
            View(expectation="/diagnosis", metric="first_mention"),
            View(split="lines@1", expectation="/diagnosis", metric="reciprocal_rank"),
        )
    )
    text = "1. Pulmonary embolism\n2. Pneumonia"
    assert [s.value for s in score(scorer, function(scorer), text, TARGETS)] == [
        25.0,
        0.5,
    ]


def test_only_the_shipped_code_at_its_version_and_its_metrics_are_run() -> None:
    at = shipped.version
    with pytest.raises(
        LookupError, match=f"is at version {at} in chatddx .*, not {at + 1}"
    ):
        _ = function(plan_scorer(version=at + 1))
    with pytest.raises(LookupError, match="isn't shipped with chatddx .*, only "):
        _ = function(plan_scorer(entry_point="chatddx.scorers.patterns:_WORD"))
    unknown = (View(metric="recall"),)
    with pytest.raises(LookupError, match="knows no metric recall"):
        _ = function(plan_scorer(views=unknown))


def test_params_are_held_to_the_schemas_the_code_publishes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    assert problems(plan_scorer(params={"top": 3})) == [
        "the scorer's params don't fit: Additional properties are not allowed "
        + "('top' was unexpected)"
    ]
    given = plan_scorer(views=(View(metric="mentions", params={"top": 3}),))
    assert problems(given) == [
        "view 0's params for mentions don't fit: Additional properties are not "
        + "allowed ('top' was unexpected)"
    ]

    def top(
        output: list[JsonValue] | None, _: list[JsonValue], params: Any, _v: Any
    ) -> Scored:
        return Scored(float(len(output or []) >= params["top"]))

    ranked = Metric(
        "1 when at least top items are given",
        top,
        {"type": "object", "properties": {"top": {"type": "integer", "minimum": 1}}},
    )
    code = Metrics(shipped.version, {"top": ranked}, {"type": "object"})
    monkeypatch.setitem(SCORERS, SHIPPED, code)
    views = (View(output="$.diagnoses[*]", metric="top", params={"top": 2}),)
    assert problems(plan_scorer(views=views, params={"any": "thing"})) == []
    zero = (View(metric="top", params={"top": 0}),)
    assert problems(plan_scorer(views=zero)) == [
        "view 0's params for top at /top: 0 is less than the minimum of 1"
    ]
    scorer = plan_scorer(views=views)
    assert score(scorer, function(scorer), ANSWER, TARGETS) == [Scored(1.0)]


def test_each_shipped_entry_point_names_the_code_it_ships() -> None:
    for entry_point, code in SCORERS.items():
        module, _, attribute = entry_point.partition(":")
        assert getattr(importlib.import_module(module), attribute) is code
    assert SCORERS[SHIPPED] is shipped


JUDGE = "sha256:" + "1" * 64
MEETS = View(metric="verdict", judge=JUDGE, params={"at": "/meets"})
POINTS = View(metric="points", judge=JUDGE, params={"at": "/points", "max": 2})


def test_a_view_names_a_judge_exactly_when_its_metric_reads_verdicts() -> None:
    assert problems(plan_scorer(views=(View(metric="mentions", judge=JUDGE),))) == [
        "view 0 names a judge, which mentions doesn't read"
    ]
    unjudged = MEETS.model_copy(update={"judge": None})
    assert problems(plan_scorer(views=(unjudged,))) == [
        "view 0's metric verdict reads a judge's verdicts"
    ]
    assert problems(plan_scorer(views=(MEETS, POINTS))) == []
    assert problems(plan_scorer(views=(MEETS.model_copy(update={"params": {}}),))) == [
        "view 0's params for verdict don't fit: 'at' is a required property"
    ]


def test_a_judged_view_is_scored_from_its_judge_s_verdicts() -> None:
    differential = View(
        output="$.diagnoses[*].diagnosis",
        expectation="/diagnosis",
        metric="reciprocal_rank",
    )
    scorer = plan_scorer(views=(differential, MEETS, POINTS))
    run = function(scorer)
    with pytest.raises(ValueError, match=r"views \[1, 2\] need their judges' verdicts"):
        _ = score(scorer, run, ANSWER, TARGETS)
    verdicts: dict[int, list[JsonValue | None]] = {
        1: [{"meets": True}, {"meets": False}, None, {"meets": "yes"}],
        2: [{"points": 2}, {"points": 1}],
    }
    assert score(scorer, run, ANSWER, TARGETS, verdicts) == [
        Scored(0.5, {"answer": "2. Pneumonia"}),
        Scored(0.5, {"seeds": [1.0, 0.0, None, None]}),
        Scored(0.75, {"seeds": [1.0, 0.5]}),
    ]
    assert score(scorer, run, ANSWER, TARGETS, {1: [None], 2: [{}]})[1:] == [
        Scored(None, {"seeds": [None], "reason": "no seed gave a verdict"}),
        Scored(None, {"seeds": [None], "reason": "no seed gave a verdict"}),
    ]


def test_a_judged_view_explains_what_it_picked_from_each_seed_s_verdict() -> None:
    scorer = plan_scorer(views=(MEETS, POINTS))
    run = function(scorer)
    meets: list[JsonValue | None] = [
        {"meets": True},
        None,
        {"meets": "yes"},
        {"why": "no meets"},
    ]
    replayed = explain_view(scorer, run, 0, ANSWER, TARGETS, meets)
    assert replayed.explained == Explained(
        Scored(1.0, {"seeds": [1.0, None, None, None]}),
        picks=(
            Pick("/meets", True, 1.0),
            None,
            Pick("/meets", "yes", None),
            Pick("/meets", None, None),
        ),
    )
    graded = explain_view(scorer, run, 1, ANSWER, TARGETS, [{"points": 1}])
    assert graded.explained.picks == (Pick("/points", 1, 0.5),)


def test_a_judge_is_asked_only_when_it_has_what_it_reads() -> None:
    plan = read_only_plan()
    judge = resolve(plan.registry.get, plan.named("judge", "verdict").digest, Judge)
    skeleton = resolve(plan.registry.get, judge.skeleton, Skeleton)
    view = View(
        expectation="$.notes[?@.author == 'carol'].comment",
        metric="verdict",
        judge=judge.digest,
        params={"at": "/meets"},
    )
    noted = cast(dict[str, Any], load_cases(DATA)["noted"].targets)
    unnoted = {k: v for k, v in noted.items() if k != "notes"}
    assert asked(judge, skeleton, view, "Sepsis", noted) == {
        "completion": "Sepsis",
        "expectation": noted["notes"][0]["comment"],
    }
    assert asked(judge, skeleton, view, None, noted) == Scored(
        None, {"reason": "no answer"}
    )
    emptied = view.model_copy(update={"output": "/nothing"})
    assert asked(judge, skeleton, emptied, {"x": 1}, noted) == Scored(
        None, {"reason": "nothing in the answer to judge"}
    )
    assert asked(judge, skeleton, view, "Sepsis", unnoted) == Scored(
        None, {"reason": "no target"}
    )
    unread = Skeleton.model_validate(
        skeleton.model_dump()
        | {
            "messages": [
                {"role": "user", "content": ["Safe?\n", {"slot": "completion"}]}
            ]
        }
    )
    assert asked(judge, unread, view, "Sepsis", unnoted) == {
        "completion": "Sepsis",
        "expectation": "",
    }


TARGETS_SCHEMA = json.loads((DATA / "schemas" / "targets.json").read_text())


def world_scorer(name: str) -> tuple[Scorer, tuple[str | None, ...]]:
    plan = read_only_plan()
    stanza = plan.named("scorer", name)
    scorer = plan.registry.get(stanza.digest)
    assert isinstance(scorer, Scorer)
    return scorer, stanza.labels


def scored(name: str, answer: JsonValue, targets: JsonValue) -> dict[str, Scored]:
    scorer, labels = world_scorer(name)
    values = score(scorer, function(scorer), answer, targets)
    return {str(label): value for label, value in zip(labels, values, strict=True)}


def test_a_judge_reads_a_case_s_notes_beside_the_targets_the_patterns_read() -> None:
    targets = load_cases(DATA)["noted"].targets
    answer: JsonValue = {
        "diagnoses": [
            {"diagnosis": "Pneumonia", "critical": False},
            {"diagnosis": "Septic shock", "critical": True},
        ],
        "acute_warning": "Signs of shock",
        "disposition": "Intensive care",
    }
    assert scored("answer", answer, targets)["differential"] == Scored(
        0.5, {"answer": "2. Septic shock"}
    )
    carol = "$.notes[?@.author == 'carol']"
    assert reaches(TARGETS_SCHEMA, f"{carol}.comment")
    reg = Registry()
    ids = world(reg)
    judge = resolve(reg.get, ids["judge"], Judge)

    def fills(expectation: str) -> dict[SlotName, str]:
        view = View(
            output="$.diagnoses[*].diagnosis",
            expectation=expectation,
            metric="judge",
            judge=ids["judge"],
        )
        return judge.fills(view, answer, targets)

    [note, _] = cast(dict[str, list[dict[str, str]]], targets)["notes"]
    assert note["author"] == "carol"
    assert fills(f"{carol}.comment") == {
        "completion": "Pneumonia\nSeptic shock",
        "expectation": note["comment"],
    }
    assert fills(f"{carol}.answer")["expectation"] == note["answer"]


def test_a_dont_miss_is_held_to_what_each_output_can_say() -> None:
    targets: JsonValue = {
        "diagnosis": {"pattern": "pneumonia"},
        "dont_miss": {"text": "Pulmonary embolism", "pattern": "pulmonary embolism"},
    }

    def plan(critical: bool) -> JsonValue:
        return {
            "diagnoses": [
                {"diagnosis": "Pneumonia", "critical": False},
                {"diagnosis": "Pulmonary embolism", "critical": critical},
            ],
            "acute_warning": None,
            "disposition": "Admit",
        }

    assert scored("answer", plan(critical=True), targets)["dont-miss"] == Scored(
        1.0, {"answer": "Pulmonary embolism"}
    )
    named = scored("answer", plan(critical=False), targets)
    assert named["dont-miss"] == Scored(0.0, {"reason": "not named"})
    assert named["differential"] == Scored(1.0, {"answer": "1. Pneumonia"})
    listed: JsonValue = {"diagnoses": ["Pneumonia", "Pulmonary embolism"]}
    assert scored("list", listed, targets)["dont-miss"].value == 1.0
    lines = "1. Pneumonia\n2. Pulmonary embolism"
    assert scored("lines", lines, targets)["dont-miss"].value == 1.0
    assert scored("lines", "1. Pneumonia", targets)["dont-miss"].value == 0.0
    no_dont_miss: JsonValue = {"diagnosis": {"pattern": "pneumonia"}}
    assert scored("answer", plan(critical=True), no_dont_miss)["dont-miss"] == Scored(
        None, {"reason": "no target"}
    )


def test_a_case_that_calls_for_no_warning_is_met_by_a_plan_that_raises_none() -> None:
    targets: JsonValue = {"diagnosis": {"pattern": "pneumonia"}, "warning": False}
    plan: dict[str, JsonValue] = {
        "diagnoses": [{"diagnosis": "Pneumonia", "critical": False}],
        "acute_warning": None,
        "disposition": "Home",
    }
    assert scored("answer", plan, targets)["warning"] == Scored(
        1.0, {"reason": "none named, as expected"}
    )
    raised = plan | {"acute_warning": "Signs of sepsis"}
    assert scored("answer", raised, targets)["warning"] == Scored(
        0.0, {"answer": "Signs of sepsis", "reason": "none expected"}
    )


def test_a_target_s_words_are_a_judge_s_and_its_pattern_the_pattern_scorers() -> None:
    words: JsonValue = {"diagnosis": {"text": "Community-acquired pneumonia"}}
    answer: JsonValue = {
        "diagnoses": [{"diagnosis": "Pulmonary embolism"}, {"diagnosis": "Pneumonia"}],
        "acute_warning": None,
        "disposition": "Admit",
    }
    assert scored("answer", answer, words)["differential"] == Scored(
        None, {"reason": "the target has words, for a judge, but no pattern"}
    )
    assert reaches(TARGETS_SCHEMA, "/diagnosis/text")
    reg = Registry()
    ids = world(reg)
    judge = resolve(reg.get, ids["judge"], Judge)
    view = View(
        output="$.diagnoses[*].diagnosis",
        expectation="/diagnosis/text",
        metric="judge",
        judge=ids["judge"],
    )
    assert judge.fills(view, answer, words) == {
        "completion": "Pulmonary embolism\nPneumonia",
        "expectation": "Community-acquired pneumonia",
    }


READS = {
    "native": "answer",
    "native-tools": "answer",
    "native-inlined": "answer",
    "prompted": "answer",
    "tool-answer": "list",
    "tool-answer-tools": "list",
    "raw": "whole",
}


def test_each_scorer_s_views_pick_from_the_answers_it_reads() -> None:
    plan = read_only_plan()
    read: set[str] = set()
    for stanza in plan.stanzas:
        if stanza.kind != "skeleton":
            continue
        skeleton = plan.registry.get(stanza.digest)
        assert isinstance(skeleton, Skeleton)
        if skeleton.purpose == "judge":
            continue
        configuration = stanza.name.partition(" (")[0]
        reader = READS.get(configuration, "lines")
        scorer = plan.registry.get(plan.named("scorer", reader).digest)
        assert isinstance(scorer, Scorer)
        schema = skeleton.output_schema
        answer: JsonValue = ANSWER_TEXT if schema is None else instance(schema)
        if isinstance(answer, dict) and isinstance(answer.get("diagnoses"), list):
            for item in cast(list[JsonValue], answer["diagnoses"]):
                if isinstance(item, dict) and "critical" in item:
                    item["critical"] = True
        for view in scorer.views:
            assert view.output_items(answer), (stanza.name, view.output)
        values = score(scorer, function(scorer), answer, TARGETS)
        assert len(values) == len(scorer.views)
        read.add(reader)
    assert read == {"answer", "list", "lines", "whole"}

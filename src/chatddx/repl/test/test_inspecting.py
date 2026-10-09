from chatddx.bench import Bench
from chatddx.bench.test.sample import another_expectation
from chatddx.repl.test.sample import FREE_TEXT, GPT_OSS, PLAN, QWEN, Say

INTENTS = [
    "default",
    "off",
    "on",
    "minimal",
    "low",
    "medium",
    "high",
    "xhigh",
    "budget",
]


def line_of(written: str, start: str) -> str:
    return [line for line in written.splitlines() if line.strip().startswith(start)][-1]


def row_names(table: str) -> list[str]:
    cells = [
        line.split("│")[1].strip()
        for line in table.splitlines()
        if line.startswith("│")
    ]
    return [cell.removeprefix("▸ ") for cell in cells if cell]


def test_show_needs_something_in_the_cell(say: Say):
    assert "the cell is empty: use CONFIGURATION, on ENDPOINT" in say("show")


def test_show_sets_each_part_beside_what_it_is_and_renders_the_request(say: Say):
    written = say(f"cell {FREE_TEXT} {QWEN}", "show")

    assert f"cell: {FREE_TEXT} × {QWEN}" in written
    assert "temperature 0.6, top_p 0.95" in line_of(written, "sampling")
    assert "text output" in line_of(written, "output")
    assert "List the plausible diagnoses, one per line, most likely first." in written
    assert "‹vignette›‹appendices›" in written
    assert '"seed": 7' in written
    assert "[warning] language.mixed: the request is en, but 20 of 99 cases are sv" in (
        written
    )


def test_show_says_what_is_set_and_what_the_configuration_has(say: Say):
    written = say(f"cell {FREE_TEXT} {QWEN}", "set reasoning off", "show")

    assert f"off (set; {FREE_TEXT} has —)" in written
    assert "enable_thinking false" in line_of(written, "reasoning")
    assert '"enable_thinking": false' in written


def test_show_says_what_the_lints_say_of_the_pair(say: Say):
    written = say(f"cell plan-web {QWEN}", "show")

    assert "[warning] vllm.native_tools_uncallable" in written
    assert "with web_search" in line_of(written, "toolset")


def test_show_leaves_the_output_s_schema_to_show_output(say: Say):
    written = say(f"cell {PLAN} {QWEN}", "show")

    assert "‹the output's schema›" in written
    assert "IndividualDiagnosis" not in written
    assert "IndividualDiagnosis" in say("show output")


def test_show_says_the_seed_isn_t_sent_when_sampling_is_greedy(say: Say):
    written = say(f"cell {FREE_TEXT} {QWEN}", "set sampling greedy", "show")

    assert "greedy: the seed isn't sent" in written
    assert '"seed"' not in written


def test_show_says_which_cases_each_scorer_can_hold_the_cell_to(say: Say):
    written = say(f"cell {PLAN} {QWEN}", "show")

    assert "of 99 cases" in written
    assert "99 have it" in line_of(written, "plan       differential")
    assert "0 have it; missing: DutchFall10w" in line_of(
        written, "plan       dont-miss"
    )

    written = say(f"use {FREE_TEXT}", "show")

    assert "the output offers no such view" in line_of(written, "plan       warning")
    assert "99 have it" in line_of(written, "free-text  text")


def test_show_tag_counts_only_the_cases_with_any_of_the_tags(say: Say):
    written = say(f"cell {PLAN} {QWEN}", "show tag edn")

    assert "of 20 cases tagged edn" in written
    assert "20 have it" in line_of(written, "plan       differential")

    written = say("show tag edn dutch-fall")

    assert "of 50 cases tagged edn or dutch-fall" in written


def test_show_tag_needs_a_tag_with_cases(say: Say):
    assert "usage: show tag TAG..." in say("show tag")
    assert "no case tagged nowhere for alice" in say(f"use {PLAN}", "show tag nowhere")


def test_show_case_says_its_vignette_expectation_and_tags(say: Say):
    written = say("show case Dutchfall11w")

    assert "case Dutchfall11w, archive's" in written
    assert "sample/Dutchfall11w" in line_of(written, "source")
    assert "Main complaint: general weakness" in line_of(written, "vignette")
    assert "aaa | (abdominal | aortic) & aneurysm" in line_of(
        written, "expectation.diagnosis.pattern"
    )
    assert "dutch-fall" in line_of(written, "tags")
    assert "en" in line_of(written, "language")
    assert '"author": "Olof"' in written
    assert "no runs of yours with this case" in written


def test_show_case_says_when_scoring_has_expectations_to_choose_from(
    bench: Bench, say: Say
):
    case = bench.family("Dutchfall11w").case
    _ = another_expectation(bench, case, {"diagnosis": {"pattern": "sepsis"}})
    written = say("show case Dutchfall11w")

    assert "has expectations to choose from" in line_of(written, "expectation")


def test_show_without_a_name_shows_the_cell_s(say: Say):
    written = say(f"cell {FREE_TEXT} {QWEN}", "show output")

    assert "output free-text (en)  " in written
    assert "List the plausible diagnoses" in line_of(written, "guidance")
    assert "no runs of yours with this output" in written

    written = say("show engine", "show model", "show endpoint")

    assert "chatddx fake-vllm" in line_of(written, "runtime.closure")
    assert "Qwen/Qwen3-8B-AWQ" in line_of(written, "repo")
    assert "sample" in line_of(written, "cleared for")


def test_show_configuration_says_when_the_cell_s_is_unsaved(say: Say):
    written = say(f"cell {FREE_TEXT} {QWEN}", "set reasoning off", "show configuration")

    assert f"configuration {FREE_TEXT}+reasoning=off, unsaved" in written
    assert "enable_thinking" in written


def test_show_writes_what_is_json_as_json(say: Say):
    written = say("show tool web_search")

    assert '"additionalProperties": false' in written
    assert "chatddx.tools.web_search:web_search" in line_of(written, "entry_point")


def test_show_says_what_it_can_t_show(say: Say):
    assert "no kind 'frobnicate'" in say("show frobnicate")
    assert "a case isn't in the cell: show case NAME" in say("show case")
    assert "no case 'nope' for alice" in say("show case nope")
    assert "the cell has no configuration: show output NAME" in say("show output")
    assert "the cell has no endpoint: show engine NAME" in say("show engine")
    assert "a scorer isn't in the cell: show scorer NAME" in say("show scorer")
    assert "the cell has no reasoning" in say(
        f"cell {FREE_TEXT} {QWEN}", "show reasoning"
    )


def test_the_reasoning_table_sets_every_level_on_every_model(say: Say):
    written = say("reasoning")

    assert row_names(written) == INTENTS
    assert written.count(QWEN) == 1
    assert written.count(GPT_OSS) == 1
    assert "refused: always reasons" in written
    assert "thinking_token_budget=N" in written
    assert "the cell has no configuration on a model the facts know" in written


def test_the_reasoning_table_marks_the_cell_s_level(say: Say):
    written = say(f"cell {FREE_TEXT} {QWEN}", "reasoning")

    assert "│ ▸ default" in written
    assert f"▸ {QWEN}" in written

    written = say("set reasoning off", "reasoning")

    assert "│ ▸ off" in written
    assert "│ ▸ default" not in written


def test_scorers_say_whether_the_cell_s_output_offers_each_view(say: Say):
    written = say("scorers")

    assert "reciprocal_rank" in line_of(written, "plan ")
    assert "$.diagnoses[?@.critical == true].diagnosis" in written

    written = say(f"cell {FREE_TEXT} {QWEN}", "scorers")

    assert "doesn't offer it" in line_of(written, "plan ")
    assert "offers it" in line_of(written, "free-text")
    assert "the whole answer, lines@1" in written

from chatddx.repl.bench import SEEDS
from chatddx.repl.shell import Repl
from chatddx.repl.test.sample import FREE_TEXT, QWEN, Say


def test_seed_draws_a_short_seed_or_holds_one(repl: Repl, say: Say):
    written = say("seed")

    assert 0 <= repl.seed < SEEDS
    assert f"seed: #{repl.seed}" in written

    _ = say("seed 2147483647")
    assert repl.prompt == "alice #2147483647> "


def test_seed_says_what_isn_t_a_seed(repl: Repl, say: Say):
    written = say("seed -1", "seed 2147483648", "seed none")

    assert written.count("a seed is a whole number from 0 to 2147483647") == 3
    assert repl.seed == 7


def test_seed_says_a_greedy_configuration_isn_t_sent_it(say: Say):
    assert "greedy" not in say(f"cell {FREE_TEXT} {QWEN}", "seed 1")
    assert "greedy: the seed isn't sent" in say("set sampling greedy", "seed 2")

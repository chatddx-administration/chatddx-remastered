import math
import random

REPLICATES = 4


def drawn(
    seed: int, case: str, configuration: int, scorer: str, view: int, metric: str
) -> list[float]:
    """What a gathering of a case under a configuration would score on a scorer's view,
    a value per replicate, drawn as the seed has it alike every time: the configuration
    strong or weak, the case easy or hard and the view lenient or strict alike for every
    other they meet. Costs nothing but the drawing."""
    found = _sigmoid(
        0.8
        + 1.2 * _gauss(seed, "configuration", configuration)
        - 1.3 * _gauss(seed, "case", case)
        + 0.8 * _gauss(seed, "view", scorer, view)
    )
    draw = random.Random(f"{seed}/{case}/{configuration}/{scorer}/{view}")
    values: list[float] = []
    for _ in range(REPLICATES):
        hit = draw.random() < found
        if metric == "reciprocal_rank":
            rank = draw.choices((1, 2, 3, 4), weights=(65, 20, 10, 5))[0]
            values.append(1 / rank if hit else 0.0)
        else:
            values.append(1.0 if hit else 0.0)
    return values


def _gauss(seed: int, *of: object) -> float:
    return random.Random("/".join(map(str, (seed, *of)))).gauss()


def _sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))

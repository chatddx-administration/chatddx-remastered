from dataclasses import dataclass

from chatddx.bench import KINDS, Bench
from chatddx.catalog import threads as catalog_threads
from chatddx.identity import sees


@dataclass(frozen=True)
class Shelf:
    heading: str
    about: str
    kinds: dict[str, str]


SHELVES = (
    Shelf(
        "Cases",
        "What a model is asked about, and what a good answer holds.",
        {
            "appendix": "Extra text written for a case's vignette, such as lab results, "
            + "sent along with it.",
            "case": "A vignette, with the appendices sent along with it.",
            "expectation": "What a good answer to one case holds, written in an "
            + "expectation schema's form.",
            "expectation_schema": "The form expectations are written in, which a scorer "
            + "grades against.",
        },
    ),
    Shelf(
        "Configurations",
        "What is sent to a model: a configuration is put together from its parts and "
        + "a model.",
        {
            "configuration": "Everything a request sends but the case: its parts and "
            + "its model.",
            "few_shot": "Example exchanges, sent before the case.",
            "instructions": "The first message: what the model is and what it is to do.",
            "output": "The shape the answer takes, and how it is held to it.",
            "passthrough": "Request options no other part covers, sent as written.",
            "prompt": "The last message: where the case goes, and what is asked of it.",
            "reasoning": "How much the model thinks before it answers.",
            "sampling": "How freely the model picks its words, and how long the answer "
            + "may be.",
            "tool": "A function the model may call, such as a web search.",
            "toolset": "The tools a configuration offers, and how to use them.",
            "translations": "A configuration's texts in another language, for cases "
            + "written in it.",
        },
    ),
    Shelf(
        "Models",
        "The models, the engines serving them and what is known about them.",
        {
            "canary_set": "Fixed probes sent with a run, which show whether an engine "
            + "changed.",
            "engine": "What answers requests: a model served by given software on given "
            + "hardware.",
            "facts": "What is known about a model: its reasoning levels, recommended "
            + "sampling and limits.",
            "model": "A model's weights, pinned so that a run can be repeated.",
        },
    ),
    Shelf(
        "Scoring",
        "How answers are graded.",
        {
            "judge": "A model asked to grade answers, with its configuration and seeds.",
            "scorer": "Grades answers against expectations, a view at a time.",
        },
    ),
    Shelf(
        "Trials",
        "What is run.",
        {"trial": "A configuration on an engine, over cases, with seeds."},
    ),
)

_SHELVED = sorted(w for s in SHELVES for w in s.kinds)
if _SHELVED != sorted([*KINDS, "case"]):
    raise RuntimeError(
        f"the Library shelves every kind once: it shelves {', '.join(_SHELVED)}, the "
        + f"kinds are {', '.join(sorted([*KINDS, 'case']))}"
    )


def _label(word: str) -> str:
    return word.replace("_", " ")


@dataclass(frozen=True)
class Shelved:
    word: str
    about: str
    mine: int
    seen: int
    written: bool


def shelved(bench: Bench, written: list[str]) -> list[tuple[Shelf, list[Shelved]]]:
    counted = _counted(bench)
    return [
        (
            shelf,
            [
                Shelved(w, shelf.kinds[w], *counted[w], w in written)
                for w in sorted(shelf.kinds, key=_label)
            ],
        )
        for shelf in sorted(SHELVES, key=lambda s: s.heading)
    ]


def _counted(bench: Bench) -> dict[str, tuple[int, int]]:
    person = bench.person.id
    counted: dict[str, tuple[int, int]] = {}
    for word, kinds in KINDS.items():
        seen = [
            a
            for k in kinds
            for _, a in catalog_threads.heads(bench.rows, k)
            if sees(person, a)
        ]
        counted[word] = (sum(a.owner == person for a in seen), len(seen))
    families = bench.families()
    counted["case"] = (sum(f.about.owner == person for f in families), len(families))
    return counted

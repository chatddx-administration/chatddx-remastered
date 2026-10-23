from dataclasses import dataclass

from chatddx.bench import KINDS, Bench
from chatddx.catalog import threads as catalog_threads
from chatddx.identity import sees
from chatddx.locale import N_, pgettext, pgettext_noop, tr


@dataclass(frozen=True)
class Shelf:
    heading: str
    about: str
    kinds: dict[str, str]


SHELVES = (
    Shelf(
        N_("Cases"),
        N_("What a model is asked about, and what a good answer holds."),
        {
            "appendix": N_(
                "Extra text written for a case's vignette, such as lab results, sent "
                + "along with it."
            ),
            "case": N_("A vignette, with the appendices sent along with it."),
            "expectation": N_(
                "What a good answer to one case holds, written in an expectation "
                + "schema's form."
            ),
            "expectation_schema": N_(
                "The form expectations are written in, which a scorer grades against."
            ),
        },
    ),
    Shelf(
        N_("Configurations"),
        N_(
            "What is sent to a model: a configuration is put together from its parts "
            + "and a model."
        ),
        {
            "configuration": N_(
                "Everything a request sends but the case: its parts and its model."
            ),
            "few_shot": N_("Example exchanges, sent before the case."),
            "instructions": N_(
                "The first message: what the model is and what it is to do."
            ),
            "output": N_("The shape the answer takes, and how it is held to it."),
            "passthrough": N_("Request options no other part covers, sent as written."),
            "prompt": N_(
                "The last message: where the case goes, and what is asked of it."
            ),
            "reasoning": N_("How much the model thinks before it answers."),
            "sampling": N_(
                "How freely the model picks its words, and how long the answer may be."
            ),
            "tool": N_("A function the model may call, such as a web search."),
            "toolset": N_("The tools a configuration offers, and how to use them."),
            "translations": N_(
                "A configuration's texts in another language, for cases written in it."
            ),
        },
    ),
    Shelf(
        N_("Models"),
        N_("The models, the engines serving them and what is known about them."),
        {
            "canary_set": N_(
                "Fixed probes sent with a run, which show whether an engine changed."
            ),
            "engine": N_(
                "What answers requests: a model served by given software on given "
                + "hardware."
            ),
            "facts": N_(
                "What is known about a model: its reasoning levels, recommended "
                + "sampling and limits."
            ),
            "model": N_("A model's weights, pinned so that a run can be repeated."),
        },
    ),
    Shelf(
        N_("Scoring"),
        N_("How answers are graded."),
        {
            "judge": N_(
                "A model asked to grade answers, with its configuration and seeds."
            ),
            "scorer": N_("Grades answers against expectations, a view at a time."),
        },
    ),
    Shelf(
        N_("Trials"),
        N_("What is run."),
        {"trial": N_("A configuration on an engine, over cases, with seeds.")},
    ),
)

_SHELVED = sorted(w for s in SHELVES for w in s.kinds)
if _SHELVED != sorted([*KINDS, "case"]):
    raise RuntimeError(
        f"the Library shelves every kind once: it shelves {', '.join(_SHELVED)}, the "
        + f"kinds are {', '.join(sorted([*KINDS, 'case']))}"
    )


_WORDS = {
    "appendix": pgettext_noop("kind", "appendix"),
    "canary_set": pgettext_noop("kind", "canary set"),
    "case": pgettext_noop("kind", "case"),
    "configuration": pgettext_noop("kind", "configuration"),
    "engine": pgettext_noop("kind", "engine"),
    "expectation": pgettext_noop("kind", "expectation"),
    "expectation_schema": pgettext_noop("kind", "expectation schema"),
    "facts": pgettext_noop("kind", "facts"),
    "few_shot": pgettext_noop("kind", "few shot"),
    "instructions": pgettext_noop("kind", "instructions"),
    "judge": pgettext_noop("kind", "judge"),
    "model": pgettext_noop("kind", "model"),
    "output": pgettext_noop("kind", "output"),
    "passthrough": pgettext_noop("kind", "passthrough"),
    "prompt": pgettext_noop("kind", "prompt"),
    "reasoning": pgettext_noop("kind", "reasoning"),
    "sampling": pgettext_noop("kind", "sampling"),
    "scorer": pgettext_noop("kind", "scorer"),
    "tool": pgettext_noop("kind", "tool"),
    "toolset": pgettext_noop("kind", "toolset"),
    "translations": pgettext_noop("kind", "translations"),
    "trial": pgettext_noop("kind", "trial"),
}
if sorted(_WORDS) != _SHELVED:
    raise RuntimeError(
        f"a word for each kind the Library shelves: {', '.join(sorted(_WORDS))} are "
        + f"worded, {', '.join(_SHELVED)} shelved"
    )


def worded(word: str) -> str:
    return pgettext("kind", _WORDS.get(word, word.replace("_", " ")))


def _label(word: str) -> str:
    return word.replace("_", " ")


@dataclass(frozen=True)
class Shelved:
    word: str
    about: str
    mine: int
    seen: int
    written: bool

    @property
    def worded(self) -> str:
        return worded(self.word)


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
        for shelf in sorted(SHELVES, key=lambda s: tr(s.heading))
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

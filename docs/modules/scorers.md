```
AGENT: write
The module doc of scorers, now solidified (AGENTS.md, "Development stages"). Each section is its own suggestion.
---
# Scorers

The scoring code chatddx ships: what reads an item's answer, the metrics a scorer's views are scored by, what a judge is
asked, and the aggregates the edges show. The scorer as a factor, with its views and judges, is the factors'
(docs/modules/factors.md, "Scoring"), and scoring a run, item by item and judge by judge, the runner's
(docs/modules/runner.md, "A score").

This document describes the code `chatddx.scorers` (src/chatddx/scorers/). Its surface is `docs/surfaces/scorers.md`.
```

```
AGENT: write
What "shipped" means for a scorer, and how a scorer is checked against the code.
---
## Shipped code

A scorer runs only code chatddx ships, named by an entry point and the version it pins (docs/modules/factors.md,
"Code"). `SCORERS` holds what is shipped (src/chatddx/scorers/shipped.py:SCORERS): one entry point today,
`chatddx.scorers.metrics:score`, at version 2, with five metrics.

A scorer can run when its code is shipped at the version it pins, each view names a metric the code publishes, the views
of a judged metric name a judge and no other view does, and the scorer's parameters and each view's fit the schemas the
code publishes for them (src/chatddx/scorers/scorer.py:Metrics.problems). `problems` says why one can't, and is what
loading a data set, the bench and the portal check a scorer with; `function` gives the code, or refuses for the same
reasons.

The code publishes, for each metric, what it measures, a JSON Schema for a view's parameters, whether it reads a judge's
verdicts, and the unit of a value that isn't a score from 0 to 1. The API serves this as `GET /api/scorer-code`, and the
edges write a value with its unit (`unit_of`).
```

```
AGENT: write
The interface a metric is called through, and what it gives back.
---
## Scoring a view

The code is called once for each view (src/chatddx/scorers/scorer.py:ScoreFunction), with the view's metric, what the
view picks from the answer, none when the item has no answer, what it picks from the expectation, the scorer's
parameters with the view's over them, and, for a judged view, its judge's verdicts, one per seed. It gives a `Scored`: a
value, or none, and a detail, a JSON object saying what was found (`answer`) or why there is no value or a zero
(`reason`), such as "no answer" and "no target".

`score` scores every view of a scorer, and refuses a judged view that has no verdicts; `score_view` scores one view.
```

```
AGENT: write
The five shipped metrics, which docs/modules/factors.md, "Scorer" describes only as "the shipped pattern metrics".
---
## The metrics

- `reciprocal_rank`: 1 over the rank of the first item the target's pattern matches; 0 when none does.
- `first_mention`: where in its item the pattern is first matched, in characters, written with `@`; none when it never
  is.
- `mentions`: 1 when an item matches the pattern, or when nothing is named and nothing is expected; else 0.
- `verdict`, judged, with `at`, a JSON Pointer: the share of the judge's seeds whose verdict is true at `at`.
- `points`, judged, with `at` and a `max` over 0: the mean over the judge's seeds of the number at `at`, over `max`.

The first three give none without an answer. They take one target from what the view picks from the expectation, and
match a pattern as the factors say (docs/modules/factors.md, "Scorer"). An item that isn't text is matched as its JSON,
and a null item is left out. `first_mention` looks sentence by sentence, the text broken at line breaks and after `.`,
`!` and `?`, so that parts joined by `&` are found in one sentence. `reciprocal_rank` and `first_mention` give none when
nothing is expected.

The two judged metrics read each seed's verdict at `at`: `verdict` a boolean, `points` a number. A seed whose verdict
couldn't be read, or holds no value of that type at `at`, counts as none and is left out; when every seed is, there is
no value. The detail keeps each seed's.
```

```
AGENT: write
Reading an answer: the parts docs/modules/factors.md, "Scorer" leaves to the code.
---
## Reading an answer

`read` reads an item's answer from its last response by the skeleton's contract (src/chatddx/scorers/answer.py:read), as
docs/modules/factors.md, "Scorer" says, and the runner reads a judge's verdict the same way, by the judge skeleton's. It
gives the value, a problem, and whether the value was salvaged:

- A text answer whose output has a schema is the whole content as JSON, else the last fenced block that is JSON, else
  the last JSON value in the text.
- An answer that breaks the output's schema keeps its value, with the most relevant violation as its problem:
  `at /path: message`.
- An answer that can't be read has no value, and its problem says why: no response, no content, no call to the answer
  tool, JSON that doesn't parse, or null.
```

```
AGENT: write
What a judge is asked, which the runner sends and the gate guards.
---
## Asking a judge

`asked` gives what a judged view's judge is asked about one item, its slots filled by the judge's fill rule
(docs/modules/factors.md, "Judge"), or a `Scored` with no value when there is nothing to ask
(src/chatddx/scorers/verdicts.py:asked): no target, when the judge skeleton has an `expectation` slot and the view picks
nothing from the expectation; no answer; or nothing in the answer for the view to pick.
```

```
AGENT: write
The aggregates, and that they are for display.
---
## Aggregates

`mean` and `stderr`, with `std` and `var`, summarize a view's values for display only: the repl's summaries and the
means the API tells (src/chatddx/scorers/aggregate.py). No values give 0, and one value a spread of 0. What aggregates
scores for research isn't planned yet (docs/backlog.md, "Aggregation").
```

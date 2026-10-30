# The bench

The bench is what one person sees and does, whatever the edge: a `:Bench` built for a person, on a connection and an
inventory (`src/chatddx/bench/bench.py:Bench`). For that person it decides what they see and by what name, what they may
write, and where what they start runs. It keeps nothing of its own: the catalog says what holds of threads, families and
runs, the store keeps components, records and typed texts, the factors compile and lint, and the runner starts, sends
and scores behind its `:Gate`.

The examples run in order on the sample World, loaded for alice (`chatddx init-data alice --giftbag`), with
`chatddx fake-engines` serving; ids and digests are left out of what they show.

## Reads and writes

`Seen` holds the reads (`src/chatddx/bench/seen.py:Seen`), and `Bench` binds each write onto them from a module by what
it writes: components (`components.py`), configurations (`configurations.py`), cases (`cases.py`), `:Taking`
(`taking.py`), `:Saying` (`saying.py`), `:Updating` (`updating.py`) and runs (`runs.py`).

- **The connection** is in autocommit mode, as the runner needs (`src/chatddx/runner/run.py:Runner`): a read sees what
  is committed as it reads, and a write holds what it writes in transactions of its own.
- **Kept for the bench's life**: logins, an engine's model and a weights' handle (`Seen.__init__`), which for the repl
  is the session. The facts are read each time they're asked for (`Seen.facts`).
- **A write that keeps a component** returns its edit and what lints find of it once committed
  (`src/chatddx/bench/model.py:Written`). An edit names the head it was made on, and one made on a head the thread has
  moved on from is refused; `check` lints a component or a recipe with nothing stored.
- **Refusals**: what a person asks for that can't be is a `NotFound`, `Ambiguous`, `Conflict` or `OverQuota`
  (`src/chatddx/bench/errors.py`), the catalog's `MovedOn`, or else a `ValueError`; a start passes the gate's `Refused`
  on.

```python
import psycopg

from chatddx import settings
from chatddx.bench import Bench
from chatddx.factors.request import Instructions
from chatddx.inventory import World
from chatddx.store import People

conn = psycopg.connect(settings.database(), autocommit=True)
alice = People(conn).find("alice")
bench = Bench(conn, alice, World.load(settings.world()).inventory)

first = bench.new(Instructions(text="Answer as an emergency physician."), "brief", "en")
first.what, first.findings  # ('created', [])
second = bench.edit(
    first.edit.thread, first.edit.id, Instructions(text="Answer briefly."), "en"
)
second.what  # 'a new version'
bench.thread("brief", "instructions")[0] == second.edit  # True
bench.edit(first.edit.thread, first.edit.id, Instructions(text="Be terse."), "en")
# MovedOn: thread … has moved on since edit …: its head is edit …
```

## What a person sees

- **Visibility** is `:Sees` (`src/chatddx/identity/identity.py:sees`): a thread at its head, a family at its current
  binding, a run and its scores by their owner only. A person's own deleted things are read only where a read asks for
  them. A recipe or a variation names its parts by digest, checked for their kind only, seen or not (`Seen.variation`;
  `agents/wip-clearance.md`, "Before real patient data").
- **Words**: threads are asked for by `:Word` (`src/chatddx/bench/model.py:KINDS`). A person writes components of the
  kinds in `WRITTEN`, and configurations as recipes compiled or variations kept; the other kinds come by `:Loading`, and
  a person forks none of them.
- **Names**: a thread or a family is found by its id, its name or `OWNER/NAME`. Where a name holds several, the person's
  own win (`src/chatddx/identity/identity.py:preferred`), and several left are `Ambiguous`. A case is found by its
  `:Case title` (`Seen.case_titled`). A digest is shown by the name of a thread the person sees holding it, their own
  first, or else by its `:Title` (`Seen.title`).

```python
from chatddx.catalog import Subject

# alice's own, though the archive's is named plan-web too
mine, _ = bench.thread("plan-shown", "configuration")
bench.say(Subject(thread=mine.thread), deleted=True)
_, about = bench.thread("plan-shown", "configuration")
bench.login(about.owner)  # 'archive'
bench.thread("alice/plan-shown")
# NotFound: no thread 'alice/plan-web' for alice
[a.name for _, a in bench.threads("configuration", deleted=True)]  # ['plan-web']
bench.say(Subject(thread=mine.thread), deleted=False)
bench.thread("plan-shown", "configuration")[0] == mine  # True
```

## Model handles

- A person picks a model by its `:Handle`. Given weights are held by one model thread, which is checked as a process
  starts and before init-data commits (`src/chatddx/bench/handles.py:broken`), and the one endpoint serving a handle's
  head is where it runs (`Seen.served`). A deleted handle, or one no endpoint here serves, is refused as a pick to make
  again.
- Where a variation runs (`Seen.at`): under the handle of its recipe's model, which must hold that model still; under a
  handle the person names, only for a hand-written configuration; at an endpoint named, only for a `:Scripted run`.
- A judge is asked where its model's handle is served (`Seen.judged`), and is refused once its handle holds other
  weights. It still applies to a run (`Seen.scorers`), so that its scorer stays `:Left to score` and scoring says why.

```python
for edit, _ in bench.threads("model"):
    handle = bench.handle(edit.digest)
    print(handle.name, bench.served(handle).name)
# qwen3-8b-awq qwen3-8b-awq@fake
# gpt-oss-20b gpt-oss-20b@fake
# mistral-small mistral-small@remote

plan = bench.variation("plan")
bench.at(plan).name  # 'qwen3-8b-awq@fake'
bench.at(plan, model="gpt-oss-20b")
# ValueError: plan runs under its model's handle: set its model instead
mistral = bench.handle_named("mistral-small")
on_mistral = bench.variation("plan", {"model": mistral.weights})
bench.at(on_mistral).name  # 'mistral-small@remote'
```

## Variations

- A `:Variation` is built by `Seen.variation` and compiled by `Seen.skeleton`: under the facts its configuration was
  compiled with while nothing is varied, and under the facts as they are now once anything is
  (`src/chatddx/bench/seen.py:compiled_with`). `save`, `fork` and `edit` keep it, with its compilation.
- A `:Look` reads a variation with nothing stored: the request it would send, rendered with placeholders for the slots
  and the model (`src/chatddx/bench/model.py:PLACEHOLDERS`); what lints find of a trial on the person's first family, or
  on each language's cases (`Seen.findings`); where its reasoning and sampling `:Land` (`Seen.landed`); and its `:Reach`
  (`Seen.reach`).

```python
on, _ = bench.thread("on", "reasoning")
thinking = bench.variation("plan", {"reasoning": on.digest})
thinking.label  # 'plan+reasoning=on'
engine = bench.at(thinking).engine
bench.request(thinking, engine, seed=7)["chat_template_kwargs"]
# {'enable_thinking': True}
{part: at.level for part, at in bench.landed(thinking).items()}
# {'reasoning': 'on', 'sampling': 'on'}
bench.findings(thinking, engine, seed=7)  # []
bench.save(thinking, "plan-thinking").what  # 'created'
```

## Languages

- Cases are sent in their family's `:Language` (`Seen.languages`): as written when it is the configuration's
  `:Own language`, or when the configuration has none and no translations into it; `:Translated` when its recipe's
  translations go into it; `:Left out` otherwise, and linted as such (`translations.missing`).
- A trial written by hand holds cases of one language and is carried into it the same way, refused where a start would
  leave its cases out (`src/chatddx/bench/components.py:_carried`).

```python
from chatddx.bench.model import MODEL, PLACEHOLDERS

sample, _ = bench.thread("sample", "translations")
translating = bench.variation("plan", {"translations": sample.digest})
en, sv = bench.family("dutch-10"), bench.family("akm-01")
for carried in bench.languages(translating, [en.case, sv.case]):
    print(carried.language, carried.translated, carried.refused)
# en False None
# sv True None
swedish = bench.skeleton(translating, "sv")
swedish.render(model=MODEL, seed=7, fills=PLACEHOLDERS)["messages"][0]
# {'role': 'system', 'content': 'Fyll i handläggningsplanen för fallet.'}
[c.refused for c in bench.languages(bench.variation("plan"), [sv.case])]
# ['plan has no translations into sv']
```

## Cases, expectations and appendices

- A `:Typed case` stores its text in a database source of the inventory and adopts its case into a family of the
  person's own, in the language they say (`src/chatddx/bench/cases.py:type_case`). A text holds at most
  `settings.TYPED_TEXT_LIMIT` characters, and a person types at most `settings.TYPED_PER_DAY` a day.
- A case with appendices is made of a family and appendices the person sees (`case`), and a stale case's `:Replacement`
  is stored when asked for (`replacement`).
- An appendix is bound to the current vignette of a family the person sees (`src/chatddx/bench/components.py:bound`). A
  new version of it stores again each case that held the old one, returned in `Written.cases`.
- A person has one live expectation of a case under a schema: a write, a follow or a restore that would make two is
  refused (`src/chatddx/bench/seen.py:check_expecting`), and an expectation's new version stays on a case of its family
  (`:Carrying`). `take` forks the one expectation shared with them of each case, and says which cases they keep their
  own of, have none for, or have several `:To choose from` (`src/chatddx/bench/model.py:Taken`); `take_from` takes one,
  in place of their own when asked to replace it.

```python
from chatddx.factors.cases import Appendix

family = bench.family("dutch-10")
hb = bench.new(Appendix(vignette=family.vignette, text="Hb 98 g/L"), "hb")
case = bench.case(family.id, [hb.edit.digest])
bench.title(case)  # 'DutchFall10w with hb'
bench.case_titled("dutch-10 with hb")[1] == case  # True
lower = Appendix(vignette=family.vignette, text="Hb 96 g/L")
again = bench.edit(hb.edit.thread, hb.edit.id, lower).cases[case]
again in bench.family("dutch-10").cases  # True

(schema,) = bench.expectation_schemas(family.case)
bench.title(schema)  # 'targets'
bench.expectation(family.case, schema).data["diagnosis"]
# {'pattern': 'biliary & (colic | stone*)'}
```

## Runs and scoring

- `start` begins a run of a variation's cases for each language they're sent in (`src/chatddx/bench/runs.py:start`),
  with the endpoint's execution and canary set unless given, and the text cleanup their sources ask for
  (`Seen.cleanup`). Each is named by the variation's `:Label (variation)` and says the edit and parts it varies, and the
  runs after the first name it (`started_with`).
- `again` begins a run of a run's skeleton and cases under other seeds at its handle's latest endpoint, and is refused
  once the handle holds other weights. `start_trials` begins stored trials at the endpoint serving each one's engine.
- Runs a day and items a run are held to `settings.RUNS_PER_DAY` and `settings.ITEMS_PER_RUN`
  (`src/chatddx/bench/runs.py:check_quota`), checked for all of a start's runs before any is begun.
- The bench begins and queues, and sends nothing itself. `queue` puts a run's `:Job` at its execution's concurrency, to
  be scored once finished if asked; `queue_scoring` puts a finished run's, to score again. The worker sends what
  `resume` gives it and scores with `score` (`src/chatddx/bench/runs.py:score`).
- `gathering` gathers the person's runs about a `:Center` into seedings, those of one start if asked, a group for each
  configuration they varied and the latest run first (`src/chatddx/bench/gathering.py:gathering`): a component's runs
  are those `Seen.runs` finds reaching it or scored by what reaches it, a seed's those whose trial holds it.
- `Seen.unscored` and `Seen.outstanding` say what is `:Left to score`, and `Seen.scores_of` gives a run's latest score
  under each scorer, or every score.

```python
plan = bench.variation("plan")
case = bench.family("dutch-10").case
running = bench.start(plan, bench.at(plan).name, [case], seeds=(7,)).first
running.send()  # as a worker does with what bench.queue(running) puts
running.finish()  # []
run = bench.run(running.run)
bench.described(run)  # 'plan × qwen3-8b-awq × DutchFall10w (seed 7)'
len(bench.unscored(run))  # 2
for graded in bench.score(run):
    print(graded.name, {graded.label(i.view): i.value for i in graded.score.items})
# diagnoses {'differential': 0.0, 'dont-miss': 0.0}
# plan {'differential': 0.0, 'warning': 0.0, 'disposition': 0.0, 'dont-miss': 0.0}
bench.unscored(run)  # []
```

## Sensitive content

What the bench touches of `:Sensitive` content (`docs/chatddx.md`, "Vignettes and anything made from them are
sensitive"):

- **A typed case's text**, which it stores, so that the database holds vignettes (`agents/wip-clearance.md`, "Typed
  vignettes").
- **What a run or a judged scoring sends**, which it hands to the runner, whose gate refuses an endpoint before anything
  is written. A judged scorer the gate refuses doesn't apply to a run (`Seen.scorers`).
- **Not sensitive**: a look's request, rendered with placeholders, never a case's text.

```python
from chatddx.runner import Refused

fall = bench.type_case("A 74-year-old fell at home.", language="en", name="fall")
fall.vignette.source  # 'typed'
mistral = bench.handle_named("mistral-small")
remote = bench.variation("plan", {"model": mistral.weights})
bench.request(remote, None, seed=7)["messages"][1]
# {'role': 'user', 'content': '‹vignette›‹appendices›'}
bench.start(remote, bench.at(remote).name, [fall.case], seeds=(7,))
# Refused: endpoint 'mistral-small@remote' isn't cleared for source typed, which is sensitive
```

# Curation

Curation loads a data set (init-data), moves families whose vignettes moved (repair-data), and takes a person's share
back (wipe-data). Importing, exporting and verifying the store's content are its business too, and aren't written yet
(docs/backlog.md, "Loading data sets" and "Exporting data sets"). It's the housekeeper for data and a natural home for
a garbage collector (docs/backlog.md, "Garbage collection").

This document describes what curation does and why. The code is `chatddx.curation` (src/chatddx/curation/) and its
commands in src/chatddx/cli.py. Curation builds on the factors, the facts, the inventory, the catalog and the store.

## The archive
The archive is a person, `archive`, created the first time anything is loaded. It owns everything a data set loads:
a thread per record, and a family and an expectation thread per case. Whoever it is shared with collaborates on it,
and may be given forks of their own.

Owning the loaded content as a person, rather than as no one, uses the catalog as it is: what a person sees, owns or
forks works the same for the archive's threads as for anyone's. It also tells the data set's version of a thing apart
from a person's: a re-run recognises its own records by kind, name and the archive as owner (docs/catalog.md,
"Names"), and leaves everyone else's alone.

The archive is never wiped.

## Data sets
A data set is a directory of authored files: a `factors.toml`, the texts in `texts-<language>.toml` files, the cases
in `cases-<language>.toml` files, and the files they load, such as JSON schemas.

A data set says what the model reads, the language each text is written in, and the cases it is run on.
What a data set can't hold, engines, which engine judges and which engine its configurations are made for, is its
World's (docs/inventory.md, "Worlds").

A World may carry one beside its vignettes, in `_data/`. A World is what lies outside chatddx, and a data set is
chatddx's own authored content, so the leading `_` marks it as no part of the World: `World.load` doesn't read it.
`data` is init-data's `--data`, which loads it unless it names another.

The sample World carries the sample (worlds/sample/_data/), Kompismoln's World loads it with
`--data worlds/sample/_data`.

The test World carries the tests' data set (worlds/test/_data/).

### Factors

Both kinds of file hold one table per kind of component, keyed by name, whose keys are the component's fields
(docs/reference/factors.md).

On top of the fields:
- **References by name.** A toolset's tools, a scorer's expectation schema and a view's judge, a local engine's model
  a `local_model` record, and a remote engine's model, a `remote_model` record; and a recipe's parts name records,
  not digests.
- **Judges.** A judge names a `recipe`, its `seeds` and its `fill`, and no engine: the World binds a data set's judge
  to a handle, whose latest engine judges, and its recipe is compiled for the handle's model; a handle that doesn't
  resolve skips the judge and its scorers, reported as ops' error.
- **Files.** `json_schema_path` loads a JSON file, relative to the file that names it, in place of `json_schema`.
- **Forks.** `fork_of` names a record of the same kind that this one is a fork of. It is loaded as a fork of
  that record's thread, so the catalog knows what it varies (docs/catalog.md, "Forks"). It inherits no fields. A record
  whose origin isn't planned, as when the origin's recipe was skipped, is loaded as no fork and reported. A thread's
  origin is set when the thread is created, so a re-run only reports a held thread whose origin differs from the
  data's.
- **Code.** A tool or a scorer that names no `version` pins the version of its entry point that the running chatddx
  ships, so loading the data again after a deploy that raises a version moves it on. Its entry point must be shipped,
  at the version pinned, and a scorer's views must name metrics the code publishes, with params its schemas take.
- **Catalog entries.** `tags` and `description` are entries on the record's thread, and a scorer view's `label` is a
  label of the edit the scorer is kept with, so a renamed view is a new edit of the same scorer. A tool's
  `description` is also a field, the one the model reads.
- **Intents.** A reasoning chunk may ask for a `level` and a sampling chunk for the `recommended` sampling, worked
  out from the facts when a recipe is compiled (docs/factors.md, "Reasoning" and "Sampling"). A `from_facts` record
  is refused: "from_facts is gone; the facts are applied when a recipe is compiled, so ask for a reasoning `level` or
  a `recommended` sampling".
- **Translations by record.** A translations record's entries may be written in `of`, grouped by the record whose
  texts they translate, any record of texts (instructions, few-shot, prompt, output, toolset) or a recipe, for its
  appendix layout, each entry a `text` and its `translation`: `[[translations.sample.of."instructions.clinician"]]`.
  Loading makes them the chunk's entries into the texts file's language, and refuses a record that isn't one of texts
  ("'sampling.greedy' names no record of texts"), one the data set doesn't have ("'output.nope': no output named
  'nope'"), one written in the file's own language ("output.plan is written in en"), a text its record doesn't hold,
  so an entry no text uses any more is found, an entry that isn't a text and its translation, and a text translated
  two ways. A text that several records hold is written once, under any of them. A text left untranslated doesn't
  stop the loading (see "Texts").

A name is defined once per kind: a text is written in one texts file, and only a translations record's name comes
back in several, as one chunk (see "Texts"). A data set's `factors.toml` holds no `local_model`, `remote_model`,
`local_engine` or `remote_engine` tables, and a recipe names no `model`: engines are the World's (see "The World"),
and a recipe that names one is refused.

### Texts
What the model reads is written in a language, and a texts file's name gives it: every text record in
`texts-sv.toml` is written in Swedish, every translations record there translates into Swedish, and no record says its
own language. A chunk holds text when an instruction, an example, a prompt, a guidance, an answer-function or tool
description, or schema prose says something, so a prompt of slots alone, or an output without guidance or schema,
holds none. A chunk that holds text is written in a texts file, and one that holds none in `factors.toml`, where it
serves every language. Loading writes each text's language on its digest, and names it plainly, such as
`management-plan`; a translations chunk says its languages itself, and is given none.

A text is written in one language and translated into the others. A text record in two texts files, or in
`factors.toml` and a texts file, is refused: "instructions.clinician is in texts-en.toml and texts-sv.toml: a text is
written in one language, and translated into others". A translations record is written in the texts file of the
language it translates into, and gives its `entries` or its `of`, and no other field; one in `factors.toml` is refused.
Translations records of one name in several texts files are one chunk, into each file's language (docs/factors.md,
"Translations"): `description` and `fork_of` may be given in any of them, and must agree, and their tags are merged.

A recipe is made once, named plainly, such as `plan`, and names its parts by name: a part the data set doesn't have
is refused ("recipe.plan: no output named 'plans'"). It is written in its texts' language, and runs in that language
as written, and in each its translations carry it into, translated (docs/catalog.md, "Languages"). Loading compiles
it into each language its translations name, and says each it can't carry it into, and why (see "Loading"); the
recipe is made all the same.

The sample is written in English, in `texts-en.toml`. Its `texts-sv.toml` holds only `translations.sample`, into
Swedish: `free-text-guided`'s instructions and worked example, and every text the outputs and the toolset hold,
schemas included. Only `free-text-guided` names it, so it runs on the Swedish cases translated, and the other recipes
run on the English cases, the Swedish ones left out; the sample's translations, set in a variation, carry any of its
recipes but the judges' into Swedish.

### Cases
A case may have appendices, `[case.<id>.appendices]`, texts by name, each kept as a thread named by its name and told
apart by its vignette, and cases that send them after the vignette, `[[case.<id>.with]]`, each naming its `appendices` in
order and, optionally, `targets` of its own, since an appendix can change the right answer (docs/factors.md, "Case").
Line endings are made LF before an appendix is digested, as every edge does.

A cases file holds `[case.<id>]` tables, keyed by the vignette's id at the source. A case has `tags`, entries on its
family, and `targets`, its expectation, which must fit the data set's one expectation schema. A case is in exactly one
file, and the file's name gives its language: every case in `cases-sv.toml` is in Swedish.

Splitting by language rather than tagging each case keeps a language's cases together, as they are sent, scored and
compared together: a case runs in the language it was written in, under the configuration translated into it where
that isn't the configuration's own (docs/catalog.md, "Languages"). Notes in the targets keep a language of their
own.

### Facts and the engine
Some of what a request sends can only be worked out for a model: the sampling its makers recommend, the way a
reasoning level is asked for. The facts about each model an engine of the World serves are loaded as a thread of kind
`facts`, named after the model, such as `Qwen/Qwen3-8B-AWQ`, and a recipe is made for that endpoint's engine's model,
its intents compiled against its facts (docs/facts.md, "Compiling intents").

A served model the facts don't know is reported, since its engines can't compile a reasoning level or a recommended
sampling, and a recipe is skipped and reported when the facts refuse it on that engine, or when the World names no
endpoint for configurations. Engines and facts are planned first for this reason. A researcher swaps the model at the
bench, as any other part (docs/bench.md).

## The World
A World is a directory (docs/inventory.md, "Worlds"). Loading reads its `inventory.toml` for the source of the cases'
vignettes, the endpoints its judges are bound to and the endpoint whose engine its configurations are made for, and
takes its `engines.toml`, the models and engines its endpoints serve and nothing else, with the data set's factors,
and its `facts.toml`, facts about models the bundled facts don't know, with the bundled ones. So the sample World's
fake engines are loaded only with the sample World, and a World that serves a model of its own brings what is known
about it, which loading stores for the models its engines serve.

The World is `--world DIR`, or by default the directory `CHATDDX_WORLD` names. The repl reads the same World for its
endpoints and vignettes, and the facts from the store, as loading stored them.

A loading ends with the inventory checked against the engines just planned, all at once: what starting or reaching
each endpoint would refuse, and what is likely a slip (src/chatddx/inventory/check.py).

## Loading
`chatddx init-data USER [--world DIR] [--source NAME] [--giftbag] [--data DIR] [--facts PATH …]`
loads a data set, the World's `_data/` unless `--data` names another, for the archive, and shares it with USER,
who is added when missing. It connects as the writer and does everything in one transaction. It prints a line for each
thing it comes to.

1. **Plan.** The data set and the World's engines are planned into components, without the store: references
   resolved, the facts about each served model the facts know, recipes made once and compiled for the engine the
   World names for configurations, and into each language their translations name, judges' recipes compiled for
   their own engines, texts and entry points checked. A data set that can't be planned is refused before anything is
   written. A recipe its translations can't carry into a language is made all the same, and said after the records:
   `[untranslated] recipe asked: no translation into sv for 'You are an emergency physician.'`. Neither World's data
   set gives one.
2. **Records.** Each planned record becomes a thread named after it. A record the archive already has, by kind and
   name, is validated when its digest is unchanged and gets a new edit when it changed; a compiled skeleton's edit
   records its compilation. Its tags, description, view labels and language are brought in line with the data.
3. **Cases.** Each case is read from the World's source, the one `--source` names or the only one that lists its
   vignettes (a database source lists none), and adopted into a family named after its id, with its tags and its
   file's language, and gets an expectation thread.
4. **Appendices** are bound to the vignette as read, each a thread of the archive's, and each case that sends them is
   stored, with an expectation thread when it has targets. A case the source doesn't have, or one whose family can't
   adopt it, is reported, with what a survey of the source says happened to it: renamed to or from another id, or
   changed, and the family repair-data would move.
4. **Leftovers.** The archive's threads and families that the data no longer names are listed, but not deleted.
5. **Sharing.** USER becomes a collaborator on every thread and family the run came to.
6. **Giftbag.** With `--giftbag`, USER also gets a fork of every chunk, tool, skeleton and expectation thread, so
   what has moved on in the archive is proposed to them (docs/catalog.md, "What has moved on"). The forks of the
   expectation threads are also what USER is scored against: without them, the archive's shared expectations score
   nothing for USER. Expectation schemas, scorers, models, engines and facts stay the archive's. A fork they already
   have is kept, and one they deleted comes back, unless they own an expectation of that case under that schema by
   then: a person owns one at most (docs/catalog.md, "Owners"), so theirs is kept instead.
7. **Lints.** Every component the run came to is linted, with the catalog's languages and the facts' reasons, and
   the findings are printed, not stored. For the sample the fake models and engines say they are fake.
8. **The World.** The inventory check's findings, and a count.

A tag the archive gave that the data no longer lists is withdrawn; tags people gave stay theirs. Sharing is only
ever added.

Running it again is how a change to the data set is loaded, and how it is checked that the store still holds it: a
second run of an unchanged data set writes nothing and validates every record.

## Repairing
A vignette can be renamed or edited at its source. Its family then needs a repair, which moves it to the vignette's
new place (docs/catalog.md, "Repairing"). Loading only reports this, since a repair also moves the threads of everyone
who used those cases.

`chatddx repair-data [--world DIR] [--source NAME] [--dry-run]` surveys the source, the one `--source` names or the
World's only directory source, and repairs each of the archive's families it finds renamed or changed
there, printing what moved. A family that isn't the archive's is named and left to its owner. With `--dry-run`, it
only lists them.

After a rename, the data set should name the new id; after new content, the expectations stay with the old case
until someone confirms them for the new one (docs/catalog.md, "Repairing"), and the next loading gives the new case an
expectation of its own.

## Wiping
`chatddx wipe-data USER` takes back what a person has: it deletes what they own and withdraws them from what is shared
with them, an entry each, and only where it changes something, so wiping again writes nothing. The person stays.
Loading with `--giftbag` gives it back, restoring the deleted forks rather than forking anew, so a cycle of the two
writes an entry per gift and per share and no thread.

Wiping covers all a person owns, their runs and their own threads included, not only what loading gave them.

## Tests
src/chatddx/curation/test/.

- The tests run on the test World (worlds/test/, its data set in worlds/test/_data/), built so that each of its
  records exercises something a test reads. Its paths, the names tests share and the helpers they import are in
  src/chatddx/test/world.py; the fixtures built on them are in src/chatddx/conftest.py.
- What `curated` loads holds no mistakes: its only skips, lints and findings are the ones the World is built to
  give. Only `test_the_test_world.py` writes counts, skip lines or lint lines out; other tests derive them from the
  plan, the cases or the inventory. Broken data, such as an invalid expectation, an unreachable view, a misplaced
  clearance or a vignette that isn't UTF-8, is an edit a test makes to a copy of the World (`copied` and `edit` in
  src/chatddx/test/world.py).
- The test World's remote endpoint, `unknown@remote`, names `CHATDDX_TEST_REMOTE` as its credential. Tests run with it
  unset to see the gate refuse the endpoint for its secret (src/chatddx/bench/test/test_seen.py,
  src/chatddx/runner/test/test_score.py).
- `test_plan.py` plans data sets and needs no database.
- `test_init.py`, `test_repair.py`, `test_giftbag.py` and `test_pins.py` load the test World's data set whole, with a
  stand-in source whose vignettes are a line of text each (src/chatddx/curation/test/cases.py). A test that tells
  what a first load says, or loads data edited first, loads it into a copy of the migrated, empty store; the rest
  start from a copy of `loaded`, alice and the archive after one such load (src/chatddx/curation/test/conftest.py).
  The command tests read the test World itself, or a copy they edit.
- `test_tables.py` reads a case's appendices and the cases that send them, refuses what they say wrongly, and lands
  them and a canary set from the test World.

The Worlds' content is tested beside the names tests share, in src/chatddx/test/:
- `test_the_test_world.py` pins what the test World plans, skips and lints, and the quirks its vignettes carry.
- `test_worlds.py` checks every World in `worlds/`: each endpoint serves the engine planned under its name,
  init-data binds each World's endpoints and leaves the others' engines out, every target's pattern reads, the fake
  vLLM answers each skeleton as its contract asks or refuses it exactly when a `vllm.*` lint says vLLM would, and what
  it writes holds to each data set's schemas.
- `test_sample.py` holds what is true of the sample alone, and that it uses every table a data set and a World can
  hold at least once, as the example new Worlds follow.

The first two read the test World and every World; `test_sample.py` reads the sample, loaded once for it and
test_sample_world.py (src/chatddx/conftest.py, `sampled`).

## Terms

| Term | Meaning |
| --- | --- |
| Curation | Getting authored content into the store as the archive's, keeping it in step with its files, and taking it out of people's way. |
| Archive | The person who owns what a data set loads, and shares it with everyone else. |
| Data set | A directory of authored files: factors, cases by language, and what they load. |
| Record | A named entry of a data set's factors file, loaded as a thread. |
| Text | A chunk that holds text the model reads, written in a texts file whose name gives its language. |
| Giftbag | A person's own forks of the archive's chunks, tools, skeletons and expectations. |
| Leftover | An archive thread or family the data set no longer names. |
| Translations | A chunk that translates a data set's texts into other languages, written in the texts file of each language it translates into. |

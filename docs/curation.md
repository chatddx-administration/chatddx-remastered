# Curation

Most of what the store holds is authored: the chunks, recipes, tools and scorers people write, the engines a World
serves, the cases a source holds and the targets they are scored against. Someone has to get that content into the
store, keep it in step with the files it was written in, and take it back out of people's way. That is curation. It
is done for one person, the archive, whose content everyone else is given a share of.

Curation writes only components and what the catalog says about them (docs/catalog.md). Nothing refers to it, so no
digest depends on how something was loaded, and loading the same files twice changes nothing. It never writes the
ledger: runs and scores are the runner's.

This document describes what curation does and why. The code is `chatddx.curation` (src/chatddx/curation/) and its
commands in src/chatddx/cli.py. Curation builds on the factors, the facts, the inventory, the catalog and the store.

Today curation loads a data set (init-data), moves families whose vignettes moved (repair-data), and takes a
person's share back (wipe-data). Importing, exporting and verifying the store's content are its business too, and
aren't written yet (see "Open design issues").

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
in `cases-<language>.toml` files, and the files they load, such as JSON schemas. chatddx ships one, the sample
(src/chatddx/data/sample/), the old chatddx's inventory hand-edited into this shape (agents/wip-sample-data.md). The
sample holds no vignettes and no engines: those are a World's (see "The World").

````
AGENT: ADD
The sample has Swedish texts now (src/chatddx/data/sample/texts-sv.toml).
---
  texts-sv.toml   the same, in Swedish: free-text-guided's instructions and example, and translations of every
                  output and toolset text
````
```
src/chatddx/data/sample/
  factors.toml    what holds no text: models and engines (none here), sampling, reasoning, passthrough, tools,
                  expectation schemas, scorers, recipes, and chunks of slots alone
  texts-en.toml   what holds text the model reads, in English: instructions, few-shot, prompts, outputs, toolsets
                  and translations
  cases-en.toml   the English cases
  cases-sv.toml   the Swedish cases
  schemas/
```

### Factors
Both kinds of file hold one table per kind of component, keyed by name, whose keys are the component's fields
(docs/factors-api.md). The kinds are models, local and remote engines, instructions, few-shot, prompts, outputs,
sampling, reasoning, passthrough, translations, tools, toolsets, expectation schemas, scorers and recipes. On top of
the fields:
- **References by name.** A toolset's tools, a scorer's expectation schema, a local engine's model and a recipe's
  parts name records, not digests.
- **Files.** `json_schema_path` loads a JSON file, relative to the file that names it, in place of `json_schema`.
- **Forks.** `fork_of` names a record of the same kind that this one is a variation of. It is loaded as a fork of
  that record's thread, so the catalog knows what it varies (docs/catalog.md, "Forks"). It inherits no fields.
- **Code.** A tool or a scorer that names no `code` pins the running chatddx, as a compilation records it as its
  compiler, and its entry point must name a function there.
- **Catalog entries.** `tags` and `description` are entries on the record's thread, and a scorer view's `label` is a
  label. A tool's `description` is also a field, the one the model reads.
- **From facts.** `from_facts` asks for a sampling or reasoning chunk per model (see "Per model").

A name is defined once per kind across `factors.toml` and the World's, and a text's name may come back in each texts
file, as the same text in another language.

### Texts
What the model reads is written in a language, and a texts file's name gives it: every text in `texts-sv.toml` is
Swedish, and no record says its own language. A chunk holds text when an instruction, an example, a prompt, a
guidance, an answer-function or tool description, or schema prose says something, so a prompt of slots alone, or an
output without guidance or schema, holds none. A chunk that holds text is written in a texts file, and one that holds
none in `factors.toml`, where it serves every language. Loading writes each text's language on its digest, and names
it after it, such as `management-plan (en)`.

Texts come in two kinds. Instructions, few-shot and prompts are written in each language they are used in, as cases
are. Outputs and toolsets bring text with code, guidance and schemas, and may be written in one language and
translated into the others by a translations chunk of each (docs/factors.md, "Translations"); a native one can
still be written in a language of its own.

A recipe that names a text is made in each language that has it, named after the language, such as
`plan (en, Qwen/Qwen3-8B-AWQ)`. In a language, it takes each text written in that language. An output or a toolset
written only in another language is taken from there, and the recipe's translations in its language stand in for it;
a recipe without them there is skipped and reported. In the language its output and toolset are written in, it needs
no translations and is made without them. A recipe that names no text is made once, as before.

```
AGENT: CHANGE
The sample had no instructions, few-shot, passthrough or translations, and no Swedish texts. `free-text-guided` uses
all four and is made in both languages; the other recipes are unchanged, so their bare names stay unambiguous. The
Swedish texts are agent-translated and unreviewed (src/chatddx/data/sample/texts-sv.toml).
---
The sample is written in English, and one recipe in Swedish too. Its six outputs with guidance, its toolset, and
`free-text-guided`'s instructions and worked example are in `texts-en.toml`, and every recipe is made in English. The
instructions and the example are written again in `texts-sv.toml`, with translations of every text its outputs and
toolset hold, schemas included, so `free-text-guided` is made in Swedish too, its output translated. A trial of an
English recipe on the Swedish cases is linted as mixing languages, which is what a trial of an English request on a
Swedish case is; the sample's translations, set in a variation, carry any of its recipes into Swedish.
```
The sample is written in English: its six outputs with guidance and its toolset are in `texts-en.toml`, and every
recipe is made in English. A trial of them on the Swedish cases is linted as mixing languages until the sample has
Swedish texts, which is what a trial of an English request on a Swedish case is.

### Cases
A cases file holds `[case.<id>]` tables, keyed by the vignette's id at the source. A case has `tags`, entries on its
family, and `targets`, its expectation, which must fit the data set's one expectation schema. A case is in exactly one
file, and the file's name gives its language: every case in `cases-sv.toml` is in Swedish. The sample has 79 English
and 20 Swedish cases.

Splitting by language rather than tagging each case keeps a language's cases together, as they will be translated,
scored and compared together: a case runs in the language it was written in (docs/catalog.md, "Languages"). Notes in
the targets keep a language of their own.

### Per model
Some chunks can only be written for a model: the sampling its makers recommend, the way a reasoning level is asked
for. A `from_facts` record is written from each model's facts (docs/facts.md, "Writing chunks") for every model an
engine of the plan serves and the facts know, and named after it, such as `recommended (Qwen/Qwen3-8B-AWQ)`. A recipe
that uses one is made per model too. What the facts refuse is skipped, together with the recipes that need it, and
reported, and so are a served model the facts don't know and a known model no engine serves. Models and engines are
planned first for this reason.

## The World
A World is a directory (docs/inventory.md, "Worlds"). Loading reads its `inventory.toml` for the source of the cases'
vignettes, and takes its `factors.toml`, the engines and models its endpoints serve, with the data set's, and its
`facts.toml`, facts about models the bundled facts don't know, with the bundled ones. So the sample World's fake
engines are loaded only with the sample World, and a World that serves a model of its own brings what is known
about it.

The World is `--world DIR`, or by default the directory `CHATDDX_WORLD` names. The repl reads the same World, for its
endpoints, vignettes and facts.

A loading ends with the inventory checked against the engines just planned, all at once: what starting or reaching
each endpoint would refuse, and what is likely a slip (docs/inventory.md, "Checks happen when an entry is used").

## Loading
```
AGENT: CHANGE
The sample gained free-text-guided and its chunks: 10 more threads.
---
`chatddx init-data USER [--world DIR] [--source NAME] [--giftbag] [--data DIR] [--factors FILE …] [--facts PATH …]`
loads a data set, the sample by default, for the archive, and shares it with USER, who is added when missing. It
connects as the writer and does everything in one transaction. It prints a line for each thing it comes to, and
the sample's first run comes to 258 threads and families.
```
`chatddx init-data USER [--world DIR] [--source NAME] [--giftbag] [--data DIR] [--factors FILE …] [--facts PATH …]`
loads a data set, the sample by default, for the archive, and shares it with USER, who is added when missing. It
connects as the writer and does everything in one transaction. It prints a line for each thing it comes to, and
the sample's first run comes to 248 threads and families.

1. **Plan.** The data set, the World's factors and any more `--factors` are planned into components, without the
   store: references resolved, per-model records written, recipes made per language and compiled, texts and entry
   points checked. A data set that can't be planned is refused before anything is written.
2. **Records.** Each planned record becomes a thread named after it. A record the archive already has, by kind and
   name, is validated when its digest is unchanged and gets a new edit when it changed; a compiled skeleton's edit
   records its compilation. Its tags, description, view labels and language are brought in line with the data.
3. **Cases.** Each case is read from the World's source, by `--source` (`sample`), and adopted into a family named
   after its id, with its tags and its file's language, and gets an expectation thread. A case the source doesn't
   have, or one whose family can't adopt it, is reported, with what a survey of the source says happened to it:
   renamed to or from another id, or changed, and the family repair-data would move.
4. **Leftovers.** The archive's threads and families that the data no longer names are listed, but not deleted.
5. **Sharing.** USER becomes a collaborator on every thread and family the run came to.
6. **Giftbag.** With `--giftbag`, USER also gets a fork of every chunk, tool, skeleton and expectation thread, so
   what has moved on in the archive is proposed to them (docs/catalog.md, "What has moved on"). The forks of the
   expectation threads are also what USER is scored against: without them, the archive's shared expectations score
   nothing for USER. Expectation schemas, scorers, models and engines stay the archive's. A fork they already have is
   kept, and one they deleted comes back, unless they own an expectation of that case under that schema by then: a
   person owns one at most (docs/catalog.md, "Owners"), so theirs is kept instead.
7. **Lints.** Every component the run came to is linted, with the catalog's languages and the facts' reasons, and
   the findings are printed, not stored. For the sample the fake models and engines say they are fake, and without
   `CHATDDX_REVISION` the scorers say their code has no revision.
8. **The World.** The inventory check's findings, and a count.

A tag the archive gave that the data no longer lists is withdrawn; tags people gave stay theirs. Sharing is only
ever added.

Running it again is how a change to the data set is loaded, and how it is checked that the store still holds it: a
second run of an unchanged data set writes nothing and validates every record.

## Repairing
A vignette can be renamed or edited at its source. Its family then needs a repair, which moves it to the vignette's
new place (docs/catalog.md, "Repairing"). Loading only reports this, since a repair also moves the threads of everyone
who used those cases.

`chatddx repair-data [--world DIR] [--source NAME] [--dry-run]` surveys the source and repairs each of the archive's
families it finds renamed or changed there, printing what moved. A family that isn't the archive's is named and left
to its owner. With `--dry-run`, it only lists them.

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
src/chatddx/curation/test/, marked `solidified`.

- `test_plan.py` plans data sets and needs no database.
- `test_init.py` and `test_repair.py` load into a database of their own: a copy of the migrated, empty store, made
  for each test (src/chatddx/conftest.py, `migrated`, `db`). Their vignettes are mostly one line of text each.
  The command test also loads the sample world and Kompismoln's.
- The sample is loaded whole once, by the test that checks it loads cleanly
  (`test_init_data_loads_the_archive`). The tests of loading's mechanics load three of its cases, one of them Swedish
  (src/chatddx/curation/test/sample.py:FEW).
- Even three cases take 0.2 to 2 s a test, since every record of the data set is still written. So every test that
  loads is marked `slow`: 11 of the 24. The quick run (`pytest -m "not slow"`) keeps the planning tests and the pin
  of the vignettes.
- The sample World's vignettes are pinned to the old chatddx at 7893656
  (`test_the_sample_world_holds_the_vignettes_at_7893656`).

`api`, `bench` and `repl` start from the sample as init-data lands it from the sample World, with alice and her giftbag.
It is loaded once per session, and only when one of those tests asks for it (src/chatddx/conftest.py, `curated`).
Each test of the packages whose conftest overrides `template` with `curated` (api, bench, repl) gets a copy of it.
The runner's and the store's tests start from the migrated store, as curation's do.

## Terms

| Term | Meaning |
| --- | --- |
| Curation | Getting authored content into the store as the archive's, keeping it in step with its files, and taking it out of people's way. |
| Archive | The person who owns what a data set loads, and shares it with everyone else. |
| Data set | A directory of authored files: factors, cases by language, and what they load. |
| Record | A named entry of a data set's factors file, loaded as a thread. |
| Per-model record | A record written from each served model's facts, named after the model. |
| Text | A chunk that holds text the model reads, written in a texts file whose name gives its language. |
| Variant | A record made for a language, a model or both, named after them: `plan (en, Qwen/Qwen3-8B-AWQ)`. |
| Giftbag | A person's own forks of the archive's chunks, tools, skeletons and expectations. |
| Leftover | An archive thread or family the data set no longer names. |

## Open design issues

### Garbage collection
Nothing is ever removed from the store, and a leftover is only listed. A collection run as the admin could delete what
nothing refers to: components no thread, family, run or other component reaches, and the catalog rows of what it
deletes. The tiers forbid it on purpose (docs/store.md, "Tiers"), and what counts as unreferenced must include the
ledger and every person's threads, deleted ones too, since history answers questions about the past (docs/catalog.md,
"Deleting").

### Import, export and verification
Curation is the place for the rest of the store's authored content to come and go:
- verifying that the store holds a data set, without writing anything, which a loading's validated lines only do
  inside a transaction that writes;
- exporting what the archive or a person holds back into a data set's files, so a change made in the portal can be
  kept in git;
- importing a data set as someone other than the archive.

### What a data set can't hold yet
Trials, executions, judges, scorings, canary sets, appendices and hand-written skeletons have no tables, and a data
set has one expectation schema. A canary set is the next asked for (agents/wip-runner.md).

### Picking a variant by the case's language
The bench picks a configuration's variant by the model the engine it runs on serves, and by language only when there
is one (src/chatddx/catalog/variants.py). With texts in several languages, the cases a variation runs on should run the
variant in their own language, so a batch of English and Swedish cases runs each under its own. A variant is known
only by its name today; what recording it would take is in agents/wip-variants.md.

### Smaller issues
- **One source a run.** A data set's cases all come from the source `--source` names.
- **Leftovers are listed every run.** Nothing records that a leftover is known and meant to stay.
- **A rename isn't followed into the data.** After repair-data, loading says the old id is missing until the data set
  names the new one.
- **The runner and the engine import don't run the inventory check** that loading does.

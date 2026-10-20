# Curation

Curation loads a data set (init-data), moves families whose vignettes moved (repair-data), and takes a person's share
back (wipe-data). Importing, exporting and verifying the store's content are its business too, and aren't written yet
(docs/backlog.md, "Loading data sets" and "Exporting data sets"). It's the housekeeper for data and a natural home for a
garbage collector (docs/backlog.md, "Garbage collection").

This document describes what curation does and why. The code is `chatddx.curation` (src/chatddx/curation/) and its
commands in src/chatddx/cli.py. Curation builds on the factors, the facts, the inventory, the catalog and the store.

## The archive

The archive is a person, `archive`, created the first time anything is loaded. It owns everything a data set loads: a
thread per stanza, and a family and an expectation thread per case. Whoever it is shared with collaborates on it, and
may be given forks of their own.

Owning the loaded content as a person, rather than as no one, uses the catalog as it is: what a person sees, owns or
forks works the same for the archive's threads as for anyone's. It also tells the data set's version of a thing apart
from a person's: a re-run recognises its own stanzas by kind, name and the archive as owner (docs/modules/catalog.md,
"Names"), and leaves everyone else's alone.

The archive is never wiped.

## Data sets

A data set is a directory of authored files: a `factors.toml`, the texts in `texts-<language>.toml` files, the cases in
`cases-<language>.toml` files, and the files they load, such as JSON schemas.

A data set says what the model reads, the language each text is written in, and the cases it is run on. What a data set
can't hold, engines, which engine judges and which engine its configurations are made for, is its World's
(docs/modules/inventory.md, "Worlds").

A World may carry one beside its vignettes, in `_data/`, which is chatddx's own and so no part of the World
(docs/modules/inventory.md, "Worlds"): `World.load` doesn't read it. `data` is init-data's `--data`, which loads it
unless it names another. Output-types and tool signatures are kept in `schemas/`.

The sample World carries the sample (worlds/sample/_data/), Kompismoln's World loads it with
`--data worlds/sample/_data`.

The test World carries the tests' data set (worlds/test/_data/).

### Factors

Both kinds of file hold one table per kind of component, keyed by name, whose keys are the component's fields
(docs/reference/factors.md).

On top of the fields:

- **References by name.** A toolset's tools, a scorer's expectation schema and a view's judge, a local engine's model a
  `local_model` stanza, and a remote engine's model, a `remote_model` stanza; and a recipe's parts name stanzas, not
  digests.
- **Judges.** A judge names a `recipe`, its `seeds` and its `fill`, and no engine.
- **Files.** `json_schema_path` loads a JSON file, relative to the file that names it, in place of `json_schema`.
- **Forks.** `fork_of` names a stanza of the same kind that this one is a fork of.
- **Code.** A tool or a scorer that names no `version` pins the version of its entry point that the running chatddx
  ships, so loading the data again after a deploy that raises a version moves it on. Its code, and a scorer's views, are
  held to what is shipped (docs/modules/factors.md, "Tool" and "Scorer").
- **Catalog entries.** `tags` and `description` are entries on the stanza's thread, and a scorer view's `label` is a
  label of the edit the scorer is kept with (docs/modules/catalog.md, "Scorer labels"). A tool's `description` is also a
  field, the one the model reads.
- **Intents.** A reasoning chunk may ask for a `level` and a sampling chunk for the `recommended` sampling, worked out
  from the facts when a recipe is compiled (docs/modules/factors.md, "Reasoning" and "Sampling"). A `from_facts` stanza
  is refused: "from_facts is gone; the facts are applied when a recipe is compiled, so ask for a reasoning `level` or a
  `recommended` sampling".
- **Translations by stanza.** A translations stanza's entries may be written in `of`, grouped by the stanza whose texts
  they translate, any stanza of texts (instructions, few-shot, prompt, output, toolset) or a recipe.

A name is defined once per kind: a text is written in one texts file, and only a translations stanza's name comes back
in several, as one chunk (see "Texts"). A data set's `factors.toml` holds no `local_model`, `remote_model`,
`local_engine` or `remote_engine` tables, and a recipe names no `model`: engines are the World's (see "The World"), and
a recipe that names one is refused.

### Texts

A text is written in one language and translated into the others. A text stanza in two texts files, or in `factors.toml`
and a texts file, is refused: "instructions.clinician is in texts-en.toml and texts-sv.toml: a text is written in one
language, and translated into others". A translations stanza is written in the texts file of the language it translates
into, and gives its `entries` or its `of`, and no other field; one in `factors.toml` is refused. Translations stanzas of
one name in several texts files are one chunk, into each file's language (docs/modules/factors.md, "Translations"):
`description` and `fork_of` may be given in any of them, and must agree, and their tags are merged.

The sample is written in English, in `texts-en.toml`. Its `texts-sv.toml` holds only `translations.sample`, into
Swedish: `free-text-guided`'s instructions and worked example, and every text the outputs and the toolset hold, schemas
included. Only `free-text-guided` names it, so it runs on the Swedish cases translated, and the other recipes run on the
English cases, the Swedish ones left out; the sample's translations, set in a variation, carry any of its recipes but
the judges' into Swedish.

### Cases

A cases file holds `[case.<id>]` tables, keyed by the vignette's id at the source. A case has `tags`, entries on its
family, and `targets`, its expectation, which must fit the data set's one expectation schema. A case is in exactly one
file, and the file's name gives its language: every case in `cases-sv.toml` is in Swedish.

Splitting by language rather than tagging each case keeps a language's cases together, as they are sent, scored and
compared together: a case runs in the language it was written in, under the configuration translated into it where that
isn't the configuration's own (docs/modules/catalog.md, "Languages"). Notes in the targets keep a language of their own.

## The World

A World is a directory (docs/modules/inventory.md, "Worlds"). Loading reads its `inventory.toml`, and takes its
`engines.toml` with the data set's factors and its `facts.toml` with the bundled facts. So the sample World's fake
engines are loaded only with the sample World, and a World that serves a model of its own brings what is known about it,
which loading stores for the models its engines serve.

The World is `--world DIR`, or by default the directory `CHATDDX_WORLD` names. The repl reads the same World for its
endpoints and vignettes, and the facts from the store, as loading stored them.

Before it commits, a loading checks what a process checks as it starts (src/chatddx/bench/handles.py:broken): weights
held by several model threads, or served at several endpoints, refuse it, and nothing is written. A loading ends with
the inventory checked against the engines just planned, all at once: what starting or reaching each endpoint would
refuse, and what is likely a slip (src/chatddx/inventory/check.py).

## Loading

`chatddx init-data USER [--world DIR] [--source NAME] [--giftbag] [--data DIR] [--facts PATH …]` loads a data set, the
World's `_data/` unless `--data` names another, for the archive, and shares it with USER, who is added when missing. It
connects as the writer and does everything in one transaction. It prints a line for each thing it comes to.

1. **Plan.** The data set and the World's engines are planned into components, without the store: references resolved,
   the facts about each served model the facts know, recipes made once and compiled for the engine the World names for
   configurations (docs/modules/inventory.md, "Configurations"), and into each language their translations name, judges'
   recipes compiled for their own engines, texts and entry points checked. A data set that can't be planned is refused
   before anything is written. A recipe its translations can't carry into a language is made all the same, and said
   after the stanzas: `[untranslated] recipe asked: no translation into sv for 'You are an emergency physician.'`.
   Neither World's data set gives one.
2. **Stanzas.** Each planned stanza becomes a thread named after it. A stanza the archive already has, by kind and name,
   is validated when its digest is unchanged and gets a new edit when it changed; a compiled skeleton's edit records its
   compilation. Its tags, description, view labels and language are brought in line with the data.
3. **Cases.** Each case is read from the World's source, the one `--source` names or the only one that lists its
   vignettes (a database source lists none), and adopted into a family named after its id, with its tags and its file's
   language, and gets an expectation thread.
4. **Appendices** are bound to the vignette as read, each a thread of the archive's, and each case that sends them is
   stored, with an expectation thread when it has targets. A case the source doesn't have, or one whose family can't
   adopt it, is reported, with what a survey of the source says happened to it: renamed to or from another id, or
   changed, and the family repair-data would move.
5. **Leftovers.** The archive's threads and families that the data no longer names are listed, but not deleted.
6. **Sharing.** USER becomes a collaborator on every thread and family the run came to.
7. **Giftbag.** With `--giftbag`, USER also gets a fork of every chunk, tool, skeleton and expectation thread, so what
   has moved on in the archive is proposed to them (docs/modules/catalog.md, "What has moved on"). The forks of the
   expectation threads are also what USER is scored against: without them, the archive's shared expectations score
   nothing for USER. Expectation schemas, scorers, models, engines and facts stay the archive's. A fork they already
   have is kept, and one they deleted comes back, unless they own an expectation of that case under that schema by then:
   a person owns one at most (docs/modules/catalog.md, "Owners"), so theirs is kept instead.
8. **Lints.** Every component the run came to is linted, with the catalog's languages and the facts' reasons, and the
   findings are printed, not stored. For the sample the fake models and engines say they are fake.
9. **The World.** The inventory check's findings, and a count.

A tag the archive gave that the data no longer lists is withdrawn; tags people gave stay theirs. Sharing is only ever
added.

Running it again is how a change to the data set is loaded, and how it is checked that the store still holds it: a
second run of an unchanged data set writes nothing and validates every stanza.

## Repairing

A vignette can be renamed or edited at its source. Its family then needs a repair, which moves it to the vignette's new
place (docs/modules/catalog.md, "Repairing"). Loading only reports this, since a repair also moves the threads of
everyone who used those cases.

`chatddx repair-data [--world DIR] [--source NAME] [--dry-run]` surveys the source, the one `--source` names or the
World's only directory source, and repairs each of the archive's families it finds renamed or changed there, printing
what moved. A family that isn't the archive's is named and left to its owner. With `--dry-run`, it only lists them.

After a rename, the data set should name the new id; after new content, the expectations stay with the old case until
someone confirms them for the new one (docs/modules/catalog.md, "Repairing"), and the next loading gives the new case an
expectation of its own.

## Wiping

`chatddx wipe-data USER` takes back what a person has: it deletes what they own and withdraws them from what is shared
with them, an entry each, and only where it changes something, so wiping again writes nothing. The person stays. Loading
with `--giftbag` gives it back, restoring the deleted forks rather than forking anew, so a cycle of the two writes an
entry per gift and per share and no thread.

Wiping covers all a person owns, their runs and their own threads included, not only what loading gave them.

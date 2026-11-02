## Compose

Compose is where researchers write a configuration from its building blocks, its texts and settings, the evolution of
configurations (`docs/chatddx.md`, "Intended evolution of configurations").

Drafted: `/compose/{id}` (`src/chatddx/portal/compose.py`; `src/chatddx/portal/test/test_compose.py`) is where a
configuration is written and saved, and `/compose` leads to the first in the list. In its address is the variation's
query (`schemas.Varying`, its parts, `head`, `under`, `tag`).

- **Configurations**, always shown: the person's own of generation, flat, by name, as Review runs a case under
  (`src/chatddx/portal/pages.py:configurations`); no archive's, no lineage.
- **The configuration**: its name, with **Show in the Library** across from it, as Review's case is; its versions by
  link; **Update** it where it is behind what it was made from; and its island (`frontend/src/islands/compose.ts`),
  which writes its chunks in place rather than picking them:
  - **Its texts**: a tab in its own language with the chunks that hold text, an output's and a toolset's guidance among
    them, and a tab for each language it is translated into, each text beside its translation
    (`frontend/src/lib/compose/Texts.svelte`). As a text is typed, `POST /api/threads/{id}/drafts` says the texts the
    draft holds and carries each translation over to the text it changed into, in place and in order
    (`src/chatddx/factors/request.py:remapped`).
  - **Its settings**: the model, picked, and the chunks that hold no text, each by its schema's form
    (`frontend/src/lib/compose/Settings.svelte`): sampling, reasoning, passthrough, and an output's and a toolset's
    structure.
  - **Save**: `POST /api/threads/{id}/saves` (`src/chatddx/bench/composing.py:compose`) writes, in one transaction, each
    chunk that changed to the thread its own came from, a version where that is the person's and else a fork under its
    name, and then the configuration, as a version or a fork; a fork of the configuration forks the chunks it changes. A
    chunk held by no thread starts one named after the configuration and the part. Tags stay the Library's.

Nothing is run from Compose: a configuration runs on a case in Review, and a trial of it from the Library through
`/lab/run` (`src/chatddx/portal/starting.py`), the portal's, which keeps the Lab's address for now.

A judge's configuration is written and saved there too.

# Refine: plan

### Edit history: who, when and why
Who changed an entry, a label or a language, and when, shown; and why an edit was made, kept.

Decided: an edit may carry an optional note, stored with it as a commit message is; what changed stays derived from the
references.

- **Who changed an entry or a language isn't shown.** Every row records who wrote it and when, but for these only
  what holds now is shown.
- When an entry, a label or a language was written isn't given, nor who wrote a label or a language:
  `Reader.entries` gives an entry's writer only.
- **Why an edit was made isn't stored.** It can be worked out by comparing consecutive versions' references.
- Why an edit was made isn't stored.

### Following a part that moved on
A configuration offered the new version of a chunk of its recipe, as it is offered its facts' and its model's.

- **Only the facts and the model are followed.** The catalog lists every part of a configuration's recipe whose
  thread has moved on (`src/chatddx/catalog/threads.py:behind`), but the bench follows `/facts` and `/recipe/model`
  only (`src/chatddx/bench/following.py:_moved`), so a new version of a chunk, a translator's translations among them,
  reaches a configuration only by a variation that picks it, saved.

# Curation

Loading a data set into the store as the :Archive's, and keeping it in step with its files and its vignettes' sources.
<<<<<<< signed
`chatddx init-data` plans a data set's factors, texts and cases with its World's engines and facts
(`src/chatddx/curation/plan.py:plan_factors`, `src/chatddx/curation/plan.py:load_cases`), writes each stanza as a thread
of the archive's and shares them with a person (`src/chatddx/curation/write.py:init`); `chatddx repair-data` moves the
archive's families whose vignettes were renamed or changed at their source (`src/chatddx/curation/repair.py:repair`);
and `chatddx wipe-data` deletes what a person owns and unshares what they collaborate on
(`src/chatddx/curation/write.py:wipe`). It writes through the store, under the catalog's checks as any writer is.
=======
`chatddx sync-archive`, run by each deploy after the migrations, plans a data set's factors, texts and cases with its
World's engines and facts (`src/chatddx/curation/plan.py:plan_factors`, `src/chatddx/curation/plan.py:load_cases`),
writes each stanza as a thread of the archive's, prunes what the archive holds that the data no longer does, and shares
what it holds with each person it is shared with already (`src/chatddx/curation/write.py:sync`); `chatddx person
provision <login>`, run by hand for a new person or again for one there is, shares what the archive holds with them and
gives them the giftbag (`src/chatddx/curation/write.py:provision`); `chatddx repair-data` moves the archive's families
whose vignettes were renamed or changed at their source (`src/chatddx/curation/repair.py:repair`); and `chatddx
wipe-data` deletes what a person owns and unshares what they collaborate on (`src/chatddx/curation/write.py:wipe`). It writes through the store, under the catalog's checks as any writer is.
>>>>>>> @stamp

A case's vignette is sensitive: curation reads it at its source only to fingerprint it, and keeps the fingerprint, not
the text.
<<<<<<< signed
=======

## Syncing and provisioning

Built: a sync prunes, deletes and unshares, what the archive holds and the data doesn't: a stanza, a case's family, an
appendix, an expectation. It leaves alone what the data names that it can't write this time: an appendix or an
expectation of a case missing at its source or waiting for repair-data, and a stanza this World can't plan. What comes
back to the data comes back as it was, the thread it pruned restored, its forks' origin with it. A case of appendices
the archive pruned leaves every person's case list, as an appendix they can't see doesn't branch it.

Built: a provision shares what the archive holds, then gives the person a fork of each chunk, tool, skeleton and
expectation they have none of: one they have is kept as it is, one they deleted stays deleted, and, for an expectation,
one of their own of its case keeps theirs. What is new in the archive since is given.
>>>>>>> @stamp

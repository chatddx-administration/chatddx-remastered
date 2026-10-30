# Curation

Loading a data set into the store as the :Archive's, and keeping it in step with its files and its vignettes' sources.
`chatddx init-data` plans a data set's factors, texts and cases with its World's engines and facts
(`src/chatddx/curation/plan.py:plan_factors`, `src/chatddx/curation/plan.py:load_cases`), writes each stanza as a thread
of the archive's and shares them with a person (`src/chatddx/curation/write.py:init`); `chatddx repair-data` moves the
archive's families whose vignettes were renamed or changed at their source (`src/chatddx/curation/repair.py:repair`);
and `chatddx wipe-data` deletes what a person owns and unshares what they collaborate on
(`src/chatddx/curation/write.py:wipe`). It writes through the store, under the catalog's checks as any writer is.

A case's vignette is sensitive: curation reads it at its source only to fingerprint it, and keeps the fingerprint, not
the text.

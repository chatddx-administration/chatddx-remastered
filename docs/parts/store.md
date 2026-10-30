# Store

What chatddx keeps, in PostgreSQL 16: the components by digest and the ledger's records
(`src/chatddx/store/store.py:Store`), the catalog's rows (`src/chatddx/store/catalog.py:Rows`,
`src/chatddx/store/catalog.py:Catalog`), people, their passwords and sessions (`src/chatddx/store/people.py:People`),
the texts people type as vignettes (`src/chatddx/store/texts.py:Texts`), and the worker's queue
(`src/chatddx/store/queue.py:Queue`) with the notifications that tell of it and of runs (`src/chatddx/store/notify.py`).
Its schemas are migrated by :Tier as the :Admin (database) (`src/chatddx/store/migrate.py:migrate`), each listed in
docs/migrations.md, and the app connects as the :Writer.

The store is sensitive: the ledger's records, the typed vignettes, the notifications and a job's reasons can hold
sensitive content. It is cleared by definition until the clearance pipeline exists (docs/chatddx.md, "Vignettes and
anything made from them are sensitive").

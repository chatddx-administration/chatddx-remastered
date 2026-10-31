# Store

What chatddx keeps, in PostgreSQL 16: the components by digest and the ledger's records
(`src/chatddx/store/store.py:Store`), the catalog's rows (`src/chatddx/store/catalog.py:Rows`,
`src/chatddx/store/catalog.py:Catalog`), people, their passwords and sessions (`src/chatddx/store/people.py:People`),
the texts people type as vignettes (`src/chatddx/store/texts.py:Texts`), and the worker's queue
(`src/chatddx/store/queue.py:Queue`) with the notifications that tell of it and of runs (`src/chatddx/store/notify.py`).
Its schemas are migrated by :Tier as the :Admin (database) (`src/chatddx/store/migrate.py:migrate`), each listed in
docs/migrations.md, and the app connects as the :Writer.

The components, the catalog's rows and the ledger's records are insert-only, as the schemas' triggers have it, so what
is read of them can be held (`src/chatddx/store/cache.py:Cache`): per process, database and key, once read outside a
transaction, the least recently used let go. A component is held without a version: `Store.get` and `Store.load` read it
from the database once. What is read of the catalog is held under the catalog's version, which each transaction that
writes to it bumps as it commits (`src/chatddx/store/cache.py:catalogued`), and read again once it has moved on: the
threads `GET /api/threads` lists (`src/chatddx/api/threads.py:_THREADS`). A finished run or score is held without a
version too, as its finished record seals what was written before it: `Store.run` and `Store.score` read one from the
database once, one not finished every time.

The store is sensitive: the ledger's records, the typed vignettes, the notifications and a job's reasons can hold
sensitive content. It is cleared by definition until the clearance pipeline exists (docs/chatddx.md, "Vignettes and
anything made from them are sensitive").

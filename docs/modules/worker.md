# Worker

The :Worker claims the runs queued for it (`src/chatddx/store/queue.py:Queue.claim`) and works each :Job on a thread of
its own: it sends or resumes the run through its owner's bench, then scores it when asked, scorer by scorer
(`src/chatddx/worker/worker.py:Worker`). It runs as `chatddx worker`, or in `chatddx run` beside the portal, with up to
`src/chatddx/settings.py:WORKER_JOBS` jobs and no more at an endpoint than its capacity. Stopped, it ends its runs after
the items under way and its scorings at `src/chatddx/settings.py:WORKER_DEADLINE`, and queues them again.

What a run's items and judges say as they stream is published over the store's notifications for the API to follow
(`src/chatddx/worker/publish.py:Publisher`), and is sensitive, as the responses are.

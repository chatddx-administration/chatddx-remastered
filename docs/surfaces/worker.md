# `chatddx.worker`

Written by `chatddx stamp` from `src/chatddx/worker/`; how to read it is in [docs/surfaces/README.md](README.md).

## `EVERY`
`src/chatddx/worker/publish.py:EVERY`

`EVERY = 0.1`

## `LEFT`
`src/chatddx/worker/worker.py:LEFT`

`LEFT = "its worker stopped"`

## `publish.log`
`src/chatddx/worker/publish.py:log`

`log = logging.getLogger(__name__)`

## `worker.log`
`src/chatddx/worker/worker.py:log`

`log = logging.getLogger(__name__)`

## `PAUSED`
`src/chatddx/worker/worker.py:PAUSED`

`PAUSED = "paused"`

## `Publisher`
`src/chatddx/worker/publish.py:Publisher`

## `Publisher.__init__`
`src/chatddx/worker/publish.py:Publisher.__init__`

* `conn: Connection`
* `run: UUID`

## `Publisher.close`
`src/chatddx/worker/publish.py:Publisher.close`

* ∟`None`

## `Publisher.put`
`src/chatddx/worker/publish.py:Publisher.put`

* `said: Named`
* ∟`None`

## `Publisher.run_event`
`src/chatddx/worker/publish.py:Publisher.run_event`

* `event: RunEvent`
* ∟`None`

## `Publisher.scoring_event`
`src/chatddx/worker/publish.py:Publisher.scoring_event`

* `event: ScoringEvent`
* ∟`None`

## `Worker`
`src/chatddx/worker/worker.py:Worker`

* `id: UUID`

## `Worker.__init__`
`src/chatddx/worker/worker.py:Worker.__init__`

* `conninfo: str`
* `inventory: Inventory`
* `beat: timedelta = settings.WORKER_BEAT`
* `lost: timedelta = settings.WORKER_LOST`
* `deadline: timedelta = settings.WORKER_DEADLINE`

## `Worker.serve`
`src/chatddx/worker/worker.py:Worker.serve`

* `stopping: threading.Event`
* ∟`None`

## `Worker.wake`
`src/chatddx/worker/worker.py:Worker.wake`

* ∟`None`

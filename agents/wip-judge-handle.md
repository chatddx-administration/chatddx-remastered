# Judge handles: work in progress

## Taken from the backlog

### Judges name a model
A judge names a model, as a recipe does, rather than an engine: its calls go to the endpoint serving that model,
picked as a run's endpoint is (see "Picking an endpoint for a model"), and the engine they went to is pinned with the
score, as a trial pins a run's. It changes the judge's kind, so it is cheapest before real scores are stored.

Decided: a judge's model is picked by handle, and its engine is the handle's latest.

Take: judges name model handles, as recipes do. The section becomes "Judges name a handle":

A judge's model is picked by its handle, such as `qwen3-8b`, as a recipe's is: the judge pins the weights, and its
calls go to the endpoint ops map the handle to, at its latest engine, which the scoring pins. A handle that doesn't
resolve to one endpoint refuses the scoring as ops' error, and a judge whose weights the handle no longer holds is
behind, and doesn't judge under it until followed.

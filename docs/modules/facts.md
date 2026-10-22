# Facts

The :Facts about models as people write them, in TOML, and the lints that read them. `src/chatddx/facts/models.py:Facts`
loads the bundled ones (`src/chatddx/facts/models.toml`) with a World's and any others named, refusing a model with
facts in more than one file. `src/chatddx/facts/lint.py:lints` adds to the factors' lint the checks of each trial's and
judge's skeleton against its model's facts, the `facts.*` findings among them. What facts are written as is the factors'
(`src/chatddx/factors/facts.py:ModelFacts`), which this package re-exports.

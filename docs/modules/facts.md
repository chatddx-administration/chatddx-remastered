# Facts

The :Facts about models as people write them, in TOML, and the lints that read them. `src/chatddx/facts/models.py:Facts`
loads the bundled ones (`src/chatddx/facts/models.toml`) with a World's and any others named: a World's facts about a
model take the place of the bundled ones, and a model with facts in more than one file besides the bundled one is
refused. The engines a World plans narrow the facts about the model they serve where every one of them, a vLLM 0.24,
does (`Facts.served`): the context to the longest `--max-model-len` they serve, and no thinking budget where none has a
reasoning parser.

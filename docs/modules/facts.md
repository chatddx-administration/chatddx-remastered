# Facts

The :Facts about models as people write them, in TOML, and the lints that read them. `src/chatddx/facts/models.py:Facts`
loads the bundled ones (`src/chatddx/facts/models.toml`) with a World's and any others named: a World's facts about a
model take the place of the bundled ones, as its engines may serve the model otherwise, and a model with facts in more
than one file besides the bundled one is refused.

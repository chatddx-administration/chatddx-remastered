# Test

The names tests share are spelled once in `src/chatddx/test/world.py`, with a World on free ports and its fakes served
(`src/chatddx/test/world.py:faked`); `src/chatddx/test/helpers.py` holds the fixtures tests share, and the databases
copied ahead from templates (`src/chatddx/test/helpers.py:Copies`); and `src/chatddx/test/budget.py` is the pytest
plugin `check.sh` runs with, which weighs the slow budget and says which tests to mark slow and which to unmark. Its own
tests check the Worlds in `worlds/` and the tests themselves (`src/chatddx/test/test_tests.py`).

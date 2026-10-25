# Test

The names tests share are spelled once in `src/chatddx/test/world.py`, with a World on free ports and its fakes served
(`src/chatddx/test/world.py:faked`); `src/chatddx/test/helpers.py` holds the fixtures tests share, and the databases
copied ahead from templates (`src/chatddx/test/helpers.py:Copies`); and `src/chatddx/test/budget.py` is the pytest
plugin `check.sh` runs with, on 4 workers, which weighs the slow budget as a run in one process would, a test's wait for
its database left out, and says which tests are far enough off the cut to mark slow and which to unmark. Its own
tests check the Worlds in `worlds/` and the tests themselves (`src/chatddx/test/test_tests.py`).

# Comments in `chatddx.test`

Written by `chatddx stamp write` from the comments in `src/chatddx/test/`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now, till it is stamped.

## `src/chatddx/test/budget.py:Budget.pytest_fixture_setup`

```
# Policy: a fixture wider than a test is set up for every test after it, so the one
# that happens to set it up isn't charged for it; nor is the last test for the
# session's teardown.
```

## `src/chatddx/test/budget.py:Budget.pytest_runtest_makereport`

```
# Accommodating for pytest-xdist, whose workers run the tests and set up the fixtures
# while the controller sums the reports: what the budget weighs rides on them.
```

## `src/chatddx/test/budget.py:MARGIN`

```
# Policy: a test's time varies from run to run, and more so beside other workers, so only
# one off from the cut by this factor is worth marking or unmarking.
```

## `src/chatddx/test/budget.py:WAITED`

```
# Dependency: src/chatddx/conftest.py:db takes a copy made ahead on Copies' threads, so
# waiting for it weighs the copying, which falls behind beside other workers, not the test.
```

## `src/chatddx/test/helpers.py:_settled`

```
# Accommodating for PostgreSQL: a session closed a moment ago may still be ending on the
# server, and neither a template's copy nor DROP ... WITH (FORCE) waits for it: FORCE
# may not end a session of DB_USER's as DB_ADMIN.
```

## `src/chatddx/test/helpers.py:Copies`

```
# Optimization: copies of a template are made ahead and dropped behind, on threads of
# their own, so that a test waits for its database only when they fall behind.
```

## `src/chatddx/test/helpers.py:Copies.forget`

```
# Dependency: before the template itself is dropped.
```

## `src/chatddx/test/helpers.py:curated_template`

```
# Accommodating for pytest, which takes the fixtures a conftest or a test module
# imports: these are the variants several of them take, each listed in its __all__ so
# that linters see the import used.
```

## `src/chatddx/test/helpers.py:drop_database`

```
# Accommodating for a run's or a scoring's job, which outlives the request that started
# it, and may connect again between settling and dropping after its test has ended.
```

## `src/chatddx/test/helpers.py:needs_git`

```
# Accommodating for nix's sandbox, which checks the package without git.
```

## `src/chatddx/test/helpers.py:one_attempt`

```
# Dependency: `admin` is a conninfo taken before any test runs, since tests point
# DB_NAME at their own database.
```

## `src/chatddx/test/test_sample.py:test_the_sample_uses_every_table_a_data_set_and_a_world_hold`

```
# Policy: the sample is the example a new World follows, so it uses everything a data
# set and a World can hold at least once.
```

## `src/chatddx/test/test_tests.py:GAP`

```
# Accommodating for the repl's tables: rich puts 3 spaces or more between columns, the
# repl's own layouts 2.
```

## `src/chatddx/test/test_tests.py:LINES`

```
# Accommodating for a regex's newline, written as the two characters \n.
```

## `src/chatddx/test/test_tests.py:parsed`

```
# Optimization: parsed once for the tests that read them, as a fixture, so that the slow
# budget weighs it as set up for many rather than charging whichever test parses first.
```

## `src/chatddx/test/test_tests.py:WORD`

```
# Accommodating for plain words, which name other things too: a kind (judge), a level (off).
```

## `src/chatddx/test/test_worlds.py:UNCONSTRAINED`

```
# Dependency: the lint says harmony and Mistral models take tools unconstrained where
# vLLM refuses others.
```

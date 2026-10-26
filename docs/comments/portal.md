# Comments in `chatddx.portal`

Written by `chatddx stamp write` from the comments in `src/chatddx/portal/`, sorted by file and then by name whatever its case:

````
## `<file>:<the name it is in or right above>`

```
<the comment, as written>
```
````

- A comment in or above no name is under its file alone, and comments on lines one after another are one.
- A stamp pending is a git conflict, from `<<<<<<< signed` to `=======` as last stamped and on to the `>>>>>>>` closing it as written now: a human stamps it.

## `src/chatddx/portal/cases.py:building`

```
# Policy: a page that builds a case is given it back as `case` in its address.
```

## `src/chatddx/portal/editors.py:_FORMED`

```
# Policy: a field earns its schema's form where what it holds is shaped by the schema;
# one that holds whatever a request or a template takes, or mostly whitespace, is
# clearer as JSON.
```

## `src/chatddx/portal/fields.py:_engines`

```
# Policy: an engine is picked by its model's handle, as researchers see handles, not
# engines.
```

## `src/chatddx/portal/fields.py:_given`

```
# Accommodating for browsers, which send a textarea's line breaks as CRLF.
```

## `src/chatddx/portal/fields.py:listed`

```
# Accommodating for the API, which lists configurations of one purpose at a time.
```

## `src/chatddx/portal/lab.py:_columns`

```
# Policy: Configurations that send the set's cases as the same skeletons under the same
# handle share a column, as a fork that varies nothing does its origin's.
```

## `src/chatddx/portal/lab.py:_FARING`

```
# Accommodating for the variation's query, whose schema refuses what it doesn't know: the
# Lab's own parameters are taken out of the address before it is read.
```

## `src/chatddx/portal/lab.py:_trials`

```
# Policy: a trial is the configuration's when its skeleton is one of its versions, or
# compiled from the recipe of one into a language.
```

## `src/chatddx/portal/pages.py`

```
# Accommodating for Jinja, whose tojson sorts keys: an island sends back what it's given,
# and a component's digest holds the order of its keys.
```

```
# pyright: ignore[reportAttributeAccessIssue, reportUnknownMemberType]
```

```
# Accommodating for Jinja, whose globals are typed as its own defaults are.
```

## `src/chatddx/portal/pages.py:refusable`

```
# Policy: what a person can set right on the page they sent, which shows it again with
# what they typed and why it was refused; the rest is answered as the API answers it.
```

## `src/chatddx/portal/pages.py:refusal_of`

```
# Policy: what a person can cause is worded, and what isn't worded they couldn't have
# caused, so it is passed on as it is.
```

## `src/chatddx/portal/pages.py:signing_in`

```
# Policy: a sign-in passes by the sign-in page once more, which sends the person on if
# their browser kept the session's cookie and says so if it didn't.
```

## `src/chatddx/portal/runs.py:halting`

```
# Policy: as with pressed, a run with nothing left under way is halted already.
```

## `src/chatddx/portal/runs.py:pressed`

```
# Policy: a press made while something is under way for its run, from a second tab, a
# stale page or a second click, counts as made: the page it leads back to says so.
```

## `src/chatddx/portal/runs.py:run`

```
# Accommodating for a job ending once its run's rows are written: asked before the run
# is read.
```

## `src/chatddx/portal/shelves.py:AUTHORED`

```
# Accommodating for configurations, which a person writes as recipes, not as components.
```

## `src/chatddx/portal/shelves.py:IN_WORLD`

```
# Dependency: the cards of src/chatddx/portal/templates/world.html, by the kinds they
# show.
```

## `src/chatddx/portal/test/conftest.py:paged`

```
# Accommodating for signed's client, which runs the app's lifespan and its worker: this one
# shares them, so it is never entered.
```

## `src/chatddx/portal/test/conftest.py:pytest_collection_modifyitems`

```
# Policy: a browser test starts a browser, so it runs only when asked for by its mark.
```

## `src/chatddx/portal/test/helpers.py:_Submitted`

```
# Accommodating for what a browser sends of a form: a select's chosen option, else its
# first, a checkbox only when checked, and a textarea's text without the line break that
# follows its opening tag.
```

## `src/chatddx/portal/test/helpers.py:ran_template`

```
# Accommodating for pytest, as src/chatddx/test/helpers.py:curated_template does.
```

## `src/chatddx/portal/test/test_browser.py:portal`

```
# Accommodating for a browser, which keeps the __Host- session cookie over plain HTTP
# only on localhost.
```

## `src/chatddx/portal/test/test_browser.py:test_a_press_shows_until_the_next_page_comes_and_sends_its_form_once`

```
# Accommodating for Chromium, which runs no script on a page while a navigation from it is held:
# the navigations a press starts are cancelled instead, which leaves the page as pressed.
```

## `src/chatddx/portal/threads.py:_drawn`

```
# Policy: a new trial is begun with what a start of a variation takes when none is
# given.
```

## `src/chatddx/portal/threads.py:_editable`

```
# Policy: an expectation stays of the case and the schema it was written for; Review
# carries it to a case that replaces its own.
```

## `src/chatddx/portal/threads.py:_shipped`

```
# Policy: a new scorer pins the code chatddx ships, as it is shown and not asked.
```

## `src/chatddx/portal/translations.py:_NEAR`

```
# Policy: an entry under half of whose words are the text's is too far off to start from.
```

## `src/chatddx/portal/translations.py:posted`

```
# Accommodating for browsers, which send a textarea's line breaks as CRLF.
```

## `src/chatddx/portal/world.py:_sent`

```
# Dependency: what src/chatddx/factors/request.py:compile_request sends of a level's
# writes.
```

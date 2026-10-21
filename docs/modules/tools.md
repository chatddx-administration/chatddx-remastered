```
AGENT: write
The module doc of tools, now solidified (AGENTS.md, "Development stages"). Each section is its own suggestion.
---
# Tools

The tool code chatddx ships, which a tool pins by entry point and version (docs/modules/factors.md, "Tool"). Running a
skeleton's tools in an item's rounds is the runner's (docs/modules/runner.md, "Tool rounds").

This document describes the code `chatddx.tools` (src/chatddx/tools/). Its surface is `docs/surfaces/tools.md`.
```

```
AGENT: write
What is shipped, and what a shipped tool promises.
---
## Shipped tools

`TOOLS` holds what is shipped, each entry point with its version and function (src/chatddx/tools/shipped.py:TOOLS):
one today, `chatddx.tools.web_search:web_search`, at version 1, which the sample's `web_search` tool pins. A tool is
called with the model's arguments as keywords, once they fit its parameters, and gives back text. Its developers raise
its version when what it gives back changes, which makes it a new tool, so a new skeleton and a new trial
(docs/modules/factors.md, "Code").

The test World's tools are the runner's test tools, shipped for the tests only
(src/chatddx/conftest.py:shipped_test_tools).
```

```
AGENT: write
The web search: what it asks of whom, and what it gives back.
---
## Web search

`web_search` asks DuckDuckGo's HTML search (`SEARCH_URL`) for the model's query, as `USER_AGENT` and within 10 seconds,
and gives back up to `max_results` results, 5 unless the model asks for another number: each numbered, with its title,
URL and snippet. A result's URL is the one DuckDuckGo's redirect leads to. Without results it says so. It fails as
urllib does, and the model is then told the error (docs/modules/runner.md, "Tool rounds"). `results` reads a page, so
that reading one is tested without the network.

It hands the model's query to a third party, which answers differently from day to day: what it returned is recorded per
run, an observed factor (docs/modules/factors.md, "Tool"). A tool can't be cleared yet, so the gate refuses a run with
tools on a sensitive source (docs/modules/runner.md, "The gate"; agents/wip-clearance.md, "Tools"). It goes through the
proxy its environment names, as the engine client does.
```

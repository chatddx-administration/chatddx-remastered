# Tools

The code chatddx ships for the tools a model may call between rounds, each by its entry point and version
(`src/chatddx/tools/shipped.py:TOOLS`): a :Tool pins one, and the runner runs it. One ships, `web_search`, which asks
DuckDuckGo and answers its first results as text (`src/chatddx/tools/web_search.py:web_search`).

A tool's arguments are written by the model from the case, and its results are kept in the ledger, so both are
sensitive. A tool that sends them off the host hands them to a third party, so the gate refuses tools on a sensitive
source until a tool can be cleared (agents/wip-clearance.md, "Tools").

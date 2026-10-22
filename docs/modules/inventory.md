# Inventory

Where one deployment's world is. A :World is a directory holding an :Inventory, the engines and model facts it adds, and
the data carried with it (`src/chatddx/inventory/world.py:World`). The inventory names the vignette sources, a directory
or the texts people type (`src/chatddx/inventory/sources.py:Source`), the endpoints, the hosts that run local engines,
and for now which endpoints are cleared for which sources, which handle each judge is bound to and which handle
configurations are made for (`src/chatddx/inventory/inventory.py:Inventory`). It is checked against the engines its
endpoints serve (`src/chatddx/inventory/check.py:check`), and says what starting a local engine's endpoint takes
(`src/chatddx/inventory/serving.py:start_up`).

A source is sensitive unless it says otherwise, and a directory source reads its vignettes from disk
(`src/chatddx/inventory/sources.py:DirectorySource.fetch`). An endpoint not :Cleared for a sensitive source is refused
its cases (agents/wip-clearance.md, "Vetted endpoints").

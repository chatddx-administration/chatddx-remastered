# Importers

Reading what lies outside chatddx's control into a World's files. There is one, the :Engine import:
`chatddx import-engine` reads o11n's reports of the vLLM servers on a host, by URL or file
(`src/chatddx/importers/o11n.py:read`), makes a model, an engine, an endpoint and a host of each server
(`src/chatddx/importers/o11n.py:imported`), and writes them whole as an engines file and an :Include
(`src/chatddx/importers/o11n.py:engines_toml`, `src/chatddx/importers/o11n.py:endpoints_toml`), with the findings of
checking them as an inventory (`src/chatddx/importers/o11n.py:checked`).

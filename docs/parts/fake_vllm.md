# The fake vLLM

`chatddx.fake_vllm` stands in for vLLM 0.24 where no real one runs: the tests, the Worlds' fake engines and stand-ins
(`chatddx fake-engines`) and the scripted runs. It serves vLLM's chat completions, streamed or not, and its
`/v1/models`, `/health` and `/version` (`src/chatddx/fake_vllm/server.py:server`), set up by `vllm serve`'s own flags
(`src/chatddx/fake_vllm/served.py:Served.of`), and refuses what vLLM refuses, with vLLM's errors
(`src/chatddx/fake_vllm/chat.py:check`). It answers with made-up diagnoses or an instance of the schema or tool it is
held to (`src/chatddx/fake_vllm/chat.py:respond`), or with the next turn of a :Script
(`src/chatddx/fake_vllm/chat.py:scripted`). What it pins of vLLM is in docs/vllm.md.

It is sent sensitive content as an engine is, and keeps and logs none of it.

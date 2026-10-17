import pytest

from chatddx.fake_vllm.served import Served
from chatddx.fake_vllm.server import serving
from chatddx.inventory import start_up
from chatddx.runner.gate import Refused, admit
from chatddx.test.world import GPT_OSS, QWEN, free_world, world_plan


def test_an_endpoint_is_confirmed_by_the_name_its_server_lists() -> None:
    inventory = free_world()
    get = world_plan().registry.get
    at = inventory.endpoint(GPT_OSS).model_copy(
        update={"url": inventory.endpoint(QWEN).url}
    )
    inventory = inventory.model_copy(
        update={"endpoints": {**inventory.endpoints, GPT_OSS: at}}
    )
    qwen, gpt_oss = (inventory.endpoint(n).engine for n in (QWEN, GPT_OSS))
    startup = start_up(inventory, get, QWEN)
    with serving([Served.of(startup.argv[0], startup.argv[1:])]):
        assert admit(inventory, get, QWEN, qwen, (), False, "trial") is None
        with pytest.raises(Refused, match=f"serves {qwen} at .*, not {gpt_oss}"):
            _ = admit(inventory, get, GPT_OSS, gpt_oss, (), False, "trial")
    with pytest.raises(Refused, match=f"endpoint '{QWEN}' can't be confirmed"):
        _ = admit(inventory, get, QWEN, qwen, (), False, "trial", timeout=1.0)

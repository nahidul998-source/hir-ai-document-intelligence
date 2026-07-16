import os
import pytest
from app.infrastructure.adapters.ai_provider_manager import AIProviderManager


@pytest.fixture
def manager():
    # Construct relative path to the existing config file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(test_dir, "../../configs/ai.yaml")
    return AIProviderManager(config_path)


@pytest.mark.asyncio
async def test_fallback_sequence_all_healthy(manager):
    # Ensure all providers are active & healthy
    for key in manager.priority:
        manager.set_provider_health(key, True)

    # First priority is local_qwen
    active = await manager.get_active_provider()
    assert active.name == "local_qwen"

    # Execution returns local Qwen mock
    res = await manager.generate_json("test prompt", {})
    assert res["provider"] == "local_qwen"


@pytest.mark.asyncio
async def test_fallback_sequence_local_unhealthy(manager):
    # Set local_qwen unhealthy
    manager.set_provider_health("local_qwen", False)
    manager.set_provider_health("github", True)
    manager.set_provider_health("gemini", True)

    # Fallback to github (second priority)
    active = await manager.get_active_provider()
    assert active.name == "github"

    res = await manager.generate_json("test prompt", {})
    assert res["provider"] == "github"


@pytest.mark.asyncio
async def test_fallback_sequence_local_and_github_unhealthy(manager):
    # Set local_qwen and github unhealthy
    manager.set_provider_health("local_qwen", False)
    manager.set_provider_health("github", False)
    manager.set_provider_health("gemini", True)

    # Fallback to gemini (third priority)
    active = await manager.get_active_provider()
    assert active.name == "gemini"

    res = await manager.generate_json("test prompt", {})
    assert res["provider"] == "gemini"


@pytest.mark.asyncio
async def test_fallback_exhausted(manager):
    # Set all providers unhealthy
    for key in manager.priority:
        manager.set_provider_health(key, False)

    with pytest.raises(RuntimeError, match="No healthy AI Providers are available"):
        await manager.get_active_provider()

    with pytest.raises(RuntimeError, match="AI Generation failed. All configured fallback providers failed"):
        await manager.generate_json("test prompt", {})

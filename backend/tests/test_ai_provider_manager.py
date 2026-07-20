import os
import pytest
from unittest.mock import AsyncMock, patch
from app.infrastructure.adapters.ai_provider_manager import AIProviderManager

@pytest.fixture
def manager():
    # Construct relative path to the existing config file
    test_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(test_dir, "../../configs/ai.yaml")
    m = AIProviderManager(config_path)
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    loop.run_until_complete(m.initialize())
    return m

def set_provider_health(manager, key: str, healthy: bool):
    """Helper to mock health checks for testing."""
    if key in manager.providers:
        # Patch the is_healthy method of the provider instance
        manager.providers[key].is_healthy = AsyncMock(return_value=healthy)

def set_provider_output(manager, key: str, output: dict, fail: bool = False):
    """Helper to mock generate_json for testing."""
    if key in manager.providers:
        if fail:
            manager.providers[key].generate_json = AsyncMock(side_effect=RuntimeError("Provider failed"))
        else:
            manager.providers[key].generate_json = AsyncMock(return_value=output)

@pytest.mark.asyncio
async def test_fallback_sequence_all_healthy(manager):
    # Ensure all providers are active & healthy
    for key in manager.priority:
        set_provider_health(manager, key, True)
        set_provider_output(manager, key, {"provider": key})

    # First priority is local_qwen
    active = await manager.get_active_provider()
    assert active.name == "local_qwen"

    # Execution returns local Qwen mock
    res = await manager.generate_json("test prompt", {})
    assert res["provider"] == "local_qwen"


@pytest.mark.asyncio
async def test_fallback_sequence_local_unhealthy(manager):
    # Set local_qwen unhealthy
    set_provider_health(manager, "local_qwen", False)
    set_provider_health(manager, "github", True)
    set_provider_health(manager, "gemini", True)
    
    set_provider_output(manager, "github", {"provider": "github"})

    # Fallback to github (second priority)
    active = await manager.get_active_provider()
    assert active.name == "github"

    res = await manager.generate_json("test prompt", {})
    assert res["provider"] == "github"


@pytest.mark.asyncio
async def test_fallback_sequence_local_and_github_unhealthy(manager):
    # Set local_qwen and github unhealthy
    set_provider_health(manager, "local_qwen", False)
    set_provider_health(manager, "github", False)
    set_provider_health(manager, "gemini", True)

    set_provider_output(manager, "gemini", {"provider": "gemini"})

    # Fallback to gemini (third priority)
    active = await manager.get_active_provider()
    assert active.name == "gemini"

    res = await manager.generate_json("test prompt", {})
    assert res["provider"] == "gemini"

@pytest.mark.asyncio
async def test_fallback_during_generation_failure(manager):
    # Set all healthy, but local_qwen fails during generation (e.g. timeout or invalid JSON)
    for key in manager.priority:
        set_provider_health(manager, key, True)
        set_provider_output(manager, key, {"provider": key})
        
    set_provider_output(manager, "local_qwen", {}, fail=True)

    # get_active_provider will return local_qwen because it's healthy
    active = await manager.get_active_provider()
    assert active.name == "local_qwen"
    
    # but generate_json should fallback to github
    res = await manager.generate_json("test prompt", {})
    assert res["provider"] == "github"
    assert manager.metrics["local_qwen"]["errors"] == 1


@pytest.mark.asyncio
async def test_fallback_exhausted(manager):
    # Set all providers unhealthy
    for key in manager.priority:
        set_provider_health(manager, key, False)

    with pytest.raises(RuntimeError, match="No healthy AI Providers are available"):
        await manager.get_active_provider()

    with pytest.raises(RuntimeError, match="AI Generation failed. All configured fallback providers failed"):
        await manager.generate_json("test prompt", {})

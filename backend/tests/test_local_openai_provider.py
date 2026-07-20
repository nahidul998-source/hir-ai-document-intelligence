import pytest
import httpx
from unittest.mock import patch, MagicMock, AsyncMock

from app.infrastructure.adapters.providers.openai_provider import LocalOpenAIProvider

@pytest.fixture
def provider():
    return LocalOpenAIProvider(
        name="test_local",
        enabled=True,
        api_url="http://localhost:11434/v1",
        api_key="test-key",
        model_name="qwen-test"
    )

@pytest.mark.asyncio
async def test_extract_json_success(provider):
    json_str = '{"data": "value"}'
    res = await provider._extract_json(json_str)
    assert res == {"data": "value"}
    
    markdown_str = '```json\n{"data": "value2"}\n```'
    res = await provider._extract_json(markdown_str)
    assert res == {"data": "value2"}

@pytest.mark.asyncio
async def test_extract_json_fail(provider):
    invalid_str = "No json here"
    with pytest.raises(ValueError):
        await provider._extract_json(invalid_str)

@pytest.mark.asyncio
async def test_generate_json_success(provider):
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": '{"result": "success"}'}}]
    }
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await provider.generate_json("Test prompt", {"type": "object"})
        assert result == {"result": "success"}
        mock_post.assert_called_once()

@pytest.mark.asyncio
async def test_generate_json_retry_then_success(provider):
    mock_response_fail = MagicMock()
    mock_response_fail.json.return_value = {
        "choices": [{"message": {"content": 'invalid json'}}]
    }
    
    mock_response_success = MagicMock()
    mock_response_success.json.return_value = {
        "choices": [{"message": {"content": '{"result": "recovered"}'}}]
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = [mock_response_fail, mock_response_success]
        result = await provider.generate_json("Test prompt", {"type": "object"})
        assert result == {"result": "recovered"}
        assert mock_post.call_count == 2

@pytest.mark.asyncio
async def test_is_healthy(provider):
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        assert await provider.is_healthy() is True
        
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPError("Connection failed")
        assert await provider.is_healthy() is False

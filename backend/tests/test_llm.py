"""T03 LLM Provider 抽象层测试：工厂 / Mock / OpenAI 解析逻辑（不外呼真实 API）"""

import httpx
import pytest

from app.core.exceptions import ChatBotException
from app.llm.factory import get_available_providers, get_provider
from app.llm.providers.mock import MockProvider
from app.llm.providers.openai_provider import OpenAIProvider
from app.llm.schemas import LLMMessage


# ---------- 工厂 ----------


async def test_factory_returns_correct_type():
    provider = get_provider("mock")
    assert isinstance(provider, MockProvider)


async def test_factory_singleton():
    assert get_provider("mock") is get_provider("mock")


async def test_factory_xingchen_is_openai_compatible():
    provider = get_provider("xingchen")
    assert isinstance(provider, OpenAIProvider)
    assert provider.name == "xingchen"


async def test_factory_unknown_provider_raises():
    with pytest.raises(ChatBotException):
        get_provider("nonexistent")


async def test_available_providers_always_include_mock():
    names = [p["name"] for p in get_available_providers()]
    assert "mock" in names


# ---------- Mock Provider ----------


async def test_mock_stream_chat_yields_chars():
    provider = get_provider("mock")
    chunks = [c async for c in provider.stream_chat([LLMMessage(role="user", content="你好")])]
    assert "".join(chunks) == "你好世界"
    assert len(chunks) > 1  # 逐字流式


async def test_mock_chat_returns_result():
    provider = get_provider("mock")
    result = await provider.chat([LLMMessage(role="user", content="测试消息")])
    assert result.content
    assert result.tokens > 0


async def test_mock_embed_dimension():
    provider = get_provider("mock")
    result = await provider.embed("hello")
    assert len(result.embedding) == 1536


async def test_mock_embed_batch():
    provider = get_provider("mock")
    result = await provider.embed_batch(["a", "b", "c"])
    assert len(result.embeddings) == 3
    assert all(len(e) == 1536 for e in result.embeddings)


# ---------- OpenAI 兼容 Provider（MockTransport 验证解析逻辑） ----------


def _openai_provider_with(handler) -> OpenAIProvider:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return OpenAIProvider(api_key="test-key", base_url="http://test/v1", client=client)


async def test_openai_chat_parses_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/chat/completions"
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(
            200,
            json={
                "choices": [{"message": {"content": "回复内容"}}],
                "usage": {"total_tokens": 42},
            },
        )

    provider = _openai_provider_with(handler)
    result = await provider.chat([LLMMessage(role="user", content="hi")])
    assert result.content == "回复内容"
    assert result.tokens == 42


async def test_openai_stream_chat_parses_sse():
    sse_lines = [
        'data: {"choices": [{"delta": {"content": "你"}}]}',
        "",
        'data: {"choices": [{"delta": {"content": "好"}}]}',
        "",
        "data: [DONE]",
        "",
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        body = "\n".join(sse_lines).encode()
        return httpx.Response(
            200, content=body, headers={"content-type": "text/event-stream"}
        )

    provider = _openai_provider_with(handler)
    chunks = [c async for c in provider.stream_chat([LLMMessage(role="user", content="hi")])]
    assert "".join(chunks) == "你好"


async def test_openai_embed_parses_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/v1/embeddings"
        return httpx.Response(
            200,
            json={
                "data": [
                    {"index": 1, "embedding": [0.3, 0.4]},
                    {"index": 0, "embedding": [0.1, 0.2]},
                ]
            },
        )

    provider = _openai_provider_with(handler)
    result = await provider.embed_batch(["a", "b"])
    # 必须按 index 排序还原顺序
    assert result.embeddings[0] == [0.1, 0.2]
    assert result.embeddings[1] == [0.3, 0.4]


async def test_openai_http_error_raises_llm_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="server error")

    provider = _openai_provider_with(handler)
    with pytest.raises(ChatBotException) as exc_info:
        await provider.chat([LLMMessage(role="user", content="hi")])
    assert exc_info.value.code == "LLM_ERROR"

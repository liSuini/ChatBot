import asyncio
from typing import AsyncIterator

from app.llm.base import LLMProvider
from app.llm.schemas import ChatResult, EmbedBatchResult, EmbedResult, LLMMessage

_EMBED_DIM = 1536


class MockProvider(LLMProvider):
    """测试用 Mock Provider：不调用外部 API"""

    name = "mock"

    async def chat(self, messages: list[LLMMessage], model: str | None = None) -> ChatResult:
        last = messages[-1].content if messages else ""
        content = f"你好世界（Mock 回复）：已收到「{last}」"
        tokens = sum(len(m.content) for m in messages) + len(content)
        return ChatResult(content=content, tokens=tokens)

    async def stream_chat(
        self, messages: list[LLMMessage], model: str | None = None
    ) -> AsyncIterator[str]:
        # 逐字返回，模拟打字机效果
        for ch in "你好世界":
            yield ch
            await asyncio.sleep(0.02)

    async def embed(self, text: str) -> EmbedResult:
        return EmbedResult(embedding=[0.1] * _EMBED_DIM)

    async def embed_batch(self, texts: list[str]) -> EmbedBatchResult:
        return EmbedBatchResult(embeddings=[[0.1] * _EMBED_DIM for _ in texts])

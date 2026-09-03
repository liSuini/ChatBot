from abc import ABC, abstractmethod
from typing import AsyncIterator

from app.llm.schemas import ChatResult, EmbedBatchResult, EmbedResult, LLMMessage


class LLMProvider(ABC):
    """LLM 统一抽象接口：所有 Provider（Mock/OpenAI 兼容）实现同一契约，工厂按名创建"""

    name: str

    @abstractmethod
    async def chat(self, messages: list[LLMMessage], model: str | None = None) -> ChatResult:
        """非流式对话，返回完整结果"""

    @abstractmethod
    def stream_chat(
        self, messages: list[LLMMessage], model: str | None = None
    ) -> AsyncIterator[str]:
        """流式对话，逐段 yield 文本增量"""

    @abstractmethod
    async def embed(self, text: str) -> EmbedResult:
        """单条文本向量化"""

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> EmbedBatchResult:
        """批量文本向量化"""

import json
from typing import AsyncIterator

import httpx

from app.core.exceptions import LLMProviderError
from app.llm.base import LLMProvider
from app.llm.schemas import ChatResult, EmbedBatchResult, EmbedResult, LLMMessage


class OpenAIProvider(LLMProvider):
    """OpenAI 兼容 API Provider（适配星辰大模型等兼容接口）

    支持注入自定义 httpx.AsyncClient（测试用 MockTransport）；
    生产环境每次请求自建 client，避免连接跨事件循环复用问题。
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        client: httpx.AsyncClient | None = None,
        name: str = "openai",
    ):
        from app.core.config import settings

        self.name = name
        self.api_key = api_key if api_key is not None else settings.openai_api_key
        self.base_url = (base_url if base_url is not None else settings.openai_base_url).rstrip("/")
        self._injected_client = client

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def _client(self) -> httpx.AsyncClient:
        return self._injected_client or httpx.AsyncClient(timeout=120)

    async def chat(self, messages: list[LLMMessage], model: str | None = None) -> ChatResult:
        from app.core.config import settings

        payload = {
            "model": model or settings.openai_model,
            "messages": [m.model_dump() for m in messages],
        }
        client = self._client()
        try:
            resp = await client.post(
                f"{self.base_url}/chat/completions", headers=self._headers(), json=payload
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise LLMProviderError(f"LLM 请求失败: {e}") from e
        finally:
            if self._injected_client is None:
                await client.aclose()

        data = resp.json()
        usage = data.get("usage") or {}
        return ChatResult(
            content=data["choices"][0]["message"]["content"] or "",
            tokens=usage.get("total_tokens", 0),
        )

    async def stream_chat(
        self, messages: list[LLMMessage], model: str | None = None
    ) -> AsyncIterator[str]:
        from app.core.config import settings

        payload = {
            "model": model or settings.openai_model,
            "messages": [m.model_dump() for m in messages],
            "stream": True,
        }
        client = self._client()
        try:
            async with client.stream(
                "POST", f"{self.base_url}/chat/completions", headers=self._headers(), json=payload
            ) as resp:
                if resp.status_code != 200:
                    body = (await resp.aread()).decode(errors="replace")
                    raise LLMProviderError(f"LLM 流式请求失败 ({resp.status_code}): {body[:200]}")
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    data = line[len("data:") :].strip()
                    if data == "[DONE]":
                        break
                    try:
                        delta = json.loads(data)["choices"][0]["delta"].get("content")
                    except (json.JSONDecodeError, KeyError, IndexError):
                        continue
                    if delta:
                        yield delta
        except httpx.HTTPError as e:
            raise LLMProviderError(f"LLM 流式请求失败: {e}") from e
        finally:
            if self._injected_client is None:
                await client.aclose()

    async def embed(self, text: str) -> EmbedResult:
        result = await self.embed_batch([text])
        return EmbedResult(embedding=result.embeddings[0])

    async def embed_batch(self, texts: list[str]) -> EmbedBatchResult:
        from app.core.config import settings

        payload = {"model": settings.openai_embed_model, "input": texts}
        client = self._client()
        try:
            resp = await client.post(
                f"{self.base_url}/embeddings", headers=self._headers(), json=payload
            )
            resp.raise_for_status()
        except httpx.HTTPError as e:
            raise LLMProviderError(f"Embedding 请求失败: {e}") from e
        finally:
            if self._injected_client is None:
                await client.aclose()

        data = resp.json()["data"]
        # 按 index 排序还原输入顺序
        ordered = sorted(data, key=lambda item: item["index"])
        return EmbedBatchResult(embeddings=[item["embedding"] for item in ordered])

"""RAG 检索服务：问题向量化→余弦相似度检索 Top-K→拼接上下文"""

import json
import math
from typing import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.llm.factory import get_provider
from app.models.document import Document, DocumentChunk


def _cosine_similarity(a: Sequence[float], b: Sequence[float]) -> float:
    """计算两个向量的余弦相似度"""
    dot = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


class RagService:
    """RAG 上下文检索"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def retrieve(self, user_id: int, question: str, top_k: int | None = None) -> list[str]:
        """检索与问题最相关的 Top-K 文档片段"""
        k = top_k or settings.rag_top_k

        # 1. 问题向量化
        provider = get_provider(settings.default_llm_provider)
        embed_result = await provider.embed(question)
        question_vec = embed_result.embedding

        # 2. 加载用户所有 ready 文档的分块
        result = await self.db.execute(
            select(DocumentChunk)
            .join(Document)
            .where(Document.user_id == user_id, Document.status == "ready")
        )
        chunks = list(result.scalars().all())
        if not chunks:
            return []

        # 3. 计算相似度并排序
        scored: list[tuple[float, str]] = []
        for chunk in chunks:
            if not chunk.embedding:
                continue
            chunk_vec = json.loads(chunk.embedding)
            score = _cosine_similarity(question_vec, chunk_vec)
            scored.append((score, chunk.content))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [content for _, content in scored[:k]]

"""文档管理服务：上传→解析→分块→向量化→存储"""

import json
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ChatBotException, NotFoundError
from app.llm.factory import get_provider
from app.models.document import Document, DocumentChunk
from app.models.user import User
from app.rag.parser import parse_file
from app.rag.splitter import split_text


class DocumentService:
    """文档上传、列表、删除、状态查询"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def upload_document(
        self, user_id: int, filename: str, file_type: str, file_size: int, file_path: str
    ) -> Document:
        """上传文档：校验→入库(processing)→解析分块向量化→更新状态"""
        # 校验文件大小
        if file_size > settings.max_file_size:
            raise ChatBotException("BAD_REQUEST", "文件超过 10MB 限制", 400)

        ext = f".{file_type.lower()}"
        if ext not in {".pdf", ".docx", ".txt", ".md"}:
            raise ChatBotException("BAD_REQUEST", f"不支持的文件类型: {ext}", 400)

        # 创建文档记录
        doc = Document(
            user_id=user_id,
            filename=filename,
            file_type=file_type,
            file_size=file_size,
            status="processing",
        )
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)

        # 同步处理：解析→分块→向量化→存储
        try:
            text = parse_file(file_path, file_type)
            chunks_text = split_text(text) if text else []

            # 向量化分块（嵌入可独立于对话模型配置）
            embed_provider_name = settings.embed_provider or settings.default_llm_provider
            provider = get_provider(embed_provider_name)
            embeddings: list[list[float]] = []
            if chunks_text:
                result = await provider.embed_batch(chunks_text)
                embeddings = result.embeddings

            # 存储分块
            for i, (content, emb) in enumerate(zip(chunks_text, embeddings, strict=True)):
                chunk = DocumentChunk(
                    document_id=doc.id,
                    chunk_index=i,
                    content=content,
                    embedding=json.dumps(emb),
                )
                self.db.add(chunk)

            doc.status = "ready"
            doc.chunk_count = len(chunks_text)
            await self.db.commit()
            await self.db.refresh(doc)
        except Exception:
            doc.status = "failed"
            await self.db.commit()
            await self.db.refresh(doc)
            raise

        return doc

    async def list_documents(self, user_id: int) -> list[Document]:
        result = await self.db.execute(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc(), Document.id.desc())
        )
        return list(result.scalars().all())

    async def delete_document(self, user_id: int, document_id: int) -> None:
        doc = await self._get_owned(user_id, document_id)
        await self.db.delete(doc)
        await self.db.commit()

    async def get_status(self, user_id: int, document_id: int) -> Document:
        return await self._get_owned(user_id, document_id)

    async def _get_owned(self, user_id: int, document_id: int) -> Document:
        result = await self.db.execute(
            select(Document).where(
                Document.id == document_id, Document.user_id == user_id
            )
        )
        doc = result.scalar_one_or_none()
        if not doc:
            raise NotFoundError("文档不存在")
        return doc

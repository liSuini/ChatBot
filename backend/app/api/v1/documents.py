"""T09: 文档上传 + 管理 端点"""

import os
import tempfile

from fastapi import APIRouter, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import ChatBotException
from app.core.database import get_db
from app.deps.auth import get_current_user
from app.models.user import User
from app.schemas.document import DocumentResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="/documents", tags=["documents"])


@router.post("", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """上传文档：自动解析→分块→向量化→存储"""
    # 校验文件大小
    content = await file.read()
    file_size = len(content)
    if file_size > settings.max_file_size:
        raise ChatBotException("BAD_REQUEST", "文件超过 10MB 限制", 400)
    if file_size == 0:
        raise ChatBotException("BAD_REQUEST", "文件为空", 400)

    # 提取扩展名
    filename = file.filename or "unknown.txt"
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    if f".{ext}" not in {".pdf", ".docx", ".txt", ".md"}:
        raise ChatBotException("BAD_REQUEST", f"不支持的文件类型: .{ext}", 400)

    # 写入临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        service = DocumentService(db)
        doc = await service.upload_document(user.id, filename, ext, file_size, tmp_path)
        return doc
    finally:
        os.unlink(tmp_path)


@router.get("", response_model=list[DocumentResponse])
async def list_documents(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """列出当前用户的全部文档"""
    service = DocumentService(db)
    return await service.list_documents(user.id)


@router.get("/{document_id}/status", response_model=DocumentResponse)
async def get_document_status(
    document_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """查询单个文档状态（大文件轮询用）"""
    service = DocumentService(db)
    return await service.get_status(user.id, document_id)


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """删除文档（级联删除分块）"""
    service = DocumentService(db)
    await service.delete_document(user.id, document_id)

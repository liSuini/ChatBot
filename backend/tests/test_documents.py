"""T09: 文档上传 + RAG 问答 测试"""

import asyncio

import pytest

from app.services.document_service import DocumentService
from app.services.rag_service import RagService


# ---- 文档上传/列表/删除 ----


async def test_upload_txt_document(auth_client):
    """上传 TXT 文档→状态变 ready→分块数>0"""
    content = "这是一个测试文档。\n" * 50
    resp = await auth_client.post(
        "/api/v1/documents",
        files={"file": ("test.txt", content.encode("utf-8"), "text/plain")},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["filename"] == "test.txt"
    assert data["file_type"] == "txt"
    assert data["status"] == "ready"
    assert data["chunk_count"] > 0


async def test_upload_md_document(auth_client):
    """上传 Markdown 文档"""
    content = "# 标题\n\n正文内容。" * 30
    resp = await auth_client.post(
        "/api/v1/documents",
        files={"file": ("note.md", content.encode("utf-8"), "text/markdown")},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "ready"


async def test_list_documents(auth_client):
    """上传多个文档→列表返回→按创建时间倒序"""
    for name in ("a.txt", "b.txt", "c.txt"):
        await auth_client.post(
            "/api/v1/documents",
            files={"file": (name, b"content", "text/plain")},
        )
    resp = await auth_client.get("/api/v1/documents")
    assert resp.status_code == 200
    docs = resp.json()
    assert len(docs) == 3
    # 最新创建的在前
    assert docs[0]["filename"] == "c.txt"


async def test_get_document_status(auth_client):
    """查询单个文档状态"""
    resp = await auth_client.post(
        "/api/v1/documents",
        files={"file": ("status.txt", b"hello", "text/plain")},
    )
    doc_id = resp.json()["id"]

    resp = await auth_client.get(f"/api/v1/documents/{doc_id}/status")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ready"


async def test_delete_document(auth_client):
    """删除文档→级联删除分块→列表为空"""
    resp = await auth_client.post(
        "/api/v1/documents",
        files={"file": ("delete.txt", b"to be deleted", "text/plain")},
    )
    doc_id = resp.json()["id"]

    resp = await auth_client.delete(f"/api/v1/documents/{doc_id}")
    assert resp.status_code == 204

    # 确认已删除
    resp = await auth_client.get("/api/v1/documents")
    assert all(d["id"] != doc_id for d in resp.json())


# ---- 文件校验 ----


async def test_upload_unsupported_type(auth_client):
    """不支持的文件类型→400"""
    resp = await auth_client.post(
        "/api/v1/documents",
        files={"file": ("evil.exe", b"MZ", "application/octet-stream")},
    )
    assert resp.status_code == 400


async def test_upload_empty_file(auth_client):
    """空文件→400"""
    resp = await auth_client.post(
        "/api/v1/documents",
        files={"file": ("empty.txt", b"", "text/plain")},
    )
    assert resp.status_code == 400


# ---- 用户隔离 ----


async def test_user_isolation(auth_client, auth_client2):
    """用户 A 不能查看/删除用户 B 的文档"""
    resp = await auth_client.post(
        "/api/v1/documents",
        files={"file": ("private.txt", b"secret", "text/plain")},
    )
    doc_id = resp.json()["id"]

    # B 看不到 A 的文档
    resp = await auth_client2.get("/api/v1/documents")
    assert all(d["id"] != doc_id for d in resp.json())

    # B 不能查 A 的文档状态
    resp = await auth_client2.get(f"/api/v1/documents/{doc_id}/status")
    assert resp.status_code == 404

    # B 不能删 A 的文档
    resp = await auth_client2.delete(f"/api/v1/documents/{doc_id}")
    assert resp.status_code == 404

    # A 的文档仍在
    resp = await auth_client.get(f"/api/v1/documents/{doc_id}/status")
    assert resp.status_code == 200


# ---- RAG 检索 ----


async def test_rag_retrieve_returns_chunks(auth_client, db_session):
    """上传文档→RAG 检索返回相关分块"""
    content = "FastAPI 是一个现代的 Python Web 框架。\n" * 20
    resp = await auth_client.post(
        "/api/v1/documents",
        files={"file": ("fastapi.txt", content.encode("utf-8"), "text/plain")},
    )
    assert resp.json()["status"] == "ready"

    # 检索
    svc = RagService(db_session)
    results = await svc.retrieve(user_id=1, question="FastAPI 是什么？")
    assert len(results) > 0
    assert "FastAPI" in results[0]


async def test_rag_retrieve_no_documents(auth_client, db_session):
    """无文档时检索返回空列表"""
    svc = RagService(db_session)
    results = await svc.retrieve(user_id=1, question="anything")
    assert results == []


# ---- RAG 上下文注入 ----


async def test_send_message_with_rag(auth_client):
    """上传文档→开启 RAG 发送消息→AI 回复（SSE 流）"""
    # 上传文档
    content = "Python 是一种解释型编程语言。\n" * 20
    resp = await auth_client.post(
        "/api/v1/documents",
        files={"file": ("python.txt", content.encode("utf-8"), "text/plain")},
    )
    assert resp.json()["status"] == "ready"

    # 创建会话
    resp = await auth_client.post("/api/v1/conversations", json={"model_provider": "mock"})
    conv_id = resp.json()["id"]

    # 发送消息（开启 RAG）
    async with auth_client.stream(
        "POST",
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Python 是什么？", "rag_enabled": True},
    ) as resp:
        assert resp.status_code == 200
        events = [line async for line in resp.aiter_lines()]

    # 验证收到 SSE 事件
    event_types = [e for e in events if e.startswith("event:")]
    assert any("done" in e for e in event_types)


async def test_send_message_without_rag(auth_client):
    """不开启 RAG 也能正常发消息"""
    resp = await auth_client.post("/api/v1/conversations", json={"model_provider": "mock"})
    conv_id = resp.json()["id"]

    async with auth_client.stream(
        "POST",
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "你好", "rag_enabled": False},
    ) as resp:
        assert resp.status_code == 200
        events = [line async for line in resp.aiter_lines()]

    assert any("event: done" in e for e in events)


# ---- fixtures ----


@pytest.fixture
async def db_session():
    """提供独立的数据库会话用于直接调用服务层"""
    from app.core.database import async_session_maker

    async with async_session_maker() as session:
        yield session

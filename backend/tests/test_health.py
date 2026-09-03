"""T01 冒烟测试：验证项目骨架、配置、模型导入、/health 端点"""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


async def test_health_endpoint(client):
    """/health 端点返回 ok"""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_config_loaded():
    """Settings 正确加载，关键字段类型正确"""
    from app.core.config import settings

    assert isinstance(settings.database_url, str)
    assert settings.database_url.startswith("mysql+aiomysql://")
    assert isinstance(settings.access_token_expire_minutes, int)
    assert settings.access_token_expire_minutes > 0
    assert isinstance(settings.rag_top_k, int)
    assert settings.rag_top_k == 5


def test_all_models_importable():
    """5 个 ORM 模型均可正确导入且表名正确"""
    from app.models import Conversation, Document, DocumentChunk, Message, User

    assert User.__tablename__ == "users"
    assert Conversation.__tablename__ == "conversations"
    assert Message.__tablename__ == "messages"
    assert Document.__tablename__ == "documents"
    assert DocumentChunk.__tablename__ == "document_chunks"


def test_exceptions_hierarchy():
    """异常体系基类与子类正确"""
    from app.core.exceptions import (
        ChatBotException,
        ForbiddenError,
        LLMProviderError,
        NotFoundError,
    )

    assert issubclass(LLMProviderError, ChatBotException)
    assert issubclass(NotFoundError, ChatBotException)
    assert issubclass(ForbiddenError, ChatBotException)

    err = NotFoundError("测试")
    assert err.code == "NOT_FOUND"
    assert err.status == 404

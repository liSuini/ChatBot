"""pytest 公共 fixtures：测试数据库隔离 + HTTP 客户端"""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from app.core.database import engine
from app.main import app


@pytest.fixture(autouse=True)
async def clean_db():
    """每个测试前清空业务表，保证测试之间相互隔离（不碰 alembic_version）"""
    async with engine.begin() as conn:
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        for table in ("messages", "document_chunks", "documents", "conversations", "users"):
            await conn.execute(text(f"TRUNCATE TABLE {table}"))
        await conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
    yield


@pytest.fixture
async def client():
    """未认证的 HTTP 客户端，直接请求 FastAPI 应用"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac


@pytest.fixture
def client_factory(client):
    """注册一个新用户并返回携带其 JWT 的客户端 (client, username)"""
    async def _make(username: str, password: str = "testpass123"):
        resp = await client.post(
            "/api/v1/auth/register", json={"username": username, "password": password}
        )
        assert resp.status_code == 200, resp.text
        client.headers["Authorization"] = f"Bearer {resp.json()['access_token']}"
        return client

    return _make


@pytest.fixture
async def auth_client(client_factory):
    """已认证客户端（用户 testuser）"""
    return await client_factory("testuser")


@pytest.fixture
async def auth_client2(client_factory):
    """第二个已认证客户端（用户 testuser2，用于隔离测试）"""
    return await client_factory("testuser2")

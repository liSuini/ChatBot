"""T11: 端到端集成测试 — 完整用户流程覆盖

注册→登录→创建会话→发消息→收SSE→停止→重生成→编辑重发→上传文档→RAG对话→删除会话→删除文档
"""

import json

import pytest

pytestmark = pytest.mark.asyncio


async def _parse_sse(resp) -> list[tuple[str, dict]]:
    """从 httpx 流式响应中解析 SSE 事件列表"""
    events: list[tuple[str, dict]] = []
    cur_event = None
    cur_data = None
    async for line in resp.aiter_lines():
        if line.startswith("event:"):
            cur_event = line[6:].strip()
        elif line.startswith("data:"):
            cur_data = line[5:].strip()
        elif line == "" and cur_event:
            data = json.loads(cur_data) if cur_data else {}
            events.append((cur_event, data))
            cur_event = None
            cur_data = None
    return events


# ─── 完整 E2E 流程 ───


async def test_full_user_journey(client, auth_client):
    """端到端：注册→登录→创建会话→发消息→SSE→重生成→编辑重发→上传文档→RAG→删除"""

    # 1. 注册
    resp = await client.post(
        "/api/v1/auth/register",
        json={"username": "e2e_user", "password": "testpass123"},
    )
    assert resp.status_code == 200
    assert "access_token" in resp.json()

    # 2. 登录
    resp = await client.post(
        "/api/v1/auth/login",
        json={"username": "e2e_user", "password": "testpass123"},
    )
    assert resp.status_code == 200
    login_token = resp.json()["access_token"]
    assert login_token

    # 3. 创建会话
    resp = await auth_client.post(
        "/api/v1/conversations", json={"model_provider": "mock"}
    )
    assert resp.status_code == 200
    conv = resp.json()
    conv_id = conv["id"]
    assert conv["model_provider"] == "mock"

    # 4. 发送消息 → 收到 SSE 事件流
    async with auth_client.stream(
        "POST",
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "你好", "rag_enabled": False},
    ) as resp:
        assert resp.status_code == 200
        events = await _parse_sse(resp)

    event_types = [e for e, _ in events]
    assert "start" in event_types
    assert "token" in event_types
    assert "done" in event_types

    # 提取消息 ID
    start_data = next(d for e, d in events if e == "start")
    done_data = next(d for e, d in events if e == "done")
    user_msg_id = start_data["message_id"]
    assistant_msg_id = done_data["message_id"]
    assert done_data["content"] == "你好世界"
    assert done_data["tokens"] == 4

    # 5. 重新生成 AI 回复
    async with auth_client.stream(
        "POST",
        f"/api/v1/conversations/{conv_id}/messages/{assistant_msg_id}/regenerate",
        json={},
    ) as resp:
        assert resp.status_code == 200
        regen_events = await _parse_sse(resp)

    regen_done = next(d for e, d in regen_events if e == "done")
    new_assistant_id = regen_done["message_id"]
    assert new_assistant_id != assistant_msg_id  # 新消息 ID

    # 6. 编辑重发用户消息
    async with auth_client.stream(
        "POST",
        f"/api/v1/conversations/{conv_id}/messages/{user_msg_id}/edit",
        json={"content": "修改后的消息"},
    ) as resp:
        assert resp.status_code == 200
        edit_events = await _parse_sse(resp)

    edit_done = next(d for e, d in edit_events if e == "done")
    assert edit_done["content"] == "你好世界"

    # 7. 上传文档
    content = "Python 是一种高级编程语言，广泛用于 Web 开发、数据分析和人工智能。"
    resp = await auth_client.post(
        "/api/v1/documents",
        files={"file": ("python_intro.txt", content.encode("utf-8"), "text/plain")},
    )
    assert resp.status_code == 201
    doc = resp.json()
    doc_id = doc["id"]
    assert doc["status"] == "ready"
    assert doc["chunk_count"] > 0

    # 8. RAG 对话（开启 RAG）
    async with auth_client.stream(
        "POST",
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Python 是什么？", "rag_enabled": True},
    ) as resp:
        assert resp.status_code == 200
        rag_events = await _parse_sse(resp)

    rag_done = next(d for e, d in rag_events if e == "done")
    assert rag_done["content"]  # 有回复内容

    # 9. 查看会话消息历史
    resp = await auth_client.get(f"/api/v1/conversations/{conv_id}")
    assert resp.status_code == 200
    messages = resp.json()["messages"]
    assert len(messages) >= 4  # 至少 4 条消息（原始 user+assistant + 后续操作）

    # 10. 删除会话
    resp = await auth_client.delete(f"/api/v1/conversations/{conv_id}")
    assert resp.status_code == 204

    # 验证会话已删除
    resp = await auth_client.get(f"/api/v1/conversations/{conv_id}")
    assert resp.status_code == 404

    # 11. 删除文档
    resp = await auth_client.delete(f"/api/v1/documents/{doc_id}")
    assert resp.status_code == 204

    # 验证文档已删除
    resp = await auth_client.get("/api/v1/documents")
    assert all(d["id"] != doc_id for d in resp.json())


async def test_stop_generation(client_factory):
    """停止生成 → 部分内容保留"""
    ac = await client_factory("stop_user")

    # 创建会话 + 发消息
    resp = await ac.post("/api/v1/conversations", json={"model_provider": "mock"})
    conv_id = resp.json()["id"]

    # 发送消息后立即停止
    async with ac.stream(
        "POST",
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "测试停止", "rag_enabled": False},
    ) as resp:
        # 读第一个事件后发 stop
        async for line in resp.aiter_lines():
            if line.startswith("event:"):
                break
        await ac.post(f"/api/v1/conversations/{conv_id}/stop")

    # 会话仍有消息记录
    resp = await ac.get(f"/api/v1/conversations/{conv_id}")
    assert resp.status_code == 200
    messages = resp.json()["messages"]
    assert len(messages) >= 1  # 至少用户消息被保存


async def test_user_isolation_e2e(client_factory):
    """用户 A 的数据对 B 不可见"""
    a = await client_factory("isol_a")
    b = await client_factory("isol_b")

    # A 创建会话
    resp = await a.post("/api/v1/conversations", json={"model_provider": "mock"})
    a_conv = resp.json()["id"]

    # A 上传文档
    resp = await a.post(
        "/api/v1/documents",
        files={"file": ("a_doc.txt", b"a content", "text/plain")},
    )
    a_doc = resp.json()["id"]

    # B 看不到 A 的会话
    resp = await b.get("/api/v1/conversations")
    assert all(c["id"] != a_conv for c in resp.json())

    # B 看不到 A 的文档
    resp = await b.get("/api/v1/documents")
    assert all(d["id"] != a_doc for d in resp.json())

    # B 访问 A 的会话 → 404
    resp = await b.get(f"/api/v1/conversations/{a_conv}")
    assert resp.status_code == 404

    # B 删除 A 的文档 → 404
    resp = await b.delete(f"/api/v1/documents/{a_doc}")
    assert resp.status_code == 404

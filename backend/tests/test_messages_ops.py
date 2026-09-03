"""T06: 消息操作 (重新生成/编辑重发) 测试"""

import json

import pytest

pytestmark = pytest.mark.asyncio


async def _create_conversation(client, model_provider: str = "mock") -> int:
    resp = await client.post("/api/v1/conversations", json={"model_provider": model_provider})
    assert resp.status_code == 200
    return resp.json()["id"]


async def _send_message(client, conv_id: int, content: str) -> dict:
    """发送消息，返回 {user_msg_id, assistant_msg_id}"""
    events = []
    async with client.stream(
        "POST", f"/api/v1/conversations/{conv_id}/messages", json={"content": content}
    ) as resp:
        assert resp.status_code == 200
        async for line in resp.aiter_lines():
            events.append(line)

    user_id = None
    assistant_id = None
    i = 0
    while i < len(events):
        if events[i].startswith("event:"):
            ev = events[i][6:].strip()
            i += 1
            if i < len(events) and events[i].startswith("data:"):
                data = json.loads(events[i][5:].strip())
                if ev == "start":
                    user_id = data["message_id"]
                elif ev == "done":
                    assistant_id = data["message_id"]
        i += 1
    return {"user_msg_id": user_id, "assistant_msg_id": assistant_id}


# ─── 重新生成 ───


async def test_regenerate_assistant_message(auth_client):
    """重新生成 AI 回复 → 新 assistant 消息 parent_message_id 指向旧 assistant"""
    conv_id = await _create_conversation(auth_client)
    msg_ids = await _send_message(auth_client, conv_id, "你好")
    old_assistant_id = msg_ids["assistant_msg_id"]

    # 重新生成
    events = []
    async with auth_client.stream(
        "POST", f"/api/v1/conversations/{conv_id}/messages/{old_assistant_id}/regenerate"
    ) as resp:
        assert resp.status_code == 200
        async for line in resp.aiter_lines():
            events.append(line)

    # 解析 done 事件获取新消息 ID
    new_assistant_id = None
    i = 0
    while i < len(events):
        if events[i].startswith("event:"):
            ev = events[i][6:].strip()
            i += 1
            if i < len(events) and events[i].startswith("data:"):
                data = json.loads(events[i][5:].strip())
                if ev == "done":
                    new_assistant_id = data["message_id"]
        i += 1

    assert new_assistant_id is not None
    assert new_assistant_id != old_assistant_id

    # 验证数据库：新 assistant 消息 parent_message_id 指向旧 assistant
    resp = await auth_client.get(f"/api/v1/conversations/{conv_id}")
    messages = resp.json()["messages"]
    # 应有 3 条消息：user(1) + old_assistant(1) + new_assistant(1)
    assert len(messages) == 3
    new_msg = next(m for m in messages if m["id"] == new_assistant_id)
    assert new_msg["parent_message_id"] == old_assistant_id
    assert new_msg["role"] == "assistant"


async def test_regenerate_user_isolation(auth_client, auth_client2):
    """用户 B 不能重新生成用户 A 的会话消息 → 404"""
    conv_id = await _create_conversation(auth_client)
    msg_ids = await _send_message(auth_client, conv_id, "你好")

    async with auth_client2.stream(
        "POST", f"/api/v1/conversations/{conv_id}/messages/{msg_ids['assistant_msg_id']}/regenerate"
    ) as resp:
        assert resp.status_code == 404


async def test_regenerate_nonexistent_message(auth_client):
    """重新生成不存在的消息 → 404"""
    conv_id = await _create_conversation(auth_client)
    async with auth_client.stream(
        "POST", f"/api/v1/conversations/{conv_id}/messages/99999/regenerate"
    ) as resp:
        assert resp.status_code == 404


# ─── 编辑重发 ───


async def test_edit_resend_user_message(auth_client):
    """编辑用户消息重发 → 新 user 消息 parent 指向原 user + 新 AI 回复"""
    conv_id = await _create_conversation(auth_client)
    msg_ids = await _send_message(auth_client, conv_id, "你好")
    old_user_id = msg_ids["user_msg_id"]

    # 编辑重发
    events = []
    async with auth_client.stream(
        "POST",
        f"/api/v1/conversations/{conv_id}/messages/{old_user_id}/edit",
        json={"content": "你好，世界"},
    ) as resp:
        assert resp.status_code == 200
        async for line in resp.aiter_lines():
            events.append(line)

    # 解析事件
    new_user_id = None
    new_assistant_id = None
    i = 0
    while i < len(events):
        if events[i].startswith("event:"):
            ev = events[i][6:].strip()
            i += 1
            if i < len(events) and events[i].startswith("data:"):
                data = json.loads(events[i][5:].strip())
                if ev == "start":
                    new_user_id = data["message_id"]
                elif ev == "done":
                    new_assistant_id = data["message_id"]
        i += 1

    assert new_user_id is not None
    assert new_assistant_id is not None
    assert new_user_id != old_user_id

    # 验证数据库
    resp = await auth_client.get(f"/api/v1/conversations/{conv_id}")
    messages = resp.json()["messages"]
    # 4 条：user(1) + assistant(1) + new_user(1) + new_assistant(1)
    assert len(messages) == 4
    new_user_msg = next(m for m in messages if m["id"] == new_user_id)
    assert new_user_msg["parent_message_id"] == old_user_id
    assert new_user_msg["role"] == "user"
    assert new_user_msg["content"] == "你好，世界"


async def test_edit_resend_user_isolation(auth_client, auth_client2):
    """用户 B 不能编辑用户 A 的会话消息 → 404"""
    conv_id = await _create_conversation(auth_client)
    msg_ids = await _send_message(auth_client, conv_id, "你好")

    async with auth_client2.stream(
        "POST",
        f"/api/v1/conversations/{conv_id}/messages/{msg_ids['user_msg_id']}/edit",
        json={"content": "hack"},
    ) as resp:
        assert resp.status_code == 404


async def test_edit_nonexistent_message(auth_client):
    """编辑不存在的消息 → 404"""
    conv_id = await _create_conversation(auth_client)
    async with auth_client.stream(
        "POST", f"/api/v1/conversations/{conv_id}/messages/99999/edit",
        json={"content": "test"},
    ) as resp:
        assert resp.status_code == 404


async def test_edit_empty_content(auth_client):
    """编辑内容为空 → 422"""
    conv_id = await _create_conversation(auth_client)
    msg_ids = await _send_message(auth_client, conv_id, "你好")
    async with auth_client.stream(
        "POST",
        f"/api/v1/conversations/{conv_id}/messages/{msg_ids['user_msg_id']}/edit",
        json={"content": ""},
    ) as resp:
        assert resp.status_code == 422

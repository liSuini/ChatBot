"""T05: 消息发送 + SSE 流式回复 测试"""

import asyncio
import json

import pytest

pytestmark = pytest.mark.asyncio


async def _create_conversation(client, model_provider: str = "mock") -> int:
    resp = await client.post("/api/v1/conversations", json={"model_provider": model_provider})
    assert resp.status_code == 200
    return resp.json()["id"]


async def _parse_sse(resp):
    """从 httpx 流式响应中解析 SSE 事件列表 [(event, data_dict), ...]"""
    events = []
    cur_event = None
    cur_data = None
    async for line in resp.aiter_lines():
        if line.startswith("event:"):
            cur_event = line[len("event:"):].strip()
        elif line.startswith("data:"):
            cur_data = line[len("data:"):].strip()
        elif line == "" and cur_event:
            data = json.loads(cur_data) if cur_data else {}
            events.append((cur_event, data))
            cur_event = None
            cur_data = None
    return events


# ─── SSE 事件流 ───


async def test_send_message_sse_events(auth_client):
    """发送消息 → 收到 SSE 事件流 (start/token/done)"""
    conv_id = await _create_conversation(auth_client)

    async with auth_client.stream(
        "POST", f"/api/v1/conversations/{conv_id}/messages", json={"content": "你好"}
    ) as resp:
        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers.get("content-type", "")
        events = await _parse_sse(resp)

    event_types = [e[0] for e in events]
    assert "start" in event_types
    assert "token" in event_types
    assert "done" in event_types

    # start 事件含 user message_id
    start_data = next(d for ev, d in events if ev == "start")
    assert "message_id" in start_data

    # done 事件含 assistant message_id + content + tokens
    done_data = next(d for ev, d in events if ev == "done")
    assert "message_id" in done_data
    assert "content" in done_data
    assert "tokens" in done_data
    # Mock provider 逐字返回 "你好世界"
    assert done_data["content"] == "你好世界"


async def test_sse_token_content(auth_client):
    """SSE token 事件的内容拼接后等于完整回复"""
    conv_id = await _create_conversation(auth_client)

    async with auth_client.stream(
        "POST", f"/api/v1/conversations/{conv_id}/messages", json={"content": "test"}
    ) as resp:
        events = await _parse_sse(resp)

    tokens = [d["content"] for ev, d in events if ev == "token"]
    assert "".join(tokens) == "你好世界"


# ─── 消息持久化 ───


async def test_message_persistence(auth_client):
    """发送消息后，user + assistant 消息持久化到数据库"""
    conv_id = await _create_conversation(auth_client)

    async with auth_client.stream(
        "POST", f"/api/v1/conversations/{conv_id}/messages", json={"content": "你好"}
    ) as resp:
        await _parse_sse(resp)

    # 通过 GET /conversations/{id} 验证消息已落盘
    resp = await auth_client.get(f"/api/v1/conversations/{conv_id}")
    assert resp.status_code == 200
    messages = resp.json()["messages"]
    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "你好"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "你好世界"
    assert messages[1]["tokens"] > 0


async def test_multi_turn_context(auth_client):
    """多轮对话：第二条 AI 回复的上下文包含第一条 user+assistant"""
    conv_id = await _create_conversation(auth_client)

    # 第一轮
    async with auth_client.stream(
        "POST", f"/api/v1/conversations/{conv_id}/messages", json={"content": "第一轮"}
    ) as resp:
        await _parse_sse(resp)

    # 第二轮
    async with auth_client.stream(
        "POST", f"/api/v1/conversations/{conv_id}/messages", json={"content": "第二轮"}
    ) as resp:
        events = await _parse_sse(resp)

    # 验证数据库有 4 条消息
    resp = await auth_client.get(f"/api/v1/conversations/{conv_id}")
    messages = resp.json()["messages"]
    assert len(messages) == 4
    assert messages[2]["role"] == "user"
    assert messages[2]["content"] == "第二轮"
    assert messages[3]["role"] == "assistant"


# ─── 停止生成 ───


async def test_stop_generation(auth_client):
    """停止生成 → 部分内容保留"""
    conv_id = await _create_conversation(auth_client)

    received_events = []

    async def stream_and_collect():
        async with auth_client.stream(
            "POST",
            f"/api/v1/conversations/{conv_id}/messages",
            json={"content": "你好"},
        ) as resp:
            async for line in resp.aiter_lines():
                received_events.append(line)

    async def send_stop():
        await asyncio.sleep(0.01)  # 让流开始
        await auth_client.post(f"/api/v1/conversations/{conv_id}/stop")

    await asyncio.gather(stream_and_collect(), send_stop())

    # 验证消息已落盘（至少 user 消息，assistant 可能有部分内容）
    resp = await auth_client.get(f"/api/v1/conversations/{conv_id}")
    messages = resp.json()["messages"]
    # user 消息一定存在
    assert any(m["role"] == "user" and m["content"] == "你好" for m in messages)


# ─── 用户隔离 ───


async def test_send_message_user_isolation(auth_client, auth_client2):
    """用户 B 不能向用户 A 的会话发消息 → 404"""
    conv_id = await _create_conversation(auth_client)

    async with auth_client2.stream(
        "POST", f"/api/v1/conversations/{conv_id}/messages", json={"content": "hack"}
    ) as resp:
        assert resp.status_code == 404


async def test_stop_user_isolation(auth_client, auth_client2):
    """用户 B 不能停止用户 A 的会话生成 → 404"""
    conv_id = await _create_conversation(auth_client)
    resp = await auth_client2.post(f"/api/v1/conversations/{conv_id}/stop")
    assert resp.status_code == 404


# ─── 边界情况 ───


async def test_send_message_nonexistent_conversation(auth_client):
    """向不存在的会话发消息 → 404"""
    async with auth_client.stream(
        "POST", "/api/v1/conversations/99999/messages", json={"content": "hi"}
    ) as resp:
        assert resp.status_code == 404


async def test_send_message_empty_content(auth_client):
    """空内容 → 422"""
    conv_id = await _create_conversation(auth_client)
    async with auth_client.stream(
        "POST", f"/api/v1/conversations/{conv_id}/messages", json={"content": ""}
    ) as resp:
        assert resp.status_code == 422

"""T04 会话管理测试：CRUD / 排序 / 用户隔离"""

import asyncio


async def _create(auth_client, **payload):
    resp = await auth_client.post("/api/v1/conversations", json=payload)
    assert resp.status_code == 200, resp.text
    return resp.json()


async def test_create_conversation_default(auth_client):
    resp = await auth_client.post("/api/v1/conversations", json={})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "新对话"
    assert data["model_provider"] == "mock"  # 默认 provider
    assert "id" in data
    assert "messages" not in data  # Summary 不含消息


async def test_create_conversation_with_provider_and_title(auth_client):
    data = await _create(auth_client, title="工作会话", model_provider="openai")
    assert data["title"] == "工作会话"
    assert data["model_provider"] == "openai"


async def test_create_unknown_provider_rejected(auth_client):
    resp = await auth_client.post("/api/v1/conversations", json={"model_provider": "nope"})
    assert resp.status_code == 400
    assert resp.json()["code"] == "PROVIDER_NOT_FOUND"


async def test_list_empty(auth_client):
    resp = await auth_client.get("/api/v1/conversations")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_detail_contains_messages(auth_client):
    data = await _create(auth_client)
    resp = await auth_client.get(f"/api/v1/conversations/{data['id']}")
    assert resp.status_code == 200
    detail = resp.json()
    assert detail["id"] == data["id"]
    assert detail["messages"] == []


async def test_rename_conversation(auth_client):
    data = await _create(auth_client)
    resp = await auth_client.patch(
        f"/api/v1/conversations/{data['id']}", json={"title": "改名了"}
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "改名了"
    # 确认持久化
    resp = await auth_client.get(f"/api/v1/conversations/{data['id']}")
    assert resp.json()["title"] == "改名了"


async def test_rename_validation_empty_title(auth_client):
    data = await _create(auth_client)
    resp = await auth_client.patch(f"/api/v1/conversations/{data['id']}", json={"title": ""})
    assert resp.status_code == 422


async def test_delete_conversation(auth_client):
    data = await _create(auth_client)
    resp = await auth_client.delete(f"/api/v1/conversations/{data['id']}")
    assert resp.status_code == 204
    # 删除后 get 404、list 不含
    resp = await auth_client.get(f"/api/v1/conversations/{data['id']}")
    assert resp.status_code == 404
    resp = await auth_client.get("/api/v1/conversations")
    assert resp.json() == []


async def test_list_ordered_by_updated_at_desc(auth_client):
    first = await _create(auth_client, title="最早")
    await asyncio.sleep(1.1)  # DATETIME 秒级精度，需制造时间差
    second = await _create(auth_client, title="最新")
    resp = await auth_client.get("/api/v1/conversations")
    titles = [c["title"] for c in resp.json()]
    assert titles == ["最新", "最早"]


# ---------- 用户隔离 ----------


async def test_isolation_list_invisible_across_users(auth_client, auth_client2):
    await _create(auth_client, title="A的会话")
    resp = await auth_client2.get("/api/v1/conversations")
    assert resp.json() == []


async def test_isolation_get_other_users_conversation_404(auth_client, auth_client2):
    data = await _create(auth_client)
    resp = await auth_client2.get(f"/api/v1/conversations/{data['id']}")
    assert resp.status_code == 404


async def test_isolation_patch_other_users_conversation_404(auth_client, auth_client2):
    data = await _create(auth_client)
    resp = await auth_client2.patch(
        f"/api/v1/conversations/{data['id']}", json={"title": "篡改"}
    )
    assert resp.status_code == 404


async def test_isolation_delete_other_users_conversation_404(auth_client, auth_client2):
    data = await _create(auth_client)
    resp = await auth_client2.delete(f"/api/v1/conversations/{data['id']}")
    assert resp.status_code == 404
    # 原会话仍然存在
    resp = await auth_client.get(f"/api/v1/conversations/{data['id']}")
    assert resp.status_code == 200


# ---------- T08: providers 端点 ----------


async def test_providers_requires_auth(client):
    resp = await client.get("/api/v1/llm/providers")
    assert resp.status_code == 401


async def test_providers_returns_available(auth_client):
    resp = await auth_client.get("/api/v1/llm/providers")
    assert resp.status_code == 200
    providers = resp.json()
    names = [p["name"] for p in providers]
    assert "mock" in names
    mock = next(p for p in providers if p["name"] == "mock")
    assert "display_name" in mock
    assert isinstance(mock["models"], list)

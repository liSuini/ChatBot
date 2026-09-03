"""T02 认证模块测试：注册/登录/me 全链路"""

async def test_register_success(client):
    response = await client.post(
        "/api/v1/auth/register", json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "testuser"
    assert "id" in data["user"]
    # 密码不能出现在任何响应字段中
    assert "testpass123" not in response.text


async def test_register_duplicate(client):
    payload = {"username": "testuser", "password": "testpass123"}
    await client.post("/api/v1/auth/register", json=payload)
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 409
    assert response.json()["code"] == "USERNAME_EXISTS"


async def test_register_validation(client):
    """密码过短 / 用户名过长的 422 校验"""
    resp = await client.post("/api/v1/auth/register", json={"username": "ab", "password": "123"})
    assert resp.status_code == 422


async def test_login_success(client):
    await client.post(
        "/api/v1/auth/register", json={"username": "testuser", "password": "testpass123"}
    )
    response = await client.post(
        "/api/v1/auth/login", json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


async def test_login_wrong_password(client):
    await client.post(
        "/api/v1/auth/register", json={"username": "testuser", "password": "testpass123"}
    )
    response = await client.post(
        "/api/v1/auth/login", json={"username": "testuser", "password": "wrongpass"}
    )
    assert response.status_code == 401
    assert response.json()["code"] == "INVALID_CREDENTIALS"


async def test_me_without_token(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401


async def test_me_with_invalid_token(client):
    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": "Bearer not.a.jwt"}
    )
    assert response.status_code == 401


async def test_me_with_token(auth_client):
    response = await auth_client.get("/api/v1/auth/me")
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '4f576d30-ec96-47fb-9739-40b8d8f749dc'
  PropagateID: '4f576d30-ec96-47fb-9739-40b8d8f749dc'
  ReservedCode1: '855c2d8c-f616-42ea-b997-b35df33a0fca'
  ReservedCode2: '855c2d8c-f616-42ea-b997-b35df33a0fca'
---

# ChatBot 实现计划

> 阶段7产出 | 日期: 2026-09-02
> **For agentic workers:** 使用 superpowers:subagent-driven-development 或 superpowers:executing-plans 按任务逐个实现。步骤使用 checkbox (`- [ ]`) 语法跟踪。

**Goal:** 构建一个团队内部类 ChatGPT 对话问答系统，支持多轮对话、SSE 流式回复、文档 RAG 问答、Markdown 渲染和消息操作。

**Architecture:** 前后端分离的渐进式单体架构。后端 FastAPI 单体分层（auth/chat/rag/llm 四模块），前端 React SPA，SSE 流式推送，MySQL 9.0 向量存储，Docker Compose 编排。

**Tech Stack:** FastAPI + SQLAlchemy 2.0 (async) + Alembic + MySQL 9.0 (VECTOR) | React 18 + Vite + TypeScript + Ant Design + Zustand | Docker Compose + Nginx

**Spec:** `docs/spec.md`

## Global Constraints

- Python 3.12+, Node.js 20+, MySQL 9.0+ (VECTOR 类型)
- 后端包管理用 uv，前端用 npm (nvm 跨盘符 yarn 有 bug)
- 所有 API 前缀 `/api/v1`，非认证接口需 `Authorization: Bearer <token>` 头
- SSE 响应必须包含 `X-Accel-Buffering: no` 头 (Nginx 关键配置)
- JSON 序列化中文不可转义 (ensure_ascii=False)
- 所有数据查询带 `user_id` 隔离
- TDD: 先写测试 → 实现 → 运行测试 → commit

---

## 里程碑概览

```
M1: 项目骨架 + 数据库     → M2: 认证模块    → M3: LLM 抽象层
→ M4: 会话+消息+SSE      → M5: 前端对话核心 → M6: RAG 模块
→ M7: 前端文档管理       → M8: Docker 部署  → M9: 集成测试+打磨
```

---

## M1: 项目骨架 + 数据库

### Task 1: 后端项目初始化

**Files:**
- Create: `backend/pyproject.toml`
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/core/__init__.py`
- Create: `backend/app/core/config.py`

**Interfaces:**
- Produces: `settings` 对象 (Settings 类实例, pydantic-settings)

- [ ] **Step 1: 创建 pyproject.toml 并安装依赖**

```toml
[project]
name = "chatbot-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115",
    "uvicorn[standard]>=0.30",
    "sqlalchemy[asyncio]>=2.0",
    "alembic>=1.13",
    "aiomysql>=0.2",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "passlib[bcrypt]>=1.7",
    "python-jose[cryptography]>=3.3",
    "slowapi>=0.1",
    "httpx>=0.27",
    "python-multipart>=0.0.9",
    "PyMuPDF>=1.24",
    "python-docx>=1.1",
    "langchain-text-splitters>=0.2",
    "sse-starlette>=2.1",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
```

运行: `cd backend && uv init && uv add fastapi uvicorn[standard] sqlalchemy[asyncio] alembic aiomysql pydantic pydantic-settings 'passlib[bcrypt]' 'python-jose[cryptography]' slowapi httpx python-multipart PyMuPDF python-docx langchain-text-splitters sse-starlette pytest pytest-asyncio`

- [ ] **Step 2: 创建配置模块**

```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "mysql+aiomysql://chatbot:changeme@localhost:3306/chatbot"
    
    # JWT
    secret_key: str = "change-me-in-production-at-least-32-chars"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    algorithm: str = "HS256"
    
    # LLM
    default_llm_provider: str = "xingchen"
    xingchen_api_key: str = ""
    xingchen_base_url: str = ""
    xingchen_model: str = "xingchen-pro"
    xingchen_embed_model: str = "xingchen-embedding"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"
    
    # Rate Limiting
    rate_limit_general: str = "60/minute"
    rate_limit_llm: str = "20/minute"
    
    # File Upload
    max_file_size: int = 10485760
    sync_process_threshold: int = 5242880
    
    # RAG
    rag_top_k: int = 5
    rag_chunk_size: int = 500
    rag_chunk_overlap: int = 50
    
    class Config:
        env_file = ".env"
        env_prefix = ""

settings = Settings()
```

- [ ] **Step 3: 创建 FastAPI 入口**

```python
# backend/app/main.py
from fastapi import FastAPI

app = FastAPI(title="ChatBot API", version="0.1.0")

@app.get("/health")
async def health():
    return {"status": "ok"}
```

- [ ] **Step 4: 验证启动**

运行: `cd backend && uv run uvicorn app.main:app --reload --port 8000`
访问 `http://localhost:8000/health` 返回 `{"status": "ok"}`

- [ ] **Step 5: Commit**

```bash
git add backend/
git commit -m "feat: init backend project with config and health check"
```

### Task 2: 数据库模型 + 迁移

**Files:**
- Create: `backend/app/core/database.py`
- Create: `backend/app/models/__init__.py`
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/conversation.py`
- Create: `backend/app/models/message.py`
- Create: `backend/app/models/document.py`
- Init: `backend/alembic/` (alembic init)

**Interfaces:**
- Produces: `async_session_maker` (数据库 Session 工厂), `Base` (SQLAlchemy Declarative Base)
- Produces: ORM 模类: `User`, `Conversation`, `Message`, `Document`, `DocumentChunk`

- [ ] **Step 1: 创建数据库引擎和 Session**

```python
# backend/app/core/database.py
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

engine = create_async_engine(settings.database_url, echo=True, pool_pre_ping=True)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def get_db():
    async with async_session_maker() as session:
        yield session
```

- [ ] **Step 2: 创建 ORM 模型**

```python
# backend/app/models/user.py
from sqlalchemy import BigInteger, String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

```python
# backend/app/models/conversation.py
class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False, default="新对话")
    model_provider: Mapped[str] = mapped_column(String(50), nullable=False)
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    # relationship
    messages: Mapped[list["Message"]] = relationship(back_populates="conversation", cascade="all, delete-orphan")
```

```python
# backend/app/models/message.py
class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(Enum("user", "assistant", "system"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    parent_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # relationship
    conversation: Mapped["Conversation"] = relationship(back_populates="messages")
```

```python
# backend/app/models/document.py
class Document(Base):
    __tablename__ = "documents"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(20), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(Enum("processing", "ready", "failed"), nullable=False, default="processing")
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    # relationship
    chunks: Mapped[list["DocumentChunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")

class DocumentChunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    document_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # VECTOR as JSON string fallback
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    # relationship
    document: Mapped["Document"] = relationship(back_populates="chunks")
```

> 注: embedding 列先用 Text 存 JSON 字符串（兼容 MySQL 8.0），生产环境用 MySQL 9.0 时改为 `VECTOR(1536)` 类型

- [ ] **Step 3: 初始化 Alembic**

运行: `cd backend && uv run alembic init alembic`
修改 `alembic/env.py` 引入 `Base.metadata`，设置 `target_metadata = Base.metadata`
修改 `alembic.ini` 的 `sqlalchemy.url` 指向测试数据库

- [ ] **Step 4: 生成迁移**

运行: `cd backend && uv run alembic revision --autogenerate -m "create all tables"`
检查生成的迁移文件，确保 5 张表均正确

- [ ] **Step 5: 运行迁移**

运行: `cd backend && uv run alembic upgrade head`
验证数据库中 5 张表已创建

- [ ] **Step 6: Commit**

```bash
git add backend/
git commit -m "feat: add database models and initial migration"
```

### Task 3: 前端项目初始化

**Files:**
- Create: `frontend/` (Vite + React + TS 脚手架)
- Create: `frontend/src/App.tsx`
- Create: `frontend/src/router/index.tsx`
- Create: `frontend/src/pages/Login.tsx`
- Create: `frontend/src/layouts/ChatLayout.tsx`

**Interfaces:**
- Produces: 可运行的前端骨架，含路由和空白页面

- [ ] **Step 1: 创建 Vite React 项目**

运行: `cd D:\CODES\AICodeStudy\ChatBot && npm create vite@latest frontend -- --template react-ts`
运行: `cd frontend && npm install`
安装依赖: `npm install antd zustand axios react-router-dom markdown-it highlight.js`
安装 dev 依赖: `npm install -D @types/markdown-it @types/highlight.js`

- [ ] **Step 2: 配置 Vite 代理**

```typescript
// frontend/vite.config.ts
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
    }
  }
})
```

- [ ] **Step 3: 创建路由和基础页面**

```typescript
// frontend/src/router/index.tsx
import { createBrowserRouter } from 'react-router-dom'
import Login from '../pages/Login'
import Chat from '../pages/Chat'
import Documents from '../pages/Documents'
import ChatLayout from '../layouts/ChatLayout'

export const router = createBrowserRouter([
  { path: '/login', element: <Login /> },
  {
    path: '/',
    element: <ChatLayout />,
    children: [
      { path: 'chat', element: <Chat /> },
      { path: 'documents', element: <Documents /> },
    ]
  }
])
```

- [ ] **Step 4: 验证启动**

运行: `cd frontend && npm run dev`
访问 `http://localhost:5173` 看到页面渲染

- [ ] **Step 5: Commit**

```bash
git add frontend/
git commit -m "feat: init frontend project with routing"
```

---

## M2: 认证模块

### Task 4: 安全工具 + 认证服务

**Files:**
- Create: `backend/app/core/security.py`
- Create: `backend/app/deps/__init__.py`
- Create: `backend/app/deps/auth.py`
- Create: `backend/app/services/auth_service.py`
- Create: `backend/app/schemas/auth.py`
- Test: `backend/tests/test_auth.py`

**Interfaces:**
- Produces: `create_access_token(user_id)`, `create_refresh_token(user_id)`, `verify_token(token)`, `hash_password(plain)`, `verify_password(plain, hash)`, `get_current_user()` (FastAPI dependency)
- Consumes: `User` model, `settings`

- [ ] **Step 1: 写测试 — 注册和登录**

```python
# backend/tests/test_auth.py
async def test_register_success(client):
    response = await client.post("/api/v1/auth/register", json={
        "username": "testuser", "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

async def test_register_duplicate(client):
    await client.post("/api/v1/auth/register", json={
        "username": "testuser", "password": "testpass123"
    })
    response = await client.post("/api/v1/auth/register", json={
        "username": "testuser", "password": "testpass123"
    })
    assert response.status_code == 409

async def test_login_success(client):
    await client.post("/api/v1/auth/register", json={
        "username": "testuser", "password": "testpass123"
    })
    response = await client.post("/api/v1/auth/login", json={
        "username": "testuser", "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

async def test_login_wrong_password(client):
    response = await client.post("/api/v1/auth/login", json={
        "username": "testuser", "password": "wrong"
    })
    assert response.status_code == 401

async def test_me_without_token(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401

async def test_me_with_token(client, auth_token):
    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {auth_token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && uv run pytest tests/test_auth.py -v`
Expected: FAIL (路由不存在)

- [ ] **Step 3: 实现安全工具**

```python
# backend/app/core/security.py
from passlib.context import CryptContext
from jose import jwt, JWTError
from datetime import datetime, timedelta, timezone
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"])

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode({"sub": str(user_id), "exp": expire}, settings.secret_key, algorithm=settings.algorithm)

def create_refresh_token(user_id: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    return jwt.encode({"sub": str(user_id), "exp": expire, "type": "refresh"}, settings.secret_key, algorithm=settings.algorithm)

def verify_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None
```

- [ ] **Step 4: 实现认证服务和依赖注入**

```python
# backend/app/services/auth_service.py
async def register(db: AsyncSession, username: str, password: str) -> User:
    existing = await db.scalar(select(User).where(User.username == username))
    if existing:
        raise ChatBotException("USERNAME_EXISTS", "用户名已存在", 409)
    user = User(username=username, password_hash=hash_password(password))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

async def login(db: AsyncSession, username: str, password: str) -> User:
    user = await db.scalar(select(User).where(User.username == username))
    if not user or not verify_password(password, user.password_hash):
        raise ChatBotException("INVALID_CREDENTIALS", "用户名或密码错误", 401)
    return user
```

```python
# backend/app/deps/auth.py
async def get_current_user(token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)) -> User:
    payload = verify_token(token)
    if not payload:
        raise HTTPException(401, "无效的认证凭据")
    user = await db.scalar(select(User).where(User.id == int(payload["sub"])))
    if not user:
        raise HTTPException(401, "用户不存在")
    return user
```

- [ ] **Step 5: 实现认证路由**

```python
# backend/app/api/v1/auth.py
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
async def register(body: RegisterRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.register(db, body.username, body.password)
    return {"access_token": create_access_token(user.id), "token_type": "bearer",
            "user": {"id": user.id, "username": user.username}}

@router.post("/login")
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await auth_service.login(db, body.username, body.password)
    return {"access_token": create_access_token(user.id),
            "refresh_token": create_refresh_token(user.id), "token_type": "bearer",
            "user": {"id": user.id, "username": user.username}}

@router.get("/me")
async def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "created_at": user.created_at}
```

- [ ] **Step 6: 运行测试验证通过**

运行: `cd backend && uv run pytest tests/test_auth.py -v`
Expected: 5 PASS

- [ ] **Step 7: Commit**

```bash
git add backend/
git commit -m "feat: implement auth module (register/login/me) with JWT"
```

---

## M3: LLM 抽象层

### Task 5: LLM Provider 接口 + 实现

**Files:**
- Create: `backend/app/llm/__init__.py`
- Create: `backend/app/llm/base.py`
- Create: `backend/app/llm/schemas.py`
- Create: `backend/app/llm/factory.py`
- Create: `backend/app/llm/providers/__init__.py`
- Create: `backend/app/llm/providers/xingchen.py`
- Create: `backend/app/llm/providers/openai_provider.py`
- Test: `backend/tests/test_llm.py`

**Interfaces:**
- Produces: `LLMProvider` (ABC), `LLMFactory.get_provider(name)`, `LLMMessage`, `ChatResult`
- Consumes: `settings` (Provider 配置)

- [ ] **Step 1: 写测试 — Mock Provider + 工厂**

```python
# backend/tests/test_llm.py
async def test_factory_returns_provider():
    provider = LLMFactory.get_provider("mock")
    assert isinstance(provider, LLMProvider)

async def test_stream_chat_yields_tokens():
    provider = LLMFactory.get_provider("mock")
    tokens = []
    async for token in provider.stream_chat([LLMMessage(role="user", content="hi")]):
        tokens.append(token)
    assert "".join(tokens) == "你好世界"

async def test_embed_returns_vector():
    provider = LLMFactory.get_provider("mock")
    vector = await provider.embed("hello")
    assert len(vector) == 1536
    assert all(isinstance(v, float) for v in vector)

async def test_embed_batch():
    provider = LLMFactory.get_provider("mock")
    vectors = await provider.embed_batch(["hello", "world"])
    assert len(vectors) == 2
    assert len(vectors[0]) == 1536
```

- [ ] **Step 2: 运行测试验证失败**

运行: `cd backend && uv run pytest tests/test_llm.py -v`
Expected: FAIL

- [ ] **Step 3: 实现基类和数据结构**

```python
# backend/app/llm/schemas.py
from pydantic import BaseModel
from typing import Literal

class LLMMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class ChatResult(BaseModel):
    content: str
    tokens: int
    model: str
```

```python
# backend/app/llm/base.py
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from app.llm.schemas import LLMMessage, ChatResult

class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[LLMMessage], **kwargs) -> ChatResult: ...
    
    @abstractmethod
    async def stream_chat(self, messages: list[LLMMessage], **kwargs) -> AsyncGenerator[str, None]: ...
    
    @abstractmethod
    async def embed(self, text: str) -> list[float]: ...
    
    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]: ...
```

- [ ] **Step 4: 实现 Mock Provider (测试用)**

```python
# backend/app/llm/providers/mock.py
class MockProvider(LLMProvider):
    async def chat(self, messages, **kwargs):
        return ChatResult(content="你好世界", tokens=4, model="mock")
    
    async def stream_chat(self, messages, **kwargs):
        for token in ["你", "好", "世", "界"]:
            yield token
    
    async def embed(self, text):
        return [0.1] * 1536
    
    async def embed_batch(self, texts):
        return [[0.1] * 1536 for _ in texts]
```

- [ ] **Step 5: 实现工厂**

```python
# backend/app/llm/factory.py
from app.llm.base import LLMProvider
from app.llm.providers.mock import MockProvider
from app.llm.providers.openai_provider import OpenAIProvider
from app.llm.providers.xingchen import XingchenProvider
from app.core.config import settings

class LLMFactory:
    _instances: dict[str, LLMProvider] = {}
    
    @classmethod
    def get_provider(cls, name: str | None = None) -> LLMProvider:
        name = name or settings.default_llm_provider
        if name not in cls._instances:
            providers = {
                "mock": MockProvider,
                "openai": OpenAIProvider,
                "xingchen": XingchenProvider,
            }
            cls._instances[name] = providers[name]()
        return cls._instances[name]
    
    @classmethod
    def get_available_providers(cls) -> list[dict]:
        return [
            {"name": "xingchen", "display_name": "星辰大模型", "models": [settings.xingchen_model]},
            {"name": "openai", "display_name": "OpenAI GPT", "models": [settings.openai_model]},
        ]
```

- [ ] **Step 6: 实现 OpenAI Provider (兼容星辰 OpenAI 兼容接口)**

```python
# backend/app/llm/providers/openai_provider.py
import httpx
from app.llm.base import LLMProvider
from app.llm.schemas import LLMMessage, ChatResult
from app.core.config import settings

class OpenAIProvider(LLMProvider):
    def __init__(self):
        self.api_key = settings.openai_api_key
        self.base_url = settings.openai_base_url
        self.model = settings.openai_model
        self.embed_model = settings.openai_embed_model
    
    async def chat(self, messages, **kwargs):
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model,
                      "messages": [{"role": m.role, "content": m.content} for m in messages],
                      **kwargs})
            resp.raise_for_status()
            data = resp.json()
            return ChatResult(content=data["choices"][0]["message"]["content"],
                             tokens=data["usage"]["total_tokens"], model=self.model)
    
    async def stream_chat(self, messages, **kwargs):
        async with httpx.AsyncClient() as client:
            async with client.stream("POST", f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.model, "stream": True,
                      "messages": [{"role": m.role, "content": m.content} for m in messages],
                      **kwargs}) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        import json
                        data = json.loads(line[6:])
                        if data["choices"][0]["delta"].get("content"):
                            yield data["choices"][0]["delta"]["content"]
    
    async def embed(self, text):
        result = await self.embed_batch([text])
        return result[0]
    
    async def embed_batch(self, texts):
        async with httpx.AsyncClient() as client:
            resp = await client.post(f"{self.base_url}/embeddings",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"model": self.embed_model, "input": texts})
            resp.raise_for_status()
            data = resp.json()
            return [item["embedding"] for item in data["data"]]
```

- [ ] **Step 7: 运行测试验证通过**

运行: `cd backend && uv run pytest tests/test_llm.py -v`
Expected: 4 PASS

- [ ] **Step 8: Commit**

```bash
git add backend/
git commit -m "feat: implement LLM abstraction layer with Mock and OpenAI providers"
```

---

## M4: 会话 + 消息 + SSE

### Task 6: 会话 CRUD API

**Files:**
- Create: `backend/app/schemas/conversation.py`
- Create: `backend/app/schemas/message.py`
- Create: `backend/app/services/chat_service.py` (会话部分)
- Create: `backend/app/api/v1/conversations.py`
- Test: `backend/tests/test_conversations.py`

- [ ] **Step 1: 写测试 — 会话 CRUD + 数据隔离**

```python
# backend/tests/test_conversations.py
async def test_create_conversation(auth_client):
    response = await auth_client.post("/api/v1/conversations", json={"model_provider": "mock"})
    assert response.status_code == 201
    assert response.json()["title"] == "新对话"

async def test_list_conversations(auth_client):
    await auth_client.post("/api/v1/conversations", json={"model_provider": "mock"})
    response = await auth_client.get("/api/v1/conversations")
    assert response.status_code == 200
    assert len(response.json()["items"]) == 1

async def test_rename_conversation(auth_client):
    created = await auth_client.post("/api/v1/conversations", json={"model_provider": "mock"})
    cid = created.json()["id"]
    response = await auth_client.patch(f"/api/v1/conversations/{cid}", json={"title": "测试标题"})
    assert response.status_code == 200
    assert response.json()["title"] == "测试标题"

async def test_delete_conversation(auth_client):
    created = await auth_client.post("/api/v1/conversations", json={"model_provider": "mock"})
    cid = created.json()["id"]
    response = await auth_client.delete(f"/api/v1/conversations/{cid}")
    assert response.status_code == 204

async def test_isolation_between_users(auth_client, auth_client2):
    created = await auth_client.post("/api/v1/conversations", json={"model_provider": "mock"})
    cid = created.json()["id"]
    response = await auth_client2.get(f"/api/v1/conversations/{cid}")
    assert response.status_code == 404
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 实现 ChatService 会话部分**

```python
# backend/app/services/chat_service.py
async def create_conversation(db: AsyncSession, user_id: int, model_provider: str, system_prompt: str | None = None) -> Conversation:
    conv = Conversation(user_id=user_id, model_provider=model_provider, system_prompt=system_prompt)
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv

async def list_conversations(db: AsyncSession, user_id: int, skip: int = 0, limit: int = 20):
    result = await db.execute(
        select(Conversation).where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc()).offset(skip).limit(limit))
    convs = result.scalars().all()
    total = await db.scalar(select(func.count()).where(Conversation.user_id == user_id))
    return convs, total

async def get_conversation(db: AsyncSession, user_id: int, conv_id: int) -> Conversation:
    conv = await db.scalar(select(Conversation).where(Conversation.id == conv_id, Conversation.user_id == user_id))
    if not conv:
        raise ChatBotException("NOT_FOUND", "会话不存在", 404)
    return conv

async def rename_conversation(db: AsyncSession, user_id: int, conv_id: int, title: str) -> Conversation:
    conv = await get_conversation(db, user_id, conv_id)
    conv.title = title
    await db.commit()
    await db.refresh(conv)
    return conv

async def delete_conversation(db: AsyncSession, user_id: int, conv_id: int):
    conv = await get_conversation(db, user_id, conv_id)
    await db.delete(conv)
    await db.commit()
```

- [ ] **Step 4: 实现会话路由**

```python
# backend/app/api/v1/conversations.py
router = APIRouter(prefix="/conversations", tags=["conversations"])

@router.post("")
async def create(body: ConversationCreate, user: User = Depends(get_current_user), db = Depends(get_db)):
    conv = await chat_service.create_conversation(db, user.id, body.model_provider, body.system_prompt)
    return conv  # 序列化

@router.get("")
async def list_(skip: int = 0, limit: int = 20, user = Depends(get_current_user), db = Depends(get_db)):
    convs, total = await chat_service.list_conversations(db, user.id, skip, limit)
    return {"items": convs, "total": total}

# ... get, patch, delete 类似
```

- [ ] **Step 5: 运行测试验证通过**

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: implement conversation CRUD with user isolation"
```

### Task 7: 消息发送 + SSE 流式回复

**Files:**
- Modify: `backend/app/services/chat_service.py` (追加消息方法)
- Create: `backend/app/api/v1/messages.py`
- Create: `backend/app/core/exceptions.py`
- Test: `backend/tests/test_messages.py`

**Interfaces:**
- Produces: `POST /conversations/{cid}/messages` (SSE), `POST /conversations/{cid}/messages/{id}/regenerate` (SSE), `POST /conversations/{cid}/messages/{id}/stop`

- [ ] **Step 1: 写测试 — 消息发送 + SSE 事件**

```python
# backend/tests/test_messages.py
async def test_send_message_sse(auth_client):
    # 创建会话
    conv = await auth_client.post("/api/v1/conversations", json={"model_provider": "mock"})
    cid = conv.json()["id"]
    # 发送消息
    response = await auth_client.post(f"/api/v1/conversations/{cid}/messages",
        json={"content": "你好", "rag_enabled": False})
    assert response.status_code == 200
    assert "text/event-stream" in response.headers["content-type"]
    # 解析 SSE 事件
    events = parse_sse_response(response.text)
    assert any(e["event"] == "start" for e in events)
    assert any(e["event"] == "token" for e in events)
    assert any(e["event"] == "done" for e in events)

async def test_message_persisted(auth_client, db_session):
    # ... 发送消息后查询数据库验证 user 消息和 assistant 消息已存
    pass

async def test_stop_generation(auth_client):
    # ... 发送消息后立即调 stop，验证部分内容存库
    pass

async def test_regenerate(auth_client):
    # ... 先发消息，再 regenerate，验证 parent_message_id 正确
    pass
```

- [ ] **Step 2: 运行测试验证失败**

- [ ] **Step 3: 实现异常体系**

```python
# backend/app/core/exceptions.py
class ChatBotException(Exception):
    def __init__(self, code: str, message: str, status: int = 400):
        self.code = code
        self.message = message
        self.status = status

class LLMProviderError(ChatBotException):
    def __init__(self, message="LLM 调用失败"):
        super().__init__("LLM_ERROR", message, 502)

class NotFoundError(ChatBotException):
    def __init__(self, message="资源不存在"):
        super().__init__("NOT_FOUND", message, 404)
```

- [ ] **Step 4: 实现 ChatService 消息部分**

```python
# backend/app/services/chat_service.py (追加)

# 取消标志位 (生产环境用 Redis)
_cancel_flags: dict[int, bool] = {}

async def save_user_message(db, conv_id, content, parent_id=None) -> Message:
    msg = Message(conversation_id=conv_id, role="user", content=content, parent_message_id=parent_id)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg

async def build_context(db, conv_id, user_id, rag_enabled=False) -> list[LLMMessage]:
    conv = await get_conversation(db, user_id, conv_id)
    messages_list = []
    # system prompt
    if conv.system_prompt:
        messages_list.append(LLMMessage(role="system", content=conv.system_prompt))
    # RAG (如果有)
    if rag_enabled:
        # M6 实现
        pass
    # 历史消息 (最近20条, parent_message_id IS NULL)
    result = await db.execute(
        select(Message).where(Message.conversation_id == conv_id, Message.parent_message_id.is_(None))
        .order_by(Message.created_at.desc()).limit(20))
    history = result.scalars().all()
    history = list(reversed(history))  # 按时间正序
    messages_list.extend([LLMMessage(role=m.role, content=m.content) for m in history])
    return messages_list

async def save_assistant_message(db, conv_id, content, parent_id=None) -> Message:
    msg = Message(conversation_id=conv_id, role="assistant", content=content, parent_message_id=parent_id, tokens=len(content))
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg
```

- [ ] **Step 5: 实现 SSE 消息路由**

```python
# backend/app/api/v1/messages.py
from sse_starlette.sse import EventSourceResponse

router = APIRouter(prefix="/conversations/{cid}/messages", tags=["messages"])

def format_sse(event: str, data: dict) -> dict:
    return {"event": event, "data": json.dumps(data, ensure_ascii=False)}

@router.post("")
async def send_message(cid: int, body: MessageCreate, user: User = Depends(get_current_user), db = Depends(get_db)):
    conv = await chat_service.get_conversation(db, user.id, cid)
    provider = LLMFactory.get_provider(conv.model_provider)
    
    async def event_generator():
        try:
            # 存 user 消息
            user_msg = await chat_service.save_user_message(db, cid, body.content, body.parent_message_id)
            # 构建上下文
            context = await chat_service.build_context(db, cid, user.id, body.rag_enabled)
            # start
            yield format_sse("start", {"message_id": 0})
            # 流式生成
            full_content = ""
            async for token in provider.stream_chat(context):
                full_content += token
                yield format_sse("token", {"content": token})
            # 存 assistant 消息
            assistant_msg = await chat_service.save_assistant_message(db, cid, full_content, parent_id=None)
            # done
            yield format_sse("done", {"message_id": assistant_msg.id, "tokens": assistant_msg.tokens})
        except Exception as e:
            yield format_sse("error", {"message": str(e)})
    
    return EventSourceResponse(event_generator())

@router.post("/{mid}/stop")
async def stop_message(cid: int, mid: int, user: User = Depends(get_current_user)):
    chat_service._cancel_flags[mid] = True
    return {"stopped": True, "message_id": mid}
```

- [ ] **Step 6: 运行测试验证通过**

- [ ] **Step 7: Commit**

```bash
git commit -m "feat: implement message sending with SSE streaming"
```

### Task 8: 模型列表 + 限流

**Files:**
- Create: `backend/app/api/v1/llm.py` (providers 列表)
- Create: `backend/app/middleware/rate_limit.py`
- Modify: `backend/app/main.py` (注册限流中间件)

- [ ] **Step 1: 实现模型列表接口**

```python
# backend/app/api/v1/llm.py
@router.get("/providers")
async def list_providers(user: User = Depends(get_current_user)):
    return {"providers": LLMFactory.get_available_providers()}
```

- [ ] **Step 2: 实现限流中间件**

```python
# backend/app/middleware/rate_limit.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
```

- [ ] **Step 3: 在消息路由上加限流**

```python
# messages.py
@router.post("", dependencies=[Depends(RateLimiter(f"20/minute"))])
```

- [ ] **Step 4: 测试 + Commit**

```bash
git commit -m "feat: add provider list endpoint and rate limiting"
```

---

## M5: 前端对话核心

### Task 9: 认证前端 (登录/注册 + Auth Store)

**Files:**
- Create: `frontend/src/stores/authStore.ts`
- Create: `frontend/src/services/api.ts`
- Create: `frontend/src/services/authApi.ts`
- Create: `frontend/src/pages/Login.tsx`
- Create: `frontend/src/types/index.ts`

- [ ] **Step 1: 定义类型**

```typescript
// frontend/src/types/index.ts
export interface User { id: number; username: string; }
export interface AuthResponse { access_token: string; refresh_token: string; user: User; }
export interface Conversation {
  id: number; title: string; model_provider: string;
  system_prompt: string | null; created_at: string; updated_at: string;
  messages?: Message[];
}
export interface Message {
  id: number; role: 'user' | 'assistant' | 'system'; content: string;
  tokens: number; parent_message_id: number | null; created_at: string;
}
export interface Document {
  id: number; filename: string; file_type: string; file_size: number;
  status: 'processing' | 'ready' | 'failed'; chunk_count: number; created_at: string;
}
export interface Provider {
  name: string; display_name: string; models: string[];
}
```

- [ ] **Step 2: 实现 Axios 实例 + 拦截器**

```typescript
// frontend/src/services/api.ts
import axios from 'axios';
import { useAuthStore } from '../stores/authStore';

export const api = axios.create({ baseURL: '/api/v1' });

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);
```

- [ ] **Step 3: 实现 authStore**

```typescript
// frontend/src/stores/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  user: User | null;
  login: (token: string, user: User) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist((set) => ({
    token: null, user: null,
    login: (token, user) => set({ token, user }),
    logout: () => set({ token: null, user: null }),
  }), { name: 'chatbot-auth' })
);
```

- [ ] **Step 4: 实现登录/注册页面**

```typescript
// frontend/src/pages/Login.tsx
// Ant Design Form, 支持登录/注册切换
// 注册成功自动 login
// 登录成功跳转 /chat
```

- [ ] **Step 5: 浏览器验证**

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: implement login/register page with auth store"
```

### Task 10: SSE Hook + Chat Store

**Files:**
- Create: `frontend/src/hooks/useSSE.ts`
- Create: `frontend/src/utils/sse-parser.ts`
- Create: `frontend/src/stores/chatStore.ts`

- [ ] **Step 1: 实现 SSE 解析工具**

```typescript
// frontend/src/utils/sse-parser.ts
export interface SSEEvent { event: string; data: any; }

export function parseSSEEvents(buffer: string): { events: SSEEvent[]; remainder: string } {
  const events: SSEEvent[] = [];
  const chunks = buffer.split('\n\n');
  const remainder = chunks.pop() || '';

  for (const chunk of chunks) {
    if (!chunk.trim()) continue;
    const lines = chunk.split('\n');
    let event = '', data = '';
    for (const line of lines) {
      if (line.startsWith('event: ')) event = line.slice(7);
      if (line.startsWith('data: ')) data = line.slice(6);
    }
    if (event) events.push({ event, data: JSON.parse(data) });
  }
  return { events, remainder };
}
```

- [ ] **Step 2: 实现 useSSE Hook**

```typescript
// frontend/src/hooks/useSSE.ts
import { useRef } from 'react';
import { useAuthStore } from '../stores/authStore';
import { parseSSEEvents } from '../utils/sse-parser';

export function useSSE() {
  const abortRef = useRef<AbortController | null>(null);

  const sendMessage = async (url: string, body: any, callbacks: {
    onStart?: (d: any) => void;
    onToken?: (d: any) => void;
    onDone?: (d: any) => void;
    onError?: (d: any) => void;
  }) => {
    abortRef.current = new AbortController();
    const token = useAuthStore.getState().token;

    const response = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
      body: JSON.stringify(body),
      signal: abortRef.current.signal,
    });

    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const { events, remainder } = parseSSEEvents(buffer);
      buffer = remainder;
      for (const evt of events) {
        switch (evt.event) {
          case 'start': callbacks.onStart?.(evt.data); break;
          case 'token': callbacks.onToken?.(evt.data); break;
          case 'done': callbacks.onDone?.(evt.data); break;
          case 'error': callbacks.onError?.(evt.data); break;
        }
      }
    }
  };

  const stop = () => abortRef.current?.abort();
  return { sendMessage, stop };
}
```

- [ ] **Step 3: 实现 chatStore**

```typescript
// frontend/src/stores/chatStore.ts
interface ChatState {
  conversations: Conversation[];
  currentId: number | null;
  messagesMap: Record<number, Message[]>;
  isStreaming: boolean;
  streamingContent: string;

  loadConversations: () => Promise<void>;
  selectConversation: (id: number) => Promise<void>;
  createConversation: (provider: string) => Promise<void>;
  deleteConversation: (id: number) => Promise<void>;
  appendToken: (token: string) => void;
  startStreaming: () => void;
  finishStreaming: (msg: Message) => void;
}
// ... 完整实现
```

- [ ] **Step 4: Commit**

```bash
git commit -m "feat: implement SSE hook and chat store"
```

### Task 11: 聊天界面组件

**Files:**
- Create: `frontend/src/components/chat/ChatWindow.tsx`
- Create: `frontend/src/components/chat/MessageList.tsx`
- Create: `frontend/src/components/chat/MessageBubble.tsx`
- Create: `frontend/src/components/chat/MarkdownRenderer.tsx`
- Create: `frontend/src/components/chat/InputArea.tsx`
- Create: `frontend/src/components/chat/StreamingCursor.tsx`
- Create: `frontend/src/components/sidebar/ConversationList.tsx`
- Create: `frontend/src/components/sidebar/ConversationItem.tsx`
- Create: `frontend/src/components/common/ModelSelector.tsx`
- Create: `frontend/src/pages/Chat.tsx`
- Modify: `frontend/src/layouts/ChatLayout.tsx`

- [ ] **Step 1: 实现 ChatLayout (侧边栏 + 内容区)**

```typescript
// 布局: 左侧 collapsible sidebar (会话列表 + 新建按钮 + 导航)
// 右侧 Outlet (Chat 或 Documents)
// 顶部: 用户信息 + 退出登录
```

- [ ] **Step 2: 实现 MarkdownRenderer**

```typescript
// markdown-it 实例 + highlight.js 代码高亮
// 流式 mode: 直接渲染可能不完整的 markdown
// 完成 mode: 完整渲染
```

- [ ] **Step 3: 实现 MessageBubble + MessageList**

```typescript
// 用户消息右对齐, AI 左对齐
// AI 消息下方: 重新生成按钮
// 用户消息: 编辑按钮
// 流式消息: 追加 streamingContent + 光标
```

- [ ] **Step 4: 实现 InputArea**

```typescript
// TextArea 自适应高度
// 回车发送, Shift+回车换行
// 流式中: 发送按钮变停止按钮
// 空消息禁止发送
```

- [ ] **Step 5: 实现 Chat 页面 (组合所有组件)**

```typescript
// Chat 页面 = ModelSelector + ChatWindow + InputArea + RAG 开关
// useSSE 发送消息
// chatStore 管理状态
```

- [ ] **Step 6: 实现会话侧边栏**

```typescript
// ConversationList: 新建按钮 + 列表
// ConversationItem: 标题 (可编辑) + 删除按钮
```

- [ ] **Step 7: 浏览器验证完整流程**

注册 → 登录 → 新建会话 → 发消息 → 看到流式回复 → 停止 → 重新生成 → 编辑重发 → 切换会话 → 删除会话

- [ ] **Step 8: Commit**

```bash
git commit -m "feat: implement chat UI with streaming, markdown, and conversation sidebar"
```

---

## M6: RAG 模块

### Task 12: 文档处理管线 (解析+分块+向量化)

**Files:**
- Create: `backend/app/rag/__init__.py`
- Create: `backend/app/rag/parser.py`
- Create: `backend/app/rag/splitter.py`
- Create: `backend/app/rag/cleaner.py`

- [ ] **Step 1: 实现文件解析器**

```python
# backend/app/rag/parser.py
import fitz  # PyMuPDF
from docx import Document as DocxDocument
from pathlib import Path

class FileParser:
    @staticmethod
    def parse(file_path: str, file_type: str) -> str:
        parser_map = {
            "pdf": FileParser._parse_pdf,
            "docx": FileParser._parse_docx,
            "txt": FileParser._parse_txt,
            "md": FileParser._parse_txt,
        }
        return parser_map[file_type](file_path)
    
    @staticmethod
    def _parse_pdf(path: str) -> str:
        doc = fitz.open(path)
        return "\n\n".join(page.get_text() for page in doc)
    
    @staticmethod
    def _parse_docx(path: str) -> str:
        doc = DocxDocument(path)
        return "\n\n".join(para.text for para in doc.paragraphs if para.text.strip())
    
    @staticmethod
    def _parse_txt(path: str) -> str:
        return Path(path).read_text(encoding="utf-8")
```

- [ ] **Step 2: 实现分块器**

```python
# backend/app/rag/splitter.py
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings

class TextSplitter:
    def __init__(self):
        self.splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.rag_chunk_size,
            chunk_overlap=settings.rag_chunk_overlap,
            separators=["\n\n", "\n", "。", " ", ""]
        )
    
    def split(self, text: str) -> list[str]:
        return self.splitter.split_text(text)
```

- [ ] **Step 3: Commit**

```bash
git commit -m "feat: implement RAG document pipeline (parser + splitter)"
```

### Task 13: 文档 API + RAG 检索

**Files:**
- Create: `backend/app/services/document_service.py`
- Create: `backend/app/services/rag_service.py`
- Create: `backend/app/schemas/document.py`
- Create: `backend/app/api/v1/documents.py`
- Test: `backend/tests/test_documents.py`

- [ ] **Step 1: 写测试 — 文档上传 + 删除 + 状态**

- [ ] **Step 2: 实现 DocumentService**

```python
# 上传 → 解析 → 分块 → 向量化 → 存储
async def upload_document(db, user_id, file: UploadFile) -> Document:
    # 保存文件
    # 创建 Document 记录
    # 解析+分块+向量化
    # 批量写入 DocumentChunk
    # 更新 status=ready
    pass

async def delete_document(db, user_id, doc_id):
    # 级联删除
    pass
```

- [ ] **Step 3: 实现 RAGService**

```python
# backend/app/services/rag_service.py
async def retrieve(db, question: str, user_id: int, top_k: int = 5) -> str | None:
    provider = LLMFactory.get_provider()
    query_vector = await provider.embed(question)
    # MySQL VECTOR 检索 (或 JSON 降级方案)
    # 返回拼接的上下文字符串
    pass
```

- [ ] **Step 4: 实现文档路由**

- [ ] **Step 5: 在 ChatService.build_context 中接入 RAG**

```python
if rag_enabled:
    rag_context = await rag_service.retrieve(db, last_user_content, user_id)
    if rag_context:
        messages_list.insert(0, LLMMessage(role="system", content=rag_context))
```

- [ ] **Step 6: 测试 + Commit**

```bash
git commit -m "feat: implement document upload, RAG retrieval, and context injection"
```

---

## M7: 前端文档管理

### Task 14: 文档管理页面

**Files:**
- Create: `frontend/src/pages/Documents.tsx`
- Create: `frontend/src/components/common/UploadButton.tsx`
- Create: `frontend/src/services/documentApi.ts`
- Create: `frontend/src/stores/settingsStore.ts` (RAG 开关)

- [ ] **Step 1: 实现文档 API 调用**

- [ ] **Step 2: 实现上传按钮 (拖拽 + 进度)**

- [ ] **Step 3: 实现文档列表 (Ant Design Table)**

- [ ] **Step 4: 实现 RAG 开关**

- [ ] **Step 5: 浏览器验证**

上传文档 → 看到处理中 → 变为 ready → 在对话中开启 RAG → 提问 → 获得基于文档的回答

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: implement document management page with RAG toggle"
```

---

## M8: Docker 部署

### Task 15: Docker 编排

**Files:**
- Create: `backend/Dockerfile`
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`
- Create: `docker-compose.yml`
- Create: `.env.example`

- [ ] **Step 1: 实现后端 Dockerfile**

```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen
COPY . .
RUN uv run alembic upgrade head
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 2: 实现前端 Dockerfile + Nginx**

```dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

```nginx
# nginx.conf
server {
    listen 80;
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    location ~ ^/api/v1/conversations/.*/messages$ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
        chunked_transfer_encoding on;
    }
}
```

- [ ] **Step 3: 实现 docker-compose.yml**

```yaml
services:
  mysql:
    image: mysql/mysql-server:9.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: chatbot
      MYSQL_USER: ${MYSQL_USER}
      MYSQL_PASSWORD: ${MYSQL_PASSWORD}
    volumes:
      - mysql_data:/var/lib/mysql
    ports:
      - "3306:3306"

  backend:
    build: ./backend
    environment:
      DATABASE_URL: mysql+aiomysql://chatbot:${MYSQL_PASSWORD}@mysql:3306/chatbot
      SECRET_KEY: ${SECRET_KEY}
    depends_on:
      - mysql
    ports:
      - "8000:8000"

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend

volumes:
  mysql_data:
```

- [ ] **Step 4: 创建 .env.example**

- [ ] **Step 5: 测试 docker compose up**

运行: `docker compose up --build`
访问 `http://localhost` 验证全链路

- [ ] **Step 6: Commit**

```bash
git commit -m "feat: add Docker Compose deployment with Nginx SSE config"
```

---

## M9: 集成测试 + 打磨

### Task 16: 端到端集成测试

**Files:**
- Test: `backend/tests/test_e2e.py`

- [ ] **Step 1: 写 E2E 测试 — 完整用户流程**

```python
# 注册 → 登录 → 创建会话 → 发消息 → 收到 SSE → 重新生成 → 上传文档 → RAG 对话 → 删除会话 → 删除文档
```

- [ ] **Step 2: 修复发现的问题**

- [ ] **Step 3: Commit**

### Task 17: 错误处理打磨

- [ ] 前端: 网络错误重试按钮
- [ ] 前端: token 过期自动跳登录
- [ ] 前端: 文档处理失败状态展示
- [ ] 后端: 限流 429 响应格式
- [ ] Commit

### Task 18: 自动滚动 + 交互细节

- [ ] 前端: 流式接收时自动滚动到底部
- [ ] 前端: 用户手动滚动时不自动跳回底部
- [ ] 前端: 输入框自适应高度 + 最大高度限制
- [ ] 前端: 删除确认对话框
- [ ] Commit
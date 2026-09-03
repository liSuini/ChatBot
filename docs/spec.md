---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '591b7237-0b5a-4ebb-8577-c07c133e68fb'
  PropagateID: '591b7237-0b5a-4ebb-8577-c07c133e68fb'
  ReservedCode1: 'e1d8464b-ba31-4177-bd5b-fa2a7d11649c'
  ReservedCode2: 'e1d8464b-ba31-4177-bd5b-fa2a7d11649c'
---

# ChatBot 技术规格

> 阶段5产出 | 日期: 2026-09-02

---

## Problem Statement

团队内部缺少统一的 AI 对话工具。成员需要一个能进行多轮上下文对话、基于上传文档进行精准问答的系统，且各成员数据相互隔离。现有公开工具无法满足数据隐私和多文档 RAG 的需求。

## Solution

构建一个前后端分离的类 ChatGPT 对话问答系统：后端 FastAPI 单体分层（认证/对话/RAG/LLM 四模块），前端 React SPA，通过 SSE 实现流式打字机回复，支持文档上传与向量检索增强问答，Docker Compose 一键部署。

## User Stories

1. As a 团队成员, I want to 自行注册账号, so that I can 使用系统进行 AI 对话
2. As a 已注册用户, I want to 用用户名密码登录, so that I can 访问我的对话和文档
3. As a 已登录用户, I want to 查看当前登录信息, so that I can 确认登录状态
4. As a 已登录用户, I want to 创建新会话, so that I can 开始一段独立对话
5. As a 已登录用户, I want to 查看会话列表按时间倒序, so that I can 快速找到最近的对话
6. As a 已登录用户, I want to 点击切换会话, so that I can 查看不同对话的内容
7. As a 已登录用户, I want to 重命名会话, so that I can 用有意义的标题区分对话
8. As a 已登录用户, I want to 删除会话, so that I can 清理不需要的对话
9. As a 已登录用户, I want to 查看某会话的全部消息历史, so that I can 回顾之前的对话
10. As a 已登录用户, I want to 在输入框中输入消息并发送, so that I can 向 AI 提问
11. As a 已登录用户, I want to 看到 AI 流式逐字回复, so that I can 实时看到回答内容
12. As a 已登录用户, I want to 在 AI 回复过程中点击停止, so that I can 中断不需要的长回复
13. As a 已登录用户, I want to 对 AI 回复点击重新生成, so that I can 获得不同的回答
14. As a 已登录用户, I want to 编辑已发送的消息并重发, so that I can 修正提问
15. As a 已登录用户, I want to AI 回复支持 Markdown 渲染和代码高亮, so that I can 清晰阅读技术内容
16. As a 已登录用户, I want to 上传文档(PDF/Word/TXT/MD), so that I can 基于文档内容进行问答
17. As a 已登录用户, I want to 查看文档处理状态, so that I can 知道文档何时可用
18. As a 已登录用户, I want to 查看文档列表, so that I can 管理已上传的文档
19. As a 已登录用户, I want to 删除文档, so that I can 清理不再需要的文档
20. As a 已登录用户, I want to 在对话中开关 RAG 检索, so that I can 按需启用文档问答
21. As a 已登录用户, I want to 选择不同的 AI 模型, so that I can 根据需要切换模型
22. As a 已登录用户, I want to 长对话不会因超长而报错, so that I can 持续对话不被打断
23. As a 已登录用户, I want to 遇到错误时看到清晰提示, so that I can 知道发生了什么
24. As a 已登录用户, I want to 我的对话和文档与他人隔离, so that I can 保护隐私
25. As a 部署人员, I want to 通过 docker compose up 一键启动, so that I can 快速部署

## Implementation Decisions

### 1. 数据库 DDL

```sql
-- users 表
CREATE TABLE users (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    username    VARCHAR(50)  NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- conversations 表
CREATE TABLE conversations (
    id              BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id         BIGINT       NOT NULL,
    title           VARCHAR(200) NOT NULL DEFAULT '新对话',
    model_provider  VARCHAR(50)  NOT NULL,
    system_prompt   TEXT         NULL,
    created_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_updated (user_id, updated_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- messages 表
CREATE TABLE messages (
    id                BIGINT AUTO_INCREMENT PRIMARY KEY,
    conversation_id   BIGINT  NOT NULL,
    role              ENUM('user', 'assistant', 'system') NOT NULL,
    content           TEXT    NOT NULL,
    tokens            INT     NOT NULL DEFAULT 0,
    parent_message_id BIGINT  NULL,
    created_at        DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
    INDEX idx_conv_created (conversation_id, created_at),
    INDEX idx_parent (parent_message_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- documents 表
CREATE TABLE documents (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id     BIGINT       NOT NULL,
    filename    VARCHAR(255) NOT NULL,
    file_type   VARCHAR(20)  NOT NULL,
    file_size   BIGINT       NOT NULL,
    status      ENUM('processing', 'ready', 'failed') NOT NULL DEFAULT 'processing',
    chunk_count INT          NOT NULL DEFAULT 0,
    created_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_created (user_id, created_at DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- document_chunks 表 (MySQL 9.0+ VECTOR 类型)
CREATE TABLE document_chunks (
    id          BIGINT AUTO_INCREMENT PRIMARY KEY,
    document_id BIGINT  NOT NULL,
    chunk_index INT     NOT NULL,
    content     TEXT    NOT NULL,
    embedding   VECTOR(1536) NULL,
    created_at  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_document (document_id),
    VECTOR INDEX idx_embedding (embedding)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

### 2. API 契约

所有 API 前缀 `/api/v1`，除注册/登录外均需 `Authorization: Bearer <token>` 头。

#### 认证模块

**POST /auth/register**
```
Request:
  { "username": "string (1-50字符)", "password": "string (6-128字符)" }
Response 200:
  { "access_token": "string", "token_type": "bearer", "user": { "id": int, "username": "string" } }
Response 409:
  { "code": "USERNAME_EXISTS", "message": "用户名已存在" }
```

**POST /auth/login**
```
Request:
  { "username": "string", "password": "string" }
Response 200:
  { "access_token": "string", "refresh_token": "string", "token_type": "bearer", "user": { "id": int, "username": "string" } }
Response 401:
  { "code": "INVALID_CREDENTIALS", "message": "用户名或密码错误" }
```

**GET /auth/me**
```
Response 200:
  { "id": int, "username": "string", "created_at": "datetime" }
```

#### 会话模块

**GET /conversations?skip=0&limit=20**
```
Response 200:
  { "items": [ConversationSummary], "total": int }

ConversationSummary:
  { "id": int, "title": "string", "model_provider": "string", "updated_at": "datetime" }
```

**POST /conversations**
```
Request:
  { "model_provider": "string", "system_prompt": "string|null" }
Response 201:
  { "id": int, "title": "新对话", "model_provider": "string", "system_prompt": "string|null", "created_at": "datetime" }
```

**GET /conversations/{id}**
```
Response 200:
  {
    "id": int, "title": "string", "model_provider": "string",
    "system_prompt": "string|null", "created_at": "datetime", "updated_at": "datetime",
    "messages": [Message]
  }
Response 404: { "code": "NOT_FOUND", "message": "会话不存在" }
Response 403: { "code": "FORBIDDEN", "message": "无权访问该会话" }

Message:
  { "id": int, "role": "user|assistant|system", "content": "string", "tokens": int,
    "parent_message_id": "int|null", "created_at": "datetime" }
```

**PATCH /conversations/{id}**
```
Request:
  { "title": "string (可选)" }
Response 200:
  { "id": int, "title": "string", "updated_at": "datetime" }
Response 404/403: 同上
```

**DELETE /conversations/{id}**
```
Response 204: (无内容)
Response 404/403: 同上
```

#### 消息模块

**POST /conversations/{cid}/messages** (SSE 流式响应)
```
Request:
  { "content": "string", "parent_message_id": "int|null", "rag_enabled": false }

Response: text/event-stream
  event: start
  data: {"message_id": 123}

  event: token
  data: {"content": "你"}

  event: token
  data: {"content": "好"}

  event: done
  data: {"message_id": 124, "tokens": 45}

  // 异常时:
  event: error
  data: {"message": "LLM 调用失败"}
```

行为说明:
- 先存储 user 消息（如果 parent_message_id 不为空，则为编辑重发场景）
- 从当前会话构建上下文消息列表（截断到最近 N 条）
- 如果 rag_enabled=true，先检索用户文档 Top-K=5 拼接为 system 上下文
- 调用 LLMProvider.stream_chat() 逐 token 推送
- 完成（或停止）后将完整 assistant 消息存库

**POST /conversations/{cid}/messages/{id}/regenerate**
```
Request:
  { "rag_enabled": false }
Response: 同 SSE 流式

行为说明:
- 找到该 assistant 消息对应的 user 消息
- 重新调用 LLM 生成回复
- 新 assistant 消息的 parent_message_id 指向旧 assistant 消息
```

**POST /conversations/{cid}/messages/{id}/stop**
```
Response 200:
  { "message_id": 124, "content": "已生成的部分内容...", "tokens": 15, "stopped": true }

行为说明:
- 设置取消标志位，中断正在进行的 stream_chat
- 将已生成的部分内容存为 assistant 消息
- 返回部分内容和 token 数
```

#### 文档模块

**POST /documents/upload**
```
Request: multipart/form-data
  file: 文件 (pdf/docx/txt/md, max 10MB)
Response 201 (小文件同步处理完成):
  { "id": 1, "filename": "report.pdf", "file_type": "pdf", "file_size": 1048576,
    "status": "ready", "chunk_count": 42, "created_at": "datetime" }
Response 202 (大文件后台处理中):
  { "id": 1, "filename": "report.pdf", "status": "processing", "chunk_count": 0 }
Response 413: { "code": "FILE_TOO_LARGE", "message": "文件超过10MB限制" }
Response 415: { "code": "UNSUPPORTED_TYPE", "message": "不支持的文件类型" }
```

**GET /documents?skip=0&limit=20**
```
Response 200:
  { "items": [DocumentSummary], "total": int }

DocumentSummary:
  { "id": int, "filename": "string", "file_type": "string", "file_size": int,
    "status": "processing|ready|failed", "chunk_count": int, "created_at": "datetime" }
```

**GET /documents/{id}/status**
```
Response 200:
  { "status": "processing|ready|failed", "chunk_count": int }
Response 404/403: 同会话模块
```

**DELETE /documents/{id}**
```
Response 204: (无内容)
Response 404/403: 同上
```

**GET /documents/providers** (获取可用模型列表)
```
Response 200:
  { "providers": [
    { "name": "xingchen", "display_name": "星辰大模型", "models": ["xingchen-pro"] },
    { "name": "openai", "display_name": "OpenAI GPT", "models": ["gpt-4o-mini"] }
  ]}
```

### 3. LLM Provider 接口契约

```python
class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: list[LLMMessage], **kwargs) -> ChatResult:
        """非流式对话"""

    @abstractmethod
    async def stream_chat(self, messages: list[LLMMessage], **kwargs) -> AsyncGenerator[str, None]:
        """流式对话，逐 token yield"""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """单段文本向量化"""

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量向量化"""

# 数据结构
class LLMMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class ChatResult(BaseModel):
    content: str
    tokens: int
    model: str
```

### 4. 上下文截断策略

```
发送给 LLM 的消息数组构建规则:
1. 如果 conversation.system_prompt 非空，作为第一条 system 消息
2. 如果 rag_enabled，RAG 检索结果作为 system 消息追加到首部
3. 获取会话最近 N 条消息 (N=20)，按 created_at 升序
4. 过滤: 只取 parent_message_id IS NULL 的消息（当前版本活跃链）
5. 如果总 token 数超过模型上限 (如 8192)，从最早的消息开始剔除，直到满足限制
6. 最终消息数组: [system?(可多条)] + [历史对话消息]
```

### 5. SSE 推送实现契约

```python
# 后端 SSE 端点实现模式
@router.post("/conversations/{cid}/messages")
async def send_message(cid: int, body: MessageCreate, user: User = Depends(get_current_user)):
    async def event_generator():
        try:
            # 1. 存储 user 消息
            user_msg = await chat_service.save_user_message(cid, user.id, body)

            # 2. 构建上下文
            context = await chat_service.build_context(cid, user.id, body.rag_enabled)

            # 3. 推送 start 事件
            yield format_sse("start", {"message_id": placeholder_id})

            # 4. 流式调用 LLM，逐 token 推送
            full_content = ""
            async for token in provider.stream_chat(context):
                if chat_service.is_stopped(message_id):
                    break
                full_content += token
                yield format_sse("token", {"content": token})

            # 5. 存储 assistant 消息
            assistant_msg = await chat_service.save_assistant_message(
                cid, full_content, parent_id=body.parent_message_id
            )

            # 6. 推送 done 事件
            yield format_sse("done", {"message_id": assistant_msg.id, "tokens": assistant_msg.tokens})

        except Exception as e:
            yield format_sse("error", {"message": str(e)})

    return EventSourceResponse(event_generator())
```

### 6. 前端状态机

```
聊天页面状态流转:

IDLE (空闲)
  │ 用户输入消息后按回车
  ▼
SENDING (发送中，等待 start 事件)
  │ 收到 start 事件
  ▼
STREAMING (流式接收中)
  │ ┌─ 收到 done 事件 ──────▶ IDLE
  │ ├─ 用户点击停止 ────────▶ STOPPING → IDLE
  │ └─ 收到 error 事件 ─────▶ ERROR → IDLE (保留已接收内容)
  │
STREAMING 中:
  - 发送按钮变为停止按钮
  - 输入框禁用
  - AI 气泡实时追加 token 内容
  - 自动滚动到底部
```

### 7. 配置项清单

```env
# .env.example

# Database
MYSQL_ROOT_PASSWORD=changeme
MYSQL_DATABASE=chatbot
MYSQL_USER=chatbot
MYSQL_PASSWORD=changeme
DATABASE_URL=mysql+aiomysql://chatbot:changeme@mysql:3306/chatbot

# JWT
SECRET_KEY=your-secret-key-at-least-32-chars
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# LLM Providers
DEFAULT_LLM_PROVIDER=xingchen

## Xingchen (星辰大模型)
XINGCHEN_API_KEY=your-api-key
XINGCHEN_BASE_URL=https://api.xxx.com/v1
XINGCHEN_MODEL=xingchen-pro
XINGCHEN_EMBED_MODEL=xingchen-embedding

## OpenAI
OPENAI_API_KEY=your-api-key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small

# Rate Limiting
RATE_LIMIT_GENERAL=60/minute
RATE_LIMIT_LLM=20/minute

# File Upload
MAX_FILE_SIZE=10485760
SYNC_PROCESS_THRESHOLD=5242880

# RAG
RAG_TOP_K=5
RAG_CHUNK_SIZE=500
RAG_CHUNK_OVERLAP=50
```

## Testing Decisions

### 测试策略

1. **后端 API 屋试验 (最高 seam)**: 通过 httpx AsyncClient 对 FastAPI TestClient 发送真实 HTTP 请求，验证完整链路（路由 → 服务 → 数据库）。这是主要测试 seam，覆盖绝大部分用户故事。

2. **服务层单测 (内部 seam)**: Mock LLMProvider 和 RAGService，单独测试 ChatService / DocumentService / AuthService 的业务逻辑和边界条件。Mock Provider 返回固定 token 流，不依赖真实 LLM API。

3. **LLM Provider 层单测**: 用 httpx 的 MockTransport 模拟 LLM API 响应，验证 Provider 的请求构造、流式解析、错误重试逻辑。

4. **前端**: 暂以手动浏览器验证为主（配合 dev-browser skill），关键组件（useSSE hook、chatStore 状态流转）补充 Vitest 单测。

### 测试 Fixture 设计

```python
# tests/conftest.py
@pytest.fixture
async def db_session():
    """提供隔离的测试数据库会话，测试后回滚"""

@pytest.fixture
async def auth_client(db_session):
    """已认证的 TestClient，自动注入 JWT"""

@pytest.fixture
def mock_llm_provider():
    """Mock LLM Provider，stream_chat 逐字返回 "你好世界" """
    provider = AsyncMock(spec=LLMProvider)
    provider.stream_chat = AsyncMock(
        return_value=async_generator(["你", "好", "世", "界"])
    )
    provider.embed = AsyncMock(return_value=[0.1] * 1536)
    return provider

@pytest.fixture
def sample_user(db_session):
    """创建测试用户"""
```

### 测试覆盖优先级

| 优先级 | 测试范围 | 验证内容 |
|--------|---------|---------|
| P0 | 认证流程 | 注册→登录→获取用户信息→未授权访问拒绝 |
| P0 | 消息发送+SSE | 发送消息→收到 start/token/done 事件→消息持久化 |
| P0 | 数据隔离 | 用户 A 不能访问用户 B 的会话/文档 |
| P1 | 会话 CRUD | 创建/列表/详情/重命名/删除 |
| P1 | 停止生成 | 中断后部分内容存库 |
| P1 | 重新生成 | 旧回复保留，新回复关联 parent |
| P2 | 文档上传+RAG | 上传→分块→向量化→检索→上下文注入 |
| P2 | 编辑重发 | parent_message_id 正确关联 |
| P2 | 上下文截断 | 超长对话正确截断 |
| P3 | 限流 | 普通接口和 LLM 接口分别限流 |
| P3 | 错误处理 | LLM 失败→error 事件，文档处理失败→status=failed |

## Out of Scope

- 多角色权限管理 (RBAC)，不设管理员角色
- 对话导出 (Markdown/JSON)
- Prompt 模板库
- 用户可调模型参数 (temperature/top_p 等)
- 内容审核/敏感词过滤
- 消息搜索
- 移动端原生 App
- 暗色模式
- 多语言国际化
- 实时多人协作/共享会话
- 用量计费/统计面板
- LLM Provider 自动降级/故障转移 (首版)

## Further Notes

- 星辰大模型 API 地址和接口规格待确认，Provider 实现时如发现不兼容 OpenAI 格式需适配
- MySQL 9.0 VECTOR 类型在 Windows Docker Desktop 下的稳定性需在原型阶段验证
- 文档分块参数 (chunk_size=500, overlap=50) 为保守初始值，上线后可根据 RAG 检索效果调优
- npm 作为前端包管理器 (避免 nvm 跨盘符 yarn bug)
- uv 作为后端包管理器
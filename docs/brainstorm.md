---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '30acc702-3211-458c-b55f-bc4fa46c798f'
  PropagateID: '30acc702-3211-458c-b55f-bc4fa46c798f'
  ReservedCode1: 'd5424276-c5ca-491c-bf5d-b44565864c96'
  ReservedCode2: 'd5424276-c5ca-491c-bf5d-b44565864c96'
---

# ChatBot 头脑风暴记录

> 阶段1产出 | 日期: 2026-09-02

---

## 一、需求画像

| 维度 | 结论 |
|------|------|
| 项目定位 | 团队内部工具（<50人） |
| 核心功能 | 多轮对话 + 会话管理 + 文档RAG问答 + Markdown渲染 + 消息操作 |
| 权限模型 | JWT认证，单角色，用户数据隔离 |
| 技术栈 | React + FastAPI + MySQL + Docker，多模型可切换 |
| 向量存储 | MySQL 向量扩展 |
| LLM 对接 | 多模型可切换（星辰/OpenAI等） |

## 二、方案对比

### 方案A：渐进式单体架构（已选定）

前后端分离，后端 FastAPI 单体分层（auth / chat / rag / llm 模块），前端 React SPA。Docker Compose 编排。所有模块在一个后端进程内，通过内部模块边界隔离。

- **优点**：开发快、运维简单、调试方便、适合团队工具规模
- **缺点**：未来高并发场景需重构拆分（但内部工具不太会到这个量）
- **适合度**：恰好匹配当前场景

### 方案B：微服务拆分（未采用）

后端拆为认证服务 + 对话服务 + RAG 服务三个独立进程，引入消息队列做异步文档解析。过度设计，运维复杂度激增。

### 方案C：Next.js SSR + FastAPI（未采用）

前端用 Next.js 替代纯 React SPA。内部工具不需要 SEO/SSR，两套后端逻辑导致维护混乱。

---

## 三、整体架构设计

```
┌──────────────────────────────────────────────────────┐
│                 前端 (React SPA)                       │
│  Vite + TypeScript + Ant Design + Zustand             │
│  ┌─────────┐ ┌──────────┐ ┌──────────┐ ┌───────────┐  │
│  │聊天界面  │ │会话侧边栏 │ │文档管理  │ │设置页面   │  │
│  │SSE接收  │ │CRUD操作  │ │上传/解析 │ │模型/参数  │  │
│  └─────────┘ └──────────┘ └──────────┘ └───────────┘  │
└────────────────────┬─────────────────────────────────┘
                     │ HTTP / SSE
┌────────────────────▼─────────────────────────────────┐
│              后端 (FastAPI 单体分层)                   │
│                                                        │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │Auth模块  │ │Chat模块  │ │RAG模块   │ │LLM抽象层 │  │
│  │JWT认证   │ │会话/消息 │ │文档/向量 │ │Provider  │  │
│  │用户管理  │ │流式返回  │ │检索增强  │ │接口+实现 │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │
│                     │                                  │
│              ┌──────▼──────┐                           │
│              │  MySQL 9.0+ │                           │
│              │ 数据+向量存储│                           │
│              └─────────────┘                           │
└──────────────────────────────────────────────────────┘
                     │ Docker Compose
```

### 关键架构决策

1. **SSE 而非 WebSocket**：对话场景是单向流式推送（服务端→客户端），SSE 更轻量、断线自动重连、不需双向通信
2. **LLM 抽象层独立模块**：Provider 接口定义统一的 `chat()` / `stream_chat()` / `embed()` 方法，具体实现（星辰/OpenAI/其他）作为子类注入，切换模型不改业务代码
3. **RAG 作为独立模块但与 Chat 模块协作**：用户提问时，Chat 模块调用 RAG 模块检索相关文档片段，注入到上下文中再发给 LLM

---

## 四、数据模型

### User
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT, PK, AUTO_INCREMENT | 主键 |
| username | VARCHAR(50), UNIQUE, NOT NULL | 用户名 |
| password_hash | VARCHAR(255), NOT NULL | bcrypt哈希 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### Conversation
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT, PK | 主键 |
| user_id | FK → User.id, INDEX | 所属用户 |
| title | VARCHAR(200), DEFAULT '新对话' | 会话标题 |
| model_provider | VARCHAR(50) | 该会话使用的模型 |
| system_prompt | TEXT, NULLABLE | 可选的自定义系统提示词 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### Message
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT, PK | 主键 |
| conversation_id | FK → Conversation.id, INDEX | 所属会话 |
| role | ENUM: 'user', 'assistant', 'system' | 消息角色 |
| content | TEXT, NOT NULL | 消息原文 |
| tokens | INT, DEFAULT 0 | token计数 |
| parent_message_id | BIGINT, NULLABLE | 编辑重发场景的链式追溯 |
| created_at | DATETIME | 创建时间 |
| | INDEX (conversation_id, created_at) | 复合索引 |

### Document
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT, PK | 主键 |
| user_id | FK → User.id, INDEX | 所属用户 |
| filename | VARCHAR(255) | 文件名 |
| file_type | VARCHAR(20) | pdf/docx/txt/md |
| file_size | BIGINT | 文件大小(字节) |
| status | ENUM: 'processing', 'ready', 'failed' | 处理状态 |
| chunk_count | INT, DEFAULT 0 | 分块数量 |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |

### DocumentChunk
| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT, PK | 主键 |
| document_id | FK → Document.id, INDEX | 所属文档 |
| chunk_index | INT | 块序号 |
| content | TEXT | 块文本 |
| embedding | VECTOR(1536) | 向量列 |
| created_at | DATETIME | 创建时间 |

### 关键设计决策

- **Message.parent_message_id**：支持"编辑后重发"场景。用户编辑某条消息时，新消息的 `parent_message_id` 指向被编辑的原消息，形成消息树而非覆盖原消息，保留完整对话历史
- **Document + DocumentChunk 两表分离**：文档元信息和分块内容分开存储，一个文档可能切成几十上百个块，各自有独立向量。删除文档时级联删除块
- **embedding 用 VECTOR(1536)**：1536 是主流嵌入模型（如 OpenAI text-embedding-3-small）的维度。如果换模型维度不同，通过 Alembic 迁移调整。MySQL 向量检索用 `DISTANCE` 函数做余弦相似度
- **Conversation.model_provider**：每个会话绑定一个模型，切换模型在新会话生效，避免中途切换导致上下文不一致

---

## 五、LLM 抽象层设计

### Provider 接口

```python
class LLMProvider(ABC):
    """所有 LLM 提供商的统一接口"""

    @abstractmethod
    async def chat(self, messages: list[Message], **kwargs) -> ChatResult:
        """非流式对话，返回完整结果"""

    @abstractmethod
    async def stream_chat(self, messages: list[Message], **kwargs) -> AsyncGenerator[str, None]:
        """流式对话，逐 token 返回 (用于 SSE 推送)"""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """单段文本向量化 (用于 RAG 文档入库)"""

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """批量向量化 (用于文档分块批量入库)"""
```

### 配置驱动的 Provider 切换

```python
# config/settings.py
LLM_PROVIDERS = {
    "xingchen": {
        "class": "app.llm.providers.XingchenProvider",
        "api_key": env("XINGCHEN_API_KEY"),
        "base_url": "https://api.xxx.com/v1",
        "model": "xingchen-pro",
        "embed_model": "xingchen-embedding",
    },
    "openai": {
        "class": "app.llm.providers.OpenAIProvider",
        "api_key": env("OPENAI_API_KEY"),
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "embed_model": "text-embedding-3-small",
    },
}

DEFAULT_PROVIDER = env("DEFAULT_LLM_PROVIDER", "xingchen")
```

### 工厂模式

```python
# app/llm/factory.py
class LLMFactory:
    _instances: dict[str, LLMProvider] = {}

    @classmethod
    def get_provider(cls, name: str | None = None) -> LLMProvider:
        name = name or DEFAULT_PROVIDER
        if name not in cls._instances:
            config = LLM_PROVIDERS[name]
            provider_cls = import_class(config["class"])
            cls._instances[name] = provider_cls(**config)
        return cls._instances[name]
```

### 关键设计决策

- **统一接口 4 个方法**：`chat` + `stream_chat` 服务对话场景，`embed` + `embed_batch` 服务 RAG 场景
- **单例缓存**：Factory 内部缓存 Provider 实例，避免每次请求重复创建 HTTP 客户端连接池
- **配置驱动**：新增模型提供商只需在配置中添加一条记录 + 编写 Provider 类，不需要改动业务代码
- **stream_chat 返回 AsyncGenerator**：天然适配 SSE——后端逐块推送到前端，不需要缓冲整个响应
- **kwargs 透传**：`temperature`、`max_tokens`、`top_p` 等参数通过 `**kwargs` 透传

---

## 六、RAG 模块设计

### 文档处理 Pipeline

```
上传文件 ──▶ 保存到临时目录
           │
           ▼
     文件解析器 (按类型分发)
     ┌──────────────────────────┐
     │ PDF  → PyMuPDF 提取文本   │
     │ DOCX → python-docx       │
     │ TXT  → 直接读取           │
     │ MD   → 直接读取           │
     └──────────────────────────┘
           │
           ▼
     文本清洗 (去除多余空白、页眉页脚噪音)
           │
           ▼
     智能分块 (RecursiveCharacterTextSplitter)
     ┌──────────────────────────┐
     │ chunk_size: 500 字符     │
     │ chunk_overlap: 50 字符   │
     │ 分隔符优先级:             │
     │   \n\n → \n → 。 → 空格  │
     └──────────────────────────┘
           │
           ▼
     批量向量化 (provider.embed_batch)
           │
           ▼
     写入 DocumentChunk + embedding
           │
           ▼
     更新 Document.status = "ready"
```

### 文档处理策略

- 小文件（<5MB）：同步处理，用户等待最多10秒可接受
- 大文件（≥5MB）：标记 `status=processing` 后台处理，前端轮询状态

### 检索增强流程

```python
async def retrieve_and_augment(
    question: str,
    user_id: int,
    conversation_id: int,
    provider: LLMProvider,
    top_k: int = 5,
) -> list[Message]:
    # 1. 问题向量化
    query_vector = await provider.embed(question)

    # 2. 向量相似度搜索 (MySQL VECTOR + DISTANCE)
    chunks = await search_similar_chunks(
        user_id=user_id,
        query_vector=query_vector,
        top_k=top_k,
    )

    if not chunks:
        return []

    # 3. 拼接文档上下文
    context = "\n\n---\n\n".join([
        f"[文档: {c.filename}] {c.content}" for c in chunks
    ])

    # 4. 构造 system 消息注入上下文
    rag_system_prompt = (
        "你是专业问答助手。以下是与用户问题相关的参考资料，"
        "请基于资料回答问题，如果资料中没有答案请如实告知。\n\n"
        f"参考资料:\n{context}"
    )

    return [Message(role="system", content=rag_system_prompt)]
```

### MySQL 向量检索 SQL

```sql
SELECT
    dc.id,
    dc.content,
    dc.document_id,
    d.filename,
    DISTANCE(dc.embedding, ?) AS similarity
FROM document_chunks dc
JOIN documents d ON dc.document_id = d.id
WHERE d.user_id = ?
ORDER BY similarity ASC
LIMIT ?;
```

### 关键设计决策

- **分块策略用递归字符分割器**：按分隔符优先级尝试拆分（段落 > 换行 > 句号 > 空格），保持语义完整性。500 字符 + 50 重叠是保守值，可配置
- **Top-K 检索而非阈值过滤**：固定取 5 个最相关片段，简单可靠。不设相似度阈值是因为不同嵌入模型的距离分布差异大
- **检索范围按 user_id 隔离**：SQL 中 `WHERE d.user_id = ?` 确保只能检索到自己的文档

---

## 七、API 接口设计

### 认证模块 /api/v1/auth

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /auth/register | 注册 |
| POST | /auth/login | 登录 → 返回 JWT |
| GET | /auth/me | 获取当前用户信息 |

### 会话模块 /api/v1/conversations

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /conversations | 会话列表(分页) |
| POST | /conversations | 创建会话 |
| GET | /conversations/{id} | 会话详情(含消息历史) |
| PATCH | /conversations/{id} | 修改(标题/模型/系统提示) |
| DELETE | /conversations/{id} | 删除会话(级联删消息) |

### 消息模块 /api/v1/conversations/{cid}/messages

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /messages | 发送消息 → SSE 流式返回 |
| POST | /messages/{id}/regenerate | 重新生成AI回复 |
| POST | /messages/{id}/stop | 停止当前生成 |

### SSE 事件协议

```
event: start     data: {"message_id": 123}
event: token     data: {"content": "你"}
event: token     data: {"content": "好"}
event: done      data: {"message_id": 123, "tokens": 45}
event: error     data: {"message": "生成失败"}
```

### 文档模块 /api/v1/documents

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /documents/upload | 上传文档(max 10MB) |
| GET | /documents | 文档列表 |
| DELETE | /documents/{id} | 删除文档(级联删分块) |
| GET | /documents/{id}/status | 查询处理状态(轮询用) |

### 关键设计决策

- **SSE 事件分四种类型**：`start`/ `token`/ `done`/ `error`，前端根据事件类型做不同 UI 更新
- **停止生成用 POST 而非连接断开**：后端设置取消标志位，正在执行的循环检测到标志后 break。已生成的部分内容仍然存库保留
- **regenerate 复用同一条 user 消息**：新 AI 消息的 `parent_message_id` 指向上一条 AI 消息，保留历史版本
- **RAG 检索由前端按会话开关**：`rag_enabled` 参数由前端传入

---

## 八、前端架构设计

### 目录结构

```
src/
├── main.tsx
├── App.tsx
├── router/index.tsx
├── layouts/ChatLayout.tsx
├── pages/
│   ├── Login.tsx
│   ├── Chat.tsx
│   └── Documents.tsx
├── components/
│   ├── chat/
│   │   ├── ChatWindow.tsx
│   │   ├── MessageList.tsx
│   │   ├── MessageBubble.tsx
│   │   ├── MarkdownRenderer.tsx
│   │   ├── InputArea.tsx
│   │   └── StreamingCursor.tsx
│   ├── sidebar/
│   │   ├── ConversationList.tsx
│   │   └── ConversationItem.tsx
│   └── common/
│       ├── UploadButton.tsx
│       └── ModelSelector.tsx
├── hooks/
│   ├── useSSE.ts
│   ├── useAutoScroll.ts
│   └── useConversation.ts
├── stores/
│   ├── authStore.ts
│   ├── chatStore.ts
│   └── settingsStore.ts
├── services/
│   ├── api.ts
│   ├── authApi.ts
│   ├── chatApi.ts
│   └── documentApi.ts
├── types/index.ts
└── utils/
    ├── request.ts
    └── constants.ts
```

### SSE 接收 Hook

```typescript
// hooks/useSSE.ts
function useSSE() {
  const abortRef = useRef<AbortController | null>(null)

  const sendMessage = async (url, body, callbacks) => {
    abortRef.current = new AbortController()

    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify(body),
      signal: abortRef.current.signal,
    })

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const events = parseSSEEvents(buffer)
      for (const evt of events) {
        switch (evt.event) {
          case 'start':   callbacks.onStart?.(evt.data);   break
          case 'token':   callbacks.onToken?.(evt.data);   break
          case 'done':    callbacks.onDone?.(evt.data);    break
          case 'error':   callbacks.onError?.(evt.data);   break
        }
      }
    }
  }

  const stop = () => abortRef.current?.abort()

  return { sendMessage, stop }
}
```

### 状态管理 (Zustand)

```typescript
interface ChatStore {
  conversations: Conversation[]
  currentId: number | null
  messagesMap: Record<number, Message[]>

  isStreaming: boolean
  streamingMessageId: number | null
  streamingContent: string

  loadConversations: () => Promise<void>
  selectConversation: (id: number) => Promise<void>
  createConversation: () => Promise<void>
  deleteConversation: (id: number) => Promise<void>

  startStreaming: () => void
  appendToken: (token: string) => void
  finishStreaming: (msgId: number, tokens: number) => void
  stopStreaming: () => void
}
```

### 关键设计决策

- **React + Vite + TypeScript + Ant Design**：与 UserCenter 的 Ant Design Pro 生态一致
- **状态管理用 Zustand**：轻量无 boilerplate，适合对话场景的 state 管理
- **SSE 用 fetch + ReadableStream**：`EventSource` 只支持 GET 且不能自定义请求头，`fetch` + `ReadableStream` 可以 POST + 带 Authorization 头
- **messagesMap 按 conversation_id 分组缓存**：切换会话时优先从内存读取，避免每次切换都请求后端
- **流式内容实时渲染**：每个 `token` 事件触发 `appendToken` 更新 `streamingContent`，Markdown 增量渲染

---

## 九、Docker 部署架构

### 架构图

```
docker-compose.yml
┌─────────────────────────────────────────────────┐
│                  Docker Network                  │
│                                                  │
│  ┌──────────┐     ┌──────────┐    ┌──────────┐  │
│  │ Frontend │     │ Backend  │    │  MySQL   │  │
│  │ Nginx    │────▶│ FastAPI  │───▶│  9.0+    │  │
│  │ :80      │     │ :8000    │    │ :3306    │  │
│  │ 静态资源  │     │ Uvicorn  │    │ 数据+向量 │  │
│  │ +反代     │     │          │    │          │  │
│  └──────────┘     └──────────┘    └──────────┘  │
│                         │                        │
│                         ▼                        │
│                   ┌──────────┐                   │
│                   │ LLM API  │                   │
│                   │ (外部)    │                   │
│                   └──────────┘                   │
└─────────────────────────────────────────────────┘
```

### Nginx 关键配置

- 前端静态资源 + SPA history 路由
- API 反代到后端
- SSE 请求单独配置：`proxy_buffering off`、`proxy_read_timeout 300s`、`chunked_transfer_encoding on`

### Docker Compose 服务

- **mysql**: mysql/mysql-server:9.0，数据卷持久化
- **backend**: FastAPI + Uvicorn，环境变量注入密钥
- **frontend**: Nginx 静态资源 + 反向代理

### 关键设计决策

- **Nginx 作为统一入口**：前端静态资源 + API 反代统一走 80 端口，避免跨域
- **MySQL 9.0+**：原生 VECTOR 类型 + DISTANCE 函数支撑 RAG 向量检索。备选方案 MySQL 8.0 + JSON 列存向量 + 应用层计算
- **环境变量管理密钥**：`.env` 文件注入，`.env.example` 提供模板
- **后端用 uvicorn + uvloop**：异步框架支撑 SSE 长连接并发

---

## 十、安全与错误处理

### 安全措施

1. **JWT 认证**：access_token (30min) + refresh_token (7d)，所有 API 路由依赖 `Depends(get_current_user)`，SSE 请求通过 fetch headers 带 Authorization
2. **数据隔离**：所有查询带 `WHERE user_id = current_user.id`，RAG 检索范围按 user_id 隔离
3. **输入校验**：Pydantic schemas 校验所有请求体，文件上传类型白名单 + 大小限制(10MB)，SQLAlchemy 参数化查询
4. **速率限制**：slowapi 中间件，普通接口 60次/分钟，LLM 消息接口 20次/分钟
5. **密码安全**：bcrypt 哈希存储 (passlib)，JWT HS256 + 环境变量密钥

### 错误处理

- **后端统一异常**：`ChatBotException` 基类携带 error_code + message + status，子类包括 `LLMProviderError`、`DocumentProcessError`、`RateLimitError`、`NotFoundError`
- **SSE 流中错误**：以 `event: error` 推送，不中断 HTTP 连接，前端已收到内容保留
- **前端错误层级**：Axios 拦截器统一处理 HTTP 错误 (401 跳登录)，SSE onError 保留已接收内容，组件级 try/catch 局部处理
- **LLM 调用降级**：首选 Provider 超时/报错时可配置降级到备用 Provider，首版先记录日志+返回错误，后续迭代
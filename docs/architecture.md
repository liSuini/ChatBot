---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '70f15352-de00-432e-996f-38a485ae8bff'
  PropagateID: '70f15352-de00-432e-996f-38a485ae8bff'
  ReservedCode1: '1c1fffab-6bfb-4edb-94d8-08c56ff5b121'
  ReservedCode2: '1c1fffab-6bfb-4edb-94d8-08c56ff5b121'
---

# ChatBot 架构设计

> 阶段4产出 | 日期: 2026-09-02

---

## 一、项目整体结构

```
ChatBot/
├── docs/                    # 项目文档（阶段1-8产出）
│   ├── brainstorm.md
│   ├── prd.md
│   ├── domain.md
│   ├── architecture.md      ← 本文件
│   ├── adr/
│   ├── spec.md
│   ├── prototype/
│   ├── plan.md
│   └── tickets.md
├── CONTEXT.md               # 领域术语表
├── backend/                 # 后端 FastAPI
├── frontend/                # 前端 React
├── docker-compose.yml       # 编排文件
├── .env.example             # 环境变量模板
└── README.md
```

## 二、后端目录结构设计

```
backend/
├── alembic/                          # 数据库迁移
│   ├── versions/
│   └── env.py
├── alembic.ini
├── app/
│   ├── __init__.py
│   ├── main.py                       # FastAPI 应用入口，注册路由/中间件
│   ├── core/                         # 基础设施层（深模块：配置/安全/数据库）
│   │   ├── __init__.py
│   │   ├── config.py                 # 配置管理 (pydantic-settings, 读环境变量)
│   │   ├── database.py               # 异步数据库引擎 + Session 工厂
│   │   ├── security.py               # JWT 生成/校验 + bcrypt 哈希
│   │   └── exceptions.py             # 统一异常体系
│   ├── deps/                         # FastAPI 依赖注入
│   │   ├── __init__.py
│   │   ├── auth.py                   # get_current_user (JWT → User)
│   │   └── db.py                     # get_db_session
│   ├── models/                       # SQLAlchemy ORM 模型（持久化层）
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   └── document.py               # Document + DocumentChunk
│   ├── schemas/                      # Pydantic 请求/响应模型（接口契约层）
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── conversation.py
│   │   ├── message.py
│   │   └── document.py
│   ├── api/                          # API 路由层（薄：只做请求转发和响应组装）
│   │   ├── __init__.py
│   │   ├── router.py                 # 汇总所有子路由
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── auth.py               # /auth/register, /auth/login, /auth/me
│   │       ├── conversations.py      # 会话 CRUD
│   │       ├── messages.py           # 发送消息(SSE) / 重新生成 / 停止
│   │       └── documents.py          # 文档上传 / 列表 / 删除 / 状态查询
│   ├── services/                     # 领域服务层（深模块：业务逻辑所在）
│   │   ├── __init__.py
│   │   ├── auth_service.py           # 注册/登录/Token管理
│   │   ├── chat_service.py           # 消息发送/流式回复/RAG判断与注入
│   │   ├── document_service.py       # 文档解析/分块/向量化/删除
│   │   └── rag_service.py            # 向量检索/上下文拼接
│   ├── llm/                          # LLM 抽象层（深模块：Provider 接口 + 实现）
│   │   ├── __init__.py
│   │   ├── base.py                   # LLMProvider 抽象基类
│   │   ├── factory.py                # LLMFactory 工厂
│   │   ├── schemas.py                # LLM 相关数据结构 (Message, ChatResult)
│   │   └── providers/
│   │       ├── __init__.py
│   │       ├── xingchen.py           # 星辰大模型 Provider
│   │       └── openai.py             # OpenAI Provider
│   ├── rag/                          # RAG 文档处理管线（深模块：解析+分块+清洗）
│   │   ├── __init__.py
│   │   ├── parser.py                 # 文件解析器 (PDF/DOCX/TXT/MD 分发)
│   │   ├── splitter.py               # 文本分块器 (RecursiveCharacterTextSplitter)
│   │   └── cleaner.py                # 文本清洗
│   └── middleware/                   # 中间件
│       ├── __init__.py
│       └── rate_limit.py             # slowapi 限流配置
├── tests/
│   ├── conftest.py                   # pytest fixtures
│   ├── test_auth/
│   ├── test_chat/
│   ├── test_document/
│   └── test_llm/
├── requirements.txt
├── Dockerfile
└── .env
```

### 后端分层依赖关系

```
API 路由层 (api/v1/)        ← 薄：接收请求 → 调服务 → 组装响应
    │ 依赖
    ▼
领域服务层 (services/)      ← 深：业务逻辑、跨聚合协调
    │ 依赖
    ▼
┌───────────────────────────────────────┐
│  LLM 抽象层 (llm/)   RAG 管线 (rag/)   │  ← 深：复杂实现，小接口
├───────────────────────────────────────┤
│  ORM 模型 (models/)  Pydantic (schemas/)│  ← 数据层
└───────────────────────────────────────┘
    │ 依赖
    ▼
基础设施层 (core/)          ← 深：配置/数据库/安全，全局单例
```

### 后端深模块设计

| 模块 | 接口（小） | 实现（深） |
|------|-----------|-----------|
| `LLMFactory` | `get_provider(name) -> LLMProvider` | 配置解析、类导入、单例缓存 |
| `LLMProvider` | `chat()` `stream_chat()` `embed()` `embed_batch()` | HTTP 客户端、请求构造、响应解析、错误重试 |
| `ChatService` | `send_message()` `regenerate()` `stop()` | 上下文截断、RAG 判断、SSE 推送、消息存储 |
| `RAGService` | `retrieve(question, user_id) -> str` | 向量检索、Top-K、上下文拼接 |
| `DocumentService` | `upload()` `delete()` `get_status()` | 文件解析、分块、向量化、异步处理 |
| `RAGParser` | `parse(file_path, file_type) -> str` | 按类型分发解析器、异常处理 |
| `RAGSplitter` | `split(text) -> list[str]` | 递归字符分割、重叠控制 |
| `security` | `create_token()` `verify_token()` `hash_password()` `verify_password()` | JWT 编解码、bcrypt、过期管理 |
| `database` | `get_session()` | 引擎创建、连接池、异步 Session |

## 三、前端目录结构设计

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── main.tsx                     # 入口
│   ├── App.tsx                      # 路由根 + 全局 Provider
│   ├── router/
│   │   └── index.tsx                # 路由定义 (React Router v6)
│   │
│   ├── layouts/
│   │   └── ChatLayout.tsx           # 主布局: 侧边栏 + 内容区 + ProtectedRoute
│   │
│   ├── pages/
│   │   ├── Login.tsx                # 登录/注册页
│   │   ├── Chat.tsx                 # 对话主页
│   │   └── Documents.tsx            # 文档管理页
│   │
│   ├── components/
│   │   ├── chat/
│   │   │   ├── ChatWindow.tsx       # 聊天窗口容器 (组合 MessageList + InputArea)
│   │   │   ├── MessageList.tsx      # 消息列表渲染
│   │   │   ├── MessageBubble.tsx    # 单条消息气泡 (含编辑/重发/重新生成按钮)
│   │   │   ├── MarkdownRenderer.tsx # Markdown 渲染 + 代码高亮
│   │   │   ├── InputArea.tsx        # 输入框 (自适应高度 + 发送/停止按钮)
│   │   │   └── StreamingCursor.tsx  # 流式打字光标动画
│   │   ├── sidebar/
│   │   │   ├── ConversationList.tsx # 会话列表 (新建/切换/重命名/删除)
│   │   │   └── ConversationItem.tsx # 单条会话项
│   │   └── common/
│   │       ├── UploadButton.tsx     # 文档上传 (拖拽 + 进度)
│   │       └── ModelSelector.tsx    # 模型选择下拉框
│   │
│   ├── hooks/
│   │   ├── useSSE.ts                # SSE 连接管理 (fetch + ReadableStream)
│   │   ├── useAutoScroll.ts         # 自动滚动到底部
│   │   └── useConversation.ts       # 当前会话状态管理逻辑
│   │
│   ├── stores/                      # Zustand 状态管理
│   │   ├── authStore.ts             # 认证: token / user / login / logout
│   │   ├── chatStore.ts             # 会话: 列表 / 当前ID / 消息缓存 / 流式状态
│   │   └── settingsStore.ts         # 设置: 当前模型 / RAG 开关
│   │
│   ├── services/                    # API 调用层
│   │   ├── api.ts                   # Axios 实例 (拦截器: 加 JWT / 401 跳登录)
│   │   ├── authApi.ts               # 认证接口: register / login / me
│   │   ├── chatApi.ts               # 会话/消息接口: CRUD / SSE
│   │   └── documentApi.ts           # 文档接口: upload / list / delete / status
│   │
│   ├── types/
│   │   └── index.ts                 # TypeScript 类型定义 (对齐后端 schema)
│   │
│   └── utils/
│       ├── sse-parser.ts            # SSE 协议解析工具
│       └── constants.ts             # 常量 (API base, storage keys)
│
├── package.json
├── tsconfig.json
├── vite.config.ts
└── Dockerfile
```

### 前端深模块设计

| 模块 | 接口（小） | 实现（深） |
|------|-----------|-----------|
| `useSSE` | `sendMessage(url, body, callbacks)` `stop()` | fetch 流管理、ReadableStream 读取、SSE 协议解析、AbortController 中断 |
| `chatStore` | `loadConversations()` `selectConversation(id)` `createConversation()` `deleteConversation(id)` `startStreaming()` `appendToken(token)` `finishStreaming(msgId, tokens)` `stopStreaming()` | 会话缓存策略、流式状态机、消息树管理 |
| `api.ts` (Axios) | 自动注入 JWT | 拦截器配置、401 自动刷新/跳转、统一错误格式化 |
| `MarkdownRenderer` | `<MarkdownRenderer content={string} />` | markdown-it 配置、highlight.js 集成、安全过滤(XSS) |
| `InputArea` | `onSend(content)` `onStop()` | 自适应高度计算、快捷键处理、发送状态管理 |

## 四、深模块 seam 设计要点

### 1. LLM 抽象层 seam

```
          Seam: LLMProvider 接口
    ┌──────────────────────────────┐
    │  stream_chat(messages) → Gen │  ← 调用者只知道这个接口
    └──────────┬───────────────────┘
               │
    ┌──────────▼───────────────────┐
    │   XingchenProvider           │  ← 实现内部: httpx 客户端、
    │   OpenAIProvider             │     请求构造、SSE 解析、重试
    └──────────────────────────────┘
```

- ChatService 调用 `provider.stream_chat(msgs)` 时完全不关心是哪个模型
- 新增 Provider 只需在 `llm/providers/` 下加一个类 + 在配置中加一条记录
- 测试时可注入 Mock Provider，不依赖真实 API

### 2. ChatService seam

```
          Seam: ChatService 三个方法
    ┌────────────────────────────────────────┐
    │  send_message(conv_id, content, opts)  │
    │  regenerate(conv_id, message_id)       │
    │  stop(message_id)                      │
    └────────────────┬───────────────────────┘
                     │
    ┌────────────────▼───────────────────────┐
    │ 内部协调:                               │
    │  - Conversation.add_message            │
    │  - Conversation.get_context_messages   │
    │  - [可选] RAGService.retrieve          │
    │  - LLMProvider.stream_chat             │
    │  - SSE event 推送                       │
    │  - 消息持久化                            │
    └────────────────────────────────────────┘
```

- API 层只调 `ChatService.send_message()`，不需要知道 RAG/LLM/上下文截断的细节
- 测试时可 Mock LLMProvider 和 RAGService，验证 ChatService 的协调逻辑

### 3. RAG 处理管线 seam

```
          Seam: RAGService + DocumentService
    ┌──────────────────────────────────────────┐
    │  RAGService.retrieve(question, user_id)  │  → 返回拼接好的上下文字符串
    │  DocumentService.upload(file, user_id)   │  → 返回 document_id + status
    └──────────────────┬───────────────────────┘
                       │
    ┌──────────────────▼───────────────────────┐
    │ 内部管线:                                 │
    │  RAGParser.parse() → RAGSplitter.split() │
    │  → LLMProvider.embed_batch()              │
    │  → DocumentChunk 批量写入                  │
    │  → MySQL VECTOR DISTANCE 检索              │
    └──────────────────────────────────────────┘
```

## 五、技术选型总结

### 后端

| 类别 | 选型 | 版本 | 理由 |
|------|------|------|------|
| Web 框架 | FastAPI | 0.115+ | 原生 async + SSE 支持、自动 OpenAPI 文档 |
| ASGI 服务器 | uvicorn[standard] | 0.30+ | 含 uvloop，SSE 长连接性能好 |
| ORM | SQLAlchemy | 2.0+ | async 支持完善、与 Alembic 配合 |
| 迁移 | Alembic | 1.13+ | SQLAlchemy 官方迁移工具 |
| MySQL 驱动 | aiomysql | 0.2+ | 纯异步 MySQL 驱动 |
| 数据校验 | Pydantic | 2.0+ | FastAPI 原生集成 |
| 配置管理 | pydantic-settings | 2.0+ | 环境变量自动绑定 |
| 密码哈希 | passlib[bcrypt] | 1.7+ | 行业标准 bcrypt |
| JWT | python-jose[cryptography] | 3.3+ | 成熟稳定的 JWT 库 |
| 限流 | slowapi | 0.1+ | FastAPI 兼容的限流中间件 |
| LLM HTTP 客户端 | httpx | 0.27+ | 支持 async，可流式读取 |
| PDF 解析 | PyMuPDF | 1.24+ | 速度快、文本提取质量好 |
| DOCX 解析 | python-docx | 1.1+ | 纯 Python，无系统依赖 |
| 文本分块 | langchain-text-splitters | 0.2+ | RecursiveCharacterTextSplitter |

### 前端

| 类别 | 选型 | 版本 | 理由 |
|------|------|------|------|
| 框架 | React | 18+ | 用户指定，生态成熟 |
| 构建 | Vite | 5+ | 构建快、HMR 体验好 |
| 语言 | TypeScript | 5+ | 类型安全，前后端类型对齐 |
| UI 库 | Ant Design | 5+ | 中后台组件齐全，与 UserCenter 一致 |
| 状态管理 | Zustand | 5+ | 轻量无 boilerplate |
| 路由 | React Router | 6+ | 标准选择 |
| HTTP 客户端 | Axios | 1.7+ | 拦截器机制成熟 |
| Markdown 渲染 | markdown-it | 14+ | 可扩展、性能好 |
| 代码高亮 | highlight.js | 11+ | 支持语言全、集成简单 |
| SSE 工具 | 自实现 (fetch + ReadableStream) | - | 需 POST + JWT header，EventSource 不支持 |

### 基础设施

| 类别 | 选型 | 理由 |
|------|------|------|
| 数据库 | MySQL 9.0+ | 原生 VECTOR 类型 + DISTANCE 函数 |
| 容器编排 | Docker Compose | 三个服务简单编排 |
| 反向代理 | Nginx | 静态资源 + API/SSE 反代 |
| 包管理 (前端) | npm | 兼容性最好 (nvm 跨盘符 yarn 有 bug) |
| 包管理 (后端) | uv | 速度快、现代化 Python 包管理 |
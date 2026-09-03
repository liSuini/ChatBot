---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'f5f13cd3-2293-47c2-8fc5-81f58e949359'
  PropagateID: 'f5f13cd3-2293-47c2-8fc5-81f58e949359'
  ReservedCode1: '3bd195f9-09dc-4069-8ec3-9820647d963d'
  ReservedCode2: '3bd195f9-09dc-4069-8ec3-9820647d963d'
---

# ChatBot 开发工单

> 阶段8产出 | 日期: 2026-09-02
> 共 11 个垂直切片工单，按依赖序排列

---

## 依赖关系图

```
T01 (骨架+DB)
 ├── T02 (认证) ──── T04 (会话管理) ────┐
 │                                      ├── T05 (消息+SSE) ──┬── T06 (消息操作)
 ├── T03 (LLM抽象) ──┐                   │                    └── T07 (Markdown)
 │                   ├── T09 (RAG) ─────┘
 │                   └── T08 (模型切换)
 │
 └──────────────── T10 (Docker) ← T05 + T09
                        └── T11 (集成测试+打磨)
```

## 可并行执行分组

| 批次 | 工单 | 说明 |
|------|------|------|
| 第1批 | T01 | 基础设施，必须先完成 |
| 第2批 | T02, T03 | 认证和 LLM 互不依赖，可并行 |
| 第3批 | T04, T08 | T04 依赖 T02，T08 依赖 T03，可并行 |
| 第4批 | T05, T09 | T05 依赖 T03+T04，T09 依赖 T03+T04，可并行 |
| 第5批 | T06, T07 | 都依赖 T05，之间无依赖，可并行 |
| 第6批 | T10 | 依赖 T05+T09 |
| 第7批 | T11 | 依赖 T10 |

---

## T01: 项目骨架 + 数据库

**What to build:** 搭建前后端项目骨架，创建全部数据库表结构和迁移文件，使`uvicorn` 和 `npm run dev` 都能启动，数据库 5 张表就绪。

**Blocked by:** 无（可立即开始）

**Status:** done (2026-09-03)

- [x] 后端: 创建 pyproject.toml，安装全部依赖 (FastAPI/SQLAlchemy/Alembic/aiomysql 等)
- [x] 后端: 实现 `app/core/config.py` (pydantic-settings 配置类，读取 .env)
- [x] 后端: 实现 `app/core/database.py` (异步引擎 + Session 工厂 + DeclarativeBase)
- [x] 后端: 创建 5 个 ORM 模型 (User/Conversation/Message/Document/DocumentChunk)
- [x] 后端: 初始化 Alembic，生成并运行初始迁移 (5 张表 + 索引 + 外键)
- [x] 后端: 创建 `app/main.py` 含 `/health` 端点，启动验证通过
- [x] 后端: 创建 `app/core/exceptions.py` 统一异常体系
- [x] 前端: Vite + React + TS 脚手架，安装 antd/zustand/axios/react-router-dom/markdown-it/highlight.js
- [x] 前端: 配置 Vite 代理 (/api → localhost:8010，8000 被本机其他项目占用)
- [x] 前端: 创建路由结构 (Login/Chat/Documents + ChatLayout)
- [x] 前端: 创建 `types/index.ts` 全部 TypeScript 类型定义
- [x] 验证: 后端 `http://localhost:8010/health` 返回 ok (4 项冒烟测试通过)，前端 `http://localhost:5173` 可访问

---

## T02: 用户认证全链路

**What to build:** 用户可以注册、登录、查看当前登录信息，JWT 认证全程生效，前端有登录/注册页面，未登录访问自动跳转登录页。

**Blocked by:** T01

**Status:** ready-for-agent

- [ ] 后端: 实现 `core/security.py` (hash_password / verify_password / create_access_token / create_refresh_token / verify_token)
- [ ] 后端: 实现 `services/auth_service.py` (register / login，用户名唯一校验)
- [ ] 后端: 实现 `deps/auth.py` (get_current_user FastAPI 依赖)
- [ ] 后端: 实现 `schemas/auth.py` (RegisterRequest / LoginRequest 响应模型)
- [ ] 后端: 实现 `api/v1/auth.py` (POST /auth/register, POST /auth/login, GET /auth/me)
- [ ] 后端: 注册路由到 main.py，统一异常处理器 (409/401)
- [ ] 后端: 测试 — 注册成功/重复注册/登录成功/密码错误/无token访问me/有token访问me
- [ ] 前端: 实现 `stores/authStore.ts` (token/user 状态 + persist 持久化)
- [ ] 前端: 实现 `services/api.ts` (Axios 实例 + 请求拦截器加 JWT + 401 跳登录)
- [ ] 前端: 实现 `services/authApi.ts` (register / login / me 调用)
- [ ] 前端: 实现 `pages/Login.tsx` (Ant Design Form，登录/注册切换，成功跳转 /chat)
- [ ] 前端: 实现 `layouts/ChatLayout.tsx` ProtectedRoute (未登录重定向 /login)
- [ ] 验证: 浏览器中 注册→登录→跳转聊天页→刷新仍登录→退出→跳登录页

---

## T03: LLM Provider 抽象层

**What to build:** 定义 LLM 统一接口，实现 Mock Provider (测试用) 和 OpenAI 兼容 Provider (适配星辰等)，工厂模式按名称获取 Provider 实例。无前端，纯后端基础设施。

**Blocked by:** T01

**Status:** ready-for-agent

- [ ] 后端: 实现 `llm/schemas.py` (LLMMessage / ChatResult 数据结构)
- [ ] 后端: 实现 `llm/base.py` (LLMProvider ABC: chat / stream_chat / embed / embed_batch)
- [ ] 后端: 实现 `llm/providers/mock.py` (stream_chat 逐字返回"你好世界"，embed 返回 1536 维固定向量)
- [ ] 后端: 实现 `llm/providers/openai_provider.py` (httpx 调 OpenAI 兼容 API，支持流式)
- [ ] 后端: 实现 `llm/factory.py` (单例缓存 + get_provider(name) + get_available_providers())
- [ ] 后端: 测试 — 工厂返回正确类型、stream_chat yields tokens、embed 返回正确维度、embed_batch

---

## T04: 会话管理全链路

**What to build:** 用户可以创建、查看、重命名、删除会话，侧边栏展示会话列表，点击切换会话，所有操作按用户隔离。

**Blocked by:** T02

**Status:** ready-for-agent

- [ ] 后端: 实现 `schemas/conversation.py` (ConversationCreate / ConversationSummary / ConversationDetail)
- [ ] 后端: 实现 `services/chat_service.py` 会话部分 (create / list / get / rename / delete，全部带 user_id 隔离)
- [ ] 后端: 实现 `api/v1/conversations.py` (GET/POST/PATCH/DELETE /conversations + GET /conversations/{id} 含消息历史)
- [ ] 后端: 测试 — 创建/列表/重命名/删除/用户间隔离 (A 不能访问 B 的会话返回 404)
- [ ] 前端: 实现 `services/chatApi.ts` (会话 CRUD 调用)
- [ ] 前端: 实现 `stores/chatStore.ts` (conversations / currentId / messagesMap / loadConversations / selectConversation / createConversation / deleteConversation)
- [ ] 前端: 实现 `components/sidebar/ConversationList.tsx` (新建按钮 + 列表，按 updated_at 倒序)
- [ ] 前端: 实现 `components/sidebar/ConversationItem.tsx` (标题、重命名编辑、删除确认对话框)
- [ ] 前端: 在 ChatLayout 中集成侧边栏，切换会话时加载消息历史
- [ ] 验证: 浏览器中 新建会话→列表显示→重命名→切换→删除→隔离验证

---

## T05: 消息发送 + SSE 流式回复

**What to build:** 用户在输入框发送消息后，AI 以打字机效果逐字流式返回，消息持久化到数据库，这是整个系统的核心交互。

**Blocked by:** T03, T04

**Status:** pending (等待 T03, T04 完成)

- [ ] 后端: 实现 `services/chat_service.py` 消息部分 (save_user_message / build_context / save_assistant_message + 取消标志位)
- [ ] 后端: 实现上下文截断策略 (system prompt + 最近 20 条，parent_message_id IS NULL)
- [ ] 后端: 实现 `api/v1/messages.py` (POST /conversations/{cid}/messages，SSE 事件流 start/token/done/error)
- [ ] 后端: SSE 响应包含 `X-Accel-Buffering: no` 头，JSON 中文不转义
- [ ] 后端: 实现 `api/v1/messages.py` POST /stop 端点 (设置取消标志，部分内容存库)
- [ ] 后端: 实现 `middleware/rate_limit.py` (slowapi，LLM 接口 20次/分钟)
- [ ] 后端: 测试 — 发送消息收到 SSE 事件 (start/token/done)、消息持久化验证、停止生成验证
- [ ] 前端: 实现 `utils/sse-parser.ts` (SSE 协议解析：按 \n\n 分割，event/data 行提取，buffer 拼接)
- [ ] 前端: 实现 `hooks/useSSE.ts` (fetch + ReadableStream + AbortController，onStart/onToken/onDone/onError 回调)
- [ ] 前端: 实现 `components/chat/InputArea.tsx` (自适应高度、回车发送、Shift+回车换行、流式中发送变停止)
- [ ] 前端: 实现 `components/chat/MessageBubble.tsx` (用户右对齐/AI左对齐、流式内容追加)
- [ ] 前端: 实现 `components/chat/MessageList.tsx` (消息列表渲染、流式消息追加)
- [ ] 前端: 实现 `components/chat/ChatWindow.tsx` (组合 MessageList + InputArea)
- [ ] 前端: 实现 `pages/Chat.tsx` (组合 ChatWindow + useSSE + chatStore)
- [ ] 前端: chatStore 追加流式状态 (isStreaming / streamingContent / appendToken / finishStreaming)
- [ ] 验证: 浏览器中 发送消息→看到逐字流式回复→停止生成→部分内容保留→消息持久化

---

## T06: 消息操作 (停止/重新生成/编辑重发)

**What to build:** 用户可以停止正在生成的回复、对 AI 回复点击重新生成、编辑已发送的消息并重发，所有操作通过 parent_message_id 保留历史版本。

**Blocked by:** T05

**Status:** pending (等待 T05 完成)

- [ ] 后端: 实现重新生成端点 (POST /conversations/{cid}/messages/{id}/regenerate，复用原 user 消息，新 assistant 消息 parent 指向旧 assistant)
- [ ] 后端: 实现编辑重发逻辑 (新 user 消息 parent_message_id 指向原 user 消息，重新生成 AI 回复)
- [ ] 后端: 测试 — 重新生成 parent_message_id 正确、编辑重发 parent 关联正确
- [ ] 前端: MessageBubble AI 消息下方添加"重新生成"按钮
- [ ] 前端: MessageBubble 用户消息添加"编辑"功能 (点击变输入框，编辑后发送触发重发)
- [ ] 前端: 停止按钮连接 useSSE.stop() + 后端 /stop 端点
- [ ] 前端: 重新生成/编辑重发期间输入框禁用
- [ ] 验证: 浏览器中 停止生成→重新生成→编辑消息重发，历史版本保留

---

## T07: Markdown 渲染 + 代码高亮

**What to build:** AI 回复的 Markdown 内容正确渲染，支持标题、加粗、列表、表格、代码块语法高亮、行内代码、链接。流式过程中增量渲染，完成后完整渲染。

**Blocked by:** T05

**Status:** pending (等待 T05 完成)

- [ ] 前端: 实现 `components/chat/MarkdownRenderer.tsx` (markdown-it 实例 + highlight.js 集成)
- [ ] 前端: markdown-it 配置: html=false (防 XSS)、linkify=true、typographer=true
- [ ] 前端: highlight.js 配置: 常用语言 (js/ts/python/bash/json/sql/html/css)
- [ ] 前端: 流式模式: 直接渲染 streamingContent (可能不完整的 markdown)
- [ ] 前端: 完成模式: 完整渲染最终内容，确保代码块、表格等正确闭合
- [ ] 前端: 样式: 代码块背景色、行内代码样式、表格边框、链接颜色
- [ ] 前端: 实现 `components/chat/StreamingCursor.tsx` (流式光标动画)
- [ ] 验证: AI 回复含代码块→正确高亮、含表格→正确渲染、流式→增量显示

---

## T08: 模型切换

**What to build:** 用户可以在新建会话时选择不同的 AI 模型，模型列表从后端配置获取。会话创建后模型绑定不可更改。

**Blocked by:** T03

**Status:** pending (等待 T03 完成)

- [ ] 后端: 实现 `api/v1/llm.py` (GET /providers 返回可用模型列表)
- [ ] 后端: 测试 — 返回配置的 provider 列表
- [ ] 前端: 实现 `components/common/ModelSelector.tsx` (Ant Design Select 下拉)
- [ ] 前端: 实现 `stores/settingsStore.ts` (当前选择的 provider)
- [ ] 前端: 在 Chat 页面或侧边栏新建会话时展示 ModelSelector
- [ ] 前端: 创建会话时传入选定的 model_provider
- [ ] 验证: 切换模型→新建会话→会话绑定正确模型→已有会话模型不变

---

## T09: 文档上传 + RAG 问答

**What to build:** 用户可以上传文档 (PDF/Word/TXT/MD)，系统自动解析、分块、向量化存储。在对话中开启 RAG 开关后，提问会先检索相关文档片段注入上下文，AI 基于文档内容回答。

**Blocked by:** T03, T04

**Status:** pending (等待 T03, T04 完成)

- [ ] 后端: 实现 `rag/parser.py` (FileParser: PDF→PyMuPDF, DOCX→python-docx, TXT/MD→直读)
- [ ] 后端: 实现 `rag/splitter.py` (RecursiveCharacterTextSplitter, 500字符+50重叠)
- [ ] 后端: 实现 `services/document_service.py` (upload: 解析→分块→embed_batch→存储; delete: 级联删除; get_status)
- [ ] 后端: 实现 `services/rag_service.py` (retrieve: 问题向量化→向量检索 Top-K=5→拼接上下文)
- [ ] 后端: 在 `chat_service.build_context` 中接入 RAG (rag_enabled 时调用 rag_service.retrieve)
- [ ] 后端: 实现 `api/v1/documents.py` (POST upload / GET list / GET status / DELETE)
- [ ] 后端: 文件校验: 类型白名单 (pdf/docx/txt/md) + 大小限制 (10MB)
- [ ] 后端: 小文件 (<5MB) 同步处理，大文件标记 processing
- [ ] 后端: 测试 — 上传→分块→状态变 ready→RAG 检索→上下文注入→删除级联
- [ ] 前端: 实现 `services/documentApi.ts` (upload/list/delete/status)
- [ ] 前端: 实现 `pages/Documents.tsx` (Ant Design Table + 上传按钮 + 状态标签)
- [ ] 前端: 实现 `components/common/UploadButton.tsx` (拖拽上传 + 文件校验 + 进度)
- [ ] 前端: 在 Chat 页面添加 RAG 开关 (Toggle)，存入 settingsStore
- [ ] 前端: 发送消息时传入 rag_enabled 参数
- [ ] 前端: 大文件上传后轮询状态 (GET /documents/{id}/status)
- [ ] 验证: 上传 PDF→状态 ready→对话开启 RAG→提问→AI 基于文档回答→关闭 RAG→普通对话

---

## T10: Docker 部署

**What to build:** 通过 `docker compose up` 一键启动 MySQL + 后端 + 前端 Nginx 三个服务，后端自动迁移数据库，Nginx 正确代理 API 和 SSE，全部功能可用。

**Blocked by:** T05, T09

**Status:** pending (等待 T05, T09 完成)

- [ ] 创建 `backend/Dockerfile` (python:3.12-slim + uv + 迁移 + uvicorn 启动)
- [ ] 创建 `frontend/Dockerfile` (node:20 build + nginx:alpine 静态服务)
- [ ] 创建 `frontend/nginx.conf` (静态资源 + /api/ 反代 + SSE 关闭 buffering + proxy_read_timeout 300s)
- [ ] 创建 `docker-compose.yml` (mysql 9.0 + backend + frontend 三服务 + 数据卷 + 依赖关系)
- [ ] 创建 `.env.example` (全部环境变量模板)
- [ ] 后端 Dockerfile 中 `alembic upgrade head` 自动迁移
- [ ] 验证: `docker compose up --build` → http://localhost 全链路可用 (注册→对话→RAG→停止→重生成)

---

## T11: 集成测试 + 打磨

**What to build:** 端到端集成测试覆盖完整用户流程，前端错误处理和交互细节打磨到产品级体验。

**Blocked by:** T10

**Status:** pending (等待 T10 完成)

- [ ] 后端: E2E 测试 — 注册→登录→创建会话→发消息→收SSE→停止→重生成→编辑重发→上传文档→RAG对话→删除会话→删除文档
- [ ] 前端: 网络错误时显示重试按钮
- [ ] 前端: token 过期自动跳登录页 (Axios 401 拦截)
- [ ] 前端: 文档处理失败时 status 显示 failed 并提示
- [ ] 前端: 后端 429 限流时提示"请求过于频繁，请稍候"
- [ ] 前端: 流式接收时自动滚动到底部，用户手动上滚时不强制跳回
- [ ] 前端: InputArea 自适应高度 + 最大高度限制 (200px后内部滚动)
- [ ] 前端: 删除操作统一确认对话框
- [ ] 前端: 空状态提示 (无会话/无消息/无文档)
- [ ] 前端: 加载骨架屏 (会话列表加载中、消息历史加载中)
- [ ] 验证: 完整流程无报错，错误场景有友好提示，交互流畅
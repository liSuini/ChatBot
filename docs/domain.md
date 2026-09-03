---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '7b2f43d6-eb5d-4581-8efa-fc4f6b6a9495'
  PropagateID: '7b2f43d6-eb5d-4581-8efa-fc4f6b6a9495'
  ReservedCode1: 'a42c9270-bc62-4e4e-91be-34eb98c114c9'
  ReservedCode2: 'a42c9270-bc62-4e4e-91be-34eb98c114c9'
---

# ChatBot 领域模型

> 阶段3产出 | 日期: 2026-09-02

---

## 一、聚合根与边界

系统包含三个聚合根（Aggregate Root），每个聚合根管理一组紧密关联的实体：

```
┌─────────────────────────────────────────────────────────────────┐
│                        User 聚合                                 │
│  ┌──────────┐                                                    │
│  │   User   │ ◄── 聚合根                                         │
│  └──────────┘                                                    │
│  边界: 用户身份和认证，不直接持有会话/文档引用                      │
│  不变式: username 全局唯一; password_hash 非空                     │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     Conversation 聚合                            │
│  ┌──────────────┐                                                │
│  │ Conversation │ ◄── 聚合根                                      │
│  │  (会话)      │                                                │
│  └──────┬───────┘                                                │
│         │ 1:N                                                    │
│  ┌──────▼───────┐                                                │
│  │   Message    │                                                │
│  │  (消息)      │──┐ parent_message_id (自引用)                   │
│  └──────────────┘  │                                             │
│                    └──► Message (历史版本)                        │
│  边界: 会话内的消息管理、上下文截断、消息版本树                      │
│  不变式: Message 必须属于一个 Conversation;                        │
│         同一会话的消息按 created_at 有序;                          │
│         parent_message_id 只能指向同一会话内的消息                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Document 聚合                               │
│  ┌──────────┐                                                    │
│  │ Document │ ◄── 聚合根                                         │
│  │ (文档)   │                                                    │
│  └──────┬───┘                                                    │
│         │ 1:N                                                    │
│  ┌──────▼───────────┐                                            │
│  │ DocumentChunk    │                                            │
│  │ (文档分块+向量)   │── Embedding (1:1)                         │
│  └──────────────────┘                                            │
│  边界: 文档的生命周期管理，分块和向量随文档级联删除                   │
│  不变式: Chunk 必须属于一个 Document;                              │
│         Document 删除时所有 Chunk 和 Embedding 同时删除;            │
│         status=ready 的文档才可被 RAG 检索                         │
└─────────────────────────────────────────────────────────────────┘
```

## 二、实体定义

### 1. User（用户）

| 属性 | 类型 | 说明 |
|------|------|------|
| id | int | 唯一标识 |
| username | str | 登录用户名，全局唯一 |
| password_hash | str | bcrypt 哈希后的密码 |
| created_at | datetime | 注册时间 |
| updated_at | datetime | 更新时间 |

**行为**:
- `verify_password(plain) -> bool`: 校验明文密码是否匹配
- `is_owner(resource) -> bool`: 判断某资源（会话/文档）是否属于该用户

### 2. Conversation（会话）

| 属性 | 类型 | 说明 |
|------|------|------|
| id | int | 唯一标识 |
| user_id | int | 所属用户 |
| title | str | 会话标题，默认"新对话" |
| model_provider | str | 绑定的 LLM 提供商名称 |
| system_prompt | str \| None | 自定义系统提示词，可选 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 最后更新时间 |

**行为**:
- `add_message(role, content, parent_id=None) -> Message`: 向会话添加消息
- `get_context_messages(limit=20) -> list[Message]`: 获取上下文消息列表（用于发送给 LLM），按时间排序，截断到最近 N 条
- `get_message_tree(message_id) -> list[Message]`: 获取某条消息的版本历史链（沿 parent_message_id 回溯）
- `rename(title) -> None`: 重命名会话
- `belongs_to(user_id) -> bool`: 判断会话是否属于某用户

**聚合不变式**:
- 删除 Conversation 时级联删除其所有 Message
- model_provider 创建后不可更改（中途换模型会导致上下文不连贯）
- get_context_messages 返回的列表始终以 system prompt 开头（如有）

### 3. Message（消息）

| 属性 | 类型 | 说明 |
|------|------|------|
| id | int | 唯一标识 |
| conversation_id | int | 所属会话 |
| role | MessageRole | user / assistant / system |
| content | str | 消息文本内容 |
| tokens | int | token 计数，默认 0 |
| parent_message_id | int \| None | 编辑/重发时的父消息 ID |
| created_at | datetime | 创建时间 |

**MessageRole 枚举**:
- `USER`: 用户提问
- `ASSISTANT`: AI 回复
- `SYSTEM`: 系统提示

**行为**:
- `is_user_message() -> bool`: 是否为用户消息
- `is_assistant_message() -> bool`: 是否为 AI 消息
- `has_parent() -> bool`: 是否有父消息（是否为编辑/重发版本）
- `is_partial() -> bool`: 是否为停止生成的不完整内容（tokens < 预期且无后续消息）

### 4. Document（文档）

| 属性 | 类型 | 说明 |
|------|------|------|
| id | int | 唯一标识 |
| user_id | int | 所属用户 |
| filename | str | 原始文件名 |
| file_type | str | pdf / docx / txt / md |
| file_size | int | 文件大小（字节） |
| status | DocumentStatus | processing / ready / failed |
| chunk_count | int | 分块数量 |
| created_at | datetime | 上传时间 |
| updated_at | datetime | 更新时间 |

**DocumentStatus 枚举**:
- `PROCESSING`: 正在解析/分块/向量化
- `READY`: 处理完成，可被 RAG 检索
- `FAILED`: 处理失败

**行为**:
- `is_ready() -> bool`: 是否可被检索
- `is_large_file() -> bool`: 文件是否 ≥5MB（决定同步/异步处理策略）
- `belongs_to(user_id) -> bool`: 判断文档是否属于某用户
- `mark_ready(chunk_count) -> None`: 标记为已就绪
- `mark_failed() -> None`: 标记为处理失败

### 5. DocumentChunk（文档分块）

| 属性 | 类型 | 说明 |
|------|------|------|
| id | int | 唯一标识 |
| document_id | int | 所属文档 |
| chunk_index | int | 块序号 |
| content | str | 分块文本 |
| embedding | list[float] | 向量嵌入（1536维） |
| created_at | datetime | 创建时间 |

**行为**:
- `belongs_to(document) -> bool`: 判断属于某文档

### 6. LLMProvider（抽象实体，非持久化）

> LLMProvider 不持久化到数据库，是运行时对象，通过工厂模式创建。

| 属性/方法 | 说明 |
|-----------|------|
| `chat(messages, **kwargs)` | 非流式对话 |
| `stream_chat(messages, **kwargs)` | 流式对话，返回 AsyncGenerator |
| `embed(text)` | 单段文本向量化 |
| `embed_batch(texts)` | 批量向量化 |

**具体实现**: XingchenProvider, OpenAIProvider（可扩展）

## 三、实体关系图

```
┌──────┐ 1     N ┌──────────────┐ 1     N ┌─────────┐
│ User │─────────│ Conversation │─────────│ Message │
└──┬───┘         └──────────────┘         └────┬────┘
   │                                          │
   │ 1     N ┌──────────┐ 1     N ┌────────────┼────────┐
   └─────────│ Document │─────────│ DocumentChunk      │
             └──────────┘         └────────────────────┘

  Message.parent_message_id ──► Message (同会话内，版本链)
  User × Conversation:       用户只能看到/操作自己的会话
  User × Document:           用户只能看到/操作自己的文档
  LLMProvider × Conversation: 会话通过绑定的 provider 生成回复
  LLMProvider × Document:     文档通过 provider 的 embed 方法向量化
```

## 四、跨聚合协作场景

### 场景1: 发送消息 + 流式回复

```
用户发送消息
    │
    ▼
Chat 模块接收请求
    │
    ├─► Conversation 聚合: add_message(role=USER, content)
    ├─► Conversation 聚合: get_context_messages(limit=20)
    │
    ├─► [如果 rag_enabled]
    │     └─► Document 聚合: 检索 Top-K chunks (按 user_id 隔离)
    │         └─► 拼接为 system prompt 注入上下文
    │
    ├─► LLMProvider: stream_chat(messages)
    │     └─► 逐 token 推送 SSE events
    │
    └─► Conversation 聚合: add_message(role=ASSISTANT, content=完整回复)
```

### 场景2: 编辑消息后重发

```
用户编辑某条 user 消息
    │
    ▼
Chat 模块接收请求
    │
    ├─► Conversation 聚合: add_message(
    │       role=USER,
    │       content=新内容,
    │       parent_message_id=原消息ID   ← 指向被编辑的原消息
    │   )
    │
    ├─► Conversation 聚合: get_context_messages()
    │     └─► 从新消息开始重新构建上下文（不含旧消息链）
    │
    ├─► LLMProvider: stream_chat(messages)
    │
    └─► Conversation 聚合: add_message(
            role=ASSISTANT,
            content=新回复,
            parent_message_id=原AI回复ID   ← 指向旧 AI 回复
        )
```

### 场景3: 上传文档 + RAG 处理

```
用户上传文件
    │
    ▼
Document 模块接收请求
    │
    ├─► Document 聚合: 创建 Document (status=PROCESSING)
    │
    ├─► 文件解析 (PDF/DOCX/TXT/MD)
    ├─► 文本分块 (RecursiveCharacterTextSplitter)
    │
    ├─► LLMProvider: embed_batch(chunks) ← 生成向量
    │
    ├─► Document 聚合: 批量创建 DocumentChunk (含 embedding)
    │
    └─► Document 聚合: mark_ready(chunk_count=N)
```

## 五、领域服务

跨多个聚合的协作逻辑不适合放在单个实体内，提取为领域服务：

| 服务 | 职责 | 依赖的聚合 |
|------|------|------------|
| ChatService | 消息发送、流式回复、RAG 判断与注入 | Conversation + Document + LLMProvider |
| DocumentService | 文档上传、解析、分块、向量化、删除 | Document + LLMProvider |
| RAGService | 向量检索、上下文拼接 | Document + LLMProvider |
| AuthService | 注册、登录、Token 生成与校验 | User |
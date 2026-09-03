---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: '385f5149-8a71-413e-a8da-7c89cc3fe3eb'
  PropagateID: '385f5149-8a71-413e-a8da-7c89cc3fe3eb'
  ReservedCode1: '351bb523-a967-4f7d-860c-fcbb2f50162b'
  ReservedCode2: '351bb523-a967-4f7d-860c-fcbb2f50162b'
---

# ChatBot 领域上下文

一个面向团队内部的 AI 对话问答系统，支持多轮对话、文档 RAG 问答和流式回复。

## Language

**User**:
系统注册用户，团队内部成员。拥有自己的会话和文档，数据与其他用户隔离。
_Avoid_: 账号, 账户, account

**Conversation**:
用户与 AI 的一段完整对话，包含多条按时间排列的消息。创建时绑定一个模型，可自定义系统提示词。
_Avoid_: 聊天, 会话(session), 对话窗口

**Message**:
对话中的一条消息，角色为 user/assistant/system。通过 parent_message_id 可形成消息版本树，支持编辑重发和重新生成的历史追溯。
_Avoid_: 记录, 条目, entry

**MessageRole**:
消息角色的枚举值，区分消息来源。user=用户提问，assistant=AI回复，system=系统提示。
_Avoid_: 类型, sender

**Document**:
用户上传的知识文档（PDF/Word/TXT/MD），经过解析、分块、向量化后用于 RAG 检索增强。
_Avoid_: 文件, 知识库, file

**DocumentChunk**:
文档被切分后的文本片段，每个片段有独立的向量嵌入。是 RAG 向量检索单位。
_Avoid_: 片段, 块, fragment

**Embedding**:
文本的向量表示，由 LLM 嵌入模型生成。用于计算语义相似度，支撑 RAG 检索。
_Avoid_: 向量, 特征, vector

**LLMProvider**:
大语言模型提供商的抽象接口，定义对话和向量化的统一契约。具体实现（星辰/OpenAI等）可配置切换。
_Avoid_: 模型, 引擎, engine

**RAG**:
检索增强生成（Retrieval-Augmented Generation）。用户提问时，先检索相关文档片段注入上下文，再由 LLM 生成回答。
_Avoid_: 文档问答, 知识检索

**StreamEvent**:
SSE 流式推送的事件单元，类型为 start/token/done/error。前端根据事件类型更新 UI。
_Avoid_: 推送, 事件流

**DocumentStatus**:
文档处理状态的枚举值。processing=处理中，ready=可用，failed=处理失败。
_Avoid_: 状态, state

## Relationships

- User **拥有** 多个 Conversation（1:N）
- User **拥有** 多个 Document（1:N）
- Conversation **包含** 多条 Message（1:N），Message 不能脱离 Conversation 存在
- Message **可指向** 另一条 Message 作为 parent（自引用，编辑/重发的历史链）
- Document **包含** 多个 DocumentChunk（1:N），Chunk 不能脱离 Document 存在
- DocumentChunk **持有** 一个 Embedding（1:1）
- LLMProvider **服务于** Conversation 的消息生成和 Document 的向量化
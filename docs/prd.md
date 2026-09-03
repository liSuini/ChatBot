---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'dc371e9e-ec6f-439f-b898-dbe8b7c31389'
  PropagateID: 'dc371e9e-ec6f-439f-b898-dbe8b7c31389'
  ReservedCode1: '931340dc-df6a-49c1-bbbe-c051859d7c10'
  ReservedCode2: '931340dc-df6a-49c1-bbbe-c051859d7c10'
---

# PRD: ChatBot 对话问答系统

> 阶段2产出 | 日期: 2026-09-02

---

## 1. Introduction / 概述

ChatBot 是一个面向团队内部（<50人）的类 ChatGPT 对话问答系统。支持多轮对话、会话管理、文档 RAG 问答、Markdown 渲染和消息操作。系统采用前后端分离架构，后端 FastAPI 单体分层，前端 React SPA，通过 Docker Compose 一键部署。

**解决的核心问题**：团队成员需要一个统一的 AI 对话工具，能够进行多轮上下文对话、基于上传文档进行精准问答，且各成员数据相互隔离。

## 2. Goals / 目标

- 支持多轮上下文对话，会话历史持久化存储
- 支持 SSE 流式返回，前端实时打字机效果
- 支持文档上传 + RAG 检索增强问答
- AI 回复支持 Markdown 渲染和代码高亮
- 支持消息编辑重发、停止生成、重新生成
- 多 LLM 模型可切换（星辰/OpenAI 等）
- 用户数据隔离，JWT 认证
- Docker Compose 一键部署

## 3. User Stories / 用户故事

### US-001: 用户注册
**Description:** As a 团队成员, I want to 自行注册账号 so that I can 使用系统进行 AI 对话.

**Acceptance Criteria:**
- [ ] 注册页面包含用户名、密码、确认密码字段
- [ ] 用户名唯一校验，重复时返回 409 错误
- [ ] 密码 bcrypt 哈希存储
- [ ] 注册成功后自动登录并跳转聊天页
- [ ] Typecheck/lint passes

### US-002: 用户登录
**Description:** As a 已注册用户, I want to 登录系统 so that I can 查看和管理我的对话.

**Acceptance Criteria:**
- [ ] 登录页面包含用户名、密码字段
- [ ] 登录成功返回 JWT access_token (30min) + refresh_token (7d)
- [ ] 登录失败返回 401 并提示错误原因
- [ ] Token 存储在前端，后续请求自动携带
- [ ] Typecheck/lint passes

### US-003: 创建新会话
**Description:** As a 已登录用户, I want to 创建新的对话会话 so that I can 开始一段独立的对话.

**Acceptance Criteria:**
- [ ] 侧边栏有"新建对话"按钮
- [ ] 点击后创建新会话，默认标题"新对话"
- [ ] 新会话自动选中并显示空白聊天界面
- [ ] 会话创建时绑定当前选择的模型
- [ ] Typecheck/lint passes
- [ ] Verify in browser

### US-004: 会话列表展示与切换
**Description:** As a 已登录用户, I want to 在侧边栏看到所有会话并切换 so that I can 管理多个对话主题.

**Acceptance Criteria:**
- [ ] 侧边栏按 updated_at 倒序展示当前用户的所有会话
- [ ] 每条会话显示标题和最后更新时间
- [ ] 当前选中的会话高亮显示
- [ ] 点击切换会话时加载该会话的消息历史
- [ ] 切换会话时优先从内存缓存读取，不重复请求
- [ ] Typecheck/lint passes
- [ ] Verify in browser

### US-005: 重命名会话
**Description:** As a 已登录用户, I want to 重命名会话 so that I can 用有意义的标题区分不同对话.

**Acceptance Criteria:**
- [ ] 会话项支持点击编辑标题
- [ ] 回车保存，ESC 取消
- [ ] 保存后侧边栏实时更新
- [ ] Typecheck/lint passes
- [ ] Verify in browser

### US-006: 删除会话
**Description:** As a 已登录用户, I want to 删除不需要的会话 so that I can 保持列表整洁.

**Acceptance Criteria:**
- [ ] 会话项有删除按钮（hover 显示）
- [ ] 删除前弹出确认对话框
- [ ] 确认后删除会话及其所有消息（级联删除）
- [ ] 删除当前选中会话后自动切换到列表第一条
- [ ] Typecheck/lint passes
- [ ] Verify in browser

### US-007: 发送消息并获得流式回复
**Description:** As a 已登录用户, I want to 发送消息并获得 AI 的流式回复 so that I can 像使用 ChatGPT 一样实时看到回答.

**Acceptance Criteria:**
- [ ] 输入框支持多行文本，自适应高度
- [ ] 回车发送，Shift+回车换行
- [ ] 发送后立即显示用户消息气泡（右侧）
- [ ] AI 回复以流式打字机效果逐字显示（左侧气泡）
- [ ] 流式过程中发送按钮变为"停止生成"按钮
- [ ] 生成完成后输入框重新可用
- [ ] 发送空消息被禁止
- [ ] Typecheck/lint passes
- [ ] Verify in browser

### US-008: 停止生成
**Description:** As a 已登录用户, I want to 在 AI 回复过程中点击停止 so that I can 中断不需要的长回复.

**Acceptance Criteria:**
- [ ] 流式过程中显示"停止生成"按钮
- [ ] 点击停止后立刻中断流式传输
- [ ] 已生成的部分内容保留在界面上
- [ ] 后端将部分内容存入数据库作为 assistant 消息
- [ ] 停止后输入框恢复可用
- [ ] Typecheck/lint passes
- [ ] Verify in browser

### US-009: 重新生成回复
**Description:** As a 已登录用户, I want to 对 AI 的回复点击重新生成 so that I can 获得不同的回答.

**Acceptance Criteria:**
- [ ] AI 消息气泡下方有"重新生成"按钮
- [ ] 点击后重新请求 LLM 生成回复
- [ ] 新回复以流式方式显示
- [ ] 旧回复标记为历史版本（parent_message_id 指向旧回复）
- [ ] 重新生成期间输入框禁用
- [ ] Typecheck/lint passes
- [ ] Verify in browser

### US-010: 编辑消息后重发
**Description:** As a 已登录用户, I want to 编辑我之前发送的消息 so that I can 修正提问并获得新的回答.

**Acceptance Criteria:**
- [ ] 用户消息气泡支持点击编辑
- [ ] 编辑后发送触发重新生成 AI 回复
- [ ] 新消息的 parent_message_id 指向被编辑的原消息
- [ ] 编辑前的消息和回复保留为历史版本
- [ ] Typecheck/lint passes
- [ ] Verify in browser

### US-011: Markdown 渲染与代码高亮
**Description:** As a 已登录用户, I want to AI 回复支持 Markdown 格式渲染 so that I can 清晰阅读代码块、表格、列表等内容.

**Acceptance Criteria:**
- [ ] AI 回复支持标题、加粗、斜体、列表、表格、引用块
- [ ] 代码块语法高亮
- [ ] 行内代码用不同背景色区分
- [ ] 链接可点击跳转
- [ ] 流式传输过程中增量渲染，完成后做一次完整渲染确保格式正确
- [ ] Typecheck/lint passes
- [ ] Verify in browser

### US-012: 上传文档用于 RAG 问答
**Description:** As a 已登录用户, I want to 上传文档（PDF/Word/TXT/MD） so that I can 基于文档内容进行 AI 问答.

**Acceptance Criteria:**
- [ ] 文档管理页有上传按钮，支持拖拽上传
- [ ] 支持文件类型：pdf, docx, txt, md
- [ ] 单文件最大 10MB，超限提示
- [ ] 小文件（<5MB）同步处理，上传成功后 status 为 ready
- [ ] 大文件（≥5MB）后台处理，status 为 processing，前端可轮询状态
- [ ] 上传成功后显示文件名、大小、状态、分块数
- [ ] 文档列表按上传时间倒序展示
- [ ] Typecheck/lint passes
- [ ] Verify in browser

### US-013: 基于文档的 RAG 问答
**Description:** As a 已登录用户, I want to 在对话中开启 RAG 检索 so that I can 基于上传的文档内容获得精准回答.

**Acceptance Criteria:**
- [ ] 聊天界面有 RAG 开关按钮
- [ ] 开启 RAG 后发送消息时，后端先检索相关文档片段
- [ ] 检索到相关内容时注入到 system prompt 中
- [ ] AI 回复基于文档内容回答
- [ ] 未检索到相关文档时走普通对话
- [ ] RAG 检索范围限当前用户的文档
- [ ] Typecheck/lint passes
- [ ] Verify in browser

### US-014: 删除文档
**Description:** As a 已登录用户, I want to 删除已上传的文档 so that I can 清理不再需要的文档.

**Acceptance Criteria:**
- [ ] 文档列表每项有删除按钮
- [ ] 删除前确认对话框
- [ ] 确认后删除文档及其所有分块和向量
- [ ] 删除后列表实时更新
- [ ] Typecheck/lint passes
- [ ] Verify in browser

### US-015: 模型切换
**Description:** As a 已登录用户, I want to 选择不同的 AI 模型 so that I can 根据需要使用不同的模型.

**Acceptance Criteria:**
- [ ] 聊天界面顶部或侧边有模型选择下拉框
- [ ] 可选模型列表从后端配置获取
- [ ] 选择模型后新会话使用该模型
- [ ] 模型切换不影响已有会话的模型绑定
- [ ] Typecheck/lint passes
- [ ] Verify in browser

### US-016: 会话上下文管理
**Description:** As a 已登录用户, I want to 系统自动管理对话上下文 so that I can 长时间对话不会因为超长而报错.

**Acceptance Criteria:**
- [ ] 后端自动拼接历史消息作为上下文发送给 LLM
- [ ] 对话超过模型 token 上限时自动截断早期消息（保留最近 N 条）
- [ ] 截断策略：保留 system prompt + 最近 N 条对话
- [ ] 截断对用户透明，用户无感知
- [ ] Typecheck/lint passes

### US-017: 错误处理与用户反馈
**Description:** As a 已登录用户, I want to 遇到错误时看到清晰的提示 so that I can 知道发生了什么并采取行动.

**Acceptance Criteria:**
- [ ] 网络错误时显示重试按钮
- [ ] LLM 生成失败时在消息区域显示错误提示，已有内容保留
- [ ] 未登录或 token 过期自动跳转登录页
- [ ] 文档处理失败时状态显示 failed 并提示用户
- [ ] 请求被限流时提示等待
- [ ] Typecheck/lint passes
- [ ] Verify in browser

### US-018: Docker 一键部署
**Description:** As a 部署人员, I want to 通过 docker compose up 一键启动系统 so that I can 快速部署到服务器.

**Acceptance Criteria:**
- [ ] docker-compose.yml 包含 mysql、backend、frontend 三个服务
- [ ] .env.example 提供所有必需环境变量模板
- [ ] 后端自动运行数据库迁移（alembic upgrade head）
- [ ] 前端构建产物由 Nginx 提供静态服务
- [ ] Nginx 配置 SSE 代理（关闭 buffering，延长超时）
- [ ] 启动后访问 http://localhost 即可使用

## 4. Functional Requirements / 功能需求

- FR-1: 用户可自行注册，用户名唯一，密码 bcrypt 哈希存储
- FR-2: 登录返回 JWT access_token (30min) + refresh_token (7d)
- FR-3: 所有 API 路由需 JWT 认证（除注册/登录外）
- FR-4: 用户可创建会话，会话创建时绑定选定模型
- FR-5: 用户可查看、重命名、删除自己的会话
- FR-6: 会话列表按 updated_at 倒序排列
- FR-7: 删除会话时级联删除其所有消息
- FR-8: 用户可发送消息，后端存储 user 消息后调用 LLM
- FR-9: LLM 回复以 SSE 流式返回（start/token/done/error 四类事件）
- FR-10: 发送消息时可指定 rag_enabled 参数启用 RAG 检索
- FR-11: RAG 检索 Top-K=5，范围限当前用户文档
- FR-12: 检索到的文档片段注入 system prompt 后发送给 LLM
- FR-13: 用户可停止正在生成的回复，部分内容存库保留
- FR-14: 用户可对 AI 回复点击重新生成，旧回复保留为历史版本
- FR-15: 用户可编辑已发送的消息并重发，新旧消息通过 parent_message_id 关联
- FR-16: 对话上下文超过 token 上限时自动截断早期消息
- FR-17: 用户可上传文档（pdf/docx/txt/md），单文件最大 10MB
- FR-18: 文档上传后自动解析、分块、向量化、存储
- FR-19: 小文件（<5MB）同步处理，大文件（≥5MB）后台处理+轮询状态
- FR-20: 用户可查看文档列表和处理状态
- FR-21: 用户可删除文档，级联删除分块和向量
- FR-22: 前端 AI 回复支持 Markdown 渲染和代码语法高亮
- FR-23: 流式传输过程中增量渲染，完成后完整渲染
- FR-24: 普通接口限流 60 次/分钟，LLM 消息接口限流 20 次/分钟
- FR-25: 所有数据查询带 user_id 隔离，不可访问他人数据
- FR-26: 系统通过 docker compose up 一键部署
- FR-27: 后端启动时自动运行数据库迁移
- FR-28: 前端构建产物由 Nginx 提供服务并代理 API 请求

## 5. Non-Goals / 不在范围内

- 不做多角色权限管理（RBAC），无管理员角色
- 不做对话导出功能（Markdown/JSON 导出）
- 不做 Prompt 模板库功能
- 不做模型参数细粒度配置（temperature/top_p 等首版不开放给用户）
- 不做对话内容审核/敏感词过滤
- 不做消息搜索功能
- 不做移动端原生 App
- 不做暗色模式（首版）
- 不做多语言国际化
- 不做实时多人协作/共享会话
- 不做用量计费/统计面板

## 6. Design Considerations / 设计考量

- UI 布局参考 ChatGPT：左侧会话列表侧边栏 + 右侧聊天区域
- 消息气泡：用户消息右对齐，AI 消息左对齐，头像区分
- 输入框底部固定，自适应高度，最大高度限制后内部滚动
- 文档管理页独立路由，不在聊天界面内
- Ant Design 组件库统一风格
- 响应式：侧边栏可折叠，窄屏适配

## 7. Technical Considerations / 技术考量

- **后端**: FastAPI + SQLAlchemy (async) + Alembic + aiomysql
- **前端**: React 18 + Vite + TypeScript + Ant Design + Zustand
- **SSE**: fetch + ReadableStream 手动解析 SSE 协议（非 EventSource，因需 POST + JWT header）
- **LLM**: 抽象 Provider 接口，工厂模式 + 配置驱动切换
- **RAG**: PyMuPDF(PDF) / python-docx(DOCX) 解析，RecursiveCharacterTextSplitter 分块
- **向量存储**: MySQL 9.0+ VECTOR(1536) 类型 + DISTANCE 函数
- **数据库**: MySQL 9.0+，备选 8.0 + JSON 列存向量
- **部署**: Docker Compose（mysql + backend + frontend/Nginx）
- **安全**: JWT + bcrypt + slowapi 限流 + Pydantic 校验 + 参数化查询

## 8. Success Metrics / 成功指标

- 用户可完成注册→登录→创建会话→发送消息→获得流式回复的完整流程
- 文档上传后 10 秒内完成处理并可进行 RAG 问答
- SSE 流式延迟 < 1 秒（首 token 到达时间）
- 停止生成、重新生成、编辑重发均正常工作
- 多用户数据完全隔离，不可越权访问
- docker compose up 后 30 秒内系统可用

## 9. Open Questions / 待确认

- 星辰大模型的 API 地址和接口规格需确认（是否兼容 OpenAI 格式）
- MySQL 9.0 在 Windows Docker Desktop 下的稳定性需验证
- 文档分块参数（chunk_size=500, overlap=50）是否需根据实际效果调优
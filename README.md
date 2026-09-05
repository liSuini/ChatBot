---
AIGC:
  ContentProducer: '001191110102MAD55U9H0F10002'
  ContentPropagator: '001191110102MAD55U9H0F10002'
  Label: '1'
  ProduceID: 'f5f13cd3-2293-47c2-8fc5-81f58e949359'
  PropagateID: 'f5f13cd3-2293-47c2-8fc5-81f58e949359'
  ReservedCode1: '3bd195f9-09dc-4069-8ec3-9820647d963d'
  ReservedCode2: '3bd195f9-09dc-4069-8fc5-81f58e949359'
---

# ChatBot 使用说明

一个面向团队内部的 AI 对话问答系统，支持多轮对话、文档 RAG 问答、流式回复和 Docker 一键部署。

---

## 目录

| 页面 | 路径 | 说明 |
|------|------|------|
| 登录/注册 | `/login` | 用户登录与注册入口 |
| 聊天 | `/chat` | AI 对话主界面（支持 SSE 流式回复、Markdown 渲染） |
| 文档管理 | `/documents` | 上传/管理知识文档（PDF/DOCX/TXT/MD） |
| 健康检查 | `/health` | 后端健康检查端点（GET，返回 `{"status":"ok"}`） |
| API 文档 | `/docs` | FastAPI 自动生成的 Swagger 文档 |

> **注意**：本项目无独立的管理后台。文档管理页面 (`/documents`) 兼具内容管理功能，用户管理需通过数据库直接操作。

---

## 快速开始（Docker 一键部署）

### 前置要求

- [Docker](https://www.docker.com/) 29+（含 Docker Compose v2+）
- 操作系统：Windows / macOS / Linux 均可

### 步骤

```bash
# 1. 克隆仓库
git clone https://github.com/liSuini/ChatBot.git
cd ChatBot

# 2. 复制环境变量模板并按需修改
cp .env.example .env

# 3. 一键构建并启动（首次会拉取镜像，约 5-10 分钟）
docker compose up --build -d

# 4. 查看服务状态
docker compose ps
```

启动完成后，浏览器访问：

- **应用首页**：<http://localhost>
- **API 文档**：<http://localhost/docs>

### 首次使用

1. 打开 <http://localhost>，自动跳转到登录页
2. 点击「注册」，创建账号（用户名 + 密码）
3. 登录后进入聊天页面
4. 点击左侧「新建对话」开始对话
5. 如需文档问答，先在「文档管理」上传文档，再在聊天页打开 RAG 开关

### 停止与清理

```bash
# 停止服务（数据保留）
docker compose stop

# 重新启动
docker compose start

# 停止并删除容器（数据库数据保留在 volume 中）
docker compose down

# 彻底清除包括数据（谨慎！）
docker compose down -v
```

---

## 在其他计算机上拉取部署

### 方式一：Docker 部署（推荐）

在新计算机上只需安装 Docker，然后：

```bash
# 1. 安装 Docker（参考 https://docs.docker.com/get-docker/）

# 2. 克隆仓库
git clone https://github.com/liSuini/ChatBot.git
cd ChatBot

# 3. 创建环境变量文件
cp .env.example .env

# 4. 按需修改 .env 中的配置（至少修改 SECRET_KEY 和数据库密码）
#    Windows: notepad .env
#    macOS/Linux: nano .env

# 5. 构建并启动
docker compose up --build -d

# 6. 验证服务是否正常
curl http://localhost/health
# 预期输出: {"status":"ok"}
```

### 方式二：本地开发模式部署（不使用 Docker）

适用于需要修改代码或无法使用 Docker 的场景。

#### 前置要求

- Python 3.12+
- [uv](https://docs.astral.sh/uv/)（Python 包管理工具）
- Node.js 20+（含 npm）
- MySQL 9.0（或 MySQL 8.0+）

#### 步骤

```bash
# 1. 克隆仓库
git clone https://github.com/liSuini/ChatBot.git
cd ChatBot

# 2. 准备数据库
#    在 MySQL 中创建数据库和用户：
#    CREATE DATABASE chatbot CHARACTER SET utf8mb4;
#    CREATE USER 'chatbot'@'%' IDENTIFIED BY 'your_password';
#    GRANT ALL ON chatbot.* TO 'chatbot'@'%';

# 3. 配置后端环境变量
cd backend
cp .env.example .env
#    编辑 .env，填写 DATABASE_URL、SECRET_KEY 等

# 4. 安装后端依赖并迁移数据库
uv sync
uv run alembic upgrade head

# 5. 启动后端（端口 8010）
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8010

# 6. 新开终端，安装前端依赖并启动
cd frontend
npm install
npm run dev    # 启动在 http://localhost:5173
```

浏览器访问 <http://localhost:5173> 即可。

---

## 环境变量说明

`.env` 文件中所有可配置项（参考 `.env.example`）：

### 数据库

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `MYSQL_ROOT_PASSWORD` | `rootpass` | MySQL root 密码 |
| `MYSQL_DATABASE` | `chatbot` | 数据库名 |
| `MYSQL_USER` | `chatbot` | 数据库用户 |
| `MYSQL_PASSWORD` | `changeme` | 数据库密码 |
| `DATABASE_URL` | 自动拼接 | 本地开发时需手动填写完整连接串 |

### JWT 认证

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `SECRET_KEY` | `change-me-...` | JWT 签名密钥（**生产环境必须修改**） |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access Token 过期时间（分钟） |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh Token 过期时间（天） |

### LLM 模型

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DEFAULT_LLM_PROVIDER` | `mock` | 默认模型（mock=测试用/openai/xingchen） |
| `XINGCHEN_API_KEY` | 空 | 星辰 API Key |
| `XINGCHEN_BASE_URL` | 空 | 星辰 API 地址 |
| `XINGCHEN_MODEL` | `xingchen-pro` | 星辰对话模型名 |
| `XINGCHEN_EMBED_MODEL` | `xingchen-embedding` | 星辰嵌入模型名 |
| `OPENAI_API_KEY` | 空 | OpenAI API Key |
| `OPENAI_BASE_URL` | `https://api.openai.com/v1` | OpenAI API 地址 |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI 对话模型名 |
| `OPENAI_EMBED_MODEL` | `text-embedding-3-small` | OpenAI 嵌入模型名 |
| `EMBED_PROVIDER` | 空（跟随对话模型） | 嵌入模型独立配置（见下方说明） |

> 使用 `mock` 模式时，AI 固定回复"你好世界"，适合测试和演示。要使用真实 AI，配置对应 Provider 的 API Key。

### 嵌入模型独立配置（RAG 文档向量化）

文档上传和 RAG 检索需要调用 **Embedding 接口**将文本转为向量。部分对话模型（如 DeepSeek）**不提供 Embedding 接口**，此时需要通过 `EMBED_PROVIDER` 单独配置嵌入模型，实现「对话模型」和「嵌入模型」分离。

> **核心规则**：`EMBED_PROVIDER` 留空时跟随 `DEFAULT_LLM_PROVIDER`；设置后独立使用。嵌入模型必须支持 **1536 维**输出，否则文档上传会失败。

#### 方案一：仅用 mock 嵌入（默认，快速体验）

文档可上传管理，但 RAG 检索不做语义匹配（返回空），适合不需要文档问答的场景：

```env
DEFAULT_LLM_PROVIDER=openai          # 对话用 DeepSeek
OPENAI_API_KEY=你的deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
EMBED_PROVIDER=mock                  # 嵌入用 mock（不调用外部 API）
```

#### 方案二：DeepSeek 对话 + OpenAI 嵌入（推荐，RAG 可用）

对话走 DeepSeek，文档向量化走 OpenAI `text-embedding-3-small`：

```env
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=你的OpenAI-key        # 用于嵌入（和对话可以是同一个 key）
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
OPENAI_EMBED_MODEL=text-embedding-3-small
EMBED_PROVIDER=openai                # 嵌入走 OpenAI 官方
```

> ⚠️ 注意：此配置下 `OPENAI_API_KEY` 和 `OPENAI_BASE_URL` 同时用于对话和嵌入。若对话用 DeepSeek、嵌入用 OpenAI，两者 base_url 不同，需通过以下方式分离：

```env
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=你的OpenAI-key        # OpenAI 的 key（嵌入用）
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini             # 对话模型（若仍想用 DeepSeek 对话，见下方方案四）
OPENAI_EMBED_MODEL=text-embedding-3-small
EMBED_PROVIDER=openai
```

#### 方案三：DeepSeek 对话 + 星辰嵌入

对话走 DeepSeek，文档向量化走星辰大模型：

```env
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=你的deepseek-key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat

XINGCHEN_API_KEY=你的星辰key
XINGCHEN_BASE_URL=https://your-xingchen-endpoint/v1
XINGCHEN_EMBED_MODEL=xingchen-embedding
EMBED_PROVIDER=xingchen              # 嵌入走星辰
```

#### 方案四：对话和嵌入用不同 Provider 的 OpenAI 兼容服务

系统当前 `EMBED_PROVIDER` 支持 `mock`、`openai`、`xingchen` 三个值。如果对话和嵌入都是 OpenAI 兼容协议但 base_url 不同（如对话用 DeepSeek、嵌入用智谱），可通过以下方式实现：

由于 `openai` provider 的 base_url 是全局的，对话和嵌入无法用不同的 base_url。如需这种组合，建议：
- 对话用 DeepSeek（`DEFAULT_LLM_PROVIDER=openai` + deepseek base_url）
- 嵌入用 mock 或星辰（`EMBED_PROVIDER=mock` 或 `xingchen`）

#### 配置生效

修改 `.env` 后重建后端容器（环境变量变更必须重建，不能仅 restart）：

```bash
docker compose up -d backend
```

**验证 RAG 是否生效**：上传一份文档 → 状态变「就绪」→ 聊天页打开 RAG 开关 → 提问文档内容，AI 应能基于文档回答。若回答不涉及文档内容，检查后端日志是否有 Embedding 调用成功记录。

---

## 模型配置指南

系统支持 3 个 LLM Provider，通过 `.env` 配置切换。配置好 API Key 后，前端新建会话时会自动显示可用的模型下拉框。

### 支持的 Provider

| Provider | 名称 | 说明 |
|----------|------|------|
| `mock` | Mock（测试） | 不调用外部 API，固定回复"你好世界" |
| `xingchen` | 星辰大模型 | 走 OpenAI 兼容协议 |
| `openai` | OpenAI | 官方 API，兼容所有 OpenAI 协议的模型 |

### 配置方法

编辑 `.env` 文件（Docker 部署在项目根目录，本地开发在 `backend/` 目录），按需选择以下一种配置：

#### 方式一：使用 OpenAI

```env
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=sk-你的key
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
OPENAI_EMBED_MODEL=text-embedding-3-small
```

#### 方式二：使用星辰大模型

```env
DEFAULT_LLM_PROVIDER=xingchen
XINGCHEN_API_KEY=你的key
XINGCHEN_BASE_URL=https://your-xingchen-endpoint/v1
XINGCHEN_MODEL=xingchen-pro
XINGCHEN_EMBED_MODEL=xingchen-embedding
```

#### 方式三：兼容其他 OpenAI 协议模型（DeepSeek / 通义千问 / Moonshot 等）

填到 `openai` 配置项，修改 `base_url` 和模型名即可：

```env
DEFAULT_LLM_PROVIDER=openai
OPENAI_API_KEY=你的key
OPENAI_BASE_URL=https://api.deepseek.com/v1
OPENAI_MODEL=deepseek-chat
OPENAI_EMBED_MODEL=text-embedding-3-small
```

> **嵌入模型**（`*_EMBED_MODEL`）用于文档 RAG 向量化，必须支持 1536 维输出。如果嵌入维度不一致，文档上传和 RAG 检索会失败。不使用 RAG 功能时可忽略。

### 应用配置

修改 `.env` 后需重启后端服务使配置生效：

```bash
# Docker 部署
docker compose restart backend

# 本地开发：Ctrl+C 停止 uvicorn 后重新运行
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
```

### 前端使用

1. 配置好 API Key 并重启后端后，打开聊天页面
2. 点击左侧「新建对话」
3. 在弹出的模型下拉框中选择已配置的模型
4. 开始对话

> **注意**：会话创建后模型绑定不可更改。如需切换模型，请新建会话。`mock` 模型不需要任何 API Key，适合快速测试系统功能。

---

## 功能概览

### 聊天功能

- **多轮对话**：创建会话后持续对话，AI 保留上下文
- **流式回复**：SSE 逐字流式输出，打字机效果
- **Markdown 渲染**：支持代码高亮、表格、列表、链接
- **消息操作**：停止生成、重新生成、编辑重发（保留历史版本）
- **模型切换**：创建会话时选择不同 AI 模型

### 文档 RAG

- **支持格式**：PDF、DOCX、TXT、MD（最大 10MB）
- **自动处理**：上传后自动解析 → 分块 → 向量化 → 存储
- **检索问答**：聊天页打开 RAG 开关，提问时自动检索相关文档片段注入上下文

### 用户隔离

- 每个用户的会话和文档完全隔离
- 用户 A 无法访问用户 B 的任何数据
- 所有 API 请求需携带 JWT Bearer Token

---

## 常见问题

### 端口冲突

| 端口 | 用途 | 冲突时处理 |
|------|------|------------|
| 80 | 前端 Nginx | 修改 `docker-compose.yml` 中 `"80:80"` 为其他端口 |
| 3306 | MySQL（容器内） | 默认不暴露到宿主机，无冲突 |
| 8010 | 后端 Uvicorn（容器内） | 默认不暴露到宿主机，无冲突 |

如果本地已运行 MySQL 占用 3306，Docker 部署不受影响（容器 MySQL 不映射端口）。

### 首次启动慢

首次 `docker compose up --build` 需要拉取基础镜像并安装依赖，约 5-10 分钟。后续启动利用缓存，约 10-30 秒。

### 数据库迁移

后端容器启动时会自动执行 `alembic upgrade head` 迁移数据库。如需手动迁移：

```bash
docker compose exec backend uv run alembic upgrade head
```

### 查看日志

```bash
# 查看所有服务日志
docker compose logs

# 查看后端日志（实时）
docker compose logs -f backend

# 查看最近 50 行
docker compose logs --tail 50 backend
```

### 进入容器调试

```bash
# 进入后端容器
docker compose exec backend bash

# 进入 MySQL 容器
docker compose exec mysql mysql -u chatbot -p chatbot
```

---

## 技术架构

```
浏览器 → Nginx (:80) ─┬─ 静态资源 (React SPA)
                       ├─ /api/ → FastAPI (:8010) ── MySQL (:3306)
                       └─ /health → FastAPI
```

| 组件 | 技术栈 |
|------|--------|
| 前端 | React 19 + TypeScript + Vite + Ant Design + Zustand |
| 后端 | FastAPI + SQLAlchemy 2.0 (async) + Alembic |
| 数据库 | MySQL 9.0（原生 VECTOR(1536) 向量支持） |
| 部署 | Docker + Docker Compose + Nginx |

---

## 项目结构

```
ChatBot/
├── docker-compose.yml      # 一键部署编排文件
├── .env.example             # 环境变量模板
├── backend/                 # 后端
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── alembic/             # 数据库迁移
│   ├── app/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── core/            # 配置、数据库、异常
│   │   ├── models/          # ORM 模型
│   │   ├── api/v1/          # API 路由
│   │   ├── services/        # 业务逻辑
│   │   ├── llm/             # LLM Provider 抽象
│   │   └── rag/             # 文档解析 + RAG
│   └── tests/               # 测试（71 项）
├── frontend/                # 前端
│   ├── Dockerfile
│   ├── nginx.conf           # Nginx 配置
│   ├── package.json
│   └── src/
│       ├── pages/           # 页面 (Login/Chat/Documents)
│       ├── components/      # 组件
│       ├── stores/          # Zustand 状态管理
│       └── services/        # API 调用
└── docs/                    # 设计文档 + 工单
```

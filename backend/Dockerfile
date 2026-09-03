# 后端镜像：python:3.12-slim + uv + alembic 迁移 + uvicorn
FROM python:3.12-slim

# 编译依赖所需系统包（bcrypt 等）
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libmariadb-dev pkg-config \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv（与项目锁定的版本无关，仅作依赖安装工具）
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# 先拷贝依赖清单，利用 Docker 层缓存
COPY pyproject.toml uv.lock ./

# 同步生产依赖（不含 dev 组）
RUN uv sync --frozen --no-dev

# 拷贝应用代码与 Alembic 配置
COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app

# 创建上传目录
RUN mkdir -p /app/uploads

# 启动脚本：先迁移再启动
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8010"]

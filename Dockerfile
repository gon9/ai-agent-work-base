# Builder stage: Python依存関係
FROM python:3.12-slim-bookworm AS python-builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-install-project

# Builder stage: Node.js依存関係（pptxgenjs）
FROM node:22-slim AS node-builder

WORKDIR /app/pptxjs_env

COPY src/ai_agent_work_base/skills/pptxjs_env/package.json ./
COPY src/ai_agent_work_base/skills/pptxjs_env/package-lock.json ./

RUN npm ci --omit=dev

# Runtime stage
FROM python:3.12-slim-bookworm

WORKDIR /app

# Node.jsをインストール（pptxgenjsスクリプト実行用）
RUN apt-get update && apt-get install -y --no-install-recommends \
    nodejs \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from python-builder
COPY --from=python-builder /app/.venv /app/.venv

# Copy node_modules from node-builder
COPY --from=node-builder /app/pptxjs_env/node_modules \
    /app/src/ai_agent_work_base/skills/pptxjs_env/node_modules

# Enable venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY src ./src
COPY workflows ./workflows
COPY pyproject.toml .

# Expose port for Chainlit
EXPOSE 8000

# Run Chainlit
CMD ["chainlit", "run", "src/ai_agent_work_base/app.py", "--host", "0.0.0.0", "--port", "8000"]

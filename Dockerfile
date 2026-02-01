# Builder stage
FROM python:3.12-slim-bookworm AS builder

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-install-project

# Runtime stage
FROM python:3.12-slim-bookworm

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Enable venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy application code
COPY src ./src
COPY pyproject.toml .

# Expose port for Chainlit
EXPOSE 8000

# Run Chainlit
CMD ["chainlit", "run", "src/ai_agent_work_base/app.py", "--host", "0.0.0.0", "--port", "8000"]

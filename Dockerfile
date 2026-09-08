FROM ghcr.io/astral-sh/uv:0.11.7-python3.12-bookworm-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "gunicorn", "mctp_api.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]

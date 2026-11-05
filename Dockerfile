FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    UV_PYTHON=3.12 \
    PATH="/opt/venv/bin:$PATH"

RUN pip install --no-cache-dir uv==0.11.7
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY . .

RUN SECRET_KEY=build-only-not-for-production python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "mctp_api.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "2"]

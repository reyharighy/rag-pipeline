FROM python:3.12-slim AS base

WORKDIR /app

RUN pip install uv
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /app

USER appuser

COPY --chown=appuser:appuser pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY --chown=appuser:appuser . .

FROM base as development
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
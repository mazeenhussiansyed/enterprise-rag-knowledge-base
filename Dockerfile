FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY scripts ./scripts
COPY data/corpus ./data/corpus

RUN python -m pip install --no-cache-dir .

EXPOSE 8000
EXPOSE 7860
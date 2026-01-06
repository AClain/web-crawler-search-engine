FROM python:3.11-slim-trixie

RUN apt-get update
RUN apt-get install -y libpq-dev gcc

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml pyproject.toml
COPY uv.lock uv.lock

RUN uv add psycopg2-binary

RUN uv sync

COPY .env .env
COPY logs/ logs/
COPY src/ src/
FROM python:3.10.16
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml .
COPY .python-version .
COPY main.py .

# Install dependencies
RUN uv sync

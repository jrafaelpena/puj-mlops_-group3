FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY app/pyproject.toml .
COPY app/.python-version .
COPY app/main.py .
COPY app/uv.lock .
COPY app/model.pkl .

# Install dependencies
RUN uv sync --frozen

# Expose port 8989
EXPOSE 8989

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8989"]
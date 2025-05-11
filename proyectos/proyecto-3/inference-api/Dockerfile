FROM python:3.12
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml .
COPY .python-version .
COPY main.py .
COPY uv.lock .

# Install dependencies
RUN uv sync --frozen

# Expose port 8989
EXPOSE 8989

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8989"]
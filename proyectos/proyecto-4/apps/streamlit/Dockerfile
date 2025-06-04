FROM python:3.10-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml .
COPY uv.lock .

# Install dependencies
RUN uv sync --frozen

COPY streamlit_app.py .

# Expose Streamlit's default port
EXPOSE 8501

# Command to run the Streamlit app
CMD ["uv", "run", "streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0", "--server.port=8501"]
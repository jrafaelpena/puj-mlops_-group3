FROM apache/airflow:2.10.5

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/

# Create the temp directory first
RUN mkdir -p /tmp/build

# Copy your pyproject.toml to the temp directory
COPY pyproject.toml /tmp/build/pyproject.toml

USER root
RUN cd /tmp/build && uv pip install --system .

USER airflow
